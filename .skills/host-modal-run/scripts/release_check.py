#!/usr/bin/env python3
"""Credential-free, process-isolated Modal release readiness checks."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence


HOST_TESTS = (
    "tests/synaptic_host/test_training_operator_status.py",
    "tests/synaptic_host/test_training_operator_reconcile.py",
    "tests/synaptic_host/test_training_operator_cli.py",
    "tests/synaptic_host/test_training_operator_retrieve.py",
    "tests/synaptic_host/test_modal_artifact_retrieval.py",
    "tests/synaptic_host/test_sqlite_repository.py",
    "tests/synaptic_host/test_modal_training.py",
)
NATIVE_TESTS = (
    "tests/synaptic_host/test_modal_native_login.py",
    "tests/skills/host_modal_run/test_g2_native_host.py",
    "tests/skills/host_modal_run/test_g5_isolation_triple.py",
    "tests/skills/host_modal_run/test_release_check.py",
)
SUPPLEMENTAL_HOST_TESTS = (
    "tests/synaptic_host/test_modal_provider.py",
    "tests/synaptic_host/test_modal_restore_descriptor.py",
    "tests/synaptic_host/test_modal_key_rotation.py",
    "tests/synaptic_host/test_modal_smoke_acceptance.py",
    "tests/synaptic_host/test_modal_resolver.py",
    "tests/synaptic_host/test_cli.py",
    "tests/synaptic_host/test_security.py",
)
ENGINE_TESTS = (
    "tests/execution/providers/test_modal_bundle.py",
    "tests/execution/providers/test_modal_composition.py",
    "tests/execution/providers/test_modal_config.py",
    "tests/execution/providers/test_modal_control_plane.py",
    "tests/execution/providers/test_modal_deployment_v1.py",
    "tests/execution/providers/test_modal_model_snapshot.py",
    "tests/execution/providers/test_modal_prepared_run_atomicity.py",
    "tests/execution/providers/test_modal_remote.py",
    "tests/execution/providers/test_modal_runtime_ports.py",
    "tests/execution/providers/test_modal_sdk154_adapter.py",
    "tests/execution/providers/test_modal_source_resolution.py",
    "tests/execution/providers/test_modal_training_operations.py",
    "tests/execution/providers/test_modal_run_reads.py",
    "tests/execution/providers/test_modal_verification.py",
    "tests/execution/providers/test_modal_worker_staging.py",
    "tests/contract/test_modal_runtime_lock.py",
    "tests/contract/test_offline_sft_worker_closure.py",
    "tests/runtime/test_offline_sft_worker.py",
    "tests/trainers/sft/test_runtime_v1.py",
)
_TIMEOUT_SECONDS = 900


def _environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin", "MODAL_IS_REMOTE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }


def _run(
    command: Sequence[str], *, cwd: Path, runner: Callable[..., object]
) -> object:
    return runner(
        tuple(command), cwd=cwd, env=_environment(), capture_output=True,
        text=True, timeout=_TIMEOUT_SECONDS, check=False, stdin=subprocess.DEVNULL,
    )


def _git(
    root: Path, arguments: Sequence[str], *, runner: Callable[..., object]
) -> str | None:
    result = _run(("git", "-C", str(root), *arguments), cwd=root, runner=runner)
    if getattr(result, "returncode", 1) != 0:
        return None
    return str(getattr(result, "stdout", "")).strip()


def _admit(root: Path, *, runner: Callable[..., object]) -> Path | None:
    engine = root / "synaptic-tuner"
    host_status = _git(root, ("status", "--porcelain", "--untracked-files=all"), runner=runner)
    host_top = _git(root, ("rev-parse", "--show-toplevel"), runner=runner)
    engine_status = _git(engine, ("status", "--porcelain", "--untracked-files=all"), runner=runner)
    engine_top = _git(engine, ("rev-parse", "--show-toplevel"), runner=runner)
    gitlink = _git(root, ("ls-tree", "HEAD", "--", "synaptic-tuner"), runner=runner)
    engine_head = _git(engine, ("rev-parse", "HEAD"), runner=runner)
    fields = () if gitlink is None else gitlink.split()
    if (
        host_status != "" or host_top != str(root) or engine_status != ""
        or engine_top != str(engine)
        or len(fields) < 3
        or tuple(fields[0:2]) != ("160000", "commit") or fields[2] != engine_head
    ):
        return None
    return engine


def _pytest(root: Path, paths: Sequence[Path | str]) -> tuple[str, ...]:
    code = (
        "import sys,pytest;"
        f"sys.path[:0]=[{str(root)!r},{str(root / 'synaptic-tuner')!r}];"
        "raise SystemExit(pytest.main(sys.argv[1:]))"
    )
    return (sys.executable, "-B", "-c", code, "-q", *(str(path) for path in paths))


def _offline_g5_output(root: Path) -> str:
    return f"""G5 isolation triple (29.7 ruling 5, 29.9 ruling 7, 29.12)
configuration : {root}/training/providers/modal.json

