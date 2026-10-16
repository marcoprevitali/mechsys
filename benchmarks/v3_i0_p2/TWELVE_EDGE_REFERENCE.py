#!/usr/bin/env python3
"""Independent Decimal segment/sphere quadratic, twelve edges, never solver code.

All inputs are exact binary64 values promoted to 70 decimal digits. Edge order:
upper 0..3, lower 4..7, vertical 8..11. This is NOT a volume fraction.
"""
import argparse, csv, itertools, json, math, random
from decimal import Decimal as D, getcontext
from pathlib import Path
getcontext().prec=70
ZERO=D(0)
def dec(x): return x if isinstance(x,D) else D.from_float(float(x))
def dot(a,b): return sum((x*y for x,y in zip(a,b)),ZERO)
def segment(A,B,X,R):
    d=[b-a for a,b in zip(A,B)];q=[a-x for a,x in zip(A,X)]
    a=dot(d,d)
    if not a: return ZERO # a point has zero covered length
    b=2*dot(q,d);c=dot(q,q)-R*R;disc=b*b-4*a*c
    if disc<=0: return ZERO # tangency has zero length
    s=disc.sqrt();lo=max(ZERO,(-b-s)/(2*a));hi=min(D(1),(-b+s)/(2*a))
    return max(ZERO,hi-lo)*a.sqrt()
def edges(X,C,R,dx):
    X=list(map(dec,X));C=list(map(dec,C));R=dec(R);dx=dec(dx)
    if dx<=0 or R<0: raise ValueError('positive dx and nonnegative R required')
    signs=[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1)]
    p=[[c+dx*s/2 for c,s in zip(C,v)] for v in signs]
    pairs=[(j,(j+1)%4) for j in range(4)]+[(j+4,(j+1)%4+4) for j in range(4)]+[(j,j+4) for j in range(4)]
    return [segment(p[a],p[b],X,R) for a,b in pairs]
