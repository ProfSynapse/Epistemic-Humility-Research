from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import re

from synaptic_host.bundle_io_v1.model import digest_v1
from .model import (
    DockerCLICommandV1,
    DockerCLIOutcomeV1,
    DockerCLIResultV1,
    DockerCLIVerbV1,
    DockerPlatformCodeV1,
    DockerPlatformErrorV1,
)

OWNED_LABEL_PREFIX_V1 = "ai.synapticlabs.tuner.v1."
OWNED_LABEL_NAMES_V1 = (
    "command-digest", "provider-id", "profile-ref", "account-ref", "namespace-ref",
    "project-ref", "run-id", "plan-fingerprint", "preparation-digest", "effect-id",
    "effect-kind", "effect-identity-digest", "adapter-descriptor-digest",
    "labels-digest", "schema-version",
)
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_NAME = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}\Z")

def _bad():
    raise DockerPlatformErrorV1(DockerPlatformCodeV1.OUTPUT_INVALID) from None


def _sha(value):
    if type(value) is not str or _SHA.fullmatch(value) is None:
        _bad()


def _check_digest(value):
    _sha(value.projection_digest)
    if value.projection_digest != digest_v1(value.canonical_without_digest()):
        _bad()

class DockerTypedResultKindV1(str, Enum):
    IMAGE_INSPECT = "IMAGE_INSPECT"
    CONTAINER_INSPECT = "CONTAINER_INSPECT"
    EXACT_NAME_INVENTORY = "EXACT_NAME_INVENTORY"
    CREATE_EXECUTION = "CREATE_EXECUTION"
    START_EXECUTION = "START_EXECUTION"

class DockerContainerStatusV1(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    EXITED = "exited"
    DEAD = "dead"

def docker_typed_request_digest_v1(kind, target, command_digest):
    try:
        if (
            type(kind) is not DockerTypedResultKindV1
            or type(target) is not str
            or not target
        ):
            raise ValueError
        _sha(command_digest)
        return digest_v1({
            "command_digest": command_digest,
            "kind": kind.value,
            "schema_version": "synaptic-host-docker-typed-request/v1",
            "target": target,
        })
    except DockerPlatformErrorV1:
        raise
    except BaseException:
        _bad()


def docker_create_execution_request_digest_v1(target, command_digest):
    return docker_typed_request_digest_v1(
        DockerTypedResultKindV1.CREATE_EXECUTION, target, command_digest
    )


def docker_start_execution_request_digest_v1(target, command_digest):
    return docker_typed_request_digest_v1(
        DockerTypedResultKindV1.START_EXECUTION, target, command_digest
    )


@dataclass(frozen=True, slots=True)
class DockerCreateExecutionProjectionV1:
    container_ref: str
    request_digest: str
    command_digest: str
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "command_digest": self.command_digest,
            "container_ref": self.container_ref,
            "request_digest": self.request_digest,
            "schema_version": "synaptic-host-docker-create-execution-projection/v1",
        }

    def __post_init__(self):
        _sha(self.container_ref)
        _sha(self.request_digest)
        _sha(self.command_digest)
        _check_digest(self)

    @classmethod
    def build(cls, container_ref, request_digest, command_digest):
        body = {
            "command_digest": command_digest,
            "container_ref": container_ref,
            "request_digest": request_digest,
            "schema_version": "synaptic-host-docker-create-execution-projection/v1",
        }
        return cls(
            container_ref, request_digest, command_digest, digest_v1(body)
        )

@dataclass(frozen=True, slots=True)
class DockerLabelProjectionV1:
    name: str
    value_digest: str
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "name": self.name,
            "schema_version": "synaptic-host-docker-label-projection/v1",
            "value_digest": self.value_digest,
        }

    def __post_init__(self):
        if self.name not in OWNED_LABEL_NAMES_V1:
            _bad()
        _sha(self.value_digest)
        _check_digest(self)

    @classmethod
    def build(cls, name, value_digest):
        body = {
            "name": name,
            "schema_version": "synaptic-host-docker-label-projection/v1",
            "value_digest": value_digest,
        }
        return cls(name, value_digest, digest_v1(body))

