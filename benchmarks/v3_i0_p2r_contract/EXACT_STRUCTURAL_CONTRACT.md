# P2R-KN exact/structural specification — proposed, not approved

The first prospective scope is default-off legacy coupled single-owner canonical
spheres with the pinned CUDA large model/configuration. It is NOT a general
polyhedral, frictional, coupled VV/restart or robust-on-versus-legacy contract.
The existing robust-on geometry/exchange gates and negative guards are retained.

## Matching and identity rules

Record immutable baseline and candidate commits, header/executable SHA256,
compiler/device/configuration, parameter/fixture hashes, initial serialized
state and stage. Different implementation SHAs/executable hashes are expected;
each must equal its own preregistered identity, NOT each other's SHA. Shared
model/configuration/input and mapped initial physical state must be identical.
Source changes outside the registered default-off interface are a scope failure.

Use physical PersistentId, cell ID, feature ID and periodic-image code, with an
explicit storage-index mapping. Pair keys are canonical physical IDs plus
feature/image identity, not just current array indices. Count a MULTISET:
sets alone conceal duplicates. Check ownership and exactly-once state updates
before checking magnitudes. Hash history ownership, payload and update ordinal
separately. A zero force does not excuse a missing/duplicate/wrong owner.

Map iteration/storage order may differ only if proven observationally irrelevant.
Record original order when it controls force/update history, owner selection or
rounding. Atomic arrival order is not a physical identifier. Reordering inputs
to a supposedly deterministic reference sum changes its arithmetic contract.
Periodic reindexing requires a bijection and the corresponding unwrapped lever;
different physical images must not be collapsed as harmless storage changes.

For identical complete pre-force state and unchanged production operations,
individual force and body-torque contributions must match binary64 bits.
Changed contributions cannot pass merely because their total is small. CPU/GPU
contribution differences require separately frozen independent references and
formation budgets; the reduction budget does not authorize them. Initial
identical particle state alone is insufficient if populations/history differ.

## Five mandatory categories

| Category/quantity | Invariant and comparison | Budget/justification | Scope/exclusion | Failure classification |
|---|---|---|---|---|
|1 source/input/initial state | each source/binary matches registered SHA; shared parameters and full initial numerical payload exact | zero; controlled provenance, no NaNs | pinned builds/configuration; source hashes need not equal each other | IDENTITY/SCOPE_FAIL |
|1 persistent/cell/image/feature IDs | exact physical-key multiset, multiplicity and mapping | zero; topology/ownership are discrete | all proposed cases; no storage-index-only pairing | STRUCTURAL_FAIL |
|1 ownership/law/phase | one owner/update; exact collision/contact law and model flags, clocks/phase ordinals | zero; choose the same equations/state | backend-specific clock expectation in phase table; no silent VV relabel | OWNERSHIP/MODEL/PHASE_FAIL |
|1 rebuild schedule | identical decision when identical state/reference/Alpha; or proved common side of threshold interval | zero decision mismatch in certified region | evolved near-threshold case requires event study, not automatic same schedule | EVENT_UNRESOLVED or REBUILD_FAIL |
|2 occupancy/Omega/individual force/torque | matched state, independent frozen proxy/collision oracle; bitwise unchanged operations | existing per-edge/population/exchange budgets only; separate formation graph if approved | legacy occupancy and robust proxy are distinct configured references | GEOMETRY/FORMATION_FAIL |
|2 fluid impulse/angular exchange | actual collision write, reaction, correct frames/images | frozen independent budgets, no new allowance; see collision contract | single owner,Fconv1,alpha1; fixed pose not full angular dynamics | EXCHANGE/FRAME/UNIT_FAIL |
|3 force/torque reduction | exact rounded-term reference; actual scalar sum/order model | gamma_n*sum_abs, or separately certified arithmetic graph | zero initializer/93 terms in witness; other seeds/trees explicitly modeled | ACCUMULATION_FAIL or MODEL_UNRESOLVED |
|4 x/xb/vS/wS/wb/wa/q | each side's exact discrete map plus certified local rounding and propagated input radii | field/step-specific derivation, not observed maximum; currently unclosed | first/two-step scope, no generic long-time extension | EVOLUTION_UNRESOLVED/FAIL |
|4 populations/energy/work | phase-aware collision/stream maps and applicable discrete identity | independent collision budget plus a nonduplicated propagation ledger; NOT a conserved-LBM-energy epsilon | frozen branches,positive density/norm; no unaligned output work metric | FLUID/PHASE/WORK_UNRESOLVED/FAIL |
|5 creation/loss/slip/image/rebuild | exact branch/ownership/history transitions away from certified thresholds | zero topology/branch allowance; separate physical event criterion at ambiguity | new history/event controls NOT RUN; see requirements | STRUCTURAL_FAIL or EVENT_UNRESOLVED |

Every applicable category must pass independently. A large unused allowance in
one category cannot pay for a defect in another. A quantity lacking an approved
reference/budget is UNRESOLVED, never a default PASS. All unsupported modes and
negative controls must still reject explicitly. Hypothetical KN approval does
not alter old K or automatically promote corrected occupancy.
