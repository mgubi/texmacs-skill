"""Phase 2: fill the text of links to other lectures with the numbers that
TeXmacs computed for the target documents (their <references> collection).

usage: fill_xref.py outdir base...
Reads outdir/<base>.tm (typeset) for numbers and rewrites outdir/<base>.scm.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, walk, is_node

out, bases = sys.argv[1], sys.argv[2:]

def refs(base):
    s = open(os.path.join(out, base + '.tm'), encoding='latin-1').read()
    i = s.find('<\\references>')
    d = {}
    for m in re.finditer(r'<associate\|([^|>]+)\|<tuple\|([^|]*)\|', s[i:]):
        d[m.group(1)] = m.group(2)
    return d

R = {b: refs(b) for b in bases}
missing = 0
for b in bases:
    t = load(os.path.join(out, b + '.scm'))
    def f(x):
        global missing
        if is_node(x, 'hlink') and isinstance(x[1], str) and x[1].startswith('XREF@'):
            _, kind, d, l = x[1].split('@', 3)
            d = d.replace('-', '_')
            num = R.get(d, {}).get(l)
            if num is None:
                print('missing', b, d, l); missing += 1; num = '??'
            x[1] = '(%s)' % num if kind == 'eq' else num
        return x
    t = walk(t, f)
    dump(t, os.path.join(out, b + '.scm'))
print('filled; missing', missing)
