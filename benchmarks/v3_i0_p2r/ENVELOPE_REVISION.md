# Proved envelope extension, not a tolerance change

First frozen suite passed; first supplemental sweep explicitly rejected some
cases (including seeded_6) whose stored inputs span ~350 exponents, beyond the
initial >=2^-200 normalized-input envelope. Original outputs are preserved in
raw/attempt1. No zero or incorrect sign was returned as an accepted result.
Supplemental geometries are not regenerated or removed.

The same expansion algorithm permits normalized nonzero inputs >=2^-400:
normalized input least bit >=2^-452, half-dx least bit >=2^-453; therefore all
exact quadratic terms are integer multiples of2^-906. Magnitudes are bounded
by a small constant (<64 before expansion); neither TwoSum nor FMA residuals
underflow/overflow. Capacity56-term proof unchanged. This extension is derived
from binary64's normal exponent range, not fitted to error outcomes.

Positive final lengths that underflow when rescaled are explicitly unsupported
(NaN), never silently zero. Such an unrepresentable length is outside the
output contract; none of the registered suites require it. Input scale remains
[-400,400]. No mathematical model, frozen fixture, reference or budget changed.
