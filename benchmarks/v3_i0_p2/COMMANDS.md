# Commands actually executed

Working directory /tmp/mechsys-v3-i0-p2.d7OPg0/work; RUN below is the new
/tmp/mechsys-v3-i0-p2.d7OPg0/raw directory. No timed benchmarks.

```bash
git clone https://github.com/marcoprevitali/mechsys.git /tmp/mechsys-v3-i0-p2.d7OPg0/work
git switch -c fix/v3-i0-p2-edge-proxy e0d6c2fcc581b4caf9d020ebbf05f15c2f5a102f
git remote add upstream https://github.com/Axtal/mechsys.git
git remote set-url --push upstream PUSH_DISABLED
git config remote.pushDefault origin
git config push.default simple
python3 benchmarks/v3_i0_p2/TWELVE_EDGE_REFERENCE.py --output benchmarks/v3_i0_p2 --old-raw /tmp/mechsys-v3-i0.30PYI0/raw/final --failures benchmarks/v3_i0/PROXY_CONTROL_FLOW_FAILURES.json
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2/edge_probe.cu --output "$RUN/legacy-edge-build"
"$RUN/legacy-edge-build/cpu" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/legacy-cpu.csv"
"$RUN/legacy-edge-build/cuda" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/legacy-cuda.csv"
# All sixteen matching-backend outputs asserted bitwise equal to archived gamma.
# Preregistration committed at88eb5a2, then candidate implemented.
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2/edge_probe.cu --output "$RUN/corrected-edge-build"
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p2/probe.cu --observe --output "$RUN/coupled-build"
"$RUN/corrected-edge-build/cpu" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/corrected-cpu.csv"
"$RUN/corrected-edge-build/cuda" < benchmarks/v3_i0_p2/GEOMETRIES.txt > "$RUN/corrected-cuda.csv"
python3 benchmarks/v3_i0_p2/check_edges.py --raw "$RUN" --output /tmp/mechsys-v3-i0-p2.d7OPg0/edge-analysis
# Exit1:98 edge mismatches. Hard stop; NO P2-enabled coupled runs after this.
mkdir /tmp/mechsys-v3-i0-p2.d7OPg0/reference
git archive e0d6c2fcc581b4caf9d020ebbf05f15c2f5a102f | tar -x -C /tmp/mechsys-v3-i0-p2.d7OPg0/reference
python3 benchmarks/v3_i0/build.py --root /tmp/mechsys-v3-i0-p2.d7OPg0/reference --source benchmarks/v3_i0_p2/probe.cu --observe --output "$RUN/reference-build"
# P2_MODE unset/false in all existing P1 controls below.
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN/p1-regression" --observer "$RUN/coupled-build" --reference "$RUN/reference-build" --backend cpu --register
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN/p1-regression" --observer "$RUN/coupled-build" --reference "$RUN/reference-build" --backend cpu
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN/p1-regression" --observer "$RUN/coupled-build" --reference "$RUN/reference-build" --backend cuda
python3 benchmarks/v3_i0_p1/analyze.py --raw "$RUN/p1-regression" --output "$RUN/p1-regression-analysis"
python3 benchmarks/v3_i0/build.py --source benchmarks/v2/reference_suite.cu --output "$RUN/standalone-vv-build"
python3 benchmarks/v2/run_suite.py --build "$RUN/standalone-vv-build" --output "$RUN/standalone-vv" --cases 0 1 9 --laws 0 --damping 1
# Two original coupled VV guard calls, P1_MODE=0/P2_MODE=0/audit1:
"$RUN/coupled-build/cpu" moving "$RUN/legacy-vv-guard-cpu" 1
"$RUN/coupled-build/cuda" moving "$RUN/legacy-vv-guard-cuda" 1
python3 benchmarks/v3_i0_p2/diagnose_failure.py
OPENBLAS_NUM_THREADS=1 python3 benchmarks/v3_i0_p2/model_accuracy.py
python3 benchmarks/v3_i0_p2/publish.py --raw "$RUN" --edges /tmp/mechsys-v3-i0-p2.d7OPg0/edge-analysis
```

Build manifests contain expanded compile/link commands and source/header/binary
hashes. Run manifests/checkpoint validation store complete arguments, input
parameters, expected exits and hashes. Generated analysis artifacts do not
overwrite original V3-I0/P1 evidence. External DELIVERY.json records completion
of origin-only push/new full clone/archive checks (scientific result stays FAIL).
