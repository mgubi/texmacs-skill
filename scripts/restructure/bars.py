"""Pair bare | bars in maths into <around|\\||...|\\|> (absolute values).

At each level (a math concat, or an around body), the bare bars are paired
in order when there is an even number of them; a single bar inside a
bracket is a conditioning/middle bar and is kept.  Everything else, and any
pair whose body is empty or starts/ends with a relation or operator, is
reported for manual review (and left unchanged).
usage: bars.py in.scm out.scm
"""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'latex2tm'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump
from scan import TOK, tostr, MATH
from fixaround import has_large, merge, mk_body, SKIP

REL = re.compile(r'^(=|<leqslant>|<geqslant>|<less>|<gtr>|<lesssim>|<gtrsim>|<ll>|<gg>|<approx>|<sim>|<to>|<in>|\+|-|,|;|:|<assign>)$')
log = []

def bad_edge(tok):
    return isinstance(tok, str) and (REL.match(tok) or tok in ('*', ' '))

def pair_level(children, inside_bracket):
    items = []
    for c in children:
        items.extend(TOK.findall(c) if isinstance(c, str) else [c])
    idx = [i for i, t in enumerate(items) if t == '|']
    if not idx:
        return None
    ctx = tostr(['concat'] + merge(items))[:300]
    if len(idx) % 2:
        if len(idx) == 1 and inside_bracket:
            return None
        k = idx[-1]
        if len(idx) == 1 and k + 1 < len(items) and isinstance(items[k+1], list) and items[k+1][0] == 'rsub':
            # evaluation / restriction bar: from the last relation before it
            a = 0
            for i in range(k - 1, -1, -1):
                if isinstance(items[i], str) and items[i] in ('=', '<assign>'):
                    a = i + 1; break
            body = items[a:k]
            while body and body[0] == ' ':
                body = body[1:]; a += 1
            items[a:k+1] = [['around*', '.', mk_body(body), '|']]
            log.append('EVAL    ' + tostr(items[a])[:300])
            return merge(items)
        log.append('ODD     ' + ctx)
        return None
    pairs = list(zip(idx[::2], idx[1::2]))
    for a, b in pairs:
        body = [t for t in items[a+1:b] if t != ' ']
        if not body or bad_edge(body[0]) and body[0] not in ('-',) or bad_edge(body[-1]):
            log.append('REVIEW  ' + ctx)
            return None
    for a, b in reversed(pairs):
        body = items[a+1:b]
        node = ['around*' if has_large(body) else 'around', '|', mk_body(body), '|']
        items[a:b+1] = [node]
    log.append('PAIRED%d ' % len(idx) + ctx + '\n   -> ' + tostr(['concat'] + merge(items))[:400])
    return merge(items)

def rec(x, math, bracket=False):
    if isinstance(x, str):
        return x
    lab = x[0]
    if lab in SKIP or lab == 'label':
        if lab in ('big', 'wide', 'wide*', 'math-up', 'math-bf'):
            x[1] = rec(x[1], math)
        return x
    if lab == 'with':
        m = math
        for k, v in zip(x[1:-1:2], x[2:-1:2]):
            if k == 'mode':
                m = v == 'math'
        x[-1] = rec(x[-1], m)
        return x
    if lab in ('around', 'around*'):
        b = x[2]
        kids = b[1:] if isinstance(b, list) and b[0] == 'concat' else [b]
        kids = [rec(k, True) for k in kids]
        new = pair_level(kids, x[1] in ('(', '[', '{', '<langle>'))
        x[2] = mk_body(new if new is not None else kids)
        return x
    m = math or lab in MATH
    for i in range(1, len(x)):
        x[i] = rec(x[i], m)
    if m and lab == 'concat':
        new = pair_level(x[1:], False)
        if new is not None:
            return mk_body(new) if len(new) != 1 else new[0]
    elif m and lab not in ('concat',):
        for i in range(1, len(x)):
            if isinstance(x[i], str) and '|' in x[i]:
                new = pair_level([x[i]], False)
                if new is not None:
                    x[i] = mk_body(new)
    return x

if __name__ == '__main__':
    t = load(sys.argv[1])
    t = rec(t, False)
    print('\n'.join(log))
    dump(t, sys.argv[2])