The four names this smoke will use:
  provider environment : synaptic-smoke-v1
  control volume       : synaptic-training-control-smoke-v1
  artifact volume      : synaptic-training-artifacts-smoke-v1
  runtime named object : synaptic-training-runtime-smoke-v1

The app name is not in this list on purpose. Ruling (5) settled that it
is a module constant and cannot vary from Host configuration, so
isolation is carried by the provider environment alone.

PASS S1 fresh-names  overlap with the existing deployment: none; distinct names: 4 of 4
PASS S2 fixed-key-set  declared key set matches the fixed set: True (2 declared, 2 required)
     the evidence MAC key is the WORKER key. Ruling (7) property 1: the
     Host key is never placed here, and it is rotated before the smoke.
PASS S3 standing-safety  unrelaxed at the pin: 4 of 4; missing: none
     the image is digest-pinned in the same decorator; egress is
     unrestricted at this pin by user ruling, so no network claim is
     made here in either direction.
FAIL S4 rotation-attested  operator attestation supplied: False
     no probe can see a rotation, and reading a key to prove one
     would defeat it. Pass --rotation-recorded-at with the instant
     recorded in the run record.

EXISTENCE lookups NOT performed (no --check, so no provider call was made).
With --check the script would ask, by name only:
  does the environment 'synaptic-smoke-v1' exist?
  does the volume 'synaptic-training-control-smoke-v1' exist?
  does the volume 'synaptic-training-artifacts-smoke-v1' exist?
  does the named runtime object 'synaptic-training-runtime-smoke-v1' exist?
It would read no contents, and would print only a yes or no per name.

G5 FAIL  failing checks: ['S4 rotation-attested']
"""


def _expected_offline_g5(result: object, root: Path) -> bool:
    return (
        getattr(result, "returncode", -1) == 1
        and str(getattr(result, "stdout", "")) == _offline_g5_output(root)
        and str(getattr(result, "stderr", "")) == ""
    )


def main(
    argv: list[str] | None = None, *, runner: Callable[..., object] = subprocess.run
) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[3]
    prepare = False
    project_root_seen = False
    while values:
        value = values.pop(0)
        if value == "--prepare-runtime" and not prepare:
            prepare = True
        elif value == "--project-root" and values and not project_root_seen:
            supplied = Path(values.pop(0))
            if not supplied.is_absolute():
                print("RELEASE_CHECK FAIL stage=arguments reason=invalid")
                return 2
            root = supplied
            project_root_seen = True
        else:
            print("RELEASE_CHECK FAIL stage=arguments reason=invalid")
            return 2
    try:
        root = root.resolve(strict=True)
    except OSError:
        print("RELEASE_CHECK FAIL stage=admission reason=unavailable")
        return 2
    try:
        engine = _admit(root, runner=runner)
    except (OSError, subprocess.TimeoutExpired):
        print("RELEASE_CHECK FAIL stage=admission reason=unavailable")
        return 2
    if engine is None:
        print("RELEASE_CHECK FAIL stage=admission reason=dirty-or-pin")
        return 2
    print("RELEASE_CHECK PASS stage=admission")
    lanes = (
        ("host", _pytest(root, tuple(root / path for path in HOST_TESTS)), root),
        ("host-supplemental", _pytest(root, tuple(root / path for path in SUPPLEMENTAL_HOST_TESTS)), root),
        ("native", _pytest(root, tuple(root / path for path in NATIVE_TESTS)), root),
        ("cold", _pytest(root, (root / "tests/synaptic_host/test_cold_bootstrap.py",)), root),
        ("engine", _pytest(root, tuple(engine / path for path in ENGINE_TESTS)), root),
        ("mirrors", (sys.executable, "-B", str(root / "bin/sync_skills.py"), "--check"), root),
        ("g2", (sys.executable, "-B", str(root / ".skills/host-modal-run/scripts/g2_native_host.py"), *(("--prepare-runtime",) if prepare else ())), root),
        ("g3", (sys.executable, "-B", str(root / ".skills/host-modal-run/scripts/g3_engine_lock_digests.py"), "--expect", "0"), root),
        ("g5-offline", (sys.executable, "-B", str(root / ".skills/host-modal-run/scripts/g5_isolation_triple.py")), root),
    )
    for stage, command, cwd in lanes:
        try:
            result = _run(command, cwd=cwd, runner=runner)
        except (OSError, subprocess.TimeoutExpired):
            print(f"RELEASE_CHECK FAIL stage={stage} reason=unavailable")
            return 1
        if stage == "g5-offline":
            if not _expected_offline_g5(result, root):
                print("RELEASE_CHECK FAIL stage=g5-offline reason=truth")
                return 1
            print("RELEASE_CHECK PASS stage=g5-offline result=S1-S3-pass-S4-expected-refusal-not-full-G5")
        elif getattr(result, "returncode", 1) != 0:
            print(f"RELEASE_CHECK FAIL stage={stage} reason=child")
            return 1
        else:
            print(f"RELEASE_CHECK PASS stage={stage}")
    print("RELEASE_CHECK PASS result=credential-free-ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