def gamma(f): return sum(edges(f['X'],f['C'],f['R'],f['dx']),ZERO)/(12*dec(f['dx']))
def dump(p,x): p.write_text(json.dumps(x,indent=2,default=str)+'\n')
def register(out,oldraw,failures):
    out.mkdir(parents=True,exist_ok=True);fixtures=[];repro=[]
    for n,f in enumerate(json.loads(failures.read_text())):
        path=oldraw/('runs-'+f['backend'])/f['backend']/f['case']/'enabled'/('step-%s-before_imprint.json'%f['step'])
        p=json.loads(path.read_text())['particles'][f['particle']];ic=f['cell']
        q={'name':'original_%02d'%n,'X':p['x'],'C':[ic%10,ic//10%10,ic//100],'R':p['R'],'dx':1}
        ee=edges(q['X'],q['C'],q['R'],1);g=sum(ee,ZERO)/12
        assert abs(g-D(f['mathematical_edge_proxy']))<D('1e-60')
        assert abs(g-dec(f['observed_gamma']))>D('1e-10')
        fixtures.append(q);repro.append({**f,**q,'reference_edges':list(map(str,ee)),
          'upper':str(sum(ee[:4])),'lower':str(sum(ee[4:8])),'vertical':str(sum(ee[8:])),
          'legacy_length':str(12*dec(f['observed_gamma'])),'reference_length':str(sum(ee)),
          'source_snapshot':str(path)})
    base=[('centered',[0,0,0],1.2),('corner',[.5,.5,.5],.6),('edge_mid',[0,.5,.5],.3),
      ('face_mid',[0,0,.5],.6),('sphere_inside',[0,0,0],.1),('cube_inside',[0,0,0],2),
      ('outside',[3,0,0],.2),('top_only',[0,-.5,.65],.2),('bottom_only',[0,-.5,-.65],.2),
      ('vertical_only',[.65,.5,0],.2),('multiple',[.3,.2,.1],1),('tangent',[0,-.75,.5],.25),
      ('partial',[.45,.2,.1],1.2),('boundary',[.49,0,0],1.2),('small',[.5,.5,0],.05),('large',[0,0,0],2.2)]
    for name,x,r in base: fixtures.append({'name':name,'X':x,'C':[0,0,0],'R':r,'dx':1})
    # All 48 signed axis permutations, including improper cube reflections.
    for idx,(perm,sgn) in enumerate(itertools.product(itertools.permutations(range(3)),itertools.product([-1,1],repeat=3))):
        for name,x,r in base:
            fixtures.append({'name':f'sym_{idx}_{name}','X':[sgn[k]*x[perm[k]] for k in range(3)],'C':[0,0,0],'R':r,'dx':1,'same_as':name})
    for axis in range(3):
        f={'name':f'translate_{axis}','X':[.25,.125,.375],'C':[0,0,0],'R':1.2,'dx':1}
        fixtures.append(f)
        for v in [1.,-8.,32.]:
            q={**f,'name':f'translate_{axis}_{v}','same_as':f['name'],'X':f['X'].copy(),'C':f['C'].copy()}
            q['X'][axis]+=v;q['C'][axis]+=v;fixtures.append(q)
    for n in range(101): fixtures.append({'name':f'continuity_{n}','X':[.5+(n-50)*1e-7,.25,.5],'C':[0,0,0],'R':.25,'dx':1})
    for n in range(41): fixtures.append({'name':f'radius_{n}','X':[.375,.125,.25],'C':[0,0,0],'R':n*.05,'dx':1})
    rng=random.Random(20261016)
    for n in range(300):
        dx=rng.choice([.25,1.,4.]);c=[rng.uniform(-10,10) for _ in range(3)]
        fixtures.append({'name':f'random_{n}','X':[v+dx*rng.uniform(-2,2) for v in c],'C':c,'R':dx*rng.uniform(.01,3),'dx':dx})
    expected={f['name']:gamma(f) for f in fixtures};checks=0
    for f in fixtures:
        e=edges(f['X'],f['C'],f['R'],f['dx']);assert all(0<=a<=dec(f['dx']) for a in e);assert 0<=expected[f['name']]<=1;checks+=13
        if 'same_as' in f: assert abs(expected[f['name']]-expected[f['same_as']])<D('1e-10');checks+=1
    assert expected['cube_inside']==1 and expected['sphere_inside']==0 and expected['outside']==0 and expected['tangent']==0
    rr=[expected[f'radius_{n}'] for n in range(41)];assert all(b>=a for a,b in zip(rr,rr[1:]))
    cc=[expected[f'continuity_{n}'] for n in range(101)];assert max(abs(b-a) for a,b in zip(cc,cc[1:]))<D('1e-4')
    assert segment([ZERO]*3,[ZERO]*3,[ZERO]*3,D(1))==0
    # Segment limits, endpoint, full, two crossings, tangent, no intersection.
    assert [segment(list(map(D,A)),list(map(D,B)),[ZERO]*3,D(1)) for A,B in [([0,0,0],[1,0,0]),([-2,0,0],[2,0,0]),([2,1,0],[3,1,0]),([-2,1,0],[2,1,0])]]==[D(1),D(2),ZERO,ZERO]
    for f in fixtures: f['expected_edges']=list(map(str,edges(f['X'],f['C'],f['R'],f['dx'])));f['expected_gamma']=str(expected[f['name']])
    dump(out/'ORIGINAL_FAILURE_GEOMETRIES.json',repro)
    dump(out/'REFERENCE_TESTS.json',{'registration':'before production edit','seed':20261016,'precision_digits':70,
      'edge_budget':'1e-10*dx + 1e-9*max(abs(reference),abs(observed)) (existing I0 close, scaled length)',
      'gamma_budget':'1e-10 + 1e-9*max(abs(reference),abs(observed)) (unchanged I0)',
      'collision_budget':'128*eps*S_cell + 1e-12*Jref_cell, Jref_cell=.01; original accumulated global/angular budgets unchanged',
      'acceptance_threshold_length':'1e-12 (existing production cutoff)',
      'checks':checks+148,'fixtures':fixtures,'invariance':'48 cube symmetries; exact dyadic translations xyz',
      'limitations':'continuity bound and reference identity are sampled tests, not a general rounding theorem'})
    with (out/'GEOMETRIES.txt').open('w') as h:
        for f in fixtures: h.write(' '.join(format(float(x),'.17g') for x in [*f['X'],*f['C'],f['R'],f['dx']])+'\n')
    print(json.dumps({'fixtures':len(fixtures),'original_failures':len(repro),'reference_checks':checks+148,'max_original_gamma_error':str(max(abs(gamma(f)-dec(f['observed_gamma'])) for f in repro))}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--old-raw',type=Path,required=True);p.add_argument('--failures',type=Path,required=True);a=p.parse_args();register(a.output,a.old_raw,a.failures)
