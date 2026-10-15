# P1-P milestone report - polyhedral workstream (2026-10-15)

Branch: perf/p1-poly-diagnostics (isolated clone /home/msys/git/mechsys-p1-poly)
Base: perf/p0-reconciliation @ 826f28d. Commit: ab4c780 (docs) + this report.

## 1. Interaction-count reconciliation (interaction_count_reconciliation.md)
- ListPosPairs is ALPHA-INDEPENDENT (linked-cell size = 2*Beta*MaxDmax), CONFIRMED
  empirically: Alpha=4e-4 probe gives candidate_pair_max=85,748,325, identical to
  Alpha=1e-4 and to the historical value. The P0-L claim that the ListPosPairs match
  pins Alpha=1e-4 is CORRECTED; Alpha=1e-4 remains a valid registered choice, not a
  calibrated one.
- The historical neeint=15,992,853 is unreachable at any Alpha compatible with the
  reported in-window rebuild: at Alpha=4e-4, neeint=4.16M/step (vs 2.49M at 1e-4,
  15.99M historical). The historical interaction counts are mutually inconsistent with
  (in-window rebuild + current code). UNRESOLVED - most plausible causes: different
  measurement state/revision or different counting scope; the historical patch is not
  the preserved artifact, so the exact historical construction code is unrecoverable.
- EQUIVALENT: geometry, final energy (369.835, again reproduced in all 3 runs),
  ListPosPairs. NOT EQUIVALENT: per-step feature counts (5.8-6.4x), CInteracton
  creations (1.9x).

## 2. CUDA transfer audit (cuda_transfer_audit.md)
- Per-step transfers are ONLY 8 B + 16 B control scalars (1 each per step).
- The 87.7 GB total is dominated by ~100 output dumps (~600+ MB full-state D2H each)
  and 5+1 rebuild-state downloads.
- NO transfer qualifies as safely deferrable under the P1 criteria (control, output,
  and reconstruction all depend on them). Per the brief, no transfer experiment was
  implemented; the recommendation is an output-implementation optimization (P4-class)
  and device-resident stepping (P4/S2-class) later.

## 3. Non-diagnostic P-large timing repetitions (P0-R1 completion attempt)
- Clean runs: rep1 220.9 s (226% CPU) [this session]; P0-L rep 225.5 s (214% CPU).
  Physics identical in every run (final kinetic energy 369.835).
- Reps 2-3 (both attempts): 305.8-315.5 s at 156-164% CPU - CONTAMINATED by an
  external MoFEM solver process (99.9% of one core, hours long) and desktop load;
  excluded per the documented criteria (CPU-percent consistency).
- Clean sample size: 2 across sessions (220.9 s and 225.5 s; ~2% session-to-session
  variability). Per-step: ~92-95 ms/step default-off (window ~0.09-0.1 s of 1001
  steps after ~125 s generation).
- Comparison: historical 197 ms/step; P0-L diagnostic 271 ms/step. The default-off
  ~95 ms/step is FASTER than historical because the interaction lists are 6.4x smaller
  (neeint gap) - the profiler-overhead explanation alone was insufficient, as required.
- P0-R1 remains PARTIAL: 3 clean reps were not obtainable under the documented
  contention; not promoted to PASS.

## 4. Safe transfer experiment
NOT implemented - the audit found no safely deferrable per-step transfer (see above).
Recommendation: output-implementation optimization (largest single fixable cost,
~63 GB of output D2H per 1001 steps) and later device-resident stepping; both are
P4-class and outside P1 scope.

## Remaining blockers
- neeint 6.4x gap (blocks kernel-share conclusions and any EE/VF/FV optimization case).
- External CPU contention (blocks 3 clean non-diagnostic reps).
