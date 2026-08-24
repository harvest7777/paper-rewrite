#!/usr/bin/env bash
# usage: ./run.sh ./baseline/bin/dot
set -e
if [ -z "$1" ]; then echo "usage: $0 ./baseline/bin/dot" >&2; exit 1; fi
cd "$(dirname "$0")"

DOT="$1"
DIR="$(dirname "$DOT")"   # ./baseline/bin
NAME="${DIR//\//-}"       # baseline-bin

OUT="results/$NAME/hyperfine-dumps"
mkdir -p "$OUT"

for graph in graphs/*.gv; do
  g="$(basename "$graph")"
  for phase in 1 2 3 full; do
    if [ "$phase" = full ]; then flag=""; else flag="-Gphase=$phase"; fi
    hyperfine -w 3 -r 5 --export-json "$OUT/$g-phase$phase.json" \
      "$DOT $flag $graph -o /dev/null"
  done
done
