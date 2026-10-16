# Independent validation specification (A–J), not executed tests

V3-D design only, base `2b8d8c335709046e224f4c43aa930144ae6854e7`.
Every new case/gate below is **NOT_RUN**. Preserve the existing
[V2 report](../v2/V2_REPORT.md), [matrix](../v2/results/standalone.json),
[independent checks](../v2/results/independent_spheres.json) and raw failed coupled
evidence. Source anchors: D:336–447,450–552,798–951; K:407–707; M:834–887,
977–1065,4167–4198, in [CURRENT_COUPLED_SEQUENCE.md](CURRENT_COUPLED_SEQUENCE.md).
No V2 success is promoted to coupled acceptance by this plan.

## Common execution and evidence protocol

Use an isolated future implementation branch, explicit coupled mode/phase marker,
FP64, one collision/stream ordinal per timestep, fixed seed/geometry and small
inputs. Start with D3Q15/Nl=1, smooth Bn, Sc=0, alpha=1, Fconv=1, Gammaf=0,
fluid BForce=0, Gv=Gm=0 and isotropic spheres. Nonzero fluid-body forcing is first
an observational ledger test, not initially enabled physical forcing support.
Log all effective parameters, compiler/GPU, source
SHA/diff, executable/input hashes, timestep and all clock copies. Unsupported
shared ownership/nonunit conversions/limiting/multiphase fail explicitly until
their gates are authorized. Tests are sequential diagnostics, never P2-B data.

Capture pre-imprint f/moments/particle pose and surface velocities, every actual
owner/gamma/B/Omega, pre/post collision populations and solid/bulk/other increments,
impulse reduction results, pre/post particle kick, pre-force contact records,
endpoint state and work/energy. Read actual GPU ParticleCU.T, A/Wdot and dynamic
contact records; ordinary host reports are insufficient. Boundary callbacks
receive a declared phase/time and may not rely on a report-triggered download.

Use an independent scalar implementation for population moments/equilibrium and
force/torque ledgers, not the same compiled collision helper as an oracle.
Round-trip FP64 values at 17 digits; perform reference sums in long double or
exact-decimal reductions, retaining individual increments. Also retain failed
attempts and distinguish an expected-negative process exit from a physical PASS.

## Force-time candidate and cell-mapping oracles

At **each actual contact-force kernel/call**, after drift and any narrow rebuild,
read the geometry/velocity phase and exact launch extents/record identities that
will be consumed. Enumerate independent sphere/finite-plane or bounded convex
feature contacts at that geometry; canonical lifetime particle IDs, immutable
local features and selected periodic image identify one physical contribution.
Check `N_missing=0`, `N_duplicate=0`, `N_bad_image=0` exactly. Force values/torques
must also follow the recorded geometry. Do not use host maps rebuilt after the
step as evidence of applied force. Record vertex motion including rotation and
fixed/moving walls, not only center displacement.

Independently enumerate all particle–cell geometric intersections at the imprint
pose. For each, compute the **existing edge-coverage proxy** separately from the
exact intersection test; a positive proxy must be covered by the actual PaCeV/
PaCe/PaCeF arrays used by VC/FC. Exact-volume/proxy disagreement is a separate
model-resolution statistic, not automatically a missing candidate. Test partial
cells whose centers lie outside a sphere, periodic images, pure rotation, and
movement between list generations. Compare CPU/GPU gamma/B/Omega before comparing
net forces; a net cancellation can conceal different cells.

Negative controls must remove and duplicate an **actual uploaded** record/extent,
alter an image/free-fixed flag, and inject a stale coupling-cell generation.
Each must terminate before the affected force/imprint is used. Reuse V2 feature
oracle independence; do not assume its sphere oracle covers particle–cell lists.

## Numerical tolerances and acceptance levels

1. IDs, counts, ordinals, phase tags, history-commit count and unsupported-mode
   rejection: exact. Zero-hydro within-backend restart/step ordering should also
   check bits where it uses the unchanged V2 path, but not require bitwise
   CPU/GPU reductions.
2. Reused V2 physical fixtures keep their existing FP64 gate
   `abs(error)<=1e-10+1e-9*max(abs(values))` in their recorded unit system. Keep
   exact-zero/absent feature storage qualifications; never discard a nonzero
   history under a new “smallness” threshold.
