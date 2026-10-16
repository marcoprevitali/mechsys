# AGENTS.md — MechSys GPU DEM optimization

**Applicable to:** the **user-owned fork** of `https://github.com/Axtal/mechsys` created for GPU DEM performance research.
**Primary project record:** [`PROJECT_STATUS.md`](PROJECT_STATUS.md). Read it **first**, each session.
**Expected coding agent:** GLM-5.3 Flash; follow instructions literally, use short scoped experiments, record evidence, and do not infer success from compilation alone.

## 1. Mission, authority, and nonnegotiable rules

Improve **full-simulation GPU throughput** of MechSys DEM without changing its mechanical model. Sphere and polyhedral workloads are separate engineering tracks. Optimizations under consideration: GPU neighbor generation; uniform/adaptive Verlet margins; active-contact compaction; SoA/AoSoA; spatial ordering; particle-centric/warp/pair force ownership; reduction of atomics; improved contact management. **No optimization is pre-approved as faster**.

- The historical DeepSeek summary is **reported evidence, not local verification**. Do not silently equate it to the present checkout's state.
- Keep **FP64** as the only accepted production precision unless the user explicitly authorizes a separate mixed-precision validation program. Prior FP32 attempts changed physics severely.
- **Velocity-Verlet (VV, `UseVelocityVerlet=true`) is the reference integration mode for all new validation, profiling, benchmarks and optimization decisions in this program** (user decision, 2026-10-16). Explicitly select and verify VV; label position-Verlet/leapfrog runs as legacy compatibility or historical controls, never as VV reference evidence. This reference-mode policy does not change the library's backwards-compatible constructor default. Use `test_cu_04 <input> <Nproc> <dthoot> <qin> 1` and verify `DEM_BENCHMARK_INTEGRATOR velocity_verlet=1`; registered-oracle runs must pass `--vv`.
- Preserve contact laws, normal/tangential forces, friction and rolling state, effective radii, contact moment arms, damping, energy work, periodic images, coupled LBM–DEM and restarts.
- Favor independent oracles and minimal reversible experiments. Every performance change has an explicit numerical pass/fail gate and measured **complete simulation** speedup.
- Do not launch unattended massive benchmark campaigns or combine multiple major architectural changes in one unreviewable patch. Small diagnostic tests are encouraged.
- Never claim that the project/fork/commit/test exists unless the relevant command returned success.

## 2. Git isolation and fork creation — FIRST SESSION ONLY (`F0`)

**Why:** the earlier work reportedly modified five files without committing; careless `git checkout`, `git reset`, `git stash`/`pop`, remote changes, or merges could lose work or contaminate other MechSys projects.

### 2.1 Discover original checkout, inspect; do not mutate

1. Find the MechSys checkout actually used for the historical A6000 tests. Example **candidate** `/home/msys/git/mechsys` is not guaranteed to be correct. If several exist, identify the correct one from `mechsyscc`, test paths, `git status`, build configs and file diffs. Do not guess.
2. From the **old** directory run **read-only** commands:

   ```bash
   pwd -P
   git rev-parse --show-toplevel
   git status --porcelain=v1 -uall
   git log -1 --format='%H %ci %s'
   git branch -avv
   git remote -v
   git diff --stat HEAD
   git diff --name-status HEAD
   git ls-files --others --exclude-standard
   ```

