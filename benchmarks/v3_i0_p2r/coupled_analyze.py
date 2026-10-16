#!/usr/bin/env python3
"""Unmodified I0 independent ledger, explicitly routed to the intended proxy.

I0's compatibility-oracle hook legacy_proxy normally models the defective loop.
For THIS analysis only, route that hook to the independent quadratic. Never
change I0 source/artifacts, collision arithmetic, budgets or tolerance checks.
Other inherited 'legacy' field names describe legacy coupled integration.
"""
import argparse,csv,importlib.util,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
base=Path(__file__).parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
i0=module('i0',base/'v3_i0/analyze.py');ref=module('ref',base/'v3_i0_p2/TWELVE_EDGE_REFERENCE.py')
assert json.loads((a.output/'STAGE12.json').read_text())['status']=='PASS','Stage1/2 first'
i0.legacy_proxy=lambda r,R:sum(ref.edges([i0.Z]*3,r,R,1),i0.Z)/12
i0.analyze(a.raw,a.output)
summary=json.loads((a.output/'SUMMARY.json').read_text());assert summary['known_mathematical_proxy_failures']==0
parity=list(csv.DictReader((a.output/'CPU_GPU_CELL_COMPARISON.csv').open()))
coverage=list(csv.DictReader((a.output/'CELL_PARITY_RESULTS.csv').open()))
for row in parity:
 assert row['parity']=='PASS'
 for f in ['gamma_max_difference','B_max_difference','Omega_max_difference','solid_increment_max_difference']:assert i0.dec(row[f])<=i0.D('1e-10')
for row in coverage:
 for backend in ['CPU','GPU']:
  for f in ['candidate_missing','duplicates','conflicts','bad_images']:
   assert int(row[backend+'_'+f])==0,(row['case'],row['stage'],f)
  if row['stage']=='imprint':assert int(row[backend+'_missing'])==0 and int(row[backend+'_extra'])==0
# Verify identical INITIAL poses and incoming fluid populations, rather than
# assuming independently evolved states are comparable.
for case in [r['case'] for r in parity]:
 for mode in ['enabled','legacy']:
  cpu=a.raw/'runs-cpu/cpu'/case/mode;gpu=a.raw/'runs-cuda/cuda'/case/mode
  c=i0.load(cpu/'step-0-before_imprint.json');g=i0.load(gpu/'step-0-before_imprint.json')
  for x,y in zip(c['particles'],g['particles']):
   for key in ['id','x','v','w','Q','R','free']:assert x[key]==y[key],(case,key)
