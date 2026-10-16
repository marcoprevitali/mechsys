#!/usr/bin/env python3
"""Separate supplemental data: exact stored-binary64 input interpretation.

No frozen fixtures are regenerated. Reference is the unmodified P2 quadratic,
evaluated with a larger Decimal context for the supplemental dynamic range.
Exact Fraction margins/endpoint classification independently cross-check it.
"""
import argparse,importlib.util,itertools,json,math,random
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
sp=importlib.util.spec_from_file_location('ref',Path(__file__).parents[1]/'v3_i0_p2/TWELVE_EDGE_REFERENCE.py');ref=importlib.util.module_from_spec(sp);sp.loader.exec_module(ref)
SIGNS=[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1)]
def fractions(f,e):
    j=e%4;v=j if e<4 or e>=8 else j+4;axis=j%2 if e<8 else 2
    X=list(map(F.from_float,map(float,f['X'])));C=list(map(F.from_float,map(float,f['C'])));h=F.from_float(float(f['dx']))/2;R=F.from_float(float(f['R']))
    q=[C[k]-X[k]+h*SIGNS[v][k] for k in range(3)]
    margin=R*R-sum(q[k]**2 for k in range(3) if k!=axis)
    lo=C[axis]-X[axis]-h;hi=C[axis]-X[axis]+h
    positive=margin>0 and not (lo>=0 and lo*lo>=margin) and not (hi<=0 and hi*hi>=margin)
    return margin,positive
def generate(out):
    fixtures=[]
    def add(name,x,r,dx=1,c=None):fixtures.append({'name':name,'X':list(x),'C':list(c or [0,0,0]),'R':r,'dx':dx})
    # Binary-rational exactly tangent edge lines, and adjacent FP64 offsets.
    for axis in range(3):
      for t in [.0,.25,.5,1.]:
        for n,q in [('tangent',.75),('positive',math.nextafter(.75,0)),('negative',math.nextafter(.75,math.inf))]:
            x=[0,-q+.5,.5];x[0]=t
            x=x[axis:]+x[:axis];add(f'{n}_axis{axis}_endpoint{t}',x,.25)
    # Original cancellation witness plus every cube symmetry, several scales.
    for exp in [-400,-200,0,200,400]:
      s=math.ldexp(1.,exp)
      for n,(perm,sgn) in enumerate(itertools.product(itertools.permutations(range(3)),itertools.product([-1,1],repeat=3))):
        x=[sgn[k]*[.3,.2,.1][perm[k]]*s for k in range(3)]
        add(f'witness_scale{exp}_sym{n}',x,s,s)
    # Margin at ~106-bit resolution: R=1, q1=1, q2=2^-53 -> negative -2^-106.
    # Neighboring representable input radii and centers, not decimal reals.
    for k in [26,40,52,53,54,80,100,150,180]:
      for rtag,r in [('exact',1.),('down',math.nextafter(1.,0)),('up',math.nextafter(1.,math.inf))]:
        add(f'low_margin_{k}_{rtag}',[-.5,-.5+math.ldexp(1.,-k),0],r)
        add(f'low_margin_smallcube_{k}_{rtag}',[0,0,0],r,math.ldexp(1.,-k),[0,1,math.ldexp(1.,-k)])
    # Translation includes large original coordinates and near-cancellation.
    for exp in [0,10,30,45,50,80]:
      for sign in [-1,1]:
        c=[sign*math.ldexp(1.,exp)]*3
        for dx in [1.,math.ldexp(1.,exp-20)]:
          add(f'offset_{exp}_{sign}_{dx}',[c[0]+.3*dx,c[1]+.2*dx,c[2]+.1*dx],dx,dx,c)
    rng=random.Random(2026101602)
    for n in range(300):
        exp=rng.choice([-350,-100,0,100,350]);s=math.ldexp(1.,exp);r=rng.choice([.25,.5,1,1.2])*s
        x=[rng.uniform(-1.5,1.5)*s for _ in range(3)];c=[0.,0.,0.]
        if n%2==0:
            # One exactly selected perpendicular coordinate is an adjacent float
            # around a line tangency. Classify the actual quantized result.
            x[1]=math.nextafter(.5+r,rng.choice([-math.inf,math.inf]));x[2]=.5*s
        add(f'seeded_{n}',x,r,s,c)
    with localcontext() as ctx:
      ctx.prec=700
      for f in fixtures:
        ee=ref.edges(f['X'],f['C'],f['R'],f['dx']);sg=[];positive=[]
        for e,L in enumerate(ee):
            m,p=fractions(f,e);sg.append((m>0)-(m<0));positive.append(p);assert (L>0)==p,(f['name'],e)
        f['expected_edges']=list(map(str,ee));f['expected_gamma']=str(sum(ee)/(12*ref.dec(f['dx'])));f['margin_signs']=sg;f['positive_edges']=positive
    out.mkdir(parents=True,exist_ok=True)
    target=out/'STRESS_FIXTURES.json'
    if target.exists():raise RuntimeError('Refuse regenerate supplemental fixtures')
    target.write_text(json.dumps({'seed':2026101602,'reference':'unmodified P2 quadratic, Decimal700; exact Fraction sign/finite-segment crosscheck','fixtures':fixtures},indent=2)+'\n')
    with (out/'STRESS_GEOMETRIES.txt').open('w') as h:
      for f in fixtures:h.write(' '.join(format(float(x),'.17g') for x in [*f['X'],*f['C'],f['R'],f['dx']])+'\n')
    print('Supplemental geometries registered:',len(fixtures))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();generate(a.output)
