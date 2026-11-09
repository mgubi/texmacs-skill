#!/usr/bin/env python3
"""tmpatch.py: format-respecting edits of TeXmacs .tm files.

TeXmacs files are serialized trees in the Cork (T1) encoding, not UTF-8:
accented Latin letters are single bytes (mostly as in Latin-1, but e.g.
§ = 0x9F, Œ = 0xD7, ß = 0xFF), Cork bytes below 0x20 are written as a
backslash and a letter (en dash 0x15 is the two characters "\\U"), and
any other Unicode character is written <#XXXX>.  UTF-8 tools corrupt such
files, and an edit that leaves one '<' or '>' unbalanced can make TeXmacs
drop the rest of the document without an error.

This tool lets an agent write patches in readable UTF-8 with TeXmacs markup,
and applies them safely:

  * the patch text is encoded to the .tm serialization (Cork bytes, "\\X"
    escapes for Cork control bytes, <#XXXX> for everything else);
  * the old text is matched whitespace-insensitively (TeXmacs rewraps lines),
    and must occur exactly COUNT times (default 1);
  * all blocks are applied atomically, in order;
  * after patching, every top-level paragraph of the body must have balanced
    angle brackets and the block tags <\\tag> ... </tag> must nest; otherwise
    nothing is written;
  * --check additionally imports the patched file with a headless TeXmacs
    (tm-dump) and compares the number of body paragraphs with the text;
  * a backup FILE.orig is kept unless --no-backup.

Patch format (UTF-8 text file, any number of blocks):

    @@ replace [count=N]
    <<<
    old text, TeXmacs markup, Unicode allowed (é, –, ∞ ...)
    ===
    new text
    >>>

An empty new part deletes the old text.  Lines before the first "@@" are
comments.  The markers must be alone on their lines.

Usage:
    tmpatch.py FILE.tm PATCH [--dry-run] [--check] [--no-backup] [--force]
    tmpatch.py --show FILE.tm      # print the file decoded to UTF-8
    tmpatch.py --encode TEXT       # print TEXT in the .tm serialization
"""
import os, re, subprocess, sys, tempfile, difflib, shutil

# Cork (T1) code points 0x00-0x1F and 0x80-0xFF; 0x20-0x7F are ASCII.
_CORK_LOW = ['`', '\u00b4', '\u02c6', '\u02dc', '\u00a8', '\u02dd', '\u02da', '\u02c7',
             '\u02d8', '\u00af', '\u02d9', '\u00b8', '\u02db', '\u201a', '\u2039', '\u203a',
             '\u201c', '\u201d', '\u201e', '\u00ab', '\u00bb', '\u2013', '\u2014', '\u200c',
             '\u2080', '\u0131', '\u0237', '\ufb00', '\ufb01', '\ufb02', '\ufb03', '\ufb04']
_CORK_HIGH = ('\u0102\u0104\u0106\u010c\u010e\u011a\u0118\u011e\u0139\u013d\u0141\u0143\u0147\u014a\u0150\u0154'
              '\u0158\u015a\u0160\u015e\u0164\u0162\u0170\u016e\u0178\u0179\u017d\u017b\u0132\u0130\u0111\u00a7'
              '\u0103\u0105\u0107\u010d\u010f\u011b\u0119\u011f\u013a\u013e\u0142\u0144\u0148\u014b\u0151\u0155'
              '\u0159\u015b\u0161\u015f\u0165\u0163\u0171\u016f\u00ff\u017a\u017e\u017c\u0133\u00a1\u00bf\u00a3'
              '\u00c0\u00c1\u00c2\u00c3\u00c4\u00c5\u00c6\u00c7\u00c8\u00c9\u00ca\u00cb\u00cc\u00cd\u00ce\u00cf'
              '\u00d0\u00d1\u00d2\u00d3\u00d4\u00d5\u00d6\u0152\u00d8\u00d9\u00da\u00db\u00dc\u00dd\u00de\u1e9e'
              '\u00e0\u00e1\u00e2\u00e3\u00e4\u00e5\u00e6\u00e7\u00e8\u00e9\u00ea\u00eb\u00ec\u00ed\u00ee\u00ef'
              '\u00f0\u00f1\u00f2\u00f3\u00f4\u00f5\u00f6\u0153\u00f8\u00f9\u00fa\u00fb\u00fc\u00fd\u00fe\u00df')
assert len(_CORK_LOW) == 32 and len(_CORK_HIGH) == 128
ENC = {}
for i, u in enumerate(_CORK_LOW):
    ENC.setdefault(u, '\\' + chr(i + 0x40))
for i, u in enumerate(_CORK_HIGH):
    ENC.setdefault(u, chr(0x80 + i))
