# MechSys GPU DEM optimization — PROJECT_STATUS.md

**As-of:** 2026-10-15 (P0 first measurements; P0-L registered)
**State:** `F0 PASS` / `V0 PARTIAL` / `P0 FIRST MEASUREMENTS COMPLETE` / `P0-L REGISTERED — NEXT`
**Next authorized work:** `P0-L` exact legacy benchmark reproduction (recover/verify the 18.6k/154k sphere and 77k polyhedron historical configurations, reproduce timing decompositions, classify per `AGENTS.md` §5.1). **No CUDA algorithm changes during P0-L.** Then `P0-R` reconciliation and remaining `V0` oracles. Do not begin a broad rewrite.
**Agent:** GLM-5.3 Flash (or successor); operational rules in `AGENTS.md`.
**Original project:** https://github.com/Axtal/mechsys
**Fork URL / owner:** https://github.com/marcoprevitali/mechsys / `marcoprevitali` (authenticated account and public fork metadata verified 2026-10-15)
**Old local checkout:** `/home/msys/mechsys` at `e4ba163ec9f32c8bccb0fd8619ba79e000d3d6d8`; preserved dirty and not mutated during `F0`
**New isolated clone:** `/home/msys/git/mechsys-gpu-opt`, branch `perf/gpu-baseline` at the matching old SHA
**Precision of historical benchmarks:** GPU double precision (`-DUSE_GPU_DOUBLE`) on NVIDIA RTX A6000 (84 SMs); do not assume the current host/GPU is unchanged.

> **Evidence levels:** `HISTORICAL_REPORTED` means results transcribed from the user-supplied DeepSeek work summary dated 2026-10-14; they have **not** yet been independently reproduced or verified against source. `SOURCE_VERIFIED` requires auditing the actual local code. `MEASURED` requires raw timing/logs + code SHA. `PASS` requires documented numerical acceptance checks. Keep these labels distinct.

## 0. Why this project exists

Improve **complete GPU DEM simulation throughput** while keeping MechSys physics, contact histories, periodic-image behavior, and coupling interfaces correct. The development program arose from discussion of: GPU Verlet construction; spatially heterogeneous skins based on velocity/fluctuation temperature/shear/mixing; active-contact compaction; SoA/AoSoA; spatial ordering; and conflict-free or aggregated force accumulation. Existing profiling suggests **two separate bottlenecks**: spherical DEM is dominated by CPU-mediated contact rebuilds; polyhedral DEM is dominated by geometric feature-pair tests. Do not force one optimization recipe onto both.

The project's Git isolation is part of its correctness requirements: **develop in a separate GitHub fork, on topic branches, with the original checkout preserved**. `F0` established that isolation on 2026-10-15. The historical performance patch described below was not present as a coherent five-file worktree diff in the original checkout; the actual dirty state was preserved but not automatically imported because it contains later PID/ratcheting/example work and an accidental `test_cu_01.cu` prefix edit unrelated to this optimization program.

## 1. Historical evidence — preserve, replicate, and critically audit

**Source:** the user's supplied `Pasted text(20261014-090646).txt` (previous DeepSeek optimization summary). Archive a *reviewed* copy or an integrity hash in `docs/perf/history/` once the fork exists; do not quietly replace historical outputs. The previous report says five files were changed and **none had been committed**:

- `lib/dem/dem.cuh`
- `lib/dem/distance.h`
- `lib/dem/domain.h`
- `lib/dem/interacton.h`
- `lib/lbmdem/Domain.h`

Do not infer that those edits still exist until inspected. If present, back up the entire tracked diff, inventories of untracked files, commit/branch/remote state, and relevant source fixtures **before** touching Git remotes, switching branches, or editing.

### 1.1 Spheres — rebuild-bound (`HISTORICAL_REPORTED`)

| Workload | Observation | Consequence |
|---|---|---|
| `tdem/test_cu_04`, 18,600 spheres; compression + shear | Contact rebuild ~84% of shear solve | Optimize *whole rebuild*, not only pair-force kernel |
| `tdem/test_cu_04`, 154,000 spheres | Contact rebuild ~91% of shear solve | CPU/host ↔ device dependencies scale poorly |
| Breakdown *within a rebuild* | CPU neighbor search/interaction management ~62.8–70%; D2H ~14–15%; H2D ~15–23% | GPU-resident reconstruction **could replace CPU work and transfers**; its upside is **not capped at 30%** |
| `Alpha`: 0.01 → 0.02 | 7.585 → 5.757 s (~24.1% lower runtime); rebuilds 38 → 17 | Tune uniform skin early with a correctness oracle; report increased candidate work |
| Device sticky rebuild flag + pipelined host check | ~1.04–1.05× total speedup | Needs delayed-rebuild safety and asynchronous-copy ordering audit |
| Interaction `Stamp` sweep instead of `UniquePair` hash set | ~1.03–1.07× total speedup, 12/12 paired runs faster | Retain as candidate, then reproduce and validate |

The reported asynchronous flag may be read one step late, with a four-step host throttle. **A sticky flag alone does not establish that no physical contact can be missed during delayed rebuild**. The required bound is on additional maximum vertex/surface-point motion until *the next force evaluation using a rebuilt list*, including accelerated particles, moving walls, and rotations. Confirm stream/event ordering and host memory suitability for `cudaMemcpyAsync`.

### 1.2 Polyhedra — geometry-test-bound (`HISTORICAL_REPORTED`)

Case: `tdem/test_cu_03`, Voronoi column collapse; ~77,002 polyhedra; 1,815,920 vertices; 1,361,939 edges; 530,981 faces; 403,764 particle-pair interaction records.

| Feature family | Candidate feature tests / step | Kernel time / step |
|---|---:|---:|
| Edge–edge (`EE`) | 15,992,853 | 26.41 ms |
| Vertex–face (`VF`) | 5,936,551 | 18.61 ms |
| Face–vertex (`FV`) | 5,938,065 | 18.09 ms |
| **Total** | **27,867,469** | **63.11 ms** |

