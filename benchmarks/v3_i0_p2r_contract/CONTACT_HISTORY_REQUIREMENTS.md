# Nonzero history and transitions — future design, NONE RUN

CUDA large has one sphere and zero DEM contacts/histories. Its bitwise empty
history result establishes NO numerical compatibility for friction/rolling.
The following controls are required before extending P2R-KN beyond that scope.
Each uses immutable input/model flags, explicit physical/feature/image IDs,
per-step contribution records and an independent mechanical/history oracle.
Do not overwrite prior V0/V1/V2 evidence or claim these controls already passed.

| Proposed control | Exact required agreement | Numerical/physical requirement | Boundary handling |
|---|---|---|---|
|nonzero tangential history, sustained stick|same physical key,owner,update count,stick branch and predecessor state|independent tangential recurrence with its OWN formation/propagation bound; action/reaction and work|choose a certified strict margin to Coulomb threshold|
|nonzero rolling history|same rolling owner,branch,frame and persistence|nonzero rolling moment/state independently reconstructed; torque/work identity|zero rolling slots do not qualify; no duplicated rolling update|
|Coulomb sliding, away from threshold|same slip branch/cap invocation and contact normal|independent capped-force/damping law under actual mode; dissipation sign/bookkeeping|branch mismatch is failure, not paid for by E_sum|
|at/near Coulomb threshold|same identity and documented trial/cap operands|first compare the branch predicate's uncertainty interval; derive physical onset/dissipation criterion separately|if interval straddles threshold, EVENT_UNRESOLVED; no automatic equivalence or universal force tolerance|
|loading reversal|same contact identity/orientation/committed history and reversal step when margin certified|independent sign/history rotation, elastic energy and dissipation through reversal|different branch/timing requires explicit event investigation|
|creation|same new key/image,multiplicity,one history initialization and first-update count|activation/first-contact correction follows exact registered law; no fabricated prehistory|away from boundary exact activation step; grazing interval needs event-specific reference|
|separation|same loss/separation decision and baseline history retention/deletion semantics|independent zero/retained-state behavior; no ghost force/work|do not silently erase a mismatch by zeroing history in parser|
|recontact|same physical key and prescribed retained/new state,one update|replay documented baseline retention semantics,nonzero prior history|no arbitrary carryover/reset choice to make a trajectory match|
|contact-list rebuild/reorder|same physical/feature/image multiset,one history owner/update,stable old-to-new mapping|forces/histories before/after migration independently compared|same threshold side -> exact decision; differing certified-margin decisions fail; straddling interval unresolved|
|periodic image change|exact physical mapping/image code and unwrapped contact lever|same physical continuous history and action/reaction/torque under boundary transform|raw array/image labels may change only under a verified bijection; wrong image never a small-roundoff pass|

For smooth branch-separated controls, exact branch agreement is mandatory;
continuous histories can have independently derived, phase-aware arithmetic
differences only AFTER matched-input history updates/identities pass. Histories
are not arbitrary nearby vectors: committed state, transport frame, reset
semantics, update count and owner are part of the model.

For threshold-straddling evolved controls, the only automatic outcome is
EVENT_UNRESOLVED. A separately reviewed physical event criterion could use
an independent high-precision/contact-time reference and timestep refinement
to assess onset time, dissipated work and subsequent state. No numerical
threshold for that study is defined from the largest observed run difference.
Until the criterion is derived and approved, it cannot produce a KN PASS.

Any missing contact, duplicate contribution, changed owner, wrong image,
unexplained stick/slip branch or lost history is a hard structural/model
failure (or an explicitly diagnosed unresolved event), however small its
first force. A matched initial force comparison does not authorize a changed
history update in later steps. Nonzero-history CPU/GPU consistency must also
respect their actual selected law, damping and frame conventions.