3. Identify the exact tracked modifications in `lib/dem/dem.cuh`, `lib/dem/distance.h`, `lib/dem/domain.h`, `lib/dem/interacton.h`, `lib/lbmdem/Domain.h`. Note unexpected local changes, deleted files, and existing user branches; **do not reset them**. Record the original SHA, branch, dirty state and all remote URLs in `PROJECT_STATUS.md`.
4. Create a timestamped **external backup**, e.g. `/home/msys/SIMS/mechsys_gpu_backups/<timestamp>/`, not inside either checkout:

   ```bash
   BACKUP=/home/msys/SIMS/mechsys_gpu_backups/<timestamp>
   mkdir -p "$BACKUP"
   git status --porcelain=v1 -uall > "$BACKUP/original-status.txt"
   git remote -v > "$BACKUP/original-remotes.txt"
   git log -1 --format='%H %ci %s' > "$BACKUP/original-head.txt"
   git diff HEAD --binary > "$BACKUP/tracked-working-tree.patch"
   git diff --cached --binary > "$BACKUP/staged-only.patch"
   git ls-files --others --exclude-standard > "$BACKUP/untracked-paths.txt"
   sha256sum "$BACKUP"/*.patch > "$BACKUP/patch-sha256.txt"
   ```

   Run this from the old checkout. `git diff HEAD --binary` captures staged + unstaged **tracked** changes; untracked files must be examined and copied **separately**, especially input fixtures and documentation. Never automatically commit logs, secrets, credentials, binary builds, large result folders, or copyrighted publisher PDFs. Optionally archive local branch history with `git bundle create ... --all` if there are commits not reachable from upstream. **Do not alter the original checkout or its remotes.**

5. Check backup paths and hashes and keep their location outside Git. If the checkout has untracked source files required for testing, make a reviewed separate archive; do not rely on `git diff` alone.

### 2.2 Fork using GitHub CLI without modifying old remotes

The request authorizes creating a fork under the authenticated user's account; it does **not** authorize pushing to upstream. The following are commands for the user's actual machine, **not statements that have already run**:

```bash
gh auth status
gh api user --jq .login
gh api repos/Axtal/mechsys --jq .default_branch
# Run outside the old checkout:
gh repo fork Axtal/mechsys --clone=false
# Identify the fork actually returned / associated with the authenticated user.
# Example, not a substitute for reading the actual owner:
OWNER="$(gh api user --jq .login)"
gh repo view "$OWNER/mechsys" --json nameWithOwner,isFork,url --jq '{nameWithOwner,isFork,url}'
# Use an UNUSED directory (inspect before choosing):
gh repo clone "$OWNER/mechsys" /home/msys/git/mechsys-gpu-opt
cd /home/msys/git/mechsys-gpu-opt
git remote -v
```

If GitHub reports the fork already exists, **reuse it** after verifying its parent with `gh repo view ... --json parent` (if supported); do not create an unrelated copy with an invented owner. If CLI/authentication is unavailable, do not request credentials in chat; report the exact `F0` blocker and provide the user the standard `gh auth login` step. Do not fall back to creating a new unrelated public GitHub repository without asking. A GitHub fork generally follows GitHub's fork-visibility constraints—review visibility before transferring any nonpublic work.

The new clone **must** have:

```text
origin   = https://github.com/<authenticated-owner>/mechsys(.git) [push and fetch]
upstream = https://github.com/Axtal/mechsys(.git) [fetch only]
```

If `upstream` is absent, add it in the **new clone only**:

```bash
git remote add upstream https://github.com/Axtal/mechsys.git
```

Disable accidental pushing to upstream in the new clone, and prefer explicit remote names for every push:

```bash
git remote set-url --push upstream PUSH_DISABLED
git config --local remote.pushDefault origin
git config --local push.default simple
git remote -v
```

Set upstream fetch branches from upstream only when explicitly needed; no automatic pull/rebase/merge. The `PUSH_DISABLED` URL is an intentional protective invalid push destination, not a fetch URL. Never use `git push upstream`, `git push --mirror`, `git push --all`, a force-push to a shared branch, or `gh pr create -R Axtal/mechsys` unless the user separately requests an upstream contribution.

### 2.3 Establish a feature branch and migrate the old work safely