This is ~69 **candidate feature tests per recorded particle pair**. It is **not** a measured active-contact fraction or a claim that 1 in 69 features contacts. Reported force kernels occupy ~95.3% of profiled **GPU kernel** time, **not** necessarily of the end-to-end wall clock. A separate comparison reports ~197 s for 1,000-step runs, versus ~63.5 s force-kernel time per 1,001-step profile: different measurement boundaries/rebuild counts must be reconciled before any overall speedup projection.

One polyhedral contact rebuild reportedly cost **23.6 s**: ~19.2 s in `CInteracton` creation/collection, ~2.8 s stale cleanup; a candidate-pair list contained ~85.75 million entries (~1.4 GB). Count true allocation costs separately from feature-context construction and other work included in that bucket.

### 1.3 Previous experiments — do not repeat blindly

| Change | Historical outcome | Decision |
|---|---|---|
| Sort EE/VF/FV **interaction records by owning particle** | No measurable force-kernel benefit; sort cost ~3.6 s/rebuild for ~900 MB | `REJECTED_FOR_THAT_VARIANT`; **not** a test of SoA, AoSoA, spatial particle sorting, or new neighbor-list layout |
| Cache face centroids on GPU, refresh during upload/rebuild | ~2.1% lower polyhedral wall time; same **printed** final energy | `CORRECTNESS_UNRESOLVED`: centroid may become stale between rebuilds; compare exact current centroid vs cache in every evaluated pretest; prove conservative rejection or update each step using current body pose |
| FP32 in place of FP64 | Sphere test faster but materially different mechanical state; polyhedra diverged and ran slower | **Do not enable** as a performance shortcut; diagnose cancellations separately if later requested |
| Replace unordered-map stale sweep with flat pointer vector | No improvement | Do not reimplement without new evidence |

**Interpretation:** Failure of feature-record sorting suggests that sort alone did not address the dominant cost. It does not prove the force kernels are universally computation-bound; require profiler metrics and feature-stage counters before concluding that.

## 2. Reference architecture — LAMMPS, as guidance rather than a speedup promise

Study **LAMMPS KOKKOS** specifically (GPU-resident data/neighbor construction), not just its older GPU offload package. Useful sources:

- Paper: A. Johansson et al., *LAMMPS-KOKKOS: Performance Portable Molecular Dynamics Across Exascale Architectures* (2025), https://arxiv.org/html/2508.13523.
- GPU bins and neighbor search: https://github.com/lammps/lammps/tree/develop/src/KOKKOS (`nbin_kokkos.cpp`, `npair_kokkos.cpp`).
- Granular Hooke-history style: `pair_gran_hooke_history_kokkos.cpp`; history management: `fix_neigh_history_kokkos.cpp` in the same tree.
- Documentation: https://docs.lammps.org/Speed_kokkos.html and https://docs.lammps.org/Developer_par_neigh.html.

Design lessons **to benchmark, not copy uncritically**:

1. Keep neighbor construction, particle integration and contact work on GPU where beneficial; time full pipeline, including history migration.
2. Separate GPU spatial-bin formation, neighbor-list layout and force-kernel ownership. LAMMPS uses multiple layouts for multiple kernels.
3. Compare **contact-centric one thread/contact**, **particle-centric central-particle local accumulation + neighbor reaction atomics**, and **cooperative neighbors per particle/pair**. Small systems can suffer insufficient particle parallelism.
4. Half vs full neighbor lists have different compute/atomic tradeoffs. **History-dependent DEM is not ordinary Lennard-Jones:** a physical contact's tangential/rolling history must advance exactly once. Never naively run two independent history updates for a full pair list.
5. Interaction preprocessing/compaction demonstrated in expensive ReaxFF kernels motivates a polyhedral test, but does not guarantee sphere DEM benefit.
6. SoA/AoSoA, GPU neighbor-list transposition, spatial sorting and reductions are separate hypotheses. Real gains depend on access patterns and device architecture.

**Porting boundary:** LAMMPS's API and memory manager are reference designs, not drop-in components. Avoid introducing Kokkos as a prerequisite to optimizing this MechSys CUDA implementation.

## 3. Mandatory correctness gates (`V0` before new speed work)

`V0.1 REBUILD_PIPELINE`: Inspect flag allocation/reset, producer stream and copy/event dependencies, host-pinned vs pageable memory, back-pressure, maximum rebuild detection latency, and reference-state resets. Construct an adversarial rapidly moving/accelerating particle or wall whose missed neighbor would be detectable. Require **no missed candidate pair at each force-evaluation timestep**, not just post-hoc energy agreement. If the delayed pipeline cannot be proved or tested safely, disable it in the baseline or use a conservative guaranteed look-ahead bound.

`V0.2 CENTROID_CACHE`: Determine when all cached face centroids are actually refreshed. For rotating/translating rigid polyhedra, compare cached broad-phase rejection against original current-geometry rejection on many timesteps, including near-boundary cases. **Zero false rejections** is required. Prefer inexpensive body-frame centroids transformed by current pose or a conservative margin over stale world-space positions. Output-energy equality at printed precision is not a proof.

`V0.3 HISTORY_AND_IDENTITIES`: Verify same contact-law formulas, VV/EE/VF/FV contributions, normals, torque signs, rolling and friction history evolution, per-pair totals, wall reactions, periodic images, fixed/moving boundaries, restart and coupled LBM–DEM call paths. Distinguish legitimate FP64 summation-order changes from state corruption. Tests must explicitly validate creation, persistence, separation, recontact and geometric-feature identity across rebuild.

`V0.4 BASELINE_COMPATIBILITY`: Preserve an unmodified upstream reference and separately profile the *historical-patch* implementation, **if reconstructed and validated**. Do not treat previous uncommitted changes as upstream baseline.

The pass evidence must include source SHA, commands, independent oracle or control, thresholds, observed errors/counters, and raw artifact paths. Failure blocks dependent optimization work. **No production speed claim before these gates.**

