# Default-off regression — FAIL, no tolerance waiver

Required46 non-shared controls:43 attempted,42 bitwise PASS,CUDA large strict
FAIL,three CUDA tail controls NOT_RUN. The failure was found before completing
the existing P1-only coverage regression, so that full regression is PARTIAL.
P2/P2R are false throughout these controls. Raw runner's historic `on` means
P1 ConservativeSphereCells only, not robust occupancy. The failed last large
comparison is recovered from actual snapshots even though the original runner
aborts before appending that comparison to its RUNS.json. No selective report.

Same unchanged baseline binary/identical input repeats produce multiple
state1/state2 hashes; all six base/candidate initial per-candidate claims match
bitwise. Atomic live sums vary. Maximum first strict difference1.38778e-17.
This baseline non-repeatability does not satisfy or replace the registered
bitwise criterion. All first failures and repeats retained in
DEFAULT_OFF_DIAGNOSIS.json and raw archive. No deterministic reduction rewrite.

Six standalone explicit VV/checkpoint restarts (existing cases0/1/9,
law0/damping1,CPU/CUDA) remain bitwise; three CPU/GPU comparisons pass original
budgets. Not full V2 recertification. Coupled VV guard remains fail-closed.
18 explicit negatives pass:missing P1/P2 flags,noncanonical representation,
Fconv2,Sc!=0,shared geometry,VV,limiter risk,and fixed out-of-envelope pose,
each on CPU/CUDA. Limiter-risk states reject before any production collision;
not production limiter validation. Shared CUDA legacy strict negative retained,
not silently promoted to support. Supported periodic/free wrapping remains intact.

Contact laws,collision arithmetic,DEM stepping/checkpoint bodies and prior
artifacts are unchanged. New FP64 helper wrappers/flags remain default false.
No default promotion or overall PASS until user resolves the strict-gate issue.
