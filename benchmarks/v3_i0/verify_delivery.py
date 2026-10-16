#!/usr/bin/env python3
"""Verify final clean origin-only delivery and write a non-self-referential external receipt."""
import argparse,hashlib,json,subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--clone',type=Path,required=True);p.add_argument('--expected',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Refusing to overwrite '+str(a.output))
def cmd(args,path=a.clone):return subprocess.check_output(args,cwd=path,text=True).strip()
branch='validation/v3-i0-exchange-audit'
assert cmd(['git','branch','--show-current'])==branch
assert cmd(['git','rev-parse','HEAD'])==a.expected
assert cmd(['git','rev-parse','--is-shallow-repository'])=='false'
assert not cmd(['git','status','--porcelain=v1','-uall'])
assert cmd(['git','remote','get-url','origin'])=='https://github.com/marcoprevitali/mechsys.git'
assert cmd(['git','remote','get-url','--push','origin'])=='https://github.com/marcoprevitali/mechsys.git'
assert cmd(['git','remote','get-url','upstream'])=='https://github.com/Axtal/mechsys.git'
assert cmd(['git','remote','get-url','--push','upstream'])=='PUSH_DISABLED'
remote=cmd(['git','ls-remote','origin','refs/heads/'+branch]).split()[0];assert remote==a.expected
subprocess.run(['git','diff','d801c80cce15691b2a886a31d7e0bd864de35c10','--exit-code','--','lib/dem','benchmarks/v2','benchmarks/v3_coupled_design','AGENTS.md'],cwd=a.clone,check=True)
preserved={}
for path,expected in [('/home/msys/git/mechsys-v2-restart','2b8d8c335709046e224f4c43aa930144ae6854e7'),('/home/msys/git/mechsys-v3-coupled-design','d801c80cce15691b2a886a31d7e0bd864de35c10')]:
    assert cmd(['git','rev-parse','HEAD'],path)==expected and not cmd(['git','status','--porcelain=v1','-uall'],path);preserved[path]=expected
original=subprocess.check_output(['git','diff','HEAD','--binary'],cwd='/home/msys/mechsys');original_sha=hashlib.sha256(original).hexdigest()
assert original_sha=='e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9'
archive=json.loads((a.output.parent/'ARCHIVE_VERIFICATION.json').read_text());assert archive['status']=='PASS'
receipt={'date':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'milestone':'V3-I0','overall':'PARITY BLOCKED','branch':branch,'commit':a.expected,'origin_sha':remote,'working_tree':'clean','clone':str(a.clone),'full_clone':True,'remotes':cmd(['git','remote','-v']),
 'gates':{'I0-A':'PARTIAL; shared equivalence blocked','I0-B':'PASS registered alpha=1','I0-C':'PASS diagnostic attribution','I0-D':'PASS fixed-pose exchange','I0-E':'FAIL parity; acceptance BLOCKED','I0-F':'PASS diagnosis; shared support BLOCKED','I0-G':'PASS with explicit synthetic limiter qualification','I0-H':'PARTIAL; 20 non-shared strict PASS, shared strict FAIL','I0-I':'PASS','I0-J':'PASS'},
 'archive_verification':archive,'original_diff_sha256':original_sha,'preserved_clean_clones':preserved,'protected_trees':'lib/dem, benchmarks/v2, benchmarks/v3_coupled_design, AGENTS.md unchanged from reference',
 'next':'Separate authorization for V3-I0-P1 conservative candidate/imprint coverage parity correction; no automatic Scheme A/P2-B'}
a.output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
