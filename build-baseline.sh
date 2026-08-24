#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# have to hard pass a bison path because apples is < 3.0 which graphviz requries
cmake -S graphviz -B build-baseline \
  -DCMAKE_INSTALL_PREFIX="$PWD/baseline" \
  -DBISON_EXECUTABLE=/opt/homebrew/opt/bison/bin/bison \
  -DWITH_POPPLER=OFF \
  -DWITH_GVEDIT=OFF \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build-baseline -j12
cmake --install build-baseline
