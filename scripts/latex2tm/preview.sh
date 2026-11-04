#!/bin/sh
cd "$(dirname "$0")"; W=$PWD; b=$1
python3 -I preview_slides.py sout/$b.scm sout/$b.preview.scm
./run.sh "(tm-undump \"$W/sout/$b.preview.scm\" \"$W/sout/$b.preview.tm\")"
rm -f sout/$b.preview.pdf
./run.sh "(tm-typeset \"$W/sout/$b.preview.tm\" \"$W/sout/$b.preview.pdf\")"
mutool info sout/$b.preview.pdf 2>/dev/null | grep Pages
