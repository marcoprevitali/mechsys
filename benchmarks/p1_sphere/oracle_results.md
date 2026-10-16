# P1-S candidate-completeness oracle - results (2026-10-15)

**2026-10-16 correction:** [the evidence review](../p1_review/README.md) gives the
raw check counts and demonstrates why these original host-map checks do not
establish uploaded-feature completeness, duplicate-free force evaluation, z
periodicity or VV post-drift coverage. The stronger implementation has passed
the five registered cases; its adversarial VV test exposes a baseline defect.

Implementation: MECHSYS_CANDIDATE_ORACLE=1 (default-off) in lib/dem/domain.h.
At every step, immediately before the contact-force kernels (after any rebuild decision),
the oracle copies current device positions (DynParticleCU.x) and device plane verts
(VertsCU), enumerates ALL particle pairs brute-force on the host, applies the SAME
criterion as the force kernels (sphere-sphere: delta = R_i + R_j - min-image distance > 0
with image enumeration on periodic axes for free pairs; sphere-plane: |perpendicular
distance to the plane through its device vertices| < R_sphere + R_plane), and verifies
each contacting pair is represented in PairtoCInt (the live candidate/interaction
records that feed the GPU kernels). Read-only with respect to the simulation state.
O(N^2) -> restricted to small registered scenarios.

Counters per check: N_reference_contacts (pairs with delta>0 under any tested image),
N_candidate_contacts (reference pairs found in PairtoCInt), N_missing_contacts,
N_duplicate_contacts (records beyond the first for the same unordered pair),
N_incorrect_image_contacts (not separable on the host: record Branch reflects the
previous step; documented limitation - reported as 0 by definition in this version).

## Scenarios (registered inputs, SHA256SUMS in oracle/)

| Scenario | Config | Checks | Reference contacts | Missing | Duplicates | Verdict |
|---|---|---|---|---|---|---|
| A dense | 1.5^3 box, frac 0.99, p0=5, 1001+10001 steps | 11,001 | 830,774 | 0 | 0 | PASS |
| B low-density | same box, frac 0.12 | 11,001 | 21,589 | 0 | 0 | PASS |
| C high-acceleration | p0=100, 201+201 steps | 402 | 367,340 | 0 | 0 | PASS |
| D shear/moving walls | 2.0^3, p0=10, 1001+10001 steps | 11,002 | 4,197,770 | 0 | 0 | PASS |
| E periodic squeeze | 0.6x0.6x1.0, p0=50 | 1002 | 3,644 | 0 | 0 | PASS |

Acceptance: N_missing_contacts = 0 and N_duplicate_contacts = 0 in all scenarios: PASS.

Coverage notes:
- Compression stage covers acceleration, near-threshold contact appearance, repeated
  contact creation/separation, and moving walls (planes -4/-5, moving in stage 2 of D).
- Periodic images are exercised on every near-boundary pair (x,y periodic); scenario E
  squeezes a dense packing in a small periodic box. A single particle crossing the
  periodic boundary over a full box length was not produced (no gravity-driven drift in
  test_cu_04); image handling is nevertheless checked on every adjacent-image pair.
- Contact-history persistence across rebuilds is checked indirectly: the same
  CInteracton objects persist in PairtoCInt across rebuilds (stale sweep only removes
  departed pairs), so a persistently contacting pair keeps its FrictionMap; full
  history-value verification remains a V0.3 item.
- The oracle state is captured before the force kernels of the same step, so a delayed
  rebuild decision (if introduced later) would be detected by the same hook.
