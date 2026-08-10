// MechSys
#include <mechsys/dem/domain.h>
#include <mechsys/util/fatal.h>
#include <mechsys/util/util.h>
#include <mechsys/mesh/unstructured.h>
#include <mechsys/linalg/matvec.h>

using std::cout;
using std::endl;


struct UserData
{
    bool               StrainCtrl;   ///< Is a failuretest ?
    bool               RenderVideo;  ///< RenderVideo ?
    size_t             InitialIndex; ///< The initial index marking the bounding box
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

double PID(double SP, double PV, double dt)
{
    static double prev_error = 0.0;
    static bool   first_iter = true;
    static double integral   = 0.0;

    double error = SP - PV;
    double kp = 0.01;
    double ki = 0.001;
    double kd = 0.001;
    
    if (first_iter == true)
    {
        prev_error = error;
        first_iter = false;
    }

    double P = kp*error;

    integral = ((error + prev_error)/2)*dt*ki;

    double D = ((error - prev_error)/dt)*kd;

    prev_error = error;

    return P + integral + D;
}

void SetTxTest (Vec3_t const & Sigf, bVec3_t const & pEps, Vec3_t const & dEpsdt, bool TheStrainCtrl, UserData & UD, DEM::Domain const & D)
{
    std::cout << "\033[1;33m\n--- Setting up Triaxial Test -------------------------------------\033[0m\n";
    double start = std::clock();

    UD.StrainCtrl = TheStrainCtrl;
    if (TheStrainCtrl) UD.Sig0 = UD.Sig;

    for (size_t i=0; i<D.Particles.Size(); i++) D.Particles[i]->Initialize(i);

    UD.pSig = false, false, false;

    // Eps(0) prescribed ?
    Vec3_t veloc;
    double area;
    double pforce;
    double force_x;
    double Velocity;
    
    area = (D.Particles[UD.InitialIndex+2]->x(1)-D.Particles[UD.InitialIndex+3]->x(1))*(D.Particles[UD.InitialIndex+4]->x(2)-D.Particles[UD.InitialIndex+5]->x(2));
    force_x = UD.Sig(0)*area;
    pforce = UD.Sig0(0)*area;
    Velocity = PID(pforce , force_x, UD.dt);
    D.Particles[UD.InitialIndex  ]->v =  Velocity;
    D.Particles[UD.InitialIndex  ]->FixVeloc();
    D.Particles[UD.InitialIndex  ]->vxf = false;
    D.Particles[UD.InitialIndex+1]->Ff = -Velocity;
    D.Particles[UD.InitialIndex+1]->FixVeloc();
    D.Particles[UD.InitialIndex+1]->vxf = false;
    UD.pSig(0) = true;

    // Eps(1) prescribed ?
    area = (D.Particles[UD.InitialIndex]->x(0)-D.Particles[UD.InitialIndex+1]->x(0))*(D.Particles[UD.InitialIndex+4]->x(2)-D.Particles[UD.InitialIndex+5]->x(2));
    force_x = UD.Sig(1)*area;
    pforce = UD.Sig0(1)*area;
    Velocity = PID(pforce , force_x, UD.dt);
    D.Particles[UD.InitialIndex+2]->v =  Velocity;
    D.Particles[UD.InitialIndex+2]->FixVeloc();
    D.Particles[UD.InitialIndex+2]->vyf = false;
    D.Particles[UD.InitialIndex+3]->v = -Velocity;
    D.Particles[UD.InitialIndex+3]->FixVeloc();
    D.Particles[UD.InitialIndex+3]->vyf = false;
    UD.pSig(1) = true;

    // Eps(2) prescribed ?
    double height = (D.Particles[UD.InitialIndex+4]->x(2)-D.Particles[UD.InitialIndex+5]->x(2));
    veloc = 0.0, 0.0, 0.5*dEpsdt(2)*height;
    D.Particles[UD.InitialIndex+4]->Ff = 0.0,0.0,0.0;
    D.Particles[UD.InitialIndex+4]->FixVeloc();
    D.Particles[UD.InitialIndex+4]->v  =  veloc;
    D.Particles[UD.InitialIndex+5]->Ff = 0.0,0.0,0.0;
    D.Particles[UD.InitialIndex+5]->FixVeloc();
    D.Particles[UD.InitialIndex+5]->v  = -veloc;

    double total = std::clock() - start;
    std::cout << "\033[1;36m    Time elapsed          = \033[1;31m" <<static_cast<double>(total)/CLOCKS_PER_SEC<<" seconds\033[0m\n";
}



void ResetEps(DEM::Domain const & dom, UserData & UD)
{
    UD.L0(0) = dom.Particles[UD.InitialIndex  ]->x(0)-dom.Particles[UD.InitialIndex+1]->x(0);
    UD.L0(1) = dom.Particles[UD.InitialIndex+2]->x(1)-dom.Particles[UD.InitialIndex+3]->x(1);
    UD.L0(2) = dom.Particles[UD.InitialIndex+4]->x(2)-dom.Particles[UD.InitialIndex+5]->x(2);
}



void Setup (DEM::Domain & dom, void * UD)
{
    UserData & dat = (*static_cast<UserData *>(UD));
    Vec3_t force;
    Vec3_t pforce;
    double Velocity;
    bool   update_sig = false;

    double area = (dom.Particles[dat.InitialIndex+2]->x(1)-dom.Particles[dat.InitialIndex+3]->x(1))*(dom.Particles[dat.InitialIndex+4]->x(2)-dom.Particles[dat.InitialIndex+5]->x(2));
    force  = dat.Sig(0)*area, 0.0, 0.0;
    pforce = dat.Sig0(0)*area, 0.0, 0.0;
    Velocity = PID(pforce(0) , force(0), dat.dt);
    dom.Particles[dat.InitialIndex  ]->v = Velocity;
    dom.Particles[dat.InitialIndex+1]->v = -Velocity;
    if (!dat.StrainCtrl) update_sig = true;

    area = (dom.Particles[dat.InitialIndex]->x(0)-dom.Particles[dat.InitialIndex+1]->x(0))*(dom.Particles[dat.InitialIndex+4]->x(2)-dom.Particles[dat.InitialIndex+5]->x(2));
    force  = 0.0, dat.Sig(1)*area, 0.0;
    pforce = 0.0, dat.Sig0(1)*area, 0.0;
    Velocity = PID(pforce(1) , force(1), dat.dt);
    dom.Particles[dat.InitialIndex+2]->v =  Velocity;
    dom.Particles[dat.InitialIndex+3]->v = -Velocity;
    if (!dat.StrainCtrl) update_sig = true;
    
    area = (dom.Particles[dat.InitialIndex]->x(0)-dom.Particles[dat.InitialIndex+1]->x(0))*(dom.Particles[dat.InitialIndex+2]->x(1)-dom.Particles[dat.InitialIndex+3]->x(1));
    dat.Sig(2) = -0.5*(dom.Particles[dat.InitialIndex+4]->F(2)-dom.Particles[dat.InitialIndex+5]->F(2))/area;
    
    if (update_sig) dat.Sig += dat.dt*dat.DSig/(dat.tspan);
}


void Report (DEM::Domain & dom, void *UD)
{
    UserData & dat = (*static_cast<UserData *>(UD));

    if (dom.idx_out==0)
    {
        String fs;
        fs.Printf("%s_walls.res",dom.FileKey.CStr());
        dat.oss_ss.open(fs.CStr());
        dat.oss_ss << Util::_10_6 << "Time" << Util::_8s << "sx" << Util::_8s << "sy" << Util::_8s << "sz";
        dat.oss_ss <<                          Util::_8s << "ex" << Util::_8s << "ey" << Util::_8s << "ez";
        dat.oss_ss << Util::_8s   << "e"                         << Util::_8s << "Nc" << Util::_8s << "Nsc";         
        dat.oss_ss <<                                               Util::_8s << "Nb" << Util::_8s << "Nbb" << "\n";
    }
    if (dat.RenderVideo)
    {
        String ff;
        ff.Printf    ("%s_bf_%04d",dom.FileKey.CStr(), dom.idx_out);
        dom.WriteBF(ff.CStr());
    }
    if (!dom.Finished) 
    {
        dat.oss_ss << Util::_10_6 << dom.Time << Util::_8s << dat.Sig(0) << Util::_8s << dat.Sig(1) << Util::_8s << dat.Sig(2);

        dat.oss_ss << Util::_8s << (dom.Particles[dat.InitialIndex  ]->x(0)-dom.Particles[dat.InitialIndex+1]->x(0)-dat.L0(0))/dat.L0(0);
        dat.oss_ss << Util::_8s << (dom.Particles[dat.InitialIndex+2]->x(1)-dom.Particles[dat.InitialIndex+3]->x(1)-dat.L0(1))/dat.L0(1);
        dat.oss_ss << Util::_8s << (dom.Particles[dat.InitialIndex+4]->x(2)-dom.Particles[dat.InitialIndex+5]->x(2)-dat.L0(2))/dat.L0(2);

        double volumecontainer = (dom.Particles[dat.InitialIndex  ]->x(0)-dom.Particles[dat.InitialIndex+1]->x(0)-dom.Particles[dat.InitialIndex  ]->Props.R+dom.Particles[dat.InitialIndex+1]->Props.R)*
                                 (dom.Particles[dat.InitialIndex+2]->x(1)-dom.Particles[dat.InitialIndex+3]->x(1)-dom.Particles[dat.InitialIndex+2]->Props.R+dom.Particles[dat.InitialIndex+3]->Props.R)*
                                 (dom.Particles[dat.InitialIndex+4]->x(2)-dom.Particles[dat.InitialIndex+5]->x(2)-dom.Particles[dat.InitialIndex+4]->Props.R+dom.Particles[dat.InitialIndex+5]->Props.R);

        dat.oss_ss << Util::_8s << (volumecontainer-dom.Vs)/dom.Vs;

        size_t Nc = 0;
        size_t Nsc = 0;
        for (auto it=dom.PairtoCInt.begin();it!=dom.PairtoCInt.end();++it)
        {
            if(it->second->I2<dat.InitialIndex)
            {
                Nc  += it->second->Nc;
                Nsc += it->second->Nsc;
            }
        }

        size_t Nb  = dom.BInteractons.Size();
        size_t Nbb = 0;
        for (size_t i=0; i<dom.BInteractons.Size(); i++)
        {
            if(!dom.BInteractons[i]->valid)
            {
                Nbb ++;
            }
        }

        dat.oss_ss << Util::_8s << Nc << Util::_8s << Nsc << Util::_8s << Nb << Util::_8s << Nbb;

        dat.oss_ss << std::endl;
    }
    else
    {
        dat.oss_ss.close();
        String fn;
        fn.Printf("%s_forces.res",dom.FileKey.CStr());
        std::ofstream OF(fn.CStr());
        OF <<  Util::_10_6 << "Fn" << Util::_8s << "Ft" << Util::_8s << "NContacts" << Util::_8s << "Issliding" << "\n";

        String f;
        f.Printf("%s_stress.res",dom.FileKey.CStr());
        std::ofstream SF(f.CStr());
        Mat3_t S,B;
        for (size_t m=0;m<3;m++)
        {
            for (size_t n=0;n<3;n++)
            {
                S(m,n)=0.0;
                B(m,n)=0.0;
            }
        }
        double volumecontainer = (dom.Particles[dat.InitialIndex  ]->x(0)-dom.Particles[dat.InitialIndex+1]->x(0)-dom.Particles[dat.InitialIndex  ]->Props.R-dom.Particles[dat.InitialIndex+1]->Props.R)*
                                 (dom.Particles[dat.InitialIndex+2]->x(1)-dom.Particles[dat.InitialIndex+3]->x(1)-dom.Particles[dat.InitialIndex+2]->Props.R-dom.Particles[dat.InitialIndex+3]->Props.R)*
                                 (dom.Particles[dat.InitialIndex+4]->x(2)-dom.Particles[dat.InitialIndex+5]->x(2)-dom.Particles[dat.InitialIndex+4]->Props.R-dom.Particles[dat.InitialIndex+5]->Props.R);
        for (auto it=dom.PairtoCInt.begin();it!=dom.PairtoCInt.end();++it)
        {
            DEM::CInteracton * CI = it->second;
            if (CI->Nc>0&&CI->P1->IsFree()&&CI->P2->IsFree())
            {
                Vec3_t branch    = CI->P2->x - CI->P1->x;
                for (size_t m=0;m<3;m++)
                {
                    for (size_t n=0;n<3;n++)
                    {
                        S(m,n) += (CI->Fnet(m) + CI->Ftnet(m))*branch(n)/volumecontainer;
                    }
                }
            }
        }
        size_t Ncontacts = 0;
        for (auto it=dom.PairtoCInt.begin();it!=dom.PairtoCInt.end();++it)
        {
            if (norm(it->second->Fnet)>0.0&&it->second->P1->IsFree()&&it->second->P2->IsFree())
            {
                OF << Util::_10_6 << it->second->Fnet(0) << Util::_8s << it->second->Fnet(1) << Util::_8s << it->second->Fnet(2) << Util::_8s <<  "\n";
                Ncontacts+=it->second->Nc;
            }
        }
        OF.close();

        for (size_t m=0;m<3;m++)
        {
            for (size_t n=0;n<3;n++)
            {
                SF << Util::_8s << S(m,n);
            }
            SF << std::endl;
        }
        for (size_t m=0;m<3;m++)
        {
            for (size_t n=0;n<3;n++)
            {
                SF << Util::_8s << B(m,n)/Ncontacts;
            }
            SF << std::endl;
        }
        SF.close();
    }
}



int main(int argc, char **argv) try

{
    
    if (argc<2) throw new Fatal("This program must be called with one argument: the name of the data input file without the '.inp' suffix.\nExample:\t %s filekey\n",argv[0]);  
    

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
    dom.Solve     (/*tf*/Tf, /*dt*/dt, /*dtOut*/dtOut, &Setup, &Report, fkey_c.CStr(),RenderVideo,Nproc);
    dom.Save(fkey_c.CStr());

    return 0;
}
MECHSYS_CATCH