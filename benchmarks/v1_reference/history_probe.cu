// FP64, real VV solves: emit full precision state before/after every force step.
#include <mechsys/dem/domain.h>
#include <cstdio>
#include <cstdlib>

static void vector(char const * name, Vec3_t const & v)
{
    printf(",\"%s\":[%.17g,%.17g,%.17g]",name,v(0),v(1),v(2));
}

static void report(DEM::Domain & d, void *)
{
    printf("VV_HISTORY {\"step\":%zu,\"time\":%.17g,\"records\":%zu",d.iter,d.Time,d.Interactons.Size());
#ifdef USE_CUDA
    real3 ref=d.bVertsoCU[0];
    vector("reference0",Vec3_t(ref.x,ref.y,ref.z));
#else
    vector("reference0",*d.Particles[0]->Vertso[0]);
#endif
    for (size_t i=0;i<d.Particles.Size();i++)
    {
        auto * p=d.Particles[i];
        char key[32];
        snprintf(key,sizeof(key),"x%zu",i); vector(key,p->x);
        snprintf(key,sizeof(key),"v%zu",i); vector(key,p->v);
        snprintf(key,sizeof(key),"w%zu",i); vector(key,p->w);
        snprintf(key,sizeof(key),"F%zu",i); vector(key,p->F);
        snprintf(key,sizeof(key),"host_T%zu",i); vector(key,p->T);
        Vec3_t torque=p->T;
#ifdef USE_CUDA
        // DnLoadDevice does not refresh ParticleCU::T on the host. Read the
        // actual force-kernel torque rather than that stale diagnostic field.
        DEM::ParticleCU device_particle=d.bParticlesCU[i];
        torque=Vec3_t(device_particle.T.x,device_particle.T.y,device_particle.T.z);
#endif
        snprintf(key,sizeof(key),"T%zu",i); vector(key,torque);
        printf(",\"Q%zu\":[%.17g,%.17g,%.17g,%.17g]",i,p->Q(0),p->Q(1),p->Q(2),p->Q(3));
    }
    if (d.Interactons.Size())
    {
        auto * c=static_cast<DEM::CInteractonSphere *>(d.Interactons[0]);
        Vec3_t fr=c->Fdr;
#ifdef USE_CUDA
        DEM::DynInteractonCU h=d.bDynInteractonsVV[0];
        fr=Vec3_t(h.Fr.x,h.Fr.y,h.Fr.z);
#endif
        vector("ft",Vec3_t(c->Kt*c->Fdvv));
        vector("fr",fr);
        vector("host_fr",c->Fdr);
        printf(",\"pair\":[%d,%d],\"contact\":%d,\"overlap\":%.17g,\"Epot\":%.17g,\"dEvis\":%.17g,\"dEfric\":%.17g",
               c->P1->Tag,c->P2->Tag,int(c->InContact),c->PrevDelta,c->Epot,c->dEvis,c->dEfric);
    }
    printf("}\n");
}

int main(int argc,char ** argv) try
{
    // No diagnostic changes to integration, contact law or displacement control.
    int scenario=argc>1?atoi(argv[1]):0;
    double alpha=argc>2?atof(argv[2]):0.001;
    DEM::Domain d;
    d.UseVelocityVerlet=true;
    d.Alpha=alpha;
#ifdef USE_CUDA
    d.CandidateOracle=true;
#endif
    d.AddSphere(-1,Vec3_t(0,0,0),0.1,1.0);
    d.AddSphere(-2,Vec3_t(0.199,0,0),0.1,1.0);
    for(size_t i=0;i<2;i++)
    {
        auto * p=d.Particles[i];
        p->Props.Kn=1000.0;
        p->Props.Kt=20.0;
        p->Props.Gn=0.0;
        p->Props.Gt=0.0;
        p->Props.Mu=0.4;
        p->Props.Beta=0.3;
        p->Props.Eta=0.2;
        p->v=Vec3_t(10.0,i?-0.1:0.1,0);
        p->w=Vec3_t(0,0,i?-1.0:1.0);
        if(scenario==0) p->Ff=Vec3_t(i?-0.75:0.75,0,0);
        if(scenario==1) p->v(1)=i?-5.0:5.0;
        if(scenario==2)
        {
            p->v(0)=10.0+(i?0.3:-0.3);
            p->Ff=Vec3_t(i?-0.2:0.2,0,0);
        }
    }
    printf("VV_HISTORY_MODE velocity_verlet=%d scenario=%d alpha=%.17g\n",int(d.UseVelocityVerlet),scenario,alpha);
    d.Solve(0.01999,2e-5,2e-5,NULL,report,NULL,false,1);
    return 0;
}
MECHSYS_CATCH