### 3.1 Current baseline audit — 2026-10-15

Baseline source is fork commit `e4ba163ec9f32c8bccb0fd8619ba79e000d3d6d8`; the default-off instrumentation is isolated at `4ae0111ebd10249605519b0ccd4155018d72d5d3`.

- `V0.1 PARTIAL / HISTORICAL VARIANT ABSENT`: the baseline launches `MaxD`, evaluates `thrust::max_element`, dereferences the device iterator on the host, and immediately calls `UpdateContactsDevice()` when `maxdis > Alpha`. There is no asynchronous copy, sticky device flag, host polling throttle, or delayed-rebuild path in this source. This removes the historical delay hazard from the selected baseline but does not validate the unavailable historical patch or prove the full candidate-set oracle.
- `V0.2 PARTIAL / HISTORICAL VARIANT ABSENT`: no `CalcCentroids`, `OverlapCentroid`, or cached face-centroid buffer exists in the baseline DEM path. EE/VF/FV use current vertex geometry. The historical cached-centroid experiment remains unresolved and is not accepted or imported.
- `V0.3 PARTIAL`: rebuild history follows `DnLoadDevice` -> `PairtoCInt`/feature maps -> `UpLoadDevice`; pair keys use ordered particle indices and feature keys use ordered local feature indices. They are stable in the present unsorted storage but are not a canonical unordered physical-ID abstraction suitable for future sorting without redesign.
- A 10-step, initially overlapping, tangential two-sphere FP64 test compared CPU and CUDA outputs. Stored `Position`, `PVelocity`, `PAngVelocity`, `Quaternion`, `PEkin`, applied-force fields, tags, radii and rods were exactly equal at float32 output precision for all 10 frames. Contact branch/normal/tangential/dashpot/history outputs were exactly equal from frames 1-9. Final printed energies matched (`Ekin=0.82916`, `Epot=5.8649`). Input SHA256: `f5b17b40be4e216053fd99444ec0340baacdbddcb71560cea4a327058cd860a8`; artifacts: `/tmp/mechsys_gpu_opt_contact_cpu/` and `/tmp/mechsys_gpu_opt_contact_gpu/`.
- Two baseline diagnostic-output defects were exposed and are not silently treated as dynamics failures: CUDA frame-0 contact-force output is zero before the first device force evaluation, while CPU reports its host-initialized force; CUDA `PAngacceleration` remains zero on the host because `DnLoadDevice` does not copy `bWdot`, even though angular velocity and the full stored trajectory match CPU. These need a separate output-semantics decision before claiming complete V0 parity.
- Candidate completeness across rebuilds, separation/recontact, restart, periodic-image transitions, moving walls, polyhedral feature histories and action-reaction/energy identities still require dedicated oracles. `V0` is therefore not a PASS.
- `V0.4 COMPILE ONLY`: `tlbmdem_cu_02` compiles and links with the shared headers at `sm_86`; no coupled runtime acceptance test was run. Compilation is not coupled-runtime evidence.

## 4. Parallel work tracks and milestones

Statuses at handoff are `NOT_STARTED` unless explicitly marked `HISTORICAL_REPORTED` in §1.

| ID | Workstream | Main deliverable | Dependency / stop rule |
|---|---|---|---|
| **F0** | **Fork + safe import** | Fork owned by user, isolated clone, complete old-work provenance and reviewed patch migration | FIRST; original checkout must remain untouched |
| **V0** | Numerical audits of existing optimizations | Rebuild-delay and centroid-cache truth tables; contact-history and pair-oracle gates | Before promoting old patches |
| **P0** | Reproduce instrumented baselines | Full-solve and GPU sub-timings, matching windows, toolchain, build/inputs archived | Before prioritizing new algorithms |
| **S1** | Spheres: uniform-skin sweep | Candidate fraction, rebuild interval, full wall time vs `Alpha` | V0 + P0 |
| **S2** | Spheres: **complete** GPU-resident neighbor/rebuild pipeline | Binning, pair-generation, history preservation, device rebuild decision; CPU reference mode | S1; prove geometric superset at every step |
| **S3** | Spheres: kernel ownership | Contact-centric vs central-particle vs warp-cooperative, with history-safe force updates | S2 or separately isolated prototype; no assumed winner |
| **P1** | Polyhedra: instrument feature screening | EE/VF/FV counts passing coarse bounds, exact geometry, penetration, force law; timing per stage | V0 + P0 |
| **P2** | Polyhedra: reduce tested feature pairs | Conservative hierarchical/feature screening, optionally a broad-phase cache | P1; zero missed feature contact |
| **P3** | Polyhedra: active compaction | Device-resident active index queue; compact vs fused resolution; no duplicate geometry work | P1/P2; total cost incl. scans and launches |
| **P4** | Polyhedra: rebuild and allocation architecture | Profile/replace expensive CPU `CInteracton` creation and huge candidate allocations | V0 + P0, can prototype independently |
| **X1** | Layout and ordering study | AoS vs pure SoA vs AoSoA (8/16/32/64); optional spatial cell ordering; measure conversion cost | P0; separate layout from sorting experiments |
| **X2** | Force accumulation study | Direct atomics vs local central accumulation vs warp/pair grouping vs CSR gather | Require measured atomic bottleneck or cheap discriminating prototype |
| **X3** | Spatially heterogeneous skin | Conservative `a_i` budgets using velocity, granular temperature, shear/mixing as *predictors* | S2 validated; must beat tuned S1 in relevant workloads |
| **Z0** | Portfolio selection | Accepted variants, per-workload speedups, uncertainty, memory, numerical evidence | All selected experiments PASS |

**Initial execution limit for a new agent session:** Carry out `F0` completely, then audit `V0` and build `P0` evidence. Propose the first bounded performance experiment from the actual profile. **Do not implement S2/P2/P3/X1/X3 simultaneously.**

### Adaptive-skin validity contract (for eventual X3)

