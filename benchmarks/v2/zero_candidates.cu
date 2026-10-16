// Explicit full-state continuation with zero contacts AND zero candidate pairs.
#include <mechsys/dem/domain.h>
#include <cstdio>
#include <cstring>
#include <stdexcept>
static void create(DEM::Domain & d) {
    d.UseVelocityVerlet=true;d.Alpha=0.001;
    d.AddSphere(-1,Vec3_t(0,0,0),0.1,1);
    d.Particles[0]->v=Vec3_t(1,0.2,0);d.Particles[0]->Ff=Vec3_t(0.01,0,0);
}
static void solve(DEM::Domain & d,int steps) {
    d.Solve((steps-0.5)*2e-5,2e-5,1,NULL,NULL,NULL,false,1);
    if(d.Interactons.Size() || d.ListPosPairs.Size())throw std::runtime_error("Not a zero-contact/zero-candidate fixture");
}
int main() try {
    DEM::Domain reference,prefix,resumed;create(reference);create(prefix);
    solve(reference,40);reference.SaveCheckpoint("reference.vv.json");
    solve(prefix,20);prefix.SaveCheckpoint("prefix.vv.json");
    resumed.LoadCheckpoint("prefix.vv.json");
    if(resumed.iter!=20 || resumed.Interactons.Size() || resumed.ListPosPairs.Size())throw std::runtime_error("Empty list state was not preserved");
    solve(resumed,40);resumed.SaveCheckpoint("resumed.vv.json");
    auto * a=reference.Particles[0];auto * b=resumed.Particles[0];size_t checked=0;
    auto exact=[&](double x,double y){checked++;if(std::memcmp(&x,&y,sizeof(double)))throw std::runtime_error("Zero-candidate restart not bitwise exact");};
    for(size_t i=0;i<3;i++) {
        exact(a->x(i),b->x(i));exact(a->v(i),b->v(i));exact(a->w(i),b->w(i));exact(a->F(i),b->F(i));exact(a->T(i),b->T(i));
        exact(reference.A[0](i),resumed.A[0](i));exact(reference.Wdot[0](i),resumed.Wdot[0](i));
    }
    for(size_t i=0;i<4;i++)exact(a->Q(i),b->Q(i));exact(reference.Time,resumed.Time);
    if(reference.iter!=resumed.iter || a->PersistentId!=b->PersistentId)throw std::runtime_error("Zero-candidate identity/step mismatch");
    printf("V2_ZERO_CANDIDATES PASS steps=%zu candidates=0 contacts=0 bitwise_scalar_checks=%zu\n",resumed.iter,checked);return 0;
}
MECHSYS_CATCH
