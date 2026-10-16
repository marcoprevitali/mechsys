#!/usr/bin/env python3
"""Verify exact P1 clean delivery, preserved evidence, and origin-only topic."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--clone',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Refuse overwrite receipt')
def git(*args,where=a.clone):return subprocess.check_output(['git',*args],cwd=where,text=True).strip()
branch='fix/v3-i0-p1-cell-coverage';assert git('branch','--show-current')==branch
assert git('rev-parse','HEAD')==a.sha and not git('status','--porcelain=v1','-uall')
assert git('rev-parse','--is-shallow-repository')=='false'
assert git('remote','get-url','origin')=='https://github.com/marcoprevitali/mechsys.git'
assert git('remote','get-url','--push','origin')=='https://github.com/marcoprevitali/mechsys.git'
assert git('remote','get-url','upstream')=='https://github.com/Axtal/mechsys.git'
assert git('remote','get-url','--push','upstream')=='PUSH_DISABLED'
remote=git('ls-remote','origin','refs/heads/'+branch).split()[0];assert remote==a.sha
subprocess.run(['git','diff','38da1b9','--exit-code','--','lib/dem','lib/flbm','lib/lbmdem/lbmdem.cuh','benchmarks/v3_i0','benchmarks/v2','benchmarks/v3_coupled_design','AGENTS.md'],cwd=a.clone,check=True)
for path,sha in [('/home/msys/git/mechsys-v3-i0-exchange-audit','38da1b918281883fdc5fb46ea8171082993a1136'),('/home/msys/git/mechsys-v3-coupled-design','d801c80cce15691b2a886a31d7e0bd864de35c10'),('/home/msys/git/mechsys-v2-restart','2b8d8c335709046e224f4c43aa930144ae6854e7')]:assert git('rev-parse','HEAD',where=path)==sha and not git('status','--porcelain=v1','-uall',where=path)
old=subprocess.check_output(['git','diff','HEAD','--binary'],cwd='/home/msys/mechsys');assert hashlib.sha256(old).hexdigest()=='e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9'
archive=json.loads((a.output.parent/'ARCHIVE_VERIFICATION.json').read_text());assert archive['status']=='PASS'
data={'milestone':'V3-I0-P1','status':'PASS within registered canonical single-geometric-owner subset','branch':branch,'commit':a.sha,'remote_sha':remote,'working_tree':'clean','clone':str(a.clone),'gates':{'P1-'+k:'PASS' for k in 'ABCDEFGHIJK'},'archive':archive,'defaults':'ConservativeSphereCells=false; no production promotion','unresolved':['edge-loop proxy defect','shared support','production limiter','coupled VV/restart'],'next':'Separate reviewed SphereCube edge-loop correction; no automatic implementation'}
a.output.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
