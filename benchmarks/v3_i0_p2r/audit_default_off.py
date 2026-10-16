#!/usr/bin/env python3
"""Read-only diagnosis; never turn observed strict FAIL into a PASS."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def load(p):return json.loads(p.read_text())
def differences(x,y,path=''):
 rows=[]
 if isinstance(x,dict):
  for k in x:rows+=differences(x[k],y[k],path+'/'+k)
 elif isinstance(x,list):
  for k,(xx,yy) in enumerate(zip(x,y)):rows+=differences(xx,yy,path+'/'+str(k))
 elif x!=y:
  try:d=abs(float(x)-float(y))
  except (TypeError,ValueError):d=None
  rows.append({'path':path,'base':x,'other':y,'absolute_difference':d})
 return rows
original=a.raw/'p1-regression/runs-cuda/cuda/large';diff=[]
for f in sorted((original/'reference').glob('state-*.json')):
 diff.extend({'snapshot':f.name,**r} for r in differences(load(f),load(original/'off'/f.name)))
assert diff
reps=load(a.raw/'default-off-diagnosis/RUNS.json');hashes={}
for b in ['base','candidate']:
 rr=[r for r in reps if r['label']==b];hashes[b]={n:len({r['hashes'][n] for r in rr}) for n in ['state-0.json','state-1.json','state-2.json']}
assert hashes['base']['state-1.json']>1,'baseline nondeterminism not established'
dirs=[a.raw/'default-off-diagnosis'/(r['label']+'-'+str(r['repetition'])) for r in reps]
claims=[load(d/'step-0-after_imprint.json')['claims'] for d in dirs]
claim_equal=all(c==claims[0] for c in claims)
inputs=[load(d/'step-0-before_imprint.json') for d in dirs]
input_equal=all(c==inputs[0] for c in inputs)
result={'strict_default_off_result':'FAIL CUDA large; not relaxed or rerun until lucky PASS',
 'root_cause_evidence':'same baseline executable/identical initial inputs gives multiple state hashes; per-candidate initial claims identical, live accumulation differs',
 'atomic_order_attribution':'supported by identical claim forces/torques, varying actual live sums and existing atomicAdd accumulation; no deterministic reduction implemented',
 'same_initial_inputs':input_equal,'same_initial_per_candidate_claims':claim_equal,
 'unique_hashes_by_executable':hashes,'first_strict_differences':diff,
 'maximum_strict_absolute_difference':max(r['absolute_difference'] or 0 for r in diff),
 'gate':'P2R-K FAIL; strict compatibility acceptance blocked pending user decision, overall not PASS',
 'preservation':'all failed and self-repeatability runs retained; historical P1/P2 results not rewritten',
 'next':'separate default-off reproducibility study or explicitly authorized deterministic accumulation work; do not silently replace bitwise gate with tolerance'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='first_strict_differences'},indent=2))
