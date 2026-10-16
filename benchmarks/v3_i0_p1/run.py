#!/usr/bin/env python3
"""Registered bounded P1 matrix; immutable original fixtures plus explicit extensions."""
import argparse,csv,hashlib,json,os,subprocess,sys
from pathlib import Path
CASES={n:{} for n in ['zero','fixed','moving','rotating','partial','boundary','periodic','rebuild','fconv','contact','shared']}
for j,axis in enumerate('xyz'):
    x=[5.2,5.1,5.3];v=[0,0,0];x[j]=9.999;v[j]=.002
    CASES['cross_'+axis]={'P1_POSITION':' '.join(map(str,x)),'P1_VELOCITY':' '.join(map(str,v)),'P1_ALPHA':'.0001'}
    v[j]=.001;CASES['translate_'+axis]={'P1_POSITION':'5.11 5.23 5.37','P1_VELOCITY':' '.join(map(str,v)),'P1_ALPHA':'.0001'}
CASES.update({'offset1':{'P1_POSITION':'5.49 5.49 5.49'},'offset2':{'P1_POSITION':'5.9 5.01 5.8'},
 'small':{'P1_RADIUS':'.2','P1_POSITION':'5.5 5.5 5'},'large':{'P1_RADIUS':'2.2'},
 'wide_skin':{'P1_ALPHA':'6'},'near_inside':{'P1_RADIUS':str(2**.5/2+1e-7)},
 'near_outside':{'P1_RADIUS':str(2**.5/2-1e-7)},'empty':{'P1_POSITION':'-100 -100 -100'}})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--observer',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--backend',required=True);p.add_argument('--register',action='store_true');a=p.parse_args()
 a.raw.mkdir(parents=True,exist_ok=True)
 if a.register:
  (a.raw/'REGISTERED.json').write_text(json.dumps({'cases':CASES,'precision':'FP64','budgets':'unchanged V3-I0/ V3-D','corrected_excluded':['shared','contact','fconv'],'shared':'explicit rejection; conservative geometric conflict guard may reject zero-proxy shared cells too'},indent=2)+'\n');sys.exit()
 results=[]
 for case,params in CASES.items():
  states={}
  modes=['reference','off','on'] if case not in ['shared','contact','fconv'] else ['reference','off']
  if case=='wide_skin':modes=['on'] # legacy window duplicates/observer overflow; outside old non-shared scope
  for mode in modes:
   out=a.raw/('runs-'+a.backend)/a.backend/case/('enabled' if mode=='on' else mode)
   if out.exists():raise RuntimeError('Refuse overwrite '+str(out))
   out.mkdir(parents=True);env={**os.environ,**params,'P1_MODE':'1' if mode=='on' else '0','MECHSYS_EXCHANGE_AUDIT':'1'}
   exe=(a.reference if mode=='reference' else a.observer)/a.backend
   cmd=[str(exe.resolve()),case,str(out.resolve())]
   with (out/'run.log').open('w') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
   results.append({'case':case,'mode':mode,'exit':r.returncode,'command':cmd,'environment':params,'binary_sha256':sha(exe)});print(a.backend,case,mode,r.returncode,flush=True)
   (a.raw/('runs-'+a.backend)/'RUNS.json').write_text(json.dumps(results,indent=2)+'\n')
   if r.returncode:raise RuntimeError('Unexpected runtime failure '+str(out))
   states[mode]=out
  if 'reference' not in states:continue
  equal=all(sha(x)==sha(states['off']/x.name) for x in states['reference'].glob('state-*.json'))
  results.append({'case':case,'default_off_bitwise':equal,'qualification':'shared unsupported; no strict equivalence claim' if case=='shared' else ''})
  if not equal and case!='shared':raise RuntimeError('STOP default-off changed '+case)
  (a.raw/('runs-'+a.backend)/'RUNS.json').write_text(json.dumps(results,indent=2)+'\n')
 # Separate negative corrected shared mode: must fail before any production imprint.
 out=a.raw/('runs-'+a.backend)/'shared-rejection';out.mkdir();env={**os.environ,'P1_MODE':'1','MECHSYS_EXCHANGE_AUDIT':'1'}
 with (out/'run.log').open('w') as f:r=subprocess.run([str((a.observer/a.backend).resolve()),'shared',str(out.resolve())],env=env,stdout=f,stderr=subprocess.STDOUT)
 assert r.returncode!=0 and 'shared geometric/positive-occupancy cell blocked' in (out/'run.log').read_text()
 print(a.backend,'shared explicit rejection PASS',flush=True)
