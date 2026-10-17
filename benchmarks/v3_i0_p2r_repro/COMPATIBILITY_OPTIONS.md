# Compatibility options — proposals ONLY

P2R-K FAIL is immutable historical evidence. Neither option below changes that
gate or accepts P2R. Both require a separately reviewed work order before code
or acceptance criteria change. No option is implemented in this branch.

## A. A reproducible reference execution path

Prototype a default-off diagnostic/reference path that writes each existing
particle/cell contribution once, in stable (physical particle ID,periodic image,
cell ID) order, then gathers per particle in a fixed arithmetic order. A serial
per-particle gather is the smallest correctness prototype; a later fixed tree
or segmented scheme is a different numerical ordering requiring new evidence.
Preserve initial Ff/Flbmf/Tf and the existing force/collision/integration sequence.
The existing history owner must still advance each physical DEM contact once;
do not duplicate friction/rolling computations. This fixture has no DEM contact
history and cannot certify a general DEM deterministic-force design.

Storage lower bound is6 FP64 numbers per particle/cell contributor (force and
body torque),48*M bytes;4,464 bytes for93 contributors, plus keys, CSR offsets,
sorting/index buffers and allocation overhead. Keep F and Flbm accumulator
semantics distinct even when they happen to be equal here. The extra write,
read and launch/gather are real overhead; contention reduction may offset some
cost. Nothing has been measured, and no performance improvement is claimed.
Stable key construction/order must be preserved across rebuilds/restarts.

A same-binary/same-GPU/configuration bitwise guarantee is plausible only after
all contributing operations/inputs are also reproducible. A fixed final
reduction does not make different CPU/GPU transcendental/FMA/compiler behavior
bitwise equal. The reproducibility scope must explicitly pin compiler,
architecture, flags and reduction topology; cross-backend validation still
needs independent physical/numerical oracles.

IMPORTANT: changing only the candidate to a fixed order cannot guarantee that
it matches an arbitrary old atomic-order baseline. A NEW deterministic
baseline and candidate control would both need the same reviewed path; the old
P2R-K remains FAIL. Strict compatibility is not restored by choosing one old
run that happens to match. Determinism is useful for regression/reference and
debugging; this audit does not establish it is necessary for scientific
accuracy or warrants mandatory production overhead.

## B. A new, explicitly numerical default-off contract

This is a design proposal, NOT a tolerance waiver:

1. Exact immutable source/input/initial-state checks and unchanged deterministic
   fields. Require candidate/cell IDs, image codes, ownership, multiplicities,
   contact-history updates and candidate order to match the registered contract.
2. For matched input states, compare individually computed contributions and
   the independently validated geometry/collision ledger. Do not excuse a
   contribution change as merely an accumulation change. The present first
   imprint is bitwise at this level.
3. Derive each scalar summation budget from its actual arithmetic graph,
   initializer, term count and magnitudes. For93 native sequential FP64 RN
   atomic additions of identical precomputed terms starting at0:
   E=gamma_93*sum(abs(term)),u=2^-53. Two such valid sums differ by at most
   E_A+E_B (2E for identical inputs). This is not a universal ULP threshold.
   Formation error, nonzero initial state, partial trees and FMA paths must be
   accounted separately. Use absolute budgets under severe cancellation.
4. Keep the existing independent V3-D collision/exchange budgets unchanged:
   per-cell scale-dependent128*eps*S+1e-12*Jref (eps=2^-52,Jref=.01), with
   documented accumulation propagation. This audit's exact rational exchange
   sums are an additional check, not permission to enlarge those budgets.
5. Register separate, derived propagation budgets for the actual legacy
   translation/rotation and subsequent fluid populations, including coordinate
   subtraction, inertia/quaternion formation and collision rounding. A bound
   on first-step force alone does NOT bound the trajectory. Matched-input
   stepwise/shadow checks may isolate regressions but do not by themselves
   validate the independently evolved full solve.
6. Define phase-consistent physical balances before interpreting residuals.
   An isothermal dissipative LBM does not supply an automatically conserved
   total mechanical energy. Legacy output v is staggered; use the appropriate
   particle/fluid phase. Nonzero histories/rebuilds/contact transitions require
   their own tests. No current final-step or long-time tolerance is justified
   by merely taking the maximum seen here.

The numerical evidence here justifies the summation component of a possible
NEW contract, not the entire evolved-state acceptance gate. Statistical overlap,
the67 exact pair matches and small absolute mismatch are not substitutes for
its derivation or review. Existing geometry tolerances, failed shared-cell
case, nonunit Fconv limitation, coupled VV/restart and old P2 failure remain.

## Recommendation and smallest next milestone

Prefer a small **design-only compatibility decision** first: freeze the scope
of exact/structural checks and derive phase-aware one/two-step propagation and
balance budgets, then choose B or authorize A's reference-only gather prototype.
That decision is smaller than a production deterministic-accumulation rewrite
and prevents accidentally redefining old K. If strict same-configuration
bitwise regression is a scientific requirement, choose A explicitly and apply
the reference ordering to both new controls. Otherwise review B's complete
budgets before rerunning/promoting P2R. Neither path is pre-authorized here.