For conservative spheres, the list at rebuild time `t_b` may include a pair if its separation is below the interaction cutoff plus `a_i + a_j`. Until the next rebuild, bound every particle's accumulated relevant motion by its fixed allowance `a_i`. For rotating polyhedra, bound the motion of **all potentially interacting features**, not merely the center. To accommodate delayed device-to-host control, retain a rigorously bounded margin for extra motion before new-list use. Local velocity, `T_g`, shear rate and neighbor turnover select *performance guesses*, not the correctness condition. Check candidate set completeness every tested step with an independent oracle. Account for periodic images and moving wall geometry; validate dimensional consistency of `T_g` definitions.

## 5. Performance and test contract

**Benchmark sets:**

- `S-small`: ~5k spheres (representative research scale; launch overhead relevant).
- `S-legacy`: original 18.6k spheres compression/shear and 154k spheres (if inputs accessible).
- `S-nonuniform`: moving wall / intruder / shear-band case, with x–y periodicity where applicable.
- `P-small`: small polyhedra to validate feature geometry and histories by independent oracle.
- `P-legacy`: 77,002-particle polyhedral collapse / feature counts (if resource/input accessible).

For every paired A/B comparison, record: SHA and exact diff state; compiler, GPU, CUDA, precision and build flags; fixed input hash/seed; number of steps, rebuild count, generated feature candidates and actual contact fractions; kernel event times; D2H/H2D, host rebuild and idle/sync; **complete-solve wall time**, output cadence, memory footprint and allocation pressure. Split startup from warmed steady-state and compare the **same integration and output windows**. Use >=3 interleaved paired repetitions for screening and >=5 for final promotion, with dispersion and confidence in the result. No claim of a 2% win from one run. For very expensive 77k polyhedral cases, establish a shorter but representative registered workload first without relabeling it as the historical full run.

Where possible use `nsys` for stream/host timeline and `ncu` for kernel-level memory sectors/cache/occupancy, instruction issue, branch activity and atomics. Do not infer an architecture bottleneck solely from a lack of speedup in sorting. Distinguish **candidate particle pairs, feature candidates, broad-phase survivors, physical contacts and force evaluations** with explicit counter definitions.

**Numerical gates:** (i) complete candidate superset at force evaluation time, (ii) no duplicates/overflow, (iii) continuity of canonical pair/feature histories and image transitions, (iv) force/torque/momentum/energy identities within justified FP64 tolerances, (v) stable restart/output behavior, (vi) coupled `lib/lbmdem/Domain.h` coverage for changed shared functions. A faster solver failing any hard correctness gate is **REJECTED**.

### 5.1 P0 implementation and blocker — 2026-10-15

- Toolchain: NVIDIA RTX A6000, compute capability 8.6, 49,140 MiB, driver 595.84; CUDA 12.6.85; GCC/G++/GFortran 13.3.0; CMake 3.28.3; Nsight Systems 2024.5.1; `ncu` unavailable. CPU is Intel Xeon Gold 6430. Production precision remains FP64 (`USE_GPU_DOUBLE`).
- Valid build: `/tmp/mechsys_gpu_opt_build_sm86`, Release/O3, OpenMP, CUDA, FP64. `cuobjdump --list-elf` verified `sm_86` for `test_cu_01`, `test_cu_02`, `test_2spheres_gpu`, `test_cu_04`, and `tlbmdem_cu_02`. A prior sandbox-only build fell back from `-arch=native` to `sm_52` and is rejected for A6000 timing.
- Commit `4ae0111` adds default-off rebuild profiling. Set `MECHSYS_PROFILE_GPU_REBUILD=1` to synchronize only at profile stage boundaries and print one `DEM_GPU_REBUILD_PROFILE` record with rebuild count; download/reset, host-contact, state-pack and upload/refresh seconds; particle-candidate and interaction-record sums/maxima; and VV/EE/VF/FV feature-candidate sums. Because enabling it adds synchronizations, its stage totals are diagnostic and enabled/disabled whole-run times must not be compared as an optimization result.
- Default-off regression: the instrumented CUDA binary reproduced all 20 HDF files from the pre-instrumentation two-sphere run with maximum absolute stored-field difference `0.0`; artifacts: `/tmp/mechsys_gpu_opt_instrumented_default/` and `/tmp/mechsys_gpu_opt_contact_gpu/`.
- Counter smoke only: a 10-step `Alpha=1e-6` run reported 10 rebuilds, candidate-pair sum/max `10/1`, interaction-record sum/max `10/1`, VV sum `10`, and EE/VF/FV sums `0/0/0`. Its timing fields are rejected because a separate `ratcheting_gpu_v15` process was using about 66% GPU at 79 C; artifacts: `/tmp/mechsys_gpu_opt_profile_smoke/`.
- `P0 BLOCKED`: do not run or report a complete-solve baseline, Alpha sweep, `nsys`, or small-speedup A/B comparison until that user workload is finished and the GPU is thermally idle. No new performance or speedup claim was made in this session.

### 5.2 P0 first measurements — 2026-10-15 (A6000 idle, 0-8% util, 48-62 C)

Environment: same toolchain as §5.1; build `/tmp/mechsys_gpu_opt_build_sm86` at commit `54574e0` (`test_cu_04` binary contains instrumentation, verified by string; `test_cu_03` rebuilt after the parameterization commit). All runs sequential, uncontaminated. Raw artifacts: `/home/msys/SIMS/mechsys_p0_baseline/20261015-p0sphere/` and `/home/msys/SIMS/mechsys_p0_baseline/20261015-p0poly/`.

**Registered inputs (hashed in `inputs/` subdirs):**

