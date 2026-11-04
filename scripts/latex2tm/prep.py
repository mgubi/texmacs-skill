"""LaTeX preprocessing before the TeXmacs import.

- expands the user macros of the preamble (so that the import produces
  native TeXmacs markup instead of user macros);
- resolves \\cref / \\Cref / \\eqref with the cleveref data of the .aux files:
  internal labels become "Lemma~\\ref{x}", external ones (xr prefixes) become
  hyperlinks to the label in the other .tm file;
- compiles every tikzpicture to a standalone PDF and replaces it by an image.

usage: prep.py src_dir name.tex out_dir   (aux files are read from src_dir)
"""
import os, re, sys, subprocess

src, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
text = open(os.path.join(src, name), encoding='utf-8').read()
base = name[:-4]

# ------------------------------------------------------------------ utils
def read_group(s, i):
    """s[i]=='{' -> (content, index after closing brace)"""
    assert s[i] == '{', s[i:i+40]
    depth = 0
    j = i
    while True:
        c = s[j]
        if c == '\\':
            j += 2; continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return s[i+1:j], j+1
        j += 1

def skip_ws(s, i):
    while i < len(s) and s[i] in ' \t\n': i += 1
    return i

def read_arg(s, i):
    i = skip_ws(s, i)
    if s[i] == '{':
        return read_group(s, i)
    if s[i] == '\\':
        m = re.match(r'\\([a-zA-Z]+|.)', s[i:])
        return m.group(0), i + m.end()
    return s[i], i+1

# ------------------------------------------------------------------ macros
pre, body = text.split('\\begin{document}', 1)
macros = {}      # name -> (nargs, body)
paired = {}      # name -> (left, right, nargs, body)
defs_spans = []

for m in re.finditer(r'\\(?:newcommand|renewcommand|providecommand)\*?\s*\{?\\([a-zA-Z]+)\}?(\[(\d)\])?', pre):
    nargs = int(m.group(3) or 0)
    j = skip_ws(pre, m.end())
    b, e = read_group(pre, j)
    if m.group(1) not in macros:
        macros[m.group(1)] = (nargs, b)
    defs_spans.append((m.start(), e))
for m in re.finditer(r'\\DeclareMathOperator\*?\{\\([a-zA-Z]+)\}', pre):
    b, e = read_group(pre, m.end())
    macros[m.group(1)] = (0, '\\operatorname{%s}' % b)
    defs_spans.append((m.start(), e))
for m in re.finditer(r'\\DeclarePairedDelimiter(X?)\{\\([a-zA-Z]+)\}', pre):
    j = m.end(); nargs = 1; pb = '#1'
    if m.group(1):
        mm = re.match(r'\[(\d)\]', pre[j:]); nargs = int(mm.group(1)); j += mm.end()
    l, j = read_group(pre, j)
    r, j = read_group(pre, j)
    if m.group(1):
        pb, j = read_group(pre, j)
    paired[m.group(2)] = (l, r, nargs, pb)
    defs_spans.append((m.start(), j))

# TeXmacs-friendly overrides
over = {
    'dd': (0, '\\mathrm{d}'), 'ee': (0, '\\mathrm{e}'), 'ii': (0, '\\mathrm{i}'),
    'wick': (1, '{:}#1{:}'),
    'formal': (0, '\\textup{(formal)}'), 'sketch': (0, '\\textup{(sketch)}'),
    'one': (0, '\\mathbb{1}'),
}
for k, v in over.items():
    if k in macros: macros[k] = v

def subst(b, args):
    for n, a in enumerate(args, 1):
        b = b.replace('#%d' % n, a)
    return b

def expand(s):
    out = []; i = 0
    while i < len(s):
        m = re.compile(r'\\([a-zA-Z]+)').search(s, i)
        if not m:
            out.append(s[i:]); break
        out.append(s[i:m.start()])
        nm = m.group(1); j = m.end()
        if nm in macros:
            n, b = macros[nm]
            args = []
            for _ in range(n):
                a, j = read_arg(s, j); args.append(a)
            rep = subst(b, args)
            # protect against gluing a control word to a following letter
            if n == 0 and j < len(s) and s[j].isalpha() and re.search(r'\\[a-zA-Z]+$', rep):
                rep += ' '
            if n == 0 and j < len(s) and s[j] == '*':
                rep = '{' + rep + '}'
            out.append('{' + rep + '}' if n == 0 and '^' not in rep and '_' not in rep and False else rep)
            i = j
        elif nm in paired:
            l, r, n, b = paired[nm]
            size = None
            if s.startswith('*', j):
                size = 'auto'; j += 1
            elif s.startswith('[', j):
                k = s.index(']', j); size = s[j+1:k]; j = k+1
            args = []
            for _ in range(n):
                a, j = read_arg(s, j); args.append(a)
            inner = subst(b, args)
            dl = {'\\lvert': '|', '\\rvert': '|', '\\lVert': '\\|', '\\rVert': '\\|'}
            l, r = dl.get(l, l), dl.get(r, r)
            if size == 'auto':
                out.append('\\left%s %s\\right%s ' % (l, inner, r))
            elif size:
                out.append('%sl%s %s%sr%s ' % (size, l, inner, size, r))
            else:
                out.append('%s %s%s ' % (l, inner, r))
            i = j
        else:
            out.append(m.group(0)); i = j
    return ''.join(out)

