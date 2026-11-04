"""Wrap bare matched delimiters in math into around/around*; report the rest.

usage: fixaround.py in.scm out.scm
"""
import re, sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'latex2tm'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump
from scan import MATH, TEXT, TOK, tostr

OPEN = {'(', '[', '<langle>', '<lfloor>', '<lceil>'}
CLOSE = {')', ']', '<rangle>', '<rfloor>', '<rceil>'}
TOGGLE = {'<||>'}
LARGE = {'frac', 'big', 'sqrt', 'around*', 'tabular', 'matrix', 'choose'}
SKIP = TEXT | {'mid', 'left', 'right', 'big', 'wide', 'wide*', 'math-up', 'math-bf'}

log = []

def has_large(items):
    def rec(x):
        if isinstance(x, str):
            return False
        if x[0] in LARGE:
            return True
        return any(rec(c) for c in x[1:])
    return any(rec(x) for x in items)

def merge(items):
    out = []
    for x in items:
        if isinstance(x, str) and out and isinstance(out[-1], str):
            out[-1] = out[-1] + x
        elif x != '':
            out.append(x)
    return out

def mk_body(items):
    items = merge(items)
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    return ['concat'] + items

def fix_seq(children, where):
    """children: list of concat children (str or node). Returns new list."""
    items = []
    for c in children:
        if isinstance(c, str):
            items.extend(TOK.findall(c))
        else:
            items.append(c)
    changed = True
    while changed:
        changed = False
        stack = []
        for i, x in enumerate(items):
            if not isinstance(x, str):
                continue
            if x in OPEN or (x in TOGGLE and not (stack and items[stack[-1]] == x)):
                stack.append(i)
            elif x in CLOSE or x in TOGGLE:
                if not stack:
                    continue
                j = stack.pop()
                o = items[j]
                if (o in TOGGLE) != (x in TOGGLE):
                    stack.append(j)
                    continue
                if o == '<langle>' and x != '<rangle>' or x == '<rangle>' and o != '<langle>':
                    stack.append(j)
                    continue
                body = items[j+1:i]
                tag = 'around*' if has_large(body) else 'around'
                node = [tag, o, mk_body(body), x]
                log.append('  ' + tostr(node))
                items[j:i+1] = [node]
                changed = True
                break
    left = [x for x in items if isinstance(x, str) and (x in OPEN or x in CLOSE or x in TOGGLE)]
    if left:
        log.append('UNMATCHED %s in %s: %s' % (left, where, tostr(['concat'] + merge(items))[:300]))
    return merge(items)

def rec(x, math, where):
    if isinstance(x, str):
        return x
    lab = x[0]
    if lab == 'with':
        m = math
        for k, v in zip(x[1:-1:2], x[2:-1:2]):
            if k == 'mode':
                m = v == 'math'
        x[-1] = rec(x[-1], m, where)
        return x
    if lab in SKIP:
        if lab in ('big', 'wide', 'wide*', 'math-up', 'math-bf'):
            x[1] = rec(x[1], math, where)
        return x
    if lab == 'label':
        return x
    if lab in ('around', 'around*', 'big-around'):
        if isinstance(x[2], str):
            x[2] = mk_body(fix_seq([x[2]], lab))
        else:
            x[2] = rec(x[2], True, where)
        return x
    m = math or lab in MATH
    for i in range(1, len(x)):
        c = x[i]
        if isinstance(c, str) and m and lab != 'concat':
            if any(t in OPEN or t in CLOSE or t in TOGGLE for t in TOK.findall(c)):
                new = fix_seq([c], lab)
                x[i] = mk_body(new)
        else:
            x[i] = rec(c, m, where)
    if lab == 'concat' and m:
        new = fix_seq(x[1:], where)
        return mk_body(new) if len(new) != 1 else new[0]
    return x

def check_arounds(x, path=''):
    """heuristics for around nodes that enclose the wrong extent"""
    if isinstance(x, str):
        return
    if x[0] in ('around', 'around*'):
        b = x[2]
        bad = False
        if isinstance(b, list) and b[0] == 'concat':
            if isinstance(b[1], list) and b[1][0] in ('rsup', 'rsub'):
                bad = True
            if isinstance(b[-1], str) and re.search(r'[-+=*,]$', b[-1]):
                bad = True
        elif isinstance(b, list) and b[0] in ('rsup', 'rsub'):
            bad = True
        elif isinstance(b, str) and re.search(r'^[+=*,]|[-+=*,]$', b):
            bad = True
        if bad:
            log.append('SUSPICIOUS ' + tostr(x)[:300])
    for c in x[1:]:
        check_arounds(c)

if __name__ == '__main__':
    t = load(sys.argv[1])
    t = rec(t, False, '')
    check_arounds(t)
    print('\n'.join(log))
    dump(t, sys.argv[2])
