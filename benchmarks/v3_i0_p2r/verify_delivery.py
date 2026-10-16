#!/usr/bin/env python3
"""Delivery PASS is not scientific PASS. P2R-K must retain its strict FAIL."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--clone',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Refuse overwrite receipt')
def git(*args,where=a.clone):return subprocess.check_output(['git',*args],cwd=where,text=True).strip()
branch='fix/v3-i0-p2r-robust-tangency'
assert git('branch','--show-current')==branch and git('rev-parse','HEAD')==a.sha
assert not git('status','--porcelain=v1','-uall') and git('rev-parse','--is-shallow-repository')=='false'
assert git('remote','get-url','origin')=='https://github.com/marcoprevitali/mechsys.git'
assert git('remote','get-url','--push','origin')=='https://github.com/marcoprevitali/mechsys.git'
assert git('remote','get-url','upstream')=='https://github.com/Axtal/mechsys.git'
assert git('remote','get-url','--push','upstream')=='PUSH_DISABLED'
remote=git('ls-remote','origin','refs/heads/'+branch).split()[0];assert remote==a.sha
protected=['lib/flbm','lib/dem/domain.h','lib/dem/dem.cuh','lib/dem/interacton.h','lib/dem/particle.h','lib/dem/checkpoint.h','benchmarks/v3_i0','benchmarks/v3_i0_p1','benchmarks/v3_i0_p2','benchmarks/v2','benchmarks/v3_coupled_design','AGENTS.md']
assert not git('diff','bf66169','--',*protected)
changed=git('diff','--name-only','bf66169','--','lib').splitlines()
assert set(changed)=={'lib/dem/special_functions.h','lib/dem/sphere_cube_robust.h','lib/lbmdem/Domain.h','lib/lbmdem/lbmdem.cuh'}
freeze=json.loads((a.clone/'benchmarks/v3_i0_p2r/FROZEN_MANIFEST.json').read_text())
for name,sha in freeze['frozen_files_sha256'].items():assert hashlib.sha256((a.clone/name).read_bytes()).hexdigest()==sha
prior={
 '/home/msys/git/mechsys-v3-i0-p2-edge-proxy':'bf6616973be1335da1caa7d75f8a34aa0f6c1c22',
 '/home/msys/git/mechsys-v3-i0-p1-cell-coverage':'e0d6c2fcc581b4caf9d020ebbf05f15c2f5a102f',
 '/home/msys/git/mechsys-v3-i0-exchange-audit':'38da1b918281883fdc5fb46ea8171082993a1136',
 '/home/msys/git/mechsys-v3-coupled-design':'d801c80cce15691b2a886a31d7e0bd864de35c10',
 '/home/msys/git/mechsys-v2-restart':'2b8d8c335709046e224f4c43aa930144ae6854e7'}
for path,head in prior.items():assert git('rev-parse','HEAD',where=path)==head and not git('status','--porcelain=v1','-uall',where=path)
old=subprocess.check_output(['git','diff','HEAD','--binary'],cwd='/home/msys/mechsys');oldsha=hashlib.sha256(old).hexdigest()
assert oldsha=='e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9'
archive=json.loads((a.output.parent/'ARCHIVE_VERIFICATION.json').read_text());assert archive['status']=='PASS'
s=json.loads((a.clone/'benchmarks/v3_i0_p2r/P2R_SUMMARY.json').read_text());assert s['gates']['P2R-K']=='FAIL' and s['geometry_failures']==0
gates=s['gates'];gates['P2R-N']='PASS'
data={'milestone':'V3-I0-P2R','scientific_status':'PARTIAL; strict default-off K FAIL despite baseline self-nondeterminism','delivery_status':'PASS',
 'branch':branch,'commit':a.sha,'remote_sha':remote,'working_tree':'clean','full_clone':str(a.clone),'gates':gates,'archive':archive,
 'prior_clones_preserved':prior,'original_tracked_diff_sha256':oldsha,'frozen_evidence_files_verified':len(freeze['frozen_files_sha256']),
 'defaults':'all experimental occupancy modes false, unmerged','next':'User direction on strict default-off reproducibility contract; no implicit waiver or force reduction work'}
a.output.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
