#!/usr/bin/env python3
"""Serial exact-binary repeats/sanitizers; never stop other GPU users."""
import argparse, datetime, os, subprocess, time
from pathlib import Path
from prepare import sha, save
import json

DESKTOP='/usr/libexec/gnome-remote-desktop-daemon'
def command(argv):
    p=subprocess.run(argv,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode:raise RuntimeError(str(argv)+'\n'+p.stdout)
    return p.stdout

def inventory(allow):
    q=command(['nvidia-smi','--query-compute-apps=pid,process_name,gpu_uuid,used_memory','--format=csv,noheader'])
    rows=[r.strip() for r in q.splitlines() if r.strip()]
    for r in rows:
        cols=[c.strip() for c in r.split(',')]
        assert allow and cols[1]==DESKTOP, 'Competing GPU process; STOP: '+r
    gpu=command(['nvidia-smi','--query-gpu=name,uuid,driver_version,utilization.gpu,temperature.gpu','--format=csv,noheader'])
    pmon=command(['nvidia-smi','pmon','-c','1'])
    # Any non-desktop compute process in pmon is also forbidden.
    for line in pmon.splitlines():
        if line.startswith('#') or not line.strip():continue
        fields=line.split()
        if 'C' in fields[2]:assert allow and fields[-1].startswith('gnome-remote-de'),line
        if not allow and any(v.isdigit() and int(v)>0 for v in fields[3:5]):
            raise RuntimeError('Active graphics workload violates strict exclusivity: '+line)
    return dict(gpu=gpu,compute=q,pmon=pmon,ps=command(['ps','-eo','pid,ppid,pcpu,comm','--sort=-pcpu']))

def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path)
    p.add_argument('--resident-desktop-exception',action='store_true')
    p.add_argument('--sanitizers',action='store_true');a=p.parse_args()
    assert json.loads((a.raw/'PRIOR_EVIDENCE_VERIFICATION.json').read_text())['status']=='PASS'
    builds=json.loads((a.raw/'EXECUTABLES.json').read_text());fixture=json.loads((a.raw/'INPUT.json').read_text())
    env={k:v for k,v in os.environ.items() if not k.startswith(('P1_','P2_','P2R_','MECHSYS_'))}
    env.update(fixture['environment'])
    config={k:v for k,v in env.items() if k.startswith(('CUDA','NVIDIA','OMP','LD_'))}
    root=a.raw/('sanitizers' if a.sanitizers else 'repeats')
    assert not root.exists(), 'Refuse overwrite runs';root.mkdir()
    save(root/'CONFIG.json',dict(input_sha256=sha(a.raw/'INPUT.json'),environment=fixture['environment'],cuda_environment=config,
         desktop_exception=a.resident_desktop_exception,Nproc=1,exclusive_simulation_process=True,
         cuda_compiler=command(['/usr/local/cuda-12.6/bin/nvcc','--version']),
         host_compiler=command(['g++','--version']),sanitizer=command(['/usr/local/cuda-12.6/bin/compute-sanitizer','--version'])))
    tasks=([(b,0,t) for t in ['memcheck','racecheck','initcheck','synccheck'] for b in ['baseline','candidate']]
           if a.sanitizers else [(b,i,None) for i in range(10) for b in ['baseline','candidate']])
    runs=[]
    for order,(label,rep,tool) in enumerate(tasks):
        exe=Path(builds[label]['executable']);assert sha(exe)==builds[label]['sha256']
        before=inventory(a.resident_desktop_exception)
        name=label+'-'+(tool if tool else str(rep).zfill(2));dest=root/name;dest.mkdir()
        argv=[str(exe),'large',str(dest)]
        if tool:argv=['/usr/local/cuda-12.6/bin/compute-sanitizer','--tool',tool,'--error-exitcode','99']+argv
        row=dict(order=order,label=label,repetition=rep,tool=tool,argv=argv,binary_sha256=sha(exe),
                 input_sha256=sha(a.raw/'INPUT.json'),before=before,start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(dest/'EXECUTION.json',row)
        start=time.monotonic()
        with (dest/'run.log').open('w') as f:
            proc=subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90)
        row.update(returncode=proc.returncode,elapsed_s=time.monotonic()-start,after=inventory(a.resident_desktop_exception),
                   files={f.name:sha(f) for f in sorted(dest.iterdir()) if f.is_file() and f.name!='EXECUTION.json'})
        save(dest/'EXECUTION.json',row);runs.append(row);save(root/'RUNS.json',runs)
        print(name+' exit='+str(proc.returncode)+' states='+str({k:v for k,v in row['files'].items() if k.startswith('state-')}),flush=True)
        if proc.returncode and not tool:raise RuntimeError('Failed normal run; preserve all outputs')
    assert all(sha(Path(b['executable']))==b['sha256'] for b in builds.values())

if __name__=='__main__':main()
