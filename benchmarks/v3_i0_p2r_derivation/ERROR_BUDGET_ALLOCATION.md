# Immutable independent budgets and nonduplicated ledger

The source/tests/formulas in ../v3_i0/analyze.py and all P1/P2/P2R/R/C artifacts
are byte-identical to base. Historical P2R-K remains FAIL. There is no new
budget, relaxed gate, KN harness, or addition of E_sum to an old tolerance.

The old per-cell impulse scale remains
eps=2^-52,Jref=.01,
S_c=sum_k (|f|+|fStar|+|BGK|+|solid|+|other|)*||e_k||1,
b_c=128*eps*S_c+1e-12*Jref.
Particle/global/angular aggregates remain the actual old gamma_(15N)(eps)
expressions and lever factors. They are not replaced by gamma93(2^-53).

| Error source | Where charged | Must not be charged again |
|---|---|---|
|first rounded force/body-T sum|one gamma93 box per destination/component|not in first local integration rounding|
|first coordinate/rotation RN|the actual composed node interval|not another blanket r added after the same composition|
|shared first Gamma/Omega and fluid collision|common deterministic first fluid input DAG|not an independent perturbation per atomic-order run|
|second surface/frame/Feq/Omega/local force formation|per-term interval and D_formation1|not the second atomic reduction U1|
|second reduction|E_A1+E_B1 on their respective interval term sets|not reused as2E0,not added to b_c|
|periodic streaming|exact index permutation|no extra arithmetic allowance|
|moments and Cs/rho|their own sequential/FMA/ratio graph|not an extra full collision error at every direction|
|independent reference geometry/Feq/frame|must have its own correlated error proof|not supplied by the compatibility boxes|

For Fconv=1,alpha=1,h=dx=Cs=1, the dimensional reaction is
J_fluid=dx³*Cs*sum(B*Omega*e), h*F_particle=−J_fluid. The body torque uses the
entry image lever and conjugate entry Q. The frozen independent test compares
actual collision writes against its own independent formation reference, not
only two quantities copied from the same production expression.

**Preservation is certified; complete allocation is UNRESOLVED.** The present
boxes bound variation among contractions/orders under fixed geometry premises.
They do NOT bound the joint actual-write-minus-independent-reference residual
under every existing per-cell,particle,global and angular budget. In particular,
one may not subtract independently widened fluid/particle boxes and call the
result a valid exchange proof: common Omega/B/frame nodes are correlated.
No assertion that the complete decomposition fits B_old is justified yet.
This is D-J PARTIAL, even though all existing numerical exchange PASS evidence
remains valid within its old scope. No old PASS is rederived from these boxes.

The next proof must pin the independent reference's exact arithmetic/error
enclosures and preserve shared nodes, then prove each complete residual fits
its existing old bound. If any does not fit, leave it UNRESOLVED; do not use
unused budget in another field,old b_c+E_sum,observed small residuals,or a new
geometric epsilon. Isothermal fluid has no assumed conserved full mechanical
energy, and phase-aligned coordinate balances are a separate diagnostic.
