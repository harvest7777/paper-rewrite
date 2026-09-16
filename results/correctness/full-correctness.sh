#!/usr/bin/env bash
# Byte-identity sweep for every binary that shipped layout code.
# Per graph: run the baseline twice (skip graphs it cannot reproduce), then each
# binary once, comparing -Tdot output byte for byte.
# Written for bash 3.2 (macOS): indexed arrays only, no associative arrays.
set -u
cd /Users/ryantran/Developer/projects/paper-rewrite
GRAPHS=sandboxes/timestamped/graphviz/tests/graphs
BINARIES=(claude claude_2 claude_parallel claude_parallel_2 codex)
ENGINES=(dot neato)
TIMEOUT=60; TIMEOUT_RC=142
n=${#BINARIES[@]}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
run() { rc=0; perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" "$2" -Tdot "$3" > "$1" 2>/dev/null || rc=$?; }

for engine in "${ENGINES[@]}"; do
  same=(); differ=()
  for ((i = 0; i < n; i++)); do same[$i]=0; differ[$i]=0; done
  skipped=0; compared=0
  for graph in "$GRAPHS"/*.gv; do
    name=$(basename "$graph")
    run "$work/base" "binaries/timestamped/bin/$engine" "$graph"; base_rc=$rc
    if [ $base_rc -eq $TIMEOUT_RC ]; then skipped=$((skipped + 1)); continue; fi
    run "$work/base2" "binaries/timestamped/bin/$engine" "$graph"
    if [ $rc -ne $base_rc ] || ! cmp -s "$work/base" "$work/base2"; then
      skipped=$((skipped + 1)); continue
    fi
    compared=$((compared + 1))
    for ((i = 0; i < n; i++)); do
      b=${BINARIES[$i]}
      run "$work/out" "binaries/$b/bin/$engine" "$graph"
      if [ $rc -eq $base_rc ] && cmp -s "$work/base" "$work/out"; then
        same[$i]=$(( ${same[$i]} + 1 ))
      else
        differ[$i]=$(( ${differ[$i]} + 1 ))
        echo "  DIFFERS $engine $b $name (baseline_rc=$base_rc agent_rc=$rc)"
      fi
    done
  done
  echo "== $engine  compared $compared graphs, skipped $skipped the baseline could not reproduce"
  for ((i = 0; i < n; i++)); do
    printf '   %-20s identical %4d   differing %3d\n' "${BINARIES[$i]}" "${same[$i]}" "${differ[$i]}"
  done
done
echo ALL-DONE
