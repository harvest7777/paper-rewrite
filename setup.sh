#!/usr/bin/env bash
# Create one pristine graphviz checkout per agent, all pinned to the same commit.
# Each checkout gets its own named branch so agent commits land on a real ref
# instead of a detached HEAD, where they are easy to lose.
#
# Pass --fresh to delete existing sandboxes and re-clone from scratch.
set -e
root="$(dirname "$0")"
cd $root
echo $PWD

SHA=23b06521ab916e7f4f2ae2f9ef8413a8ccc66601
REPO=https://gitlab.com/graphviz/graphviz.git
BRANCH=agent-work

if [ "$1" = "--fresh" ]; then
  echo "Removing existing sandboxes"
  rm -rf sandboxes
fi

mkdir -p sandboxes

for name in baseline claude codex; do
  ogdir=$PWD
  dir="sandboxes/$name"
  mkdir -p $dir
  cd $dir

  if [ -d "graphviz" ]; then
    echo "Directory graphviz exists in $dir, skipping"
  else
    git clone $REPO
    cd graphviz
    git checkout $SHA
    git checkout -b $BRANCH
  fi
  cd $ogdir
done