- Preserve the fork's initial main/default branch as an **integration/reference branch**; create a dedicated branch such as `perf/gpu-baseline` for the imported historic changes and current documents.
- Check whether the original checkout `HEAD` commit is available in the clone: `git cat-file -e <old_sha>^{commit}` (quote carefully in shell). If available, start the import branch **at the matching old SHA** so the dirty patch has its original base. Record how far the imported branch is from the fork default branch.
- If the original SHA is **not** available, or historical edits are already partly present in the fork, **stop automatic importing**. Inspect ancestry, fetch a known local branch explicitly or generate reviewed commits with `git format-patch`, and reconcile duplicate changes carefully. Never force a patch to apply against an unrelated base.
- When the base matches, run `git apply --check "$BACKUP/tracked-working-tree.patch"`; only then `git apply "$BACKUP/tracked-working-tree.patch"` in the **new clone**. If it fails, preserve the patch, inspect rejects and reconcile manually; don't run destructive resets. Empty patches are fine if no tracked modifications existed.
- Copy only reviewed untracked source/config/docs fixtures, separate from build and experimental outputs. Copy these `AGENTS.md` and `PROJECT_STATUS.md` to the fork root (the names are part of the handoff contract).
- Commit the provenance/import changes on `perf/gpu-baseline` in **small, meaningful commits** after passing relevant checks. An unvalidated historical experiment may be committed as an **opt-in** experimental variant, but **not enabled by default** or described as accepted.
- Push with `git push -u origin perf/gpu-baseline` **only after verifying `origin` is the user's fork**. Local commits are preferable to pushing a branch containing large personal fixtures or unexplained changes.
- Consider topic branches such as `perf/sphere-gpu-neighbors`, `perf/poly-feature-screening`, `perf/layout-study` **from the validated baseline branch**. Do not develop every experiment directly on fork `main`.
- When integrating, prefer a reviewed pull request **within the fork** (`feature → fork default/integration branch`) or carefully inspected `git merge --no-ff` after relevant gates PASS. Keep old and current patches traceable. Never merge a known numerical failure merely for performance.
- For upstream updates: `git fetch upstream`, inspect `git log --oneline --left-right ...` and `git diff`; pick a controlled integration point. Never automatically `git pull --rebase`, force-reset to upstream, or rebase a dirty/shared experiment branch. Resolve changes in isolated integration branch and rerun validation.
- Record actual fork URL, SHAs, branches, commit hashes, and backup path in `PROJECT_STATUS.md`. **`F0 PASS` requires evidence of both provenance preservation and correct `origin`/`upstream`.**

## 3. Scope and source-entry points

First inspect local symbols; don't assume public filenames or old line numbers still match:

- `lib/dem/domain.h`: `Solve`, `UpdateContactsDevice`, `UpdateContacts`, `ResetContacts`, `UpLoadDevice`, `DnLoadDevice`, `ResetMaxD`, contact launch sequence.
- `lib/dem/dem.cuh`: `CalcForceVV`, `CalcForceEE`, `CalcForceVF`, `CalcForceFV`, `MaxD`, `CalcCentroids` if historical patch present.
- `lib/dem/distance.h`: `OverlapVF`, `OverlapFV`, `OverlapCentroid` and exact geometry tests.
- `lib/dem/interacton.h`: `CInteracton`, `Stamp`, identity/pair history, `Fnnet`/`Ftnet`, contact feature records.
- `lib/dem/particle.h`: `ParticleCU`, `DynParticleCU`, bounding geometry and update paths.
- `lib/lbmdem/Domain.h`: shared kernel launches, coupling behavior, data lifetime.
- Benchmarks: `tdem/test_cu_04` (spheres) and `tdem/test_cu_03` (polyhedra) where available. Record if inputs/fixtures are missing and never invent results.

Avoid modifying subprojects used for unrelated research, such as the user's granular thermostat or conduction studies, without an explicit request. Use dedicated benchmark outputs outside the source tree or a properly ignored `benchmarks/results/` directory.

## 4. Validation policy — HARD STOP for numerical failures

### 4.1 Before accepting historical changes: `V0`

**V0.1 Device-flag / asynchronous rebuild**: Verify stream ordering, events, pinned memory/asynchronous visibility, sticky flag reset ordering, and max permissible steps of run-ahead. Derive a conservative displacement bound for motions between detection of threshold and execution of the next contact-force kernel using a rebuilt list. Test sudden acceleration, fast intruder, moving walls, periodic crossings, vertex rotations and small `Alpha`. Treat "only four steps" or "energy looked similar" as insufficient. Oracle: at each force-evaluation timestep enumerate geometrically possible pairs on CPU for small controlled cases and require **zero missed pairs**.

