#!/bin/sh
# typeset_all.sh dir base... : undump dir/<base>.scm -> .tm, two typesetting passes each
cd "$(dirname "$0")/.."; W=$PWD; D=$1; shift
for b in "$@"; do
  rm -f "$W/$D/$b.tm"
  ./run.sh "(tm-undump \"$W/$D/$b.scm\" \"$W/$D/$b.tm\")"
  for k in 1 2; do
    rm -f "$W/$D/$b.pdf"
    ./run.sh "(tm-typeset \"$W/$D/$b.tm\" \"$W/$D/$b.pdf\")"
    grep -a 'convert-error\|SCHEME-ERROR' tmlog.txt | head -3
  done
  [ -f "$W/$D/$b.pdf" ] || echo "NO PDF for $b"
done
