from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import types
import unicodedata
from pathlib import Path

import pytest

import synaptic_host.__main__ as entry
import synaptic_host.cli as cli
import synaptic_host.launcher as launcher
from synaptic_host.cli import (
    TrainingRunCommandCodeV2,
    TrainingRunCommandResultV2,
    TrainingRunIngressV1,
    prepare_training_run_ingress_v1,
)


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "synaptic-tuner"


def _ingress(
    tmp_path: Path, provider: str = "modal", suffix: str = "1",
) -> TrainingRunIngressV1:
    if cli._ENGINE_CONTRACT_CACHE is None:
        for name in tuple(sys.modules):
            if name == "synaptic_tuner" or name.startswith("synaptic_tuner."):
                sys.modules.pop(name, None)
    project = tmp_path / f"{provider}-{suffix}"
    training = project / "training"
    training.mkdir(parents=True)
    document = {
        "schema_version": "synaptic-training-input/v1",
        "method": "sft",
        "model": {
            "ref": "organization/model", "revision": "revision-1",
            "tokenizer_revision": "tokenizer-1",
        },
        "dataset": {"ref": "dataset://organization/corpus"},
        "hyperparameters": {
            "schema_version": "synaptic-sft-hyperparameters/v1",
            "batch_size": 2, "gradient_accumulation_steps": 4,
            "learning_rate": 0.0002,
            "duration": {"max_steps": 100, "num_epochs": None},
            "max_seq_length": 2048, "seed": int(suffix), "save_steps": 25,
            "save_total_limit": 2, "lora_rank": 16, "lora_alpha": 32,
            "lora_dropout": 0.05,
            "lora_target_modules": ["k_proj", "q_proj", "v_proj"],
            "use_dora": False, "use_rslora": True,
            "init_lora_weights": True, "split_dataset": False,
        },
        "artifacts": {
            "required_kinds": ["final_model", "training_lineage"],
            "retain_checkpoints": True,
        },
    }
    (training / "input.json").write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    prepared = prepare_training_run_ingress_v1(
        [
            "training", "run", "--provider", provider, "--config",
            "project://training/input.json", "--destination", "provider-staging",
        ],
        project_root=project,
        engine_root=ENGINE,
    )
    assert type(prepared) is TrainingRunIngressV1
    return prepared


