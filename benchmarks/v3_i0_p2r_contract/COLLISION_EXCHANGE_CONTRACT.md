# Independent collision/exchange — existing budgets are NOT enlarged

P2R-KN is unapproved. Existing V3-I0/P1/P2R independent collision/exchange
scripts, reference routing, inputs, tolerances and failures remain unchanged.
Authoritative arithmetic: ../v3_i0/analyze.py:74-77,135-191; robust routing in
../v3_i0_p2r/coupled_analyze.py. Do not substitute a new permissive ledger.
First proposed numerical scope is the original unit dx=h=1,D3Q15/Nl1,Sc0,
smooth Bn,Gammaf/BForce/G/Gmix0,Fconv1,alpha1,single geometric owner,canonical
spheres. Physical h/dx formulas below explain units, not authorize new scales.

## Separate the four errors

For each cell/direction record its actual incoming f_k, actual written f*_k,
rho/raw velocity, gamma,Omega,B,effective tau and ACTUAL alpha. From these:

```
dActual_k = f*_k-f_k
dSolid_k  = alpha_k*B*Omega_k
dBGK_k    = -alpha_k*(1-B)*(f_k-Feq_k)/tau
dOther_k  = dActual_k-dBGK_k-dSolid_k.
```

Calculate rho=sum(f), uRaw=Cs*sum(f*e)/rho, Feq,B and surface Omega independently
from binary64 inputs, using the registered independent high-precision oracle.
Capturing production `solid` is necessary to track actual writes, but comparing
only two production-derived expressions is not an independent collision oracle.
Verify directionwise increments, full population write and their impulse sums;
also check actual before/Omega inputs match the named collision phase.

| Error | Reference/comparison | Allowance source |
|---|---|---|
|collision population|actual f* versus independently reconstructed collision|unchanged per-cell b_c and original direction checks|
|fluid impulse|sum of ACTUAL changes, separately BGK/solid/other, versus independent impulse|same frozen collision/impulse ledger, not a force-sum allowance|
|particle accumulation|actual live hydro increment versus exact sum of captured rounded contributions|E_sum for its own graph/seed; matched-input contribution checks separate|
|fluid-particle exchange|actual hydro increment versus independent negative solid impulse|unchanged registered particle/global budget; ALL other checks also mandatory|

No lost/duplicate contribution or wrong cell owner may pass any of these
checks merely because its contribution is zero or small.

## Units, phase and torque

For dimensionless directions e_k, c=Cs=dx/h and density populations:

```
JFluid,c = dx^3*c * sum_k dSolid_ck*e_k
FParticle,c = -Fconv*c^2*dx^2 * sum_k B_c*Omega_ck*e_k
h*FParticle,c = -JFluid,c              [Fconv1,alpha1,h*c=dx].
```

Use the actual hydro INCREMENT, subtracting Flbmf or other accumulator seeds.
F already includes hydro; never add Flbm twice. Nonunit Fconv is a known
conversion defect/unsupported configuration, not a rounding allowance.
Actual limiter activity breaks this preregistered reaction identity and must
reject until separately modeled, even when the eventual residual happens to
be small. CPU/GPU inconsistencies are not silently averaged away.

Let r_c=XCellImage_c-x_n use the exact registered periodic-image convention,
and q_n the entry pose. World KParticle_c=r_c cross (-JFluid,c),
body K=R_conjugate(q_n)(KWorld). Compare actual h*T hydro increment against
independent body K with the existing frame/arithmetic budget. The fixed-pose
identity `(x_n+r_c) cross JFluid + x_n cross JParticle + KParticle = 0`
is a separate geometric check. It is NOT conservation of the integrated
particle+fluid world angular momentum after q/position change. Stored q is
not exactly unit in real arithmetic; account for its actual helper's products,
do not secretly normalize it or use a changed torque frame.

## Freeze numerical budgets, do not double spend them

At the original unit configuration the registered per-cell scale is

```
eps=2^-52; Jref=.01
S_c = sum_k (|f_k|+|f*_k|+|dBGK_k|+|dSolid_k|+|dOther_k|)*||e_k||_1
b_c = 128*eps*S_c + 1e-12*Jref.
```

Keep its exact existing formulas/interpretations and per-particle/global
aggregates: the legacy scripts use their registered gamma_(15*N)(eps) terms,
world-lever factors and separate angular check. Those frozen historical
aggregates are not retroactively rewritten as the new gamma93(u) theorem.
eps and u differ by factor2. Existing geometry/P2R edge budgets also remain
unchanged; independent legacy-control-flow compatibility is not mathematical
twelve-edge correctness. Robust-on configured geometry is tested against its
own frozen reference, not expected to equal the intentionally defective legacy.

For the NEW prospective contract:

1. Run every frozen independent check under its existing budget, unchanged.
2. In parallel, require an exact-rounded-term accumulation check under E_sum.
3. Keep the final actual exchange check under B_old, NOT B_old+E_sum. If a
   proposed arithmetic proof needs formation+sum+reference terms, trace each
   error source ONCE and show their enclosure fits B_old. Otherwise that scope
   is UNRESOLVED; do not enlarge B_old or count a local b_c again at each edge.
4. Multiple tests against the same b_c are conjunctive diagnostics, not unused
   budget coupons to add. Correlated input errors/shared Omega are the same
   graph node. If two valid bounds constrain the same residual, both apply;
   their sum is not a newly authorized tolerance.

The present document freezes these constraints; a complete nonduplicated proof
allocation for the evolved-state path is still required. No derived allowance
may hide the historical missing-cell/shared-owner/Fconv defects. Unsupported
geometry and shared cells remain explicit failures/rejections, not KN support.
