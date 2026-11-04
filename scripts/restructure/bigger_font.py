"""Base font 10pt in a slide deck; the listed (dense) slides keep 9pt for their body."""
import sys
from rwlib import *
src, dst = sys.argv[1:3]
dense = [int(x) for x in sys.argv[3:]]
d = load(src); n = [0]
def f(y):
    if is_node(y, 'associate') and y[1] == 'font-base-size':
        y[2] = '10'; n[0] += 1
visit(d, f); assert n[0] == 1
sc = []; visit(d, lambda y: sc.append(y) if is_node(y, 'screens') else None)
for k in dense:
    doc = sc[0][k][1]
    assert is_node(doc, 'document')
    kids = doc[1:]
    i = next((j for j, c in enumerate(kids) if is_node(c, 'mytitle')), -1)
    head, rest = kids[:i + 1], kids[i + 1:]
    doc[1:] = head + [['with', 'font-size', '0.9', ['document'] + rest]]
dump(d, dst)
print(src.split('/')[-1], 'dense', dense)
