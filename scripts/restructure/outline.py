import sys; sys.path.insert(0, '.')
from stree import load, is_node, text_of
SEC = {'section','section*','subsection','subsection*','subsubsection','paragraph','appendix'}
def flat(x):
    if isinstance(x, str): return x
    if is_node(x, 'math'): return '$' + flat(x[1]) + '$'
    return ''.join(flat(c) for c in x[1:])
def body_of(d):
    return [c for c in d[1:] if is_node(c, 'body')][0][1]
doc = load(sys.argv[1]); b = body_of(doc)
for i, p in enumerate(b[1:]):
    items = p[1:] if is_node(p, 'concat') else [p]
    for c in items:
        if is_node(c) and c[0] in SEC:
            lab = [x[1] for x in items if is_node(x, 'label')]
            print('%4d %-12s %s %s' % (i, c[0], flat(c[1])[:70], lab[:1]))
        if is_node(c, 'assign') and c[1] == 'section-nr': print('%4d   section-nr %s' % (i, c[2]))