**V0.2 Face centroid cache**: Determine whether centroid world coordinates are refreshed each timestep. If not, produce tests comparing the cached rejection predicate against the original exact/current centroid predicate **at each timestep** under translation and rotation near the threshold. Any false rejection is FAIL. Options: compute body-local centroid once and transform by current pose every step, or expand bounds with rigorously tracked centroid displacement. Measure added update cost. Printed equal final energies do **not** prove numerical identity.

**V0.3 Contact history and identities**: Compare canonical unordered physical particle-pair key plus geometry-feature identifiers and periodic image handling. Preserve one state update per physical contact per step; maintain tangential/rolling history across reordering, rebuild, restart and temporary separation per baseline semantics. Validate particle/wall forces/torques, action–reaction and energy-work bookkeeping.

**V0.4 Coupled call paths**: Every shared CUDA kernel signature/interface update must compile and run relevant tests under `lib/lbmdem/Domain.h`, not just standalone DEM.

Do not unilaterally change the contact model to make a test pass. Investigate first and record any baseline defect separately. Large chaotic trajectory divergence is not the primary oracle; prefer stepwise force, history and conservation tests with explicitly justified FP64 tolerances.

### 4.2 For any GPU neighbor-list modification

- At rebuild `t_b`, candidate list **must contain a conservative superset** of all contacts that can arise until the next rebuild. Validate at force-evaluation times; no false negatives or duplicate force contributions.
- Begin with verified uniform `Alpha` semantics; don't assume the same cutoff for spheres and geometric features without reading the implementation.
- Include 3D/periodic cells, boundary particles, free–fixed pairs, moving walls, rotations of polyhedra, triclinic/sheared geometry if supported, and all collision-feature classes.
- Handle capacity counting and overflow **without truncation**. Prefer count/prefix-sum/fill with documented memory limits, or an overflow-safe dynamic expansion path.
- Contact and feature keys must be **stable across storage sorting**. Physical IDs are not array indices; preserve image-code semantics and histories. Zero active contacts, zero candidates, large cell occupancy and restart are required test cases.
- Do not transfer an active-count scalar to CPU to launch a force kernel unless explicitly justified; benchmark extra kernels/buffers rather than hand-waving launch overhead.

### 4.3 For eventual heterogeneous Verlet margins (`X3`)

- Define per-particle **fixed-at-rebuild** allowable displacement `a_i`. Candidate search must conservatively include potential interactions with the corresponding sum of allowances. Validate actual surface/vertex motion since reference state, not just center translation for polyhedra.
- Motion predictors (speed, fluctuating velocity/granular temperature, local shear/mixing or contact turnover) set only the *desired allowance*. They never override the exact geometric validity criterion.
- A delayed rebuild needs additional proved displacement headroom. Verify recheck ordering; if safety cannot be established, disable delayed mode for this implementation.
- Compare against a tuned global `Alpha` baseline, not only the historical `0.01` choice. Adaptive mode must include its own statistics/rebuild decision cost.

## 5. Profiling, metrics and decision criteria (`P0`)

1. Identify actual GPU/SMs, CUDA/driver and compiler (`mechsyscc` flags), precision, source SHA, input/seed, timestep count, CPU thread count, run/output cadence. Historical NVIDIA RTX A6000 numbers are not current facts until reproduced.
2. Profile **complete solve** including initialization, neighbor rebuild CPU time, D2H/H2D, host stalls/synchronization, kernels and wall-clock. Use matching execution windows; reconcile historical 63.5 s profiled force kernels vs ~197 s polyhedral run before using percentages.
3. For sphere benchmark, report candidate particle pairs, active contacts, `Alpha`, rebuild counts, per-rebuild CPU maps/allocations/transfers, force-kernel and all-in timestep costs.
4. For polyhedral benchmark, instrument independent atomic or device counters for `N_candidates_EE/VF/FV`, `N_pass_first_bound`, `N_pass_exact_geometry`, `N_positive_overlap`, `N_force_evaluated`, with a clear denominator, per-step or sampled over a representative window. Do not call 27.9M tests "actual contacts".
5. Gather `nsys`/`ncu` evidence where available: memory sectors/cache, occupancy, register usage, branch-lane utilization, instruction mix, atomics, warp stalls. Separate total GPU kernel time from full run time.
6. For small performance differences use interleaved A/B measurements on identical input windows. >=3 paired repetitions for exploratory, >=5 for final. Report paired effect sizes, range/dispersion, and thermal/clock variance. A failed/unstable numerical gate invalidates performance promotion.
7. Cost model: report `T_total`, not just `T_kernel`. Include preprocessing, sorting/compaction, memory copy, extra launch, state conversion and list rebuild overhead. Negative results are reportable outcomes.

