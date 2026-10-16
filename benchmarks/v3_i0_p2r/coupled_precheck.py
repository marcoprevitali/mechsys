#!/usr/bin/env python3
"""Stage1 parity and Stage2 completeness BEFORE independent ledger analysis."""
import argparse,importlib.util,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('i0',Path(__file__).parents[1]/'v3_i0/analyze.py');i0=importlib.util.module_from_spec(sp);sp.loader.exec_module(i0)
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();checks=0;maxima={k:i0.Z for k in ['gamma','B','Omega','force']};saved={}
for b in ['cpu','cuda']:
 for d in (a.raw/('runs-'+b)/b).glob('*/enabled'):
  for path in d.glob('step-*-before_imprint.json'):
   step=path.name.split('-')[1];pre=i0.load(path);post=i0.load(d/f'step-{step}-after_imprint.json');per=i0.dv(pre['Per']);ref=set();pairs={(int(x['particle']),int(x['cell'])) for x in i0.arr(pre['pairs'])}
   assert len(pairs)==len(i0.arr(pre['pairs']))
   for ip,p in enumerate(pre['particles']):
    for ic in range(1000):
     _,g,r,im=i0.geometry(p,ic,per)
     if g>i0.D('1e-12')/12:ref.add((ip,ic))
   claims={(int(x['particle']),int(x['cell'])):x for x in i0.arr(post['claims']) if int(x['accepted'])}
   assert set(claims)==ref and not ref-pairs,(b,d.parent.name,step,'completeness')
   for (ip,ic),c in claims.items():
    _,g,r,im=i0.geometry(pre['particles'][ip],ic,per)
    assert i0.close(g,i0.dec(c['gamma'])) and i0.vmax(i0.sub(r,i0.dv(c['lever'])))<=i0.D('1e-12')
   for stage in ['before_rebuild','after_rebuild']:
    f=d/f'step-{step}-{stage}.json'
    if not f.exists():continue
    state=i0.load(f);ps={(int(x['particle']),int(x['cell'])) for x in i0.arr(state['pairs'])};assert len(ps)==len(i0.arr(state['pairs']))
    for ip,p in enumerate(state['particles']):
     for ic in range(1000):
      _,g,_,_=i0.geometry(p,ic,per)
      if g>i0.D('1e-12')/12:assert (ip,ic) in ps,(b,d.parent.name,stage,ic)
   if step=='0':saved[b,d.parent.name]=(pre,claims)
   checks+=1
for case in {k[1] for k in saved}:
 cp,c=saved['cpu',case];gp,g=saved['cuda',case]
 assert set(c)==set(g)
 for x,y in zip(cp['particles'],gp['particles']):
  for key in ['id','x','v','w','Q','R','free']:assert x[key]==y[key]
 for key in c:
  for field in ['gamma','B']:
   diff=abs(i0.dec(c[key][field])-i0.dec(g[key][field]));maxima[field]=max(maxima[field],diff);assert diff<=i0.D('1e-10')
  for field,metric in [('omega','Omega'),('force','force')]:
   diff=i0.vmax(i0.sub(i0.dv(c[key][field]),i0.dv(g[key][field])));maxima[metric]=max(maxima[metric],diff);assert diff<=i0.D('1e-10')
a.output.mkdir(parents=True,exist_ok=True);(a.output/'STAGE12.json').write_text(json.dumps({'status':'PASS','imprint_checks':checks,'identical_initial_cases':len(saved)//2,'maxima':maxima,'missing_candidates':0,'missing_imprints':0,'duplicates':0,'periodic_image_errors':0},default=str,indent=2)+'\n');print('Coupled Stage1/2 PASS',checks,'imprints')
