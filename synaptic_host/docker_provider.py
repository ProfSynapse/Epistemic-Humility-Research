"""Declarative Host policy for canonical Docker training admission."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


_SCHEMA = "synaptic-docker-host/v1"
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_IMAGE = re.compile(r"^\S+@sha256:[0-9a-f]{64}$")
_PYTHON = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
_REF = re.compile(r"^[a-z0-9][a-z0-9._/-]{0,127}$")
_DISTRO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_BYTES = 64 * 1024


def _object(value: object, fields: frozenset[str], label: str) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != fields:
        raise ValueError(f"{label} contains missing or unknown fields")
    return {key: dict.__getitem__(value, key) for key in dict.keys(value)}


def _text(value: object, label: str, *, pattern: re.Pattern[str] | None = None) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{label} must be canonical nonblank text")
    if len(value.encode("utf-8")) > 512 or (pattern is not None and pattern.fullmatch(value) is None):
        raise ValueError(f"{label} is invalid")
    return value


def _bounded_integer(value: object, label: str, *, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{label} is outside its admitted bounds")
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must be an exact list")
    items = tuple(_text(item, label, pattern=_REF) for item in value)
    if items != tuple(sorted(items)) or len(items) != len(set(items)):
        raise ValueError(f"{label} must be unique and ascending")
    return items


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("Docker provider JSON contains duplicate or invalid fields")
        result[key] = value
    return result


def _read_json_bytes(raw: bytes) -> dict[str, object]:
    try:
        if type(raw) is not bytes or not raw or len(raw) > _MAX_BYTES:
            raise ValueError
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except Exception:
        raise ValueError("Docker provider configuration is unavailable or invalid") from None
    if type(value) is not dict:
        raise ValueError("Docker provider configuration must be an exact object")
    return value


@dataclass(frozen=True, slots=True)
class DockerProviderProfileV1:
    profile_ref: str
    image: str
    dependency_lock_digest: str
    python_implementation: str
    python_version: str
    python_executable: str
    python_executable_digest: str
    load_in_4bit: bool
    inventory_root_ref: str
    supported_methods: tuple[str, ...]
    workload_transport: str
    source_mode: str
    accelerators: tuple[str, ...]
    accelerator_count_maximum: int
    cpu_count: int
    timeout_seconds_maximum: int
    memory_bytes_maximum: int
    network_mode: str
    docker_policy_ref: str
    wsl_distro: str
    maximum_artifact_bytes: int
    maximum_total_bytes: int
    cache_admission: bool

    def __post_init__(self) -> None:
        _text(self.profile_ref, "profile_ref", pattern=_REF)
        _text(self.image, "runtime.image", pattern=_IMAGE)
        _text(self.dependency_lock_digest, "runtime.dependency_lock_digest", pattern=_DIGEST)
        if self.python_implementation != "cpython":
            raise ValueError("runtime.python_implementation must be cpython")
        _text(self.python_version, "runtime.python_version", pattern=_PYTHON)
        if type(self.python_executable) is not str or not self.python_executable.startswith("/"):
            raise ValueError("runtime.python_executable must be an absolute provider path")
        _text(self.python_executable_digest, "runtime.python_executable_digest", pattern=_DIGEST)
        if type(self.load_in_4bit) is not bool:
            raise TypeError("model.load_in_4bit must be an exact boolean")
        _text(self.inventory_root_ref, "model.inventory_root_ref", pattern=_REF)
        if self.supported_methods != tuple(sorted(self.supported_methods)):
            raise ValueError("supported_methods must be unique and ascending")
        if self.workload_transport != "sealed_file" or self.source_mode != "dual_clone_read_only":
            raise ValueError("Docker source and workload transports are unsupported")
        if not self.accelerators or self.accelerators != tuple(sorted(self.accelerators)):
            raise ValueError("accelerator policy is invalid")
        if self.cpu_count != 1:
            raise ValueError("Docker admission requires exactly one CPU")
        if self.network_mode != "none":
            raise ValueError("Docker admission requires network_mode none")
        _text(self.docker_policy_ref, "docker_policy_ref", pattern=_REF)
        _text(self.wsl_distro, "docker_host.wsl_distro", pattern=_DISTRO)
        if type(self.cache_admission) is not bool:
            raise TypeError("cache_admission must be an exact boolean")
        if self.maximum_artifact_bytes > self.maximum_total_bytes:
            raise ValueError("artifact byte bounds are invalid")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "DockerProviderProfileV1":
        root = _object(
            value,
            frozenset({
                "schema_version", "profile_ref", "runtime", "capabilities",
                "model", "accelerator", "resources", "network", "docker_host", "artifacts",
            }),
            "Docker provider profile",
        )
        if root["schema_version"] != _SCHEMA:
            raise ValueError("unsupported Docker provider profile schema")
        runtime = _object(root["runtime"], frozenset({
            "image", "dependency_lock_digest", "python_implementation", "python_version",
            "python_executable", "python_executable_digest",
        }), "Docker runtime")
        capabilities = _object(root["capabilities"], frozenset({
            "supported_methods", "workload_transport", "source_mode",
        }), "Docker capabilities")
        model = _object(root["model"], frozenset({
            "load_in_4bit", "inventory_root_ref",
        }), "Docker model policy")
        accelerator = _object(root["accelerator"], frozenset({
            "allowed", "count_maximum",
        }), "Docker accelerator policy")
        resources = _object(root["resources"], frozenset({
            "cpu_count", "timeout_seconds_maximum", "memory_bytes_maximum",
        }), "Docker resource policy")
        network = _object(root["network"], frozenset({"mode"}), "Docker network policy")
        docker_host = _object(root["docker_host"], frozenset({
            "policy_ref", "wsl_distro",
        }), "Docker Host policy")
        artifacts = _object(root["artifacts"], frozenset({
            "maximum_artifact_bytes", "maximum_total_bytes", "cache_admission",
        }), "Docker artifact policy")
        return cls(
            _text(root["profile_ref"], "profile_ref", pattern=_REF),
            _text(runtime["image"], "runtime.image", pattern=_IMAGE),
            _text(runtime["dependency_lock_digest"], "runtime.dependency_lock_digest", pattern=_DIGEST),
            _text(runtime["python_implementation"], "runtime.python_implementation"),
            _text(runtime["python_version"], "runtime.python_version", pattern=_PYTHON),
            _text(runtime["python_executable"], "runtime.python_executable"),
            _text(runtime["python_executable_digest"], "runtime.python_executable_digest", pattern=_DIGEST),
            model["load_in_4bit"],
            _text(model["inventory_root_ref"], "model.inventory_root_ref", pattern=_REF),
            _string_tuple(capabilities["supported_methods"], "supported_methods"),
            _text(capabilities["workload_transport"], "workload_transport"),
            _text(capabilities["source_mode"], "source_mode"),
            _string_tuple(accelerator["allowed"], "accelerator.allowed"),
            _bounded_integer(accelerator["count_maximum"], "accelerator.count_maximum", minimum=1, maximum=64),
            _bounded_integer(resources["cpu_count"], "resources.cpu_count", minimum=1, maximum=1),
            _bounded_integer(resources["timeout_seconds_maximum"], "timeout_seconds_maximum", minimum=1, maximum=86400),
            _bounded_integer(resources["memory_bytes_maximum"], "memory_bytes_maximum", minimum=1, maximum=2**63 - 1),
            _text(network["mode"], "network.mode"),
            _text(docker_host["policy_ref"], "docker_host.policy_ref", pattern=_REF),
            _text(docker_host["wsl_distro"], "docker_host.wsl_distro", pattern=_DISTRO),
            _bounded_integer(artifacts["maximum_artifact_bytes"], "maximum_artifact_bytes", minimum=1, maximum=2**63 - 1),
            _bounded_integer(artifacts["maximum_total_bytes"], "maximum_total_bytes", minimum=1, maximum=2**63 - 1),
            artifacts["cache_admission"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": _SCHEMA,
            "profile_ref": self.profile_ref,
            "runtime": {
                "image": self.image,
                "dependency_lock_digest": self.dependency_lock_digest,
                "python_implementation": self.python_implementation,
                "python_version": self.python_version,
                "python_executable": self.python_executable,
                "python_executable_digest": self.python_executable_digest,
            },
            "model": {
                "load_in_4bit": self.load_in_4bit,
                "inventory_root_ref": self.inventory_root_ref,
            },
            "capabilities": {
                "supported_methods": list(self.supported_methods),
                "workload_transport": self.workload_transport,
                "source_mode": self.source_mode,
            },
            "accelerator": {
                "allowed": list(self.accelerators),
                "count_maximum": self.accelerator_count_maximum,
            },
            "resources": {
                "cpu_count": self.cpu_count,
                "timeout_seconds_maximum": self.timeout_seconds_maximum,
                "memory_bytes_maximum": self.memory_bytes_maximum,
            },
            "network": {"mode": self.network_mode},
            "docker_host": {
                "policy_ref": self.docker_policy_ref,
                "wsl_distro": self.wsl_distro,
            },
            "artifacts": {
                "maximum_artifact_bytes": self.maximum_artifact_bytes,
                "maximum_total_bytes": self.maximum_total_bytes,
                "cache_admission": self.cache_admission,
            },
        }

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            _SCHEMA.encode("ascii") + b"\0" + json.dumps(
                self.to_dict(), sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()

    def supports(self, method: str) -> bool:
        return type(method) is str and method in self.supported_methods

    @classmethod
    def load(cls, *, project_root: Path) -> "DockerProviderProfileV1":
        root = Path(project_root).resolve(strict=True)
        path = root / "training" / "providers" / "docker.json"
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to((root / "training").resolve(strict=True)):
            raise ValueError("Docker provider profile must live below training")
        return cls.from_bytes(resolved.read_bytes())

    @classmethod
    def from_bytes(cls, raw: bytes) -> "DockerProviderProfileV1":
        return cls.from_mapping(_read_json_bytes(raw))


__all__ = ["DockerProviderProfileV1"]
