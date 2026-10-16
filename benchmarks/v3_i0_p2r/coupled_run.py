#!/usr/bin/env python3
"""P2R on vs P1-only legacy occupancy, identical initial cases, tiny actual Solves."""
import argparse,hashlib,importlib.util,json,os,subprocess
from pathlib import Path
sp=importlib.util.spec_from_file_location('p1',Path(__file__).parents[1]/'v3_i0_p1/run.py');p1=importlib.util.module_from_spec(sp);sp.loader.exec_module(p1)
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--raw',type=Path,required=True);p.add_argument('--backend',required=True);p.add_argument('--geometry-summary',type=Path,required=True);a=p.parse_args()
assert json.loads(a.geometry_summary.read_text())['failures_count']==0,'STOP geometry gates first'
cases={k:v for k,v in p1.CASES.items() if k not in ['shared','contact','fconv']}
cases['coupled_tangent_witness']={'P1_RADIUS':'1','P1_POSITION':'5.3 5.2 5.1'}
results=[]
for case,params in cases.items():
 for robust in [False,True]:
    out=a.raw/('runs-'+a.backend)/a.backend/case/('enabled' if robust else 'legacy')
    if out.exists():raise RuntimeError('Refuse overwrite '+str(out))
    out.mkdir(parents=True);env={k:v for k,v in os.environ.items() if not k.startswith(('P1_','P2_','P2R_','MECHSYS_'))}
    env.update(params);env.update({'P1_MODE':'1','P2_MODE':str(int(robust)),'P2R_MODE':str(int(robust)),'MECHSYS_EXCHANGE_AUDIT':'1'})
    exe=(a.build/a.backend).resolve();cmd=[str(exe),case,str(out.resolve())]
    with (out/'run.log').open('w') as h:r=subprocess.run(cmd,env=env,stdout=h,stderr=subprocess.STDOUT)
    results.append({'case':case,'robust':robust,'exit':r.returncode,'command':cmd,'parameters':params,'binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()})
    (a.raw/('RUNS-'+a.backend+'.json')).write_text(json.dumps(results,indent=2)+'\n');print(a.backend,case,'robust' if robust else 'legacy',r.returncode,flush=True)
    assert r.returncode==0,'STOP coupled failure '+str(out)
