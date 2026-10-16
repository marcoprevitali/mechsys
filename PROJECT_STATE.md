# Persistent project state — MechSys GPU optimization

Read AGENTS.md, then PROJECT_STATUS.md for the full scientific gate/provenance
record. This file is a concise re-entry point, not a replacement for that record.

## Current objective and boundary

V3-I0 observational legacy fluid-exchange/cell-parity audit is delivered with
**PARITY BLOCKED**, not coupled numerical acceptance. The latest detailed
decision is [benchmarks/v3_i0/V3_I0_DECISION.md](benchmarks/v3_i0/V3_I0_DECISION.md).
Gates A/H are PARTIAL, E FAIL; B/C/D pass only within their documented diagnostic
scope, F diagnoses unsupported shared cells, G includes a synthetic limiter
control, I covers reporting. Final Git gate J is verified in external DELIVERY.json.

VV remains the reference mode for new solver/performance validation. V3-I0 uses
explicitly labeled legacy compatibility controls because the coupled solver
does not implement VV. Its fail-closed VV/restart guard remains intact.
Backwards-compatible constructor defaults have not changed. FP64 only.
Scheme A, coupled restart and P2-B remain NOT_STARTED / NOT_VALIDATED / NOT_RUN.

## Implementation and verified evidence

- Isolated branch `validation/v3-i0-exchange-audit`, exact base
  `d801c80cce15691b2a886a31d7e0bd864de35c10`. Preregistration 9f6a5e9;
  observer `28e292f2f421a7254a18889dfb2b50d7590ba42f`; probe/oracles 30a65e1.
  Production expressions/order are unchanged; added observers require compile
  definition MECHSYS_EXCHANGE_AUDIT and the probe's explicit environment opt-in.
  No DEM/checkpoint, V2 artifacts, V3-D design documents or AGENTS.md changed.
- 66 bounded final CPU/CUDA legacy runs plus two VV guard rejections. FP64,
  D3Q15/Nl=1, 10³ cells, dx=dt=1, nu=.1/tau=.8, Sc/Gammaf/BForce/Gv/Gm=0,
  Nproc=1, isotropic spheres; all actual production alpha=1.
- Independent 70-digit reference checked 44,000 cell collisions / 660,000
  direction records. Decomposition max 4.955142741437657e-20; independent
  BGK/solid impulse error 6.071532165918825e-17. Original V3-D budgets unchanged.
  Twenty non-shared case/backend controls match reference bitwise, off and on.
  Contact control exercises tangent-history creation/separation, but rolling
  slots remain zero; do not claim new nonzero-rolling validation from it.
- Nonidentity-Q torque and periodic levers pass the fixed-pose exchange ledger;
  this is not full-step angular conservation or physical added-mass acceptance.
  V2 standalone VV/restart results are preserved, not rerun or promoted to
  coupled acceptance by this milestone.

## Measured defects and unsupported behavior

- Centered sphere: independent positive-edge reference 27 cells, CPU accepts 7,
  CUDA 27. CPU imprint center-distance cutoff excludes partial outside-center
  cells. Common-cell gamma/B agree; total force parity does not follow.
- ResetParCell sphere-vertex eligibility <R+2Alpha removes valid partial cells
  on both backends. Alpha=.0001 misses 20/27 candidates even after rebuild;
  periodic fixture misses one. Widening CPU imprint alone is insufficient.
- Existing SphereCube/cudaSphereCube `continue` skips later edges in a shared
  loop group. Sixteen recorded gamma values fail the mathematical twelve-edge
  proxy but are independently explained by the actual control flow. Preserve
  that failed expectation; no formula correction or exact-volume substitution.
- Fconv=2 doubles CUDA sphere reaction but not collision impulse; measured
  residual .012564025997669046. CPU ignores this conversion. Nonunit Fconv is
  outside initial support. Production limiter activation remains unvalidated;
  the alpha=.5 witness is explicitly synthetic exact-rational D3Q15 algebra.
- Shared CUDA case: nine conflict cells; both particle reactions survive while
  cell data are overwritten/mixed. Residual .0008675864358344791 is explained by
  those shared-cell terms. Strict final reference/off/enabled state comparison
  fails; no observational-equivalence claim for shared ownership. Stop affected
  support acceptance. Do not invent an owner, mixture, serialization or
  compensating force. Shared positive cells remain unsupported for Scheme A.

## Artifacts, preservation and exact next task

Compact evidence, scripts, all mismatch IDs/geometry and strict failures:
`benchmarks/v3_i0/`. Commands/hashes: README.md and PROVENANCE.json.
Durable raw archive:
`/home/msys/SIMS/mechsys_v3_i0_validation/20261016-v3-i0-exchange-audit/V3_I0_RAW.tgz`.
SHA256 `9a33398a9f88d1f0aa48acd6f2539784daf3b6d7b6940fc3913cb35345d19e2e`;
all 1,265 payload files verified by size/SHA256, including pilots/failed attempts.
External ARCHIVE_VERIFICATION.json and DELIVERY.json contain closure evidence.
Final delivery workspace target: `/home/msys/git/mechsys-v3-i0-exchange-audit`;
the final exact tip/remote/clean status is recorded by delivery verification.
Original `/home/msys/mechsys` and all earlier clones are READ ONLY and preserved;
original tracked-diff SHA256 remains e98dcc...132e9 (full hash in PROJECT_STATUS).

**Next requires separate authorization:** V3-I0-P1 conservative sphere-cell
candidate/imprint cutoff parity correction, independently checked before/after
rebuild and periodic crossings. Keep collision, reaction, integration and actual
legacy proxy arithmetic unchanged in that bounded patch; separately review the
proxy control-flow defect. Do not automatically start Scheme A or P2-B.
