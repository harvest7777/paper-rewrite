#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

BASELINE=timestamped
AGENTS=(claude codex)
ENGINES=(dot neato fdp twopi circo)
GRAPHS=sandboxes/$BASELINE/graphviz/tests/graphs

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# An engine whose output varies run to run cannot be byte-compared. Force-directed
# engines fail this. Probe several graphs, since some are stable by luck.
probes=$(ls "$GRAPHS"/*.gv | awk 'NR%40==1' | head -6)
deterministic=()
for engine in "${ENGINES[@]}"; do
  stable=yes
  for probe in $probes; do
    "./binaries/$BASELINE/bin/$engine" -Tdot "$probe" > "$work/p1" 2>/dev/null || true
    "./binaries/$BASELINE/bin/$engine" -Tdot "$probe" > "$work/p2" 2>/dev/null || true
    if ! cmp -s "$work/p1" "$work/p2"; then
      echo "SKIP $engine: nondeterministic, differs from itself on $(basename "$probe")"
      stable=no
      break
    fi
  done
  [ "$stable" = yes ] && deterministic+=("$engine")
done
ENGINES=("${deterministic[@]}")

total_same=0
total_diff=0

for engine in "${ENGINES[@]}"; do
  same=0
  differ=0
  errored=0

  for graph in "$GRAPHS"/*.gv; do
    "./binaries/$BASELINE/bin/$engine" -Tdot "$graph" > "$work/base" 2>/dev/null
    baseline_rc=$?

    for agent in "${AGENTS[@]}"; do
      "./binaries/$agent/bin/$engine" -Tdot "$graph" > "$work/$agent" 2>/dev/null
      agent_rc=$?

      if [ $baseline_rc -ne 0 ] && [ $agent_rc -ne 0 ]; then
        errored=$((errored + 1))
      elif [ $baseline_rc -ne $agent_rc ]; then
        differ=$((differ + 1))
        echo "  EXIT MISMATCH  $agent  $(basename "$graph")  baseline=$baseline_rc agent=$agent_rc"
      elif cmp -s "$work/base" "$work/$agent"; then
        same=$((same + 1))
      else
        differ=$((differ + 1))
        echo "  OUTPUT DIFFERS $agent  $(basename "$graph")"
      fi
    done
  done

  printf '%-7s identical %4d   differing %3d   both-errored %3d\n' \
    "$engine" "$same" "$differ" "$errored"
  total_same=$((total_same + same))
  total_diff=$((total_diff + differ))
done

echo
if [ $total_diff -eq 0 ]; then
  echo "PASS  $total_same comparisons, all byte-identical to $BASELINE"
else
  echo "FAIL  $total_diff of $((total_same + total_diff)) comparisons differ"
  exit 1
fi
