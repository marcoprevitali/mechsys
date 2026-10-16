// Bounded actual legacy Solve. Diagnostic callbacks ONLY read solver state.
#include <mechsys/lbmdem/Domain.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <cstring>
#include <vector>
#include <stdexcept>
using Tree=boost::property_tree::ptree;
static std::string outdir,casename;
static void num(Tree &t,const char *k,double x){DEM::Checkpoint::number(t,k,x);}
static void vec(Tree &t,const char *k,Vec3_t const &x){DEM::Checkpoint::vector(t,k,x);}
static Tree numbers(std::vector<double> const &v){Tree a;for(double x:v){Tree b;num(b,"",x);a.push_back({"",b});}return a;}
static void save(std::string const &name,Tree const &t){boost::property_tree::write_json(outdir+"/"+name,t);}
#ifdef USE_CUDA
static void ck(cudaError_t e){if(e!=cudaSuccess)throw std::runtime_error(cudaGetErrorString(e));}
template<class T> static std::vector<T> read(T const *p,size_t n){std::vector<T> v(n);if(n)ck(cudaMemcpy(v.data(),p,n*sizeof(T),cudaMemcpyDeviceToHost));return v;}
static Vec3_t cv(real3 const &v){return Vec3_t(v.x,v.y,v.z);}
#endif
static Tree particles(LBMDEM::Domain &d){
    Tree all;
#ifdef USE_CUDA
    auto dyn=read(d.DEMDOM.pDynParticlesCU,d.DEMDOM.Particles.Size());
    auto par=read(d.DEMDOM.pParticlesCU,d.DEMDOM.Particles.Size());
#endif
    for(size_t i=0;i<d.DEMDOM.Particles.Size();i++){
        auto *p=d.DEMDOM.Particles[i];Tree t;t.put("id",p->PersistentId);t.put("index",i);
        num(t,"R",p->Props.R);num(t,"Dmax",p->Dmax);num(t,"mass",p->Props.m);t.put("free",int(p->IsFree()));
        std::vector<double> q;
#ifdef USE_CUDA
        auto &a=dyn[i];vec(t,"x",cv(a.x));vec(t,"xb",cv(a.xb));vec(t,"v",cv(a.v));vec(t,"w",cv(a.w));vec(t,"wb",cv(a.wb));vec(t,"wa",cv(a.wa));
        vec(t,"F",cv(a.F));vec(t,"Flbm",cv(a.Flbm));vec(t,"T",cv(par[i].T));q={a.Q.w,a.Q.x,a.Q.y,a.Q.z};
#else
        vec(t,"x",p->x);vec(t,"xb",p->xb);vec(t,"v",p->v);vec(t,"w",p->w);vec(t,"wb",p->wb);vec(t,"wa",p->wa);
        vec(t,"F",p->F);vec(t,"Flbm",p->Flbm);vec(t,"T",p->T);q={p->Q(0),p->Q(1),p->Q(2),p->Q(3)};
#endif
        t.add_child("Q",numbers(q));all.push_back({"",t});
    }return all;
}
static Tree pairs(LBMDEM::Domain &d){Tree a;
#ifdef USE_CUDA
    auto v=read(d.pPaCeV,2*d.lbmdemaux.nvc);
    for(size_t i=0;i<v.size();i+=2){Tree t;t.put("cell",v[i]);t.put("particle",v[i+1]);a.push_back({"",t});}
#else
    for(auto const &p:d.ParCellPairs){Tree t;t.put("cell",p.ICell(0)+10*(p.ICell(1)+10*p.ICell(2)));t.put("particle",p.IPar);a.push_back({"",t});}
#endif
    return a;
}
static Tree grid(LBMDEM::Domain &d,bool full){Tree a;auto &l=d.LBMDOM;
#ifdef USE_CUDA
    auto f=read(l.pF,l.Ncells*15),ft=read(l.pFtemp,l.Ncells*15),g=read(d.pGamma,l.Ncells),om=read(d.pOmeis,l.Ncells*15),rho=read(l.pRho,l.Ncells);
    auto vel=read(l.pVel,l.Ncells),bf=read(l.pBForce,l.Ncells);
#endif
    for(size_t z=0;z<10;z++)for(size_t y=0;y<10;y++)for(size_t x=0;x<10;x++){
        Tree t;size_t ic=x+10*(y+10*z);t.put("cell",ic);std::vector<double> pop,post,omega;
#ifdef USE_CUDA
        num(t,"rho",rho[ic]);num(t,"gamma",g[ic]);vec(t,"vel",cv(vel[ic]));vec(t,"bforce",cv(bf[ic]));
        for(size_t k=0;k<15;k++){pop.push_back(f[ic*15+k]);post.push_back(ft[ic*15+k]);omega.push_back(om[ic*15+k]);}
#else
        num(t,"rho",l.Rho[0][x][y][z]);num(t,"gamma",l.Gamma[x][y][z]);vec(t,"vel",l.Vel[0][x][y][z]);vec(t,"bforce",l.BForce[0][x][y][z]);
        for(size_t k=0;k<15;k++){pop.push_back(l.F[0][x][y][z][k]);post.push_back(l.Ftemp[0][x][y][z][k]);omega.push_back(l.Omeis[x][y][z][k]);}
#endif
        t.add_child("f",numbers(pop));t.add_child("omega",numbers(omega));if(full)t.add_child("scratch",numbers(post));a.push_back({"",t});
    }return a;
}
static void report(LBMDEM::Domain &d,void *){
    Tree t;t.put("step",d.iter);num(t,"time",d.Time);t.put("dem_iter",d.DEMDOM.iter);num(t,"dem_time",d.DEMDOM.Time);num(t,"lbm_time",d.LBMDOM.Time);
    num(t,"Evis",d.DEMDOM.Evis);num(t,"Efric",d.DEMDOM.Efric);num(t,"Wext",d.DEMDOM.Wext);
    Tree caches,vertices,common;
#ifdef USE_CUDA
    auto aa=read(d.DEMDOM.pA,d.DEMDOM.Particles.Size()),ww=read(d.DEMDOM.pWdot,d.DEMDOM.Particles.Size());
    auto vv=read(d.DEMDOM.pVertsCU,d.DEMDOM.demaux.nverts),vo=read(d.DEMDOM.pVertsoCU,d.DEMDOM.demaux.nverts);
    for(size_t i=0;i<aa.size();i++){Tree v;vec(v,"A",cv(aa[i]));vec(v,"Wdot",cv(ww[i]));caches.push_back({"",v});}
    for(size_t i=0;i<vv.size();i++){Tree v;vec(v,"current",cv(vv[i]));vec(v,"reference",cv(vo[i]));vertices.push_back({"",v});}
    auto cc=read(d.DEMDOM.pComInteractons,d.DEMDOM.demaux.ncoint);
    for(auto &c:cc){Tree v;vec(v,"Fnnet",cv(c.Fnnet));vec(v,"Ftnet",cv(c.Ftnet));vec(v,"Fndpot",cv(c.Fndpot));vec(v,"Ftdpot",cv(c.Ftdpot));vec(v,"Fther",cv(c.Fther));num(v,"Epot",c.Epot);num(v,"dEvis",c.dEvis);num(v,"dEfric",c.dEfric);common.push_back({"",v});}
#else
    for(size_t i=0;i<d.DEMDOM.Particles.Size();i++){Tree v;vec(v,"A",d.DEMDOM.A[i]);vec(v,"Wdot",d.DEMDOM.Wdot[i]);caches.push_back({"",v});auto *p=d.DEMDOM.Particles[i];
        for(size_t k=0;k<p->Verts.Size();k++){Tree v;vec(v,"current",*p->Verts[k]);vec(v,"reference",*p->Vertso[k]);vertices.push_back({"",v});}}
    for(auto *b:d.DEMDOM.Interactons){auto *c=static_cast<DEM::CInteracton *>(b);Tree v;vec(v,"Fnet",c->Fnet);vec(v,"Ftnet",c->Ftnet);vec(v,"Fndpot",c->Fndpot);vec(v,"Ftdpot",c->Ftdpot);vec(v,"Fther",c->Fther);num(v,"Epot",c->Epot);num(v,"dEvis",c->dEvis);num(v,"dEfric",c->dEfric);common.push_back({"",v});}
#endif
    t.add_child("caches",caches);t.add_child("vertices",vertices);t.add_child("common",common);
    t.add_child("particles",particles(d));t.add_child("grid",grid(d,true));t.add_child("pairs",pairs(d));
    Tree hist;
    for(auto *b:d.DEMDOM.Interactons){auto *c=dynamic_cast<DEM::CInteractonSphere *>(b);if(!c)throw std::runtime_error("sphere history expected");Tree h;h.put("a",c->P1->PersistentId);h.put("b",c->P2->PersistentId);
        vec(h,"F1",c->F1);vec(h,"F2",c->F2);vec(h,"T1",c->T1);vec(h,"T2",c->T2);vec(h,"Fdvv",c->Fdvv);vec(h,"Fdr",c->Fdr);vec(h,"vtprev",c->vt_prev);num(h,"PrevDelta",c->PrevDelta);h.put("InContact",int(c->InContact));hist.push_back({"",h});}
    t.add_child("histories",hist);
#ifdef USE_CUDA
    DEM::Checkpoint::gpu_history(t,"gpu_vv",d.DEMDOM.bDynInteractonsVV,true);
    auto da=read(d.DEMDOM.pdemaux,1);auto la=read(d.LBMDOM.plbmaux,1);
    num(t,"device_dem_time",da[0].Time);t.put("device_dem_iter",da[0].iter);num(t,"device_lbm_time",la[0].Time);t.put("device_lbm_iter",la[0].iter);
#endif
    save("state-"+std::to_string(d.iter)+".json",t);
}
#ifdef MECHSYS_EXCHANGE_AUDIT
namespace A=MechSysExchangeAudit;
static std::vector<A::Collision> collisions;
static std::vector<A::Claim> claims;
#ifdef USE_CUDA
static A::Collision *dc=nullptr;static A::Claim *di=nullptr;
#endif
static void stage(void *ptr,const char *name){auto &d=*static_cast<LBMDEM::Domain *>(ptr);std::string s(name),prefix="step-"+std::to_string(d.iter)+"-";
#ifdef USE_CUDA
    ck(cudaDeviceSynchronize());
#endif
    if(s=="before_imprint"){
        if(d.LBMDOM.Nl!=1 || d.LBMDOM.Nneigh!=15)throw std::runtime_error("audit unsupported lattice");
        size_t n=d.ParCellPairs.Size();
#ifdef USE_CUDA
        n=d.lbmdemaux.nvc;
        if(d.lbmdemaux.nfc)throw std::runtime_error("audit spheres only");
#endif
        if(n>10000)throw std::runtime_error("audit claim capacity exceeded before launch");
        claims.assign(n,{});collisions.assign(15000,{});A::claim_capacity=n;A::collision_capacity=collisions.size();
#ifdef USE_CUDA
        if(di)ck(cudaFree(di));if(dc)ck(cudaFree(dc));
        ck(cudaMalloc(&di,std::max(size_t(1),n)*sizeof(A::Claim)));ck(cudaMalloc(&dc,collisions.size()*sizeof(A::Collision)));
        ck(cudaMemset(di,0,std::max(size_t(1),n)*sizeof(A::Claim)));ck(cudaMemset(dc,0,collisions.size()*sizeof(A::Collision)));
        ck(cudaMemcpyToSymbol(A::gpu_claim,&di,sizeof(di)));ck(cudaMemcpyToSymbol(A::gpu_collision,&dc,sizeof(dc)));
        ck(cudaMemcpyToSymbol(A::gpu_claim_capacity,&n,sizeof(n)));size_t nc=collisions.size();ck(cudaMemcpyToSymbol(A::gpu_collision_capacity,&nc,sizeof(nc)));
#else
        A::cpu_claim=claims.data();A::cpu_collision=collisions.data();
#endif
    }
    Tree t;t.put("stage",s);t.put("step",d.iter);num(t,"time",d.Time);vec(t,"Per",d.DEMDOM.Per);
    t.add_child("particles",particles(d));
    if(s=="before_imprint" || s=="before_rebuild" || s=="after_rebuild")t.add_child("pairs",pairs(d));
    if(s=="before_collision")t.add_child("grid",grid(d,false));
    if(s=="after_imprint"){
#ifdef USE_CUDA
        if(!claims.empty())ck(cudaMemcpy(claims.data(),di,claims.size()*sizeof(A::Claim),cudaMemcpyDeviceToHost));
#endif
        Tree all;auto ps=pairs(d);size_t i=0;
        for(auto const &p:ps){Tree c=p.second;auto &r=claims.at(i++);c.put("computed",r.computed);c.put("accepted",r.accepted);num(c,"gamma",r.gamma);num(c,"B",r.B);
            c.add_child("omega",numbers(std::vector<double>(r.omega,r.omega+15)));c.add_child("force",numbers(std::vector<double>(r.force,r.force+3)));c.add_child("torque",numbers(std::vector<double>(r.torque,r.torque+3)));
            c.add_child("lever",numbers(std::vector<double>(r.lever,r.lever+3)));c.add_child("surface",numbers(std::vector<double>(r.surface,r.surface+3)));all.push_back({"",c});}
        t.add_child("claims",all);
    }
    if(s=="after_collision"){
#ifdef USE_CUDA
        ck(cudaMemcpy(collisions.data(),dc,collisions.size()*sizeof(A::Collision),cudaMemcpyDeviceToHost));int over=0;ck(cudaMemcpyFromSymbol(&over,A::gpu_overflow,sizeof(over)));if(over)throw std::runtime_error("audit device buffer overflow");
#endif
        std::ofstream f(outdir+"/"+prefix+"collision.csv");f<<std::setprecision(17);
        f<<"cell,k,before,after,neq,omega,gamma,B,rho,tau0,tau,alpha,bgk,solid,other\n";
        for(size_t i=0;i<collisions.size();i++){auto &r=collisions[i];f<<i/15<<','<<i%15<<','<<r.before<<','<<r.after<<','<<r.neq<<','<<r.omega<<','<<r.gamma<<','<<r.B<<','<<r.rho<<','<<r.tau0<<','<<r.tau<<','<<r.alpha<<','<<r.bgk<<','<<r.solid<<','<<r.other<<'\n';}
    }
    save(prefix+s+".json",t);
}
#endif
int main(int argc,char **argv) try {
    if(argc<3)throw std::runtime_error("probe CASE OUTPUT [VV]");casename=argv[1];outdir=argv[2];std::filesystem::create_directories(outdir);
    LBMDEM::Domain d(D3Q15,.1,iVec3_t(10,10,10),1,1);d.LBMDOM.Sc=0;d.Alpha=.4;d.PeriodicX=d.PeriodicY=d.PeriodicZ=true;
    d.DEMDOM.UseVelocityVerlet=argc>3 && atoi(argv[3]);
#ifdef MECHSYS_CELL_COVERAGE_FIX_AVAILABLE
    d.ConservativeSphereCells=getenv("P1_MODE") && std::string(getenv("P1_MODE"))=="1";
#endif
#ifdef MECHSYS_TWELVE_EDGE_PROXY_AVAILABLE
    d.CorrectTwelveEdgeProxy=getenv("P2_MODE") && std::string(getenv("P2_MODE"))=="1";
#endif
#ifdef MECHSYS_ROBUST_EDGE_PROXY_AVAILABLE
    d.RobustTwelveEdgeProxy=getenv("P2R_MODE") && std::string(getenv("P2R_MODE"))=="1";
#endif
    Vec3_t x(5,5,5),u(0,0,0);double R=1.2;
    if(casename=="zero")R=.05;
    if(casename=="partial")x=Vec3_t(5.45,5.2,5.1);
    if(casename=="boundary")x=Vec3_t(5.49,5,5);
    if(casename=="periodic")x=Vec3_t(.2,5.2,5.1);
    if(casename=="shared")x=Vec3_t(3.81,5,5);
    if(casename=="contact"){x=Vec3_t(4.9,5,5);R=.1;}
    if(getenv("P1_RADIUS"))R=atof(getenv("P1_RADIUS"));
    if(getenv("P1_POSITION")){std::istringstream s(getenv("P1_POSITION"));s>>x(0)>>x(1)>>x(2);}
    d.DEMDOM.AddSphere(-1,x,R,100);
    if(getenv("P2_NONCANONICAL"))d.DEMDOM.Particles[0]->Dmax+=.1;
    if(getenv("P2_SC"))d.LBMDOM.Sc=.17;
    if(getenv("P2_LIMITER_RISK"))u=Vec3_t(1,0,0); // deliberately invalid fluid populations; reject before collision
    if(casename=="shared")d.DEMDOM.AddSphere(-2,Vec3_t(6.19,5,5),R,100);
    if(casename=="contact")d.DEMDOM.AddSphere(-2,Vec3_t(5.099,5,5),R,100);
    if(casename=="rebuild")d.Alpha=.0001;
    if(casename=="fconv")d.Fconv=2;
    if(getenv("P1_ALPHA"))d.Alpha=atof(getenv("P1_ALPHA"));
    for(auto *p:d.DEMDOM.Particles){p->Props.Kn=1;p->Props.Kt=.2;p->Props.Gn=0;p->Props.Gt=0;p->Props.Mu=.5;p->Props.Beta=.1;p->Props.Eta=.1;p->Props.Gv=p->Props.Gm=0;
        p->v=Vec3_t(.002,-.001,.0005);p->Q=Quaternion_t(sqrt(.5),sqrt(.5),0,0);
        if(casename=="fixed"){p->FixVeloc();u=Vec3_t(.002,-.001,.0005);}
        if(casename=="rotating"){p->v=OrthoSys::O;p->w=Vec3_t(.001,.002,-.001);}
        if(casename=="shared" && p->Tag==-2)p->v=Vec3_t(-.001,0,0);
        if(casename=="contact")p->w=Vec3_t(.001,.002,-.001);
        if(getenv("P1_VELOCITY")){std::istringstream s(getenv("P1_VELOCITY"));s>>p->v(0)>>p->v(1)>>p->v(2);}
        if(casename=="empty")p->FixVeloc();
    }
    for(size_t z=0;z<10;z++)for(size_t y=0;y<10;y++)for(size_t x0=0;x0<10;x0++)d.LBMDOM.Initialize(0,iVec3_t(x0,y,z),1,u);
#ifdef MECHSYS_EXCHANGE_AUDIT
    if(getenv("MECHSYS_EXCHANGE_AUDIT") && std::string(getenv("MECHSYS_EXCHANGE_AUDIT"))=="1")A::stage=stage;
#endif
    Tree fixture;fixture.put("case",casename);num(fixture,"dx",d.dx);num(fixture,"dt",d.dt);num(fixture,"Alpha",d.Alpha);num(fixture,"Fconv",d.Fconv);num(fixture,"Sc",d.LBMDOM.Sc);num(fixture,"tau0",d.LBMDOM.Tau[0]);vec(fixture,"u_initial",u);save("fixture.json",fixture);
    int steps=casename=="shared"?1:(casename=="contact"?3:2);
    d.Solve((steps-.5)*d.dt,d.dt,nullptr,report,nullptr,false,1);
    return 0;
} MECHSYS_CATCH
