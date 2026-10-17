#!/usr/bin/env python3
"""Create a new immutable raw namespace and verify every streamed member."""
import argparse,csv,hashlib,json,tarfile
from pathlib import Path
from prepare import sha,save,verify_archive

def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    assert not a.destination.exists(), 'Refuse overwrite archive namespace'
    index=a.raw/'ARTIFACT_INDEX.csv';assert not index.exists()
    files=sorted(f for f in a.raw.rglob('*') if f.is_file());assert not any(f.is_symlink() for f in files)
    with index.open('w') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['path','bytes','sha256'])
        for path in files:w.writerow([str(path.relative_to(a.raw)),path.stat().st_size,sha(path)])
    a.destination.mkdir(parents=True);archive=a.destination/'P2R_REPRO_RAW.tgz'
    with tarfile.open(archive,'w:gz',compresslevel=1) as t:
        for f in [index,*files]:t.add(f,arcname=str(f.relative_to(a.raw)),recursive=False)
    # verify_archive also checks the index against a prior receipt; write the
    # expectation first, and publish the PASS receipt only after full checking.
    expected=dict(status='VERIFICATION_PENDING',archive_sha256=sha(archive),index_sha256=sha(index))
    save(a.destination/'ARCHIVE_VERIFICATION.json',expected)
    receipt=verify_archive(archive,expected['archive_sha256']);save(a.destination/'ARCHIVE_VERIFICATION.json',receipt)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
