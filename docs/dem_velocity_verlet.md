# DEM integration, sphere contact controls, and contact output

`DEM::Domain` retains the legacy integration default. Select mechanical
velocity Verlet explicitly with `domain.UseVelocityVerlet = true` on CPU or
CUDA. Translation and body-frame rotation use half kicks, a geometry update,
and a final kick. Neighbor validity is checked after the drift and before
contact forces; a CUDA rebuild preserves the current particle state,
accelerations, and surviving tangential/rolling histories. Initial acceleration
uses a zero-duration force evaluation, so initialization consumes no contact
history step. Calculations use
FP64 when `A_MAKE_USE_GPU_DOUBLE=ON` (the existing build default).

Upstream's cached feature-force kernels, combined legacy movement kernel,
block displacement maximum, and build configuration remain available. The
VV path refreshes the rotation caches before the cached feature kernels run.
The legacy coupled solver rejects the standalone VV selector instead of
silently running a different integrator.

## Sphere contact controls

These controls apply to linear and Hertz sphere contacts on CPU and CUDA.
They do not select new polyhedral contact laws.

| Domain member | Default | Meaning |
| --- | --- | --- |
| `SphereCoulombMode` | `0` | Mode 0 caps elastic tangential force using elastic normal force and retains the tangential dashpot. |
| `SphereCoulombMode = 1` | opt-in | Same elastic cap, with the tangential dashpot disabled during sliding. |
| `SphereCoulombMode = 2` | opt-in | Caps total tangential force using total normal force; stores the corresponding elastic history. |
| `SphereTensileCutoff` | `false` | Clamps a tensile elastic-plus-dashpot normal result to zero. |
| `SphereFirstContactCorrection` | `false` | Scales the first tangential increment by the fraction of the step spent in contact, interpolating between previous and current signed overlap. |

The cutoff's reported normal dashpot component includes the clamp adjustment:
elastic plus dashpot reconstructs the normal force actually applied. In mode
2 the elastic tangential component can oppose the dashpot; their sum is the
capped force. The optional onset correction estimates an activation fraction;
it is not an exact collision-time solver. Energy diagnostics follow the
selected force decomposition. The two-sphere example accepts these settings
in `tdem/test_2spheres.inp`; its CPU and CUDA targets share one source.

## HDF5 and XDMF contact output

`WriteBF` exports a particle-pair row when there is an active overlapping
feature **or any nonzero contact-force component**, including tangential,
dashpot, or custom thermostat force. An overlapping contact remains visible
when its resultant force is zero. A separated candidate without a force is
omitted. Existing dataset names and float32 visualization precision remain
unchanged; solver precision is independent of visualization precision.

| Dataset | Meaning |
| --- | --- |
| `Normal`, `Tangential` | Elastic normal and tangential contact force, summed over active features. |
| `DashpotForceNormal`, `DashpotForceTangential` | Normal and tangential dashpot contributions. |
| `Rolling` | Sphere rolling-resistance force history; zero for nonspherical rows when a mixed output contains this dataset. |
| `NormalOverlap` | Maximum positive active feature overlap for the pair; sphere overlap is radius sum minus separation. Zero for force-only rows. |
| `TangentialOverlap` | Sphere tangential displacement history; zero for nonspherical pairs, which have multiple feature histories. |
| `ID1`, `ID2`, `Position`, `Branch` | Existing pair identification and display geometry. |

All new fields have matching XDMF dataset references. Polyhedral
`NormalOverlap` is a maximum, not a center-distance estimate or an average.
Custom CUDA force kernels that replace the built-in kernels must maintain
the common contact count and overlap fields to supply geometric-only rows.
`RecordContactOverlap` provides that bookkeeping without changing forces.

## Coupled VV: existing experimental API

The separate `LBMDEM::Experimental::Benchmark::Session` API is opt-in through
`MECHSYS_EXPERIMENTAL_BENCHMARK_COUPLING`; the example target is built only
with `A_WITH_EXPERIMENTAL_VV_COUPLING=ON`. Include
`mechsys/lbmdem/experimental/benchmark_coupling.h`, select
`Selection::ImplicitVV`, set `DEMDOM.UseVelocityVerlet=true`, and supply a
finite `max_intervals` before initializing and advancing the session.
`tlbmdem/tlbmdem_cu_benchmark.cu` is the complete usage example.

