#!/usr/bin/env bash
# Build every sandbox into binaries/<name>/. Same flags for all of them, so the
# source is the only thing that differs.
set -e
cd "$(dirname "$0")"

for dir in sandboxes/*; do
  name="$(basename "$dir")"   # baseline, claude, codex
  src="$dir/graphviz"
  echo "==> $name"

  # have to hard pass a bison path because apples is < 3.0 which graphviz requries
  if cmake -S "$src" -B "builds/$name" \
       -DCMAKE_INSTALL_PREFIX="$PWD/binaries/$name" \
       -DBISON_EXECUTABLE=/opt/homebrew/opt/bison/bin/bison \
       -DWITH_POPPLER=OFF \
       -DWITH_GVEDIT=OFF \
       -DCMAKE_BUILD_TYPE=Release \
     && cmake --build "builds/$name" -j12 \
     && cmake --install "builds/$name"; then
    echo "OK $name"
  else
    echo "FAILED $name"
  fi
done
