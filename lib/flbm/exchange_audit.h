// V3-I0 observational hooks. Entirely absent unless explicitly compiled in.
// The harness additionally requires MECHSYS_EXCHANGE_AUDIT=1 in its environment.
#ifndef MECHSYS_FLBM_EXCHANGE_AUDIT_H
#define MECHSYS_FLBM_EXCHANGE_AUDIT_H
#ifdef MECHSYS_EXCHANGE_AUDIT
#include <cstddef>
namespace MechSysExchangeAudit {
struct Collision {
    double before, after, neq, omega, gamma, B, rho, tau0, tau, alpha;
    double bgk, solid, other;
};
struct Claim {
    int computed, accepted;
    double gamma, B, omega[27], force[3], torque[3], lever[3], surface[3];
};
inline Collision *cpu_collision = nullptr;
inline Claim *cpu_claim = nullptr;
inline std::size_t collision_capacity = 0, claim_capacity = 0;
inline void (*stage)(void *, const char *) = nullptr;
inline void notify(void *domain, const char *name) { if (stage) stage(domain,name); }
inline void capture(Collision &r, double before, double after, double neq,
                    double omega, double gamma, double B, double rho,
                    double tau0, double tau, double alpha) {
    r.before=before; r.after=after; r.neq=neq; r.omega=omega; r.gamma=gamma;
    r.B=B; r.rho=rho; r.tau0=tau0; r.tau=tau; r.alpha=alpha;
    r.bgk=-alpha*(1.0-B)*neq/tau; r.solid=alpha*B*omega;
    r.other=(after-before)-r.bgk-r.solid;
}
#ifdef USE_CUDA
// Internal linkage for the existing whole-program, single-TU CUDA builds.
static __device__ Collision *gpu_collision = nullptr;
static __device__ Claim *gpu_claim = nullptr;
static __device__ std::size_t gpu_collision_capacity=0, gpu_claim_capacity=0;
static __device__ int gpu_overflow=0;
__device__ inline void capture_device(Collision &r, double before, double after,
                    double neq, double omega, double gamma, double B, double rho,
                    double tau0, double tau, double alpha) {
    r.before=before; r.after=after; r.neq=neq; r.omega=omega; r.gamma=gamma;
    r.B=B; r.rho=rho; r.tau0=tau0; r.tau=tau; r.alpha=alpha;
    r.bgk=-alpha*(1.0-B)*neq/tau; r.solid=alpha*B*omega;
    r.other=(after-before)-r.bgk-r.solid;
}
#endif
}
#endif
#endif
