#!/usr/bin/env python3
"""Build the review probes with an existing MechSys CMake toolchain's dependencies."""
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-build",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--cuda",type=Path,required=True)
    parser.add_argument("--sm",default="86")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    args.output.mkdir(parents=True,exist_ok=True)
    toolchain=args.reference_build/"tdem/CMakeFiles/test_cu_04.dir"
    definitions=next(x.split("=",1)[1].strip() for x in (toolchain/"flags.make").read_text().splitlines()
                     if x.startswith("CUDA_DEFINES ="))
    includes=toolchain/"includes_CUDA.rsp"
    link=toolchain/"linkLibs.rsp"
    manifest={"reference_build":str(args.reference_build),"sm":args.sm,"definitions":definitions,
              "includes_sha256":hashlib.sha256(includes.read_bytes()).hexdigest(),
              "link_sha256":hashlib.sha256(link.read_bytes()).hexdigest(),"targets":{}}
    sources={"oracle_negative_controls_hardened":root/"benchmarks/p1_review/oracle_negative_controls.cu",
             "test_cu_04":root/"tdem/test_cu_04.cu"}
    for name,source in sources.items():
        obj=args.output/(name+".o")
        exe=args.output/name
        compile_cmd=[str(args.cuda/"bin/nvcc"),"-std=c++17","-O3","-arch=sm_"+args.sm,
                     "-Xcompiler=-fopenmp",*shlex.split(definitions),"-DUSE_CUDA","-I"+str(root),
                     "--options-file",str(includes),"-c",str(source),"-o",str(obj)]
        link_cmd=["g++","-fopenmp",str(obj),"-o",str(exe),"@"+str(link),
                  "-L"+str(args.cuda/"targets/x86_64-linux/lib")]
        with (args.output/(name+".build.log")).open("w") as log:
            subprocess.run(compile_cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            subprocess.run(link_cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        manifest["targets"][name]={"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                                  "compile":compile_cmd,"link":link_cmd,
                                  "binary_sha256":hashlib.sha256(exe.read_bytes()).hexdigest()}
        print(name+": built",flush=True)
        (args.output/"build_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")


if __name__=="__main__":
    main()
