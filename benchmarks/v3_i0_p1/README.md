# V3-I0-P1: conservative sphere-cell eligibility

**PASS for the registered canonical, single-geometric-owner sphere subset.**
Opt in with `LBMDEM::Domain::ConservativeSphereCells=true`; default false in all
constructors. This corrects eligibility, NOT occupancy arithmetic or integration.
All coupled runs are explicitly legacy compatibility controls, not coupled VV.

Authoritative scientific record: PROJECT_STATUS.md. PROJECT_STATE.md is the
concise entry point. Prior V3-I0 results and strict shared FAIL are unchanged.
Start with V3_I0_P1_DECISION.md and GEOMETRIC_BOUND.md. Corrected mode deliberately
uses a full-grid scan, canonical representation checks, independent map-position
references and a conservative shared-geometric-cell rejection. It can be slower;
there is no throughput claim or production promotion. Noncanonical particles
must use legacy mode. Shared geometry can be rejected even if edge proxy is zero.

## Reproduce in a fresh isolated clone

Use UNUSED REF/RUN paths, installed V2 archived compiler response files and GPU
access. Reference headers are the exact 38da1b9 archive, not edited prior clones.

```bash
REF=/tmp/p1-reference
RUN=/tmp/p1-reproduce
mkdir "$REF"
git archive 38da1b918281883fdc5fb46ea8171082993a1136 | tar -x -C "$REF"
python3 benchmarks/v3_i0/build.py --root "$REF" --source benchmarks/v3_i0_p1/probe.cu --observe --output "$RUN/reference-build"
python3 benchmarks/v3_i0/build.py --source benchmarks/v3_i0_p1/probe.cu --observe --output "$RUN/build"
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN" --reference "$RUN/reference-build" --observer "$RUN/build" --backend cpu --register
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN" --reference "$RUN/reference-build" --observer "$RUN/build" --backend cpu
python3 benchmarks/v3_i0_p1/run.py --raw "$RUN" --reference "$RUN/reference-build" --observer "$RUN/build" --backend cuda
python3 benchmarks/v3_i0_p1/analyze.py --raw "$RUN" --output "$RUN/analysis-new"
```

`P1_MODE=1` selects the library field only in the probe; production callers use
the C++ field. MECHSYS_EXCHANGE_AUDIT is separately compile/env opt-in. The
default-off comparison keeps the existing observer enabled on both reference
and changed builds to retain actual arrays; observer implementation is unchanged.
Published CSVs use LF; immutable raw CSVs retain the original generated format.

25 registered geometries, 22 corrected single-owner cases/backend, two steps
each; 140 completed runs plus two explicit shared rejections. 46 non-shared
reference/off comparisons are bitwise. Wide-skin Alpha=6 is corrected-only:
the legacy wrapped-window duplicate/observer-capacity path is outside the old
non-shared validation contract. Alpha=.4 and .0001 also exercise matched legacy
controls. Shared/contact/Fconv negatives are retained legacy-only; corrected
shared fixture fails explicitly before imprint. No physical positive acceptance
is claimed for unsupported shared geometry or nonunit conversion.

## Evidence and provenance

CPU_GPU_PARITY.csv separates geometric/mathematical/legacy references,
candidate omissions, imprint omissions, proxy-zero cells and duplicates.
CPU_GPU_CELL_COMPARISON.csv compares actual gamma/B/Omega/solid increments at
identical initial inputs only; evolved geometry is independently enumerated per
backend. IMPULSE_REGRESSION.csv and TORQUE_EXCHANGE_RESULTS.csv hold unchanged
V3-D-budget ledger checks. LEGACY_REGRESSION.json preserves shared strict FAIL.

PROVENANCE.json contains exact base/implementation SHA, source/executable/input
hashes and compiler/CUDA commands. Builds used immutable byte snapshots before
source commit; hashes match committed implementation and probe, not relabeled as
clean-SHA builds. CUDA sm_86, FP64/O3/C++17, Nproc=1, a=h=1, 10³ D3Q15/Nl=1,
Sc=0 and the V3-I0 physical parameters remain fixed except explicit manifest
offset/radius/Alpha/velocity extensions. Python standard library only.

Preparation clone `/tmp/mechsys-v3-i0-p1.WEgVFC/work`; persistent delivery target
`/home/msys/git/mechsys-v3-i0-p1-cell-coverage`. New immutable raw archive and final
verification receipt reside in
`/home/msys/SIMS/mechsys_v3_i0_p1_validation/20261016-coverage/`.
No prior clone, original checkout or V3-I0 archive is modified.
