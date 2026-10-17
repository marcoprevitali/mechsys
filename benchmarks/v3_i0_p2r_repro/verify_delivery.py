#!/usr/bin/env python3
"""Read-only Git/preservation verification; write external delivery receipt."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
from prepare import BASE,save,sha
from evidence import git,preservation

def main():
    p=argparse.ArgumentParser();p.add_argument('work',type=Path);p.add_argument('raw',type=Path);p.add_argument('archive',type=Path);p.add_argument('persistent',type=Path);a=p.parse_args()
    head=git(a.work,'rev-parse','HEAD').decode().strip()
    branch='validation/v3-i0-p2r-reproducibility'
    assert not git(a.work,'status','--porcelain=v1','-uall').strip()
    assert git(a.work,'branch','--show-current').decode().strip()==branch
    changed=git(a.work,'diff','--name-only',BASE,head).decode().splitlines()
    assert all(n in ['PROJECT_STATUS.md','PROJECT_STATE.md'] or n.startswith('benchmarks/v3_i0_p2r_repro/') for n in changed)
    # Content against BASE, not just status: all tracked prior source/artifacts
    # other than the two current handoff records must remain byte-identical.
    for rawpath in git(a.work,'ls-tree','-r','--name-only','-z',BASE).split(b'\0'):
        if not rawpath:continue
        name=rawpath.decode()
        if name in ['PROJECT_STATUS.md','PROJECT_STATE.md']:continue
        path=a.work/name
        content=os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
        assert content==git(a.work,'show',BASE+':'+name),name
    assert not (a.work/'.git').is_file(), 'Require full clone, not worktree'
    assert not (a.persistent/'.git').is_file()
    assert git(a.persistent,'rev-parse','HEAD').decode().strip()==head
    assert not git(a.persistent,'status','--porcelain=v1','-uall').strip()
    remote=git(a.work,'ls-remote','origin','refs/heads/'+branch).decode().split()[0]
    assert remote==head
    for clone in [a.work,a.persistent]:
        assert git(clone,'remote','get-url','origin').decode().strip()=='https://github.com/marcoprevitali/mechsys.git'
        assert git(clone,'remote','get-url','upstream').decode().strip()=='https://github.com/Axtal/mechsys.git'
        assert git(clone,'remote','get-url','--push','upstream').decode().strip()=='PUSH_DISABLED'
        assert git(clone,'rev-parse','--is-shallow-repository').decode().strip()=='false'
        assert not (clone/'.git/objects/info/alternates').exists()
    previous=json.loads((a.raw/'PRESERVATION_BEFORE_DELIVERY.json').read_text());current=preservation()
    assert previous==current,'A protected checkout changed; investigate, do not overwrite'
    archive=json.loads((a.archive/'ARCHIVE_VERIFICATION.json').read_text());assert archive['status']=='PASS'
    assert sha(Path(archive['path']))==archive['sha256']
    result=dict(status='PASS',milestone='V3-I0-P2R-R',branch=branch,base=BASE,head=head,remote_sha=remote,
       preparation_full_clone=str(a.work),persistent_full_clone=str(a.persistent),both_clean=True,
       origin='https://github.com/marcoprevitali/mechsys.git',upstream='https://github.com/Axtal/mechsys.git',upstream_push='PUSH_DISABLED',
       changed_files=changed,prior_source_and_artifacts_byte_identical=True,protected_checkouts=current,
       commits=git(a.work,'log','--format=%H %s',BASE+'..'+head).decode().splitlines(),
       raw_archive=archive,original_gate='P2R-K FAIL unchanged',
       scientific_status='observational PASS within tested scope, NOT P2R acceptance')
    assert not (a.archive/'DELIVERY.json').exists()
    save(a.archive/'DELIVERY.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
