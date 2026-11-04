"""Turn the LaTeX-imported stree of a document into a native TeXmacs document.

usage: post_notes.py in.scm out.scm figdir

Environment (optional):
  TM_DOC_TITLE        replace the imported title by this text; the imported
                      title's font-size part then becomes the subtitle
                      (for a series of notes sharing one title)
  TM_STYLE_PACKAGES   comma-separated style packages appended to
                      <tuple|article|number-long-article|british>
"""
import os, re, sys
DOC_TITLE = os.environ.get('TM_DOC_TITLE', '')
STYLE_PACKAGES = [p for p in os.environ.get('TM_STYLE_PACKAGES', '').split(',') if p]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, walk, is_node, text_of
from eqarrays import native_equation

inp, outp, figdir = sys.argv[1:4]
doc = load(inp)

FLAGS = {}
THM = {'theorem', 'proposition', 'lemma', 'corollary', 'definition', 'remark',
       'exercise', 'example', 'conjecture', 'notation'}

def raw(path):
    return open(path, 'rb').read().decode('latin-1')

def embed_image(path, w='', h=''):
    name = os.path.basename(path)
    return ['image', ['tuple', ['raw-data', raw(path)], name], w, h, '', '']

def first_concat(body):
    """the first paragraph (concat or string) of a (document ...) body"""
    if is_node(body, 'document') and len(body) > 1:
        return body, 1
    return None, None

def take_marker(env_body, marker):
    """remove (marker X) from the start of the first paragraph; return X"""
    if not is_node(env_body, 'document') or len(env_body) < 2:
        return None
    p = env_body[1]
    if is_node(p, marker):
        env_body[1] = ''
        return p[1]
    if is_node(p, 'concat'):
        for k, c in enumerate(p[1:], 1):
            if is_node(c, marker):
                del p[k]
                return c[1]
            if isinstance(c, str) and c.strip():
                break
    return None

def pop_marker(t, marker):
    """remove the first (marker X) found in t outside nested lists; return X"""
    if not isinstance(t, list):
        return None
    for k, c in enumerate(t[1:], 1):
        if is_node(c, marker):
            del t[k]
            return text_of(c[1])
        if isinstance(c, list) and not c[0].startswith(('enumerate', 'itemize', 'description')):
            r = pop_marker(c, marker)
            if r is not None:
                return r
    return None

def strip_lead_space(par):
    if is_node(par, 'concat') and len(par) > 1 and isinstance(par[1], str):
        par[1] = par[1].lstrip()
    elif isinstance(par, str):
        return par.lstrip()
    return par

def clean_title(t):
    """doc-title of the form  SC(A Constructive Introduction) next-line
    SC(to Quantum Field Theory) next-line vspace (with font-size .. SUBTITLE)"""
    sub = None
    def f(x):
        nonlocal sub
        if is_node(x, 'with') and x[1] == 'font-size':
            sub = x[-1]
            return ''
        return x
    walk(t, f)
    def nl(x):
        if is_node(x, 'next-line'):
            return ' '
        if is_node(x, 'vspace*'):
            return None
        return x
    if sub is not None:
        sub = walk(sub, nl)
        sub = ['concat', sub] if not is_node(sub, 'concat') else sub
        # drop leading/trailing whitespace pieces
    return sub

