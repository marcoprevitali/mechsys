#!/usr/bin/env python3
"""Verify immutable prior evidence before experiments; prepare exact binary copies."""
import argparse, csv, hashlib, io, json, shutil, subprocess, tarfile
from pathlib import Path

BASE = '26bf84aa2a3acb4edf9accc295a3cbcec7398770'
OLDRAW = Path('/tmp/mechsys-v3-i0-p2r.do4dZe/raw')
ARCHIVES = [
 ('mechsys_v3_i0_p2r_validation/20261016-robust-tangency-partial/P2R_RAW.tgz', 'cd31c91956d94a25d0014c01f03b888c65bb06e92107dc00428b6b319d070b38'),
 ('mechsys_v3_i0_p2_validation/20261016-edge-proxy-stopped/P2_RAW.tgz', '3c42c2032c8444d94cd4d8896d67e01f775263022d379c10e1292306276a796b'),
 ('mechsys_v3_i0_p1_validation/20261016-coverage/P1_RAW.tgz', '770a9639e551ed4a7142780cb50ec074265d82dae624f01d27ae7d22917dd2d2'),
 ('mechsys_v3_i0_validation/20261016-v3-i0-exchange-audit/V3_I0_RAW.tgz', '9a33398a9f88d1f0aa48acd6f2539784daf3b6d7b6940fc3913cb35345d19e2e'),
]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')

def verify_archive(path, expected_sha):
    assert sha(path)==expected_sha, path
    checked=set(); total=0
    # Older archives have a raw/ prefix and put the index last; read the
    # index independently before the streaming payload pass (no extraction).
    with tarfile.open(path,'r:gz') as t:
        matches=[m for m in t.getmembers() if m.name.endswith('ARTIFACT_INDEX.csv')]
        assert len(matches)==1
        index_name=matches[0].name;prefix=index_name[:-len('ARTIFACT_INDEX.csv')]
        data=t.extractfile(matches[0]).read()
    index_sha=hashlib.sha256(data).hexdigest()
    rows={r['path']:r for r in csv.DictReader(io.StringIO(data.decode()))}
    with tarfile.open(path,'r|gz') as t:
        for m in t:
            if m.isdir():continue
            assert m.isfile(), m.name
            assert m.name.startswith(prefix)
            name=m.name[len(prefix):]
            stream=t.extractfile(m)
            if name=='ARTIFACT_INDEX.csv':
                assert hashlib.sha256(stream.read()).hexdigest()==index_sha
                continue
            assert name in rows and name not in checked, name
            h=hashlib.sha256()
            for b in iter(lambda:stream.read(1024*1024),b''): h.update(b)
            r=rows[name]
            assert m.size==int(r['bytes']) and h.hexdigest()==r['sha256'], m.name
            total+=m.size; checked.add(name)
    assert checked==set(rows)
    previous=json.loads((path.parent/'ARCHIVE_VERIFICATION.json').read_text())
    assert index_sha==previous['index_sha256']
    return dict(path=str(path),sha256=expected_sha,index_sha256=index_sha,
                payload_files=len(checked),payload_bytes=total,status='PASS')

def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);a=p.parse_args()
    assert not a.raw.exists(), 'Refuse overwrite investigation namespace'
    a.raw.mkdir(parents=True)
    receipts=[]
    for relative,digest in ARCHIVES:
        receipt=verify_archive(Path('/home/msys/SIMS')/relative,digest)
        receipts.append(receipt);print(json.dumps(receipt),flush=True)
    # The live prior raw tree is the source of the execution copies. Check every
    # indexed payload too, so trusting a tar does not silently trust a changed tree.
    rows=list(csv.DictReader((OLDRAW/'ARTIFACT_INDEX.csv').open()))
    for r in rows:
        f=OLDRAW/r['path']; assert f.stat().st_size==int(r['bytes']) and sha(f)==r['sha256'], f
    assert sha(OLDRAW/'ARTIFACT_INDEX.csv')==receipts[0]['index_sha256']
    save(a.raw/'PRIOR_EVIDENCE_VERIFICATION.json',dict(archives=receipts,live_p2r_files=len(rows),status='PASS'))
    provenance=json.loads((Path(__file__).parent.parent/'v3_i0_p2r/PROVENANCE.json').read_text())
    fixture=dict(case='large',argv=['large','OUTPUT'],environment={
        'P1_MODE':'0','P2_MODE':'0','P2R_MODE':'0','P1_RADIUS':'2.2','MECHSYS_EXCHANGE_AUDIT':'1'},
        Nproc=1,steps=2,integrator='legacy coupled compatibility; NOT VV reference',
        lattice='D3Q15',Nl=1,cells=[10,10,10],dx=1,dt=1,Sc=0,nu=.1,tau=.8,
        periodic=[True,True,True],position=[5,5,5],R=2.2,density=100,
        velocity=[.002,-.001,.0005],quaternion=['sqrt(.5)','sqrt(.5)',0,0],omega=[0,0,0],
        Alpha=.4,Fconv=1,Kn=1,Kt=.2,Gn=0,Gt=0,Mu=.5,Beta=.1,Eta=.1,Gv=0,Gm=0,
        initial_fluid_rho=1,initial_fluid_velocity=[0,0,0],
        driver_sha256=provenance['builds']['reference-build']['source_sha256'])
    save(a.raw/'INPUT.json',fixture)
    builds={}
    for label,name,commit in [('baseline','reference-build','bf6616973be1335da1caa7d75f8a34aa0f6c1c22'),
                              ('candidate','coupled-build','1bde930295a9852e64a810e02e22b2bba21f98fc')]:
        meta=json.loads((OLDRAW/name/'manifest.json').read_text())
        exe=OLDRAW/name/'cuda'; digest=meta['targets']['cuda']['executable_sha256']
        assert sha(exe)==digest
        dest=a.raw/'binaries'/label;dest.parent.mkdir(exist_ok=True);shutil.copy2(exe,dest)
        assert sha(dest)==digest
        builds[label]=dict(source_commit=commit,executable=str(dest),sha256=digest,build=meta)
    save(a.raw/'EXECUTABLES.json',builds)
    print('ALL PRIOR PAYLOADS VERIFIED; exact executables copied; input '+sha(a.raw/'INPUT.json'),flush=True)

if __name__=='__main__':main()
