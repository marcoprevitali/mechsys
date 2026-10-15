# MechSys GPU DEM optimization — PROJECT_STATUS.md

**As-of:** 2026-10-15
**State:** `F0 PASS` / `V0` SOURCE AUDIT IN PROGRESS / `P0` NOT YET MEASURED
**Next authorized work:** finish the bounded `V0` source/runtime audit, then establish the reproducible `P0` baseline. **Do not begin a broad rewrite.**
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
Feature branch:     perf/gpu-baseline (created at the exact original SHA)
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

### Current bounded task

1. Finish the `V0` source/runtime audit on the isolated `e4ba163` baseline, including contact-history and coupled CUDA paths.
2. Add only the instrumentation needed for a reproducible `P0` profile, default-off and separately reviewable.
3. Obtain uncontaminated complete-solve timings and rebuild-stage measurements when the RTX A6000 is idle.
4. Use the measured profile to choose one bounded next experiment; do not start S2/P2/P3/X1/X3 from historical percentages alone.

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