**Do not set a universal mandatory speedup percentage.** Promote only measured improvements whose confidence and maintenance complexity justify them; small (<~3%) wins require extra scrutiny and repeated independent runs. Never invent new benchmarks from theoretical peak bandwidth or atomic counts.

### 5.1 Legacy benchmark verification (`P0-L`) — mandatory before optimization selection

**Objective:** reconstruct and reproduce the original MechSys CUDA benchmarks used in the previous GPU performance study (`S-legacy-small` = `tdem/test_cu_04` sphereboxhcp 18,600 particles; `S-legacy-large` = same at 154,000; `P-legacy-large` = `tdem/test_cu_03` Voronoi column collapse 77,002 particles), and determine whether discrepancies between historical and current P0 measurements arise from simulation configuration, particle counts, execution stages, code versions, or profiling methodology.

**Hard rules:**

- Do **not modify CUDA algorithms** during `P0-L`. The milestone is strictly about reproducing and understanding existing performance results. Any source change is limited to benchmark harness/input parameterization that provably preserves default behavior.
- The historical experiments and the current P0 measurements remain **separate datasets, each with its own provenance**. Never merge, average, or relabel one as the other.
- Do **not** substitute approximately equivalent particle counts or newly constructed geometries and label them as legacy reproductions. If original inputs or initialization procedures cannot be recovered, report `LEGACY_UNAVAILABLE` (or the lower classification) explicitly; never silently reconstruct from assumptions.
- Historical performance numbers must not be used to justify any future GPU optimization unless the supporting workload is classified `LEGACY_EXACT`, or `LEGACY_EQUIVALENT` with every difference from the historical state documented in `PROJECT_STATUS.md`.
- Only `LEGACY_EXACT` results may be described as "exact reproductions" in any document or claim.

**Classification (per workload):**

- `LEGACY_EXACT` — original configuration recovered and verified, including initial state where reference data permit.
- `LEGACY_EQUIVALENT` — relevant numerical configuration reproduced, but exact initial state or software environment cannot be independently verified.
- `LEGACY_APPROXIMATE` — reconstructed workload differs in documented ways.
- `LEGACY_UNAVAILABLE` — insufficient information or resources to reproduce the simulation.

**Configuration-equivalence checklist (verify and record all twelve):** (1) exact particle count after initialization; (2) particle sizes, densities, material properties; (3) initial coordinates and geometries; (4) contact stiffnesses, damping, friction; (5) boundary conditions and periodic dimensions; (6) timestep and total timestep count; (7) Verlet distance (`Alpha`) and reconstruction settings; (8) precision (FP64) and compiler options; (9) random seeds and generation procedures; (10) compression/shear/column-collapse execution stages; (11) initial contact-list construction and restart conditions; (12) GPU model and source revision.

**Verification gates:**

- *Initial physical state (Task 3):* compare generated assemblies against the historical reference (spheres: count, packing fraction, size distribution, domain, initial coordinates where available, initial candidate/contact counts; polyhedra: particle/vertex/edge/face counts plus post-build candidate feature counts). Matching particle count alone does **not** pass this gate. Distinguish verified equivalence from quantities that cannot be checked.
- *Timing decomposition (Task 4):* separate setup/initial-list generation, force kernels, integration, per-step synchronization and transfers, CPU list reconstruction, GPU uploads, allocation, and finalization, with numerator and denominator over the same interval. Report `f_rebuild = (sum_k T_rebuild,k) / T_measured_wall` and explicitly test whether the historical 84-91% rebuild contribution is reproducible, including the internal consistency of ~38 rebuilds at ~119.6 ms against the reported total runtime. Use >=3 comparable repetitions, interleaved for A/B; never compare an initialization-heavy short run against a long steady-state run without separating components.
- *Comparison table (Task 5):* maintain the Historical vs Exact-legacy-reproduction vs Current-P0 table in `PROJECT_STATUS.md`, explaining discrepancies quantitatively and attributing them to workload size, stages, contact density, code differences, or profiling method.
- *Machine-readable manifest (Task 2):* for each workload record input-file hashes, executable hash, Git commit, particle/geometry counts, and all simulation parameters; store it with the raw artifacts.
- If the original full-size benchmark cannot run within available resources, preserve the verified configuration, document the limiting resource, and report the incomplete measurement. Do not silently reduce the problem size.