@dataclass(frozen=True, slots=True)
class DockerEnvironmentEntryProjectionV1:
    key_digest: str
    value_digest: str
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "key_digest": self.key_digest,
            "schema_version": "synaptic-host-docker-environment-entry/v1",
            "value_digest": self.value_digest,
        }

    def __post_init__(self):
        _sha(self.key_digest)
        _sha(self.value_digest)
        _check_digest(self)

    @classmethod
    def build(cls, key_digest, value_digest):
        body = {
            "key_digest": key_digest,
            "schema_version": "synaptic-host-docker-environment-entry/v1",
            "value_digest": value_digest,
        }
        return cls(key_digest, value_digest, digest_v1(body))

@dataclass(frozen=True, slots=True)
class DockerEnvironmentProjectionV1:
    entries: tuple[DockerEnvironmentEntryProjectionV1, ...]
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "entries": [item.projection_digest for item in self.entries],
            "schema_version": "synaptic-host-docker-environment/v1",
        }

    def __post_init__(self):
        if (
            type(self.entries) is not tuple
            or len(self.entries) > 256
            or any(
                type(item) is not DockerEnvironmentEntryProjectionV1
                for item in self.entries
            )
            or tuple(sorted(
                self.entries,
                key=lambda item: (item.key_digest, item.value_digest),
            )) != self.entries
            or len({item.key_digest for item in self.entries}) != len(self.entries)
        ):
            _bad()
        _check_digest(self)

    @classmethod
    def build(cls, entries):
        entries = tuple(sorted(
            entries, key=lambda item: (item.key_digest, item.value_digest)
        ))
        body = {
            "entries": [item.projection_digest for item in entries],
            "schema_version": "synaptic-host-docker-environment/v1",
        }
        return cls(entries, digest_v1(body))

@dataclass(frozen=True, slots=True)
class DockerMountProjectionV1:
    mount_type: str
    source_digest: str
    destination_digest: str
    read_write: bool
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "destination_digest": self.destination_digest,
            "mount_type": self.mount_type,
            "read_write": self.read_write,
            "schema_version": "synaptic-host-docker-mount-projection/v1",
            "source_digest": self.source_digest,
        }

    def __post_init__(self):
        if (
            self.mount_type not in ("bind", "volume", "tmpfs")
            or type(self.read_write) is not bool
        ):
            _bad()
        _sha(self.source_digest)
        _sha(self.destination_digest)
        _check_digest(self)

    @classmethod
    def build(cls, mount_type, source_digest, destination_digest, read_write):
        body = {
            "destination_digest": destination_digest,
            "mount_type": mount_type,
            "read_write": read_write,
            "schema_version": "synaptic-host-docker-mount-projection/v1",
            "source_digest": source_digest,
        }
        return cls(
            mount_type, source_digest, destination_digest, read_write,
            digest_v1(body),
        )

@dataclass(frozen=True, slots=True)
class DockerContainerStateV1:
    status: DockerContainerStatusV1
    running: bool
    exit_code: int
    started: bool
    restart_count: int
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "exit_code": self.exit_code,
            "restart_count": self.restart_count,
            "running": self.running,
            "schema_version": "synaptic-host-docker-state/v1",
            "started": self.started,
            "status": self.status.value,
        }

    def __post_init__(self):
        matrix = {
            DockerContainerStatusV1.CREATED: (False, False),
            DockerContainerStatusV1.RUNNING: (True, True),
            DockerContainerStatusV1.PAUSED: (True, True),
            DockerContainerStatusV1.RESTARTING: (True, True),
            DockerContainerStatusV1.EXITED: (False, True),
            DockerContainerStatusV1.DEAD: (False, True),
        }
        if (
            type(self.status) is not DockerContainerStatusV1
            or type(self.running) is not bool
            or type(self.started) is not bool
            or matrix.get(self.status) != (self.running, self.started)
            or type(self.exit_code) is not int
            or not -(2**31) <= self.exit_code <= 2**31 - 1
            or type(self.restart_count) is not int
            or not 0 <= self.restart_count <= 2**31 - 1
        ):
            _bad()
        _check_digest(self)

    @classmethod
    def build(cls, status, running, exit_code, started, restart_count):
        body = {
            "exit_code": exit_code,
            "restart_count": restart_count,
            "running": running,
            "schema_version": "synaptic-host-docker-state/v1",
            "started": started,
            "status": status.value,
        }
        return cls(
            status, running, exit_code, started, restart_count,
            digest_v1(body),
        )

