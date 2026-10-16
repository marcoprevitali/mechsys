#!/usr/bin/env python3
"""Publish FAILED P2 evidence. Never relabel P1/default-off checks as P2-on."""
import argparse,csv,hashlib,json,shutil,subprocess
from decimal import Decimal as D
from pathlib import Path
from TWELVE_EDGE_REFERENCE import dec
p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--edges',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];dst=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2)+'\n')
def csvout(p,rows):
    with p.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
edge=json.loads((a.edges/'EDGE_SUMMARY.json').read_text());assert edge['reference_mismatches']==98
for name in ['EDGE_SUMMARY.json','CPU_GPU_EDGE_RESULTS.csv']:shutil.copy2(a.edges/name,dst/name)
rows=list(csv.DictReader((dst/'CPU_GPU_EDGE_RESULTS.csv').open()));fs=json.loads((dst/'REFERENCE_TESTS.json').read_text())['fixtures'];diffs=[]
for n,r in enumerate(rows):
    f=fs[n%len(fs)];gl=dec(r['legacy_gamma']);gc=dec(r['gamma']);dg=gc-gl;tau=D('.8')
    def B(g):return g*(tau-D('.5'))/(1-g+tau-D('.5'))
    diffs.append({'backend':r['backend'],'fixture':r['fixture'],'sphere_center':json.dumps(f['X']),'cube_center':json.dumps(f['C']),
      'R':f['R'],'dx':f['dx'],'gamma_legacy':str(gl),'gamma_candidate':str(gc),'delta_gamma':str(dg),'delta_B_theoretical_tau_0_8':str(B(gc)-B(gl)),
      'relative_gamma_change':str(abs(dg/gl)) if abs(gl)>D('1e-12') else 'NOT_MEANINGFUL',
      'affected_above_1e_10':abs(dg)>D('1e-10'),'legacy_zero_candidate_positive':gl==0 and gc>D('1e-12'),
      'delta_Omega':'NOT_RUN','delta_J':'NOT_RUN','reaction_change':'NOT_RUN','torque_change':'NOT_RUN','scope':'direct helper geometry only; P2 coupled tests stopped'})
csvout(dst/'OCCUPANCY_DIFFERENCES.csv',diffs)
for file in ['IMPULSE_REGRESSION.csv','TORQUE_REGRESSION.csv']:
    csvout(dst/file,[{'scope':'P2 enabled coupled path','status':'NOT_RUN','reason':'P2-C/P2-D failed independent edge reference; hard stop'}])
reg=[]
for b in ['cpu','cuda']:
    rr=json.loads((a.raw/'p1-regression'/('runs-'+b)/'RUNS.json').read_text())
    reg.extend({'backend':b,**r} for r in rr if 'default_off_bitwise' in r)
assert len(reg)==48 and all(r['default_off_bitwise'] for r in reg if r['case']!='shared')
p1=json.loads((a.raw/'p1-regression-analysis/P1_SUMMARY.json').read_text());assert p1['failures_count']==0
vv=json.loads((a.raw/'standalone-vv/validation.json').read_text());assert vv['pass']
guards=json.loads((a.raw/'VV_GUARDS.json').read_text());assert all(r['guard_pass'] for r in guards)
dump(dst/'LEGACY_REGRESSION.json',{'controls':reg,'P2_mode':'false throughout every coupled compatibility run','standalone':vv,'coupled_vv_guards':guards})
for n in ['P1_SUMMARY.json','SUMMARY.json','CPU_GPU_CELL_COMPARISON.csv']:
    shutil.copy2(a.raw/'p1-regression-analysis'/n,dst/('P1_'+n))
