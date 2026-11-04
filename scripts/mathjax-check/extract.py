import re, json, sys, glob
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=True); s.t=[]; s.skip=0
    def handle_starttag(s,tag,a):
        if tag in ('script','style','title'): s.skip+=1
    def handle_endtag(s,tag):
        if tag in ('script','style','title'): s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.t.append(d)
out=[]
import os
for f in sorted(glob.glob(os.path.join(sys.argv[1], os.environ.get('TM_HTML_GLOB', '*.html')))):
    raw=open(f,encoding='utf-8').read()
    for m in re.finditer(r'\\\((?:(?!\\\)).)*?<[A-Za-z!/?](?:(?!\\\)).)*?\\\)',raw,re.S):
        print('RAW < IN MATH', f.split('/')[-1], m.group(0)[:120].replace('\n',' '))
    p=P(); p.feed(raw); t=''.join(p.t)
    pat=re.compile(r'\\\((.*?)\\\)|\\\[(.*?)\\\]|(\\begin\{(\w+\*?)\}.*?\\end\{\4\})',re.S)
    for m in pat.finditer(t):
        tex=m.group(1) if m.group(1) is not None else (m.group(2) if m.group(2) is not None else m.group(3))
        out.append({'file':f.split('/')[-1],'tex':tex,'display':m.group(1) is None})
json.dump(out,open(sys.argv[2],'w'))
print(len(out))
