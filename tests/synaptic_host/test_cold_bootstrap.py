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
from concurrent.futures import ThreadPoolExecutor
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


def _commit_project(project: Path) -> Path:
    """Commit the project's training tree so it has a HEAD to read from.

    C1 (section 29.5(f)).  Both provider arms now read the COMMITTED blob, so
    a bare directory is no longer a project: the harness commits what it
    writes.  Without this every modal-arm case here would refuse with
    CONFIG_UNAVAILABLE before reaching the behaviour it is about.
    """

    identity = (
        "-c", "user.name=synaptic-test",
        "-c", "user.email=synaptic-test@example.invalid",
        "-c", "commit.gpgsign=false",
    )
    for arguments in (
        ("init", "--quiet", "--initial-branch", "main"),
        ("add", "--force", "--", "training"),
        (*identity, "commit", "--quiet", "-m", "committed training input"),
    ):
        subprocess.run(
            ("git", "-C", str(project), *arguments),
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    return project


def _ingress(
    tmp_path: Path, provider: str = "modal", suffix: str = "1",
) -> TrainingRunIngressV1:
    if cli._ENGINE_CONTRACT_CACHE is None:
        for name in tuple(sys.modules):
            if name == "synaptic_tuner" or name.startswith("synaptic_tuner."):
                sys.modules.pop(name, None)
    if provider == "docker":
        prepared = prepare_training_run_ingress_v1(
            [
                "training", "run", "--provider", "docker", "--config",
                "project://training/smokes/modal-sft.json", "--destination",
                "local-default",
            ],
            project_root=ROOT,
            engine_root=ENGINE,
        )
        assert type(prepared) is TrainingRunIngressV1
        return prepared
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
    _commit_project(project)
    prepared = prepare_training_run_ingress_v1(
        [
            "training", "run", "--provider", provider, "--config",
            "project://training/input.json", "--destination",
            "local-default" if provider == "docker" else "provider-staging",
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


def _mint_child_authority(
    monkeypatch, tmp_path: Path, ingress: TrainingRunIngressV1,
    *, runtime_proof_callback=None, environment_factory=None,
) -> object:
    project, engine, python, _expected = _locked_runtime(tmp_path)
    monkeypatch.setenv(launcher._MARKER, "1")
    monkeypatch.setenv(launcher._INGRESS_DIGEST, ingress.envelope_digest)
    monkeypatch.setenv(
        launcher._CONTRACT_IDENTITY_DIGEST, ingress.contract_identity_digest
    )
    monkeypatch.setenv(launcher._RUNTIME_PROOF_DIGEST, "f" * 64)
    monkeypatch.setenv("MODAL_TOKEN_ID", "isolated-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "isolated-secret")
    monkeypatch.setattr(
        launcher, "_runtime_proof",
        runtime_proof_callback or (lambda *_a: ({}, "f" * 64)),
    )
    monkeypatch.setattr(launcher.sys, "executable", str(python))
    if environment_factory is not None:
        monkeypatch.setattr(
            launcher.os, "environ",
            environment_factory(dict(launcher.os.environ)),
        )
    issue, authenticate, consume = launcher._install_isolated_child_authority_v1()
    monkeypatch.setattr(launcher, "_issue_isolated_child_authority_v1", issue)
    monkeypatch.setattr(
        launcher, "_authenticate_isolated_child_authority_v1", authenticate
    )
    monkeypatch.setattr(launcher, "_consume_isolated_child_authority_v1", consume)
    return launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=[],
        ingress_digest=ingress.envelope_digest,
        contract_identity_digest=ingress.contract_identity_digest,
    )


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
    def dispatch(value, **kwargs):
        events.append(("docker", value, kwargs))
        return cli._failure(
            TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED,
            provider_ref=value.provider_ref, config_ref=value.config_ref,
            destination_ref=value.destination_ref, input_digest=value.input_digest,
        )
    monkeypatch.setattr(entry, "dispatch_validated_training_run_v1", dispatch)
    assert entry.main(["training", "run"]) == 2
    assert len(events) == 1 and events[0][0] == "docker"
    assert events[0][2]["isolated_child_authority"] is None
    assert events[0][2]["project_root"] == ROOT
    assert events[0][2]["engine_root"] == ENGINE
    assert json.loads(capsys.readouterr().out)["code"] == "CAPABILITY_UNSUPPORTED"


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


def test_authoritative_child_passes_authority_and_emits_once(
    monkeypatch, capsys, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    monkeypatch.setenv("MODAL_TOKEN_ID", "test-id")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "test-secret")
    events = []
    authority = object()
    fake = types.ModuleType("synaptic_host.launcher")
    fake.ensure_and_reexec = lambda **_kwargs: events.append("launcher") or authority
    monkeypatch.setitem(sys.modules, "synaptic_host.launcher", fake)
    monkeypatch.setattr(
        entry, "prepare_training_run_ingress_v1",
        lambda *_a, **_k: events.append("prepare") or ingress,
    )
    monkeypatch.setattr(
        entry, "dispatch_validated_training_run_v1",
        lambda value, *, isolated_child_authority: (
            events.append((value, isolated_child_authority))
            or cli._failure(
                TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE,
                provider_ref=value.provider_ref, config_ref=value.config_ref,
                destination_ref=value.destination_ref,
                input_digest=value.input_digest,
            )
        ),
    )
    assert entry.main(["training", "run"]) == 4
    assert events == ["prepare", "launcher", (ingress, authority)]
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["code"] == "COMPOSITION_UNAVAILABLE"


def test_direct_modal_none_and_forged_authority_never_import_training(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path)
    imported: list[str] = []
    original_import = cli.importlib.import_module

    def guarded(name: str, *args, **kwargs):
        imported.append(name)
        if name == "synaptic_host.modal_training":
            pytest.fail("unauthenticated dispatch imported Modal composition")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli.importlib, "import_module", guarded)
    assert (
        cli.dispatch_validated_training_run_v1(
            ingress, isolated_child_authority=None
        ).code
        is TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
    )
    assert imported == []
    assert (
        cli.dispatch_validated_training_run_v1(
            ingress, isolated_child_authority=object()
        ).code
        is TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
    )
    assert "synaptic_host.modal_training" not in imported


def test_isolated_authority_is_one_use_and_result_is_reconstructed(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path / "ingress")
    authority = _mint_child_authority(monkeypatch, tmp_path / "runtime", ingress)
    calls: list[tuple[object, ...]] = []
    fake = types.ModuleType("synaptic_host.modal_training")

    def execute(value, **kwargs):
        calls.append((value, kwargs))
        return cli._failure(
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE,
            provider_ref=value.provider_ref, config_ref=value.config_ref,
            destination_ref=value.destination_ref,
            input_digest=value.input_digest,
        )

    fake.execute_modal_training_run_v2 = execute
    monkeypatch.setitem(sys.modules, "synaptic_host.modal_training", fake)
    first = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert type(first) is TrainingRunCommandResultV2
    assert first.code is TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
    assert len(calls) == 1
    assert calls[0][0] is ingress
    assert calls[0][1]["token_id"] == "isolated-id"
    assert calls[0][1]["token_secret"] == "isolated-secret"
    second = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert second.code is TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE
    assert len(calls) == 1


def test_concurrent_child_authority_consumption_allows_one_executor_call(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path / "ingress")
    authority = _mint_child_authority(monkeypatch, tmp_path / "runtime", ingress)
    calls: list[object] = []
    fake = types.ModuleType("synaptic_host.modal_training")

    def execute(value, **_kwargs):
        calls.append(value)
        return cli._failure(
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE,
            provider_ref=value.provider_ref, config_ref=value.config_ref,
            destination_ref=value.destination_ref,
            input_digest=value.input_digest,
        )

    fake.execute_modal_training_run_v2 = execute
    monkeypatch.setitem(sys.modules, "synaptic_host.modal_training", fake)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = tuple(
            pool.map(
                lambda _index: cli.dispatch_validated_training_run_v1(
                    ingress, isolated_child_authority=authority
                ),
                range(64),
            )
        )
    assert len(calls) == 1
    assert sum(
        result.code is TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
        for result in results
    ) == 1
    assert all(
        result.code in {
            TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE,
            TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE,
        }
        for result in results
    )
@pytest.mark.parametrize(
    "mutation",
    ("credential", "proof", "interpreter"),
)
def test_isolated_authority_runtime_drift_fails_before_executor(
    monkeypatch, tmp_path: Path, mutation: str,
) -> None:
    ingress = _ingress(tmp_path / "ingress")
    authority = _mint_child_authority(monkeypatch, tmp_path / "runtime", ingress)
    fake = types.ModuleType("synaptic_host.modal_training")
    fake.execute_modal_training_run_v2 = lambda *_a, **_k: pytest.fail(
        "drifted authority reached executor"
    )
    monkeypatch.setitem(sys.modules, "synaptic_host.modal_training", fake)
    if mutation == "credential":
        monkeypatch.setenv("MODAL_TOKEN_SECRET", "changed")
    elif mutation == "proof":
        monkeypatch.setenv(launcher._RUNTIME_PROOF_DIGEST, "0" * 64)
    else:
        monkeypatch.setattr(launcher.sys, "executable", str(ROOT / "foreign-python"))
    result = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert result.code is TrainingRunCommandCodeV2.BOOTSTRAP_UNAVAILABLE


@pytest.mark.parametrize("raises", (False, True))
def test_consume_runtime_proof_ingress_mutation_closes_before_modal_import(
    monkeypatch, tmp_path: Path, raises: bool,
) -> None:
    ingress = _ingress(tmp_path / "ingress")
    calls = 0

    def runtime_proof(*_args):
        nonlocal calls
        calls += 1
        if calls == 3:
            object.__setattr__(ingress, "source_sha256", "0" * 64)
            if raises:
                raise RuntimeError("private runtime detail")
        return {}, "f" * 64

    authority = _mint_child_authority(
        monkeypatch, tmp_path / "runtime", ingress,
        runtime_proof_callback=runtime_proof,
    )
    imported: list[str] = []
    original_import = cli.importlib.import_module

    def guarded(name: str, *args, **kwargs):
        imported.append(name)
        if name == "synaptic_host.modal_training":
            pytest.fail("mutated ingress reached Modal import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli.importlib, "import_module", guarded)
    result = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert "synaptic_host.modal_training" not in imported
    assert calls == 3
    assert "private runtime detail" not in result.canonical_json()


def test_consume_credential_environment_mutation_closes_before_modal_import(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path / "ingress")

    class MutatingEnvironment(dict):
        token_reads = 0

        def get(self, name, default=None):
            if name == "MODAL_TOKEN_ID":
                self.token_reads += 1
                if self.token_reads == 2:
                    object.__setattr__(ingress, "source_sha256", "0" * 64)
            return dict.get(self, name, default)

    authority = _mint_child_authority(
        monkeypatch, tmp_path / "runtime", ingress,
        environment_factory=MutatingEnvironment,
    )
    imported: list[str] = []
    original_import = cli.importlib.import_module

    def guarded(name: str, *args, **kwargs):
        imported.append(name)
        if name == "synaptic_host.modal_training":
            pytest.fail("credential mutation reached Modal import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli.importlib, "import_module", guarded)
    result = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert "synaptic_host.modal_training" not in imported


def test_authority_authentication_mutation_closes_before_consumption_or_import(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path / "ingress")
    authority = _mint_child_authority(monkeypatch, tmp_path / "runtime", ingress)
    original = launcher._authenticate_isolated_child_authority_v1
    consumed = []
    imported: list[str] = []
    original_import = cli.importlib.import_module

    def authenticate(value):
        object.__setattr__(ingress, "source_sha256", "0" * 64)
        return original(value)

    monkeypatch.setattr(
        launcher, "_authenticate_isolated_child_authority_v1", authenticate
    )
    monkeypatch.setattr(
        launcher, "_consume_isolated_child_authority_v1",
        lambda *_a, **_k: consumed.append(True),
    )

    def guarded(name: str, *args, **kwargs):
        imported.append(name)
        if name == "synaptic_host.modal_training":
            pytest.fail("authority mutation reached Modal import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli.importlib, "import_module", guarded)
    result = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert consumed == []
    assert "synaptic_host.modal_training" not in imported


def test_executor_import_mutation_closes_before_executor_call(
    monkeypatch, tmp_path: Path,
) -> None:
    ingress = _ingress(tmp_path / "ingress")
    authority = _mint_child_authority(monkeypatch, tmp_path / "runtime", ingress)
    executor_calls = []
    fake = types.ModuleType("synaptic_host.modal_training")
    fake.execute_modal_training_run_v2 = (
        lambda *_a, **_k: executor_calls.append(True)
    )
    original_import = cli.importlib.import_module

    def importing(name: str, *args, **kwargs):
        if name == "synaptic_host.modal_training":
            object.__setattr__(ingress, "source_sha256", "0" * 64)
            return fake
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli.importlib, "import_module", importing)
    result = cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert executor_calls == []


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
    issue, authenticate, consume = launcher._install_isolated_child_authority_v1()
    monkeypatch.setattr(launcher, "_issue_isolated_child_authority_v1", issue)
    monkeypatch.setattr(
        launcher, "_authenticate_isolated_child_authority_v1", authenticate
    )
    monkeypatch.setattr(launcher, "_consume_isolated_child_authority_v1", consume)
    authority = launcher.ensure_and_reexec(
        project_root=project, engine_root=engine, argv=[], ingress_digest=digest,
        contract_identity_digest="e" * 64,
    )
    assert launcher._authenticate_isolated_child_authority_v1(authority)
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


# --- Section 29.5(a): B-15 recurrence on the modal arm (feature #420). -------


def test_modal_arm_establishes_the_engine_import_root_before_its_import(
    monkeypatch, tmp_path: Path,
) -> None:
    """29.5(a).  The modal arm must establish what the docker arm establishes.

    `cli.py` calls `_establish_engine_import_root` inside the docker branch and
    imports `synaptic_host.docker_training` on the next line.  The modal arm
    imports `synaptic_host.modal_training`, whose module scope imports
    top-level `tuner`, with no establishment anywhere above it.  With
    `PYTHONPATH` never exported (standing rule 21.2) that import dies exactly
    as run 9 died on the other provider, and the ninety-line handler behind it
    reports an opaque failure rather than the missing name.

    The reading is taken AT THE MOMENT OF THE IMPORT rather than after the
    dispatch returns, and that is the point of the fixture: an establishment
    that ran after the import would leave `sys.path` correct at the end and
    still have failed.  `sys.path` is snapshotted through `monkeypatch` so the
    appended entry cannot leak into the rest of the session.
    """

    ingress = _ingress(tmp_path / "ingress")
    authority = _mint_child_authority(monkeypatch, tmp_path / "runtime", ingress)
    engine = tmp_path / "runtime" / "engine"
    monkeypatch.setattr(sys, "path", list(sys.path))

    at_import: list[list[str]] = []
    fake = types.ModuleType("synaptic_host.modal_training")
    fake.execute_modal_training_run_v2 = lambda value, **_kwargs: cli._failure(
        TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED,
        provider_ref=value.provider_ref, config_ref=value.config_ref,
        destination_ref=value.destination_ref, input_digest=value.input_digest,
    )
    original_import = cli.importlib.import_module

    def guarded(name: str, *args, **kwargs):
        if name == "synaptic_host.modal_training":
            at_import.append(list(sys.path))
            return fake
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(cli.importlib, "import_module", guarded)
    cli.dispatch_validated_training_run_v1(
        ingress, isolated_child_authority=authority
    )

    assert at_import, "the modal arm never reached its own import"
    assert str(engine) in at_import[0], (
        "the modal arm imported modal_training with the engine root absent "
        "from sys.path; B-15 recurs on this provider"
    )
    assert at_import[0][-1] == str(engine), (
        "the engine root must be APPENDED, never given precedence (24.3)"
    )


def test_launcher_refusal_at_the_entrypoint_names_its_own_cause(
    monkeypatch, capsys, tmp_path: Path,
) -> None:
    """B-18 fourth site (29.5(b)) and the item 3 disposition under gate G6.

    `__main__.py`'s modal arm wrapped `ensure_and_reexec` in a bare
    `except BaseException` and returned BOOTSTRAP_UNAVAILABLE with the
    exception unbound, unchained and unlogged.  The launcher's own refusals
    are the ones that arrive here -- `launcher.py:628` refuses an allowlisted
    child environment value over the 4096-byte bound, which is exactly what a
    long operator PATH produces (#432) -- so the operator learned that
    bootstrap was unavailable and nothing about which refusal fired.

    The result contract does NOT widen: the envelope is what the run driver
    parses, so the code, the exit status and stdout stay byte-identical and
    the cause goes to stderr on the mechanism 20.11 ruled and 24.4 already
    uses at `cli.py`'s own bare catch.  The exception's CLASS is named and its
    TEXT never is.
    """

    prepared = _ingress(tmp_path)
    fake = types.ModuleType("synaptic_host.launcher")

    def ensure(**_kwargs):
        # The literal refusal at launcher.py:628, reached under a long PATH.
        raise RuntimeError("child environment value is invalid")

    fake.ensure_and_reexec = ensure
    monkeypatch.setitem(sys.modules, "synaptic_host.launcher", fake)
    monkeypatch.setattr(
        entry, "prepare_training_run_ingress_v1", lambda *_a, **_k: prepared
    )

    assert entry.main(["training", "run"]) == 4
    captured = capsys.readouterr()

    # The contract the driver parses is unchanged.
    assert json.loads(captured.out)["code"] == "BOOTSTRAP_UNAVAILABLE"

    # G6: the refusal names its own cause.
    assert "RuntimeError" in captured.err, (
        "the launcher refusal reached the operator unnamed; the fourth "
        "B-18 site still swallows its cause"
    )
    assert "BOOTSTRAP_UNAVAILABLE" in captured.err
    assert "__main__.py" in captured.err, (
        "the cause line must name the frame that decided the refusal"
    )
    # The renderer names the class, never the text (20.11).
    assert "child environment value is invalid" not in captured.err


def test_uv_subprocess_environment_is_a_closed_allowlist(
    monkeypatch, tmp_path: Path,
) -> None:
    """R7, section 29.5(d).  No whole-environment copy to the uv subprocesses.

    `_uv_environment` opened with `dict(os.environ)` and handed the entire
    operator environment to `uv venv` and `uv pip install`.  The submit host
    now holds the provider token pair by user decision, so this is the one
    code path in the package that hands credentials to a third-party process
    tree.  The ruled shape is the closed constructor this file already uses
    for the child environment: a NAMED allowlist, each value validated.

    The assertion is on the KEY SET, never on a value: the test sets its own
    non-secret sentinels and proves they do not cross the boundary.
    """

    uv_keys = {
        "UV_CACHE_DIR", "UV_LINK_MODE", "UV_NO_PROGRESS",
        "UV_PYTHON_INSTALL_DIR", "UV_PYTHON_PREFERENCE",
    }

    # An allowlisted name, an arbitrary operator name, and the credential
    # pair -- all present in the parent environment, all non-secret values.
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SYNAPTIC_R7_OPERATOR_SENTINEL", "sentinel")
    monkeypatch.setenv("MODAL_TOKEN_ID", "sentinel-not-a-credential")
    monkeypatch.setenv("MODAL_TOKEN_SECRET", "sentinel-not-a-credential")

    environment = launcher._uv_environment(tmp_path)
    observed = set(environment)

    allowed = set(launcher._ALLOWED_CHILD_ENV) | uv_keys
    assert observed <= allowed, (
        "the uv subprocesses receive names outside the allowlist: {}".format(
            sorted(observed - allowed)
        )
    )
    assert uv_keys <= observed, "the uv settings must still be applied"
    assert "PATH" in environment, "uv needs the allowlisted PATH"

    # The two findings the ruling names, stated separately so a failure says
    # which one recurred.
    assert "SYNAPTIC_R7_OPERATOR_SENTINEL" not in environment
    for name in launcher._MODAL_CREDENTIAL_ENV:
        assert name not in environment, (
            "the provider credential pair reaches the uv process tree; R7 "
            "recurs"
        )
