# Serialization audit

The original gate hashes state-0/1/2.json bytes. ORIGINAL_FAILURE.csv verifies
the actual archived reference/off files, not a later favorable pair. It reports
18 differing binary64 fields at state1,20 at state2; history and pair identities
are identical. Original verdict P2R-K FAIL is unchanged.

Probe report/stage (benchmarks/v3_i0_p2r/probe.cu) serializes named fields,
vectors and loops over particle indices, candidate array order and fixed z/y/x
cell order. lib/dem/checkpoint.h:18-20 uses17 significant digits and rejects
nonfinite output. Binary64 finite numbers round-trip. JSON contains no wall
timestamps, raw C++ padding, pointer values, elapsed-time text or unordered-map
iteration. Simulation clocks are real compared state, not ignored metadata.
run.log includes timings and is deliberately NOT a numerical-state oracle.

The parser canonicalizes object key order, preserves array order/length and
empty-node/object/array structure, and translates numeric strings into exact
binary64 bit patterns. Alternate spelling 1/1.000 hashes identically;
+0/-0 retain distinct bits (ULP distance0); negative-number ULP order is correct
across zero. Infinities are handled explicitly; NaNs are NEVER accepted as
equal, even to the same NaN bit pattern. Self-tests cover these cases, adjacent
negative/positive floats, subnormals across zero, missing array items and numeric
formatting. No actual run contains nonfinite fields.

Separate CSV columns retain file hashes, full parsed-state hashes, particle
hashes, contact/common/GPU-history hashes, ordered pair hashes and complete
claim hashes. All45 baseline-baseline,45 candidate-candidate and100 cross pairs
are compared at11 chronological snapshots, including after first imprint and
first particle update, not only final trajectories.

Both executables have one initial hash and two first-step numerical/particle
hashes. Baseline has three final hashes; candidate four. File-hash differences
correspond to real parsed force/torque/angular-state differences, NOT formatting.
Contact histories remain empty/exact,93 pair IDs/order exact. Full fluid grid
values remain bitwise equal across all20 runs at each of state0/1/2, despite
particle angular-state differences.

Classification: A file difference, B serialized numerical difference,
C accumulated-force/torque difference and D small rotational trajectory
difference. E changed DEM histories is NOT observed. This is not CASE D
(serialization-only). Do not weaken the parser to discard force/torque fields.
