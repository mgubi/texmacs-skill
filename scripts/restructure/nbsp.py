"""Non-breaking spaces before citations/references and in 'Lecture 3', 'Section 8', ... (text only)."""
import re, sys
from rwlib import *
SKIP = {'math', 'equation', 'equation*', 'eqnarray', 'eqnarray*', 'align', 'align*', 'script-output', 'image',
        'raw-data', 'label', 'cite', 'cite-detail', 'reference', 'eqref', 'pageref', 'hlink', 'href', 'table-of-contents',
        'bibitem*', 'bibitem', 'specific', 'hide-preamble', 'tuple', 'associate', 'tformat', 'cwith'}
REF = {'cite', 'reference', 'eqref', 'pageref'}
WORDS = (r'Lectures?|Sections?|Subsections?|Theorems?|Propositions?|Lemmas?|Corollary|Corollaries|Exercises?|Figures?|'
         r'Remarks?|Examples?|Definitions?|Chapters?|Parts?|Appendix|Tables?|Steps?|Equations?')
PAT = re.compile(r'\b(%s) (?=[0-9IVX])' % WORDS)
def is_ref(x):
    if isinstance(x, list) and x and x[0] in REF: return True
    return is_node(x, 'hlink') and isinstance(x[1], str) and re.match(r'^[0-9IVX]', x[1] or '') is not None
def fix(y, log):
    if not isinstance(y, list) or not y or not isinstance(y[0], str) or y[0] in SKIP: return
    for c in y[1:]: fix(c, log)
    i = 1
    while i < len(y):
        s = y[i]
        if isinstance(s, str):
            # split on word-number spaces
            pos = 0; new = []
            for m in PAT.finditer(s):
                new.append(s[pos:m.end(1)]); new.append(['nbsp']); pos = m.end(); log.append(m.group(0) + '#')
            new.append(s[pos:])
            # space before a reference node
            if i + 1 < len(y) and is_ref(y[i + 1]) and new[-1].endswith(' '):
                new[-1] = new[-1][:-1]; new.append(['nbsp']); log.append('->' + y[i + 1][0])
            new = [x for x in new if x != '']
            if new != [s]:
                if y[0] == 'concat': y[i:i + 1] = new; i += len(new); continue
                y[i] = ['concat'] + new
        i += 1
if __name__ == '__main__':
    dry = sys.argv[1] == '-n'; files = sys.argv[2:] if dry else sys.argv[1:]
    for f in files:
        d = load(f); log = []
        for p in body(d)[1:]: fix(p, log)
        import collections
        c = collections.Counter(l if l.startswith('->') else re.sub(r'\d.*', '', l) for l in log)
        print(f.split('/')[-1], len(log), dict(c))
        if not dry: dump(d, f)
