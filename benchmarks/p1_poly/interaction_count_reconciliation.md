# P1-P - historical/current interaction-count reconciliation (2026-10-15)

## Categories (kept strictly separate)
- Broad-phase particle-pair candidates: ListPosPairs entries (linked cells, cell size
  2*Beta*MaxDmax - ALPHA-INDEPENDENT)
- Accepted particle-pair interactions: CInteracton records in PairtoCInt
  (CInteractonSphere::UpdateContacts: center distance <= Dmax1+Dmax2+2*Alpha)
- Constructed geometric feature interactions: Lee/Lvf/Lfv entries per record
  (CInteracton::_update_contacts: Overlap(feature,feature,R_i+Alpha,R_j+Alpha) AND
   Distance(feature,feature) <= R_i+R_j+2*Alpha)
- Geometric interactions actually tested per step: the GPU kernel workload (neeint/nvfint/nfvint)
- Positive-overlap geometric contacts: delta>0 inside the kernels (P0-R4 counters)

## Measured at the verified legacy state (P-legacy-large, 1001 steps)
| Quantity | Historical record | Current measurement | Ratio |
|---|---|---|---|
| ListPosPairs (per rebuild) | 85,748,325 | 85,748,325 | 1.000 EXACT |
| CInteracton creations (per rebuild) | 743,000 | 387,939 records | 1.91x |
| neeint (per step) | 15,992,853 | 2,489,068 | 6.42x |
| nvfint | 5,936,551 | 1,016,528 | 5.84x |
| nfvint | 5,938,065 | 1,016,449 | 5.84x |
| Final kinetic energy | 369.835 | 369.835 | 1.000 EXACT |
| Geometry | 77,002/1,815,920/1,361,939/530,981 | exact | 1.000 EXACT |

Per-particle-pair feature counts: historical neeint/ncoint = 39.6; current = 6.4.

## Findings
1. ListPosPairs is ALPHA-INDEPENDENT (linked-cell size = 2*Beta*MaxDmax; source
   Domain::UpdateContacts). The P0-L statement that the bit-exact ListPosPairs match pins
   Alpha=1e-4 is therefore CORRECTED: ListPosPairs does not pin Alpha. The Alpha=1e-4 value
   remains the only tested value producing an in-window rebuild with an energy match, but it
   is not uniquely determined by the candidate count.
2. The feature-acceptance rule in the current code (Distance(feature,feature) <=
   R_i+R_j+2*Alpha) yields 6.4 EE records per particle pair at the verified state. The
   historical 39.6 per pair implies an effective acceptance ~1.5x larger, which would require
   Alpha ~= 0.05 - but Alpha ~= 0.05 cannot produce an in-window rebuild (free-fall
   displacement at 1001 steps is ~4.9e-4) and cannot produce the reported 23.6 s rebuild.
   The historical quantities are MUTUALLY INCONSISTENT under the current code: no single
   Alpha reproduces (ListPosPairs, rebuild-in-window, neeint) simultaneously.
3. Candidate explanations, with evidence status:
   - Different measurement state (collapsed column): REJECTED - the 369.835 energy pins the
     free-fall state bit-exactly.
   - Alpha difference: REJECTED for the pair (neeint, in-window rebuild) - contradictory.
   - Different code revision of the feature construction: PLAUSIBLE but unverifiable - the
     historical uncommitted patch is NOT the preserved artifact (the preserved dirty-state
     patch contains later unrelated PID/prescribed-wall work, F0 finding), so the exact
     historical interacton.h/domain.h construction code is unrecoverable. The described
     patch (Stamp sweep replacing UniquePair) does not obviously alter Lee construction,
     but the remaining patch contents are unknown.
   - Different counter definition/scope: PLAUSIBLE - e.g. counting per-direction records
     (x2), per-image expansion, or CPU-side test counts rather than accepted records.

## Verdict
EQUIVALENT: geometry, final energy, ListPosPairs (candidate search reproduces exactly).
NOT EQUIVALENT: per-step feature-interaction counts (5.8-6.4x) and CInteracton creation
counts (1.9x) - UNRESOLVED. The P0-R4 screening fractions (21.8-23.9% active) are valid
for the CURRENT implementation and must not be treated as reproductions of the historical
feature lists. Kernel-share conclusions that depend on the historical neeint (e.g. the
63.5 ms/step force-kernel time) cannot be projected onto the current code.
