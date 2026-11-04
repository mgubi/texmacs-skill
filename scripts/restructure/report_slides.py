import sys, re
from rwlib import *
for f in sys.argv[1:]:
    doc = load(f); scr = []
    visit(doc, lambda x: scr.append(x) if is_node(x, 'screens') else None)
    print('=====', os.path.basename(f))
    for k, s in enumerate(scr[0][1:], 1):
        sl = lecture_slots(s)
        if not sl: continue
        tik = []
        visit(s, lambda x: tik.append(x) if is_node(x, 'script-output') else None)
        intik = sum(len(lecture_slots(t)) for t in tik)
        t = re.sub(r'\s+', ' ', flat(s))
        ctx = [t[max(0, m.start()-35): m.end()+25] for m in re.finditer(r'Lectures?\s*[1-9]', t)]
        print('  %2d %-16s tikz=%d %s' % (k, [x[1].replace('\x15', '-') for x in sl], intik, ' | '.join(ctx)[:330]))
