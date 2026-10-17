# V3-I0-P2R-D — targeted derivation, PARTIAL

2026-10-17 / Codex. **No full one-step or two-step numerical compatibility
certificate is claimed. Outcome D4: proof-closure stop.** The discrete phase
contract, host inertia recovery, rounded-input summation theorem and compiled
first-step translation enclosure are established. Rotation/fluid/second-step
intervals are explicitly CONDITIONAL; see DERIVATION_DECISION.md.

P2R-K remains historical **FAIL**. P2R-KN remains **NOT APPROVED / NOT
IMPLEMENTED / NOT RUN**. All production headers, prior tests/evidence,
tolerances, defaults, coupled VV guard and history code are unchanged. No
compiler build, solver timestep, GPU campaign, new accumulation kernel, Scheme
A, P2-B, restart validation or production performance measurement was run.
The separately authorized debugger diagnostic observed host construction in
the unchanged frozen binaries, stopped before Solve, and terminated only its
own inferior processes. It is not a new historical/device snapshot.

## Read and verify

1. STARTUP_PHASE_CONTRACT.md: exact discrete phases, no invented physical labels.
2. FROZEN_STATE_BITS.json and binary_evidence/: input bits and inertia provenance.
3. FP64_OPERATION_GRAPH.md / LOCAL_ARITHMETIC_BOUNDS.md: scope of the proof.
4. ONE_STEP_CERTIFICATE.json / TWO_STEP_CERTIFICATE.json: rational intervals;
   a conditional result is not an accepted production bound.
5. BRANCH_PREDICATE_CERTIFICATE.csv: exact-sign classifications and limits.
6. COLLISION_FEEDBACK_BOUNDS.md / ERROR_BUDGET_ALLOCATION.md: DAG and old budgets.
7. DERIVATION_DECISION.md: gates, remaining proof obligations, next bounded task.

Run from this independent clone (no solver, GPU, compiler or network needed):

```bash
PYTHONDONTWRITEBYTECODE=1 python benchmarks/v3_i0_p2r_derivation/CERTIFICATE_VERIFIER.py
```

This verifies the **partial** artifact arithmetic, not P2R-KN acceptance or full
SASS/source equivalence. Exact rational strings are authoritative; decimal
and hexadecimal endpoint displays are presentation only when endpoints are
not representable. Input binary64 hex strings preserve signed zero.

Full extraction/reproduction commands are in REPRODUCTION.md. Raw partial
attempts, whole embedded PTX, original SASS references and delivery receipts
are archived externally; no frozen R/P2R archive was overwritten. Base
031e5e307a1d3a5001537c58cb791bf31edc6ae5, branch
analysis/v3-i0-p2r-targeted-derivation. PROJECT_STATUS.md is authoritative.
VV remains the program reference; this explicitly authorized LEGACY coupled
fixture is not VV reference evidence.
