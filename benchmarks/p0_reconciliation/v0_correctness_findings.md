# P0-R6 - V0 correctness status (2026-10-15)

## V0-A - asynchronous Verlet rebuild (historical change 1)
Status: V0_ASYNC_REBUILD_UNPROVEN. Variant ABSENT from the baseline (verified: the baseline uses
synchronous MaxD + thrust readback + immediate rebuild; see PROJECT_STATUS.md 3.1).

The historical description (docs/perf/history/DEM_GPU_OPTIMIZATIONS.txt) claims a stale async flag
read is only late, never wrong. That is insufficient: a late rebuild means contact evaluation
continues on a candidate list up to pipeDepth=4 steps stale; safety requires
D_current_max + D_possible_before_next_rebuild <= Alpha
for the actual velocity/wall/rotation state, which the report argues only heuristically.
Proof obligations for any re-implementation: (i) flag init/reset ordering; (ii) no torn async
reads; (iii) event-ring bound on run-ahead vs displacement; (iv) zero missed candidate pairs at
every force-evaluation step under adversarial fast-particle/moving-wall/rotation tests;
(v) coupled LBM-DEM path equivalence. Energy agreement is not accepted as evidence.

## V0-B - cached polyhedral face centroids (historical change 3)
Status: V0_CENTROID_CACHE_UNPROVEN, likely unsafe as described. Variant ABSENT from the baseline
(no CalcCentroids/OverlapCentroid; EE/VF/FV use current vertex geometry).

Per the historical description, centroids are computed from live vertices at the END of
UpLoadDevice (once per rebuild) and the VF/FV pre-tests then use the cached world-space centroid
for all later steps. Vertices move between rebuilds (translation and rotation), so the cached
centroid drifts without any described margin; the rejection test can yield FALSE NEGATIVES when a
vertex approaches a face whose cached centroid has drifted. The reported 2.1% gain with
bit-identical energy does not establish N_false_negative = 0 over 1001 settling steps.
Required targeted test: translate/rotate a polyhedron between rebuilds; compare cached screening
vs direct current-geometry screening every step; report N_false_negative (must be 0),
N_false_positive, max centroid position error, max displacement since rebuild. BLOCKED until then.

Both historical measurements (1.04-1.05x, 2.1%) remain HISTORICAL_REPORTED and are not accepted
as baseline features. Re-implementation must pass the corresponding V0 gates first.
