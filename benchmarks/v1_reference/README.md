# V1 follow-up: completed-rebuild reference refresh — 2026-10-16

Branch `fix/vv-reference-reset`, based on verified V1 commit
`7f99c4cef62686110b4bd7f85926e07228c8e86c`. Work is isolated from the original
checkout, V1 clone, and all P1 clones. Persistent clone:
`/home/msys/git/mechsys-v1-reference`.
Implementation and validation commit: `c57c495`.

## Defect and correction

V1 moves GPU VV reconstruction to the correct pre-force point, but the new
`UpdateContactsDevicePreForce()` calls `ResetMaxD` to refresh the list reference.
That kernel wraps particles and resets **only wrapped vertices**. Non-wrapped
particles retain their accumulated displacement intentionally. Because the new
path uses `UpLoadDevice(first=false, updateState=false)`, it never copies current
vertices into `bVertsoCU`. Once Alpha is reached, every following step rebuilds
against the original reference, until an unrelated wrap or first upload occurs.

Controlled reproduction: two separated, co-moving spheres, v=(100,0,0),
dt=1e-4, Alpha=0.025, ten integration steps. Rebuilds occur at zero-based
iterations 2,3,4,5,6,7,8,9 in V1. Final x=0.1, reference x=0, residual=0.1.
An ordinary regression assertion exits **1** on the unpatched V1 commit; the
`--expect-stale` mode archives the known failure while continuing other checks.

The correction retains the initial wrapping and interaction-only upload. After
that upload succeeds, it copies current vertices to **every** device reference
and zeros the displacement cache, on the same stream. It does not upload
particle state or accelerations and does not advance tangential/rolling history.
The corrected ten-step sequence rebuilds only at iterations **2,5,8**: three
rebuilds, final reference x=0.09, residual=0.01. This removes five redundant
reconstructions in this diagnostic; it is not a complete-simulation speed claim.

The side-effect audit also found unassigned vector fields in the automatic
`ComInteractonCU CIcu` uploaded by `UpLoadDevice`. V1 rebuilds after `pReset`, so
the reset of the previous array cannot initialize fresh records. Value-initializing
`CIcu` makes the new accumulators deterministic and zero before force evaluation.
This is a source-verified uninitialized-data hazard; the chosen baseline probe
happened to observe zeros and does not demonstrate an accumulator runtime failure.

## Numerical and implementation evidence

The final probe verifies:

- A completed rebuild has exactly zero reference residual and a zero displacement
  cache. Repeating the refresh is idempotent.
- Particle dynamic state and device A/Wdot are bitwise unchanged across the narrow
  rebuild. A surviving contact retains its identity and seeded tangential force,
  rolling state, previous overlap and contact flag exactly in this linear-law fixture.
  This does not claim a complete evolving-history/restart oracle.
- The repeated-step test passes on GPU with both standard and persistent reduction,
  and on CPU. All yield reference x=0.09 and residual 0.01 after ten steps.
- CPU and GPU fast-contact cases use Kn=1000, zero damping, R=0.1, separation 0.24,
  v=+300/-300, dt=1e-4, Alpha=0.001. Post-drift separation 0.18 gives overlap 0.02
  and analytic force 20 N. Observed particle forces are -20.000000000000018 and
  +20.000000000000018 N, action-reaction exactly zero. GPU common-contact normal
  force is also 20.000000000000018 N. Assertion tolerance is 1e-10 N.
- A pure rotation of eight cube vertices, with no center motion, produces GPU
  `MaxD`=0.070681219018733893, matching sqrt(2)*sin(0.05) within 1e-14.
  **The V1 claim that displacement monitoring is center-only is superseded**:
  GPU `MaxD` and CPU `Particle::MaxDisplacement` both traverse all vertices.
  A full polyhedral feature-completeness oracle remains outstanding.
- The final CPU and GPU drivers compile and run; final coupled `tlbmdem_cu_02`
  compiles and links at `sm_86`. Coupled runtime validation remains outstanding.