affected=[r for r in diffs if r['affected_above_1e_10']]
orig=[r for r in rows if r['fixture'].startswith('original_')]
s={'milestone':'V3-I0-P2','status':'FAIL; hard stop, not accepted','default':'CorrectTwelveEdgeProxy=false; unmerged experimental branch',
 'reference_fixtures_per_backend':len(fs),'edge_comparisons':edge['individual_edge_comparisons'],
 'CPU_failed_fixtures':49,'CUDA_failed_fixtures':49,'CPU_GPU_accepted_helper_mismatches':0,
 'original_16_corrected_gamma_max_error':str(max(abs(dec(r['gamma'])-D(r['reference_gamma'])) for r in orig)),
 'direct_helper_affected_geometry_rows':len(affected),'direct_helper_max_delta_gamma':str(max(abs(D(r['delta_gamma'])) for r in affected)),
 'direct_helper_mean_abs_delta_gamma_affected':str(sum(abs(D(r['delta_gamma'])) for r in affected)/len(affected)),
 'direct_helper_legacy_zero_positive_rows':sum(r['legacy_zero_candidate_positive'] for r in diffs),
 'coupled_affected_cells':'NOT_RUN','corrected_conservation':'NOT_RUN','corrected_CPU_GPU_B_Omega_parity':'NOT_RUN',
 'unchanged_P1_scope':{'completed_processes':140,'shared_rejections':2,'independent_failures':0,'nonshared_bitwise_off_controls':46},
 'standalone_VV_restart':'3 fixtures x CPU/CUDA; all six restart comparisons bitwise, CPU/GPU within original budgets',
 'gates':{'P2-A':'PASS','P2-B':'PASS','P2-C':'FAIL','P2-D':'FAIL','P2-E':'NOT_RUN','P2-F':'NOT_RUN','P2-G':'NOT_RUN',
          'P2-H':'PASS','P2-I':'PARTIAL','P2-J':'PARTIAL','P2-K':'PARTIAL','P2-L':'Pending exact remote/clean delivery receipt'},
 'no_work_on':['Scheme A','coupled restart','coupled VV','P2-B performance','collision arithmetic','contact laws'],
 'next':'Review robust FP64 near-tangency edge evaluation with this exact counterexample and frozen budgets before resuming P2 gates'}
dump(dst/'P2_SUMMARY.json',s)
builds={}
for n in ['legacy-edge-build','corrected-edge-build','coupled-build','reference-build','standalone-vv-build']:
    m=json.loads((a.raw/n/'manifest.json').read_text())
    if n in ['corrected-edge-build','coupled-build','standalone-vv-build']:
        assert all(sha(root/k)==v for k,v in m['headers'].items()),n
        assert sha(Path(m['source']))==m['source_sha256'],n
    builds[n]=m
subprocess.run(['git','diff','e0d6c2f','--exit-code','--','lib/flbm','lib/dem/domain.h','lib/dem/dem.cuh','lib/dem/interacton.h','lib/dem/particle.h','lib/dem/checkpoint.h','benchmarks/v3_i0','benchmarks/v3_i0_p1','benchmarks/v2','benchmarks/v3_coupled_design','AGENTS.md'],check=True,cwd=root)
dump(dst/'PROVENANCE.json',{'base':'e0d6c2fcc581b4caf9d020ebbf05f15c2f5a102f','preregistration_commit':subprocess.check_output(['git','rev-parse','88eb5a2'],cwd=root,text=True).strip(),
 'failed_candidate_commit':subprocess.check_output(['git','rev-parse','c8a8f28'],cwd=root,text=True).strip(),
 'builds':builds,'build_note':'Built from dirty candidate at preregistration HEAD; byte hashes verified against committed files, not falsely called clean-SHA builds',
 'input_sha256':sha(dst/'REFERENCE_TESTS.json'),'geometry_text_sha256':sha(dst/'GEOMETRIES.txt'),'raw':str(a.raw),
 'original_evidence_snapshot_sha256':{f['source_snapshot']:sha(Path(f['source_snapshot'])) for f in json.loads((dst/'ORIGINAL_FAILURE_GEOMETRIES.json').read_text())},
 'GPU':'RTX A6000 / GPU-8cfc4ebf-51b9-f72f-6d58-98b94dbdf5de / driver 595.84','precision':'FP64','compiler':'g++13.3 / CUDA12.6 sm_86 C++17 O3, no fast-math; exact commands in builds',
 'scientific_status':'P2 failed; old P1 compatibility checks do NOT establish P2-on correctness','authoritative_record':'PROJECT_STATUS.md, PROJECT_STATE.md concise pointer'})
for f in dst.glob('*.csv'):f.write_bytes(f.read_bytes().replace(b'\r\n',b'\n'))
print(json.dumps(s,indent=2))
