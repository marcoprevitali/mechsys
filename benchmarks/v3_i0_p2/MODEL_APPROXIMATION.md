# Edge proxy versus volume — independent analysis only

Twenty-one geometries: R/dx=.05,.2,.5,sqrt(.5),1,1.2,2.2 at centered,
offset(.45,.2,.1) and cube-corner sphere positions. The edge gamma here is the
independent mathematical reference, not an accepted candidate solver value.
No occupancy model, collision or acceptance gate was changed by this diagnostic.

Volume reference: analytical contained sphere/cube/disjoint cases; otherwise
analytical z interval integrated over xy by successively refined composite
midpoints (128 up to2048 per axis). Recorded adjacent-grid change must be less
than min(5e-5 absolute,1e-3 relative). All21 meet that empirical criterion;
it is convergence evidence, not a rigorous integration error bound. Full
refinement traces and relative differences are in MODEL_ACCURACY.csv. NumPy1.26.4.

| Unit-cube case | Mathematical edge gamma | Volume reference |
|---|---:|---:|
| Centered R=.05 | 0 | .0005235987755983 (analytic) |
| Centered R=.5 | 0 | .5235987755983 (analytic) |
| Centered R=sqrt(.5), binary64 input | ~1.65358e-8 | ~.9650765530 |
| Corner R=.05 | .0125 | ~.00006544950 |
| Centered R=1 | 1 | 1 (analytic) |

Largest sampled absolute model difference ~.9650765365; corner R=.05 relative
difference ~190. Edge intersections sample the cube skeleton, not its interior:
a sphere may occupy substantial volume without reaching an edge; a tiny corner
sphere's edge gamma scales as R while its volume scales as R³. This diagnostic
does not favor exact-volume replacement in this milestone and must not be used
to tune or excuse the failed numerical edge gate. A future model-accuracy study
would be a distinct scientific decision.
