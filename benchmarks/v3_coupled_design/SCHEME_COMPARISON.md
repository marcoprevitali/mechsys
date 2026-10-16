# Coupling candidates and recommendation basis

V3-D, design only. Base `2b8d8c335709046e224f4c43aa930144ae6854e7`.
[Current source audit](CURRENT_COUPLED_SEQUENCE.md) covers D:798–951,
K:407–707, standalone stages M:834–887/977–1065 and G:800–952.
[V2 C2 evidence](../v2/V2_REPORT.md#coupled-runtime-blocker-and-preserved-failures)
establishes absence of a coupled VV algorithm, not superiority of any candidate.
All candidates require the [same exchange ledger](MOMENTUM_EXCHANGE_LEDGER.md)
and unchanged contact laws. None is implemented or numerically accepted here.

## A. Explicit staggered exchange followed by the V2 VV step — recommended

1. On x_n,Q_n,v_n,omega_n and f_n, prepare/validate occupancy and owner records.
2. One collision -> one stream -> moment refresh; export the actual solid
   population increments and corresponding particle J/K. Bulk forcing/boundary
   effects remain separate, not a balancing force applied to particles.
3. Apply that J/K once at fixed particle x_n,Q_n. This is an operator kick.
4. Perform the **one** V2 mechanical VV step: old nonhydro half-kick, full drift
   and rotation, pre-force validity/rebuild, one endpoint contact/history commit,
   endpoint nonhydro half-kick. Hydro never enters A_ce/Wdot_ce.
5. Joint state/clock commit at n+1.

This contract is fully specified in [COUPLED_VV_TIME_CONTRACT.md](COUPLED_VV_TIME_CONTRACT.md).
It pairs the actual fluid increment with a unique particle impulse without
assuming a nonexistent endpoint hydro force. Its formal splitting error is
first order for smooth, consistent, non-stiff cases. A contact-free constant
force example already has an O(h²) local position defect from left impulse then
drift. Therefore even an independently second-order mechanical step cannot
establish second-order accuracy of the coupled scheme.

## B. Midpoint-geometry predictor/corrector with one accepted fluid update

Define a concrete **B1** candidate to expose the actual requirements rather than
calling any drift-before-force sequence “midpoint”:

1. Nonhydro half-kick at n. Predict particle pose to t_half by a half drift/
   quaternion rotation using that auxiliary velocity. Use scratch pose buffers;
   contact history H_n remains immutable. Verify coupling-cell list validity on
   this trial geometry before any fluid evaluation.
2. At this pose evaluate one trial collision on **the unchanged f_n** using the
   pre-hydro surface velocity, obtaining provisional J0/K0. Do not stream or
   advance clocks and do not apply this trial impulse to live particles.
3. Predict centered surface velocity using v_half,ce+J0/(2m) and the matching
   body angular-impulse half increment at Q_half. Replay the fluid evaluation
   from **f_n**, not from the trial collision output; compute J1/K1 and commit
   one fluid collision/stream only. Discard J0, not add J0+J1.
4. Materialize the mechanical midpoint pose, apply J1/K1 **once at that same
   midpoint center/orientation**, then complete the second half drift/rotation.
   Evaluate endpoint contact/history once with h after endpoint validity; final
   nonhydro half-kick and joint commit. Cell torque levers use this actual
   midpoint pose, not a different predictor that has already been overwritten.

No contact force trial is necessary in this B1 definition. It still needs two
solid/collision evaluations, scratch populations/impulses and midpoint geometry;
the initial trial need not stream. A pure zero-hydro path should call the exact
V2 full drift rather than introducing two half drifts with extra rounding or
new rebuild cadence. If a corrector instead changes the endpoint after contacts
were evaluated, the **entire** contact trial and candidate/reference state must
be rolled back and only the final history/work increment committed.

**Important limit:** B1's fluid populations are still f_n. Midpoint particle
geometry and a corrected surface velocity alone do not establish Fh_half or
second-order fluid-particle coupling. Expect first-order overall until a separate
LBM time-centering derivation and convergence evidence justify more. This
candidate can reduce some particle position/velocity splitting errors, but the
gain is a hypothesis, not measured evidence that its extra work is justified.

A **B2** second-order-target upgrade would require a consistent fluid midpoint
population/forcing variable, including any transformed-distribution convention,
half-force macroscopic correction, PSM B/Omega weighting, limiter and boundary
time quadrature. A trial f_np1 and `(f_n+f_trial_np1)/2` alone is not proof that
the existing collision applied to f_n becomes a midpoint kinetic integrator.
B2 is **not a closed implementation-ready scheme in this milestone**. It is a
research branch of B, not a hidden requirement or untested claim of order two.
Do not replace this checkout's collision law under the name of a VV refactor.

## C. Iterated B-type interface coupling — deferred

At fixed provisional midpoint pose, initialize interface velocity and repeat
the B1 trial from the same f_n, with no persistent writes. For iteration r let
`J_r=J_fluid_operator(f_n,pose_half,surface_velocity_r)` and update the surface
velocity from `v_half,ce+J_r/(2m)` and corresponding angular impulse. Solve the
discrete interface consistency, not the time-advanced fluid from r-1.

Use both a scaled impulse-change residual and velocity/rotation residual:

`r_J=max_p |J_r-J_(r-1)| / (Jscale_p+|J_r|)`,
`r_v=max_surface |v_surface,r - v_surface(J_r)| / Vscale`.

Tolerances must make remaining iteration impulse error less than 10% of the
registered step ledger budget; record absolute and scaled residuals. Set a
finite iteration limit, retain the last rejected state and fail/retry only under
a separately approved timestep policy if it is exceeded. Do not silently accept
the last iterate or advance clocks h on each trial. Underrelaxation is an
explicit input with provenance, not automatic tuning until a gate passes.

Provisional state includes f/f*/stream roles, rho/u, BForce/BC state, occupancy/
ownership/Omega, limiter coefficients, J/K, pose/vertices/velocities/gyro caches,
all clocks and coupling-list references. If contact forces are included in the
iteration, add full contact/feature histories, retained/deleted records and work
arrays, then commit one accepted h update. Interface-only iteration as defined
above leaves contacts until the final endpoint and does not solve a fully
implicit contact-fluid problem. Residual convergence does not itself raise the
temporal order of the underlying fluid coupling discretization.

The reduced-cell stability bound in the ledger motivates a future light-particle
stress test; it is not a measured failure of A in a full coupled simulation.
Select C only if A/B tests establish a relevant stability/consistency limitation
and demonstrate that iteration resolves it without losing the ledger/history
gates. No such experiment is authorized or reported in V3-D.

## Comparison (expectations, not performance measurements)

| Criterion | A | B1 (B2 is unresolved research) | C |
|---|---|---|---|
| Time consistency | left-state exchange, explicit interval impulse | midpoint particle pose/velocity predictor, fluid f_n retained | same fluid discretization plus solved interface residual |
| Expected coupled order | at best 1, local splitting derivation | 1 until kinetic/time-forcing derivation establishes more | underlying scheme's order; iteration is not order promotion |
| Linear exchange pairing | same actual solid increment / one particle kick | same, with only J1 accepted | same, final trial only; residual budget additionally required |
| Torque exchange | kick at x_n,Q_n, exact cell lever cancellation | kick at actual midpoint pose; otherwise predictor-lever residual | converged trial pose/lever must be the committed kick pose |
| Mechanical angular integration | inherited VV error; isotropic first subset | additional split rotations, anisotropic extension unvalidated | iteration does not fix baseline rotational discretization |
| Contact histories | one endpoint h commit, no trial | one endpoint h commit; rollback if correcting endpoint contacts | immutable or deep scratch; one final commit |
| Contact force evaluations | one endpoint plus existing bootstrap/cache | one endpoint in B1; more if contact-inclusive correction | one final or one per trial if contacts are iterated, never live |
| Fluid evaluations | 1 collision/stream | 1 provisional collision + 1 accepted collision/stream | r trial collisions, one committed stream (or discarded trial streams) |
| Extra memory | O(Np) J/K/cache and O(Ncell) owner/ledger; reuse current population ping-pong | A + O(Np+Nverts) midpoint/trial state; f* scratch can reuse existing buffer when trial never streams | B + rollback state/histories if contact-inclusive; an extra O(Ncell*Q) buffer if trials stream while preserving f_n |
| CPU complexity | split imprint side effects; impulse ledger + VV stage wiring | trial/replay and midpoint pose isolation | transactional replay and solver/termination policy |
| GPU complexity | phase kernels, owner/count checks, impulse reduction; one stream ordering | extra trial kernels/buffer roles and midpoint list checks | multiple trials; residual reduction/host or device control |
| Host/device synchronization | baseline rebuild scalar/CPU rebuild only, diagnostic readbacks explicit | extra rebuild branch if midpoint crosses skin; trial dependencies on stream | iteration convergence scalar/event or GPU control each iteration |
| LBM-law compatibility | registered SCDEM subset only until ledger proves more | no implicit permission to change BGK/PSM forcing | every trial must obey the same registered law; cannot hide clipping |
| Standalone VV compatibility | exact zero-hydro stage path in initial subset | special zero-hydro route needed; half drifts/rotations otherwise alter ordering | use unmodified VV zero-hydro route; rollback adds regression risk |
| Known risk | explicit coupling stiffness, first-order lag | old-fluid centering remains; geometry/trial ownership complexity | convergence failure, added-mass stiffness, accidental multiple commits |

**Recommendation:** A for a bounded, gated reference prototype after the
exchange audit gates, not as a speed or accuracy winner. It addresses the actual
source mismatch with an identifiable impulse and preserves the zero-fluid VV
reference without an unproved fluid midpoint. B1 adds work but has no derived
order advantage yet; C has no demonstrated full-solver need. If required accuracy
is second order, A cannot meet it by relabeling: close B2's kinetic derivation and
refinement gates in a separate design revision before implementation selection.

Primary-method context, not an acceptance proof: the
[PSM study §2.3](https://arxiv.org/html/1702.04910v1#S2.SS3) treats solid contributions
and macroscopic conventions explicitly; this is why changing only particle kicks
does not justify importing another method's time accuracy.