- `test_cu_04_reduced.inp` (pre-existing, gitignored in original checkout) SHA256 `2330f50f411915d0b219f2c3e8e762881261efce269ffb12107925ac88ed5fc3`: 207 spheres, 601 iterations, wall 0.41-0.49 s (3 reps). Micro-run reference only; startup-dominated.
- `test_cu_04_ssmall.inp` SHA256 `93e6466e0c0ccba7d77d1f0ed0e14cb1f885484e31e0b7caa47e43829d10e30c` (S-small): 7,471 spheres, 1,001 + 2,001 iterations (two Solve stages), wall 8.41/9.18/9.04 s (3 default-off reps).
- `test_cu_04_ssmalldyn_a{0.025,0.01,0.005}.inp` SHA256 `bb2e46d7…`, `77e7a25a…`, `1bd2d7a1…`: same geometry, T0=0.1/Tf=0.2 (30,001 iterations).
- `test_cu_04_smid_a0.01.inp` SHA256 `81319e5e…` (S-mid): 17,825 spheres, Alpha=0.01, 30,001 iterations.
- Polyhedron P-small is argv-defined (see commit `54574e0`): `test_cu_03 8 0.01 256 12 12 0.002` = 12x12x12 cells, 1,382 polyhedra (32,118 vertices), 200 iterations.

**Sphere results (`DEM_GPU_REBUILD_PROFILE`, enabled runs are diagnostic only):**

| Workload | Alpha | rebuilds | host rebuild total | wall | candidate pairs /rebuild | interaction records /rebuild |
|---|---|---:|---:|---:|---:|---:|
| S-small 7,471 | 0.25 | 0 | 0 | 8.73 s | 0 | 0 |
| S-small dyn | 0.025 | 5 | 0.207 s | 15.54 s | 795,698 | 31,949 |
| S-small dyn | 0.01 | 12 | 0.450 s | 14.64 s | 795,699 | 31,949 |
| S-small dyn | 0.005 | 25 | 0.786 s | 14.83 s | 795,710 | 31,949 |
| S-mid 17,825 | 0.01 | 10 | 1.031 s | 31.00 s | 1,962,239 | 77,310 |

Findings: (1) rebuild count scales ~1/Alpha; per-rebuild host cost ~31 ms (7.5k) / ~103 ms (17.8k); candidate pairs ~106-110 per particle. (2) At registered scales rebuild cost is only ~1.3-3.3% of wall: **the historical 84-91% rebuild dominance does NOT reproduce here.** (3) `nsys` on S-small-dyn a=0.01: per-step GPU busy ~216 us (CalcForceVV 95.4 us, CalcForceVF 55.7 us, Reset 25.4 us, Rotate 19.5 us, Translate 8.8 us, MaxD+reductions ~10 us), but wall ~0.5 ms/step: `cudaStreamSynchronize` 4.09 s + `cudaMemcpyAsync` 2.11 s (2/step) + 200k launches 0.82 s over the window; **GPU idle ~55%**. The S-small regime is **host-synchronization-bound**, consistent in direction with the historical pipelining win (~1.04-1.05x) but not with rebuild-share percentages. Fixed startup (generation + CUDA init + initial build) is ~6-7 s and must be excluded in A/B windows.

**Polyhedron results:**

| Config | steps | wall | rebuilds | host rebuild total | candidate pairs /rebuild | interaction records /rebuild | EE/VF/FV feature sums |
|---|---:|---:|---:|---:|---:|---:|---|
| 12^3, Alpha=0.01 (fixed list) | 200 | 5.99-6.13 s (3 reps) | 0 | 0 | n/a | n/a | not sampled |
| 12^3, Alpha=1e-4 (dyn) | 1000 | 3.25 s | 5 | 0.310 s | 567,398 | 6,152 | 199,245 / 80,675 / 80,630 |

Findings: (1) fixed-list run costs ~27 ms/step wall but only ~1.60 ms/step GPU (CalcForceEE 528 us + CalcForceVF 398 us + CalcForceFV 388 us + Rotate 240 us + Translate 39 us): `nsys` shows `cudaMemcpyAsync` 2.75 s over 1,020 calls (~5/step, avg 2.7 ms, max 30 ms) and 416 `cudaMalloc` calls (max 129 ms) dominate; **the registered P-small regime is per-step host-transfer-bound, not geometry-kernel-bound.** (2) The dyn run's low wall/step (~1-3 ms) during free flight shows contact-list size, not particle count, drives per-step cost. (3) Historical 77k-polyhedron percentages cannot be projected from 1.4k-polyhedron data; kernel cost scales with feature pairs while per-step transfers scale with state size. Registered P-legacy reproduction remains open.

**Consequences for work order:** the measured evidence does not support starting S1 (uniform-skin sweep) as the next optimization on these registered workloads, because rebuild cost is not yet dominant at accessible scales; the priority is to quantify how the sphere host-sync overhead and the polyhedron per-step memcpy behave at larger N (toward the historical 18.6k/154k sphere and 77k polyhedron regimes) before choosing the first optimization target. Update §4 dependencies after that reconciliation.

### 5.3 `P0-L` — exact legacy benchmark reproduction (NEXT; registered 2026-10-15)

Priority: HIGH — mandatory before optimization selection. Requirements and hard rules: `AGENTS.md` §5.1. **No CUDA algorithm changes during P0-L.** Historical and current P0 datasets remain separate, each with its own provenance.

**Recovered historical record (Task 1, first pass — 2026-10-15):**

- The canonical previous-study summary was located at `/home/msys/Documents/xwechat_files/wxid_3vuoi80voian22_571b/msg/file/2026-10/DEM_GPU_OPTIMIZATIONS.txt` (received 2026-10-14, 21,206 bytes, SHA256 `a62db59489f1a169e258f99e49c536ad37c32f676a5f386f9a4161c33131667c`) and archived in the fork at `docs/perf/history/DEM_GPU_OPTIMIZATIONS.txt` (hash in `docs/perf/history/SHA256SUMS.txt`). This supersedes the second-hand transcription in §1 as the primary historical source.
- No original legacy input files were found: the only `test_cu_04` input in the original checkout is the unrelated `test_cu_04_reduced.inp` (207 spheres); the HPC checkout `/home/msys/HPC/storage/mechsys` is an older revision of the same branch (HEAD `fb6eee8`) with unrelated untracked diagnostics work and no legacy inputs; no legacy inputs exist in any build/sandbox directory. A date-filtered sweep of all `.inp` files modified 2026-09-01..2026-10-20 found only unrelated `vibrated_shear` project inputs.

