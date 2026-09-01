"""Prepared Docker run execution over one durable aggregate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path
import stat
from typing import TYPE_CHECKING, Callable, Protocol

if TYPE_CHECKING:
    from .publication_composition import HostPublicationFacadeV1
    from .sqlite_repository import SqliteTrainingRepository

from synaptic_tuner.api.v1 import RevisionConflict
from tuner.execution.foundation_v2.commands import SubmitCommandV2, parse_exact_command
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCommandBindingV1,
    DockerEffectIdentityV1,
    PreparedDockerPlanV1,
    labels_for,
    DockerCreateDispositionV1,
    DockerLabelsV1,
    DockerStartDispositionV1,
)
from synaptic_host.bundle_io_v1.model import digest_v1

from .docker_execution_state import (
    DockerRunMutationRecordV1,
    DockerRunPhaseV1,
    DockerReconcileOperationV1,
    ProviderPreparationRecordV1,
    VerifiedDockerArtifactV1,
    verified_inventory_digest_v1,
)
from .docker_staging import DockerStagingResultV1
from .docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1,
    DockerAdmissionDispositionV1,
    DockerAdmissionResultV1,
    DockerCASDispositionV1,
    DockerCASResultV1,
    DockerControlOperationV1,
    DockerMutationAdmissionRequestV1,
    DockerMutationCASRequestV1,
    DockerMutationLookupDispositionV1,
    DockerMutationLookupResultV1,
    DockerMutationPhaseV1,
    AuthenticatedDockerExpectedCreateBindingV1,
)
from .docker_v1.control_model import (
    DockerContainerInspectResultV1,
    DockerContainerStatusV1,
)
from .docker_v1.model import DockerCLIOutcomeV1
from .docker_v1.ports import DockerTypedCLIRunnerPortV1
from .docker_v1.verification import docker_create_projection_matches_v1


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _aggregate(
    current: DockerRunMutationRecordV1, **changes: object
) -> DockerRunMutationRecordV1:
    values = {
        name: getattr(current, name)
        for name in DockerRunMutationRecordV1.__dataclass_fields__
        if name != "record_digest"
    }
    values.update(changes)
    values["revision"] = current.revision + 1
    values["previous_record_digest"] = current.record_digest
    return DockerRunMutationRecordV1.build(**values)


@dataclass(frozen=True, slots=True)
class DockerPreparedRunRequestV1:
    project_ref: str
    run_id: str
    preparation: ProviderPreparationRecordV1
    prepared_plan: PreparedDockerPlanV1
    staging: DockerStagingResultV1

    def __post_init__(self) -> None:
        if (
            type(self.preparation) is not ProviderPreparationRecordV1
            or type(self.prepared_plan) is not PreparedDockerPlanV1
            or type(self.staging) is not DockerStagingResultV1
            or self.project_ref != self.preparation.project_ref
            or self.run_id != self.preparation.run_id
            or self.prepared_plan.project_ref != self.project_ref
            or self.prepared_plan.run_id != self.run_id
            or self.prepared_plan.plan_fingerprint
            != self.preparation.plan_fingerprint
            or self.prepared_plan.digest
            != self.preparation.prepared_docker_plan_digest
            or self.staging.projection != self.preparation.stage
        ):
            raise ValueError("prepared Docker run request is inconsistent")
        command = parse_exact_command(self.preparation.submit_command_bytes)
        profile = self.prepared_plan.profile
        if (
            type(command) is not SubmitCommandV2
            or command.digest != self.preparation.submit_command_digest
            or command.preparation.preparation_digest
            != self.prepared_plan.preparation_digest
            or command.preparation.provider != profile.provider
            or command.preparation.scope != profile.scope
            or command.preparation.source_digest != self.prepared_plan.source_digest
            or command.preparation.workload_digest
            != profile.workload.workload_digest
            or command.preparation.runtime_digest != profile.runtime.digest
            or command.preparation.resource_digest != profile.resource_digest
            or command.preparation.artifact_contract_digest
            != profile.artifacts.digest
            or command.preparation.quote_digest != profile.quote_digest
            or command.preparation.secret_requirements_digest
            != profile.secret_requirements_digest
            or command.executor != profile.executor_descriptor
        ):
            raise ValueError("submit command differs from the prepared Docker plan")


@dataclass(frozen=True, slots=True, init=False)
class DockerPreparedRunOutcomeV1:
    project_ref: str
    run_id: str
    effect_id: str
    phase: DockerRunPhaseV1
    revision: int
    record_digest: str
    container_ref: str | None
    submitted_at: str | None
    process_exit_code: int | None
    diagnostic: str | None
    verified_artifacts: tuple[VerifiedDockerArtifactV1, ...]
    publication_id: None = None
    publication_state: None = None

    def __new__(cls, *_args: object, **_kwargs: object):
        raise TypeError("Docker prepared run outcomes are factory-issued")

    def __post_init__(self) -> None:
        stable = self.phase in {
            DockerRunPhaseV1.SUBMITTED,
            DockerRunPhaseV1.PROCESS_SUCCEEDED, DockerRunPhaseV1.PROCESS_FAILED,
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        }
        closed = self.phase in {
            DockerRunPhaseV1.PROCESS_SUCCEEDED, DockerRunPhaseV1.PROCESS_FAILED,
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        }
        if (
            type(self.phase) is not DockerRunPhaseV1
            or type(self.revision) is not int
            or self.revision < 1
            or type(self.verified_artifacts) is not tuple
            or any(type(item) is not VerifiedDockerArtifactV1
                   for item in self.verified_artifacts)
            or self.publication_id is not None
            or self.publication_state is not None
            or (
                self.phase is not DockerRunPhaseV1.RECONCILE_REQUIRED
                and stable != (
                    type(self.container_ref) is str
                    and type(self.submitted_at) is str
                )
            )
            or closed != (type(self.process_exit_code) is int)
            or (
                self.phase is DockerRunPhaseV1.RECONCILE_REQUIRED
                and ((self.container_ref is None) != (self.submitted_at is None))
            )
            or (self.diagnostic is not None) != (
                self.phase in {
                    DockerRunPhaseV1.RECONCILE_REQUIRED,
                    DockerRunPhaseV1.PROCESS_FAILED,
                }
            )
            or (self.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED) != (
                len(self.verified_artifacts) == 5
            )
            or (
                self.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED
                and tuple(item.role for item in self.verified_artifacts) != (
                    "final_model", "tokenizer", "training_lineage",
                    "training_metrics", "workload_record",
                )
            )
        ):
            raise ValueError("Docker prepared run outcome is invalid")
        for value in (self.project_ref, self.run_id, self.effect_id, self.record_digest):
            if type(value) is not str or not value:
                raise ValueError("Docker prepared run outcome is invalid")
        if not _is_sha256(self.record_digest):
            raise ValueError("Docker prepared run outcome is invalid")

    @classmethod
    def from_record(
        cls, record: DockerRunMutationRecordV1
    ) -> "DockerPreparedRunOutcomeV1":
        if type(record) is not DockerRunMutationRecordV1:
            raise TypeError("exact Docker run aggregate is required")
        issued = object.__new__(cls)
        values = {
            "project_ref": record.project_ref,
            "run_id": record.run_id,
            "effect_id": record.effect_id,
            "phase": record.phase,
            "revision": record.revision,
            "record_digest": record.record_digest,
            "container_ref": record.container_ref,
            "submitted_at": record.submitted_at,
            "process_exit_code": record.process_exit_code,
            "diagnostic": record.diagnostic,
            "verified_artifacts": record.verified_artifacts,
            "publication_id": None,
            "publication_state": None,
        }
        for name, value in values.items():
            object.__setattr__(issued, name, value)
        issued.__post_init__()
        return issued

    @property
    def failed(self) -> bool:
        return self.phase is DockerRunPhaseV1.PROCESS_FAILED

    @property
    def published(self) -> bool:
        return self.publication_id is not None or self.publication_state is not None

    @property
    def reconcile_required(self) -> bool:
        return self.phase is DockerRunPhaseV1.RECONCILE_REQUIRED

    @property
    def pending(self) -> bool:
        return self.phase not in {
            DockerRunPhaseV1.PROCESS_FAILED,
            DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        }


@dataclass(frozen=True, slots=True)
class DockerPreparedControlsV1:
    labels: DockerLabelsV1
    expected_create: AuthenticatedDockerExpectedCreateBindingV1
    create: object
    start: object
    control: object
    typed_runner: DockerTypedCLIRunnerPortV1

    def __post_init__(self) -> None:
        if (
            type(self.labels) is not DockerLabelsV1
            or type(self.expected_create)
            is not AuthenticatedDockerExpectedCreateBindingV1
            or self.expected_create.content.labels != self.labels
            or not callable(getattr(self.create, "create_once", None))
            or not callable(getattr(self.start, "start_once", None))
            or not callable(getattr(self.control, "lookup", None))
            or not callable(getattr(self.typed_runner, "inspect_container", None))
        ):
            raise ValueError("prepared Docker controls are invalid")


class DockerPreparedControlFactoryPortV1(Protocol):
    def build(
        self, request: DockerPreparedRunRequestV1, mutation_repository: object,
    ) -> DockerPreparedControlsV1: ...


class DockerPreparedControlFactoryV1:
    """Derive exact effect inputs before delegating low-level composition."""

    def __init__(self, builder: object) -> None:
        if not callable(getattr(builder, "build", None)):
            raise TypeError("Docker control builder is unavailable")
        self._builder = builder

    def build(
        self,
        request: DockerPreparedRunRequestV1,
        mutation_repository: object,
    ) -> DockerPreparedControlsV1:
        command = parse_exact_command(request.preparation.submit_command_bytes)
        if type(command) is not SubmitCommandV2:
            raise ValueError("durable command is not an exact submit command")
        identity = DockerEffectIdentityV1(
            command.digest,
            command.operation.effect.effect_id,
            "submit",
            request.prepared_plan,
        )
        if identity.effect_id != request.preparation.effect_id:
            raise ValueError("durable submit effect differs from preparation")
        labels = labels_for(identity)
        binding = DockerCommandBindingV1(identity, command.canonical_bytes)
        controls = self._builder.build(
            request=request,
            mutation_repository=mutation_repository,
            binding=binding,
            labels=labels,
        )
        create = getattr(controls, "create", None)
        start = getattr(controls, "start", None)
        control = getattr(controls, "control", None)
        typed_runner = getattr(controls, "typed_runner", None)
        expected_create = getattr(controls, "expected_create", None)
        if not callable(getattr(create, "create_once", None)) or not callable(
            getattr(start, "start_once", None)
        ) or type(expected_create) is not AuthenticatedDockerExpectedCreateBindingV1 or (
            expected_create.content.labels != labels
        ) or not callable(getattr(control, "lookup", None)) or not callable(
            getattr(typed_runner, "inspect_container", None)
        ):
            raise TypeError("Docker control builder returned invalid controls")
        return DockerPreparedControlsV1(
            labels, expected_create, create, start, control, typed_runner
        )


class DockerAggregateMutationRepositoryV1:
    """Present one aggregate as the existing authenticated low-level CAS port."""

    def __init__(
        self, repository: object, *, project_ref: str, run_id: str,
        clock: Callable[[], str],
    ) -> None:
        if not callable(clock):
            raise TypeError("clock is required")
        self._repository = repository
        self._project_ref = project_ref
        self._run_id = run_id
        self._clock = clock

    def _load(self) -> DockerRunMutationRecordV1:
        value = self._repository.load_docker_run_mutation(
            self._project_ref, self._run_id
        )
        if type(value) is not DockerRunMutationRecordV1:
            raise ValueError("Docker run mutation is unavailable")
        return value

    @staticmethod
    def _selected(
        current: DockerRunMutationRecordV1, operation: DockerControlOperationV1
    ) -> AuthenticatedDockerMutationRecordV1 | None:
        return (
            current.create_mutation
            if operation is DockerControlOperationV1.CREATE
            else current.start_mutation
        )

    def _cas(
        self, current: DockerRunMutationRecordV1,
        replacement: DockerRunMutationRecordV1,
    ) -> DockerRunMutationRecordV1:
        return self._repository.compare_and_swap_docker_run_mutation(
            replacement,
            expected_revision=current.revision,
            expected_record_digest=current.record_digest,
        )

    def admit(
        self, request: DockerMutationAdmissionRequestV1
    ) -> DockerAdmissionResultV1:
        if type(request) is not DockerMutationAdmissionRequestV1:
            raise TypeError("exact Docker admission request is required")
        current = self._load()
        operation = request.candidate.content.operation
        selected = self._selected(current, operation)
        if selected is not None:
            disposition = (
                DockerAdmissionDispositionV1.EXISTING
                if selected.content.control_intent_proof_digest
                == request.candidate.content.control_intent_proof_digest
                else DockerAdmissionDispositionV1.CONFLICT
            )
            return DockerAdmissionResultV1.build(request, disposition, selected)
        if (
            operation is not DockerControlOperationV1.START
            or current.phase is not DockerRunPhaseV1.CREATED
        ):
            return DockerAdmissionResultV1.build(
                request, DockerAdmissionDispositionV1.INDETERMINATE, None
            )
        replacement = _aggregate(
            current,
            phase=DockerRunPhaseV1.START_ADMITTED,
            start_mutation=request.candidate,
        )
        try:
            durable = self._cas(current, replacement)
        except RevisionConflict:
            durable = self._load()
            selected = durable.start_mutation
            if selected is None:
                return DockerAdmissionResultV1.build(
                    request, DockerAdmissionDispositionV1.INDETERMINATE, None
                )
            disposition = (
                DockerAdmissionDispositionV1.EXISTING
                if selected.content.control_intent_proof_digest
                == request.candidate.content.control_intent_proof_digest
                else DockerAdmissionDispositionV1.CONFLICT
            )
            return DockerAdmissionResultV1.build(request, disposition, selected)
        return DockerAdmissionResultV1.build(
            request, DockerAdmissionDispositionV1.ADMITTED,
            durable.start_mutation,
        )

    def compare_and_swap(
        self, request: DockerMutationCASRequestV1
    ) -> DockerCASResultV1:
        if type(request) is not DockerMutationCASRequestV1:
            raise TypeError("exact Docker CAS request is required")
        current = self._load()
        operation = request.expected.content.operation
        selected = self._selected(current, operation)
        if selected != request.expected:
            if selected is None:
                return DockerCASResultV1.build(
                    request, DockerCASDispositionV1.INDETERMINATE, None
                )
            return DockerCASResultV1.build(
                request, DockerCASDispositionV1.CURRENT, selected
            )
        phase = request.replacement.content.phase
        if operation is DockerControlOperationV1.CREATE:
            aggregate_phase = (
                DockerRunPhaseV1.CREATE_ATTEMPTED
                if phase is DockerMutationPhaseV1.ATTEMPTED
                else DockerRunPhaseV1.CREATED
            )
            changes = {
                "phase": aggregate_phase,
                "create_mutation": request.replacement,
            }
            if aggregate_phase is DockerRunPhaseV1.CREATED:
                changes.update({"reconcile_operation": None, "diagnostic": None})
        else:
            aggregate_phase = (
                DockerRunPhaseV1.START_ATTEMPTED
                if phase is DockerMutationPhaseV1.ATTEMPTED
                else DockerRunPhaseV1.SUBMITTED
            )
            changes = {
                "phase": aggregate_phase,
                "start_mutation": request.replacement,
            }
            if aggregate_phase is DockerRunPhaseV1.SUBMITTED:
                changes.update({
                    "container_ref": request.replacement.content.container_ref,
                    "submitted_at": self._clock(),
                    "reconcile_operation": None,
                    "diagnostic": None,
                })
        replacement = _aggregate(current, **changes)
        try:
            durable = self._cas(current, replacement)
        except RevisionConflict:
            durable = self._load()
            selected = self._selected(durable, operation)
            if selected is None:
                return DockerCASResultV1.build(
                    request, DockerCASDispositionV1.INDETERMINATE, None
                )
            return DockerCASResultV1.build(
                request, DockerCASDispositionV1.CURRENT, selected
            )
        return DockerCASResultV1.build(
            request, DockerCASDispositionV1.APPLIED,
            self._selected(durable, operation),
        )

    def lookup(self, operation_id: str) -> DockerMutationLookupResultV1:
        current = self._load()
        records = tuple(
            record for record in (
                current.create_mutation, current.start_mutation
            )
            if record is not None
            and record.content.operation_id == operation_id
        )
        if len(records) != 1:
            return DockerMutationLookupResultV1.build(
                operation_id, DockerMutationLookupDispositionV1.ABSENT, None
            )
        return DockerMutationLookupResultV1.build(
            operation_id, DockerMutationLookupDispositionV1.FOUND, records[0]
        )


class _DockerProcessObservationKindV1(str, Enum):
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNCERTAIN = "UNCERTAIN"
    CONTRADICTED = "CONTRADICTED"


@dataclass(frozen=True, slots=True)
class _DockerProcessObservationV1:
    kind: _DockerProcessObservationKindV1
    exit_code: int | None
    observation_digest: str | None
    diagnostic: str | None

    def __post_init__(self) -> None:
        if type(self.kind) is not _DockerProcessObservationKindV1:
            raise TypeError("exact Docker process observation kind is required")
        matrix = {
            _DockerProcessObservationKindV1.RUNNING: (
                self.exit_code is None and type(self.observation_digest) is str
                and self.diagnostic is None
            ),
            _DockerProcessObservationKindV1.SUCCEEDED: (
                self.exit_code == 0 and type(self.observation_digest) is str
                and self.diagnostic is None
            ),
            _DockerProcessObservationKindV1.FAILED: (
                type(self.exit_code) is int
                and type(self.observation_digest) is str
                and self.diagnostic in {"PROCESS_EXIT_NONZERO", "PROCESS_DEAD"}
                and (
                    self.diagnostic != "PROCESS_EXIT_NONZERO"
                    or self.exit_code != 0
                )
            ),
            _DockerProcessObservationKindV1.UNCERTAIN: (
                self.exit_code is None and self.observation_digest is None
                and self.diagnostic == "PROCESS_OBSERVATION_UNAVAILABLE"
            ),
            _DockerProcessObservationKindV1.CONTRADICTED: (
                self.exit_code is None and type(self.observation_digest) is str
                and self.diagnostic in {
                    "CONTAINER_IDENTITY_MISMATCH", "CONTAINER_STATE_REGRESSED"
                }
            ),
        }
        if not matrix[self.kind]:
            raise ValueError("Docker process observation matrix is invalid")
        if self.observation_digest is not None and not _is_sha256(
            self.observation_digest
        ):
            raise ValueError("Docker process observation digest is invalid")


def _observe_docker_process_v1(
    *, request: DockerPreparedRunRequestV1,
    controls: DockerPreparedControlsV1, container_ref: str,
) -> _DockerProcessObservationV1:
    try:
        raw = controls.typed_runner.inspect_container(container_ref)
        if type(raw) is not DockerContainerInspectResultV1:
            raise ValueError
        inspected = DockerContainerInspectResultV1(
            raw.result_kind, raw.target, raw.request_digest, raw.command,
            raw.evidence, raw.projection, raw.result_digest,
        )
        if (
            inspected.target != container_ref
            or inspected.evidence.policy_digest
            != request.preparation.cli_policy_digest
            or inspected.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS
            or inspected.projection is None
        ):
            raise ValueError
        projection = inspected.projection
        observation_digest = digest_v1({
            "schema_version": "synaptic-host-docker-process-observation/v1",
            "preparation_digest": request.preparation.preparation_digest,
            "container_ref": container_ref,
            "inspect_result_digest": inspected.result_digest,
            "projection_digest": projection.projection_digest,
            "status": projection.state.status.value,
            "exit_code": projection.state.exit_code,
        })
        if not docker_create_projection_matches_v1(
            controls.labels, controls.expected_create,
            controls.expected_create.content.environment_binding,
            projection, container_ref, inspected.evidence,
        ):
            return _DockerProcessObservationV1(
                _DockerProcessObservationKindV1.CONTRADICTED, None,
                observation_digest, "CONTAINER_IDENTITY_MISMATCH",
            )
        state = projection.state
        if state.status in {
            DockerContainerStatusV1.RUNNING,
            DockerContainerStatusV1.PAUSED,
            DockerContainerStatusV1.RESTARTING,
        }:
            return _DockerProcessObservationV1(
                _DockerProcessObservationKindV1.RUNNING, None,
                observation_digest, None,
            )
        if state.status is DockerContainerStatusV1.CREATED:
            return _DockerProcessObservationV1(
                _DockerProcessObservationKindV1.CONTRADICTED, None,
                observation_digest, "CONTAINER_STATE_REGRESSED",
            )
        if state.status is DockerContainerStatusV1.EXITED:
            if state.exit_code == 0:
                return _DockerProcessObservationV1(
                    _DockerProcessObservationKindV1.SUCCEEDED, 0,
                    observation_digest, None,
                )
            return _DockerProcessObservationV1(
                _DockerProcessObservationKindV1.FAILED, state.exit_code,
                observation_digest, "PROCESS_EXIT_NONZERO",
            )
        if state.status is DockerContainerStatusV1.DEAD:
            return _DockerProcessObservationV1(
                _DockerProcessObservationKindV1.FAILED, state.exit_code,
                observation_digest, "PROCESS_DEAD",
            )
    except BaseException:
        pass
    return _DockerProcessObservationV1(
        _DockerProcessObservationKindV1.UNCERTAIN, None, None,
        "PROCESS_OBSERVATION_UNAVAILABLE",
    )


class _DockerArtifactVerificationKindV1(str, Enum):
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True, slots=True)
class _DockerArtifactVerificationV1:
    kind: _DockerArtifactVerificationKindV1
    artifacts: tuple[VerifiedDockerArtifactV1, ...]
    inventory_digest: str | None
    diagnostic: str | None

    def __post_init__(self) -> None:
        if type(self.kind) is not _DockerArtifactVerificationKindV1:
            raise TypeError("exact Docker artifact verification kind is required")
        verified = self.kind is _DockerArtifactVerificationKindV1.VERIFIED
        if (
            type(self.artifacts) is not tuple
            or any(type(item) is not VerifiedDockerArtifactV1 for item in self.artifacts)
            or verified != (len(self.artifacts) == 5 and type(self.inventory_digest) is str)
            or verified == (self.diagnostic is not None)
            or (
                not verified
                and (self.artifacts or self.inventory_digest is not None)
            )
            or (
                verified and tuple(item.role for item in self.artifacts) != (
                    "final_model", "tokenizer", "training_lineage",
                    "training_metrics", "workload_record",
                )
            )
            or (
                self.kind is _DockerArtifactVerificationKindV1.INVALID
                and self.diagnostic not in {
                    "ARTIFACT_INVENTORY_MISSING", "ARTIFACT_INVENTORY_INVALID",
                    "ARTIFACT_INTEGRITY_INVALID", "ARTIFACT_SEMANTIC_INVALID",
                }
            )
            or (
                self.kind is _DockerArtifactVerificationKindV1.UNCERTAIN
                and self.diagnostic != "ARTIFACT_READ_UNAVAILABLE"
            )
        ):
            raise ValueError("Docker artifact verification matrix is invalid")
        if self.inventory_digest is not None and not _is_sha256(
            self.inventory_digest
        ):
            raise ValueError("Docker artifact inventory digest is invalid")
        if verified and self.inventory_digest != verified_inventory_digest_v1(
            self.artifacts
        ):
            raise ValueError("Docker artifact inventory digest is invalid")


class _DockerPreparedArtifactVerifierPortV1(Protocol):
    def verify(
        self, *, request: DockerPreparedRunRequestV1,
        process_observation_digest: str,
    ) -> _DockerArtifactVerificationV1: ...


class _DockerPreparedArtifactVerifierV1:
    """Read and verify the exact runtime artifact inventory without following links."""

    @staticmethod
    def _directory_token(path: Path) -> tuple[int, int]:
        metadata = path.lstat()
        attributes = getattr(metadata, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or attributes & reparse
        ):
            raise ValueError("invalid artifact directory")
        return metadata.st_dev, metadata.st_ino

    @classmethod
    def _directory_chain(
        cls, root: Path, relative: tuple[str, ...],
    ) -> tuple[tuple[Path, tuple[int, int]], ...]:
        if not root.is_absolute() or any(part in {"", ".", ".."} for part in relative):
            raise ValueError("invalid artifact containment")
        cursor = root
        result = [(cursor, cls._directory_token(cursor))]
        for part in relative:
            cursor /= part
            result.append((cursor, cls._directory_token(cursor)))
        return tuple(result)

    @classmethod
    def _verify_directory_chain(
        cls, chain: tuple[tuple[Path, tuple[int, int]], ...],
    ) -> None:
        if any(cls._directory_token(path) != token for path, token in chain):
            raise OSError("artifact directory changed during read")

    @staticmethod
    def _read_regular(path: Path, maximum: int) -> bytes:
        before = path.lstat()
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

        def snapshot(metadata: os.stat_result) -> tuple[object, ...]:
            attributes = getattr(metadata, "st_file_attributes", 0)
            if (
                stat.S_ISLNK(metadata.st_mode)
                or not stat.S_ISREG(metadata.st_mode)
                or attributes & reparse
                or metadata.st_size > maximum
            ):
                raise ValueError("invalid artifact member")
            return (
                metadata.st_dev, metadata.st_ino,
                stat.S_IFMT(metadata.st_mode), metadata.st_size,
                bool(attributes & reparse),
                getattr(metadata, "st_mtime_ns", None),
                getattr(metadata, "st_ctime_ns", None),
            )

        baseline = snapshot(before)
        if before.st_size < 0:
            raise ValueError("invalid artifact member")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if snapshot(opened) != baseline:
                raise ValueError("artifact changed before read")
            data = bytearray()
            while len(data) <= maximum:
                chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
            after_read = os.fstat(descriptor)
            if snapshot(after_read) != baseline:
                raise ValueError("artifact changed during read")
            if len(data) != before.st_size or len(data) > maximum:
                raise ValueError("invalid artifact member")
        finally:
            os.close(descriptor)
        try:
            final = path.lstat()
        except FileNotFoundError:
            raise ValueError("artifact changed after read") from None
        if snapshot(final) != baseline:
            raise ValueError("artifact changed after read")
        return bytes(data)

    def verify(
        self, *, request: DockerPreparedRunRequestV1,
        process_observation_digest: str,
    ) -> _DockerArtifactVerificationV1:
        from synaptic_tuner.api.v1.training import CanonicalDocument
        from tuner.runtime.artifacts import ArtifactEntry, ArtifactInventory
        from tuner.runtime.dispatch import ProcessResult
        from tuner.runtime.verification import (
            ArtifactReadError, VerificationService, VerificationStatus,
            WorkloadBindingVerifier,
        )
        from tuner.training.methods.sft import SFT_ARTIFACT_CONTRACT
        from tuner.training.recipes import CompiledWorkload

        root = request.staging.artifact_root
        inventory_path = root / "state" / "runtime-v1-inventory.json"
        maximum_member = request.prepared_plan.profile.artifacts.maximum_artifact_bytes
        maximum_total = request.prepared_plan.profile.artifacts.maximum_total_bytes
        try:
            state_chain = self._directory_chain(root, ("state",))
            raw_inventory = self._read_regular(inventory_path, 262_144)
            self._verify_directory_chain(state_chain)
        except FileNotFoundError:
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None,
                "ARTIFACT_INVENTORY_MISSING",
            )
        except ValueError:
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None,
                "ARTIFACT_INVENTORY_INVALID",
            )
        except (PermissionError, OSError):
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.UNCERTAIN, (), None,
                "ARTIFACT_READ_UNAVAILABLE",
            )
        try:
            document = json.loads(raw_inventory.decode("utf-8"))
            canonical = json.dumps(
                document, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8")
            if canonical != raw_inventory or set(document) != {
                "schema_version", "workload_fingerprint", "artifacts"
            } or document["schema_version"] != "synaptic-artifact-inventory/v1" or (
                document["workload_fingerprint"]
                != request.staging.worker_bundle.workload_fingerprint
            ):
                raise ValueError
            rows = document["artifacts"]
            if type(rows) is not list or len(rows) != 5:
                raise ValueError
            entries = tuple(ArtifactEntry(
                row["role"], row["path"], row["sha256"], row["size"]
            ) for row in rows if type(row) is dict and set(row) == {
                "role", "path", "sha256", "size"
            })
            if len(entries) != 5 or sum(item.size for item in entries) > maximum_total:
                raise ValueError
            inventory = ArtifactInventory(entries)
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None,
                "ARTIFACT_INVENTORY_INVALID",
            )

        verifier = self
        data_root = root / "artifacts"
        try:
            data_chain = self._directory_chain(root, ("artifacts",))
        except FileNotFoundError:
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None,
                "ARTIFACT_INTEGRITY_INVALID",
            )
        except ValueError:
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None,
                "ARTIFACT_INTEGRITY_INVALID",
            )
        except (PermissionError, OSError):
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.UNCERTAIN, (), None,
                "ARTIFACT_READ_UNAVAILABLE",
            )

        class Reader:
            uncertain = False

            def read_bytes(self, artifact, *, maximum):
                try:
                    if artifact.size > min(maximum, maximum_member):
                        raise ValueError
                    relative = Path(artifact.path)
                    candidate = data_root.joinpath(*relative.parts)
                    chain = verifier._directory_chain(
                        data_root, tuple(relative.parts[:-1])
                    )
                    data = verifier._read_regular(
                        candidate, min(maximum, maximum_member)
                    )
                    verifier._verify_directory_chain(data_chain)
                    verifier._verify_directory_chain(chain)
                    return data
                except FileNotFoundError as error:
                    raise ArtifactReadError("artifact_read_failed") from error
                except (PermissionError, OSError) as error:
                    self.uncertain = True
                    raise ArtifactReadError("artifact read unavailable") from error
                except ValueError as error:
                    raise ArtifactReadError("artifact_read_failed") from error

        try:
            workload_bytes = request.staging.worker_bundle.canonical_workload_bytes
            workload_document = CanonicalDocument(
                workload_bytes.decode("utf-8")
            ).to_dict()
            workload = CompiledWorkload(
                method=workload_document["method"],
                schema_version=workload_document["schema_version"],
                entrypoint=workload_document["entrypoint"],
                canonical_bytes=workload_bytes,
            )
            reader = Reader()
            report = VerificationService(WorkloadBindingVerifier(
                closure_digest=request.preparation.stage.worker_source_closure_digest,
                closure_manifest_path=(
                    request.staging.worker_bundle.closure_manifest_runtime_path.as_posix()
                ),
            )).verify(
                provider_completed=True, process=ProcessResult(0),
                workload=workload, contract=SFT_ARTIFACT_CONTRACT,
                inventory=inventory, reader=reader,
            )
        except (PermissionError, OSError):
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.UNCERTAIN, (), None,
                "ARTIFACT_READ_UNAVAILABLE",
            )
        except Exception:
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.UNCERTAIN, (), None,
                "ARTIFACT_READ_UNAVAILABLE",
            )
        if reader.uncertain:
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.UNCERTAIN, (), None,
                "ARTIFACT_READ_UNAVAILABLE",
            )
        if any(
            "artifact_read_failed" in item.errors
            for item in report.integrity.artifacts
        ):
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None,
                "ARTIFACT_INTEGRITY_INVALID",
            )
        if report.status is not VerificationStatus.VERIFIED:
            diagnostic = (
                "ARTIFACT_INTEGRITY_INVALID"
                if not report.integrity.valid else "ARTIFACT_SEMANTIC_INVALID"
            )
            return _DockerArtifactVerificationV1(
                _DockerArtifactVerificationKindV1.INVALID, (), None, diagnostic
            )
        artifacts = tuple(sorted((VerifiedDockerArtifactV1(
            item.role, item.path, item.size, item.sha256
        ) for item in inventory.entries), key=lambda item: item.role))
        return _DockerArtifactVerificationV1(
            _DockerArtifactVerificationKindV1.VERIFIED, artifacts,
            verified_inventory_digest_v1(artifacts), None,
        )


class DockerPreparedRunServiceV1:
    def __init__(
        self, *, repository: SqliteTrainingRepository,
        control_factory: DockerPreparedControlFactoryPortV1,
        artifact_verifier: _DockerPreparedArtifactVerifierPortV1,
        clock: Callable[[], str], publication: HostPublicationFacadeV1 | None,
    ) -> None:
        if (
            publication is not None
            or not callable(clock)
            or not callable(getattr(repository, "load_docker_run_mutation", None))
            or not callable(getattr(
                repository, "compare_and_swap_docker_run_mutation", None
            ))
            or not callable(getattr(control_factory, "build", None))
            or not callable(getattr(artifact_verifier, "verify", None))
        ):
            raise ValueError("Docker Slice A does not support publication")
        self._repository = repository
        self._control_factory = control_factory
        self._artifact_verifier = artifact_verifier
        self._clock = clock

    def _load(self, request: DockerPreparedRunRequestV1):
        record = self._repository.load_docker_run_mutation(
            request.project_ref, request.run_id
        )
        if type(record) is not DockerRunMutationRecordV1 or (
            record.preparation_digest != request.preparation.preparation_digest
        ):
            raise ValueError("durable Docker run is unavailable")
        return record

    def _write(self, current, **changes):
        replacement = _aggregate(current, **changes)
        return self._repository.compare_and_swap_docker_run_mutation(
            replacement, expected_revision=current.revision,
            expected_record_digest=current.record_digest,
        )

    def _require_reconcile(self, current, operation, diagnostic):
        if current.phase is DockerRunPhaseV1.RECONCILE_REQUIRED:
            return current
        return self._write(
            current, phase=DockerRunPhaseV1.RECONCILE_REQUIRED,
            reconcile_operation=operation, diagnostic=diagnostic,
        )

    def submit(self, request: DockerPreparedRunRequestV1) -> DockerPreparedRunOutcomeV1:
        initial = self._load(request)
        adapter = DockerAggregateMutationRepositoryV1(
            self._repository, project_ref=request.project_ref,
            run_id=request.run_id, clock=self._clock,
        )
        controls = self._control_factory.build(request, adapter)
        profile = request.prepared_plan.profile
        if initial.phase in {
            DockerRunPhaseV1.CREATE_ADMITTED,
            DockerRunPhaseV1.CREATE_ATTEMPTED,
        }:
            result = controls.create.create_once(
                labels=controls.labels, image=profile.image,
                runtime=profile.runtime, workload=profile.workload,
                source_ref=profile.roots.source_ref,
                artifact_ref=profile.roots.artifact_ref,
                working_directory=request.staging.worker_bundle.dispatch.cwd.as_posix(),
            )
            current = self._load(request)
            if result.disposition is not DockerCreateDispositionV1.CREATED:
                if current.phase is DockerRunPhaseV1.CREATE_ATTEMPTED:
                    current = self._require_reconcile(
                        current, DockerReconcileOperationV1.LOOKUP_CREATE,
                        "CREATE_RESULT_UNCERTAIN",
                    )
            return DockerPreparedRunOutcomeV1.from_record(current)
        if initial.phase is DockerRunPhaseV1.CREATED:
            result = controls.start.start_once(
                initial.create_mutation.content.container_ref, controls.labels
            )
            current = self._load(request)
            if result.disposition is not DockerStartDispositionV1.STARTED:
                if current.phase is DockerRunPhaseV1.START_ATTEMPTED:
                    current = self._require_reconcile(
                        current, DockerReconcileOperationV1.LOOKUP_START,
                        "START_RESULT_UNCERTAIN",
                    )
            return DockerPreparedRunOutcomeV1.from_record(current)
        return DockerPreparedRunOutcomeV1.from_record(initial)

    def _reconcile_low_level(
        self, request: DockerPreparedRunRequestV1,
        current: DockerRunMutationRecordV1,
        controls: DockerPreparedControlsV1,
    ) -> DockerPreparedRunOutcomeV1:
        profile = request.prepared_plan.profile
        if current.reconcile_operation is DockerReconcileOperationV1.LOOKUP_CREATE:
            controls.create.create_once(
                labels=controls.labels, image=profile.image,
                runtime=profile.runtime, workload=profile.workload,
                source_ref=profile.roots.source_ref,
                artifact_ref=profile.roots.artifact_ref,
                working_directory=request.staging.worker_bundle.dispatch.cwd.as_posix(),
            )
        else:
            controls.start.start_once(
                current.create_mutation.content.container_ref, controls.labels
            )
        return DockerPreparedRunOutcomeV1.from_record(self._load(request))

    def reconcile(self, request: DockerPreparedRunRequestV1) -> DockerPreparedRunOutcomeV1:
        current = self._load(request)
        if current.phase is DockerRunPhaseV1.PROCESS_SUCCEEDED:
            verified = self._artifact_verifier.verify(
                request=request,
                process_observation_digest=current.process_observation_digest,
            )
            if verified.kind is _DockerArtifactVerificationKindV1.UNCERTAIN:
                return DockerPreparedRunOutcomeV1.from_record(current)
            if verified.kind is _DockerArtifactVerificationKindV1.INVALID:
                current = self._write(
                    current, phase=DockerRunPhaseV1.PROCESS_FAILED,
                    diagnostic=verified.diagnostic,
                )
            else:
                current = self._write(
                    current, phase=DockerRunPhaseV1.ARTIFACTS_VERIFIED,
                    verified_artifacts=verified.artifacts,
                    verified_inventory_digest=verified.inventory_digest,
                )
            return DockerPreparedRunOutcomeV1.from_record(current)
        adapter = DockerAggregateMutationRepositoryV1(
            self._repository, project_ref=request.project_ref,
            run_id=request.run_id, clock=self._clock,
        )
        controls = self._control_factory.build(request, adapter)
        if current.reconcile_operation in {
            DockerReconcileOperationV1.LOOKUP_CREATE,
            DockerReconcileOperationV1.LOOKUP_START,
        }:
            return self._reconcile_low_level(request, current, controls)
        if current.phase is DockerRunPhaseV1.SUBMITTED or (
            current.phase is DockerRunPhaseV1.RECONCILE_REQUIRED
            and current.reconcile_operation is DockerReconcileOperationV1.OBSERVE_PROCESS
        ):
            observation = _observe_docker_process_v1(
                request=request, controls=controls,
                container_ref=current.container_ref,
            )
            if observation.kind is _DockerProcessObservationKindV1.RUNNING:
                return DockerPreparedRunOutcomeV1.from_record(current)
            if observation.kind in {
                _DockerProcessObservationKindV1.UNCERTAIN,
                _DockerProcessObservationKindV1.CONTRADICTED,
            }:
                current = self._require_reconcile(
                    current, DockerReconcileOperationV1.OBSERVE_PROCESS,
                    observation.diagnostic,
                )
                return DockerPreparedRunOutcomeV1.from_record(current)
            phase = (
                DockerRunPhaseV1.PROCESS_SUCCEEDED
                if observation.kind is _DockerProcessObservationKindV1.SUCCEEDED
                else DockerRunPhaseV1.PROCESS_FAILED
            )
            current = self._write(
                current, phase=phase,
                reconcile_operation=None,
                process_exit_code=observation.exit_code,
                process_observation_digest=observation.observation_digest,
                diagnostic=observation.diagnostic,
            )
            return DockerPreparedRunOutcomeV1.from_record(current)
        return DockerPreparedRunOutcomeV1.from_record(current)


__all__ = [
    "DockerAggregateMutationRepositoryV1",
    "DockerPreparedControlFactoryV1",
    "DockerPreparedControlsV1",
    "DockerPreparedRunServiceV1",
    "DockerPreparedRunOutcomeV1",
    "DockerPreparedRunRequestV1",
]
