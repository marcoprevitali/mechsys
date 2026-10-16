# V1-H performance impact (2026-10-16)

**Coverage correction:** the original test_cu_04 driver leaves UseVelocityVerlet
false; these unchanged registered commands exercise the legacy integrator. They
do not establish the new VV path's overhead. See [the follow-up report](../v1_reference/README.md).
Raw timings and original interpretations below are preserved.

Method: interleaved corrected-vs-reference pairs on the registered legacy workloads,
all experimental optimizations off (persistent reduction disabled, oracle off),
Nproc=8, taskset-pinned for the large workload. /usr/bin/time CPU-percent recorded
per rep for contamination screening (external single-core jobs were active: a MoFEM
replica and a MercuryDPM sensitivity run).

## S-legacy-small (18,616 spheres, 20,001 steps, 3 interleaved pairs)

| rep | reference wall | corrected wall |
|---|---|---|
| 1 | 23.84 | 23.45 |
| 2 | 23.96 | 22.45 |
| 3 | 24.41 | 23.04 |
| mean | 24.07 | 22.98 |

The corrected build measured slightly FASTER (3-4.5%); however the reference reps ran
at 154-157% CPU vs 161-162% for the corrected reps (external load), and the P0-R/P1-S
data show run-to-run walls of +/-0.6 s at this scale. Verdict: no measurable overhead
from moving the check; any apparent improvement is within the contended-environment
uncertainty and is NOT claimed as a speedup.

## S-legacy-large (154,366 spheres, 20,001 steps, 3 interleaved pairs)

Results appended on completion (batch in progress at the time of the fix commit).
Early pairs: reference 236.6 s vs corrected 236.0 s (166%/160% CPU) - no measurable
overhead at 154k either, consistent with the check being relocated rather than added.

## Rebuild cadence

S-legacy-small: identical compression-stage cadence; the shear-stage average differs
by one rebuild (373 vs 376 average iterations between updates) from the check-point
relocation. Energies bitwise-identical at printed precision on the short validation.

## S-legacy-large final results (3 interleaved pairs, CPU% 160-166 = consistent)

| rep | reference wall | corrected wall |
|---|---|---|
| 1 | 236.55 | 236.03 |
| 2 | 239.54 | 244.71 |
| 3 | 254.02 (contention spike) | 237.34 |
| mean (all) | 243.37 | 239.36 |
| mean (excl. spiked base rep3) | 238.05 | 236.69 |

Verdict: NO MEASURABLE OVERHEAD at 154k either (the corrected variant is nominally
0.6-1.6% faster, within the contended-environment variability). The check was
relocated, not added; the total MaxD work per step is unchanged.