**Upstream survey (`Axtal/mechsys`, fetched 2026-10-15; fetch-only):**

- Upstream refs: `main` (`552c02b`), `yintingchang` (`e7cbf3a`, 2024-10-29), and `refs/pull/1/head` = `e4ba163` — our baseline branch is open upstream as PR #1. No other branches or tags.
- `tdem/test_cu_04.cu` has six upstream versions (from `b419503` "first upload" 2024-04-02 through `62279b2` 2025-07-23); **every version reads all parameters from an external `.inp` file**, and no `test_cu_04` input was ever committed. Pickaxe search of all upstream refs for `18600`/`154000`: zero hits. The `yintingchang` variant is also `.inp`-driven.
- `tdem/test_cu_03.cu` has two upstream versions; the physical formulation is unchanged since first upload: `AddVoroPack(-1, 0.1, 20,20,240, 20,20,240, 1.0, false, true, 1000, 0.8)` (implying ~76,800 grains), `dt=1e-5`, `Tf=10` → 1,000,001 steps. `ddeb3ee` (2025-11-27, "addressed memory issues") only changed output cadence (`dtOut=Tf/100`) and memory handling. `tdem/log.txt` is a stale compiler-error log, not benchmark evidence.
- The only upstream "DeepSeek" commit, `6a77203` (2026-10-05, "considerable optimizations carried out with Deepseek Harness"), touches **only the LBM side** (`lib/flbm`, `lib/lbmdem`, `tflbm`, `tlbmdem`) — zero overlap with the DEM performance patch (`CalcCentroids`/`Stamp`/`pRebuildFlag` absent). It is a separate effort by the upstream author, not the recovered October DEM work.
- Our baseline `e4ba163` already contains every upstream change to `test_cu_03.cu`/`test_cu_04.cu` (ddeb3ee and ca7eccd are ancestors). Upstream `main` has 11 newer commits (mechsyscc build fixes, Gmsh packaging, `DEM::Save` friction history, LBM optimizations) — none affect the legacy benchmark formulations.
- **Conclusion:** the "larger particle count / longer simulation time" legacy formulations were never in upstream Git. The inputs lived only on the previous researcher's machine and are currently unrecoverable (`LEGACY_UNAVAILABLE` as file artifacts). Paradoxically, the *upstream default* polyhedron run (Tf=10, 1,000,001 steps) is far *longer* than the historically measured 1001-step run, so an upstream-default reproduction would NOT match the historical measurement window either; the historical 1001-step configuration remains a modified, uncommitted local variant that must be reconstructed and labeled accordingly.

**Historical configuration facts extracted from the primary record:**

| Benchmark | Historical facts |
|---|---|
| S-legacy-small (18.6k) | `test_cu_04`, sphereboxhcp; compression 6.647 s, shear 7.648 s (before change 1); 38 rebuilds averaging ~119.6 ms (pre-change-2); rebuild inner split: CPU search 67-70%, D2H ~15%, H2D 15-18%; Alpha sweep 0.01→0.02: 7.585→5.757 s, 38→17 rebuilds; run continued past iteration 20001; 154k energies bit-identical: 0 / 11.1031 / 51.104 |
| S-legacy-large (154k) | rebuild is 91% of the shear solve; CPU search 62.8%, D2H 14.4%, H2D 22.8% |
| P-legacy-large (77k) | 77,002 particles; 1,815,920 vertices; 1,361,939 edges; 530,981 faces; 403,764 contact pairs; per-step candidates EE 15,992,853 / VF 5,936,551 / FV 5,938,065 / VV 0; **1001 steps**; solve ~197.36 s (197.79/197.34/196.96) → ~197 ms/step; one rebuild 23.6 s (81.2% CInteracton construction, 12.3% stale erase); ListPosPairs peak 85,748,325 (~1.4 GB); final energy 369.835 deterministic over 6 runs |

**Preliminary reconciliation observations (to be resolved by Tasks 2-5):**

1. *Sphere rebuild share:* 38 rebuilds × ~119.6 ms = 4.54 s = **59%** of the reported 7.648 s shear solve, not the reported 84%. Either the 84% used a different window/definition, or rebuild-adjacent work (solve-loop D2H/H2D, map maintenance outside the timed bucket) was included. The Alpha sweep is roughly consistent with ~120 ms/rebuild (21 fewer rebuilds ≈ the 1.83 s saved), so per-rebuild cost and the sweep agree with each other but not with the 84% headline.
2. *Polyhedron step count:* the record's 1001 steps is irreconcilable with current `test_cu_03.cu` defaults (dt=1e-5, Tf=10 → 1,000,001 steps). The historical run therefore used modified, never-committed parameters. A 1001-step reconstruction is possible via the `54574e0` argv parameterization, but timestep/stage equivalence must be argued explicitly or the workload classified below `LEGACY_EXACT`.
3. *Polyhedron particle count:* current `AddVoroPack(-1, 0.1, 20,20,240, 20,20,240, 1.0, false, true, 1000, 0.8)` implies 96,000×0.8 = 76,800 grains, not the recorded 77,002. The 202-grain difference (library version, fraction semantics, or a different recorded run) must be identified empirically before any reproduction claim.

**Workload classification (initial, per `AGENTS.md` §5.1):**

| Benchmark | Input files | Configuration | Initial state | Classification (initial) |
|---|---|---|---|---|
| S-legacy-small | `LEGACY_UNAVAILABLE` | partially recoverable from record | not yet checkable | `LEGACY_UNAVAILABLE` (pending Task 2 reconstruction) |
| S-legacy-large | `LEGACY_UNAVAILABLE` | partially recoverable | not yet checkable | `LEGACY_UNAVAILABLE` (pending) |
| P-legacy-large | `LEGACY_UNAVAILABLE` | step count/defaults conflict noted above | counts checkable against record | `LEGACY_UNAVAILABLE` (pending) |

