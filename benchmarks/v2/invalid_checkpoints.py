#!/usr/bin/env python3
"""Negative full-state checkpoint format/identity/count tests; no input overwrite."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--build",type=Path,required=True);p.add_argument("--valid",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
p.add_argument("--legacy",type=Path,help="Existing R1 legacy HDF5 Save file, never overwritten")
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
result={"pass":True,"tests":{}}
for backend in ["cpu","cuda"]:
    source=a.valid/f"case0_law0_damp0_{backend}.vv.json";original=json.loads(source.read_text())
    mutations={
        "version":lambda d:d.update(version="999"),
        "precision":lambda d:d.update(precision="binary32"),
        "phase":lambda d:d.update(phase="half-step"),
        "backend":lambda d:d.update(backend="cuda" if backend=="cpu" else "cpu"),
        "particle_count":lambda d:d.update(particle_count="99"),
        "duplicate_id":lambda d:d["particles"][1].update(id=d["particles"][0]["id"]),
        "unknown_endpoint":lambda d:d["contacts"][0].update(particle_a="999999"),
        "duplicate_contact":lambda d:(d["contacts"].append(copy.deepcopy(d["contacts"][0])),d.update(contact_count="2")),
        "missing_history":lambda d:d["contacts"][0].pop("Fdvv"),
        "nonfinite":lambda d:d["particles"][0]["props"].update(Kn="nan"),
        "bad_fixity":lambda d:d["contacts"][0].update(BothFree="0"),
        "invalid_mass":lambda d:d["particles"][0]["props"].update(m="0"),
    }
    if backend=="cuda":
        mutations["gpu_count"]=lambda d:d.update(gpu_vv=[])
        mutations["gpu_identity"]=lambda d:d["gpu_vv"][0].update(contact="99")
    for name,mutate in mutations.items():
        d=copy.deepcopy(original);mutate(d);path=(a.output/f"{backend}_{name}.vv.json").resolve();path.write_text(json.dumps(d))
        command=[str((a.build/backend).resolve()),"validate","0","0","0","300",str(path)]
        log=a.output/f"{backend}_{name}.log"
        with log.open("w") as out:r=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=30)
        ok=r.returncode==1;result["tests"][f"{backend}_{name}"]={"pass":ok,"exit_code":r.returncode,"log_sha256":hashlib.sha256(log.read_bytes()).hexdigest()};result["pass"] &= ok
    # Writer must refuse existing evidence without replacing its bytes.
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    command=[str((a.build/backend).resolve()),"split","0","0","0","50",str(source.resolve())]
    log=a.output/f"{backend}_overwrite.log"
    with log.open("w") as out:r=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=30)
    after=hashlib.sha256(source.read_bytes()).hexdigest();ok=r.returncode==1 and before==after
    result["tests"][f"{backend}_no_overwrite"]={"pass":ok,"exit_code":r.returncode,"sha256_before":before,"sha256_after":after};result["pass"] &= ok
    if a.legacy:
        command=[str((a.build/backend).resolve()),"validate","0","0","0","300",str(a.legacy.resolve())]
        log=a.output/f"{backend}_legacy_not_checkpoint.log"
        before=hashlib.sha256(a.legacy.read_bytes()).hexdigest()
        with log.open("w") as out:r=subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,timeout=30)
        after=hashlib.sha256(a.legacy.read_bytes()).hexdigest()
        ok=r.returncode==1 and "legacy HDF5 Save/Load is not a checkpoint" in log.read_text() and before==after
        result["tests"][f"{backend}_legacy_rejection"]={"pass":ok,"exit_code":r.returncode,"sha256_before":before,"sha256_after":after};result["pass"] &= ok
(a.output/"results.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({"pass":result["pass"],"checks":len(result["tests"])}));raise SystemExit(0 if result["pass"] else 1)
