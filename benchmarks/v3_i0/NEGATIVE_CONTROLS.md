# Negative controls and retained qualifications

## Nonunit Fconv: actual legacy CPU/CUDA runs

The centered moving fixture sets Fconv=2 without changing fluid collision.
First-step GPU Jsolid,x=.012564025997669036; expected particle Jx is its negative,
but actual legacy hFx=-.02512805199533808. Residual magnitude
.012564025997669046, many orders above the unchanged ~6.68e-11 global budget.
The independently predicted `(1-Fconv)*Jsolid` explains it within roundoff.
Actual live F increment and Flbm agree; Flbm is not applied a second time.
CPU ignores Fconv: Jsolid,x=.008353349348328622 and hFx=-.008353349348328622,
residual ~4.13e-19. Different occupancy is reported separately, not charged to
conversion. GPU VC-only conversion source is frozen `lbmdem.cuh:592`;
CPU/FC reaction lacks it. Nonunit conversion is outside initial support.

## Limiter: explicitly SYNTHETIC, not production activation

All production records have alpha=1. No collision law/input was perturbed to
force unsafe limiting. [SYNTHETIC_LIMITER_WITNESS.csv](SYNTHETIC_LIMITER_WITNESS.csv)
is an independent exact-Fraction D3Q15 witness for all 15 directions:
rho=a=h=c=1, tau=.8, gamma=.5, B=3/16, vfluid=0, vs=(1/100,0,0).
Actual **synthetic** solid increment is `(1/2)*B*Omega`; all synthetic output
populations remain positive. Jsolid,x=3/1600, whereas the legacy alpha-free
reaction is -3/800; exchange residual -3/1600. Deliberately omitting alpha is
detected without changing the preregistered threshold.

The scalar total is independently checked from the 15 rational direction
increments, not substituted as a production measurement. This fulfills the
allowed synthetic I0-I control. Actual CPU limiter activation, GPU two-pass
cap/direction-dependent alpha, clipping and broader limiter support remain
NOT_VALIDATED. The observer captures last-written alpha before mutation, but
only the alpha=1 production path was exercised here.

## Shared ownership

Nine conflicting cells; CUDA residual .0008675864358344791 max component and
strict bitwise regression failure. Complete claimant/stored-cell evidence and
affected stop: [SHARED_CELL_DIAGNOSTICS.md](SHARED_CELL_DIAGNOSTICS.md).
CPU's near-zero residual is not a positive multiowner result.

## Scope guards, failed attempts and tolerance preservation

Explicit VV requests on both final binaries exit 1 with the original coupled
guard message. Neither Scheme A nor coupled restart was implemented. V2 and
V3-D artifact/source hashes remain unchanged.

Raw failed build attempts are retained: initial probe used generic rather than
sphere-specific history members; corrected probe compilation did not change a
library law. An initial CUDA inline-device-symbol declaration failed whole-
program compilation and was replaced with internal-linkage diagnostic symbols.
The raw first mathematical-proxy oracle FAIL (16 final strict expectations)
was attributed to legacy early-continue control flow, not hidden by a looser
tolerance. The mathematical failures remain FAIL in a separate result file.
A collector initially demanded bitwise equality for the preregistered shared
negative too; its assertion exposed the final strict failure. The collector now
preserves that FAIL and only asserts non-shared comparisons. A/H remain PARTIAL;
there is no retrospective general observational PASS.
