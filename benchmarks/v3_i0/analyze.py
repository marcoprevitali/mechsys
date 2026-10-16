#!/usr/bin/env python3
"""Independent 70-digit Decimal population/geometry/exchange oracle (no solver imports)."""
import argparse, csv, hashlib, itertools, json, math
from collections import defaultdict
from decimal import Decimal as D, getcontext, ROUND_HALF_UP
from fractions import Fraction as F
from pathlib import Path
getcontext().prec=70
EPS=D(2)**-52; JR=D('.01'); Z=D(0); HALF=D('.5')
C=[(0,0,0),(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1),(1,1,1),(-1,-1,-1),(1,1,-1),(-1,-1,1),(1,-1,1),(-1,1,-1),(1,-1,-1),(-1,1,1)]
OP=[0,2,1,4,3,6,5,8,7,10,9,12,11,14,13]
W=[D(2)/9]+[D(1)/9]*6+[D(1)/72]*8
def dec(x):return D.from_float(float(x))
def dv(v):return [dec(x) for x in v]
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def neg(a):return [-x for x in a]
def mul(a,s):return [x*s for x in a]
def dot(a,b):return sum((x*y for x,y in zip(a,b)),Z)
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def vmax(a):return max(map(abs,a),default=Z)
def rotate(q,v,inverse=False):
    # Independent quaternion matrix, scalar first. No production rotation helper.
    w,x,y,z=q
    if inverse:x,y,z=-x,-y,-z
    return [(1-2*(y*y+z*z))*v[0]+2*(x*y-w*z)*v[1]+2*(x*z+w*y)*v[2],
            2*(x*y+w*z)*v[0]+(1-2*(x*x+z*z))*v[1]+2*(y*z-w*x)*v[2],
            2*(x*z-w*y)*v[0]+2*(y*z+w*x)*v[1]+(1-2*(x*x+y*y))*v[2]]
def feq(k,rho,v):
    vc=dot(v,C[k]);return W[k]*rho*(1+3*vc+D('4.5')*vc*vc-D('1.5')*dot(v,v))
