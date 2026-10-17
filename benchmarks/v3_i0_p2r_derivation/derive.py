#!/usr/bin/env python3
"""Offline derivation, not a solver acceptance harness.

Generate local exact-rational certificates and explicitly conditional feedback
boxes. No production import, compiler, GPU, acceptance-test or solver execution.
"""
import argparse, csv, hashlib, json, re, struct
from pathlib import Path
from fractions import Fraction as Q
import arithmetic as A
from arithmetic import I, exact, from_bits, bits, rn, sqrt, fma, dot, cross, hull, U
from extract import HERE, ROOT, BASE, DEFAULT_RAW, save, sha, preservation, bit_tree

C=[(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),
   (1,1,1),(-1,-1,-1),(1,1,-1),(-1,-1,1),(1,-1,1),(-1,1,-1),(1,-1,-1),(-1,1,1)]
OP=[0,2,1,4,3,6,5,8,7,10,9,12,11,14,13]
W=[exact(2./9.)]+[exact(1./9.)]*6+[exact(1./72.)]*8
INERTIA=from_bits('40c0dd7f24550855')

def read(p):return json.loads(Path(p).read_text())
def csvout(p,rows):
    with Path(p).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def vdata(v):return [x.data() for x in v]
def vec(x):return [I(exact(v)) for v in x]
def vhull(v):return I(min(x.lo for x in v),max(x.hi for x in v))
def compact_fluid(post,streamed,macro):
    return dict(domain='cell0..999; direction0..14; bounds uniform across cells, not pairwise errors',
      post_by_direction=[vhull([p[k] for p in post]).data() for k in range(15)],
      streamed_by_direction=[vhull([p[k] for p in streamed]).data() for k in range(15)],
      rho=vhull([v[0] for v in macro]).data(),
      velocity=[vhull([v[1][j] for v in macro]).data() for j in range(3)],
      streaming_destinations=15000,streaming_is_bijection=True,streaming_rounding=0)
def state_memory(p,force,torque):
    d={};pa={32:I(exact(p['mass']))}
    for name,offset in [('x',0),('xb',24),('v',48),('w',72),('wa',96),('wb',120),('F',144),('Flbm',168)]:
        vv=force if name in ['F','Flbm'] else (p[name] if isinstance(p[name][0],I) else vec(p[name]))
        for j,v in enumerate(vv):d[offset+8*j]=v
    q=p['Q'] if isinstance(p['Q'][0],I) else vec(p['Q'])
    for j,v in enumerate(q[1:]+q[:1]):d[192+8*j]=v
    for j,v in enumerate(torque):pa[112+8*j]=v;pa[160+8*j]=I(INERTIA)
    return d,pa

class FloatVM:
    """Straight-line floating slice of frozen PTX, with resolved memory map.

    NOT an interpreter for arbitrary PTX. Branches/pointers are established
    separately; unsupported float instructions are errors, never skipped.
    """
    def __init__(self,memory,pointers):self.r={};self.mem=memory;self.ptr=pointers;self.executed=[]
    def val(self,s):
        s=s.strip()
        if s.startswith('0d'):return I(from_bits(s[2:]))
        return self.r[s]
    def addr(self,s):
        m=re.fullmatch(r'\[(%rd\d+)([+-]-?\d+)?\]',s.strip());assert m,s
        name,offset=self.ptr[m[1]];return name,offset+(int(m[2].replace('+-','-')) if m[2] else 0)
    def run(self,text,tag):
        for line in text.splitlines():
            line=line.strip()
            if not line or line.startswith('.reg') or not '.f64 ' in line:continue
            instr,args=line.rstrip(';').split(' ',1)
            if instr.startswith('ld.global'):
                dest,addr=args.rsplit(', ',1);name,off=self.addr(addr)
                regs=re.findall(r'%fd\d+',dest)
                for j,r in enumerate(regs):self.r[r]=self.mem[name][off+8*j]
            elif instr.startswith('st.global'):
                addr,src=args.split(', ',1);name,off=self.addr(addr)
                regs=re.findall(r'%fd\d+',src)
                for j,r in enumerate(regs):self.mem[name][off+8*j]=self.r[r]
            else:
                aa=[a.strip() for a in args.split(',')];dest=aa.pop(0)
                kind=instr.split('.')[0]
                if kind=='selp':out=self.val(aa[0]) # all six fixed flags false, separately pinned
                elif kind=='mov':out=self.val(aa[0])
                elif kind=='neg':out=-self.val(aa[0])
                elif kind in ['add','sub','mul','div','fma','sqrt']:
                    out=A.op(kind,*[self.val(a) for a in aa],tag=tag+':'+line)
                else:raise ValueError('Unsupported floating instruction '+line)
                self.r[dest]=out
            self.executed.append(line)
        return self

