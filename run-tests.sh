#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PREFIX="${1:-$PWD/baseline}"

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
  ../../.venv/bin/python -m pytest test_regression.py -q -m "not slow" -n 12
