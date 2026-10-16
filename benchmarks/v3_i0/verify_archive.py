#!/usr/bin/env python3
"""Read-only streaming verification of every inventoried archive payload, no extraction."""
import argparse,csv,hashlib,io,json,tarfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--index',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise RuntimeError('Refusing to overwrite '+str(a.output))
def sha(stream):
    h=hashlib.sha256()
    while block:=stream.read(1024*1024):h.update(block)
    return h.hexdigest()
with a.index.open() as f:expected={r['path']:r for r in csv.DictReader(f)}
seen=set();total=0;index_seen=False
with tarfile.open(a.archive,'r|gz') as archive:
    for member in archive:
        if not member.isfile():continue
        name=member.name.removeprefix('raw/');stream=archive.extractfile(member)
        if name=='ARTIFACT_INDEX.csv':
            assert sha(stream)==hashlib.sha256(a.index.read_bytes()).hexdigest();index_seen=True;continue
        assert name in expected and name not in seen,name
        assert member.size==int(expected[name]['bytes']),name
        assert sha(stream)==expected[name]['sha256'],name
        seen.add(name);total+=member.size
assert seen==set(expected) and index_seen
with a.archive.open('rb') as f:archive_sha=sha(f)
result={'status':'PASS','payload_files':len(seen),'payload_bytes':total,'archive_sha256':archive_sha,'index_sha256':hashlib.sha256(a.index.read_bytes()).hexdigest(),'method':'stream every tar member, exact size and SHA256; no extraction'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