@dataclass(frozen=True, slots=True)
class DockerImageInspectProjectionV1:
    image_digest: str
    request_digest: str
    command_digest: str
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "command_digest": self.command_digest,
            "image_digest": self.image_digest,
            "request_digest": self.request_digest,
            "schema_version": "synaptic-host-docker-image-inspect/v1",
        }

    def __post_init__(self):
        if (
            type(self.image_digest) is not str
            or _IMAGE.fullmatch(self.image_digest) is None
        ):
            _bad()
        _sha(self.request_digest)
        _sha(self.command_digest)
        if self.request_digest != docker_typed_request_digest_v1(
            DockerTypedResultKindV1.IMAGE_INSPECT,
            self.image_digest,
            self.command_digest,
        ):
            _bad()
        _check_digest(self)

    @classmethod
    def build(cls, image_digest, request_digest, command_digest):
        body = {
            "command_digest": command_digest,
            "image_digest": image_digest,
            "request_digest": request_digest,
            "schema_version": "synaptic-host-docker-image-inspect/v1",
        }
        return cls(
            image_digest, request_digest, command_digest, digest_v1(body)
        )

@dataclass(frozen=True, slots=True)
class DockerExactNameInventoryV1:
    container_name: str
    query: str
    request_digest: str
    command_digest: str
    container_refs: tuple[str, ...]
    projection_digest: str

    def canonical_without_digest(self):
        return {
            "command_digest": self.command_digest,
            "container_name": self.container_name,
            "container_refs": list(self.container_refs),
            "query": self.query,
            "request_digest": self.request_digest,
            "schema_version": "synaptic-host-docker-exact-name-inventory/v1",
        }

    def __post_init__(self):
        if (
            type(self.container_name) is not str
            or _NAME.fullmatch(self.container_name) is None
            or self.query != f"name=^/{self.container_name}$"
            or type(self.container_refs) is not tuple
            or len(self.container_refs) > 64
            or tuple(sorted(set(self.container_refs))) != self.container_refs
            or any(
                type(item) is not str or _SHA.fullmatch(item) is None
                for item in self.container_refs
            )
        ):
            _bad()
        _sha(self.request_digest)
        _sha(self.command_digest)
        if self.request_digest != docker_typed_request_digest_v1(
            DockerTypedResultKindV1.EXACT_NAME_INVENTORY,
            self.container_name,
            self.command_digest,
        ):
            _bad()
        _check_digest(self)

    @classmethod
    def build(
        cls, container_name, query, request_digest, command_digest,
        container_refs,
    ):
        container_refs = tuple(sorted(container_refs))
        body = {
            "command_digest": command_digest,
            "container_name": container_name,
            "container_refs": list(container_refs),
            "query": query,
            "request_digest": request_digest,
            "schema_version": "synaptic-host-docker-exact-name-inventory/v1",
        }
        return cls(
            container_name, query, request_digest, command_digest,
            container_refs, digest_v1(body),
        )

def _container_body(v):
    return {
        "argument_count": v["argument_count"],
        "arguments_digest": v["arguments_digest"],
        "command_digest": v["command_digest"],
        "container_name": v["container_name"],
        "container_ref": v["container_ref"],
        "environment_digest": v["environment"].projection_digest,
        "image_digest": v["image_digest"],
        "memory_bytes": v["memory_bytes"],
        "mounts": [item.projection_digest for item in v["mounts"]],
        "nano_cpus": v["nano_cpus"],
        "network_mode": v["network_mode"],
        "owned_labels": [
            item.projection_digest for item in v["owned_labels"]
        ],
        "request_digest": v["request_digest"],
        "schema_version": "synaptic-host-docker-container-inspect/v1",
        "state_digest": v["state"].projection_digest,
    }


