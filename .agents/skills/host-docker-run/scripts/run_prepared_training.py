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
import tempfile
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

# The exact environment the prepared composition hands its docker.exe children
# (`docker_prepared_composition.py:116`, enforced by
# `docker_v1/model.py:1144` and asserted by test E1). Restated here, not
# imported: this driver is a checked-in script outside the package and has
# never taken that seam. P10 is the only probe that uses it.
#
# Deliberately NO `USERPROFILE`. That absence is blocker B-13: without a home,
# `docker context inspect` resolves a RELATIVE `.docker` path and exits 1, so
# the composition constructs the endpoint from constants instead and proves the
# daemon with an explicit `--host` version probe (section 22.6). P10 issues that
# same probe, under that same environment, before a run is issued.
_COMPOSITION_ENVIRONMENT_KEYS = ("SystemRoot", "TEMP", "TMP", "WINDIR")

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


def _run(
    argv: list[str], *, timeout: int = 300, env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:
    """Run a child and capture it. `env` REPLACES the environment when given.

    Every probe but P10 inherits this process's environment, which is the
    operator's own shell. P10 alone passes an explicit `env`, because its whole
    purpose is to reproduce the child the prepared composition issues, and that
    child runs under a hardened environment of exactly four keys
    (`docker_prepared_composition.py:116`). An inherited environment would make
    P10 a weaker check than the thing it stands in for.

    `cwd` matters for exactly one probe too. P11 must run where the cut runs,
    because Python puts the working directory at `sys.path[0]` and the working
    directory therefore DECIDES which `synaptic_host` is imported (task #215).
    Every other probe is indifferent to it.
    """
    print(f"    $ {subprocess.list2cmdline(argv)}", flush=True)
    return subprocess.run(
        argv, text=True, capture_output=True, check=False, timeout=timeout,
        env=env, cwd=cwd,
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


def _check_p10_daemon_alive(docker: str, endpoint: str) -> None:
    """The engine answers the SAME probe the composition uses to prove it alive.

    Blocker B-13, section 22.7. `docker context inspect` is NOT a daemon check:
    test-host measured it with Docker Desktop STOPPED (task #203) and it exits 0
    with stdout byte-identical to the running case, because it reads a local
    config store and never opens the pipe. `docker desktop status` and
    `docker desktop start` also misreport while the engine is absent. The
    explicit `--host ... version --format {{.Server.Version}}` probe is the only
    one of the three that separates the two states: exit 1 stopped, exit 0
    running (29.3.1 measured).

    So P2 proving the endpoint CONSTANT and P10 proving the endpoint ANSWERS are
    two different facts, and only the second one is a daemon check.

    This is the same command the prepared composition issues at
    `docker_prepared_composition.py:172-178` after constructing the endpoint,
    run under the same four-key environment. Reproducing the composition's child
    exactly is the point: the environment IS the B-13 variable, and a probe under
    the operator's own inherited environment would pass in the one case the Host
    fails.

    Two tags, because the remedies differ:

    - `P10-environment-incomplete`: one of the four keys is absent from the
      operator's environment, so the composition's own child cannot be built.
      The Host reports this as `one absolute Windows Docker executable is
      required` (`docker_prepared_composition.py:145`, a `KeyError` folded into
      that one message), which names the executable and not the missing key.
      This probe names the key instead. The remedy is the shell, not Docker.
    - `P10-daemon-unavailable`: the probe ran and the engine did not answer.
      The remedy is to start Docker Desktop and wait for the Linux engine.

    Key NAMES are printed; values never are. Ordered right after P2 and before
    everything else, so a stopped engine costs one command rather than a full
    precondition sweep including P7's network read.
    """
    missing = [
        key for key in _COMPOSITION_ENVIRONMENT_KEYS if not os.environ.get(key)
    ]
    if missing:
        _fail(
            "P10-environment-incomplete",
            f"the prepared composition requires {len(_COMPOSITION_ENVIRONMENT_KEYS)} "
            f"environment keys and this shell is missing {', '.join(missing)}; "
            "the Host folds that into a message about the docker executable, so "
            "it would not name the key. Run from a normal Windows shell",
        )
    environment = {key: os.environ[key] for key in _COMPOSITION_ENVIRONMENT_KEYS}
    print(
        "    P10-daemon-alive: child environment keys = "
        f"{', '.join(_COMPOSITION_ENVIRONMENT_KEYS)} "
        f"({len(_COMPOSITION_ENVIRONMENT_KEYS)} keys, names only, no values); "
        "restated from docker_prepared_composition.py:116"
    )
    completed = _run(
        [docker, "--host", endpoint, "version", "--format", "{{.Server.Version}}"],
        env=environment,
    )
    if completed.returncode != 0:
        _fail(
            "P10-daemon-unavailable",
            f"exit {completed.returncode} from the version probe against {endpoint}: "
            f"{(completed.stderr or completed.stdout).strip() or 'no output'}. "
            "Start Docker Desktop and wait for the Linux engine, then re-run. "
            "Do NOT read `docker context inspect` or `docker desktop status` as "
            "proof: section 22.7 measured both reporting success with the engine "
            "stopped",
        )
    version = completed.stdout.strip()
    if not version:
        # Reported, not gated. The ruling makes a NON-ZERO exit the gate, and a
        # zero exit with no version is a shape nobody has measured; refusing a
        # run on it would be this driver inventing a condition the Host does not
        # have.
        print(
            "    WARN P10-daemon-alive: the probe exited 0 but printed no server "
            "version. The Host's own liveness check accepts this, so the run is "
            "not gated on it; treat an unexpected later failure as related"
        )
        return
    print(f"    PASS P10-daemon-alive: server {version} answered on {endpoint}")


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


# The child P11 runs. It resolves the package the way the import system will,
# WITHOUT importing it: `find_spec` answers for a package whose `__init__`
# would fail, and it distinguishes the three outcomes that matter here. Reading
# `synaptic_host.__file__` instead would raise TypeError on a namespace package,
# whose `__file__` is None -- exactly the wrong-tree shape this probe exists to
# catch, turned into a crash.
_PACKAGE_RESOLUTION_SCRIPT = (
    "import importlib.util as u\n"
    "s = u.find_spec('synaptic_host')\n"
    "if s is None:\n"
    "    print('MISSING')\n"
    "elif s.origin:\n"
    "    print('ORIGIN ' + s.origin)\n"
    "else:\n"
    "    print('NAMESPACE ' + '|'.join(s.submodule_search_locations or ()))\n"
)


def _check_p11_package_resolves_under_project_root(
    python_executable: str, project_root: Path
) -> None:
    """The `synaptic_host` a run will import comes from the project root given.

    Found by test-host during run 8 (task #211): its wrapper imported
    `synaptic_host` from a WORKTREE while every checkout identity check reported
    the release commit. Nothing was wrong with those checks. P6 reads the
    committed config blob, P7 proves HEAD is the published commit and P9 reads
    blobs at that commit, so all three answer the question "which tree is this?"
    -- and none answers "which tree will the code come from?".

    The mechanism, measured on this interpreter rather than taken from the
    report: Python puts the working directory at `sys.path[0]` and PYTHONPATH
    after it, so with a package in the working directory that package wins; with
    NO package in the working directory the child falls through to PYTHONPATH
    and imports a different tree with no warning of any kind. The silent
    fallback is the dangerous half. `_one_cut` sets `cwd=project_root`, so a
    release root that carries the package is safe; a root that does not is not.

    This probe reproduces the cut's child exactly: the SAME interpreter
    (`--python`, default `sys.executable`) and the SAME `cwd`, and it INHERITS
    the operator's environment because `_one_cut` passes no `env`. That is the
    opposite of P10, which passes a restricted four-key environment because it
    mirrors the composition's docker child. A probe under the wrong environment
    would answer for a shape no run uses.

    Four named refusals, one per remedy:

    - `P11-resolution-failed`: the child itself did not run.
    - `P11-package-not-found`: nothing named `synaptic_host` is importable from
      the project root at all. The remedy is the checkout, not the path.
    - `P11-namespace-package`: the name resolved to a directory with no
      `__init__.py`. Measured (PEP 420): such a directory does NOT shadow a real
      package further along the path, so this state means the root's own package
      is not importable and some other tree is one PYTHONPATH entry away from
      being used instead.
    - `P11-wrong-tree`: it resolved somewhere outside the project root. The
      message names BOTH paths, because the whole failure is that they differ
      while every other check says they agree.

    Containment under the given project root is the rule. There is deliberately
    NO refusal on a `_worktrees` path component: that substring was a proxy for
    containment in test-host's wrapper, it would refuse a legitimate
    `--probe-only` pass from a worktree, and P7 already refuses a worktree for a
    real run because a worktree branch has no local upstream.

    Ordered after P3, which has just proven the root is a Windows drive path,
    and before P5/P6/P7, which read that tree: knowing WHICH code will run
    should precede reading what it is configured to do.
    """
    completed = _run(
        [python_executable, "-c", _PACKAGE_RESOLUTION_SCRIPT],
        timeout=60, cwd=str(project_root),
    )
    if completed.returncode != 0:
        _fail(
            "P11-resolution-failed",
            f"{python_executable} could not resolve synaptic_host from {project_root}: "
            f"{completed.stderr.strip() or 'no output'}",
        )
    answer = completed.stdout.strip()
    if answer == "MISSING":
        _fail(
            "P11-package-not-found",
            f"no synaptic_host is importable from {project_root}. The run would "
            "import nothing at all. Check that the released checkout is complete",
        )
    if answer.startswith("NAMESPACE "):
        _fail(
            "P11-namespace-package",
            f"synaptic_host resolved to a directory with no __init__.py: "
            f"{answer[len('NAMESPACE '):]}. The project root's own package is not "
            "importable, so any tree on PYTHONPATH would be used instead. Check "
            "that the released checkout is complete",
        )
    if not answer.startswith("ORIGIN "):
        _fail(
            "P11-resolution-failed",
            f"unexpected resolution output {answer!r} from {python_executable}",
        )
    resolved = Path(answer[len("ORIGIN "):]).resolve()
    if project_root != resolved and project_root not in resolved.parents:
        _fail(
            "P11-wrong-tree",
            f"synaptic_host resolves to {resolved}, which is NOT under the project "
            f"root {project_root}. The run would exercise that tree while every "
            "commit check reported this one. Launch from the released checkout, "
            "and check PYTHONPATH",
        )
    print(f"    PASS P11-package-under-project-root: {resolved}")


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


# Restated from `docker_staging.py:45-47`. Section 21.7 repurposes the first and
# third: after B-12 they bound the STAGED INPUT SET, not the operator's
# repository. Restated rather than imported, because a skill script does not
# import `synaptic_host` and this driver has never taken that seam. The cost of
# restating is that the copy can drift, so the coupling is named in the task
# #188 handoff for the auditor: if the Host's values move, this block moves in
# the same change.
_MAX_PROJECT_ARCHIVE_BYTES = 256 * 1024 * 1024
_MAX_PROJECT_EXPANDED_BYTES = 512 * 1024 * 1024
_MAX_PROJECT_ENTRIES = 20_000

_PROJECT_REF_PREFIX = "project://"


def _project_relative(ref: str) -> str | None:
    """`project://<path>` -> `<path>`, or None when the ref is not a project ref.

    Deliberately separate from P6's inline slicing (`:274-275`), which is scoped
    to `project://training/` because that is all a config ref is ever spelled
    as. A dataset ref is author-supplied and need not sit under `training/`, so
    this one refuses rather than mis-slices.
    """
    if not ref.startswith(_PROJECT_REF_PREFIX):
        return None
    relative = ref[len(_PROJECT_REF_PREFIX):]
    return relative or None


def _blob_size_at(project_root: Path, commit: str, relative: str) -> int | None:
    """`git cat-file -s <commit>:<path>`, or None if it cannot be read."""
    completed = _git(project_root, "cat-file", "-s", f"{commit}:{relative}")
    if completed.returncode != 0:
        return None
    try:
        return int(completed.stdout.strip())
    except ValueError:
        return None


def _check_p9_locked_project_inputs(project_root: Path, config_ref: str) -> None:
    """Report what the prepared path will stage from the project. Never gates.

    Blocker B-12 (task #179), measured on run 6: staging archived the WHOLE
    superproject at the locked commit, 412,794,880 bytes against the 256 MiB
    bound at `docker_staging.py:45`, and refused before any container existed.
    Section 21.4 rules that staging stages only the descriptors
    `source_lock.inputs` already records -- `training-config` and
    `training-dataset` (`docker_training.py:278-281`) -- so the staged volume is
    now a property of the WORKLOAD, not of the repository. This probe puts that
    number in front of the operator BEFORE a run is issued, instead of after a
    failed cut.

    It REPORTS. It never gates, never exits and never raises (section 21.13:
    the Host owns the refusal, admission is the gate). A driver-side gate would
    be a second opinion about a set the driver does not own and cannot see at
    admission time, and it would enforce a copy of a constant whose meaning
    section 21.7 has already moved once.

    Where the descriptors come from, since there is no pre-run lock artifact to
    read -- the lock is built DURING admission:

    - `training-config` is `--config`, already on the prepared command.
    - `training-dataset` is that config's own `dataset.ref`, which is what
      admission resolves as `ingress.training_input.dataset.ref`
      (`docker_training.py:727`).

    Both are read at the LOCKED COMMIT rather than from the working tree, which
    is the same source of truth admission uses (`_read_committed_git_blob_v1`
    reads the commit) and the property section 21.6 keeps.

    That makes this a SECOND derivation of a scope the Host owns, and section
    21.4's addendum names quiet divergence -- two things that should agree,
    disagreeing, with success reported both times -- as the failure worth
    engineering against. So the report says it is the DRIVER's derivation and
    names the commit and both paths, which is what lets a human check it against
    the staged source manifest instead of inferring agreement. For the same
    reason it SKIPs with a named reason rather than printing a number it is not
    sure of: nothing downstream re-checks this arithmetic.

    Ordered after P7, which has just proven HEAD is the published commit this
    reads at, and before the bind probe.
    """
    completed = _git(project_root, "rev-parse", "HEAD")
    if completed.returncode != 0 or not completed.stdout.strip():
        print(
            "    SKIP P9-locked-project-inputs: git.exe could not resolve HEAD "
            f"({completed.stderr.strip() or 'no output'}); no size is reported "
            "rather than one read at an unknown commit"
        )
        return
    commit = completed.stdout.strip()

    config_relative = _project_relative(config_ref)
    if config_relative is None:
        print(
            f"    SKIP P9-locked-project-inputs: --config {config_ref!r} is not a "
            f"{_PROJECT_REF_PREFIX} reference, so the locked input set cannot be derived"
        )
        return

    print(f"    P9-locked-project-inputs: derived by the DRIVER at {commit}")

    config_size = _blob_size_at(project_root, commit, config_relative)
    if config_size is None:
        print(
            f"    SKIP P9-locked-project-inputs: {config_relative} is not readable "
            f"at {commit}; P6 checks the working tree, this reads the commit"
        )
        return
    print(f"    P9-INPUT kind=training-config path={config_relative} bytes={config_size}")

    dataset_relative = _dataset_relative_from_config(project_root, commit, config_relative)
    if dataset_relative is None:
        print(
            "    WARN P9-locked-project-inputs: the dataset ref is unresolved, so the "
            "total is NOT reported; the config above is one of two locked inputs. "
            "This probe reports and does not gate, so the run is unaffected and "
            "admission remains the gate."
        )
        return
    dataset_size = _blob_size_at(project_root, commit, dataset_relative)
    if dataset_size is None:
        print(
            f"    WARN P9-locked-project-inputs: {dataset_relative} is not readable at "
            f"{commit}, so the dataset size is unresolved and no total is reported. "
            "The Host would refuse this at admission; this probe does not gate."
        )
        return
    print(f"    P9-INPUT kind=training-dataset path={dataset_relative} bytes={dataset_size}")

    total = config_size + dataset_size
    count = 2
    within = total <= _MAX_PROJECT_ARCHIVE_BYTES and count <= _MAX_PROJECT_ENTRIES
    print(
        f"    P9-TOTAL count={count} bytes={total} "
        f"archive_bound={_MAX_PROJECT_ARCHIVE_BYTES} entries_bound={_MAX_PROJECT_ENTRIES}"
    )
    if within:
        print(
            f"    PASS P9-locked-project-inputs: {total} byte(s) in {count} input(s), "
            "which is what the prepared path stages from the project. The SIZE OF THE "
            "PROJECT is not part of this number and is not a precondition."
        )
        return
    print(
        f"    WARN P9-locked-project-inputs: {total} byte(s) in {count} input(s) exceeds "
        f"the Host's staging bound ({_MAX_PROJECT_ARCHIVE_BYTES} bytes, "
        f"{_MAX_PROJECT_ENTRIES} entries). Admission will refuse this run at "
        "docker_staging.py; this probe reports and does not gate. Shrink the workload's "
        "dataset, not the repository."
    )


def _dataset_relative_from_config(
    project_root: Path, commit: str, config_relative: str
) -> str | None:
    """The config's own `dataset.ref`, read at the locked commit.

    This follows the workload contract section 21.3 documents, not staging
    logic: the ref is a literal in a committed file, and admission reads the
    same value. Returns None rather than guessing, so an unresolvable dataset is
    reported as unresolved instead of being completed by inference.
    """
    completed = _git(project_root, "cat-file", "-p", f"{commit}:{config_relative}")
    if completed.returncode != 0:
        return None
    try:
        document = json.loads(completed.stdout)
    except ValueError:
        return None
    if type(document) is not dict:
        return None
    dataset = document.get("dataset")
    if type(dataset) is not dict:
        return None
    reference = dataset.get("ref")
    if type(reference) is not str:
        return None
    return _project_relative(reference)


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

# The REAL stage parent, the one `docker_staging.py:1699-1700` creates with the
# same idempotent call. Probing it rather than a scratch directory removes an
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

    The chain this creates is EXPECTED to be inherited, and that is not a fault
    (blocker B-11, section 20.10, task #160). The `mkdir` below is an ordinary
    pathlib call, so on Windows `.synaptic` and everything under it carries the
    access list it inherits from the project directory. After a `--probe-only`
    pass that is exactly the state the Host will find. It is not a failure and
    it needs no operator action: the Host REPAIRS the chain at activation, from
    the never-protected state only, and only through the path that creates the
    storage (`for_docker` repairs; `initialize` does not). Section 20.16 row 1
    judges the run against that design.

    Do NOT "fix" this by pre-protecting `.synaptic` here. Two reasons, both
    measured rather than argued. Writing a protected list from this script would
    change the access list of the model inventory's PARENT before the inventory
    is written, which is the one arm of B-11-M1 (task #165) that was never
    measured, and it would alter the shape of the only thing that worked in run
    5. And the path-based form of that call is DESTRUCTIVE: section 20.17 row
    20.1a records that it empties the access list of every child, leaving them
    unreadable to the owner, to WSL and to the container, while the Host's own
    validator still accepts the root -- a silent failure with a green check.
    """
    stage_parent = project_root.joinpath(*_STAGE_PARENT_PARTS)
    existed = stage_parent.is_dir()
    try:
        # The identical idempotent call the staging code makes at
        # `docker_staging.py:1699-1700`. Matching it is the point: this probe
        # measures the directory the run will actually use.
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


# --------------------------------------------------------------------------
# B-10 evidence (architecture section 19.14)
# --------------------------------------------------------------------------

# Inside a stage the artifact root is `<stage>/artifacts`
# (`docker_staging.py:1755`), and it holds five directories
# (`_ARTIFACT_DIRECTORY_NAMES` at `:49`). Four of them must be EMPTY or
# `_verify_artifact_topology` raises "artifact writable directory is not empty"
# (`:1473-1478`); `cache` is the model inventory and is exempt.
_ARTIFACT_ROOT_NAME = "artifacts"

# `state` first because section 19.14 names it as the directory to watch. The
# other three are reported too: the verifier fails on ANY of them, so evidence
# about `state` alone could mislead if `tmp` is what actually filled.
_WRITABLE_ARTIFACT_NAMES = ("state", "artifacts", "tmp", "tracking")


def _find_stage_directories(project_root: Path) -> list[Path]:
    """Every staged run directory under the stage parent.

    A stage is identified by carrying an `artifacts` child, which is what
    `docker_staging.py:1755` builds. `p8-probe` is excluded by name: it is this
    driver's own probe directory (section 18.11), normally removed at once, and
    mistaking it for a stage would report emptiness for a directory the run
    never touches.
    """
    parent = project_root.joinpath(*_STAGE_PARENT_PARTS)
    try:
        candidates = sorted(entry for entry in parent.iterdir() if entry.is_dir())
    except OSError:
        return []
    return [
        entry for entry in candidates
        if entry.name != _P8_PROBE_DIRECTORY
        and (entry / _ARTIFACT_ROOT_NAME).is_dir()
    ]


def _report_b10_evidence_before_cut(project_root: Path, cut: int) -> None:
    """Record whether the stage's writable roots are non-empty BEFORE the cut.

    Blocker B-10 (section 19, task #137) is proven by reading and has never been
    observed: staging re-verifies on every cut, so the first cut issued after the
    trainer writes under `/artifacts` would fail `START_UNAVAILABLE`. Section
    19.14 closes it on evidence, and this is half of that evidence. Read-only;
    it changes nothing about what the cut does.
    """
    stages = _find_stage_directories(project_root)
    if not stages:
        flags = " ".join(f"{name}_nonempty=unknown" for name in _WRITABLE_ARTIFACT_NAMES)
        print(f"B10-EVIDENCE cut={cut} stage=NONE {flags}")
        return
    for stage in stages:
        root = stage / _ARTIFACT_ROOT_NAME
        flags = []
        for name in _WRITABLE_ARTIFACT_NAMES:
            try:
                with os.scandir(root / name) as entries:
                    value = "true" if any(entries) else "false"
            except OSError:
                value = "unreadable"
            flags.append(f"{name}_nonempty={value}")
        print(f"B10-EVIDENCE cut={cut} stage={stage} {' '.join(flags)}")


def _report_b10_evidence_after_cut(cut: int, exit_code: int, result: dict) -> None:
    """Record the result code the cut returned, the other half of 19.14."""
    print(
        f"B10-EVIDENCE cut={cut} result={result.get('code')} "
        f"status={result.get('status')} exit={exit_code}"
    )


# --------------------------------------------------------------------------
# First-container capture (section 22.11 row 4, 23.5 row 2, follow-up #219)
# --------------------------------------------------------------------------
#
# Run 8 created the first container this path has ever produced and the capture
# still missed it live. Two independent causes, and the instrument has to answer
# both or it repeats the failure:
#
#   1. the poller filtered `docker ps` on the image field containing `unsloth`,
#      but the prepared composition creates from a DIGEST-PINNED reference which
#      never prints that repository tag, so the filter matched nothing;
#   2. the container lived 0.7 s, under a 1 s sampling window.
#
# Cause 2 is why this subscribes to `docker events` instead of polling: an event
# stream has no sampling window. Cause 1 is the more important one, because a
# narrowing applied UPSTREAM turns a miss into silence, and silence read exactly
# like "no container yet". So the SERVER-side filter stays as broad as the ruling
# allows -- `--filter type=container` and nothing else -- and every narrowing
# happens here, where a non-match can be COUNTED and PRINTED. Zero matches out of
# N container events looks nothing like zero events, which is the whole point.
#
# Keys, per the ruling on #229. The container name prefix is primary: run 8's
# container was `synaptic-95d3dbda863cb9bdd7db30b4` and `--name` comes from
# `control_private.py:405`. The Host ALSO sets fifteen labels under
# `ai.synapticlabs.tuner.v1.` (`control_model.py:18-25`, emitted at `:414-417`),
# which arrive as extra `Actor.Attributes` keys, so a container whose name
# convention ever changes is still matched on the label. Which key matched is
# reported. Neither key is ever sent to the server.
#
# The instrument is an OBSERVER. It adds no Host verb, never calls `docker rm`,
# does not touch the prepared command or the composition, and cannot fail the
# run: every path here reports and returns, and a stream that will not start is
# the `capture-unavailable` tag. The run's own result codes remain the
# acceptance; this is evidence.

_CONTAINER_NAME_PREFIX = "synaptic-"
_HOST_LABEL_PREFIX = "ai.synapticlabs.tuner.v1."
_CAPTURE_HEAD_LINES = 50
_CAPTURE_TAIL_LINES = 50
_CAPTURE_SHOWN_UNPARSEABLE = 5
_CAPTURE_SHOWN_OTHERS = 10
_CAPTURE_STOP_SECONDS = 10
_CENSUS_SHOWN_IDS = 10
_CENSUS_TIMEOUT_SECONDS = 60


def _capture_matched_key(attributes: dict) -> tuple[str, str] | None:
    """Which key identifies this as ours, or None.

    `name` first because it is the ruling's primary key; the Host label prefix
    second. Sorted so the reported key is stable across runs.
    """
    name = attributes.get("name")
    if isinstance(name, str) and name.startswith(_CONTAINER_NAME_PREFIX):
        return "name", name
    for key in sorted(attributes):
        if key.startswith(_HOST_LABEL_PREFIX):
            return key, str(attributes[key])
    return None


def _parse_container_events(text: str) -> tuple[dict, int, list[str], list[str]]:
    """Parse an events stream tolerantly.

    Returns (matched by container id, container events parsed, one line per
    non-matching event, unparseable lines).

    Tolerant on purpose. The child's stderr is merged into the same file, so a
    `Cannot connect to the Docker daemon` line lands here as an unparseable line
    and gets REPORTED rather than swallowed -- which is the diagnosis an operator
    needs, and is cheaper than a second file. A malformed line must never cost
    the well-formed lines around it.
    """
    matched: dict[str, dict] = {}
    parsed = 0
    others: list[str] = []
    unparseable: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            unparseable.append(line)
            continue
        if not isinstance(record, dict):
            unparseable.append(line)
            continue
        parsed += 1
        actor = record.get("Actor")
        actor = actor if isinstance(actor, dict) else {}
        attributes = actor.get("Attributes")
        attributes = attributes if isinstance(attributes, dict) else {}
        identifier = str(actor.get("ID") or record.get("id") or "")
        action = str(record.get("Action") or record.get("status") or "?")
        hit = _capture_matched_key(attributes)
        if hit is None:
            others.append(
                f"{action} id={identifier[:12] or '?'} "
                f"name={attributes.get('name', '?')}"
            )
            continue
        entry = matched.setdefault(
            identifier,
            {
                "id": identifier,
                "name": str(attributes.get("name", "")),
                "image": str(attributes.get("image", "")),
                "matched_on": hit[0],
                "actions": [],
            },
        )
        entry["actions"].append(action)
    return matched, parsed, others, unparseable


def _container_census(docker: str, endpoint: str) -> tuple[set[str] | None, str | None]:
    """Every container id the daemon holds, or None plus the reason it is unknown.

    Read-only, unfiltered, id-only. Unfiltered for the same reason the event
    stream is (section 22.11 row 4): a narrowing applied on the SERVER turns a
    miss into silence, and a filtered census that answers nothing looks exactly
    like a daemon holding no containers. `-a` because the container this exists
    to notice may already have exited -- run 8's lived 0.7 s. Never raises; a
    failure degrades exactly like `capture-unavailable` and the run continues.
    """
    argv = [
        docker, "--host", endpoint, "ps", "-a", "--no-trunc", "--format", "{{.ID}}",
    ]
    try:
        completed = _run(argv, timeout=_CENSUS_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError) as error:
        return None, f"{type(error).__name__}: {error}"
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip() or "no output"
        return None, f"the census exited {completed.returncode}: {detail}"
    identifiers = {
        line.strip() for line in (completed.stdout or "").splitlines() if line.strip()
    }
    return identifiers, None


def _start_container_capture(docker: str, endpoint: str) -> dict:
    """Subscribe to container events BEFORE the cut that creates the container.

    `docker events` never exits on its own, so it cannot go through `_run`, which
    blocks. It needs `Popen`, and its stdout goes to a FILE rather than a pipe:
    nothing has to drain a pipe while cut 1 blocks for minutes, so there is no
    buffer to deadlock on.

    `--since` is a timestamp taken HERE, one second back, because `Popen` returns
    before `docker.exe` has connected to the daemon. A create event landing in
    that gap would otherwise be lost -- the same class of miss the run 8 poller
    had, arriving by a different door.

    Never raises. A stream that will not start is recorded as `capture-unavailable`
    and the run continues.
    """
    # The census FIRST, so `--since` is taken as late as possible: `ps` is a
    # child process, and the window between that timestamp and `Popen` is the
    # one gap the stream cannot see.
    census_before, census_error = _container_census(docker, endpoint)
    since = str(int(time.time()) - 1)
    argv = [
        docker, "--host", endpoint, "events",
        "--since", since,
        "--filter", "type=container",
        "--format", "{{json .}}",
    ]
    capture: dict = {
        "argv": argv, "since": since,
        "path": None, "process": None, "stream": None, "unavailable": None,
        "census_before": census_before, "census_error": census_error,
    }
    try:
        handle, path = tempfile.mkstemp(
            prefix="host-docker-run-events-", suffix=".jsonl"
        )
        os.close(handle)
        capture["path"] = Path(path)
        capture["stream"] = open(path, "wb")
        print(f"    $ {subprocess.list2cmdline(argv)}", flush=True)
        capture["process"] = subprocess.Popen(
            argv, stdout=capture["stream"], stderr=subprocess.STDOUT,
        )
    except (OSError, ValueError) as error:
        capture["unavailable"] = f"{type(error).__name__}: {error}"
        stream = capture.get("stream")
        if stream is not None:
            try:
                stream.close()
            except OSError:
                pass
            capture["stream"] = None
        print(
            "CAPTURE capture-unavailable: the container event stream could not "
            f"start ({capture['unavailable']}). The run continues; the capture is "
            "evidence, not acceptance"
        )
        return capture
    print(
        f"CAPTURE listening on {endpoint} since={since} "
        "filter=type=container (server-side); the name prefix "
        f"{_CONTAINER_NAME_PREFIX!r} and the label prefix "
        f"{_HOST_LABEL_PREFIX!r} are matched HERE, never sent to the server. "
        f"stream file: {capture['path']}"
    )
    return capture


def _stop_container_capture(capture: dict) -> None:
    """End the subscription. Never raises, never blocks the run for long."""
    process = capture.get("process")
    if process is not None:
        try:
            process.terminate()
            process.wait(timeout=_CAPTURE_STOP_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
                process.wait(timeout=_CAPTURE_STOP_SECONDS)
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f"    NOTE could not stop the event stream: {error}")
        except OSError as error:
            print(f"    NOTE could not stop the event stream: {error}")
    stream = capture.get("stream")
    if stream is not None:
        try:
            stream.close()
        except OSError:
            pass
        capture["stream"] = None


def _replay_container_events(docker: str, endpoint: str, since: str) -> str:
    """Re-read the same window with a bounded, self-terminating command.

    The fallback for one specific failure: terminating the streaming child loses
    whatever it had buffered but not yet flushed. `--until` in the past makes
    `docker events` print the window and exit on its own, so no signal is
    involved and nothing depends on flush-on-terminate. Issued ONLY when the
    stream yielded no match, so it costs one command in the case that would
    otherwise repeat run 8.
    """
    argv = [
        docker, "--host", endpoint, "events",
        "--since", since,
        "--until", str(int(time.time())),
        "--filter", "type=container",
        "--format", "{{json .}}",
    ]
    try:
        completed = _run(argv, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"    NOTE bounded event replay failed: {error}")
        return ""
    if completed.returncode != 0:
        print(
            f"    NOTE bounded event replay exited {completed.returncode}: "
            f"{(completed.stderr or '').strip() or 'no output'}"
        )
    return completed.stdout or ""


def _report_captured_container(docker: str, endpoint: str, entry: dict) -> None:
    """Read the container's record and its stderr after the cut.

    Both survive the container's exit because the Host verb set is version,
    create, start, stop, inspect, ps and logs -- there is no `rm`, so nothing
    removes the container and a 0.7 s life is not a reason to lose its record.
    """
    identifier = entry["id"]
    print(
        f"CAPTURE container id={identifier[:12]} name={entry['name'] or '?'} "
        f"matched_on={entry['matched_on']} events={','.join(entry['actions'])}"
    )
    try:
        completed = _run(
            [docker, "--host", endpoint, "inspect", "--format", "{{json .}}",
             identifier],
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"    NOTE inspect failed: {error}")
        completed = None
    if completed is not None and completed.returncode == 0:
        try:
            record = json.loads(completed.stdout.strip() or "{}")
        except ValueError:
            record = {}
        state = record.get("State") if isinstance(record.get("State"), dict) else {}
        config = record.get("Config") if isinstance(record.get("Config"), dict) else {}
        print(
            f"    inspect name={record.get('Name', '?')} "
            f"image={record.get('Image', '?')} "
            f"config_image={config.get('Image', '?')}"
        )
        print(
            f"    inspect status={state.get('Status', '?')} "
            f"exit={state.get('ExitCode', '?')} "
            f"started={state.get('StartedAt', '?')} "
            f"finished={state.get('FinishedAt', '?')}"
        )
        if state.get("Status") == "running":
            print(
                "    NOTE the container is still running, so the exit code above "
                "is not final; read it again after the next cut"
            )
    elif completed is not None:
        print(
            f"    NOTE inspect exited {completed.returncode}: "
            f"{(completed.stderr or '').strip() or 'no output'}"
        )
    try:
        completed = _run([docker, "--host", endpoint, "logs", identifier], timeout=180)
    except (OSError, subprocess.SubprocessError) as error:
        print(f"    NOTE logs failed: {error}")
        return
    if completed.returncode != 0:
        print(f"    NOTE logs exited {completed.returncode}")
    lines = (completed.stderr or "").splitlines()
    print(f"    stderr lines: {len(lines)} (stdout lines: {len((completed.stdout or '').splitlines())})")
    if len(lines) <= _CAPTURE_HEAD_LINES + _CAPTURE_TAIL_LINES:
        shown = [(index, line) for index, line in enumerate(lines, start=1)]
    else:
        shown = [(index, line) for index, line in enumerate(lines[:_CAPTURE_HEAD_LINES], start=1)]
        shown.append((0, f"... {len(lines) - _CAPTURE_HEAD_LINES - _CAPTURE_TAIL_LINES} line(s) omitted ..."))
        shown.extend(
            (len(lines) - _CAPTURE_TAIL_LINES + offset + 1, line)
            for offset, line in enumerate(lines[-_CAPTURE_TAIL_LINES:])
        )
    for index, line in shown:
        print(f"    stderr|{index if index else '':>5} {line}")


def _report_census_verdict(
    before: set[str] | None, after: set[str] | None, error: str | None,
    parsed: int, matched_count: int,
) -> None:
    """Say which of the three worlds this is, and never guess between two.

    Run 9's reading had two states and the world has three. `matched=0` with
    `parsed>0` was reported as a MISS, which sent the reader to the match keys;
    but `parsed` counts every container event in the window INCLUDING this
    driver's own `--rm` probes, so a run that died before composition read as a
    key failure. Run 9 was exactly that. The census diff separates them: a
    census that did not grow means no container was ever created, which is a
    question about the Host envelope, not about the keys (section 24.7).
    """
    if before is None or after is None:
        print(
            f"CAPTURE verdict=census-unavailable ({error}). Without a census "
            f"the reading is ambiguous: {parsed} container event(s) were seen "
            f"and {matched_count} matched, which is EITHER a run that never "
            "composed a container OR a match that failed"
        )
        return
    created = sorted(after - before)
    counts = f"census before={len(before)} after={len(after)} created={len(created)}"
    if matched_count:
        print(
            f"CAPTURE verdict=matched {matched_count} container(s) captured. "
            f"{counts}"
        )
        return
    if not created:
        print(
            f"CAPTURE verdict=no-container {counts}. Nothing was created at "
            "all, so this is NOT a match failure: the run stopped before "
            "composition. Read the Host envelope and the `synaptic-host:` "
            f"cause line, not the match keys; the {parsed} event(s) in the "
            "window are this driver's own probes"
        )
        return
    print(
        f"CAPTURE verdict=match-failed {counts}. A container WAS created and no "
        "key matched it: suspect the container name prefix or the label field "
        "paths, and read the 'other|' lines above for the names that arrived"
    )
    for identifier in created[:_CENSUS_SHOWN_IDS]:
        print(f"    created| {identifier}")
    if len(created) > _CENSUS_SHOWN_IDS:
        print(f"    created| ... {len(created) - _CENSUS_SHOWN_IDS} more not shown")


def _report_first_container(docker: str, endpoint: str, capture: dict) -> None:
    """Turn the captured stream into the 22.11 row 4 reading. Never raises."""
    if capture.get("unavailable") is not None:
        print(
            "CAPTURE capture-unavailable: no event stream was running for cut 1 "
            f"({capture['unavailable']})"
        )
        return
    path = capture.get("path")
    text = ""
    if path is not None:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            print(f"    NOTE could not read the event stream file: {error}")
    matched, parsed, others, unparseable = _parse_container_events(text)
    print(
        f"CAPTURE container events parsed={parsed} matched={len(matched)} "
        f"other={len(others)} unparseable={len(unparseable)} "
        f"stream file: {path}"
    )
    for line in others[:_CAPTURE_SHOWN_OTHERS]:
        print(f"    other| {line}")
    if len(others) > _CAPTURE_SHOWN_OTHERS:
        print(f"    other| ... {len(others) - _CAPTURE_SHOWN_OTHERS} more not shown")
    for line in unparseable[:_CAPTURE_SHOWN_UNPARSEABLE]:
        print(f"    unparseable| {line}")
    if len(unparseable) > _CAPTURE_SHOWN_UNPARSEABLE:
        print(
            f"    unparseable| ... {len(unparseable) - _CAPTURE_SHOWN_UNPARSEABLE} "
            "more not shown"
        )
    if not matched:
        replayed = _replay_container_events(docker, endpoint, capture["since"])
        if replayed:
            matched, parsed, others, unparseable = _parse_container_events(replayed)
            print(
                f"CAPTURE bounded replay parsed={parsed} matched={len(matched)} "
                f"other={len(others)} unparseable={len(unparseable)}"
            )
    # The post-cut census. This runs in the `finally` beside the stop, so it
    # reads the daemon after the only cut that can have created the container.
    census_after, census_error = _container_census(docker, endpoint)
    _report_census_verdict(
        capture.get("census_before"), census_after,
        capture.get("census_error") or census_error, parsed, len(matched),
    )
    for entry in matched.values():
        _report_captured_container(docker, endpoint, entry)


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
        if cut == 2:
            # Section 19.14: the stage is fresh at run 5, so cut 1 tells us
            # nothing. Cut 2 is the first observe cut after submit and the one
            # that closes B-10. An EMPTY `state` here is a DEFERRAL, not a pass:
            # the trainer may simply have buffered and not written yet.
            print("           section 19.14: cut 2 is the cut that closes B-10. "
                  "state non-empty with a code other than START_UNAVAILABLE "
                  "confirms the fix; state empty is a DEFERRAL, not a pass.")
        capture: dict | None = None
        if cut == 1:
            # Started BEFORE the cut that creates the container, because cut 1
            # is the only cut that can create it and run 8's container lived
            # 0.7 s (section 22.11 row 4, 23.5 row 2, follow-up #219).
            capture = _start_container_capture(args.docker, args.endpoint)
        _report_b10_evidence_before_cut(project_root, cut)
        try:
            exit_code, result = _one_cut(python_executable, project_root, args)
        finally:
            # In the `finally` so a cut that times out still yields its capture:
            # a run that dies at cut 1 is exactly the run whose container nobody
            # has ever seen. Neither call raises, so neither can mask the cut's
            # own failure.
            if capture is not None:
                _stop_container_capture(capture)
                _report_first_container(args.docker, args.endpoint, capture)
        _report_b10_evidence_after_cut(cut, exit_code, result)
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
        # Immediately after P2 and before everything else. P2 proves the
        # endpoint CONSTANT; P10 proves the endpoint ANSWERS, which `docker
        # context inspect` cannot (section 22.7, measurement #203). Placing it
        # here means a stopped engine costs one command instead of a full
        # precondition sweep including P7's network read.
        _check_p10_daemon_alive(args.docker, args.endpoint)
        _check_p3_drive_letter_root(project_root)
        # After P3, which has just proven the root's SHAPE, and before P5/P6/P7,
        # which read that tree's CONTENT. Knowing which code a run will import
        # should precede reading what it is configured to do (task #215).
        _check_p11_package_resolves_under_project_root(args.python, project_root)
        profile = _load_profile(project_root)
        distro, drive_mount_root = _check_p5_drive_mount_root(profile)
        _check_p6_config_is_committed(project_root, args.config)
        _check_p7_branch_is_publishable(project_root)
        # After P7, which has just proven HEAD is the published commit, and
        # before the bind probe. Reports the staged project volume (blocker
        # B-12, section 21.13); it never gates.
        _check_p9_locked_project_inputs(project_root, args.config)
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