rows=[];totals=[]
for b in ['cpu','cuda']:
 for directory in (a.raw/('runs-'+b)/b).glob('*/enabled'):
  case=directory.parent.name;old=directory.parent/'legacy';n=i0.load(directory/'step-0-before_collision.json');o=i0.load(old/'step-0-before_collision.json')
  ni=i0.load(directory/'step-0-before_imprint.json');oi=i0.load(old/'step-0-before_imprint.json')
  for np,op in zip(ni['particles'],oi['particles']):
   for key in ['id','x','v','w','Q','R','free']:assert np[key]==op[key]
  newclaims={int(r['cell']):r for r in i0.arr(i0.load(directory/'step-0-after_imprint.json')['claims']) if int(r['accepted'])}
  oldclaims={int(r['cell']):r for r in i0.arr(i0.load(old/'step-0-after_imprint.json')['claims']) if int(r['accepted'])}
  for ic,(ng,og) in enumerate(zip(n['grid'],o['grid'])):
   for key in ['f','rho','vel','bforce']:assert ng[key]==og[key],(b,case,ic,key)
   gc=i0.dec(ng['gamma']);gl=i0.dec(og['gamma']);tau=i0.D.from_float(.8)
   B=lambda x:x*(tau-i0.HALF)/(1-x+tau-i0.HALF)
   omc=i0.dv(ng['omega']);oml=i0.dv(og['omega']);ds=i0.sub(i0.mul(omc,B(gc)),i0.mul(oml,B(gl)));jf=i0.impulse(ds)
   nc=newclaims.get(ic);oc=oldclaims.get(ic);zero=['0']*3
   jp=i0.sub(i0.dv(nc['force'] if nc else zero),i0.dv(oc['force'] if oc else zero));kt=i0.sub(i0.dv(nc['torque'] if nc else zero),i0.dv(oc['torque'] if oc else zero))
   nw=i0.cross(i0.dv(nc['lever']),i0.dv(nc['force'])) if nc else [i0.Z]*3
   ow=i0.cross(i0.dv(oc['lever']),i0.dv(oc['force'])) if oc else [i0.Z]*3
   affected=abs(gc-gl)>i0.D('1e-10')
   if not affected:
    assert i0.vmax(ds)<=i0.D('1e-10') and i0.vmax(jp)<=i0.D('1e-10') and i0.vmax(kt)<=i0.D('1e-10')
   rows.append({'backend':b,'case':case,'step':0,'cell':ic,'cell_center':json.dumps(list(map(int,i0.center(ic)))),'comparison':'identical registered initial particle and fluid inputs',
    'gamma_legacy':str(gl),'gamma_robust':str(gc),'delta_gamma':str(gc-gl),'delta_B':str(B(gc)-B(gl)),
    'delta_Omega':json.dumps(i0.sub(omc,oml),default=str),'delta_J_fluid':json.dumps(jf,default=str),'delta_J_particle':json.dumps(jp,default=str),
    'delta_world_torque':json.dumps(i0.sub(nw,ow),default=str),'delta_body_torque':json.dumps(kt,default=str),'delta_J_residual_max':str(i0.vmax(i0.add(jf,jp))),'affected':affected,'legacy_zero_robust_positive':gl==0 and gc>0})
  selected=[r for r in rows if r['backend']==b and r['case']==case]
  np=i0.load(directory/'step-0-after_imprint.json')['particles'];op=i0.load(old/'step-0-after_imprint.json')['particles']
  total=lambda key:[sum((i0.D(json.loads(r[key])[k]) for r in selected),i0.Z) for k in range(3)]
  actualF=i0.sub(i0.sub(i0.dv(np[0]['Flbm']),i0.dv(ni['particles'][0]['Flbm'])),i0.sub(i0.dv(op[0]['Flbm']),i0.dv(oi['particles'][0]['Flbm'])))
  actualT=i0.sub(i0.sub(i0.dv(np[0]['T']),i0.dv(ni['particles'][0]['T'])),i0.sub(i0.dv(op[0]['T']),i0.dv(oi['particles'][0]['T'])))
  totals.append({'backend':b,'case':case,'affected_cells':sum(r['affected'] for r in selected),'delta_J_fluid':json.dumps(total('delta_J_fluid'),default=str),'delta_J_particle_actual':json.dumps(actualF,default=str),'delta_world_torque':json.dumps(total('delta_world_torque'),default=str),'delta_body_torque_actual':json.dumps(actualT,default=str),'reaction_vs_cell_sum_error':str(i0.vmax(i0.sub(actualF,total('delta_J_particle'))))})
i0.writecsv(a.output/'OCCUPANCY_FORCE_DIFFERENCES.csv',rows)
i0.writecsv(a.output/'TOTAL_FORCE_DIFFERENCES.csv',totals)
summary['reference_routing']='independent P2 quadratic; frozen I0 collision and exchange budgets unchanged'
summary['identical_initial_cases']=len(parity);summary['affected_initial_backend_cells']=sum(r['affected'] for r in rows)
summary['effect_max_delta_gamma']=str(max(abs(i0.D(r['delta_gamma'])) for r in rows))
affected=[r for r in rows if r['affected']]
summary['effect_mean_abs_delta_gamma_affected']=str(sum(abs(i0.D(r['delta_gamma'])) for r in affected)/len(affected))
summary['legacy_zero_robust_positive_cells']=sum(r['legacy_zero_robust_positive'] for r in rows)
summary['max_corrected_impulse_change']=str(max(i0.vmax([i0.D(x) for x in json.loads(r['delta_J_particle_actual'])]) for r in totals))
summary['max_corrected_body_torque_change']=str(max(i0.vmax([i0.D(x) for x in json.loads(r['delta_body_torque_actual'])]) for r in totals))
(a.output/'P2R_COUPLED_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print('P2R independent coupled gates PASS',len(parity),'cases/backend')
