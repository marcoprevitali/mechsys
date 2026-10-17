# Option A1 retained — reference prototype ONLY, not implemented

Compute each existing contribution/history update ONCE. Write its force/body
torque with stable physical destination,feature/cell ID and periodic image.
Build a stable per-destination index (or sort keys if the existing construction
cannot guarantee order). Gather in a fixed arithmetic order into F/Flbm/T,
preserving their distinct initializers. A serial per-particle gather is the
smallest diagnostic reference; a fixed tree is a different arithmetic baseline.
Do not implement this design or change production atomics in this milestone.

| Resource/implication | Design estimate, NOT measurement |
|---|---|
|contribution storage|6 binary64 fields =48*M bytes;93 contributors ->4,464 bytes, excluding keys/history/index|
|stable keys|e.g. two64-bit ID/index fields adds16*M bytes (1,488 for93), more for feature/image data; exact representation must be designed|
|index/offsets|64-bit permutation8*M and CSR offsets8*(Nparticles+1), plus capacity/temporary buffers|
|launches|existing contribution kernel changed to write records, at least one gather launch; optional key/count/prefix/sort launches, number backend/library-dependent|
|sorting|not intrinsically necessary if canonical destination/cell order is already guaranteed; otherwise stable indexing/sort cost and temporary storage must be included|
|history|retain one physical owner/update; sorting records does not create another friction/rolling computation; exact migration across rebuilds/restarts|
|CPU/GPU|implement same logical key order if desired, but contribution formation/FMA/library differences remain; no automatic cross-backend bitwise guarantee|
|performance|extra storage writes/reads and gather can cost time; no measured speedup or overhead percentage; no campaign here|

Guarantee, if later validated: same pinned binary/GPU/configuration/input,
same contribution bits and same fixed order produce the same sums. It is NOT
global numerical determinism if other owners, histories, callbacks, reductions
or library math remain nondeterministic. Checkpoint reproducibility also needs
the entire solver state/phase, which remains a separate blocked coupled task.

A1 creates a NEW numerical reference. Both future baseline and candidate must
use it for a strict prospective comparison. It cannot force an arbitrary old
atomic-order baseline to reproduce, cannot change old K FAIL and does not solve
phase interpretation, physics accuracy or missing structural contacts.

Choose A1 only for value beyond a justified numerical contract: isolating
transition defects, reproducible regression/checkpoint diagnosis or order
sensitivity studies. Current need is the unclosed phase/feedback derivation;
deterministic sums would not close it. Therefore A1 is retained, not recommended
as the immediate next step or mandatory production policy.
