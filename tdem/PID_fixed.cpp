/************************************************************************
 * MechSys - Open Library for Mechanical Systems                        *
 * Copyright (C) 2009 Sergio Galindo                                    *
 *                                                                      *
 * This program is free software: you can redistribute it and/or modify *
 * it under the terms of the GNU General Public License as published by *
 * the Free Software Foundation, either version 3 of the License, or    *
 * any later version.                                                   *
 *                                                                      *
 * This program is distributed in the hope that it will be useful,      *
 * but WITHOUT ANY WARRANTY; without even the implied warranty of       *
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the         *
 * GNU General Public License for more details.                         *
 *                                                                      *
 * You should have received a copy of the GNU General Public License    *
 * along with this program. If not, see <http://www.gnu.org/licenses/>  *
 ************************************************************************/

// MechSys
#include <mechsys/dem/domain.h>
#include <mechsys/util/fatal.h>
#include <mechsys/util/util.h>
#include <mechsys/mesh/unstructured.h>
#include <mechsys/linalg/matvec.h>

#include <cmath>

using std::cout;
using std::endl;

struct UserData
{
    bool               isfailure;   ///< Is a failuretest ?
    bool               RenderVideo;  ///< RenderVideo ?
    size_t             InitialIndex; ///< The initial index marking the bounding box
    double             Thf;          ///< Angle in the p=cte plane
    double             Alp;          ///< Angle in the p q plane
    double             dt;           ///< Time step
    double             tspan;        ///< Time span for the different stages
    Vec3_t             Sig;          ///< Current stress state
    Vec3_t             Sig0;         ///< Initial stress state
    Vec3_t             DSig;         ///< Total stress increment to be applied by Solve => after
    bVec3_t            pSig;         ///< Prescribed stress ?
    Vec3_t             L0;           ///< Initial length of the packing
    std::ofstream      oss_ss;       ///< file for stress strain data

    //Constructor
    UserData() {Sig = 0.0,0.0,0.0;}     
};

void SetTxTest (Vec3_t const & Sigf, bVec3_t const & pEps, Vec3_t const & dEpsdt, bool TheStrainCtrl, UserData & UD, DEM::Domain const & D)
{
    if (TheStrainCtrl)
    {
        UD.pSig = false,false,false;
        UD.Sig  = Vec3_t(0.0,0.0,0.0);
        UD.pSig = false, false, false;
        // Strain controlled test
        for (int i=0;i<3;i++)
        {
            if (pEps(i))    UD.pSig(i) = true;
            else            UD.Sig(i)  = Sigf(i);
        }
    }
    else
    {
        UD.pSig = true,true,true; // fully stress controlled
        UD.Sig  = Sigf;
    }
    //UD.DSig   = UD.Sig - UD.Sig0;
    UD.Sig0   = UD.Sig; // because the stress will be ramped
    UD.tspan  = 0.0;

    if (!TheStrainCtrl)
    {
        for (int i=0;i<D.Particles.Size();i++)
        {
            if (!D.Particles[i]->IsFree()) continue;
            D.Particles[i]->Sig0(i, D.Particles[i]->Props.eps, UD.Sig0);
        }
    }
}


void ResetEps (DEM::Domain const & D, UserData & UD)
{
    for (size_t i=0;i<D.Particles.Size();i++)
    {
        if (!D.Particles[i]->IsFree()) continue;
        D.Particles[i]->epsp  = 0.0;
        D.Particles[i]->epspn = 0.0;
        D.Particles[i]->epspw = 0.0;
        D.Particles[i]->epspt = 0.0;
    }
}