**Comparison table skeleton (Task 5; fill during P0-L execution):** Measurement | Historical | Exact legacy reproduction | Current P0 — rows: particle count; geometry count; candidate interactions; actual contacts; Verlet distance; rebuild count; average rebuild time; rebuild percentage (84-91% spheres vs measured); GPU kernel percentage; total runtime. Current-P0 column values are in §5.2 (spheres rebuild share 1.3-3.3%).

**Timing decomposition requirements (Task 4):** separate setup/initial-list, force kernels, integration, per-step sync/transfers, CPU list reconstruction, GPU uploads, allocation, finalization; report `f_rebuild = (Σ_k T_rebuild,k) / T_measured_wall` with numerator and denominator over the same interval; >=3 comparable repetitions, interleaved for A/B; never compare initialization-heavy short runs against long steady-state runs without separating components.

**Acceptance (Task 6):** per-workload classification per `AGENTS.md` §5.1; only `LEGACY_EXACT` may be called an exact reproduction. If a full-size benchmark cannot run within resources, preserve the verified configuration, document the limiting resource, and report the incomplete measurement — do not silently reduce problem size.

**Deliverables (Task 7):** machine-readable configuration manifests (input/executable hashes, Git commit, particle/geometry counts, all parameters) stored with raw artifacts under `/home/msys/SIMS/mechsys_p0_baseline/`; completed comparison table; timing decomposition; quantitative discrepancy explanation; final classifications; recommendation for the first optimization milestone.

**Revised milestone sequence:**

| Milestone | Task | Status |
|---|---|---|
| P0 | Initial performance measurements | Complete (§5.2) |
| P0-L | Recover and reproduce exact legacy benchmarks | **Next** |
| P0-R | Reconcile historical and current bottlenecks | Pending P0-L |
| V0 | Complete numerical correctness oracles | Outstanding |
| P1 | Select first optimization from verified bottlenecks | Blocked by P0-R and relevant V0 gates |

## 6. Git/repository topology and record





```text
Original upstream:  https://github.com/Axtal/mechsys
New fork origin:    https://github.com/marcoprevitali/mechsys.git
Fork owner:         marcoprevitali
Original local dir: /home/msys/mechsys (preserved dirty)
New clone dir:      /home/msys/git/mechsys-gpu-opt
Upstream branch:    main (remote HEAD verified by `git ls-remote --symref`)
Original SHA:       e4ba163ec9f32c8bccb0fd8619ba79e000d3d6d8
Imported patch SHA: NOT IMPORTED; preserved artifact SHA256 e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9
Baseline branch:    perf/gpu-baseline at c88dc99f415dbf7b7bc3b1764fdf5506f0d66c9e
Active topic:       perf/p0-instrumentation (P0 measurements + P0-L registration; see `git log` for exact SHAs; branch pushed to origin)
Protection:         `origin` = user's fork; `upstream` fetch-only / push-disabled
```

`F0` evidence:

- Backup: `/home/msys/SIMS/mechsys_gpu_backups/20261015-150003/`.
- Complete local-ref bundle SHA256: `65c154286ff35b8d4fb6d51de0b2c2d662a419b1608fd2815fc8fdeef23f31ec` (`git bundle verify` PASS).
- Reviewed untracked source/docs archive SHA256: `1ff12f3e0c2bc03b3ae210fe0d3d2212b41fdcd6ea9cd15fb22f48fd7c7e061a`.
- Original worktree: seven tracked modifications and nine untracked source/doc files; full inventories are in the backup. Of the five historically reported performance files, only four were dirty and their observed changes were later contact-output, prescribed-wall, ratcheting-counter, and Lees-Edwards edits, not the reported asynchronous rebuild/centroid-cache patch. `lib/lbmdem/Domain.h` was clean.
- Fork proof: authenticated GitHub account `marcoprevitali`; public repository metadata reported `repository_is_fork=true` and parent `Axtal/mechsys`.
- Clone remotes: `origin` fetch/push is the user fork; `upstream` fetch is Axtal and push is the intentionally invalid `PUSH_DISABLED` URL.
- `git apply --check` confirmed that the preserved dirty patch applies to the matching base. It was deliberately not applied to the optimization branch. This is a reviewed non-import decision, not loss of the work; the patch, untracked archive, and Git bundle are preserved externally.

**Import sequence:** archive old `HEAD`/branch/remotes/status; save `git diff HEAD --binary` and untracked inventory **outside both repos**; optionally save an offline bundle of local branches; create a fork via `gh repo fork Axtal/mechsys --clone=false`; clone fork into a **new** directory; verify remote URLs; fetch upstream; create a topic branch at the old base commit **if available**, else stop and plan explicit commit/patch migration; apply backed-up tracked diff only after `git apply --check`; review and copy relevant untracked source/config/docs separately; test; commit changes in coherent branches. Full commands and safety checks: `AGENTS.md` §2.

**Never:** push to `Axtal/mechsys`, rewrite original branch history, `git reset --hard` or `git clean -fd` in the original checkout, force-push shared branches, merge all optimization experiments into one indiscriminate commit, or use `git checkout --` to discard unexplained edits. Do not submit a pull request to upstream without explicit user instruction.

## 7. Decisions, blockers, and re-entry log

