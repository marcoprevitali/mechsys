#!/usr/bin/env python3
"""Bounded FP64 CPU/GPU VV history oracle, with preserved raw failures."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ATOL=1e-10
RTOL=1e-9


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a,b):
    return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=ATOL+RTOL*max(abs(a),abs(b))


def compare(a,b,fields):
    worst={}
    failures=[]
    if len(a)!=len(b):
        return [{"error":"snapshot count differs","left":len(a),"right":len(b)}],{}
    for left,right in zip(a,b):
        step=left["step"]
        if step!=right["step"]:
            failures.append({"step":step,"error":"snapshot steps differ"})
        for field in fields:
            # Absent inactive candidates are permitted, absent physical contacts not.
            if field not in left or field not in right:
                if left.get("contact",False) or right.get("contact",False):
                    failures.append({"step":step,"field":field,"error":"missing active contact"})
                continue
            x,y=left[field],right[field]
            if not isinstance(x,list):
                x,y=[x],[y]
            for i,(u,v) in enumerate(zip(x,y)):
                delta=abs(u-v)
                worst[field]=max(worst.get(field,0.0),delta)
                if not close(u,v):
                    failures.append({"step":step,"field":field,"component":i,"left":u,"right":v,"error":delta})
    return failures,worst


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--scenarios",nargs="+",type=int,default=[0,1,2])
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    result={"absolute_tolerance":ATOL,"relative_tolerance":RTOL,"runs":{},"comparisons":{},"pass":True}
    rows={}
    for scenario in args.scenarios:
        for alpha in [0.001,1.0]:
            for backend in ["cpu","cuda"]:
                name=f"case{scenario}_{alpha}_{backend}"
                binary=args.build/("history_"+backend)
                command=[str(binary),str(scenario),str(alpha)]
                log=args.output/(name+".log")
                with log.open("w") as stream:
                    proc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
                raw=log.read_text()
                data=[json.loads(line.removeprefix("VV_HISTORY ")) for line in raw.splitlines() if line.startswith("VV_HISTORY {")]
                rows[name]=data
                contacts=[r.get("contact",False) for r in data]
                transitions=[{"step":r["step"],"contact":c} for i,(r,c) in enumerate(zip(data,contacts)) if i==0 or c!=contacts[i-1]]
                # Raw pre-force reference changes count reconstruction, not output events.
                rebuilds=sum(data[i].get("reference0")!=data[i-1].get("reference0") for i in range(1,len(data)))
                checks=[dict(re.findall(r"(\w+)=(\d+)",line)) for line in raw.splitlines() if line.startswith("DEM_ORACLE_STEP ")]
                errors=[]
                if proc.returncode or len(data)!=1001 or "VV_HISTORY_MODE velocity_verlet=1" not in raw:
                    errors.append("run/coverage/mode check failed")
                if backend=="cuda" and (len(checks)!=1000 or any(int(c[k]) for c in checks for k in ["missing","dup","bad_periodicity"])):
                    errors.append("candidate oracle coverage/completeness failed")
                if scenario==0 and alpha==0.001 and "reference0" in (data[0] if data else {}) and rebuilds<10:
                    errors.append("insufficient repeated rebuild coverage")
                if data and not close(data[0]["fr"][1],1.2e-5):
                    errors.append("analytic initial rolling force failed (Kr=6, Vr=0.1, dt=2e-5)")
                host_errors=[]
                for r in data:
                    if r.get("pair") not in [None,[-1,-2]] or r["records"]>1:
                        errors.append("physical pair identity/uniqueness failed")
                    if "fr" in r:
                        for j,(f,h) in enumerate(zip(r["fr"],r["host_fr"])):
                            if not close(f,h):
                                host_errors.append({"step":r["step"],"component":j,"device":f,"host":h})
                    if r["step"]>0:
                        for j in range(3):
                            # Applied forces are equal and opposite in every fixture.
                            if not close(r["F0"][j]+r["F1"][j],0):
                                errors.append("action-reaction failed")
                stats={"command":command,"binary_sha256":sha(binary),"log_sha256":sha(log),"exit_code":proc.returncode,
                       "snapshots":len(data),"transitions":transitions,"rebuild_reference_changes":rebuilds,
                       "candidate_oracle_checks":len(checks),"reference_contacts":sum(int(c["ref"]) for c in checks),
                       "host_rolling_mismatch_count":len(host_errors),"first_host_mismatch":host_errors[:1],"errors":errors}
                result["runs"][name]=stats
                result["pass"] &= not errors and not host_errors
                print(f"{name}: snapshots={len(data)} transitions={transitions} host_mismatches={len(host_errors)}",flush=True)
            left=rows[f"case{scenario}_{alpha}_cpu"]
            right=rows[f"case{scenario}_{alpha}_cuda"]
            state=[f"{f}{p}" for p in range(2) for f in ["x","v","w","F","T","Q"]]
            errors,worst=compare(left,right,state+["ft","fr","host_fr","contact","overlap"])
            # GPU frame-zero common accumulators are historically unset until the first device force.
            energy_errors,energy_worst=compare(left[1:],right[1:],["Epot","dEvis","dEfric"])
            errors+=energy_errors
            worst.update(energy_worst)
            key=f"case{scenario}_{alpha}_cpu_vs_cuda"
            result["comparisons"][key]={"failures":len(errors),"first_failure":errors[:1],"max_absolute_errors":worst}
            result["pass"] &= not errors
            print(f"{key}: failures={len(errors)} first={errors[:1]}",flush=True)
        if scenario==0:
            for backend in ["cpu","cuda"]:
                errors,worst=compare(rows[f"case0_0.001_{backend}"],rows[f"case0_1.0_{backend}"],
                                     state+["ft","fr","contact","overlap"])
                key=f"persistent_skin_control_{backend}"
                result["comparisons"][key]={"failures":len(errors),"first_failure":errors[:1],"max_absolute_errors":worst}
                result["pass"] &= not errors
    (args.output/"history_validation.json").write_text(json.dumps(result,indent=2)+"\n")
    raise SystemExit(0 if result["pass"] else 1)


if __name__=="__main__":
    main()
