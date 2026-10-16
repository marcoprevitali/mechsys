#!/usr/bin/env python3
"""Reuse the frozen independent V3-I0 oracle; add separate P1 candidate/imprint/parity gates."""
import argparse,csv,importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('i0',Path(__file__).resolve().parents[1]/'v3_i0/analyze.py');i0=importlib.util.module_from_spec(spec);spec.loader.exec_module(i0)
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
i0.analyze(a.raw,a.output)
coverage=[];fail=[];reproduced=[]
for backend in ['cpu','cuda']:
 for directory in sorted((a.raw/('runs-'+backend)/backend).glob('*/enabled')):
  for path in sorted(directory.glob('step-*-before_imprint.json')):
   step=int(path.name.split('-')[1]);pre=i0.load(path);post=i0.load(directory/f'step-{step}-after_imprint.json');ps=i0.arr(pre['particles']);per=i0.dv(pre['Per']);pairs={(int(x['particle']),int(x['cell'])) for x in i0.arr(pre['pairs'])};ref=set();math=set();exact=set();boundmiss=0
   for ip,pa in enumerate(ps):
    for ic in range(1000):
     ex,g,r,image=i0.geometry(pa,ic,per);gl=i0.legacy_proxy(r,i0.dec(pa['Dmax']))
     if ex:exact.add((ip,ic))
     if g>i0.D('1e-12')/12:math.add((ip,ic))
     if gl>i0.D('1e-12')/12:ref.add((ip,ic))
     if ex and i0.dot(r,r).sqrt()>i0.dec(pa['R'])+i0.D(3).sqrt()/2:boundmiss+=1
   accepted={(int(x['particle']),int(x['cell'])) for x in i0.arr(post['claims']) if int(x['accepted'])}
   row={'backend':backend,'case':directory.parent.name,'step':step,'stage':'imprint','exact_intersections':len(exact),'math_proxy':len(math),'legacy_proxy_reference':len(ref),'candidates':len(pairs),'accepted':len(accepted),'missing_candidate':len(ref-pairs),'missing_geometric_candidate':len(exact-pairs),'missing_math_candidate':len(math-pairs),'missing_imprint':len(ref-accepted),'zero_due_existing_proxy':len(math-ref),'duplicates':len(i0.arr(pre['pairs']))-len(pairs),'bound_counterexamples':boundmiss}
   coverage.append(row)
   if row['missing_candidate'] or row['missing_geometric_candidate'] or row['missing_math_candidate'] or row['missing_imprint'] or row['duplicates'] or boundmiss or accepted-ref:fail.append(row)
   # Immediate actual before/after rebuild, independently test moved geometry against actual map.
   for stage in ['before_rebuild','after_rebuild']:
    q=directory/f'step-{step}-{stage}.json'
    if not q.exists():continue
    t=i0.load(q);pairs2={(int(x['particle']),int(x['cell'])) for x in i0.arr(t['pairs'])};required=set()
    for ip,pa in enumerate(i0.arr(t['particles'])):
     for ic in range(1000):
      _,_,r,_=i0.geometry(pa,ic,per)
      if i0.legacy_proxy(r,i0.dec(pa['Dmax']))>i0.D('1e-12')/12:required.add((ip,ic))
    row2={**row,'stage':stage,'legacy_proxy_reference':len(required),'candidates':len(pairs2),'accepted':'NOT_EVALUATED','missing_candidate':len(required-pairs2),'missing_imprint':'NOT_EVALUATED','duplicates':len(i0.arr(t['pairs']))-len(pairs2)};coverage.append(row2)
    # Before rebuild may legitimately exceed the entry Alpha allowance; report, don't mislabel force-time validity.
    if stage=='after_rebuild' and (required-pairs2 or row2['duplicates']):fail.append(row2)
 for directory in sorted((a.raw/('runs-'+backend)/backend).glob('*/off')):
  case=directory.parent.name;pre=i0.load(directory/'step-0-before_imprint.json');post=i0.load(directory/'step-0-after_imprint.json');acc=sum(int(x['accepted']) for x in i0.arr(post['claims']));reproduced.append({'backend':backend,'case':case,'initial_candidates':len(i0.arr(pre['pairs'])),'initial_accepted':acc})
comparison=list(csv.DictReader((a.output/'CPU_GPU_CELL_COMPARISON.csv').open()))
for r in comparison:
 if r['parity']!='PASS':fail.append(r)
 for field in ['gamma_max_difference','B_max_difference','Omega_max_difference','solid_increment_max_difference']:
  if abs(i0.dec(r[field]))>i0.D('1e-10'):fail.append(r)
i0.writecsv(a.output/'CPU_GPU_PARITY.csv',coverage);i0.writecsv(a.output/'ORIGINAL_REPRODUCTION.csv',reproduced)
summary={'coverage_rows':len(coverage),'parity_cases':len(comparison),'failures':fail,'failures_count':len(fail),'old_centered': [r for r in reproduced if r['case']=='moving'],'legacy_shared':'retained; explicit corrected rejection; not accepted as a physical case'}
(a.output/'P1_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if fail:sys.exit(1)
