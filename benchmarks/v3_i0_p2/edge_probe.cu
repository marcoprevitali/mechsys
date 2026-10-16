// Direct production helper calls, same input bits on both backends.
#include <mechsys/lbmdem/Domain.h>
#include <iostream>
#include <iomanip>
struct Input { double x[3],c[3],r,dx; };
#ifdef USE_CUDA
__global__ void evaluate(Input *in,double *out,size_t n) {
    size_t i=blockIdx.x*blockDim.x+threadIdx.x;if(i>=n)return;
    auto f=in[i];real3 x=make_real3(f.x[0],f.x[1],f.x[2]),c=make_real3(f.c[0],f.c[1],f.c[2]);
    out[i*14]=LBMDEM::cudaSphereCube(x,c,f.r,f.dx);
#ifdef MECHSYS_TWELVE_EDGE_PROXY_AVAILABLE
    out[i*14+1]=LBMDEM::cudaSphereCube12EdgeCorrected(x,c,f.r,f.dx,out+i*14+2);
#endif
}
#endif
int main(){std::vector<Input> in;Input f;while(std::cin>>f.x[0]>>f.x[1]>>f.x[2]>>f.c[0]>>f.c[1]>>f.c[2]>>f.r>>f.dx)in.push_back(f);
    std::vector<double> out(14*in.size(),0.0);
#ifdef USE_CUDA
    Input *di;double *dout;cudaMalloc(&di,in.size()*sizeof(Input));cudaMalloc(&dout,out.size()*sizeof(double));cudaMemset(dout,0,out.size()*sizeof(double));
    cudaMemcpy(di,in.data(),in.size()*sizeof(Input),cudaMemcpyHostToDevice);evaluate<<<(in.size()+255)/256,256>>>(di,dout,in.size());
    auto err=cudaDeviceSynchronize();if(err!=cudaSuccess){std::cerr<<cudaGetErrorString(err);return 2;}
    cudaMemcpy(out.data(),dout,out.size()*sizeof(double),cudaMemcpyDeviceToHost);cudaFree(di);cudaFree(dout);
#else
    for(size_t i=0;i<in.size();i++){auto a=in[i];Vec3_t x(a.x[0],a.x[1],a.x[2]),c(a.c[0],a.c[1],a.c[2]);out[i*14]=DEM::SphereCube(x,c,a.r,a.dx);
#ifdef MECHSYS_TWELVE_EDGE_PROXY_AVAILABLE
        out[i*14+1]=DEM::SphereCube12EdgeCorrected(x,c,a.r,a.dx,out.data()+i*14+2);
#endif
    }
#endif
    std::cout<<std::setprecision(17);for(size_t i=0;i<in.size();i++){std::cout<<i;for(size_t k=0;k<14;k++)std::cout<<','<<out[i*14+k];std::cout<<'\n';}return 0;
}
