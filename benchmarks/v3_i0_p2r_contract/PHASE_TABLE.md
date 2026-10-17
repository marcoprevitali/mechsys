# Actual legacy phases — no ideal-VV substitution

Audited at587dfbf. Source anchors are relative to this branch's unchanged lib/.
`h=dt`, `t_n=t_0+n*h` labels the outer loop/position/fluid step. These labels
do NOT imply every stored variable is a synchronized physical endpoint value.
`c=Cs=dx/h`, not the lattice sound speed. Raw population velocity has no hidden
half-force correction. Initial scope: canonical spheres,D3Q15/Nl1,Sc0,Gammaf0,
G/Gmix0,BForce0,Fconv1,smooth Bn,alpha1,Gv/Gm0,unit mass-density conversion.

## Discrete state definitions (source-verified)

At entry to loop n, define x_n, xb_n=x_(n-1), q_n, b_n=stored wb,
vS_n=stored v, wS_n=stored w, aB_n=stored wa and f_n=post-stream populations.
At startup xb_0 is a synthetic predecessor, not an evolved sample. For n>=1:

```
vS_n = (x_n-x_(n-2))/(2h)        [rounding omitted in these identities]
wS_n = b_(n-1)+(h/2)*a_(n-1)
b_n  = b_(n-1)+h*a_(n-1)
aB_n = a_(n-1)
```

Thus vS_n is the central-difference velocity at t_(n-1), not t_n. Define the
position-derived half-step velocities vMinus_n=(x_n-xb_n)/h and
vPlus_n=(x_(n+1)-x_n)/h; nominal times t_(n-1/2),t_(n+1/2) follow the coordinate
stencil. They are not the standalone `v_half` cache, which this solver does not
advance. Rotational b_n is an algorithmic accumulator, not automatically a
physical omega(t_n) or omega(t_(n-1/2)); wS is its arithmetic midpoint over the
previous update. Compare these exact stage definitions, not guessed time tags.

### Startup caveat — an explicit unresolved physical interpretation

dem/domain.h:545-554 calls Particle::InitializeVelocity; particle.h:682-690
sets xb=x-h*v_seed and wb=w_seed, with no acceleration-based half-step shift.
Initial A/Wdot caches are zeroed in lbmdem/Domain.h:828-832 for safe upload, not
used to bootstrap coupled VV. Source specifies bits/recurrences but does not
specify whether the supplied velocities are intended endpoint or staggered data.

An algebraic constant-force example (NOT an executed test) gives
x_1=x_0+h*v_seed+h^2*a and vS_1=v_seed+h*a/2. If v_seed were an exact physical
v(t0), x(h) would instead contain h^2*a/2. This deterministic initialization/
discretization distinction is not FP64 uncertainty and cannot be added to a
roundoff allowance. The phase convention for scientific initial-value balances
needs explicit review. We do NOT change initialization or assert a new physical
accuracy result. Discrete-map compatibility can still be derived separately.

## Stage table (no rebuild or user callback mutation in the base fixture)

| Stage | Position/orientation | Stored linear/angular quantities | Force/torque phase | Fluid populations/momentum |
|---|---|---|---|---|
| reported state-n, before reset | x_n,xb_n,q_n | vS_n,wS_n,b_n,aB_n; startup exception at n0 | previous step F/T/Flbm for n>=1; CPU imprint startup values at n0 | f_n and raw moments at t_n; f scratch is role-specific |
| before imprint, after reset/contact | x_n,xb_n,q_n | unchanged vS_n,wS_n,b_n | Ff+contact_n,Tf+contact_n; Flbmf diagnostic seed; histories have advanced once at entry geometry | f_n,rho_n,uRaw_n; Gamma reset, no collision yet |
| after imprint | same geometry/velocities | unchanged | F_n=Fext+Fcontact_n+Fhydro_n, T_n body, Flbm diagnostic; reaction evaluated at entry pose and stored lagging velocities | f_n unchanged; Gamma_n/Omega_n cached from entry state |
| after Translate/Rotate | x_(n+1),xb=x_n,q_(n+1) | vS_(n+1) central at t_n; a_n,b_(n+1),wS_(n+1) from recurrence | F_n/T_n unchanged, no new endpoint evaluation | still f_n,old rho/u; Gamma/Omega still entry-pose caches |
| before collision | same integrated particle state | same | same F_n/T_n | incoming f_n, entry-derived Gamma/Omega; not recomputed at x_(n+1) |
| after collision | same integrated particle state | same | same | Ftemp=f*_n; F still f_n at observer; moments still incoming; do not call f* post-stream |
| after streaming/moment refresh | same particle state | same | same F_n/T_n | swaps then periodic stream -> f_(n+1); rho/u refreshed, BForce/Omega cleared for fluid cells |
| final/report state-(n+1) | x_(n+1),q_(n+1) | lagging vS/wS with updated wb/wa | still last F_n/T_n, not F_(n+1) | f_(n+1), raw moments; Gamma can still label preceding imprint |

## Exact source maps to audit

- lbmdem/Domain.h:989-1011 reset, contacts, imprint;1022-1045 integration,
  MaxD/optional rebuild;1057-1090 collision, pointer swaps, stream/moment refresh;
 1183-1198 outer clocks/final download/report. dem/dem.cuh:969-1066 equations.
- cudaImprintLatticeVC reads x_n,q_n,vS_n,wS_n,f_n,rho_n; converts body w through
  q_n to world surface velocity. T is accumulated in the conjugate-q_n body
  frame. Translate does not consume Flbm a second time. wa is angular
  acceleration; A/Wdot are unused standalone caches, not its aliases.
- Device DEM clock advances in MaxD; device LBM clock in cudaStream2; outer and
  host auxiliary copies advance at their own source locations. CPU host clock
  behavior differs. Exact expected clocks are backend/stage-specific, not all
  equal. A callback reading host state before report download may see old data;
  arbitrary callbacks are excluded from the first prospective comparison.
- A rebuild after integration may wrap coordinates/reassign reference/list
  storage without a second force evaluation. There is no rebuild in CUDA large.
  Extension must retain continuous image-unwrapped geometry, histories and
  pre-collision cache provenance. Do not label wrapped xb or Gamma by guess.

## Which balances use which state?

Exchange: entry x_n,q_n,image lever, cached Omega_n, actual collision increments
and the actual hydro accumulator increment (subtract its seed/other forces).
Translation: h*F_n against m*(vPlus_n-vMinus_n), with coordinate/arithmetic
rounding tracked. Discrete work: F_n·(x_(n+1)-xb_n)/2 equals the change in the two
half-step translational kinetic energies in exact arithmetic. NOT a balance of
the lagging reported v values. Rotation uses the actual b/wS/wa and q maps;
fixed-pose torque exchange is not full-step world angular conservation.
An isothermal dissipative LBM has no assumed conserved total mechanical energy.
The prior unaligned centered-output energy residual is EXCLUDED as a gate.
