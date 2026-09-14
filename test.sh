#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

BASELINE=timestamped
AGENTS=(claude codex)
ENGINES=(dot neato fdp twopi circo)
GRAPHS=sandboxes/$BASELINE/graphviz/tests/graphs
# Seconds before a single layout is killed. Some engines (circo on b100.gv) run
# for hours on the larger test graphs.
TIMEOUT=60
TIMEOUT_RC=142   # SIGALRM

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# run <out> <binary> <graph>: lay out with a time limit, store the exit code in rc.
# macOS ships no timeout(1), so perl's alarm stands in for it.
run() {
  rc=0
  perl -e 'alarm shift; exec @ARGV' "$TIMEOUT" "$2" -Tdot "$3" > "$1" 2>/dev/null || rc=$?
}

# An engine whose output varies run to run cannot be byte-compared. Force-directed
# engines fail this. Probe several graphs, since some are stable by luck.
probes=$(ls "$GRAPHS"/*.gv | awk 'NR%40==1' | head -6)
deterministic=()
for engine in "${ENGINES[@]}"; do
  stable=yes
  for probe in $probes; do
    run "$work/p1" "./binaries/$BASELINE/bin/$engine" "$probe"
    run "$work/p2" "./binaries/$BASELINE/bin/$engine" "$probe"
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
  unstable=0
  timed_out=0

  for graph in "$GRAPHS"/*.gv; do
    name=$(basename "$graph")

    run "$work/base" "./binaries/$BASELINE/bin/$engine" "$graph"
    baseline_rc=$rc
    if [ $baseline_rc -eq $TIMEOUT_RC ]; then
      timed_out=$((timed_out + 1))
      echo "  TIMEOUT        $BASELINE  $name"
      continue
    fi

    # Engines that pass the probe can still be nondeterministic on some graphs
    # (twopi on newarrows.gv). Only compare graphs the baseline reproduces.
    run "$work/base2" "./binaries/$BASELINE/bin/$engine" "$graph"
    if [ $rc -ne $baseline_rc ] || ! cmp -s "$work/base" "$work/base2"; then
      unstable=$((unstable + 1))
      echo "  UNSTABLE       $BASELINE  $name"
      continue
    fi

    for agent in "${AGENTS[@]}"; do
      run "$work/$agent" "./binaries/$agent/bin/$engine" "$graph"
      agent_rc=$rc

      if [ $agent_rc -eq $TIMEOUT_RC ]; then
        differ=$((differ + 1))
        echo "  TIMEOUT        $agent  $name  (baseline finished)"
      elif [ $baseline_rc -ne 0 ] && [ $agent_rc -ne 0 ]; then
        errored=$((errored + 1))
      elif [ $baseline_rc -ne $agent_rc ]; then
        differ=$((differ + 1))
        echo "  EXIT MISMATCH  $agent  $name  baseline=$baseline_rc agent=$agent_rc"
      elif cmp -s "$work/base" "$work/$agent"; then
        same=$((same + 1))
      else
        differ=$((differ + 1))
        echo "  OUTPUT DIFFERS $agent  $name"
      fi
    done
  done

  printf '%-7s identical %4d   differing %3d   both-errored %3d   unstable %3d   timed-out %3d\n' \
    "$engine" "$same" "$differ" "$errored" "$unstable" "$timed_out"
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
