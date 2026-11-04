"""Beamer -> article-like LaTeX with slide markers, for the TeXmacs import.

usage: prep_slides.py slides/talk.tex out_dir
Writes out_dir/<base>.tex (then run prep.py on it) and out_dir/<base>.json
with the title data.  Frames become \\tmslide{T} ... \\tmslideend, sections
\\tmsectionslide{T}, blocks \\tmblock{T}...\\tmblockend, columns
\\tmcols \\tmcol{w} ... \\tmcolsend, \\refs{..} -> \\tmrefs{..}.
"""
import json, os, re, sys

path, out = sys.argv[1], sys.argv[2]
base = os.path.basename(path)[:-4]
s = open(path, encoding='utf-8').read()
pre, body = s.split('\\begin{document}', 1)
body = body.split('\\end{document}')[0]

def group(t, i):
    depth = 0; j = i
    while True:
        c = t[j]
        if c == '\\': j += 2; continue
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return t[i+1:j], j+1
        j += 1

def get_cmd(name):
    m = re.search(r'\\%s\s*(\[[^\]]*\])?\s*\{' % name, pre)
    if not m: return ''
    return group(pre, m.end() - 1)[0]

meta = {'title': get_cmd('title'), 'subtitle': get_cmd('subtitle'),
        'author': get_cmd('author'), 'date': get_cmd('date')}

# keep only the macro definitions of the preamble
defs = []
for m in re.finditer(r'\\(newcommand|renewcommand|providecommand|DeclareMathOperator|DeclarePairedDelimiterX?)\*?', pre):
    j = m.end()
    # take the definition up to the end of its last brace group on the line(s)
    k = pre.find('\n', j)
    line = pre[m.start():k]
    while line.count('{') > line.count('}'):
        k2 = pre.find('\n', k + 1); line = pre[m.start():k2]; k = k2
    defs.append(line)
defs += re.findall(r'\\definecolor\{[^}]*\}\{[^}]*\}\{[^}]*\}', pre)
defs = [d for d in defs if not re.match(r'\\newcommand\{\\refs\}', d)]
defs.append('\\newcommand{\\refs}[1]{\\tmrefs{#1}}')

# frames
def frame(m):
    j = m.end()
    j2 = j
    while j2 < len(body) and body[j2] in ' \t': j2 += 1
    title = ''
    if j2 < len(body) and body[j2] == '{':
        title, j2 = group(body, j2)
    return '\n\n\\tmslide{%s}\n\n' % title, j2
out_body = []; i = 0
for m in re.finditer(r'\\begin\{frame\}(\[[^\]]*\])?', body):
    pass
while True:
    m = re.compile(r'\\begin\{frame\}(\[[^\]]*\])?').search(body, i)
    if not m:
        out_body.append(body[i:]); break
    out_body.append(body[i:m.start()])
    rep, i = frame(m)
    out_body.append(rep)
body = ''.join(out_body)
body = body.replace('\\end{frame}', '\n\n\\tmslideend\n\n')
body = re.sub(r'\\frametitle\{([^}]*)\}', r'', body)
body = re.sub(r'\\section\*?\{([^}]*)\}', r'\n\n\\tmsectionslide{\1}\n\n', body)
body = body.replace('\\maketitle', '\n\n\\tmtitleslide\n\n')

# blocks
for env in ('block', 'alertblock', 'exampleblock'):
    body = re.sub(r'\\begin\{%s\}\{((?:[^{}]|\{[^{}]*\})*)\}' % env,
                  lambda m: '\n\n\\tmblock{%s}\n\n' % m.group(1), body)
    body = body.replace('\\end{%s}' % env, '\n\n\\tmblockend\n\n')

# columns
body = re.sub(r'\\begin\{columns\}(\[[^\]]*\])?', '\n\n\\\\tmcols\n\n', body)
body = re.sub(r'\\begin\{column\}(\[[^\]]*\])?\{([\d.]+)\\(?:text|line)width\}',
              lambda m: '\n\n\\tmcol{%s}\n\n' % m.group(2), body)
body = body.replace('\\end{column}', '\n\n')
body = body.replace('\\end{columns}', '\n\n\\tmcolsend\n\n')

body = re.sub(r'\\usebeamercolor\[fg\]\{alerted text\}\\large\s*(.*?)\n', lambda m: '\\alert{%s}\n' % m.group(1), body)

# sizes and spacing that only served to cram beamer frames
body = re.sub(r'\\(textstyle|displaystyle)\b\s*', '', body)
body = re.sub(r'\\setlength\{[^}]*\}\{[^}]*\}', '', body)
body = re.sub(r'\\(footnotesize|scriptsize|small|normalsize|raggedright)\b\s*', '{}', body)
# aligned rows with a trailing comment column (&& \text{...}): TeXmacs aligned has two columns
body = re.sub(r'&&\s*', r'\\qquad ', body)
body = re.sub(r'\\(medskip|bigskip)\b', r'\n\n', body)
body = re.sub(r'\\smallskip\b', '', body)
body = re.sub(r'\\vfill\b|\\centering\b', '', body)
body = body.replace('\\qed', '')
body = re.sub(r'\\begin\{center\}|\\end\{center\}', '\n\n', body)

doc = ('\\documentclass{article}\n\\usepackage{amsmath,amssymb,amsthm,graphicx}\n'
       + '\n'.join(defs) + '\n\\begin{document}\n' + body + '\n\\end{document}\n')
open(os.path.join(out, base + '.tex'), 'w', encoding='utf-8').write(doc)
json.dump(meta, open(os.path.join(out, base + '.json'), 'w'))
print('slides prepared', base, body.count('\\tmslide{'), 'frames')
