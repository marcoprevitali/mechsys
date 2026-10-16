# Default-off and unchanged-eligibility regression

48 reference/off case-backend comparisons: 46 non-shared are bitwise identical
for serialized populations/macros/scratch, pose/velocity/Q, actual force/body
torque, histories, vertex references, acceleration caches, clocks and diagnostic
energy/work fields. The retained CPU shared control matches; CUDA shared strict
comparison FAILS as before. It is not normalized, relaxed or called supported.

For zero-edge and empty-map configurations, corrected/reference physical state
is also bitwise identical (four controls across CPU/CUDA). Only candidate-list
metadata is excluded from that physical comparison, because extra inactive
candidates are explicitly allowed. No force/history/population value is removed.
Where eligibility changes, old trajectories are NOT the oracle: added cell
impulses must instead match the independent collision/torque ledger.

Corrected mode rejects the original shared fixture on both backends with explicit
cell/particle diagnostic before imprint. No owner/mixture/force normalization is
introduced. The guard is deliberately stronger: shared geometric intersections,
even zero-proxy ones, are unsupported. CPU would otherwise expose additional
shared positive cells after its restrictive cutoff is widened. The unchanged
V3-I0 archive remains the canonical observed legacy claimant/overwrite evidence.

The library's mode defaults false; diagnostics remain independently default-off.
No collision kernel, force/torque law, standalone VV/checkpoint implementation,
occupancy helper or coupled VV guard was edited. Entire lib/dem, lib/flbm,
lbmdem.cuh and V2/V3-I0/V3-D artifacts match the starting commit. Corrected
polyhedral mode is rejected rather than applying a sphere bound indiscriminately;
non-sphere legacy paths remain source unchanged.