**Milestone order:** `P0` (initial measurements) → `P0-L` (legacy reproduction) → `P0-R` (reconcile historical vs current bottlenecks) → `V0` completion → `P1` (first optimization selection, blocked by `P0-R` and relevant `V0` gates).

### 5.2 Measurement-environment rules (added during P0-R)

- Before any timed run, record GPU utilization/temperature and the system load; identify competing CPU processes (`ps aux --sort=-%cpu`). Validate each rep's `/usr/bin/time` "Percent of CPU" against the expected value for its Nproc; exclude and re-run contaminated reps, and record the exclusion and its cause.
- On a multi-agent machine, verify immediately before EVERY commit that HEAD, the branch name, and the working tree are what you expect (concurrent sessions may switch branches, delete branches, or edit shared files). Push protected work promptly; never assume an uncommitted working tree will still be yours an hour later.
- Diagnostic instrumentation must be default-off, env-gated, add no host synchronization in production mode, and never alter forces, histories, or ordering. Verify the default-off binary reproduces reference outputs before collecting timing data.
- `ncu` is unavailable on this host: occupancy/register-level claims are NOT_MEASURED unless a supported profiler metric exists; do not fabricate them.

## 6. Work sequencing for this agent



**Session 1 is strictly scoped to `F0` → `V0` investigation → `P0` baseline.** Produce a fork and new clone if GitHub authentication and repository access permit, preserve old edits, verify current code, and run only minimal baseline/validation tests. If `V0` FAIL, fix/disable that specific unsafe change in a separate reviewable patch before benchmarking it as accepted. Do **not** start S2/P2/P3/X1/X3 on the same session just because the plan exists.

**After `P0`, the order is `P0-L` → `P0-R` → `V0` completion → `P1`;** see §5.1 for the mandatory legacy-verification rules. Historical measurements must not justify optimization work until their workloads are classified `LEGACY_EXACT` or `LEGACY_EQUIVALENT` with documented differences.

Next work orders after current evidence supports them:

- **P0-L** (legacy reproduction): recover/verify the exact historical benchmark configurations (18.6k/154k spheres, 77k polyhedra), reproduce their timing decomposition, classify per §5.1, and reconcile with current P0 measurements. **No CUDA algorithm changes.**
- **P0-R** (reconciliation): quantitatively explain historical-vs-current discrepancy sources (workload size, stages, contact density, code versions, profiling method) using only P0-L-classified evidence.

