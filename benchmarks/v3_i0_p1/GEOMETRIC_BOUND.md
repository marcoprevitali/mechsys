# Conservative bound and its precise support contract

For cube center c, side a=dx, any point y in the closed cube has
|y-c| <= sqrt(3)*a/2 = H. If it intersects a sphere of radius R centered at x,
there is such a y with |x-y|<=R. Triangle inequality gives |c-x|<=R+H.
This screens **geometric intersection**, not exact intersection volume or a new
occupancy fraction. Both mathematical and legacy-control-flow positive edge
proxies imply intersection, so the bound includes both.

The same proof applies on the periodic torus using minimum-image center
distance: the center of the nearest sphere image is no farther than that of
any image containing an intersecting y. Imprint and the oracle use the existing
BranchVec/free-particle convention; fixed particles are not periodically imaged.
Each physical particle/cell identity is enumerated once, not once per image.

## Radius, representation and movement

Particle construction computes Dmax=max_vertex|vertex-center|+Props.R. It is
not generally the radius Props.R (and never generally Dmax/2). The canonical
one-centered-vertex sphere initialization in particle.h:1015–1025 establishes
vertex=x and Dmax=Props.R exactly. The experimental mode validates that identity,
no faces/edges/tori/cylinders/boundary proxy, and rejects noncanonical particles.
Polyhedral callers keep legacy mode; their eligibility path is unchanged.

Coupled Solve imprints at entry, then translates/rotates, evaluates all-vertex
displacement, and if maxdis>Alpha rebuilds DEM and particle-cell lists before
the next entry imprint. A canonical sphere's vertex is its center; rotation
does not move that vertex. Thus **at every imprint** distance since the current
map reference is <=Alpha, including equality. Triangle inequality yields the
candidate radius R+H+Alpha. No speed predictor, step-count guess or extra
unproved displacement constant is substituted. A post-drift/pre-rebuild state
can exceed Alpha; it is not an imprint-force-time validity assertion.

Corrected map references are saved at ResetParCell. Before imprint the mode
checks the current center against them, reading authoritative device centers
on CUDA, and fails if displacement exceeds Alpha. This catches stale-map pose
edits rather than silently treating a changed reference as valid. Particle
radius/geometry and periodic settings must remain fixed during Solve; arbitrary
application mutations are not a new supported model. There is no new drift,
force, collision or rebuild-time integration stage.

FP screening adds 64*epsilon*(1+|x|+screening_length) length headroom; the map
validity/overlap guard uses the corresponding scale including R, Alpha and dx.
This is conservative eligibility headroom at registered finite coordinates,
not a changed numerical acceptance tolerance. The oracle uses 70-digit exact
FP64 inputs and the original V3-D exchange budgets.

## Implementation choices, not a performance claim

`Domain::ConservativeSphereCells` defaults false in all constructors. The on
path scans every lattice cell once per canonical sphere and retains those
within R+H+Alpha, excluding preexisting static fluid cells. This intentionally
simple experimental enumeration avoids window wrapping duplicates for broad
skins. Records retain IPar/ICell/IGeo=0 identities and the existing upload path.
CPU imprint admits R+H; existing CUDA R+1.74dx is already a conservative
superset and needs no kernel/signature change. Both call the unchanged proxy.

On-mode preflight rejects **shared geometric sphere/cube intersections**, a
deliberately conservative superset of shared positive occupancy. This can
reject two spheres in one cell even when their edge proxy is zero. It neither
selects an owner nor supplies a mixture model. It uses current device poses
before CUDA imprint, so adds synchronous diagnostic/validation cost only on
the experimental path. Legacy off mode has none of this cost or rejection.
