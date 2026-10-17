#!/usr/bin/env python3
"""Verify the PARTIAL proof package offline. This cannot approve P2R-KN.

No solver, compiler, debugger, GPU, production Python import, or network call.
It checks exact arithmetic/interval claims and honest conditional statuses.
"""
import argparse, copy, csv, hashlib, json, os, sys
from itertools import permutations
from fractions import Fraction as Q
from pathlib import Path
import arithmetic as A
from arithmetic import I, from_bits, rn
from derive import accumulation, translate, rotate, second_feedback, vdata, first_collision, compact_fluid, vec, collision, moments, stream
from extract import HERE, ROOT, BASE, sha, git, save

def read(p):return json.loads(Path(p).read_text())
def decode(x):
    if isinstance(x,dict):
        if 'binary64' in x:return from_bits(x['binary64'])
        return {k:decode(v) for k,v in x.items()}
    if isinstance(x,list):return [decode(v) for v in x]
    return x
def equal_values(expected,actual):
    assert expected==actual,'Exact regenerated certificate differs'

def independent_witnesses(p,graphs):
    # Exact hand-derived dyadic maps, separate from archived output values.
    z=[I(0)]*3
    synthetic={**p,'mass':Q(4),'x':[Q(2)]*3,'xb':[Q(3,2)]*3}
    t1,_=translate(synthetic,[I(Q(1,8))]*3,z,graphs['Translate'][0])
    assert all(v.point()==Q(81,32) for v in t1['x'])
    assert all(v.point()==Q(33,64) for v in t1['v'])
    t2,_=translate({**synthetic,**t1},[I(Q(-1,8))]*3,z,graphs['Translate'][0])
    assert all(v.point()==Q(97,32) for v in t2['x'])
    assert all(v.point()==Q(33,64) for v in t2['v'])
    qsynthetic={**p,'Q':[Q(1),Q(0),Q(0),Q(0)],'wb':[Q(1,8),Q(0),Q(0)]}
    r,_=rotate(qsynthetic,z,z,graphs['Rotate'][0])
    assert [v.point() for v in r['qD']]==[Q(1023,1024),Q(1,16),Q(0),Q(0)]
    assert r['norm'].point()==Q(1025,1024)
    assert [v.point() for v in r['Q']]==[rn(Q(1023,1025)),rn(Q(64,1025)),Q(0),Q(0)]
    # A non-exact divide and midpoint angular update, checked as rationals.
    tq=A.exact(.1);acc=A.op('div',I(tq),I(3));assert acc.point()==rn(tq/3)
    mid=A.fma(I(Q(1,2)),acc,I(Q(1,8)));assert mid.point()==rn(Q(1,8)+acc.point()/2)
    pop=[I(Q(1,2)),I(Q(1,4)),I(Q(1,8)),I(Q(1,8))]+[I(0)]*11
    rho,vel,mom=moments(pop)
    assert rho.point()==1 and [v.point() for v in mom]==[Q(1,8),Q(1,8),Q(0)]
    assert [v.point() for v in vel]==[Q(1,8),Q(1,8),Q(0)]
    from derive import W
    pp,tau,B,neq=collision([I(w) for w in W],I(1),z,I(Q(1,2)),[I(Q(1,64)),I(Q(-1,64))]+[I(0)]*13)
    assert all(v.point()==0 for v in neq)
    b=rn(rn(Q(1,2)*rn(A.exact(.8)-Q(1,2)))/rn(Q(1,2)+rn(A.exact(.8)-Q(1,2))))
    assert B.point()==b
    for k,om in [(0,Q(1,64)),(1,Q(-1,64))]:
        assert pp[k].contains(rn(W[k]+rn(b*om)))
        assert pp[k].contains(rn(W[k]+b*om))
    terms=list(map(A.exact,[.1,.2,-.3]));s=sum(terms);g=3*A.U/(1-3*A.U);e=g*sum(map(abs,terms))
    for order in permutations(terms):
        acc=Q(0)
        for v in order:acc=rn(acc+v)
        assert abs(acc-s)<=e
    return dict(translation_rounding=True,angular_rounding=True,ordered_quaternion_and_normalization=True,
      density_velocity=True,collision_formation=True,force_accumulation_six_orders=True,
      one_step=True,two_step=True)

