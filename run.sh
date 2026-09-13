#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

BINARIES=(timestamped claude codex)
GRAPHS=(
  graphs/5000-default.gv
  graphs/5000-sparse-deep.gv
  graphs/5000-dense-shallow.gv
)
WARMUP=10
RUNS=10

binary_count=${#BINARIES[@]}
first_real_run=$((WARMUP + 1))
mkdir -p results results/phases

for graph in "${GRAPHS[@]}"; do
  graph_name="$(basename "$graph")"

  for ((rotation = 0; rotation < binary_count; rotation++)); do
    permutation=$((rotation + 1))

    commands=()
    prepares=()
    phase_logs=()
    run_counters=()

    for ((position = 0; position < binary_count; position++)); do
      binary="${BINARIES[(rotation + position) % binary_count]}"
      phase_log="results/phases/$graph_name-$binary-perm$permutation.txt"
      run_counter="$phase_log.count"

      printf 'WARMUP START\n' > "$phase_log"
      echo 0 > "$run_counter"

      phase_logs+=("$phase_log")
      run_counters+=("$run_counter")
      commands+=("env GV_PHASE_TIMING=1 ./binaries/$binary/bin/dot $graph -o /dev/null 2>>$phase_log")
      prepares+=(--prepare "n=\$(( \$(cat '$run_counter') + 1 )); echo \$n > '$run_counter'; if [ \$n -eq $first_real_run ]; then printf 'WARMUP END\nREAL START\n' >> '$phase_log'; fi")
    done

    echo "==> $graph_name  permutation $permutation of $binary_count"
    hyperfine -w "$WARMUP" -r "$RUNS" \
      "${prepares[@]}" \
      --export-json "results/$graph_name-full-perm$permutation.json" \
      "${commands[@]}"

    for i in "${!phase_logs[@]}"; do
      printf 'REAL END\n' >> "${phase_logs[$i]}"
      rm -f "${run_counters[$i]}"
    done
  done
done

echo
echo "Phase timings: results/phases/"
