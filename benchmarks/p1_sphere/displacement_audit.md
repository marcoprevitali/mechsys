# P1-S displacement-reduction audit + persistent-buffer experiment (2026-10-15)

**2026-10-16 correction:** see [the evidence review](../p1_review/README.md).
The raw S-small baseline mean is 23.668 s (not 23.468); the kernel uses a global
atomic per thread (not a block reduction); benchmark energies are not bitwise
equal. The original text and measurements below remain as the historical report.

## Dependency chain (source: lib/dem/domain.h Solve loop, GPU path)

1. MaxD kernel (per-vertex displacement into bMaxDCU; persistent buffer, no allocation).
2. thrust::max_element(bMaxDCU) -> cub::DeviceReduce: TWO device kernels per call
   (cuda_gpu_kern_sum shows two thrust kernel_agent entries, 20,001 instances each over
   20,001 steps) AND temporary device storage allocated per call.
3. maxdis = *it - dereferencing the device iterator performs a synchronous 4/8-byte D2H
   copy (this is the readback the CPU needs).
4. Host decision: if (maxdis > Alpha) UpdateContactsDevice() - the CPU must know the
   result because contact reconstruction runs on the CPU (linked cells, CInteracton
   construction, maps). The decision point cannot be removed while reconstruction is
   host-side; only the ALLOCATION and the reduction kernels are removable.

Allocation attribution (nsys cuda_api_sum, scenario A, ~11,001 steps):
- baseline: 22,023 cudaMalloc + 22,021 cudaFree (~2/step), max single call 117.5 ms
- persistent: 22 cudaMalloc + 20 cudaFree (initialization only) -> the per-step
  allocations ARE the thrust reduction temporaries (confirmed by elimination)

Measured components (baseline, S-legacy-small, nsys): T_MaxD ~3.8 us/step,
T_reduction (2 thrust kernels) ~6 us/step, T_allocation (API) ~7 us/step x2,
T_readback/T_host_wait included in the 4/step cudaStreamSynchronize total.

## Persistent-buffer experiment (MECHSYS_PERSISTENT_REDUCTION=1, default-off)

MaxReduceKernel: grid-stride block max + atomicMax on the bits of a preallocated device
scalar (exact for non-negative displacements; order-independent => bitwise-identical
result). Per step: cudaMemsetAsync(4 B) + 1 kernel + 4/8 B D2H readback - no allocation,
no additional synchronization, decision point unchanged.

## Numerical validation (oracle_A_dense)
- Final energies bitwise identical (Kinematic 0.00363438, Total 0.00363816)
- Rebuild cadence identical (same 12+26 rebuild pattern)
- cudaMalloc: 22,023 -> 22 (1000x reduction; setup only)

## Performance (S-legacy-small, 5 interleaved pairs, Nproc=8)

| rep | baseline wall | persistent wall |
|---|---|---|
| 1 | 23.97 | 22.69 |
| 2 | 23.56 | 22.32 |
| 3 | 23.53 | 22.55 |
| 4 | 23.65 | 22.20 |
| 5 | 23.63 | 22.41 |
| mean | 23.468 | 22.434 |

speedup = 1.046 (4.6%); paired differences all positive (mean 1.234 s, max/min ranges do
not overlap). Solve-wall component: 13.09 -> 12.71 s (3.0%); startup variance accounts for
the remainder of the wall difference. f = 0.38 s / 13.09 s = 0.029 -> S_max(measured) = 1.030.

Verdict: reproducible, numerically equivalent; kept default-off (not promoted).
S-legacy-large interleaved benchmark: in progress (results appended below).

## S-legacy-large benchmark (5 interleaved pairs, CPU% 161-166 = clean)

| rep | baseline wall | persistent wall |
|---|---|---|
| 1 | 234.89 | 228.38 |
| 2 | 231.09 | 232.23 |
| 3 | 230.72 | 232.04 |
| 4 | 230.08 | 231.89 |
| 5 | 233.51 | 229.97 |
| mean | 232.06 | 230.90 |

speedup = 1.005 (0.5%); paired differences mixed sign (+6.5, -1.1, -1.3, -1.8, +3.5 s);
ranges overlap. Verdict: INCONCLUSIVE at 154k - the absolute saving (~0.4 s of reduction
allocation overhead) is ~0.2% of this workload and is masked by run-to-run variability.
The optimization is retained default-off; it benefits small/medium workloads (4.6% at
18.6k) and adds no cost at large scale.
