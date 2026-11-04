"""Assemble a TeXmacs beamer document (screens) in a given talk style from the
marker paragraphs produced by prep_slides.py (after post_notes.py has made the
content native). talk_style.scm is the stree dump of a reference talk: its
style, hide-preamble and initial environment are reused.

usage: post_slides.py mid.scm meta.json talk_style.scm number out.scm

Environment (optional):
  TM_SLIDES_PACKAGE  style package appended to the talk's style tuple
  TM_TALK_TITLE      main line of the title slide (default: meta title)
  TM_TALK_AUTHOR     author line of the title slide
  TM_TALK_FOOTER     grey line of the title slide; {part} and {date} are
                     replaced by the subtitle's first part and the date
  TM_PART_LABEL      label under section slides, followed by the number
                     (default "Lecture")
"""
import json, os, sys
SLIDES_PACKAGE = os.environ.get('TM_SLIDES_PACKAGE', '')
TALK_TITLE = os.environ.get('TM_TALK_TITLE', '')
TALK_AUTHOR = os.environ.get('TM_TALK_AUTHOR', '')
TALK_FOOTER = os.environ.get('TM_TALK_FOOTER', '{part}')
PART_LABEL = os.environ.get('TM_PART_LABEL', 'Lecture')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stree import load, dump, walk, is_node, text_of

mid, metaf, stylef, nr, outp = sys.argv[1:6]
doc = load(mid)
meta = json.load(open(metaf))
_, style, preamble, initial = load(stylef)
style = ['style', style[1] + ([SLIDES_PACKAGE] if SLIDES_PACKAGE else [])]

body = [c for c in doc[1:] if is_node(c, 'body')][0][1]
pars = body[1:]

MARKERS = {'tmslide', 'tmslideend', 'tmsectionslide', 'tmtitleslide', 'tmblock',
           'tmblockend', 'tmcols', 'tmcol', 'tmcolsend'}

def marker(p):
    """(name, arg) if paragraph p is a marker paragraph"""
    if is_node(p) and p[0] in MARKERS:
        return p[0], (p[1] if len(p) > 1 else None)
    if is_node(p, 'concat'):
        ms = [c for c in p[1:] if is_node(c) and c[0] in MARKERS]
        rest = [c for c in p[1:] if not (is_node(c) and c[0] in MARKERS)]
        if len(ms) == 1 and all(isinstance(c, str) and not c.strip() for c in rest):
            return ms[0][0], (ms[0][1] if len(ms[0]) > 1 else None)
    return None

def latex_text(t):
    """title strings from the beamer preamble (plain enough)"""
    t = t.replace('---', '\x16').replace('--', '\x15').replace('~', ' ')
    t = t.replace('\\S', '\x9f').replace('\\\\', ' ')
    import re
    t = re.sub(r'\{\\small\s*([^}]*)\}', r'\1', t)
    t = re.sub(r'\[[0-9.]+pt\]', '', t)
    return t.strip()

def math_title(t):
    """split $...$ in a title string into math nodes (simple cases)"""
    import re
    parts = re.split(r'\$([^$]*)\$', t)
    out = ['concat']
    for k, p in enumerate(parts):
        if not p: continue
        if k % 2:
            p = (p.replace('\\Phi', '<Phi>').replace('\\phi', '<phi>').replace('\\varphi', '<varphi>'))
            m = re.match(r'^(.*?)\^(\{[^}]*\}|.)_(\{[^}]*\}|.)$', p)
            if m:
                out.append(['math', ['concat', m.group(1), ['rsup', m.group(2).strip('{}')], ['rsub', m.group(3).strip('{}')]]])
            else:
                out.append(['math', p])
        else:
            out.append(p)
    return out if len(out) > 2 else (out[1] if len(out) == 2 else '')

def title_slide():
    sub = meta.get('subtitle', '')
    lect, _, rest = latex_text(sub).partition(' \x16 ')
    return ['document', ['with', 'par-mode', 'left', ['document',
        ['vspace*', '0.8cm'], '',
        ['with', 'font-size', '2.1', 'font-series', 'bold', 'color', 'dark red',
         TALK_TITLE or latex_text(meta.get('title', ''))],
        ['vspace', '0.2cm'],
        ['with', 'font-size', '1.3', math_title(rest) if rest else lect],
        ['vspace', '0.65cm'], '',
        ['small', TALK_AUTHOR],
        ['small', ['with', 'color', 'dark grey',
                   TALK_FOOTER.format(part=lect, date=latex_text(meta.get('date', '')).replace('Notes: ', ''))]],
        '']]]

def section_slide(t):
    return ['document', ['vspace*', '2.5cm'], '',
            ['with', 'font-size', '1.6', 'font-series', 'bold', 'color', 'dark red', t],
            ['vspace', '0.3cm'],
            ['with', 'color', 'dark grey', PART_LABEL + ' ' + nr], '']

