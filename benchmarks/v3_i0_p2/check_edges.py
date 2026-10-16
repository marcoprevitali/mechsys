#!/usr/bin/env python3
"""Check the actual compiled CPU/CUDA helpers against the frozen independent oracle."""
import argparse,csv,json
from pathlib import Path
from decimal import Decimal as D
from TWELVE_EDGE_REFERENCE import dec
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
reg=json.loads(Path(__file__).with_name('REFERENCE_TESTS.json').read_text());fixtures=reg['fixtures'];allrows=[];fail=[];maxerr=D(0);parity=D(0)
actual={b:list(csv.reader((a.raw/('corrected-'+b+'.csv')).open())) for b in ['cpu','cuda']}
for b,rows in actual.items():
    legacy=list(csv.reader((a.raw/('legacy-'+b+'.csv')).open()));assert len(rows)==len(fixtures)==len(legacy)
    for f,row,old in zip(fixtures,rows,legacy):
        i=int(row[0]);ll,total,*ee=map(dec,row[1:]);ref=list(map(D,f['expected_edges']));dx=dec(f['dx']);g=total/(12*dx);rg=D(f['expected_gamma'])
        assert ll==dec(old[1]), ('legacy helper changed',b,i)
        for j,(r,e) in enumerate(zip(ref,ee)):
            er=abs(r-e);maxerr=max(maxerr,er)
            if er>D('1e-10')*dx+D('1e-9')*max(abs(r),abs(e)): fail.append([b,i,j,'edge',str(er)])
        if abs(g-rg)>D('1e-10')+D('1e-9')*max(abs(g),abs(rg)): fail.append([b,i,'gamma'])
        if not all(0<=x<=dx for x in ee) or not 0<=g<=1:fail.append([b,i,'bounds'])
        if (total>=D('1e-12'))!=(rg*12*dx>=D('1e-12')):fail.append([b,i,'accepted'])
        allrows.append({'backend':b,'fixture':f['name'],'legacy_length':str(ll),'corrected_length':str(total),'reference_length':str(sum(ref)),
            'legacy_gamma':str(ll/(12*dx)),'gamma':str(g),'reference_gamma':str(rg),'accepted':int(total>=D('1e-12')),
            **{f'edge_{j}':str(x) for j,x in enumerate(ee)},'max_edge_error':str(max(abs(x-y) for x,y in zip(ee,ref)))})
for i,f in enumerate(fixtures):
    x,y=actual['cpu'][i],actual['cuda'][i];diff=max(abs(dec(a)-dec(b)) for a,b in zip(x[2:],y[2:]));parity=max(parity,diff)
    if diff>D('1e-10')*dec(f['dx']):fail.append(['parity',i,str(diff)])
    if (float(x[2])>=1e-12)!=(float(y[2])>=1e-12):fail.append(['accepted parity',i])
a.output.mkdir(parents=True,exist_ok=True)
with (a.output/'CPU_GPU_EDGE_RESULTS.csv').open('w') as h:w=csv.DictWriter(h,fieldnames=list(allrows[0]),lineterminator='\n');w.writeheader();w.writerows(allrows)
s={'fixtures_per_backend':len(fixtures),'individual_edge_comparisons':len(fixtures)*24,'reference_mismatches':len(fail),'failures':fail,'max_edge_reference_error':str(maxerr),'max_cpu_gpu_length_or_edge_difference':str(parity),'legacy_helpers':'bitwise unchanged on all geometries'}
(a.output/'EDGE_SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2));assert not fail
