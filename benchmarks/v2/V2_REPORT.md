# V2 — VV restart and reference validation

2026-10-16, Codex. **Overall PARTIAL, not V2 complete.** The user explicitly
selected: record the coupled VV blocker and design that scheme next. No coupled
time-centering scheme or performance optimization is implemented here.

| Gate | Verdict | Evidence / scope |
|---|---|---|
| R1 | PASS | Legacy Save/Load loses nonzero tangent/rolling history; expected exit 1 recorded before correction in `results_r1/` |
| R2 | PASS | [RESTART_STATE.md](RESTART_STATE.md): required units, frames, IDs, derived state and unsupported modes |
| R3 | PASS, bounded support | Explicit version-1 FP64 full-step same-backend checkpoint; legacy Save/Load unchanged; unsupported modes fail closed |
| R4 | PASS, registered suite | 100 uninterrupted/restarted comparisons, all bitwise identical; full-step force/history boundary included |
| C1 | PASS, registered sphere laws | Linear/Hertz, Gn/Gt zero or positive, 38 main CPU/GPU comparisons; independent force/history/energy-work recurrence |
| C2 | BLOCKED | Actual coupled runtime has no VV sequence; CPU/GPU now reject VV instead of silently using legacy integration. User deferred scheme design |
| C3 | PASS, bounded physical scope | Six deterministic linear convex-feature fixtures, 12 bitwise restarts and six physical CPU/GPU comparisons; independent force-time geometry and negative control |
| P2-B1 / B3 | NOT_RUN | Coupled correctness unresolved; no five-repetition clean VV performance baseline |
| P2-B2 | PASS for correctness runs | Persistent reduction off except one explicitly labeled legacy V1 compatibility probe; no run-ahead, centroid cache, compaction or layout variant |

R3 is **not** a claim that every historical DEM constitutive mode can restart.
Unsupported BInteractons, MostlySpheres, torus/cylinder geometry, callback-owned
state/custom kernels and coupled fluid state are rejected. Cross-backend loading,
arbitrary sorting/topology edits and new periodic conventions are not supported.
See the precise API contract in RESTART_STATE.md. Coulomb mode 0 is the validated
configuration. Generic wall/Hertz behavior is not added or claimed.

## Repository and implementation

- Fork: `https://github.com/marcoprevitali/mechsys`, parent `Axtal/mechsys` verified.
- Base: `73466999e0601a083fb9718281d88d161c75231d`,
  `validation/vv-reference-history` (preserved clean).
- Persistent clone: `/home/msys/git/mechsys-v2-restart`.
- Branch: `validation/v2-restart-coupled`; no integration/default-branch merge.
- R1/state-audit commit: `9f45398`; checkpoint implementation: `91dc185`;
  coupled guard/legacy startup: `8402d38`; validation harness: `88cdf55`.
  Exact implementation commits: `91dc1852ec8e5d2e536bef8f80a085ade2855e76`
  and `8402d38a3d940f1e1839d65e0012f205897dd140`.
  Zero-candidate probe: `9e66212caec11207c0997b0c374c1eb38fa069ee`.
  The final evidence/documentation commit follows these; use `git rev-parse HEAD`.
- `lib/dem/checkpoint.h`: separate JSON schema/version/precision/phase and record
  validation, stable lifetime particle IDs and local-feature identities, exact
  history/force/acceleration/list-reference restoration, no-replace publication.
- `lib/dem/domain.h`: one-shot continuation skips Initialize/initial force/list
  reconstruction; default-off post-drift/pre-force diagnostic hook.
- `lib/dem/particle.h`: lifetime ID and deterministic initialization of unused wa.
- `lib/lbmdem/Domain.h`: fail-closed VV guard; allocate shared acceleration arrays
  needed by legacy upload and read back final GPU state for the final report.
  These compatibility fixes do not create a coupled VV algorithm.

No feature-list construction, contact-force formula or production precision is
changed. Existing VV reference policy in AGENTS.md is retained; the constructor
default remains false for backward compatibility. Every new reference fixture
explicitly selects VV. The diagnostic hook adds no host synchronization when null.

## Numerical evidence

FP64 CPU and CUDA, Nproc=1 in new deterministic fixtures, dt=2e-5. CPU/GPU gates:
`abs(error) <= 1e-10 + 1e-9*max(abs(a),abs(b))` for finite scalar state, exact IDs,
list sizes and coverage. This accommodates FP64 reductions/geometry ordering and
is far below force scales (~0.5–2 N in polyhedral fixtures). All within-backend
restart comparisons also check binary64 bits; observed maximum error is zero.
This is bounded evidence, not a guarantee of long chaotic bitwise trajectories.

