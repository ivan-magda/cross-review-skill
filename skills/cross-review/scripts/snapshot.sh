#!/bin/sh
# Snapshot a Git worktree without changing its working tree, index, or refs:
# new objects and the scratch index go to STORE (outside the repository).
#
#   snapshot.sh REPO STORE                -> prints "HEAD INDEX TREE"
#   snapshot.sh REPO STORE diff A B [...] -> git diff between two saved trees
#
# INDEX is a hash of the staged entries. TREE is the working tree content:
# tracked files as they are on disk plus nonignored untracked files.
# Ignored files and the contents of nested repositories are not covered.
set -eu

repo=$1
mkdir -p "$2/objects"
store=$(cd "$2" && pwd)
cd "$repo"

index=$(git rev-parse --path-format=absolute --git-path index)
GIT_ALTERNATE_OBJECT_DIRECTORIES=$(git rev-parse --path-format=absolute --git-path objects)
GIT_OBJECT_DIRECTORY=$store/objects
GIT_OPTIONAL_LOCKS=0
export GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_OBJECT_DIRECTORY GIT_OPTIONAL_LOCKS

if [ "${3:-}" = diff ]; then
  shift 3
  exec git diff --no-ext-diff --no-textconv "$@"
fi

staged=$(git ls-files -s | git hash-object --stdin)

GIT_INDEX_FILE=$store/index
export GIT_INDEX_FILE
rm -f "$GIT_INDEX_FILE"
if [ -f "$index" ]; then cp -p "$index" "$GIT_INDEX_FILE"; fi

cd "$(git rev-parse --show-toplevel)"
git -c advice.addEmbeddedRepo=false add -A
head=$(git rev-parse --verify -q HEAD || echo none)
echo "$head $staged $(git write-tree)"