for _ in range(6):
    nb = expand(body)
    if nb == body: break
    body = nb
pre_clean = pre
for a, b in sorted(defs_spans, reverse=True):
    pre_clean = pre_clean[:a] + pre_clean[b:]
# title/author/date may use macros
pre_clean = expand(expand(pre_clean))

# ------------------------------------------------------------------ labels
TYPE = {
    'section': ('Section', 'Sections'), 'subsection': ('Section', 'Sections'),
    'subsubsection': ('Section', 'Sections'),
    'equation': ('Eq.', 'Eqs.'), 'figure': ('Figure', 'Figures'),
    'table': ('Table', 'Tables'), 'theorem': ('Theorem', 'Theorems'),
    'proposition': ('Proposition', 'Propositions'), 'lemma': ('Lemma', 'Lemmas'),
    'corollary': ('Corollary', 'Corollaries'), 'definition': ('Definition', 'Definitions'),
    'remark': ('Remark', 'Remarks'), 'exercise': ('Exercise', 'Exercises'),
    'enumi': ('Item', 'Items'),
}
def load_aux(path):
    d = {}
    if not os.path.exists(path): return d
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'\\newlabel\{(.*)@cref\}\{\{\[([a-z]+)\]\[[^\]]*\]\[[^\]]*\]([^}]*)\}', line)
        if m:
            d[m.group(1)] = (m.group(2), m.group(3))
    return d

labels = load_aux(os.path.join(src, base + '.aux'))
externals = {}
for m in re.finditer(r'\\externaldocument\[([^\]]+)\]\{([^}]+)\}', pre):
    externals[m.group(1)] = (m.group(2), load_aux(os.path.join(src, m.group(2) + '.aux')))

def resolve(lab):
    """-> (type, number, latex for the reference)"""
    for pfx, (doc, aux) in externals.items():
        if lab.startswith(pfx):
            l = lab[len(pfx):]
            if l in aux:
                t, num = aux[l]
                return t, num, ('ext', doc, l, num)
            print('UNRESOLVED external', lab, file=sys.stderr)
            return 'section', '??', ('txt', '??')
    if lab in labels:
        t, num = labels[lab]
        return t, num, ('int', lab)
    print('UNRESOLVED', lab, file=sys.stderr)
    return 'section', '??', ('txt', '??')

def ref_tex(r, eq):
    if r[0] == 'int':
        return '\\eqref{%s}' % r[1] if eq else '\\ref{%s}' % r[1]
    if r[0] == 'ext':
        return '\\href{XREFURL}{XREF@%s@%s@%s}' % ('eq' if eq else 'nr', r[1].replace('_', '-'), r[2])
    return r[1]

def join(items):
    if len(items) == 1: return items[0]
    return ', '.join(items[:-1]) + ' and ' + items[-1]

def cref(labs, cap):
    groups = []
    for lab in [x.strip() for x in labs.split(',') if x.strip()]:
        t, num, r = resolve(lab)
        if groups and groups[-1][0] == t:
            groups[-1][1].append(r)
        else:
            groups.append((t, [r]))
    parts = []
    for t, rs in groups:
        sing, plur = TYPE.get(t, (t.capitalize(), t.capitalize() + 's'))
        nm = sing if len(rs) == 1 else plur
        parts.append(nm + '~' + join([ref_tex(r, t == 'equation') for r in rs]))
    return join(parts)

body = re.sub(r'\\([cC])ref\{([^}]*)\}', lambda m: cref(m.group(2), m.group(1) == 'C'), body)
body = re.sub(r'\\eqref\{([^}]*)\}', lambda m: ref_tex(resolve(m.group(1))[2], True), body)
body = re.sub(r'\\ref\{([^}]*)\}', lambda m: ref_tex(resolve(m.group(1))[2], False), body)