FP64 only; GCC/G++ 13.3.0; CUDA 12.6.85; explicit `sm_86` verified by `cuobjdump`;
RTX A6000 UUID `GPU-8cfc4ebf-51b9-f72f-6d58-98b94dbdf5de`. Exact commands,
input/log/executable hashes and source/header hashes are in `results/` manifests.

## Verify the actual integrator, not only the workload name

The original `test_cu_04.cu` never selects VV, while the Domain default is false.
Consequently the V1 five-scenario results and legacy timing repetitions exercise
position-Verlet unless an independently changed executable/source is documented.
Those runs are valid legacy regression evidence, not tests of the new VV path.
The V1-H conclusion of no VV overhead is **not established** by those timings.

The harness now accepts a final optional argument:
`test_cu_04 <input_without_suffix> <Nproc> <dthoot> <qin> <VV=0|1>`.
Existing commands retain their behavior. The optional path prints
`DEM_BENCHMARK_INTEGRATOR velocity_verlet=1`, which the runner verifies.

Final five registered cases, unchanged input hashes, Nproc=2, oracle enabled,
VV explicitly selected, persistent reduction disabled:

| Case | Checks | Reference contacts | Missing / duplicates / bad periodicity |
|---|---:|---:|---|
| A dense | 11,001 | 830,486 | 0 / 0 / 0 |
| B low density | 11,001 | 21,566 | 0 / 0 / 0 |
| C high acceleration | 10,401 | 367,394 | 0 / 0 / 0 |
| D shear | 12,001 | 4,196,361 | 0 / 0 / 0 |
| E periodic squeeze | 12,001 | 3,643 | 0 / 0 / 0 |
| Total | **56,405** | **5,419,450** | **0 / 0 / 0** |

These VV totals legitimately differ from the legacy trajectory's 5,421,117;
equality to a different integrator was not an acceptance condition. The runner
requires complete reference coverage, no duplicate uploaded features, correct
periodicity and successful process exit. Diagnostic elapsed times are excluded
from performance evidence. No adaptive skin, delayed rebuild, GPU reconstruction
or production precision change is included.

## Reproduction and handoff

```sh
python3 benchmarks/v1_reference/build_probe.py --reference-build /tmp/mechsys_v1_build --cuda /usr/local/cuda-12.6 --output /tmp/v1-reference-build
/tmp/v1-reference-build/reference_cpu
/tmp/v1-reference-build/reference_cuda
/tmp/v1-reference-build/reference_cuda --persistent
python3 benchmarks/v1_reference/build_probe.py --reference-build /tmp/mechsys_v1_build --cuda /usr/local/cuda-12.6 --source-root /home/msys/git/mechsys-v1-vv --targets reference_cuda --output /tmp/v1-reference-original
/tmp/v1-reference-original/reference_cuda --expect-stale
# Without --expect-stale, the preceding unpatched probe must exit 1.
python3 benchmarks/p1_review/run_registered_oracles.py --binary /tmp/v1-reference-build/test_cu_04 --inputs /home/msys/SIMS/mechsys_p0_baseline/20261015-p1/oracle --output /tmp/v1-reference-vv-oracles --vv
python3 benchmarks/v1_reference/build_probe.py --reference-build /tmp/mechsys_v1_build --cuda /usr/local/cuda-12.6 --targets coupled_cuda --output /tmp/v1-reference-coupled
```

Raw baseline, intermediate and final evidence is preserved under
`/tmp/mechsys-v1-followup.0hJdwE/evidence/` (temporary); compact logs, build manifests
and final scenario hashes are committed under `results/`. Registered input files
remain in `/home/msys/SIMS/mechsys_p0_baseline/20261015-p1/oracle/` and were copied
for each run. The original V1 counterexample is retained and now has CPU runtime
coverage for the controlled linear-law case.

Next bounded task: extend stepwise FP64 force/history validation through repeated
rebuilds, separation/recontact and restart, and close the relevant coupled runtime
gate. Obtain an uncontaminated, explicitly selected VV complete-solve baseline
before performance promotion. Delayed reconstruction and adaptive allowances still
need their own displacement-validity proof; these tests do not authorize run-ahead.
