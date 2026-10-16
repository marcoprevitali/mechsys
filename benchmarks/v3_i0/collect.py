#!/usr/bin/env python3
"""Publish compact derived evidence and provenance; never alter raw observations."""
import argparse,csv,hashlib,json,shutil,subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];dest=root/'benchmarks/v3_i0';final=a.raw/'final';analysis=final/'analysis'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cmd(args,cwd=root):return subprocess.check_output(args,cwd=cwd,text=True).strip()
summary=json.loads((analysis/'SUMMARY.json').read_text());assert summary['failures_count']==0
for path in analysis.iterdir():
    if path.is_file():shutil.copy2(path,dest/path.name)
reg=[];run_count=0
for backend in ['cpu','cuda']:
    runs=json.loads((final/('runs-'+backend)/'runs.json').read_text());run_count+=sum('mode' in x for x in runs)
    for r in runs:
        if 'bitwise_serialized_states' in r:
            if r['case']!='shared':assert all(r['bitwise_serialized_states'].values()),r
            # Shared ownership is preregistered unsupported. Preserve its strict FAIL;
            # do not normalize fields or use it as observational-equivalence evidence.
            reg.append(r)
        elif r['case']=='VV fail-closed':assert r['exit']!=0
        else:assert r['exit']==0
(dest/'REGRESSION.json').write_text(json.dumps({'bounded_runs':run_count,'comparisons':reg},indent=2)+'\n')
builds={}
for name in ['observer','reference']:
    build=json.loads((a.raw/('build-'+name+'-v5')/'manifest.json').read_text())
    assert sha(dest/'probe.cu')==build['source_sha256']
    base=root if name=='observer' else a.raw.parent/'reference'
    assert all(sha(base/k)==v for k,v in build['headers'].items())
    builds[name]=build
subprocess.run(['git','diff','d801c80cce15691b2a886a31d7e0bd864de35c10','--exit-code','--','lib/dem','benchmarks/v2','benchmarks/v3_coupled_design','AGENTS.md'],cwd=root,check=True)
original=Path('/home/msys/mechsys');diff=subprocess.check_output(['git','diff','HEAD','--binary'],cwd=original)
assert hashlib.sha256(diff).hexdigest()=='e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9'
prior={}
for path,expected in [('/home/msys/git/mechsys-v2-restart','2b8d8c335709046e224f4c43aa930144ae6854e7'),('/home/msys/git/mechsys-v3-coupled-design','d801c80cce15691b2a886a31d7e0bd864de35c10')]:
    assert cmd(['git','rev-parse','HEAD'],path)==expected;assert not cmd(['git','status','--porcelain=v1','-uall'],path);prior[path]=expected
metadata={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'reference_commit':'d801c80cce15691b2a886a31d7e0bd864de35c10',
 'instrumentation_commit':'28e292f'+cmd(['git','rev-parse','28e292f'])[7:],'evidence_collection_commit':cmd(['git','rev-parse','HEAD']),
 'branch':cmd(['git','branch','--show-current']),'source_headers_sha256':builds['observer']['headers'],
 'probe_source_sha256':sha(dest/'probe.cu'),'test_manifest_sha256':sha(dest/'TEST_MANIFEST.json'),
 'scripts_sha256':{x.name:sha(x) for x in dest.glob('*.py')},'builds':builds,
 'gcc':cmd(['g++','--version']).splitlines()[0],'cuda':cmd(['/usr/local/cuda-12.6/bin/nvcc','--version']),
 'gpu':cmd(['nvidia-smi','--query-gpu=name,uuid,driver_version,compute_cap','--format=csv']),
 'original_tracked_diff_sha256':hashlib.sha256(diff).hexdigest(),'original_status':cmd(['git','status','--porcelain=v1','-uall'],original),
 'prior_clones_verified_clean':prior,'remotes':cmd(['git','remote','-v']),
 'raw_preparation_root':str(a.raw),'durable_raw_directory':'/home/msys/SIMS/mechsys_v3_i0_validation/20261016-v3-i0-exchange-audit',
 'persistent_clone':'/home/msys/git/mechsys-v3-i0-exchange-audit','phase':'legacy, entry imprint -> drift -> actual collision write before swaps/stream',
 'units':'common M,L,T; a=h=c=rho_ref=1, J_ref_cell=.01, J_ref_problem=10',
 'reference_error_bound':'70-digit Decimal with <1e-60 absolute reference error at registered magnitudes/contributor counts; negligible against unchanged FP64 budgets'}
(dest/'PROVENANCE.json').write_text(json.dumps(metadata,indent=2)+'\n')
# Inventory the large artifacts outside Git; archive packaging happens after collection.
paths=sorted(x for x in a.raw.rglob('*') if x.is_file() and x.name!='ARTIFACT_INDEX.csv')
with (a.raw/'ARTIFACT_INDEX.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['path','bytes','sha256'])
    for path in paths:w.writerow([str(path.relative_to(a.raw)),path.stat().st_size,sha(path)])
(dest/'ARTIFACT_SUMMARY.json').write_text(json.dumps({'files':len(paths),'bytes':sum(x.stat().st_size for x in paths),'inventory_sha256':sha(a.raw/'ARTIFACT_INDEX.csv'),'includes':'final raw traces, all pilots, failed build logs, manifests, executables and prior failed mathematical-proxy oracle outputs'},indent=2)+'\n')
print('compact evidence, source checks, original/prior-clone preservation and artifact inventory PASS')
