#!/bin/sh
# tm2md.sh in.tm [out.md|out.tex]
#
# Convert a TeXmacs document to Markdown (default) or LaTeX for reading, with a
# headless TeXmacs. Markdown is the better reading copy for agents: theorem and
# equation numbers and cross-references are resolved from the stored
# <\references>, formulas are LaTeX, links keep their labels. The LaTeX export
# keeps \label/\ref unresolved. Both are far more faithful than the text of the
# typeset PDF (mutool draw -F txt), which mangles inline mathematics.
#
# The conversion runs on a scratch copy of the document, with a private
# TEXMACS_HOME_PATH whose fonts/plugins/packages/styles/progs are links to the
# real home, so concurrent TeXmacs processes do not interfere. Style packages
# next to the document (*.ts) are copied with it.
#
# Binary: $TEXMACS_HEADLESS if set; otherwise the Qt port of TeXmacs Upsilon
# ("TeXmacs Upsilon Qt.app", in /Applications or ~/Downloads), otherwise the
# standard TeXmacs. Cocoa builds may not run headless; use a Qt build.
# A few stray lines "bad assign" in the Markdown are harmless.
set -e
[ $# -ge 1 ] || { echo "usage: $0 in.tm [out.md|out.tex]"; exit 2; }
IN=$1
case "$IN" in /*) ;; *) IN="$PWD/$IN";; esac
OUT=${2:-${IN%.tm}.md}
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT";; esac
[ -f "$IN" ] || { echo "no such file: $IN"; exit 1; }

X=${TEXMACS_HEADLESS:-}
if [ -z "$X" ]; then
  for c in "/Applications/TeXmacs Upsilon Qt.app/Contents/MacOS/TeXmacs" \
           "$HOME/Applications/TeXmacs Upsilon Qt.app/Contents/MacOS/TeXmacs" \
           "$HOME/Downloads/TeXmacs Upsilon Qt.app/Contents/MacOS/TeXmacs" \
           "/Applications/TeXmacs.app/Contents/MacOS/TeXmacs"; do
    [ -x "$c" ] && { X=$c; break; }
  done
fi
[ -n "$X" ] || X=texmacs

W=$(mktemp -d "${TMPDIR:-/tmp}/tm2md.XXXXXX")
H=$W/home; mkdir -p "$H"
for d in fonts plugins packages styles progs; do
  [ -e "$HOME/.TeXmacs/$d" ] && ln -s "$HOME/.TeXmacs/$d" "$H/$d"
done
cp "$IN" "$W/"
for ts in "$(dirname "$IN")"/*.ts; do [ -f "$ts" ] && cp "$ts" "$W/"; done
B=$(basename "$IN")
EXT=${OUT##*.}
TEXMACS_HOME_PATH=$H "$X" -headless -c "$W/$B" "$W/out.$EXT" -q > "$W/log.txt" 2>&1 &
P=$!; i=0
while kill -0 $P 2>/dev/null; do
  sleep 1; i=$((i+1))
  [ $i -gt ${TM2MD_TIMEOUT:-300} ] && { kill $P; echo "TIMEOUT (log: $W/log.txt)"; exit 1; }
done
[ -s "$W/out.$EXT" ] || { echo "conversion failed (log: $W/log.txt)"; exit 1; }
mv "$W/out.$EXT" "$OUT"
rm -rf "$W"
echo "$OUT"
