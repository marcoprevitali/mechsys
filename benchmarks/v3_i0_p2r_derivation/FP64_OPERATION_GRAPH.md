# Actual binaries and arithmetic graph boundary

Frozen baseline SHA256
3ca0d0c65992015065c5907f451430b049d94b22bdd6f94e21e6f302129144f7;
candidate SHA256
12b44d4de0e70fc1be203180a3bb369308688c9dab1e653165093689cc3565ca.
Both have embedded PTX8.5/sm86. Existing EXECUTABLES.json pins nvcc12.6.85,
FP64,C++17,O3,default fmad enabled,no fast math,ftz false and all headers.
No binary was rebuilt. extract.py extracts PTX and host AddSphere disassembly;
whole SASS remains in the immutable R raw archive.

## Certified compiled translation slice

Both embedded Translate PTX definitions are byte-identical. Actual SASS has
DADD doubling, DADD subtracting xb, div.rn coefficient lowering, and DFMA at
0x04a0/0x04c0/0x04e0 for the three new coordinates (candidate Translate).
The nominal scalar graph is:

```text
d = RN(x+x); b = RN(d-xb)
k = RN(RN(h*h)/m)
xNew = RN(F*k+b)                  [one FMA, not mul then add]
vNew = RN(RN(.5*RN(xNew-xb))/h)
xbNew = copy(x)
```

The FP64 division/sqrt lowerings contain reciprocal/rsqrt refinements and
slow paths; they are not treated as one MUFU approximation. We use the
documented IEEE RN semantics of the *complete* div.rn.f64/sqrt.rn.f64
instructions. No proof for a bare approximate reciprocal is claimed.

The native nine RED.E.ADD.F64.RN destinations were established by the frozen
R SASS audit, not newly assumed. Each address gets its own 93-term order.

## Pinned but still CONDITIONAL graph families

ARITHMETIC_GRAPHS.json contains complete frozen Rotate,Translate,BnSmooth,
collision and streaming PTX. IMPRINT_GRAPH_SUFFIX.json retains the relevant
surface/force/body-torque suffix and hash of the entire extracted PTX.
FloatVM evaluates a resolved straight-line floating slice, NOT arbitrary
CUDA/PTX control flow. Integer counts, free flags and center-vertex conditions
are explicit premises, not silently inferred from a register value.

Crucially, plain PTX mul/add/sub may contract again in ptxas. Actual Rotate
SASS includes e.g. DFMA at0x09d0/0x09e0 and q-increment DFMA at0x0a80 where a
naive independent PTX mul/sub replay would introduce another rounding.
arithmetic.py retains the union of separate and immediate-one-FMA paths.
That is a mathematically enclosed graph FAMILY, not a completed proof that
EVERY executed SASS dataflow/reassociation belongs to that family.

| Operation | Implemented calculation | Current evidence limit |
|---|---|---|
|add/sub/mul/FMA/div/sqrt|exact-rational interval image with RN endpoint rounding|primitive certificate; no empirical epsilon|
|translation|resolved compiled DADD/DFMA graph|CERTIFIED for frozen input sum boxes|
|angular/ordered q update|frozen PTX floating slice; inertia exact isotropic; contraction union|CONDITIONAL pending complete SASS mapping audit|
|body/world Rotation|actual scalar-first quaternion helper and conjugate; no unit-norm assumption|CONDITIONAL PTX suffix graph|
|Feq|actual direction weights, y product then x/z FMA dot, ordered polynomial|CONDITIONAL caller/SASS correspondence|
|Bn|gamma*(tau0-.5)/[(1-gamma)+(tau0-.5)]|actual source/PTX; denominator proved in conditional boxes|
|collision|Bn from tau0 BEFORE effective tau; actual noneq/population-write sequence|CONDITIONAL arithmetic/branch correspondence|
|moments|15 sequential rho adds,15 FMA per momentum component, RN(Cs/rho)*moment|CONDITIONAL caller/SASS correspondence|
|stream|integer periodic push,exact population copy|15,000 destinations bijective; no arithmetic error on permutation|
|legacy SphereCube|actual early-continue source control flow, exact-rational RN/FMA-family probe|not a full compiled predicate/dataflow translation|

No old contract document is edited. One refinement to its shorthand is
recorded here: collision Bn uses tau0 BEFORE effective-tau evaluation in this
source, not a newly recomputed Bn from tau_eff. Similarly the formal startup
question is now explicitly separate from algorithmic compatibility.

The authoritative primitive reference is NVIDIA's
[PTX ISA8.5](https://docs.nvidia.com/cuda/archive/12.6.0/parallel-thread-execution/index.html),
sections9.7.3 (rounding,FMA,division,sqrt). Its semantics are not a trajectory
theorem and do not close the compiled-graph obligations above.
