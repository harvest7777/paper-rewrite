#!/usr/bin/env bash
# usage: ./run-single.sh test_2241
set -e
if [ -z "$1" ]; then echo "usage: $0 test_2241" >&2; exit 1; fi
cd "$(dirname "$0")"
PREFIX="$PWD/baseline"

cd graphviz/tests
env PATH="$PREFIX/bin:$PATH" \
    C_INCLUDE_PATH="$PREFIX/include" \
    DYLD_LIBRARY_PATH="$PREFIX/lib" \
    LIBRARY_PATH="$PREFIX/lib" \
    PYTHONPATH="$PREFIX/lib/graphviz/python3" \
    TCLLIBPATH="$PREFIX/lib/graphviz/tcl" \
    PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig" \
    graphviz_ROOT="$PREFIX" \
    build_system=cmake \
  ../../.venv/bin/python -m pytest "test_regression.py::$1" -q
