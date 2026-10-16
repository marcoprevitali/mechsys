# Cell parity: FAIL; no coverage correction in V3-I0

Only step 0 uses identical registered CPU/GPU entry states. The independent
oracle enumerates all 1,000 cell centers and sphere/AABB intersections. It
separately integrates the twelve edge intervals, and separately reproduces the
legacy early-continue control flow using analytic projected intervals. No
compiled production geometry helper is called.

Initial counts (particle–cell pairs; each single-particle row is unique cells):

| Case | Exact / twelve-edge reference | Legacy-control-flow reference | Candidates CPU/GPU | Accepted CPU/GPU | Missing vs twelve-edge CPU/GPU |
|---|---:|---:|---:|---:|---:|
| centered fixed/moving/rotating | 27 | 27 | 27 / 27 | 7 / 27 | 20 / 0 |
| partial, outside-center | 29 | 28 | 35 / 35 | 6 / 28 | 23 / 1 |
| lattice boundary | 28 | 24 | 28 / 28 | 10 / 24 | 18 / 4 |
| periodic | 27 | 27 | 31 / 31 | 6 / 26 | 21 / 1 |
| small Alpha rebuild | 27 | 27 | 7 / 7 | 7 / 7 | 20 / 20 |
| contained small sphere, B=0 | 1 exact / 0 edge | 0 | 1 / 1 | 0 / 0 | 0 / 0 |

There are zero extra accepted pairs, zero duplicate candidate pairs and zero
wrong image levers in the registered cases. This does not make missing periodic
cells acceptable. Actual before/after rebuild snapshots still have seven
candidates against 27 positive-edge cells; a rebuild does not repair the cutoff.

## Measured source attribution (frozen V3-D source coordinates)

1. `lib/lbmdem/Domain.h:350`: CPU imprint rejects cell-center distance >Dmax.
   Active CUDA VC at `lib/lbmdem/lbmdem.cuh:569` admits Dmax+1.74dx before proxy
   evaluation. E.g. centered sphere R=1.2: cell (4,4,5), distance sqrt(2), has
   positive proxy but CPU rejects it. This causes 20 missing cells in the
   centered CPU case even when the actual candidate list contains all 27.
2. `Domain.h:450–552`, especially vertex eligibility near 533–540: ResetParCell
   only retains a sphere vertex if center distance <R+2Alpha. It is shared by
   CPU/GPU, so a small skin can exclude outside-center cells on **both** backends
   before CUDA's wider imprint bound is reached. The periodic fixture misses
   one positive-proxy candidate on both; Alpha=.0001 misses 20 on both before
   and after actual rebuild. Matching CPU/GPU counts of seven is therefore not
   a completeness PASS.
3. `lib/dem/special_functions.h:392–478` and CUDA `lbmdem.cuh:47–126`:
   `continue` in a top/bottom edge test skips remaining bottom/vertical edges
   in the same j iteration. This is not the mathematical sum of 12 independent
   covered-edge lengths. Boundary cell 545 has mathematical gamma
   .42141829910287303 but measured .34506022450983775. Partial CUDA cell 567 has
   .08830603488964169 vs .013514891676865814. The independent compatibility
   oracle reproduces the measured gamma without changing a tolerance.

There are 16 captured computed-gamma failures against the mathematical proxy
across backend/case/timestep (including repeats), all explained by that control
flow. Original strict failures remain in raw `analysis-full-v1/`; final
[PROXY_CONTROL_FLOW_FAILURES.json](PROXY_CONTROL_FLOW_FAILURES.json) preserves
the failed mathematical expectation and its independent attribution. Some
cells become zero occupancy and never reach a computed claim; those are also
retained in [CELL_MISMATCHES.json](CELL_MISMATCHES.json). This is an observed
legacy proxy implementation defect, not an exact-volume-vs-proxy correction.

On common positive single-owner cells initial gamma and B match exactly;
max Omega difference 1.2335764327338003e-17, solid population increment difference
6.071532165918825e-18. They cannot certify total force parity on different cell
sets. Centered moving Jsolid,x is CPU .008353349348328622 vs GPU
.012564025997669036. Their isolated unit-conversion reactions each pair within
roundoff, but they represent different occupancy. Shared cells are separately
BLOCKED, not included in these common-cell agreement claims.

Stop condition: common positive CPU/GPU coverage acceptance is blocked; no
geometry, cutoff or occupancy formula was corrected. Per-backend collision and
unique common-cell ledgers remain meaningful and were completed independently.
These fixtures demonstrate causes for **their own** discrepancies, not a new
attribution of V2's different fast two-sphere residual without replaying it.