def verify(root,manifest=True):
    A.selftest()
    one=read(root/'ONE_STEP_CERTIFICATE.json');two=read(root/'TWO_STEP_CERTIFICATE.json')
    frozen=read(root/'FROZEN_STATE_BITS.json');graphs=read(root/'ARITHMETIC_GRAPHS.json')
    assert one['status']=='PARTIAL' and two['status']=='PARTIAL; NO complete two-step certificate'
    assert 'CONDITIONAL' in one['rotation_status'] and 'CONDITIONAL' in one['collision_status']
    p=decode(frozen['initial_particles'])[0];claims=decode(frozen['first_claims'])
    witnesses=independent_witnesses(p,graphs)
    f,fr=accumulation(claims,'force');t,tr=accumulation(claims,'torque')
    assert one['accumulation']==fr+tr
    inertia=from_bits(frozen['principal_inertia']['binary64'][0])
    assert all(from_bits(b)==inertia for b in frozen['principal_inertia']['binary64'])
    assert rn(rn(rn(A.exact(.4)*p['mass'])*p['R'])*p['R'])==inertia
    assert inertia>0 and p['mass']>0
    tr1,_=translate(p,f,t,graphs['Translate'][0]);ro1,_=rotate(p,f,t,graphs['Rotate'][0])
    for k,v in tr1.items():equal_values(one['translation'][k],vdata(v))
    for k,v in ro1.items():equal_values(one['rotation'][k],v.data() if isinstance(v,I) else vdata(v))
    assert all(v.width()==0 for v in tr1['x']+tr1['v'])
    # A lower bound on the EXACT real pre-normalization norm, independent of
    # the rounded norm helper. Squared component extrema are rational.
    norm2min=sum(0 if v.lo<=0<=v.hi else min(v.lo*v.lo,v.hi*v.hi) for v in ro1['qD'])
    assert norm2min>Q(99,100)**2
    assert sum(x*x for x in p['Q'])!=1 # retain the actual nonunit input
    inp=decode(read(root/'FEEDBACK_INPUT_BITS.json'))
    grid0=[None]*1000
    for group in frozen['initial_grid_groups']:
        payload=decode(group['state'])
        for ic in group['cells']:grid0[int(ic)]={'cell':ic,**payload}
    assert all(c is not None for c in grid0)
    A.CONTRACT=True
    po,st,ma,ta,_=first_collision({'grid':grid0},claims)
    fc=one['first_collision'];expected=compact_fluid(po,st,ma)
    assert all(fc[k]==v for k,v in expected.items()) and fc['effective_tau']==ta[0].data()
    p1={**p,**tr1,**{k:v for k,v in ro1.items() if k not in ['qD','norm']}}
    imp=read(root/'IMPRINT_GRAPH_SUFFIX.json')['text']
    feedback,formed,termrows,ledger=second_feedback(p1,inp['grid1'],inp['second_occupancy'],imp)
    assert ledger==two['feedback_ledger'] and termrows==two['second_contributions']
    bycell={c['cell']:c for c in formed};po2=[];tau2=[]
    for ic,cell in enumerate(inp['grid1']):
        cl=bycell.get(ic)
        pp,tt,_,_=collision(vec(cell['f']),I(cell['rho']),vec(cell['vel']),cl['gamma'] if cl else I(0),cl['omega'] if cl else [I(0)]*15)
        po2.append(pp);tau2.append(tt)
    st2=stream(po2);ma2=[moments(pp) for pp in st2]
    expected=compact_fluid(po2,st2,ma2)
    assert all(two['second_collision'][k]==v for k,v in expected.items())
    tr2,_=translate(p1,feedback['force'],feedback['torque'],graphs['Translate'][0]);ro2,_=rotate(p1,feedback['force'],feedback['torque'],graphs['Rotate'][0])
    for k,v in tr2.items():equal_values(two['translation'][k],vdata(v))
    for k,v in ro2.items():equal_values(two['rotation'][k],v.data() if isinstance(v,I) else vdata(v))
    branches=list(csv.DictReader((root/'BRANCH_PREDICATE_CERTIFICATE.csv').open()))
    unresolved=[]
    for row in branches:
        lo=Q(row['lo']);hi=Q(row['hi']);assert lo<=hi
        signed=lo>0 or hi<0
        assert row['strict_sign_status']==('PASS' if signed else 'UNRESOLVED')
        status='PASS' if signed and row['basis'] in ['CERTIFIED','SOURCE_AND_FROZEN_INPUT'] else 'UNRESOLVED'
        assert row['status']==status
        if not signed:unresolved.append(row)
    assert len(unresolved)==292
    assert all(r['step']=='0' and r['predicate'].startswith('corner-') and Q(r['lo'])==Q(r['hi'])==0 for r in unresolved)
    # Three counterfactual in-memory corruptions must be rejected. No frozen
    # fixture, production test or file is changed by these proof-unit witnesses.
    faults=0
    for mutate in ['translation','reduction','promotion']:
        bad=copy.deepcopy(one)
        if mutate=='translation':bad['translation']['x'][0]['lo']='5'
        elif mutate=='reduction':bad['accumulation'][0]['error']='0'
        else:bad['status']='PASS'
        try:
            assert bad['translation']['x']==vdata(tr1['x'])
            assert bad['accumulation']==fr+tr
            assert bad['status']=='PARTIAL'
        except AssertionError:faults+=1
    assert faults==3
    summary=read(root/'DERIVATION_SUMMARY.json')
    assert summary['recommended_outcome']=='D4' and summary['production_unchanged']
    assert summary['strict_sign_unresolved_branch_rows']==292 and summary['branch_rows']==len(branches)
    assert summary['unresolved_branch_rows']==sum(r['status']=='UNRESOLVED' for r in branches)
    assert summary['conditional_branch_rows']==sum(r['basis'] not in ['CERTIFIED','SOURCE_AND_FROZEN_INPUT'] for r in branches)
    # Every historical tracked source/test/artifact is byte-identical to base.
    for name in git(ROOT,'ls-tree','-r','--name-only','-z',BASE).split(b'\0'):
        if not name:continue
        name=name.decode()
        if name in ['PROJECT_STATUS.md','PROJECT_STATE.md']:continue
        fpath=ROOT/name
        data=os.readlink(fpath).encode() if fpath.is_symlink() else fpath.read_bytes()
        assert data==git(ROOT,'show',BASE+':'+name),name
    for path,digest in summary['source_sha256'].items():assert sha(ROOT/path)==digest
    if manifest:
        for path,digest in read(root/'ARTIFACT_MANIFEST.json')['sha256'].items():assert sha(root/path)==digest,path
    return dict(status='PASS verification of PARTIAL artifacts only',milestone='V3-I0-P2R-D',
      historical_P2R_K='FAIL unchanged',prospective_P2R_KN='NOT_APPROVED / NOT_IMPLEMENTED / NOT_RUN',
      exact_RN_witnesses=True,translation_replay=True,conditional_rotation_replay=True,
      independent_arithmetic_witnesses=witnesses,
      conditional_two_step_particle_feedback_replay=True,first_qD_real_norm_floor='>99/100',
      conditional_collision_streaming_moment_replay=True,
      branch_rows=len(branches),strict_sign_unresolved=292,corruption_witnesses_rejected=faults,
      prior_source_tests_artifacts_byte_identical=True,full_two_step_certificate=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=HERE);p.add_argument('--without-manifest',action='store_true');p.add_argument('--receipt',type=Path)
    a=p.parse_args();result=verify(a.root,not a.without_manifest)
    if a.receipt:
        assert not a.receipt.exists(),'Use a new receipt path';save(a.receipt,result)
    print(json.dumps(result,indent=2))
