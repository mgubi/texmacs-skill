#!/bin/sh
# build_all_notes.sh BASE... : build_note.sh for each base, then fill the
# cross-document links (phase2.sh) and report pages and unresolved '?'.
cd "$(dirname "$0")"
for b in "$@"; do ./build_note.sh $b 2>&1 | grep -v "^-rw"; done
./phase2.sh "$@"
for b in "$@"; do echo "$b: $(mutool info out/$b.pdf 2>/dev/null | grep Pages) ?=$(mutool draw -F txt -o - out/$b.pdf 2>/dev/null | grep -o '?' | wc -l)"; done