// P, Q, Theta to L1, L2, L3 (principal stresses)
void pqth2L (double p, double q, double th, Vec3_t & L, const char* Mode)
{
    if (strcmp(Mode,"cam")==0)
    {
        L(0) = p + 2.0/3.0*q*cos(th);
        L(1) = p + 2.0/3.0*q*cos(th-2.0*M_PI/3.0);
        L(2) = p + 2.0/3.0*q*cos(th+2.0*M_PI/3.0);
    }
    else if (strcmp(Mode,"axi")==0)
    {
        L(0) = p + 1.0/3.0*q;
        L(1) = p + 1.0/3.0*q;
        L(2) = p - 2.0/3.0*q;
    }
    else if (strcmp(Mode,"txe")==0)
    {
        L(0) = p + 1.0/3.0*q;
        L(1) = p - 2.0/3.0*q;
        L(2) = p + 1.0/3.0*q;
    }
    else
    {
        throw new Fatal("Mode <%s> not supported: pqth2L",Mode);
    }
}

// PID controller for triaxial test
double PIDcontrol(double setpoint, double current, double dt, double &integral, double &previous_error, 
    double kp, double ki, double kd)
{
    double error = setpoint - current;
    integral += error * dt;
    double derivative = (error - previous_error) / dt;
    previous_error = error;
    return kp * error + ki * integral + kd * derivative;
}

double computeStress(int dir, DEM::Domain const & d, UserData & UD)
{
    double stress = 0;
    double volume = 0;
    for (size_t i=0;i<d.Particles.Size();i++)
    {
        if (!d.Particles[i]->IsFree()) continue;
        stress += d.Particles[i]->F(i,dir);
        //Vec3_t pos = d.Particles[i]->x;
        //double ep = d.Particles[i]->Props.eps;
        //Vec3_t L0 = UD.L0;
        //if (L0.Norm() < 1e-12) continue;
        //// approximate stress
        //double press = (d.Particles[i]->Ff(dir) + d.Particles[i]->F(dir)) / (3.0*L0((dir+1)%3)*L0((dir+2)%3));
        //stress += press;
        //volume += 1;
    }
    //return stress/volume*L0(0)*L0(1)*L0(2);
    return stress/(UD.L0(0)*UD.L0(1)*UD.L0(2));
}

void Ramptest(Vec3_t & Sig, Vec3_t & Sig0, Vec3_t & dS, double dt, double tspan, double t, bool TheStrainCtrl)
{
    if (tspan>1.0e-12)
    {
        Sig = Sig0 + dS*t/tspan;
    }
    else
    {
        Sig = Sig0;
    }
}

// calculate Principal stresses
void principalstress (Vec3_t & Sig, DEM::Domain const & d, UserData & UD)
{
    for (size_t i=0;i<3;i++) Sig(i) = computeStress(i,d,UD);
}

// calculate packing length
void getlength (Vec3_t & L, DEM::Domain const & d, UserData & UD)
{
    double xmax=-1e12,ymax=-1e12,zmax=-1e12;
    double xmin=1e12,ymin=1e12,zmin=1e12;
    
    for(size_t i=0;i<d.Particles.Size();i++)
    {
        if(!d.Particles[i]->IsFree()) continue;
        Vec3_t pos = d.Particles[i]->x;
        xmax = std::max(pos(0), xmax);
        ymax = std::max(pos(1), ymax);
        zmax = std::max(pos(2), zmax);
        xmin = std::min(pos(0), xmin);
        ymin = std::min(pos(1), ymin);
        zmin = std::min(pos(2), zmin);
    }
    L = Vec3_t(xmax-xmin, ymax-ymin, zmax-zmin);
}

