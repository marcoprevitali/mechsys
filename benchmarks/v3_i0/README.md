# V3-I0: observational legacy exchange audit

2026-10-16 Asia/Shanghai. **PARITY BLOCKED.** No Scheme A, coupled VV,
checkpoint change, geometry correction or performance measurement. The coupled
VV guard remains enabled. These are explicitly legacy compatibility controls,
not a change to the program's VV reference policy.

Start with [V3_I0_DECISION.md](V3_I0_DECISION.md). Numerical data are in
[SUMMARY.json](SUMMARY.json), [momentum](MOMENTUM_EXCHANGE_RESULTS.csv),
[torque](TORQUE_EXCHANGE_RESULTS.csv), [coverage](CELL_PARITY_RESULTS.csv)
and [REGRESSION.json](REGRESSION.json). The original V2 and all seven V3-D
documents/results are unchanged.
Published CSV copies use LF line endings for Git; their parsed fields are
identical to the original CRLF CSVs retained in the immutable raw archive.

## Scope and provenance

Full user-fork clone, base `d801c80cce15691b2a886a31d7e0bd864de35c10`, branch
`validation/v3-i0-exchange-audit`. Work was prepared in
`/tmp/mechsys-v3-i0.30PYI0/work`; persistent delivery clone is
`/home/msys/git/mechsys-v3-i0-exchange-audit` (final Git verification recorded at
delivery). Instrumentation commit `28e292f2f421a7254a18889dfb2b50d7590ba42f`.
Preregistration `9f6a5e98e2618092b639286011facacb63fa9c6c` precedes runtime.
Source/executable/input/toolchain hashes: [PROVENANCE.json](PROVENANCE.json).
Builds used pre-commit source snapshots; their byte hashes were verified against
the committed observer headers and final probe, not relabeled as clean-SHA builds.

FP64 D3Q15, Nl=1, 10³ periodic lattice, a=h=c=1, rho=1, nu=.1, tau0=.8,
Sc=Gammaf=BForce=Gv=Gm=0, smooth B, Fconv=1 except the labeled negative.
Spheres have R=1.2 and density 100 except the registered zero/contact controls.
Nproc=1; no random geometry. Eleven cases/backend, 1–3 timesteps, identical
initialization/allocation/output cadence across reference/off/enabled modes.
66 final bounded runs plus two explicit VV-guard rejections. No timed campaign.
The contact control exercises nonzero tangential-history creation/separation;
its rolling-history slots stay zero. The preregistered shorthand “nonzero
tangent/rolling” was not fully realized: this is not a new nonzero-rolling
validation, and no V2 rolling result is replaced by that narrower control.

## Reproduction

Use a fresh isolated clone, not any preserved checkout. `RUN` and `REF` below
must be unused directories; never overwrite an existing evidence directory.
The build uses the existing archived V2 compiler response files (paths/commands
are recorded in PROVENANCE.json); installed dependencies are required.

```bash
git switch validation/v3-i0-exchange-audit
RUN=/tmp/mechsys-v3-i0-reproduce
REF=/tmp/mechsys-v3-i0-reference
mkdir "$REF"
git archive d801c80cce15691b2a886a31d7e0bd864de35c10 | tar -x -C "$REF"
python3 benchmarks/v3_i0/build.py --root "$REF" --output "$RUN/build-reference-v5"
python3 benchmarks/v3_i0/build.py --observe --output "$RUN/build-observer-v5"
python3 benchmarks/v3_i0/run.py --raw "$RUN/final/runs-cpu" --reference "$RUN/build-reference-v5" --observer "$RUN/build-observer-v5" --backends cpu
python3 benchmarks/v3_i0/run.py --raw "$RUN/final/runs-cuda" --reference "$RUN/build-reference-v5" --observer "$RUN/build-observer-v5" --backends cuda
python3 benchmarks/v3_i0/analyze.py --raw "$RUN/final" --output "$RUN/final/analysis"
python3 benchmarks/v3_i0/export.py --raw "$RUN/final"
```

CUDA runtime needs GPU access. Python 3 standard library only; no compiled
collision helper is imported by the oracle. The collector is for this session's
preservation checks and compact publication; its original-checkout/prior-clone
assertions are intentionally site-specific, not required for an independent run.
Shared-cell strict regressions may fail and are retained; **stop that affected
support claim**, do not serialize or repair the production kernel to pass it.

## Raw data and interpretation

Durable archive directory:
`/home/msys/SIMS/mechsys_v3_i0_validation/20261016-v3-i0-exchange-audit/`.
`V3_I0_RAW.tgz` contains raw `final/`, original pilots/failed builds and failed
mathematical-proxy oracle outputs. `ARTIFACT_INDEX.csv` inside the archive hashes
1,265 payload files; [ARTIFACT_SUMMARY.json](ARTIFACT_SUMMARY.json) records counts.
The external `DELIVERY.json` records final archive/Git verification.

Each enabled step contains entry pose/IDs and actual pair lists, accepted claim
records, pre-collision populations/macros/gamma/Omega and the **actual collision
write** CSV. `*-complete-ledger.csv.gz` is a lossless directionwise join including
owner ID, image, x/Q, cell center, lever, surface velocity and all increments.
Geometry is the **imprint-entry pose**, not the drifted pose at collision time.
No owner is invented for a shared/mixed cell: AMBIGUOUS is explicit.

Coverage counts are particle–cell pairs (identical to unique cell counts for
single-owner cases). Shared case: 54 reference pairs, 45 distinct cells, nine
conflicted cells. Mathematical twelve-edge coverage, implemented legacy
control-flow proxy, and exact sphere/AABB intersection are separate columns.
Rebuild rows inspect actual lists at moved geometry; accepted occupancy is
NOT_EVALUATED there, not inferred from a stale imprint. Only initial step-0
CPU/GPU comparisons have identical registered states; evolved states are audited
against their own geometry, never relabeled as identical-input comparisons.

The full-grid raw-population ledger includes PSM interior fluid. It is not a
validated physical exterior-fluid/added-mass ledger or a new integrator test.
