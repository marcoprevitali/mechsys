#!/usr/bin/env python3
"""Seal this partial artifact package; no solver or acceptance invocation."""
from extract import HERE, save, sha

def main():
    paths=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts
      and p.name!='ARTIFACT_MANIFEST.json' and not p.name.endswith('.pyc'))
    save(HERE/'ARTIFACT_MANIFEST.json',dict(status='PARTIAL; hashes do not certify missing proof claims',
      sha256={str(p.relative_to(HERE)):sha(p) for p in paths}))
    print('Sealed',len(paths),'partial proof artifacts')

if __name__=='__main__':main()
