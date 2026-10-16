# Current coupled algorithm: source audit, not numerical acceptance

V3-D, 2026-10-16 (Asia/Shanghai), Codex. Audited immutable base:
`2b8d8c335709046e224f4c43aa930144ae6854e7`, user fork
`marcoprevitali/mechsys`. **No solver changes or new simulations in V3-D.**
The coupled VV/restart guard remains at [D:591–594][D591].
[V2 report](../v2/V2_REPORT.md#coupled-runtime-blocker-and-preserved-failures)
and [V2 coupled results](../v2/results/coupled_legacy_and_rejections.json) remain
the runtime evidence: legacy controls complete; explicit VV fails closed. The
audit below describes the accessible **legacy** path, not a hidden VV algorithm.

## Notation and source keys

`h=dt`, `c=Cs=dx/h` (lattice speed, NOT sound speed), `e_k=C[k]` dimensionless.
`f_n` is the post-stream/pre-collision population array at loop entry; `rho_n`
and `u_raw,n=c*sum(f_n e_k)/rho_n` are its moments where macroscopic refresh has
completed. `x_n,Q_n` are entry geometry. Legacy stored `v,w` do **not** have the
full-step synchronized VV meaning assumed in the new contract. In particular,
legacy translation stores a central velocity at the old geometry time while
advancing x. Thus after the first step, imprint uses current entry geometry
with a lagging stored velocity; do not merely rename this value `v_n`.

Source keys, all relative to this recorded base:

| Key | Source |
|---|---|
| D | [lib/lbmdem/Domain.h](../../lib/lbmdem/Domain.h) |
| K | [lib/lbmdem/lbmdem.cuh](../../lib/lbmdem/lbmdem.cuh) |
| P | [lib/dem/particle.h](../../lib/dem/particle.h) |
| M | [lib/dem/domain.h](../../lib/dem/domain.h) |
| G | [lib/dem/dem.cuh](../../lib/dem/dem.cuh) |
| L | [lib/flbm/Domain.h](../../lib/flbm/Domain.h) |
| F | [lib/flbm/lbm.cuh](../../lib/flbm/lbm.cuh) |
| H | [lib/dem/interacton.h](../../lib/dem/interacton.h) |

## Startup (both backends, D:598–765)

1. Set DEM Dt, initialize particle properties/legacy xb and wb, thread workspaces,
   bounds and lifetime IDs; classify free/fixed particles. A/Wdot are allocated
   and zeroed for shared upload, **not** initialized by a coupled VV bootstrap.
2. Set periodic DEM extents; derive `Per`. `Reset()` seeds particle F/T and
   zeros gamma/Omega; `ResetParCell()` builds padded particle–cell/feature pairs;
   `ImprintLattice()` computes initial gamma/Omega and particle fluid reaction
   from the initial populations, without advancing those populations.
3. `DEMDOM.UpdateContacts()` creates candidate/contact records. Constructors
   may evaluate `CalcForce(0)` for diagnostics; this is not an applied force step.
4. Optional multiphase cell-pair table. GPU uploads DEM, fluid and coupling data.
   Coupling upload initializes device Omega to zero (D:981–1018); first GPU
   imprint, not the host bootstrap Omega, supplies the first collision input.
5. Setup callback runs **before** report-time download on GPU. Callbacks reading
   host particle/fluid data can therefore be stale; prescribed updates need an
   explicit device route. Final V2 readback is at D:959–964.

## CPU timestep, Nl=1 actual path

Each row depends on the preceding writes unless explicitly stated. `n->n+1`
here labels the loop interval, not a proven force quadrature time.

| Operation / location | Reads / input stage | Writes / output / dependency |
|---|---|---|
| callback/report D:772–794 | entry x,Q,stored v,w, f and moments | caller Ff/Tf/BForce/BC edits; reports precede resets; caller state is outside solver ownership |
| `Reset` D:555–580,890 | IsSolid, Ff, Tf | gamma=IsSolid; Omega=0; particle F=Ff, Flbm=0, T=Tf. Does not reset contact histories or fluid BForce |
| contact `CalcForce(h,Per,iter)` D:895–916 | entry geometry and stored velocities; existing lists/history | advances contact history by h at **entry geometry**, sets per-contact F1/F2/T1/T2 and diagnostics; locks accumulate into particle F/T. Three-argument call does not explicitly forward all standalone law/options |
| `ImprintLattice` D:336–447,920 | same entry geometry/velocities, f_n,rho_n,Tau[0], candidate particle–cell list | sphere/feature overlap, gamma and Omega; adds fluid reaction to F, Flbm, body-frame T **before fluid collision**; no population update yet |
| particle Translate P:861–906, D:931 | accumulated contact+fluid+external F, x,xb,stored v | `x_next=2x-xb+h²(F/m-Gv*v)`; `v_stored=(x_next-xb)/(2h)` is centered at the old x time; xb=old x; translates every vertex |
| particle Rotate P:694–739, D:933 | current Q, w/wb, total body T/Tf, Gm | angular acceleration wa, intermediate w, wb leapfrog update, normalized Q_next and rotated vertices; legacy rotation, not standalone VV. CPU calls this unconditionally here |
| MaxDisplacement/rebuild D:935–948 | all current vertices/reference vertices | after motion, compare max displacement > Alpha; UpdateContacts wraps/resets references/reconstructs histories; ResetParCell rebuilds coupling pairs. **No second contact force is applied at this new geometry in this step** |
| `CollideSCDEM` L:1404–1475, D:950 | f_n,rho_n,u_raw,n,BForce; **cached entry-geometry** gamma/Omega despite particle motion | post-collision f* into Ftemp, then swap. Effective tau/positivity scaling can differ from values used to precompute particle reaction |
| `StreamSC` L:1787–1851, D:951 | f* | periodic push to f_np1, swap; recompute rho/u_raw, clear BForce. Omega cleared by next CPU Reset |
| clocks D:954–956 | outer Time/iter | outer Time+=h, outer iter and DEMDOM.iter++; CPU does not advance LBMDOM.Time/DEMDOM.Time in this loop. Do not infer coherence from field names |

## GPU timestep (default-stream ordered launches)

| Operation / location | Reads / input stage | Writes / output / dependency |
|---|---|---|
| callback/report/download D:772–794 | entry device state; possibly stale host before download | report downloads DEM, LBM, gamma; host torque/A/Wdot have V2 diagnostic caveats |
| `cudaReset` K:127–133, D:798 | IsSolid, Gammaf | gamma=1 for static solid, otherwise Gammaf; **does not clear Omega** |
| DEM `pReset` G:1070–1091, D:800 | static Ff, Flbmf, Tf and common-contact seeds | DPar.F=Ff, DPar.Flbm=Flbmf, Par.T=Tf; reset common force/work sums, **not** persistent Ft/Fr/overlap/contact flags |
| VV/EE/VF/FV force kernels D:801–804 | entry x/Q, stored legacy v/w, actual uploaded records | advance contact histories once with h; atomic additions into DPar.F and Par.T; before any drift/list recheck |
| `cudaImprintLatticeVC` K:549–609, D:813 | entry device sphere geometry/velocity, f_n/rho_n, uploaded particle–cell pairs | write gamma/Omega; atomic additions into particle F/Flbm and body T; Bn from function pointer, **Fconv applied** |
| `cudaImprintLatticeFC` K:612–707, D:814 | entry current polyhedral vertices/Q, f_n/rho_n, face-cell pairs | analogous reaction, hard-coded smooth Bn and **no Fconv**; Nl loop has unoffset population/Omega indexing, a separate multiphase limitation |
| `pTranslate` G:965–987, D:824 | net F, x/xb | same legacy central-difference geometry and lagging velocity convention; unlike CPU Translate, this kernel does **not** apply Gv |
| `pRotate` G:990–1066, D:825 | Q, body T, wb | legacy angular update/rotation when RotPar=true; no Gm term in this GPU legacy kernel |
| `MaxD` G:1095–1104, D:826–843 | every vertex and reference | computes displacements **and advances device DEM auxiliary clock/counter**; host DEM auxiliary copy is separately advanced. max_element host read synchronizes; if > Alpha, ordinary UpdateContactsDevice + ResetParCell + coupling list upload. No new force evaluation this step |
| optional SC/MP forcing D:853–869, K:710–844 | f moments, gamma, cell-pair table | accumulates BForce (GPU branches only here); MP collision has distinct indexing/limiting behavior |
| `cudaCollideSCDEM` K:407–473, D:860 | f_n, entry-derived gamma/Omega, old moments, current BForce | postcollision f*, effective tau and alpha. Particle has already moved; old geometry buffers remain the collision source; it does not recompute imprint |
| swaps, `FLBM::cudaStream1` F:746–764, D:871–877 | f* | periodic push, second swap to f_np1; swaps are pointer roles, not physical advances |
| coupled `cudaStream2` K:848–869, D:879 | f_np1 | rho/u_raw refresh; BForce=0; Omega=0 in non-static cells; advances fluid device clock/iter. No half-force velocity correction is added |
| outer clocks D:954–956 | host copies | outer Time+=h, DEMDOM.iter++, outer iter++; host/device clocks require explicit synchronization rather than assuming every field was updated |

The commented old non-template VC/IBB implementation K:134–387 is **not** the
active PSM force path. Active Bn functions are K:392–404.

## Force ownership, resets, units and differences

| Field | Current ownership / meaning |
|---|---|
| particle F | force, world frame; Reset seeds Ff, contacts and imprint add; legacy Translate consumes it immediately |
| Ff / Tf | application-prescribed world force / body torque; never fluid collision outputs |
| particle Flbm | fluid-reaction diagnostic, force units; imprint adds the **same contribution** also added to F; do not add Flbm to F again |
| Flbmf | GPU Reset seeds Flbm with it, **not F**; CPU Reset clears Flbm instead. It is not a universally applied external force; initial design requires zero and documents the discrepancy |
| particle T | body-frame total torque, seeded Tf, contact and fluid torques add; GPU authoritative storage is ParticleCU.T, not the ordinary host download |
| A/Wdot vs wa | standalone VV acceleration caches vs legacy rotational wa; allocating zero A/Wdot in V2 solved startup bounds, not coupled time integration |
| fluid F / Ftemp | populations (density units), not particle forces; collision and streaming swap roles |
| Omega/Omeis | solid collision **population increment** before weight/limiter, density units; no h factor is stored |
| gamma / Gammaf | edge-length occupancy proxy `len/(12 dx)` / prescribed occupancy, dimensionless; proxy is not exact volume fraction. CPU Reset ignores Gammaf; GPU honors it |
| fluid BForce | force density, inferred from `h*tau*BForce/rho` velocity shift; refreshed by application/optional GPU forces, cleared after stream |
| Fconv | dimensionless multiplicative reaction scale **if fluid populations use the DEM mass-density unit**; default 1. Applied only in GPU VC, not CPU/FC or fluid collision. It is not an h or dx conversion already missing from all paths. Different density units require one coherent global mass conversion, not this unilateral multiplier |

Source-verified exchange hazards, **not individually proven explanations of V2
runtime residuals**:

1. Sphere CPU center cutoff D:350 is Dmax; GPU VC K:569 admits centers out to
   Dmax+1.74dx before geometric intersection. Thus CPU can omit partially filled
   outside-center cells that CUDA includes. Do not silently replace a model or
   accept CPU/GPU agreement without the independent cell oracle.
2. Grid gamma/Omega assignment is not locked/atomic; particle force addition is.
   More than one particle per cell can overwrite the fluid owner yet leave
   previous reaction on another particle; within GPU kernels also race. Later
   FC can replace earlier VC without retracting its force. A max comparison alone
   is not a conservative multi-particle partition. Diagnose/reject ownership
   conflicts in the first prototype; a general mixture rule needs separate review.
3. Collision computes a per-cell alpha; pre-imprint reaction uses alpha=1. GPU's
   capped last pass can also have directionwise applied coefficients. The
   algebraic residual and body-force/tau effects are derived in the
   [ledger](MOMENTUM_EXCHANGE_LEDGER.md), not fixed here.
4. Baseline source uses raw fluid velocity moments, not an implicit Guo midpoint
   convention; Gamma/Omega live through particle drift until collision. Neither
   drift order nor the variable name Flbm turns it into Fh_np1 or Fh_half.
5. Current coupled CPU loop is SCDEM even when Nl>1; GPU has MPDEM. FC multiphase
   indexing, Gammaf, nondefault Bn and nonunit Fconv need separate gates.

## Standalone VV reference that must survive

M:720–765 defines bootstrap; M:834–887 / 977–1065 define the GPU/CPU VV step.
Half-kick/drift and quaternion update precede all-vertex validity checks and
**post-drift** contact forces. G:800–952 and P:776–856 supply integration stages.
The narrow rebuild M:4167–4198 does not overwrite particle state/A/Wdot or advance
surviving histories. Ordinary rebuild M:4201–4272 does overwrite/recompute them
and cannot simply be moved into a coupled VV pre-force stage.

See [time contract](COUPLED_VV_TIME_CONTRACT.md), [history policy](COUPLED_VV_TIME_CONTRACT.md#contact-history-commit-contract)
and [V2 state audit](../v2/RESTART_STATE.md). V2's fast-motion physical failure
(post-drift overlap 0.005447..., applied contact 0 vs ~5.447 N) is retained; a
post-step constructed host normal is not a force-time oracle.

[D591]: https://github.com/marcoprevitali/mechsys/blob/2b8d8c335709046e224f4c43aa930144ae6854e7/lib/lbmdem/Domain.h#L591-L594
