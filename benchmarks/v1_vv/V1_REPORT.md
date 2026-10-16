# V1 - Velocity-Verlet contact-list validity fix (2026-10-16)

**Follow-up correction:** [v1_reference/README.md](../v1_reference/README.md)
reproduces a stale device-reference defect in this V1 implementation, fixes it,
and tests VV explicitly. It also supersedes the center-only motion-monitoring
claim: both CPU and GPU displacement monitors traverse vertices. The report
below is retained as historical evidence, not a blanket current PASS.

Branch: fix/vv-preforce-neighbor-validity (isolated clone /home/msys/git/mechsys-v1-vv)
Base: perf/p1-evidence-review @ 634fbee. Probes: benchmarks/p1_review/oracle_negative_controls.cu
(updated; built via build_review.py against this clone's toolchain).

## Root cause

In the GPU Velocity-Verlet path the per-iteration order was:

  pReset -> pVerletStep1 (DRIFT) -> pOrientationUpdate -> pForceVV/EE/VF/FV ->
  pFinalizeVelocity/Rotation -> MaxD -> thrust readback -> [rebuild decision]

The force kernels of iteration k evaluate the POST-DRIFT geometry of step k, but the
displacement check and rebuild ran only at the END of iteration k-1 (i.e. before that
drift). A contact formed by the drift is therefore absent from the force-time list.
The end-of-step check is one iteration too late for the VV ordering.

Counterexample (benchmarks/p1_review/oracle_negative_controls.cu, case vv_force_time_drift):
two spheres R=0.1, separation 0.24, v=+/-300, dt=1e-4, Alpha=0.001. Candidate cutoff
0.202 > 0.24, so the initial list has no pair; the drift reduces the separation to 0.18
(overlap 0.02) and the first force evaluation runs with an empty feature list.
Baseline evidence: hardened oracle reports rejected=1 missing=1 at iter=1 with records=0
(steps_since_rebuild=1); with --uncaught-missing the probe exits 1 with
'Fatal: Candidate oracle failed: missing=1'.

## Side-effect audit (why the naive fix is wrong)

Calling the existing UpdateContactsDevice at the pre-force stage would:
- re-upload particle dynamic state from the host (state-pack block), and
- upload A/Wdot from the host (updateState=true) - stale in GPU mode, clobbering the
device acceleration written by the last FinalizeVelocity, and then
- call RecomputeAccelerations against the just-reset force accumulators (pReset),
zeroing the accelerations -> the next VerletStep1 would lose the force contribution.
The brief's warning is confirmed by source inspection: FinalizeVelocity writes A[ic]=a_new
(lib/dem/dem.cuh); VerletStep1 consumes A (v_half = v + 0.5*dt*a_prev).

## Corrected sequence (lib/dem/domain.h, GPU Velocity-Verlet branch)

  pReset -> pVerletStep1 (drift) -> pOrientationUpdate ->
  MaxD (displacement vs the reference of the current list) ->
  readback -> if (D_max >= Alpha) UpdateContactsDevicePreForce() ->
  OracleCheck (diagnostic) -> pForceVV/EE/VF/FV -> pFinalizeVelocity/Rotation

The end-of-iteration displacement check is skipped for the VV path (guarded by
!UseVelocityVerlet) and retained unchanged for the position-Verlet/leapfrog path, whose
order is self-consistent (its forces use the list checked after the previous Translate).
Bookkeeping (demaux.iter++, demaux.Time += Dt, numup/iter_t/iter_b) is preserved.

The rebuild criterion uses the same convention as the candidate cutoff:
D_max = max over particles of the displacement since the last valid list construction;
rebuild if D_max >= Alpha. For spheres the monitored quantity is the center (vertex)
displacement, matching the single-vertex particle geometry. Polyhedral rotation-driven
feature motion is NOT covered by a center-displacement criterion and remains a known
limitation of the baseline monitoring (unchanged by this patch; flagged for P1-P follow-up).

## Narrow rebuild (UpdateContactsDevicePreForce)

New method: ResetMaxD (device reference := current verts) -> DnLoadDevice(force=true)
(current geometry + contact histories to the host) -> host box update -> UpdateContacts()
(CPU reconstruction from post-drift geometry) -> UpLoadDevice(Nproc,false,false)
(interaction structures + preserved histories only; first=false keeps particles/verts,
updateState=false keeps device A/Wdot) -> ResetMaxD (reference := current verts).
Skipped relative to UpdateContactsDevice: the particle state re-upload, the A/Wdot upload,
and RecomputeAccelerations. Contact histories are preserved: surviving CInteractonSphere
objects carry Fdvv/Fdr/PrevDelta across the DnLoadDevice(force=true)/UpLoadDevice round
trip; new pairs start fresh; departed pairs are erased by the stale sweep.

## Validation

- V1-A: baseline defect reproduced (see counterexample; exit 1 with --uncaught-missing).
- V1-D: corrected probe exits 0; vv_force_time_drift rejected=0 missing=0; the contact
  record exists in bDynInteractonsVV; the force kernel evaluated Fn=(79382.2,0,0) N
  (repulsive, along the contact normal); particle forces F1=(-79382.2,0,0),
  F2=(+79382.2,0,0) satisfy action-reaction exactly.
- V1-E: all five registered oracle scenarios pass on the corrected binary with
  IDENTICAL reference-contact totals (830,774 / 21,589 / 367,340 / 4,197,770 / 3,644),
  zero missing/duplicate/bad-periodicity.
- V1-F: numerical regression on oracle_A_dense (valid-list case): corrected vs baseline
  bitwise-identical at printed precision (elastic 3.06524e-06, kinetic 0.00363438,
  total 0.00363816) with identical rebuild cadence (3970 avg iterations between updates);
  the S-legacy-small cadence differs by at most one rebuild in the shear stage (373 vs
  376 avg iterations) from the check-point relocation - a scheduling shift, not a
  contact-set difference (the oracle confirms completeness in both).
- V1-G: tlbmdem_cu_02 (coupled LBM-DEM) compiles/links at sm_86 with the shared headers;
  the CPU (non-CUDA) Velocity-Verlet path was audited and has the SAME defect class -
  its displacement check was commented out entirely; a symmetric pre-force check was
  added (host-side, using MaxDisplacement() vs Alpha and UpdateContacts()).
- V1-H: see performance section (appended).

## Remaining limitations
- Polyhedral rotation-driven feature displacement is still monitored by center
  displacement only (baseline behavior; flagged, not changed here).
- The coupled LBM-DEM runtime gate and history-value oracle remain outstanding.
- The CPU (non-CUDA) VV fix is validated by inspection + shared-code compilation only;
  a CPU-runtime oracle run is future work.