3. Cell exchange identity: epsilon=2^-52. Let S_cell be the sum of absolute
   pre/post population momentum contributions and explicit increments, and
   J_ref a declared physical impulse scale from rho_ref, volume and U_ref.
   Initial budget is `128 epsilon S_cell + 1e-12 J_ref`; Q<=27. Test bulk/solid/
   boundary decomposition separately, not just their cancelling total.
4. Global ledger: sum cell budgets, add the documented accumulation bound
   `gamma_m sum|J|`, `gamma_m=m epsilon/(1-m epsilon)`, for actual particle
   contributor counts, plus pairwise/extended reference reduction error. Report
   the bound and measured residual both in physical units and normalized by
   problem J_ref. If the bound exceeds 1e-8 of problem J_ref, the test is
   ill-conditioned for this gate: use a better-scaled/higher-precision reference
   or mark unresolved, **do not relax acceptance to the observed residual**.
5. Fixed-pose **exchange** angular impulse gets the corresponding lever-scaled
   roundoff budget. Full rigid-body step angular drift, time error, occupancy
   discretization and continuum drag error are separate convergence tests, not
   mislabeled roundoff. Initial isotropic bodies simplify this separation.

Constants are prospective engineering targets, not fitted to a V2 run. Gate
review must verify their operation/error budget on the registered fixture before
running an implementation comparison. Preserve any inadequate budget as a failed
specification rather than altering it silently after seeing results.

## Test A — no particles

- Small periodic D3Q15 lattice, e.g. 16³, positive equilibrium rho=1, BForce=0,
  then a smooth shear wave `u_x=U sin(2 pi y/L)` with U/c<=0.01. Same dx,h,nu,
  tau,Sc and population initialization on uncoupled FLBM and the coupled mode.
- Compare every f/rho/u after each collision/stream; one stream ordinal and no
  invalid zero-particle launches. Mass/raw momentum satisfy the ledger.
- Independent continuum wave decay `U(t)=U0 exp(-nu k² t)` diagnoses fluid
  discretization separately from direct uncoupled equality.
- Failure: extra collision/swap, different forcing, stale macros or counter
  side effects. Source: L:2376–2567 vs D:853–951/F:746–792.

## Test B — particles, hydrodynamic coupling disabled

- Reuse the actual V2 reference suite including damped/Hertz sustained, sliding,
  reversal, rolling, periodic, multiple contacts, separation/recontact and the
  before/after-rebuild inputs. Enforce J/K=0 and no incidental imprint writes.
- Match standalone pose/v/w/Q, applied forces/torques, histories, contact IDs,
  acceleration caches and energy/work at **each** full-step boundary; include
  actual first force after bootstrap. A zero-force fluid operator cannot reseed
  histories or insert another bootstrap.
- Retain the 100/100 V2 restart controls and explicit checkpoint rejections;
  they test standalone behavior only, not a coupled fluid restart.
- Failure: hydro in both acceleration caches, stale ordinary rebuild upload,
  second history update or wrong CPU contact-law option forwarding.

## Test C — one fixed particle

- One isotropic sphere; prescribed zero translation/rotation, fluid given a
  weak initial velocity or forcing. Use a grid-resolved geometry plus a small
  cell-level analytic fixture. Compare independent gamma/Omega and population
  increments on every intersecting cell, including outside-center partial cells.
- Particle receives no velocity kick; support reaction is retained. Require
  `Delta P_fluid - J_BGK - J_boundary - J_support = R` and cellwise torque
  cancellation. Record nonzero fluid forcing as its actual collision impulse.
