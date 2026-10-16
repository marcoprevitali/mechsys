# V3-I0-P1 decision: PASS within registered experimental sphere subset

2026-10-16 Asia/Shanghai, Codex. Retain default-off ConservativeSphereCells;
no merge/default promotion. Exact starting commit
38da1b918281883fdc5fb46ea8171082993a1136. Implementation 2b2cc38 (full SHA in
PROVENANCE.json), branch fix/v3-i0-p1-cell-coverage, origin user fork only.

| Gate | Verdict / evidence |
|---|---|
| P1-A | PASS: old centered CPU 7/CUDA 27 and small-skin omissions reproduced |
| P1-B | PASS: R+sqrt(3)dx/2+Alpha bound derived, independent geometry and entry motion checks |
| P1-C | PASS: zero geometric/math/legacy-positive candidate omissions on registered entries |
| P1-D | PASS: zero legacy-positive CPU imprint omissions |
| P1-E | PASS: 22 identical initial single-owner configurations, accepted sets identical |
| P1-F | PASS: gamma/B/Omega and individual solid increments within unchanged FP64 gates |
| P1-G | PASS: independent collision/linear/body/world torque ledgers |
| P1-H | PASS within previous non-shared scope: 46 strict off/reference controls; shared FAIL preserved |
| P1-I | PASS rejection only: shared geometry blocked explicitly, no positive support claim |
| P1-J | PASS: occupancy helpers/control-flow defect source unchanged and separately documented |
| P1-K | Final Git verification in external DELIVERY.json / final response |

88,000 cell collisions / 1,320,000 direction records; no unexpected independent
failures. Maximum decomposition 4.086933970502e-20 M L/T, independent BGK/solid
impulse error 8.23993651089e-17, population-write error 1.96114685060e-16.
Unit-Fconv particle/solid exchange residual <=1.07450629222e-16.
Actual body-torque mismatch <=9.62171177362e-18; fixed-pose angular identity
<=9e-72 in 70-digit reference algebra, not full-step angular conservation.
Initial CPU/GPU gamma/B/Omega/solid-increment maximum differences respectively
2.22044604925e-16 / 2.15357303247e-16 / 1.23361878439e-17 / 6.07153216592e-18.
V3-D budgets and V3-I0 FP64 tolerances are unchanged. No wrong periodic levers.

This supersedes the V3-I0 eligibility BLOCKER for this opt-in registered subset,
not its historical failure verdict. Shared geometry stays blocked (guard can
reject even zero-proxy shared cells); corrected noncanonical/polyhedral mode,
mutable radius/periodic conventions, production limiting and broader models
are unsupported/unvalidated. Full-grid scan and synchronous opt-in validation
have no performance acceptance. VV reference policy/compatibility defaults and
the coupled VV guard are unchanged; Scheme A, restart and P2-B not implemented.

**One next bounded milestone:** separately review/correct the SphereCube edge-
group early-continue defect with independent twelve-edge reference and default-
off regression. Do not automatically start it or Scheme A. Passing eligibility
does not establish correctness of the mathematical occupancy approximation.

Artifacts: README/GEOMETRIC_BOUND/CANDIDATE_COMPLETENESS/PERIODIC_TESTS,
CPU_GPU_PARITY.csv, IMPULSE_REGRESSION.csv, torque and strict legacy results,
PROVENANCE.json. Raw archive/verification and exact final published SHA/clean
receipt: /home/msys/SIMS/mechsys_v3_i0_p1_validation/20261016-coverage/.
Previous clones and original checkout are read only and preserved.
