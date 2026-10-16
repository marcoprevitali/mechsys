// Actual bounded LBMDEM::Solve runtime; a mode flag is not proof of VV execution.
#include <mechsys/lbmdem/Domain.h>
#include <cstdio>
#include <stdexcept>
static bool fast=false;
static Vec3_t previous_fluid(0,0,0);
static bool previous_valid=false;
static void report(LBMDEM::Domain & d,void *) {
#ifdef USE_CUDA
    if(d.Finished){d.DEMDOM.DnLoadDevice(1,true);d.LBMDOM.DnLoadDevice(1);d.DnLoadDevice(1);}
#endif
    Vec3_t fluid(0,0,0),particle(0,0,0),exchange(0,0,0);double mass=0;
    for(size_t z=0;z<d.LBMDOM.Ndim(2);z++)for(size_t y=0;y<d.LBMDOM.Ndim(1);y++)for(size_t x=0;x<d.LBMDOM.Ndim(0);x++) {
        double rho=d.LBMDOM.Rho[0][x][y][z];double cellmass=rho*d.dx*d.dx*d.dx;
        mass+=cellmass;fluid+=cellmass*d.LBMDOM.Vel[0][x][y][z];
    }
    printf("V2_COUPLED {\"step\":%zu,\"time\":%.17g,\"vv_flag\":%d,\"fluid_mass\":%.17g,\"particles\":[",d.iter,d.Time,int(d.DEMDOM.UseVelocityVerlet),mass);
    for(size_t i=0;i<d.DEMDOM.Particles.Size();i++) {
        if(i)printf(",");auto * p=d.DEMDOM.Particles[i];particle+=p->Props.m*p->v;exchange+=p->Flbm;
        printf("{\"id\":%llu,\"x\":[%.17g,%.17g,%.17g],\"v\":[%.17g,%.17g,%.17g],\"F\":[%.17g,%.17g,%.17g],\"Flbm\":[%.17g,%.17g,%.17g]}",
               (unsigned long long)p->PersistentId,p->x(0),p->x(1),p->x(2),p->v(0),p->v(1),p->v(2),p->F(0),p->F(1),p->F(2),p->Flbm(0),p->Flbm(1),p->Flbm(2));
    }
    Vec3_t residual=previous_valid?Vec3_t(fluid-previous_fluid+d.dt*exchange):Vec3_t(0,0,0);
    printf("],\"particle_momentum\":[%.17g,%.17g,%.17g],\"fluid_momentum\":[%.17g,%.17g,%.17g],\"fluid_force\":[%.17g,%.17g,%.17g],\"exchange_residual_norm\":%.17g}\n",
           particle(0),particle(1),particle(2),fluid(0),fluid(1),fluid(2),exchange(0),exchange(1),exchange(2),norm(residual));
    previous_fluid=fluid;previous_valid=true;
    if(!std::isfinite(mass)||!std::isfinite(norm(particle)))throw std::runtime_error("Coupled runtime produced non-finite state");
}
int main(int argc,char ** argv) try {
    bool vv=argc>1?atoi(argv[1])!=0:true;fast=argc>2?atoi(argv[2])!=0:false;
    LBMDEM::Domain d(D3Q15,0.1,iVec3_t(12,12,12),0.1,1e-4);
    d.DEMDOM.UseVelocityVerlet=vv;d.Alpha=0.001;d.PeriodicX=true;d.PeriodicY=true;d.PeriodicZ=true;
    d.DEMDOM.AddSphere(-1,Vec3_t(0.4,0.6,0.6),0.1,1);
    d.DEMDOM.AddSphere(-2,Vec3_t(fast?0.64:0.599,0.6,0.6),0.1,1);
    for(size_t i=0;i<2;i++) {
        auto * p=d.DEMDOM.Particles[i];p->Props.Kn=1000;p->Props.Kt=20;p->Props.Gn=0;p->Props.Gt=0;
        p->v=Vec3_t(fast?(i?-300:300):0.001,0,0);
        if(!fast)p->Ff=Vec3_t(0.001,0,0);
    }
    for(size_t z=0;z<12;z++)for(size_t y=0;y<12;y++)for(size_t x=0;x<12;x++)d.LBMDOM.Initialize(0,iVec3_t(x,y,z),1,OrthoSys::O);
    d.Solve((fast?0.5:4.5)*d.dt,d.dt,NULL,report,NULL,false,1);
    if(fast) {
        double delta=0.2-norm(d.DEMDOM.Particles[1]->x-d.DEMDOM.Particles[0]->x),normal=0;
        for(auto * c:d.DEMDOM.Interactons)normal+=norm(static_cast<DEM::CInteracton *>(c)->Fnet);
        auto * p=d.DEMDOM.Particles[0];double applied_contact=norm(p->F-p->Ff-p->Flbm);
        printf("V2_COUPLED_CONTACT vv_flag=%d post_step_overlap=%.17g host_reconstructed_normal=%.17g actual_particle_contact=%.17g required_force_at_current_geometry=%.17g\n",int(vv),delta,normal,applied_contact,1000*std::max(0.0,delta));
        if(vv && delta>1e-4 && applied_contact<0.5*1000*delta)throw std::runtime_error("Coupled VV contract FAIL: flag ignored; contact force evaluated before drift, not at current geometry");
    }
    return 0;
}
MECHSYS_CATCH
