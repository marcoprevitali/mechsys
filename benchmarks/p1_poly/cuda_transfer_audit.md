# P1-P - CUDA transfer dependency audit (2026-10-15, from pleg_large_nsys.sqlite)

Source: 2,721 memcpy operations / 87.7 GB total in the profiled 1001-step legacy run.

| Size (B) | Count | Direction | Device time | Attribution |
|---|---|---|---|---|
| 8 | 1,001 (1/step) | D2H | 1.2 s | control scalar (demaux field for host loop) |
| 16 | 1,001 (1/step) | D2H | 1.3 s | control scalar (second demaux field) |
| 17,248,672 | 112 | D2H | 548 ms | state component at rebuilds + output dumps |
| 43,582,080 | 118 | D2H | 1,553 ms | state component (e.g. vertices/particles) |
| 62,070,080 | 84 | D2H | 3,068 ms | state component (interacton arrays) |
| 154,502,072 | 67 | D2H | 6,089 ms | large state component |
| 377,304,584 | 46 | D2H | 10,536 ms | full-state download (~360 MB) |
| others (62-379 MB) | ~110 | D2H | ~11,000 ms | output/rebuild variants |

Total: 2,721 copies / 87.7 GB. The ONLY per-step transfers are the 8 B and 16 B control
scalars. All large copies occur at REBUILDS (5 in-window + initial build) and OUTPUT dumps
(dtOut = Tf/100 -> ~100 dumps x full-state download of ~600+ MB each).

Dependency assessment:
- 8/16 B per-step scalars: consumed by the host loop (rebuild decision / output trigger
  logic). Deferral changes control flow -> NOT safely deferrable without an on-device
  control redesign (which is the P4-class device-resident stepping, out of P1 scope).
- Large output dumps: REQUIRED at dtOut cadence for output correctness; the payload is
  consumed by file writing, not by dynamics. Deferrable only as an output-implementation
  optimization (async/buffered I/O), which changes output behavior and is out of the
  'safe transfer' scope defined for P1.
- Large rebuild downloads: REQUIRED - CPU reconstruction consumes the device state
  (DnLoadDevice). Deferral would starve the rebuild.

CONCLUSION: no per-step transfer qualifies as a SAFE deferrable transfer under the P1
criteria (postponing any of them changes control, output, or reconstruction). The dominant
fixable costs for polyhedra are (a) the output-dump volume (an output-implementation
optimization, P4-class), (b) the rebuild download volume (tied to CPU reconstruction,
P4/S2-class), and (c) host per-step processing. Per the P1 brief, no transfer experiment
was implemented; recommendation recorded in the P1-P summary.

Timing separation (measured, profiling-enabled run): device transfer time (sum of memcpy
durations) 53.1 s of which ~40 s belongs to rebuild+output large copies; API submission
time overlaps; host wait (cudaStreamSynchronize) 18.6 s. No double-counting: API and
device durations reported separately.