@dataclass(frozen=True, slots=True)
class DockerContainerInspectProjectionV1:
    container_ref: str
    container_name: str
    image_digest: str
    request_digest: str
    command_digest: str
    owned_labels: tuple[DockerLabelProjectionV1, ...]
    network_mode: str
    nano_cpus: int
    memory_bytes: int
    mounts: tuple[DockerMountProjectionV1, ...]
    state: DockerContainerStateV1
    environment: DockerEnvironmentProjectionV1
    argument_count: int
    arguments_digest: str
    projection_digest: str

    def canonical_without_digest(self):
        names = (
            "argument_count", "arguments_digest", "command_digest",
            "container_name", "container_ref", "environment", "image_digest",
            "memory_bytes", "mounts", "nano_cpus", "network_mode",
            "owned_labels", "request_digest", "state",
        )
        return _container_body({name: getattr(self, name) for name in names})

    def __post_init__(self):
        if (
            type(self.container_ref) is not str
            or _SHA.fullmatch(self.container_ref) is None
            or type(self.container_name) is not str
            or _NAME.fullmatch(self.container_name) is None
            or type(self.image_digest) is not str
            or _IMAGE.fullmatch(self.image_digest) is None
            or type(self.owned_labels) is not tuple
            or any(
                type(item) is not DockerLabelProjectionV1
                for item in self.owned_labels
            )
            or tuple(item.name for item in self.owned_labels)
            != OWNED_LABEL_NAMES_V1
            or type(self.network_mode) is not str
            or not self.network_mode
            or type(self.nano_cpus) is not int
            or not 0 <= self.nano_cpus <= 2**63 - 1
            or type(self.memory_bytes) is not int
            or not 0 <= self.memory_bytes <= 2**63 - 1
            or type(self.mounts) is not tuple
            or len(self.mounts) > 64
            or any(type(item) is not DockerMountProjectionV1 for item in self.mounts)
            or type(self.state) is not DockerContainerStateV1
            or type(self.environment) is not DockerEnvironmentProjectionV1
            or type(self.argument_count) is not int
            or not 0 <= self.argument_count <= 256
        ):
            _bad()
        for value in (
            self.request_digest, self.command_digest, self.arguments_digest
        ):
            _sha(value)
        if self.request_digest != docker_typed_request_digest_v1(
            DockerTypedResultKindV1.CONTAINER_INSPECT,
            self.container_ref,
            self.command_digest,
        ):
            _bad()
        _check_digest(self)

    @classmethod
    def build(cls, **values):
        return cls(
            **values,
            projection_digest=digest_v1(_container_body(values)),
        )

def _snapshot_command(command):
    if type(command) is not DockerCLICommandV1:
        _bad()
    rebuilt = DockerCLICommandV1(
        command.verb,
        tuple(command.arguments),
        command.command_digest,
    )
    if rebuilt != command:
        _bad()
    return rebuilt


def _snapshot_evidence(evidence):
    if type(evidence) is not DockerCLIResultV1:
        _bad()
    rebuilt = DockerCLIResultV1(
        evidence.command_digest,
        evidence.policy_digest,
        evidence.outcome,
        evidence.exit_code,
        evidence.stdout_size,
        evidence.stdout_digest,
        evidence.stderr_size,
        evidence.stderr_digest,
        evidence.result_digest,
    )
    if rebuilt != evidence:
        _bad()
    return rebuilt


def _snapshot_projection(projection):
    if type(projection) is DockerImageInspectProjectionV1:
        rebuilt = DockerImageInspectProjectionV1(
            projection.image_digest,
            projection.request_digest,
            projection.command_digest,
            projection.projection_digest,
        )
    elif type(projection) is DockerExactNameInventoryV1:
        rebuilt = DockerExactNameInventoryV1(
            projection.container_name,
            projection.query,
            projection.request_digest,
            projection.command_digest,
            tuple(projection.container_refs),
            projection.projection_digest,
        )
    elif type(projection) is DockerContainerInspectProjectionV1:
        labels = tuple(
            DockerLabelProjectionV1(
                item.name, item.value_digest, item.projection_digest
            )
            for item in projection.owned_labels
        )
        environment_entries = tuple(
            DockerEnvironmentEntryProjectionV1(
                item.key_digest, item.value_digest, item.projection_digest
            )
            for item in projection.environment.entries
        )
        environment = DockerEnvironmentProjectionV1(
            environment_entries, projection.environment.projection_digest
        )
        mounts = tuple(
            DockerMountProjectionV1(
                item.mount_type, item.source_digest, item.destination_digest,
                item.read_write, item.projection_digest,
            )
            for item in projection.mounts
        )
        state = DockerContainerStateV1(
            projection.state.status,
            projection.state.running,
            projection.state.exit_code,
            projection.state.started,
            projection.state.restart_count,
            projection.state.projection_digest,
        )
        rebuilt = DockerContainerInspectProjectionV1(
            projection.container_ref,
            projection.container_name,
            projection.image_digest,
            projection.request_digest,
            projection.command_digest,
            labels,
            projection.network_mode,
            projection.nano_cpus,
            projection.memory_bytes,
            mounts,
            state,
            environment,
            projection.argument_count,
            projection.arguments_digest,
            projection.projection_digest,
        )
    else:
        _bad()
    if rebuilt != projection:
        _bad()
    return rebuilt