| Date | Decision | Evidence | Status |
|---|---|---|---|
| 2026-10-14 | A previous developer tested sorting feature interactions; it did not improve EE/VF/FV kernels | User-supplied performance summary | HISTORICAL_REPORTED |
| 2026-10-14 | Larger uniform `Alpha` substantially reduced sphere runtime | Same summary, one parameter comparison | HISTORICAL_REPORTED; needs sweep |
| 2026-10-15 | Split sphere/polydedra tracks; prioritize actual bottlenecks, not assumed universal AoSoA/compaction speedups | Profiling summary + LAMMPS architecture references | PLAN |
| 2026-10-15 | Treat stale centroid and delayed rebuild as **unresolved** correctness risks | Prior implementation description, source audit pending | BLOCKER FOR ACCEPTING OLD PATCHES |
| 2026-10-15 | Isolate all future work in a user-owned GitHub fork and a new clone | User request | REQUIRED at handoff; superseded by the `F0 PASS` evidence below |
| 2026-10-15 | Preserve but do not import the observed dirty worktree into the GPU-optimization baseline | Binary patch/archive inspection: changes do not match the historical performance patch and include unrelated ongoing work | `F0 PASS`; original work retained externally |
| 2026-10-15 | Use validated fork commit `e4ba163` as the initial baseline rather than fork `main` | Exact old SHA exists in fork; branch is 28 commits ahead of `origin/main` | SOURCE BASE SELECTED; runtime/profile gates still pending |
| 2026-10-15 | Keep delayed rebuild and centroid cache out of the baseline | Source has synchronous displacement check and current geometry; historical variants were not recoverable as a coherent patch | BASELINE SAFE FROM THOSE TWO VARIANTS; historical claims still unresolved |
| 2026-10-15 | Add default-off P0 rebuild instrumentation on its own branch | `sm_86` DEM and LBM-DEM compile; enabled counter smoke; default-off output difference 0.0 | IMPLEMENTED, NOT A SPEEDUP CLAIM |
| 2026-10-15 | Defer baseline timing while the A6000 is occupied | `ratcheting_gpu_v15` at about 66% SM and 79 C during the check | `P0 BLOCKED` for uncontaminated timing |
| 2026-10-15 | A6000 became idle; P0 first measurements taken on registered S-small/S-mid/P-small inputs | §5.2 tables, hashed inputs, nsys reports in `/home/msys/SIMS/mechsys_p0_baseline/` | `P0 FIRST MEASUREMENTS COMPLETE` |
| 2026-10-15 | Historical sphere rebuild dominance (84-91%) does NOT reproduce at registered scales; S-small/S-mid are host-synchronization-bound (GPU idle ~55%) | §5.2 rebuild shares 1.3-3.3% of wall; nsys API/kernel split | MEASURED; needs larger-N reconciliation before S1 |
| 2026-10-15 | Registered P-small polyhedron regime is per-step-transfer-bound (cudaMemcpyAsync ~5/step), not geometry-kernel-bound | §5.2 nsys: 1.6 ms/step GPU vs 27 ms/step wall | MEASURED; needs larger-N reconciliation before P1/P2 |
| 2026-10-15 | Do not start S1 solely from historical percentages; reconcile bottleneck scaling with N first | §5.2 consequences paragraph | PLAN REVISED |
| 2026-10-15 | `P0-L` milestone registered with hard rules (no CUDA algorithm changes; separate dataset provenance; explicit legacy classifications) | User work order; `AGENTS.md` §5.1 | REQUIRED, NEXT |
| 2026-10-15 | Canonical historical record recovered and archived (`DEM_GPU_OPTIMIZATIONS.txt`, SHA256 `a62db594…`); no legacy input files found anywhere on the machine | §5.3 Task-1 first pass | SOURCE VERIFIED |
| 2026-10-15 | Historical record is internally inconsistent on the sphere rebuild share (38×119.6 ms = 59% of shear solve, not 84%) and the polyhedron config (1001 steps and 77,002 particles vs current defaults' 1,000,001 steps and 76,800 grains) | §5.3 preliminary observations | UNRESOLVED — P0-L Tasks 2-5 |
| 2026-10-15 | Upstream surveyed for original legacy formulations: none exist in upstream Git (test_cu_04 always .inp-driven with no committed input; test_cu_03 formulation unchanged since first upload and *longer* than the historical 1001-step run); upstream `6a77203` "Deepseek Harness" commit is LBM-only, unrelated to the DEM patch; baseline already contains all upstream test changes | §5.3 upstream survey | SOURCE VERIFIED |

### Current bounded task (`P0-L`)

1. **Task 2 — configuration recovery:** reconstruct the three legacy configurations from the primary record (`docs/perf/history/DEM_GPU_OPTIMIZATIONS.txt`) plus code reading. For the spheres, identify the `sphereboxhcp` parameters (box, R, fraction, seed, dt, stages, Alpha) that yield exactly 18,600 and 154,000 particles; for polyhedra, resolve the 1001-step and 77,002-particle conflicts against current defaults. Produce machine-readable manifests with all hashes; record every assumption explicitly.
2. **Task 3 — initial-state verification:** run the reconstructed initializations and compare particle/vertex/edge/face counts and candidate/contact counts against the historical reference values; distinguish verified equivalence from unverifiable quantities.
3. **Task 4 — timing reproduction:** run the legacy configurations unchanged (no CUDA algorithm modifications), decompose timings per `AGENTS.md` §5.1, compute `f_rebuild`, and test reproducibility of the 84-91% claim and the 38×119.6 ms arithmetic. >=3 repetitions, interleaved where comparing.
4. **Task 5-7 — comparison, classification, documentation:** complete the Historical vs Legacy-reproduction vs Current-P0 table, assign `LEGACY_*` classifications, explain discrepancies quantitatively, and record the first-optimization recommendation in this file.
5. In parallel where runs are long: continue the outstanding `V0` oracles; keep P0-L artifacts under `/home/msys/SIMS/mechsys_p0_baseline/` with manifests.

**Session log template:**

```text
UTC timestamp:
Agent/model:
Current milestone + PASS / FAIL / BLOCKED / UNRESOLVED:
Fork URL / origin and upstream URL / branch / SHA / dirty status:
Old-checkout SHA + backup location/hash:
Hardware/precision/toolchain:
Tests and raw evidence paths:
Performance results and interleaved-run uncertainty:
Unresolved numerical risks:
Files changed + commits (fork branch only):
Next bounded task:
```
