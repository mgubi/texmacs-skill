#!/bin/sh
# build_note.sh base   (phase 1: prep, import, post, typeset)
set -e
cd "$(dirname "$0")"; W=$PWD
b=$1
mkdir -p prep/figures out
cp src/figures/* prep/figures/
python3 -I prep.py src $b.tex prep
./run.sh "(tm-latex \"$W/prep/$b.tex\" \"$W/out/$b.raw.tm\") (tm-dump \"$W/out/$b.raw.tm\" \"$W/out/$b.raw.scm\")"
python3 -I post_notes.py out/$b.raw.scm out/$b.scm prep/figures
./typeset.sh $b
ls -la out/$b.tm out/$b.pdf
