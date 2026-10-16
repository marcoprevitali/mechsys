#!/usr/bin/env python3
"""Small sequential audit/regression driver. Never launches timing campaigns."""
import argparse, hashlib, json, os, subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--observer',type=Path,required=True);p.add_argument('--reference',type=Path,required=True)
p.add_argument('--cases',nargs='+',default=['zero','fixed','moving','rotating','partial','boundary','periodic','rebuild','fconv','shared','contact'])
p.add_argument('--backends',nargs='+',default=['cpu','cuda']);a=p.parse_args();a.raw.mkdir(parents=True,exist_ok=True)
results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for backend in a.backends:
    for case in a.cases:
        paths={}
        for mode,build,on in [('reference',a.reference,False),('default-off',a.observer,False),('enabled',a.observer,True)]:
            out=a.raw/backend/case/mode
            if out.exists():raise RuntimeError('Refusing to overwrite '+str(out))
            out.mkdir(parents=True);env=dict(os.environ);env['MECHSYS_EXCHANGE_AUDIT']='1' if on else '0'
            cmd=[str((build/backend).resolve()),case,str(out.resolve())]
            with (out/'run.log').open('w') as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
            result={'backend':backend,'case':case,'mode':mode,'command':cmd,'exit':r.returncode,'binary_sha256':sha(build/backend)}
            paths[mode]=out;results.append(result);print(backend,case,mode,r.returncode,flush=True)
            if r.returncode:raise RuntimeError('Runtime failed; preserve evidence, inspect '+str(out))
        ref=paths['reference'];states=sorted(ref.glob('state-*.json'))
        comparisons={m:all(sha(p)==sha(paths[m]/p.name) for p in states) for m in ['default-off','enabled']}
        results.append({'backend':backend,'case':case,'bitwise_serialized_states':comparisons,'state_count':len(states),
                        'qualification':'shared enabled races are not a bitwise observational guarantee' if case=='shared' else ''})
        (a.raw/'runs.json').write_text(json.dumps(results,indent=2)+'\n')
        if case!='shared' and not all(comparisons.values()):
            raise RuntimeError('Observational comparison differs: STOP affected audit; inspect raw states '+str(paths))
    guard=a.raw/backend/'guard';guard.mkdir()
    with (guard/'run.log').open('w') as log:r=subprocess.run([str((a.observer/backend).resolve()),'moving',str(guard),'1'],stdout=log,stderr=subprocess.STDOUT)
    results.append({'backend':backend,'case':'VV fail-closed','exit':r.returncode});assert r.returncode!=0
    (a.raw/'runs.json').write_text(json.dumps(results,indent=2)+'\n')
