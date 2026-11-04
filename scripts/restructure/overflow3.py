import sys, subprocess, re
from rwlib import *
def untitled(scm):
    d = load(scm); sc = []
    visit(d, lambda y: sc.append(y) if is_node(y, 'screens') else None)
    out = set()
    for k, s in enumerate(sc[0][1:], 1):
        t = []; visit(s, lambda y: t.append(1) if is_node(y, 'mytitle') else None)
        if not t: out.add(k)
    return out, len(sc[0]) - 1
for scm, pdf in zip(sys.argv[1::2], sys.argv[2::2]):
    un, ns = untitled(scm)
    n = int(re.search(r'Pages: (\d+)', subprocess.run(['mutool', 'info', pdf], capture_output=True, text=True).stdout).group(1))
    last = 0; over = []
    for p in range(1, n + 1):
        t = subprocess.run(['mutool', 'draw', '-F', 'txt', '-o', '-', pdf, str(p)], capture_output=True, text=True).stdout
        m = re.search(r'SLIDEMARK(\d+)', t)
        if m: last = int(m.group(1))
        elif last + 1 in un: last += 1
        else: over.append(last)
    print(pdf.split('/')[-1], ns, 'slides', n, 'pages; overflowing:', over)
