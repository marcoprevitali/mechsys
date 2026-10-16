# Proposed coupled time-level contract: Scheme A, explicit impulse then VV

**DESIGN PROPOSAL, NOT IMPLEMENTED OR VALIDATED.** Base
`2b8d8c335709046e224f4c43aa930144ae6854e7`; existing coupled guard stays enabled.
Recommendation rationale: [DESIGN_DECISION.md](DESIGN_DECISION.md).
Sources: coupled order D:798–951 and standalone VV M:720–887,977–1065,
G:800–952, P:776–856, defined in the [source audit](CURRENT_COUPLED_SEQUENCE.md).
Preserve the [V2 standalone checkpoint and history contract](../v2/RESTART_STATE.md)
and [V2 numerical evidence](../v2/V2_REPORT.md); they are not coupled evidence.

## 1. Scope and declared levels

`t_n`, `t_half=t_n+h/2`, `t_np1=t_n+h`. Common physical unit system, FP64,
one DEM timestep per one LBM collision/stream. Initial executable subset:
D3Q15, Nl=1, smooth Bn, Sc=0, alpha=1, Fconv=1, Gammaf=0, no Shan–Chen/multiphase
forces, fluid BForce=0, Gv=Gm=0, unchanged connectivity/order, isotropic-inertia spheres and
prescribed non-imprinted DEM walls. Linear/Hertz sphere kernels/options must
match the corresponding V2 reference. No custom kernels/torus/bonds/MostlySpheres.
Fail explicitly on a positive-occupancy cell claimed by more than one moving
particle until its ownership/mixture law is separately selected and validated.
This restriction is substantive, not general multi-particle hydrodynamic support.

All force-time geometry (including prescribed walls) must be current and use
the selected periodic image. Fixed/moving particle components receive support
impulses in the ledger. Fluid static walls and imposed BCs have separate reaction
and flux terms. Further geometry, forcing and multiparticle support requires
additional gates, not an assertion that a sphere oracle covers it.

At the committed entry boundary:

| Quantity | Contract |
|---|---|
| x_n,v_n,omega_n,Q_n | synchronized full-step particle pose and velocities; omega in body frame, Q maps body to world |
| f_n,rho_n,u_raw,n | post-stream/pre-collision populations and their raw moments at t_n; no automatic half-force shift |
| H_n | committed V2 contact histories, physical/feature IDs and list references |
| Fc_n,Tc_n | retained endpoint-geometry contact outputs from the preceding V2 contact evaluation; damping used its V2 half-step velocities, so these are not newly evaluated F(x_n,v_n) |
| Fext_n,Text_n | declared application force / body-frame torque at t_n; gravity belongs here, not in fluid exchange |
| A_ce,n,Wdot_ce,n | nonhydrodynamic acceleration caches used by the V2 half-kick; initial isotropic/Gv=Gm=0 subset makes their force-to-acceleration interpretation unambiguous |
| Fh_n | optional raw left-state imprint diagnostic, evaluated on f_n,x_n,v_n,Q_n; not yet the accepted reaction if collision modifies its increment |
| Fh_half,Fh_np1 | **not available** in Scheme A; neither is invented by copying Fh_n |
| Jp_h[n,np1],Kp_h[n,np1] | not yet available; produced from this interval's actual solid collision increment |

History seeding at initialization reproduces V2 exactly: constructors may call
CalcForce(0), then standalone bootstrap calls CalcForce(h) once at initial
geometry. Count that as the existing **bootstrap convention**, not an extra
coupled timestep. Thereafter one history commit per step. No second bootstrap
on continuation; coupled checkpoint continuation itself remains unsupported.

## 2. Complete timestep, one physical advance

The diagram is operator ordering, not two advances of physical time:

```text
committed n
  -> H_h: geometry at n; ONE fluid collision -> ONE stream; obtain Jp_h
  -> instantaneous particle exchange kick at fixed x_n,Q_n
  -> D_VV,h: contact half-kick -> full drift/rotation -> validity ->
             ONE endpoint contact/history update -> final half-kick
  -> commit all systems at n+1
```

H_h advances the fluid while particle geometry is frozen; D_VV,h advances the
mechanical part while fluid is frozen. This is an explicitly **first-order
partitioned composition**, not two time intervals h+h. Intermediate states are
operator states, not synchronized physical observations.

### A0. Snapshot, external data and list preconditions

