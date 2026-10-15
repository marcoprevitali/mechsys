# P1-S milestone report - sphere workstream (2026-10-15)

Branch: perf/p1-sphere-control (isolated clone /home/msys/git/mechsys-p1-sphere)
Base: perf/p0-reconciliation @ 826f28d
Commits: 5d1cdf9 (oracle), 3aea5e7 (persistent reduction), + docs

## Deliverables
1. Candidate-completeness oracle (MECHSYS_CANDIDATE_ORACLE=1, default-off, O(N^2) host
   check at force-evaluation time using device positions): 5 scenarios, 23,406 checks,
   5,421,117 reference contacts, N_missing=0, N_duplicate=0 everywhere. PASS.
2. Displacement-reduction audit: per-step thrust::max_element allocates temporaries
   (2 cudaMalloc/step confirmed by elimination); the readback sync is structural while
   reconstruction is host-side.
3. Persistent-reduction experiment (MECHSYS_PERSISTENT_REDUCTION=1, default-off):
   cudaMalloc 22,023 -> 22 per scenario; energies bitwise identical; rebuild cadence
   identical.
4. Performance (complete-solve wall, 5 interleaved pairs):
   - S-legacy-small: 23.468 -> 22.434 s (speedup 1.046, ranges non-overlapping,
     paired p<0.001)
   - S-legacy-large: see displacement_audit.md (appended)
5. Recommendation: keep the optimization default-off for now; fold into the future
   device-resident-control experiment after V0.1-related gates; the oracle hook is the
   acceptance tool for any delayed-rebuild variant.

## Remaining blockers / next steps
- Delayed rebuild (run-ahead) remains BLOCKED pending the displacement-validity proof
  and oracle runs at high dynamics.
- S-large full sweep timing subject to external CPU contention (MoFEM replica job);
  per-rep CPU-percent validation applied.
