# Executed bounded workflow and exact output locations

RUN=/tmp/mechsys-v3-i0-p2r.do4dZe/raw;working directory new isolated clone
/tmp/mechsys-v3-i0-p2r.do4dZe/work. Canonical runtime builds are
robust-edge-build-r2,coupled-build,reference-build,arithmetic-build and
standalone-vv-build. Expanded compiler/link commands and hashes:PROVENANCE.json.
No production benchmark or optimization campaign.

```bash
git clone https://github.com/marcoprevitali/mechsys.git /tmp/mechsys-v3-i0-p2r.do4dZe/work
git switch -c fix/v3-i0-p2r-robust-tangency bf6616973be1335da1caa7d75f8a34aa0f6c1c22
git remote add upstream https://github.com/Axtal/mechsys.git
git remote set-url --push upstream PUSH_DISABLED
git config remote.pushDefault origin
git config push.default simple
python3 benchmarks/v3_i0_p2r/freeze.py --output benchmarks/v3_i0_p2r/FROZEN_MANIFEST.json
python3 benchmarks/v3_i0_p2r/stress.py --output benchmarks/v3_i0_p2r
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2/edge_probe.cu --output "$RUN/base-edge-build"
"$RUN/base-edge-build/cpu" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/base-cpu.csv"
"$RUN/base-edge-build/cuda" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/base-cuda.csv"
# Baseline failure audit records49/backend;preregistration committed before edits.
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2r/edge_probe.cu --output "$RUN/robust-edge-build"
# First complete sweep: frozenPASS,31 stress inputs explicitly unsupported.
# All first outputs remain at raw/attempt1;old helper source recovered/hash-verified.
# Proved exponent extension;no fixture/tolerance change.
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2r/edge_probe.cu --output "$RUN/robust-edge-build-r2"
"$RUN/robust-edge-build-r2/cpu" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/geometry-r2/frozen-cpu.csv"
"$RUN/robust-edge-build-r2/cuda" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/geometry-r2/frozen-cuda.csv"
"$RUN/robust-edge-build-r2/cpu" < benchmarks/v3_i0_p2r/STRESS_GEOMETRIES.txt > "$RUN/geometry-r2/stress-cpu.csv"
"$RUN/robust-edge-build-r2/cuda" < benchmarks/v3_i0_p2r/STRESS_GEOMETRIES.txt > "$RUN/geometry-r2/stress-cuda.csv"
python3 benchmarks/v3_i0_p2r/check_geometry.py --raw "$RUN/geometry-r2" --output /tmp/mechsys-v3-i0-p2r.do4dZe/geometry-analysis-final
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2r/probe.cu --observe --output "$RUN/coupled-build"
python3 benchmarks/v3_i0_p2r/coupled_run.py --build "$RUN/coupled-build" --raw "$RUN/coupled" --backend cpu --geometry-summary /tmp/mechsys-v3-i0-p2r.do4dZe/geometry-analysis-r2/GEOMETRY_SUMMARY.json
python3 benchmarks/v3_i0_p2r/coupled_run.py --build "$RUN/coupled-build" --raw "$RUN/coupled" --backend cuda --geometry-summary /tmp/mechsys-v3-i0-p2r.do4dZe/geometry-analysis-r2/GEOMETRY_SUMMARY.json
python3 benchmarks/v3_i0_p2r/coupled_precheck.py --raw "$RUN/coupled" --output /tmp/mechsys-v3-i0-p2r.do4dZe/coupled-analysis
python3 benchmarks/v3_i0_p2r/coupled_analyze.py --raw "$RUN/coupled" --output /tmp/mechsys-v3-i0-p2r.do4dZe/coupled-analysis
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2r/arithmetic_probe.cu --output "$RUN/arithmetic-build"
"$RUN/arithmetic-build/cpu" > "$RUN/arithmetic-cpu.csv"
"$RUN/arithmetic-build/cuda" > "$RUN/arithmetic-cuda.csv"
mkdir /tmp/mechsys-v3-i0-p2r.do4dZe/reference
git archive bf6616973be1335da1caa7d75f8a34aa0f6c1c22 | tar -x -C /tmp/mechsys-v3-i0-p2r.do4dZe/reference
python3 benchmarks/v3_i0/build.py --root /tmp/mechsys-v3-i0-p2r.do4dZe/reference --source benchmarks/v3_i0_p2r/probe.cu --observe --output "$RUN/reference-build"
python3 benchmarks/v3_i0_p2r/negative_tests.py --build "$RUN/coupled-build" --output "$RUN/negative-tests-r2"
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN/p1-regression" --observer "$RUN/coupled-build" --reference "$RUN/reference-build" --backend cpu --register
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN/p1-regression" --observer "$RUN/coupled-build" --reference "$RUN/reference-build" --backend cpu
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN/p1-regression" --observer "$RUN/coupled-build" --reference "$RUN/reference-build" --backend cuda
# CUDA runner stops on large strict off mismatch. No tail/representative runs.
python3 benchmarks/v3_i0/build.py --source benchmarks/v2/reference_suite.cu --output "$RUN/standalone-vv-build"
python3 benchmarks/v2/run_suite.py --build "$RUN/standalone-vv-build" --output "$RUN/standalone-vv" --cases 0 1 9 --laws 0 --damping 1
# 3 baseline+3 candidate diagnostic large repeats, flagsall0,R2.2,audit1.
# Exact arguments/hashes in raw/default-off-diagnosis/RUNS.json.
python3 benchmarks/v3_i0_p2r/audit_default_off.py --raw "$RUN" --output benchmarks/v3_i0_p2r/DEFAULT_OFF_DIAGNOSIS.json
python3 benchmarks/v3_i0_p2r/publish.py --raw "$RUN" --geometry /tmp/mechsys-v3-i0-p2r.do4dZe/geometry-analysis-final --coupled /tmp/mechsys-v3-i0-p2r.do4dZe/coupled-analysis
```

Raw also retains failed first negative-fixture expectation,compile-only
robust-edge-final/coupled-final-build snapshots with an equivalent FP64 typedef
spelling,and prepared representative geometry inputs. They are NOT substituted
for accepted runtime runs. Final production headers exactly match the canonical
runtime manifests after restoring that typedef spelling; verified before commit.
