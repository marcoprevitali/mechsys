#!/usr/bin/env python3
"""Check complete input cohorts, serialization payloads and bounded balances."""
import argparse,csv,itertools,json,math
from collections import Counter
from pathlib import Path
from analyze import canonical,load,writecsv,flat,compare,bits,arr,sum_audit,exact
from fractions import Fraction as Q
from prepare import save

def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    dirs=[a.raw/'repeats'/f'{b}-{i:02d}' for i in range(10) for b in ['baseline','candidate']]
    rows=[];stats=[]
    for step in range(2):
        state=[load(d/f'state-{step}.json') for d in dirs]
        pre=[load(d/f'step-{step}-before_imprint.json') for d in dirs]
        post=[load(d/f'step-{step}-after_imprint.json') for d in dirs]
        state_hash=[canonical(o) for o in state];pre_hash=[canonical(o) for o in pre]
        claim_hash=[canonical(o['claims']) for o in post];pair_hash=[canonical(o['pairs']) for o in pre]
        for i,j in itertools.combinations(range(20),2):
            same=state_hash[i]==state_hash[j] and pre_hash[i]==pre_hash[j]
            claims=claim_hash[i]==claim_hash[j]
            assert not same or claims, 'same complete input but changed contribution'
            pair_equal=pair_hash[i]==pair_hash[j]
            assert pair_equal
            rows.append(dict(step=step,run_a=dirs[i].name,run_b=dirs[j].name,complete_input_equal=same,
                contributions_equal=claims,pairs_and_order_equal=pair_equal,
                particle_indices_equal=canonical([c['particle'] for c in post[i]['claims']])==canonical([c['particle'] for c in post[j]['claims']]),
                force_terms_a=sum(int(c['accepted']) for c in post[i]['claims']),force_terms_b=sum(int(c['accepted']) for c in post[j]['claims'])))
        for d,o in zip(dirs,pre):
            pairs=arr(o['pairs']);assert len(pairs)==93
            assert len({(int(c['cell']),int(c['particle'])) for c in pairs})==len(pairs)
            assert len({int(c['cell']) for c in pairs})==len(pairs)
            assert all(0<=int(c['cell'])<1000 and int(c['particle'])==0 for c in pairs)
        stats.append(dict(step=step,complete_input_cohorts=len({s+p for s,p in zip(state_hash,pre_hash)}),
            contribution_cohorts=len(set(claim_hash)),pair_order_cohorts=len(set(pair_hash))))
    writecsv(a.output/'CONTROLLED_INPUT_CHECKS.csv',rows)
    # Parsed grid payload: separate physical fluid values from particle changes.
    grid=[]
    for name in ['state-0.json','state-1.json','state-2.json']:
        states=[load(d/name) for d in dirs]
        grid.append(dict(snapshot=name,fluid_hashes=len({canonical(s['grid']) for s in states}),
               histories_hashes=len({canonical(s['histories']) for s in states}),
               gpu_history_hashes=len({canonical(s['gpu_vv']) for s in states}),
               pairs_hashes=len({canonical(s['pairs']) for s in states}),
               energy_bookkeeping_hashes=len({canonical({k:s[k] for k in ['Evis','Efric','Wext']}) for s in states})))
    writecsv(a.output/'FLUID_HISTORY_STRUCTURE.csv',grid)
    kinetic=[]
    for step in range(3):
        ps=[load(d/f'state-{step}.json')['particles'][0] for d in dirs]
        energies=[]
        for par in ps:
            inertia=Q(2,5)*exact(par['mass'])*exact(par['R'])**2
            energies.append(inertia*sum((exact(w)**2 for w in par['w']),Q())/2)
        kinetic.append(dict(snapshot=f'state-{step}.json',quantity='sphere rotational kinetic energy',
            max_pairwise_difference=float(max(energies)-min(energies)),inertia_convention='exact 2mR^2/5 of serialized m,R; diagnostic only'))
    writecsv(a.output/'KINETIC_ENERGY_VARIATION.csv',kinetic)
    sruns=load(a.raw/'sanitizers/RUNS.json');sdirs=[a.raw/'sanitizers'/(r['label']+'-'+r['tool']) for r in sruns]
    sbefore=[load(d/'step-0-before_imprint.json') for d in sdirs];safter=[load(d/'step-0-after_imprint.json') for d in sdirs]
    normal=load(dirs[0]/'step-0-after_imprint.json')['claims']
    assert all(canonical(o['claims'])==canonical(normal) for o in safter)
    assert all(canonical(o)==canonical(load(dirs[0]/'step-0-before_imprint.json')) for o in sbefore)
    sums,witnesses,_=sum_audit(sdirs,[r['label'] for r in sruns],sbefore,safter)
    assert all(r['within_gamma_n'] and r['permutation_witness'] for r in sums)
    writecsv(a.output/'SANITIZER_INDEPENDENT_SUMS.csv',sums);save(a.output/'SANITIZER_ORDER_WITNESSES.json',witnesses)
    balances=list(csv.DictReader((a.output/'BALANCE_AND_WORK_PHASE_ALIGNED.csv').open()))
    metrics=['exchange_momentum_residual_max','total_population_plus_particle_impulse_residual_max',
       'actual_particle_plus_fluid_momentum_change_max','phase_aligned_total_momentum_residual_max',
       'discrete_translational_energy_work_residual','kinetic_minus_work_diagnostic','particle_delta_kinetic']
    summary=[]
    for step in [0,1]:
      for key in metrics:
        values=[float(r[key]) for r in balances if int(r['step'])==step]
        summary.append(dict(step=step,quantity=key,minimum=min(values),maximum=max(values),max_abs=max(map(abs,values)),
                            range=max(values)-min(values)))
    writecsv(a.output/'BALANCE_SUMMARY.csv',summary)
    save(a.output/'TRACE_SUMMARY.json',dict(cohorts=stats,fluid=grid,all_indices_unique_and_in_range=True,
        all_equal_complete_inputs_give_equal_claims=True,
        limitation='existing diagnostics synchronize; exact instruction order not traced; two-step legacy case, zero DEM histories'))
    print(json.dumps(stats,indent=2))

if __name__=='__main__':main()
