# Short-time propagation — derived pieces and explicit closure stop

**PARTIAL, not an approved tolerance table.** This derives the actual discrete
maps. It does not prove continuum accuracy of legacy integration or close an
independently evolved two-step fluid/particle compatibility gate. Critical open
items at the end trigger the work-order stop: recommend D, no harness yet.

Use fixed common h>0,m>0,positive principal I_j and identical model parameters.
For scalars/components D_y=|y_A-y_B|; for quaternions/rotation vectors use the
Euclidean norm, stated explicitly. Maxima are certified over BOTH enclosing
state boxes, never simply selected observed differences. Each r_y below is the
SUM of two local implementation-rounding bounds relative to the exact real
source map at its own inputs. No generic epsilon is chosen for these symbols.

## 1. Rounding accounting, operation counts and domains

For a certified RN primitive, local absolute error <=u*|exact result| (normal
range). An outward state enclosure supplies its magnitude. Add/subtract
propagate D_a+D_b, product propagates |a|_max*D_b+|b|_max*D_a, division requires
a nonzero denominator lower bound. FMA propagates its EXACT ab+c expression
with ONE local rounding, not three independent errors. Powers-of-two scalings
and exact copies are exact only after excluding overflow/subnormal issues.
Nonfinite/unsupported arithmetic is a gate failure, not a larger bound.

Counts must describe the compiled/default-flag path; a conservative unfused
graph may cover contraction only when the enclosing magnitudes and formula
prove it. The accumulator's native RN graph is already verified; that is not
a verification of every integration/collision primitive. Future certification
must pin their graphs and outward-rounding implementation as well. CPU and GPU
local budgets are distinct when their operation graphs differ.

For example, CUDA Translate's scalar k=fl(fl(h*h)/m) has
eta_k<=gamma2*|h^2/m|. An unfused source-graph enclosure for one x component is

```
eta_x <= gamma4*(2|x|+|xb|+|k_exact F|)
         +(1+gamma4)*|F|*eta_k.
eta_v <= gamma3*(|x_new|+|xb_old|)/(2h).
```

The four counted x operations are scale2,multiply-by-k,subtract,add; coefficient
formation is separate. v counts subtract,scale1/2,divide. These deliberately
conservative bounds are conditional on normal finite intermediates, no
reassociation outside this certified graph and common input h/m. For each
execution its eta is evaluated on a fixed enclosing box; r_x=eta_x,A+eta_x,B.
The acceleration diagnostic F/m needs its own division eta, but the legacy
pA cache is NOT updated by Translate and must not be compared as acceleration.

## 2. Translation: exact source map, one step

dem/dem.cuh:969-979, with fixed velocity flags inactive:

```
a_n       = F_n/m                       [conceptual, not pA]
x_new     = 2*x_n-xb_n+(h^2/m)*F_n
vS_new    = (x_new-xb_n)/(2h)
xb_new    = x_n                         [exact assignment]

D_a,n     <= D_F,n/m + r_a,n
D_x,n+1   <= 2D_x,n+D_xb,n+(h^2/m)D_F,n+r_x,n
D_vS,n+1  <= (D_x,n+1+D_xb,n)/(2h)+r_v,n
D_xb,n+1   = D_x,n.
```

At matched initial state, D_x,0=D_xb,0=0:

```
D_x,1  <= (h^2/m)D_F,0+r_x,0
D_vS,1 <= h*D_F,0/(2m)+r_x,0/(2h)+r_v,0.
```

The force-induced reported-velocity scale is h*D_F/(2m), NOT h*D_F/m.
The latter belongs to the phase-aligned change of HALF-STEP velocity. If
vPlus is reconstructed from positions with exact/high-precision reference
arithmetic, D_vPlus <=(D_x,new+D_x,old)/h; an FP64 diagnostic adds its own
reconstruction error. Coordinate rounding can dominate these force scales.

Illustration from fixed first-step x-force sum bound: D_F,x=2E_x~2.411e-15,
m=4460.2238100565492,h1, so acceleration/position force-only uncertainty~5.405e-19
and reported-velocity force-only uncertainty~2.703e-19. These exclude local
rounding; they are NOT proposed x/v tolerances or fits to the measured zero
position difference. Distinct exact inputs can round to the same stored x.

## 3. Rotation, including gyroscopic dependence and body/world frame

Let b=wb, T total body torque and j,k,l cyclic. The actual update is

