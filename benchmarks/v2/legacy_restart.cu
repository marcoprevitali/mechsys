// Required R1 negative control: legacy Save/Load is not a full-state restart.
#include <mechsys/dem/domain.h>
#include <stdexcept>
#include <cstdio>

static void configure(DEM::Domain & d)
{
    d.UseVelocityVerlet=true;
    d.Alpha=0.001;
    for(size_t i=0;i<d.Particles.Size();i++)
    {
        auto * p=d.Particles[i];
        p->Props.Kn=1000; p->Props.Kt=20;
        p->Props.Gn=0; p->Props.Gt=0;
        p->Props.Mu=0.4; p->Props.Beta=0.3; p->Props.Eta=0.2;
        p->Ff=Vec3_t(i?-0.75:0.75,0,0);
    }
}
static void create(DEM::Domain & d)
{
    d.AddSphere(-1,Vec3_t(0,0,0),0.1,1);
    d.AddSphere(-2,Vec3_t(0.199,0,0),0.1,1);
    configure(d);
    for(size_t i=0;i<2;i++)
    {
        d.Particles[i]->v=Vec3_t(10,i?-0.1:0.1,0);
        d.Particles[i]->w=Vec3_t(0,0,i?-1:1);
    }
}
static void report(DEM::Domain & d,void *)
{
    if(d.iter<49 || d.iter>51) return;
    auto * c=d.Interactons.Size()?static_cast<DEM::CInteractonSphere *>(d.Interactons[0]):nullptr;
    printf("V2_R1_FORCE step=%zu time=%.17g contacts=%zu normal=%.17g tangential=%.17g rolling=%.17g overlap=%.17g\n",
           d.iter,d.Time,d.Interactons.Size(),c?norm(c->Fnet):0,c?norm(c->Ftnet):0,c?norm(c->Fdr):0,c?c->PrevDelta:0);
}
int main() try
{
    DEM::Domain reference,split;
    create(reference); create(split);
    reference.Solve(50.5*2e-5,2e-5,2e-5,NULL,report,NULL,false,1);
    split.Solve(49.5*2e-5,2e-5,2e-5,NULL,report,NULL,false,1);
    auto * c=static_cast<DEM::CInteractonSphere *>(split.Interactons[0]);
    double before_t=norm(c->Kt*c->Fdvv),before_r=norm(c->Fdr);
    if(before_t<=1e-6 || before_r<=1e-6) throw std::runtime_error("Fixture failed to create nonzero histories");
    printf("V2_R1_BEFORE_SAVE step=%zu tangential=%.17g rolling=%.17g contact=%d overlap=%.17g pair_tags=%d,%d\n",
           split.iter,before_t,before_r,int(c->InContact),c->PrevDelta,c->P1->Tag,c->P2->Tag);
    split.Save("legacy");
    DEM::Domain loaded;
    loaded.Load("legacy");
    double pose_error=0,velocity_error=0,angular_error=0,orientation_error=0;
    for(size_t i=0;i<2;i++)
    {
        pose_error=std::max(pose_error,norm(loaded.Particles[i]->x-split.Particles[i]->x));
        velocity_error=std::max(velocity_error,norm(loaded.Particles[i]->v-split.Particles[i]->v));
        angular_error=std::max(angular_error,norm(loaded.Particles[i]->w-split.Particles[i]->w));
        for(size_t q=0;q<4;q++) orientation_error=std::max(orientation_error,fabs(loaded.Particles[i]->Q(q)-split.Particles[i]->Q(q)));
    }
    printf("V2_R1_AFTER_LOAD records=%zu stored_time=%.17g position_error=%.17g velocity_error=%.17g angular_error=%.17g orientation_error=%.17g\n",
           loaded.PairtoCInt.size(),loaded.Time,pose_error,velocity_error,angular_error,orientation_error);
    if(pose_error||velocity_error||angular_error||orientation_error) throw std::runtime_error("Unexpected particle-state loss in fixture");
    configure(loaded); // Explicitly restore material and forcing omitted by legacy files.
    loaded.Time=split.Time; loaded.iter=split.iter;
    loaded.Solve(loaded.Time+0.5*2e-5,2e-5,2e-5,NULL,report,NULL,false,1);
    auto * r=static_cast<DEM::CInteractonSphere *>(reference.Interactons[0]);
    auto * l=static_cast<DEM::CInteractonSphere *>(loaded.Interactons[0]);
    double history_error=norm(r->Fdvv-l->Fdvv);
    printf("V2_R1_FIRST_RESTART_FORCE history_error=%.17g tangential_force_error=%.17g rolling_error=%.17g normal_force_error=%.17g\n",
           history_error,norm(r->Ftnet-l->Ftnet),norm(r->Fdr-l->Fdr),norm(r->Fnet-l->Fnet));
    if(history_error>1e-10) throw std::runtime_error("Legacy Save/Load loses persistent tangential/rolling histories; not full continuation");
    return 0;
}
MECHSYS_CATCH
