"""make a print preview: screens -> pages (for checking only)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, walk, is_node
t = load(sys.argv[1])
def f(x):
    if is_node(x, 'screens'):
        out = []
        for k, s in enumerate(x[1:]):
            if k: out.append(['new-page*'])
            out.extend(s[1][1:])
        return ('splice', out)
    return x
t = walk(t, f)
dump(t, sys.argv[2])
