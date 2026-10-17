# V3-I0-P2R-C — phase-aware compatibility contract, design ONLY

2026-10-17 / Codex. **PARTIAL design; recommend Option D, targeted derivation.**
P2R-K remains historical FAIL. P2R-KN is a NEW PROPOSAL, NOT YET APPROVED,
NOT IMPLEMENTED and NOT RUN. No solver/test/tolerance/default changes, new
simulation, GPU diagnostic, acceptance campaign or performance measurement.
Standalone VV remains the program reference; this document audits explicitly
legacy coupled controls because coupled VV is still blocked/fail-closed.

Exact base587dfbff889495b4a7ade6b5c2c107ae4febdfde; branch
`design/v3-i0-p2r-compatibility`, independent full clone
`/tmp/mechsys-v3-i0-p2r-contract.FxULUy/work`. Persistent target
`/home/msys/git/mechsys-v3-i0-p2r-compatibility-design`.
Final commit/origin/clean/protection proof is external DELIVERY.json under
`/home/msys/SIMS/mechsys_v3_i0_p2r_contract/20261017-phase-aware-design/`.
PROJECT_STATUS.md is authoritative; PROJECT_STATE.md is the re-entry pointer.

## Review order and evidence

1. CONTRACT_DECISION.md: scope, gate status and why a new gate cannot yet be used.
2. PHASE_TABLE.md: actual source equations/array roles, startup and report phase.
3. EXACT_STRUCTURAL_CONTRACT.md: five categories, exact identity/branch checks.
4. FP64_SUMMATION_BOUNDS.md and COLLISION_EXCHANGE_CONTRACT.md: separate
   rounded-term sums, independent arithmetic and immutable physical budgets.
5. PHASE_AWARE_PROPAGATION.md: one/two-step recurrences, operation-rounding
   accounting and explicitly unclosed assumptions. Symbols are not tolerances.
6. CONTACT_HISTORY_REQUIREMENTS.md, DETERMINISTIC_ALTERNATIVE.md and
   PROSPECTIVE_TEST_PLAN.md: proposed future work, none executed here.

SOURCE_AND_EVIDENCE.json pins the read-only source/artifacts used. Previous
P2/P2R/P2R-R directories are byte-identical to base, including all failed
evidence. The prior audit's raw archive has SHA256
516c9a6ca7c79983883e87a1fdc6a9d5e86a6a3bf5965129808df30e92b341f7;
its exact final source/provenance receipts remain in the preceding namespace.
No raw archive or result is rewritten by this design.

Existing evidence: ten baseline and ten candidate-off legacy CUDA large runs,
93 rounded contributions/component, zero initializer, native FP64 RN atomics,
all-pairs snapshots. This establishes reduction nondeterminism, not frictional
history or general independently evolved compatibility. The P2R robust mode's
intentional occupancy correction is not expected to match legacy occupancy;
its independent geometry/exchange validation stays separate from default-off KN.

The numerical examples below are algebraic scales calculated from frozen
roundoff bounds and mass, NOT new run results or registered tolerances. Design
checks inspect source, hashes, documentation links and immutable-tree diffs;
they do not execute any prospective acceptance test.
