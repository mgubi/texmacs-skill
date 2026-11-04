#!/bin/sh
cd "$(dirname "$0")"
python3 -I fill_xref.py out "$@"
./typeset.sh "$@"
