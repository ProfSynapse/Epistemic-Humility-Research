from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import TrainingInputV1

from synaptic_host import docker_model_inventory as inventory_module
from synaptic_host.docker_model_inventory import resolve_docker_model_inventory_v1
from synaptic_host.docker_provider import DockerProviderProfileV1


REVISION = "12fd25f77366fa6b3b4b768ec3050bf629380bac"
ROOT_REF = "docker-model-inventory-source"


def _training_input(
    *,
    model_ref: str = "HuggingFaceTB/SmolLM2-135M-Instruct",
    revision: str = REVISION,
    tokenizer_revision: str = REVISION,
) -> TrainingInputV1:
    return TrainingInputV1.from_dict(
        {
            "schema_version": "synaptic-training-input/v1",
            "method": "sft",
            "model": {
                "ref": model_ref,
                "revision": revision,
                "tokenizer_revision": tokenizer_revision,
            },
            "dataset": {"ref": "project://training/input/data.jsonl"},
            "hyperparameters": {
                "schema_version": "synaptic-sft-hyperparameters/v1",
                "batch_size": 1,
                "gradient_accumulation_steps": 1,
                "learning_rate": 0.0002,
                "duration": {"max_steps": 1, "num_epochs": None},
                "max_seq_length": 128,
                "seed": 1,
                "save_steps": 1,
                "save_total_limit": 1,
                "lora_rank": 8,
                "lora_alpha": 16,
                "lora_dropout": 0.0,
                "lora_target_modules": ["q_proj"],
                "use_dora": False,
                "use_rslora": False,
                "init_lora_weights": True,
                "split_dataset": False,
            },
            "artifacts": {
                "required_kinds": ["final_model"],
                "retain_checkpoints": False,
            },
        }
    )


def _profile(*, cache_admission: bool = True) -> DockerProviderProfileV1:
    return DockerProviderProfileV1.from_mapping(
        {
            "schema_version": "synaptic-docker-host/v1",
            "profile_ref": "docker-sft-test",
            "runtime": {
                "image": "example.invalid/trainer@sha256:" + "a" * 64,
                "dependency_lock_digest": "b" * 64,
                "python_implementation": "cpython",
                "python_version": "3.12.7",
                "python_executable": "/usr/bin/python3",
                "python_executable_digest": "c" * 64,
            },
            "capabilities": {
                "supported_methods": ["sft"],
                "workload_transport": "sealed_file",
                "source_mode": "dual_clone_read_only",
            },
            "model": {
                "load_in_4bit": False,
                "inventory_root_ref": ROOT_REF,
            },
            "accelerator": {"allowed": ["nvidia"], "count_maximum": 1},
            "resources": {
                "cpu_count": 1,
                "timeout_seconds_maximum": 60,
                "memory_bytes_maximum": 1024,
            },
            "network": {"mode": "none"},
            "docker_host": {
                "policy_ref": "docker-test-policy",
                "wsl_distro": "Ubuntu-22.04",
                "drive_mount_root": "/mnt",
                "container_user": "1000:1000",
            },
            "artifacts": {
                "maximum_artifact_bytes": 1,
                "maximum_total_bytes": 1,
                "cache_admission": cache_admission,
            },
        }
    )


