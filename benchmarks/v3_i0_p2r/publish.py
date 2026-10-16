#!/usr/bin/env python3
"""Publish P2R PARTIAL without hiding its strict default-off failure."""
import argparse,csv,hashlib,json,shutil,subprocess
from decimal import Decimal as D
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--geometry',type=Path,required=True);p.add_argument('--coupled',type=Path,required=True);a=p.parse_args()
here=Path(__file__).parent;root=here.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2)+'\n')
def load(p):return json.loads(p.read_text())
def csvread(p):return list(csv.DictReader(p.open()))
def csvout(p,rows):
 with p.open('w') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
g=load(a.geometry/'GEOMETRY_SUMMARY.json');c=load(a.coupled/'P2R_COUPLED_SUMMARY.json');s12=load(a.coupled/'STAGE12.json')
assert g['failures_count']==0 and c['failures_count']==0 and s12['status']=='PASS'
for n in ['FROZEN_FIXTURE_RESULTS.csv','NEAR_TANGENCY_STRESS.csv','CPU_GPU_PARITY.csv','FALLBACK_STATISTICS.csv','GEOMETRY_SUMMARY.json']:
 shutil.copy2(a.geometry/n,here/n)
stats=csvread(here/'FALLBACK_STATISTICS.csv')
for b in ['cpu','cuda']:stats.append({'dataset':'representative_candidate_geometry','backend':b,'edge_evaluations':'NOT_RUN','ordinary_FP64':'NOT_RUN','compensated':'NOT_RUN','exact_predicate_fallback':'NOT_RUN','max_fallback_depth':'NOT_RUN','always_exact_expansion':'NOT_RUN','max_expansion_components':'NOT_RUN'})
csvout(here/'FALLBACK_STATISTICS.csv',stats)
for src,dst in [('CPU_GPU_CELL_COMPARISON.csv','COUPLED_PARITY.csv'),('CELL_PARITY_RESULTS.csv','CANDIDATE_COVERAGE.csv'),('P2R_COUPLED_SUMMARY.json','COUPLED_SUMMARY.json'),('TOTAL_FORCE_DIFFERENCES.csv','TOTAL_FORCE_DIFFERENCES.csv'),('STAGE12.json','STAGE12.json')]:shutil.copy2(a.coupled/src,here/dst)
effect=csvread(a.coupled/'OCCUPANCY_FORCE_DIFFERENCES.csv');selected=[r for r in effect if r['affected']=='True' or r['legacy_zero_robust_positive']=='True'];csvout(here/'OCCUPANCY_FORCE_DIFFERENCES.csv',selected)
mom=csvread(a.coupled/'MOMENTUM_EXCHANGE_RESULTS.csv');tor={(r['backend'],r['case'],r['step']):r for r in csvread(a.coupled/'TORQUE_EXCHANGE_RESULTS.csv')}
joined=[]
for row in mom:
 t=tor[row['backend'],row['case'],row['step']];joined.append({**row,**{k:v for k,v in t.items() if k not in ['backend','case','step','budget']},'angular_budget':t['budget']})
csvout(here/'IMPULSE_TORQUE_REGRESSION.csv',joined)
reg=[]
for b in ['cpu','cuda']:
 for d in sorted((a.raw/'p1-regression'/('runs-'+b)/b).glob('*')):
  if not (d/'reference').exists() or not (d/'off').exists():continue
  equal=all(sha(f)==sha(d/'off'/f.name) for f in (d/'reference').glob('state-*.json'))
  reg.append({'backend':b,'case':d.name,'bitwise_equal':equal,'scope':'unsupported shared negative' if d.name=='shared' else 'required non-shared control'})
required=[r for r in reg if r['case']!='shared'];assert len(required)==43 and sum(r['bitwise_equal'] for r in required)==42
vv=load(a.raw/'standalone-vv/validation.json');assert vv['pass'];neg=load(a.raw/'negative-tests-r2/SUMMARY.json');assert neg['pass'] and len(neg['tests'])==18
diag=load(here/'DEFAULT_OFF_DIAGNOSIS.json');assert diag['same_initial_per_candidate_claims'] and diag['unique_hashes_by_executable']['base']['state-1.json']>1
dump(here/'COMPATIBILITY_SUMMARY.json',{'required_controls':46,'tested':43,'bitwise_pass':42,'strict_fail':1,'not_run':3,'controls':reg,'standalone_vv':vv,'unsupported_guards':neg,'P1_only_regression':'PARTIAL; CUDA tail stopped on default-off failure','corrected_mode':'false in all compatibility controls'})
builds={}
for n in ['base-edge-build','robust-edge-build-r2','coupled-build','reference-build','arithmetic-build','standalone-vv-build']:
 m=load(a.raw/n/'manifest.json')
 if n in ['robust-edge-build-r2','coupled-build','arithmetic-build','standalone-vv-build']:
  assert all(sha(root/k)==v for k,v in m['headers'].items()),n
  assert sha(Path(m['source']))==m['source_sha256'],n
 builds[n]=m
