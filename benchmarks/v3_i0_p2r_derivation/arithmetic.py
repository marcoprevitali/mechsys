"""Exact-rational interval arithmetic with binary64 RN endpoint rounding.

No decimal approximation is used for a proof decision. Square roots use an
integer binary search and exact squared-midpoint comparisons. Subnormals are
supported. Signed zero is preserved in the input manifest, not interval order.
"""
from fractions import Fraction as Q
from functools import lru_cache
import math, struct

U=Q(1,2**53)
ETA=Q(1,2**1074)
MAX_BITS=0x7fefffffffffffff
LOG=[]
RECORD=False
CONTRACT=False

def power(e):return Q(2**e) if e>=0 else Q(1,2**(-e))
def from_bits(b):
    if isinstance(b,str):b=int(b.removeprefix('0x'),16)
    sign=-1 if b>>63 else 1;exp=(b>>52)&2047;mant=b&((1<<52)-1)
    assert exp!=2047,'Nonfinite binary64 is outside the certificate'
    return sign*Q(mant if exp==0 else (1<<52)+mant)*power(-1074 if exp==0 else exp-1075)
def bits(x):return struct.pack('>d',float(x)).hex()
def exact(x):
    if isinstance(x,Q):return x
    if isinstance(x,int):return Q(x)
    return from_bits(bits(x))
def floorlog2(x):
    assert x>0
    e=x.numerator.bit_length()-x.denominator.bit_length()
    return e-1 if x<power(e) else e
def round_even(q):
    n,r=divmod(q.numerator,q.denominator)
    return n+(2*r>q.denominator or (2*r==q.denominator and n%2))
def rn(x):
    x=Q(x)
    if not x:return Q(0)
    sign=-1 if x<0 else 1;x=abs(x)
    assert x<=from_bits(MAX_BITS),'Overflow is not allowed'
    quantum=power(max(-1074,floorlog2(x)-52))
    return sign*round_even(x/quantum)*quantum

@lru_cache(maxsize=32768)
def sqrt_rn(x):
    x=Q(x);assert x>=0
    if not x:return Q(0)
    lo=0;hi=MAX_BITS
    # Positive binary64 bit patterns have the same order as their real values.
    while lo<hi:
        mid=(lo+hi+1)//2;q=from_bits(mid)
        if q*q<=x:lo=mid
        else:hi=mid-1
    a=from_bits(lo)
    if a*a==x:return a
    b=from_bits(lo+1);m=(a+b)/2
    return b if x>m*m or (x==m*m and lo%2) else a

class I:
    __slots__=('lo','hi','product')
    def __init__(self,lo,hi=None):
        self.lo=exact(lo);self.hi=self.lo if hi is None else exact(hi)
        self.product=None
        assert self.lo<=self.hi
    def __neg__(self):return I(-self.hi,-self.lo)
    def __add__(self,b):return op('add',self,b)
    def __sub__(self,b):return op('sub',self,b)
    def __mul__(self,b):return op('mul',self,b)
    def __truediv__(self,b):return op('div',self,b)
    def absmax(self):return max(abs(self.lo),abs(self.hi))
    def width(self):return self.hi-self.lo
    def contains(self,x):return self.lo<=exact(x)<=self.hi
    def point(self):assert self.lo==self.hi;return self.lo
    def data(self):
        return dict(lo=str(self.lo),hi=str(self.hi),lo_binary64=bits(self.lo),hi_binary64=bits(self.hi),
          lo_display=float(self.lo),hi_display=float(self.hi),width=str(self.width()),width_display=float(self.width()))

def interval(x):return x if isinstance(x,I) else I(x)
def hull(a,b):a=interval(a);b=interval(b);return I(min(a.lo,b.lo),max(a.hi,b.hi))
def realop(kind,*args):
    a=[interval(v) for v in args]
    if kind=='add':return I(a[0].lo+a[1].lo,a[0].hi+a[1].hi)
    if kind=='sub':return I(a[0].lo-a[1].hi,a[0].hi-a[1].lo)
    if kind in ['mul','fma']:
        vals=[x*y for x in [a[0].lo,a[0].hi] for y in [a[1].lo,a[1].hi]]
        z=I(min(vals),max(vals))
        return realop('add',z,a[2]) if kind=='fma' else z
    if kind=='div':
        assert not a[1].lo<=0<=a[1].hi, 'Uncertified divisor'
        vals=[x/y for x in [a[0].lo,a[0].hi] for y in [a[1].lo,a[1].hi]]
        return I(min(vals),max(vals))
    raise ValueError(kind)

def op(kind,*args,tag=''):
    a=[interval(v) for v in args]
    if kind=='sqrt':
        assert a[0].lo>=0,'Uncertified square root domain'
        out=I(sqrt_rn(a[0].lo),sqrt_rn(a[0].hi));real=None
        # Bound local sqrt rounding by u times an upper enclosure plus eta/2.
        local=U*out.hi/(1-U)+ETA/2
    else:
        real=realop(kind,*a);out=I(rn(real.lo),rn(real.hi))
        local=U*real.absmax()+ETA/2
        if real.lo==real.hi:local=abs(out.lo-real.lo)
        # A plain PTX mul followed by add/sub may be contracted by ptxas.
        # Retain a union of the separate and one-FMA paths, not the incorrect
        # assertion that the separately rounded point encloses the fused one.
        if CONTRACT and kind in ['add','sub']:
            for j in [0,1]:
                if a[j].product is None:continue
                p,q=a[j].product;other=a[1-j]
                if kind=='sub' and j==1:p=-p
                if kind=='sub' and j==0:other=-other
                fused=realop('fma',p,q,other)
                out=hull(out,I(rn(fused.lo),rn(fused.hi)))
                local=max(local,U*fused.absmax()+ETA/2)
    if RECORD:
        LOG.append(dict(tag=tag,operation=kind,input=[v.data() for v in a],
          exact_real_hull=real.data() if real is not None else None,output=out.data(),local_rounding_bound=str(local),
          denominator_floor=str(min(abs(a[1].lo),abs(a[1].hi))) if kind=='div' else None))
    if kind=='mul':out.product=tuple(a)
    return out

def fma(a,b,c,tag=''):return op('fma',a,b,c,tag=tag)
def sqrt(a,tag=''):return op('sqrt',a,tag=tag)
def dot(a,b):return fma(a[2],b[2],fma(a[0],b[0],interval(a[1])*b[1]))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def selftest():
    # Midpoint, tie-even, binade, negative and subnormal witnesses.
    for x in [Q(0),Q(1),Q(1)+power(-53),Q(1)+3*power(-53),-Q(1)-power(-53),
              power(-1075),3*power(-1075),power(-1022)-power(-1075)]:
        assert rn(x)==Q.from_float(float(x))
    assert rn(Q(1)+power(-53))==1
    assert rn(Q(1)+3*power(-53))==1+power(-51)
    assert sqrt_rn(Q(2))==exact(math.sqrt(2))
    for b in [1,0x0010000000000000,0x3fefffffffffffff,0x3ff0000000000000,0x4000000000000000]:
        a=from_bits(b);c=from_bits(b+1);m=(a+c)/2
        assert sqrt_rn(m*m)==(c if b%2 else a)
        assert sqrt_rn(a*a)==a
    assert op('fma',1+power(-27),1-power(-27),-1).point()==-power(-54)
    assert ((I(1+power(-27))*I(1-power(-27)))-I(1)).point()==0
    assert (I(-1,1)*I(-1,1)).lo==-1 # dependency over-enclosure, never omit it

if __name__=='__main__':selftest();print('Exact RN and sqrt midpoint witnesses PASS')