def _expected_command(kind, target):
    if kind is DockerTypedResultKindV1.EXACT_NAME_INVENTORY:
        return DockerCLICommandV1.build(
            DockerCLIVerbV1.PS,
            ("--all", "--quiet", "--no-trunc", "--filter",
             f"name=^/{target}$"),
        )
    inspect_type = (
        "image" if kind is DockerTypedResultKindV1.IMAGE_INSPECT
        else "container"
    )
    return DockerCLICommandV1.build(
        DockerCLIVerbV1.INSPECT,
        ("--type", inspect_type, target),
    )


def _result_body(kind, target, request_digest, command, evidence, projection):
    return {
        "command_digest": command.command_digest,
        "evidence_result_digest": evidence.result_digest,
        "kind": kind.value,
        "projection_digest": (
            None if projection is None else projection.projection_digest
        ),
        "request_digest": request_digest,
        "schema_version": "synaptic-host-docker-typed-result/v1",
        "target": target,
    }


def _validate_result(
    kind, target, request_digest, command, evidence, projection,
    result_digest, projection_type,
):
    command = _snapshot_command(command)
    evidence = _snapshot_evidence(evidence)
    expected_command = _expected_command(kind, target)
    if command != expected_command or evidence.command_digest != command.command_digest:
        _bad()
    if ((evidence.outcome is DockerCLIOutcomeV1.SUCCESS)
            != (type(projection) is projection_type)):
        _bad()
    for value in (request_digest, result_digest):
        _sha(value)
    if request_digest != docker_typed_request_digest_v1(
        kind, target, command.command_digest
    ):
        _bad()
    if projection is not None:
        projection = _snapshot_projection(projection)
        if (projection.request_digest != request_digest
                or projection.command_digest != command.command_digest):
            _bad()
        projected_target = (
            projection.image_digest
            if kind is DockerTypedResultKindV1.IMAGE_INSPECT
            else projection.container_ref
            if kind is DockerTypedResultKindV1.CONTAINER_INSPECT
            else projection.container_name
        )
        if projected_target != target:
            _bad()
    expected_digest = digest_v1(_result_body(
        kind, target, request_digest, command, evidence, projection
    ))
    if result_digest != expected_digest:
        _bad()


def _validate_result_closed(*arguments):
    try:
        _validate_result(*arguments)
    except BaseException:
        _bad()

@dataclass(frozen=True, slots=True)
class DockerImageInspectResultV1:
    result_kind: DockerTypedResultKindV1
    target: str
    request_digest: str
    command: DockerCLICommandV1
    evidence: DockerCLIResultV1
    projection: DockerImageInspectProjectionV1 | None
    result_digest: str

    @property
    def command_digest(self):
        return self.command.command_digest

    def __post_init__(self):
        if self.result_kind is not DockerTypedResultKindV1.IMAGE_INSPECT:
            _bad()
        _validate_result_closed(
            self.result_kind, self.target, self.request_digest, self.command,
            self.evidence, self.projection, self.result_digest,
            DockerImageInspectProjectionV1,
        )

    @classmethod
    def build(cls, target, request_digest, command, evidence, projection):
        kind = DockerTypedResultKindV1.IMAGE_INSPECT
        return cls(
            kind, target, request_digest, command, evidence, projection,
            digest_v1(_result_body(
                kind, target, request_digest, command, evidence, projection
            )),
        )

