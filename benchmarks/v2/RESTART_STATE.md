# V2 restart contract and state audit

Reference: `73466999e0601a083fb9718281d88d161c75231d`, FP64 VV.

## R1: legacy semantics and recorded counterexample

`Domain::Save/Load` are partial particle/geometry snapshots, not a full dynamic
continuation contract. Save stores geometry, selected particle kinematics,
mass/inertia, tags and periodic bounds. It does not store Time, iteration,
material/contact parameters, fixities, forcing, VV accelerations, list reference
vertices or live histories. Its interaction-output block is commented out.
Load creates particles and assigns fresh storage indices. The test_write/read
examples use this format for geometry round trips; test_cu_04 loads geometry and
then supplies material/loading. Neither API promises a checkpoint phase/version.
Therefore retain these APIs unchanged, and add explicitly named full-state APIs.

`legacy_restart.cu` runs sustained friction/rolling two-sphere VV dynamics and
compares 51 uninterrupted steps against 50 steps, Save, Load, and one more step.
It explicitly restores the omitted material/loading and time before continuation,
so the recorded force discontinuity is not attributed to those omissions alone.
At step 50: tangential=0.0040573895336843526 N, rolling=0.00061162062601771846 N.
Immediately after Load: no contact records, stored Time=0, but position, velocity,
angular velocity and quaternion differences are exactly zero. The first force
at the restart pose has tangential=7.867181479634245e-5 N, rolling=1.1977661567416122e-5 N,
normal=0.94255683272356783 N (normal agrees at that pose).
After the first post-drift force: tangential error=0.0039786913008329865 N;
rolling error=0.00059964253486766779 N. Assertion exits **1** as required.
Raw negative evidence: `/tmp/mechsys-v2.g2YtyY/r1-run/`; generated before any
checkpoint correction. No previous successful milestone is replaced.

## R2: state needed at a completed VV timestep

| Scope | Persistent/required state | Units/frame; reconstruction rules |
|---|---|---|
| Domain | Time, iteration, Dt, phase, integrator, law and Coulomb/tensile/activation switches; Alpha/Beta; periodic bounds; energy/work accounting | Completed full-step VV only. A fresh Solve bootstrap evaluates forces and advances histories, so must be skipped on explicit restart. No hidden extra timestep |
| Particle identity | Immutable lifetime ID distinct from Tag and current Index | Tags may repeat; Index is a storage address. Checkpoint endpoint references use lifetime IDs and validate uniqueness. Preserve serialized particle ordering; sorting/topology mutation is not introduced |
| Particle mechanics | All material parameters, mass/volume, principal inertia, pose, v/w, F/T, applied Ff/Tf/Flbmf, Flbm, fixities/flags; VV A/Wdot and auxiliary v_half/w_half/wa/xb/wb | x/v/F in world coordinates; w/T/inertia/angular acceleration in body coordinates. Q maps body to world. Force/acceleration from previous evaluation is needed for the next half-step |
| Rigid geometry/list validity | Current vertices, edge/face connectivity, reference vertices since list construction, active interaction/feature lists, candidate particle pairs | Local feature IDs are immutable connectivity indices, not particle-array indices. Restore references and active lists without a rebuild/history update; otherwise rebuild timing and separation-retention semantics may change |
| Linear sphere | Fdvv, Fdr, PrevDelta, InContact; actual contact coefficients/overrides | Fdvv is global tangential displacement (m); Fdr is global rolling force (N). GPU Ft=Kt*Fdvv; GPU Fr=Fdr. On force evaluation each history is projected into the current contact tangent plane |
| Hertz sphere | Same state; tangential stiffness Kt*sqrt(positive overlap) | GPU Ft is a force; restoring displacement from Ft uses the previous overlap, not the new overlap. Rolling history is already force. Activation needs signed PrevDelta/InContact even after separation |
| Generic feature contact | Fdee/Fdvf/Fdfv/Fdvt/Fdtv/Fdvc/Fdcv maps, active EE/VF/FV/VT/TV/VC/CV lists | Map values are world tangent displacement. Keys combine ordered local feature IDs. World normals and contact points are derived from current geometry at each force evaluation; torque is transformed back to the body frame |
| MostlySpheres shortcut | FricSpheres, RollSpheres, PrevSphereDelta and candidate-pair list | Separate CPU pathway, not interchangeable with CInteractonSphere maps. Must serialize explicitly or reject this mode; never silently reset it |
| Cohesive bonds | Bond endpoints and face IDs, valid/broken flag, An, L0, s1/t1/s2/t2, coefficients, forces, geometry-dependent constructor state | BInteracton is distinct from CInteracton. Not reconstructible just from current positions. Must serialize explicitly or fail closed; GPU reference support is not established |
| Per-contact diagnostics | Normal/tangential/dashpot totals, energy/work increments, forces/torques | Derived outputs, retained at the boundary so inspection/reports don't change on load. Not re-evaluated during restoration |
| Periodicity | Bounds/Per, free/fixed semantics, current geometry and reference vertices | Baseline uses instantaneous minimum images, not a persistent explicit image-code field. Preserve exactly that behavior. Do not invent new image histories or transfer histories to a different ordered pair |
| Custom/coupled models | Callback-owned state, overridden kernels, fluid distributions, particle-cell mapping and fluid forces | Standalone DEM checkpoint cannot claim these. Must reject unsupported custom paths. Coupled checkpoint is a separate contract and test |

Normals, distances, exact geometric contact points, linked-cell arrays, CUDA
addresses, allocation capacities and raw pointers are derived, not permanent IDs.
CUDA accelerations/torques must be read from actual device arrays at save time;
ordinary DnLoadDevice leaves host torque and A/Wdot stale. CPU/GPU feature
summation ordering may differ; exact restored boundary values and short FP64
comparisons are primary, not long chaotic trajectory identity.

## Explicit full-state checkpoint design

Use the existing Boost property-tree JSON facility, not a general serialization
framework. A separately named `.vv.json` file carries magic, schema version,
IEEE-754 binary64 precision, source backend, completed-step phase, counts,
persistent IDs and all supported state. Doubles are formatted at 17 significant
digits for binary64 round trips. Validate metadata, counts, identifiers,
connectivity and history key bounds; reject malformed/incompatible files.
Legacy HDF5 stays readable only by legacy Load; full-state Load must reject it
with a clear error, never silently reinterpret it as history-safe.

Checkpoint support must fail closed for a constitutive/custom mode not yet
implemented. This audit documents required bond/shortcut/coupled state, not
evidence that those modes are checkpoint-safe. Acceptance must distinguish
implemented scopes and tested scopes.
