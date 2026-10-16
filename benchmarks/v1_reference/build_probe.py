#!/usr/bin/env python3
"""Build VV reference regressions and the registered driver with a known CMake toolchain."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-build",type=Path,required=True)
    parser.add_argument("--cuda",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--source-root",type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument("--targets",nargs="+",default=["reference_cuda","reference_cpu","test_cu_04"])
    args=parser.parse_args()
    root=args.source_root.resolve()
    args.output.mkdir(parents=True,exist_ok=True)
    flags=args.reference_build/"tdem/CMakeFiles/test_cu_04.dir"
    definitions=shlex.split(next(x.split("=",1)[1] for x in (flags/"flags.make").read_text().splitlines()
                                if x.startswith("CUDA_DEFINES =")))
    include=flags/"includes_CUDA.rsp"
    libs=flags/"linkLibs.rsp"
    sources={"reference_cuda":Path(__file__).with_name("reference_probe.cu"),
             "reference_cpu":Path(__file__).with_name("reference_probe.cu"),
             "test_cu_04":root/"tdem/test_cu_04.cu",
             "coupled_cuda":root/"tlbmdem/tlbmdem_cu_02.cu"}
    manifest={"source_root":str(root),"headers":{str(p):sha(root/p) for p in [Path("lib/dem/domain.h"),Path("lib/dem/dem.cuh")]},
              "targets":{}}
    for target in args.targets:
        source=sources[target]
        obj=args.output/(target+".o")
        binary=args.output/target
        gpu=target!="reference_cpu"
        compiler=[str(args.cuda/"bin/nvcc"),"-arch=sm_86","-Xcompiler=-fopenmp","-DUSE_CUDA"] if gpu else ["g++","-fopenmp","-x","c++"]
        includes=["--options-file",str(include)] if gpu else ["@"+str(include)]
        compile=compiler+["-std=c++17","-O3",*definitions,"-I"+str(root),*includes,"-c",str(source),"-o",str(obj)]
        link=["g++","-fopenmp",str(obj),"-o",str(binary),"@"+str(libs),"-L"+str(args.cuda/"targets/x86_64-linux/lib")]
        with (args.output/(target+".build.log")).open("w") as log:
            subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,check=True)
            subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
        manifest["targets"][target]={"source_sha256":sha(source),"binary_sha256":sha(binary),"compile":compile,"link":link}
        (args.output/"build_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
        print(target+": built",flush=True)


if __name__=="__main__":
    main()