This implementation combines mechanical VV with implicit rigid-body
momentum exchange, retaining physical particle mass and inertia. Opposite
particle impulses are computed from the actual fluid population increments.
The supported configuration is FP64 CUDA, smooth single-fluid D3Q15,
canonical spheres, free or fully prescribed bodies, and the original sphere
contact-law subset. Its guards reject unsupported combinations. It includes
the previously developed sphere/grid occupancy calculation and optional
compensated density summation. Coupled restart, partial constraints,
prescribed spin, multiple fluids, and general polyhedral coupling are not
supported by this API. Ordinary `LBMDEM::Domain::Solve` retains its upstream
legacy algorithm. The experimental session downloads particle/fluid snapshots;
call `DEMDOM.DnLoadDevice(1,true)` before `DEMDOM.WriteBF(...)` when current
contact diagnostics are required from that session.

Incoming fluid populations and entry geometry are still used. Mechanical VV
does **not** make the complete coupling second order: the composition is
conservatively described as first order. Prior restricted validation does
not establish general continuum accuracy, universal stability, or a speedup.
The publication integration does not reopen or extend that physical study.

## Additional integration support

Quaternion helpers, Hertz force/displacement history conversion, preserved
prescribed-velocity position history, and pre-force rebuild state handling
are required by these paths. The explicit, versioned standalone VV
`SaveCheckpoint`/`LoadCheckpoint` API and persistent particle IDs accompany
the imported validated VV implementation. Legacy HDF5 `Save`/`Load` retains
upstream's history serialization; coupled checkpoint continuation is rejected.
No performance experiment, mixed-precision path, unfinished application
driver, or private evidence package is part of this contribution.

## Example applications

Three complete drivers exercise the optional integration and contact paths.
They are ordinary example programs, not regression tests, and they are built by
default with the other `tdem` targets.

| Target | Source / input | Purpose |
| --- | --- | --- |
| `PID_v2` | `tdem/PID_v2.cpp`, `tdem/test_pid_v2.inp` | Wall-particle servo that compresses a box to a target pressure and then shears it at constant axial wall velocity. Uses velocity Verlet and Coulomb mode 2. |
| `TX_PID_periodic` / `TX_PID_periodic_gpu` | `tdem/TX_PID_periodic.{cpp,cu}`, `tdem/test_tx_pid_periodic.inp` | Same PID workflow driven through the periodic cell instead of walls: the stress is measured from the contact virial and the servo resizes `Xmin`/`Xmax`/`Per`. The GPU variant reduces the virial on the device. |
| `shearbox_LE_const_vol` | `tdem/shearbox_LE_const_vol.cu`, `tdem/test_shearbox_LE.inp` | Constant-volume three-phase periodic shearbox with Lees-Edwards kinematics. It owns its step loop and supplies the Lees-Edwards branch vector, force kernels and reset through `Domain`'s existing function pointers, so no Lees-Edwards support is required inside the library. |

All PID drivers select velocity Verlet explicitly. The shearbox uses legacy
position Verlet during compression and velocity Verlet during shear; its local
shear loop preserves contact histories and checks candidate validity after the
drift and before forces. Nothing here changes a library default. `TX_PID_periodic` and
`TX_PID_periodic_gpu` share the same physics but are separate sources, so the
CPU and GPU builds can be compared directly. The shearbox example in
`tdem/test_shearbox_LE.inp` is a small, quick configuration (1188 spheres); the
solvers read every physical parameter from the input file, so larger
production boxes only need a different `.inp`.

## Selecting the integrator in the CUDA examples


The four CUDA example drivers take the integrator as an optional trailing
argument, so the same binary runs both schemes and prints the selection it
actually used.  Position Verlet remains the default, matching the library.

