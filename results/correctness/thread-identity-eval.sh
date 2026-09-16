#!/usr/bin/env bash
# Byte-identity across thread counts on the EVALUATION graphs -- the inputs big
# enough to actually execute the parallel code paths (unlike tests/graphs).
# bash 3.2 safe: indexed arrays only.
set -u
cd /Users/ryantran/Developer/projects/paper-rewrite
GRAPHS=(graphs/5000-sparse-deep.gv graphs/5000-default.gv graphs/5000-dense-shallow.gv)
BINARIES=(claude_parallel claude_parallel_2)
THREADS=(1 2 4 8 12 default)
REPS=3
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT

total=0; bad=0
for graph in "${GRAPHS[@]}"; do
  name=$(basename "$graph")
  ./binaries/timestamped/bin/dot -Tdot "$graph" > "$work/base" 2>/dev/null
  ./binaries/timestamped/bin/dot -Tdot "$graph" > "$work/base2" 2>/dev/null
  if ! cmp -s "$work/base" "$work/base2"; then
    echo "BASELINE NONDETERMINISTIC on $name -- comparison meaningless"; continue
  fi
  base_md5=$(md5 -q "$work/base")
  for b in "${BINARIES[@]}"; do
    for t in "${THREADS[@]}"; do
      ident=0
      for ((r = 1; r <= REPS; r++)); do
        if [ "$t" = default ]; then
          ./binaries/$b/bin/dot -Tdot "$graph" > "$work/out" 2>/dev/null
        else
          GV_THREADS=$t ./binaries/$b/bin/dot -Tdot "$graph" > "$work/out" 2>/dev/null
        fi
        total=$((total + 1))
        if [ "$(md5 -q "$work/out")" = "$base_md5" ]; then
          ident=$((ident + 1))
        else
          bad=$((bad + 1))
          echo "  DIFFERS $b $name GV_THREADS=$t rep=$r"
        fi
      done
      printf '   %-18s %-16s GV_THREADS=%-8s %d/%d identical\n' "$b" "$name" "$t" "$ident" "$REPS"
    done
  done
done
echo "TOTAL comparisons: $total   differing: $bad"
echo ALL-DONE
