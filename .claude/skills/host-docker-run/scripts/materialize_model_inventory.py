"""Materialize the Docker model inventory for the prepared training path.

Builds `<project_root>/.synaptic/model-inventory/models--<ns>--<repo>/snapshots/
<revision>/` as a tree of REAL files, then verifies it against the invariants the
Host enforces at admission time.

Why a throwaway container does the download
-------------------------------------------
The operator host has NO conda environment and NO venv, by standing user ruling:
everything model-related runs through Docker. So the download runs in a
throwaway `python:3.12-slim` container driven by plain `docker.exe`, never
through `synaptic_host`, and NO downloader is added to the Host. This script is
an operator tool, not a Host feature.

That throwaway container is the ONLY thing on this path with network access.
The prepared TRAINING container is unrelated to it and stays offline: the
prepared composition emits `--network none` and `--pull never` unconditionally
(`synaptic_host/docker_v1/control_private.py:392-393`). Never repurpose this
script to fetch the training image.

No credential is read or forwarded. The target repository is public, so the
container runs with no `-e` flag, and this script reads no credential from the
host environment and passes none into the container.

Why `copyfile` is load-bearing
------------------------------
`huggingface_hub` can lay a snapshot out as symlinks into a `blobs/<sha>` store.
`shutil.copyfile` opens the source for reading, so it DEREFERENCES, which is
what turns those links into the real files the Host demands.

Note the deliberate difference from the sketch in section 4.3 of
`docs/architecture/prepared-path-alpine-diagnostic.md`: that sketch filters with
`if p.is_file() and not p.is_symlink()`. Under the symlink layout that filter
skips every file and produces an EMPTY snapshot, which the Host then rejects as
"model snapshot is empty". This script instead copies every path that resolves
to a regular file, symlink or not, and lets `copyfile` dereference. Same intent,
correct under both layouts.

Why the invariants are restated here instead of imported
--------------------------------------------------------
`synaptic_host.docker_model_inventory` cannot be imported without pulling in
`.docker_staging` and `.local_io_v1.config`. That would couple this operator
tool to the import health of Host modules that are under active edit, so a
broken Host import would break inventory materialization for an unrelated
reason. The invariants are therefore RESTATED below, each against the line it
mirrors. If those lines move, update `_verify_inventory` and say so.

Verified against `synaptic_host/docker_model_inventory.py` at branch
`feat/submodule-cloud-api-v1-host-clean`:

  1. no symlink and no reparse point, in the tree or in the four directories
     above it, and each of those four must satisfy
     `resolve(strict=True) == absolute()`                      `:62-75`, `:145-146`
  2. relative paths NFC-normalized, no backslash                       `:148-149`
  3. no case-colliding paths                                           `:150-153`
  4. regular files only, at least one, at most 20 000            `:159-166`, `:27`
  5. every file hashed                                                  `:91-123`
  6. repo id is exactly two parts matching `[A-Za-z0-9][A-Za-z0-9._-]{0,95}`,
     neither ending in `.` or `-`, neither containing `..` or `--`       `:78-88`
  7. revision is 40 lowercase hex                                  `:25`, `:223`

Usage (Windows Host Python; see the skill's SKILL.md):

    python.exe .skills\\host-docker-run\\scripts\\materialize_model_inventory.py
    python.exe ...\\materialize_model_inventory.py --verify-only

Exit code is 0 only when every check passed. Any failure names the check.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path

# Mirrors synaptic_host/docker_model_inventory.py:25-27.
_REVISION = re.compile(r"[0-9a-f]{40}")
_REPOSITORY_COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}")
_MAX_INVENTORY_FILES = 20_000

# The committed smoke pins both of these (training/smokes/docker-sft.json:5-7).
_DEFAULT_REPO = "HuggingFaceTB/SmolLM2-135M-Instruct"
_DEFAULT_REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"

# Measured on this host by PREPARE; overridable because it is host-specific.
_DEFAULT_DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"

# Pinned by tag. The resolved digest is printed after the pull so the run is
# auditable. Already present locally per PREPARE's image list.
_DEFAULT_IMAGE = "python:3.12-slim"

# This script lives at <project_root>/.skills/host-docker-run/scripts/<name>.py,
# so the project root is three parents up from the script's directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CheckFailure(Exception):
    """A named invariant failed. The name is the first argument."""


def _fail(check: str, detail: str) -> None:
    raise CheckFailure(f"{check}: {detail}")


def _repository_components(model_ref: str) -> tuple[str, str]:
    """Mirror of docker_model_inventory.py:78-88."""
    parts = tuple(model_ref.split("/"))
    if (
        len(parts) != 2
        or any(_REPOSITORY_COMPONENT.fullmatch(item) is None for item in parts)
        or any(
            item.endswith((".", "-")) or ".." in item or "--" in item
            for item in parts
        )
    ):
        _fail("I6-repo-id", f"{model_ref!r} is not an exact Hugging Face repository id")
    return parts[0], parts[1]


def _is_reparse(info: os.stat_result) -> bool:
    """Mirror of docker_model_inventory.py:30-34.

    `st_file_attributes` exists only on Windows, which is where this script is
    meant to run. On any other platform this degrades to False and only the
    symlink check applies; `_verify_inventory` says so in its output.
    """
    return bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _require_direct_directory(path: Path, label: str) -> None:
    """Mirror of docker_model_inventory.py:62-75 (`_direct_directory`).

    `resolve(strict=True)` walks the whole ancestor chain, so this also rejects
    a reparse point ABOVE the inventory, not just on the directory itself.
    """
    try:
        info = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as error:
        _fail("I1-no-redirect", f"{label} is unavailable ({path}): {error}")
    if path.is_symlink() or _is_reparse(info):
        _fail("I1-no-redirect", f"{label} is a symlink or reparse point ({path})")
    if not stat.S_ISDIR(info.st_mode):
        _fail("I1-no-redirect", f"{label} is not a directory ({path})")
    if resolved != path.absolute():
        _fail(
            "I1-no-redirect",
            f"{label} resolves elsewhere: {path.absolute()} -> {resolved}",
        )


def _container_program(repo: str, revision: str) -> str:
    """The Python program the throwaway container runs.

    Returned as source text so the caller can print it verbatim before running
    it. Nothing here touches a credential.
    """
    return f'''
import pathlib, shutil, sys
from huggingface_hub import snapshot_download

REPO = {repo!r}
REV = {revision!r}

tmp = pathlib.Path(snapshot_download(REPO, revision=REV, local_dir="/tmp/snap"))
dest = pathlib.Path("/out") / ("models--" + REPO.replace("/", "--")) / "snapshots" / REV
dest.mkdir(parents=True, exist_ok=True)

copied = 0
for source in sorted(tmp.rglob("*")):
    if not source.is_file():
        continue
    relative = source.relative_to(tmp)
    if relative.parts and relative.parts[0] == ".cache":
        continue
    target = dest / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    copied += 1

print("copied %d file(s) into %s" % (copied, dest), flush=True)
if copied == 0:
    sys.exit("no files were copied; the snapshot layout was not understood")
'''


def _run(
    argv: list[str], *,
    stdin_text: str | None = None,
    stdin_bytes: bytes | None = None,
) -> subprocess.CompletedProcess:
    """Run a command, optionally feeding it stdin.

    `stdin_bytes` sends the payload BYTE-EXACT. Use it whenever the child
    parses what it reads, because `text=True` translates newlines on the way
    in; see the B-3 note at the container call site. stdout and stderr are
    decoded either way, so callers always get str.
    """
    print(f"    $ {subprocess.list2cmdline(argv)}", flush=True)
    if stdin_bytes is not None:
        completed = subprocess.run(
            argv,
            input=stdin_bytes,
            capture_output=True,
            check=False,
        )
        return subprocess.CompletedProcess(
            completed.args,
            completed.returncode,
            completed.stdout.decode("utf-8", "replace"),
            completed.stderr.decode("utf-8", "replace"),
        )
    return subprocess.run(
        argv,
        input=stdin_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _materialize(
    *, docker: str, image: str, output_root: Path, repo: str, revision: str
) -> None:
    """Pull the pinned image, print its digest, then run the throwaway container."""

    print(f"[1/3] pulling {image}")
    pulled = _run([docker, "image", "pull", image])
    if pulled.returncode != 0:
        _fail("M1-image-pull", f"{image} could not be pulled: {pulled.stderr.strip()}")

    inspected = _run(
        [docker, "image", "inspect", "--format", "{{index .RepoDigests 0}}", image]
    )
    if inspected.returncode == 0 and inspected.stdout.strip():
        print(f"    resolved image digest: {inspected.stdout.strip()}")
    else:
        # A locally-built or never-pushed image has no RepoDigest. Not fatal,
        # but the run is then less auditable, so say so rather than hide it.
        print("    resolved image digest: UNAVAILABLE (image has no repo digest)")

    program = _container_program(repo, revision)
    print("[2/3] container program (verbatim):")
    for line in program.strip().splitlines():
        print(f"    | {line}")

    # The program is base64-encoded onto the container's stdin so no quoting of
    # Python source has to survive the Windows command line. `-i` keeps stdin
    # open for `sh -s`.
    encoded = base64.b64encode(program.encode("utf-8")).decode("ascii")
    shell = (
        "set -eu\n"
        f"printf %s {encoded} | base64 -d > /tmp/materialize.py\n"
        "pip install --no-cache-dir --quiet huggingface_hub\n"
        "python3 /tmp/materialize.py\n"
    )

    # `-v` is correct for THIS throwaway container. The prepared path uses
    # `--mount type=bind` instead, deliberately, so that a missing source fails
    # hard rather than being created silently; that distinction belongs to the
    # Host and must not be copied from here. The output directory is created
    # below before the run, so `-v` never auto-creates anything either.
    argv = [
        docker, "run", "--rm", "-i",
        "-v", f"{output_root}:/out",
        image, "sh", "-s",
    ]
    # Wording note: the PACT pre-commit hook (git_commit_check.py:110-134) is a
    # blunt secret-in-log guard. It rejects any staged .py whose file content
    # matches a print call followed on the SAME line by one of a few
    # credential-ish words, case-insensitively. Keep such words out of the
    # output lines below. This script forwards no credential at all, so the
    # wording costs nothing.
    print("[3/3] running the throwaway container (no -e flag, no credentials forwarded)")

    # B-3: the container shell must receive LF line endings and nothing else.
    # `subprocess.run(..., text=True)` wraps the child's stdin in a
    # TextIOWrapper whose default newline handling rewrites "\n" to os.linesep,
    # so on a Windows host every line arrived as CRLF. dash inside
    # python:3.12-slim then read `set -eu\r` and died with
    # "sh: 1: set: Illegal option -", before any of the real work. Encoding
    # here and sending bytes bypasses that translation on every platform. The
    # guard makes the invariant explicit rather than implicit in the encoding.
    payload = shell.encode("utf-8")
    if b"\r" in payload:
        _fail("M3-stdin-newlines", "the container shell program contains a CR byte")
    completed = _run(argv, stdin_bytes=payload)
    if completed.stdout:
        for line in completed.stdout.strip().splitlines():
            print(f"    {line}")
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "no stderr"
        _fail("M2-container", f"materialization container exited {completed.returncode}: {detail}")


def _verify_inventory(
    *, output_root: Path, repo: str, revision: str
) -> tuple[int, int, str]:
    """Assert the Host's invariants over the materialized tree.

    Returns (file_count, total_bytes, fingerprint) where the fingerprint is a
    SHA-256 over the sorted `<sha256>  <relative>` listing, so two
    materializations can be compared with one value.
    """
    namespace, repository = _repository_components(repo)
    if _REVISION.fullmatch(revision) is None:
        _fail("I7-revision", f"{revision!r} is not 40 lowercase hex characters")

    model_directory = output_root / f"models--{namespace}--{repository}"
    snapshots_directory = model_directory / "snapshots"
    snapshot = snapshots_directory / revision

    # The Host checks exactly these four, in this order (:249-256).
    for path, label in (
        (output_root, "model inventory root"),
        (model_directory, "model repository cache"),
        (snapshots_directory, "model snapshots directory"),
        (snapshot, "model snapshot"),
    ):
        _require_direct_directory(path, label)

    if not hasattr(os.stat_result, "st_file_attributes") and os.name != "nt":
        print(
            "    NOTE: not running on Windows, so the reparse-point half of "
            "check I1 cannot be observed here; only symlinks were checked."
        )

    files: list[tuple[str, Path]] = []
    folded_nodes: dict[str, str] = {}
    pending = [snapshot]
    while pending:
        directory = pending.pop()
        try:
            entries = tuple(os.scandir(directory))
        except OSError as error:
            _fail("I1-no-redirect", f"model snapshot is unavailable ({directory}): {error}")
        for entry in entries:
            path = Path(entry.path)
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as error:
                _fail("I1-no-redirect", f"model snapshot is unavailable ({path}): {error}")
            if entry.is_symlink() or _is_reparse(info):
                _fail("I1-no-redirect", f"model snapshot contains a redirect ({path})")

            relative = path.relative_to(snapshot).as_posix()
            if unicodedata.normalize("NFC", relative) != relative or "\\" in relative:
                _fail("I2-canonical-path", f"noncanonical relative path {relative!r}")

            folded = relative.casefold()
            previous = folded_nodes.setdefault(folded, relative)
            if previous != relative:
                _fail(
                    "I3-no-case-collision",
                    f"{relative!r} collides with {previous!r} when case-folded",
                )

            if stat.S_ISDIR(info.st_mode):
                _require_direct_directory(path, "model snapshot directory")
                pending.append(path)
            elif stat.S_ISREG(info.st_mode):
                files.append((relative, path))
            else:
                _fail("I4-regular-files-only", f"special file {relative!r}")

            if len(files) > _MAX_INVENTORY_FILES:
                _fail(
                    "I4-regular-files-only",
                    f"more than {_MAX_INVENTORY_FILES} files",
                )

    if not files:
        _fail("I4-regular-files-only", "model snapshot is empty")

    listing: list[str] = []
    total_bytes = 0
    for relative, source in sorted(files, key=lambda item: item[0]):
        digest = hashlib.sha256()
        try:
            with open(source, "rb") as handle:
                while True:
                    chunk = handle.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
        except OSError as error:
            _fail("I5-hashable", f"{relative!r} could not be read: {error}")
        size = source.stat().st_size
        total_bytes += size
        listing.append(f"{digest.hexdigest()}  {relative}")

    fingerprint = hashlib.sha256(
        ("\n".join(listing) + "\n").encode("utf-8")
    ).hexdigest()

    print(f"    snapshot: {snapshot}")
    for line in listing:
        print(f"    {line}")
    return len(files), total_bytes, fingerprint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize and verify the Docker model inventory in a throwaway "
            "container. Runs no training and touches no Host state."
        )
    )
    parser.add_argument("--project-root", default=str(_PROJECT_ROOT))
    parser.add_argument("--repo", default=_DEFAULT_REPO)
    parser.add_argument("--revision", default=_DEFAULT_REVISION)
    parser.add_argument("--docker", default=_DEFAULT_DOCKER)
    parser.add_argument("--image", default=_DEFAULT_IMAGE)
    parser.add_argument(
        "--verify-only", action="store_true",
        help="verify an already-materialized tree; start no container.",
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve(strict=False)
    output_root = project_root / ".synaptic" / "model-inventory"

    print(f"project root     : {project_root}")
    print(f"inventory root   : {output_root}")
    print(f"model            : {args.repo} @ {args.revision}")
    print()

    try:
        # Validate the identifiers BEFORE spending a pull on them.
        _repository_components(args.repo)
        if _REVISION.fullmatch(args.revision) is None:
            _fail("I7-revision", f"{args.revision!r} is not 40 lowercase hex characters")

        if not args.verify_only:
            # Idempotent: re-running over an existing tree re-copies the same
            # bytes to the same paths.
            output_root.mkdir(parents=True, exist_ok=True)
            _materialize(
                docker=args.docker,
                image=args.image,
                output_root=output_root,
                repo=args.repo,
                revision=args.revision,
            )
            print()

        print("verifying the inventory contract")
        count, total_bytes, fingerprint = _verify_inventory(
            output_root=output_root, repo=args.repo, revision=args.revision
        )
    except CheckFailure as failure:
        print(f"\nFAILED {failure}", file=sys.stderr)
        return 1

    print()
    print(f"OK  {count} file(s), {total_bytes} byte(s)")
    print(f"OK  inventory fingerprint sha256:{fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
