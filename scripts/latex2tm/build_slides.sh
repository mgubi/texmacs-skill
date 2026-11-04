#!/bin/sh
# build_slides.sh BASE N  -> sout/BASE.tm / .pdf  (slides/BASE.tex, part number N)
# needs talk_style.scm: the stree dump of a reference talk (tm-dump in dump.scm)
set -e
cd "$(dirname "$0")"; W=$PWD
b=$1; n=${2:-1}
mkdir -p sprep sout prep/figures
cp slides/*.png slides/*.pdf prep/figures/ 2>/dev/null || true
python3 -I prep_slides.py slides/$b.tex sprep
python3 -I prep.py sprep $b.tex prep
./run.sh "(tm-latex \"$W/prep/$b.tex\" \"$W/sout/$b.raw.tm\") (tm-dump \"$W/sout/$b.raw.tm\" \"$W/sout/$b.raw.scm\")"
python3 -I post_notes.py sout/$b.raw.scm sout/$b.mid.scm prep/figures
python3 -I post_slides.py sout/$b.mid.scm sprep/$b.json talk_style.scm $n sout/$b.scm
./run.sh "(tm-undump \"$W/sout/$b.scm\" \"$W/sout/$b.tm\")"
rm -f sout/$b.pdf
./run.sh "(tm-typeset \"$W/sout/$b.tm\" \"$W/sout/$b.pdf\")"
ls -la sout/$b.tm sout/$b.pdf
