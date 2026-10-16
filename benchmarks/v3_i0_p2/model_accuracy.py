#!/usr/bin/env python3
"""Analysis ONLY: mathematical edge proxy vs independently refined volume estimate.

Analytically integrate z length, composite midpoint quadrature over xy. Exact
containment/disjoint shortcuts; convergence is empirical, not a certified bound.
Never imported by solver, never used as correction acceptance criterion.
"""
import csv,json,math
from pathlib import Path
import numpy as np
from TWELVE_EDGE_REFERENCE import gamma
def volume(x,r,n):
    u=(np.arange(n)+.5)/n-.5
    q=r*r-(u[:,None]-x[0])**2-(u[None,:]-x[1])**2
    root=np.sqrt(np.maximum(q,0));z=np.maximum(0,np.minimum(.5,x[2]+root)-np.maximum(-.5,x[2]-root))
    z[q<=0]=0
    return float(z.sum()/n**2)
rows=[]
for r in [.05,.2,.5,math.sqrt(.5),1.,1.2,2.2]:
    for tag,x in [('center',[0,0,0]),('offset',[.45,.2,.1]),('corner',[.5,.5,.5])]:
        trace=[]
        if all(abs(v)+r<=.5 for v in x):v=4*math.pi*r**3/3;method='analytical contained sphere';conv=True
        elif sum((abs(v)+.5)**2 for v in x)<=r*r:v=1.;method='analytical contained cube';conv=True
        elif sum(max(abs(v)-.5,0)**2 for v in x)>=r*r:v=0.;method='analytical disjoint';conv=True
        else:
            for n in [128,256,512,1024,2048]:
                v=volume(x,r,n);trace.append([n,v])
                if len(trace)>1 and abs(v-trace[-2][1])<min(5e-5,1e-3*max(v,1e-12)):break
            conv=abs(v-trace[-2][1])<min(5e-5,1e-3*max(v,1e-12));method='z-analytic/xy composite midpoint, successive refinement'
        g=float(gamma({'X':x,'C':[0,0,0],'R':r,'dx':1}));diff=abs(g-v)
        rows.append({'case':tag,'R_over_dx':r,'sphere_center':json.dumps(x),'gamma_edge_mathematical':g,'gamma_volume_reference_estimate':v,
          'absolute_difference':diff,'relative_difference':diff/v if v>1e-12 else 'NOT_MEANINGFUL','method':method,
          'successive_refinement_converged':conv,'volume_refinement_trace':json.dumps(trace)})
out=Path(__file__).parent
with (out/'MODEL_ACCURACY.csv').open('w') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
assert all(r['successive_refinement_converged'] for r in rows)
print(json.dumps({'diagnostic_only':True,'cases':len(rows),'converged':sum(r['successive_refinement_converged'] for r in rows),'max_absolute_model_difference':max(r['absolute_difference'] for r in rows)}))
