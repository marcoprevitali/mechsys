# Rounded-term accumulation, not a blanket numerical waiver

For the frozen CUDA large first imprint, each scalar F/Flbm/body-T component
starts at exact zero and receives93 already-computed binary64 values a_i.
Identical contributions means the two lists match element-by-element bits;
the93 terms are NOT necessarily equal to each other. Native instructions are
FP64 round-to-nearest additions. Scalar atomic serialization may vary; each
address has its own order. All terms/intermediates must be finite, with no
overflow or unmodeled subnormal/flush behavior. F/Flbm are distinct accumulators.

## Derivation and preconditions

For normal RN results, fl(s+a)=(s+a)(1+delta), |delta|<=u, u=2^-53.
Expanding n successive updates, the exact coefficient of each rounded input
is a product of at most n such factors. If n*u<1, its deviation from1 is at
most gamma_n=n*u/(1-n*u). Therefore, for exact S=sum(a_i),

```
|S_GPU-S| <= E_sum = gamma_n * sum_i |a_i|.
|S_A-S_B| <= E_A+E_B = 2*E_sum       [same initial0, same terms/model]
```

n counts actual additions, including additions of zero. The first addition to
zero is exact; using n93 is conservative rather than claiming93 inexact steps.
Any permutation has the same sum_abs. Reference arithmetic must accumulate
exact binary rationals (or an independently certified high-precision result).
Do not add correct-reference rounding again if comparison uses the exact sum.

For a known nonzero seed s0, the same model gives
gamma_n*(|s0|+sum_abs) for S=s0+sum(a_i), provided s0 is an exact common input.
If its formation or value differs, that uncertainty is a separate input term.
This extension is mathematical, not acceptance of an untested mixed force path.
FMA contribution formation, partial/tree reductions and mixed initializers
need explicit graphs; do not apply sequential gamma93 to a different algorithm.

## Derived witness values (from frozen terms, not measured maxima)

gamma93=1.0325074129014063e-14. Rounded display below; future decisions use
exact/rational or outward-rounded bounds, not the last printed decimal.

| Scalar | E_sum | Pairwise allowance 2E_sum |
|---|---|---|
|F.x / Flbm.x|1.2053958324770065e-15|2.4107916649540130e-15|
|F.y / Flbm.y|6.02697916238488e-16|1.205395832476976e-15|
|F.z / Flbm.z|3.0134895811924437e-16|6.0269791623848874e-16|
|T.x body|5.122338687766165e-16|1.0244677375532330e-15|
|T.y body|1.0241330769658802e-15|2.0482661539317604e-15|
|T.z body|9.3341074170203e-16|1.86682148340406e-15|

These display values come from INDEPENDENT_SUMS.csv of the immutable audit;
the exact inputs are CONTRIBUTION_BITS.csv. The prior largest exact-sum error
4.526544070126981e-17 is a historical observation, NOT how the bounds were set.

Near cancellation, |S| can be tiny despite large sum_abs. Use absolute errors;
relative/ULP distances are diagnostics only, no universal ULP cutoff. NaN is
always failure; signed zero is retained in exact payload checks even though
its numerical distance is zero. Infinity is unsupported in this contract.

## What this does not buy

No allowance for changed cells, owners, histories, branch selection, occupancy,
contribution bits, units/frames, input orientation, mass/inertia or integration
phase. It also excludes contribution formation error and all subsequent state
propagation. Pairwise compatibility of evolved sums needs the DIFFERENT-term
triangle inequality plus separately derived term sensitivity, not 2E93 alone.

The RN/FMA/primitive assumptions must be pinned to the compiled graph. NVIDIA's
[CUDA12.6 floating-point reference](https://docs.nvidia.com/cuda/archive/12.6.0/floating-point/index.html)
describes default rounding and fused versus separate operations; the previous
SASS audit establishes the particular native accumulator instructions. Neither
reference supplies a theorem about this coupled trajectory.
