"""Read/write TeXmacs strees as dumped by Guile `write` (see dump.scm).

A node is either a Python str (TeXmacs string, Cork encoded, kept as latin-1
code points so that bytes round-trip) or a list [label, child, ...] with
label a str.  Files are read and written as latin-1.
"""

def parse(s):
    i, n = 0, len(s)
    stack = [[]]
    while i < n:
        c = s[i]
        if c == '(':
            stack.append([]); i += 1
        elif c == ')':
            node = stack.pop(); stack[-1].append(node); i += 1
        elif c == '"':
            j = i + 1; buf = []
            while True:
                d = s[j]
                if d == '\\':
                    e = s[j+1]
                    if e == 'x':
                        buf.append(chr(int(s[j+2:j+4], 16))); j += 4
                    else:
                        buf.append({'n': '\n', 't': '\t', '"': '"', '\\': '\\', '0': '\0'}.get(e, e)); j += 2
                elif d == '"':
                    break
                else:
                    buf.append(d); j += 1
            stack[-1].append(Str(''.join(buf))); i = j + 1
        elif c in ' \t\n\r':
            i += 1
        else:
            j = i
            while j < n and s[j] not in ' \t\n\r()"':
                j += 1
            stack[-1].append(Sym(s[i:j])); i = j
    return stack[0][0]

class Str(str): pass
class Sym(str): pass

def to_tree(x):
    """convert parsed s-expression: lists with a leading Sym -> [label,...]"""
    if isinstance(x, list):
        return [str(x[0])] + [to_tree(y) for y in x[1:]]
    return str(x)

def load(path):
    return to_tree(parse(open(path, encoding='latin-1', newline='').read()))

def _w(x, out):
    if isinstance(x, list):
        out.append('(' + x[0])
        for y in x[1:]:
            out.append(' '); _w(y, out)
        out.append(')')
    else:
        out.append('"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"')

def dump(x, path):
    out = []; _w(x, out)
    open(path, 'w', encoding='latin-1', newline='').write(''.join(out))

def is_node(x, label=None):
    return isinstance(x, list) and (label is None or x[0] == label)

def walk(x, f):
    """bottom-up rewrite; f(node) returns a node, or a list of nodes
    wrapped as ('splice', [...]) to splice into the parent"""
    if not isinstance(x, list):
        return f(x)
    kids = []
    for y in x[1:]:
        r = walk(y, f)
        if isinstance(r, tuple) and r[0] == 'splice':
            kids.extend(r[1])
        elif r is not None:
            kids.append(r)
    return f([x[0]] + kids)

def text_of(x):
    if isinstance(x, list):
        return ''.join(text_of(y) for y in x[1:])
    return x
