# Occupancy arithmetic deliberately unmodified

SphereCube in lib/dem/special_functions.h and cudaSphereCube in
lib/lbmdem/lbmdem.cuh have an independent edge-group early-continue defect:
rejecting a top edge can skip bottom/vertical edges in that same j iteration.
The preserved V3-I0 strict failures are evidence, not a correct twelve-edge model.

P1 does not edit either file or any gamma/B/Omega/collision/force/torque formula.
Independent enumeration retains three references: exact sphere/AABB intersection
(boolean, not exact volume), mathematical twelve-edge coverage, and the actual
legacy control-flow proxy. Accepted-cell gates use the last one. Candidate
gates additionally require every mathematical-positive and geometrically
intersecting cell, so a proxy zero cannot conceal an eligibility omission.

Changing eligibility can expose this existing proxy defect on additional cells;
that is reported, not repaired or treated as a new model. No exact-volume
occupancy was substituted. The next bounded proposal is a separate review and
correction of this edge-loop control flow, with new independent validation.
No automatic Scheme A, restart or performance work follows P1.
