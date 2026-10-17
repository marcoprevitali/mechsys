#!/usr/bin/env python3
"""All-pairs binary64 audit. No solver imports; no acceptance tolerance changes."""
import argparse, csv, hashlib, itertools, json, math, random, struct
from collections import Counter, defaultdict
from fractions import Fraction as Q
from pathlib import Path
from prepare import sha,save

SIGN=1<<63; MASK=SIGN-1
# Keep the registered D3Q15 ordering, not a guessed lattice convention.
C=[(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),
   (1,1,1),(-1,-1,-1),(1,1,-1),(-1,-1,1),(1,-1,1),(-1,1,-1),(1,-1,-1),(-1,1,1)]

def bits(x):return struct.unpack('>Q',struct.pack('>d',float(x)))[0]
def value(b):return struct.unpack('>d',struct.pack('>Q',b))[0]
def ordered(b):return SIGN-(b&MASK) if b&SIGN else SIGN+b
def ulp(a,b):
    a=float(a);b=float(b)
    if math.isnan(a) or math.isnan(b):return None
    if math.isinf(a) or math.isinf(b):return 0 if a==b else None
    return abs(ordered(bits(a))-ordered(bits(b)))
def different(a,b):return math.isnan(value(a)) or math.isnan(value(b)) or a!=b
def exact(x):return Q.from_float(float(x))
def load(p):return json.loads(p.read_text())
def arr(x):return x if isinstance(x,list) else []
def flat(obj,path=''):
    nums={};other={}
    if isinstance(obj,dict):
        other[path]={'type':'object','keys':sorted(obj)}
        for k,v in obj.items():
            n,o=flat(v,path+'/'+k);nums.update(n);other.update(o)
    elif isinstance(obj,list):
        other[path]={'type':'array','length':len(obj)}
        for i,v in enumerate(obj):
            n,o=flat(v,path+'/'+str(i));nums.update(n);other.update(o)
    else:
        try:nums[path]=bits(obj)
        except (ValueError,TypeError):other[path]=obj
    return nums,other
def canonical(obj):
    n,o=flat(obj);h=hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':')).encode())
    for p,b in sorted(n.items()):h.update(p.encode()+b'\0'+struct.pack('>Q',b))
    return h.hexdigest()
def writecsv(path,rows):
    if not rows:path.write_text('status\nNOT_RUN\n');return
    with path.open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def compare(x,y):
    nx,ox=x;ny,oy=y;keys=sorted(set(nx)|set(ny));diff=[];maxabs=0.;maxulp=0;nonfinite=0
    for p in keys:
        a=nx.get(p);b=ny.get(p)
        if a is None or b is None:diff.append(p);continue
        if not different(a,b):continue
        diff.append(p);a=value(a);b=value(b);u=ulp(a,b)
        if math.isfinite(a) and math.isfinite(b):maxabs=max(maxabs,abs(a-b))
        else:nonfinite+=1
        if u is not None:maxulp=max(maxulp,u)
    return dict(differing_binary64_fields=len(diff),max_abs=maxabs,max_ulp=maxulp,
                first_path=diff[0] if diff else '',structural_equal=ox==oy,nonfinite_differences=nonfinite)

def selftest():
    assert ulp(0.,-0.)==0 and bits(0.)!=bits(-0.)
    assert ulp(-1.,math.nextafter(-1.,-math.inf))==1
    assert ulp(-1.,math.nextafter(-1.,math.inf))==1
    tiny=math.ulp(0.);assert ulp(-tiny,tiny)==2
    assert ulp(float('nan'),float('nan')) is None
    assert different(bits(float('nan')),bits(float('nan')))
    assert ulp(math.inf,math.inf)==0 and ulp(math.inf,-math.inf) is None
    assert ulp(1.,math.nextafter(1.,math.inf))==1
    assert canonical({'v':'1'})==canonical({'v':'1.000'})
    assert canonical({'v':'0'})!=canonical({'v':'-0'})
    assert compare(flat([1]),flat([1,2]))['structural_equal'] is False

