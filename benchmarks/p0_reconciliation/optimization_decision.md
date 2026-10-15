# P0-R7/P0-R8 - Amdahl bounds and first-experiment recommendation (2026-10-15)

Amdahl: S_max = 1/(1-f); partial S = 1/((1-f) + f/S_component). Fractions are of T_solve_wall on
the same workload, measured default-off where noted; profiling-enabled runs supplied structure
only. Category overlap avoided via nsys non-overlapping segments plus internal solve timers.

## Spherical DEM (S-legacy-small 18.6k, Nproc=8; S-legacy-large 154k)
- f(rebuild host work) ~= 0.30 (18.6k) / 0.56 (154k whole-run). GPU-resident Verlet construction
  at S_component 3-10 -> S ~= 1.2-1.35 (18.6k), ~1.5-2 (154k).
- f(per-step sync + MaxD readback + thrust temporaries + launch overhead) ~= 0.55-0.58
  (GPU idle 55-58%). Device-resident timestep control: S_max ~= 2.2-2.4.
- DECISION: first sphere experiment = DEVICE-RESIDENT PER-STEP CONTROL: remove the per-step
  thrust::max_element readback and its 2 cudaMalloc/step, decide the rebuild on-device with a
  bounded look-ahead (pipeDepth=1 initially), batch demaux readbacks to output cadence.
  Target: Domain::Solve loop, MaxD/thrust block. Complexity: moderate.
  Numerical risk: V0-A (delayed rebuild) - MUST pass the V0.1 candidate-completeness oracle
  (zero missed pairs at every force-evaluation step, adversarial fast/moving-wall/rotation cases)
  before any speed claim; the historical sticky-flag design is NOT auto-approved
  (V0_ASYNC_REBUILD_UNPROVEN).
  Smallest experiment: on-device rebuild decision, pipeDepth=1, persistent reduction buffer;
  benchmark S-legacy-small and S-legacy-large, 5 interleaved reps; acceptance = oracle PASS and
  >=3% complete-solve improvement, paired p<0.05.

## Polyhedral DEM (P-legacy-large 77k, Alpha=1e-4)
- f(force kernels) ~= 0.15 of default-off solve (15.4 of ~100 ms/step);
  f(per-step transfers + sync + host loop) ~= 0.85 (GPU idle ~94% profiled).
  Eliminating per-step D2H/H2D round-trips at S_component 3-6 -> S ~= 1.9-3.4.
- f(rebuild) ~= 0.12 at the historical Nproc=1 setting (P4, CPU-side).
- Screening waste: 76-78% of feature candidates rejected in pretests (P0-R4), but pretests cost
  ~2.4 ns/candidate; kernel share too small for screening optimizations until transfers are fixed
  and the neeint 6.4x gap is resolved.
- DECISION: first polyhedron experiment = REMOVE PER-STEP HOST/DEVICE STATE ROUND-TRIPS
  (buffer-resident stepping). Target: the ~2.7 cudaMemcpyAsync calls/step (avg 19.6 ms, max 275 ms)
  moving particle/vertex state, plus the per-step demaux readback.
  Complexity: moderate-high (prescribed walls, output, restart must be preserved).
  Numerical risk: output/restart equivalence; friction histories untouched if only transfer
  placement changes. Smallest experiment: extract the per-step memcpyAsync contents/sizes from the
  saved nsys trace, move the largest non-essential per-step D2H behind dtOut cadence, verify
  energy 369.835 bit-exactness and output equality, measure P-legacy-large default-off,
  5 interleaved reps.
- Second-priority (P1, before any screening work): resolve the neeint 6.4x interaction-list gap
  with kernel-side per-record feature counters; all kernel-share conclusions depend on it.

Rejected for now (with evidence): active-contact compaction and hierarchical screening (kernels
~15% of poly solve; active fraction 22-24%; Case B real but small until transfers fixed); SoA/AoSoA
(no measured memory-stall evidence; ncu unavailable); particle-centric contact kernels (atomics not
measured as bottleneck at these scales); CUDA Graphs (launches ~5% of API time; sync/readback
dominates); adaptive Verlet skin (defer until the rebuild path is device-resident and S1 sweeps).
