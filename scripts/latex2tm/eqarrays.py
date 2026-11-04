"""Native TeXmacs layouts for amsmath blocks inside an equation, as left by
the LaTeX import.

- `gathered` has no TeXmacs counterpart (the import keeps it as an undefined
  macro): the equation becomes an eqnarray* with the lines in the centred
  middle column.
- `aligned` is a TeXmacs macro, but inside an equation the number is set on
  a line of its own below the block: the equation becomes an align.

In both cases the equation number and the labels go at the end of the last
row, like in a hand-made TeXmacs document."""
from stree import is_node


def split_lines(body):
    items = body[1:] if is_node(body, 'concat') else [body]
    lines, cur = [], []
    for c in items:
        if is_node(c, 'next-line'):
            lines.append(cur); cur = []
        else:
            cur.append(c)
    lines.append(cur)
    return [l[0] if len(l) == 1 else ['concat'] + l for l in lines if l]


def gathered_equation(x):
    """eqnarray* for an equation/equation* whose body is a gathered block, else None"""
    if not (is_node(x, 'equation') or is_node(x, 'equation*')) or len(x) != 2:
        return None
    body = x[1]
    if is_node(body, 'document') and len(body) == 2:
        body = body[1]
    items = body[1:] if is_node(body, 'concat') else [body]
    labels = [c for c in items if is_node(c, 'label')]
    gath = [c for c in items if is_node(c, 'gathered')]
    rest = [c for c in items if not (is_node(c, 'label') or is_node(c, 'gathered'))
            and not (isinstance(c, str) and not c.strip())]
    if len(gath) != 1 or rest:
        return None
    lines = split_lines(gath[0][1])
    rows = [['row', ['cell', ''], ['cell', l], ['cell', '']] for l in lines]
    if x[0] == 'equation':
        rows[-1][3] = ['concat', ['eq-number']] + labels
    elif labels:
        rows[-1][3] = ['concat'] + labels
    return ['eqnarray*', ['tformat', ['table'] + rows]]


def unwrap(c):
    return c[1] if is_node(c, 'document') and len(c) == 2 else c


def aligned_equation(x):
    """align for an equation/equation* whose body is an aligned block, else None"""
    if not (is_node(x, 'equation') or is_node(x, 'equation*')) or len(x) != 2:
        return None
    body = x[1]
    items = []
    for p in (body[1:] if is_node(body, 'document') else [body]):
        items += p[1:] if is_node(p, 'concat') else [p]
    labels = [c for c in items if is_node(c, 'label')]
    al = [c for c in items if is_node(c, 'aligned')]
    if len(al) != 1:
        return None
    k = items.index(al[0])
    if any(not is_node(c, 'label') and not (isinstance(c, str) and not c.strip())
           for c in items[:k]):
        return None
    rest = [c for c in items[k+1:] if not is_node(c, 'label')]
    tf = unwrap(al[0][1])
    if not (is_node(tf, 'tformat') and is_node(tf[-1], 'table')):
        return None
    rows = tf[-1][1:]
    last = rows[-1][-1]
    tail = rest + ([['eq-number']] if x[0] == 'equation' else []) + labels
    if tail:
        c = unwrap(last[1])
        last[1] = ['concat'] + (c[1:] if is_node(c, 'concat') else [c]) + tail
    return ['align', ['tformat'] + tf[1:-1] + [['table'] + rows]]


def native_equation(x):
    g = gathered_equation(x)
    return g if g is not None else aligned_equation(x)
