# VV reference and evolving sphere-history gate — 2026-10-16

VV (`UseVelocityVerlet=true`) is the reference integration mode for new work,
by the user's explicit decision. `AGENTS.md` records this policy; legacy results
remain separately labeled controls. The backwards-compatible library constructor
default has not changed. This milestone extends correctness coverage, not speed.

Worktree: `/home/msys/git/mechsys-v1-reference`; topic
`validation/vv-reference-history`, based on verified
`517da81fac3a997b088558bf23d958994b55f0de`. Oracle/policy commit `e467fda`;
rolling transfer correction `8d878da7269440a72a1f37ca8ba68b9d84d9ae49`.
The original source worktree and all other experiment branches are preserved.
The requested VV note is also added to `/home/msys/mechsys/AGENTS.md`; no original
simulation source or Git state is changed by this session.

## Reproduced transfer defect and bounded fix

Both CPU sphere laws accumulate `CInteractonSphere::Fdr` as a **force**:
`Fdr += beta * Kt * Vr * dt` for the linear law. GPU `Fr` is also a force.
The linear-law upload nevertheless multiplies Fdr by `Kt*beta`, and download
divides by that factor. A device round trip can therefore preserve a seeded
device value yet bootstrap it incorrectly from a real CPU force evaluation.
This is why the prior seeded-value preservation probe was insufficient.

Independent first-force check: R=0.1, opposite angular velocities +/-1 rad/s,
normal along x, beta=0.3, Kt=20, dt=2e-5 gives Vr_y=0.1 and
Fr_y=6*0.1*2e-5=**1.2e-5 N**. The previous source uploads **7.2e-5 N**.
The identical, full-precision oracle fails against that source with exit 1.
The negative control is retained, not relabeled as a passing historical test.

The fix transfers rolling force directly in both directions, for both laws;
the Hertz branch already did so. It does not change force/history recurrence,
friction limits, rolling caps, integration ordering or rebuild control. It also
removes the obsolete linear-law divide-by-Kt conversion. The misleading Fdr
field comment is corrected. This is a CPU/GPU state-units correction, not a
new contact model. Its linear transfer scope is shared by VV and legacy GPU
integration; legacy timing/trajectory data remain historical, not revalidated.

## Stepwise acceptance evidence

`history_probe.cu` runs **actual VV Solve calls**, with the standard reduction
and one CPU thread, for 1,000 steps each (dt=2e-5, final time 0.02).
Two spheres, FP64, Kn=1000, Kt=20, zero damping, Mu=0.4, beta=0.3, eta=0.2;
nonzero tangential and opposite angular velocities. Three fixtures each run
with Alpha=0.001 and Alpha=1, independently on CPU and GPU:

| Fixture | Coverage |
|---|---|
| Persistent friction/rolling contact | Applied compression +/-0.75 N; contact survives all steps; 200 rebuilds at Alpha=0.001 versus none at Alpha=1 |
| Sliding and separation | Initial tangential velocities +/-5; contact separates at step 75; nonzero frictional work |
| Separation and recontact | Initial outward velocities +/-0.3, attractive forces +/-0.2 N; separates at step 67 and recontacts at step 911 |

All **six CPU/GPU comparisons**, 1,001 snapshots each, pass. The persistent
fixture's frequent-rebuild/no-rebuild controls also pass for each backend.
Compared every step: positions, velocities, angular velocities, quaternions,
particle forces and actual device torques, physical tag-pair identity,
tangential and rolling histories, previous overlap/contact flag. Per-step
elastic energy and viscous/frictional-work outputs are compared after step 0.
Tolerance is `abs(error) <= 1e-10 + 1e-9 * max(abs(left),abs(right))`, appropriate
for these short FP64 two-particle controls without chaotic amplification;
observed maximum particle-force error is 2.501e-13 N and maximum rolling-history
error is 1.735e-18 N. Every host/device rolling-state comparison passes.
Particle action-reaction passes with equal/opposite applied forces.

