# V3-I0-P2R-R decision — observational PASS within bounded scope

2026-10-17 / Codex. **CASE A within the tested CUDA large fixture:** changing
serialization of legitimate FP64 atomic sums explains the first divergence;
no competing correctness defect was found by the source/index/initialization/
ordering audit and supported sanitizer checks. This is not proof of all-path
race freedom, the actual executed atomic permutation, long-time equivalence,
performance or coupled physical accuracy. **P2R remains PARTIAL; P2R-K FAIL.**

| Gate | Result and scope |
|---|---|
|R-A|PASS: four archives/9,944 payloads,3,980 live P2R files and exact executable/header hashes; original strict failure reproduced by parsing archived files|
|R-B|PASS characterization:10 unchanged baseline runs,1/2/3 initial/step1/final numerical hashes; bitwise self-repeatability FAIL|
|R-C|PASS characterization:10 candidate-off runs,1/2/4 hashes; self-repeatability FAIL;45/45/100 all pairs|
|R-D|PASS: first varying snapshot step-0-after_imprint for99 pairs; matched inputs/93 contributions, particleId1/index0, varying F/T sums|
|R-E|PASS: exact binary-rational sums, actual93-addition budgets,180 normal+72 diagnostic sums checked, every observed result has a valid-order witness|
|R-F|PASS assessed scope:8 sanitizer runs,zero reports; source/index/lifetime/stream checks; limitations explicit, not universal global-race proof|
|R-G|PASS: real parsed numerical differences, not output-only; separate file/numeric/particle/history hashes|
|R-H|PASS observed two-step consequences quantified; angular state differs, x/v/fluid/history/lists exact; phase/work caveats retained|
|R-I|PASS proposals: deterministic reference ordering and new derived numerical contract; neither implemented|
|R-J|PASS: preserve old FAIL, no tolerance/code/default/promotion changes; next design decision specified|
|R-K|Exact final commit/origin/clean/full-clone/archive verification in external DELIVERY.json; do not infer delivery from this table|

## First-divergence and numerical consequences

2,090 snapshot comparisons over all190 pairs.99 first differ after step0
imprint,24 after step1 imprint,67 are identical throughout. Complete initial
particle/fluid state, all93 contributions, pair ordering and destination are
identical. First F.x differs by1.3877787807814457e-17 (one ULP); torque differences
reach2.4936649967166602e-18 at this imprint. All actual first sums lie within
gamma_93*sum_abs (gamma_93=1.0325074129014063e-14). Largest absolute deviation
from the exact rounded-input sum4.526544070126981e-17. Cancellation makes some
torque ULP distances enormous; do not describe ALL differences as a few ULPs.

At final state2: maximum force component difference4.336808689942018e-18,
torque4.065758146820642e-18,w5.24199863811339e-22,
wb7.596102962651022e-22,wa4.708208649075264e-22,
Q3.7512640779279805e-22. Position and linear velocity are bitwise identical.
All fluid grid values,93 candidate IDs/order,empty DEM histories and stored
Evis/Efric/Wext are exact across all20 runs at state0/1/2. Sphere rotational
kinetic-energy difference reconstructed with analytic inertia is9.039701079966678e-27
at state2; physical state really does vary, although very slightly.

Exact rational exchange J_particle+J_solid residual<=4.824022041202691e-17;
actual population change plus particle FORCE impulse residual<=5.516420653606247e-16.
Phase-aligned particle HALF-STEP momentum plus fluid-population change has
residual<=1.5456423771899377e-12, identical across runs, dominated by reconstruction
from rounded coordinates. It is not the same identity as exchange balance.
Discrete translational kinetic/work residual<=4.787173422244152e-16, pairwise
variation<=3.446744115758989e-20. The unaligned centered-output energy/work
diagnostic is much larger (~1.53e-4) because legacy state is staggered; it is
explicitly NOT a conservation/acceptance metric. No conserved full LBM+particle
energy or long-time trajectory bound is asserted. Tables retain all values,
including the large unaligned residual, instead of reporting only good-looking
exchange values.

## Required ten answers

1. **Unchanged baseline bitwise self-repeatable? No:** two first-step/three
   final numerical states in10 independent runs.
2. **Candidate-off self-repeatable? No:** two first-step/four final states in10.
3. **Identical individual forces/torques at first divergence? Yes:** all93
   hydrodynamic particle/cell claims bitwise. DEM contact histories are empty,
   not a new nonzero-history validation.
4. **Compatible with legitimate FP64 orders? Yes:** exact-sum bounds and full
   scalar permutation witnesses for all first sums. Actual GPU order untraced;
   each atomic destination can have its own order.
5. **Initialization/invalid-write/sync defect excluded? No defect found within
   executed scope:** all eight tool runs clean and source checks consistent.
   Racecheck cannot exclude arbitrary global races; no universal exclusion.
6. **Only output bits or physical evolution? Real force/torque and subsequent
   angular evolution vary at the quantified small scales.** x/v/fluid/lists
   remain exact over two steps, not over arbitrarily long trajectories.
7. **Strict gate currently achievable reliably? No:** unchanged architecture
   does not even reproduce itself. An occasional equal pair is not a reliable
   gate. Candidate-only determinism cannot match every old atomic baseline.
8. **Determinism scientifically warranted? Useful for a reference/regression
   path, but not shown necessary for physical accuracy or production use.**
   Its cost and scientific requirement need a separate decision.
9. **Independent budgets for a proposed new contract?** Actual-operation
   gamma_n bounds for sums plus unchanged independent collision/exchange
   budgets. Complete phase-aware propagation/final-state budgets still require
   derivation/review; observed maxima and overlapping distributions are not
   acceptance tolerances.
10. **Smallest next milestone?** A separately reviewed, design-only
    compatibility-contract decision and phase-aware propagation budgets;
    alternatively explicitly authorize a default-off deterministic reference
    gather prototype applied to both new controls. Do not start either now.

No production headers or old evidence changed; no deterministic reduction,
Scheme A, occupancy promotion, coupled VV/restart, P2-B or performance campaign.
See COMPATIBILITY_OPTIONS.md for costs, history ownership and limitations.

Fresh-directory offline replay regenerated20 CSV/JSON analysis artifacts with
identical SHA256 values (OFFLINE_REPLAY_VERIFICATION.json). Simulation binaries
were never rebuilt. Tooling commit0e8b0f4 is separate from the evidence/handoff
commit; final full hashes and push/clean proof are in external DELIVERY.json.
