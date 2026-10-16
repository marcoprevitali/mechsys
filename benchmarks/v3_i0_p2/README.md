# V3-I0-P2 — stopped at independent geometry gate

**FAIL, not validated for coupled use.** Both candidate helpers miss a small
near-tangent edge under the frozen per-edge error budget. Do not enable
`CorrectTwelveEdgeProxy`, merge this experiment, or infer coupled acceptance.
Default remains false. Previous P1 acceptance and historical failures survive.

Start with V3_I0_P2_DECISION.md and MINIMAL_COUNTEREXAMPLE.json.
Authoritative state: PROJECT_STATUS.md §5.12; PROJECT_STATE.md is its pointer.
The new independent full clone started at exact P1 tip
e0d6c2fcc581b4caf9d020ebbf05f15c2f5a102f. Branch fix/v3-i0-p2-edge-proxy.
Original checkout and every previous clone were read only.

## What was executed

1. Recovered all sixteen exact archived V3-I0 failed geometries and their
   upper/lower/vertical contributions. Compiled legacy CPU/CUDA helper values
   reproduce archived gamma bitwise. Largest original error .0763580745930353.
2. Registered 1,254 geometries, expected twelve-edge lengths and unchanged I0
   tolerances at commit 88eb5a213a9fe14ae85efc63b9a33020e1f4ebdc **before**
   production changes. Independent Python Decimal quadratic reference, 70 digits,
   exact binary64 inputs; no solver imports. Cube symmetries, translations xyz,
   named limiting geometries, radius monotonicity, continuity, seed 20261016.
3. Compiled candidate CPU/CUDA helpers. 30,096 individual edge comparisons:
   98 failures (49 fixtures/backend), all one near-tangent geometry and its 48
   cube symmetries. Preserved complete failed batch, not a selected PASS.
4. Stopped all P2-enabled coupled/parity/conservation runs per work order §13.
   No post-failure tolerance changes, numerical repair, Scheme A or speed work.
5. Separately reran existing P1 and default-off compatibility controls, **P2
   false throughout**: 140 completed processes, two shared rejections, 46
   non-shared off/reference bitwise comparisons, zero independent P1 failures.
   Six standalone VV/restart comparisons (cases 0,1,9; law0/damping1;
   CPU/CUDA) bitwise; three CPU/GPU comparisons pass existing budgets. Original
   coupled VV guard rejects on both backends. Not full V2 suite recertification.
6. Analysis-only edge-versus-volume diagnostic; never used by solver or as gate.

## Candidate implementation (unaccepted)

Only three production headers changed: lib/dem/special_functions.h adds the
independent-edge CPU helper; lib/lbmdem/lbmdem.cuh adds CUDA helper/flag/routing;
lib/lbmdem/Domain.h adds default-off mode, routing and restrictive guards.
Legacy helper bodies, gamma-to-B expressions, Omega, collisions, contact laws,
integration and checkpoint code remain unchanged. Both helpers can expose all
twelve edge lengths. Their FP64 axis projections avoid cross-edge `continue`,
but do not resolve near-tangent geometric rounding: see failure witness.

Intended mode requires ConservativeSphereCells=true, canonical centered spheres,
single geometric owner (P1 guard), Fconv=1, unit dx/dt, single D3Q15 fluid,
Sc=G=Gmix=0, default B function, zero body force, tau>.5 and legacy integration.
A conservative pre-collision triangle-bound guard is present to reject limiter
risk; it can reject safe states. **New P2 guard/runtime semantics are compile
only, NOT validated** because the earlier helper gate failed. No shared-cell,
limiter or coupled-VV support claim. Do not confuse intended scope with acceptance.

## Reproduction

Exact compiler/link/header/executable/input hashes are in PROVENANCE.json.
CPU g++13.3, CUDA12.6 sm_86, FP64/O3/C++17, no fast-math; A6000 driver595.84.
Builds at dirty preregistration HEAD are identified by verified byte hashes,
not falsely attributed to a clean implementation SHA. Keep output paths unused.

```bash
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2/edge_probe.cu --output "$RUN/corrected-edge-build"
"$RUN/corrected-edge-build/cpu" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/corrected-cpu.csv"
"$RUN/corrected-edge-build/cuda" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/corrected-cuda.csv"
# Legacy CSVs are from the same source harness built against the e0d6c2f archive.
python3 benchmarks/v3_i0_p2/check_edges.py --raw "$RUN" --output "$RUN/edge-analysis"
# Expected failure: 98 individual edge mismatches; do not proceed to P2 coupled runs.
python3 benchmarks/v3_i0_p2/diagnose_failure.py
OPENBLAS_NUM_THREADS=1 python3 benchmarks/v3_i0_p2/model_accuracy.py
```

Initial preregistration command (requires archived raw V3-I0 snapshots):

```bash
python3 benchmarks/v3_i0_p2/TWELVE_EDGE_REFERENCE.py --output "$REG" --old-raw "$I0_RAW/final" --failures benchmarks/v3_i0/PROXY_CONTROL_FLOW_FAILURES.json
```

Raw evidence and archive verification are stored separately under the new
`/home/msys/SIMS/mechsys_v3_i0_p2_validation/20261016-edge-proxy-stopped/`.
P2_RAW.tgz retains binaries, failed result batch, compiler logs, compatibility
traces and standalone checkpoints. External DELIVERY.json records exact final
commit/remote/clean state, not scientific acceptance. No prior evidence overwritten.