def analyze(root,out,archived=False):
    selftest();out.mkdir(parents=True,exist_ok=True)
    if archived:
        dirs=[root/f'{b}-{i}' for b in ['base','candidate'] for i in range(3)]
        labels=['baseline']*3+['candidate']*3
    else:
        dirs=[root/f'{b}-{i:02d}' for i in range(10) for b in ['baseline','candidate']]
        labels=[b for i in range(10) for b in ['baseline','candidate']]
    names=['state-0.json']
    for i in range(2):names += [f'step-{i}-{s}.json' for s in ['before_imprint','after_imprint','before_collision','after_collision']]+[f'state-{i+1}.json']
    allpairs=list(itertools.combinations(range(len(dirs)),2));pairrows=[];first={};hashrows=[];consequences=[]
    claimsets=[];before=[];after=[]
    for name in names:
        parsed=[load(d/name) for d in dirs];flattened=[flat(o) for o in parsed]
        for d,label,o,(n,other) in zip(dirs,labels,parsed,flattened):
            histories={k:o[k] for k in ['histories','gpu_vv','common'] if k in o}
            hashrows.append(dict(run=d.name,label=label,snapshot=name,file_sha256=sha(d/name),
                 numerical_sha256=canonical(o),particle_sha256=canonical(o.get('particles',[])),
                 contact_history_sha256=canonical(histories),pair_sha256=canonical(o.get('pairs',[])),
                 claim_sha256=canonical(o.get('claims',[])),binary64_fields=len(n),
                 nonfinite_fields=sum(not math.isfinite(value(b)) for b in n.values())))
        for i,j in allpairs:
            group='baseline-baseline' if labels[i]==labels[j]=='baseline' else 'candidate-candidate' if labels[i]==labels[j]=='candidate' else 'baseline-candidate'
            c=compare(flattened[i],flattened[j]);row=dict(group=group,run_a=dirs[i].name,run_b=dirs[j].name,snapshot=name,**c)
            pairrows.append(row)
            if (c['differing_binary64_fields'] or not c['structural_equal']) and (i,j) not in first:
                p=c['first_path'];a=flattened[i][0].get(p);b=flattened[j][0].get(p)
                first[i,j]=dict(row,last_identical_snapshot=names[names.index(name)-1] if names.index(name) else 'NONE',
                      value_a=repr(value(a)) if a is not None else '',value_b=repr(value(b)) if b is not None else '')
        # Quantify observed changes by field, not a single global max dominated by units.
        for field in ['F','Flbm','T','v','x','xb','w','wb','wa','Q']:
            maxa=0.;maxu=0;count=0
            for i,j in allpairs:
                for pa,pb in zip(parsed[i]['particles'],parsed[j]['particles']):
                    for a,b in zip(pa[field],pb[field]):
                        if bits(a)!=bits(b):count+=1
                        maxa=max(maxa,abs(float(a)-float(b)));maxu=max(maxu,ulp(a,b) or 0)
            consequences.append(dict(snapshot=name,quantity=field,metric='maximum pairwise component difference',
                                     max_abs=maxa,max_ulp=maxu,differing_fields_over_all_pairs=count))
        if name=='step-0-before_imprint.json':before=parsed
        if name=='step-0-after_imprint.json':after=parsed;claimsets=[o['claims'] for o in parsed]
        print('compared '+name,flush=True)
    allfirst=[]
    for i,j in allpairs:
        row=first.get((i,j),dict(group=('baseline-baseline' if labels[i]==labels[j]=='baseline' else 'candidate-candidate' if labels[i]==labels[j]=='candidate' else 'baseline-candidate'),run_a=dirs[i].name,run_b=dirs[j].name,snapshot='IDENTICAL',
            differing_binary64_fields=0,max_abs=0,max_ulp=0,first_path='',structural_equal=True,nonfinite_differences=0,last_identical_snapshot=names[-1],value_a='',value_b=''))
        allfirst.append(row)
    writecsv(out/'ALL_PAIRWISE_SNAPSHOTS.csv',pairrows);writecsv(out/'FIRST_DIVERGENCE.csv',allfirst)
    for label in ['baseline','candidate']:writecsv(out/(label.upper()+'_REPEATABILITY.csv'),[r for r in hashrows if r['label']==label])
    writecsv(out/'NUMERICAL_CONSEQUENCES.csv',consequences)
    assert all(canonical(c)==canonical(claimsets[0]) for c in claimsets),'first-step contributions differ'
    assert all(canonical(b)==canonical(before[0]) for b in before),'pre-imprint states differ'
    assert not any(r['nonfinite_fields'] for r in hashrows)
    sums,witnesses,inputs=sum_audit(dirs,labels,before,after)
    writecsv(out/'INDEPENDENT_SUMS.csv',sums);save(out/'ORDER_WITNESSES.json',witnesses)
    writecsv(out/'CONTRIBUTION_BITS.csv',inputs)
    balances=balance_audit(dirs)
    writecsv(out/'BALANCE_AND_WORK.csv',balances)
    writecsv(out/'BALANCE_AND_WORK_PHASE_ALIGNED.csv',balances)
    summary=dict(run_count=len(dirs),pair_counts=dict(Counter(r['group'] for r in allfirst)),
        first_divergence=dict(Counter(r['snapshot'] for r in allfirst)),
        same_initial_claims=True,same_before_imprint=True,
        unique_hashes={label:{name:{kind:len({r[kind] for r in hashrows if r['label']==label and r['snapshot']==name})
          for kind in ['file_sha256','numerical_sha256','particle_sha256','contact_history_sha256','pair_sha256','claim_sha256']}
          for name in names} for label in ['baseline','candidate']},
        max_first_sum_error=max(float(r['absolute_error']) for r in sums),
        all_first_sums_within_gamma=all(r['within_gamma_n'] for r in sums),
        all_observed_sums_have_permutation_witness=all(r['permutation_witness'] for r in sums),
        first_summation_n=sums[0]['n_additions'],comparison_selftest='PASS',
        original_gate='P2R-K FAIL unchanged',archived_only=archived)
    save(out/'SUMMARY.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='unique_hashes'},indent=2))

def sum_audit(dirs,labels,before,after):
    rows=[];witnesses={};inputs=[];rng=random.Random(20261017)
    claims=after[0]['claims'];accepted=[(i,c) for i,c in enumerate(claims) if int(c['accepted'])]
    assert len({(int(c['cell']),int(c['particle'])) for _,c in accepted})==len(accepted)
    for i,c in accepted:
        for field in ['force','torque']:
            for j,x in enumerate(c[field]):inputs.append(dict(candidate_index=i,cell=c['cell'],particle_index=c['particle'],particle_id=before[0]['particles'][int(c['particle'])]['id'],quantity=field,component=j,hex64=f'{bits(x):016x}',hexfloat=float(x).hex(),value=repr(float(x))))
    for field,source in [('F','force'),('Flbm','force'),('T','torque')]:
      for j in range(3):
        vals=[float(c[source][j]) for _,c in accepted];initial=float(before[0]['particles'][0][field][j])
        assert initial==0 and all(math.isfinite(x) for x in vals)
        ref=exact(initial)+sum(map(exact,vals),Q());magnitude=abs(exact(initial))+sum(map(lambda x:abs(exact(x)),vals),Q())
        n=len(vals);u=Q(1,2**53);assert n*u<1
        gamma=n*u/(1-n*u);bound=gamma*magnitude
        target={bits(o['particles'][0][field][j]) for o in after};found={}
        # Existential witnesses per independently atomic address. Not a claimed
        # hardware execution trace, and no claim that 9 addresses share an order.
        orders=[list(range(n)),list(reversed(range(n)))]
        trials=0
        for trial in range(20002):
            order=orders[trial] if trial<2 else rng.sample(range(n),n)
            s=initial
            for k in order:s=s+vals[k]
            b=bits(s);trials+=1
            if b in target and b not in found:found[b]=order
            if target<=set(found):break
        witnesses[f'{field}/{j}']=dict(seed=20261017,trials=trials,orders={f'{b:016x}':order for b,order in found.items()},
                                      limitation='existence of a valid scalar order, NOT actual GPU atomic order')
        for d,label,o in zip(dirs,labels,after):
            gpu=float(o['particles'][0][field][j]);err=abs(exact(gpu)-ref)
            rows.append(dict(run=d.name,label=label,particle_id=o['particles'][0]['id'],quantity=field,component=j,
              gpu=repr(gpu),gpu_bits=f'{bits(gpu):016x}',reference_rational=str(ref),reference_rounded=repr(float(ref)),
              reference_rounded_bits=f'{bits(float(ref)):016x}',absolute_error=float(err),
              relative_error=float(err/abs(ref)) if abs(ref)>bound else 'NOT_MEANINGFUL_CANCELLATION',
              ulp_to_correctly_rounded=ulp(gpu,float(ref)),n_additions=n,u=float(u),gamma_n=float(gamma),
              sum_abs=float(magnitude),roundoff_bound=float(bound),within_gamma_n=err<=bound,
              permutation_witness=bits(gpu) in found))
    return rows,witnesses,inputs

def balance_audit(dirs):
    rows=[]
    for d in dirs:
      for step in range(2):
        pre=load(d/f'step-{step}-before_imprint.json')['particles'][0]
        post=load(d/f'step-{step}-after_imprint.json')['particles'][0]
        moved=load(d/f'step-{step}-before_collision.json')['particles'][0]
        jtotal=[Q() for _ in range(3)];jsolid=jtotal.copy();jbgk=jtotal.copy();jother=jtotal.copy()
        with (d/f'step-{step}-collision.csv').open() as f:
          for r in csv.DictReader(f):
            c=C[int(r['k'])]
            if not any(c):continue
            total=exact(r['after'])-exact(r['before']);solid=exact(r['solid']);bgk=exact(r['bgk']);other=exact(r['other'])
            for k in range(3):
                if c[k]:jtotal[k]+=total*c[k];jsolid[k]+=solid*c[k];jbgk[k]+=bgk*c[k];jother[k]+=other*c[k]
        force=[exact(post['F'][k])-exact(pre['F'][k]) for k in range(3)]
        m=exact(pre['mass']);R=exact(pre['R']);I=Q(2,5)*m*R*R
        kinetic=lambda p:m*sum((exact(x)**2 for x in p['v']),Q())/2+I*sum((exact(x)**2 for x in p['w']),Q())/2
        # Midpoint output-velocity power is a diagnostic convention only:
        # legacy v and x are staggered; this is NOT a conserved energy theorem.
        work=sum((force[k]*(exact(pre['v'][k])+exact(moved['v'][k]))/2+
              (exact(post['T'][k])-exact(pre['T'][k]))*(exact(pre['w'][k])+exact(moved['w'][k]))/2) for k in range(3))
        # dt=1: phase-aligned position-Verlet half-step velocities, reconstructed
        # from stored coordinates, avoid mistaking centered v for a full kick.
        minus=[exact(pre['x'][k])-exact(pre['xb'][k]) for k in range(3)]
        plus=[exact(moved['x'][k])-exact(pre['x'][k]) for k in range(3)]
        discrete_work=sum((force[k]*(plus[k]+minus[k])/2 for k in range(3)),Q())
        discrete_dk=m*sum((plus[k]**2-minus[k]**2 for k in range(3)),Q())/2
        halfstep_residual=[m*(plus[k]-minus[k])+jtotal[k] for k in range(3)]
        rows.append(dict(run=d.name,step=step,
           exchange_momentum_residual_max=float(max(abs(force[k]+jsolid[k]) for k in range(3))),
           total_population_plus_particle_impulse_residual_max=float(max(abs(force[k]+jtotal[k]) for k in range(3))),
           actual_particle_plus_fluid_momentum_change_max=float(max(abs(m*(exact(moved['v'][k])-exact(pre['v'][k]))+jtotal[k]) for k in range(3))),
           collision_decomposition_residual_max=float(max(abs(jtotal[k]-jsolid[k]-jbgk[k]-jother[k]) for k in range(3))),
           particle_delta_kinetic=float(kinetic(moved)-kinetic(pre)),midpoint_output_work=float(work),
           kinetic_minus_work_diagnostic=float(kinetic(moved)-kinetic(pre)-work),
           energy_convention='staggered output v/w midpoint diagnostic; NOT conservation/acceptance; I=2mR^2/5 exact diagnostic',
           phase_aligned_total_momentum_residual_max=float(max(map(abs,halfstep_residual))),
           discrete_translational_delta_kinetic=float(discrete_dk),
           discrete_translational_work=float(discrete_work),
           discrete_translational_energy_work_residual=float(discrete_dk-discrete_work),
           dem_history_count=len(arr(load(d/f'state-{step+1}.json')['histories']))))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);p.add_argument('--archived',action='store_true');a=p.parse_args()
    analyze(a.root,a.output,a.archived)