Read committed x_n,Q_n,v_n,omega_n,H_n, caches and f_n. Sample Fext_n/Text_n from
the declared time/geometry function, stage fluid BForce/boundary populations at
t_n, and establish particle–cell validity on x_n,Q_n **before imprint**.
Prescribed discontinuities happen at declared step boundaries and their impulse
is logged. Initial force functions are time/position prescribed, not unspecified
velocity-dependent callbacks. For continuous loading, the prior endpoint's
Fext_n equals this beginning sample; replacing an external component must never
advance H_n or replace Fc_n with a newly history-advancing call.

### A1. Reset only coupling scratch, select/validate cell ownership

Clear gamma/Omega/reaction and ledger scratch without touching H_n, Fc_n or
A_ce/Wdot_ce. Compute overlap and surface velocity
`v_s,n=v_n+R(Q_n)omega_n cross r_n` from entry geometry. Build Omega(f_n,rho_n,v_s,n)
and B(gamma_n,tau0). Assert one owner per positive-coupling cell and independent
cell-coverage completeness. No physical particle force is accumulated yet;
the old ImprintLattice side effect on F/T must be separated in a future patch.

### A2. One fluid collision, exchange reduction, stream and moments

From f_n perform the existing registered SCDEM collision exactly once, keeping
its fluid relaxation, solid increment and other/boundary increments separate.
For each cell export the solid population increment **actually applied** and
derive Jp_h and Kp_h with the [ledger](MOMENTUM_EXCHANGE_LEDGER.md).
Alpha other than 1 is an explicit unsupported/failure result in the first
experiment, not ignored; later limiter support must use its actual increments.

Collision -> F/Ftemp swap -> one stream -> swap -> raw moment refresh gives
`f_np1^H,rho_np1^H,u_raw,np1^H`. These are provisional joint-system endpoint
buffers while particles still have x_n. Clear BForce/Omega only after their
ledger values have been captured. Do not recompute Omega from f_np1 and apply a
second particle reaction. Record exactly one collision/stream ordinal.

### A3. Apply each interval hydrodynamic impulse once

At unchanged x_n,Q_n:

`v_n^H = v_n + P_free Jp_h/m`,
`omega_n^H = omega_n + P_rot I^-1 R(Q_n)^T Kp_h,world`.

For isotropic I this maps the exchange spin impulse directly; record constrained
components as support reactions. This state is a left-operator kick result,
**not** v_np1 or a measured v_half. Hydrodynamic impulse is never copied into
both old and new VV acceleration caches. Flbm output is the tagged **interval
equivalent reaction** Jp_h/h; it is not a second force to integrate.

### A4. Mechanical VV half-kicks and geometry

With nonhydrodynamic cached acceleration only:

`v_half^A = v_n^H + (h/2) A_ce,n`,
`omega_half^A = omega_n^H + (h/2) Wdot_ce,n`,
`x_np1 = x_n + h v_half^A`,
`Q_np1 = normalize(Q_n * Exp_body(h omega_half^A))`.

Translate and rotate **all vertices** with the same x/Q operations as V2.
The superscript A matters: this is the mechanical VV auxiliary at t_half for
the split problem, not a proven centered full-coupled velocity. Scheme A's
position error due to the left hydrodynamic kick is intentional first-order
splitting error, to be quantified by refinement rather than hidden.

For general anisotropic inertia the future extension must specify gyro evaluation
and preserve body/world transformations. The CPU half-rotation currently
recomputes gyro from w while GPU uses cached Wdot (P:813–837 vs G:843–853,939–951).
Do not assume these match after a fluid kick. One possible extension recomputes
the nonhydrodynamic Euler acceleration on both backends at omega_n^H without
history advancement, but that changes acceleration scheduling and requires an
explicit zero-fluid compatibility decision. It is **not silently supported** by
this initial isotropic contract; rotating-sphere tests still exercise Q frames.

### A5. Pre-force validity and one committed contact update

On x_np1,Q_np1 compute max **surface/vertex** displacement since each list's
reference. If it reaches Alpha, perform the V1 narrow history-preserving contact
rebuild before force evaluation. Do not use ordinary UpdateContactsDevice here:
it overwrites state/A/Wdot and recomputes acceleration. Coupling-cell lists have
their own reference/generation; refreshing the DEM reference must not mark stale
particle–cell pairs valid. Rebuild them at A0 or preserve the union criterion
until both reference generations have actually been rebuilt.