| Canonical run directory | Restart checks | CPU/GPU checks |
|---|---:|---:|
| `closure-matrix` | 76 | 38 |
| `rebuild-before` (step 4) | 2 | 1 |
| `rebuild-after` (step 5) | 2 | 1 |
| `separated-restart` (step 200) | 8 | 4 |
| `poly-closure` | 12 | 6 |
| Total | **100 bitwise PASS** | **50 physical PASS** |

Main cases: sustained tangent/rolling contact, loading reversal, actual Coulomb
sliding (nonzero friction work), separation/recontact, periodic crossing, moving
wall (linear), three simultaneous spheres, normal collision and oblique collision.
Linear and Hertz spheres run both undamped and with positive Gn=3/Gt=2. R=0.1,
rho=1, Kn=1000; Kt=20 linear and 400 Hertz (nu=0.25); mu=0.4, beta=0.3, eta=0.2.
Alpha=0.001. Hertz damping uses its existing law, not linear reduced-mass scaling.

Independent Python audit: **72 reference runs, 668,272 scalar checks PASS**,
max error `6.650235917504688e-14`. Recomputes material reductions, normals,
half-step velocities, tangent and rolling recurrences/caps, particle F/T, elastic
energy, viscous work and friction work without importing solver code/effective
coefficients. Skips bootstrap frame 0 and the externally overwritten loading
reversal frame 75; recurrence resumes at 76. Does not claim a separate total
mechanical-energy conservation proof for the rolling model. Main comparisons
still include all state/report frames and the saved/loaded boundary.

Polyhedral fixtures explicitly use zero-angle/fixed-axis constructors (the
default null axis otherwise randomly rotates even at angle zero). Finite
sphere/cube VF and reversed FV, four crossing rod EE contacts, translating and
rotating rods, separation/recontact rods, and periodic sphere/cube motion.
Prescribed velocities/rotations keep the geometry deterministic; Alpha=0.0001.
Force-time independent point/polygon and segment geometry checks actual uploaded
EE/VF/FV records on GPU and active CPU records. Per backend: **2,100 checks**,
EE=3,716, VF=600, FV=300; zero missing/duplicates. Eight first-force analytical
normal checks pass (0.5 N VF/FV, 2 N total four-edge contacts). Removing an actual
positive uploaded feature produces `reference=1 missing=1`, exit 1 as required.
Rod contact transitions match: creation 91, separation 310, recontact 491; restart
350 has zero contacts (one broad-phase candidate) and continues bitwise. A
separate one-sphere checkpoint fixture covers zero contacts **and** zero candidates.
Other fixtures restart
with nonzero feature history. Rotation checks use all vertices, not centers.

**Storage qualification:** strict CPU/GPU map equality fails at candidate-only
steps in the separation fixture: CUDA materializes four exactly-zero history
slots, CPU has no entries. Retain `poly_strict_storage_failure.json` and the raw
failed run. Physical comparisons omit **only exact zero entries**, never a small
nonzero displacement; tolerances and every other field remain unchanged. Strict
storage results remain visible inside the final physical-comparison result.
Restart comparisons do not normalize anything. No production history semantics
were changed to make this pass.

30 malformed-format/metadata/ID/count/history/backend/precision and overwrite
checks pass, including legacy HDF5 rejection and unchanged input hashes.
Two additional one-sphere CPU/GPU zero-candidate restart controls pass: positions,
velocities, rotation, forces, accelerations and time are bitwise exact, and the
entire final checkpoint records equal the uninterrupted records.
Existing V1 CPU/GPU reference probes pass (including separately labeled
persistent-reduction compatibility control). The five registered VV candidate
scenarios pass with unchanged input hashes: 56,405 checks / 5,419,450 reference
contacts, zero missing/duplicates/image errors. Results are archived separately,
never used as performance data.

## Coupled runtime blocker and preserved failures

Actual `LBMDEM::Solve`, 12^3 D3Q15 cells, dx=0.1, dt=1e-4, two spheres, five steps.
The reference coupled source ignores DEMDOM.UseVelocityVerlet on both backends.
CPU vv=0 and vv=1 follow the same legacy path. The fast case has post-drift
overlap `0.0054470335296184502` and requires ~5.447 N at VV force time, but actual
particle contact contribution `F-Ff-Flbm` is zero. A newly reconstructed host
CInteracton can misleadingly report ~5.447 N after the step; it is not the force
that was applied. The first pilot's exit 0 reflected that defective test check,
not a coupled VV PASS. Preserve that original result and the corrected diagnosis.

