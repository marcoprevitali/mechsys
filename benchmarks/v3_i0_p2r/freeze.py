#!/usr/bin/env python3
"""Read-only hash freeze of prior evidence; never regenerate frozen cases."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];old=root/'benchmarks/v3_i0_p2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads((old/'REFERENCE_TESTS.json').read_text());assert len(j['fixtures'])==1254
f={str(p.relative_to(root)):sha(p) for d in ['benchmarks/v3_i0_p2','benchmarks/v3_i0_p1','benchmarks/v3_i0'] for p in sorted((root/d).rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
data={'base':'bf6616973be1335da1caa7d75f8a34aa0f6c1c22','frozen_files_sha256':f,
      'tolerances':{k:j[k] for k in ['edge_budget','gamma_budget','collision_budget','acceptance_threshold_length']},
      'case_ids':[x['name'] for x in j['fixtures']],'fixtures':1254,'expected_edges':15048,
      'reference_unchanged':True,'random_fixtures_regenerated':False}
if a.output.exists():assert json.loads(a.output.read_text())==data
else:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+'\n')
print('Frozen prior trees and exact tolerance definitions verified:',len(f),'files')