def translate(p,force,torque,graph):
    d,pa=state_memory(p,force,torque);mem={'d':d,'p':pa,'aux':{80:I(1)}}
    # Stop before the vertex loop. A single center vertex follows x exactly:
    # Sterbenz exact subtraction of nearby x_new/x_old, followed by exact
    # reconstruction; rotations of a zero relative vector remain zero.
    text=graph[:graph.index('ld.global.u64 %rd22')]
    vm=FloatVM(mem,{'%rd18':('d',0),'%rd21':('p',0),'%rd2':('aux',72)})
    A.CONTRACT=False;vm.run(text,'Translate')
    return {'x':[d[8*j] for j in range(3)],'xb':[d[24+8*j] for j in range(3)],
            'v':[d[48+8*j] for j in range(3)]},vm

def rotate(p,force,torque,graph):
    d,pa=state_memory(p,force,torque);mem={'d':d,'p':pa,'aux':{80:I(1)}}
    vm=FloatVM(mem,{'%rd20':('d',0),'%rd23':('p',0),'%rd3':('aux',72),'%rd4':('d',208),'%rd5':('p',112)})
    # All center-vertex arithmetic is zero relative to the center and cannot
    # affect the quaternion/wa/w/wb. Retain the actual ordered q-update graph.
    text=graph[:graph.index('ld.global.u64 %rd24')]
    norm=graph[graph.index('mul.f64 %fd156'):graph.index('ld.global.u64 %rd28')]
    A.CONTRACT=True;vm.run(text,'Rotate');vm.run(norm,'Rotate.norm')
    return {'wa':[d[96+8*j] for j in range(3)],'w':[d[72+8*j] for j in range(3)],
      'wb':[d[120+8*j] for j in range(3)],'Q':[d[216]]+[d[192+8*j] for j in range(3)],
      'qD':[vm.r['%fd8'],vm.r['%fd5'],vm.r['%fd6'],vm.r['%fd7']],
      'norm':vm.r['%fd160']},vm

def accumulation(claims,key):
    n=len(claims);g=Q(n)*U/(1-Q(n)*U);rows=[];out=[]
    for j in range(3):
        terms=[exact(c[key][j]) for c in claims];s=sum(terms);sa=sum(map(abs,terms));e=g*sa
        out.append(I(s-e,s+e))
        # Every rounded partial sum has magnitude <=sum_abs*(1+gamma_n).
        # Terms and all RN partial sums are multiples of this dyadic quantum.
        # Thus every NONZERO partial result is normal (zeros are exact).
        quantum=Q(1,max(x.denominator for x in terms))
        assert quantum>=A.power(-1022) and sa*(1+g)<A.from_bits(A.MAX_BITS)
        rows.append(dict(quantity=key,component=j,n=n,exact_sum=str(s),sum_abs=str(sa),gamma_n=str(g),
          error=str(e),pairwise=str(2*e),error_display=float(e),nonzero_partial_quantum=str(quantum),interval=out[-1].data()))
    return out,rows

def bns(g,t):return (g*(t-I(.5)))/((I(1)-g)+(t-I(.5)))
def feq(k,rho,u):
    # The PTX uses y product then two FMA nodes for both dot products;
    # scalar polynomial operations are retained in the original order.
    vc=dot(u,[I(c) for c in C[k]]);vv=dot(u,u)
    a=vc*I(3)/I(1)+I(1)
    b=(vc*(vc*I(4.5)))/I(1)
    return (rho*I(W[k]))*((a+b)-(vv*I(1.5))/I(1))

def collision(pop,rho,u,g,omega):
    t0=I(.8);B=bns(g,t0);ne=[pop[k]-feq(k,rho,u) for k in range(15)]
    # Sc=0: Q is finite and Q*0 is exact zero. Keeping the actual tau square,
    # sqrt, addition and half scaling proves the effective tau, rather than
    # silently replacing it by tau0.
    t=I(.5)*(t0+sqrt(fma(t0,t0,I(0))))
    result=[]
    for k in range(15):
        noneq=((I(1)-B)*ne[k])/t-B*omega[k]
        result.append(pop[k]-I(1)*noneq)
    return result,t,B,ne