Original GPU runs all SIGSEGV (-11): GDB identifies shared DEM.UpLoadDevice
reading empty A/Wdot arrays. After the scoped allocation correction, CPU/GPU
legacy controls complete; VV requests fail explicitly before stepping, exit 1.
Final legacy fluid masses: CPU 1.7279999999999918, GPU 1.7279999999999889;
exchange residual norm CPU ~1.18e-15, GPU ~2.14e-7; final particle velocities
differ ~4.5e-4. These are **diagnostics, not coupled numerical acceptance**.
Fluid time-centering, momentum exchange and a coupled restart contract remain
unvalidated. User choice: record blocker; design coupled VV next.

Preserved exploratory attempts: `matrix-first` failed because the test-driver
reversed stale GPU host velocity (fixed by current-device download in setup);
`poly-pilot` used unintended random orientations/excessive overlap (invalid
fixtures, fixed in harness only); `poly-registered` strict zero-slot map failure;
`coupled-runs` original crash/ignored-VV evidence. No failed evidence is deleted.

## Reproduction and provenance

Compact raw-derived results/build manifests/hashes: `results/`. Full logs,
checkpoints, failed attempts, build logs and executables:
`/home/msys/SIMS/mechsys_v2_validation/20261016-v2-standalone/`.
Original execution root was `/tmp/mechsys-v2.g2YtyY`; preserve that path in raw
commands rather than rewriting provenance. The durable archive mirrors it except
the temporary Git worktree and intermediate .o objects. Source is in this branch.
Archive copy verified: 1,712 files / 406,225,404 bytes matched their source hashes;
inventory digest is recorded in `results/archive_verification.json`.

Measured hardware: RTX A6000, UUID `GPU-8cfc4ebf-51b9-f72f-6d58-98b94dbdf5de`,
driver 595.84; CUDA 12.6.85, sm_86; G++ 13.3.0, -O3, C++17/OpenMP. Build manifests
contain full compile/link flags and executable/source/header hashes. Some builds
preceded commits: recorded then-HEAD alone is insufficient. `results/index.json`
verifies all six final library header hashes against the committed source.

```sh
python3 benchmarks/v2/build.py --source benchmarks/v2/reference_suite.cu --output /tmp/v2-build
python3 benchmarks/v2/run_suite.py --build /tmp/v2-build --output /tmp/v2-spheres
python3 benchmarks/v2/independent_spheres.py --runs /tmp/v2-spheres --output /tmp/v2-independent.json
python3 benchmarks/v2/run_suite.py --build /tmp/v2-build --output /tmp/v2-poly --cases 11 12 13 14 15 16 --laws 0 --damping 0
python3 benchmarks/v2/audit_features.py --matrix /tmp/v2-poly --binary /tmp/v2-build/cuda --output /tmp/v2-features
python3 benchmarks/v2/invalid_checkpoints.py --build /tmp/v2-build --valid /tmp/v2-spheres --legacy /home/msys/SIMS/mechsys_v2_validation/20261016-v2-standalone/r1-run/legacy.hdf5 --output /tmp/v2-invalid
# Before/after rebuild; repeat with --restart-step 5 and a fresh output directory:
python3 benchmarks/v2/run_suite.py --build /tmp/v2-build --output /tmp/v2-before --cases 0 --laws 0 --damping 0 --restart-step 4
python3 benchmarks/v2/run_suite.py --build /tmp/v2-build --output /tmp/v2-separated --cases 2 --restart-step 200
python3 benchmarks/v2/build.py --source benchmarks/v2/coupled_runtime.cu --output /tmp/v2-coupled
/tmp/v2-coupled/cpu 0 0
/tmp/v2-coupled/cuda 0 0
# Explicit unsupported VV controls must exit 1, not be called numerical PASS:
/tmp/v2-coupled/cpu 1 0
/tmp/v2-coupled/cuda 1 0
```

The builder reuses `/tmp/mechsys_v1_build` response files by default; pass
`--reference-build /home/msys/SIMS/mechsys_v2_validation/20261016-v2-standalone/toolchain`
to use their archived copies (installed third-party libraries still required).
Alternatively use an equivalent configured CMake build. Archived manifests
retain the exact original response-file paths/commands. R1 command is recorded
in its build manifest; its expected failure remains with legacy Save/Load.

Original checkout `/home/msys/mechsys` remained READ ONLY: original HEAD
`e4ba163ec9f32c8bccb0fd8619ba79e000d3d6d8`, tracked-diff SHA256 unchanged
`e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9`, status inventory
unchanged. Original F0 backup remains `/home/msys/SIMS/mechsys_gpu_backups/20261015-150003/`.
Prior reference clone remains clean at 7346699. No other campaign or clone edited.

**Next bounded milestone:** design and review a coupled VV fluid/particle
time-centering contract with independent exchange/conservation and force-time
candidate oracles, before implementing it. Coupled restart remains separate.
Only after the relevant correctness gates close, register/run P2-B. The historical
polyhedral feature-count discrepancy is still a separate unresolved study.
