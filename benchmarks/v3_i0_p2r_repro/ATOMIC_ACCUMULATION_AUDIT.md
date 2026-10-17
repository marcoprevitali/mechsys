# Atomic accumulation and first divergence

All locations below are candidate source at base26bf84a/implementation1bde930;
baseline locations differ by the documented P2R additions. No source edited.

## First divergent operation

Particle PersistentId=1, storage index0. Initial state-0 and
step-0-before_imprint are bitwise equal in every run. Before imprint,
F/Flbm/T are exactly +0. There are93 unique (cell,index0) records in identical
order, each computed/accepted once. Candidate array indices0..92 identify
threads; full cell/physical-ID/force/torque bits are in CONTRIBUTION_BITS.csv.
These are hydrodynamic particle/cell contributions, NOT DEM pair contacts.
There are zero DEM contacts/history records; no contact transition is tested.

The templated `cudaImprintLatticeVC` at lib/lbmdem/lbmdem.cuh:596 computes
one contribution/thread; lines673-677 capture its binary64 force/body torque,
then lines680-688 perform nine atomicAdd operations:

| Destinations | Index | Precision | Contributions/component |
|---|---|---|---|
| DPar[ip].F.{x,y,z} | ip=PaCeV[2*ic+1]=0 | FP64 |93|
| DPar[ip].Flbm.{x,y,z} | same | FP64 |93|
| Par[ip].T.{x,y,z} | same | FP64 |93|

Launch Domain.h:1008 is one256-thread block,93 active threads spanning three
warps; other threads return before indexed access. The FC launch at1009 has
nfc=0 and returns. Source candidate list order is stable, but does not prescribe
atomic serialization. Different components/addresses need not share an order.

Last identical stage for99/190 pairs: step-0-before_imprint. First different:
step-0-after_imprint, initially F.x (-.11674452090273846 versus
-.11674452090273847) with other force/torque components. All93 complete claim
records remain bitwise equal. Translate/Rotate follow at Domain.h:1022-1023;
angular velocity/acceleration and quaternion differ at before_collision.
Another24 pairs first differ at step-1-after_imprint;67 pairs are equal through
the final snapshot. No mismatching pair is removed from the result.

At step1 there are two complete-input cohorts and two contribution cohorts,
caused by the preceding angular-state differences. All380 step/pair cohort
checks find identical contributions for identical complete inputs. Later
different claims are not incorrectly called arithmetic regressions.

## Executable evidence and competing writers

Both exact executables were disassembled with CUDA12.6 cuobjdump, no rebuild.
In the templated VC symbol the corresponding nine instructions are
`RED.E.ADD.F64.RN.STRONG.GPU`. Baseline addresses e980..ea00 (SASS lines7484..7500),
candidate1e720..1e7a0 (15600..15616). Scalar accumulator offsets are
F90/98/a0,Flbma8/b0/b8,T70/78/80. Captured contributions and atomic operands
come from the same local FP64 values, not a separately recomputed host formula.
The added branch changes binary size/instruction schedule; it does not change
the observed matched-input contributions. No identical binary claim is made.

DEM::Reset dem.cuh:1069-1080 initializes F/Flbm/T non-atomically in a preceding
kernel, one thread/particle. Domain.h:991-996 launches reset then DEM force
kernels, all on the default stream; all four contact-family counts are zero
here. DEM VV/Hertz (dem.cuh:285-296/463-474), EE610-621,VF692-703 and
FV775-786 normally update particle forces/torques atomically, but contribute
no writes in this fixture. They are not given general race/history acceptance.
Legacy non-templated VC (lbmdem.cuh:414-422) is not the selected overload;
polyhedral FC778-786 is inactive. BForce pair atomics822-827/855-860/888-922
are inactive because fluid G/Gmix=0. Diagnostic integer counters do not alias
particle force storage. There are no mixed simultaneous ordinary/atomic writes
to the nine relevant scalars in the tested VC path.

Default-stream launch ordering and diagnostic cudaDeviceSynchronize at each
callback establish reset -> claim/atomics -> snapshot -> integration ordering.
No production synchronization, buffer lifetime or compiler flag was changed.

## Independent sum and interpretation

Each component starts from exact0 and undergoes93 scalar rounded additions.
All terms and sums are finite, normal-or-zero FP64. SASS confirms ordinary
FP64 RN atomic adds, not FMA or a different partial-reduction tree. Exact
Fraction sums preserve every input binary64 bit. With u=2^-53 and n=93,
gamma_n=1.0325074129014063e-14; gamma_n*sum_abs bounds the rounding of already
computed contributions. Including the exact first zero-add makes this
conservative; contribution-formation error is explicitly NOT included.

All180 normal-run/component sums satisfy that bound. Largest absolute error
from exact sum4.526544070126981e-17. All72 sanitizer-run/component sums are
checked separately too. First force component bounds are1.2053958324770065e-15,
6.02697916238488e-16,3.0134895811924437e-16; torque bounds are separately derived
from their own sum_abs. Near-cancelling T.y has a small absolute sum, so large
ULP/relative differences there do not mean large physical torque error.
INDEPENDENT_SUMS.csv marks ill-conditioned relative errors NOT_MEANINGFUL.

Seeded offline permutations reproduce every observed first-step scalar sum
exactly (normal AND sanitizer); complete witness orders are retained. They
establish legitimate-order compatibility, NOT the actual GPU order. Source,
native instructions, identical complete inputs/contributions, changing only
accumulated sums and the scoped safety audit together support CASE A within
this fixture. They are not a universal exclusion of all possible defects.
