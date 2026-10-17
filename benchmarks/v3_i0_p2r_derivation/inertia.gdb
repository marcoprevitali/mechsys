set pagination off
set confirm off
set disable-randomization off
set environment P1_MODE 0
set environment P2_MODE 0
set environment P2R_MODE 0
set environment P1_RADIUS 2.2
set environment MECHSYS_EXCHANGE_AUDIT 1
# Same instruction offset in both archived AddSphere implementations.
# After the third principal-moment store; before any Solve invocation.
break *'DEM::Domain::AddSphere(int, blitz::TinyVector<double, 3> const&, double, double)'+0x20f
run
printf "INERTIA_BITS %016lx %016lx %016lx\n", *(unsigned long*)($rax+0x148), *(unsigned long*)($rax+0x150), *(unsigned long*)($rax+0x158)
printf "MASS_BITS %016lx\n", *(unsigned long*)($rax+0x298)
printf "MXCSR %08x\n", $mxcsr
bt 3
quit
