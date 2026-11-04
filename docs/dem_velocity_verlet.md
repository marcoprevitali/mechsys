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
budgets. The history probe supports short CPU/CUDA comparisons, feature
oracles, and full-step checkpoint continuation. Export checks require Python
with `h5py` and `numpy`. These are bounded regressions, not a full workload
or scientific-accuracy certification.
