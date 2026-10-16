#!/usr/bin/env python3
"""Diagnostic geometry operation counts, not production speed qualification."""
import argparse,csv,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--coupled',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--results',type=Path);a=p.parse_args()
if a.results:
 rows=[]
 for b in ['cpu','cuda']:
  rr=list(csv.DictReader((a.results/('representative-'+b+'.csv')).open()))
  assert all(float(r['length'])>=0 for r in rr)
  rows.append({'dataset':'representative_candidate_geometry','backend':b,'edge_evaluations':len(rr),'ordinary_FP64':0,'compensated':len(rr),'exact_predicate_fallback':0,'max_fallback_depth':0,'always_exact_expansion':len(rr),'max_expansion_components':max(int(r['components']) for r in rr)})
 with a.output.open('w') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 print('Representative diagnostic edges/backend',len(rr))
else:
 sp=importlib.util.spec_from_file_location('i0',Path(__file__).parents[1]/'v3_i0/analyze.py');i0=importlib.util.module_from_spec(sp);sp.loader.exec_module(i0);rows=[]
 for d in sorted((a.coupled/'runs-cpu/cpu').glob('*/enabled')):
  pre=i0.load(d/'step-0-before_imprint.json');per=i0.dv(pre['Per'])
  for pair in i0.arr(pre['pairs']):
   ic=int(pair['cell']);p=pre['particles'][int(pair['particle'])];r,_=i0.lever(p,ic,per);c=list(map(float,i0.center(ic)));x=[cc-float(v) for cc,v in zip(c,r)]
   rows.append([*x,*c,float(p['R']),1.])
 with a.output.open('w') as h:
  for r in rows:h.write(' '.join(format(x,'.17g') for x in r)+'\n')
 print('Representative sampled candidate geometries',len(rows))
