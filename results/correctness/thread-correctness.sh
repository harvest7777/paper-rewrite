#!/usr/bin/env bash
# Does the parallel binaries' output depend on thread count?
# Compares dot -Tdot against the baseline for every tests/graphs/*.gv, at
# GV_THREADS=1, 2, 8 and at the binary's own default.
set -e
cd /Users/ryantran/Developer/projects/paper-rewrite

BASELINE=binaries/timestamped/bin/dot
GRAPHS=sandboxes/timestamped/graphviz/tests/graphs
BINARIES=(claude_parallel claude_parallel_2)
THREADS=(1 2 8 default)
TIMEOUT=60
TIMEOUT_RC=142

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# run <out> <binary> <graph> [threads]: lay out with a time limit; rc holds the code.
run() {
  rc=0
  if [ -n "$4" ] && [ "$4" != default ]; then
    GV_THREADS="$4" perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" "$2" -Tdot "$3" > "$1" 2>/dev/null || rc=$?
  else
    perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" "$2" -Tdot "$3" > "$1" 2>/dev/null || rc=$?
  fi
}

for binary in "${BINARIES[@]}"; do
  for t in "${THREADS[@]}"; do
    same=0; differ=0; skipped=0
    for graph in "$GRAPHS"/*.gv; do
      name=$(basename "$graph")

      run "$work/base" "$BASELINE" "$graph"
      base_rc=$rc
      [ $base_rc -eq $TIMEOUT_RC ] && { skipped=$((skipped+1)); continue; }

      # Only compare graphs the baseline reproduces byte for byte.
      run "$work/base2" "$BASELINE" "$graph"
      if [ $rc -ne $base_rc ] || ! cmp -s "$work/base" "$work/base2"; then
        skipped=$((skipped+1)); continue
      fi

      run "$work/agent" "binaries/$binary/bin/dot" "$graph" "$t"
      if [ $rc -ne $base_rc ]; then
        differ=$((differ+1))
        echo "  EXIT MISMATCH  $binary GV_THREADS=$t  $name  baseline=$base_rc agent=$rc"
      elif cmp -s "$work/base" "$work/agent"; then
        same=$((same+1))
      else
        differ=$((differ+1))
        echo "  OUTPUT DIFFERS $binary GV_THREADS=$t  $name"
      fi
    done
    printf '%-20s GV_THREADS=%-8s identical %4d   differing %3d   skipped %3d\n' \
      "$binary" "$t" "$same" "$differ" "$skipped"
  done
done
