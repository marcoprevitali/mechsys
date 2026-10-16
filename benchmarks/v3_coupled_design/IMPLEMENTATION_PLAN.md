# Bounded implementation plan — future authorization required

V3-D is **design only**. No production source, guard, solver configuration or
V2 artifact changes are made. Base `2b8d8c335709046e224f4c43aa930144ae6854e7`.
Prerequisites: review [DESIGN_DECISION.md](DESIGN_DECISION.md), the
[complete Scheme A contract](COUPLED_VV_TIME_CONTRACT.md),
[ledger](MOMENTUM_EXCHANGE_LEDGER.md) and [G0–G9 tests](VALIDATION_PLAN.md).
[V2 report](../v2/V2_REPORT.md) remains the standalone reference and coupled
blocker record. A planned patch is not an implementation or a validated result.

## 1. One bounded next milestone: V3-I0, observational exchange audit

**Do not start a general coupled VV rewrite first.** After the user accepts the
design, add default-off observation hooks or a dedicated cell probe to capture
the current **legacy** imprint/collision arrays and stage order without changing
their formulas. Preserve both CPU and GPU original outputs with hooks disabled.

Run a small isolated one-cell/one-particle stencil and a small D3Q15 lattice,
one step, Sc=0/alpha=1/Fconv=1/Gammaf=0/BForce=0; then separately labeled negative cases
for outside-center occupancy, shared ownership, nonunit Fconv and limiter use.
Export f before/after, actual increments, per-cell ownership and J/K. Independent
reference reductions must distinguish exchange, BGK/body force, static boundary
and unexplained increments. Verify torque frames at fixed pose. No fitting or
residual correction, no production VV path and no P2-B.

Required deliverable: source/parameter hashes and compact raw cell ledger,
CPU/GPU cell-coverage verdict, attribution of each failure or an explicit
UNRESOLVED entry. Source hazards in V3-D are not automatically measured causes
of V2 residuals. If the CPU/GPU sphere cutoff discrepancy produces different
cell sets, document and propose a **separate reviewed parity correction**; do
not alter geometry in an instrumentation commit. For shared cells, initial
support must reject; a deterministic winner or multi-particle mixture is a
separate modeling/ownership decision before positive general two-particle tests.

Stop on any unaccounted impulse or occupancy mismatch. Retain the fail-closed
coupled VV guard D:591–594. This milestone alone does not implement Scheme A.

## 2. Subsequent milestones, not automatically authorized

| Milestone | Small patch / source targets | Required exit gate |
|---|---|---|
| I0 instrumentation | benchmark probes and optional read-only hooks around D:813–879/K:407–707 | G1/G2 observed; default-off unchanged, all failures retained |
| I0-P parity/model decisions | separately reviewed CPU/GPU coverage/ownership/unit/limiter corrections if required | independent cell reference passes; accepted supported subset explicit |
| I1 bounded Scheme A harness | additive experimental entry/harness using registered SCDEM plus V2 stage helpers; existing Solve still guarded | A/B/C/D/E-dry, actual-record oracle, one J and one history update |
| I2 scoped runtime integration | explicit default-off coupled-mode dispatch only after I1 review; no automatic legacy flag reinterpretation | F/G/H/I and J within registered support; source regression and scope rejection tests |
| I3 extensions | shared cells, anisotropic gyro, Gammaf, Fconv unit changes, limiter, alternate Bn/multiphase individually | each extension's model decision and independent tests; no omnibus patch |
| R-coupled | versioned full fluid+DEM restart, separate from V2 standalone schema | uninterrupted/restarted fluid/particle/impulse phase validation |
| P2-B | clean explicitly selected VV timing only after relevant correctness closure | original registered workloads/five clean sequential reps, no optimization promotion |

## 3. Required CPU changes for I1/I2

