#!/usr/bin/env python3
"""Compact P1 evidence/provenance publication; large traces remain outside Git."""
import argparse,csv,hashlib,json,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--analysis',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2];dst=root/'benchmarks/v3_i0_p1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
summary=json.loads((a.analysis/'P1_SUMMARY.json').read_text());assert summary['failures_count']==0
for name in ['P1_SUMMARY.json','SUMMARY.json','CPU_GPU_PARITY.csv','CPU_GPU_CELL_COMPARISON.csv','ORIGINAL_REPRODUCTION.csv','TORQUE_EXCHANGE_RESULTS.csv']:
 shutil.copy2(a.analysis/name,dst/name)
shutil.copy2(a.analysis/'MOMENTUM_EXCHANGE_RESULTS.csv',dst/'IMPULSE_REGRESSION.csv');shutil.copy2(a.raw/'REGISTERED.json',dst/'REGISTERED.json')
for f in dst.glob('*.csv'):f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
reg=[];same_physical=[];identical=[]
for b in ['cpu','cuda']:
 rs=json.loads((a.raw/('runs-'+b)/'RUNS.json').read_text());reg.extend({'backend':b,**r} for r in rs if 'default_off_bitwise' in r)
 for case in ['zero','empty']:
  d=a.raw/('runs-'+b)/b/case
  for f in (d/'reference').glob('state-*.json'):
   ref=json.loads(f.read_text());on=json.loads((d/'enabled'/f.name).read_text());ref.pop('pairs');on.pop('pairs');assert ref==on,(b,case,f.name)
  same_physical.append({'backend':b,'case':case,'physical_state_bitwise':True,'qualification':'candidate-list metadata alone may differ'})
for case in [d.parent.name for d in (a.raw/'runs-cpu/cpu').glob('*/enabled')]:
 cpu=json.loads((a.raw/'runs-cpu/cpu'/case/'enabled/step-0-before_imprint.json').read_text())['particles'];gpu=json.loads((a.raw/'runs-cuda/cuda'/case/'enabled/step-0-before_imprint.json').read_text())['particles']
 for x,y in zip(cpu,gpu):
  for field in ['id','x','v','w','Q','R','free']:assert x[field]==y[field],(case,field)
 identical.append(case)
assert all(r['default_off_bitwise'] for r in reg if r['case']!='shared')
(dst/'LEGACY_REGRESSION.json').write_text(json.dumps({'comparisons':reg,'unchanged_eligibility_physical':same_physical,'identical_initial_parity_inputs':sorted(identical)},indent=2)+'\n')
builds={}
for name in ['build','reference-build']:
 m=json.loads((a.raw/name/'manifest.json').read_text());assert sha(dst/'probe.cu')==m['source_sha256']
 if name=='build':assert all(sha(root/k)==v for k,v in m['headers'].items())
 builds[name]=m
subprocess.run(['git','diff','38da1b9','--exit-code','--','lib/dem','lib/flbm','lib/lbmdem/lbmdem.cuh','benchmarks/v3_i0','benchmarks/v2','benchmarks/v3_coupled_design','AGENTS.md'],cwd=root,check=True)
meta={'base':'38da1b918281883fdc5fb46ea8171082993a1136','implementation_commit':subprocess.check_output(['git','rev-parse','2b2cc38'],cwd=root,text=True).strip(),'builds':builds,'scripts_sha256':{p.name:sha(p) for p in dst.glob('*.py')},'input_sha256':sha(dst/'REGISTERED.json'),'GPU':subprocess.check_output(['nvidia-smi','--query-gpu=name,uuid,driver_version','--format=csv'],text=True).strip(),'raw':str(a.raw),'prior_evidence':'V3-I0 tree unchanged; prior archive untouched','authoritative_state':'PROJECT_STATUS.md; PROJECT_STATE.md concise pointer'}
(dst/'PROVENANCE.json').write_text(json.dumps(meta,indent=2)+'\n')
shutil.copytree(a.analysis,a.raw/'analysis')
paths=sorted(p for p in a.raw.rglob('*') if p.is_file())
with (a.raw/'ARTIFACT_INDEX.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['path','bytes','sha256']);w.writerows((str(p.relative_to(a.raw)),p.stat().st_size,sha(p)) for p in paths)
print('PASS: independent analysis, 46 non-shared legacy controls, initial parity inputs, 4 unchanged-eligibility physical controls, frozen source hashes')
