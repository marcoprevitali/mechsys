#!/usr/bin/env python3
"""Frozen budgets, per-edge errors/classification, exact margin witnesses."""
import argparse,csv,importlib.util,json,math,statistics
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
from pathlib import Path
from stress import fractions
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();here=Path(__file__).parent
def dec(x):return D.from_float(float(x))
def write(p,rows):
    with p.open('w') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
summary={};parity=[];counts=[];fail=[]
oldmap={(bb['backend'],x['fixture'],x['edge']):x['error'] for bb in json.loads((here/'BASELINE_REPRODUCTION.json').read_text()) for x in bb['failed_edges']}
a.output.mkdir(parents=True,exist_ok=True)
with localcontext() as ctx:
 ctx.prec=700
 for dataset,file in [('frozen',here.parent/'v3_i0_p2/REFERENCE_TESTS.json'),('stress',here/'STRESS_FIXTURES.json')]:
    fs=json.loads(file.read_text())['fixtures'];results={};allrows=[];errors=[];relerrors=[];meaningful_rel=[];normalized=[];gammaerr=[];dust=0
    for b in ['cpu','cuda']:
        rows=list(csv.DictReader((a.raw/f'{dataset}-{b}.csv').open()));assert len(rows)==12*len(fs)
        if dataset=='frozen':baseline=list(csv.reader((a.raw/('base-'+b+'.csv')).open()))
        for row in rows:
            i=int(row['fixture']);e=int(row['edge']);f=fs[i];r=D(f['expected_edges'][e]);v=dec(row['length']);dx=dec(f['dx']);g=dec(row['total_length'])/(12*dx);rg=D(f['expected_gamma'])
            assert v.is_finite() and g.is_finite(),(dataset,b,f['name'],'unsupported/NaN')
            er=abs(r-v);tol=D('1e-10')*dx+D('1e-9')*max(abs(r),abs(v));ge=abs(g-rg)
            margin,positive=fractions(f,e);rs=(margin>0)-(margin<0);margin_actual=(dec(row['margin_hi'])+dec(row['margin_lo']))*D(2)**(2*int(row['scale']))
            exactmargin=D(margin.numerator)/D(margin.denominator)
            if er>tol or ge>D('1e-10')+D('1e-9')*max(abs(g),abs(rg)):fail.append([dataset,b,f['name'],e,'frozen error budget'])
            if (v>0)!=positive or int(row['margin_sign'])!=rs:fail.append([dataset,b,f['name'],e,'exact classification'])
            # Returned hi+lo is a diagnostic approximation of an exact expansion;
            # classification uses all components. Cross-check within 4eps.
            if abs(margin_actual-exactmargin)>D(2)**-50*abs(exactmargin):fail.append([dataset,b,f['name'],e,'margin value'])
            if not 0<=v<=dx or not 0<=g<=1:fail.append([dataset,b,f['name'],e,'bounds'])
            if dataset=='frozen':
                assert dec(row['legacy_length'])==dec(baseline[i][1])
                assert dec(row['failed_P2_length'])==dec(baseline[i][2])
            olderror=oldmap.get((b,f['name'],e),'') if dataset=='frozen' else ''
            entry={'dataset':dataset,'backend':b,'fixture':f['name'],'edge':e,'dx':f['dx'],'reference_length':str(r),'actual_length':str(v),
             'absolute_error':str(er),'relative_error':str(er/abs(r)) if r else 'NOT_MEANINGFUL','budget':str(tol),'old_P2_error':olderror,
             'margin_reference_sign':rs,'margin_actual_sign':row['margin_sign'],'margin_hi':row['margin_hi'],'margin_lo':row['margin_lo'],
             'exact_expansion_components':row['components'],'positive_returned_zero':int(positive and v==0),'zero_returned_positive':int(not positive and v>0),
             'gamma':str(g),'gamma_error':str(ge),'status':'PASS' if not (er>tol or (v>0)!=positive or not 0<=v<=dx) else 'FAIL'}
            allrows.append(entry);results[b,i,e]=row;errors.append(er);gammaerr.append(ge)
            normalized.append(er/dx)
            if r:relerrors.append(er/abs(r))
            if r and positive:meaningful_rel.append(er/abs(r))
            if r and not positive:dust+=1
        counts.append({'dataset':dataset,'backend':b,'edge_evaluations':len(rows),'ordinary_FP64':0,'compensated':len(rows),'exact_predicate_fallback':0,'max_fallback_depth':0,'always_exact_expansion':len(rows),'max_expansion_components':max(int(r['components']) for r in rows)})
    for i,f in enumerate(fs):
      for e in range(12):
        x,y=results['cpu',i,e],results['cuda',i,e];diff=abs(dec(x['length'])-dec(y['length']));bound=D('1e-10')*dec(f['dx'])+D('1e-9')*max(abs(dec(x['length'])),abs(dec(y['length'])))
        if diff>bound or x['margin_sign']!=y['margin_sign']:fail.append([dataset,'CPU_GPU',f['name'],e])
        parity.append({'dataset':dataset,'fixture':f['name'],'edge':e,'CPU_length':x['length'],'GPU_length':y['length'],'absolute_difference':str(diff),'CPU_components':x['components'],'GPU_components':y['components'],'same_margin_sign':x['margin_sign']==y['margin_sign'],'status':'PASS' if diff<=bound and x['margin_sign']==y['margin_sign'] else 'FAIL'})
    errors.sort();summary[dataset]={'fixtures_per_backend':len(fs),'individual_edge_comparisons':len(allrows),'max_absolute_error':str(max(errors)),'max_absolute_error_over_dx':str(max(normalized)),'median_absolute_error':str(statistics.median(errors)),'p95_absolute_error':str(errors[math.ceil(.95*len(errors))-1]),'max_relative_error_nonzero_reference':str(max(relerrors,default=D(0))),'max_relative_error_exact_positive_reference':str(max(meaningful_rel,default=D(0))),'frozen_decimal_reference_dust_at_exact_rational_zero':dust,'max_gamma_error':str(max(gammaerr)),'positive_returned_zero':sum(r['positive_returned_zero'] for r in allrows),'zero_returned_positive':sum(r['zero_returned_positive'] for r in allrows),'invalid_lengths_or_gamma':0}
    # Compact publication formatting only, after all checks use full precision.
    for row in allrows:
     for key in ['reference_length','actual_length','absolute_error','relative_error','budget','gamma','gamma_error']:
      if row[key]!='NOT_MEANINGFUL':row[key]=format(D(row[key]),'.18E')
    write(a.output/('FROZEN_FIXTURE_RESULTS.csv' if dataset=='frozen' else 'NEAR_TANGENCY_STRESS.csv'),allrows)
 write(a.output/'CPU_GPU_PARITY.csv',parity);write(a.output/'FALLBACK_STATISTICS.csv',counts)
summary['failures']=fail;summary['failures_count']=len(fail)
(a.output/'GEOMETRY_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print('Geometry failures:',len(fail));assert not fail