def center(ic):return [D(ic%10),D(ic//10%10),D(ic//100)]
def lever(p,ic,per):
    r=sub(center(ic),dv(p['x']));image=[0,0,0]
    for j in range(3):
        if int(p['free']) and per[j]:
            image[j]=-int((r[j]/per[j]).to_integral_value(rounding=ROUND_HALF_UP));r[j]+=image[j]*per[j]
    return r,image
def geometry(p,ic,per):
    r,image=lever(p,ic,per);R=dec(p['Dmax'])
    exact=sum((max(abs(x)-HALF,Z)**2 for x in r),Z)<R*R
    # Analytic line/sphere intervals along the twelve cube edges. NOT copied quadratic code.
    length=Z
    for axis in range(3):
        other=[j for j in range(3) if j!=axis]
        for signs in itertools.product([-HALF,HALF],repeat=2):
            rad2=R*R-sum(((r[j]+s)**2 for j,s in zip(other,signs)),Z)
            if rad2<=0:continue
            root=rad2.sqrt();length+=max(Z,min(r[axis]+HALF,root)-max(r[axis]-HALF,-root))
    return exact,length/12,r,image
def legacy_proxy(r,R):
    # Compatibility oracle for the observed loop-control defect, NOT the intended
    # twelve independent edges. A disjoint top edge skips bottom+vertical in its j group;
    # a disjoint bottom edge skips vertical. Analytic projected intervals avoid reusing
    # the production quadratic helper/arithmetic. Preserve the mathematical proxy separately.
    corners=[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1)]
    P=[add(r,[HALF*x for x in c]) for c in corners];length=Z
    for j in range(4):
        for ia,ib in [(j,(j+1)%4),(j+4,(j+1)%4+4),(j,j+4)]:
            a=P[ia];delta=sub(P[ib],a);L2=dot(delta,delta);t=-dot(a,delta)/L2
            d2=dot(a,a)-dot(a,delta)**2/L2;rad2=R*R-d2
            if rad2<=0:continue
            half=(rad2/L2).sqrt();lo,hi=t-half,t+half
            if lo>1 or hi<0:break
            length+=max(Z,min(D(1),hi)-max(Z,lo))*L2.sqrt()
    return length/12
def load(p):return json.loads(p.read_text())
def arr(x):return x if isinstance(x,list) else []
def writecsv(p,rows):
    if not rows:p.write_text('status\nNOT_RUN\n');return
    with p.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def serial(o):
    if isinstance(o,D):return str(o)
    raise TypeError(type(o))
def budget(f,post,bgk,solid,other):
    S=sum(((abs(f[k])+abs(post[k])+abs(bgk[k])+abs(solid[k])+abs(other[k]))*sum(abs(x) for x in C[k]) for k in range(15)),Z)
    return 128*EPS*S+D('1e-12')*JR
def impulse(v):return [sum((v[k]*C[k][j] for k in range(15)),Z) for j in range(3)]
def close(a,b):return abs(a-b)<=D('1e-10')+D('1e-9')*max(abs(a),abs(b))
def analyze(root,out):
    out.mkdir(parents=True,exist_ok=True);momentum=[];torque=[];coverage={};details=[];comparisons=[];shared=[];shared_cells=[]
    maxima=defaultdict(lambda:Z);failures=[];known_proxy_failures=[];measured={};direction_checks=0;cell_checks=0
    def check(ok,what,where):
        if not ok:failures.append({'check':what,**where})
    for backend in ['cpu','cuda']:
      for directory in sorted((root/('runs-'+backend)/backend).glob('*/enabled')):
        case=directory.parent.name;fixture=load(directory/'fixture.json');fc=dec(fixture['Fconv']) if backend=='cuda' else D(1)
        for path in sorted(directory.glob('step-*-before_imprint.json')):
          step=int(path.name.split('-')[1]);pre=load(path);post=load(directory/f'step-{step}-after_imprint.json');cin=load(directory/f'step-{step}-before_collision.json')
          per=dv(pre['Per']);ps=arr(pre['particles']);po=arr(post['particles']);claims=arr(post['claims']);pairs={(int(x['particle']),int(x['cell'])) for x in arr(pre['pairs'])}
          refs={};exact=set();refset=set();legacy_refset=set()
          for ip,p in enumerate(ps):
            for ic in range(1000):
                ex,g,r,im=geometry(p,ic,per)
                if ex:exact.add((ip,ic))
                if g>D('1e-12')/12:refset.add((ip,ic));refs[ip,ic]=(g,r,im)
                if legacy_proxy(r,dec(p['Dmax']))>D('1e-12')/12:legacy_refset.add((ip,ic))
          accepted={(int(x['particle']),int(x['cell'])) for x in claims if int(x['accepted']) and dec(x['gamma'])>0}
          owners=defaultdict(list);allowners=defaultdict(list)
          for ip,ic in refset:allowners[ic].append(ip)
          for ip,ic in accepted:owners[ic].append(ip)
          conflicts=sum(len(v)>1 for v in allowners.values());image_errors=0;geom_err=Z;surface_err=Z
          for cl in claims:
            ip,ic=int(cl['particle']),int(cl['cell'])
            if not int(cl['computed']):continue
            ex,g,r,im=geometry(ps[ip],ic,per);geom_err=max(geom_err,abs(g-dec(cl['gamma'])))
            actual_gamma=dec(cl['gamma']);legacy_gamma=legacy_proxy(r,dec(ps[ip]['Dmax']))
            check(close(legacy_gamma,actual_gamma),'legacy control-flow proxy attribution',{'backend':backend,'case':case,'step':step,'cell':ic,'particle':ip})
            if not close(g,actual_gamma):known_proxy_failures.append({'backend':backend,'case':case,'step':step,'cell':ic,'particle':ip,'mathematical_edge_proxy':g,'observed_gamma':actual_gamma,'independent_legacy_controlflow':legacy_gamma,'status':'FAIL_MATHEMATICAL_PROXY; ATTRIBUTED continue skips remaining edges'})
            if int(cl['accepted']):
                diff=vmax(sub(r,dv(cl['lever'])));image_errors+=int(diff>D('1e-12'))
                vs=add(dv(ps[ip]['v']),cross(rotate(dv(ps[ip]['Q']),dv(ps[ip]['w'])),r))
                surface_err=max(surface_err,vmax(sub(vs,dv(cl['surface']))))
          check(image_errors==0 and surface_err<D('1e-10'),'image and surface velocity',{'backend':backend,'case':case,'step':step})
          coverage[backend,case,step,'imprint']={'reference':len(refset),'legacy_controlflow_reference':len(legacy_refset),'missing_legacy_reference':len(legacy_refset-accepted),'exact_intersections':len(exact),'candidate':len(pairs),'accepted':len(accepted),'missing':len(refset-accepted),'extra':len(accepted-refset),'candidate_missing':len(refset-pairs),'duplicates':len(arr(pre['pairs']))-len(pairs),'conflicts':conflicts,'bad_images':image_errors,'gamma_error':geom_err,'surface_error':surface_err}
          for ip,ic in sorted(refset-accepted):
            g,r,im=refs[ip,ic]
            if (ip,ic) not in pairs:cause='ResetParCell vertex-distance eligibility'
            elif backend=='cpu' and dot(r,r)>dec(ps[ip]['Dmax'])**2:cause='CPU imprint center-distance cutoff'
            elif legacy_proxy(r,dec(ps[ip]['Dmax']))<=D('1e-12')/12:cause='legacy edge-loop continue skips remaining edges'
            elif len(allowners[ic])>1:cause='shared claimant rejected/overwritten'
            else:cause='UNRESOLVED'
            details.append({'backend':backend,'case':case,'step':step,'particle_id':ps[ip]['id'],'cell':ic,'cell_center':center(ic),'particle_position':ps[ip]['x'],'image':im,'lever':r,'gamma_proxy':g,'R':ps[ip]['R'],'candidate':(ip,ic) in pairs,'cause':cause})
          for stage in ['before_rebuild','after_rebuild']:
            rp=directory/f'step-{step}-{stage}.json'
            if not rp.exists():continue
            t=load(rp);rps=arr(t['particles']);rpairs={(int(x['particle']),int(x['cell'])) for x in arr(t['pairs'])};rrefs=set();rex=set()
            for ip,p in enumerate(rps):
              for ic in range(1000):
                ex,g,_,_=geometry(p,ic,per)
                if ex:rex.add((ip,ic))
                if g>D('1e-12')/12:rrefs.add((ip,ic))
            coverage[backend,case,step,stage]={'reference':len(rrefs),'legacy_controlflow_reference':'NOT_EVALUATED','missing_legacy_reference':'NOT_EVALUATED','exact_intersections':len(rex),'candidate':len(rpairs),'accepted':'NOT_EVALUATED','missing':'NOT_EVALUATED','extra':'NOT_EVALUATED','candidate_missing':len(rrefs-rpairs),'duplicates':len(arr(t['pairs']))-len(rpairs),'conflicts':0,'bad_images':0,'gamma_error':'NOT_EVALUATED','surface_error':'NOT_EVALUATED'}
          with (directory/f'step-{step}-collision.csv').open() as f:rows=list(csv.DictReader(f))
          cg=arr(cin['grid']);percell={};jtot=[Z]*3;jbgk=[Z]*3;jsol=[Z]*3;jother=[Z]*3;gbudget=Z;localmax=Z;refmax=Z;opmax=Z;omegaerr=Z;masserr=Z;velerr=Z;alphas=set()
          perparticle=defaultdict(lambda:{'J':[Z]*3,'K':[Z]*3,'budget':Z,'angular':Z,'body':[Z]*3,'angular_budget':Z,'cells':0})
          for ic in range(1000):
            group=rows[ic*15:(ic+1)*15];rr=[{k:dec(v) for k,v in x.items() if k not in ['cell','k']} for x in group]
            pop=[r['before'] for r in rr];after=[r['after'] for r in rr];db=[r['bgk'] for r in rr];ds=[r['solid'] for r in rr];do=[r['other'] for r in rr];total=sub(after,pop)
            rho=sum(pop,Z);u=mul(impulse(pop),1/rho);stored=cg[ic];storedrho=dec(stored['rho']);storedu=dv(stored['vel']);tau0=rr[0]['tau0'];gamma=rr[0]['gamma'];B=gamma*(tau0-HALF)/(1-gamma+tau0-HALF)
            masserr=max(masserr,abs(rho-storedrho));velerr=max(velerr,vmax(sub(u,storedu)))
            # Sc=0 => effective tau=tau0. Body force zero verified explicitly.
            check(all(x==0 for x in dv(stored['bforce'])),'BForce zero',{'backend':backend,'case':case,'step':step,'cell':ic})
            alpha=[r['alpha'] for r in rr];alphas.update(alpha)
            independent_bg=[-alpha[k]*(1-B)*(pop[k]-feq(k,rho,u))/tau0 for k in range(15)]
            independent_solid=[alpha[k]*B*rr[k]['omega'] for k in range(15)]
            # Check true writes against an independently evaluated full operation.
            independent_after=[pop[k]+independent_bg[k]+independent_solid[k] for k in range(15)]
            b=budget(pop,after,db,ds,do);gbudget+=b
            e=vmax(sub(impulse(total),add(add(impulse(db),impulse(ds)),impulse(do))));localmax=max(localmax,e)
            er=max(vmax(sub(impulse(db),impulse(independent_bg))),vmax(sub(impulse(ds),impulse(independent_solid))));refmax=max(refmax,er)
            eo=max(abs(after[k]-independent_after[k]) for k in range(15));opmax=max(opmax,eo)
            where={'backend':backend,'case':case,'step':step,'cell':ic}
            check(e<=b,'collision decomposition',where);check(er<=b,'independent increments',where);check(eo<=b,'independent population write',where)
            check(abs(rho-storedrho)<=b and vmax(sub(u,storedu))<=b,'independent density/raw velocity',where)
            check(vmax(do)<=b and all(a==1 for a in alpha),'roundoff-only other and registered alpha=1',where)
            for k,r in enumerate(rr):
                check(abs(r['solid']-independent_solid[k])<=b and abs(r['bgk']-independent_bg[k])<=b,'directionwise increment',dict(where,k=k))
                check(abs(r['B']-B)<=b and r['tau']==tau0,'collision parameters',dict(where,k=k))
                check(r['omega']==dec(stored['omega'][k]) and r['before']==dec(stored['f'][k]),'actual collision inputs',dict(where,k=k))
            direction_checks+=15;cell_checks+=1
            js=impulse(ds);jt=impulse(total);jb=impulse(db);jo=impulse(do)
            jtot=add(jtot,jt);jbgk=add(jbgk,jb);jsol=add(jsol,js);jother=add(jother,jo)
            claim=owners[ic]
            # Shared geometric cells are explicitly excluded from single-owner acceptance.
            if len(claim)==1 and len(allowners[ic])==1:
                ip=claim[0];p=ps[ip];g,r,im=refs[ip,ic];q=dv(p['Q']);vs=add(dv(p['v']),cross(rotate(q,dv(p['w'])),r))
                om=[pop[OP[k]]-feq(OP[k],storedrho,vs)-pop[k]+feq(k,storedrho,vs) for k in range(15)]
                oerr=max(abs(om[k]-rr[k]['omega']) for k in range(15));omegaerr=max(omegaerr,oerr);check(oerr<=b,'independent surface equilibrium/Omega',where)
                jp=neg(js);K=cross(r,jp);kb=rotate(q,K,True);xp=dv(p['x']);xc=add(xp,r)
                ar=add(add(cross(xc,js),cross(xp,jp)),K);ang=vmax(ar)
                v=perparticle[ip];v['J']=add(v['J'],jp);v['K']=add(v['K'],K);v['body']=add(v['body'],kb);v['budget']+=b;v['cells']+=1;v['angular']=max(v['angular'],ang);v['angular_budget']+=b*(1+sum(map(abs,r))+sum(map(abs,xp))+sum(map(abs,xc)))
            percell[ic]={'gamma':gamma,'B':B,'J':js,'omega':[r['omega'] for r in rr],'ds':ds,'alpha':alpha,'owners':claim}
          legacy=[Z]*3;legacyT=[Z]*3;claimF=defaultdict(lambda:[Z]*3);claimT=defaultdict(lambda:[Z]*3)
          for cl in claims:
            if int(cl['accepted']):ip=int(cl['particle']);claimF[ip]=add(claimF[ip],dv(cl['force']));claimT[ip]=add(claimT[ip],dv(cl['torque']))
          for ip,p in enumerate(ps):
            actual=sub(dv(po[ip]['Flbm']),dv(p['Flbm']));actualT=sub(dv(po[ip]['T']),dv(p['T']));legacy=add(legacy,actual);legacyT=add(legacyT,actualT)
            check(vmax(sub(sub(dv(po[ip]['F']),dv(p['F'])),actual))<=gbudget,'reaction applied to live force exactly once',{'backend':backend,'case':case,'step':step,'particle':ip})
            # Actual live particle accumulation independently checked against captured per-claim sums.
            check(vmax(sub(actual,claimF[ip]))<=gbudget,'actual legacy force accumulation',{'backend':backend,'case':case,'step':step,'particle':ip})
            check(vmax(sub(actualT,claimT[ip]))<=gbudget*10,'actual legacy torque accumulation',{'backend':backend,'case':case,'step':step,'particle':ip})
            if conflicts:continue
            v=perparticle[ip];m=15*v['cells'];gamma_m=D(m)*EPS/(1-D(m)*EPS);pb=v['budget']+gamma_m*sum(map(abs,actual))
            exchange=sub(actual,v['J']);explained=sub(actual,mul(v['J'],fc))
            check(vmax(explained)<=pb,'legacy Fconv attribution',{'backend':backend,'case':case,'step':step,'particle':ip})
            ab=v['angular_budget']+gamma_m*sum(map(abs,actualT));terr=vmax(sub(actualT,mul(v['body'],fc)))
            check(v['angular']<=ab and terr<=ab,'angular ledger/body torque',{'backend':backend,'case':case,'step':step,'particle':ip})
            torque.append({'backend':backend,'case':case,'step':step,'particle_id':p['id'],'world_exchange_residual_max':v['angular'],'expected_body_K':json.dumps(v['body'],default=serial),'actual_legacy_body_hT':json.dumps(actualT,default=serial),'body_discrepancy_max':vmax(sub(actualT,v['body'])),'conversion_explained_residual_max':terr,'budget':ab,'periodic_image_errors':image_errors})
          residual=add(jsol,legacy)
          mb=gbudget+D(15*len(accepted))*EPS/(1-D(15*len(accepted))*EPS)*sum(map(abs,legacy))
          check(mb<=D('1e-8')*10,'budget conditioning',{'backend':backend,'case':case,'step':step})
          support=neg(legacy) if case=='fixed' else [Z]*3
          momentum.append({'backend':backend,'case':case,'step':step,'J_total':json.dumps(jtot,default=serial),'J_BGK':json.dumps(jbgk,default=serial),'J_solid':json.dumps(jsol,default=serial),'J_other':json.dumps(jother,default=serial),'J_particle_expected':json.dumps(neg(jsol),default=serial),'J_particle_legacy':json.dumps(legacy,default=serial),'support_impulse_on_particle':json.dumps(support,default=serial),'legacy_residual_max':vmax(residual),'decomposition_max':localmax,'independent_impulse_max':refmax,'population_write_max':opmax,'Omega_reference_max':omegaerr,'rho_reference_max':masserr,'velocity_reference_max':velerr,'budget':mb,'budget_over_problem_Jref':mb/10,'alpha_min':min(alphas),'alpha_max':max(alphas),'ownership':'BLOCKED_SHARED' if conflicts else 'single_owner'})
          maxima['decomposition']=max(maxima['decomposition'],localmax);maxima['independent_impulse']=max(maxima['independent_impulse'],refmax);maxima['population_write']=max(maxima['population_write'],opmax);maxima['legacy_residual']=max(maxima['legacy_residual'],vmax(residual));maxima['omega_reference']=max(maxima['omega_reference'],omegaerr)
          if case=='shared':
            shared_sum=[Z]*3
            for ic,ips in sorted(allowners.items()):
                if len(ips)<2:continue
                pop=dv(cg[ic]['f']);rho=dec(cg[ic]['rho']);claimants=[];cellF=[Z]*3;matches=[]
                for ip in ips:
                    p=ps[ip];g,r,im=refs[ip,ic];gl=legacy_proxy(r,dec(p['Dmax']));tau=dec(fixture['tau0']);B=gl*(tau-HALF)/(1-gl+tau-HALF)
                    vs=add(dv(p['v']),cross(rotate(dv(p['Q']),dv(p['w'])),r));om=[pop[OP[k]]-feq(OP[k],rho,vs)-pop[k]+feq(k,rho,vs) for k in range(15)]
                    actual=[c for c in claims if int(c['particle'])==ip and int(c['cell'])==ic];c=actual[0] if actual else None
                    force=dv(c['force']) if c and int(c['accepted']) else [Z]*3;cellF=add(cellF,force)
                    if c and int(c['accepted']) and dec(c['gamma'])==percell[ic]['gamma'] and dv(c['omega'])==percell[ic]['omega']:matches.append(p['id'])
                    claimants.append({'particle_id':p['id'],'gamma_math_proxy':g,'gamma_legacy_reference':gl,'B_legacy_reference':B,'Omega_independent':om,'computed_by_production':bool(c and int(c['computed'])),'actual_claim_record':c,'reaction_applied':force})
                cellres=add(percell[ic]['J'],cellF);shared_sum=add(shared_sum,cellres)
                shared_cells.append({'backend':backend,'cell':ic,'claimants':claimants,'actual_stored_gamma':percell[ic]['gamma'],'actual_collision_B':percell[ic]['B'],'actual_stored_Omega':percell[ic]['omega'],'actual_solid_J':percell[ic]['J'],'actual_claim_reaction_sum':cellF,'residual':cellres,'matching_final_claimant_ids':matches,'status':'BLOCKED shared support; observed overwrite' if len(matches)==1 else 'BLOCKED ambiguous/mixed owner'})
            unattributed=sub(residual,shared_sum)
            check(vmax(unattributed)<=mb,'shared residual entirely explained by overlapping-cell overwrites',{'backend':backend,'case':case,'step':step})
            shared.append({'backend':backend,'step':step,'geometric_conflicts':conflicts,'accepted_claimants':[(int(c['particle']),int(c['cell'])) for c in claims if int(c['accepted'])],'legacy_J':legacy,'solid_J':jsol,'residual':residual,'shared_cell_residual_sum':shared_sum,'unattributed_residual':unattributed,'support':'BLOCKED; no unique conservative ownership model','raw':str(directory)})
          measured[backend,case,step]=percell
    parity=[]
    keys=sorted(set((case,step,stage) for backend,case,step,stage in coverage))
    for case,step,stage in keys:
        a=coverage.get(('cpu',case,step,stage));b=coverage.get(('cuda',case,step,stage));row={'case':case,'step':step,'stage':stage,'input_comparison':'identical registered initial state' if step==0 and stage=='imprint' else 'backend-specific evolved geometry; no identical-input parity claim'}
        for key in ['reference','legacy_controlflow_reference','missing_legacy_reference','exact_intersections','candidate','accepted','missing','extra','candidate_missing','duplicates','conflicts','bad_images','gamma_error','surface_error']:
            row['CPU_'+key]=a[key] if a else 'NOT_RUN';row['GPU_'+key]=b[key] if b else 'NOT_RUN'
        parity.append(row)
        if step!=0 or stage!='imprint' or not a or not b:continue
        cells1=measured['cpu',case,0];cells2=measured['cuda',case,0];sets1={ic for ic,v in cells1.items() if v['gamma']>0};sets2={ic for ic,v in cells2.items() if v['gamma']>0}
        common=sets1&sets2;dg=max((abs(cells1[i]['gamma']-cells2[i]['gamma']) for i in common),default=Z);db=max((abs(cells1[i]['B']-cells2[i]['B']) for i in common),default=Z);do=max((vmax(sub(cells1[i]['omega'],cells2[i]['omega'])) for i in common),default=Z);ds=max((vmax(sub(cells1[i]['ds'],cells2[i]['ds'])) for i in common),default=Z)
        comparisons.append({'case':case,'step':0,'common_cells':len(common),'CPU_only':len(sets1-sets2),'GPU_only':len(sets2-sets1),'gamma_max_difference':dg,'B_max_difference':db,'Omega_max_difference':do,'solid_increment_max_difference':ds,'parity':'FAIL_COVERAGE' if sets1!=sets2 else ('BLOCKED_SHARED' if a['conflicts'] else 'PASS')})
    writecsv(out/'MOMENTUM_EXCHANGE_RESULTS.csv',momentum);writecsv(out/'TORQUE_EXCHANGE_RESULTS.csv',torque);writecsv(out/'CELL_PARITY_RESULTS.csv',parity);writecsv(out/'CPU_GPU_CELL_COMPARISON.csv',comparisons)
    (out/'CELL_MISMATCHES.json').write_text(json.dumps(details,default=serial,indent=2)+'\n');(out/'SHARED_RESULTS.json').write_text(json.dumps(shared,default=serial,indent=2)+'\n')
    (out/'PROXY_CONTROL_FLOW_FAILURES.json').write_text(json.dumps(known_proxy_failures,default=serial,indent=2)+'\n')
    (out/'SHARED_CELL_LEDGER.json').write_text(json.dumps(shared_cells,default=serial,indent=2)+'\n')
    summary={'reference_precision_decimal_digits':70,'direction_checks':direction_checks,'cell_checks':cell_checks,'maxima':dict(maxima),'failures':failures,'failures_count':len(failures),'known_mathematical_proxy_failures':len(known_proxy_failures),'shared':shared,'cpu_gpu_first_step':comparisons}
    # Independent exact rational witness: prescribed alpha, NOT production activation.
    B=F(3,16);Om=F(1,50);J=B*Om
    weights=[F(2,9)]+[F(1,9)]*6+[F(1,72)]*8;vs=[F(1,100),F(0),F(0)]
    def eq(k):
        vc=sum(vs[j]*C[k][j] for j in range(3));return weights[k]*(1+3*vc+F(9,2)*vc*vc-F(3,2)*sum(x*x for x in vs))
    om=[eq(k)-eq(OP[k]) for k in range(15)]
    solid=[F(1,2)*B*x for x in om];post=[weights[k]+solid[k] for k in range(15)]
    exactJ=sum(solid[k]*C[k][0] for k in range(15));assert exactJ==F(3,1600) and all(x>0 for x in post)
    witness=[{'k':k,'f_before':str(weights[k]),'Omega':str(om[k]),'B':str(B),'alpha_applied':'1/2','solid_actual_synthetic':str(solid[k]),'f_after_synthetic':str(post[k]),'unlimited_solid_negative_control':str(B*om[k])} for k in range(15)]
    writecsv(out/'SYNTHETIC_LIMITER_WITNESS.csv',witness)
    summary['synthetic_limiter']={'label':'SYNTHETIC full 15-direction exact-rational witness only; not a production limiter activation','alpha':'1/2','unlimited_J':str(J),'limited_J':str(exactJ),'legacy_J':str(-J),'residual':str(-J/2),'pass':J==F(3,800) and exactJ==F(3,1600),'missing_alpha_negative_detected':abs(J-exactJ)>F(1,10**12)}
    (out/'SUMMARY.json').write_text(json.dumps(summary,default=serial,indent=2)+'\n');print(json.dumps({'checks':direction_checks,'failures':len(failures),'maxima':dict(maxima)},default=serial,indent=2))
    if failures:raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.raw,a.output)
