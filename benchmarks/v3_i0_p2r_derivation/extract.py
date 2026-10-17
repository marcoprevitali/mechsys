#!/usr/bin/env python3
"""Read frozen evidence; extract static binary evidence, never run a solver."""
import argparse, hashlib, json, os, re, struct, subprocess
from pathlib import Path

BASE = '031e5e307a1d3a5001537c58cb791bf31edc6ae5'
DEFAULT_RAW = '/tmp/mechsys-v3-i0-p2r-repro.iXq6mh/raw-verified'
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p, x): Path(p).write_text(json.dumps(x, indent=2, sort_keys=True)+'\n')
def git(p, *a): return subprocess.check_output(['git', '-C', str(p), *a])
def preservation():
    old=json.loads((ROOT/'benchmarks/v3_i0_p2r_contract/SOURCE_AND_EVIDENCE.json').read_text())['protected_checkouts_before']
    paths=list(old)+['/home/msys/git/mechsys-v3-i0-p2r-compatibility-design']
    result={}
    for p in paths:
        names=git(p,'ls-files','-z').split(b'\0')+git(p,'ls-files','--others','--exclude-standard','-z').split(b'\0')
        h=hashlib.sha256()
        for n in sorted(set(names)-{b''}):
            f=Path(p)/n.decode();h.update(n+b'\0'+(sha(f).encode() if f.is_file() else b'MISSING'))
        result[p]=dict(head=git(p,'rev-parse','HEAD').decode().strip(),branch=git(p,'branch','--show-current').decode().strip(),
          status=git(p,'status','--porcelain=v1','-uall').decode(),remotes=git(p,'remote','-v').decode(),
          tracked_diff_sha256=hashlib.sha256(git(p,'diff','HEAD','--binary')).hexdigest(),
          all_tracked_and_untracked_content_sha256=h.hexdigest())
    return result

def bits(v):return struct.pack('>d',float(v)).hex()
def bit_tree(x):
    if isinstance(x,list):return [bit_tree(v) for v in x]
    if isinstance(x,dict):return {k:bit_tree(v) for k,v in x.items()}
    try:return {'binary64':bits(x),'decimal':str(x)}
    except (TypeError,ValueError):return x

def extract(raw, out):
    out.mkdir(parents=True,exist_ok=True)
    frozen=raw/'repeats/baseline-00'
    builds=json.loads((raw/'EXECUTABLES.json').read_text())
    hashes={}
    for label in ['baseline','candidate']:
        binary=raw/'binaries'/label
        assert sha(binary)==builds[label]['sha256']
        hashes[str(binary)]=sha(binary)
        # Exact embedded PTX, and host instructions used to recover inertia.
        ptx=subprocess.check_output(['/usr/local/cuda-12.6/bin/cuobjdump','--dump-ptx',str(binary)],text=True)
        (out/(label+'.ptx')).write_text(ptx)
        host=subprocess.check_output(['objdump','-d','-C','--no-show-raw-insn',str(binary)],text=True)
        start=host.index('<DEM::Domain::AddSphere(')
        # Find the actual function definition rather than a call site.
        m=re.search(r'^([0-9a-f]+) <DEM::Domain::AddSphere\(.*?>:\n',host,re.M)
        assert m
        end=re.search(r'^\n[0-9a-f]+ <',host[m.end():],re.M)
        block=host[m.start():m.end()+end.start()]
        (out/(label+'-AddSphere.asm')).write_text(block+'\n')
        selected={}
        for key in ['Translate','Rotate','cudaStream1','cudaStream2','cudaCollideSCDEM','cudaImprintLatticeVC','BnSmooth']:
            # Include complete entry/function definitions, not prototypes.
            matches=[]
            for mm in re.finditer(r'(?m)^(?:\.visible )?\.(?:entry|func)[^\n]*(?:'+key+r')[^\n]*\n',ptx):
                brace=ptx.find('{',mm.end()); semi=ptx.find(';',mm.end())
                if semi>=0 and semi<brace:continue
                level=1;i=brace+1
                while level:
                    level+=(ptx[i]=='{')-(ptx[i]=='}');i+=1
                matches.append(ptx[mm.start():i])
            selected[key]=matches
        save(out/(label+'-selected-ptx.json'),selected)
        hashes[str(out/(label+'.ptx'))]=sha(out/(label+'.ptx'))
    for p in [raw/'INPUT.json',raw/'EXECUTABLES.json',frozen/'state-0.json',frozen/'fixture.json',
              frozen/'step-0-before_imprint.json',frozen/'step-0-after_imprint.json']:
        hashes[str(p)]=sha(p)
    initial=json.loads((frozen/'state-0.json').read_text())
    before=json.loads((frozen/'step-0-before_imprint.json').read_text())
    claims=json.loads((frozen/'step-0-after_imprint.json').read_text())['claims']
    # Uniform initial grid except gamma/scratch: retain groups losslessly.
    groups={}
    for cell in initial['grid']:
        payload={k:v for k,v in cell.items() if k!='cell'}
        key=json.dumps(payload,sort_keys=True)
        groups.setdefault(key,[]).append(cell['cell'])
    grid=[{'cells':ids,'state':bit_tree(json.loads(k))} for k,ids in groups.items()]
    save(out/'INPUT_BITS.json',dict(initial_particles=bit_tree(initial['particles']),
      initial_grid_groups=grid,initial_other=bit_tree({k:v for k,v in initial.items() if k not in ['particles','grid']}),
      before_imprint=bit_tree(before),first_claims=bit_tree(claims),
      registered_input=json.loads((raw/'INPUT.json').read_text()),fixture=bit_tree(json.loads((frozen/'fixture.json').read_text())),
      source_hashes=hashes))
    save(out/'EXTRACTION.json',dict(base=BASE,solver_executions=0,raw=str(raw),sha256=hashes,
      protected_checkouts_before=preservation()))
    print('Extracted exact frozen data and embedded PTX; no executable was run.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=Path(DEFAULT_RAW));p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();extract(a.raw,a.out)
