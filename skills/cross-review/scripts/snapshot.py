#!/usr/bin/env python3
"""Print a repeatable observation of a Git worktree; redirect outside the repo.

Captures HEAD, status, index/unstaged diffs, and nonignored untracked files.
Not atomic; ignored/external files and nested-repository/submodule contents
are outside coverage. Untracked nested repositories receive an unhashed marker.
"""

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args],
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        stdout=subprocess.PIPE,
        check=True,
    ).stdout


def untracked_record(root, name):
    path = os.path.join(os.fsencode(root), name)
    mode = os.lstat(path).st_mode
    if stat.S_ISDIR(mode):
        return {"path": os.fsdecode(name), "type": "nested-repository"}
    digest = hashlib.sha256()
    if stat.S_ISLNK(mode):
        kind = "symlink"
        digest.update(os.readlink(path))
    elif stat.S_ISREG(mode):
        kind = "file"
        with open(path, "rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    else:
        raise OSError("unsupported untracked file type: " + repr(os.fsdecode(name)))
    return {"path": os.fsdecode(name), "type": kind, "sha256": digest.hexdigest()}


def snapshot(repo):
    # Remove exactly Git's final newline; a repository path may contain newlines.
    root = os.fsdecode(git(repo, "rev-parse", "--show-toplevel")[:-1])
    diff_options = ("--binary", "--no-ext-diff", "--no-textconv", "--no-color")
    head = git(root, "rev-parse", "--verify", "HEAD").decode("ascii").strip()
    status = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    index = git(root, "diff", "--cached", *diff_options)
    unstaged = git(root, "diff", *diff_options)
    names = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    return {
        "head": head,
        "status_porcelain_v1_z": os.fsdecode(status),
        "index_diff_sha256": hashlib.sha256(index).hexdigest(),
        "unstaged_diff_sha256": hashlib.sha256(unstaged).hexdigest(),
        "untracked": [untracked_record(root, name) for name in sorted(names.split(b"\0")) if name],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="path to a Git worktree with a HEAD commit")
    args = parser.parse_args()
    try:
        result = snapshot(args.repository)
        print(json.dumps(result, sort_keys=True, ensure_ascii=True, indent=2))
    except (OSError, subprocess.CalledProcessError) as error:
        print("snapshot failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
