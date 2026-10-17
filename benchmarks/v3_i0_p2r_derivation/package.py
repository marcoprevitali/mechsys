#!/usr/bin/env python3
"""Publish generated proof artifacts; preserve earlier attempts externally."""
import argparse, json, shutil
from pathlib import Path
from extract import HERE, save, sha

def main():
    p=argparse.ArgumentParser();p.add_argument('analysis',type=Path);p.add_argument('static',type=Path);p.add_argument('observation',type=Path);a=p.parse_args()
    for src in sorted(a.analysis.iterdir()):
        if src.is_file():
            dest=HERE/src.name;assert not dest.exists(),dest;shutil.copy2(src,dest)
    dest=HERE/'binary_evidence';dest.mkdir(exist_ok=False)
    for src in [a.static/'baseline-AddSphere.asm',a.static/'candidate-AddSphere.asm',a.observation/'baseline.log',a.observation/'candidate.log',a.observation/'OBSERVATION.json']:
        shutil.copy2(src,dest/src.name)
    save(dest/'EXTRACTION.json',json.loads((a.static/'EXTRACTION.json').read_text()))
    print('Copied generated certificates and bounded host observation receipts.')

if __name__=='__main__':main()