- Separate overlap/Omega preparation from physical force/torque accumulation in
  ImprintLattice (D:336–447). No immediate particle reaction before the collision
  knows the applied solid population increment. Preserve the existing registered
  occupancy proxy and SCDEM operator unless a separate parity patch is approved.
- Collision L:1404–1475 exports solid/bulk/other increments and supports; reduction
  produces world J/K from the same cell/owner snapshot. Store before stream clears
  BForce; alpha!=1 fails for the first supported subset.
- Apply J/K once; use the nonhydrodynamic F/T cache when calling the exact V2
  half-kick/drift/force/final-kick sequence. Forward contact law, Coulomb, tensile
  and activation options explicitly (legacy D:898 does not).
- Respect all-vertex pre-force validity and keep coupling-map reference validity
  independent from DEM resets. Do not rerun Solve/Initialize per timestep;
  that would bootstrap/reconstruct histories and reset counters.
- Expose setup functions with explicit beginning/end time; sample external force
  at both endpoint stages. Keep prescribed wall/support and fluid BC work separate.
- Initial Gv/Gm=0 and isotropic sphere assumptions are checked, not just documented.
  Support for anisotropic caches is a separate scheduling and regression gate.

## 4. Required CUDA changes for I1/I2

- Keep f/f*, rho/u, BForce, gamma/Omega, owner/count, particle x/v/w/Q/vertices,
  persistent Ft/Fr/PrevDelta/flags, nonhydro A/Wdot and J/K on device.
- Split current VC/FC preparation from reaction addition, or write only scratch
  during preparation; the live DPar.F/Flbm and Par.T must not receive J twice.
  A future kernel exports **actual** collision solid increments and cell moments;
  reduce them to a per-particle impulse buffer before the kick.
- Use V2 pVerletStep1/pOrientationUpdate and finalizers with **nonhydro caches**;
  leave torque authoritative on ParticleCU.T. Existing pReset seeds Flbmf, unlike
  CPU Reset; require Flbmf=0 initially and a separate output/support policy later.
- Use narrow UpdateContactsDevicePreForce (M:4167–4198), not the ordinary path
  that uploads stale A/Wdot and recomputes acceleration (M:4201–4272). Rebuild
  coupling-cell tables too when their own validity expires, without resetting
  impulse, pose, half velocities or history state.
- Same-stream ordering establishes preparation -> collision/reduction -> kick
  -> mechanical drift -> validity -> endpoint contact -> final kick. Any future
  multiple streams require events at these edges; no implicit cross-stream order.
- Baseline host displacement/rebuild decision remains; copy a scalar/event when
  needed to select the CPU rebuild, then download only required geometry/history,
  upload changed interaction/map extents and refresh the correct references.
  No asynchronous run-ahead or new GPU neighbor algorithm is authorized.
- Diagnostic array readbacks and reductions are explicitly synchronized. In
  non-diagnostic mode no new per-step host force/count readback is required to
  launch a force kernel: extents live in the existing device auxiliary data.
  Overflow/owner failures may need a checked status scalar; failure cannot be
  hidden to avoid synchronization.
- Own clock/phase changes in the integrator. MaxD currently increments device
  auxiliary time (G:1095–1103); extra midpoint/trial calls cannot be allowed to
  increment physical time. Host aux, fluid aux and outer clocks get one committed
  ordinal, with array-stage tags separate from that integer.

These changes are stage/ownership wiring and explicit compatibility corrections,
not permission to modify standalone contact recurrences or reduce precision.
No CPU-only operation sequence may be accepted and later approximated on CUDA.

## 5. Buffer lifetimes and memory, no performance claim

