#!/bin/sh
X=/Applications/TeXmacs.app/Contents/MacOS/TeXmacs
"$X" -headless -x "(begin (load \"$PWD/dump.scm\") (catch #t (lambda () $1) (lambda args (display \"SCHEME-ERROR \") (write args) (newline))) (quit-TeXmacs))" > tmlog.txt 2>&1 &
P=$!; i=0
while kill -0 $P 2>/dev/null; do sleep 1; i=$((i+1)); [ $i -gt 280 ] && kill $P && echo TIMEOUT; done
grep -a "SCHEME-ERROR" tmlog.txt || true
