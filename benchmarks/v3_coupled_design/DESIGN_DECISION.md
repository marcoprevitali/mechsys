# V3-D design decision and re-entry

2026-10-16, Codex. **Design deliverable complete; numerical coupled VV acceptance
is still BLOCKED.** No new production algorithm, numerical run, checkpoint mode
or performance benchmark is implemented in V3-D. The existing fail-closed guard
and every V2 source/result are unchanged.

## Git and artifact provenance

- User fork: `https://github.com/marcoprevitali/mechsys`, parent `Axtal/mechsys`,
  verified with `gh repo view ... --json nameWithOwner,isFork,parent,url`.
- Separate full, non-shallow remote clone; base
  `2b8d8c335709046e224f4c43aa930144ae6854e7` from
  `origin/validation/v2-restart-coupled`. No experimental branch merged.
- Design branch: `design/v3-coupled-vv`.
- Persistent clone: `/home/msys/git/mechsys-v3-coupled-design`.
  Source audit was prepared in `/tmp/mechsys-v3-design.coivTF/work`.
- Origin fetch/push: user fork; upstream fetch Axtal, push `PUSH_DISABLED`.
- Design/handoff commit: inspect `git rev-parse HEAD`; source/guard/V2 hashes are
  in `SOURCE_MANIFEST.json`. Final reply records the verified remote tip.
- Scoped commits: source audit/ledger `3f6903bdd046f3ade825b58f72e35c9e1a3f9bba`,
  time contract/independent requirements `88294764eafa15a27cb641d4aa535837a13826c8`.
- Original `/home/msys/mechsys` and `/home/msys/git/mechsys-v2-restart` are
  read-only. Original tracked-diff hash remains
  `e98dcc578695992948f3d804f572f6b212888ac2381832ae261be9c4e99132e9`;
  F0 backup remains `/home/msys/SIMS/mechsys_gpu_backups/20261015-150003/`.

## Findings and selection

Current coupled order is entry reset -> contact force/history -> imprint/fluid
reaction -> legacy particle translate/rotate -> end-motion list/cell-map rebuild
-> LBM collision -> stream -> raw moments -> clocks. Contact and hydrodynamic
inputs precede drift, but the particle reaction is already applied **before**
collision selects its actual population increment. No synchronized VV sequence
exists. Stored legacy velocities also lag the advanced geometry. Simply moving
the list rebuild or enabling the standalone flag cannot establish coupled VV.

The exact registered solid increment is `delta_f_h=alpha B Omega` (or actual
directionwise increments if limiting is not uniform). With common units,
`J_fluid,h=dx³ Cs sum(delta_f_h C)` and particle `Jp_h=-J_fluid,h`; world torque
is the same cell-image lever cross Jp, then transformed by conjugate Q to body.
Current pre-imprint reaction omits collision alpha and Fconv is inconsistent
between CPU/VC/FC paths. Shared-cell ownership, CPU outside-center coverage,
Gammaf, body-force weighting, effective tau and multiphase indexing are additional
source-verified hazards. Their individual contribution to V2's residuals remains
unmeasured; **no artificial balancing force is proposed**.

Evaluate A/B/C as specified in [SCHEME_COMPARISON.md](SCHEME_COMPARISON.md).
**Recommend A: explicit left-state fluid exchange impulse, applied once, followed
by the validated nonhydrodynamic VV mechanical step.** This is a bounded reference
proposal, not an approved production method or a claim it is fastest.

Reasons are numerical and evidentiary, not implementation simplicity alone:

1. It names the actual collision interval impulse, avoiding an unsupported
   identification of old-fluid imprint as endpoint/midpoint force.
2. One shared solid increment determines both reactions, so exchange pairing is
   algebraically reviewable independently of bulk forcing and boundaries.
3. J/K are excluded from both ce acceleration caches, preventing an easy double
   integration error; zero-hydro reproduces the V2 stage/history reference.
4. There is no fluid replay/contact trial, so one collision/stream and one history
   commit have a simple independently testable ordinal contract.
5. B1's midpoint-particle predictor still consumes f_n and has no established
   coupled order advantage; B2 requires an uncompleted fluid/forcing derivation.
   C costs rollback/convergence machinery without a demonstrated full-solver
   failure that requires it. Both remain options if A fails registered goals.

## Expected accuracy, proved properties and unproved hypotheses

| Class | Statement |
|---|---|
| Source verified | current operation/reset order, raw moment convention, units conversion, force/torque locations, guard and listed CPU/GPU differences |
| Existing runtime evidence, not rerun | V2 100/100 restart, 50/50 physical CPU/GPU and 668,272 scalar checks; original coupled crash/ignored flag and final legacy diagnostic residuals in [V2_REPORT](../v2/V2_REPORT.md) |
| Derived conditional property | equal/opposite solid exchange impulses and fixed-pose angular cancellation if the same actual increments, unique owners, units and image levers are used |
| Derived order limitation | A has O(h²) local left-impulse/drift splitting error in a smooth constant-force model; expect at best first-order **coupling** even with VV mechanics |
| Not established | global coupled momentum/angular conservation, hydrodynamic accuracy, fluid midpoint interpretation, physical interior-fluid/added-mass consistency, stability of light bodies, CPU/GPU numerical equivalence of a future implementation |
| Hypothesis requiring tests | A is adequate for a bounded reference subset; B1's correction may improve errors; iteration might help only if demonstrated interface stiffness warrants it |