def finish_blocks(items):
    """group block and column markers inside one slide"""
    out = []; i = 0
    while i < len(items):
        m = marker(items[i])
        if m and m[0] == 'tmblock':
            j = i + 1; inner = []
            while j < len(items) and not (marker(items[j]) and marker(items[j])[0] == 'tmblockend'):
                inner.append(items[j]); j += 1
            inner = finish_blocks(inner)
            out.append(['myframed', ['document', ['strong', m[1]]] + inner])
            i = j + 1; continue
        if m and m[0] == 'tmcols':
            j = i + 1; cols = []; cur = None
            while j < len(items) and not (marker(items[j]) and marker(items[j])[0] == 'tmcolsend'):
                mm = marker(items[j])
                if mm and mm[0] == 'tmcol':
                    cur = [text_of(mm[1]), []]; cols.append(cur)
                elif cur is not None:
                    cur[1].append(items[j])
                j += 1
            n = len(cols)
            fmt = ['tformat',
                   ['cwith', '1', '1', '1', '-1', 'cell-valign', 't'],
                   ['cwith', '1', '1', '1', '-1', 'cell-hyphen', 't'],
                   ['cwith', '1', '1', '1', '-1', 'cell-lsep', '0em'],
                   ['cwith', '1', '1', '1', '-1', 'cell-rsep', '1em']]
            for k, (w, _) in enumerate(cols, 1):
                fmt += [['cwith', '1', '1', str(k), str(k), 'cell-width', w + 'par'],
                        ['cwith', '1', '1', str(k), str(k), 'cell-hmode', 'exact']]
            def scale(w):
                def g(y):
                    if is_node(y, 'image') and isinstance(y[2], str) and y[2].endswith('par'):
                        try:
                            y[2] = '%.3fpar' % (float(y[2][:-3] or 1) * float(w))
                        except ValueError:
                            pass
                    return y
                return g
            row = ['row'] + [['cell', ['document'] + ([walk(p, scale(w)) for p in finish_blocks(c)] or [''])] for w, c in cols]
            fmt.append(['table', row])
            out.append(['wide-tabular', fmt])
            i = j + 1; continue
        out.append(items[i]); i += 1
    return out

def slide_content(items, title):
    # empty paragraphs and stray markers out
    items = [p for p in items if not (isinstance(p, str) and not p.strip())]
    items = finish_blocks(items)
    refs = [p for p in items if is_node(p, 'tmrefs')]
    items = [p for p in items if not is_node(p, 'tmrefs')]
    d = ['document', ['mytitle', title], ''] + items
    for r in refs:
        d.append(['with', 'par-mode', 'right', ['small', ['with', 'color', 'dark grey', r[1]]]])
    return d

screens = []
i = 0
while i < len(pars):
    m = marker(pars[i])
    if m and m[0] == 'tmtitleslide':
        screens.append(title_slide()); i += 1; continue
    if m and m[0] == 'tmsectionslide':
        screens.append(section_slide(m[1])); i += 1; continue
    if m and m[0] == 'tmslide':
        j = i + 1; items = []
        while j < len(pars) and not (marker(pars[j]) and marker(pars[j])[0] == 'tmslideend'):
            items.append(pars[j]); j += 1
        screens.append(slide_content(items, m[1]))
        i = j + 1; continue
    i += 1

# inline markup: alert -> strong, theorem-like -> unnumbered
STAR = {'theorem', 'proposition', 'lemma', 'corollary', 'definition', 'remark', 'example'}
def inline(x):
    if is_node(x, 'tmrefs'):
        return ['small', ['with', 'color', 'dark grey', x[1]]]
    if is_node(x, 'script-output'):
        # beamer 16:9 text width is about 397pt: keep the picture's relative size
        img = x[4]
        if is_node(img, 'image'):
            import re
            m = re.search(r'%%BoundingBox: (-?\d+) (-?\d+) (-?\d+) (-?\d+)', img[1][1][1])
            if m:
                w = (int(m.group(3)) - int(m.group(1))) / 397.0
                img[2] = '%.3fpar' % min(w, 1.0)
        return ['with', 'par-mode', 'center', x]
    if is_node(x, 'alert'):
        return ['strong'] + x[1:]
    if is_node(x) and x[0] in STAR:
        return [x[0] + '*'] + x[1:]
    if is_node(x, 'equation'):
        return ['equation*'] + x[1:]
    return x
screens = [walk(s, inline) for s in screens]

scr = ['screens'] + [['shown' if k == 0 else 'hidden', s] for k, s in enumerate(screens)]
out = ['document', ['TeXmacs', '2.1.4'], style,
       ['body', ['document', scr]], initial]
dump(out, outp)
print('slides', len(screens))
