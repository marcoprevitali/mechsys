# Hydrodynamic momentum-exchange ledger

V3-D design/derivation, not a conservation PASS. Base
`2b8d8c335709046e224f4c43aa930144ae6854e7`. Source keys/locations are in
[CURRENT_COUPLED_SEQUENCE.md](CURRENT_COUPLED_SEQUENCE.md): imprint D:409–443,
K:549–707; collision L:1404–1475 and K:407–473; streaming F:746–764/K:848–869.
[V2 evidence](../v2/V2_REPORT.md#coupled-runtime-blocker-and-preserved-failures)
reports unequal CPU/GPU exchange residuals; it does not identify their per-cell
cause. **No residual is redistributed to particles to manufacture conservation.**

## 1. Unit and population conventions derived from this source

Use one consistent mass/length/time unit system `(M,L,T)` on both solvers.
`h=dt`, `a=dx`, `c=Cs=a/h`, physical lattice velocity `c e_k` with dimensionless
`e_k=C[k]`; lattice sound speed is `c/sqrt(3)` for the registered D3Q15 model.
L:469/551,956–960 and F:71–76 establish these conventions. Populations f_k and
Omega_k have density units M/L³, rho=sum f_k, u_raw=c sum(f_k e_k)/rho.
Initial scope is **3D, Nl=1**, not an unreviewed 2D thickness convention.

For a nonsolid cell q with volume a³ define raw population momentum

`P_q = a³ c sum_k f_qk e_k`.

This is the numerical-population ledger over all dynamic cells, including the
fictitious/interior fluid represented by PSM. It is **not automatically physical
fluid momentum outside particles**. A `(1-gamma)`-weighted physical-volume
ledger also needs occupancy-change/transport and interior-fluid inertia terms.
Do not change particle mass to excess/buoyant mass or add an interior-fluid
correction silently. Record both interpretations; physical transient added-mass
acceptance is a separate validation question.

`gamma=len/(12a)` is the code's edge-coverage approximation. It is not an exact
sphere/cube volume. In the active default smooth model

`B = gamma (tau0-1/2) / (1-gamma+tau0-1/2)`.

Imprint forms particle surface velocity at the cell center:
`v_s = v_p + (R(Q_p) omega_body) cross r_qp`, where r is the same minimum-image
cell-center lever used to compute geometry, and

`Omega_k = f_op(k) - feq_op(k)(rho,v_s) - f_k + feq_k(rho,v_s)`.

`Fconv` multiplies only GPU sphere reaction. For the above common-density units
it is dimensionless and must equal **1**; force already includes the a/h
conversion. A different density scale needs one explicitly derived conversion
of **all** raw fluid momentum, reaction, torque and ledgers; the current
unilateral VC-only multiplier cannot establish such a contract.

## 2. Collision before/after and the exact ledger decomposition

Let `N_k=f_k-feq_k(rho,u_shift)` and
`u_shift=u_raw + h*tau0*BForce/rho`,
`tau_eff=(tau0+sqrt(tau0²+6 Q Sc/rho))/2`.
The default SCDEM update for an unmodified direction in a converged limiter pass is

`f*_k = f_k - alpha (1-B) N_k/tau_eff + alpha B Omega_k`.

Keep three separate population increments, measured **before pointer swaps**:

| Increment | Meaning | Corresponding momentum |
|---|---|---|
| `delta_f_BGK=-alpha(1-B)N/tau_eff` | fluid relaxation, including its actual body-force shift | `J_BGK=a³ c sum delta_f_BGK e` |
| `delta_f_h=alpha B Omega` | the solid collision term actually used | `J_fluid,h=a³ c sum delta_f_h e` |
| `delta_f_other=f*-f-delta_f_BGK-delta_f_h` | clipping, boundary replacement, or incomplete limiter-pass effects | `J_other=a³ c sum delta_f_other e` |

No nonzero `J_BGK` or `J_other` may be silently charged to a particle.
For direction-dependent applied coefficients, use `alpha_qk` in these sums.
K:448–466 caps GPU SC limiting at two passes; if alpha changes inside the last
pass, earlier directions may have used a different coefficient. Log actual
per-direction increments, not just the final scalar alpha. MP K:511–535 can
also clip remaining negative populations. Such cases need a separate collision
gate; the first coupled prototype accepts alpha=1 only and fails clearly otherwise.

For one unambiguous particle owner p per cell, define the proposed reaction from
that **same solid increment**, not from the total population residual:

`J_pq,h = -a³ c sum_k delta_f_h,qk e_k`,
`K_pq,h,world = r_qp cross J_pq,h`,
`K_pq,h,body = R(Q_p)^T K_pq,h,world`.

Thus `J_fluid,h + J_pq,h = 0` is an **algebraic property of shared increments**.
The implementation must still prove that its stored arrays, ownership, units and
applied particle kick realize these terms. Export the cell contribution once,
then reduce per particle. Never infer J from a later reconstructed contact map.

Current reported force is instead

`F_reported = -s B c² a² sum_k Omega_k e_k`,

where s=Fconv for GPU VC and s=1 for CPU/FC. Since `h c² a² = c a³`,
the isolated current exchange defect (single owner, common alpha) is

`R_exchange = J_fluid,h + h F_reported
            = (alpha-s) B a³ c sum_k Omega_k e_k`.

With multiple claimants this formula must use the actual fluid owner term minus
**all** particle reactions. Overwritten/racing gamma/Omega cannot be repaired by
summing particle forces after the fact. Initial implementation must detect shared
positive-occupancy claimants and fail, or obtain a separately reviewed conservative
multi-particle occupancy model; choosing a new sum/normalization is a model change.

## 3. External forcing, boundaries, contacts and streaming are distinct

With consistent raw moments, common alpha, and exact equilibrium first moment,

`J_BGK = a³ alpha (1-B) h (tau0/tau_eff) BForce`.

For Sc=0, alpha=1, this is `(1-B) h a³ BForce`, NOT automatically h a³ BForce.
This is the **actual discrete forcing convention**. Whether physical BForce
means acceleration of exterior fluid, all numerical fluid, or a driven support
must be specified by the application. A Guo half-force macroscopic shift is not
present in this code and must not be added as a diagnostic correction alone.
Particle gravity/applied Ff and Tf are separate and never inferred from Flbm.
Do not add a second buoyancy force without deriving what the forced-fluid setup
already represents.

Static IsSolid cells use population reversal rather than the above PSM update;
account for their momentum change as a fixed-wall reservoir. Periodic streaming
is a population permutation and conserves global raw linear momentum if all
dynamic populations and crossings are counted; open/velocity boundaries require
an explicit incoming-minus-outgoing flux and imposed-population ledger.
Contact internal pairs give zero net linear impulse only if each force evaluation
has action/reaction exactly once. Moving/fixed walls have support impulses.
Gv/Gm damping, if enabled later, are external dissipation/impulse terms, not fluid
exchange; they are initially excluded from the proposed supported subset.

For prescribed particle components with free-component projector P, apply `P J_p`;
support impulse **on the particle** is `(P-I) J_p`. Include that external support
term in the combined balance, or include its opposite as the support-reservoir
momentum change. Record imposed-motion work as well. Never drop the fixed
particle's reaction merely because its velocity does not change.

The step ledger is

`Delta P_raw,fluid + Delta P_particles
 - J_BGK - J_other - J_boundary - J_ext,particles - J_support
 = R_step`.

All signs here are impulses **into the represented system**; periodic net linear
transport is zero for the whole domain but not for a subvolume. The numerical
ideal R_step is reduction/roundoff size only when all contributions are paired
and particle integration realizes the registered force quadrature. It is not a
license to cancel a measured residual with a compensating force.

## 4. Angular ledger and frames

At a fixed collision pose and a single cell-image origin Xq,

`Xq cross J_fluid,h + Xp cross J_p,h + K_p,h,world = 0`.

This establishes cellwise exchange angular cancellation, provided the **same**
Xp, image and lever are used on both sides. Existing imprint maps world torque
to body via conjugate Q (D:434–443 / K:595–609). During the proposed instantaneous
kick at fixed Q, update `I omega_body` by `K_body`. Do not divide by h twice,
or use body torque directly in a world angular-momentum sum.

Streaming transports each population parallel to its lattice momentum, so free
unwrapped streaming has zero angular change about a fixed origin. Periodic
wrapping introduces an origin/image transport term `(-box_translation) cross p`;
angular momentum on a periodic torus is not an unqualified global invariant.
Compute image-aware transport or test angular balance in a non-crossing setup.
The subsequent rigid-body VV gyro/orientation update can have a finite
discretization residual for anisotropic I; no roundoff-level angular conservation
is asserted for that separate integrator. Test cellwise exchange and full-step
angular convergence separately.

## 5. Small algebraic witnesses (not solver runs)

Density=1, c=a=h=1, raw fluid u=0, surface v_s=(0.01,0,0), tau0=0.8,
gamma=0.5 -> B=0.1875. The equilibrium first moment gives
`sum Omega e=(0.02,0,0)` and unscaled fluid exchange J0=(0.00375,0,0).

| Condition | J_fluid,h,x | Current h F_reported,x | Residual |
|---|---:|---:|---:|
| alpha=1, s=1, one owner | 0.00375 | -0.00375 | 0 |
| alpha=0.5, s=1 | 0.001875 | -0.00375 | -0.001875 |
| alpha=1, VC s=2 | 0.00375 | -0.0075 | -0.00375 |

These are independently derived counterexamples to unconditional pairing, not
claims that the V2 fixture activated a limiter or nonunit Fconv. For r=(0,2,0),
the first row gives particle K_world,z=+0.0075 and fluid angular impulse -0.0075.

For one-cell exchange with `beta=2 alpha B rho a³`, masses Mp and Mf=rho a³,
relative velocity multiplier after an explicit kick is
`g=1-beta(1/Mp+1/Mf)`. B=0.5, alpha=1, Mp=Mf gives g=-1 (marginal);
B=1 gives g=-3. This proves a **reduced-model** explicit stability limitation,
not instability of the full streaming LBM solver or a reason to select iteration
without the planned density-ratio tests. No existing law is modified here.

## 6. Literature boundary, not code substitution

[Rettinger and Rüde, §2.3](https://arxiv.org/html/1702.04910v1#S2.SS3)
describes separate solid collision contributions and force/torque summation;
it also documents several PSM variants and a different macroscopic convention.
The local equations above are derived from this checkout, not copied in as a
different PSM model. [Guo, Zheng and Shi](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.65.046308)
establish that discrete forcing effects require analysis; the accessible abstract
does not establish that this checkout implements their scheme. Noble/Torczynski's
original DOI is 10.1142/S0129183198001084; publisher full text was inaccessible
(403), so no original-paper equation is claimed as directly verified here.

Next: [validation ledger tolerances](VALIDATION_PLAN.md) and
[selected time contract](COUPLED_VV_TIME_CONTRACT.md). Coupled restart remains
unvalidated; standalone [V2 checkpoint contract](../v2/RESTART_STATE.md) is unchanged.
