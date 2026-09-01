"""Closed durable records for the one-run Docker training vertical slice."""

from __future__ import annotations

import hashlib
import base64
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import PurePosixPath
from typing import Mapping

from tuner.execution.foundation_v2.commands import (
    SubmitCommandV2,
    parse_exact_command,
)

from .docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1,
    DockerControlOperationV1,
    DockerMutationCASRequestV1,
    DockerControlContractErrorV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
)


_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,511}$")
_DIAGNOSTIC = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_MAX_RECORD_BYTES = 1024 * 1024
_ARTIFACT_ROLES = (
    "final_model",
    "tokenizer",
    "training_lineage",
    "training_metrics",
    "workload_record",
)
_ZERO_EXIT_FAILURE_DIAGNOSTICS = frozenset({
    "ARTIFACT_INVENTORY_MISSING",
    "ARTIFACT_INVENTORY_INVALID",
    "ARTIFACT_INTEGRITY_INVALID",
    "ARTIFACT_SEMANTIC_INVALID",
    "PROCESS_DEAD",
})


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _seal(domain: bytes, value: object) -> str:
    return hashlib.sha256(domain + b"\0" + _canonical(value)).hexdigest()


def _text(value: object, label: str, *, pattern: re.Pattern[str] = _REF) -> str:
    if (
        type(value) is not str
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 512
        or pattern.fullmatch(value) is None
    ):
        raise ValueError(f"{label} is invalid")
    return value


