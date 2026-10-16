#!/usr/bin/env python3
"""Archive compact history evidence; retain full raw trajectories outside Git."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    e=args.evidence.resolve()
    fixed=json.loads((e/"final-device/history_validation.json").read_text())
    negative=json.loads((e/"negative-control/history_validation.json").read_text())
    registered=json.loads((e/"registered-vv/results.json").read_text())
    assert fixed["pass"] is True and negative["pass"] is False
    assert len(fixed["runs"])==12 and len(registered["cases"])==5
    assert registered["velocity_verlet"] and all(c["verdict"]=="PASS" for c in registered["cases"].values())
    assert all(c["first_failure"][0]["field"]=="fr" for k,c in negative["comparisons"].items() if "cpu_vs_cuda" in k)
    for backend in ["cpu","cuda"]:
        assert fixed["runs"][f"case0_0.001_{backend}"]["rebuild_reference_changes"]==200
        assert fixed["runs"][f"case0_1.0_{backend}"]["rebuild_reference_changes"]==0
        assert fixed["runs"][f"case2_0.001_{backend}"]["transitions"]==[
            {"step":0,"contact":1},{"step":67,"contact":0},{"step":911,"contact":1}]
    for name in ["final-build","after-build"]:
        build=json.loads((e/name/"build_manifest.json").read_text())
        assert build["headers"]["lib/dem/domain.h"]==sha(root/"lib/dem/domain.h")
    files={"history_validation.json":"final-device/history_validation.json",
           "negative_control.json":"negative-control/history_validation.json",
           "registered_vv.json":"registered-vv/results.json",
           "final_build.json":"final-build/build_manifest.json",
           "reference_coupled_build.json":"after-build/build_manifest.json",
           "negative_build.json":"unpatched-build/build_manifest.json",
           **{f"reference_{k}.log":f"reference_{k}.log" for k in ["cpu","gpu","persistent"]}}
    args.output.mkdir(parents=True,exist_ok=False)
    for destination,source in files.items():
        shutil.copyfile(e/source,args.output/destination)
    sources=["AGENTS.md","lib/dem/domain.h","lib/dem/dem.cuh","lib/dem/interacton.h","lib/dem/particle.h",
             "benchmarks/v1_reference/history_probe.cu","benchmarks/v1_reference/check_history.py",
             "benchmarks/v1_reference/reference_probe.cu","tdem/test_cu_04.cu"]
    metadata={"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),
              "source_sha256":{p:sha(root/p) for p in sources},"raw_evidence":str(e),
              "archive_sha256":{p:sha(args.output/p) for p in files},
              "registered_totals":{k:sum(c[k] for c in registered["cases"].values()) for k in ["checks","reference","missing","duplicates","bad_periodicity"]},
              "history_runs":len(fixed["runs"]),"history_candidate_checks":sum(c["candidate_oracle_checks"] for c in fixed["runs"].values()),
              "history_reference_contacts":sum(c["reference_contacts"] for c in fixed["runs"].values()),
              "negative_control_exit_code":1,"coupled_gate":"compile/link only, no runtime",
              "performance":"not measured; diagnostic readbacks/output enabled"}
    (args.output/"evidence_manifest.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print(json.dumps({k:metadata[k] for k in ["source_commit","registered_totals","history_candidate_checks","history_reference_contacts"]},indent=2))


if __name__=="__main__":
    main()
