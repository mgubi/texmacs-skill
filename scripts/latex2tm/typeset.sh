#!/bin/sh
# typeset.sh base... : undump out/<base>.scm -> .tm, then typeset twice with a
# real pdf export (the export is what typesets; the save stores <references>).
cd "$(dirname "$0")"; W=$PWD
for b in "$@"; do
  ./run.sh "(tm-undump \"$W/out/$b.scm\" \"$W/out/$b.tm\")"
  for k in 1 2; do
    rm -f "out/$b.pdf"
    ./run.sh "(tm-typeset \"$W/out/$b.tm\" \"$W/out/$b.pdf\")"
  done
  [ -f "out/$b.pdf" ] || echo "NO PDF for $b"
done