def _digest(value: object, label: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _timestamp(value: object, label: str) -> str:
    if type(value) is not str or not value.endswith("Z"):
        raise ValueError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{label} must be a UTC timestamp") from None
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{label} must be a UTC timestamp")
    return value


def _mapping(value: object, fields: frozenset[str], label: str) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != fields:
        raise ValueError(f"{label} contains missing or unknown fields")
    return dict(value)


def _read(raw: bytes) -> dict[str, object]:
    try:
        if type(raw) is not bytes or not raw or len(raw) > _MAX_RECORD_BYTES:
            raise ValueError
        value = json.loads(raw.decode("utf-8"))
    except Exception:
        raise ValueError("Docker durable record is unavailable or invalid") from None
    if type(value) is not dict or _canonical(value) != raw:
        raise ValueError("Docker durable record is not canonical")
    return value


@dataclass(frozen=True, slots=True)
class DockerStageProjectionV1:
    source_stage_ref: str
    source_manifest_digest: str
    artifact_stage_ref: str
    worker_projection_digest: str
    workload_fingerprint: str
    workload_sha256: str
    worker_closure_manifest_path: str
    worker_closure_manifest_sha256: str
    worker_source_closure_digest: str
    staged_model_inventory_digest: str
    staged_storage_configuration_digest: str

    def __post_init__(self) -> None:
        _text(self.source_stage_ref, "source_stage_ref")
        _text(self.artifact_stage_ref, "artifact_stage_ref")
        _text(self.worker_closure_manifest_path, "worker_closure_manifest_path")
        for name in (
            "source_manifest_digest",
            "worker_projection_digest",
            "workload_fingerprint",
            "workload_sha256",
            "worker_closure_manifest_sha256",
            "worker_source_closure_digest",
            "staged_model_inventory_digest",
            "staged_storage_configuration_digest",
        ):
            _digest(getattr(self, name), name)

    def to_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    @classmethod
    def from_mapping(cls, value: object) -> "DockerStageProjectionV1":
        fields = frozenset(cls.__dataclass_fields__)
        exact = _mapping(value, fields, "Docker stage projection")
        return cls(**exact)


@dataclass(frozen=True, slots=True)
class VerifiedDockerArtifactV1:
    role: str
    relative_path: str
    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        if self.role not in _ARTIFACT_ROLES:
            raise ValueError("artifact role is not admitted")
        _digest(self.sha256, "artifact sha256")
        if type(self.byte_count) is not int or not 0 <= self.byte_count <= 2**63 - 1:
            raise ValueError("artifact byte_count is invalid")
        if type(self.relative_path) is not str:
            raise ValueError("artifact relative_path is invalid")
        path = PurePosixPath(self.relative_path)
        if (
            not self.relative_path
            or path.is_absolute()
            or path.as_posix() != self.relative_path
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError("artifact relative_path is invalid")

    def to_dict(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    @classmethod
    def from_mapping(cls, value: object) -> "VerifiedDockerArtifactV1":
        exact = _mapping(
            value, frozenset(cls.__dataclass_fields__), "verified artifact"
        )
        return cls(**exact)


@dataclass(frozen=True, slots=True)
class ProviderPreparationRecordV1:
    project_ref: str
    run_id: str
    plan_fingerprint: str
    effect_id: str
    source_lock_digest: str
    prepared_docker_plan_digest: str
    endpoint_descriptor_digest: str
    cli_policy_digest: str
    destination_ref: str
    destination_declaration_digest: str
    submit_command_bytes: bytes
    stage: DockerStageProjectionV1
    prepared_at: str
    preparation_digest: str

    def _body(self) -> dict[str, object]:
        return {
            "schema_version": "synaptic-host-docker-preparation/v1",
            "project_ref": self.project_ref,
            "run_id": self.run_id,
            "plan_fingerprint": self.plan_fingerprint,
            "effect_id": self.effect_id,
            "source_lock_digest": self.source_lock_digest,
            "prepared_docker_plan_digest": self.prepared_docker_plan_digest,
            "endpoint_descriptor_digest": self.endpoint_descriptor_digest,
            "cli_policy_digest": self.cli_policy_digest,
            "destination_ref": self.destination_ref,
            "destination_declaration_digest": self.destination_declaration_digest,
            "submit_command_base64": base64.b64encode(
                self.submit_command_bytes
            ).decode("ascii"),
            "stage": self.stage.to_dict(),
            "prepared_at": self.prepared_at,
        }

    def __post_init__(self) -> None:
        for name in ("project_ref", "run_id", "effect_id", "destination_ref"):
            _text(getattr(self, name), name)
        for name in (
            "plan_fingerprint",
            "source_lock_digest",
            "prepared_docker_plan_digest",
            "endpoint_descriptor_digest",
            "cli_policy_digest",
            "destination_declaration_digest",
        ):
            _digest(getattr(self, name), name)
        if type(self.stage) is not DockerStageProjectionV1:
            raise TypeError("stage must be DockerStageProjectionV1")
        if (
            type(self.submit_command_bytes) is not bytes
            or not 1 <= len(self.submit_command_bytes) <= 262_144
        ):
            raise ValueError("submit command bytes are invalid")
        try:
            command = parse_exact_command(self.submit_command_bytes)
        except Exception:
            raise ValueError("submit command bytes are invalid") from None
        if (
            type(command) is not SubmitCommandV2
            or command.canonical_bytes != self.submit_command_bytes
            or command.preparation.provider.provider_id != "docker"
            or command.preparation.project_ref != self.project_ref
            or command.preparation.run_id != self.run_id
            or command.preparation.plan_fingerprint != self.plan_fingerprint
            or command.operation.effect.kind.value != "submit"
            or command.operation.effect.effect_id != self.effect_id
        ):
            raise ValueError("submit command does not bind the preparation")
        _timestamp(self.prepared_at, "prepared_at")
        _digest(self.preparation_digest, "preparation_digest")
        if self.preparation_digest != _seal(
            b"synaptic-host-docker-preparation/v1", self._body()
        ):
            raise ValueError("preparation_digest does not bind the record")

    @classmethod
    def build(cls, **values: object) -> "ProviderPreparationRecordV1":
        provisional = cls.__new__(cls)
        for name, value in values.items():
            object.__setattr__(provisional, name, value)
        body = ProviderPreparationRecordV1._body(provisional)
        return cls(
            **values,
            preparation_digest=_seal(b"synaptic-host-docker-preparation/v1", body),
        )

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical({**self._body(), "preparation_digest": self.preparation_digest})

    @property
    def submit_command_digest(self) -> str:
        command = parse_exact_command(self.submit_command_bytes)
        if type(command) is not SubmitCommandV2:  # pragma: no cover - invariant
            raise ValueError("submit command bytes are invalid")
        return command.digest

    @classmethod
    def from_canonical_bytes(cls, raw: bytes) -> "ProviderPreparationRecordV1":
        value = _read(raw)
        fields = frozenset({
            "schema_version", "project_ref", "run_id", "plan_fingerprint",
            "effect_id", "source_lock_digest", "prepared_docker_plan_digest",
            "endpoint_descriptor_digest", "cli_policy_digest", "destination_ref",
            "destination_declaration_digest", "stage", "prepared_at",
            "submit_command_base64", "preparation_digest",
        })
        exact = _mapping(value, fields, "Docker preparation")
        if exact.pop("schema_version") != "synaptic-host-docker-preparation/v1":
            raise ValueError("unsupported Docker preparation schema")
        encoded = exact.pop("submit_command_base64")
        try:
            if type(encoded) is not str or not encoded:
                raise ValueError
            raw = base64.b64decode(encoded, validate=True)
            if base64.b64encode(raw).decode("ascii") != encoded:
                raise ValueError
        except Exception:
            raise ValueError("submit_command_base64 is invalid") from None
        exact["submit_command_bytes"] = raw
        exact["stage"] = DockerStageProjectionV1.from_mapping(exact["stage"])
        return cls(**exact)


class DockerRunPhaseV1(str, Enum):
    CREATE_ADMITTED = "CREATE_ADMITTED"
    CREATE_ATTEMPTED = "CREATE_ATTEMPTED"
    CREATED = "CREATED"
    START_ADMITTED = "START_ADMITTED"
    START_ATTEMPTED = "START_ATTEMPTED"
    SUBMITTED = "SUBMITTED"
    RECONCILE_REQUIRED = "RECONCILE_REQUIRED"
    PROCESS_SUCCEEDED = "PROCESS_SUCCEEDED"
    PROCESS_FAILED = "PROCESS_FAILED"
    ARTIFACTS_VERIFIED = "ARTIFACTS_VERIFIED"


class DockerReconcileOperationV1(str, Enum):
    LOOKUP_CREATE = "LOOKUP_CREATE"
    LOOKUP_START = "LOOKUP_START"
    OBSERVE_PROCESS = "OBSERVE_PROCESS"


def _mutation_content_to_dict(value: DockerMutationRecordV1) -> dict[str, object]:
    if type(value) is not DockerMutationRecordV1:
        raise TypeError("exact low-level Docker mutation record is required")
    return {**value.canonical_without_digest(), "record_digest": value.record_digest}


def _mutation_to_dict(value: AuthenticatedDockerMutationRecordV1 | None) -> object:
    if value is None:
        return None
    if type(value) is not AuthenticatedDockerMutationRecordV1:
        raise TypeError("exact authenticated Docker mutation is required")
    return {
        "content": _mutation_content_to_dict(value.content),
        "authority_ref": value.authority_ref,
        "key_ref": value.key_ref,
        "tag": value.tag,
    }


def _mutation_content_from_mapping(value: object) -> DockerMutationRecordV1:
    fields = frozenset({
        "schema_version", "operation_id", "operation", "effect_id",
        "control_intent_proof_digest", "phase", "revision", "attempt_count",
        "previous_record_digest", "container_ref", "verification_result_digest",
        "record_digest",
    })
    exact = _mapping(value, fields, "low-level Docker mutation")
    if exact.pop("schema_version") != "synaptic-host-docker-mutation-record/v1":
        raise ValueError("unsupported low-level Docker mutation schema")
    exact["operation"] = DockerControlOperationV1(exact["operation"])
    exact["phase"] = DockerMutationPhaseV1(exact["phase"])
    return DockerMutationRecordV1(**exact)


def _mutation_from_mapping(
    value: object,
) -> AuthenticatedDockerMutationRecordV1 | None:
    if value is None:
        return None
    exact = _mapping(
        value,
        frozenset({"content", "authority_ref", "key_ref", "tag"}),
        "authenticated Docker mutation",
    )
    return AuthenticatedDockerMutationRecordV1(
        _mutation_content_from_mapping(exact["content"]),
        exact["authority_ref"],
        exact["key_ref"],
        exact["tag"],
    )


@dataclass(frozen=True, slots=True)
class DockerRunMutationRecordV1:
    project_ref: str
    run_id: str
    effect_id: str
    preparation_digest: str
    phase: DockerRunPhaseV1
    revision: int
    previous_record_digest: str | None
    create_mutation: AuthenticatedDockerMutationRecordV1
    start_mutation: AuthenticatedDockerMutationRecordV1 | None
    reconcile_operation: DockerReconcileOperationV1 | None
    container_ref: str | None
    submitted_at: str | None
    process_exit_code: int | None
    process_observation_digest: str | None
    diagnostic: str | None
    verified_artifacts: tuple[VerifiedDockerArtifactV1, ...]
    verified_inventory_digest: str | None
    record_digest: str

    def _body(self) -> dict[str, object]:
        return {
            "schema_version": "synaptic-host-docker-run-mutation/v1",
            "project_ref": self.project_ref,
            "run_id": self.run_id,
            "effect_id": self.effect_id,
            "preparation_digest": self.preparation_digest,
            "phase": self.phase.value,
            "revision": self.revision,
            "previous_record_digest": self.previous_record_digest,
            "create_mutation": _mutation_to_dict(self.create_mutation),
            "start_mutation": _mutation_to_dict(self.start_mutation),
            "reconcile_operation": (
                None if self.reconcile_operation is None
                else self.reconcile_operation.value
            ),
            "container_ref": self.container_ref,
            "submitted_at": self.submitted_at,
            "process_exit_code": self.process_exit_code,
            "process_observation_digest": self.process_observation_digest,
            "diagnostic": self.diagnostic,
            "verified_artifacts": [item.to_dict() for item in self.verified_artifacts],
            "verified_inventory_digest": self.verified_inventory_digest,
        }

    def __post_init__(self) -> None:
        for name in ("project_ref", "run_id", "effect_id"):
            _text(getattr(self, name), name)
        _digest(self.preparation_digest, "preparation_digest")
        if type(self.phase) is not DockerRunPhaseV1:
            raise TypeError("phase must be DockerRunPhaseV1")
        if type(self.revision) is not int or self.revision < 1:
            raise ValueError("revision must be a positive integer")
        if self.revision == 1:
            if self.previous_record_digest is not None:
                raise ValueError("initial mutation cannot name a previous record")
        else:
            _digest(self.previous_record_digest, "previous_record_digest")
        if (self.revision == 1) != (
            self.phase is DockerRunPhaseV1.CREATE_ADMITTED
        ):
            raise ValueError("revision one must be canonical CREATE_ADMITTED")
        if type(self.create_mutation) is not AuthenticatedDockerMutationRecordV1:
            raise TypeError("create_mutation must be an authenticated envelope")
        if (
            self.create_mutation.content.operation
            is not DockerControlOperationV1.CREATE
            or self.create_mutation.content.effect_id != self.effect_id
        ):
            raise ValueError("create mutation identity differs from the aggregate")
        if self.start_mutation is not None and (
            type(self.start_mutation) is not AuthenticatedDockerMutationRecordV1
            or self.start_mutation.content.operation
            is not DockerControlOperationV1.START
            or self.start_mutation.content.effect_id != self.effect_id
        ):
            raise ValueError("start mutation identity differs from the aggregate")
        if self.reconcile_operation is not None and type(
            self.reconcile_operation
        ) is not DockerReconcileOperationV1:
            raise TypeError("reconcile_operation is invalid")
        if self.container_ref is not None:
            _text(self.container_ref, "container_ref")
        if self.submitted_at is not None:
            _timestamp(self.submitted_at, "submitted_at")
        if self.process_exit_code is not None and (
            type(self.process_exit_code) is not int
            or not -(2**31) <= self.process_exit_code <= 2**31 - 1
        ):
            raise ValueError("process_exit_code is invalid")
        if self.process_observation_digest is not None:
            _digest(self.process_observation_digest, "process_observation_digest")
        if self.diagnostic is not None:
            _text(self.diagnostic, "diagnostic", pattern=_DIAGNOSTIC)
        if (self.diagnostic is not None) != (
            self.phase in {
                DockerRunPhaseV1.RECONCILE_REQUIRED,
                DockerRunPhaseV1.PROCESS_FAILED,
            }
        ):
            raise ValueError("diagnostic is only valid for a closed failure")
        if type(self.verified_artifacts) is not tuple or any(
            type(item) is not VerifiedDockerArtifactV1
            for item in self.verified_artifacts
        ):
            raise TypeError("verified_artifacts must be exact descriptors")
        if tuple(sorted(self.verified_artifacts, key=lambda item: item.role)) != self.verified_artifacts:
            raise ValueError("verified artifacts must be sorted by role")
        if self.verified_inventory_digest is not None:
            _digest(self.verified_inventory_digest, "verified_inventory_digest")
        self._validate_phase()
        _digest(self.record_digest, "record_digest")
        if self.record_digest != _seal(
            b"synaptic-host-docker-run-mutation/v1", self._body()
        ):
            raise ValueError("record_digest does not bind the aggregate")

    def _validate_phase(self) -> None:
        create_phase = self.create_mutation.content.phase
        start_phase = (
            None if self.start_mutation is None else self.start_mutation.content.phase
        )
        if self.phase is DockerRunPhaseV1.CREATE_ADMITTED:
            valid = (
                self.revision == 1
                and create_phase is DockerMutationPhaseV1.ADMITTED
                and self.start_mutation is None
            )
        elif self.phase is DockerRunPhaseV1.CREATE_ATTEMPTED:
            valid = create_phase is DockerMutationPhaseV1.ATTEMPTED and self.start_mutation is None
        elif self.phase is DockerRunPhaseV1.CREATED:
            valid = create_phase is DockerMutationPhaseV1.VERIFIED and self.start_mutation is None
        elif self.phase is DockerRunPhaseV1.START_ADMITTED:
            valid = create_phase is DockerMutationPhaseV1.VERIFIED and start_phase is DockerMutationPhaseV1.ADMITTED
        elif self.phase is DockerRunPhaseV1.START_ATTEMPTED:
            valid = create_phase is DockerMutationPhaseV1.VERIFIED and start_phase is DockerMutationPhaseV1.ATTEMPTED
        elif self.phase is DockerRunPhaseV1.RECONCILE_REQUIRED:
            valid = {
                DockerReconcileOperationV1.LOOKUP_CREATE: (
                    create_phase is DockerMutationPhaseV1.ATTEMPTED
                    and self.start_mutation is None
                ),
                DockerReconcileOperationV1.LOOKUP_START: (
                    create_phase is DockerMutationPhaseV1.VERIFIED
                    and start_phase is DockerMutationPhaseV1.ATTEMPTED
                ),
                DockerReconcileOperationV1.OBSERVE_PROCESS: (
                    create_phase is DockerMutationPhaseV1.VERIFIED
                    and start_phase is DockerMutationPhaseV1.VERIFIED
                ),
            }.get(self.reconcile_operation, False)
        else:
            valid = create_phase is DockerMutationPhaseV1.VERIFIED and start_phase is DockerMutationPhaseV1.VERIFIED
        if not valid:
            raise ValueError("aggregate phase differs from low-level mutations")
        stable = self.phase in {
            DockerRunPhaseV1.SUBMITTED,
            DockerRunPhaseV1.PROCESS_SUCCEEDED,
            DockerRunPhaseV1.PROCESS_FAILED,
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        } or (
            self.phase is DockerRunPhaseV1.RECONCILE_REQUIRED
            and self.reconcile_operation is DockerReconcileOperationV1.OBSERVE_PROCESS
        )
        if stable != (self.container_ref is not None and self.submitted_at is not None):
            raise ValueError("submitted phases require a stable container receipt")
        if stable and (
            self.container_ref != self.create_mutation.content.container_ref
            or self.container_ref != self.start_mutation.content.container_ref
        ):
            raise ValueError("aggregate container differs from low-level verification")
        process_closed = self.phase in {
            DockerRunPhaseV1.PROCESS_SUCCEEDED,
            DockerRunPhaseV1.PROCESS_FAILED,
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        }
        if process_closed != (
            self.process_exit_code is not None
            and self.process_observation_digest is not None
        ):
            raise ValueError("process terminal state requires one exact observation")
        if self.phase in {
            DockerRunPhaseV1.PROCESS_SUCCEEDED,
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        } and self.process_exit_code != 0:
            raise ValueError("successful process phase requires exit code zero")
        if self.phase is DockerRunPhaseV1.PROCESS_FAILED and (
            self.diagnostic is None
            or (
                self.process_exit_code == 0
                and self.diagnostic not in _ZERO_EXIT_FAILURE_DIAGNOSTICS
            )
        ):
            raise ValueError("failed process phase requires a closed diagnostic")
        if self.phase is DockerRunPhaseV1.RECONCILE_REQUIRED:
            if self.reconcile_operation is None or self.diagnostic is None:
                raise ValueError("reconciliation requires an operation and diagnostic")
        elif self.reconcile_operation is not None:
            raise ValueError("reconcile_operation is only valid while reconciliation is required")
        if self.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED:
            if tuple(item.role for item in self.verified_artifacts) != _ARTIFACT_ROLES:
                raise ValueError("verified inventory must contain exactly five roles")
            expected = _seal(
                b"synaptic-host-docker-artifact-inventory/v1",
                [item.to_dict() for item in self.verified_artifacts],
            )
            if self.verified_inventory_digest != expected:
                raise ValueError("verified inventory digest is invalid")
        elif self.verified_artifacts or self.verified_inventory_digest is not None:
            raise ValueError("artifacts are only valid after exact verification")

    @classmethod
    def build(cls, **values: object) -> "DockerRunMutationRecordV1":
        provisional = cls.__new__(cls)
        for name, value in values.items():
            object.__setattr__(provisional, name, value)
        body = DockerRunMutationRecordV1._body(provisional)
        return cls(
            **values,
            record_digest=_seal(b"synaptic-host-docker-run-mutation/v1", body),
        )

    @classmethod
    def initial(
        cls,
        preparation: ProviderPreparationRecordV1,
        create_mutation: AuthenticatedDockerMutationRecordV1,
    ) -> "DockerRunMutationRecordV1":
        if type(preparation) is not ProviderPreparationRecordV1:
            raise TypeError("exact Docker preparation is required")
        if (
            type(create_mutation) is not AuthenticatedDockerMutationRecordV1
            or create_mutation.content.operation
            is not DockerControlOperationV1.CREATE
            or create_mutation.content.effect_id != preparation.effect_id
            or create_mutation.content.phase is not DockerMutationPhaseV1.ADMITTED
        ):
            raise ValueError("initial create mutation is not canonical")
        return cls.build(
            project_ref=preparation.project_ref,
            run_id=preparation.run_id,
            effect_id=preparation.effect_id,
            preparation_digest=preparation.preparation_digest,
            phase=DockerRunPhaseV1.CREATE_ADMITTED,
            revision=1,
            previous_record_digest=None,
            create_mutation=create_mutation,
            start_mutation=None,
            reconcile_operation=None,
            container_ref=None,
            submitted_at=None,
            process_exit_code=None,
            process_observation_digest=None,
            diagnostic=None,
            verified_artifacts=(),
            verified_inventory_digest=None,
        )

    @property
    def canonical_bytes(self) -> bytes:
        return _canonical({**self._body(), "record_digest": self.record_digest})

    @classmethod
    def from_canonical_bytes(cls, raw: bytes) -> "DockerRunMutationRecordV1":
        value = _read(raw)
        fields = frozenset({
            "schema_version", "project_ref", "run_id", "effect_id",
            "preparation_digest", "phase", "revision", "previous_record_digest",
            "create_mutation", "start_mutation", "reconcile_operation",
            "container_ref", "submitted_at", "process_exit_code",
            "process_observation_digest", "diagnostic", "verified_artifacts",
            "verified_inventory_digest", "record_digest",
        })
        exact = _mapping(value, fields, "Docker run mutation")
        if exact.pop("schema_version") != "synaptic-host-docker-run-mutation/v1":
            raise ValueError("unsupported Docker run mutation schema")
        exact["phase"] = DockerRunPhaseV1(exact["phase"])
        exact["create_mutation"] = _mutation_from_mapping(exact["create_mutation"])
        exact["start_mutation"] = _mutation_from_mapping(exact["start_mutation"])
        exact["reconcile_operation"] = (
            None
            if exact["reconcile_operation"] is None
            else DockerReconcileOperationV1(exact["reconcile_operation"])
        )
        artifacts = exact["verified_artifacts"]
        if type(artifacts) is not list:
            raise ValueError("verified_artifacts must be a list")
        exact["verified_artifacts"] = tuple(
            VerifiedDockerArtifactV1.from_mapping(item) for item in artifacts
        )
        return cls(**exact)


def verified_inventory_digest_v1(
    artifacts: tuple[VerifiedDockerArtifactV1, ...],
) -> str:
    if type(artifacts) is not tuple:
        raise TypeError("artifacts must be an exact tuple")
    return _seal(
        b"synaptic-host-docker-artifact-inventory/v1",
        [item.to_dict() for item in artifacts],
    )


def validate_docker_run_transition_v1(
    current: DockerRunMutationRecordV1,
    replacement: DockerRunMutationRecordV1,
) -> None:
    if type(current) is not DockerRunMutationRecordV1 or type(
        replacement
    ) is not DockerRunMutationRecordV1:
        raise TypeError("exact Docker mutation aggregates are required")
    if (
        replacement.project_ref != current.project_ref
        or replacement.run_id != current.run_id
        or replacement.effect_id != current.effect_id
        or replacement.preparation_digest != current.preparation_digest
        or replacement.revision != current.revision + 1
        or replacement.previous_record_digest != current.record_digest
    ):
        raise ValueError("Docker mutation transition identity is invalid")
    allowed = {
        DockerRunPhaseV1.CREATE_ADMITTED: {DockerRunPhaseV1.CREATE_ATTEMPTED},
        DockerRunPhaseV1.CREATE_ATTEMPTED: {
            DockerRunPhaseV1.CREATED, DockerRunPhaseV1.RECONCILE_REQUIRED,
        },
        DockerRunPhaseV1.CREATED: {DockerRunPhaseV1.START_ADMITTED},
        DockerRunPhaseV1.START_ADMITTED: {DockerRunPhaseV1.START_ATTEMPTED},
        DockerRunPhaseV1.START_ATTEMPTED: {
            DockerRunPhaseV1.SUBMITTED, DockerRunPhaseV1.RECONCILE_REQUIRED,
        },
        DockerRunPhaseV1.SUBMITTED: {
            DockerRunPhaseV1.PROCESS_SUCCEEDED,
            DockerRunPhaseV1.PROCESS_FAILED,
            DockerRunPhaseV1.RECONCILE_REQUIRED,
        },
        DockerRunPhaseV1.RECONCILE_REQUIRED: {
            DockerRunPhaseV1.CREATED,
            DockerRunPhaseV1.SUBMITTED,
            DockerRunPhaseV1.PROCESS_SUCCEEDED,
            DockerRunPhaseV1.PROCESS_FAILED,
        },
        DockerRunPhaseV1.PROCESS_SUCCEEDED: {
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
            DockerRunPhaseV1.PROCESS_FAILED,
        },
        DockerRunPhaseV1.PROCESS_FAILED: set(),
        DockerRunPhaseV1.ARTIFACTS_VERIFIED: set(),
    }
    if replacement.phase not in allowed[current.phase]:
        raise ValueError("Docker mutation phase transition is invalid")
    transition = (current.phase, replacement.phase)
    create_changed = current.create_mutation != replacement.create_mutation
    start_changed = current.start_mutation != replacement.start_mutation

    def require_cas(
        expected: AuthenticatedDockerMutationRecordV1,
        candidate: AuthenticatedDockerMutationRecordV1,
    ) -> None:
        try:
            DockerMutationCASRequestV1.build(
                expected.content.operation_id, expected, candidate
            )
        except DockerControlContractErrorV1:
            raise ValueError("low-level Docker mutation continuity is invalid") from None

    if transition == (
        DockerRunPhaseV1.CREATE_ADMITTED,
        DockerRunPhaseV1.CREATE_ATTEMPTED,
    ):
        if not create_changed or start_changed:
            raise ValueError("create attempt must change only the create envelope")
        require_cas(current.create_mutation, replacement.create_mutation)
    elif transition == (
        DockerRunPhaseV1.CREATE_ATTEMPTED,
        DockerRunPhaseV1.CREATED,
    ):
        if not create_changed or start_changed:
            raise ValueError("create verification must change only the create envelope")
        require_cas(current.create_mutation, replacement.create_mutation)
    elif transition == (
        DockerRunPhaseV1.CREATED,
        DockerRunPhaseV1.START_ADMITTED,
    ):
        start = replacement.start_mutation
        if (
            create_changed
            or current.start_mutation is not None
            or type(start) is not AuthenticatedDockerMutationRecordV1
            or start.content.phase is not DockerMutationPhaseV1.ADMITTED
        ):
            raise ValueError("start admission continuity is invalid")
    elif transition == (
        DockerRunPhaseV1.START_ADMITTED,
        DockerRunPhaseV1.START_ATTEMPTED,
    ):
        if create_changed or not start_changed:
            raise ValueError("start attempt must change only the start envelope")
        require_cas(current.start_mutation, replacement.start_mutation)
    elif transition == (
        DockerRunPhaseV1.START_ATTEMPTED,
        DockerRunPhaseV1.SUBMITTED,
    ):
        if create_changed or not start_changed:
            raise ValueError("start verification must change only the start envelope")
        require_cas(current.start_mutation, replacement.start_mutation)
    elif replacement.phase is DockerRunPhaseV1.RECONCILE_REQUIRED:
        expected_reconcile = {
            DockerRunPhaseV1.CREATE_ATTEMPTED:
                DockerReconcileOperationV1.LOOKUP_CREATE,
            DockerRunPhaseV1.START_ATTEMPTED:
                DockerReconcileOperationV1.LOOKUP_START,
            DockerRunPhaseV1.SUBMITTED:
                DockerReconcileOperationV1.OBSERVE_PROCESS,
        }.get(current.phase)
        if (
            replacement.reconcile_operation is not expected_reconcile
            or create_changed
            or start_changed
        ):
            raise ValueError("Docker reconciliation admission is invalid")
    elif current.phase is DockerRunPhaseV1.RECONCILE_REQUIRED:
        expected_exit = {
            DockerReconcileOperationV1.LOOKUP_CREATE:
                DockerRunPhaseV1.CREATED,
            DockerReconcileOperationV1.LOOKUP_START:
                DockerRunPhaseV1.SUBMITTED,
        }.get(current.reconcile_operation)
        if current.reconcile_operation is DockerReconcileOperationV1.LOOKUP_CREATE:
            if replacement.phase is not expected_exit or not create_changed or start_changed:
                raise ValueError("create reconciliation continuity is invalid")
            require_cas(current.create_mutation, replacement.create_mutation)
        elif current.reconcile_operation is DockerReconcileOperationV1.LOOKUP_START:
            if replacement.phase is not expected_exit or create_changed or not start_changed:
                raise ValueError("start reconciliation continuity is invalid")
            require_cas(current.start_mutation, replacement.start_mutation)
        elif (
            current.reconcile_operation
            is DockerReconcileOperationV1.OBSERVE_PROCESS
        ):
            if (
                replacement.phase not in {
                    DockerRunPhaseV1.PROCESS_SUCCEEDED,
                    DockerRunPhaseV1.PROCESS_FAILED,
                }
                or create_changed
                or start_changed
            ):
                raise ValueError("process reconciliation continuity is invalid")
        else:
            raise ValueError("Docker reconciliation operation is invalid")
    elif transition == (
        DockerRunPhaseV1.PROCESS_SUCCEEDED,
        DockerRunPhaseV1.PROCESS_FAILED,
    ):
        if (
            create_changed
            or start_changed
            or replacement.process_exit_code != 0
            or replacement.process_observation_digest
            != current.process_observation_digest
            or replacement.diagnostic not in _ZERO_EXIT_FAILURE_DIAGNOSTICS
            or replacement.verified_artifacts
            or replacement.verified_inventory_digest is not None
        ):
            raise ValueError("artifact verification failure continuity is invalid")
    elif create_changed or start_changed:
        raise ValueError("unaffected Docker mutation envelope changed")
    for name in ("container_ref", "submitted_at"):
        prior = getattr(current, name)
        if prior is not None and getattr(replacement, name) != prior:
            raise ValueError("stable Docker submission receipt changed")


__all__ = [
    "DockerReconcileOperationV1",
    "DockerRunMutationRecordV1",
    "DockerRunPhaseV1",
    "DockerStageProjectionV1",
    "ProviderPreparationRecordV1",
    "VerifiedDockerArtifactV1",
    "validate_docker_run_transition_v1",
    "verified_inventory_digest_v1",
]
