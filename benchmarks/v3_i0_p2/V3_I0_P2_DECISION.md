# V3-I0-P2 decision — FAIL, hard stop observed

2026-10-16 Asia/Shanghai / Codex. Do not enable or merge the candidate.
Base e0d6c2fcc581b4caf9d020ebbf05f15c2f5a102f; preregistration 88eb5a2.
The source/test failure remains on the default-off experiment branch only.

| Gate | Verdict and evidence |
|---|---|
| P2-A | PASS: sixteen exact original failures reproduced bitwise |
| P2-B | PASS: independent quadratic reference, limiting/invariance/bounds suites; exact rational witness crosscheck |
| P2-C | FAIL: 49/1,254 CPU fixtures miss near-tangent edge beyond frozen tolerance |
| P2-D | FAIL: same 49/1,254 CUDA fixtures; CPU/GPU agreement is not correctness |
| P2-E | NOT_RUN: P2 coupled gamma/B/Omega parity stopped |
| P2-F | NOT_RUN for P2: existing P1 coverage regression independently passes with P2 false |
| P2-G | NOT_RUN for P2: no corrected momentum/torque acceptance |
| P2-H | PASS within existing registered non-shared compatibility scope; standalone VV/checkpoint subset passes |
| P2-I | PARTIAL: intended guards compile; P1 shared guard remains verified; new P2 guards not exercised |
| P2-J | PARTIAL: direct geometric gamma/B changes only; coupled force/torque changes NOT_RUN |
| P2-K | PARTIAL: direct legacy/candidate helpers separately callable; intended coupled mode not validated |
| P2-L | Exact origin-only push/clean clone/archive verification in external DELIVERY.json |

## Smallest counterexample and attribution

Sphere X=(.3,.2,.1), R=1; cube C=(0,0,0), dx=1; lower edge7 from
(-.5,.5,-.5) to (-.5,-.5,-.5). Exact binary64-input rational geometry has
R²-d_perp²=1.110223024625156525...e-17 >0. Independent covered length
6.664001874625056031...e-9. Both candidate helpers return zero. The registered
edge absolute budget is 1e-10*dx, plus the fixed relative term. Exact Fraction
algebra agrees with the separate Decimal quadratic, excluding a reference bug
for this witness. FP64 offset addition/squared-distance rounding changes the
sign (candidate -1.1102230246251565e-16). This is a geometry-rounding failure,
not a candidate-map, collision or conservation failure. All 49 failing fixtures
are this geometry plus its cube symmetries. Preserve 98 failures, no relabeling.

The original sixteen defect cases now have candidate gamma error <=8.48e-17,
but that selected result cannot close the full registered edge gate. CPU/GPU
accepted helper status matches in all registered tests; maximum edge/total
length ordering difference 4.77395900588817e-15 (contraction/order source not
separately isolated), much
smaller than the shared incorrect near-tangent error. Direct legacy helper
outputs remain bitwise unchanged on every registered geometry.

## Quantification and compatible controls

130 affected direct geometry/backend rows above |delta_gamma|>1e-10 (65 each);
maximum .2524839400809597, mean absolute change among affected rows
.0574377785299701. Two rows (one geometry/backend) have legacy gamma=0 and
candidate gamma>0. All registered locations/radii/deltas are in
OCCUPANCY_DIFFERENCES.csv. B deltas there are algebraic tau=.8 calculations,
not actual coupled results. Corrected affected-cell count, Omega/impulse,
hydrodynamic reaction and torque changes are NOT_RUN after the hard stop.

Existing P1 regression: 22 initial configurations/backend; 144 coverage rows,
88,000 cell collisions/1,320,000 directions, zero independent failures. Maximum
linear reaction residual 1.07450629222e-16, population-write error
1.96114685060e-16; these are **P2=false legacy occupancy controls only**.
Forty-six non-shared off/reference state comparisons bitwise; known CUDA
shared strict FAIL preserved, not averaged away. Two P1 shared rejections pass.
Standalone VV cases0/1/9 law0/damping1: six bitwise restarts, three CPU/GPU
comparisons pass; original coupled VV rejection passes both backends.

## Next bounded decision

Review/authorize a robust FP64 near-tangency edge evaluation experiment,
preserving this witness, all registered geometries and frozen budgets. Do not
weaken tolerances, silently clamp tiny positive references to zero, switch to
exact volume, or claim acceptance from selected original cases. Only after
CPU/CUDA helpers pass should P2 coupled parity, coverage, guards, force-change
quantification and independent ledgers resume. Scheme A/coupled restart and
P2-B performance remain untouched. No automatic next implementation.
