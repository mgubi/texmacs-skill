import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, walk, is_node
t = load(sys.argv[1])
t = walk(t, lambda x: None if is_node(x, 'hide-preamble') else x)
dump(t, sys.argv[2])
