# Shared-cell negative: measured; support BLOCKED

One step, R=1.2, centers (3.81,5,5) and (6.19,5,5), velocities
(.002,-.001,.0005) and (-.001,0,0), Kn=1. Slight mechanical overlap .02 is a
registered negative fixture, not a suspension acceptance case. There are 54
reference particle–cell pairs, 45 distinct cells, nine shared positive cells.

[SHARED_CELL_LEDGER.json](SHARED_CELL_LEDGER.json) records all claimants,
mathematical/legacy gamma, independently derived B/Omega, production computed /
accepted flags, actual per-claim reactions, final cell gamma/B/Omega, collision
impulse and matching owner candidates. A rejected/not-computed claimant's
counterfactual contribution is explicitly reference-derived, not mislabeled as
a production-applied increment. Raw complete ledgers retain each direction.

CPU Nproc=1 accepts 13 total claims. Its tight imprint cutoff rejects most
shared geometric cells; cell 555 selects one claimant after the gamma comparison.
This run's exchange residual max is 7.250602028496811e-19. A near-zero residual
does not validate a multiowner model or missing-cell coverage.

CUDA accepts 54 claims, including both owners in nine cells. Particle reaction
receives all accepted contributions, but the fluid cell is overwritten, not
their conservative sum. Measured:

```text
Jsolid = ( .0053422727490403021, -.0056352443657214273, .0028176221828607175)
sum hF = (-.0062098591848747811,  .0062098591848745044,-.0031049295924372557)
resid  = (-.0008675864358344791,  .0005746148191530772,-.0002873074095765382)
```

The sum of the nine shared-cell residuals explains the global discrepancy to
9.435947032412906e-19 maximum component; no force correction was applied.
Only four CUDA conflicted cells have one consistent gamma+full-Omega claimant
match; five do not. This measures mixed/ambiguous provenance, consistent with
unlocked grid writes. Do not assign a fabricated owner ID to those cells or
infer a validated max/mixture law from the comparison alone.

Final expanded regression retains a strict failure: CUDA shared state 0 is
identical, but state 1 has 58 differing serialized fields for reference vs
default-off, and five for reference vs enabled. These are not normalized away;
some population differences exceed roundoff (e.g. ~4.88e-5). The earlier pilot's
narrower state comparison happened to match. Thus **observational equivalence
for shared ownership is NOT established**, whether scheduling/racy writes or
the added diagnostic code influenced that unsupported execution. No additional
shared campaign, serialization, force normalization or ownership fix was run.
This triggers the affected stop condition; A/H are PARTIAL overall despite
20/20 non-shared bitwise controls. The negative diagnostic/classification is
complete, not a positive support PASS.

Shared positive cells must remain explicitly unsupported for the initial Scheme
A subset. No rule has been introduced into legacy Solve; a future prototype
needs rejection or a separately approved ownership/mixture model.
