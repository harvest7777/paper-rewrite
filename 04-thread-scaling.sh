#!/usr/bin/env bash
# How much of the parallel arms' speedup is actually threads?
# Measures each parallel binary at GV_THREADS=1 and at its own default, against
# the baseline, in one hyperfine invocation per graph per rotation.
#
# Output: results/thread-scaling/<graph>-threads-perm<N>.json
# That subdirectory is NOT matched by make_figures.py's globs, so these runs
# stay out of the paper's pooled end-to-end data.
set -e
cd /Users/ryantran/Developer/projects/paper-rewrite

SIZE="${SIZE:-5000}"
# Result files carry this tag so a re-run lands beside the previous one instead
# of overwriting it. It goes after perm<N>, which keeps the figure script's glob
# matching. Override to name a run: RUN_TAG=threshold-test ./04-thread-scaling.sh
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d-%H%M)}"
GRAPHS=(
  graphs/$SIZE-default.gv
  graphs/$SIZE-sparse-deep.gv
  graphs/$SIZE-dense-shallow.gv
)
for g in "${GRAPHS[@]}"; do
  [ -f "$g" ] || { echo "missing $g -- run gen-graphs.py first" >&2; exit 1; }
done
WARMUP=10
RUNS=10
ROTATIONS=2
OUT=results/thread-scaling
mkdir -p "$OUT"

LABELS=(baseline cp1_t1 cp1_def cp2_t1 cp2_def)
CMDS=(
  "./binaries/timestamped/bin/dot GRAPH -o /dev/null"
  "env GV_THREADS=1 ./binaries/claude_parallel/bin/dot GRAPH -o /dev/null"
  "./binaries/claude_parallel/bin/dot GRAPH -o /dev/null"
  "env GV_THREADS=1 ./binaries/claude_parallel_2/bin/dot GRAPH -o /dev/null"
  "./binaries/claude_parallel_2/bin/dot GRAPH -o /dev/null"
)
n=${#CMDS[@]}

for graph in "${GRAPHS[@]}"; do
  graph_name="$(basename "$graph")"
  for ((rot = 0; rot < ROTATIONS; rot++)); do
    perm=$((rot + 1))
    commands=()
    for ((pos = 0; pos < n; pos++)); do
      idx=$(((rot + pos) % n))
      commands+=("${CMDS[$idx]//GRAPH/$graph}")
    done
    echo "==> $graph_name  rotation $perm/$ROTATIONS"
    hyperfine -w "$WARMUP" -r "$RUNS" \
      --export-json "$OUT/$graph_name-threads-perm$perm-$RUN_TAG.json" \
      "${commands[@]}"
  done
done

echo "done: $OUT"
