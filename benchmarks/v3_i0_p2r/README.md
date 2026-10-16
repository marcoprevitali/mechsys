# V3-I0-P2R — PARTIAL, strict default-off gate failed

Robust geometry and bounded coupled exchange tests pass. **Overall acceptance
is stopped at P2R-K:** the required default-off CUDA `large` comparison differs
bitwise. The unchanged baseline also fails self-repeatability. Do not silently
replace the strict gate with a tolerance, merge, or promote this experiment.

New full clone /tmp/mechsys-v3-i0-p2r.do4dZe/work; branch
fix/v3-i0-p2r-robust-tangency; base bf6616973be1335da1caa7d75f8a34aa0f6c1c22.
Preregistration fb6405ba334a457606903dd34efd1d606804983a; implementation
1bde930295a9852e64a810e02e22b2bba21f98fc. Final published tip/remote/clean proof
is external DELIVERY.json. Original and all previous clones are preserved.
Authoritative state remains PROJECT_STATUS.md; PROJECT_STATE.md is its pointer.

## Evidence

- Frozen P2:1,254 geometries/backend,30,096 individual edges; zero robust
  reference/sign/classification failures, including all49 old failures/backend.
  No old inputs, expected values, case IDs, random fixtures or budgets changed.
- Supplemental:654 new geometries/backend,15,696 edges; zero failures after a
  proved exponent-envelope extension. Initial explicit rejections retained.
- Coupled:23 identical initial cases/backend, two steps each;92,000 cell
  collisions/1,380,000 direction records. Stage1 parity and Stage2 coverage
  passed before independent exchange-ledger analysis. No independent failure.
- Compatibility:43/46 non-shared controls attempted,42 bitwise PASS, CUDA large
  strict FAIL, three CUDA tail controls NOT_RUN after stop. Existing P1-only
  regression PARTIAL, not claimed complete. Shared strict negative retained.
  Six registered standalone VV/checkpoint restarts remain bitwise;18 explicit
  unsupported-mode rejections pass before collision.
- Baseline diagnosis:three repeats of the SAME unchanged binary have two
  distinct state1 hashes. Initial inputs and per-candidate claims are identical
  across all six base/candidate diagnostic runs. Live force/torque sums vary,
  consistent with atomic accumulation ordering. This is not a waiver for K.

## Modes and scope

All three flags default false. The new robust experiment requires
ConservativeSphereCells=true, CorrectTwelveEdgeProxy=true and
RobustTwelveEdgeProxy=true. Legacy SphereCube and failed P2 helpers remain
independently callable; old P2 FAIL evidence/classification stays unchanged.
Do not enable old P2 mode alone as a validated correction.

Registered coupled subset:FP64, canonical centered single-owner spheres,
Fconv=1, unit dx/dt, D3Q15 single fluid,Sc=G=Gmix=0,default gamma-to-B,
zero body force,tau>.5,legacy integration and previously validated minimum-image
conventions. No production limiter activation or shared support. VV remains the
standalone reference; these coupled cases are labeled legacy compatibility
controls, never coupled VV. No Scheme A/restart/performance work.

Shared math is in lib/dem/sphere_cube_robust.h. Exact expansions preserve
original binary64 coordinate tails and margin signs. Local clipping and a
rationalized short-interval formula avoid losing small positive lengths.
See COMPENSATED_ARITHMETIC.md for explicit exponent/output limitations.

## Reproduce

Use unused paths. All exact compiler/link commands and binary/header/input
hashes are in PROVENANCE.json; no new fast-math/FTZ/contraction flags were
silently applied. CPU g++13.3; CUDA12.6.85/sm_86; A6000 driver595.84.

```bash
python3 benchmarks/v3_i0_p2r/freeze.py --output benchmarks/v3_i0_p2r/FROZEN_MANIFEST.json
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2r/edge_probe.cu --output "$RUN/edge-build"
"$RUN/edge-build/cpu" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/frozen-cpu.csv"
"$RUN/edge-build/cuda" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/frozen-cuda.csv"
"$RUN/edge-build/cpu" < benchmarks/v3_i0_p2r/STRESS_GEOMETRIES.txt > "$RUN/stress-cpu.csv"
"$RUN/edge-build/cuda" < benchmarks/v3_i0_p2r/STRESS_GEOMETRIES.txt > "$RUN/stress-cuda.csv"
# Also supply base-cpu.csv/base-cuda.csv from the P2 edge_probe built at bf66169.
python3 benchmarks/v3_i0_p2r/check_geometry.py --raw "$RUN" --output "$RUN/geometry-analysis"
# Only if all geometry gates pass:
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2r/probe.cu --observe --output "$RUN/coupled-build"
python3 benchmarks/v3_i0_p2r/coupled_run.py --build "$RUN/coupled-build" --raw "$RUN/coupled" --backend cpu --geometry-summary "$RUN/geometry-analysis/GEOMETRY_SUMMARY.json"
python3 benchmarks/v3_i0_p2r/coupled_run.py --build "$RUN/coupled-build" --raw "$RUN/coupled" --backend cuda --geometry-summary "$RUN/geometry-analysis/GEOMETRY_SUMMARY.json"
python3 benchmarks/v3_i0_p2r/coupled_precheck.py --raw "$RUN/coupled" --output "$RUN/coupled-analysis"
python3 benchmarks/v3_i0_p2r/coupled_analyze.py --raw "$RUN/coupled" --output "$RUN/coupled-analysis"
```

Stress data is a separate frozen new registration; do not rerun stress.py over
it (the generator refuses overwrite). It uses seed2026101602 and the unchanged
P2 quadratic with Decimal700 plus independent exact Fraction classification.
Per-edge reported numbers are formatted for compact publication only AFTER
full-precision acceptance checks. Raw17-digit solver traces and full inputs
are preserved in the archive; no tolerance or reference was rounded for gating.

FALLBACK_STATISTICS.csv counts frozen/stress work only:all edges compensated,
exact expansion always,zero ordinary-only edges or adaptive fallback/depth.
A2,100-candidate representative sample was prepared but NOT_RUN after K;
its operation counts are not fabricated. No speed qualification.

Archive namespace:
/home/msys/SIMS/mechsys_v3_i0_p2r_validation/20261016-robust-tangency-partial/.
P2R_RAW.tgz, ARTIFACT_INDEX.csv/verification and DELIVERY.json preserve all
attempts, baseline repeats, binaries, input states, populations and checkpoints.
Persistent delivery target /home/msys/git/mechsys-v3-i0-p2r-robust-tangency.
