#!/usr/bin/env python3
"""G3: every locked file's recorded digest equals the file at the pinned engine sha.

Gate G3 of docs/architecture/prepared-path-alpine-diagnostic.md 29.12:
"B-19 cannot recur: every locked file's recorded digest equals the file at the
pinned engine sha."

The instrument reads BLOBS, not worktree files.
------------------------------------------------
`modal-runtime-v1.lock.json` records a sha256 per locked member. The engine
computes those digests from git content. On a Windows checkout the worktree
bytes are not the git content: `.gitattributes text=auto` translates LF to CRLF
on checkout, so a member whose recorded digest is correct still reads as a
mismatch when the script hashes the file on disk. A worktree-hashing script
therefore reports a defect that does not exist and hides the count that does.

This script hashes `git cat-file blob <sha>:<path>` for every member and for the
lock itself, so the reading is independent of the checkout platform, of the
worktree state, and of whether the submodule is even checked out at the pin.

Self-check (the reason the script prints both columns)
------------------------------------------------------
At engine ce539b70, a CORRECT G3 reports exactly two blob mismatches:
`modal_remote` and `sft_runtime`. That is blocker B-19.

    blob mismatches = 2   -> B-19 open, as recorded. Correct instrument.
    blob mismatches = 0   -> B-19 remediated: the lock was regenerated at the
                             pin and the Host gitlink moved to it. Gate G3 passes.
    blob mismatches = 3   -> the script read the WORKTREE, not the blob. The
                             third name is `dependency_lock` and its only
                             difference is line endings. Fix the instrument;
                             do not file a third defect.

`--expect N` turns that reading into an exit code so the gate can be automated.

Usage
-----
    python3 g3_engine_lock_digests.py                 # report only
    python3 g3_engine_lock_digests.py --expect 2      # B-19 open, as at ce539b70
    python3 g3_engine_lock_digests.py --expect 0      # B-19 remediated

No credentials, no network, no Modal call. Read-only: the script never writes to
the engine tree and never checks anything out.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

LOCK_RELATIVE_PATH = "tuner/execution/providers/modal/modal-runtime-v1.lock.json"

# The Windows git binary, used when the engine tree sits on a DrvFs mount. A
# Windows git.exe rejects a POSIX path given to -C with a fatal exit 128, so
# every invocation below sets `cwd` and omits -C entirely.
WINDOWS_GIT = Path("/mnt/c/Program Files/Git/cmd/git.exe")


def emit(line: str) -> None:
    print(line)


class GitError(RuntimeError):
    pass


def resolve_git_binary(engine_root: Path, override: str | None) -> str:
    if override:
        return override
    parts = engine_root.resolve().parts
    on_drvfs = len(parts) > 2 and parts[1] == "mnt" and len(parts[2]) == 1
    if on_drvfs and WINDOWS_GIT.is_file():
        return str(WINDOWS_GIT)
    return "git"


def run_git(git: str, engine_root: Path, args: list[str]) -> bytes:
    completed = subprocess.run(
        [git, "-c", "safe.directory=*", *args],
        cwd=str(engine_root),
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(f"git {' '.join(args)} exited {completed.returncode}: {detail}")
    return completed.stdout


def read_blob(git: str, engine_root: Path, sha: str, path: str) -> bytes:
    return run_git(git, engine_root, ["cat-file", "blob", f"{sha}:{path}"])


def pinned_sha_from_superproject(engine_root: Path, git: str) -> str:
    """Read the gitlink the superproject records for the engine submodule.

    The gitlink is the commit the Host is pinned to. It is deliberately read
    from the SUPERPROJECT tree rather than from the submodule's own HEAD:
    a checked-out submodule can sit on any commit, and G3 must measure the pin.
    """
    superproject = engine_root.resolve().parent
    name = engine_root.resolve().name
    out = run_git(git, superproject, ["ls-tree", "HEAD", "--", name]).decode()
    for line in out.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[0] == "160000" and fields[1] == "commit":
            return fields[2]
    raise GitError(f"no gitlink for {name!r} in the superproject HEAD tree")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--engine-root",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "synaptic-tuner",
        help="engine submodule working tree (default: the sibling synaptic-tuner)",
    )
    parser.add_argument(
        "--sha",
        default=None,
        help="engine commit to measure (default: the superproject gitlink at HEAD)",
    )
    parser.add_argument("--git", default=None, help="git binary to use")
    parser.add_argument(
        "--expect",
        type=int,
        default=None,
        help="required number of BLOB mismatches; exit 1 if the count differs",
    )
    parser.add_argument(
        "--no-worktree-column",
        action="store_true",
        help="skip the worktree diagnostic (blob column alone decides the gate)",
    )
    args = parser.parse_args(argv)

    engine_root: Path = args.engine_root
    if not engine_root.is_dir():
        emit(f"FAIL engine root not a directory: {engine_root}")
        return 2

    git = resolve_git_binary(engine_root, args.git)

    try:
        sha = args.sha or pinned_sha_from_superproject(engine_root, git)
        lock_bytes = read_blob(git, engine_root, sha, LOCK_RELATIVE_PATH)
    except GitError as error:
        emit(f"FAIL {error}")
        return 2

    document = json.loads(lock_bytes)
    members = document["locked_files"]

    emit(f"engine root   : {engine_root}")
    emit(f"git binary    : {git}")
    emit(f"measured sha  : {sha}")
    emit(f"lock          : {LOCK_RELATIVE_PATH}")
    emit(f"sdk_version   : {document.get('sdk_version')!r}")
    emit(f"locked members: {len(members)}")
    emit("")

    blob_mismatches: list[str] = []
    worktree_mismatches: list[str] = []

    for name in sorted(members):
        member = members[name]
        relative = member["path"]
        recorded = member["sha256"]

        try:
            blob_digest = hashlib.sha256(
                read_blob(git, engine_root, sha, relative)
            ).hexdigest()
        except GitError as error:
            blob_digest = "UNREADABLE"
            emit(f"  note: {error}")

        blob_ok = blob_digest == recorded
        if not blob_ok:
            blob_mismatches.append(name)

        if args.no_worktree_column:
            emit(f"{name:22s} blob={'OK      ' if blob_ok else 'MISMATCH'}  {relative}")
        else:
            on_disk = engine_root / relative
            if on_disk.is_file():
                worktree_digest = hashlib.sha256(on_disk.read_bytes()).hexdigest()
            else:
                worktree_digest = "ABSENT"
            worktree_ok = worktree_digest == recorded
            if not worktree_ok:
                worktree_mismatches.append(name)
            emit(
                f"{name:22s} blob={'OK      ' if blob_ok else 'MISMATCH'}"
                f"  worktree={'OK      ' if worktree_ok else 'MISMATCH'}  {relative}"
            )
            if blob_ok and not worktree_ok:
                emit(
                    "                       ^ worktree-only difference: line-ending"
                    " translation on checkout, not a defect"
                )
        if not blob_ok:
            emit(f"                       recorded={recorded}")
            emit(f"                       measured={blob_digest}")

    emit("")
    emit(f"BLOB mismatches     = {len(blob_mismatches)}  {sorted(blob_mismatches)}")
    if not args.no_worktree_column:
        emit(
            f"WORKTREE mismatches = {len(worktree_mismatches)}"
            f"  {sorted(worktree_mismatches)}   (diagnostic only)"
        )
        extra = sorted(set(worktree_mismatches) - set(blob_mismatches))
        if extra:
            emit(
                f"                      {extra} differ ONLY on disk; a worktree-hashing"
                " script would report them as defects"
            )
    emit("")
    emit("G3 verdict is the BLOB column.")

    if args.expect is None:
        emit("no --expect given: reporting only, no gate applied")
        return 0

    if len(blob_mismatches) == args.expect:
        emit(f"PASS blob mismatches == {args.expect} as required")
        return 0

    emit(f"FAIL blob mismatches {len(blob_mismatches)} != required {args.expect}")
    if len(blob_mismatches) == 3 and args.expect == 2:
        emit(
            "     three mismatches is the worktree-hashing signature; check that this"
            " run really read blobs"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
