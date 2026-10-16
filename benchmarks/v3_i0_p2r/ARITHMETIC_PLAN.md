# Pre-implementation arithmetic plan

Use Option A: every edge compensated. Exact finite floating expansions for the
coordinate differences and squared margin, built with general TwoSum and
FMA TwoProduct. One common host/device helper. No ordinary filter and no
ambiguous-sign-to-zero rule. This is stronger than a fixed double-double sign
estimate: retain every exact product/addend in the bounded-degree expression.

Normalize by an exact power of two. Supported input envelope: finite inputs,
dx>0,R>=0, maximum nonzero input exponent in [-400,400], and each nonzero
normalized original input >=2^-200. Unsupported helper calls return NaN;
coupled mode rejects unsupported geometry before imprint. This envelope includes
the frozen fixtures, registered supplemental scales/offsets and unit-grid
coupled cases; no claim for all binary64 exponent combinations.

After normalization, input magnitude<2. Each coordinate sum of three inputs
needs at most3 expansion components. A square needs at most18 components;
R² minus two squares needs at most38; endpoint margin at most56. Capacity64.
All relevant exact low product terms remain normal: original normalized
binary64 inputs have least bit >=2^-252; dx/2 least bit >=2^-253; quadratic
terms >=2^-506. No overflow/underflow within this envelope.

Use exact signs for finite-segment endpoint classification. For a partial
interval root-|endpoint|, use the rationalized exact endpoint margin divided
by root+|endpoint|, avoiding loss from subtracting close rounded square roots.
Root and final positive lengths are rounded binary64 approximations; neither
zero-tolerance floors nor geometric epsilons are introduced.

Option B considered: a legitimate filter must bound coordinate errors, product
errors, cancellation, sqrt conditioning AND endpoint clipping. A margin-only
threshold is insufficient. An outward-rounded interval filter could certify
both signs and absolute output error, otherwise falling back to this exact
expansion. It is not implemented: correctness/maintainability are the current
objective, not speed, and Option A avoids an additional proof and branch.

Frozen acceptance is exactly P2's per-edge abs1e-10*dx plus rel1e-9 term.
Supplemental tests additionally require exact positive/zero edge classification
and exact squared-margin signs. No old inputs/references are regenerated.
