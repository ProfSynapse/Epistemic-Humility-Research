"""Installed-consumer checks; no provider, ML runtime, or restricted rows."""

import ast
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from engine_host.cli_boundary import EngineCLI
from engine_host.engine_identity import inspect_engine
from engine_host.generation_log import open_generation_runlog
from engine_host.runlog import RunLog, RunLogError
from engine_host.training_request import load_training_input
from synaptic_tuner.api.v1 import (
    SFTTrainingHyperparametersV1, TrainingArtifactRequirementsV1,
    TrainingDatasetInputV1, TrainingDurationV1, TrainingInputV1,
    TrainingMethodV1, TrainingModelInputV1,
)


@pytest.fixture
def project(tmp_path):
    wheel_sha = yaml.safe_load((Path(__file__).resolve().parents[4] / "synaptic.yaml").read_text())["engine"]["wheel_sha256"]
    manifest = {"schema_version": "synaptic-project/v1",
                "project": {"id": "fixture", "name": "Fixture"},
                "engine": {"requires": ">=1.1.0rc1,<2", "api": "v1", "cli_requires": "==1.1.0rc1",
                           "wheel_sha256": wheel_sha}}
    (tmp_path / "synaptic.yaml").write_text(yaml.safe_dump(manifest))
    return tmp_path


def test_installed_engine_neutral_directory(project):
    result = subprocess.run([sys.executable, "-I", "-m", "engine_host",
                             "--project-root", str(project), "doctor"],
                            cwd=project, check=True, text=True, capture_output=True)
    identity = json.loads(result.stdout)
    assert identity["api"] == "v1"
    assert "site-packages" in identity["package_path"]
    assert identity["backend_qualification"] == "not-established-by-import"


def test_explicit_prerelease_admission(project):
    document = yaml.safe_load((project / "synaptic.yaml").read_text())
    document["engine"]["requires"] = ">=1,<2"
    (project / "synaptic.yaml").write_text(yaml.safe_dump(document))
    with pytest.raises(ValueError, match="requirement"):
        inspect_engine(project)


def test_public_training_input_roundtrip(tmp_path):
    request = public_request()
    path = tmp_path / "input.json"
    path.write_text(request.canonical_json())
    assert load_training_input(path) == request
    assert load_training_input(path).input_digest() == request.input_digest()
    document = request.to_dict()
    document["method"] = "kto"
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError):
        load_training_input(path)


def test_cli_preserves_explicit_launch_acknowledgments(project):
    boundary = EngineCLI(project)
    args = ["steer", "--mi-config", "project://cell.yaml", "--i-know-this-runs-on-gpu"]
    command = boundary.command("mechinterp", args)
    assert command[:4] == [sys.executable, "-m", "tuner", "mechinterp"]
    assert command.count("--i-know-this-runs-on-gpu") == 1
    assert "--yes" not in command
    assert "--i-know-this-runs-on-gpu" not in boundary.command("mechinterp", ["list-configs"])


@pytest.mark.parametrize("arguments", [["steer", "--project-root=/elsewhere"], ["steer", "--env-file", "secret"],
                                      ["list-configs", "--env-fi", "secret"], ["list-configs", "--base-d=/elsewhere"]])
def test_cli_cannot_override_host_selection(project, arguments):
    with pytest.raises(ValueError, match="selection"):
        EngineCLI(project).command("mechinterp", arguments)


def test_cli_refuses_training_through_legacy_boundary(project):
    with pytest.raises(ValueError, match="public APIs"):
        EngineCLI(project).command("train", [])


def test_cli_requires_separate_exact_pin(project):
    document = yaml.safe_load((project / "synaptic.yaml").read_text())
    document["engine"].pop("cli_requires")
    (project / "synaptic.yaml").write_text(yaml.safe_dump(document))
    with pytest.raises(ValueError, match="exact engine version"):
        EngineCLI(project)


def test_cli_clears_engine_pythonpath(project, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "/old/synaptic-tuner")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs)))
    EngineCLI(project).run("mechinterp", ["list-configs"])
    assert "PYTHONPATH" not in calls[0][1]["env"]
    assert calls[0][1]["cwd"] == project


