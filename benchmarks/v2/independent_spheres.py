#!/usr/bin/env python3
"""Independent FP64 sphere force/history recurrence from observed phase-space data.

Does not import solver code or use its effective-contact coefficients. Reconstructs
force-time half velocities from full-step velocity and Newton/Euler acceleration
for the declared equal-radius, isotropic, zero-global-drag fixtures.
"""
import argparse
import json
import math
from pathlib import Path
import re


def add(a,b):return [x+y for x,y in zip(a,b)]
def mul(s,a):return [s*x for x in a]
def sub(a,b):return add(a,mul(-1,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def norm(a):return math.sqrt(dot(a,a))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def rotate(q,v):return add(v,add(mul(2*q[0],cross(q[1:],v)),mul(2,cross(q[1:],cross(q[1:],v)))))


def audit(rows,case,law,damping):
    errors=[];checks=0;max_error=0;previous={}
    r=0.1;dt=2e-5;mass=4/3*math.pi*r**3;inertia=0.4*mass*r*r
    if law:
        young=1000;nu=0.25;ye=young/(2*(1-nu*nu));ge=young/(4*(2-nu)*(1+nu))
        kn=4/3*math.sqrt(r/2)*ye;kt=8*math.sqrt(r/2)*ge
        gn=3 if damping else 0;gt=2 if damping else 0
    else:kn=1000;kt=20;gn=(3 if damping else 0)*mass/2;gt=(2 if damping else 0)*mass/2

    def check(step,key,got,expected):
        nonlocal checks,max_error
        if not isinstance(got,list):got,expected=[got],[expected]
        for x,y in zip(got,expected):
            checks+=1;error=abs(x-y);max_error=max(max_error,error)
            if not math.isfinite(x) or error>1e-10+1e-9*max(abs(x),abs(y)):
                errors.append({"step":step,"field":key,"actual":x,"expected":y})

    for row in rows:
        parts={p["id"]:p for p in row["particles"]};current={}
        for c in row["contacts"]:
            pair=(c["a"],c["b"]);current[pair]=c
            if row["step"]==0 or (case==1 and row["step"]==75):continue
            if not c["contact"]:
                check(row["step"],"separated displacement",c["displacement"],[0,0,0]);continue
            p,q=parts[pair[0]],parts[pair[1]];branch=sub(q["x"],p["x"])
            if case==5:branch[0]-=round(branch[0])
            distance=norm(branch);n=mul(1/distance,branch);delta=2*r-distance
            check(row["step"],"signed overlap",c["overlap"],delta)
            def half(p):
                velocity=sub(p["v"],mul(0.5*dt/mass,p["F"]))
                omega=sub(p["w"],mul(0.5*dt/inertia,p["T"]))
                return velocity,rotate(p["Q"],omega)
            vp,wp=half(p);vq,wq=half(q)
            relative=sub(add(vp,cross(wp,mul(distance/2,n))),add(vq,cross(wq,mul(-distance/2,n))))
            vn=dot(relative,n);vt=sub(relative,mul(vn,n))
            ts=kt*(math.sqrt(delta) if law else 1);ds=delta**0.25 if law else 1
            normal=mul(kn*(delta**1.5 if law else delta),n);normal_damping=mul(gn*ds*vn,n)
            old=previous.get(pair,{"displacement":[0,0,0],"rolling":[0,0,0]})
            trial=add(old["displacement"],mul(dt,vt));trial=sub(trial,mul(dot(trial,n),n))
            elastic=mul(ts,trial);limit=0.4*norm(normal)
            if norm(elastic)>limit:elastic=mul(limit/norm(elastic),elastic)
            displacement=mul(1/ts,elastic);tangent_damping=mul(gt*ds,vt)
            rolling=add(old["rolling"],mul(0.3*ts*dt,cross(mul(r/2,sub(wp,wq)),n)))
            rolling=sub(rolling,mul(dot(rolling,n),n));rolling_limit=0.2*limit
            if norm(rolling)>rolling_limit:rolling=mul(rolling_limit/norm(rolling),rolling)
            force=add(add(normal,normal_damping),add(elastic,tangent_damping))
            world_t0=mul(-1,add(cross(mul(distance/2,n),force),mul(r,cross(n,rolling))))
            world_t1=add(cross(mul(-distance/2,n),force),mul(r,cross(n,rolling)))
            check(row["step"],"normal",c["normal"],normal);check(row["step"],"normal damping",c["normal_damping"],normal_damping)
            check(row["step"],"tangent",c["tangent"],elastic);check(row["step"],"tangent damping",c["tangent_damping"],tangent_damping)
            check(row["step"],"displacement recurrence",c["displacement"],displacement);check(row["step"],"rolling recurrence",c["rolling"],rolling)
            if len(row["contacts"])==1:
                check(row["step"],"particle force a",sub(p["F"],p["Ff"]),mul(-1,force));check(row["step"],"particle force b",sub(q["F"],q["Ff"]),force)
                inverse=lambda q:[q[0],-q[1],-q[2],-q[3]]
                check(row["step"],"body torque a",p["T"],rotate(inverse(p["Q"]),world_t0));check(row["step"],"body torque b",q["T"],rotate(inverse(q["Q"]),world_t1))
            epot=(0.4*kn*delta**2.5 if law else 0.5*kn*delta**2)+0.5*ts*dot(displacement,displacement)
            evis=(gn*ds*vn*vn+gt*ds*dot(vt,vt))*dt;efric=limit*norm(sub(trial,displacement))
            check(row["step"],"elastic energy",c["Epot"],epot);check(row["step"],"viscous work",c["dEvis"],evis);check(row["step"],"frictional work",c["dEfric"],efric)
        previous=current
    return {"pass":not errors,"scalar_checks":checks,"max_absolute_error":max_error,"failures":len(errors),"first_failure":errors[:1],
            "phase_exception":"loading-reversal frame 75 is externally overwritten before reporting; recurrence resumes at 76" if case==1 else None}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--runs",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    result={"pass":True,"cases":{}}
    for path in sorted(a.runs.glob("*_reference/run.log")):
        m=re.match(r"case(\d+)_law(\d+)_damp(\d+)_(cpu|cuda)_reference",path.parent.name)
        if not m or int(m[1])==6:continue
        rows=[json.loads(line[9:]) for line in path.read_text().splitlines() if line.startswith("V2_STATE ")]
        check=audit(rows,int(m[1]),int(m[2]),int(m[3]));result["cases"][path.parent.name]=check;result["pass"] &= check["pass"]
        print(path.parent.name+": "+json.dumps(check),flush=True)
    result["pass"] &= bool(result["cases"])
    a.output.write_text(json.dumps(result,indent=2)+"\n");raise SystemExit(0 if result["pass"] else 1)


if __name__=="__main__":main()
