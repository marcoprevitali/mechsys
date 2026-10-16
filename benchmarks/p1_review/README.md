# P1 evidence review and oracle hardening — 2026-10-16

The P1 implementations exist, and the reported remote SHAs were verified with
`git ls-remote`: spheres `9176b728a2c0397086d68e4cf8d46c10c2ee823b`,
polyhedra `eef594acf45edf4ed894951e29c633e924a4f34f`.
This review branches from the sphere commit; it does not merge or modify either
P1 workstream clone or the concurrently owned `mechsys-gpu-opt` clone.
Oracle hardening and validation commit: `05a1be9`.

## Corrections to the supplied handoff

`audit_evidence.py` reads the preserved P1 logs, hashes each source, and writes
`reanalysis.json`. Historical reports are retained; the following findings
supersede their specified claims.

| Quantity | Handoff | Recomputed from raw logs |
|---|---|---|
| S-small baseline / persistent mean wall | 23.468 / 22.434 s | **23.668 / 22.434 s** |
| S-small ratio of means | 1.046 | **1.055006**, or 5.2138% lower runtime |
| S-small paired wall savings | mixed stated means | 1.280, 1.240, 0.980, 1.450, 1.220 s; mean 1.234 s |
| S-small measured Solve timers | 13.09 / 12.71 s | 13.091485 / 12.714169 s; ratio 1.029677 |
| S-large wall means | 232.06 / 230.90 s | 232.058 / 230.902 s; ratio 1.005006, mixed signs |
| Original oracle checks | report 23,406; scenario table also inconsistent | **56,405** |
| Original reference contacts | 5,421,117 | 5,421,117; zero logged misses and host-map duplicates |
| Bitwise energy equivalence | broad claim | **Not established**; all 10 benchmark pairs differ at printed energy precision |

The S-small mean Solve-timer saving is 0.377317 s. The other 0.856683 s of the
1.234 s process-wall saving is outside those timers. That component must not all
be attributed to the displacement reduction. No new speed measurement was made
here. The five baseline repetitions themselves also have different energies;
the cross-variant differences alone do not establish a contact-law defect in
these long many-body runs. An appropriate FP64 force/history oracle remains
required for numerical promotion. Equal `%g` output in the short validation
logs does not establish bitwise state equality.

Recomputed original scenario totals:

| Scenario | Checks | Reference contacts |
|---|---:|---:|
| A dense | 11,001 | 830,774 |
| B low density | 11,001 | 21,589 |
| C high acceleration | 10,401 | 367,340 |
| D shear | 12,001 | 4,197,770 |
| E periodic squeeze | 12,001 | 3,644 |

Polyhedral P1 documents correct the earlier Alpha-calibration inference:
ListPosPairs does not determine Alpha at a fixed state. The feature-count gap
remains unresolved. Equal printed energy and geometry counts are useful checks,
but do not uniquely identify a physical state or prove the absence of missed
contacts. The available probes do not establish impossibility over every
admissible Alpha and historical measurement scope. Retain `LEGACY_EQUIVALENT`
and the unresolved construction/counting definition. The transfer audit found
no safely deferrable per-step state copy; the old proposal to eliminate large
per-step state transfers is superseded. P0-R1 still has only two reported clean
P-large timings across sessions. CPU-percent differences alone are not a proof
of contention; retain the exclusion history without strengthening its cause.

## Oracle defects reproduced, then fixed

The original oracle checks `PairtoCInt`, not the uploaded force-feature arrays.
The original `oracle_negative_controls.log` records these false acceptances:

- Delete the sole GPU VV record, leaving the host pair: reported missing = 0.
- Duplicate the GPU VV record: reported duplicates = 0.
- Place spheres across a z-periodic boundary: reported reference contacts = 0.
- Remove the host pair: reported missing = 1, but execution continues.

The original check also precedes the Velocity-Verlet drift and uses an infinite
plane approximation instead of the finite face used by the force kernel.

The default-off `MECHSYS_CANDIDATE_ORACLE=1` implementation now reads the actual
device control, particle, common-contact and VV/VF/FV arrays. It checks feature
identities and extents, enumerates all physical pairs independently of neighbor
construction, uses x/y/z minimum images and finite-face distances, counts actual
uploaded duplicates and incorrect `BothFree` periodicity, and raises `Fatal` on
failure. The hook is immediately before force evaluation in each integrator,
after the Velocity-Verlet drift/rotation. It fails explicitly for unsupported
polyhedral, custom-force or sheared-periodic paths. This is still a sphere/plane
candidate-record gate, not a force/history/restart or coupled-solver oracle.