def _storage_bytes(
    *,
    location: str = "project://.synaptic/model-inventory",
    access: str = "read_only",
    permit_ref: str = "permit-docker-model-inventory-source",
) -> bytes:
    return json.dumps(
        {
            "schema_version": "synaptic-host-storage/v1",
            "roots": [
                {
                    "root_ref": ROOT_REF,
                    "location": location,
                    "access": access,
                    "permit_ref": permit_ref,
                }
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _snapshot(project_root: Path) -> Path:
    path = (
        project_root
        / ".synaptic"
        / "model-inventory"
        / "models--HuggingFaceTB--SmolLM2-135M-Instruct"
        / "snapshots"
        / REVISION
    )
    path.mkdir(parents=True)
    return path


def _resolve(project_root: Path, **kwargs):
    return resolve_docker_model_inventory_v1(
        training_input=kwargs.pop("training_input", _training_input()),
        profile=kwargs.pop("profile", _profile()),
        storage_configuration=kwargs.pop("storage_configuration", _storage_bytes()),
        project_root=project_root,
        **kwargs,
    )


def test_resolves_exact_snapshot_as_sorted_staged_descriptors(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    (snapshot / "tokenizer").mkdir()
    (snapshot / "z.bin").write_bytes(b"model")
    (snapshot / "tokenizer" / "a.json").write_bytes(b"tokenizer")

    entries = _resolve(tmp_path)

    prefix = f"model/models--HuggingFaceTB--SmolLM2-135M-Instruct/snapshots/{REVISION}"
    assert tuple(item.relative_path for item in entries) == (
        f"{prefix}/tokenizer/a.json",
        f"{prefix}/z.bin",
    )
    assert tuple(item.source_path for item in entries) == (
        (snapshot / "tokenizer" / "a.json").absolute(),
        (snapshot / "z.bin").absolute(),
    )
    assert entries[0].byte_count == len(b"tokenizer")
    assert entries[0].sha256 == hashlib.sha256(b"tokenizer").hexdigest()


def test_committed_storage_declares_private_read_only_inventory_root() -> None:
    root = Path(__file__).resolve().parents[2]
    value = json.loads((root / "training" / "storage.json").read_text("utf-8"))
    matches = [item for item in value["roots"] if item["root_ref"] == ROOT_REF]
    assert matches == [
        {
            "root_ref": ROOT_REF,
            "location": "project://.synaptic/model-inventory",
            "access": "read_only",
            "permit_ref": "permit-docker-model-inventory-source",
        }
    ]
    assert ".synaptic/" in (root / ".gitignore").read_text("utf-8")


@pytest.mark.parametrize(
    ("field", "value"),
    (("cache", False), ("network", "bridge"), ("root_ref", "other-root")),
)
def test_rejects_nonadmitted_or_nonoffline_profile(
    tmp_path: Path, field: str, value: object
) -> None:
    profile = _profile(cache_admission=bool(value) if field == "cache" else True)
    if field == "network":
        object.__setattr__(profile, "network_mode", value)
    elif field == "root_ref":
        object.__setattr__(profile, "inventory_root_ref", value)
    with pytest.raises(ValueError):
        _resolve(tmp_path, profile=profile)


def test_rejects_model_tokenizer_revision_mismatch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="revisions must be identical"):
        _resolve(
            tmp_path,
            training_input=_training_input(tokenizer_revision="a" * 40),
        )


@pytest.mark.parametrize(
    "training_input",
    (
        _training_input(revision="main", tokenizer_revision="main"),
        _training_input(model_ref="owner/repo/extra"),
        _training_input(model_ref="owner--ambiguous/repo"),
    ),
)
def test_rejects_nonexact_revision_or_noncanonical_repository(
    tmp_path: Path, training_input: TrainingInputV1
) -> None:
    with pytest.raises(ValueError):
        _resolve(tmp_path, training_input=training_input)


@pytest.mark.parametrize(
    "storage_configuration",
    (
        b"{}",
        _storage_bytes(location="project://elsewhere"),
        _storage_bytes(access="read_create"),
        _storage_bytes(permit_ref="permit-other"),
    ),
)
def test_rejects_invalid_or_misdirected_storage_binding(
    tmp_path: Path, storage_configuration: bytes
) -> None:
    with pytest.raises((RuntimeError, ValueError)):
        _resolve(tmp_path, storage_configuration=storage_configuration)


def test_rejects_missing_and_empty_snapshot(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unavailable"):
        _resolve(tmp_path)
    _snapshot(tmp_path)
    with pytest.raises(ValueError, match="empty"):
        _resolve(tmp_path)


def test_rejects_case_colliding_paths(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    (snapshot / "ss").write_bytes(b"one")
    (snapshot / "ß").write_bytes(b"two")
    with pytest.raises(ValueError, match="case-colliding"):
        _resolve(tmp_path)


def test_rejects_symlinked_snapshot_member(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    target = snapshot / "target.bin"
    target.write_bytes(b"target")
    try:
        (snapshot / "redirect.bin").symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ValueError, match="redirect"):
        _resolve(tmp_path)


@pytest.mark.skipif(os.name == "nt", reason="FIFO fixture requires POSIX")
def test_rejects_special_snapshot_member(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    os.mkfifo(snapshot / "special")
    with pytest.raises(ValueError, match="special"):
        _resolve(tmp_path)


def test_rejects_file_identity_drift_while_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    snapshot = _snapshot(tmp_path)
    source = snapshot / "model.bin"
    source.write_bytes(b"x" * (1024 * 1024 + 1))
    original_read = inventory_module.os.read
    changed = False

    def drifting_read(descriptor: int, count: int) -> bytes:
        nonlocal changed
        chunk = original_read(descriptor, count)
        if chunk and not changed:
            changed = True
            current = source.stat().st_mtime_ns
            os.utime(source, ns=(current + 1_000_000_000, current + 1_000_000_000))
        return chunk

    monkeypatch.setattr(inventory_module.os, "read", drifting_read)
    with pytest.raises(ValueError, match="changed during its exact read"):
        _resolve(tmp_path)


def test_rejects_inventory_above_bound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    snapshot = _snapshot(tmp_path)
    (snapshot / "one").write_bytes(b"1")
    (snapshot / "two").write_bytes(b"2")
    monkeypatch.setattr(inventory_module, "_MAX_INVENTORY_FILES", 1)
    with pytest.raises(ValueError, match="file limit"):
        _resolve(tmp_path)


def test_requires_exact_public_input_and_storage_bytes(tmp_path: Path) -> None:
    with pytest.raises(TypeError, match="exact TrainingInputV1"):
        resolve_docker_model_inventory_v1(
            training_input=object(),  # type: ignore[arg-type]
            profile=_profile(),
            storage_configuration=_storage_bytes(),
            project_root=tmp_path,
        )
    with pytest.raises(TypeError, match="exact bytes"):
        resolve_docker_model_inventory_v1(
            training_input=_training_input(),
            profile=_profile(),
            storage_configuration=bytearray(_storage_bytes()),  # type: ignore[arg-type]
            project_root=tmp_path,
        )
