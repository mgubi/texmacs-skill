"""Helpers for restructuring a series of documents through their strees."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'latex2tm'))
from stree import load, dump, walk, is_node

LECT = re.compile(r'(Lectures?)( |\xa0)([1-9](?:\x15[1-9])?)')
TAIL = re.compile(r'(Lectures?)$')
HEAD = re.compile(r'^([1-9](?:\x15[1-9])?)')


def body(doc):
    return [c for c in doc[1:] if is_node(c, 'body')][0][1]


def lecture_slots(x):
    """list of (setter, number) for every 'Lecture N' mention in x, in order"""
    out = []
    def rec(node):
        if not isinstance(node, list):
            return
        kids = node
        for i in range(1, len(kids)):
            c = kids[i]
            if isinstance(c, str):
                for m in LECT.finditer(c):
                    def setter(new, i=i, m=m, node=node):
                        s = node[i]
                        node[i] = type(s)(s[:m.start(3)] + new + s[m.end(3):])
                    out.append((setter, m.group(3), (node, i, m.start(3))))
                if TAIL.search(c) and i + 2 < len(kids) and is_node(kids[i+1], 'nbsp') \
                        and isinstance(kids[i+2], str) and HEAD.match(kids[i+2]):
                    m = HEAD.match(kids[i+2])
                    def setter(new, j=i+2, m=m, node=node):
                        s = node[j]
                        node[j] = type(s)(new + s[m.end(1):])
                    out.append((setter, m.group(1), (node, i + 2, 0)))
            else:
                rec(c)
    rec(['root', x])
    # apply right-to-left within one string stays valid because we recompute per call
    return out


def relecture(x, news, where=''):
    """replace the numbers of the 'Lecture N' mentions of x, in order"""
    slots = lecture_slots(x)
    if len(slots) != len(news):
        raise SystemExit('%s: %d mentions %s, %d replacements given'
                         % (where, len(slots), [s[1] for s in slots], len(news)))
    # replace from the last to the first, so offsets inside one string stay valid
    for (setter, old, _), new in reversed(list(zip(slots, news))):
        if new is not None:
            setter(new.replace('-', '\x15'))


def flat(x):
    if isinstance(x, str): return x.replace('\x15', '-')
    if is_node(x, 'math'): return '$..$'
    if is_node(x, 'hlink'): return '[' + flat(x[1]) + '->' + flat(x[2]) + ']'
    if x[0] in ('image', 'raw-data', 'script-output'): return '<fig>'
    return ' '.join(flat(c) for c in x[1:])


def leaf_paragraphs(x, path=()):
    if is_node(x, 'document'):
        for i, c in enumerate(x[1:]):
            yield from leaf_paragraphs(c, path + (i,))
    elif is_node(x) and x[0] != 'table-of-contents' and any(is_node(c, 'document') for c in x[1:]):
        for c in x[1:]:
            if is_node(c, 'document'):
                yield from leaf_paragraphs(c, path)
    else:
        yield path, x


def visit(x, f):
    """in-place traversal: f(node) is called on every list node, top-down"""
    if isinstance(x, list):
        f(x)
        for c in x[1:]:
            visit(c, f)
