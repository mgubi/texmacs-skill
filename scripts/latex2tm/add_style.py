"""append a package to the style tuple of a dumped document"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, is_node
t = load(sys.argv[1]); pkg = sys.argv[3]
for c in t[1:]:
    if is_node(c, 'style'):
        tup = c[1] if is_node(c[1], 'tuple') else ['tuple', c[1]]
        if pkg not in tup[1:]:
            tup.append(pkg)
        c[1] = tup
dump(t, sys.argv[2])
