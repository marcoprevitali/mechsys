# Candidate and imprint acceptance

Registered corrected cases: 22 identical initial configurations on CPU/CUDA,
88 entry-imprint snapshots and 144 coverage rows including actual pre/post
rebuild snapshots. All entry and registered pre/post rebuild candidate omissions
are zero. Every geometric intersection and mathematical-positive edge pair is
also present in the entry candidate map, stronger than legacy-positive coverage.
All legacy-positive cells reach imprint on both backends; accepted sets match
exactly. Zero duplicate particle/cell records, extra accepted cells, bad image
levers or independent geometric-bound counterexamples.

Centered sphere: legacy-proxy reference 27. Before correction candidates 27 on
both, accepted CPU 7 / CUDA 27. Corrected Alpha=.4: 81 conservative candidates,
27 accepted on both. Small Alpha=.0001: old seven candidates omit 20 positive
cells, corrected 33 candidates contain all 27, including after actual rebuild.
False positives are deliberate and their inactive proxy values are not contacts.

Original base source attribution: lib/lbmdem/Domain.h:350 CPU Dmax rejection;
ResetParCell:511 broad phase and :562 vertex distance <R+2Alpha; wrapped local
window is a separate potential duplicate source. Corrected sphere mode bypasses
those sphere candidate filters with a unique-cell conservative bound; it does
not change non-sphere geometry code. Geometry representation is checked, not
inferred from a name or a Dmax/2 assumption.

Boundary geometry still has 28 mathematical-positive cells but only 24
legacy-control-flow-positive cells. Corrected CPU/CUDA both accept 24; the other
four are proxy-zero, NOT candidate/imprint false negatives. Partial case both
accept 28 legacy-positive cells against mathematical 29. Neither discrepancy is
hidden by the new counters. See EDGE_PROXY_OPEN_ISSUE.md and raw independent
proxy-failure results. No arithmetic change to SphereCube is accepted in P1.

Small R=.2 offset sphere, large R=2.2, wide Alpha=6, radius +/-1e-7 around
sqrt(.5), zero-edge R=.05 and an out-of-domain fixed sphere with no candidates
are all included. Exact/twelve-edge/legacy-control-flow references stay separate.
This is bounded validation, not proof of arbitrary mutable geometry/app callbacks.