```
a_j = [T_j+(I_k-I_l)*b_k*b_l]/I_j
wC  = b+(h/2)*a                 [written to stored w]
bNew= b+h*a                    [written to wb]
```

For common I, put K_j=|(I_k-I_l)/I_j| and B_j=max |b_j|. Then

```
D_a,j <= D_T,j/I_j+K_j*(B_k D_b,l+B_l D_b,k)+r_a,j
D_wC  <= D_b+(h/2)D_a+r_w
D_bNew<= D_b+h D_a+r_b.
```

Each anisotropic component graph includes inertia subtraction, two products,
torque addition and division (up to5 RN operations); wC coefficient/scalar
product and addition, and bNew product/add, have their own counts. Carry input
I errors separately if I is not an exact shared registered field. For the
isotropic canonical sphere K_j=0 exactly when the uploaded I components are
bitwise equal. Use actual I, not a fit to omega/T or an assumed unit inertia.
dompargen.h:585-586 constructs m and I=(2/5)mR^2; analytic I~8634.99329626948
is an explanatory scale, not the uploaded binary64 value. A gamma4 enclosure
of that expression can bound its construction if necessary, but exact I bits
should be part of future input/phase evidence. Current probe does not serialize I.

Imprint maps body w to world and world torque back via
R_q(v)=vector(q*(0,v)*conjugate(q)). This source helper does not divide by
||q||^2. Hence ||R_q(v)||<=||q||^2||v|| and

```
D_R <= Qmax^2*D_v + 2Qmax*Vmax*D_q + r_R.
```

Do not silently use an exactly orthogonal matrix for a slightly nonunit stored
q without charging the corresponding formation discrepancy to its existing
frame/reference budget. Force lever r is the entry periodic image, not the new
post-drift position. An orientation-induced next-step T difference is not a
same-input atomic-order error.

## 4. Actual quaternion map and normalization

Define H(q,w)=q*(0,w), an ordered Hamilton product. Code forms

```
qM = q+(h/4)*H(q,wC)
qD = qM+(h/4)*H(qM,bNew)
qNew = qD/||qD||.
```

Retain THIS order; it is not Exp(h*w), ideal VV, a commuted product, or a
single midpoint derivative. The source uses scalar-first q with real4 storage
helpers. Each H component uses four products and three add/subtract operations;
coefficient formation, increments and second evaluation add their own rounding.
For endpoint norm maxima Q,W,M,B covering the two executions:

```
D_qM <= (1+h*W/4)*D_q+(h*Q/4)*D_wC+r_qM
D_qD <= (1+h*B/4)*D_qM+(h*M/4)*D_bNew+r_qD.
```

Quaternion norm multiplicativity proves ||H(q,w)||=||q||||w|| and these
bilinear bounds; no arbitrary rotation Lipschitz constant is inserted.
If BOTH exact qD norms >=s>0, elementary normalization gives
||N(qD_A)-N(qD_B)||<=2*D_qD/s. Local norm/division rounding adds r_N:

```
D_qNew <= 2*D_qD/s+r_N.
```

Proof uses the reverse triangle inequality; a nonzero certified norm floor is
mandatory. For the displayed norm helper (four squares,three adds,one sqrt),
conditional RN arithmetic yields squared-sum relative error<=gamma7. With
nu=1-sqrt(1-gamma7)+u*sqrt(1+gamma7), norm error<=nu*||qD||. If nu<1,
the componentwise normalized-output error norm is bounded conservatively by
(nu+u)/(1-nu), before pairing the two executions. This uses correctly rounded
sqrt/division, no under/overflow, and a certified sum-of-squares graph; verify
these assumptions before using it. It is not a hardcoded quaternion epsilon.
Compare unnormalized norms and the normalization residual separately.
Physical orientation metrics can account for q/-q equivalence, but a spurious
sign flip does not pass the ordered discrete-map check merely for that reason.

## 5. Collision/stream feedback, not a reused first-step tolerance

For single-owner alpha1/Sc0/BForce0 with fixed tau, exact ideal primitive map:

```
B = gamma*(tau-.5)/(tau+.5-gamma)
g = f-Feq(rho,uRaw)
fStar = f-[(1-B)*g/tau-B*Omega].
```

Require a positive density and denominator lower bound d=min(tau+.5-gamma).
On this region |dB/dgamma|<=(tau-.5)*(tau+.5)/d^2. For fixed tau,

