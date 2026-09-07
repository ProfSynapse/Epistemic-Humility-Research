#!/usr/bin/env python3
"""G5: the isolation triple exists in a dedicated environment, the Secret carries
the worker key, and the Host key was rotated before it.

Gate G5 of docs/architecture/prepared-path-alpine-diagnostic.md 29.12, standing
on ruling (7) in 29.9 and ruling (5) in 29.7.

Why the gate is shaped as a checklist and not as a probe
--------------------------------------------------------
G5 has three clauses and they are knowable in three different ways.

  * ISOLATION is a CONFIGURATION property and is fully decidable offline. Ruling
    (5) settled that the app name is a module constant (`APP_NAME` in
    deployment_v1.py) and cannot vary from Host configuration, so isolation is
    carried entirely by the provider environment and by the three object names
    beside it. All four live in `training/providers/modal.json`, so this script
    reads them and checks they name a fresh set.

  * EXISTENCE is a PROVIDER property. Nothing on this machine can decide whether
    an environment, two Volumes and a Secret exist in the account. That needs
    credentials and a call, so it is off by default: without --check the script
    prints exactly what it would ask and stops. It asks only for existence BY
    NAME. It never reads a Secret's contents.

  * ROTATION is an OPERATOR ACT and no probe can see it. Reading a key to prove
    it changed would defeat the purpose. Rotation is therefore recorded as a
    dated attestation the operator passes in, and the script's job is to refuse
    to report the gate satisfied without it.

Credential values are read only to construct the explicit SDK client. They are
never printed, measured, written to a file, or placed in argv.

The offline half checks four things
-----------------------------------
S1  The four Modal object names in the configuration are all distinct from the
    four the existing deployment uses, so the smoke touches nothing that exists.
S2  The Secret's declared key set is exactly the two ruling (7) fixes. The Host
    refuses any other set at load time (modal_provider.py:168), so a violation
    here would fail before the submit; checking it in the gate names the cause
    up front instead of after a paid step.
S3  The standing safety properties of the worker function are unrelaxed, read
    from the blob at the pinned engine sha rather than from the worktree.
S4  A rotation attestation was supplied.

Usage
-----
    python3 g5_isolation_triple.py --rotation-recorded-at 2026-09-06T00:00:00Z
    python3 g5_isolation_triple.py --rotation-recorded-at ... --check --submit-image <tag>

`--check` performs the existence-by-name lookups and needs credentials in the
environment. Without it the script makes no Modal call whatsoever.

The Host performs the Git-dependent offline checks first. Only if they pass,
--check starts a retained submit container for SDK-1.5.4 existence lookups.
The lookup-only subprocess reports existence, never overall gate satisfaction.
Live account behavior still requires operator-confirmed validation.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ruling (7): the Secret's key set is fixed. modal_provider.py refuses any other
# set when the host config loads.
REQUIRED_SECRET_KEYS = ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY")

# Ruling (7) property 3: standing safety properties of the worker function,
# unrelaxed for this lane. Each is a literal in the app.function decorator.
STANDING_SAFETY_LITERALS = (
    "retries=0",
    "restrict_modal_access=True",
    "single_use_containers=True",
    "include_source=False",
)

WORKER_MODULE = "tuner/execution/providers/modal/deployment_v1.py"

# The names the existing deployment uses. The smoke must not name any of them.
# Ruling (9) in 29.11 asks for a configuration test that prevents this overlap;
# S1 is that test in gate form.
EXISTING_DEPLOYMENT_NAMES = frozenset(
    {
        "main",
        "synaptic-training-control-v1",
        "synaptic-training-artifacts-v1",
        "synaptic-training-runtime-v1",
    }
)

WINDOWS_GIT = Path("/mnt/c/Program Files/Git/cmd/git.exe")
WINDOWS_DOCKER = Path("/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe")
EXACT_MODAL_SDK_VERSION = "1.5.4"
LOOKUP_PASS = "G5 LOOKUP PASS"
LOOKUP_FAILURES = frozenset({
    "configuration", "credentials", "sdk-import", "sdk-version", "client",
    "environment", "control-volume", "artifact-volume", "secret",
})


def credentials_present() -> bool:
    return all(os.environ.get(name, "").strip()
               for name in ("MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET"))


def lookup_only(config: dict) -> int:
    """Look up only the four configured names; never enumerate or create."""
    def fail(stage: str) -> int:
        emit(f"G5 LOOKUP FAIL {stage}")
        return 1

    try:
        environment = config["environment_name"]
        control = config["volumes"]["control_name"]
        artifact = config["volumes"]["artifact_name"]
        secret = config["runtime_secret"]["name"]
        names = (environment, control, artifact, secret)
        if (not all(isinstance(name, str) and name.strip() for name in names)
                or len(set(names)) != 4
                or set(names) & EXISTING_DEPLOYMENT_NAMES
                or tuple(config["runtime_secret"]["required_keys"]) != REQUIRED_SECRET_KEYS):
            return fail("configuration")
    except (KeyError, TypeError):
        return fail("configuration")
    if not credentials_present():
        return fail("credentials")
    try:
        sdk = importlib.import_module("modal")
    except Exception:
        return fail("sdk-import")
    if getattr(sdk, "__version__", None) != EXACT_MODAL_SDK_VERSION:
        return fail("sdk-version")
    try:
        client = sdk.Client.from_credentials(
            os.environ["MODAL_TOKEN_ID"], os.environ["MODAL_TOKEN_SECRET"]
        )
    except Exception:
        return fail("client")
    # Secret.from_name has no create_if_missing parameter. required_keys
    # validates the declared key names without reading Secret contents.
    lookups = (
        ("environment", sdk.Environment.from_name, environment,
         {"create_if_missing": False, "client": client}),
        ("control-volume", sdk.Volume.from_name, control,
         {"environment_name": environment, "create_if_missing": False, "client": client}),
        ("artifact-volume", sdk.Volume.from_name, artifact,
         {"environment_name": environment, "create_if_missing": False, "client": client}),
        ("secret", sdk.Secret.from_name, secret,
         {"environment_name": environment, "required_keys": list(REQUIRED_SECRET_KEYS), "client": client}),
    )
    for stage, factory, name, kwargs in lookups:
        try:
            factory(name, **kwargs).hydrate()
        except Exception:
            return fail(stage)
    emit(LOOKUP_PASS)
    return 0


def run_lookup_container(config_path: Path, image: str, docker: str, endpoint: str) -> bool:
    """Keep Git on the Host and pass only credential names into Docker argv."""
    def daemon_path(path: Path) -> str:
        path = path.resolve()
        if docker.lower().endswith(".exe") and os.name != "nt":
            return subprocess.check_output(
                ["wslpath", "-w", str(path)], stdin=subprocess.DEVNULL, text=True
            ).strip()
        return str(path)

    try:
        # Preserve the skill-relative layout so argparse defaults resolve in
        # the worker too. Only this script and the selected config are mounted.
        script = "/workspace/.skills/host-modal-run/scripts/g5_isolation_triple.py"
        command = [docker, "--host", endpoint, "run", "--pull=never",
                   "-e", "MODAL_TOKEN_ID", "-e", "MODAL_TOKEN_SECRET",
                   "-v", f"{daemon_path(Path(__file__))}:{script}:ro",
                   "-v", f"{daemon_path(config_path)}:/workspace/modal.json:ro",
                   "-w", "/workspace", image, "python3", "-B", script,
                   "--lookup-only", "--config", "/workspace/modal.json"]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True, check=False)
    except (OSError, subprocess.SubprocessError):
        emit("FAIL existence-container: could not launch lookup process")
        return False
    output = completed.stdout.strip()
    if completed.returncode == 0 and output == LOOKUP_PASS:
        emit("PASS existence-container: all four named lookups resolved with SDK 1.5.4")
        return True
    # SDK/Docker output is untrusted and may contain credentials. Render only
    # the closed stage tokens, never raw stdout, stderr or exception messages.
    if output in {f"G5 LOOKUP FAIL {stage}" for stage in LOOKUP_FAILURES}:
        emit(output)
    else:
        emit("FAIL existence-container: lookup process failed or returned an invalid result")
    return False


def emit(line: str) -> None:
    print(line)


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def check(self, tag: str, ok: bool, detail: str) -> bool:
        emit(f"{'PASS' if ok else 'FAIL'} {tag}  {detail}")
        if not ok:
            self.failures.append(tag)
        return ok


def resolve_git_binary(engine_root: Path) -> str:
    parts = engine_root.resolve().parts
    on_drvfs = len(parts) > 2 and parts[1] == "mnt" and len(parts[2]) == 1
    if on_drvfs and WINDOWS_GIT.is_file():
        return str(WINDOWS_GIT)
    return "git"


def missing_safety_literals(source: str) -> list[str]:
    """Validate literal settings on the exact pinned worker's decorator.

    Fail closed on missing/ambiguous structure or expanded keyword arguments.
    Comments, other functions and sdk.App settings are not worker evidence.
    This parses source without importing or executing the deployment module.
    """
    failed = list(STANDING_SAFETY_LITERALS)
    try:
        module = ast.parse(source)
    except (SyntaxError, ValueError):
        return failed
    builders = [node for node in module.body
                if isinstance(node, ast.FunctionDef) and node.name == "build_modal_deployment"]
    if len(builders) != 1:
        return failed
    workers = [node for node in builders[0].body
               if isinstance(node, ast.FunctionDef) and node.name == "run_sft_v1"]
    if len(workers) != 1 or len(workers[0].decorator_list) != 1:
        return failed
    decorator = workers[0].decorator_list[0]
    if not (isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "app" and decorator.func.attr == "function"):
        return failed
    keywords = {item.arg: item.value for item in decorator.keywords}
    if None in keywords or len(keywords) != len(decorator.keywords) or decorator.args:
        return failed
    missing = []
    for literal in STANDING_SAFETY_LITERALS:
        name, text = literal.split("=", 1)
        expected = ast.literal_eval(text)
        actual = keywords.get(name)
        if not (isinstance(actual, ast.Constant)
                and type(actual.value) is type(expected) and actual.value == expected):
            missing.append(literal)
    return missing


def read_worker_blob(repo_root: Path, engine_root: Path) -> str | None:
    """Read the worker module at the commit the superproject pins.

    Read from the blob, not from the worktree, for the same reason G3 does: on a
    Windows checkout the worktree bytes carry translated line endings, and the
    worktree can also sit on a commit other than the pin.
    """
    git = resolve_git_binary(engine_root)
    try:
        listing = subprocess.run(
            [git, "-c", "safe.directory=*", "ls-tree", "HEAD", "--", "synaptic-tuner"],
            cwd=str(repo_root),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        ).stdout.decode()
        sha = ""
        for line in listing.splitlines():
            fields = line.split()
            if len(fields) >= 3 and fields[0] == "160000":
                sha = fields[2]
        if not sha:
            return None
        blob = subprocess.run(
            [git, "-c", "safe.directory=*", "cat-file", "blob", f"{sha}:{WORKER_MODULE}"],
            cwd=str(engine_root),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return blob.decode("utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "training" / "providers" / "modal.json",
        help="the Modal host configuration that names the isolation triple",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help=(
            "superproject working tree that pins the engine. Derived from THIS"
            " script's location, not from --config: pointing --config at a copy"
            " elsewhere would otherwise silently make S3 unmeasurable and read"
            " as a defect in the engine."
        ),
    )
    parser.add_argument(
        "--rotation-recorded-at",
        default=None,
        help=(
            "ISO-8601 instant at which the operator rotated the Host key, which"
            " must precede the smoke (29.3, 29.9 property 1)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="perform existence-by-name lookups against the provider (needs credentials)",
    )
    parser.add_argument("--submit-image", help="locally available pinned submit image; required by --check")
    parser.add_argument("--docker", default=(str(WINDOWS_DOCKER) if WINDOWS_DOCKER.is_file()
                                           else shutil.which("docker.exe") or "docker"))
    parser.add_argument("--endpoint", default="npipe:////./pipe/dockerDesktopLinuxEngine")
    parser.add_argument("--lookup-only", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.lookup_only:
        if args.check:
            parser.error("--lookup-only cannot be combined with --check")
        try:
            config = json.loads(args.config.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            emit("G5 LOOKUP FAIL configuration")
            return 1
        return lookup_only(config)
    if args.check and (not args.submit_image or args.submit_image.startswith("-")):
        parser.error("--check requires --submit-image naming an existing local image")

    report = Report()
    config_path: Path = args.config
    repo_root: Path = args.repo_root.resolve()
    engine_root = repo_root / "synaptic-tuner"

    if not config_path.is_file():
        emit(f"FAIL configuration not found: {config_path}")
        return 2

    config = json.loads(config_path.read_text(encoding="utf-8"))
    environment_name = config["environment_name"]
    control_name = config["volumes"]["control_name"]
    artifact_name = config["volumes"]["artifact_name"]
    secret_name = config["runtime_secret"]["name"]
    declared_keys = tuple(config["runtime_secret"]["required_keys"])

    emit("G5 isolation triple (29.7 ruling 5, 29.9 ruling 7, 29.12)")
    emit(f"configuration : {config_path}")
    emit("")
    emit("The four names this smoke will use:")
    emit(f"  provider environment : {environment_name}")
    emit(f"  control volume       : {control_name}")
    emit(f"  artifact volume      : {artifact_name}")
    emit(f"  runtime named object : {secret_name}")
    emit("")
    emit(
        "The app name is not in this list on purpose. Ruling (5) settled that it"
    )
    emit(
        "is a module constant and cannot vary from Host configuration, so"
    )
    emit("isolation is carried by the provider environment alone.")
    emit("")

    # ---- S1 no overlap with the existing deployment ----------------------
    chosen = {environment_name, control_name, artifact_name, secret_name}
    overlap = sorted(chosen & EXISTING_DEPLOYMENT_NAMES)
    report.check(
        "S1 fresh-names",
        not overlap and len(chosen) == 4,
        f"overlap with the existing deployment: {overlap or 'none'};"
        f" distinct names: {len(chosen)} of 4",
    )

    # ---- S2 the fixed key set --------------------------------------------
    report.check(
        "S2 fixed-key-set",
        declared_keys == REQUIRED_SECRET_KEYS,
        f"declared key set matches the fixed set: {declared_keys == REQUIRED_SECRET_KEYS}"
        f" ({len(declared_keys)} declared, {len(REQUIRED_SECRET_KEYS)} required)",
    )
    emit(
        "     the evidence MAC key is the WORKER key. Ruling (7) property 1: the"
    )
    emit(
        "     Host key is never placed here, and it is rotated before the smoke."
    )

    # ---- S3 standing safety properties, read at the pin -------------------
    source = read_worker_blob(repo_root, engine_root)
    if source is None:
        report.check(
            "S3 standing-safety",
            False,
            "could not read the worker module at the pinned engine sha",
        )
    else:
        missing = missing_safety_literals(source)
        report.check(
            "S3 standing-safety",
            not missing,
            f"unrelaxed at the pin: {len(STANDING_SAFETY_LITERALS) - len(missing)}"
            f" of {len(STANDING_SAFETY_LITERALS)}; missing: {missing or 'none'}",
        )
        emit(
            "     the image is digest-pinned in the same decorator; egress is"
        )
        emit(
            "     unrestricted at this pin by user ruling, so no network claim is"
        )
        emit("     made here in either direction.")

    # ---- S4 the rotation attestation --------------------------------------
    report.check(
        "S4 rotation-attested",
        bool(args.rotation_recorded_at),
        f"operator attestation supplied: {bool(args.rotation_recorded_at)}"
        + (f" at {args.rotation_recorded_at}" if args.rotation_recorded_at else ""),
    )
    if not args.rotation_recorded_at:
        emit(
            "     no probe can see a rotation, and reading a key to prove one"
        )
        emit(
            "     would defeat it. Pass --rotation-recorded-at with the instant"
        )
        emit("     recorded in the run record.")

    # ---- existence by name -------------------------------------------------
    emit("")
    wanted = [
        ("environment", environment_name),
        ("volume", control_name),
        ("volume", artifact_name),
        ("named runtime object", secret_name),
    ]
    if not args.check:
        emit("EXISTENCE lookups NOT performed (no --check, so no provider call was made).")
        emit("With --check the script would ask, by name only:")
        for kind, name in wanted:
            emit(f"  does the {kind} {name!r} exist?")
        emit("It would read no contents, and would print only a yes or no per name.")
    elif report.failures:
        emit("EXISTENCE lookups refused: offline checks failed; no container started.")
    elif not credentials_present():
        report.check("existence-credentials", False,
                     "explicit provider credentials are missing or blank; no container started")
    elif not run_lookup_container(config_path, args.submit_image, args.docker, args.endpoint):
        report.failures.append("existence-lookup")

    emit("")
    if report.failures:
        emit(f"G5 FAIL  failing checks: {report.failures}")
        return 1
    if not args.check:
        emit(
            "G5 OFFLINE HALF PASS. The gate is not satisfied until the existence"
            " half runs against the account."
        )
        return 0
    emit("G5 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
