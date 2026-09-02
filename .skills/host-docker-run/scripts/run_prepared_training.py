"""Drive the prepared-path Docker training run on the Windows host.

Runs the preconditions and the early assertions from
`docs/architecture/prepared-path-alpine-diagnostic.md` sections 9.1 and 10.1,
probes the mount source, then re-issues ONE unchanged command until the durable
phase stops advancing.

Order: `P1..P7` -> `B1` -> `P8` -> `A1` -> `A2` -> `A3` -> `A4` (section 18.11).
`P8` proves the container user can write the real stage parent; it is placed
after `B1` because it needs a bind already proven to resolve, and before the
assertions because a non-writable stage makes the rest of the run moot. Note
that `P8` CREATES `.synaptic\\state\\docker\\stages` if it is absent, so a
`--probe-only` pass is no longer free of durable state.

The command, and why it never varies
------------------------------------
    python.exe -m synaptic_host training run \\
        --provider docker \\
        --config project://training/smokes/docker-sft.json \\
        --destination local-default

Exactly eight argv tokens, which is what the fixed-arity parser demands
(`synaptic_host/cli.py:494`, option loop `:500-509`). There is NO separate
reconcile verb: the CLI has one command, each invocation performs exactly one
cut dispatched on the durable phase (`docker_training.py:920-953`), and
re-running it IS how an operator reconciles.

Section 9.3 is explicit that this takes AT LEAST THREE post-submit cuts, not
two: an observe cut which may repeat while the container runs, then a verify cut
that writes ARTIFACTS_VERIFIED and publishes nothing, then a publish cut that is
always a separate call. Reading `published == False` after one reconcile is the
CORRECT behaviour of a healthy system (risk R7). This driver therefore loops
until the phase stops advancing and logs the verify and publish cuts separately,
rather than counting to two.

No endpoint flag reaches the Host
---------------------------------
The npipe endpoint is not an operator choice. The Host probes
`docker context inspect desktop-linux` and then re-asserts the descriptor equals
`npipe:////./pipe/dockerDesktopLinuxEngine` exactly
(`docker_prepared_composition.py:140-155`). `--endpoint` here is used ONLY for
this driver's own read-only `docker.exe` probes.

Where the phase comes from
--------------------------
The command result on stdout is `synaptic-training-run-command-result/v2` and
carries status / code / run_id / plan_fingerprint / effect_id / provider_job_ref
/ submitted_at (`cli.py:307-322`). It does NOT carry the durable phase. The
phase lives in `docker_run_mutations.phase` in
`<project_root>/.synaptic/state/training.sqlite3`
(`sqlite_repository.py:272-285`, path forced at `:107-111`); the publication row
lives in `publication_records_v1` in the SAME file
(`publication_store.py:109-118`, `:164-178`). This driver opens that file
READ-ONLY and never writes to it.

Reading a failure
-----------------
On any non-advancing failure the driver surfaces `trainer.stderr.log` FIRST.
Blocker B-2 (section 7) fails inside the container at artifact assembly, before
`final_model.tar` exists, and the Host then sees only a non-zero trainer exit.
Without that log the defect is indistinguishable from a GPU, mount, or image
problem, and the only stderr line may be the opaque `OFFLINE_SFT_WORKER_REJECTED`
with exit 2.

Usage (Windows Host Python; see the skill's SKILL.md):

    python.exe .skills\\host-docker-run\\scripts\\run_prepared_training.py --probe-only
    python.exe .skills\\host-docker-run\\scripts\\run_prepared_training.py

Exit code is 0 only when every check passed and the run reached a terminal
phase without failing. Any failure names the failing check.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

_DEFAULT_DOCKER = r"C:\Program Files\Docker\Docker\resources\bin\docker.exe"
_DEFAULT_ENDPOINT = "npipe:////./pipe/dockerDesktopLinuxEngine"
_DEFAULT_CONTEXT = "desktop-linux"
_DEFAULT_CONFIG_REF = "project://training/smokes/docker-sft.json"
_DEFAULT_DESTINATION = "local-default"
_DEFAULT_PROVIDER = "docker"

# A small image for the bind probe. Pinned by tag and never pulled: the probe
# must fail loudly if it is absent rather than silently downloading.
_PROBE_IMAGE = "python:3.12-slim"

# The prepared composition sets this as the container entrypoint (architecture
# section 17.2); in the package the token is
# `synaptic_host.docker_v1.control_private._CONTAINER_ENTRYPOINT_V1`. This driver
# is a checked-in script OUTSIDE the package, so it restates the token rather
# than importing it, and the two must not drift.
#
# Why any of this is needed: the committed image's ENTRYPOINT is
# `/usr/local/bin/entrypoint.sh`, which ends in `exec /usr/bin/supervisord` and
# never runs `exec "$@"`, so an appended command is DISCARDED and the container
# starts jupyter, ollama and sshd instead (blocker B-4, section 17.1). `env`
# with no NAME=VALUE operands is the POSIX identity: it execs its argument
# vector unchanged. Without it these three probes would each start supervisord
# and time out, reporting T1-timeout for assertions whose whole purpose is to
# name a true cause.
_CONTAINER_ENTRYPOINT = "env"

# Conservative loop bounds. Both are arguments; these are the defaults.
_DEFAULT_MAX_CUTS = 40
_DEFAULT_MAX_SECONDS = 3600
_DEFAULT_CUT_INTERVAL_SECONDS = 20

# Durable ordering used only to tell "advanced" from "regressed"
# (`docker_execution_state.py:314-324`). PROCESS_FAILED and RECONCILE_REQUIRED
# sit outside the ladder and are handled explicitly.
_PHASE_RANK = {
    "CREATE_ADMITTED": 1,
    "CREATE_ATTEMPTED": 2,
    "CREATED": 3,
    "START_ADMITTED": 4,
    "START_ATTEMPTED": 5,
    "SUBMITTED": 6,
    "PROCESS_SUCCEEDED": 7,
    "ARTIFACTS_VERIFIED": 8,
}

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CheckFailure(Exception):
    """A named check failed. The name is the first argument."""


def _fail(check: str, detail: str) -> None:
    raise CheckFailure(f"{check}: {detail}")


def _run(argv: list[str], *, timeout: int = 300) -> subprocess.CompletedProcess:
    print(f"    $ {subprocess.list2cmdline(argv)}", flush=True)
    return subprocess.run(
        argv, text=True, capture_output=True, check=False, timeout=timeout
    )


# --------------------------------------------------------------------------
# Preconditions (section 9.1)
# --------------------------------------------------------------------------

def _check_p1_single_docker(docker: str) -> None:
    """Exactly one `docker.exe` on PATH.

    Mirrors `docker_prepared_composition.py:112-131`. That code counts
    CANDIDATES, not unique resolved paths, so two PATH entries that resolve to
    the same binary still fail. This check counts the same way. WSL carries two
    other docker binaries and they must not be the ones found.
    """
    path_value = os.environ.get("PATH")
    if not isinstance(path_value, str):
        _fail("P1-single-docker", "PATH is unset")
    candidates = [
        str((Path(directory) / "docker.exe").resolve(strict=True))
        for directory in path_value.split(os.pathsep)
        if directory and (Path(directory) / "docker.exe").is_file()
    ]
    if len(candidates) != 1:
        _fail(
            "P1-single-docker",
            f"expected exactly 1 docker.exe on PATH, found {len(candidates)}: {candidates}",
        )
    found = candidates[0]
    if Path(found).name.casefold() != "docker.exe" or not Path(found).is_absolute():
        _fail("P1-single-docker", f"{found} is not an absolute docker.exe")
    if Path(found).resolve() != Path(docker).resolve():
        print(
            f"    NOTE: PATH resolves to {found}, driver probes use {docker}. "
            "The Host will use the PATH one."
        )
    print(f"    PASS P1-single-docker: {found}")


def _check_p2_endpoint(docker: str, context_name: str, expected: str) -> None:
    """The desktop-linux context points at the expected npipe endpoint."""
    completed = _run(
        [docker, "context", "inspect", context_name, "--format", "{{.Endpoints.docker.Host}}"]
    )
    if completed.returncode != 0:
        _fail(
            "P2-endpoint",
            f"docker context inspect {context_name} failed: {completed.stderr.strip()}",
        )
    actual = completed.stdout.strip()
    if actual != expected:
        _fail("P2-endpoint", f"expected {expected!r}, got {actual!r}")
    print(f"    PASS P2-endpoint: {actual}")


def _check_p3_drive_letter_root(project_root: Path) -> None:
    """The project root must be a Windows drive path, not a UNC.

    `local_io_v1/config.py:113-119` refuses a root that opens on two
    separators, and `docker_v1/prepared.py:46-47` raises unless the stage path
    has a Windows drive. Both must hold, so a distro-ext4 root cannot work.
    """
    drive = project_root.drive
    if len(drive) != 2 or drive[1] != ":":
        _fail(
            "P3-drive-letter-root",
            f"project root {project_root} has drive {drive!r}, not a drive letter",
        )
    print(f"    PASS P3-drive-letter-root: {drive}")


def _load_profile(project_root: Path) -> dict:
    path = project_root / "training" / "providers" / "docker.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        _fail("P4-profile", f"{path} could not be read: {error}")


def _check_p5_drive_mount_root(profile: dict) -> tuple[str, str]:
    """The committed profile must carry `docker_host.drive_mount_root` (B-1).

    Without it the drive mount prefix is a code literal and the emitted bind
    source cannot be steered from configuration at all. The committed pair is
    `Ubuntu-22.04` with `/mnt`, which renders
    `\\\\wsl.localhost\\Ubuntu-22.04\\mnt\\f\\...`. The `docker-desktop`
    candidate is refuted by measurement: the engine exposes no mount service for
    that distro and fails with `stat
    /run/guest-services/distro-services/docker-desktop.sock: no such file or
    directory`. The composition uses `--mount type=bind`, which fails hard on a
    missing source (`control_private.py:404-407`), so a wrong pair fails the run
    rather than silently binding the wrong directory.

    This check reads both values from the profile and asserts only that they are
    present and non-empty; it never pins a particular pair, so a re-probe that
    changes the committed value needs no change here.
    """
    docker_host = profile.get("docker_host")
    if not isinstance(docker_host, dict):
        _fail("P5-drive-mount-root", "profile has no docker_host section")
    distro = docker_host.get("wsl_distro")
    root = docker_host.get("drive_mount_root")
    if not isinstance(distro, str) or not distro:
        _fail("P5-drive-mount-root", "docker_host.wsl_distro is missing")
    if not isinstance(root, str) or not root:
        _fail(
            "P5-drive-mount-root",
            "docker_host.drive_mount_root is missing from the committed profile; "
            "blocker B-1 is unfixed (task #89). Re-run with --probe-only until it lands.",
        )
    if not root.startswith("/") or root.endswith("/"):
        _fail(
            "P5-drive-mount-root",
            f"drive_mount_root {root!r} must be absolute POSIX with no trailing slash",
        )
    print(f"    PASS P5-drive-mount-root: distro={distro} root={root}")
    return distro, root


def _check_p6_config_is_committed(project_root: Path, config_ref: str) -> None:
    """Warn if the working-tree config differs from the committed blob.

    The config is read as a committed git blob at the locked project commit
    (`docker_training.py:589-593`), NOT from the working tree, so an edit that
    is not committed cannot take effect. Using the existing smoke unchanged
    avoids this entirely; this check exists so a stray edit is noticed.
    """
    prefix = "project://training/"
    relative = "training/" + config_ref[len(prefix):]
    completed = _run(["git.exe", "-C", str(project_root), "status", "--porcelain", "--", relative])
    if completed.returncode != 0:
        print(f"    SKIP P6-config-committed: git.exe unavailable ({completed.stderr.strip()})")
        return
    if completed.stdout.strip():
        _fail(
            "P6-config-committed",
            f"{relative} has uncommitted changes; the run would read the committed "
            f"blob instead: {completed.stdout.strip()!r}",
        )
    print(f"    PASS P6-config-committed: {relative} matches the committed blob")


def _git(project_root: Path, *arguments: str) -> subprocess.CompletedProcess:
    """One read-only git.exe call in the project checkout.

    Same resolution P6 uses: the bare name `git.exe`, found on the Windows PATH.
    This driver deliberately adds no second discovery path.
    """
    return _run(["git.exe", "-C", str(project_root), *arguments])


def _check_p7_branch_is_publishable(project_root: Path) -> None:
    """The project checkout must be on a branch that tracks origin at HEAD.

    Blocker B-6, measured on run 2: the released checkout was built by checking
    out the target sha, which DETACHES HEAD. Publication closure resolves the
    source through `_verified_remote_source` (`docker_training.py:242`, raising
    at `:212`), which requires an exact upstream branch, so the run died at cut 1
    reporting only RESOLUTION_UNAVAILABLE -- a status that names the symptom and
    not the cause, and cost a full diagnostic cycle to attribute.

    The three conditions below are exactly what that guard needs, checked here
    where the failure can still say what to do about it. The ENGINE submodule may
    stay detached: `GitCliLocalSourceInspector` substitutes its branch from the
    committed `.gitmodules`. The superproject may not.

    This is the only precondition that touches the network, via `ls-remote`.
    """
    head = _git(project_root, "rev-parse", "HEAD")
    if head.returncode != 0:
        _fail(
            "P7-git-unavailable",
            f"git.exe could not read HEAD in {project_root}: {head.stderr.strip()}",
        )
    head_sha = head.stdout.strip()

    branch = _git(project_root, "branch", "--show-current")
    if branch.returncode != 0:
        _fail(
            "P7-git-unavailable",
            f"git.exe could not read the current branch: {branch.stderr.strip()}",
        )
    current = branch.stdout.strip()
    if not current:
        candidates = _git(
            project_root, "branch", "--points-at", "HEAD", "--format=%(refname:short)"
        )
        names = [n for n in candidates.stdout.split() if n] if candidates.returncode == 0 else []
        remedy = (
            f"git checkout {names[0]}"
            if names
            else f"git checkout -b <branch> {head_sha[:12]}  # no local branch is at HEAD"
        )
        _fail(
            "P7-detached-head",
            f"HEAD is detached at {head_sha[:12]}; publication closure needs a branch. "
            f"Remedy: {remedy}",
        )

    # The exact read the engine inspector performs (`source_bundle.py:668-675`),
    # deliberately the same command rather than an equivalent: it consults only
    # the LOCAL config, so an upstream set in a global or included config would
    # satisfy `for-each-ref` while still failing the Host.
    remote = _git(
        project_root, "config", "--local", "--get", f"branch.{current}.remote"
    )
    tracked = remote.stdout.strip() if remote.returncode == 0 else ""
    if tracked != "origin":
        detail = f"tracks remote {tracked!r}" if tracked else "has no upstream"
        _fail(
            "P7-no-upstream",
            f"branch {current!r} {detail}; publication closure requires an upstream on "
            f"origin. Remedy: git branch --set-upstream-to=origin/{current} {current}",
        )

    # `_verified_remote_source` (`docker_training.py:214-218`) builds the ref from
    # `source.branch`, which the inspector sets from `git branch --show-current`.
    # So origin must carry refs/heads/<LOCAL branch name>, even when the upstream
    # merge ref is spelled differently.
    listed = _git(project_root, "ls-remote", "origin", f"refs/heads/{current}")
    if listed.returncode != 0:
        # ls-remote could not TALK to origin. Distinct from every branch-state
        # failure below, because pushing would not help and saying so would name
        # the wrong cause -- the defect P7 exists to avoid.
        _fail(
            "P7-origin-unreachable",
            f"git ls-remote origin refs/heads/{current} could not reach origin: "
            f"{listed.stderr.strip()}. Remedy: check network access to origin "
            f"(and credentials, if it is a private remote) and rerun.",
        )
    first = listed.stdout.split()
    remote_sha = first[0] if first else ""
    if not remote_sha:
        # Exit 0 with no refs line is git reporting SUCCESSFULLY that origin does
        # not carry the branch. That is a branch-state problem a push fixes, so it
        # stays a mismatch rather than joining the unreachable case above.
        _fail(
            "P7-remote-mismatch",
            f"origin has no refs/heads/{current}; publication closure cannot resolve it. "
            f"Remedy: git push origin {current}",
        )
    if remote_sha != head_sha:
        _fail(
            "P7-remote-mismatch",
            f"origin/{current} is {remote_sha[:12]} but HEAD is {head_sha[:12]}; the run "
            f"would resolve a different commit. Remedy: git push origin {current}",
        )

    print(f"    PASS P7-branch-publishable: {current} tracks origin at {head_sha[:12]}")


# --------------------------------------------------------------------------
# Mount-source probe (blocker B-1 residual, section 9.1 step 6)
# --------------------------------------------------------------------------

def _wsl_path(path: Path, root: str, *, check: str) -> str:
    """Restatement of `docker_v1/prepared.py:44-57` (`_wsl_path`).

    `check` is the CALLER's cause tag. Three probes render a mount source
    through here, and a fault must report the name of the probe that was
    running, not the name of whichever probe happened to be written first.
    Reporting a wrong cause is the defect P7 split its own tags to avoid, and a
    shared literal here would have re-introduced it.
    """
    if (
        not root.startswith("/") or root.endswith("/") or "\\" in root
        or any(part in {"", ".", ".."} for part in root[1:].split("/"))
    ):
        _fail(check, f"drive mount root {root!r} is invalid")
    value, drive = path.as_posix(), path.drive
    if len(drive) != 2 or drive[1] != ":" or not value.startswith(drive + "/"):
        _fail(check, f"{path} is not a Windows drive path")
    relative = value[3:]
    if not relative or any(part in {"", ".", ".."} for part in relative.split("/")):
        _fail(check, f"{path} has an invalid relative part")
    return f"{root}/{drive[0].lower()}/{relative}"


def _mount_source(path: Path, *, distro: str, root: str, check: str) -> str:
    """Restatement of the UNC concatenation at `docker_v1/prepared.py:235`."""
    return "\\\\wsl.localhost\\" + distro + _wsl_path(path, root, check=check).replace("/", "\\")


def _probe_bind_source(
    docker: str, endpoint: str, project_root: Path, *, distro: str, root: str
) -> None:
    """Bind the rendered mount source and list it. No training.

    This is the residual of blocker B-1. If it fails, the fix is a
    CONFIGURATION change, not a code change: switch
    `docker_host.drive_mount_root` to `/mnt` and `wsl_distro` to
    `Ubuntu-22.04` and re-probe (section 6.3). This driver never edits the
    profile; that field belongs to the B-1 implementation.
    """
    source = _mount_source(
        project_root, distro=distro, root=root, check="B1-bind-probe"
    )
    print(f"    rendered mount source: {source}")
    completed = _run([
        docker, "--host", endpoint, "run", "--rm", "--pull", "never",
        "--network", "none",
        "--mount", f"type=bind,source={source},target=/probe,readonly",
        _PROBE_IMAGE, "sh", "-c", "ls -1 /probe | head -20",
    ])
    if completed.returncode != 0:
        _fail(
            "B1-bind-probe",
            f"the engine could not bind {source} (candidate drive_mount_root={root!r}, "
            f"wsl_distro={distro!r}): {completed.stderr.strip()}",
        )
    listed = completed.stdout.strip().splitlines()
    if not listed:
        _fail(
            "B1-bind-probe",
            f"{source} bound but listed EMPTY; this is the legacy /mnt/f skeleton "
            "symptom, which looks plausible and is not the real drive",
        )
    print(f"    PASS B1-bind-probe: {len(listed)} entr(y|ies) visible, e.g. {listed[0]!r}")


# --------------------------------------------------------------------------
# Precondition P8 (blocker B-9, architecture section 18.11)
# --------------------------------------------------------------------------

# The committed profile declares the identity the pinned WSL distro presents as
# OWNER of the project drive, and the prepared composition emits it as `--user`
# (section 18.3). This driver restates the KEY NAME only and reads the VALUE on
# every run, because there is no universally correct uid: it is a property of
# the host, not of the design (section 18.7). That is also why this is a profile
# field and not a module constant like `_CONTAINER_ENTRYPOINT` above.
_CONTAINER_USER_KEY = "container_user"

# The REAL stage parent, the one `docker_staging.py:1686` creates with the same
# idempotent call. Probing it rather than a scratch directory removes an
# inference: the presented mode of a fresh directory comes from the mount policy
# rather than from its creator, so a throwaway would be equivalent ON THIS HOST,
# but that equivalence rests on a single measurement (section 18.11).
_STAGE_PARENT_PARTS = (".synaptic", "state", "docker", "stages")
_P8_PROBE_DIRECTORY = "p8-probe"
_P8_PROBE_FILE = ".p8probe"


def _read_container_user(profile: dict) -> str:
    """The committed `docker_host.container_user`, or a named failure.

    Deliberately separate from P5. P5 answers WHERE the drive appears; this
    answers WHO owns it there, and the two land in different commits: the field
    arrives with the Host composition change (task #134). Until it does, a run
    must say which change is missing rather than raising `KeyError`. That is the
    shape P5 already uses for blocker B-1 (`:244-248`).

    Read here, in the precondition block, rather than beside the probe below, so
    a missing field costs nothing: it fails before anything touches Docker.

    The shape check is light on purpose. The Host's create-argv parser holds the
    authoritative grammar (section 18.8(3)); restating its exact bounds here
    would be a second copy free to drift. What is worth catching early is the
    NAME form, because a name in `--user` resolves against the IMAGE's
    `/etc/passwd` and cannot express a host mount identity at all.
    """
    docker_host = profile.get("docker_host")
    if not isinstance(docker_host, dict):
        _fail("P8-container-user-missing", "profile has no docker_host section")
    value = docker_host.get(_CONTAINER_USER_KEY)
    if not isinstance(value, str) or not value:
        _fail(
            "P8-container-user-missing",
            "docker_host.container_user is missing from the committed profile, so the "
            "prepared composition cannot emit --user and blocker B-9 is unfixed "
            "(task #134). A failure here before that change lands is this check "
            "working, not a regression: the field takes effect only once it is "
            "committed AND a new released checkout is built.",
        )
    halves = value.split(":")
    if len(halves) != 2 or not all(half.isdigit() for half in halves):
        _fail(
            "P8-container-user-shape",
            f"docker_host.container_user is {value!r}; it must be numeric uid:gid. "
            "A name resolves against the IMAGE's /etc/passwd and cannot express the "
            "identity of a host mount, so the Host parser refuses it (section 18.8).",
        )
    print(f"    PASS P8-container-user: {value}")
    return value


def _remove_p8_probe(probe: Path) -> None:
    """Remove ONLY the probe directory and ONLY the probe file inside it.

    Never the stage parent, and never a stage. `_verify_artifact_topology`
    (`docker_staging.py:1446-1481`) requires the four writable artifact
    directories to be EMPTY, and section 18.18's B-10 finding is that it runs on
    EVERY cut rather than once per run, so a stray probe file left inside a stage
    would break the run at the next cut, not merely at re-staging.

    Two exact names, no recursive delete, and a failure here is reported rather
    than escalated: leaving a directory behind is cheap, and removing the wrong
    one is not.
    """
    leftover = probe / _P8_PROBE_FILE
    try:
        if leftover.exists():
            leftover.unlink()
        probe.rmdir()
    except OSError as error:
        print(f"    NOTE could not remove the probe directory {probe}: {error}")


def _check_p8_stage_writable_as_container_user(
    docker: str,
    endpoint: str,
    image: str,
    project_root: Path,
    *,
    distro: str,
    root: str,
    container_user: str,
) -> None:
    """The container user can write a bind whose source is a real stage sibling.

    Blocker B-9, measured on run 4 (task #128): the pinned distro mounts the
    project drive `metadata;uid=1000;gid=1000;umask=22;fmask=11`, so DrvFs
    honours stored POSIX modes and a fresh directory presents 0755 owned by uid
    1000. The composition passed no `--user`, the container ran as the image's
    own uid 1001, and `/artifacts` was r-x.

    The ruling (section 18.2) matches the mount's OWNER rather than fighting its
    MODE, because the owner has `rwx` under every mode policy the mount can
    present -- `umask=22` gives 755, `umask=77` gives 700, a no-`metadata` mount
    gives 0777. So the failure below is a CONFIGURATION failure with a named
    remedy, not a code failure.

    Ordered after P7 and after the B1 bind probe: this needs a bind already
    proven to resolve, or a mount-source fault would surface as a permission
    message. It precedes every assertion, because a non-writable stage makes the
    rest of the run moot.
    """
    stage_parent = project_root.joinpath(*_STAGE_PARENT_PARTS)
    existed = stage_parent.is_dir()
    try:
        # The identical idempotent call the staging code makes at
        # `docker_staging.py:1686`. Matching it is the point: this probe measures
        # the directory the run will actually use.
        stage_parent.mkdir(parents=True, exist_ok=True)
        probe = stage_parent / _P8_PROBE_DIRECTORY
        probe.mkdir(exist_ok=True)
    except OSError as error:
        _fail(
            "P8-stage-writable-as-container-user",
            f"the Host could not create {stage_parent}: {error}",
        )
    if existed:
        print(f"    stage parent already present: {stage_parent}")
    else:
        print(f"    CREATED the stage parent {stage_parent}")
        print(
            "    NOTE a --probe-only pass now creates that directory. A run creates it "
            "anyway, by this same idempotent call, but 'no durable state was written' "
            "no longer holds for a probe-only pass (section 18.11)."
        )

    source = _mount_source(
        probe, distro=distro, root=root,
        check="P8-stage-writable-as-container-user",
    )
    print(f"    rendered mount source: {source}")
    # `id` is echoed so the effective user is EVIDENCE in the run report rather
    # than an assumption. The HOME pair answers B-9-R1 and never fails the run.
    program = (
        "id; "
        f"touch /artifacts/{_P8_PROBE_FILE} && rm /artifacts/{_P8_PROBE_FILE} "
        "&& echo WRITABLE; "
        'printf "HOME=%s " "$HOME"; '
        'test -w "$HOME" && echo home-writable || echo home-not-writable'
    )
    try:
        completed = _run([
            docker, "--host", endpoint, "run", "--rm", "--pull", "never",
            "--network", "none",
            "--user", container_user,
            # `destination=` rather than `target=`, matching the spelling the
            # prepared composition itself uses (`control_private.py:410-411`).
            "--mount", f"type=bind,source={source},destination=/artifacts",
            "--entrypoint", _CONTAINER_ENTRYPOINT,
            image, "sh", "-c", program,
        ])
    finally:
        _remove_p8_probe(probe)

    for line in completed.stdout.strip().splitlines():
        print(f"    p8| {line}")
    if completed.returncode != 0 or "WRITABLE" not in completed.stdout:
        # P3 has already refused a root without a drive letter, so this is
        # normally present. Defended anyway: a failure message that raises
        # IndexError would replace the named cause with an unrelated traceback,
        # which is the opposite of what this check exists to do.
        drive = project_root.drive
        drive_letter = drive[0].lower() if drive else "<drive letter>"
        _fail(
            "P8-stage-writable-as-container-user",
            f"{container_user} could not write /artifacts over {source}: "
            f"{completed.stderr.strip()}\n"
            "  The prepared path requires docker_host.container_user to equal the "
            "identity the\n"
            "  pinned WSL distro presents as owner of the project drive. Read it with:\n"
            f"    wsl.exe -d {distro} -- awk '$2==\"{root}/{drive_letter}\""
            "{print $4}' /proc/mounts\n"
            "  and set docker_host.container_user in training/providers/docker.json to "
            "that\n"
            "  uid:gid, then commit and rebuild the released checkout. This is "
            "blocker B-9.",
        )

    if "home-not-writable" in completed.stdout:
        # A WARNING, never a failure (section 18.10). `--user` names an id with no
        # `/etc/passwd` entry, so the runtime sets HOME=/. test-host measured
        # exactly that on task #131, so this line is EXPECTED on every pass today.
        # Failing on it would refuse a configuration that is legitimate for a
        # workload that never writes there.
        print(
            "    WARN P8-home: HOME is not writable for this user. EXPECTED on this "
            "host and NOT a failure -- --user names an id with no /etc/passwd entry, "
            "so HOME=/ (measured, task #131). Deferred as B-9-R1; settled by run 5's "
            "trainer output, not here."
        )
    print(
        f"    PASS P8-stage-writable-as-container-user: {container_user} wrote and "
        f"removed a file under the real stage parent"
    )


# --------------------------------------------------------------------------
# Early assertions A1-A4 (section 10.1)
# --------------------------------------------------------------------------

def _assert_a1_gpu(docker: str, endpoint: str, image: str) -> None:
    """GPU visible inside the container.

    The image's `NVIDIA_REQUIRE_CUDA` bands top out below this host's driver
    610.88. Whether the container toolkit rejects, warns, or ignores that is
    untested, and a rejection would otherwise look like an unrelated failure.
    """
    completed = _run([
        docker, "--host", endpoint, "run", "--rm", "--pull", "never",
        "--gpus", "driver=nvidia,device=0",
        "--entrypoint", _CONTAINER_ENTRYPOINT,
        image, "nvidia-smi", "-L",
    ])
    if completed.returncode != 0:
        _fail("A1-gpu-visible", f"--gpus driver=nvidia,device=0 failed: {completed.stderr.strip()}")
    if "GPU 0" not in completed.stdout:
        _fail("A1-gpu-visible", f"no GPU listed inside the container: {completed.stdout.strip()!r}")
    print(f"    PASS A1-gpu-visible: {completed.stdout.strip().splitlines()[0]}")


def _assert_a2_artifacts_writable(
    docker: str, endpoint: str, image: str, project_root: Path,
    *, distro: str, root: str, container_user: str
) -> None:
    """`/artifacts` writable by the container's user over a bind.

    The artifact directory is mounted writable, and a read-only `/artifacts`
    fails late and confusingly. The probe writes into a scratch directory, never
    into a stage.

    The user is READ FROM THE PROFILE, not hardcoded. This probe used to pass
    `unsloth:runtimeusers`, the image's own default, which was faithful only
    while the composition passed no `--user` at all. Once it emits
    `docker_host.container_user` (section 18.3), a hardcoded name would fail a
    run the composition would have completed -- a false blocker. Section 17.10:
    the probes assert the same contract the composition uses.

    P8 above is not made redundant by this. P8 probes the real STAGE parent and
    names the cause and the remedy; A2 probes a scratch directory and has
    continuity across runs 1-4.
    """
    probe_root = project_root / "scratch" / "test-phase" / "a2-artifact-probe"
    probe_root.mkdir(parents=True, exist_ok=True)
    source = _mount_source(
        probe_root, distro=distro, root=root, check="A2-artifacts-writable"
    )
    completed = _run([
        docker, "--host", endpoint, "run", "--rm", "--pull", "never",
        "--network", "none",
        "--user", container_user,
        "--mount", f"type=bind,source={source},target=/artifacts",
        "--entrypoint", _CONTAINER_ENTRYPOINT,
        image, "sh", "-c",
        "touch /artifacts/.a2probe && rm /artifacts/.a2probe && echo WRITABLE",
    ])
    if completed.returncode != 0 or "WRITABLE" not in completed.stdout:
        _fail(
            "A2-artifacts-writable",
            f"{container_user} could not write /artifacts over {source}: "
            f"{completed.stderr.strip()}",
        )
    print(f"    PASS A2-artifacts-writable: {container_user} wrote and removed a file")


def _assert_a3_python_version(
    docker: str, endpoint: str, image: str, executable: str, expected: str
) -> None:
    """The container's Python must match the profile at FULL patch level.

    `Trainers/sft/runtime_v1.py:1121-1138` demands full patch-level equality
    against the profile's `python_version` and refuses otherwise.
    """
    completed = _run([
        docker, "--host", endpoint, "run", "--rm", "--pull", "never",
        "--network", "none",
        "--entrypoint", _CONTAINER_ENTRYPOINT,
        image, executable, "-c", "import platform; print(platform.python_version())",
    ])
    if completed.returncode != 0:
        _fail("A3-python-version", f"{executable} did not run: {completed.stderr.strip()}")
    actual = completed.stdout.strip()
    if actual != expected:
        _fail("A3-python-version", f"expected exactly {expected!r}, got {actual!r}")
    print(f"    PASS A3-python-version: {actual}")


def _assert_a4_inventory(project_root: Path, python_executable: str) -> None:
    """The snapshot exists at the cache path and contains no links.

    Delegates to the materialization script's `--verify-only` mode so there is
    exactly one implementation of the inventory contract.
    """
    script = project_root / ".skills" / "host-docker-run" / "scripts" / "materialize_model_inventory.py"
    completed = _run([python_executable, str(script), "--verify-only",
                      "--project-root", str(project_root)])
    if completed.returncode != 0:
        detail = (completed.stderr.strip() or completed.stdout.strip())
        _fail("A4-inventory-link-free", f"inventory verification failed: {detail}")
    tail = [line for line in completed.stdout.strip().splitlines() if line.startswith("OK")]
    for line in tail:
        print(f"    {line}")
    print("    PASS A4-inventory-link-free")


# --------------------------------------------------------------------------
# The run loop
# --------------------------------------------------------------------------

def _read_phase(project_root: Path, run_id: str | None) -> tuple[str | None, str | None]:
    """Read the durable phase read-only. Returns (phase, run_id)."""
    database = project_root / ".synaptic" / "state" / "training.sqlite3"
    if not database.is_file():
        return None, run_id
    uri = f"file:{database.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=30)
    except sqlite3.Error:
        return None, run_id
    try:
        connection.row_factory = sqlite3.Row
        if run_id:
            row = connection.execute(
                "SELECT run_id, phase FROM docker_run_mutations WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT run_id, phase FROM docker_run_mutations ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
    except sqlite3.Error:
        return None, run_id
    finally:
        connection.close()
    if row is None:
        return None, run_id
    return row["phase"], row["run_id"]


def _read_publications(project_root: Path, destination_ref: str) -> int:
    database = project_root / ".synaptic" / "state" / "training.sqlite3"
    if not database.is_file():
        return 0
    uri = f"file:{database.as_posix()}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=30)
    except sqlite3.Error:
        return 0
    try:
        row = connection.execute(
            "SELECT COUNT(*) FROM publication_records_v1 WHERE destination_ref = ?",
            (destination_ref,),
        ).fetchone()
    except sqlite3.Error:
        return 0
    finally:
        connection.close()
    return int(row[0]) if row else 0


def _surface_trainer_stderr(project_root: Path) -> None:
    """Print `trainer.stderr.log` FIRST on failure (section 7.3).

    The tracking root lives inside the stage the run created, so the newest
    matching file under the stages directory is the one for this run.
    """
    stages = project_root / ".synaptic" / "state" / "docker" / "stages"
    print("\n--- trainer.stderr.log (read this before diagnosing anything else) ---")
    if not stages.is_dir():
        print(f"    none found: {stages} does not exist")
        return
    logs = sorted(stages.rglob("trainer.stderr.log"), key=lambda p: p.stat().st_mtime)
    if not logs:
        print(f"    none found under {stages}")
        print("    If the trainer never started, the failure is upstream of the container.")
        return
    newest = logs[-1]
    print(f"    {newest}")
    try:
        for line in newest.read_text(encoding="utf-8", errors="replace").splitlines():
            print(f"    | {line}")
    except OSError as error:
        print(f"    could not be read: {error}")
    print(
        "    If this ends at Trainers/sft/runtime_v1.py:1811 "
        "('trainer adapter config is not recognizable LoRA'), that is blocker "
        "B-2 (task #85), NOT a platform fault."
    )


def _one_cut(python_executable: str, project_root: Path, args) -> tuple[int, dict]:
    """Issue exactly one cut of the unchanging eight-token command."""
    argv = [
        python_executable, "-m", "synaptic_host",
        "training", "run",
        "--provider", args.provider,
        "--config", args.config,
        "--destination", args.destination,
    ]
    completed = subprocess.run(
        argv, text=True, capture_output=True, check=False,
        cwd=str(project_root), timeout=args.cut_timeout_seconds,
    )
    print(f"    $ {subprocess.list2cmdline(argv)}")
    line = completed.stdout.strip().splitlines()
    result: dict = {}
    if line:
        try:
            result = json.loads(line[-1])
        except ValueError:
            result = {}
    if completed.stderr.strip():
        for entry in completed.stderr.strip().splitlines():
            print(f"    stderr| {entry}")
    return completed.returncode, result


def _drive(python_executable: str, project_root: Path, args) -> None:
    print("\n=== run loop ===")
    print(
        "Section 9.3: at least THREE post-submit cuts. An observe cut may repeat, "
        "then a verify cut writes ARTIFACTS_VERIFIED and publishes nothing, then a "
        "publish cut is a separate call. published == False after one cut is CORRECT."
    )
    deadline = time.monotonic() + args.max_seconds
    run_id: str | None = None
    previous_phase: str | None = None
    previous_rank = 0
    verify_cut_logged = False
    publish_cut_logged = False

    for cut in range(1, args.max_cuts + 1):
        if time.monotonic() > deadline:
            _fail("L2-wall-clock", f"exceeded --max-seconds={args.max_seconds} after {cut - 1} cut(s)")

        print(f"\n[cut {cut}] entering with phase={previous_phase}")
        exit_code, result = _one_cut(python_executable, project_root, args)
        status = result.get("status")
        run_id = result.get("run_id") or run_id
        phase, run_id = _read_phase(project_root, run_id)
        print(f"[cut {cut}] exit={exit_code} status={status} run_id={run_id} phase={phase}")

        # A rejected or unavailable command never mutates the durable record, so
        # the phase would stay None and the loop would spin to --max-cuts.
        # Fail immediately with the code the Host reported (`cli.py:1087-1090`
        # returns 2 for rejected).
        if status in {"rejected", "unavailable"}:
            _surface_trainer_stderr(project_root)
            _fail(
                "L6-command-refused",
                f"the Host returned status={status} code={result.get('code')} on cut {cut}",
            )

        # Section 10.3, the assertable half of M-8: SUBMITTED requires three
        # things (`docker_training.py:715-719`), so any cut that sets
        # RECONCILE_REQUIRED must NOT report a submitted run.
        if phase == "RECONCILE_REQUIRED" and status == "submitted":
            _fail(
                "M8-submitted-consistency",
                "phase is RECONCILE_REQUIRED but the command reported status=submitted",
            )

        if phase == "PROCESS_FAILED":
            _surface_trainer_stderr(project_root)
            _fail("L3-process-failed", f"durable phase reached PROCESS_FAILED after {cut} cut(s)")

        rank = _PHASE_RANK.get(phase or "", 0)
        if previous_phase is not None and phase != previous_phase and rank and rank < previous_rank:
            _surface_trainer_stderr(project_root)
            _fail("L4-phase-regressed", f"phase went backwards: {previous_phase} -> {phase}")

        # The next cut is the named one. Logged separately because section 9.3
        # requires the verify and publish cuts to be distinct calls, and because
        # confusing them is how "at least three cuts" gets miscounted as two.
        if phase == "PROCESS_SUCCEEDED" and not verify_cut_logged:
            print("           the NEXT cut is the VERIFY cut: it writes "
                  "ARTIFACTS_VERIFIED and publishes nothing.")
            verify_cut_logged = True
        if phase == "ARTIFACTS_VERIFIED" and not publish_cut_logged:
            print("           the NEXT cut is the PUBLISH cut: a separate call, "
                  "constructed only in the ARTIFACTS_VERIFIED branch.")
            publish_cut_logged = True

        # A repeating SUBMITTED is the OBSERVE cut, not a stall: while the
        # container runs, the observe cut returns the record unchanged
        # (`docker_execution.py:1201-1202`). It must not end the loop; the
        # --max-cuts and --max-seconds bounds are what end it.
        if phase == previous_phase and phase not in {None, "SUBMITTED"}:
            # The phase stopped advancing. That is success ONLY at
            # ARTIFACTS_VERIFIED with a publication row; settling anywhere else
            # is a stuck run, not a finished one.
            print(f"\n[done] phase stopped advancing at {phase}")
            if phase != "ARTIFACTS_VERIFIED":
                _surface_trainer_stderr(project_root)
                _fail(
                    "L7-settled-early",
                    f"phase settled at {phase}, which is not a completed run",
                )
            published = _read_publications(project_root, args.destination)
            print(f"[done] publication_records_v1 rows for {args.destination}: {published}")
            if published < 1:
                _fail(
                    "L5-not-published",
                    f"phase settled at ARTIFACTS_VERIFIED but no publication row exists "
                    f"for destination_ref={args.destination!r}",
                )
            return

        previous_phase = phase
        previous_rank = rank or previous_rank
        if cut < args.max_cuts:
            time.sleep(args.cut_interval_seconds)

    _fail("L1-max-cuts", f"exceeded --max-cuts={args.max_cuts} without settling")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the prepared-path Docker training cut loop with the section 9.1 "
            "preconditions and the section 10.1 early assertions."
        )
    )
    parser.add_argument("--project-root", default=str(_PROJECT_ROOT))
    parser.add_argument("--docker", default=_DEFAULT_DOCKER)
    parser.add_argument(
        "--endpoint", default=_DEFAULT_ENDPOINT,
        help="used ONLY for this driver's read-only probes; never passed to the Host.",
    )
    parser.add_argument("--context", default=_DEFAULT_CONTEXT)
    parser.add_argument("--provider", default=_DEFAULT_PROVIDER)
    parser.add_argument("--config", default=_DEFAULT_CONFIG_REF)
    parser.add_argument("--destination", default=_DEFAULT_DESTINATION)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--max-cuts", type=int, default=_DEFAULT_MAX_CUTS)
    parser.add_argument("--max-seconds", type=int, default=_DEFAULT_MAX_SECONDS)
    parser.add_argument(
        "--cut-interval-seconds", type=int, default=_DEFAULT_CUT_INTERVAL_SECONDS
    )
    parser.add_argument("--cut-timeout-seconds", type=int, default=900)
    parser.add_argument(
        "--probe-only", action="store_true",
        help=(
            "run the preconditions, the bind probe, P8 and A1-A4, then stop. "
            "P8 CREATES the stage parent if it is absent, so a probe-only pass is "
            "no longer free of durable state."
        ),
    )
    args = parser.parse_args(argv)

    project_root = Path(args.project_root).resolve(strict=False)
    print(f"project root : {project_root}")
    print(f"docker       : {args.docker}")
    print(f"command      : -m synaptic_host training run --provider {args.provider} "
          f"--config {args.config} --destination {args.destination}")
    print()

    try:
        print("=== preconditions (section 9.1) ===")
        _check_p1_single_docker(args.docker)
        _check_p2_endpoint(args.docker, args.context, args.endpoint)
        _check_p3_drive_letter_root(project_root)
        profile = _load_profile(project_root)
        distro, drive_mount_root = _check_p5_drive_mount_root(profile)
        _check_p6_config_is_committed(project_root, args.config)
        _check_p7_branch_is_publishable(project_root)
        container_user = _read_container_user(profile)

        runtime = profile.get("runtime") or {}
        image = runtime.get("image")
        python_version = runtime.get("python_version")
        python_executable = runtime.get("python_executable")
        if not (image and python_version and python_executable):
            _fail("P4-profile", "profile runtime section is incomplete")

        print("\n=== mount-source bind probe (blocker B-1 residual) ===")
        _probe_bind_source(
            args.docker, args.endpoint, project_root,
            distro=distro, root=drive_mount_root,
        )

        # After P7 AND after the bind probe, before A1: P8 needs a bind already
        # proven to resolve, or a mount-source fault would surface as a
        # permission message (section 18.11).
        print("\n=== stage writability as the container user (blocker B-9) ===")
        _check_p8_stage_writable_as_container_user(
            args.docker, args.endpoint, image, project_root,
            distro=distro, root=drive_mount_root, container_user=container_user,
        )

        print("\n=== early assertions (section 10.1) ===")
        _assert_a1_gpu(args.docker, args.endpoint, image)
        _assert_a2_artifacts_writable(
            args.docker, args.endpoint, image, project_root,
            distro=distro, root=drive_mount_root, container_user=container_user,
        )
        _assert_a3_python_version(
            args.docker, args.endpoint, image, python_executable, python_version
        )
        _assert_a4_inventory(project_root, args.python)

        if args.probe_only:
            print("\nOK  --probe-only: every precondition and early assertion passed.")
            return 0

        _drive(args.python, project_root, args)
    except CheckFailure as failure:
        print(f"\nFAILED {failure}", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired as error:
        print(f"\nFAILED T1-timeout: {error}", file=sys.stderr)
        return 1

    print("\nOK  the run reached a terminal phase with every check passing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
