#!/usr/bin/env python3
"""Run bounded actual VV restart and CPU/GPU comparisons, preserving every attempt."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import subprocess

ABS=1e-10
REL=1e-9


def close(x,y):
    return math.isfinite(x) and math.isfinite(y) and abs(x-y)<=ABS+REL*max(abs(x),abs(y))


def compare(x,y,path="",errors=None,stats=None):
    errors=[] if errors is None else errors
    stats={"max_absolute_error":0,"bitwise_numeric":True,"numbers":0} if stats is None else stats
    if isinstance(x,dict) and isinstance(y,dict):
        if set(x)!=set(y):errors.append({"path":path,"keys_differ":True})
        for key in sorted(set(x)&set(y)):compare(x[key],y[key],path+"/"+key,errors,stats)
    elif isinstance(x,list) and isinstance(y,list):
        if len(x)!=len(y):errors.append({"path":path,"lengths":[len(x),len(y)]})
        for i,(u,v) in enumerate(zip(x,y)):compare(u,v,path+f"/{i}",errors,stats)
    elif isinstance(x,(int,float)) and isinstance(y,(int,float)):
        stats["numbers"]+=1
        stats["max_absolute_error"]=max(stats["max_absolute_error"],abs(x-y))
        stats["bitwise_numeric"] &= struct.pack("d",x)==struct.pack("d",y)
        if not close(x,y):errors.append({"path":path,"left":x,"right":y})
    elif x!=y:errors.append({"path":path,"left":x,"right":y})
    return errors,stats


def normalized(row):
    row=json.loads(json.dumps(row))
    row["contacts"].sort(key=lambda c:(min(c["a"],c["b"]),max(c["a"],c["b"])))
    return row


def physical_feature_history(row):
    """Absent CPU map entries and EXACT zero GPU slots have the same state.

    This is not a tolerance: retain every nonzero component, however small.
    Strict storage comparisons are also recorded separately, and restart
    comparisons never apply this representation normalization.
    """
    row=json.loads(json.dumps(row))
    for contact in row["contacts"]:
        if "features" in contact:
            contact["features"]=[f for f in contact["features"] if any(x!=0 for x in f["displacement"])]
    return row


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--build",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--cases",nargs="+",type=int,default=[0,1,2,3,4,5,6,7,9,10])
    p.add_argument("--laws",nargs="+",type=int,default=[0,1])
    p.add_argument("--damping",nargs="+",type=int,default=[0,1])
    p.add_argument("--backends",nargs="+",default=["cpu","cuda"])
    p.add_argument("--restart-step",type=int)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    result={"absolute_tolerance":ABS,"relative_tolerance":REL,"pass":True,"runs":{},"comparisons":{},"analytical":{}}
    snapshots={}
    env={k:v for k,v in os.environ.items() if not k.startswith("MECHSYS_")}
    env["MECHSYS_PERSISTENT_REDUCTION"]="0"
    env["MECHSYS_V2_FEATURE_ORACLE"]="1"

    def run(name,command):
        directory=a.output/name;directory.mkdir()
        log=directory/"run.log"
        with log.open("w") as output:
            r=subprocess.run(command,cwd=directory,env=env,stdout=output,stderr=subprocess.STDOUT,timeout=120)
        raw=log.read_text();rows=[normalized(json.loads(line[9:])) for line in raw.splitlines() if line.startswith("V2_STATE ")]
        result["runs"][name]={"command":command,"exit_code":r.returncode,"snapshots":len(rows),"log_sha256":hashlib.sha256(log.read_bytes()).hexdigest(),
                               "binary_sha256":hashlib.sha256(Path(command[0]).read_bytes()).hexdigest()}
        if r.returncode or not rows:result["pass"]=False
        (a.output/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
        return r,rows

    for case in a.cases:
        for law in a.laws:
            if case==6 and law==1:continue # Generic wall laws have a separate constitutive audit.
            for damping in a.damping:
                steps=1000 if case==4 else (600 if case==15 else 300)
                restart=500 if case==4 else (200 if case>=9 else 50)
                if case>=11:restart=350 if case==15 else 50
                if a.restart_step is not None:restart=a.restart_step
                for backend in a.backends:
                    name=f"case{case}_law{law}_damp{damping}_{backend}"
                    binary=str((a.build/backend).resolve());checkpoint=(a.output/(name+".vv.json")).resolve()
                    def command(mode,n):return [binary,mode,str(case),str(law),str(damping),str(n),str(checkpoint)]
                    proc,reference=run(name+"_reference",command("reference",steps))
                    if proc.returncode:continue
                    snapshots[(case,law,damping,backend)]={r["step"]:r for r in reference}
                    if len(reference)!=steps+1:result["pass"]=False
                    proc,prefix=run(name+"_prefix",command("split",restart))
                    if proc.returncode:continue
                    proc,resumed=run(name+"_resumed",command("continue",steps))
                    if proc.returncode:continue
                    errors=[];stats={"max_absolute_error":0,"bitwise_numeric":True,"numbers":0}
                    if len(prefix)!=restart+1 or prefix[-1]["step"]!=restart:
                        errors.append({"error":"prefix coverage incomplete"})
                    if len(resumed)!=steps-restart+2 or resumed[-1]["step"]!=steps or any(r["step"]!=restart for r in resumed[:2]):
                        errors.append({"error":"resumed coverage incomplete"})
                    for row in prefix+resumed:
                        if row["step"] not in snapshots[(case,law,damping,backend)]:
                            errors.append({"step":row["step"],"unknown_step":True});continue
                        compare(snapshots[(case,law,damping,backend)][row["step"]],row,f"step{row['step']}",errors,stats)
                    for row in reference[1:]:
                        if any(not close(x,0) for x in row["force_balance"]):errors.append({"step":row["step"],"force_balance":row["force_balance"]})
                    result["comparisons"][name+"_restart"]={"pass":not errors,"failures":len(errors),"first_failure":errors[:1],**stats,"restart_step":restart}
                    result["pass"] &= not errors
                    print(name+f": restart {'PASS' if not errors else 'FAIL'} max={stats['max_absolute_error']:.3g} bitwise={stats['bitwise_numeric']} first={errors[:1]}",flush=True)
                    if case==0 and backend=="cpu":
                        # Independent elastic/dashpot/rolling first-force reference.
                        row=reference[0];c=row["contacts"][0];r=0.1;delta=0.001;dt=2e-5;vt=0.2
                        if law:
                            young=1000;nu=0.25;re=r/2
                            ye=young/(2*(1-nu*nu));ge=young/(4*(2-nu)*(1+nu))
                            kn=4/3*math.sqrt(re)*ye;kt=8*math.sqrt(re)*ge
                            ts=kt*math.sqrt(delta);gt=(2 if damping else 0)*delta**0.25
                        else:
                            kn=1000;kt=20;ts=kt;mass=4/3*math.pi*r**3
                            gt=(2 if damping else 0)*mass/2
                        expected={"normal":kn*(delta**1.5 if law else delta),"tangent":ts*vt*dt,
                                  "tangent_damping":gt*vt,"rolling":0.3*ts*0.1*dt}
                        checks={key:close(c[key][0 if key=="normal" else 1],value) for key,value in expected.items()}
                        result["analytical"][name]={"expected":expected,"pass":all(checks.values()),"checks":checks}
                        result["pass"] &= all(checks.values())
                if {"cpu","cuda"}<=set(a.backends) and all((case,law,damping,b) in snapshots for b in ["cpu","cuda"]):
                    cpu=snapshots[(case,law,damping,"cpu")];gpu=snapshots[(case,law,damping,"cuda")]
                    errors=[];stats={"max_absolute_error":0,"bitwise_numeric":True,"numbers":0}
                    storage_errors=[];storage_stats={"max_absolute_error":0,"bitwise_numeric":True,"numbers":0}
                    for step in sorted(set(cpu)&set(gpu)):
                        # Historical GPU frame-zero accumulators are zero until its first force kernel.
                        if step==0:continue
                        compare(cpu[step],gpu[step],f"step{step}",storage_errors,storage_stats)
                        compare(physical_feature_history(cpu[step]),physical_feature_history(gpu[step]),f"step{step}",errors,stats)
                    name=f"case{case}_law{law}_damp{damping}_cpu_vs_cuda"
                    result["comparisons"][name]={"pass":not errors,"failures":len(errors),"first_failure":errors[:1],**stats,
                        "exact_zero_feature_slots_equivalent_to_absent":True,
                        "strict_storage_comparison":{"pass":not storage_errors,"failures":len(storage_errors),"first_failure":storage_errors[:1],**storage_stats}}
                    result["pass"] &= not errors
                    print(name+f": {'PASS' if not errors else 'FAIL'} max={stats['max_absolute_error']:.3g} first={errors[:1]}",flush=True)
                (a.output/"validation.json").write_text(json.dumps(result,indent=2)+"\n")
    raise SystemExit(0 if result["pass"] else 1)


if __name__=="__main__":main()
