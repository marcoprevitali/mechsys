# V3-I0-P2R-R — observational CUDA reproducibility audit

2026-10-17 / Codex. Read REPRODUCIBILITY_DECISION.md first. P2R-K remains FAIL.
No production code, synchronization, compiler flag, tolerance or default changed.
These are explicitly legacy coupled compatibility controls, NOT VV reference
validation. Coupled VV remains unsupported/fail-closed.

## Exact experiment

Full independent clone from 26bf84aa2a3acb4edf9accc295a3cbcec7398770;
branch `validation/v3-i0-p2r-reproducibility`. Preparation workspace
`/tmp/mechsys-v3-i0-p2r-repro.iXq6mh/work`, raw sibling `raw-verified`.
Persistent clone target `/home/msys/git/mechsys-v3-i0-p2r-reproducibility`.
Durable raw archive/verification/delivery receipts have a new namespace:
`/home/msys/SIMS/mechsys_v3_i0_p2r_repro_validation/20261017-default-off-audit/`.
Exact final tip and remote/clean verification are in its DELIVERY.json.

All four preceding raw archives were streamed and their 9,944 payload files
verified, followed by all 3,980 live P2R raw files, BEFORE new experiments.
The two exact CUDA executables were copied, not rebuilt:

| Executable | Production headers | SHA256 |
|---|---|---|
| Baseline | bf6616973be1335da1caa7d75f8a34aa0f6c1c22 | 3ca0d0c65992015065c5907f451430b049d94b22bdd6f94e21e6f302129144f7 |
| Candidate | 1bde930295a9852e64a810e02e22b2bba21f98fc | 12b44d4de0e70fc1be203180a3bb369308688c9dab1e653165093689cc3565ca |

The candidate build occurred at preregistration HEAD with dirty headers; every
archived header hash now verifies against implementation 1bde930. It is NOT
represented as a clean-HEAD build. Shared probe SHA256
c49435ccc2306cbddfdbf31852adfa9bdd1a3b5859c15d0717c03578a2001739.
Complete compile/link commands, headers and toolchain versions are in the
manifest and previous archive; CUDA12.6.85/sm86, g++13.3, C++17/O3/FP64,
no fast-math, unchanged CUDA default fmad/ftz behavior.

Command: `<exact executable> large <unique output directory>`, Nproc=1.
Sanitize prior P1_/P2_/P2R_/MECHSYS_ environment keys, then set
P1_MODE=0,P2_MODE=0,P2R_MODE=0,P1_RADIUS=2.2,MECHSYS_EXCHANGE_AUDIT=1.
All three occupancy modes false; absent baseline robust flag is not enabled.
Physical configuration and canonical input SHA256
cce9fe7b636ebcb7968fc9f216b0f342c906daf1298855bee05c33563dc6dee8
are in REPRODUCTION_MANIFEST.json. The original fixture.json byte hash is
also verified against all 28 new executions (20 repeats + eight sanitizers).

GPU: RTX A6000, UUID GPU-8cfc4ebf-51b9-f72f-6d58-98b94dbdf5de, driver595.84.
The user explicitly allowed resident desktop/remote-desktop services after the
strict exclusivity conflict was reported. No other simulation/compute jobs were
present in before/after inventories. Twenty normal runs were serial/interleaved
baseline,candidate,10 repetitions each. Sanitizer runs are separate, instrumented
diagnostics, NOT additional uninstrumented repeats or performance samples.

## Reproduce in a new namespace

Run from this full clone with the prior archives/raw tree available. Replace
NEW_RAW and NEW_ANALYSIS below with unused absolute paths. `prepare.py` and
`run.py` refuse to overwrite experiment namespaces. GPU execution requires
appropriate device access. The desktop exception is explicit, not automatic.

```sh
python3 benchmarks/v3_i0_p2r_repro/prepare.py NEW_RAW
python3 benchmarks/v3_i0_p2r_repro/run.py NEW_RAW --resident-desktop-exception
python3 benchmarks/v3_i0_p2r_repro/run.py NEW_RAW --resident-desktop-exception --sanitizers
python3 benchmarks/v3_i0_p2r_repro/analyze.py NEW_RAW/repeats NEW_ANALYSIS
python3 benchmarks/v3_i0_p2r_repro/evidence.py NEW_RAW NEW_ANALYSIS NEW_REPORT
python3 benchmarks/v3_i0_p2r_repro/trace.py NEW_RAW NEW_REPORT
```

Offline replay needs no GPU: use the preserved raw archive and the final four
commands with existing repeats; `analyze.py` also accepts `--archived` for the
six old diagnostic repeats. Restore both archive payloads and metadata if paths
move; do not substitute newly rebuilt binaries. prepare.py records original
paths, so relocation must explicitly resolve verified archive/raw inputs.

## Evidence map

- REPRODUCTION_MANIFEST.json: exact binaries/source/flags/input, run order,
  process inventories, per-run initial/final and intermediate file hashes.
- ORIGINAL_FAILURE.csv: original strict failed pair, separately preserved.
- BASELINE_REPEATABILITY.csv / CANDIDATE_REPEATABILITY.csv: per-run/snapshot
  file, parsed numerical, particle, history, pair and contribution hashes.
- ALL_PAIRWISE_SNAPSHOTS.csv: 2,090 comparisons, 190 pairs x11 snapshots;
  PAIRWISE_SUMMARY.csv and FIRST_DIVERGENCE.csv include equal pairs too.
- CONTROLLED_INPUT_CHECKS.csv: 380 input-cohort comparisons, stable IDs/order.
- CONTRIBUTION_BITS.csv / INDEPENDENT_SUMS.csv / ORDER_WITNESSES.json:
  93 accepted contributors, exact binary rationals, actual sums and witnesses.
- SANITIZER_INDEPENDENT_SUMS.csv: the instrumented sums checked separately.
- NUMERICAL_CONSEQUENCES.csv / BALANCE_AND_WORK_PHASE_ALIGNED.csv /
  BALANCE_SUMMARY.csv / KINETIC_ENERGY_VARIATION.csv: units/phase-specific
  differences; no full-step energy or long-time conservation acceptance.
- ATOMIC_ACCUMULATION_AUDIT.md / CUDA_SAFETY_AUDIT.md /
  SERIALIZATION_AUDIT.md / COMPATIBILITY_OPTIONS.md: scoped source conclusions.

The first analysis balance table used an explicitly labeled centered-output
work diagnostic. The additive phase-aligned table is canonical for discrete
translation; both original offline versions are retained in raw evidence.
Fresh replay emits both table names with the phase-aligned columns included.
An initial archive verifier rejected the older raw/ prefix/index-last layout;
the corrected verifier then checked all members. No simulation ran before its
successful verification. An early parser syntax error was fixed before analysis;
the correct signed-FP64 self-tests and complete comparisons subsequently passed.
No failed attempt or prior scientific verdict was replaced with a lucky repeat.