@dataclass(frozen=True, slots=True)
class DockerContainerInspectResultV1:
    result_kind: DockerTypedResultKindV1
    target: str
    request_digest: str
    command: DockerCLICommandV1
    evidence: DockerCLIResultV1
    projection: DockerContainerInspectProjectionV1 | None
    result_digest: str

    @property
    def command_digest(self):
        return self.command.command_digest

    def __post_init__(self):
        if self.result_kind is not DockerTypedResultKindV1.CONTAINER_INSPECT:
            _bad()
        _validate_result_closed(
            self.result_kind, self.target, self.request_digest, self.command,
            self.evidence, self.projection, self.result_digest,
            DockerContainerInspectProjectionV1,
        )

    @classmethod
    def build(cls, target, request_digest, command, evidence, projection):
        kind = DockerTypedResultKindV1.CONTAINER_INSPECT
        return cls(
            kind, target, request_digest, command, evidence, projection,
            digest_v1(_result_body(
                kind, target, request_digest, command, evidence, projection
            )),
        )

@dataclass(frozen=True, slots=True)
class DockerExactNameInventoryResultV1:
    result_kind: DockerTypedResultKindV1
    target: str
    request_digest: str
    command: DockerCLICommandV1
    evidence: DockerCLIResultV1
    projection: DockerExactNameInventoryV1 | None
    result_digest: str

    @property
    def command_digest(self):
        return self.command.command_digest

    def __post_init__(self):
        if self.result_kind is not DockerTypedResultKindV1.EXACT_NAME_INVENTORY:
            _bad()
        _validate_result_closed(
            self.result_kind, self.target, self.request_digest, self.command,
            self.evidence, self.projection, self.result_digest,
            DockerExactNameInventoryV1,
        )

    @classmethod
    def build(cls, target, request_digest, command, evidence, projection):
        kind = DockerTypedResultKindV1.EXACT_NAME_INVENTORY
        return cls(
            kind, target, request_digest, command, evidence, projection,
            digest_v1(_result_body(
                kind, target, request_digest, command, evidence, projection
            )),
        )


def _create_execution_result_body(
    target, request_digest, command_digest, evidence, projection,
):
    return {
        "command_digest": command_digest,
        "evidence_result_digest": evidence.result_digest,
        "kind": DockerTypedResultKindV1.CREATE_EXECUTION.value,
        "projection_digest": (
            projection.projection_digest if projection is not None else None
        ),
        "request_digest": request_digest,
        "schema_version": "synaptic-host-docker-create-execution-result/v1",
        "target": target,
    }


@dataclass(frozen=True, slots=True)
class DockerCreateExecutionResultV1:
    result_kind: DockerTypedResultKindV1
    target: str
    request_digest: str
    command_digest: str
    evidence: DockerCLIResultV1
    projection: DockerCreateExecutionProjectionV1 | None
    result_digest: str

    def __post_init__(self):
        try:
            if (
                self.result_kind is not DockerTypedResultKindV1.CREATE_EXECUTION
                or type(self.target) is not str
                or _NAME.fullmatch(self.target) is None
            ):
                raise ValueError
            _sha(self.request_digest)
            _sha(self.command_digest)
            if self.request_digest != docker_create_execution_request_digest_v1(
                self.target, self.command_digest
            ):
                raise ValueError
            if type(self.evidence) is not DockerCLIResultV1:
                raise ValueError
            evidence = DockerCLIResultV1(
                self.evidence.command_digest, self.evidence.policy_digest,
                self.evidence.outcome, self.evidence.exit_code,
                self.evidence.stdout_size, self.evidence.stdout_digest,
                self.evidence.stderr_size, self.evidence.stderr_digest,
                self.evidence.result_digest,
            )
            if evidence.command_digest != self.command_digest:
                raise ValueError
            if self.projection is not None:
                projection = DockerCreateExecutionProjectionV1(
                    self.projection.container_ref,
                    self.projection.request_digest,
                    self.projection.command_digest,
                    self.projection.projection_digest,
                )
            else:
                projection = None
            if evidence.outcome is DockerCLIOutcomeV1.SUCCESS:
                if (
                    projection is None
                    or projection.request_digest != self.request_digest
                    or projection.command_digest != self.command_digest
                ):
                    raise ValueError
                raw = projection.container_ref.encode("utf-8")
                valid_stdout = (
                    (evidence.stdout_size == 64
                     and evidence.stdout_digest == sha256(raw).hexdigest())
                    or (evidence.stdout_size == 65
                        and evidence.stdout_digest
                        == sha256(raw + b"\n").hexdigest())
                )
                if not valid_stdout:
                    raise ValueError
            elif (
                evidence.outcome is not DockerCLIOutcomeV1.NONZERO_EXIT
                or projection is not None
            ):
                raise ValueError
            _sha(self.result_digest)
            if self.result_digest != digest_v1(_create_execution_result_body(
                self.target, self.request_digest, self.command_digest,
                evidence, projection,
            )):
                raise ValueError
            object.__setattr__(self, "evidence", evidence)
            object.__setattr__(self, "projection", projection)
        except BaseException:
            _bad()

    @classmethod
    def build(cls, target, request_digest, command_digest, evidence, projection):
        kind = DockerTypedResultKindV1.CREATE_EXECUTION
        return cls(
            kind, target, request_digest, command_digest, evidence, projection,
            digest_v1(_create_execution_result_body(
                target, request_digest, command_digest, evidence, projection
            )),
        )


