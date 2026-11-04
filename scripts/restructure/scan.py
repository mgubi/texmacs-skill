"""Scan math in an stree for bare delimiters (not marked up with around)."""
import re, sys
from collections import Counter
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'latex2tm'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load

MATH = {'math', 'equation', 'equation*', 'align', 'align*', 'eqnarray', 'eqnarray*',
        'multline', 'multline*', 'gather', 'gather*'}
TEXT = {'text', 'label', 'eqref', 'reference', 'cite', 'hlink', 'image', 'script-output',
        'math-up', 'op', 'tuple', 'associate', 'cwith', 'twith', 'with-attrs'}
TOK = re.compile(r'<[^<>]*>|.', re.S)
DELIMS = {'(', ')', '[', ']', '{', '}', '<{>', '<}>', '|', '<|>', '<||>', '<langle>', '<rangle>',
          '<lfloor>', '<rfloor>', '<lceil>', '<rceil>', '<lvert>', '<rvert>', '<lVert>', '<rVert>'}

def tostr(x):
    if isinstance(x, str):
        return x
    return '<' + x[0] + ('|' + '|'.join(tostr(c) for c in x[1:]) if len(x) > 1 else '') + '>'

found = []
cnt = Counter()

def rec(x, math, path):
    if isinstance(x, str):
        if math:
            toks = [t for t in TOK.findall(x) if t in DELIMS]
            if toks:
                cnt.update(toks)
                found.append((path, x))
        return
    lab = x[0]
    if lab in ('with',):
        # with|mode|math / text
        args = x[1:-1]
        m = math
        for k, v in zip(args[::2], args[1::2]):
            if k == 'mode' and isinstance(v, str):
                m = v == 'math'
        rec(x[-1], m, path)
        return
    if lab in TEXT:
        return
    if lab in ('around', 'around*'):
        cnt['AROUND ' + tostr(x[1]) + tostr(x[3])] += 1
        rec(x[2], True, path + [x])
        return
    m = math or lab in MATH
    for c in x[1:]:
        rec(c, m, path + [x] if lab == 'concat' else path)

if __name__ == '__main__':
    t = load(sys.argv[1])
    rec(t, False, [])
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1]):
        print(v, k)
    if len(sys.argv) > 2:
        for path, s in found:
            ctx = tostr(path[-1]) if path else s
            print('---', repr(s), '\n   ', ctx[:400])