DEC_LOW = {chr(i + 0x40): u for i, u in enumerate(_CORK_LOW)}
DEC_HIGH = {chr(0x80 + i): u for i, u in enumerate(_CORK_HIGH)}


def encode(text):
    """UTF-8 text with TeXmacs markup -> .tm serialization (a str of code points < 256)."""
    out = []
    for ch in text:
        o = ord(ch)
        if o < 0x80:
            out.append(ch)
        elif ch in ENC:
            out.append(ENC[ch])
        else:
            out.append('<#%X>' % o)
    return ''.join(out)


def decode(tm):
    """.tm serialization -> readable UTF-8 (Cork bytes, \\X escapes and <#XXXX> resolved)."""
    def esc(m):
        c = m.group(1)
        return DEC_LOW.get(c, m.group(0))
    s = re.sub(r'\\\\|\\([@-Z\[\]^_])', lambda m: m.group(0) if m.group(0) == '\\\\' else esc(m), tm)
    s = ''.join(DEC_HIGH.get(c, c) for c in s)
    return re.sub(r'<#([0-9A-Fa-f]{2,6})>', lambda m: chr(int(m.group(1), 16)), s)


def read_tm(path):
    with open(path, encoding='latin-1', newline='') as f:
        return f.read()


def write_tm(path, s):
    with open(path, 'w', encoding='latin-1', newline='') as f:
        f.write(s)


def parse_patch(text):
    blocks = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        m = re.match(r'@@\s*replace(?:\s+count=(\d+))?\s*$', lines[i])
        if not m:
            if lines[i].startswith('@@'):
                sys.exit('bad block header: %r' % lines[i])
            i += 1
            continue
        count = int(m.group(1) or 1)
        if i + 1 >= len(lines) or lines[i + 1].strip() != '<<<':
            sys.exit('expected <<< after %r' % lines[i])
        j = i + 2
        old = []
        while j < len(lines) and lines[j].strip() != '===':
            old.append(lines[j]); j += 1
        k = j + 1
        new = []
        while k < len(lines) and lines[k].strip() != '>>>':
            new.append(lines[k]); k += 1
        if j >= len(lines) or k >= len(lines):
            sys.exit('unterminated block at line %d' % (i + 1))
        blocks.append((count, '\n'.join(old), '\n'.join(new)))
        i = k + 1
    if not blocks:
        sys.exit('no @@ replace blocks in the patch')
    return blocks


def apply(s, blocks):
    for n, (count, old, new) in enumerate(blocks, 1):
        o, w = encode(old), encode(new)
        words = o.split()
        if not words:
            sys.exit('block %d: empty old text' % n)
        pat = r'\s+'.join(re.escape(x) for x in words)
        ms = list(re.finditer(pat, s))
        if len(ms) != count:
            sys.exit('block %d: old text found %d times, expected %d:\n%s'
                     % (n, len(ms), count, old[:300]))
        for m in reversed(ms):
            s = s[:m.start()] + w + s[m.end():]
    return s


# ---------------------------------------------------------------- checks

_SYM = re.compile(r'\\<[^<>]*\\>')


def _strip(p):
    p = _SYM.sub('', p)
    p = p.replace('\\\\', '').replace('\\<', '').replace('\\>', '')
    return re.sub(r'<#[0-9A-Fa-f]+>', '', p)


def body_of(s):
    if '<\\body>' not in s:
        return None
    return s.split('<\\body>', 1)[1].split('</body>', 1)[0]


def paragraphs(body):
    return [p for p in re.split(r'\n[ \t]*\n', body) if p.strip()]


def top_paragraphs(body):
    """Paragraphs of the body itself: blank lines inside block tags do not count."""
    q = _strip(body)
    tok = re.compile(r'<\\([A-Za-z0-9*_-]+)[|>]|</([A-Za-z0-9*_-]+)>|\n[ \t]*\n')
    depth, last, n = 0, 0, 0
    for m in tok.finditer(q):
        if m.group(1):
            depth += 1
        elif m.group(2):
            depth -= 1
        elif depth == 0:
            if q[last:m.start()].strip():
                n += 1
            last = m.end()
    if q[last:].strip():
        n += 1
    return n


def structure_errors(s):
    errs = []
    body = body_of(s)
    if body is None:
        return ['no <\\body> ... </body>']
    for i, p in enumerate(paragraphs(body)):
        q = _strip(p)
        if q.count('<') != q.count('>'):
            errs.append('paragraph %d: %+d unbalanced angle brackets: %s'
                        % (i, q.count('<') - q.count('>'), ' '.join(p.split())[:160]))
    stack = []
    for m in re.finditer(r'<\\([A-Za-z0-9*_-]+)[|>]|</([A-Za-z0-9*_-]+)>', _strip(body)):
        if m.group(1):
            stack.append(m.group(1))
        else:
            if not stack or stack[-1] != m.group(2):
                errs.append('block tag </%s> does not close %s'
                            % (m.group(2), ('<\\%s>' % stack[-1]) if stack else 'anything'))
                break
            stack.pop()
    if stack:
        errs.append('unclosed block tags: %s' % ', '.join('<\\%s>' % t for t in stack))
    return errs


