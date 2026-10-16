# Shared FP64 expansion algorithm and support contract

One host/device implementation, lib/dem/sphere_cube_robust.h, called by new CPU
and CUDA wrappers. All components and operations are binary64; no long double,
FP32, external big-number library or CPU-only precision repair.

## Option A chosen; Option B not implemented

Every edge uses compensated exact expansions for coordinate differences,
squared line margin and endpoint margins. General TwoSum and FMA TwoProduct
retain both rounding residuals. Grow-expansion-zero-elim follows the arithmetic
construction described by [Shewchuk's robust predicates work](https://www.cs.cmu.edu/~quake/robust.html).
This is a small independent bounded-expression implementation, not a copied
geometry predicate or an imported solver oracle. Fraction and unchanged
quadratic references independently test the actual compiled routines.

A fast ordinary filter would need outward bounds for coordinate subtraction,
products, margin, square root conditioning AND endpoint clipping. Margin-only
epsilon tuning cannot bound edge-length error. A directed interval filter that
certifies signs and the final output interval could be considered later, but is
unnecessary here. Fully compensated Option A avoids that additional proof and
has no ordinary fast path/adaptive ambiguity threshold. Performance not accepted.

## Exactness envelope

Finite dx>0,R>=0; maximum original input exponent[-400,400]. Normalize all
original stored coordinates,R,dx by a common exact power of two. Nonzero
normalized inputs must be>=2^-400. Coordinates are NEVER rounded before their
low terms are captured. Normalization is exact under the envelope.

For each perpendicular edge coordinate, grow C,-X,and signed dx/2 independently.
At most3 components. Least normalized original input bit>=2^-452, half-dx
least bit>=2^-453; every quadratic term is a multiple of2^-906. All products,
FMA residuals and nonzero expansion sums remain normal, well above2^-1022;
magnitudes are small constants (<128 including endpoint margins). No overflow
or transform underflow. R² adds at most2 terms, each squared coordinate18,
line margin38, endpoint margin56. Fixed capacity64 is sufficient, with no
truncation or dynamic allocation. Zero-eliminated nonoverlapping expansions
give their exact sign from the most significant nonzero component.

Outside the envelope the helper returns NaN, NOT zero. Coupled preflight checks
current image geometry and rejects before imprint. A positive result that
underflows on final rescaling is explicitly unsupported (NaN), not silently
clamped; none of the registered suites require an unrepresentable output.
No claim for arbitrary binary64 exponent mixtures or generic polyhedra.

## Finite-segment clipping

Line margin<=0 gives exact tangency/no covered length. For positive margin,
form exact local endpoints lo=C_axis-X_axis-dx/2 and hi=...+dx/2. Their signs
and exact margins m-lo²,m-hi² certify disjointness and endpoint membership.
If both endpoints are inside,return dx. If the whole chord is inside the
segment,return2sqrt(m). For a partial tiny interval sqrt(m)-abs(endpoint),
evaluate the equivalent (m-endpoint²)/(sqrt(m)+abs(endpoint)); its numerator
is an exact expansion, so no near-equal rounded roots are subtracted. Other
branches add quantities of the same sign. The square root and final length
are rounded FP64 approximations, not exact algebraic outputs. Last-bit upper
bounds ensure L<=dx and total<=12dx; there is no positive minimum, geometric
epsilon, smoothing, or positive-to-zero clamp.

Explicit CUDA rn add/multiply/divide/FMA and CPU volatile rounding boundaries
preserve transforms with the existing compiler flags. sqrt is ordinary FP64.
No global fast-math or contraction option changes. The exact sign does not
depend on summing an already-rounded two-component approximation; all expansion
components participate. Diagnostic hi/lo is a compact estimate plus exact sign.

## Independent checks and diagnostic operation counts

45,792 total frozen+supplemental per-edge comparisons. Exact Fraction line
margin signs and finite-segment positivity agree for every tested edge. Frozen
all49 failures/backend resolve; maximum absolute edge error6.204e-16,
gamma7.456e-17. Supplemental scales vary from2^-400 to2^400; worst normalized
edge error1.781e-16*dx (raw large-coordinate absolute error~2.096e104 has
dx~2.582e120). No positive misses,false positives,invalid lengths/gamma.
Frozen expected values/tolerances unchanged, including numerical reference dust.

All measured edges use compensation and exact expansion; zero ordinary-only
edges,zero separate exact-predicate fallback and maximum adaptive depth0.
This does NOT mean exact arithmetic was unused: it is unconditional. Counts
per backend/dataset are in FALLBACK_STATISTICS.csv. Representative sample
NOT_RUN after the strict compatibility stop; no speed claim.
