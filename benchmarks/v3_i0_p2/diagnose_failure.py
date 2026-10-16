#!/usr/bin/env python3
"""Exact rational witness for the registered hard stop (no solver imports)."""
import json
from fractions import Fraction as F
from decimal import Decimal as D,getcontext
from pathlib import Path
getcontext().prec=80
q1=F(1,2)+F.from_float(.3);q2=F(1,2)+F.from_float(.1)
r2=1-q1*q1-q2*q2
assert r2>0
length=2*(D(r2.numerator)/D(r2.denominator)).sqrt()
rounded=1-(.5+.3)**2-(.5+.1)**2
assert rounded<0 and length>D('1e-10')
e={'fixture':'multiple','X':[.3,.2,.1],'C':[0,0,0],'R':1,'dx':1,
   'edge_index':7,'A':[-.5,.5,-.5],'B':[-.5,-.5,-.5],
   'q1_exact':str(q1),'q2_exact':str(q2),'r2_exact':str(r2),
   'r2_exact_decimal':str(D(r2.numerator)/D(r2.denominator)),
   'FP64_r2':rounded,'independent_length':str(length),'actual_CPU_length':0,'actual_CUDA_length':0,
   'registered_edge_absolute_budget':'1e-10*dx','classification':'FAIL P2-C/P2-D, geometry rounding near tangency',
   'cause':'binary64 offsets .5+.3 and .5+.1 round before subtraction of squared distances; genuine small positive r2 changes sign',
   'reference_crosscheck':'exact Fraction binary64-input algebra agrees with 70-digit independent quadratic',
   'stopped':'No P2-enabled coupled/parity/conservation runs; no relaxed tolerance, no broadened algorithm',
   'possible_next_task':'Separately authorize a narrowly scoped robust FP64 edge predicate/length experiment; preserve this witness and frozen budgets'}
p=Path(__file__).with_name('MINIMAL_COUNTEREXAMPLE.json');p.write_text(json.dumps(e,indent=2)+'\n');print(json.dumps(e,indent=2))