```
D_fStar <= D_f+(|1-B|_max/tau)D_g+|B|_max D_Omega
           +(Gmax/tau+OmegaMax)D_B+r_collision
D_g <= D_f+D_Feq.
```

Feq uses a quadratic in u. With a_k=e_k·u/c,
P_k=1+3a_k+4.5a_k^2-1.5||u||^2/c^2,
an independent bound is
|delta Feq_k|<=|W_k|[Pmax D_rho+rhoMax*((3+9Amax)||e_k||/c+
3Umax/c^2)D_u]+r_Feq. Same for the surface equilibrium with vSurface;
Omega's four signed terms propagate by the triangle inequality. Body/world
rotation and lever errors enter vSurface=vS+R_q(wS) cross r through their
bilinear bounds. Include occupancy sensitivity and all formation roundings.

Periodic Stream1 is a one-to-one population permutation in this fixture: it
does not amplify the componentwise max error or add arithmetic rounding, if
cell/direction/destination mapping is identical. Stream2 sums15 f values for
rho and raw momentum then forms uRaw=c*p/rho. Derive the two15-term budgets
and ratio sensitivity c*(D_p/rhoMin+Pmax*D_rho/rhoMin^2), plus its own ratio
rounding. Reset of scratch is exact, not a free physical-state reinitialization.
Effective tau's actual floating computation and positivity alpha branch must
match the frozen scope; Sc0 does not authorize ignoring those code paths.

## 6. Two steps: equations are explicit, acceptance radii are not closed

Starting from common x0/xb0 and no wrap/rebuild, exact-copy xb1=x0 gives

```
D_x,2  <= (h^2/m)*(2D_F,0+D_F,1)+2r_x,0+r_x,1
D_vS,2 <= (h/(2m))*(2D_F,0+D_F,1)
           +(2r_x,0+r_x,1)/(2h)+r_v,1.
```

At the second rotation, apply sections3-4 with D_b,1,D_q,1 and D_T,1; do not
reset them to zero. Critically,

```
D_F,1 <= sum_i |a_i,A(state_A1)-a_i,B(state_B1)| + E_A1+E_B1
```

(and corresponding T/seed terms). It is NOT automatically2E93. The individual
difference requires a certified occupancy/surface/population/rotation formation
enclosure; if a complete input cohort matches, unchanged contributions are
instead bitwise. Candidate identity/branches remain exact prerequisites.

Equivalently, on one certified branch let z collect x,xb,vS,b,wS,q,f/moments.
If a nonnegative enclosure M_n bounds the COMPLETE source-map sensitivities,
and J_n injects only reduction-order uncertainty U_n, then

```
D_z1 <= J_0 U_0+R_0
D_z2 <= M_1*(J_0 U_0+R_0)+J_1 U_1+R_1.
```

Formation sensitivities belong in M; local formation rounding in R; do not
also add them a second time inside U. This is a conditional propagation
identity, NOT a certified value of M_1 or a general stability theorem.

## 7. Critical closure stop (UNRESOLVED)

- Discrete phases are known, but initial physical velocity/rotation time
  conventions cannot be obtained by renaming caches. Review the bootstrap
  interpretation before declaring physical endpoint energy/angular balances.
- No frozen interval certificate yet encloses ALL occupancy/legacy early-continue
  predicates, cell eligibility, periodic-image choice, rebuild Alpha, density,
  tau/limiter branches and quaternion norm through the proposed error boxes.
  Edge tangency can destroy a uniform derivative bound; legacy continue can
  change other edge contributions. Small observed differences are not margins.
- The local arithmetic enclosures above and the complete second-step M_1 have
  not been certified/instantiated for the actual compiled maps and recorded I.
  Consequently no complete one/two-step x/w/q/fluid tolerance is registered.
- Histories/events are discrete piecewise laws, not a smooth extension of M.
  A branch ambiguity is UNRESOLVED, never paid for by a force/trajectory epsilon.

Thus C-E/C-F are PARTIAL. Do not execute or adopt KN, claim design completion,
or infer a long-time bound. Targeted derivation can pin primitives/I and prove
branch-separated one/two-step envelopes using frozen data. If some physical
accuracy question needs convergence rather than a rigorous perturbation bound,
preregister a separate timestep-refinement/independent physical-oracle study;
no such study runs here and empirical agreement cannot waive structural checks.
