import sys
from rwlib import *
src, dst = sys.argv[1:3]
d = load(src); sc = []
visit(d, lambda y: sc.append(y) if is_node(y, 'screens') else None)
for k, s in enumerate(sc[0][1:], 1):
    t = []; visit(s, lambda y: t.append(y) if is_node(y, 'mytitle') else None)
    if t:
        t[0][1] = ['concat', t[0][1], ['with', 'color', '#f2f2f2', 'font-size', '0.3', ' SLIDEMARK%d' % k]]
dump(d, dst)
