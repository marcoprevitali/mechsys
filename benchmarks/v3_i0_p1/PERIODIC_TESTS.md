# Image-aware translation and rebuilding

Registered cross_x/y/z fixtures start coordinate 9.999 and speed .002 in that
axis, Alpha=.0001, with noninteger transverse offsets. Actual post-drift and
post-rebuild snapshots show crossing and wrapping. The separate translate_x/y/z
fixtures exercise each motion axis away from a periodic face. Center references
are refreshed only when particle-cell maps are rebuilt; DEM reference resets
alone cannot certify them. Broad Alpha=6 exercises unique wrapped-cell identity
without iterating duplicate image windows.

All registered entry, before-rebuild and after-rebuild required candidate pairs
are present. Zero duplicates or wrong observed image levers; correct body/world
torque transformations at the entry imprint pose. Fixed particles use the
existing nonperiodic convention. CPU/GPU identical-input comparison is step 0
only; later snapshots are checked against each backend's actual pose.

Pre-rebuild geometry is reported, not assumed valid for arbitrary displacement:
that post-drift state can exceed Alpha and is never used for an imprint before
the scheduled rebuild. All present pre-rebuild fixtures also happen to retain
complete coverage. No general post-drift headroom guarantee is inferred.
The formal guarantee is for imprint entries within the checked Alpha allowance.
