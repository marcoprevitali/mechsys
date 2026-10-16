#!/usr/bin/env python3
"""Reproduce the bounded probe with the recorded V2 FP64 toolchain, not a benchmark."""
import argparse, hashlib, json, shlex, subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
p.add_argument('--output',type=Path,required=True)
p.add_argument('--reference-build',type=Path,default=Path('/home/msys/SIMS/mechsys_v2_validation/20261016-v2-standalone/toolchain'))
p.add_argument('--source',type=Path,default=Path(__file__).with_name('probe.cu'))
p.add_argument('--observe',action='store_true')
p.add_argument('--backends',nargs='+',default=['cpu','cuda'])
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
flags=a.reference_build/'tdem/CMakeFiles/test_cu_04.dir'
defs=shlex.split(next(s.split('=',1)[1] for s in (flags/'flags.make').read_text().splitlines() if s.startswith('CUDA_DEFINES =')))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'root':str(a.root),'source':str(a.source),'source_sha256':sha(a.source),'observe_compiled':a.observe,'targets':{},
          'headers':{str(p.relative_to(a.root)):sha(p) for pattern in ['lib/flbm/*.h','lib/flbm/*.cuh','lib/lbmdem/*.h','lib/lbmdem/*.cuh','lib/dem/*.h','lib/dem/*.cuh'] for p in a.root.glob(pattern)}}
manifest['checkout_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.root,text=True).strip() if (a.root/'.git').exists() else 'immutable git archive; see reference_commit in TEST_MANIFEST.json'
for b in a.backends:
    obj=a.output/(b+'.o');exe=a.output/b
    compiler=['/usr/local/cuda-12.6/bin/nvcc','-arch=sm_86','-Xcompiler=-fopenmp','-DUSE_CUDA'] if b=='cuda' else ['g++','-fopenmp','-x','c++']
    inc=['--options-file',str(flags/'includes_CUDA.rsp')] if b=='cuda' else ['@'+str(flags/'includes_CUDA.rsp')]
    cmd=compiler+['-std=c++17','-O3',*defs,'-I'+str(a.root),*inc]+(['-DMECHSYS_EXCHANGE_AUDIT'] if a.observe else [])+['-c',str(a.source.resolve()),'-o',str(obj)]
    link=['g++','-fopenmp',str(obj),'-o',str(exe),'@'+str(flags/'linkLibs.rsp'),'-L/usr/local/cuda-12.6/targets/x86_64-linux/lib']
    with (a.output/(b+'.build.log')).open('w') as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
    manifest['targets'][b]={'compile':cmd,'link':link,'executable_sha256':sha(exe)}
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(b+': built',flush=True)
