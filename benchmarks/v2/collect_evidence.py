#!/usr/bin/env python3
"""Collect compact evidence without copying trajectories or changing verdicts."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--raw",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[2]
inputs={
    "standalone":"closure-matrix/validation.json",
    "polyhedra":"poly-closure/validation.json",
    "rebuild_before":"rebuild-before/validation.json",
    "rebuild_after":"rebuild-after/validation.json",
    "separated_restart":"separated-restart/validation.json",
    "independent_spheres":"independent-closure.json",
    "independent_features":"feature-audit/results.json",
    "invalid_checkpoints":"invalid-final/results.json",
    "coupled_legacy_and_rejections":"coupled-final-runs/results.json",
    "coupled_original":"coupled-runs/results.json",
    "v1_regression":"v1-regression-runs/results.json",
    "registered_vv_regression":"registered-vv-regression/results.json",
    "zero_candidates":"zero-runs/results.json",
    "poly_strict_storage_failure":"poly-registered/validation.json",
}
index={"reference_commit":"73466999e0601a083fb9718281d88d161c75231d",
       "collection_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
       "overall_status":"PARTIAL","C2":"BLOCKED: user deferred coupled VV design","P2_B":"NOT_RUN",
       "raw_root":str(a.raw.resolve()),"files":{},"build_verification":{}}
for name,rel in inputs.items():
    path=a.raw/rel;data=json.loads(path.read_text());target=a.output/(name+".json")
    target.write_text(json.dumps(data,indent=2)+"\n")
    index["files"][name]={"source":rel,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
for name in ("closure-build","final-build","registered-build","coupled-final-build","zero-build"):
    manifest=json.loads((a.raw/name/"manifest.json").read_text())
    verified={path:hashlib.sha256((root/path).read_bytes()).hexdigest()==sha for path,sha in manifest["headers"].items()}
    # Earlier builds were deliberately made before commits; source/header hashes,
    # not the then-HEAD alone, identify their tested implementation.
    index["build_verification"][name]={"all_headers_match":all(verified.values()),"headers":verified,
        "source_sha256":manifest["source_sha256"],"final_probe_source_matches":hashlib.sha256((root/"benchmarks/v2"/Path(manifest["source"]).name).read_bytes()).hexdigest()==manifest["source_sha256"]}
    (a.output/(name+".json")).write_text(json.dumps(manifest,indent=2)+"\n")
index["final_auxiliary_source_sha256"]=hashlib.sha256((root/"benchmarks/v2/feature_oracle.h").read_bytes()).hexdigest()
toolchain=a.raw/"toolchain/tdem/CMakeFiles/test_cu_04.dir"
index["toolchain_response_files"]={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in toolchain.iterdir() if f.is_file()}
restart=[];cross=[]
for name in ("standalone","polyhedra","rebuild_before","rebuild_after","separated_restart"):
    data=json.loads((a.output/(name+".json")).read_text())
    if not data["pass"]:raise SystemExit("Required bounded matrix did not pass: "+name)
    restart.extend(v for k,v in data["comparisons"].items() if k.endswith("_restart"))
    cross.extend(v for k,v in data["comparisons"].items() if k.endswith("_cpu_vs_cuda"))
index["aggregate"]={"restart_comparisons":len(restart),"restart_bitwise_pass":sum(v["pass"] and v["bitwise_numeric"] for v in restart),
                    "cpu_gpu_comparisons":len(cross),"cpu_gpu_pass":sum(v["pass"] for v in cross),"max_cpu_gpu_absolute_error":max(v["max_absolute_error"] for v in cross)}
independent=json.loads((a.output/"independent_spheres.json").read_text())
index["independent_spheres"]={"pass":independent["pass"],"runs":len(independent["cases"]),
    "scalar_checks":sum(v["scalar_checks"] for v in independent["cases"].values()),"max_absolute_error":max(v["max_absolute_error"] for v in independent["cases"].values())}
original=Path("/home/msys/mechsys")
index["original_read_only_verification"]={
    "head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=original,text=True).strip(),
    "status":subprocess.check_output(["git","status","--porcelain=v1","-uall"],cwd=original,text=True),
    "tracked_diff_sha256":hashlib.sha256(subprocess.check_output(["git","diff","HEAD","--binary"],cwd=original)).hexdigest()}
if index["original_read_only_verification"]["tracked_diff_sha256"]!="e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9":
    raise SystemExit("Original checkout tracked changes differ from initial read-only snapshot")
for r in index["build_verification"].values():
    if not r["all_headers_match"]:raise SystemExit("Build header provenance mismatch")
(a.output/"index.json").write_text(json.dumps(index,indent=2)+"\n")
print(json.dumps(index["aggregate"]))