| Driver | Invocation |
| --- | --- |
| `tdem/test_cu_01` | `test_cu_01 [Nproc] [final time] [integrator]` |
| `tdem/test_cu_02` | `test_cu_02 [Nproc] [final time] [integrator]` |
| `tdem/test_cu_03` | `test_cu_03 [Nproc] [Alpha] [Nthread] [final time] [integrator]` |
| `tdem/test_cu_04` | `test_cu_04 <input> [Nproc] [dthoot] [qin] [integrator]` |

`integrator` is `0` for position Verlet and `1` for velocity Verlet, and every
run prints `DEM_BENCHMARK_INTEGRATOR velocity_verlet=<0|1>` before solving.  The
existing arguments keep their positions and meanings, so previous command lines
behave exactly as before.  Tests 1 and 2 also accept a final time so a
comparison can be shortened without editing the source.

## Bounded regression checks

Configure the usual dependencies and set
`A_WITH_DEM_CONTACT_REGRESSIONS=ON` and, for the coupling smoke test,
`A_WITH_EXPERIMENTAL_VV_COUPLING=ON`. Build the `dem_test_*` targets in
`tests/dem_contact`, then run:

```sh
ctest --test-dir build -R '^dem_' --output-on-failure
python3 tests/dem_contact/check_exports.py build/tests/dem_contact/contact_cpu
python3 tests/dem_contact/check_exports.py build/tests/dem_contact/contact_gpu
python3 tests/dem_contact/check_histories.py build/tests/dem_contact fresh-history-output
```

The analytic contact test covers both laws, all three Coulomb modes,
tensile cutoff, activation correction, force decomposition, action/reaction,
and CPU/CUDA agreement. The VV test checks fast contact formation, repeated
rebuild reference resets, preserved GPU state/history, and vertex rotation.
The coupling smoke checks three tiny fixtures against fixed mass/momentum
budgets. Two-step CPU/CUDA checks also run ordinary legacy coupled Solve,
including its entry without standalone VV acceleration initialization. The history probe supports short CPU/CUDA comparisons, feature
oracles, and full-step checkpoint continuation. Export checks require Python
with `h5py` and `numpy`. These are bounded regressions, not a full workload
or scientific-accuracy certification.

## Custom CPU contact compatibility and example verification

The original four-argument virtual `Interacton::CalcForce(dt, Per, iter, law)`
remains the extension point for custom CPU interactions. The overload accepting
sphere options sets a scoped per-interaction context and dispatches through that
original virtual method. Existing four-argument overrides keep receiving solver
calls; options are restored after a return or exception. Builtin sphere contacts
consume the options, while other interactions can retain their existing laws.
This preserves source overrides; CUDA structures have changed, so rebuild all
code sharing these headers and device buffers together.

The optional regression suite also exercises the real periodic PID callbacks
and the shearbox's custom force kernels and physical-step helper. These checks
cover total contact stress, zero-duration initialization, history-preserving
rebuilds, fast post-drift contact formation, shear-image motion and periodic
wrapping. Both custom shearbox laws export overlap/count bookkeeping and force
components that reconstruct the applied force, including the linear tensile
clamp. The shearbox retains its existing custom friction laws, including their
retained tangential/rolling force histories during a temporary gap. Rebuilds
migrate those forces by pair identity; the Hertz case does not convert through
zero stiffness when separated.

After configuring a build with both regression/coupling options above, run:

```sh
python3 scripts/verify_dem_contribution.py --build build --output fresh-verification
```

The verifier builds the required targets, rejects a build configured for another
checkout, checks each return code and integrator banner, and records source,
input and binary hashes with individual logs and a final `SUMMARY.json` verdict.
It runs all bounded regressions, exports, history/restart comparisons, legacy
save/load, all four CUDA examples in both integration modes, and all four new
application targets. Default application inputs use documented smaller windows
or boxes, recorded alongside their hashes; `--full-examples` uses the checked-in
application configurations. Output directories must be new and existing evidence
is never deleted. Configure the normal library dependencies beforehand; the
verifier does not borrow paths from unrelated projects or make timing claims.
