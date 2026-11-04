import sys, re
from rwlib import *
for f in sys.argv[1:]:
    doc = load(f); b = body(doc)
    print('=====', os.path.basename(f))
    for i, p in enumerate(b[1:]):
        s = lecture_slots(p)
        if s:
            t = re.sub(r'\s+', ' ', flat(p))
            print('  %3d %-14s %s' % (i, [x[1].replace('\x15', '-') for x in s], t[:150]))