No untested second-order or conservation claim is accepted. If second-order
coupling is a requirement, this A proposal is insufficient: revise the design
through B2's full fluid time/forcing derivation before selecting implementation.
Forcing has its own discrete conventions; the
[Guo–Zheng–Shi abstract](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.65.046308)
supports investigating those effects, not assuming this source is a Guo scheme.

## Initial support and remaining blockers

Initial subset: FP64 D3Q15, Nl=1, smooth Bn, Sc=0, alpha=1, Fconv=1, Gammaf=0,
fluid BForce=0, Gv/Gm=0, isotropic spheres, no ambiguous shared positive-occupancy cells; exact
law/options and history semantics from V2. Excluded modes must fail clearly.
This is deliberately **not general suspension support**. In particular:

- CPU/GPU sphere-cell coverage mismatch must be independently measured and
  resolved in a separate reviewed parity patch before a common positive gate.
- Current shared-cell writes/reactions cannot prove conservation. Initial
  conflict rejection is safe scope control, not a positive two-particle hydro
  test. Choosing deterministic max ownership or a conservative mixture is a
  separate physical/ownership design decision, not silent force normalization.
- Limiter use, prescribed porosity, nonunit density conversion, alternate Bn,
  multiphase and anisotropic gyroscopic scheduling need separate extension gates.
- Raw full-grid conservation alone does not establish physical exterior-fluid
  momentum or correct added mass; do not silently alter particle mass/forces.
- Physical timestep/lattice refinement and interface stability remain untested.
- Coupled restart requires fluid populations, phase/roles, pending J/K and
  consumption state, forcing/BC and occupancy/map state in addition to DEM.
  It is outside the initial coupled implementation and is not V2 standalone Load.
- P2-B remains NOT_RUN. Historical polyhedral feature-count discrepancy and
  unaccepted performance variants remain separate, unresolved work.

## Validation and smallest next experiment

[VALIDATION_PLAN.md](VALIDATION_PLAN.md) specifies independent tests A–J:
uncoupled fluid limit, dry VV limit, fixed/free particle exchange, fast contact,
friction/rolling histories, periodic/moving walls, drag direction/velocity scaling,
rotating-body torque and compatible lattice refinement. Actual consumed records,
not post-step host reconstructions, must have zero missing/duplicates/image errors.
Ledger bounds are independently prescribed; all future gates are NOT_RUN.

Next bounded milestone **V3-I0**: observational single-cell/one-sphere exchange and
CPU/GPU cell-parity audit with the production VV guard intact. Capture actual
imprint/collision terms and independent J/K decomposition; preserve negative
cases, identify or retain the residual cause, and review any parity/model fix
before a separate default-off Scheme A harness. No implementation starts in V3-D.

## Artifact map and review order

1. [CURRENT_COUPLED_SEQUENCE.md](CURRENT_COUPLED_SEQUENCE.md): full CPU/GPU trace,
   source locations, field/reset ownership and time-level caveats.
2. [MOMENTUM_EXCHANGE_LEDGER.md](MOMENTUM_EXCHANGE_LEDGER.md): units, actual collision
   increments, linear/angular/external/support ledgers, algebraic witnesses.
3. [SCHEME_COMPARISON.md](SCHEME_COMPARISON.md): A/B/C accuracy/consistency/buffering/
   force/history/synchronization comparison and B2's unresolved derivation.
4. [COUPLED_VV_TIME_CONTRACT.md](COUPLED_VV_TIME_CONTRACT.md): complete A timestep,
   levels, bootstrap, external force stages, history and list validity contract.
5. [VALIDATION_PLAN.md](VALIDATION_PLAN.md): A–J, independent oracles, unit transforms,
   tolerances, expected failure signatures and scope-specific acceptance gates.
6. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md): I0 first, subsequent gated
   CPU/GPU changes, device residency and future coupled checkpoint scope.
7. This decision, source hash manifest and live root PROJECT_STATUS.md.

Documentation/source verification commands, from this clone root (no solver run):

```sh
git diff --check
git diff 2b8d8c335709046e224f4c43aa930144ae6854e7 --exit-code -- lib AGENTS.md benchmarks/v2
git rev-parse --is-shallow-repository
python3 - <<'PY'
import hashlib, json, re, subprocess
from pathlib import Path
root=Path.cwd(); d=root/'benchmarks/v3_coupled_design'
m=json.loads((d/'SOURCE_MANIFEST.json').read_text())
for p,sha in m['base_sha256'].items():
    assert hashlib.sha256((root/p).read_bytes()).hexdigest()==sha,p
assert subprocess.check_output(['git','rev-parse','HEAD:benchmarks/v2'],text=True).strip()==m['v2_artifact_tree']
links=0
for p in d.glob('*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if '://' in target or target.startswith('#'): continue
        assert (p.parent/target.split('#')[0]).resolve().exists(),(p,target)
        links+=1
print('source/V2 hashes and local links PASS; links=',links)
PY
```

Exact-rational D3Q15 moment arithmetic independently verifies the ledger's
3/800, 3/1600 and -3/800 witness values; it evaluates equilibrium moments only,
not a production collision or coupled simulation. The verified inputs/results
and scope distinction are in DESIGN_VERIFICATION.json.

Review questions before implementation: accept first-order coupled accuracy for
the initial reference experiment? Accept the explicit unsupported subset rather
than implying general coupled VV? Review observed cell-parity and ownership/
physical inertia decisions before enabling broader support. These are design
review items, not permission inferred from this completed documentation task.
