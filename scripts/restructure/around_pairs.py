import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'latex2tm'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load
from scan import tostr
OK={('(',')'),('[',']'),('[',')'),('(',']'),('{','}'),('<langle>','<rangle>'),('|','<rangle>'),('<langle>','|'),('|','|'),('<||>','<||>'),('.','|'),('{','<nobracket>'),('<nobracket>','}'),('.','<nobracket>'),('<lfloor>','<rfloor>'),('<lceil>','<rceil>'),('{','.'),('.','}'),('<nobracket>','|'),(']','['),(']',']'),('[','['),('.',')'),('(','.')}
def rec(x,path):
    if isinstance(x,str): return
    if x[0] in ('around','around*') and len(x)==4:
        # delimiters may be trees (e.g. <nobracket>); compare their string form
        pair=(tostr(x[1]),tostr(x[3]))
        # a half bracket (other side <nobracket>) splits a pair across rows/cells
        if pair not in OK and '<nobracket>' not in pair:
            par=path[-1] if path else x
            print('PAIR',repr(pair),'\n    ',tostr(par)[:400])
    for c in x[1:]: rec(c,path+[x] if x[0]=='concat' else path)
rec(load(sys.argv[1]),[])