# ------------------------------------------------------------------ tikz
figdir = os.path.join(out, 'figures')
os.makedirs(figdir, exist_ok=True)
tikz_pre = r"""\documentclass[tikz]{standalone}
\usepackage[T1]{fontenc}
\usepackage[sc]{mathpazo}
\usepackage{amsmath,amssymb,mathtools,bm}
\usepackage[mathscr]{eucal}
\usetikzlibrary{decorations.pathreplacing,arrows.meta,positioning}
\usepackage[dvipsnames]{xcolor}
\begin{document}
"""
tikz_pre = tikz_pre.replace('\\begin{document}', '\n'.join(re.findall(r'\\definecolor\{[^}]*\}\{[^}]*\}\{[^}]*\}', pre)) + '\n\\begin{document}')
count = [0]
def tikz(m):
    count[0] += 1
    fn = '%s-tikz%d' % (base.replace('_', '-'), count[0])
    # pictures are compiled standalone: references must be numbers already
    pic = re.sub(r'\\eqref\{([^}]*)\}', lambda r: '(%s)' % resolve(r.group(1))[1], m.group(0))
    pic = re.sub(r'\\ref\{([^}]*)\}', lambda r: resolve(r.group(1))[1], pic)
    code = tikz_pre + pic.strip() + '\n\\end{document}\n'
    with open(os.path.join(figdir, fn + '.tex'), 'w', encoding='utf-8') as f:
        f.write(code)
    subprocess.run(['latex', '-interaction=nonstopmode', '-halt-on-error', fn + '.tex'],
                   cwd=figdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['dvips', '-q', fn + '.dvi', '-o', fn + '.eps'],
                   cwd=figdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(os.path.join(figdir, fn + '.eps')):
        print('TIKZ FAILED', fn, file=sys.stderr)
    return '\\tmtikz{%s}' % fn
body = re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', tikz, body, flags=re.S)

# figure paths
def img(m):
    opt, f = m.group(1) or '', m.group(2)
    if not f.startswith('figures/'):
        f = 'figures/' + f
    return '\\includegraphics%s{%s}' % (opt, f)
body = re.sub(r'\\includegraphics(\[[^\]]*\])?\{([^}]*)\}', img, body)

# ------------------------------------------------------------------ optional titles
def opt_title(m):
    env = m.group(1); i = m.end()
    depth = 0; j = i
    while True:
        c = body[j]
        if c == '{': depth += 1
        elif c == '}': depth -= 1
        elif c == ']' and depth == 0: break
        j += 1
    return env, body[i:j], j + 1
ENVS = 'theorem|proposition|lemma|corollary|definition|remark|exercise|proof'
while True:
    m = re.search(r'\\begin\{(%s)\}\s*\[' % ENVS, body)
    if not m: break
    env, title, j = opt_title(m)
    mark = 'tmproofof' if env == 'proof' else 'tmdueto'
    body = body[:m.start()] + '\\begin{%s}\\%s{%s}' % (env, mark, title) + body[j:]

# ------------------------------------------------------------------ list styles
for opt, mark in [(r'\begin{enumerate}[label=(\alph*)]', 'alpha'),
                  (r'\begin{enumerate}[label=(\Alph*)]', 'Alpha'),
                  (r'\begin{enumerate}[label=(\roman*)]', 'roman'),
                  (r'\begin{enumerate}[(a)]', 'alpha'), (r'\begin{enumerate}[(i)]', 'roman'),
                  (r'\begin{enumerate}[(A)]', 'Alpha')]:
    body = body.replace(opt, r'\begin{enumerate}\tmlist{%s}' % mark)
body = re.sub(r'\\begin\{description\}\[[^\]]*nextline[^\]]*\]', r'\\begin{description}\\tmlist{long}', body)
body = re.sub(r'\\begin\{(description|enumerate|itemize)\}\[[^\]]*\]', r'\\begin{\1}', body)

# ------------------------------------------------------------------ symbols TeXmacs lacks
body = re.sub(r'\\fint_\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', lambda m: '\\frac{1}{|%s|}\\int_{%s}' % (m.group(1), m.group(1)), body)
body = body.replace('\\lVert', '\\|').replace('\\rVert', '\\|').replace('\\lvert', '|').replace('\\rvert', '|')
GREEK = 'alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho varrho sigma tau phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Phi Psi Omega'.split()
body = re.sub(r'\\(%s)\*' % '|'.join(GREEK), r'{\\\1}*', body)
body = body.replace('\\eqqcolon', '=:').replace('\\coloneqq', ':=')

# ------------------------------------------------------------------ minipages in figures
def minip(m):
    w, inner = m.group(1), m.group(2)
    inner = inner.replace('\\centering', '')
    inner = re.sub(r'width=\\textwidth', 'width=%s\\\\textwidth' % w, inner)
    return inner.strip() + ' '
body = re.sub(r'\\begin\{minipage\}(?:\[[^\]]*\])?\{([\d.]+)\\textwidth\}(.*?)\\end\{minipage\}(?:\\hfill)?', minip, body, flags=re.S)

# ------------------------------------------------------------------ tabularx
def tabx(m):
    spec = m.group(1).replace('X', 'p{8cm}')
    return '\\begin{tabular}{%s}' % spec
body = re.sub(r'\\begin\{tabularx\}\{\\textwidth\}\{((?:[^{}]|\{[^{}]*\})*)\}', tabx, body)
body = body.replace('\\end{tabularx}', '\\end{tabular}')

# ------------------------------------------------------------------ cleanups
body = re.sub(r'\\addcontentsline\{[^}]*\}\{[^}]*\}\{[^}]*\}', '', body)
body = body.replace('\\setlength{\\itemsep}{1pt}', '')
pre_clean = re.sub(r'\\externaldocument\[[^\]]*\]\{[^}]*\}', '', pre_clean)

with open(os.path.join(out, name), 'w', encoding='utf-8') as f:
    f.write(pre_clean + '\\begin{document}' + body)
print('prepared', name, 'tikz:', count[0], 'labels:', len(labels))
