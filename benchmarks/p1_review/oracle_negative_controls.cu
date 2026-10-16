// Negative controls for the hardened P1-S oracle. Mutations affect this probe only.
#include <mechsys/dem/domain.h>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <vector>

static void check_cuda(cudaError_t code)
{
    if (code != cudaSuccess) throw std::runtime_error(cudaGetErrorString(code));
}

static void expect_rejection(DEM::Domain & dom, char const * label, size_t step)
{
    bool rejected=false;
    try { dom.OracleCheck(step,0); }
    catch (Fatal * error) { error->Cout(); delete error; rejected=true; }
    printf("REVIEW_NEGATIVE_CONTROL case=%s rejected=%d\n",label,int(rejected));
    if (!rejected) throw std::runtime_error("Oracle accepted a corrupted force list");
}

int main(int argc, char **argv) try
{
    DEM::Domain dom;
    dom.CandidateOracle = false;
    dom.DiagKernelCounters = false;
    dom.ProfileGPURebuild = false;
    dom.PersistentReduction = false;
    dom.Alpha = 0.01;
    dom.AddSphere(-1, Vec3_t(0.0, 0.0, 0.0), 0.1, 1000.0);
    dom.AddSphere(-2, Vec3_t(0.199, 0.0, 0.0), 0.1, 1000.0);
    dom.Solve(1.0e-8, 1.0e-8, 1.0, NULL, NULL, NULL, false, 1);
    if (dom.bDynInteractonsVV.size()!=1 || dom.PairtoCInt.size()!=1)
        throw std::runtime_error("Probe requires exactly one uploaded sphere contact");
    dom.OracleCheck(0,0);
    if (dom.OracleRef != 1 || dom.OracleMissing != 0)
        throw std::runtime_error("Intact probe fixture failed");
    DEM::DynInteractonCU saved = dom.bDynInteractonsVV[0];

    // Host pair survives; its actual GPU force record is absent.
    dom.bDynInteractonsVV.clear();
    dom.demaux.nvvint = 0;
    check_cuda(cudaMemcpy(dom.pdemaux, &dom.demaux, sizeof(DEM::dem_aux), cudaMemcpyHostToDevice));
    size_t previous = dom.OracleMissing;
    if (argc>1 && std::strcmp(argv[1],"--uncaught-missing")==0) dom.OracleCheck(1,0);
    expect_rejection(dom,"missing_gpu_feature",1);
    if (dom.OracleMissing-previous!=1) throw std::runtime_error("Missing GPU feature was not counted");

    // The force record is duplicated; the host map still has a single pair.
    dom.bDynInteractonsVV.push_back(saved);
    dom.bDynInteractonsVV.push_back(saved);
    dom.pDynInteractonsVV = thrust::raw_pointer_cast(dom.bDynInteractonsVV.data());
    dom.demaux.nvvint = 2;
    check_cuda(cudaMemcpy(dom.pdemaux, &dom.demaux, sizeof(DEM::dem_aux), cudaMemcpyHostToDevice));
    previous = dom.OracleDup;
    expect_rejection(dom,"duplicate_gpu_feature",2);
    if (dom.OracleDup-previous!=1) throw std::runtime_error("Duplicate GPU feature was not counted");

    dom.bDynInteractonsVV.resize(1);
    dom.demaux.nvvint=1;
    check_cuda(cudaMemcpy(dom.pdemaux, &dom.demaux, sizeof(DEM::dem_aux), cudaMemcpyHostToDevice));
    // The oracle follows the actual GPU list, regardless of the unrelated host map.
    auto saved_pairs = dom.PairtoCInt;
    dom.PairtoCInt.clear();
    previous = dom.OracleMissing;
    dom.OracleCheck(3,0);
    printf("REVIEW_NEGATIVE_CONTROL case=host_map_independence reported_missing=%zu\n",
           dom.OracleMissing-previous);
    if (dom.OracleMissing!=previous) throw std::runtime_error("Oracle still depends on host pair map");
    dom.PairtoCInt = saved_pairs;

    // The force kernel uses z minimum images; the original oracle enumerates only x/y.
    thrust::host_vector<DEM::DynParticleCU> positions = dom.bDynParticlesCU;
    positions[0].x = make_real3(0.0,0.0,0.05);
    positions[1].x = make_real3(0.0,0.0,0.95);
    dom.bDynParticlesCU = positions;
    dom.demaux.Per = make_real3(0.0,0.0,1.0);
    check_cuda(cudaMemcpy(dom.pdemaux, &dom.demaux, sizeof(DEM::dem_aux), cudaMemcpyHostToDevice));
    real3 branch;
    DEM::BranchVec(positions[1].x, positions[0].x, branch, dom.demaux.Per);
    const bool reference = norm(branch) < 0.2;
    previous = dom.OracleRef;
    dom.OracleCheck(4,0);
    printf("REVIEW_NEGATIVE_CONTROL case=z_periodic actual_reference=%d reported_reference=%zu\n",
           int(reference), dom.OracleRef-previous);
    if (!reference || dom.OracleRef-previous!=1) throw std::runtime_error("Z-periodic fixture failed");

    thrust::host_vector<DEM::InteractonCU> laws = dom.bInteractons;
    laws[0].BothFree=false;
    dom.bInteractons=laws;
    previous=dom.OracleBadImg;
    expect_rejection(dom,"incorrect_pair_periodicity",5);
    if (dom.OracleBadImg-previous!=1) throw std::runtime_error("Wrong periodicity was not counted");
    laws[0].BothFree=true;
    dom.bInteractons=laws;

    // A finite plane must not create a reference contact far outside its footprint.
    DEM::Domain wall;
    wall.CandidateOracle=false;
    wall.AddSphere(-1,Vec3_t(10.0,0.0,0.15),0.1,1000.0);
    wall.AddPlane(-2,Vec3_t(0.0,0.0,0.0),0.1,1.0,1.0,1000.0);
    wall.GetParticle(-2)->FixVeloc();
    wall.Solve(1.0e-8,1.0e-8,1.0,NULL,NULL,NULL,false,1);
    wall.OracleCheck(0,0);
    if (wall.OracleRef!=0) throw std::runtime_error("Oracle uses an infinite plane");
    printf("REVIEW_NEGATIVE_CONTROL case=finite_plane_outside reported_reference=0\n");

    // This must be checked AFTER the VV drift, immediately before force evaluation.
    // Baseline (pre-V1): the end-of-step rebuild is too late; the force-time list is
    // missing the new contact -> the oracle rejects (reproduce with --expect-baseline).
    // Corrected (V1): the pre-force rebuild adds the pair, the force kernel processes
    // it, and action-reaction holds.
    DEM::Domain vv;
    vv.UseVelocityVerlet=true;
    vv.CandidateOracle=true;
    vv.Alpha=0.001;
    vv.AddSphere(-1,Vec3_t(0.0,0.0,0.0),0.1,1000.0);
    vv.AddSphere(-2,Vec3_t(0.24,0.0,0.0),0.1,1000.0);
    vv.Particles[0]->v=Vec3_t(300.0,0.0,0.0);
    vv.Particles[1]->v=Vec3_t(-300.0,0.0,0.0);
    bool expect_baseline = (argc>1 && (std::strcmp(argv[1],"--expect-baseline")==0 ||
                                       std::strcmp(argv[1],"--uncaught-missing")==0));
    bool drift_rejected=false;
    try { vv.Solve(1.0e-4,1.0e-4,1.0,NULL,NULL,NULL,false,1); }
    catch (Fatal * error) { error->Cout(); delete error; drift_rejected=true; }
    printf("REVIEW_NEGATIVE_CONTROL case=vv_force_time_drift rejected=%d missing=%zu\n",
           int(drift_rejected),vv.OracleMissing);
    if (expect_baseline)
    {
        if (!drift_rejected || vv.OracleMissing!=1)
            throw std::runtime_error("Baseline VV force-time defect was not reproduced");
    }
    else
    {
        if (drift_rejected) throw std::runtime_error("Corrected VV path rejected a valid list");
        if (vv.OracleMissing!=0) throw std::runtime_error("Corrected VV path left a missing contact at force time");
        // 1. The contact exists in the uploaded GPU records.
        if (vv.bDynInteractonsVV.size()!=1)
            throw std::runtime_error("Corrected VV path did not upload the new contact record");
        DEM::DynInteractonCU f = vv.bDynInteractonsVV[0];
        // 2./3. The force kernel processed it: nonzero normal force along x (repulsive).
        DEM::DynParticleCU p0 = vv.bDynParticlesCU[0];
        DEM::DynParticleCU p1 = vv.bDynParticlesCU[1];
        printf("REVIEW_VV_FORCE Fn=(%.9g,%.9g,%.9g) F1=(%.9g,%.9g,%.9g) F2=(%.9g,%.9g,%.9g)\n",
               f.Fn.x,f.Fn.y,f.Fn.z,
               p0.F.x,p0.F.y,p0.F.z,
               p1.F.x,p1.F.y,p1.F.z);
        if (fabs(f.Fn.y)>0.0 || fabs(f.Fn.z)>0.0 || !(fabs(f.Fn.x)>0.0))
            throw std::runtime_error("Contact normal force was not evaluated as expected");
        // 4. Action-reaction consistency on the particle force accumulators.
        real3 F1 = p0.F, F2 = p1.F;
        if (!(F1.x<0.0 && F2.x>0.0) ||
            fabs(F1.x+F2.x)>1.0e-12 || fabs(F1.y)>1.0e-12 || fabs(F1.z)>1.0e-12 ||
            fabs(F2.y)>1.0e-12 || fabs(F2.z)>1.0e-12)
            throw std::runtime_error("Action-reaction consistency violated");
    }

    // Independently verify the retained reduction for finite non-negative FP64 inputs.
    size_t cases = 0;
    for (size_t n : {size_t(1),size_t(31),size_t(32),size_t(33),size_t(255),size_t(256),size_t(257),size_t(1025),size_t(8193)})
    for (unsigned threads : {32u,64u,96u,128u,256u,1024u})
    {
        std::vector<real> values(n);
        for (size_t i=0;i<n;i++) values[i] = real((i*7919+17)%104729) * 1.0e-10;
        values[n/2] = (cases%3==0 ? std::numeric_limits<real>::max() :
                       cases%3==1 ? real(1.0e-200) : real(0.125));
        real expected = *std::max_element(values.begin(),values.end());
        thrust::device_vector<real> input(values.begin(),values.end()), result(1,real(0.0));
        DEM::MaxReduceKernel<<<(n+threads-1)/threads,threads>>>(thrust::raw_pointer_cast(input.data()),n,
                                                            thrust::raw_pointer_cast(result.data()));
        check_cuda(cudaGetLastError());
        real observed = result[0];
        if (std::memcmp(&observed,&expected,sizeof(real))) throw std::runtime_error("Reduction mismatch");
        cases++;
    }
    printf("REVIEW_REDUCTION cases=%zu sizeof_real=%zu bitwise_mismatches=0\n",cases,sizeof(real));
    return 0;
}
MECHSYS_CATCH
