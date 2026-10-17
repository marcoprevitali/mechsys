#!/usr/bin/env python3
"""Summarize provenance, preservation and bounded audit outcomes."""
import argparse,csv,hashlib,json,shutil,subprocess
from collections import Counter,defaultdict
from pathlib import Path
from prepare import sha,save,BASE,OLDRAW
from analyze import load,flat,compare,canonical,writecsv

CLONES=['/home/msys/mechsys','/home/msys/git/mechsys-v3-i0-p2r-robust-tangency',
 '/home/msys/git/mechsys-v3-i0-p2-edge-proxy','/home/msys/git/mechsys-v3-i0-p1-cell-coverage',
 '/home/msys/git/mechsys-v3-i0-exchange-audit','/home/msys/git/mechsys-v3-coupled-design','/home/msys/git/mechsys-v2-restart']
def git(root,*argv):return subprocess.check_output(['git','-C',str(root),*argv])
def preservation():
    result={}
    for root in CLONES:
        p=Path(root);paths=git(root,'ls-files','-z').split(b'\0')+git(root,'ls-files','--others','--exclude-standard','-z').split(b'\0')
        digest=hashlib.sha256()
        for name in sorted(set(paths)-{b''}):
            f=p/name.decode();digest.update(name+b'\0'+(sha(f).encode() if f.is_file() else b'MISSING'))
        result[root]=dict(head=git(root,'rev-parse','HEAD').decode().strip(),branch=git(root,'branch','--show-current').decode().strip(),
            status=git(root,'status','--porcelain=v1','-uall').decode(),
            tracked_diff_sha256=hashlib.sha256(git(root,'diff','HEAD','--binary')).hexdigest(),
            all_tracked_and_untracked_content_sha256=digest.hexdigest(),remotes=git(root,'remote','-v').decode())
    assert result[CLONES[0]]['tracked_diff_sha256']=='e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9'
    assert result[CLONES[1]]['head']==BASE
    assert all(not result[c]['status'] for c in CLONES[1:])
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('analysis',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    builds=load(a.raw/'EXECUTABLES.json');source=Path(__file__).resolve().parents[2]
    for build in builds.values():
        for name,digest in build['build']['headers'].items():
            actual=hashlib.sha256(git(source,'show',build['source_commit']+':'+name)).hexdigest()
            assert actual==digest, (name,build['source_commit'])
    # Preserve original failure classification separately from new distributions.
    original=OLDRAW/'p1-regression/runs-cuda/cuda/large';rows=[]
    for name in ['state-0.json','state-1.json','state-2.json']:
        x=load(original/'reference'/name);y=load(original/'off'/name)
        rows.append(dict(snapshot=name,reference_file_sha256=sha(original/'reference'/name),
          candidate_file_sha256=sha(original/'off'/name),**compare(flat(x),flat(y)),
          history_equal=canonical(x['histories'])==canonical(y['histories']),
          gpu_history_equal=canonical(x['gpu_vv'])==canonical(y['gpu_vv']),
          pairs_equal=canonical(x['pairs'])==canonical(y['pairs'])))
    writecsv(a.output/'ORIGINAL_FAILURE.csv',rows)
    assert any(r['differing_binary64_fields'] for r in rows)
    runs=load(a.raw/'repeats/RUNS.json');tests=load(a.raw/'sanitizers/RUNS.json')
    assert len(runs)==20 and len(tests)==8 and all(r['returncode']==0 for r in runs+tests)
    original_fixture_hash=sha(original/'reference/fixture.json')
    assert sha(original/'off/fixture.json')==original_fixture_hash
    assert all(r['files']['fixture.json']==original_fixture_hash for r in runs+tests)
    manifest=dict(milestone='V3-I0-P2R-R',source_base=BASE,branch='validation/v3-i0-p2r-reproducibility',
      raw=str(a.raw),analysis=str(a.analysis),input_sha256=sha(a.raw/'INPUT.json'),input=load(a.raw/'INPUT.json'),
      original_fixture_file_sha256=original_fixture_hash,
      builds=builds,prior_evidence_verification=load(a.raw/'PRIOR_EVIDENCE_VERIFICATION.json'),
      execution_configuration=load(a.raw/'repeats/CONFIG.json'),
      user_exception='2026-10-17 explicit permission: Allow desktop services; no other simulations',
      runs=[{k:v for k,v in r.items() if k not in ['before','after']}|{
             'inventory_before':{k:v for k,v in r['before'].items() if k!='ps'},
             'inventory_after':{k:v for k,v in r['after'].items() if k!='ps'}} for r in runs],
      sanitizer_runs=[dict(label=r['label'],tool=r['tool'],argv=r['argv'],returncode=r['returncode'],
          log_sha256=r['files']['run.log'],binary_sha256=r['binary_sha256']) for r in tests],
      source_header_provenance='all archived header SHA256 values verified against named immutable commits',
      production_unchanged=not git(source,'diff',BASE,'--','lib').strip(),
      original_gate='P2R-K FAIL preserved; historical P2 FAIL preserved')
    assert manifest['production_unchanged']
    save(a.output/'REPRODUCTION_MANIFEST.json',manifest)
    for f in a.analysis.iterdir():
        if f.is_file():
            src=(a.analysis/'BALANCE_AND_WORK_PHASE_ALIGNED.csv') if f.name=='BALANCE_AND_WORK.csv' else f
            shutil.copy2(src,a.output/f.name)
    save(a.raw/'PRESERVATION_BEFORE_DELIVERY.json',preservation())
    # Group summaries retain all pairs, including equal pairs, rather than
    # discarding exact matches or selecting a favorable cross-executable pair.
    pairrows=list(csv.DictReader((a.analysis/'ALL_PAIRWISE_SNAPSHOTS.csv').open()))
    groups=[]
    for group in ['baseline-baseline','candidate-candidate','baseline-candidate']:
      for name in sorted({r['snapshot'] for r in pairrows}):
        rr=[r for r in pairrows if r['group']==group and r['snapshot']==name]
        groups.append(dict(group=group,snapshot=name,pairs=len(rr),
             different_pairs=sum(int(r['differing_binary64_fields'])>0 or r['structural_equal']!='True' for r in rr),
             max_abs=max(float(r['max_abs']) for r in rr),max_ulp=max(int(r['max_ulp']) for r in rr),
             maximum_differing_binary64_fields=max(int(r['differing_binary64_fields']) for r in rr)))
    writecsv(a.output/'PAIRWISE_SUMMARY.csv',groups)
    print('manifest, original failure, all-pairs summary and preservation verified')

if __name__=='__main__':main()