Validation on RTX A6000, FP64 (`sizeof(real)=8`), explicit `sm_86`:

- Missing and duplicated uploaded records and incorrect periodicity are rejected.
- The check is independent of the host map; z-periodic overlap is found; a sphere
  outside a finite wall footprint is correctly excluded.
- Uncaught failure exits with status **1** through `MECHSYS_CATCH`.
- All five registered baseline scenarios pass with **56,405 checks**, **5,421,117
  reference contacts**, zero missing records, duplicates or periodicity errors.
  These diagnostic reruns use Nproc=2; input hashes are unchanged.
- The existing persistent-reduction variant passes A-dense: 11,001 checks,
  830,774 references, zero errors. No claim that all five variant scenarios were rerun.
- Direct persistent-reduction checks pass **54/54** FP64 cases (nine lengths,
  six block sizes, finite non-negative inputs, maximum compared bitwise).
  The existing kernel performs a global atomic per thread; the earlier description
  of a block reduction does not match its implementation.
- DEM CUDA probe/driver and `tlbmdem_cu_02` compile/link builds pass at `sm_86`;
  a CPU driver header syntax check also passes.
  Coupled LBM-DEM runtime, restart and history-value gates remain outstanding.

## New baseline blocker: Velocity-Verlet force-time list validity

The new negative control uses two free spheres: R=0.1, initial separation 0.24,
velocities +300/-300, dt=1e-4, Alpha=0.001. The initial list has no pair because
0.24 > 0.2+2*Alpha. The VV drift reduces separation to 0.18, so the next force
evaluation has overlap 0.02 while its feature list is empty. Rebuilding only
after force evaluation and integration is too late. The original hook checks
the pre-drift separation and can report PASS. The hardened hook catches the
missing pair before force evaluation (`vv_force_time_drift`, missing=1).

This demonstrates a baseline list-validity defect under fast motion, not a
failure introduced by persistent reduction or delayed reconstruction. The test
timestep is below the driver's printed suggested timestep (~0.00205); a contact
stability timestep alone therefore does not enforce Verlet-list validity.
No force law, integrator or rebuild scheduling was changed by this patch.
Delayed rebuild/control work remains blocked. Next bounded task: correct or
enforce the **pre-force displacement/list-validity contract** in a separate
patch, preserving force/history semantics, and pass this adversarial control.

## Reproduce and locate evidence

Raw input/evidence root:
`/home/msys/SIMS/mechsys_p0_baseline/20261015-p1/`.
Review raw build/probe/scenario artifacts:
`/tmp/mechsys-p1-review.2rptlG/evidence/` (temporary; compact logs, hashes and
results are committed under `results/`). Existing raw artifacts were read only;
scenario inputs were copied to isolated output directories.

From the review repository:

```sh
python3 benchmarks/p1_review/audit_evidence.py /home/msys/SIMS/mechsys_p0_baseline/20261015-p1 --output reanalysis.json
python3 benchmarks/p1_review/build_review.py --reference-build /tmp/mechsys_p1_sphere_build --cuda /usr/local/cuda-12.6 --sm 86 --output /tmp/mechsys-p1-review-build
/tmp/mechsys-p1-review-build/oracle_negative_controls_hardened
# Expected exit status 1:
/tmp/mechsys-p1-review-build/oracle_negative_controls_hardened --uncaught-missing
python3 benchmarks/p1_review/run_registered_oracles.py --binary /tmp/mechsys-p1-review-build/test_cu_04 --inputs /home/msys/SIMS/mechsys_p0_baseline/20261015-p1/oracle --output /tmp/mechsys-p1-reviewed-baseline
python3 benchmarks/p1_review/run_registered_oracles.py --binary /tmp/mechsys-p1-review-build/test_cu_04 --inputs /home/msys/SIMS/mechsys_p0_baseline/20261015-p1/oracle --output /tmp/mechsys-p1-reviewed-persistent --names A_dense --persistent
```

The runner refuses existing output directories and records return status,
input/binary/log hashes, commands and counters. Diagnostic runtimes are not
performance samples. The retained optimization stays default-off and unmerged.
