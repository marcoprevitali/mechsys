# Actual collision and independent increment audit

**PASS within the registered single-component, alpha=1 observational scope.**
44,000 actual cells / 660,000 direction records from 44 enabled timesteps.
This count is records checked, not a claimed count of distinct scalar assertions.

`lib/flbm/exchange_audit.h` is empty without `MECHSYS_EXCHANGE_AUDIT` at compile
time. The probe additionally requires environment `MECHSYS_EXCHANGE_AUDIT=1`.
Null host/device sinks do not allocate, synchronize, download or change ordering.
The one-translation-unit CUDA diagnostic uses internal-linkage device symbols;
it is not a new general multi-TU logging API.

CPU `CollideSCDEM` and CUDA `cudaCollideSCDEM` capture local NonEq/Omega,
gamma/B, rho, nominal/effective tau, alpha, input and output immediately after
the original Ftemp assignment and **before** its limiter update. Repeated
passes overwrite that direction's record: the retained alpha is the one used
for its last actual write, not the final loop scalar. Static bounceback,
multiphase and non-sphere observer support are not claimed; the registered
fixtures contain no static fluid cells or FC records.

Original collision expressions and force arithmetic are unchanged. Observation
computes `db=-alpha*(1-B)*NonEq/tau`, `ds=alpha*B*Omega` separately and tags
`other=(f_after-f_before)-db-ds`. The original combined subtract/FMA need not
round identically to the two isolated terms. `other` is retained roundoff here,
not a compensating force. **Decomposition alone is a construction**, so it is
not the principal independent test.

`analyze.py` converts round-trip FP64 numbers to exact Decimal inputs and uses
70-digit reductions, independent D3Q15 weights/moments/equilibrium, and analytic
geometry. It recomputes rho/raw u, B, tau (Sc=0), directionwise bulk/solid terms,
surface equilibrium/Omega and the entire population write. Actual captured
inputs must equal the pre-collision snapshot. It also checks actual live force
addition equals the Flbm addition exactly once, per-claim reaction reductions,
world/body torque and independently attributes negative-control residuals.

| Quantity | Maximum absolute discrepancy |
|---|---:|
| Measured decomposition, momentum component | 4.955142741437657e-20 |
| Independently reconstructed BGK/solid impulse | 6.071532165918825e-17 |
| Independent individual population write | 1.6798324538865574e-16 |
| Independent surface Omega | 4.259157757824008e-17 |
| Unit-Fconv unambiguous legacy exchange | 4.955142741437657e-18 |

Units: populations M/L³; impulses M L/T. Here a=h=c=rho_ref=1.
Jref_cell=.01 and Jref_problem=10 were preregistered before runtime. No tolerance
was changed after measurements. Cell budget is `128*2^-52*S_cell + 1e-14`,
with S_cell including absolute pre/post and explicit direction momentum terms.
Global budget adds cell budgets and the actual contributor-count gamma_m term;
maximum 6.684825336157286e-11, or 6.684825336157286e-12 of problem Jref,
below the 1e-8 conditioning ceiling. Reference error <1e-60 is negligible here.

Actual BGK impulse maximum component is 2.8652751219294774e-14 over the evolved
fixtures; actual other impulse maximum is 4.926924392194738e-15. Neither is
silently charged to particle reaction. First centered-moving step has zero
BGK first moment; its nonzero other is floating-point population-write residue.
Every production alpha recorded was 1. The synthetic limiter test does **not**
validate activation or direction-dependent limiting in a production run.

Hooks capture accepted imprint force/body torque, actual lever/surface velocity
and candidate index without selecting a new owner. At stage boundaries enabled
readbacks are explicitly synchronized; disabled hooks do no such work. Compare
[REGRESSION.json](REGRESSION.json): 20 non-shared cases/backend combinations are
bitwise equal to the immutable V3-D reference with hooks off **and on**. Shared
negative strict FAIL is retained, so general observational equivalence is not
claimed and gates A/H are PARTIAL overall. No ordering/normalization repair.
This tests the hooks-compiled-in/env-disabled build, not merely preprocessing
the hooks away. The ordinary no-macro path is source-identical apart from an
empty guarded include; no separate performance claim is inferred from it.