// Setup function
void Setup (DEM::Domain & dom, void * UserDataPointer)
{
    UserData & dat = *((UserData *)UserDataPointer);
    double dt = dom.dt;
    
    // compute packing length
    Vec3_t L (dat.L0);
    getlength(L,dom,dat);
    
    // compute principal stresses
    Vec3_t Sig;
    principalstress(Sig,dom,dat);
    
    // compute strain 
    Vec3_t Eps = L/dat.L0 - Vec3_t(1.0,1.0,1.0);
    Vec3_t Epsv = Eps(0) + Eps(1) + Eps(2);
    
    dat.oss_ss << dom.Time << " " << Sig(0) << " " << Sig(1) << " " << Sig(2) << " " << Eps(0) << " " << Eps(1) << " " << Eps(2) << " " << Epsv << endl;
    
    // Linear move of walls
    if (dom.Time <= dat.tspan)
    {
        Vec3_t dS = dat.Sig - dat.Sig0;
        Ramptest(Sig,dat.Sig0,dS,dt,dat.tspan,dom.Time, dat.isfailure);
    }
    
    // prepare bounding plane movement
    for (size_t i = dat.InitialIndex; i < dom.Particles.Size(); i++)
    {
        // plane identification
        if        (dom.Particles[i]->Tag == -2) {
            // Left wall
            if (dat.pSig(0)) {
                dom.Particles[i]->v(0) = dt * Sig(0) / (L(1)*L(2)) / (dom.Particles[i]->Props.rho * M_PI * pow(dom.Particles[i]->Props.R,3.0));
                dom.Particles[i]->vxf = false;
            } else {
                dom.Particles[i]->v(0) = 0.0;
                dom.Particles[i]->vxf = true;
            }
        } else if (dom.Particles[i]->Tag == -3) {
            // Right wall
            if (dat.pSig(0)) {
                dom.Particles[i]->v(0) = -dt * Sig(0) / (L(1)*L(2)) / (dom.Particles[i]->Props.rho * M_PI * pow(dom.Particles[i]->Props.R,3.0));
                dom.Particles[i]->vxf = false;
            } else {
                dom.Particles[i]->v(0) = 0.0;
                dom.Particles[i]->vxf = true;
            }
        } else if (dom.Particles[i]->Tag == -4) {
            if (dat.pSig(1)) {
                dom.Particles[i]->v(1) = dt * Sig(1) / (L(0)*L(2)) / (dom.Particles[i]->Props.rho * M_PI * pow(dom.Particles[i]->Props.R,3.0));
                dom.Particles[i]->vyf = false;
            } else {
                dom.Particles[i]->v(1) = 0.0;
                dom.Particles[i]->vyf = true;
            }
        } else if (dom.Particles[i]->Tag == -5) {
            if (dat.pSig(1)) {
                dom.Particles[i]->v(1) = -dt * Sig(1) / (L(0)*L(2)) / (dom.Particles[i]->Props.rho * M_PI * pow(dom.Particles[i]->Props.R,3.0));
                dom.Particles[i]->vyf = false;
            } else {
                dom.Particles[i]->v(1) = 0.0;
                dom.Particles[i]->vyf = true;
            }
        } else if (dom.Particles[i]->Tag == -6) {
            if (dat.pSig(2)) {
                dom.Particles[i]->v(2) = dt * Sig(2) / (L(0)*L(1)) / (dom.Particles[i]->Props.rho * M_PI * pow(dom.Particles[i]->Props.R,3.0));
                dom.Particles[i]->vzf = false;
            } else {
                dom.Particles[i]->v(2) = 0.0;
                dom.Particles[i]->vzf = true;
            }
        } else if (dom.Particles[i]->Tag == -7) {
            if (dat.pSig(2)) {
                dom.Particles[i]->v(2) = -dt * Sig(2) / (L(0)*L(1)) / (dom.Particles[i]->Props.rho * M_PI * pow(dom.Particles[i]->Props.R,3.0));
                dom.Particles[i]->vzf = false;
            } else {
                dom.Particles[i]->v(2) = 0.0;
                dom.Particles[i]->vzf = true;
            }
        }
    }
}


// Report function
void Report (DEM::Domain const & dom, void * UserDataPointer)
{
    UserData * ud = (UserData*)(UserDataPointer);
    if (!ud->RenderVideo) return;
    dom.WriteXDMF("pid");
}


