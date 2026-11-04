import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, walk, is_node
t = load(sys.argv[1])
def f(x):
    if is_node(x) and x[0] in ('vspace', 'vspace*') and isinstance(x[1], str) and x[1].startswith('-'):
        return None
    return x
dump(walk(t, f), sys.argv[2])