- **S1** (spheres): systematically sweep uniform skin with fixed physical inputs and full runtime; document validity and tradeoff with candidate count.
- **S2** (spheres): **GPU-resident full rebuild**, not merely "device cell list + CPU objects"; binning + candidate pairs + history migration, then optional device-side rebuild control. Keep fallback CPU mode. Pilot spheres; add polyhedra only after detailed design.
- **S3** (spheres): compare existing one-contact/thread vs central-particle local accumulation and cooperative warp-per-particle; keep history once per physical pair, ensure neighbor reaction forces/torques accounted for. LAMMPS KOKKOS is an algorithmic reference only.
- **P1** (polyhedra): collect stage-by-stage geometric rejection counts and `ncu` bottleneck evidence.
- **P2** (polyhedra): conservative bounding/hierarchical feature screening to **reduce number of tested feature pairs**; prove no missing contacts.
- **P3** (polyhedra): if P1 shows sufficient expensive surviving work and divergence, benchmark compacted active lists (CUB select or warp append, without CPU sync) against fused contact resolution. Include index-only and geometry-cache variants as measurements support.
- **P4** (polyhedra): reduce `CInteracton`/feature-construction and memory allocator pressure; profile within old 19.2 s bucket before claiming allocation is the cause.
- **X1**: compare only a few hot fields as AoS vs SoA vs AoSoA tiles 8/16/32/64; independently test spatial particle ordering and neighbor list layout. Historical **feature-record sorting** failed: do not repeat it in isolation.
- **X2**: benchmark atomics, pair/warp grouped force accumulation, CSR gather only if indicated by evidence. A simple full-neighbor duplicated friction computation is **not safe** without single history ownership.
- **X3**: heterogeneous `a_i`, motion metrics, temperature/shear/mixing predictions, benchmarked against tuned uniform skin; only after S2 provides safe GPU list semantics.
- **Z0**: select per-workload winners; maintain simpler baseline when alternative speedup is ambiguous.

Do not swap scheduling based on intuition alone. If a later profile changes bottlenecks, update `PROJECT_STATUS.md` and justify the revised order with data.

## 7. Branch, commit, and merge discipline after fork

- Write scoped branches (`perf/<clear-milestone>`) from a **verified, recorded base**. Keep each experiment reversible or behind a default-off flag; do not drag unrelated scripts into commits.
- Make changes in small commits: instrumentation; numerical tests; algorithm; cleanup/performance tuning. Record benchmark SHA and experiment inputs. Run `git diff --check` and review `git status` before commit. Do not silently stage large binary outputs.
- `git fetch upstream` is permitted. Incorporation of upstream commits requires a reviewed integration branch, conflict inspection and rerun numerical tests. **No implicit merges, rebase of dirty/shared branches, force pushes, or automated upstream PR.**
- `origin` must always be the user-owned fork; `upstream` must be fetch-only/push-disabled. Recheck remotes before each push. `git push origin <branch>` is the only permitted push target.
- If an optimization fails numerical gates, leave it unmerged and disabled, and report the reason. If it fails performance thresholds, document and cleanly revert on its experiment branch, retaining benchmark reports in Git only if they are lightweight.
- Check project scope before editing any separate MechSys checkout or any other simulation project. Never alter unrelated experiments or scientific outputs to manufacture speedup.

## 8. Documentation and handoff requirements

Update `PROJECT_STATUS.md` **each substantive session** with a concise, auditable status table and a re-entry note:

```text
Date / model:
Milestone and PASS / FAIL / BLOCKED / UNRESOLVED:
Fork URL, origin/upstream URLs, worktree path, active branch, exact SHA, dirty state:
Original checkout SHA and backup path/hash:
Changed files / commits (origin only):
Exact test and benchmark commands / input hashes / logs:
Numerical oracle outcomes and tolerances:
Timings, repeated-run uncertainty, candidate/rebuild statistics:
Unresolved safety or performance issues:
One next bounded task:
```

A status is `PASS` only when the required commands completed, numerical evidence is present, and source/provenance is reproducible. For inaccessible hardware, missing fixtures, CUDA failures, or unavailable GitHub credentials, say `BLOCKED` with a concrete reason and preserve completed local documentation work. **Never claim to have forked or committed until remote verification succeeds.**

## 9. External references (read only as needed)

- Upstream code: https://github.com/Axtal/mechsys
- LAMMPS-KOKKOS performance paper: https://arxiv.org/html/2508.13523
- LAMMPS granular and neighbor implementations: https://github.com/lammps/lammps/tree/develop/src/KOKKOS
- Neighbor-list engineering: https://docs.lammps.org/Developer_par_neigh.html
- KOKKOS backend tradeoffs: https://docs.lammps.org/Speed_kokkos.html
- GitHub CLI fork behavior (check before changing remotes): https://cli.github.com/manual/gh_repo_fork

**The user's 2026-10-14 DeepSeek performance summary is the canonical historical benchmark record until a new, reproducible baseline supersedes it. Cite its exact environment and do not recast its measurements as newly measured.**