Run the independent actual-record contact oracle on this geometry. Reset only
endpoint nonhydrodynamic F/T scratch; sample Fext_np1/Text_np1 (world torques, if
provided, are transformed using **Q_np1**). Evaluate the unchanged contact laws
once using x_np1,Q_np1,v_half^A,omega_half^A, h and committed H_n. Commit
`H_np1`, Fc_np1,Tc_np1 and work increments **once**, including separation flags
and baseline retention/deletion semantics. No hydrodynamic reaction enters this
contact force kernel or its acceleration cache.

### A6. Mechanical final half-kick and joint commit

`A_ce,np1 = (Fc_np1+Fext_np1)/m` in the initial no-global-drag subset,
`v_np1 = v_half^A + (h/2) A_ce,np1`.
Use the corresponding isotropic body torque for Wdot_ce,np1 and omega_np1.
Retain the normal V2 prescribed-component handling and support ledger.
Commit particle state/H/cache plus the A2 fluid endpoint, then advance the one
authoritative step ordinal/physical time to n+1. Mirror clocks explicitly;
do not let trial MaxD/macroscopic helper calls advance time. Reusing MaxD's
current hidden auxiliary increment needs a deliberate ordinal ownership wrapper.

Outputs must identify the phase and separate `Fc_np1`, external force, actual
exchange impulses and `Flbm_interval=Jp_h/h`. An optional mixed equivalent
`Fc_np1+Fext_np1+Jp_h/h` is **not** an endpoint force. CPU VV helpers must read a
nonhydrodynamic F/T cache, not an output sum accidentally including hydro.

## 3. Momentum, accuracy and limiting cases

For free components, with initial Gv/Gm=0,

`m (v_np1-v_n) = Jp_h + (h/2)(Fc_n+Fext_n+Fc_np1+Fext_np1)`.

Action/reaction at both contact endpoints cancels the contact sum; shared solid
increments cancel the fluid exchange algebraically. Boundary/external/limiter/
fluid-relaxation terms stay separate in the ledger. This derivation is not a
measured full coupled conservation result, nor a claim about physical added mass.

Hydro disabled: Jp_h=Kp_h=0 and the mechanical sequence is the V2 reference,
including bootstrap/history/force-time semantics. No particles: H_h reduces to
the registered uncoupled single-component LBM update and DEM work is skipped.
Test these **actual operation paths**, not final printed energies alone.

Smooth, non-stiff, consistently refined problems are expected to show first-order
**coupling** error at best. For the elementary force Fh, left impulse then drift
gives x increment `h v_n+h² Fh/m`; exact constant-force motion has coefficient
1/2, an O(h²) local position error. VV's mechanical order cannot remove it.
LBM forcing/occupancy, contact events and stiff interface response can dominate;
no global second-order result or unconditional stability is asserted.

## Contact-history commit contract

Preserve H:625–687, update H:681–936 and M:2891–2994 exactly, not a new contact law:

- At A0–A4 no history increment, projection, cap, deletion or separation update.
  Read-only hydro predictors in alternate schemes cannot call live CalcForce.
- At A5, after geometry/list validity: tangential displacement and rolling force
  advance once by h, project into the current tangent plane and undergo the
  existing Coulomb/rolling caps; PrevDelta/InContact follow the current overlap.
- On retained separated sphere records, tangent/activation reset per baseline;
  **do not add a new rolling reset**. A record leaving the candidate/list support
  is deleted only by the existing rebuild semantics. Generic feature maps keep
  their baseline rules, including exact-zero versus absent bookkeeping from V2.
- Rebuild is not a history timestep. New-record constructors' dt=0 work is not a
  committed finite increment. Match existing activation/bootstrap policy.
- A future trial contact evaluation must copy/restore Ft/Fr or displacement,
  PrevDelta/InContact/vt_prev, all feature maps, live list identity and retention
  state, particle/common force/torque/work arrays, gyro/cache data and trial list
  references/periodic images. Never advance the live maps and attempt to undo
  only the displacement afterward. Whole-step commit is transactional.
- No trial/corrector in A; B/C require scratch histories and one final commit.
  Restart-like state capture for tests must not rebootstrap. Actual coupled
  restart remains a separate future contract, not standalone LoadCheckpoint.

Implementation changes and buffering are specified in
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md); all required acceptance tests
are in [VALIDATION_PLAN.md](VALIDATION_PLAN.md).
