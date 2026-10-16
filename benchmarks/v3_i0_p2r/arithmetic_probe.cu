#include <mechsys/dem/sphere_cube_robust.h>
#include <cstdio>
// Explicit separated vs fused operations: no change to production compiler flags.
struct Row {double v[16];};
#ifdef USE_CUDA
__global__ void eval(Row *out) {
#else
void eval(Row *out) {
#endif
    using namespace MechSysRobustEdge;double a,al,b,bl;two_sum(-.3,-.5,a,al);two_sum(-.1,-.5,b,bl);
    double ap=mul(a,a),bp=mul(b,b),ape=fused(a,a,-ap),bpe=fused(b,b,-bp),first=add(1.,-ap),second=add(first,-bp);
    Expansion m;product(m,1.,1.,1.);Expansion qa=coordinate(0,.3,-.5),qb=coordinate(0,.1,-.5);square(m,qa,-1.);square(m,qb,-1.);
    double tiny=::scalbn(1.,-1074);
    double vals[16]={a,al,b,bl,ap,ape,bp,bpe,1.,first,second,fused(-a,a,fused(-b,b,1.)),m.value(),2*::sqrt(m.value()),tiny,add(tiny,tiny)};
    for(int k=0;k<16;k++)out->v[k]=vals[k];
}
int main(){Row out;
#ifdef USE_CUDA
    Row *p;cudaMalloc(&p,sizeof(Row));eval<<<1,1>>>(p);auto e=cudaDeviceSynchronize();if(e!=cudaSuccess)return 2;
    cudaMemcpy(&out,p,sizeof(Row),cudaMemcpyDeviceToHost);cudaFree(p);
#else
    eval(&out);
#endif
    const char *names[]={"q1_hi","q1_low_coordinate_error","q2_hi","q2_low_coordinate_error","q1_square_hi","q1_square_error","q2_square_hi","q2_square_error","radius_square","first_subtraction","unfused_margin","fused_rounded_coordinate_margin","exact_expansion_margin","robust_line_intersection_length","smallest_subnormal","subnormal_add"};
    for(int k=0;k<16;k++)printf("%s,%.17g\n",names[k],out.v[k]);
}
