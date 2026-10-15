# P0-R5 - CUDA operations audit (nsys + source inspection, 2026-10-15)

## Per-step operation inventory (nsys traces + lib/dem/domain.h inspection)

| Operation | Frequency | Purpose | Blocking | Required every step? |
|---|---|---|---|---|
| cudaMemcpyAsync D2H | 1-2/step | demaux/scalars readback for host loop + output | async, but consumed by host | mostly yes (batchable to dtOut) |
| cudaMemcpyAsync H2D | ~1/step | prescribed-wall / userdata updates | async | only with prescribed walls |
| cudaStreamSynchronize | 4/step spheres, ~4.7/step poly | MaxD readback, output, rebuild paths | blocking | MaxD readback is structural |
| thrust::max_element + deref | 1/step | rebuild decision (MaxD reduction) | device sync via deref | replaceable by on-device decision |
| cudaMalloc/cudaFree | 2/step (spheres: 40,059/20,001) | thrust temporaries for per-step reduction | can stall (max 132 ms observed) | eliminable with persistent buffers |
| Kernel launches | ~11/step spheres | Reset/Force/Integrate/MaxD chain | none by themselves | yes |

## Measured decomposition (nsys, profiling-enabled; relative structure valid, absolute times inflated)

S-legacy-small: GPU busy ~280 us/step (CalcForceVV_Hertz 195.5 us, VF 54.5 us on half-steps,
Rotate 26.3, Translate 14.6, MaxD 3.8) vs ~660 us/step solve wall -> GPU idle ~58%.
cudaStreamSynchronize 7.14 s (80,615 = 4/step), cudaMemcpyAsync 1.23 s (2/step),
cudaLaunchKernel 0.73 s (11/step), cudaMalloc 0.23 s (2/step, max single call 132 ms).

P-legacy-large: GPU busy ~15.4 ms/step (EE 6.02, VF 4.17, FV 4.15, Translate 0.84, MaxD 0.15)
vs ~271 ms/step profiled solve -> GPU idle ~94%. cudaMemcpyAsync 53.1 s over 2,710 calls
(avg 19.6 ms, max 275 ms) = 73.9% of API time; cudaStreamSynchronize 18.6 s (4,730 calls).

## Answers to the ten questions
1. Every step: demaux/scalars D2H readback feeding the host loop; MaxD result.
2. Host-based control only: MaxD readback + thrust::max_element (device already computes the max).
3. Can stay on GPU: force accumulation, integration, MaxD decision, output counters.
4. Requires a sync: any host decision (current rebuild trigger; output at dtOut).
5. Repeated allocations: thrust temporaries of the per-step max_element reduction.
6. Thrust: yes - max_element allocates each step (cub::DeviceReduce path).
7. Unnecessary syncs: per-step MaxD dereference sync; stage-boundary syncs in profile mode only.
8. Kernels without host intervention: yes - launches are sequential on one stream; only the MaxD
   readback forces a host rendezvous.
9. CUDA Graphs: would cut 11 launches/step (~0.7 s API per 20k steps) but sync/readback dominates.
10. Persistent buffers: remove 2 cudaMalloc/step and their tail latency.

Caveat: long cudaMemcpyAsync API durations reflect host submission + pageable-copy behavior; the
device transfer itself is shorter. Root cause requires reading the saved .nsys-rep timelines.