def texmacs_binary():
    # The parse check dumps the tree with Guile's write.  The standard TeXmacs
    # writes it in full; in TeXmacs Upsilon write abbreviates lists after 40
    # elements with "..." (mgubi/texmacs#840), which would look like a
    # truncated body.  Prefer the standard build.
    x = os.environ.get('TEXMACS_CHECK')
    if x:
        return x
    home = os.path.expanduser('~')
    for c in ['/Applications/TeXmacs.app/Contents/MacOS/TeXmacs',
              '/Applications/TeXmacs Upsilon Qt.app/Contents/MacOS/TeXmacs',
              home + '/Applications/TeXmacs Upsilon Qt.app/Contents/MacOS/TeXmacs',
              home + '/Downloads/TeXmacs Upsilon Qt.app/Contents/MacOS/TeXmacs']:
        if os.access(c, os.X_OK):
            return c
    return 'texmacs'


def parse_check(path, s):
    """Import the file with a headless TeXmacs and compare body paragraph counts."""
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, '..', 'latex2tm'))
    from stree import load
    dump_scm = os.path.join(here, '..', 'latex2tm', 'dump.scm')
    w = tempfile.mkdtemp(prefix='tmpatch.')
    try:
        home = os.path.join(w, 'home'); os.mkdir(home)
        for d in ['fonts', 'plugins', 'packages', 'styles', 'progs']:
            src = os.path.expanduser('~/.TeXmacs/' + d)
            if os.path.exists(src):
                os.symlink(src, os.path.join(home, d))
        tm = os.path.join(w, os.path.basename(path)); write_tm(tm, s)
        out = os.path.join(w, 'out.scm')
        expr = ('(begin (load "%s") (catch #t (lambda () (tm-dump "%s" "%s")) '
                '(lambda args (display "SCHEME-ERROR ") (write args) (newline))) (quit-TeXmacs))'
                % (dump_scm, tm, out))
        env = dict(os.environ, TEXMACS_HOME_PATH=home)
        r = subprocess.run([texmacs_binary(), '-headless', '-x', expr], env=env,
                           capture_output=True, text=True, timeout=300)
        if not os.path.exists(out):
            return ['TeXmacs import failed: ' + (r.stdout + r.stderr)[-400:]]
        tree = load(out)
        body = None
        for c in tree[1:]:
            if isinstance(c, list) and c and c[0] == 'body':
                body = c[1]
        if body is None:
            return ['TeXmacs found no body (the document was dropped)']
        n_tree = len(body) - 1 if isinstance(body, list) and body[0] == 'document' else 1
        last = body[-1] if isinstance(body, list) else body
        if isinstance(last, str) and last.strip() == '...':
            return ['the dump was abbreviated by Guile (set TEXMACS_CHECK to the standard TeXmacs)']
        n_text = top_paragraphs(body_of(s))
        if n_tree != n_text:
            return ['TeXmacs reads %d body paragraphs, the text has %d' % (n_tree, n_text)]
        return []
    finally:
        shutil.rmtree(w, ignore_errors=True)


def main(argv):
    if len(argv) >= 2 and argv[0] == '--show':
        sys.stdout.write(decode(read_tm(argv[1])))
        return
    if len(argv) >= 2 and argv[0] == '--encode':
        sys.stdout.write(encode(' '.join(argv[1:])) + '\n')
        return
    flags = {a for a in argv if a.startswith('--')}
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    path, patch = args
    s0 = read_tm(path)
    with open(patch, encoding='utf-8') as f:
        blocks = parse_patch(f.read())
    before = set(structure_errors(s0))
    s1 = apply(s0, blocks)
    errs = [e for e in structure_errors(s1) if e not in before]
    if '--check' in flags and not errs:
        errs += parse_check(path, s1)
    if errs and '--force' not in flags:
        sys.exit('refusing to write %s:\n  ' % path + '\n  '.join(errs))
    if '--dry-run' in flags:
        d = difflib.unified_diff(decode(s0).splitlines(), decode(s1).splitlines(),
                                 path, path + ' (patched)', lineterm='', n=1)
        print('\n'.join(d))
        return
    if '--no-backup' not in flags:
        write_tm(path + '.orig', s0)
    write_tm(path, s1)
    print('%s: %d block(s) applied%s' % (path, len(blocks), ', checked by TeXmacs' if '--check' in flags else ''))


if __name__ == '__main__':
    main(sys.argv[1:])
