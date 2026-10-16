#!/usr/bin/env python3
"""Independent bounded feature evidence, analytical normals and real negative control."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--matrix",type=Path,required=True)
p.add_argument("--binary",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
result={"pass":True,"geometry":{},"analytical_normals":{},"transitions":{}}
pattern=re.compile(r"V2_FEATURE_SUMMARY checks=(\d+) EE=(\d+) VF=(\d+) FV=(\d+) missing=(\d+) duplicates=(\d+)")
for case in (11,12,13,14,15,16):
    for backend in ("cpu","cuda"):
        name=f"case{case}_law0_damp0_{backend}_reference"
        log=a.matrix/name/"run.log";raw=log.read_text();m=pattern.search(raw)
        values=dict(zip(("checks","EE","VF","FV","missing","duplicates"),map(int,m.groups()))) if m else {}
        ok=bool(values) and values["checks"]==(600 if case==15 else 300) and values["missing"]==values["duplicates"]==0
        result["geometry"][name]={"pass":ok,**values,"log_sha256":hashlib.sha256(log.read_bytes()).hexdigest()};result["pass"] &= ok
        rows=[json.loads(l[9:]) for l in raw.splitlines() if l.startswith("V2_STATE ")]
        # Finite face: x=.05, sphere center=.074, Rsum=.025 => .001 overlap.
        # Orthogonal thin rods have FOUR crossing edge pairs with .001 overlap.
        # Existing generic law uses reduced Kn=1000*1000/(1000+1000)=500 N/m.
        if case in (11,12,13,16):
            expected={11:[-.5,0,0],12:[.5,0,0],13:[0,0,2],16:[-.5,0,0]}[case]
            actual=rows[1]["contacts"][0]["normal"]
            error=max(abs(x-y) for x,y in zip(expected,actual));ok=error<=1e-10
            result["analytical_normals"][name]={"pass":ok,"expected":expected,"actual":actual,"max_absolute_error":error};result["pass"] &= ok
        if case==15:
            # Verify physical absent -> present -> absent -> present, not labels.
            active=[]
            for row in rows:
                force=sum(sum(x*x for x in c["normal"]) for c in row["contacts"])
                now=force>1e-20
                if not active or active[-1]["contact"]!=now:active.append({"step":row["step"],"contact":now})
            ok=[r["contact"] for r in active]==[False,True,False,True]
            result["transitions"][name]={"pass":ok,"transitions":active};result["pass"] &= ok
env={k:v for k,v in os.environ.items() if not k.startswith("MECHSYS_")};env["MECHSYS_V2_FEATURE_ORACLE"]="1"
command=[str(a.binary.resolve()),"negative","11","0","0","2",str((a.output/"unused.vv.json").resolve())]
log=a.output/"dropped_uploaded_feature.log"
with log.open("w") as output:
    r=subprocess.run(command,cwd=a.output,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=30)
raw=log.read_text();ok=r.returncode==1 and "reference=1 missing=1 duplicates=0" in raw and "completeness oracle FAIL" in raw
result["negative_control"]={"pass":ok,"exit_code":r.returncode,"command":command,"binary_sha256":hashlib.sha256(a.binary.read_bytes()).hexdigest(),"log_sha256":hashlib.sha256(log.read_bytes()).hexdigest()};result["pass"] &= ok
(a.output/"results.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"pass":result["pass"],"geometry_runs":len(result["geometry"]),"analytical_checks":len(result["analytical_normals"]),"transitions":result["transitions"]}));raise SystemExit(0 if result["pass"] else 1)
