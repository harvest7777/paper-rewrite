#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

BINARIES=(
  timestamped
  claude claude_2 claude_parallel claude_parallel_2
  codex codex_2 codex_parallel codex_parallel_2
)
GRAPHS=(
  graphs/5000-default.gv
  graphs/5000-sparse-deep.gv
  graphs/5000-dense-shallow.gv
)
WARMUP=10
RUNS=10
# Result files carry this tag, so a later run with a different binary set lands
# beside the earlier one instead of overwriting it. Override per run:
#   RUN_TAG=parallel-only ./run.sh
RUN_TAG="${RUN_TAG:-$(date +%Y%m%d-%H%M)}"
# One rotation per binary gets expensive once every binary is in the set. Four
# is enough to cancel ordering drift.
MAX_ROTATIONS=4

binary_count=${#BINARIES[@]}
rotations=$((binary_count < MAX_ROTATIONS ? binary_count : MAX_ROTATIONS))
first_real_run=$((WARMUP + 1))
mkdir -p results results/phases

echo "run tag: $RUN_TAG  binaries: $binary_count  rotations: $rotations"

for graph in "${GRAPHS[@]}"; do
  graph_name="$(basename "$graph")"

  for ((rotation = 0; rotation < rotations; rotation++)); do
    permutation=$((rotation + 1))

    commands=()
    prepares=()
    phase_logs=()
    run_counters=()

    for ((position = 0; position < binary_count; position++)); do
      binary="${BINARIES[(rotation + position) % binary_count]}"
      phase_log="results/phases/$graph_name-$binary-perm$permutation-$RUN_TAG.txt"
      run_counter="$phase_log.count"

      printf 'WARMUP START\n' > "$phase_log"
      echo 0 > "$run_counter"

      phase_logs+=("$phase_log")
      run_counters+=("$run_counter")
      commands+=("env GV_PHASE_TIMING=1 ./binaries/$binary/bin/dot $graph -o /dev/null 2>>$phase_log")
      prepares+=(--prepare "n=\$(( \$(cat '$run_counter') + 1 )); echo \$n > '$run_counter'; if [ \$n -eq $first_real_run ]; then printf 'WARMUP END\nREAL START\n' >> '$phase_log'; fi")
    done

    echo "==> $graph_name  permutation $permutation of $rotations"
    hyperfine -w "$WARMUP" -r "$RUNS" \
      "${prepares[@]}" \
      --export-json "results/$graph_name-full-perm$permutation-$RUN_TAG.json" \
      "${commands[@]}"

    for i in "${!phase_logs[@]}"; do
      printf 'REAL END\n' >> "${phase_logs[$i]}"
      rm -f "${run_counters[$i]}"
    done
  done
done

echo
echo "Phase timings: results/phases/"
