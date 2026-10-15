# P0-R legacy comparison - historical vs reproduced (2026-10-15)

Environment: RTX A6000 (84 SM), CUDA 12.6.85, driver 595.84, FP64 (USE_GPU_DOUBLE), Xeon Gold 6430.
Branch perf/p0-reconciliation (baseline 72a33d0 + diagnostic instrumentation 62384c8, bf01109).
Raw logs: /home/msys/SIMS/mechsys_p0_baseline/20261015-p0r/logs/. Hashes: benchmark_manifest.json.

## S-legacy-small (18,616 spheres, Alpha=0.01, dt=5e-5, T0=Tf=0.5, 20,001 steps, Nproc=8)

| Measurement | Historical | Reproduction | Verdict |
|---|---|---|---|
| Particles | approx 18,600 | 18,616 (0.09%) | consistent (Bernoulli HCP removal, seed 1234) |
| Rebuild count | 38 | 38 (12 compression + 26 shear) | EXACT |
| Mean rebuild | 119.6 ms (pre-Stamp) / 92.9 (post) | 102.2 ms (median 93.7) | between historical states |
| Compression solve | 6.647 s | 6.561 s | 1.3% |
| Shear solve | 7.648 s | 6.540 s | 14.5% (Nproc/window sensitivity) |
| Rebuild share (shear) | claimed 84% | 35.5% | NOT REPRODUCED |
| Alpha 0.01->0.02 | 38 -> 17 rebuilds; 7.585 -> 5.757 s | 38 -> 19; solve 13.10 -> 11.54 s | reproduces |

Nproc sensitivity (mean rebuild ms): 178.1 (Nproc=1), 148.6 (2), 124.0 (4), 102.2 (8).
Historical 119.6 ms corresponds to Nproc ~= 4; historical compression wall matches Nproc=4 within 0.2%.

## S-legacy-large (154,366 spheres, Alpha=0.01, box 10.4^3, 20,001 steps, Nproc=8)

| Measurement | Historical | Reproduction | Verdict |
|---|---|---|---|
| Particles | approx 154,000 | 154,366 (0.24%) | consistent |
| Rebuild share (shear) | claimed 91% | 66.4% (69.1 of 104.0 s) | NOT REPRODUCED; grows with N (35.5% -> 66.4%) |
| Rebuilds | not reported | 72 (10 + 62), mean 1169 ms | new datum |

## P-legacy-large (77,002 polyhedra, Alpha=1e-4, 1001 steps)

| Measurement | Historical | Reproduction | Verdict |
|---|---|---|---|
| Geometry | 77,002 / 1,815,920 / 1,361,939 / 530,981 | exact (code counts edges/faces at 2 per feature) | EXACT |
| Final kinetic energy | 369.835 (x6 runs) | 369.835 | EXACT |
| ListPosPairs | 85,748,325 | 85,748,325 (Nproc-invariant) | EXACT |
| Solve | 197.36 s (197 ms/step) | ~100 ms/step default-off; 271 profile-enabled | see neeint gap |
| Force kernels | 63.55 s (63.5 ms/step) | 15.4 ms/step (nsys) | 4.1x less (neeint gap) |
| Rebuild | 23.6 s | 5.23 s (Nproc=8); 21.24 s (Nproc=1) | RECONCILED by CPU parallelism |
| EE/VF/FV candidates per step | 15,992,853 / 5,936,551 / 5,938,065 | 2,489,068 / 1,016,528 / 1,016,449 | 5.8-6.4x GAP - UNRESOLVED |

### The neeint gap (dominant open item)
ListPosPairs and the final energy match bit-exactly, but the historical per-step feature-interaction
counts are 5.8-6.4x ours, and the historical rebuild created 743k CInteracton objects vs our
387,939 interaction records (1.9x). Since the physics is identical, the difference is in how
candidate pairs expand into per-feature interaction records (code version or counting definition),
not in the candidate search. Kernel-side counters (P0-R4) now measure the real control flow;
closing the gap needs the original historical build or interaction-construction instrumentation.

### Reconciliation of the 84-91% sphere rebuild claim
From the record's own figures: 38 x 119.6 ms = 4.545 s = 31.7% of the reported 14.295 s total
solve, or 59.4% of the 7.648 s shear solve - never 84%. No consistent window reproduces 84%.
Measured shares (validated config, Nproc=8): 23.3%/35.5% (18.6k) and 32.4%/66.4% (154k).
CPU parallelism raises shares but cannot reach 84/91% at any tested Nproc.

STATUS: HISTORICAL_REBUILD_SHARE_UNRECONCILED. Per-rebuild costs and rebuild counts DO reproduce;
the aggregate share claim does not and contradicts the record's own arithmetic. Historical values
are preserved verbatim in docs/perf/history/.
