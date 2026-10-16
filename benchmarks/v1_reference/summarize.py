#!/usr/bin/env python3
"""Summarize preserved VV regressions; keep raw logs and timing evidence separate."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def parse(path):
    text=path.read_text()
    steps=[(int(a),int(b)) for a,b in re.findall(r"DEM_ORACLE_STEP iter=(\d+).*?steps_since_rebuild=(\d+)",text)]
    repeat=re.search(r"V1_REFERENCE_REPEAT steps=(\d+) position=(\S+) reference=(\S+) residual=(\S+)",text)
    result={"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "steps":int(repeat[1]),"position":float(repeat[2]),"reference":float(repeat[3]),
            "residual":float(repeat[4])}
    if steps:
        result["repeat_rebuild_steps"]=[i for i,since in steps if i>0 and since==0]
        result["repeat_rebuild_count"]=len(result["repeat_rebuild_steps"])
    for prefix,key in [("V1_REFERENCE_DIRECT","direct"),("V1_FAST_CONTACT","contact"),("V1_COMMON_FORCE","common_force"),
                       ("V1_VERTEX_ROTATION","rotation"),("V1_NEW_CONTACT_ACCUMULATORS","accumulators")]:
        line=next((x for x in text.splitlines() if x.startswith(prefix)),None)
        if line:
            result[key]=dict((k,float(v)) for k,v in re.findall(r"([A-Za-z_][A-Za-z_0-9]*)=([\deE.+-]+)",line))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=args.artifacts
    data={"date":"2026-10-16","baseline_commit":"7f99c4cef62686110b4bd7f85926e07228c8e86c",
          "baseline":parse(root/"v1_baseline_rebuilt.log"),"fixed_gpu":parse(root/"final_gpu.log"),
          "fixed_persistent":parse(root/"final_persistent.log"),"fixed_cpu":parse(root/"final_cpu.log"),
          "actual_vv":json.loads((root/"final_actual_vv/results.json").read_text()),
          "performance":"NO complete-simulation speedup measured; rebuild counts are diagnostic",
          "accumulator_hazard":"Unassigned automatic fields found by source audit; no failure observed in this probe's baseline build"}
    assert data["baseline"]["repeat_rebuild_count"]==8
    for key in ["fixed_gpu","fixed_persistent"]:
        item=data[key]
        assert item["repeat_rebuild_count"]==3 and item["direct"]["residual"]==0
        assert all(item["direct"][k]==1 for k in ["state_unchanged","acceleration_unchanged","history_unchanged"])
        assert item["accumulators"]["zero_initialized"]==1
        assert abs(item["common_force"]["normal_x"]-20)<1e-10
    for key in ["fixed_gpu","fixed_persistent","fixed_cpu"]:
        assert abs(data[key]["reference"]-0.09)<1e-13 and abs(data[key]["residual"]-0.01)<1e-13
        assert abs(data[key]["contact"]["F1"]+20)<1e-10 and abs(data[key]["contact"]["F2"]-20)<1e-10
        assert data[key]["contact"]["action_reaction"]==0
    cases=data["actual_vv"]["cases"]
    assert len(cases)==5 and all(x["verdict"]=="PASS" and x["integrator_selection_verified"] for x in cases.values())
    data["actual_vv_totals"]={key:sum(c[key] for c in cases.values()) for key in ["checks","reference","missing","duplicates","bad_periodicity"]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+"\n")
    print(json.dumps({"rebuilds_before":8,"rebuilds_after":3,"actual_vv":data["actual_vv_totals"]},indent=2))


if __name__=="__main__":
    main()
