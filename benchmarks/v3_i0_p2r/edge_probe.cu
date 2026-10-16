// Direct production legacy, failed-P2 and robust-P2R helpers, identical input bits.
#include <mechsys/lbmdem/Domain.h>
#include <iostream>
#include <iomanip>
struct Input {double x[3],c[3],r,dx;};
struct Output {double legacy,failed,total,edge[12];MechSysRobustEdge::Trace trace[12];};
#ifdef USE_CUDA
__global__ void evaluate(Input *in,Output *out,size_t n) {
    size_t i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
    auto f=in[i];real3 x=make_real3(f.x[0],f.x[1],f.x[2]),c=make_real3(f.c[0],f.c[1],f.c[2]);
    out[i].legacy=LBMDEM::cudaSphereCube(x,c,f.r,f.dx);
    out[i].failed=LBMDEM::cudaSphereCube12EdgeCorrected(x,c,f.r,f.dx);
    out[i].total=LBMDEM::cudaSphereCube12EdgeRobust(x,c,f.r,f.dx,out[i].edge,out[i].trace);
}
#endif
int main(){std::vector<Input> in;Input f;while(std::cin>>f.x[0]>>f.x[1]>>f.x[2]>>f.c[0]>>f.c[1]>>f.c[2]>>f.r>>f.dx)in.push_back(f);
    std::vector<Output> out(in.size());
#ifdef USE_CUDA
    Input *di;Output *dout;cudaMalloc(&di,in.size()*sizeof(Input));cudaMalloc(&dout,out.size()*sizeof(Output));
    cudaMemcpy(di,in.data(),in.size()*sizeof(Input),cudaMemcpyHostToDevice);evaluate<<<(in.size()+63)/64,64>>>(di,dout,in.size());
    auto err=cudaDeviceSynchronize();if(err!=cudaSuccess){std::cerr<<cudaGetErrorString(err);return 2;}
    cudaMemcpy(out.data(),dout,out.size()*sizeof(Output),cudaMemcpyDeviceToHost);cudaFree(di);cudaFree(dout);
#else
    for(size_t i=0;i<in.size();i++){auto a=in[i];Vec3_t x(a.x[0],a.x[1],a.x[2]),c(a.c[0],a.c[1],a.c[2]);
        out[i].legacy=DEM::SphereCube(x,c,a.r,a.dx);out[i].failed=DEM::SphereCube12EdgeCorrected(x,c,a.r,a.dx);
        out[i].total=DEM::SphereCube12EdgeRobust(x,c,a.r,a.dx,out[i].edge,out[i].trace);
    }
#endif
    std::cout<<std::setprecision(17);
    std::cout<<"fixture,legacy_length,failed_P2_length,total_length,edge,length,margin_hi,margin_lo,margin_sign,components,scale,root\n";
    for(size_t i=0;i<in.size();i++)for(size_t e=0;e<12;e++){auto &a=out[i];auto &t=a.trace[e];
        std::cout<<i<<','<<a.legacy<<','<<a.failed<<','<<a.total<<','<<e<<','<<a.edge[e]<<','<<t.margin_hi<<','<<t.margin_lo<<','<<t.sign<<','<<t.components<<','<<t.scale<<','<<t.root<<'\n';}
    return 0;
}
