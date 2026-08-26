#!/usr/bin/env bash
# Benchmark every binary in binaries/ across every graph and phase.
#
# All binaries for a given (graph, phase) are measured in ONE hyperfine call so
# they run seconds apart under the same thermal conditions. Measuring them in
# separate blocks produced a ~20% order-dependent bias on this machine.
set -e
cd "$(dirname "$0")"

DOTS=(binaries/*/bin/dot)
mkdir -p results

for graph in graphs/*.gv; do
  g="$(basename "$graph")"
  for phase in 1 2 3 full; do
    if [ "$phase" = full ]; then flag=""; else flag="-Gphase=$phase"; fi

    cmds=()
    for dot in "${DOTS[@]}"; do
      cmds+=("$dot $flag $graph -o /dev/null")
    done

    echo "==> $g phase$phase"
    hyperfine -w 10 -r 10 --export-json "results/$g-phase$phase.json" "${cmds[@]}"
  done
done