subprocess.run(['python3',str(here/'freeze.py'),'--output',str(here/'FROZEN_MANIFEST.json')],check=True)
maxval=lambda key:max(D(r[key]) for r in joined)
gates={'P2R-'+k:'PASS' for k in 'ABCDEFGHIJLM'};gates['P2R-K']='FAIL';gates['P2R-N']='PENDING delivery receipt'
summary={'milestone':'V3-I0-P2R','status':'PARTIAL; required strict default-off comparison FAIL, no merge/promotion',
 'base':'bf6616973be1335da1caa7d75f8a34aa0f6c1c22','implementation_commit':subprocess.check_output(['git','rev-parse','1bde930'],cwd=root,text=True).strip(),
 'frozen_fixtures_per_backend':1254,'stress_fixtures_per_backend':654,'geometry_failures':0,
 'frozen_max_edge_error':g['frozen']['max_absolute_error'],'frozen_max_gamma_error':g['frozen']['max_gamma_error'],
 'coupled_initial_cases':23,'coupled_imprints':92,'collision_cells':92000,'collision_directions':1380000,'coupled_reference_failures':0,
 'linear_exchange_residual_max':str(maxval('legacy_residual_max')),'world_angular_identity_residual_max':str(maxval('world_exchange_residual_max')),
 'body_torque_error_max':str(maxval('body_discrepancy_max')),'world_angular_scope':'fixed-pose exchange ledger only, NOT full-step angular conservation',
 'initial_cpu_gpu_maxima':{k:str(max(D(r[k]) for r in csvread(here/'COUPLED_PARITY.csv'))) for k in ['gamma_max_difference','B_max_difference','Omega_max_difference','solid_increment_max_difference']},
 'missing_candidates':0,'missing_imprints':0,'duplicates':0,'periodic_image_errors':0,
 'affected_initial_backend_cells':c['affected_initial_backend_cells'],'legacy_zero_positive_cells':c['legacy_zero_robust_positive_cells'],
 'max_delta_gamma':c['effect_max_delta_gamma'],'mean_abs_delta_gamma_affected':c['effect_mean_abs_delta_gamma_affected'],
 'max_delta_particle_impulse':c['max_corrected_impulse_change'],'max_delta_body_torque':c['max_corrected_body_torque_change'],
 'default_off_required_controls':46,'default_off_tested':43,'default_off_bitwise_pass':42,'default_off_strict_fail':1,'default_off_not_run':3,
 'VV_checkpoint_restart_comparisons':6,'VV_checkpoint_bitwise_pass':6,'unsupported_rejections':18,
 'representative_operation_sample':'NOT_RUN after strict default-off hard stop;2100 candidate geometries prepared, no claim of measured counts',
 'gates':gates,'defaults':'ConservativeSphereCells=false, CorrectTwelveEdgeProxy=false, RobustTwelveEdgeProxy=false',
 'next':'User decision on strict default-off reproducibility gate or separately scoped deterministic accumulation work. No implicit gate relaxation.'}
dump(here/'P2R_SUMMARY.json',summary)
dump(here/'PROVENANCE.json',{'base':summary['base'],'preregistration_commit':subprocess.check_output(['git','rev-parse','fb6405b'],cwd=root,text=True).strip(),'implementation_commit':summary['implementation_commit'],
 'builds':builds,'build_provenance':'Builds at preregistration HEAD with dirty candidate headers; their byte hashes now match committed implementation exactly, not called clean-SHA builds',
 'input_sha256':{'frozen':sha(here.parent/'v3_i0_p2/REFERENCE_TESTS.json'),'stress':sha(here/'STRESS_FIXTURES.json'),'frozen_reference':sha(here.parent/'v3_i0_p2/TWELVE_EDGE_REFERENCE.py')},
 'raw':str(a.raw),'geometry_analysis':str(a.geometry),'coupled_analysis':str(a.coupled),'GPU':'NVIDIA RTX A6000 GPU-8cfc4ebf-51b9-f72f-6d58-98b94dbdf5de driver595.84',
 'compiler':'g++13.3;CUDA12.6.85 sm_86;FP64 C++17 O3; no fast-math, CUDA fmad default=true, ftz=false; explicit rn intrinsics/local host volatile enforce transforms',
 'compatibility_failure_preserved':True,'prior_P2_status':'FAIL unchanged','final_tip':'external DELIVERY.json after push; implementation hash above identifies production source'})
for f in here.glob('*.csv'):f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
print(json.dumps(summary,indent=2))
