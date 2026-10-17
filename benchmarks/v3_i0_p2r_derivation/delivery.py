#!/usr/bin/env python3
"""New immutable D archive, full clone and exact origin/preservation receipt."""
import argparse, csv, hashlib, io, json, os, shutil, subprocess, tarfile
from pathlib import Path
from extract import ROOT, BASE, HERE, git, preservation, save, sha

BRANCH='analysis/v3-i0-p2r-targeted-derivation'
ORIGIN='https://github.com/marcoprevitali/mechsys.git'
UPSTREAM='https://github.com/Axtal/mechsys.git'

def main():
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--persistent',type=Path,required=True)
    p.add_argument('--raw-parent',type=Path,required=True);a=p.parse_args()
    head=git(ROOT,'rev-parse','HEAD').decode().strip()
    assert git(ROOT,'branch','--show-current').decode().strip()==BRANCH
    assert not git(ROOT,'status','--porcelain=v1','-uall').strip()
    assert git(ROOT,'remote','get-url','origin').decode().strip()==ORIGIN
    assert git(ROOT,'remote','get-url','--push','upstream').decode().strip()=='PUSH_DISABLED'
    remote=git(ROOT,'ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0];assert remote==head
    before=json.loads((HERE/'binary_evidence/EXTRACTION.json').read_text())['protected_checkouts_before']
    current=preservation();assert current==before,'A protected checkout changed'
    changed=git(ROOT,'diff','--name-only',BASE,head).decode().splitlines()
    assert all(n in ['PROJECT_STATE.md','PROJECT_STATUS.md'] or n.startswith('benchmarks/v3_i0_p2r_derivation/') for n in changed)
    a.archive.mkdir(parents=True,exist_ok=False)
    assert not a.persistent.exists()
    subprocess.run(['git','clone','--no-hardlinks','--branch',BRANCH,str(ROOT),str(a.persistent)],check=True)
    git(a.persistent,'remote','set-url','origin',ORIGIN);git(a.persistent,'remote','add','upstream',UPSTREAM)
    git(a.persistent,'remote','set-url','--push','upstream','PUSH_DISABLED')
    git(a.persistent,'config','--local','remote.pushDefault','origin');git(a.persistent,'config','--local','push.default','simple')
    assert not git(a.persistent,'status','--porcelain=v1','-uall').strip()
    assert git(a.persistent,'rev-parse','HEAD').decode().strip()==head
    for root in [ROOT,a.persistent]:
        assert (root/'.git').is_dir()
        assert git(root,'rev-parse','--is-shallow-repository').decode().strip()=='false'
        assert not (root/'.git/objects/info/alternates').exists()
    source=a.raw_parent/('SOURCE_'+head+'.tar');assert not source.exists()
    source.write_bytes(git(ROOT,'archive','--format=tar',head))
    rawfiles=[]
    for f in a.raw_parent.rglob('*'):
        if not f.is_file() or f.is_relative_to(ROOT):continue
        assert not f.is_symlink(),f
        rawfiles.append(f)
    index=a.raw_parent/'D_ARTIFACT_INDEX.csv';assert not index.exists()
    with index.open('w') as out:
        w=csv.writer(out);w.writerow(['path','size','sha256'])
        for f in sorted(rawfiles):w.writerow([str(f.relative_to(a.raw_parent)),f.stat().st_size,sha(f)])
    archive=a.archive/'P2R_DERIVATION_RAW.tgz'
    with tarfile.open(archive,'w:gz') as tf:
        for f in sorted(rawfiles)+[index]:tf.add(f,arcname=str(f.relative_to(a.raw_parent)),recursive=False)
    indexed={str(f.relative_to(a.raw_parent)):(f.stat().st_size,sha(f)) for f in rawfiles}
    with tarfile.open(archive,'r:gz') as tf:
        members=[m for m in tf.getmembers() if m.isfile()]
        assert len(members)==len(indexed)+1
        for m in members:
            payload=tf.extractfile(m).read()
            if m.name==index.name:assert hashlib.sha256(payload).hexdigest()==sha(index)
            else:assert (len(payload),hashlib.sha256(payload).hexdigest())==indexed[m.name]
    ar=dict(status='PASS archive verification',path=str(archive),sha256=sha(archive),payload_files=len(rawfiles),
      index_sha256=sha(index),source_commit=head,source_tar_sha256=sha(source))
    save(a.archive/'ARCHIVE_VERIFICATION.json',ar)
    assert preservation()==before
    for root in [ROOT,a.persistent]:assert not git(root,'status','--porcelain=v1','-uall').strip()
    result=dict(delivery_status='PASS',scientific_status='PARTIAL; D4 proof-closure stop; no full one/two-step certificate',
      milestone='V3-I0-P2R-D',base=BASE,branch=BRANCH,head=head,remote_sha=remote,
      preparation_full_clone=str(ROOT),persistent_full_clone=str(a.persistent),both_clean=True,
      origin=ORIGIN,upstream=UPSTREAM,upstream_push='PUSH_DISABLED',archive=ar,
      protected_checkouts=current,changed_files=changed,
      commits=git(ROOT,'log','--format=%H %s',BASE+'..'+head).decode().splitlines(),
      historical_P2R_K='FAIL unchanged',P2R_KN='NOT_APPROVED / NOT_IMPLEMENTED / NOT_RUN',new_solver_steps=0)
    save(a.archive/'DELIVERY.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
