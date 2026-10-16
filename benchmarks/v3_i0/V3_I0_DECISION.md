# V3-I0 decision: PARITY BLOCKED

2026-10-16 Asia/Shanghai, Codex. The observational audit is delivered; this is
**not coupled numerical acceptance**. No Scheme A implementation, coupled VV,
coupled restart, P2-B or performance optimization. Legacy formulas/order and
standalone VV/checkpoint sources are unchanged. Coupled VV remains fail-closed.

## Gate ledger

| Gate | Verdict | Evidence / qualification |
|---|---|---|
| I0-A observational sequence | PARTIAL | CPU/CUDA actual imprint/collision captured; bitwise off/on for 20 non-shared controls. Shared negative strict mismatch stops its equivalence claim |
| I0-B actual increments | PASS, registered alpha=1 | 44,000 cells / 660,000 directions; independent moments/equilibrium/actual writes and all increments, no unsupported limiting claim |
| I0-C linear ledger | PASS, diagnostic scope | Unit single-owner residual <=4.96e-18; nonunit Fconv and shared overwrites independently explain measured negative discrepancies |
| I0-D torque | PASS, fixed-pose exchange | Nonidentity Q, actual body torque and same periodic levers; no full-step angular-conservation claim |
| I0-E coverage/parity | FAIL; acceptance BLOCKED | Centered 27 reference vs CPU 7/GPU 27; small-Alpha lists omit 20 on both; separate proxy control-flow defect measured |
| I0-F shared behavior | PASS diagnostic; support BLOCKED | Nine shared cells, all claimants and actual writes/reactions captured; mixed ownership and strict regression failure preserved |
| I0-G conversion/limiter negatives | PASS within explicit allowed scope | Actual Fconv=2 CPU/CUDA; exact 15-direction synthetic alpha=.5 witness, not production limiting |
| I0-H default-off regression | PARTIAL | 20/20 non-shared comparisons bitwise (off and on); CUDA shared negative strict FAIL, not normalized or fixed |
| I0-I report/next task | PASS | Required reports/CSVs/scripts, preserved failures, bounded correction below |
| I0-J Git delivery | Verification recorded at delivery | Focused commits on origin-only topic; final exact SHA, clean-tree and remote proof in external DELIVERY.json and final response |

## Main measured results

Actual collision decomposition max component 4.955142741437657e-20 M L/T;
independent BGK/solid reconstruction 6.071532165918825e-17, independent population
write 1.6798324538865574e-16 density units. All retain the V3-D FP64 budgets.
Maximum global bound 6.684825336157286e-11 M L/T, normalized 6.684825336157286e-12
of declared problem Jref. BGK and other are explicitly separated, not assigned
as particle reaction.

For the first centered moving sphere: expected Jparticle,x = CPU
-.008353349348328622 / CUDA -.012564025997669036. Legacy reactions pair with
their respective captured solid increments within 4.96e-18 at unit Fconv,
but disagree because they use different occupancy cells. Fconv=2 doubles only
CUDA sphere reaction; negative residual .012564025997669046. Shared CUDA
residual .0008675864358344791 is explained by retained reactions from overwritten
claimants, with remaining attribution residue <=9.44e-19.

Fixed-pose world angular identity max 7.3e-72 in the **70-digit independent
algebra**, not a claimed solver time-integration error. Actual legacy body torque
after accounting for Fconv differs by <=2.929790657836655e-18. Nonidentity Q
rotating controls have nonzero torque; zero wrong observed periodic-image levers.
Fixed sphere support impulse is retained as -Jlegacy; no velocity kick is inferred
from its nonzero reaction.

## Findings that supersede/narrow earlier interpretations

V3-D identified differing CPU/GPU imprint cutoffs as a source hazard. I0 now
measures that discrepancy, **and** establishes an additional shared candidate-
list cutoff: ResetParCell can remove outside-center cells on both backends,
so widening only CPU imprint would not prove completeness. Also the actual
legacy edge loop is not the sum of twelve independent covered edges; early
`continue` skips subsequent edges. All 16 captured nonzero-gamma differences
against that mathematical proxy are independently attributed, not repaired.
Exact-volume intersection remains a different approximation question.

V2's original fast two-sphere residual is preserved as measured then. The I0
fixtures demonstrate mechanisms for their own discrepancies, not a re-run or
complete attribution of that older fixture. Standalone V2 acceptance is neither
weakened nor promoted to coupled acceptance.

## One next bounded task — requires separate authorization

**V3-I0-P1: conservative sphere–cell candidate/imprint coverage parity correction.**
Review and change only the sphere-cell eligibility bounds in ResetParCell and
the CPU outside-center imprint cutoff, with an independent positive-proxy cell
oracle before/after rebuild and periodic crossings. Keep collision/contact laws,
integration, Fconv and shared-cell semantics unchanged. Explicitly retain the
observed legacy proxy control-flow defect as a separate reviewed decision, not
silently bundle an occupancy arithmetic/model change into a cutoff patch.
That defect needs its own correction/review before claiming the mathematical
twelve-edge approximation is correctly implemented.

Scheme A harness is **not ready for a common CPU/GPU positive acceptance gate**
until coverage parity/completeness and the proxy decision are resolved. Shared
positive cells must remain unsupported; a new mixture/owner model is separate.
Production limiter behavior, generalized forcing/multiphase/anisotropic paths,
physical added mass and coupled restart remain outside accepted scope.
Do not start I0-P1, Scheme A or P2-B automatically.

## Provenance and artifacts

Branch `validation/v3-i0-exchange-audit`, base d801c80, preregistration 9f6a5e9,
observer 28e292f, probe/oracle 30a65e1 plus retained shared-regression collector
qualification in the evidence/handoff commit. Origin is marcoprevitali/mechsys;
upstream Axtal/mechsys push disabled. No default-branch merge.

See [README.md](README.md) for exact commands/raw layout,
[PROVENANCE.json](PROVENANCE.json) for source/executable/input/toolchain hashes,
[REGRESSION.json](REGRESSION.json) for strict individual verdicts, required CSVs,
all mismatch IDs/geometry in CELL_MISMATCHES.json, and SHARED_CELL_LEDGER.json.
Large raw archive, index and final delivery proof are outside Git at
`/home/msys/SIMS/mechsys_v3_i0_validation/20261016-v3-i0-exchange-audit/`.