- Subsequent physical accuracy target: periodic simple-cubic fixed-sphere
  Stokes-flow benchmark D=L/2, with the published normalized drag reference
  C=2.8402 and its forcing/buoyancy convention; refine spatial resolution and tau.
  A prospective 5% drag target is a model-resolution gate, not ledger tolerance.
  [Primary benchmark](https://arxiv.org/html/1702.04910v1#S3).
  Match the published superficial/macroscopic velocity definition explicitly;
  this checkout's raw-moment average is not automatically that velocity. If the
  conventions cannot be reconciled without a model change, mark this continuum
  comparison UNRESOLVED and request review rather than rescaling the plot to pass.

## Test D — one freely moving particle

- Same fluid/particle state as C but free, first zero external forcing and no
  supports. Capture J from actual solid increments and actual m*(v_after-v_before)
  at the instantaneous kick. Require paired linear impulse and fixed-pose
  world/body angular impulse, then the **full** step ledger including all other
  increments. Use heavy and near-density-matched cases as separately labeled
  stability tests, without parameter tuning after observing a failure.
- Distinguish numerical full-grid fluid momentum from exterior-fluid/physical
  added-mass interpretation. Agreement in the former alone does not certify
  transient drag/inertia of a physical suspension.
- Failure: half/duplicated J, wrong mass units/Fconv, alpha mismatch or Flbmf
  diagnostic mistaken for applied force.

## Test E — two colliding particles and the fast negative control

- Reuse R=.1, separation=.24, v=+/-300, h=1e-4, Alpha=.001, linear Kn=1000 and
  zero damping with hydro disabled. Post-drift separation=.18 gives overlap=.02
  and force magnitude 20 N. Require actual candidate once per pair and applied
  F1=-F2, not a constructor-produced host normal.
- Preserve the historical active-fluid V2 diagnostic (overlap .005447..., old
  applied contact zero vs ~5.447 N); it is a legacy failure, not a low-Mach
  accuracy benchmark. Do not demand 20 N when hydro changes the trajectory.
- Add a physically low-Mach active-fluid close-gap collision with a sufficiently
  small skin; evaluate expected contact from actual force-time geometry and
  independently computed damping, not the disabled-fluid pose.
- If both particles claim a cell, initial subset must reject, not call this a
  full two-particle hydrodynamic PASS. General support requires the ownership
  design decision and new ledger tests before broader C2 closure.

## Test F — frictional and rolling contact

- Dry V2 two-sphere history cases first; then one fluid-coupled sphere against
  a prescribed DEM wall with a separately registered fluid boundary/support,
  avoiding ambiguous moving-particle cell ownership. Nonzero tangent velocity,
  rolling, positive damping, slide/reverse/separate/recontact as in V2.
- Record pre-step H_n, post-hydro (must be identical), pre-force, and committed
  H_np1. Exactly one finite h update per step, in addition to the retained V2
  bootstrap convention. Compare force/history/work independently, including
  nonreset retained rolling state on separation.
- A snapshot/restore of *trial* state must not change H or increment clocks.
  Actual coupled checkpoint tests are NOT authorized by this case; their phase
  and pending impulses are specified for a separate milestone.

## Test G — periodic domain and moving walls

- Translate one sphere through x/y/z faces; include a moving finite DEM wall in
  the dry/contact test and an independently controlled fluid wall/periodic flux
  test. Require image-aware contact and particle–cell identities at force time,
  no duplicates at wrapped cell indices and no history transfer to another image.
- Require whole-domain raw linear ledger; subvolume momentum includes streaming
  transport. For angular accounting include image translation cross momentum,
  or use unwrapped coordinates/non-crossing tests. Do not assert unqualified
  angular conservation on a periodic torus.
- Test a skin-crossing rotation with zero center displacement and a coupling
  map reference older than the DEM list; a DEM reset alone must not validate it.

## Test H — moving particle in initially quiescent fluid

- Set one free sphere velocity U, fluid equilibrium at rest, no contacts/external
  force. First-cell Omega first moment gives reaction opposite relative velocity;
  sum independently computed cell reactions, not an empirical drag input.
- At fixed entry geometry run U,-U,U/2 at U/c<=.01: initial reaction is odd and
  linear under the registered solid operator; use the FP64 cell budget. During
  subsequent transient evolution require the full impulse ledger and decaying
  relative motion where the explicit stability regime allows it.
- All-periodic fluid eventually shares momentum; no unbounded steady Stokes drag
  is assumed for this finite, accelerating domain. Use C's matched resolved-flow
  benchmark for continuum force magnitude, not a universal terminal-velocity fit.

## Test I — rotating particle

- One sphere at nonidentity Q, omega_body chosen so world angular velocity is
  known; fluid initially quiescent. First test fixed spin and support torque,
  then release it. Capture cell levers, world K, conjugate-Q body K and actual
  `I*(omega_after-omega_before)` at fixed-pose kick; check signs and dissipation.
- A world z torque and a 90-degree-rotated body axis must map to the corresponding
  body component, not unchanged z. Initial isotropic inertia avoids unproven
  gyro cache equivalence; anisotropic particles need a separate CPU/GPU zero-fluid
  and angular-refinement gate (G:843–951 vs P:813–837).

## Test J — compatible timestep and lattice refinement

Preserve physical L,R,rho,nu,U,contact constants and final time, not just names:

`u_lattice=u_phys*h/a`, `nu_lattice=nu_phys*h/a²`,
`tau=1/2+3 nu_phys*h/a²`, `c=a/h`, `rho_lattice=rho_phys/rho_unit`,
`m_unit=rho_unit*a³`, `J_unit=rho_unit*a^4/h`,
`F_unit=rho_unit*a^4/h²`, `T_unit=rho_unit*a^5/h²`,
`omega_lattice=omega_phys*h`, `I_unit=rho_unit*a^5`.

- Fixed a: h,h/2,h/4 require tau values `1/2+(tau0-1/2)/{1,2,4}` and changed
  lattice velocities/forces, not fixed tau. Example tau0=.8 -> .8,.65,.575.
  Reinitialize populations consistently; do not scale DEM material constants in
  physical-unit inputs a second time. Keep low Mach, positive tau margin and
  physical Re/forcing/contact timescales recorded.
- This holds physical nu but changes compressibility/lattice speed and the
  tau-dependent PSM discretization. Establish a spatial/lattice-error plateau
  separately; otherwise the result is a coupled *method-family* convergence
  measurement, not isolated temporal order. Add a diffusive family a,a/2,a/4
  with h,h/4,h/16 to hold tau and physical nu fixed, clearly labeled joint
  spatial-temporal refinement, not h/2 temporal refinement.
- Observables: trajectory, impulse, angular response, smooth shear-wave amplitude,
  drag and contact-free velocity. Contact activation/discontinuities get separate
  one-sided/event-time error; no smooth second-order demand across impacts.
- Compute `p=log2(|q_h-q_h/2|/|q_h/2-q_h/4|)` only when differences exceed measured
  noise/spatial floors. A's target is first-order coupling, not order two; require
  a consistent convergent trend (prospective smooth-regime p about .8–1.2) and
  higher-resolution confirmation, or report UNRESOLVED with the competing floor.

## Acceptance ladder and stop rules

| Gate | Required future evidence | Initial status |
|---|---|---|
| G0 scope/provenance | unchanged standalone/V2 artifacts and guard; explicit supported/rejected configuration | NOT_RUN for implementation |
| G1 cell exchange | independent populations/increments and units, alpha/BForce decomposition, moment and torque ledger | NOT_RUN |
| G2 CPU/GPU cell coverage | identical declared proxy/owner policy, outside-center and partial-cell cases, actual map completeness; no silent geometry fix | NOT_RUN |
| G3 dry VV compatibility | B, existing V2 controls, original law/options/bootstrap and one history commit | NOT_RUN |
| G4 free/fixed response | C/D, actual impulse and supports, bounded positive finite states | NOT_RUN |
| G5 force-time validity | E/G and negative actual-record controls; missing=duplicates=bad_image=0 | NOT_RUN |
| G6 friction/history/work | F and V2 scalar oracle; no trial/history double advance | NOT_RUN |
| G7 fluid/particle torque | I, body/world frames and image-aware angular exchange | NOT_RUN |
| G8 consistency/accuracy | A/H/J, physical unit/lattice transforms, stated first-order target and model-error separation | NOT_RUN |
| G9 scope extensions | multi-owner cells, limiter, nonunit density conversions, Gammaf/Bn variants, anisotropic gyro, nonlinear/multiphase paths separately gated | BLOCKED until separate design/authority and evidence |
| R-coupled | full-fluid checkpoint/continuation and pending-impulse semantics | NOT_RUN; outside initial implementation |

A scoped prototype can pass G1–G8 only for its explicitly registered subset;
G9 rejection tests do not establish support for excluded cases. Overall general
coupled VV/C2 stays unresolved until the user accepts a bounded support contract
or the required extensions pass. No P2-B and no production optimization promotion
follows automatically from a diagnostic or design PASS.
