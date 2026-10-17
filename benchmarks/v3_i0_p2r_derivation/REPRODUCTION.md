# Reproduction and preservation

Independent full preparation clone:
/tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/work.
Base031e5e307a1d3a5001537c58cb791bf31edc6ae5;
branch analysis/v3-i0-p2r-targeted-derivation.
Persistent delivery target:
/home/msys/git/mechsys-v3-i0-p2r-targeted-derivation.
Origin=https://github.com/marcoprevitali/mechsys.git;
upstream=https://github.com/Axtal/mechsys.git,upstream push=PUSH_DISABLED.
No original/previous clone is modified.

Frozen R raw input tree:
/tmp/mechsys-v3-i0-p2r-repro.iXq6mh/raw-verified.
Immutable archive:
/home/msys/SIMS/mechsys_v3_i0_p2r_repro_validation/20261017-default-off-audit/P2R_REPRO_RAW.tgz,
SHA256516c9a6ca7c79983883e87a1fdc6a9d5e86a6a3bf5965129808df30e92b341f7,
verified unchanged during D. R reports in the base repository remain unchanged.
Original checkout SHAe4ba163ec9f32c8bccb0fd8619ba79e000d3d6d8,
tracked dirty-diff SHA256e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9.
Original F0 backup: /home/msys/SIMS/mechsys_gpu_backups/20261015-150003/.

## Commands actually used

All output directories below are versioned new directories, not old results.

```bash
python benchmarks/v3_i0_p2r_derivation/extract.py --out /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/static
python benchmarks/v3_i0_p2r_derivation/observe_inertia.py --out /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/host-observation
PYTHONDONTWRITEBYTECODE=1 python benchmarks/v3_i0_p2r_derivation/derive.py --static /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/static --out /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/analysis-final-v3
python benchmarks/v3_i0_p2r_derivation/package.py /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/analysis-final-v2 /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/static /tmp/mechsys-v3-i0-p2r-derivation.cHuxOt/host-observation
PYTHONDONTWRITEBYTECODE=1 python benchmarks/v3_i0_p2r_derivation/CERTIFICATE_VERIFIER.py
git diff --check
```

extract uses cuobjdump/objdump in read-only mode; no binary execution.
observe_inertia requires a debugger/ptrace permission and launches only the
unchanged frozen executables, stops at AddSphere+0x20f BEFORE Solve, reads
stored host mass/I and exits. Its environment removes all task-mode overrides
before setting registered ones. No simulation step or production numerical
update is changed. A fresh output path is required for re-running observations.
"Host observation" describes the measured storage, not absence of CUDA runtime
activity: construction may initialize CUDA and read the device Bn function
pointer symbol. No coupled Solve or numerical timestep is reached.
The default certificate verifier does not need these executables,CUDA,GDB,
the old /tmp raw tree or network. It replays exact local/conditional arithmetic
from committed input-bit manifests and graph extracts. It deliberately cannot
verify unsupported compiled-correspondence claims or approve P2R-KN.
The initial package copy used final-v2; final-v3 is an exact fresh regeneration
after correcting the summary-only conditional-row counter to exclude18
certified source/count premises. All generated final-v3 files match the
committed package; no numerical interval changed.

See ATTEMPTS.md for failed/partial derivation attempts. External new namespace:
/home/msys/SIMS/mechsys_v3_i0_p2r_derivation/20261017-targeted-derivation/.
P2R_DERIVATION_RAW.tgz and its payload index preserve static extraction,
observations,earlier attempts,final analysis and source provenance. DELIVERY.json
records actual tip/remote SHA,archive SHA and clean full clones after completion.
Never infer a successful push or full scientific certificate from a planned
command or this path alone.
