# Exact local arithmetic and what is actually certified

arithmetic.py uses Fraction and integer operations for decisions. A finite
binary64 is decoded exactly. For a rational x, its binade determines quantum
2^max(−1074,floor(log2|x|)−52); integer quotient/remainder implements ties-even.
For sqrt(x), monotone positive binary64 bit patterns are searched for adjacent
a,b with a²<=x<b²; comparing x with ((a+b)/2)² decides RN, including exact
ties. No ordinary high-precision result is passed off as an outward interval.

For interval inputs, exact rational endpoint arithmetic encloses add/sub,
four-corner product/division and FMA(ab+c). Division rejects a denominator
interval containing zero; sqrt rejects a negative lower endpoint. Monotonic
RN at the interval endpoints then encloses every rounded result. Repeated
variables may lose correlation and widen a box; that never narrows it.
FMA has one rounding. A plain multiply eligible for immediate add/sub
contraction retains both rounded and FMA images. This family still requires
an independently completed compiled-dataflow audit before production use.

Each logged node records input hulls, exact pre-rounding hull, RN output hull,
source/PTX operation tag, divisor floor and local absolute bound. For ordinary
operations the generic bound is u*max|exact result|+2^-1075; for singleton
rational nodes the exact rounding discrepancy is available instead. Subnormals
are supported in the arithmetic, not silently flushed. All primitive overflow
and zero-denominator conditions reject. Signed-zero *payload* identity belongs
to the frozen-bit manifest, not ordering of a real interval around zero.

The sqrt local bound uses a rational upper estimate of the real root from its
RN upper endpoint/(1-u), plus half the minimum subnormal. Norm inputs are
positive and near1 here; the verifier independently proves the exact-real
qD norm >99/100. The computed first-step norm helper has interval [1,1].
The actual pre-normalization qD is not assumed mathematically unit.

## Input and operation counts

- Scalar translation: add doubling,subtract predecessor,multiply h²,RN divide
  by actual m,FMA force increment,subtract,half-scale,RN divide for vS. Exact
  copies add no error. At h1, several power-of-two/unit operations are exact.
- Gyro component before division: inertia subtraction,multiply,FMA; all three
  actual I bits equal, so subtraction is exact0. One positive-I RN divide,
  FMA for wS and FMA for wb follow. The two Hamilton evaluations retain their
  actual product/add/FMA order. Quaternion squared norm uses one product and
  three FMA, then RN sqrt and four RN divides.
- Feq: dot products use a product then two FMA; polynomial is evaluated in the
  PTX caller order, with actual D3Q15 weights. The source ordered graph, not
  the reduced mathematical polynomial alone, determines local arithmetic.
- Collision retains Bn(tau0),15 NonEq formations,effective-tau sqrt path and
  each written fStar. For Sc0 and finite Q the 6*Q*Sc term is exactly0. EEk is
  (sum|e_j|)^2<=9; the finite small NonEq box bounds Q far from overflow.
- Moments:15 rho adds;15 FMA/component; one RN Cs/rho and three products.
  Streaming is a 15,000-element bijection with zero rounding.

All actual input bits, not symbolic unit mass/inertia, enter the generator.
Mass=4460.2238100565492, bits40b16c394b9da965. Host I=8634.993296269482,
bits40c0dd7f24550855 in all three components. The exact host constructor
instruction sequence multiplies the stored mass by binary64 .4,R,R, with RN
after each operation; both unchanged executables were observed immediately
after those stores. PropsReady prevents later property recomputation and
UploadParticle copies the three values. No archived device-I snapshot exists;
this distinction is preserved in FROZEN_STATE_BITS.json.

## First-step rounded-input certificate

For each of F and Flbm separately, and for each body-T component, the exact
93 stored terms give S=sum(a_i), A=sum|a_i| and E=gamma93*A, u=2^-53.
Force E displays: (1.2053958324770065e-15,6.02697916238488e-16,
3.0134895811924437e-16). Torque E displays: (5.122338687766165e-16,
1.0241330769658802e-15,9.3341074170203e-16). The two-order bound is2E per
component, never a sum of unrelated axes. Exact rational values are in JSON.

The generator proves n*u<1, bounded partial sums and a common dyadic quantum
for every rounded partial result, excluding nonzero subnormal partial sums.
Zero intermediates are exact. This justifies the gamma theorem's premises
rather than assuming severe cancellation cannot occur.
For the conditional second lists, gradual-underflow binary64 ADD is also
exact whenever its real result is subnormal: both operands, and therefore
their exact sum, are integer multiples of2^-1074. Thus the relative ADD model
still holds with delta=0 there. This is not true for a general product;
products are rounded by the separate exact endpoint machinery. The generator
checks a sum_abs*(1+gamma93) upper bound against finite binary64 range for
both steps. No unmodeled FTZ operation is admitted.

Propagating [S-E,S+E] through the compiled translation DAG makes x1,xb1,vS1
**single binary64 values** for all admissible atomic orders. This is stronger
than the generic recurrence h²*D_F/m+r_x; no measured zero difference was used
to select the interval. First angular/quaternion widths (conditional compiled
family): max wa/wb2.372052975208051e-19,wS1.1860264876040255e-19,
Q1.202252219630244e-19. These are interval diameters, not local errors or
approved acceptance tolerances. The largest logged single primitive local
bound is5.553306509544704e-16 (coordinate-scale arithmetic); inspect node
records for component/operation-specific values.

## Independent witnesses and limits

The verifier tests midpoint ties, binade boundaries, negative numbers,
subnormals, exact-square sqrt and sqrt midpoint decisions, a cancellation
witness distinguishing FMA from mul/add, positive m/I, real qD norm floor,
first translation, angular/q replay and evaluated two-step feedback. It also
rejects three deliberately corrupted in-memory certificate copies. No old
fixture/test is modified. Observation checks are performed only AFTER boxes
are generated. Agreement with observations is corroboration, not enclosure
proof. The remaining SASS/control-flow mapping and exchange-reference
allocation prevent whole-map PASS, even when every observation is enclosed.

Independent hand-derived dyadic witnesses additionally give x1=81/32,x2=97/32
and vS=33/64 for a synthetic m4 translation pair;the ordered q update for
q=(1,0,0,0),wb=(1/8,0,0),T0 gives qD=(1023/1024,1/16,0,0),norm1025/1024.
A four-population moment witness has rho1,u=(1/8,1/8,0). Zero-NonEq collision
is checked against exact rational B*Omega plus the incoming population for
separate and fused paths;all6 permutations of three cancelling rounded terms
obey their derived gamma3 bound. These are offline arithmetic proof units,
not new registered solver fixtures or a prospective compatibility harness.
