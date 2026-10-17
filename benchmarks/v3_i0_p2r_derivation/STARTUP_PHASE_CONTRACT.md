# Algorithmic startup and phase contract

## Initial-state meaning

The supplied v_seed is an **algorithmic seed velocity** for this contract.
Its continuous-time physical meaning is **PHYSICAL_STARTUP_UNRESOLVED**.
No physical endpoint, half-step or acceleration-corrected interpretation is
invented. That question remains a separate physical-accuracy/convergence gate;
it does not prevent comparison of the exact registered discrete initial state.

`Particle::InitializeVelocity`, particle.h:682-690, assigns
xb=RN(x-h*v_seed), wb=w_seed, v_half=v_seed, w_half=w_seed. There is no
acceleration-based bootstrap. Coupled Solve does not advance the half caches
as VV states. The constructor's VV default is unchanged and this fixture
explicitly selected legacy integration.

The registered x0=(5,5,5), h=1,
v_seed=(.002,-.001,.0005), xb0=(4.9980000000000002,
5.0010000000000003,4.9995000000000003), w0=wb0=wa0=0.
Actual Q0=(0.70710678118654757,0.70710678118654757,0,0), scalar first.
Its exact real squared norm is
40564819207303346393761349247529/40564819207303340847894502572032,
**not 1**. Exact bits, mass, principal inertia and all populations are in
FROZEN_STATE_BITS.json. State-0's CPU startup-imprint F/T are not the first
GPU force consumed by Translate: reset occurs first and the 93 GPU terms are
then accumulated from exact zero.

## Source equations and stages

Let n denote the outer position/fluid loop, not an asserted synchronized
physical time for every field. x_(−1) is the synthetic predecessor xb0.
With rounding suppressed only in the following algebra:

```text
x_(n+1) = 2*x_n - xb_n + h²*F_n/m
vS_(n+1) = (x_(n+1)-xb_n)/(2h); xb_(n+1) = x_n
a_j = [T_j + (I_k-I_l)*b_k*b_l]/I_j
wS_(n+1) = b_n + h*a/2; b_(n+1) = b_n+h*a; wa_(n+1)=a
qM = q_n + h*H(q_n,wS_(n+1))/4
qD = qM + h*H(qM,b_(n+1))/4
q_(n+1) = qD / norm(qD)
```

H(q,w)=q*(0,w), in that order. This is not an exponential rotation or ideal
Velocity-Verlet. The machine graph retains all intermediate RN/FMA operations.
Inertia is actually isotropic in the host observation and exact constructor
replay, so I_k-I_l is exact zero, not a numerically estimated small gyro term.

| Stage | Particle fields | Force and fluid roles |
|---|---|---|
|state-0/start|exact x0,synthetic xb0,v_seed,Q0,zero angular seed|CPU startup imprint forces; f0,rho0=1,u0=0|
|loop n entry/report|x_n,xb_n,q_n,vS_n,wS_n,b_n,wa_n|previous F/T; post-stream f_n and moments|
|after reset,before imprint|same particle state|F/Flbm/T zero here; Gamma reset; zero DEM contacts/histories|
|after imprint|same entry state|F_n/T_n; entry Gamma_n/Omega_n cached; f_n unchanged|
|after translation/rotation|x_(n+1),xb=x_n,new q,b,wa; vS/wS lag geometry|F_n/T_n retained; still f_n and entry caches|
|collision|particle pose already advanced but unused by collision|fStar_n from f_n/rho_n/u_n and cached Gamma_n/Omega_n|
|stream/moments|same advanced particle state|periodic population permutation; f_(n+1),rho_(n+1),u_(n+1)|
|state-(n+1)|advanced geometry and fluid; old centered vS and algorithmic b/wS|last F_n/T_n, not a new endpoint force|

For n>=1, vS_n=(x_n-x_(n−2))/(2h) is centered at the preceding position
level. b=wb is an algorithmic angular accumulator; wS is its last arithmetic
midpoint. No common physical time for those angular fields is source-proven.
Host/device DEM/LBM clocks have distinct source update locations; their
captured bits remain in the manifest, not relabeled to force equality.

## Valid versus unsupported identities

For the exact real discrete recurrence, define vMinus=(x_n-xb_n)/h and
vPlus=(x_(n+1)-x_n)/h. Then m*(vPlus-vMinus)=h*F_n and
Delta K_half=F_n dot (x_(n+1)-xb_n)/2. Coordinate rounding is a separate
residual, not another force-sum allowance. These are not identities for the
lagging reported vS or unused v_half cache.

For constant acceleration and ignoring rounding, the startup gives
x1=x0+h*v_seed+h²*a. If v_seed were a physical endpoint velocity, the usual
continuous IVP solution has h²*a/2. This is a deterministic discretization
difference, never FP64 uncertainty. No full mechanical-energy conservation
of isothermal dissipative LBM, full-step world-angular conservation, coupled
VV accuracy, restart equivalence or long-time stability is established.

Source anchors: lbmdem/Domain.h:780,828-832,989-1090,1183-1198;
dem/dem.cuh:963-1066; particle.h:682-690; first phase design remains unchanged
at ../v3_i0_p2r_contract/PHASE_TABLE.md.