All 6,000 force-time GPU candidate-oracle checks pass, with 2,460 reference
contacts total and zero missing/duplicate/periodicity errors. This does not
replace the existing five-case boundary/periodicity suite, which is rerun
separately on the new binary with `--vv`.

That rerun passes all five cases: **56,405 checks / 5,419,450 reference contacts**,
zero missing pairs, duplicates or periodic-image errors, with integrator markers
verified. These totals match the prior actual-VV dataset; no timing inference is made.

Two diagnostic limits are explicit, not suppressed dynamics failures:

- `DnLoadDevice` does not refresh host `Particle::T` from `ParticleCU::T`.
  The oracle records the stale host field but compares actual device torque.
  Correct angular trajectories and device torques agree with CPU. No production
  output-semantics change is included in this patch.
- GPU frame-zero common-contact accumulators are zero after upload, while CPU
  reports its bootstrap evaluation. Energy/work comparison starts after the
  first device force; initial rolling history still has the independent oracle.

This closes the **controlled linear sphere** evolving-history gate across
repeated rebuild, sliding, separation and recontact only. It does not establish
full mechanical energy-work balance, nonzero damping parity, Hertz history
coverage, polyhedral feature identity, reordered storage or restart correctness.
Rolling retention during separation remains baseline semantics, not redesigned.

## Other gates and next bounded task

CPU, GPU and persistent-reduction reference-reset/analytic-contact regressions
are rerun successfully. The coupled `tlbmdem_cu_02` binary compiles and links
against the new source, but **coupled runtime is not validated**. The existing
coupled default is large and is not launched as an unattended smoke test.

Source audit of restart support finds the interaction serialization block in
`Domain::Save` commented out, and `Load` restores particles, not the sphere
history map. Existing Save/Load must not be called a history-preserving VV
checkpoint. This is a baseline limitation, not caused or repaired here.
The next bounded task is to characterize the restart contract with a minimal
save/load counterexample before designing a versioned history-safe checkpoint;
also close the relevant coupled runtime gate. Keep persistent reduction
default-off. No delayed/adaptive rebuild, GPU reconstruction, new precision,
production promotion or full-simulation speed claim is included.

## Reproduce and inspect evidence

```sh
python3 benchmarks/v1_reference/build_probe.py --reference-build /tmp/mechsys_v1_build --cuda /usr/local/cuda-12.6 --targets history_cpu history_cuda reference_cpu reference_cuda test_cu_04 coupled_cuda --output /tmp/vv-history-build
python3 benchmarks/v1_reference/check_history.py --build /tmp/vv-history-build --output /tmp/vv-history-checks
/tmp/vv-history-build/reference_cpu
/tmp/vv-history-build/reference_cuda
/tmp/vv-history-build/reference_cuda --persistent
python3 benchmarks/p1_review/run_registered_oracles.py --binary /tmp/vv-history-build/test_cu_04 --inputs /home/msys/SIMS/mechsys_p0_baseline/20261015-p1/oracle --output /tmp/vv-history-registered --vv
# Negative control: use a preserved checkout at 517da81 (or e467fda) for headers.
python3 benchmarks/v1_reference/build_probe.py --reference-build /tmp/mechsys_v1_build --cuda /usr/local/cuda-12.6 --source-root /path/to/unfixed-checkout --targets history_cpu history_cuda --output /tmp/vv-history-unfixed
python3 benchmarks/v1_reference/check_history.py --build /tmp/vv-history-unfixed --output /tmp/vv-history-negative --scenarios 0
# The preceding negative-control command must fail with exit 1.
```

Current raw evidence, including the initial sandbox device-access failure,
intermediate stale-host-torque diagnostic, negative control, full-precision
snapshots and final logs: `/tmp/mechsys-vv-history.nPkO2A/` (temporary).
Compact acceptance/failure JSON, manifests and reference logs are retained under
`history_results/` in Git. CUDA 12.6.85, GCC 13.3, FP64, explicit sm_86;
RTX A6000 UUID GPU-8cfc4ebf-51b9-f72f-6d58-98b94dbdf5de, driver 595.84.
Diagnostic output/readback makes these runs unsuitable as performance samples.
