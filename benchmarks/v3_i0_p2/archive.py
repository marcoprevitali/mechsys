#!/usr/bin/env python3
"""New immutable raw archive and streaming payload verification; refuses overwrite."""
import argparse,csv,hashlib,io,json,tarfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
if a.destination.exists():raise RuntimeError('Refuse overwrite archive namespace '+str(a.destination))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
index=a.raw/'ARTIFACT_INDEX.csv'
if index.exists():raise RuntimeError('Refuse replace existing index')
paths=sorted(p for p in a.raw.rglob('*') if p.is_file())
with index.open('w') as h:
    w=csv.writer(h,lineterminator='\n');w.writerow(['path','bytes','sha256'])
    for f in paths:w.writerow([str(f.relative_to(a.raw)),f.stat().st_size,sha(f)])
expected={r['path']:r for r in csv.DictReader(index.open())}
a.destination.mkdir(parents=True);archive=a.destination/'P2_RAW.tgz'
with tarfile.open(archive,'w:gz',compresslevel=1) as t:
    for f in [index,*paths]:t.add(f,arcname=str(f.relative_to(a.raw)),recursive=False)
checked=set();total=0
with tarfile.open(archive,'r|gz') as t:
    for m in t:
        if m.name=='ARTIFACT_INDEX.csv':
            assert hashlib.sha256(t.extractfile(m).read()).hexdigest()==sha(index);continue
        assert m.isfile() and m.name in expected and m.name not in checked
        row=expected[m.name];h=hashlib.sha256();f=t.extractfile(m)
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        assert int(row['bytes'])==m.size and row['sha256']==h.hexdigest(),m.name
        checked.add(m.name);total+=m.size
assert checked==set(expected)
receipt={'status':'PASS','archive':str(archive),'archive_sha256':sha(archive),'payload_files':len(checked),'payload_bytes':total,'index_sha256':sha(index),'verification':'every tar member streamed and checked against SHA256/size, no extraction or prior archive overwrite'}
(a.destination/'ARCHIVE_VERIFICATION.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