def _start_execution_result_body(
    target, request_digest, command_digest, evidence,
):
    return {
        "command_digest": command_digest,
        "evidence_result_digest": evidence.result_digest,
        "kind": DockerTypedResultKindV1.START_EXECUTION.value,
        "request_digest": request_digest,
        "schema_version": "synaptic-host-docker-start-execution-result/v1",
        "target": target,
    }


@dataclass(frozen=True, slots=True)
class DockerStartExecutionResultV1:
    result_kind: DockerTypedResultKindV1
    target: str
    request_digest: str
    command: DockerCLICommandV1
    command_digest: str
    evidence: DockerCLIResultV1
    result_digest: str

    def __post_init__(self):
        try:
            if (
                self.result_kind is not DockerTypedResultKindV1.START_EXECUTION
                or type(self.target) is not str
                or _SHA.fullmatch(self.target) is None
                or type(self.command) is not DockerCLICommandV1
            ):
                raise ValueError
            command = DockerCLICommandV1(
                self.command.verb, tuple(self.command.arguments),
                self.command.command_digest,
            )
            if (
                command.verb is not DockerCLIVerbV1.START
                or command.arguments != (self.target,)
                or self.command_digest != command.command_digest
            ):
                raise ValueError
            _sha(self.request_digest)
            if self.request_digest != docker_start_execution_request_digest_v1(
                self.target, self.command_digest
            ):
                raise ValueError
            if type(self.evidence) is not DockerCLIResultV1:
                raise ValueError
            evidence = DockerCLIResultV1(
                self.evidence.command_digest, self.evidence.policy_digest,
                self.evidence.outcome, self.evidence.exit_code,
                self.evidence.stdout_size, self.evidence.stdout_digest,
                self.evidence.stderr_size, self.evidence.stderr_digest,
                self.evidence.result_digest,
            )
            if (
                evidence.command_digest != command.command_digest
                or evidence.outcome not in (
                    DockerCLIOutcomeV1.SUCCESS,
                    DockerCLIOutcomeV1.NONZERO_EXIT,
                )
            ):
                raise ValueError
            _sha(self.result_digest)
            if self.result_digest != digest_v1(_start_execution_result_body(
                self.target, self.request_digest, self.command_digest, evidence,
            )):
                raise ValueError
            object.__setattr__(self, "command", command)
            object.__setattr__(self, "evidence", evidence)
        except BaseException:
            _bad()

    @classmethod
    def build(cls, target, request_digest, command, evidence):
        command_digest = command.command_digest
        return cls(
            DockerTypedResultKindV1.START_EXECUTION, target, request_digest,
            command, command_digest, evidence,
            digest_v1(_start_execution_result_body(
                target, request_digest, command_digest, evidence,
            )),
        )

__all__: tuple[str,...]=()
