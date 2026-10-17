# CUDA safety audit — bounded dynamic evidence, not universal proof

Unchanged verified binary, `large OUTPUT`, original environment/flags. Each of
memcheck,racecheck,initcheck,synccheck was run once on BOTH executables,
serially, with the approved resident-desktop exception. Exact command/log hash
and tool version are in REPRODUCTION_MANIFEST.json; full logs and per-run GPU
inventories are in raw-verified/sanitizers. Every process returned0.

| Tool | Baseline | Candidate | Scope/limit |
|---|---|---|---|
| memcheck |0 errors|0 errors|executed out-of-bounds/misaligned accesses/hardware exceptions; not all paths|
| racecheck |0 errors/0 warnings|0 errors/0 warnings|shared-memory hazards, NOT arbitrary global-memory races|
| initcheck |0 errors|0 errors|executed uninitialized device global reads; not a host-memory checker|
| synccheck |0 errors|0 errors|supported synchronization primitives; not proof of correct inter-stream algorithm|

Tool meanings/limitations follow the [NVIDIA Compute Sanitizer manual](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html).
The installed CUDA12.6 tool's own logs are the evidence of actual execution.
No debug/recompiled executable replaced the baseline. Instrumentation changes
scheduling and produced additional low-bit sums; those are analyzed separately,
not mixed into the 10+10 uninstrumented classification.

## Relevant source and state checks

- Every93 candidate index is unique/in-range: cell0..999,particle0 in an
  allocated one-particle buffer; PaCeV has2*nvc entries, uploaded at
  lbmdem/Domain.h:1253-1319. Stable PersistentId1 is explicitly mapped to0.
  No physical-ID/storage-index confusion or duplicate contribution found.
- One particle owns each of93 cell destinations. Ordinary Gamma/Omeis writes
  in VC are therefore single-writer in THIS fixture. The historically failed
  shared-cell configuration is not tested or approved by this finding.
- Reset F/Flbm/T is ordered before imprint and every before_imprint snapshot
  confirms zeros. All initial particle/fluid/cache/history state hashes match;
  no uninitialized value is needed to explain the first varying sum.
- Ordinary reset writes and atomic contribution writes are in distinct ordered
  kernels. Translate/Rotate read after imprint, on the same default stream;
  callbacks synchronize before copying snapshots. No custom asynchronous
  stream/copy path or delayed rebuild is present in the tested sequence.
- No rebuild occurs in this two-step fixture. Existing Thrust buffers remain
  alive; raw pointers are obtained after allocation/copy. Diagnostic claim and
  collision buffers are synchronized before old buffers are freed; new buffers
  are allocated/zeroed and device symbols set before launches (probe:108-126).
- Capacity93/15000 and one writer per claim/cell-direction; overflow flag is
  checked. FC/DEM contact kernels have zero active records and return before
  access. No invalid read/write, buffer use-after-free, unintended alias or
  mixed atomic/ordinary writer was found in the executed path.

Conclusion: no competing correctness defect FOUND within the observed fixture
and supported sanitizer scope. This is stronger than merely noticing atomicAdd,
but is NOT an exhaustive exclusion of global races, all host initialization,
uninstrumented scheduling hazards, rebuilds, other geometries, nonzero DEM
histories, coupled VV or long-time behavior. No extra GPU instrumentation was
necessary; the existing archived observers were sufficient for this diagnosis.
