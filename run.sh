#!/usr/bin/env bash
# Benchmark every binary in binaries/ across every graph and phase.
set -e
cd "$(dirname "$0")"

for bin in binaries/*; do
  name="$(basename "$bin")"
  dot="$bin/bin/dot"
  out="results/$name/hyperfine-dumps"
  mkdir -p "$out"
  echo "==> $name"

  for graph in graphs/*.gv; do
    g="$(basename "$graph")"
    for phase in 1 2 3 full; do
      if [ "$phase" = full ]; then flag=""; else flag="-Gphase=$phase"; fi
      hyperfine -w 3 -r 5 --export-json "$out/$g-phase$phase.json" \
        "$dot $flag $graph -o /dev/null"
    done
  done
done
