#!/usr/bin/env python3
"""Unsupported modes reject before collision; no production limiter activation."""
import argparse,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
tests=[('no_p1','moving',{'P1_MODE':'0'},[],'requires ConservativeSphereCells'),
 ('no_p2','moving',{'P2_MODE':'0'},[],'requires CorrectTwelveEdgeProxy'),
 ('noncanonical','moving',{'P2_NONCANONICAL':'1'},[],'canonical centered spheres only'),
 ('nonunit_conversion','fconv',{},[],'Fconv=1'),
 ('smagorinsky','moving',{'P2_SC':'1'},[],'Sc=0'),
 ('shared','shared',{},[],'shared geometric/positive-occupancy cell blocked'),
 ('vv_guard','moving',{},['1'],'coupled Velocity-Verlet/full-state restart is not implemented'),
 ('limiter_risk','moving',{'P2_LIMITER_RISK':'1'},[],'production limiter risk blocked before collision'),
 ('exponent_envelope','empty',{'P1_POSITION':'1e130 5 5'},[],'outside certified FP64 exponent envelope')]
rows=[]
for b in ['cpu','cuda']:
 for name,case,params,extra,message in tests:
  out=a.output/(b+'-'+name);out.mkdir();env={k:v for k,v in os.environ.items() if not k.startswith(('P1_','P2_','P2R_','MECHSYS_'))}
  env.update({'P1_MODE':'1','P2_MODE':'1','P2R_MODE':'1','MECHSYS_EXCHANGE_AUDIT':'1'});env.update(params)
  cmd=[str((a.build/b).resolve()),case,str(out.resolve()),*extra]
  r=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=60);(out/'run.log').write_text(r.stdout)
  ok=r.returncode!=0 and message in r.stdout and not list(out.glob('*after_collision.json'))
  rows.append({'backend':b,'case':name,'command':cmd,'environment':params,'exit':r.returncode,'pass':ok,'expected_message':message,'production_collision_occurred':bool(list(out.glob('*after_collision.json')))})
  (a.output/'SUMMARY.json').write_text(json.dumps({'tests':rows,'pass':all(r['pass'] for r in rows)},indent=2)+'\n');print(b,name,'PASS' if ok else 'FAIL',flush=True)
  assert ok,'STOP negative guard failure '+str(out)
