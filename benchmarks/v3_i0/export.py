#!/usr/bin/env python3
"""Losslessly join measured collision writes to imprint-stage geometry; raw output stays outside Git."""
import argparse,csv,gzip,json
from pathlib import Path
from analyze import arr,dec,dv,lever,center
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);a=p.parse_args()
for backend in ['cpu','cuda']:
  for directory in sorted((a.raw/('runs-'+backend)/backend).glob('*/enabled')):
    for path in sorted(directory.glob('step-*-before_imprint.json')):
      step=int(path.name.split('-')[1]);pre=json.loads(path.read_text());post=json.loads((directory/f'step-{step}-after_imprint.json').read_text());cin=json.loads((directory/f'step-{step}-before_collision.json').read_text())
      claims=arr(post['claims']);particles=arr(pre['particles']);grid=arr(cin['grid']);per=dv(pre['Per']);owners={}
      for ic,g in enumerate(grid):
        applied=[c for c in claims if int(c['cell'])==ic and int(c['accepted'])]
        matches=[c for c in applied if dec(c['gamma'])==dec(g['gamma']) and dv(c['omega'])==dv(g['omega'])]
        ids=[particles[int(c['particle'])]['id'] for c in matches];geometry={}
        if len(matches)==1:
            cl=matches[0];pa=particles[int(cl['particle'])];_,image=lever(pa,ic,per)
            geometry={'owner_id':pa['id'],'periodic_image':image,'particle_position':pa['x'],'particle_Q':pa['Q'],'surface_velocity':cl['surface'],'lever':cl['lever']}
        owners[ic]={'owner_status':'NO_SOLID_OWNER' if dec(g['gamma'])==0 else ('UNIQUE_OBSERVED_MATCH' if len(matches)==1 else 'AMBIGUOUS'),'matching_owner_ids':ids,'applied_claimant_ids':[particles[int(c['particle'])]['id'] for c in applied],'cell_center':[str(x) for x in center(ic)],**geometry}
      dst=directory/f'step-{step}-complete-ledger.csv.gz'
      with (directory/f'step-{step}-collision.csv').open() as src,gzip.open(dst,'wt') as out:
        reader=csv.DictReader(src);fields=list(reader.fieldnames)+['backend','case','step','population_stage','geometry_stage','owner_status','owner_id','matching_owner_ids','applied_claimant_ids','periodic_image','particle_position','particle_Q','cell_center','lever','surface_velocity']
        writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader()
        for row in reader:
            row.update({'backend':backend,'case':directory.parent.name,'step':step,'population_stage':'actual_collision_write_before_swap_stream','geometry_stage':'before_imprint_entry_pose'})
            for k,v in owners[int(row['cell'])].items():row[k]=json.dumps(v) if isinstance(v,list) else v
            writer.writerow(row)
      print(dst,flush=True)