// Main
int main (int argc, char ** argv) try
{
    if (argc<2)
    {
        cout << "\nUsage: PID <input_file_key> [Nproc] [mostlyspheres] [binsize]\n\n";
        cout << "Example: PID test_pid 1\n\n";
        return 1;
    }

    size_t Nproc         = 1;
    bool   mostlyspheres = false;
    double binsize       = 2.0;
    if (argc>=3) Nproc         = atoi(argv[2]);
    if (argc>=4) mostlyspheres = atoi(argv[3]);
    if (argc>=5) binsize       = atof(argv[4]);
    String filekey  (argv[1]);
    String filename (filekey+".inp");
    if (!Util::FileExists(filename)) throw new Fatal("File <%s> not found",filename.CStr());
    ifstream infile(filename.CStr());
    
    double verlet;      // Verlet distance for optimization
    String ptype;       // Particle type 
    size_t RenderVideo; // Decide is video should be render=
    double fraction;    // Fraction of particles to be generated
    double Kn;          // Normal stiffness
    double Kt;          // Tangential stiffness
    double Gn;          // Normal dissipative coefficient
    double Gt;          // Tangential dissipative coefficient
    double Mu;          // Microscopic friction coefficient
    double Beta;        // Rolling stiffness coefficient (only for spheres)
    double Eta;         // Plastic moment coefficient (only for spheres, 0 if rolling resistance is not used)
    double Bn;          // Cohesion normal stiffness
    double Bt;          // Cohesion tangential stiffness
    double Bm;          // Cohesion torque stiffness
    double Eps;         // Threshold for breking bonds
    double R;           // Spheroradius
    size_t seed;        // Seed of the ramdon generator
    double dt;          // Time step
    double dtOut;       // Time step for output
    double Lx;          // Lx
    double Ly;          // Ly
    double Lz;          // Lz
    size_t nx;          // nx
    size_t ny;          // ny
    size_t nz;          // nz
    double rho;         // rho
    double p0;          // Pressure for the isotropic compression
    double T0;          // Time span for the compression
    bool   isfailure;   // Flag for a failure stress path
    bool   pssrx;       // Prescribed strain rate in X ?
    bool   pssry;       // Prescribed strain rate in Y ?
    bool   pssrz;       // Prescribed strain rate in Z ?
    double srx;         // Final Strain x
    double sry;         // Final Strain y
    double srz;         // Final Strain z
    double pf;          // Final pressure p
    double qf;          // Final deviatoric stress q
    double Tf;          // Final time for the test
    {
        infile >> verlet;       infile.ignore(200,'\n');
        infile >> ptype;        infile.ignore(200,'\n');
        infile >> RenderVideo;  infile.ignore(200,'\n');
        infile >> fraction;     infile.ignore(200,'\n');
        infile >> Kn;           infile.ignore(200,'\n');
        infile >> Kt;           infile.ignore(200,'\n');
        infile >> Gn;           infile.ignore(200,'\n');
        infile >> Gt;           infile.ignore(200,'\n');
        infile >> Mu;           infile.ignore(200,'\n');
        infile >> Beta;         infile.ignore(200,'\n');
        infile >> Eta;          infile.ignore(200,'\n');
        infile >> Bn;           infile.ignore(200,'\n');
        infile >> Bt;           infile.ignore(200,'\n');
        infile >> Bm;           infile.ignore(200,'\n');
        infile >> Eps;          infile.ignore(200,'\n');
        infile >> R;            infile.ignore(200,'\n');
        infile >> seed;         infile.ignore(200,'\n');
        infile >> dt;           infile.ignore(200,'\n');
        infile >> dtOut;        infile.ignore(200,'\n');
        infile >> Lx;           infile.ignore(200,'\n');
        infile >> Ly;           infile.ignore(200,'\n');
        infile >> Lz;           infile.ignore(200,'\n');
        infile >> nx;           infile.ignore(200,'\n');
        infile >> ny;           infile.ignore(200,'\n');
        infile >> nz;           infile.ignore(200,'\n');
        infile >> rho;          infile.ignore(200,'\n');
        infile >> p0;           infile.ignore(200,'\n');
        infile >> T0;           infile.ignore(200,'\n');
        infile >> isfailure;    infile.ignore(200,'\n');
        infile >> pssrx;        infile.ignore(200,'\n');
        infile >> pssry;        infile.ignore(200,'\n');
        infile >> pssrz;        infile.ignore(200,'\n');
        infile >> srx;          infile.ignore(200,'\n');
        infile >> sry;          infile.ignore(200,'\n');
        infile >> srz;          infile.ignore(200,'\n');
        infile >> pf;           infile.ignore(200,'\n');
        infile >> qf;           infile.ignore(200,'\n');
        infile >> Tf;           infile.ignore(200,'\n');
    }


    // domain and User data
    UserData dat;
    DEM::Domain dom(&dat);
    dom.Alpha=verlet;
    dom.Beta = binsize;
    dom.MostlySpheres = mostlyspheres;
    dat.dt = dt;
    dat.RenderVideo = (bool) RenderVideo;


    Vec3_t Xmin(-0.5*Lx,-0.5*Ly,-0.5*Lz);
    Vec3_t Xmax = -Xmin;
    dom.GenSpheresBox (-1, Xmin, Xmax, R, rho, "HCP",    seed, fraction, Eps);


    dat.InitialIndex = dom.Particles.Size();
    dom.GenBoundingBox (/*InitialTag*/-2, 0.02*R, /*Cf*/1.3,0);
    

    // properties of particles prior the triaxial test
    Dict B;
    B.Set(-1,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,Mu ,Beta,Eta,Bn,Bt ,Bm ,     Eps);
    B.Set(-2,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,0.0,Beta,Eta,Bn,0.0,0.0,-0.1*Eps);
    B.Set(-3,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,0.0,Beta,Eta,Bn,0.0,0.0,-0.1*Eps);
    B.Set(-4,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,0.0,Beta,Eta,Bn,0.0,0.0,-0.1*Eps);
    B.Set(-5,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,0.0,Beta,Eta,Bn,0.0,0.0,-0.1*Eps);
    B.Set(-6,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,0.0,Beta,Eta,Bn,0.0,0.0,-0.1*Eps);
    B.Set(-7,"Kn Kt Gn Gt Mu Beta Eta Bn Bt Bm Eps",Kn,Kt,Gn,Gt,0.0,Beta,Eta,Bn,0.0,0.0,-0.1*Eps);
    dom.SetProps(B);

    // stage 1: isotropic compresssion
    String fkey_a(filekey+"_a");
    String fkey_b(filekey+"_b");
    Vec3_t  sigf;
    bVec3_t peps(false, false, false);
    Vec3_t  depsdt(0.0,0.0,0.0);

    sigf =  Vec3_t(-p0,-p0,-p0);
    dat.Sig = sigf;
    ResetEps  (dom,dat);
    SetTxTest (sigf, peps, depsdt,false,dat,dom);
    dat.tspan = T0/2.0 - dom.Time;
    dom.Solve  (/*tf*/T0/2.0, /*dt*/dt, /*dtOut*/dtOut, &Setup, &Report, fkey_a.CStr(),RenderVideo,Nproc);
    dom.Save(fkey_a.CStr());
    SetTxTest (sigf, peps, depsdt,false,dat,dom);
    dat.tspan = T0 - dom.Time;
    dom.Solve (/*tf*/T0, /*dt*/dt, /*dtOut*/dtOut, &Setup, &Report, fkey_b.CStr(),RenderVideo,Nproc);
    dom.Save(fkey_b.CStr());

    // stage 2: The proper triaxial test
    String fkey_c(filekey+"_c");
    Vec3_t lf;
    pqth2L (pf, qf, 0.0, lf, "cam");
    sigf   = lf(0), lf(1), lf(2);
    peps   = bVec3_t(pssrx, pssry, pssrz);
    depsdt = Vec3_t(srx/(Tf-dom.Time), sry/(Tf-dom.Time), srz/(Tf-dom.Time));
    
    ResetEps  (dom,dat);
    SetTxTest (sigf, peps, depsdt, isfailure, dat, dom);
    dat.tspan = Tf - dom.Time;
    dom.Solve (/*tf*/Tf, /*dt*/dt, /*dtOut*/dtOut, &Setup, &Report, fkey_c.CStr(),RenderVideo,Nproc);
    dom.Save(fkey_c.CStr());
    
    return 0;
}
MECHSYS_CATCH