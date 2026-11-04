"""Repair wrong `around` extents: in every math concat that contains an
around with an impossible delimiter pair, or a suspicious body (starting
with a script or ending with an operator), flatten all arounds of that
concat back into delimiter tokens and pair them again.

usage: rebracket.py in.scm out.scm
"""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'latex2tm'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump
from scan import TOK, tostr
from fixaround import has_large, merge, mk_body, MATH, SKIP

OPEN = {'(', '[', '<langle>', '{'}
CLOSE = {')', ']', '<rangle>', '}'}
GOOD = {('(', ')'), ('[', ']'), ('[', ')'), ('(', ']'), ('{', '}'), ('<langle>', '<rangle>'),
        ('|', '|'), ('<||>', '<||>'), ('.', '|'), ('{', '<nobracket>'), ('<nobracket>', '}'),
        ('|', '<rangle>'), ('<langle>', '|'),            # bra and ket
        ('<lfloor>', '<rfloor>'), ('<lceil>', '<rceil>'), ('.', '<nobracket>')}
log = []

def suspicious(x):
    b = x[2]
    if isinstance(b, list) and b[0] == 'concat':
        if isinstance(b[1], list) and b[1][0] in ('rsup', 'rsub'):
            return True
        if isinstance(b[-1], str) and re.search(r'[-+=*,]$', b[-1]):
            return True
    return isinstance(b, list) and b[0] in ('rsup', 'rsub')

def bad(x):
    """x is an around that is wrong, or contains (through bodies) one"""
    if not isinstance(x, list):
        return False
    if x[0] in ('around', 'around*'):
        return (x[1], x[3]) not in GOOD or suspicious(x) or bad(x[2])
    if x[0] == 'concat':
        return any(bad(c) for c in x[1:])
    return False

def flatten(items, out):
    for x in items:
        if isinstance(x, str):
            out.extend(TOK.findall(x))
        elif x[0] in ('around', 'around*'):
            for d, body in ((x[1], None), (None, x[2]), (x[3], None)):
                if d is not None:
                    if d not in ('<nobracket>', '.'):
                        out.append(('D', d, x[0] == 'around*'))
                else:
                    flatten(body[1:] if isinstance(body, list) and body[0] == 'concat' else [body], out)
        elif x[0] == 'concat':
            flatten(x[1:], out)
        else:
            out.append(x)

def strip_stars(body):
    while body and body[0] == '*':
        body = body[1:]
    while body and body[-1] == '*':
        body = body[:-1]
    return body

def rematch(items):
    # delimiter tokens are tuples ('D', d); bare delimiters in strings also count
    items = [('D', x, False) if isinstance(x, str) and x in OPEN | CLOSE | {'|', '<||>'} else x for x in items]
    stack = []
    i = 0
    while i < len(items):
        x = items[i]
        if not isinstance(x, tuple):
            i += 1; continue
        d = x[1]
        if d in OPEN:
            stack.append(i); i += 1; continue
        if d in ('|', '<||>'):
            if stack and items[stack[-1]][1] == d:
                j = stack.pop()
            else:
                stack.append(i); i += 1; continue
        else:  # closer
            while stack and items[stack[-1]][1] in ('|',) :
                k = stack.pop()
                items[k] = '|'          # a middle bar (conditioning)
            if not stack or items[stack[-1]][1] == '<||>':
                i += 1; continue
            j = stack.pop()
        o = items[j][1]
        body = strip_stars(items[j+1:i])
        star = has_large(body) or items[j][2] or x[2]
        node = ['around*' if star else 'around', o, mk_body(body), d]
        items[j:i+1] = [node]
        i = j + 1
    left = [x[1] for x in items if isinstance(x, tuple)]
    items = [x[1] if isinstance(x, tuple) else x for x in items]
    return merge(items), left

def rec(x, math):
    if isinstance(x, str):
        return x
    lab = x[0]
    if lab in SKIP or lab == 'label':
        return x
    m = math or lab in MATH
    if lab == 'with':
        for k, v in zip(x[1:-1:2], x[2:-1:2]):
            if k == 'mode':
                m = v == 'math'
        x[-1] = rec(x[-1], m)
        return x
    if m and lab in ('concat', 'around', 'around*') and bad(x):
        before = tostr(x)
        flat = []
        flatten([x], flat)
        new, left = rematch(flat)
        res = mk_body(new)
        log.append('FIX  ' + before[:500] + '\n ->  ' + tostr(res)[:500] +
                   ('\n     UNMATCHED %s' % left if left else ''))
        return res
    for i in range(1, len(x)):
        x[i] = rec(x[i], m)
    return x

if __name__ == '__main__':
    t = load(sys.argv[1])
    t = rec(t, False)
    print('\n'.join(log))
    dump(t, sys.argv[2])