def f(x):
    if not isinstance(x, list):
        return x
    lab = x[0]
    # ------------------------------------------------ gathered, aligned
    g = native_equation(x)
    if g is not None:
        return g
    # ------------------------------------------------ symbols
    if lab == 'math-up' and len(x) == 2 and x[1] in ('d', 'e', 'i'):
        return '<math%s>' % x[1]
    # ------------------------------------------------ drop LaTeX-only markup
    if lab == 'assign' and x[1] in ('tocdepth-nr',):
        return None
    if lab == 'assign' and x[1] == 'refname':
        FLAGS['no-ref-heading'] = True
        return None
    if lab == 'no-indent':
        return None
    if lab in ('vspace', 'vspace*') and isinstance(x[1], str) and x[1].startswith('-'):
        return None   # LaTeX layout hacks (e.g. before an empty bibliography heading)
    if lab == 'hide-preamble':
        body = x[1]
        if all(isinstance(c, str) and not c.strip() for c in body[1:]):
            return None
    # ------------------------------------------------ links
    if lab == 'hlink':
        t = text_of(x[1])
        if t.startswith('XREF@'):
            _, kind, d, l = t.split('@', 3)
            x[1] = t
            x[2] = d.replace('-', '_') + '.tm#' + l
        elif isinstance(x[2], str):
            x[2] = x[2].replace('\\#', '#')
    if lab in ('iint', 'iiint', 'oint') and len(x) == 1:
        return ['big', lab]
    # ------------------------------------------------ theorem titles / proofs
    if lab in THM and len(x) == 2:
        t = take_marker(x[1], 'tmdueto')
        if t is not None:
            p = x[1][1]
            x[1][1] = strip_lead_space(p) if not isinstance(p, str) else p.lstrip()
            par = x[1][1]
            due = ['dueto', t]
            if is_node(par, 'concat'):
                x[1][1] = ['concat', due] + par[1:]
            else:
                x[1][1] = ['concat', due, par] if par else due
        return x
    if lab == 'proof' and len(x) == 2:
        t = take_marker(x[1], 'tmproofof')
        if t is not None:
            p = x[1][1]
            x[1][1] = strip_lead_space(p) if not isinstance(p, str) else p.lstrip()
            return ['render-proof', t, x[1]]
        return x
    # ------------------------------------------------ list styles
    if lab in ('enumerate', 'description', 'itemize') and len(x) == 2:
        style = pop_marker(x[1], 'tmlist')
        if style:
            return [lab + '-' + style, x[1]]
        return x
    # ------------------------------------------------ figures
    if lab == 'image' and isinstance(x[1], str):
        path = os.path.join(figdir, '..', x[1]) if not os.path.isabs(x[1]) else x[1]
        if not os.path.exists(path):
            path = os.path.join(figdir, os.path.basename(x[1]))
        w = x[2] if len(x) > 2 else ''
        h = x[3] if len(x) > 3 else ''
        if not w and not h:
            w = '0.8par'
        return embed_image(path, w, h)
    if lab == 'tmtikz':
        name = text_of(x[1]).replace("<minus>", "-")
        code = open(os.path.join(figdir, name + '.tex'), encoding='utf-8').read()
        lines = code.rstrip('\n').split('\n')
        eps = os.path.join(figdir, name + '.eps')
        out = ['image', ['tuple', ['raw-data', raw(eps)], 'ps'], '', '', '', '']
        # code is ASCII; Cork-safe
        return ['script-output', 'tikz', 'default', ['document'] + lines, out]
    # ------------------------------------------------ bibliography
    if lab == 'thebibliography':
        items = []
        for it in x[2][1:]:
            if is_node(it, 'concat') and is_node(it[1], 'bibitem-with-key'):
                key = it[1][2]
                rest = it[2:]
                if rest and isinstance(rest[0], str):
                    rest = [rest[0].lstrip()] + rest[1:]
                items.append(['concat', ['bibitem*', key], ['label', 'bib-' + key]] + rest)
            elif isinstance(it, str) and not it.strip():
                continue
            else:
                items.append(it)
        bl = ['bib-list', x[1], ['document'] + items]
        if FLAGS.get('no-ref-heading'):
            return bl
        return ('splice', [['section*', 'References'], bl])
    if lab == 'with' and len(x) == 4 and x[1] == 'font-size' and is_node(x[3], 'document') \
            and any(is_node(c, 'bib-list') for c in x[3][1:]):
        return ('splice', x[3][1:])
    # ------------------------------------------------ title
    if lab == 'doc-title' and DOC_TITLE:
        sub = clean_title(x)
        res = [['doc-title', DOC_TITLE]]
        if sub is not None:
            res.append(['doc-subtitle', sub])
        return ('splice', res)
    if lab == 'doc-data':
        # splice produced by doc-title lands here already
        return x
    return x

body = walk(doc, f)

# bib-list inside a (with ...) block that walk turned into a document splice
def tidy(x):
    if is_node(x, 'with') and len(x) >= 3 and is_node(x[-1], 'document') \
            and any(is_node(c, 'bib-list') for c in x[-1][1:]):
        return ('splice', x[-1][1:])
    return x
body = walk(body, tidy)

# ------------------------------------------------ text dashes (Cork: 0x15 en, 0x16 em)
MATHY = {'math', 'equation', 'equation*', 'align*', 'gather*', 'script-output', 'raw-data',
         'label', 'reference', 'eqref', 'cite', 'hlink', 'image', 'tuple', 'bibitem*', 'assign'}
def dashes(x, inmath=False):
    if isinstance(x, list):
        m = inmath or x[0] in MATHY
        if x[0] == 'text':
            m = False
        return [x[0]] + [dashes(y, m) for y in x[1:]]
    if inmath:
        return x
    return x.replace('---', '\x16').replace('--', '\x15')
body = dashes(body)

# ------------------------------------------------ \\mathscr: the symbol, not the font
def script_letters(x):
    if is_node(x, 'with') and len(x) == 4 and x[1:3] == ['math-font', 'cal*'] and isinstance(x[3], str) and len(x[3]) == 1:
        return ['with', 'mode', 'text', 'font', 'cal*', x[3]]
    return x
body = walk(body, script_letters)

# ------------------------------------------------ style and page layout
def restyle(x):
    if is_node(x, 'style'):
        return ['style', ['tuple', 'article', 'number-long-article', 'british'] + STYLE_PACKAGES]
    if is_node(x, 'initial'):
        return ['initial', ['collection',
            ['associate', 'font', 'TeX Gyre Pagella'],
            ['associate', 'math-font', 'TeX Gyre Pagella'],
            ['associate', 'font-base-size', '11'],
            ['associate', 'page-type', 'a4'],
            ['associate', 'page-odd', '26mm'], ['associate', 'page-even', '26mm'],
            ['associate', 'page-right', '26mm'],
            ['associate', 'page-top', '26mm'], ['associate', 'page-bot', '26mm'],
            ['associate', 'par-hyphen', 'professional'],
            ['associate', 'preamble', 'false']]]
    return x
body = walk(body, restyle)
if not any(is_node(c, 'initial') for c in body[1:]):
    body.append(restyle(['initial']))
# the user's preference: slanted inequalities everywhere
def _slant(n):
    if not isinstance(n, list) or (n and n[0] in ('raw-data', 'script-output')):
        return
    for i, c in enumerate(n):
        if isinstance(c, str):
            if i:
                n[i] = re.sub(r'<ge(q)?>', '<geqslant>', re.sub(r'<le(q)?>', '<leqslant>', c))
        else:
            _slant(c)
_slant(body)
dump(body, outp)
print('post ok', outp)