def _locked_runtime(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    project = tmp_path / "project"
    engine = tmp_path / "engine"
    requirements = engine / "requirements/modal-launcher-v1.lock"
    requirements.parent.mkdir(parents=True)
    requirements.write_text("modal==1.5.4 --hash=sha256:" + "a" * 64 + "\n")
    python = launcher.launcher_python(project)
    python.parent.mkdir(parents=True)
    python.write_bytes(b"pinned")
    expected = launcher._runtime_stamp(requirements)
    stamp = python.parent.parent / ".synaptic-lock-sha256"
    stamp.write_text(expected + "\n", encoding="ascii")
    return project, engine, python, expected


def test_cli_and_entrypoint_import_cold_without_engine_provider_or_launcher() -> None:
    code = f"""
import json, sys
sys.path.insert(0, {str(ROOT)!r})
before = set(sys.modules)
import synaptic_host.cli, synaptic_host.__main__
delta = set(sys.modules) - before
forbidden = sorted(name for name in delta if name == 'synaptic_tuner' or name.startswith(('synaptic_tuner.', 'modal', 'docker', 'sqlite3', 'synaptic_host.launcher')))
print(json.dumps(forbidden))
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=ROOT,
        check=True, capture_output=True, text=True,
    )
    assert json.loads(completed.stdout) == []


def test_old_verb_fresh_process_emits_one_closed_line_without_argparse() -> None:
    code = f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
from synaptic_host.__main__ import main
raise SystemExit(main(['provider', 'deploy']))
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=ROOT,
        check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 2
    assert completed.stderr == ""
    lines = completed.stdout.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["code"] == "COMMAND_INVALID"
    assert "usage" not in completed.stdout.casefold()


def test_docker_never_imports_or_calls_launcher(monkeypatch, capsys, tmp_path: Path) -> None:
    ingress = _ingress(tmp_path, "docker")
    events = []
    fake = types.ModuleType("synaptic_host.launcher")
    fake.ensure_and_reexec = lambda **_kwargs: events.append("launcher")
    monkeypatch.setitem(sys.modules, "synaptic_host.launcher", fake)
    monkeypatch.setattr(entry, "prepare_training_run_ingress_v1", lambda *_a, **_k: ingress)
    assert entry.main(["training", "run"]) == 4
    assert events == []
    assert json.loads(capsys.readouterr().out)["code"] == "PROVIDER_UNAVAILABLE"


def test_modal_parent_prepares_before_launcher_and_emits_nothing(
    monkeypatch, capsys, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    events = []
    fake = types.ModuleType("synaptic_host.launcher")

    def ensure(**kwargs):
        events.append(("launcher", kwargs))
        return 7

    fake.ensure_and_reexec = ensure
    monkeypatch.setitem(sys.modules, "synaptic_host.launcher", fake)

    def prepare(*_args, **_kwargs):
        events.append(("prepare", None))
        return ingress

    monkeypatch.setattr(entry, "prepare_training_run_ingress_v1", prepare)
    arguments = ["training", "run"]
    assert entry.main(arguments) == 7
    assert [item[0] for item in events] == ["prepare", "launcher"]
    assert events[1][1]["argv"] == arguments
    assert events[1][1]["ingress_digest"] == ingress.envelope_digest
    assert events[1][1]["contract_identity_digest"] == ingress.contract_identity_digest
    assert capsys.readouterr().out == ""


def test_authoritative_child_reprepares_then_emits_composition_unavailable_once(
    monkeypatch, capsys, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    monkeypatch.setenv("MODAL_TOKEN_ID", "test-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "test-secret")
    events = []
    fake = types.ModuleType("synaptic_host.launcher")
    fake.ensure_and_reexec = lambda **_kwargs: events.append("launcher") or None
    monkeypatch.setitem(sys.modules, "synaptic_host.launcher", fake)
    monkeypatch.setattr(
        entry, "prepare_training_run_ingress_v1",
        lambda *_a, **_k: events.append("prepare") or ingress,
    )
    assert entry.main(["training", "run"]) == 4
    assert events == ["prepare", "launcher"]
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["code"] == "COMPOSITION_UNAVAILABLE"


def test_reexec_mutation_digest_mismatch_is_bootstrap_unavailable(
    monkeypatch, capsys, tmp_path: Path,
) -> None:
    original = _ingress(tmp_path, suffix="1")
    mutated = _ingress(tmp_path, suffix="2")
    fake = types.ModuleType("synaptic_host.launcher")

    def ensure(**kwargs):
        if kwargs["ingress_digest"] != original.envelope_digest:
            raise RuntimeError("secret mutation")
        return None

    fake.ensure_and_reexec = ensure
    monkeypatch.setitem(sys.modules, "synaptic_host.launcher", fake)
    monkeypatch.setattr(entry, "prepare_training_run_ingress_v1", lambda *_a, **_k: mutated)
    assert entry.main(["training", "run", "mutated"]) == 4
    output = capsys.readouterr().out
    assert json.loads(output)["code"] == "BOOTSTRAP_UNAVAILABLE"
    assert "secret" not in output


def test_launcher_parent_binds_argv_and_digest_without_real_process(
    monkeypatch, tmp_path: Path,
) -> None:
    project, engine, python, _expected = _locked_runtime(tmp_path)
    monkeypatch.delenv(launcher._MARKER, raising=False)
    monkeypatch.delenv(launcher._INGRESS_DIGEST, raising=False)
    monkeypatch.setenv("HF_TOKEN", "must-not-leak")
    monkeypatch.setenv("HTTPS_PROXY", "must-not-leak")
    monkeypatch.setenv("MODAL_TOKEN_ID", "modal-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "modal-secret")
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    observed = {}

    def run(command, **kwargs):
        observed.update(command=command, kwargs=kwargs)
        return types.SimpleNamespace(returncode=9)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    argv = ["training", "run", "--provider", "modal"]
    digest = "b" * 64
    assert launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=argv, ingress_digest=digest,
        contract_identity_digest="e" * 64,
    ) == 9
    assert observed["command"] == [
        str(python), "-I", "-c", launcher._FIXED_BOOTSTRAP,
        str(project.resolve()), str(engine.resolve()), *argv,
    ]
    environment = observed["kwargs"]["env"]
    assert environment[launcher._MARKER] == "1"
    assert environment[launcher._INGRESS_DIGEST] == digest
    assert environment[launcher._CONTRACT_IDENTITY_DIGEST] == "e" * 64
    assert environment[launcher._RUNTIME_PROOF_DIGEST] == "f" * 64
    assert "HF_TOKEN" not in environment
    assert "HTTPS_PROXY" not in environment
    assert "PYTHONPATH" not in environment
    assert environment["MODAL_TOKEN_ID"] == "modal-id"
    assert environment["MODAL_TOKEN_SECRET"] == "modal-secret"


@pytest.mark.parametrize(
    ("token_id", "token_secret"),
    [
        (None, None), ("id", None), (None, "secret"), ("", "secret"),
        ("id", ""), ("id\n", "secret"), ("id", "secret\x7f"),
        ("id\u0085", "secret"),
        ("i" * 4097, "secret"), ("id", "s" * 4097),
    ],
)
def test_launcher_never_forwards_partial_or_invalid_modal_credentials(
    monkeypatch, tmp_path: Path, token_id: str | None, token_secret: str | None,
) -> None:
    project, engine, _python, _expected = _locked_runtime(tmp_path)
    monkeypatch.delenv(launcher._MARKER, raising=False)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    if token_id is not None:
        monkeypatch.setenv("MODAL_TOKEN_ID", token_id)
    if token_secret is not None:
        monkeypatch.setenv("MODAL_TOKEN_SECRET", token_secret)
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    observed = {}

    def run(_command, **kwargs):
        observed.update(kwargs)
        return types.SimpleNamespace(returncode=4)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    assert launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=[],
        ingress_digest="b" * 64, contract_identity_digest="e" * 64,
    ) == 4
    assert "MODAL_TOKEN_ID" not in observed["env"]
    assert "MODAL_TOKEN_SECRET" not in observed["env"]


def test_launcher_rejects_credential_string_subclasses(
    monkeypatch, tmp_path: Path,
) -> None:
    class String(str):
        def encode(self, *_args, **_kwargs):
            pytest.fail("credential subclass encode callback invoked")

    project, engine, _python, _expected = _locked_runtime(tmp_path)
    environment = dict(launcher.os.environ)
    environment["MODAL_TOKEN_ID"] = String("subclass-id")
    environment["MODAL_TOKEN_SECRET"] = "secret"
    monkeypatch.setattr(launcher.os, "environ", environment)
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    observed = {}

    def run(_command, **kwargs):
        observed.update(kwargs)
        return types.SimpleNamespace(returncode=4)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    assert launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=[],
        ingress_digest="b" * 64, contract_identity_digest="e" * 64,
    ) == 4
    assert "MODAL_TOKEN_ID" not in observed["env"]
    assert "MODAL_TOKEN_SECRET" not in observed["env"]


@pytest.mark.parametrize("name", launcher._ALLOWED_CHILD_ENV)
@pytest.mark.parametrize(
    "hostile", ("\u0085", "\u202e", "\ud800", "\ue000", "\u0378"),
)
def test_launcher_rejects_category_c_in_every_allowlisted_environment_value(
    monkeypatch, tmp_path: Path, name: str, hostile: str,
) -> None:
    assert unicodedata.category(hostile).startswith("C")
    project, engine, _python, _expected = _locked_runtime(tmp_path)
    monkeypatch.setattr(launcher.os, "environ", {name: "value" + hostile})
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda *_a, **_k: pytest.fail("invalid environment reached spawn"),
    )
    with pytest.raises(RuntimeError, match="child environment"):
        launcher.ensure_and_reexec(
            project_root=project, engine_root=engine, argv=[],
            ingress_digest="b" * 64, contract_identity_digest="e" * 64,
        )


@pytest.mark.parametrize("name", launcher._ALLOWED_CHILD_ENV)
def test_launcher_rejects_allowlisted_str_subclass_without_encode_callback(
    monkeypatch, tmp_path: Path, name: str,
) -> None:
    class String(str):
        def encode(self, *_args, **_kwargs):
            pytest.fail("allowlisted subclass encode callback invoked")

    project, engine, _python, _expected = _locked_runtime(tmp_path)
    monkeypatch.setattr(launcher.os, "environ", {name: String("deceptive")})
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda *_a, **_k: pytest.fail("invalid environment reached spawn"),
    )
    with pytest.raises(RuntimeError, match="child environment"):
        launcher.ensure_and_reexec(
            project_root=project, engine_root=engine, argv=[],
            ingress_digest="b" * 64, contract_identity_digest="e" * 64,
        )


def test_launcher_forwards_detached_exact_string_snapshot(
    monkeypatch, tmp_path: Path,
) -> None:
    project, engine, _python, _expected = _locked_runtime(tmp_path)
    original = "validated-" + "x" * 128
    monkeypatch.setattr(launcher.os, "environ", {"LANG": original})
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    observed = {}

    def run(_command, **kwargs):
        observed.update(kwargs)
        return types.SimpleNamespace(returncode=4)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    assert launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=[],
        ingress_digest="b" * 64, contract_identity_digest="e" * 64,
    ) == 4
    forwarded = observed["env"]["LANG"]
    assert type(forwarded) is str
    assert forwarded == original
    assert forwarded is not original


def test_launcher_child_requires_exact_marker_digest_interpreter_and_lock(
    monkeypatch, tmp_path: Path,
) -> None:
    project, engine, python, _expected = _locked_runtime(tmp_path)
    digest = "c" * 64
    monkeypatch.setenv(launcher._MARKER, "1")
    monkeypatch.setenv(launcher._INGRESS_DIGEST, digest)
    monkeypatch.setenv(launcher._CONTRACT_IDENTITY_DIGEST, "e" * 64)
    monkeypatch.setenv(launcher._RUNTIME_PROOF_DIGEST, "f" * 64)
    monkeypatch.setattr(launcher, "_runtime_proof", lambda *_a: ({}, "f" * 64))
    monkeypatch.setattr(launcher.sys, "executable", str(python))
    monkeypatch.setattr(launcher.platform, "python_version", lambda: launcher._PYTHON_VERSION)
    assert launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=[], ingress_digest=digest,
        contract_identity_digest="e" * 64,
    ) is None
    monkeypatch.setenv(launcher._INGRESS_DIGEST, "d" * 64)
    with pytest.raises(RuntimeError, match="authority"):
        launcher.ensure_and_reexec(
            project_root=project, engine_root=engine, argv=[], ingress_digest=digest,
            contract_identity_digest="e" * 64,
        )
    monkeypatch.setenv(launcher._MARKER, "wrong")
    with pytest.raises(RuntimeError, match="authority"):
        launcher.ensure_and_reexec(
            project_root=project, engine_root=engine, argv=[], ingress_digest=digest,
            contract_identity_digest="e" * 64,
        )


@pytest.mark.parametrize(
    "reported",
    [
        b"uv 0.12.0",
        b"uv 0.12.0\n",
        b"uv 0.12.0 (x86_64-unknown-linux-gnu)",
        b"uv 0.12.0 (x86_64-unknown-linux-gnu)\n",
    ],
)
def test_uv_version_accepts_only_pinned_version_and_linux_target(
    monkeypatch, tmp_path: Path, reported: bytes,
) -> None:
    observed = {}

    def run(command, **kwargs):
        observed.update(command=command, kwargs=kwargs)
        return types.SimpleNamespace(stdout=reported)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    uv = tmp_path / "uv"
    assert launcher._uv_reported_version(uv) == launcher._UV_VERSION
    assert observed == {
        "command": [str(uv), "--version"],
        "kwargs": {
            "check": True, "capture_output": True, "text": False, "env": {},
        },
    }


@pytest.mark.parametrize(
    "reported",
    [
        b"", b"uv 0.12.1", b"uv 0.12.0 ", b" uv 0.12.0",
        b"uv 0.12.0\r\n", b"uv 0.12.0\nextra", b"uv 0.12.0\n\n",
        b"uv 0.12.0 ()", b"uv 0.12.0 (x86_64-unknown-linux-gnu",
        b"uv 0.12.0 (x86_64-unknown-linux-gnu) extra",
        b"uv 0.12.0 (aarch64-unknown-linux-gnu)",
        b"uv 0.12.0 (x86_64-unknown-linux-musl)",
        b"uv 0.12.0 (x86_64-unknown-linux-gnu)\x00",
        "uv 0.12.0 (x86_64-unknown-linux-gnu)",
    ],
)
def test_uv_version_rejects_ambiguous_or_unpinned_output(
    monkeypatch, tmp_path: Path, reported: object,
) -> None:
    monkeypatch.setattr(
        launcher.subprocess, "run",
        lambda *_args, **_kwargs: types.SimpleNamespace(stdout=reported),
    )
    with pytest.raises(RuntimeError, match="pinned uv executable version mismatch"):
        launcher._uv_reported_version(tmp_path / "uv")


def test_launcher_source_has_no_modal_import_or_sdk_probe() -> None:
    source = (ROOT / "synaptic_host/launcher.py").read_text(encoding="utf-8")
    assert "import modal" not in source
    assert "modal.__version__" not in source


def test_runtime_proof_uses_canonical_relative_symlink_evidence(
    monkeypatch, tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    engine = tmp_path / "engine"
    requirements = engine / "requirements/modal-launcher-v1.lock"
    requirements.parent.mkdir(parents=True)
    requirements.write_text("locked\n", encoding="ascii")
    venv = launcher.launcher_python(project).parent.parent
    (venv / "bin").mkdir(parents=True)
    managed = project / ".synaptic/cache/uv-python-v1/cpython-test"
    final = managed / "bin/python3.11"
    final.parent.mkdir(parents=True)
    final.write_bytes(b"executable")
    final.chmod(0o755)
    launcher_link = venv / "bin/python"
    original_lstat = Path.lstat
    fake_link = False
    try:
        launcher_link.symlink_to(final)
    except OSError:
        fake_link = True
        monkeypatch.setattr(
            launcher.os, "readlink",
            lambda path: str(final) if Path(path) == launcher_link else os.readlink(path),
        )

    def fake_lstat(path):
        if fake_link and path == launcher_link:
            return types.SimpleNamespace(st_mode=stat.S_IFLNK)
        observed = original_lstat(path)
        if path == final:
            return types.SimpleNamespace(
                st_mode=observed.st_mode | 0o111,
                st_dev=observed.st_dev,
                st_ino=observed.st_ino,
                st_size=observed.st_size,
                st_mtime_ns=observed.st_mtime_ns,
            )
        return observed

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    (venv / "pyvenv.cfg").write_text("home = managed\n", encoding="ascii")
    stamp = launcher._runtime_stamp(requirements)
    (venv / ".synaptic-lock-sha256").write_text(stamp + "\n", encoding="ascii")
    uv = project / ".synaptic/cache/tools/uv-0.12.0/uv"
    uv.parent.mkdir(parents=True)
    uv.write_bytes(b"uv")
    uv.chmod(0o755)
    (uv.parent / ".archive-sha256").write_text(
        launcher._UV_ARCHIVE_SHA256 + "\n", encoding="ascii"
    )
    monkeypatch.setattr(launcher, "_uv_reported_version", lambda _uv: launcher._UV_VERSION)
    monkeypatch.setattr(
        launcher, "_python_identity",
        lambda _python: {
            "python_version": launcher._PYTHON_VERSION,
            "prefix": str(venv.absolute()),
            "base_prefix": str(managed.absolute()),
        },
    )
    body = launcher._compute_runtime_proof(
        project_root=project, engine_root=engine, uv_binary=uv
    )
    assert set(body) == {
        "schema_version", "lock_stamp", "requirements_lock_sha256", "uv_version",
        "uv_archive_sha256", "uv_executable_sha256", "python_version",
        "launcher_relative_path", "launcher_chain", "final_target_relative_path",
        "final_target_sha256", "final_target_size", "final_target_mode",
        "pyvenv_cfg_sha256", "sys_prefix_relative_path", "base_prefix_relative_path",
    }
    assert body["schema_version"] == "synaptic-modal-launcher-runtime-proof/v1"
    assert body["launcher_relative_path"] == "bin/python"
    assert body["final_target_relative_path"] == "cpython-test/bin/python3.11"
    assert body["base_prefix_relative_path"] == "cpython-test"
    assert body["launcher_chain"] == [{
        "index": 0,
        "link_location_kind": "venv",
        "link_relative_path": "bin/python",
        "link_text_sha256": hashlib.sha256(str(final).encode("utf-8")).hexdigest(),
        "resolved_target_kind": "managed",
        "resolved_target_relative_path": "cpython-test/bin/python3.11",
    }]
    rendered = json.dumps(body, sort_keys=True, separators=(",", ":"))
    assert str(project) not in rendered
    proof_digest = launcher._proof_digest(body)
    (venv / launcher._PROOF_FILE).write_text(
        json.dumps({**body, "proof_digest": proof_digest}, sort_keys=True,
                   separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(launcher, "_uv_binary", lambda _project: uv)
    assert launcher._runtime_proof(project, engine) == (body, proof_digest)
    requirements.write_text("mutated\n", encoding="ascii")
    with pytest.raises(RuntimeError):
        launcher._runtime_proof(project, engine)


@pytest.mark.parametrize("attack", ["escape", "cycle", "too_many"])
def test_launcher_chain_rejects_escape_cycle_and_excessive_hops(
    monkeypatch, tmp_path: Path, attack: str,
) -> None:
    venv = (tmp_path / "venv").absolute()
    managed = (tmp_path / "managed").absolute()
    launcher_link = venv / "bin/python"
    outside = (tmp_path / "outside/python").absolute()
    links: dict[Path, str] = {}
    if attack == "escape":
        links[launcher_link] = str(outside)
    elif attack == "cycle":
        first = managed / "first"
        links[launcher_link] = str(first)
        links[first] = str(first)
    else:
        current = launcher_link
        for index in range(9):
            target = managed / f"link-{index}"
            links[current] = str(target)
            current = target
    original_lstat = Path.lstat
    original_readlink = os.readlink

    def fake_lstat(path):
        if path in links:
            return types.SimpleNamespace(st_mode=stat.S_IFLNK)
        return original_lstat(path)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    monkeypatch.setattr(
        launcher.os, "readlink",
        lambda path: links[Path(path)] if Path(path) in links else original_readlink(path),
    )
    with pytest.raises((RuntimeError, ValueError, OSError)):
        launcher._launcher_chain(launcher_link, venv, managed)


@pytest.mark.skipif(
    os.environ.get("SYNAPTIC_RUN_WSL_LAUNCHER_INTEGRATION") != "1",
    reason="opt-in WSL/DrvFS isolated runtime build",
)
def test_opt_in_wsl_drvfs_runtime_build_reaches_authoritative_child(
    tmp_path: Path,
) -> None:
    if platform.system() != "Linux":
        pytest.skip("requires Linux under WSL")
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    shutil.copytree(ROOT / "synaptic_host", project / "synaptic_host")
    requirements = engine / "requirements/modal-launcher-v1.lock"
    requirements.parent.mkdir(parents=True)
    shutil.copy2(
        ROOT / "synaptic-tuner/requirements/modal-launcher-v1.lock", requirements
    )
    launcher._build_runtime(
        project_root=project, requirements=requirements,
        expected=launcher._runtime_stamp(requirements),
    )
    _body, proof_digest = launcher._runtime_proof(project, engine)
    assert len(proof_digest) == 64
    completed = subprocess.run(
        [
            str(launcher.launcher_python(project)), "-I", "-c",
            launcher._FIXED_BOOTSTRAP, str(project), str(engine),
            "provider", "deploy",
        ],
        cwd=project, env={}, check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 2
    assert json.loads(completed.stdout)["code"] == "COMMAND_INVALID"