def moments(pop):
    rho=I(0);mom=[I(0)]*3
    for k in range(15):
        rho=rho+pop[k]
        mom=[fma(pop[k],I(C[k][j]),mom[j]) for j in range(3)]
    assert rho.lo>0
    c=I(1)/rho;return rho,[c*v for v in mom],mom

def stream(post):
    out=[[None]*15 for _ in range(1000)];keys=[]
    for ic in range(1000):
        xyz=(ic%10,(ic//10)%10,ic//100)
        for k,c in enumerate(C):
            xx=[(xyz[j]+c[j])%10 for j in range(3)];dest=xx[0]+10*(xx[1]+10*xx[2])
            assert out[dest][k] is None;out[dest][k]=post[ic][k];keys.append((dest,k))
    assert len(set(keys))==15000 and all(v is not None for p in out for v in p)
    return out

def surface(p,lever,graph):
    d,pa=state_memory(p,[I(0)]*3,[I(0)]*3)
    vm=FloatVM({'d':d},{'%rd117':('d',0)})
    vm.r.update({'%fd2425':lever[0],'%fd2426':lever[1],'%fd2427':lever[2]})
    a=graph.index('ld.global.v2.f64 {%fd2196');b=graph.index('@%p522 bra $L__BB61_557',a)
    vm.run(graph[a:b],'surface')
    return [vm.r['%fd837'],vm.r['%fd838'],vm.r['%fd839']]

def body_torque(p,lever,force,graph):
    d,pa=state_memory(p,[I(0)]*3,[I(0)]*3)
    vm=FloatVM({'d':d},{'%rd117':('d',0)})
    vm.r.update({f'%fd{2425+j}':lever[j] for j in range(3)})
    vm.r.update({f'%fd{2676+j}':force[j] for j in range(3)})
    a=graph.index('mul.f64 %fd2331');b=graph.index('@%p522 bra $L__BB61_569',a)
    vm.run(graph[a:b],'body_torque')
    return [vm.r[f'%fd{860+j}'] for j in range(3)]

def first_collision(initial,claims):
    bycell={int(c['cell']):c for c in claims};post=[];tau=[];B=[]
    for cell in initial['grid']:
        ic=int(cell['cell']);c=bycell.get(ic)
        g=I(exact(c['gamma'])) if c else I(0);om=vec(c['omega']) if c else [I(0)]*15
        pp,t,b,_=collision(vec(cell['f']),I(exact(cell['rho'])),vec(cell['vel']),g,om)
        post.append(pp);tau.append(t);B.append(b)
    streamed=stream(post);macro=[moments(p) for p in streamed]
    return post,streamed,macro,tau,B

def branch_row(step,scope,predicate,loc,value,observed='NOT_CAPTURED',basis='CERTIFIED'):
    signed=value.lo>0 or value.hi<0
    result='PASS' if signed and basis in ['CERTIFIED','SOURCE_AND_FROZEN_INPUT'] else 'UNRESOLVED'
    margin=value.lo if value.lo>0 else (-value.hi if value.hi<0 else Q(0))
    return dict(step=step,scope=scope,predicate=predicate,source=loc,lo=str(value.lo),hi=str(value.hi),
      lo_display=float(value.lo),hi_display=float(value.hi),observed_branch=observed,
      certified_sign='positive' if value.lo>0 else ('negative' if value.hi<0 else 'EVENT_UNRESOLVED'),
      margin=str(margin),strict_sign_status='PASS' if signed else 'UNRESOLVED',status=result,basis=basis)

def geometry_probe(x,cells,step):
    """Legacy source-control-flow interval witness; no corrected proxy.

    ptxas dataflow equivalence of this source graph remains unproved. In
    particular this probe does NOT promote its branch rows to binary proof.
    """
    rows=[];gammas={};R=I(2.2)
    signs=[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1)]
    for ic in cells:
        center=vec([ic%10,(ic//10)%10,ic//100]);lever=[center[j]-x[j] for j in range(3)]
        P=[[center[k]+I(Q(s[k],2)) for k in range(3)] for s in signs]
        xs=[center[k]-lever[k] for k in range(3)]
        dist=[sqrt(dot([p[k]-xs[k] for k in range(3)],[p[k]-xs[k] for k in range(3)])) for p in P]
        dmin=R*I(2);dmax=I(0)
        def row(pred,v):
            r=branch_row(step,str(ic),pred,'lib/lbmdem/lbmdem.cuh:68-125',v,basis='CONDITIONAL_SOURCE_GRAPH');rows.append(r)
        row('candidate-broad-guard',sqrt(dot(lever,lever))-(R+I(1.74)))
        for k in range(3):
            row('periodic-plus-halfbox-'+str(k),lever[k]-I(5))
            row('periodic-minus-halfbox-'+str(k),lever[k]+I(5))
        for j,d in enumerate(dist):
            row('corner-dmin-'+str(j),dmin-d);row('corner-dmax-'+str(j),d-dmax)
            # Interval min/max encloses both outcomes even across an equality.
            dmin=I(min(dmin.lo,d.lo),min(dmin.hi,d.hi));dmax=I(max(dmax.lo,d.lo),max(dmax.hi,d.hi))
        row('far-reject',dmin-(R+I(1)));row('full-inside',R-dmax)
        if dmin.lo>(R+I(1)).hi:gammas[ic]=I(0);continue
        if dmax.hi<R.lo:gammas[ic]=I(1);continue
        length=I(0);ambiguous=False
        for j in range(4):
            # The continue skips the remaining edge groups for THIS j.
            for edge,(aidx,bidx) in enumerate([(j,(j+1)%4),(j+4,(j+1)%4+4),(j,j+4)]):
                D=[P[bidx][k]-P[aidx][k] for k in range(3)];rel=[P[aidx][k]-xs[k] for k in range(3)]
                a=dot(D,D);b=I(2)*dot(rel,D);c=dot(rel,rel)-R*R;disc=b*b-I(4)*a*c
                prefix=f'edge-{j}-{edge}'
                row(prefix+'-discriminant',disc)
                if disc.hi<0:continue
                if disc.lo<=0:ambiguous=True;break
                root=sqrt(disc);ta=(-b-root)/(I(2)*a);tb=(-b+root)/(I(2)*a)
                for name,v in [('ta-1',ta-I(1)),('tb-1',tb-I(1)),('ta',ta),('tb',tb)]:row(prefix+'-'+name,v)
                if (ta.lo>1 and tb.lo>1) or (ta.hi<0 and tb.hi<0):break
                if (ta.lo<=1<=ta.hi or tb.lo<=1<=tb.hi or ta.lo<=0<=ta.hi or tb.lo<=0<=tb.hi):ambiguous=True;break
                if ta.hi<0:ta=I(0)
                if tb.lo>1:tb=I(1)
                dl=tb-ta;length=length+sqrt(dot([dl*d for d in D],[dl*d for d in D]))
            if ambiguous:break
        if not ambiguous:
            gammas[ic]=length/I(12);row('occupancy-nonzero',length-I(1.e-12))
    return rows,gammas

def second_feedback(p1,grid1,claims,graph):
    # This box is conditional on unchanged second geometry/occupancy and on the
    # audited contraction-family graph. Do not label it a complete certificate.
    formed=[];terms=[]
    for c in claims:
        ic=int(c['cell']);xyz=[ic%10,(ic//10)%10,ic//100];lever=[I(xyz[j])-p1['x'][j] for j in range(3)]
        vel=surface(p1,lever,graph);rho=I(exact(grid1[ic]['rho']));pop=vec(grid1[ic]['f'])
        gamma=I(exact(c['gamma']));B=bns(gamma,I(.8))
        om=[(pop[OP[k]]-feq(OP[k],rho,vel))-(pop[k]-feq(k,rho,vel)) for k in range(15)]
        force=[I(0)]*3
        for k in range(15):
            # All Fconv,Cs,dx equal exactly1; every such multiply is exact.
            a=(B*I(1))*om[k];a=I(1)*a;a=I(1)*a;a=I(1)*a;a=I(1)*a
            force=[force[j]-I(C[k][j])*a for j in range(3)]
        torque=body_torque(p1,lever,force,graph)
        formed.append(dict(cell=ic,gamma=gamma,surface=vel,B=B,omega=om,force=force,torque=torque))
        terms.append(dict(cell=ic,surface=vdata(vel),force=vdata(force),torque=vdata(torque),omega=vdata(om)))
    result={};ledger=[]
    for name in ['force','torque']:
        vv=[]
        for j in range(3):
            lo=sum(c[name][j].lo for c in formed);hi=sum(c[name][j].hi for c in formed)
            sa=sum(c[name][j].absmax() for c in formed);g=Q(93)*U/(1-Q(93)*U);e=g*sa
            assert sa*(1+g)<A.from_bits(A.MAX_BITS),'Atomic partial-sum overflow domain'
            vv.append(I(lo-e,hi+e))
            ledger.append(dict(quantity=name,component=j,formation_pairwise_bound=str(hi-lo),
              accumulation_each=str(e),total_pairwise_bound=str(hi-lo+2*e),
              formation_pairwise_display=float(hi-lo),accumulation_each_display=float(e)))
        result[name]=vv
    return result,formed,terms,ledger

def run(static,raw,out):
    A.selftest();out.mkdir(parents=True,exist_ok=True)
    initial=read(raw/'repeats/baseline-00/state-0.json');claims=read(raw/'repeats/baseline-00/step-0-after_imprint.json')['claims']
    p0=initial['particles'][0];assert len(claims)==93
    graphs=read(static/'candidate-selected-ptx.json');bg=read(static/'baseline-selected-ptx.json')
    for name in ['Translate','Rotate']:
        assert graphs[name]==bg[name],name+' PTX differs'
    force,fr=accumulation(claims,'force');torque,tr=accumulation(claims,'torque')
    # Independent host instruction replay, NOT inversion of w/T.
    m=exact(p0['mass']);r=exact(p0['R']);ih=rn(rn(rn(exact(.4)*m)*r)*r)
    assert ih==INERTIA and m>0 and INERTIA>0
    A.RECORD=True
    trans,tvm=translate(p0,force,torque,graphs['Translate'][0]);rot,rvm=rotate(p0,force,torque,graphs['Rotate'][0])
    logs=A.LOG[:];A.LOG.clear();A.RECORD=False
    assert all(v.lo==v.hi for v in trans['x']+trans['v'])
    # Certify center vertex reconstruction used by the no-rebuild proof.
    for j in range(3):
        old=exact(p0['x'][j]);new=trans['x'][j].point()
        assert rn(new-old)==new-old and rn(old+rn(new-old))==new
    A.CONTRACT=True
    post,streamed,macro,tau,B=first_collision(initial,claims)
    # Check observations AFTER generating the boxes, never use a mismatch as
    # an input radius. Full raw files stay external and immutable.
    dirs=[raw/'repeats'/f'{label}-{i:02d}' for i in range(10) for label in ['baseline','candidate']]
    dirs+=sorted(p for p in (raw/'sanitizers').iterdir() if p.is_dir() and (p/'state-1.json').exists())
    assert len(dirs)==28
    checked=0
    for directory in dirs:
        state=read(directory/'state-1.json');p=state['particles'][0]
        for name,box in [('F',force),('Flbm',force),('T',torque)]:
            for v,x in zip(box,p[name]):assert v.contains(x);checked+=1
        for name in ['x','xb','v','wa','w','wb','Q']:
            vv=trans.get(name,rot.get(name))
            for v,x in zip(vv,p[name]):assert v.contains(x),(directory,name,v.data(),x);checked+=1
        with (directory/'step-0-collision.csv').open() as f:
            for row in csv.DictReader(f):
                assert post[int(row['cell'])][int(row['k'])].contains(row['after']);checked+=1
        for ic,cell in enumerate(state['grid']):
            for v,x in zip(streamed[ic],cell['f']):assert v.contains(x);checked+=1
            assert macro[ic][0].contains(cell['rho']);checked+=1
            for v,x in zip(macro[ic][1],cell['vel']):assert v.contains(x);checked+=1
    one=dict(status='PARTIAL',scope='Frozen rounded first-imprint inputs; legacy no-contact map; not P2R-KN',
      translation_status='CERTIFIED compiled FMA map',rotation_status='CONDITIONAL contraction-family graph pending full SASS translation validation',
      collision_status='CONDITIONAL compiled/source arithmetic graph correspondence',
      accumulation=fr+tr,translation={k:vdata(v) for k,v in trans.items()},
      rotation={k:(v.data() if isinstance(v,I) else vdata(v)) for k,v in rot.items()},
      first_collision=dict(**compact_fluid(post,streamed,macro),effective_tau=tau[0].data(),
        order_uncertainty='zero: first collision consumes cached entry Gamma/Omega, not the sums or updated particle pose'),
      observed_checks=checked,arithmetic_log=logs)
    save(out/'ONE_STEP_CERTIFICATE.json',one)
    p1={**p0,**trans,**{k:v for k,v in rot.items() if k not in ['qD','norm']}}
    # Atomic-order changes cannot feed the FIRST collision: its only particle
    # inputs are cached pre-integration Gamma/Omega. Grid1 is therefore a shared
    # deterministic value, not an independent error term per particle run.
    s1=read(raw/'repeats/baseline-00/state-1.json');cl1=read(raw/'repeats/baseline-00/step-1-after_imprint.json')['claims']
    save(out/'FEEDBACK_INPUT_BITS.json',dict(
      grid1=bit_tree([{k:v for k,v in c.items() if k in ['cell','f','rho','vel']} for c in s1['grid']]),
      second_occupancy=bit_tree([{'cell':c['cell'],'gamma':c['gamma']} for c in cl1]),
      source_sha256={str(raw/'repeats/baseline-00'/name):sha(raw/'repeats/baseline-00'/name) for name in ['state-1.json','step-1-after_imprint.json']},
      condition='grid1 is common by first-collision DAG; second occupancy bits are frozen CONDITIONAL inputs, not derived acceptance references'))
    feedback,formed,termrows,ledger=second_feedback(p1,s1['grid'],cl1,graphs['cudaImprintLatticeVC'][0])
    trans2,_=translate(p1,feedback['force'],feedback['torque'],graphs['Translate'][0])
    rot2,_=rotate(p1,feedback['force'],feedback['torque'],graphs['Rotate'][0])
    bycell={c['cell']:c for c in formed};post2=[];tau2=[];ne2=[]
    for ic,cell in enumerate(s1['grid']):
        cl=bycell.get(ic);g=cl['gamma'] if cl else I(0);om=cl['omega'] if cl else [I(0)]*15
        pp,t,bb,nn=collision(vec(cell['f']),I(exact(cell['rho'])),vec(cell['vel']),g,om)
        post2.append(pp);tau2.append(t);ne2+=nn
    streamed2=stream(post2);macro2=[moments(pp) for pp in streamed2]
    checks2=0
    for directory in dirs:
        st=read(directory/'state-2.json');p=st['particles'][0]
        for name in ['x','xb','v','wa','w','wb','Q']:
            for v,x in zip(trans2.get(name,rot2.get(name)),p[name]):assert v.contains(x),(directory,name,v.data(),x);checks2+=1
        observed=read(directory/'step-1-after_imprint.json')['claims']
        for a,b in zip(formed,observed):
            assert a['cell']==int(b['cell'])
            for key in ['surface','force','torque','omega']:
                for v,x in zip(a[key],b[key]):assert v.contains(x),(key,a['cell'],v.data(),x);checks2+=1
        for ic,cell in enumerate(st['grid']):
            for v,x in zip(streamed2[ic],cell['f']):assert v.contains(x);checks2+=1
            assert macro2[ic][0].contains(cell['rho']);checks2+=1
            for v,x in zip(macro2[ic][1],cell['vel']):assert v.contains(x);checks2+=1
        with (directory/'step-1-collision.csv').open() as f:
            for row in csv.DictReader(f):assert post2[int(row['cell'])][int(row['k'])].contains(row['after']);checks2+=1
    branches=[]
    for step,t in [(0,trans),(1,trans2)]:
        displacement=[t['x'][j]-I(5) for j in range(3)];dist=sqrt(dot(displacement,displacement))
        branches.append(branch_row(step,'particle1','rebuild norm(vertex-reference)-Alpha','lib/lbmdem/Domain.h:1034',dist-I(.4),'false',basis='CERTIFIED' if step==0 else 'CONDITIONAL'))
        for j,v in enumerate(t['x']):
            branches.append(branch_row(step,f'position-{j}','x>0','dem.cuh:BranchVec',v,'true',basis='CERTIFIED' if step==0 else 'CONDITIONAL'))
            branches.append(branch_row(step,f'position-{j}','10-x>0','dem.cuh:BranchVec',I(10)-v,'true',basis='CERTIFIED' if step==0 else 'CONDITIONAL'))
    for step,rq in [(0,rot),(1,rot2)]:branches.append(branch_row(step,'particle1','qD norm positive','dem/dem.cuh:1060',rq['norm'],'true',basis='CONDITIONAL'))
    for step,po,ma in [(0,post,macro),(1,post2,macro2)]:
        for k in range(15):branches.append(branch_row(step,f'ALL1000cells/k{k}','fStar>0 (limiter inactive)','lbmdem.cuh:505',vhull([pp[k] for pp in po]),'true',basis='CONDITIONAL'))
        branches.append(branch_row(step,'ALL1000cells','rho>0','lbmdem.cuh:955',vhull([v[0] for v in ma]),'true',basis='CONDITIONAL'))
        branches.append(branch_row(step,'ALL1000cells','effective tau>0','lbmdem.cuh:483',tau[0] if step==0 else vhull(tau2),'true',basis='CONDITIONAL'))
    geom0rows,geom0=geometry_probe(vec(p0['x']),[int(c['cell']) for c in claims],0);branches+=geom0rows
    geomrows,geom=geometry_probe(trans['x'],[int(c['cell']) for c in cl1],1);branches+=geomrows
    geom_observed=[]
    for step,cc,gg in [(0,claims,geom0),(1,cl1,geom)]:
        for c in cc:
            v=gg.get(int(c['cell']));match=v is not None and v.contains(c['gamma'])
            geom_observed.append(dict(step=step,cell=int(c['cell']),enclosed=match,
              gamma=c['gamma'],source_graph_interval=v.data() if v is not None else None))
    for c in formed:
        branches.append(branch_row(1,str(c['cell']),'gamma-previousGamma positive; unique owner','lbmdem.cuh:629',c['gamma'],'true',basis='CONDITIONAL_FROZEN_GEOMETRY'))
        denominator=(I(1)-c['gamma'])+(I(.8)-I(.5))
        branches.append(branch_row(1,str(c['cell']),'B denominator>0','lbmdem.cuh:427',denominator,'true',basis='CONDITIONAL_FROZEN_GEOMETRY'))
    # Discrete configuration/count predicates use exact integer/boolean
    # premises from source and the frozen list, not a geometric epsilon.
    for step in [0,1]:
        for pred,value,obs,loc in [
          ('nvc=93, active indices0..92; nvc-ic>0',I(1,93),'true','lbmdem.cuh:600'),
          ('inactive indices93..255; nvc-ic-1<0',I(-163,-1),'true','lbmdem.cuh:600'),
          ('nfc=0; no FC writer',I(-1),'true','lbmdem.cuh:705'),
          ('one particle => zero distinct DEM pairs/histories',I(1),'true','dem/domain.h:UpdateContacts'),
          ('six fixed flags false; RotPar true',I(1),'true','probe.cu:183-190'),
          ('registered smooth Bn; all occupancy switches false',I(1),'true','probe.cu:155-164'),
          ('G/Gmix/BForce/Sc=0; no extra fluid force',I(1),'true','probe.cu:149-154'),
          ('Per components nonzero (10)',I(10),'true','dem/distance.h:612'),
          ('UseVelocityVerlet=false; guard not taken',I(-1),'true','lbmdem/Domain.h:780')]:
            branches.append(branch_row(step,'frozen structural premise',pred,loc,value,obs,basis='SOURCE_AND_FROZEN_INPUT'))
    # Required operations whose compiled/memory/control-flow mapping is not
    # certified are explicitly unknown, not given a synthetic finite epsilon.
    unresolved=[dict(quantity='second-step legacy geometry compiled-graph equivalence',reason='source interval graph does not translate all SASS contractions/control predicates'),
      dict(quantity='second-step full collision/stream/macroscopic enclosure',reason='finite conditional boxes evaluated, but second geometry/formation compiled-graph certificate not closed'),
      dict(quantity='two-step independent exchange budget allocation',reason='requires a joint nonduplicated reference-formation and actual-write proof; componentwise compatibility boxes are not that residual')]
    two=dict(status='PARTIAL; NO complete two-step certificate',conditions=['common pinned grid1 by first-collision DAG independence',
      'fixed second-step occupancy/owner/image/pair list','captured candidate PTX arithmetic plus contraction family; SASS equivalence not certified'],
      feedback_ledger=ledger,second_contributions=termrows,
      translation={k:vdata(v) for k,v in trans2.items()},
      rotation={k:(v.data() if isinstance(v,I) else vdata(v)) for k,v in rot2.items()},
      second_collision=dict(**compact_fluid(post2,streamed2,macro2),
        Q_domain='non-equilibrium components bounded by supplied first-stream frozen point inputs; finite norm required',
        max_NonEq=vhull(ne2).data(),effective_tau=vhull(tau2).data()),
      first_geometry_probe={str(k):v.data() for k,v in geom0.items()},
      geometry_probe={str(k):v.data() for k,v in geom.items()},
      geometry_observation_checks=geom_observed,
      unresolved=unresolved,observed_checks=checks2)
    save(out/'TWO_STEP_CERTIFICATE.json',two);csvout(out/'BRANCH_PREDICATE_CERTIFICATE.csv',branches)
    save(out/'ARITHMETIC_GRAPHS.json',{k:v for k,v in graphs.items() if k!='cudaImprintLatticeVC'})
    # Keep only the required float suffix, not thousands of unrelated robust-mode instructions.
    imp=graphs['cudaImprintLatticeVC'][0]
    save(out/'IMPRINT_GRAPH_SUFFIX.json',dict(text=imp[imp.index('$L__BB61_555:'):],
      full_candidate_ptx_sha256=sha(static/'candidate.ptx')))
    observations=read(static.parent/'host-observation/OBSERVATION.json')
    save(out/'FROZEN_STATE_BITS.json',dict(**read(static/'INPUT_BITS.json'),
      principal_inertia=dict(binary64=['40c0dd7f24550855']*3,decimal=repr(float(INERTIA)),exact=str(INERTIA),
        method='new pre-Solve observation of both exact frozen binaries AND exact host instruction replay; no inversion of omega/torque',
        historical_limit='no archived device-I read exists; identical construction + audited copy establishes expected upload bits, not a new historical snapshot'),
      host_observation=observations,
      registered_parameter_bits=bit_tree(read(raw/'INPUT.json')),
      lattice=dict(C=C,OP=OP,weights=[dict(binary64=bits(w),exact=str(w)) for w in W]),
        flags=dict(UseVelocityVerlet=False,ConservativeSphereCells=False,CorrectTwelveEdgeProxy=False,RobustTwelveEdgeProxy=False,
        fixed_velocity=[False]*6,RotPar=True,FixFree=False,IsSolid=[False]*1000),
      scalar_parameters={k:dict(binary64=bits(v),exact=str(exact(v))) for k,v in
         dict(m=m,I=INERTIA,R=r,h=1,dx=1,Cs=1,Fconv=1,Sc=0,tau0=.8,Alpha=.4,nu=.1).items()}))
    used=['lib/dem/dem.cuh','lib/dem/particle.h','lib/dem/dompargen.h','lib/dem/domain.h','lib/lbmdem/Domain.h','lib/lbmdem/lbmdem.cuh','lib/flbm/lbm.cuh','lib/linalg/quaternion.h']
    summary=dict(base=BASE,status='PARTIAL',recommended_outcome='D4',new_solver_steps=0,
      arithmetic_witnesses='PASS',one_step_observation_checks=checked,two_step_conditional_observation_checks=checks2,
      branch_rows=len(branches),unresolved_branch_rows=sum(r['status']=='UNRESOLVED' for r in branches),
      strict_sign_unresolved_branch_rows=sum(r['strict_sign_status']=='UNRESOLVED' for r in branches),
      conditional_branch_rows=sum(r['basis'] not in ['CERTIFIED','SOURCE_AND_FROZEN_INPUT'] for r in branches),
      source_sha256={p:sha(ROOT/p) for p in used},protected_checkouts_after=preservation(),
      production_unchanged=not git_diff_lib(),
      maximum_one_step_errors={k:float(max(v.width() for v in values)) for k,values in {**trans,**{k:v for k,v in rot.items() if isinstance(v,list)}}.items()},
      initial_Q_norm_squared=str(sum(exact(x)**2 for x in p0['Q'])),
      maximum_primitive_local_error=float(max(Q(v['local_rounding_bound']) for v in logs)),
      geometry_observation_checks=len(geom_observed),geometry_observation_misses=sum(not r['enclosed'] for r in geom_observed),
      feedback_ledger=ledger,unresolved=unresolved)
    save(out/'DERIVATION_SUMMARY.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['protected_checkouts_after','source_sha256']},indent=2))

def git_diff_lib():
    from extract import git
    return git(ROOT,'diff',BASE,'--','lib').strip()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--static',type=Path,required=True);p.add_argument('--raw',type=Path,default=Path(DEFAULT_RAW));p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.static,a.raw,a.out)