def test_real_installed_manifest_validation(project):
    result = subprocess.run(EngineCLI(project).command("project", ["validate", "--json"]),
                            cwd=project, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["data"]["valid"] is True


def test_installed_cpu_pipeline_from_host(project):
    config = {"schema_version": "mechinterp-pipeline/v1", "name": "installed-host-smoke",
              "runtime": {"provider": "local", "python": sys.executable},
              "stages": [{"name": "identity", "kind": "command",
                          "command": [sys.executable, "-I", "-m", "engine_host", "doctor"]}]}
    (project / "smoke.yaml").write_text(yaml.safe_dump(config))
    command = EngineCLI(project).command("mechinterp", ["run", "--config", "project://smoke.yaml", "--dry-run", "--json"])
    result = subprocess.run(command, cwd=project, text=True, capture_output=True, check=True)
    assert "identity" in result.stdout
    command = EngineCLI(project).command("mechinterp", ["run", "--config", "project://smoke.yaml", "--provider", "local", "--yes"])
    result = subprocess.run(command, cwd=project, text=True, capture_output=True, check=True)
    assert '"project_id": "fixture"' in result.stdout


def test_runlog_resumes_torn_tail(tmp_path):
    path = tmp_path / "rows.jsonl"
    with open_generation_runlog(path, {"fixture": 1}) as log:
        log.record("one", {"out_text": "synthetic answer"})
    with path.open("ab") as stream:
        stream.write(b'{"unfinished":')
    with open_generation_runlog(path, {"fixture": 1}) as log:
        assert "one" in log.done_keys()
        log.record("two", {"out_text": "another synthetic answer"})
    assert len(path.read_text().splitlines()) == 2


def test_generation_text_and_fingerprint_are_enforced(tmp_path):
    path = tmp_path / "rows.jsonl"
    with open_generation_runlog(path, {"fixture": 1}) as log:
        with pytest.raises(RunLogError):
            log.record("one", {"score": 1})
    with pytest.raises(RunLogError):
        RunLog(path, {"fixture": 2})
    with pytest.raises(RunLogError):
        open_generation_runlog(tmp_path / "other.jsonl", {}, textless_reason=" ")


def test_new_host_does_not_import_engine_internals():
    import engine_host
    forbidden = {"tuner", "shared", "MechInterp", "Evaluator", "SynthChat", "Trainers"}
    for path in Path(engine_host.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            modules = ([node.module] if isinstance(node, ast.ImportFrom) else
                       [item.name for item in node.names] if isinstance(node, ast.Import) else [])
            assert all(module and module.split(".")[0] not in forbidden for module in modules if module)


def test_installed_host_bytes_match_reviewed_sources():
    source = Path(__file__).resolve().parents[1]
    import engine_host
    for path in source.glob("*.py"):
        installed = Path(engine_host.__file__).parent / path.name
        assert installed.read_bytes() == path.read_bytes(), f"reinstall host before testing {path.name}"


def test_exact_wheel_pin_and_package_shadowing(project):
    manifest_path = project / "synaptic.yaml"
    document = yaml.safe_load(manifest_path.read_text())
    document["engine"]["wheel_sha256"] = "0" * 64
    manifest_path.write_text(yaml.safe_dump(document))
    with pytest.raises(ValueError, match="reviewed wheel"):
        inspect_engine(project)
    document["engine"].pop("wheel_sha256")
    manifest_path.write_text(yaml.safe_dump(document))
    with pytest.raises(ValueError, match="reviewed engine.wheel_sha256"):
        EngineCLI(project)
    document["engine"]["wheel_sha256"] = yaml.safe_load((Path(__file__).resolve().parents[4] / "synaptic.yaml").read_text())["engine"]["wheel_sha256"]
    manifest_path.write_text(yaml.safe_dump(document))
    (project / "tuner.py").write_text("raise RuntimeError('must not import')")
    with pytest.raises(ValueError, match="shadows"):
        EngineCLI(project)


def test_weights_verbs_reach_actual_installed_parser(project):
    for verb in ("weights-inspect", "weights-patch"):
        result = subprocess.run(EngineCLI(project).command("mechinterp", [verb, "--help"]),
                                cwd=project, capture_output=True, text=True, check=True)
        assert "--weights-config" in result.stdout


def test_actual_manifest_and_engine_build():
    root = Path(__file__).resolve().parents[4]
    identity = inspect_engine(root)
    assert identity["wheel_pin_verified"] is True
    assert identity["installed_files_verified"] is True
    result = subprocess.run(EngineCLI(root).command("project", ["validate", "--json"]),
                            cwd=root, capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["data"]["valid"] is True


def test_storage_rejects_off_drive_and_configures_cache_on_selected_volume(tmp_path):
    from engine_host.storage import configure_storage, local_model
    mount = tmp_path / "t7"
    root = mount / "project"
    snapshot = mount / "models" / "snapshot"
    root.mkdir(parents=True)
    snapshot.mkdir(parents=True)
    config = tmp_path / "host.yaml"
    document = {"schema_version": "ehr-desktop-host/v1",
                "storage": {"wsl_mount": str(mount), "model_root": str(mount / "models")},
                "base_model": {"repo": "fixture/model", "revision": "a" * 40, "local_snapshot": str(snapshot)}}
    config.write_text(yaml.safe_dump(document))
    values = configure_storage(root, config)
    assert Path(values["HF_HOME"]).is_relative_to(mount)
    assert Path(values["HF_HUB_CACHE"]).is_dir()
    assert local_model(config, "fixture/model", "a" * 40) == str(snapshot)
    with pytest.raises(ValueError, match="selected T7"):
        configure_storage(tmp_path / "off-drive", config)
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / ".synaptic" / "artifacts").rmdir()
    (root / ".synaptic" / "artifacts").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        configure_storage(root, config)


def test_plan_training_calls_public_facade_only(tmp_path, monkeypatch):
    from engine_host.training_request import plan_training
    from synaptic_tuner.api.v1 import ProviderRef, TrainingAPI
    # Construct the real facade identity while replacing its public operations
    # with recording fakes; no provider, authority or runtime can be invoked.
    api = object.__new__(TrainingAPI)
    calls = []
    monkeypatch.setattr(TrainingAPI, "load", lambda self, value: calls.append(("load", value)) or "loaded")
    monkeypatch.setattr(TrainingAPI, "resolve", lambda self, value: calls.append(("resolve", value)) or "resolved")
    monkeypatch.setattr(TrainingAPI, "plan", lambda self, value, provider: calls.append(("plan", value, provider)) or "planned")
    request = public_request()
    provider = ProviderRef("fixture", "fixture-profile")
    assert plan_training(api, request, provider) == "planned"
    assert [call[0] for call in calls] == ["load", "resolve", "plan"]


def public_request():
    return TrainingInputV1(
        schema_version="synaptic-training-input/v1", method=TrainingMethodV1.SFT,
        model=TrainingModelInputV1("fixture/model", "a" * 40, "a" * 40),
        dataset=TrainingDatasetInputV1("prepared://sha256/" + "0" * 64),
        hyperparameters=SFTTrainingHyperparametersV1(
            batch_size=1, gradient_accumulation_steps=1, learning_rate=0.0001,
            duration=TrainingDurationV1(3, None), max_seq_length=128, seed=17,
            save_steps=3, save_total_limit=1, lora_rank=4, lora_alpha=8,
            lora_dropout=0, lora_target_modules=("q_proj", "v_proj"),
            use_dora=False, use_rslora=False, init_lora_weights=True, split_dataset=False),
        artifacts=TrainingArtifactRequirementsV1(("final_model",), False))


def test_legacy_and_host_generation_logs_resume_with_same_fingerprint(tmp_path):
    import importlib.util
    legacy_path = Path(__file__).resolve().parents[2] / "runlog_contract.py"
    spec = importlib.util.spec_from_file_location("legacy_contract", legacy_path)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    path = tmp_path / "legacy.jsonl"
    with legacy.open_generation_runlog(path, {"synthetic": True}, run_log_cls=RunLog) as log:
        log.record("one", {"out_text": "synthetic response"})
    with open_generation_runlog(path, {"synthetic": True}) as log:
        assert log.done_keys() == {"one"}
        log.record("two", {"out_text": "second synthetic response"})
    with legacy.open_generation_runlog(path, {"synthetic": True}, run_log_cls=RunLog) as log:
        assert log.done_keys() == {"one", "two"}


def test_configured_snapshot_hash_is_verified(tmp_path):
    import hashlib
    from engine_host.storage import local_model
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "model.safetensors").write_bytes(b"synthetic fixture")
    document = {"schema_version": "ehr-desktop-host/v1", "storage": {"wsl_mount": str(tmp_path)},
                "base_model": {"repo": "fixture/model", "revision": "a" * 40,
                               "local_snapshot": str(snapshot), "shard_sha256": {"model.safetensors": "0" * 64}}}
    config = tmp_path / "host.yaml"
    config.write_text(yaml.safe_dump(document))
    with pytest.raises(ValueError, match="shard hash mismatch"):
        local_model(config, "fixture/model", "a" * 40)
    document["base_model"]["shard_sha256"]["model.safetensors"] = hashlib.sha256(b"synthetic fixture").hexdigest()
    config.write_text(yaml.safe_dump(document))
    assert local_model(config, "fixture/model", "a" * 40) == str(snapshot)