| Buffer | Size/order | Lifetime / content |
|---|---|---|
| current f and f scratch | existing O(Ncell*Q) FP64 | pre/post collision and streamed roles recorded explicitly; one committed stream |
| raw moments/BForce | existing O(Ncell) | beginning-state moments and current forcing, clear only after ledger capture |
| gamma/Omega and owner/count | O(Ncell*Q) + O(Ncell) | stage-specific occupancy and solid increment provenance; conflicted owners rejected |
| per-cell J/K and ledger terms | O(Nactive cell) or dense diagnostic O(Ncell) | needed until per-particle reduction and independent diagnostic comparison |
| Jp/Kp and applied mask | O(Nparticle) | interval impulse; consumed once, never stored as both old/new VV acceleration |
| Fce/Tce/Ace/Wdotce | O(Nparticle) | nonhydro endpoint state for next step; supports external force sampling |
| contact maps/history/raw device records | existing O(Ncontact/features) | unchanged law/retention semantics, one commit |
| independent coupling reference | O(Nparticle/vertices) plus generation | prevents DEM reset hiding stale particle–cell lists |

B1 additionally needs trial pose/vertices and provisional J/K; discarded collision
scratch can reuse existing Ftemp if no trial stream occurs. C needs repeated
trial rollback and residual buffers; preserve f_n separately if trials stream.
No speedup is
predicted from these costs. No active count is assumed free to transfer to CPU.

## 6. Future coupled checkpoint scope — explicitly not I1

At a selected full joint boundary, identify what must persist:

| State | Persistence / reconstruction rule |
|---|---|
| DEM pose, velocities, IDs/materials/fixities/external loads, contact/feature histories, ce acceleration cache, list references | required; retain the V2 units/frames and no-rebootstrap rule, but extend via a separate coupled schema |
| joint integrator mode/phase and clock ordinals | required; distinguish pre-hydro, impulse-pending, post-kick and completed n+1; checkpoint first only at completed joint boundaries |
| fluid populations and authoritative F/Ftemp role | current post-stream f required; scratch Ftemp can be regenerated only at a phase that guarantees it is dead. Mid-collision/stream restart would require both arrays/roles and is outside first checkpoint scope |
| raw rho/u | derived from f only if raw-moment convention and forcing phase are identical; retain nonderived/force-shifted fields and exact report values if necessary |
| collision law, tau/nu, dx/h, Sc, Bn variant, unit/mass conversion, limiter and BC definitions | required metadata; callbacks/custom kernels need their own validated state or rejection |
| BForce / external forcing schedule / reservoirs | pending force/impulse and callback/controller/BC state required; cleared scratch may be reconstructed only when verified empty at the boundary |
| gamma/Gammaf/Omega, per-cell owners/weights | Gammaf and persistent model state required; gamma may describe the **previous left pose** in A and cannot be relabeled from x_np1. Reconstruct only for the exact named phase; preserve report/diagnostic state if exact boundary inspection requires it |
| particle–cell pair/face maps and reference/generation | topology/IDs/reference validity required or deterministic rebuild proven not to change first resumed force; never reconstruct history by current x alone |
| J/K and consumption state | if pending, require values, geometry/lever/units/time interval and applied mask to prevent duplicate/lost kicks. Completed-boundary checkpoint requires no pending impulse, checked explicitly |
| fluid static masks, boundary transport/support reactions and periodic image conventions | required if persistent; record accumulated conserved quantities and external reservoirs |
| pointers/capacity/allocation and unneeded scratch | derived, not persistent physical identities |

No claim that standalone SaveCheckpoint already captures this. Old geometry
Save/Load semantics stay unchanged; coupled Load remains guarded. A future
restart milestone must compare f, macro fields, histories, physical impulses and
the **first resumed** collision/contact stage without additional integration.

## 7. Review/commit/stop discipline

Instrumentation, diagnosed parity corrections, impulse plumbing, VV stage
algorithm and scoped runtime dispatch are separate reversible commits. Recheck
branch/SHA/status before each commit, preserve failed/raw evidence, push only
origin and keep upstream push-disabled. Never remove the legacy VV guard merely
to compile/run an experiment. Do not expand a rejected-mode list to claim general
C2 closure. Stop for review when cell ownership, physical interior-fluid inertia,
fluid forcing semantics or required accuracy changes the selected model/scope.
