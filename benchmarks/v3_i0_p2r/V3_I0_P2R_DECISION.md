# V3-I0-P2R decision — PARTIAL / strict compatibility FAIL

2026-10-16 Asia/Shanghai / Codex. Robust arithmetic and bounded coupled gates
pass; overall acceptance stopped at K. Retain default-off/unmerged. Historical
P2 remains FAIL and its complete evidence tree is unchanged.

| Gate | Verdict and evidence |
|---|---|
| P2R-A | PASS:83 prior evidence hashes,exact fixtures/reference/budgets unchanged |
| P2R-B | PASS:49 CPU and49 CUDA failures reproduced before implementation |
| P2R-C | PASS within explicit exponent envelope:shared expansion signs/lengths independently checked |
| P2R-D | PASS:1,254 frozen CPU fixtures,15,048 individual edges |
| P2R-E | PASS:same CUDA suite,zero errors above frozen budgets |
| P2R-F | PASS:654 supplemental fixtures/backend,exact rational classifications |
| P2R-G | PASS:individual CPU/CUDA occupancy tests within fixed budgets |
| P2R-H | PASS:23 identical initial coupled cases,gamma/B exact parity,Omega within1.234e-17 |
| P2R-I | PASS registered robust subset:92 imprints,no missing/duplicate/wrong-image cells |
| P2R-J | PASS:92,000 cells/1,380,000 directions,independent linear/body/world exchange budgets |
| P2R-K | FAIL:CUDA large strict default-off mismatch;baseline also non-repeatable;tail controls stopped |
| P2R-L | PASS rejection only:18 negatives before collision;shared/limiter/VV remain unsupported |
| P2R-M | PASS:identical-initial-state occupancy/fluid/particle/world/body torque changes quantified |
| P2R-N | Exact final origin-only SHA/clean/full-clone/archive proof in external DELIVERY.json |

## Validated arithmetic and positive evidence

Original witness positive length6.664001874625056e-9 is recovered. Frozen
max edge error6.204e-16,gamma7.456e-17; stress max normalized error1.781e-16*dx.
Positive returned zero0,false positive0,invalid length/gamma0. Full per-edge
errors,previous49-failure errors,median/p95/relative distributions published.
No reference or tolerance changes; exact-zero Decimal dust explicitly retained.

Shared host/device exact expansions, all FP64, preserve coordinate tails before
squaring. Exact endpoint signs and rationalized partial-chord formula avoid
cancellation. No ordinary fast path or ambiguous sign clamp; exact expansion
unconditional, no separate adaptive fallback/depth. Explicit exponent/output
limitations and initially rejected stress inputs are documented, not hidden.

Coupled legacy integration only:linear exchange residual<=1.594e-16,
body torque discrepancy<=5.008e-18,world fixed-pose angular identity<=1e-71.
These are exchange ledgers, NOT full-step angular conservation, added-mass,
coupled VV or restart acceptance. All production collision alpha=1,unit Fconv.
No changed collision,reaction,contact or integration expressions.

172 affected initial backend/cell rows above|delta_gamma|>1e-10;max change
.216803150761095,affected mean .0548185114431593.32 cells go from legacy0 to
robust positive. Max case-total particle impulse change7.58763084824e-4 and
body torque change2.19753372314e-4. Delta gamma/B/Omega/fluid/particle impulse,
world/body torque and spatial locations recorded. Comparisons use identical
initial particle and incoming fluid states, never independently evolved
trajectories as matched inputs. Evolved states each checked against own oracle.

## Blocking strict-gate evidence and next bounded decision

43/46 non-shared off controls completed:42 bitwise PASS,CUDA large strictFAIL,
three CUDA tail controlsNOT_RUN. Six standalone VV/checkpoint restarts bitwise.
Repeated unchanged baseline also varies:two state1 hashes in three runs;
identical initial per-candidate claims,variable live atomic sums. Maximum first
strict mismatch1.38777878078e-17. No selected-repeat PASS or relaxed tolerance.
Full P1-only regression and representative operation sample remain incomplete
after the stop. Representative2,100 geometries prepared,not measured.

**Next task requires user direction:** separately investigate/default-off
reproducibility and decide whether deterministic accumulation is needed or an
explicitly revised compatibility contract is justified. Do not silently change
K,combine force-ownership/reduction optimization with this arithmetic patch,
enable Scheme A,run performance work,or merge/promote this branch. The numerical
near-tangency defect is remediated in tested scope; milestone closure is not.
