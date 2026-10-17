#!/usr/bin/env python3
"""Separate host-only debugger observation. Stops before Solve; no kernels."""
import argparse, json, os, subprocess
from pathlib import Path
from extract import HERE, DEFAULT_RAW, save, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if not k.startswith(('P1_','P2_','P2R_','MECHSYS_'))}
    env['DEBUGINFOD_URLS']=''
    receipt={}
    for label in ['baseline','candidate']:
        binary=Path(DEFAULT_RAW)/'binaries'/label
        argv=['gdb','--batch','-x',str(HERE/'inertia.gdb'),'--args',str(binary),'large',str(a.out/(label+'-pre-solve'))]
        r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30)
        log=a.out/(label+'.log');log.write_text(r.stdout)
        assert r.returncode==0 and 'INERTIA_BITS 40c0dd7f24550855 40c0dd7f24550855 40c0dd7f24550855' in r.stdout
        assert 'MASS_BITS 40b16c394b9da965' in r.stdout
        receipt[label]=dict(argv=argv,returncode=r.returncode,binary_sha256=sha(binary),log_sha256=sha(log),
          stop='AddSphere+0x20f, before Solve; inferior terminated by GDB quit',
          inertia_bits=['40c0dd7f24550855']*3,mass_bits='40b16c394b9da965',solver_steps=0)
    save(a.out/'OBSERVATION.json',receipt);print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
