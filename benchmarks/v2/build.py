#!/usr/bin/env python3
"""Build one bounded V2 probe with the recorded FP64 CUDA/CMake toolchain."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument("--source",type=Path,required=True)
p.add_argument("--output",type=Path,required=True)
p.add_argument("--backends",nargs="+",default=["cpu","cuda"])
p.add_argument("--reference-build",type=Path,default=Path("/tmp/mechsys_v1_build"))
p.add_argument("--cuda",type=Path,default=Path("/usr/local/cuda-12.6"))
a=p.parse_args()
root=Path(__file__).resolve().parents[2]
flags=a.reference_build/"tdem/CMakeFiles/test_cu_04.dir"
definitions=shlex.split(next(x.split("=",1)[1] for x in (flags/"flags.make").read_text().splitlines() if x.startswith("CUDA_DEFINES =")))
a.output.mkdir(parents=True,exist_ok=True)
manifest={"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip(),"source":str(a.source.resolve()),"source_sha256":hashlib.sha256(a.source.read_bytes()).hexdigest(),"targets":{}}
for backend in a.backends:
    binary=a.output/backend
    obj=a.output/(backend+".o")
    compiler=[str(a.cuda/"bin/nvcc"),"-arch=sm_86","-Xcompiler=-fopenmp","-DUSE_CUDA"] if backend=="cuda" else ["g++","-fopenmp","-x","c++"]
    include=flags/"includes_CUDA.rsp"
    includes=["--options-file",str(include)] if backend=="cuda" else ["@"+str(include)]
    compile=compiler+["-std=c++17","-O3",*definitions,"-I"+str(root),*includes,"-c",str(a.source.resolve()),"-o",str(obj)]
    link=["g++","-fopenmp",str(obj),"-o",str(binary),"@"+str(flags/"linkLibs.rsp"),"-L"+str(a.cuda/"targets/x86_64-linux/lib")]
    with (a.output/(backend+".build.log")).open("w") as log:
        subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
    manifest["targets"][backend]={"compile":compile,"link":link,"binary_sha256":hashlib.sha256(binary.read_bytes()).hexdigest()}
    (a.output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(backend+": built",flush=True)
