import sys; sys.path.insert(0, '.')
from stree import load, is_node, walk
def flat(x):
    if isinstance(x, str): return x
    if is_node(x, 'math'): return '$' + flat(x[1]) + '$'
    return ''.join(flat(c) for c in x[1:])
doc = load(sys.argv[1])
scr = []
def f(x):
    if is_node(x, 'screens'): scr.append(x)
    return x
walk(doc, f)
for k, s in enumerate(scr[0][1:]):
    titles = []
    def g(x):
        if is_node(x, 'mytitle'): titles.append(flat(x[1]))
        return x
    walk(s, g)
    if titles: t = titles[0]
    else:
        t = '[' + flat(s)[:70].replace('\n', ' ') + ']'
    print('%3d %s' % (k + 1, t[:90]))
