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
 * along with this program. If not, see <ttp://www.gnu.org/licenses/>  *
 ************************************************************************/

/////////////////////// Two-sphere contact model test

// Std Lib
#include <cctype>
#include <sstream>
#include <string>

// MechSys
#include <mechsys/dem/domain.h>
#include <mechsys/util/fatal.h>
#include <mechsys/util/util.h>
#include <mechsys/mesh/unstructured.h>
#include <mechsys/linalg/matvec.h>

using std::cout;
using std::endl;

int main(int argc, char **argv) try
{
    // set the simulation domain ////////////////////////////////////////////////////////////////////////////

    if (argc<2) throw new Fatal("This program must be called with one argument: the name of the data input file without the '.inp' suffix.\nExample:\t %s filekey\n",argv[0]);
    //number of threads
    size_t Nproc = 1; 
    double dthoot= 4.0;     
    if (argc>=3) Nproc =atoi(argv[2]);
    if (argc>=4) dthoot=atof(argv[3]);
    String filekey  (argv[1]);
    String filename (filekey+".inp");
    if (!Util::FileExists(filename)) throw new Fatal("File <%s> not found",filename.CStr());
    ifstream infile(filename.CStr());
    
    double verlet;      // Verlet distance for optimization
    String contactlaw;  // Particle type 
    size_t  RenderVideo;// Decide is video should be render
    String particleList;    // Name of the soil to import
    double Kn;          // Normal stiffness
    double Kt;          // Tangential stiffness
    double Gn;          // Normal dissipative coefficient
    double Gt;          // Tangential dissipative coefficient
    double Mu0;         // Microscopic friction coefficient at the initial stage
    double Beta;        // Rolling stiffness coefficient (only for spheres)
    double Eta;         // Plastic moment coefficient (only for spheres, 0 if rolling resistance is not used)
    double dt;          // Time step
    double dtOut;       // Time step for output
    double rho;         // rho
    double appliedVelocity;         // Strain rate for shearing
    double Tf;          // Final time for the test
    size_t sphereCoulombMode = 0;
    int tensileCutoff = 1;
    int velocityVerlet = 1;
double X1;	
double Y1;	
double Z1;	
double X2;	
double Y2;	
double Z2;	
double R;

    {
        infile >> verlet;       infile.ignore(200,'\n');
        infile >> contactlaw;   infile.ignore(200,'\n');
        infile >> RenderVideo;  infile.ignore(200,'\n');
        infile >> Kn;           infile.ignore(200,'\n');
        infile >> Kt;           infile.ignore(200,'\n');
        infile >> Gn;           infile.ignore(200,'\n');
        infile >> Gt;           infile.ignore(200,'\n');
        infile >> Mu0;          infile.ignore(200,'\n');
        infile >> Beta;         infile.ignore(200,'\n');
        infile >> Eta;          infile.ignore(200,'\n');
        infile >> dt;           infile.ignore(200,'\n');
        infile >> dtOut;        infile.ignore(200,'\n');
        infile >> rho;          infile.ignore(200,'\n');
        infile >> R;          infile.ignore(200,'\n');
        infile >> appliedVelocity;          infile.ignore(200,'\n');
        infile >> Tf;           infile.ignore(200,'\n');
        infile >> X1;		infile.ignore(200,'\n');
        infile >> Y1;		infile.ignore(200,'\n');
        infile >> Z1;		infile.ignore(200,'\n');
        infile >> X2;		infile.ignore(200,'\n');
        infile >> Y2;		infile.ignore(200,'\n');
        infile >> Z2;		infile.ignore(200,'\n');
        infile >> sphereCoulombMode; infile.ignore(200,'\n');
        infile >> tensileCutoff; infile.ignore(200,'\n');
        infile >> velocityVerlet; infile.ignore(200,'\n');
    }

    // domain and User data
    size_t cl = 0;
    if (contactlaw=="hertz") cl=1;

    DEM::Domain dom(NULL,cl);
    dom.SphereCoulombMode = sphereCoulombMode;
    dom.SphereTensileCutoff = tensileCutoff > 0;
    dom.UseVelocityVerlet = velocityVerlet > 0;
    dom.Alpha=verlet;
    dom.Dilate = true;
    printf("Sphere contact mode: %zu, tensile cutoff: %s, velocity verlet: %s\n",
           dom.SphereCoulombMode, dom.SphereTensileCutoff ? "on" : "off",dom.UseVelocityVerlet ? "on" : "off");
    Vec3_t Xmin(-10,-10,-10);
    Vec3_t Xmax(10,10,10);



    dom.AddSphere(-2,Vec3_t(X1,Y1,Z1),R,rho);
    dom.AddSphere(-3,Vec3_t(X2,Y2,Z2),R,rho);
    
    
    dom.BoundingBox(Xmin,Xmax);



// i dont actually understand how gn works, so if i set positive gn, convert it into coeff of restitution
/*
if (Gn>0){
  printf("Converted Gn: %g",Gn);
  double m = R*R*R * M_PI* (4.0 / 3) * rho;
  double mij = m*m/(m+m);
  double discriminant = 4.0 * mij * Kn - Gn * Gn;
  double exponent = -Gn * M_PI / std::sqrt(discriminant);
  double Gn = std::exp(exponent);

  printf(" into %g\n",Gn);
  	Gn = -Gn;
}

if (Gt>0){
  printf("Converted Gt: %g",Gt);
  double m = R*R*R * M_PI* (4.0 / 3) * rho;
  double mij = m*m/(m+m);
  double discriminant = (8.0/7) * mij * Kt - Gt * Gt;
  double exponent = -Gt * M_PI / std::sqrt(discriminant);
  double Gt = std::exp(exponent);

  printf(" into %g\n",Gt);
  	Gt = -Gt;
}
*/

    for (size_t i=0;i<dom.Particles.Size();i++)
    {
        dom.Particles[i]->Props.Kn    = Kn;
        dom.Particles[i]->Props.Kt    = Kt;
        dom.Particles[i]->Props.Gn    = Gn;
        dom.Particles[i]->Props.Gt    = Gt;
        dom.Particles[i]->Props.Mu    = Mu0;
        dom.Particles[i]->Props.Eta   = Eta;
        dom.Particles[i]->Props.Beta  = Beta;        
    }

    dom.Particles[0]->v(0)=appliedVelocity;


    printf("Start test_2spheres impact..\n");
    dom.Solve (/*tf*/Tf, /*dt*/dt, /*dtOut*/dtOut, NULL, NULL, "test_2spheres",RenderVideo,Nproc);
   
    return 0;
}
MECHSYS_CATCH
