#!/usr/bin/env python3
"""Run copied P1 oracle fixtures sequentially, preserving inputs, logs and failures."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--names", nargs="*", default=["A_dense", "B_lowdens", "C_highacc", "D_shear", "E_squeeze"])
    parser.add_argument("--persistent", action="store_true")
    parser.add_argument("--vv", action="store_true", help="Select VV explicitly in the test_cu_04 harness")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    binary=args.binary.resolve()
    results={"binary": str(binary), "binary_sha256": digest(binary),
             "persistent_reduction": args.persistent, "velocity_verlet": args.vv, "cases": {}}
    env = {k: v for k, v in os.environ.items() if not k.startswith("MECHSYS_")}
    env.update(MECHSYS_CANDIDATE_ORACLE="1", MECHSYS_PERSISTENT_REDUCTION=str(int(args.persistent)))
    pattern=re.compile(r"DEM_ORACLE_STEP iter=\d+ ref=(\d+) matched=(\d+) missing=(\d+) dup=(\d+).*?bad_periodicity=(\d+)")
    for name in args.names:
        directory = args.output / name
        directory.mkdir()
        source = args.inputs/f"oracle_{name}.inp"
        copied = directory/source.name
        shutil.copyfile(source, copied)
        log=directory/"run.log"
        command=[str(binary),copied.stem,"2"]
        if args.vv:
            command.extend(["4.0","0.0","1"])
        with log.open("w") as stream:
            run=subprocess.run(command,cwd=directory,env=env,
                               stdout=stream,stderr=subprocess.STDOUT,timeout=240)
        rows=[[int(x) for x in row] for row in pattern.findall(log.read_text())]
        case={"input_sha256":digest(copied),"log":str(log),"log_sha256":digest(log),
              "returncode":run.returncode,"checks":len(rows),"command":command}
        for i, key in enumerate(["reference","matched","missing","duplicates","bad_periodicity"]):
            case[key]=sum(row[i] for row in rows)
        selected=not args.vv or "DEM_BENCHMARK_INTEGRATOR velocity_verlet=1" in log.read_text()
        case["integrator_selection_verified"]=selected
        case["verdict"]="PASS" if run.returncode==0 and rows and selected and not any(case[k] for k in ["missing","duplicates","bad_periodicity"]) else "FAIL"
        results["cases"][name]=case
        (args.output/"results.json").write_text(json.dumps(results,indent=2)+"\n")
        print(json.dumps({"case":name,**case}),flush=True)
    if any(case["verdict"]!="PASS" for case in results["cases"].values()):
        raise SystemExit(1)


if __name__=="__main__":
    main()
