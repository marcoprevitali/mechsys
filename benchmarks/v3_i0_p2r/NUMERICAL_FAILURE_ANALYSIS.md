# Numerical failure and compatibility stop analysis

Original stored binary64 witness X=(.3,.2,.1),R1,C=(0,0,0),dx1,lower edge7.
Before production edits, both compiled P2 helpers reproduced all49 frozen
failures/backend. Original16 control-flow counterexamples remain in untouched
P2 ORIGINAL_FAILURE_GEOMETRIES.json. FROZEN_MANIFEST.json records all83 prior
evidence hashes and exact tolerance strings; no regeneration or weakening.

Actual CPU AND CUDA diagnostic values (raw arithmetic-{cpu,cuda}.csv):

| Quantity | Value |
|---|---:|
| q1 high | -.80000000000000004 |
| q1 coordinate tail | +5.5511151231257827e-17 |
| q2 high | -.59999999999999998 |
| q2 coordinate tail | -2.7755575615628914e-17 |
| rounded q1² / product tail | .64000000000000012 / -5.3290705182007512e-17 |
| rounded q2² / product tail | .35999999999999999 / -1.3322676295501878e-17 |
| R² | 1 |
| first separated subtraction | .35999999999999988 |
| ordinary separated final margin | -1.1102230246251565e-16 |
| FMA margin using already rounded coordinates | -5.7731597280508142e-17 |
| exact expansion margin (rounded display) | +1.1102230246251566e-17 |
| robust line intersection length | 6.6640018746250559e-9 |

Coordinate addition/subtraction tails are essential. Merely using FMA on the
rounded coordinates still gives the WRONG sign. Exact Fraction interpretation
of the original stored inputs gives margin
14411518807585587/1298074214633706907132624082305024. The unchanged independent
quadratic and robust expansion agree within the fixed budget.

CUDA global fmad defaults true,ftz false; CPU fp-contract defaults fast,
associative/unsafe math disabled. Explicit round-to-nearest intrinsics and
local host volatile boundaries protect TwoSum/product decompositions without
changing global production arithmetic. Both diagnostics preserve the smallest
double subnormal and its doubled value (4.9406564584124654e-324 and
9.8813129168249309e-324). The original witness uses normal operands; FTZ is not
its cause. The normalized expansion envelope avoids subnormal product tails.

## Exact zeros and unchanged frozen reference dust

The frozen70-digit quadratic has36 backend/edge entries with tiny nonzero
Decimal residuals at exact finite-segment zero intersections. Exact Fraction
classification proves these are genuinely zero; every old expected value is
retained and included in absolute/relative error tables. Hence the all-nonzero-
Decimal-reference maximum relative error is1, but the meaningful exact-positive
reference maximum is2.889e-16. This is NOT a changed reference or clamping of
positive geometry. Supplemental700-digit cases have no such residual entries.
All genuinely positive intersections are returned positive; false positives0.

## Strict default-off hard stop (separate from numerical remediation)

CUDA large required comparison differs in live force by up to1.38777878078e-17
and torque/rotation tails thereafter. Initial inputs, populations and
per-candidate claims are unchanged. Three repeats of the SAME unchanged
baseline executable produce two distinct state1 hashes and two state2 hashes.
Three candidate repeats also vary; baseline and candidate hash patterns overlap.
All six initial inputs and complete initial per-candidate claims are bitwise
identical. Existing atomicAdd live accumulation is strongly implicated; no
per-contact arithmetic difference is detected by this witness. See
DEFAULT_OFF_DIAGNOSIS.json and raw/default-off-diagnosis/.

This establishes baseline non-repeatability, not a waiver of the registered
strict gate or a general proof of all default-off equivalence. Keep P2R-K FAIL,
overall PARTIAL. Do not cherry-pick matching repeats or implement deterministic
force reduction without a separate scope decision. Tail compatibility cases and
representative operation sampling remain NOT_RUN after the stop.

## Preserved unsuccessful attempts

First stress run explicitly rejected31 inputs outside the initial exponent
envelope; r2 extended it by arithmetic proof (ENVELOPE_REVISION.md), not new
tolerances. First out-of-range negative test used a free sphere at1e130; actual
periodic wrapping converted its imprint pose into supported geometry. That
fixture's expected rejection was invalid, not a silent unsupported acceptance.
The fixed-sphere version retains the out-of-range pose and rejects correctly.
Both raw attempts survive. No prior P2 FAIL classification is rewritten.
