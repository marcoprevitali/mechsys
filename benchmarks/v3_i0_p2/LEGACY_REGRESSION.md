# Compatibility controls — P2 correction disabled

PASS within existing non-shared scope; see LEGACY_REGRESSION.json and raw runs.
All coupled controls set P2_MODE absent/false. Existing P1 runner registered
25 geometries, ran 140 processes and two explicit P1 shared rejections. Forty-six
non-shared reference/off comparisons are strict bitwise; shared is excluded and
the known CUDA shared strict failure survives. Existing P1 independent analyzer
passes 88,000 cells / 1,320,000 directions and 144 coverage rows. These do not
validate corrected occupancy, despite the P1 runner's historical `on` label.
That label means ConservativeSphereCells=true only, never P2=true in this run.

Standalone reference mode is explicitly UseVelocityVerlet=true. Existing V2
cases0/1/9, law0/damping1, CPU/CUDA: six uninterrupted-versus-checkpoint restarts
bitwise, three cross-backend comparisons pass original abs1e-10/rel1e-9. This is
a bounded regression subset, not a rerun/reclassification of the entire V2 suite.
Both coupled VV requests still fail with the original guard message.

Production contact laws, DEM stepping/checkpoint bodies, lib/flbm and prior
benchmarks/AGENTS are byte-identical to e0d6c2f. Only new inline DEM geometry
helper code is added to special_functions.h; legacy helpers are untouched.
All 1,254 direct legacy helper results/backend match their base build bitwise.
Default-off mode does not enter any new P2 guard or geometry branch.

New P2 noncanonical/Fconv/limiter guards are compile evidence only, NOT_RUN at
runtime following the earlier geometry hard stop. Shared support remains blocked;
production limiter remains unvalidated. No change to reference VV policy/defaults.
