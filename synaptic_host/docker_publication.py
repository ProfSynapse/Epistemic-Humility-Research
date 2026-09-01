"""Publication composition for one exactly verified Docker run."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
from threading import RLock
from types import FunctionType
from typing import Callable, Iterator
from weakref import WeakKeyDictionary

from synaptic_tuner.api.v1 import (
    ProjectContext,
    PublicationRequest,
    PublicationResult,
    RunArtifactRequest,
    RunListRequest,
    RunOperationCode,
    RunOperationError,
    RunOutcome,
    RunVerification,
    RunsAPI,
    TrainingRunRef,
    TrainingRunState,
    VerifiedArtifact,
)

from .artifact_destinations import (
    artifact_destination_declaration_digest_v1,
    parse_artifact_destination_config_v1,
)
from .docker_execution import DockerPreparedRunRequestV1
from .docker_execution_state import DockerRunMutationRecordV1, DockerRunPhaseV1
from .publication_composition import (
    HostPublicationFacadeV1,
    PublicationConfigurationDocumentsV1,
    compose_host_publication_v1,
)


_MAX_CONFIG_BYTES = 1_048_576
_CHUNK_BYTES = 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _file_snapshot(value: os.stat_result, maximum: int) -> tuple[object, ...]:
    attributes = getattr(value, "st_file_attributes", 0)
    if (
        not stat.S_ISREG(value.st_mode)
        or stat.S_ISLNK(value.st_mode)
        or attributes & _REPARSE
        or not 0 <= value.st_size <= maximum
    ):
        raise ValueError("publication source is not a bounded regular file")
    return (
        value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode), value.st_size,
        bool(attributes & _REPARSE),
        getattr(value, "st_mtime_ns", None),
        getattr(value, "st_ctime_ns", None),
    )


def _directory_snapshot(path: Path) -> tuple[object, ...]:
    value = path.lstat()
    attributes = getattr(value, "st_file_attributes", 0)
    if not stat.S_ISDIR(value.st_mode) or stat.S_ISLNK(value.st_mode) or attributes & _REPARSE:
        raise ValueError("publication source directory is redirected")
    return value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode), bool(attributes & _REPARSE)


def _directory_chain(root: Path, parts: tuple[str, ...]):
    relative = Path(*parts)
    if (
        not root.is_absolute()
        or relative.is_absolute()
        or relative.drive
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise ValueError("publication source path is invalid")
    candidate = root.joinpath(*parts)
    try:
        if os.path.commonpath((str(root), str(candidate))) != str(root):
            raise ValueError("publication source path escapes its root")
    except ValueError:
        raise ValueError("publication source path escapes its root") from None
    cursor = root
    result = [(cursor, _directory_snapshot(cursor))]
    for part in parts:
        cursor /= part
        result.append((cursor, _directory_snapshot(cursor)))
    return tuple(result)


def _check_chain(chain) -> None:
    if any(_directory_snapshot(path) != token for path, token in chain):
        raise OSError("publication source directory changed")


def _read_regular(root: Path, relative: tuple[str, ...], maximum: int) -> bytes:
    chain = _directory_chain(root, relative[:-1])
    path = root.joinpath(*relative)
    before = path.lstat()
    baseline = _file_snapshot(before, maximum)
    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        opened = _file_snapshot(os.fstat(descriptor), maximum)
        if opened[:-1] != baseline[:-1]:
            raise ValueError("publication source changed before read")
        chunks = bytearray()
        while len(chunks) <= maximum:
            chunk = os.read(descriptor, min(_CHUNK_BYTES, maximum + 1 - len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
        if _file_snapshot(os.fstat(descriptor), maximum) != opened:
            raise ValueError("publication source changed during read")
    finally:
        os.close(descriptor)
    if _file_snapshot(path.lstat(), maximum) != baseline:
        raise ValueError("publication source changed after read")
    _check_chain(chain)
    if len(chunks) != before.st_size or len(chunks) > maximum:
        raise ValueError("publication source byte count changed")
    return bytes(chunks)


def _verified_record(repository: object, run: TrainingRunRef) -> DockerRunMutationRecordV1:
    record = repository.load_docker_run_mutation(run.project_ref, run.run_id)
    if (
        type(record) is not DockerRunMutationRecordV1
        or record.phase is not DockerRunPhaseV1.ARTIFACTS_VERIFIED
    ):
        raise RunOperationError(RunOperationCode.ARTIFACTS_UNVERIFIED)
    return record


def _artifacts(record: DockerRunMutationRecordV1) -> tuple[VerifiedArtifact, ...]:
    return tuple(
        VerifiedArtifact(item.role, item.sha256, item.byte_count)
        for item in record.verified_artifacts
    )


class _DockerArtifactStreamV1:
    def __init__(self, *, repository, run, record, artifact, root, relative, maximum_bytes):
        self.run = TrainingRunRef.from_dict(run.to_dict())
        self.artifact = VerifiedArtifact.from_dict(artifact.to_dict())
        self.maximum_bytes = maximum_bytes
        self._repository = repository
        self._record = record
        self._root = root
        self._relative = relative
        self._claimed = False

    def iter_bytes(self) -> Iterator[bytes]:
        if self._claimed:
            raise ValueError("Docker artifact stream is one-shot")
        self._claimed = True
        repository = self._repository
        baseline = self._record
        run = self.run
        artifact = self.artifact
        root = self._root
        relative = self._relative
        path = root.joinpath(*relative)
        maximum = self.maximum_bytes

        def iterator() -> Iterator[bytes]:
            if _verified_record(repository, run) != baseline:
                raise RunOperationError(RunOperationCode.STATE_CONFLICT)
            chain = _directory_chain(root, relative[:-1])
            before = path.lstat()
            token = _file_snapshot(before, maximum)
            descriptor = os.open(
                path,
                os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0),
            )
            digest = hashlib.sha256()
            count = 0
            try:
                opened = _file_snapshot(os.fstat(descriptor), maximum)
                if opened[:-1] != token[:-1]:
                    raise RunOperationError(RunOperationCode.ARTIFACT_CONTENT_INVALID)
                while True:
                    chunk = os.read(descriptor, min(_CHUNK_BYTES, maximum + 1 - count))
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > maximum:
                        raise RunOperationError(RunOperationCode.ARTIFACT_LIMIT_EXCEEDED)
                    digest.update(chunk)
                    yield bytes(chunk)
                if _file_snapshot(os.fstat(descriptor), maximum) != opened:
                    raise RunOperationError(RunOperationCode.ARTIFACT_CONTENT_INVALID)
            finally:
                os.close(descriptor)
            if (
                _file_snapshot(path.lstat(), maximum) != token
                or count != artifact.size_bytes
                or digest.hexdigest() != artifact.sha256
            ):
                raise RunOperationError(RunOperationCode.ARTIFACT_CONTENT_INVALID)
            _check_chain(chain)
            if _verified_record(repository, run) != baseline:
                raise RunOperationError(RunOperationCode.STATE_CONFLICT)

        return iterator()


class _DockerRunsOperationsV1:
    def __init__(self, *, repository, request, record, clock):
        self._repository = repository
        self._record = record
        self._artifact_root = Path(request.staging.artifact_root)
        self._clock = clock
        self._run = TrainingRunRef(request.run_id, request.project_ref)

    def _require(self, run):
        if type(run) is not TrainingRunRef or run != self._run:
            raise RunOperationError(RunOperationCode.RUN_MISSING)
        record = _verified_record(self._repository, self._run)
        if record != self._record:
            raise RunOperationError(RunOperationCode.STATE_CONFLICT)
        return record

    def show(self, run):
        record = self._require(run)
        return RunOutcome(
            "synaptic-run-outcome/v1", self._run, TrainingRunState.SUCCEEDED,
            _artifacts(record), None,
        )

    outcome = show

    def reverify(self, run):
        first = self._require(run)
        for descriptor in first.verified_artifacts:
            stream = self.artifacts(RunArtifactRequest(
                self._run, descriptor.role, max(1, descriptor.byte_count)
            ))
            for _chunk in stream.iter_bytes():
                pass
        if self._require(run) != first:
            raise RunOperationError(RunOperationCode.STATE_CONFLICT)
        return RunVerification(self._run, True, self._clock())

    verify = reverify

    def artifacts(self, request):
        if type(request) is not RunArtifactRequest:
            raise TypeError("exact artifact request is required")
        record = self._require(request.run)
        matches = tuple(item for item in record.verified_artifacts if item.role == request.role)
        if len(matches) != 1:
            raise RunOperationError(RunOperationCode.ARTIFACT_ROLE_MISSING)
        descriptor = matches[0]
        if descriptor.byte_count > request.maximum_bytes:
            raise RunOperationError(RunOperationCode.ARTIFACT_LIMIT_EXCEEDED)
        root = self._artifact_root / "artifacts"
        relative = tuple(Path(descriptor.relative_path).parts)
        return _DockerArtifactStreamV1(
            repository=self._repository, run=self._run, record=record,
            artifact=VerifiedArtifact(descriptor.role, descriptor.sha256, descriptor.byte_count),
            root=root, relative=relative, maximum_bytes=request.maximum_bytes,
        )

    def list(self, _request: RunListRequest):
        raise RunOperationError(RunOperationCode.CAPABILITY_UNAVAILABLE)

    def logs(self, _request):
        raise RunOperationError(RunOperationCode.CAPABILITY_UNAVAILABLE)

    def cancel(self, _run, _reason):
        raise RunOperationError(RunOperationCode.CAPABILITY_UNAVAILABLE)

    def reconcile(self, _run):
        raise RunOperationError(RunOperationCode.CAPABILITY_UNAVAILABLE)


@dataclass(slots=True)
class _DockerPublicationPinsV1:
    token: object
    facade: HostPublicationFacadeV1
    runs: RunsAPI
    repository: object
    request: DockerPreparedRunRequestV1
    request_binding: tuple[object, ...]
    record: DockerRunMutationRecordV1
    configuration: PublicationConfigurationDocumentsV1
    run: TrainingRunRef
    destination_ref: str
    publish_callback: object
    close_callback: object
    closed: bool = False


def _composition_pin_accessors():
    registry = WeakKeyDictionary()
    lock = RLock()
    token = object()

    def register(owner: object, pins: _DockerPublicationPinsV1, proof: object) -> None:
        if proof is not token or type(pins) is not _DockerPublicationPinsV1:
            raise ValueError("Docker publication composition is invalid")
        with lock:
            registry[owner] = pins

    def get(owner: object) -> object | None:
        with lock:
            return registry.get(owner)

    return token, register, get


_COMPOSITION_TOKEN, _register_composition, _get_composition = (
    _composition_pin_accessors()
)


def _request_binding(
    request: DockerPreparedRunRequestV1,
) -> tuple[object, ...]:
    return (
        request.project_ref,
        request.run_id,
        request.preparation.preparation_digest,
        request.preparation.destination_ref,
        request.preparation.destination_declaration_digest,
        request.preparation.stage.staged_storage_configuration_digest,
        request.prepared_plan.digest,
        str(request.staging.source_root),
        str(request.staging.artifact_root),
        request.staging.worker_bundle.projection_sha256,
    )


def _configuration_for_request(
    request: DockerPreparedRunRequestV1,
) -> PublicationConfigurationDocumentsV1:
    source = request.staging.source_root
    return PublicationConfigurationDocumentsV1(
        _read_regular(
            source, ("project", "training", "artifacts.json"), _MAX_CONFIG_BYTES
        ),
        _read_regular(source, ("control", "storage.json"), 65_536),
    )


def _validate_configuration_binding(
    request: DockerPreparedRunRequestV1,
    configuration: PublicationConfigurationDocumentsV1,
) -> None:
    if (
        type(configuration) is not PublicationConfigurationDocumentsV1
        or configuration.storage_digest
        != request.preparation.stage.staged_storage_configuration_digest
    ):
        raise ValueError("staged storage configuration differs from preparation")
    config = parse_artifact_destination_config_v1(configuration.destination_bytes)
    matches = tuple(
        item for item in config.destinations
        if item.destination_ref == request.preparation.destination_ref
    )
    if len(matches) != 1 or artifact_destination_declaration_digest_v1(
        matches[0]
    ) != request.preparation.destination_declaration_digest:
        raise ValueError("staged destination declaration differs from preparation")


class DockerPublicationCompositionV1:
    __slots__ = ("__weakref__",)

    def __new__(cls, *_args, **_kwargs):
        raise TypeError("Docker publication compositions are factory-issued")

    def publish(
        self, *, request: DockerPreparedRunRequestV1,
        record: DockerRunMutationRecordV1,
    ) -> PublicationResult:
        pins = _composition_pins(self)
        if pins.closed:
            raise ValueError("Docker publication composition is closed")
        if (
            type(request) is not DockerPreparedRunRequestV1
            or type(record) is not DockerRunMutationRecordV1
        ):
            raise ValueError("Docker publication composition differs from the run")
        if _request_binding(request) != pins.request_binding:
            raise ValueError("Docker publication composition differs from the run")
        fresh = _verified_record(pins.repository, pins.run)
        current_configuration = _configuration_for_request(request)
        if (
            request != pins.request
            or record != pins.record
            or fresh != pins.record
            or pins.record.phase is not DockerRunPhaseV1.ARTIFACTS_VERIFIED
            or pins.run != TrainingRunRef(record.run_id, record.project_ref)
            or pins.destination_ref != request.preparation.destination_ref
            or current_configuration != pins.configuration
        ):
            raise ValueError("Docker publication composition differs from the run")
        _validate_configuration_binding(request, current_configuration)
        return pins.publish_callback(
            PublicationRequest(pins.run, pins.destination_ref)
        )

    def close(self) -> None:
        pins = _composition_pins(self)
        if pins.closed:
            pins.close_callback()
            return
        pins.closed = True
        pins.close_callback()


def _composition_pins(
    value: DockerPublicationCompositionV1,
) -> _DockerPublicationPinsV1:
    pins = _get_composition(value)
    if (
        type(value) is not DockerPublicationCompositionV1
        or type(pins) is not _DockerPublicationPinsV1
        or pins.token is not _COMPOSITION_TOKEN
        or type(pins.facade) is not HostPublicationFacadeV1
        or type(pins.runs) is not RunsAPI
        or type(pins.request) is not DockerPreparedRunRequestV1
        or type(pins.request_binding) is not tuple
        or type(pins.record) is not DockerRunMutationRecordV1
        or type(pins.configuration) is not PublicationConfigurationDocumentsV1
        or pins.publish_callback != pins.facade.publish
        or pins.close_callback != pins.facade.close
    ):
        raise ValueError("Docker publication composition is invalid")
    return pins


def compose_docker_publication_v1(
    *, context: ProjectContext, repository: object,
    request: DockerPreparedRunRequestV1, clock: Callable[[], str],
    spool_root_ref: str,
    registration_builders: tuple[FunctionType, ...],
) -> DockerPublicationCompositionV1:
    if type(request) is not DockerPreparedRunRequestV1:
        raise TypeError("exact prepared Docker request is required")
    run = TrainingRunRef(request.run_id, request.project_ref)
    record = _verified_record(repository, run)
    if record.preparation_digest != request.preparation.preparation_digest:
        raise ValueError("Docker publication preparation differs from the run")
    configuration = _configuration_for_request(request)
    _validate_configuration_binding(request, configuration)
    operations = _DockerRunsOperationsV1(
        repository=repository, request=request, record=record, clock=clock
    )
    runs = RunsAPI(operations)
    facade = compose_host_publication_v1(
        context=context, runs=runs, configuration=configuration,
        spool_root_ref=spool_root_ref, clock=clock,
        registration_builders=registration_builders,
    )
    try:
        changed = (
            _configuration_for_request(request) != configuration
            or _verified_record(repository, run) != record
        )
    except (KeyboardInterrupt, SystemExit):
        try:
            facade.close()
        except BaseException:
            pass
        raise
    except BaseException:
        try:
            facade.close()
        except BaseException:
            pass
        raise ValueError(
            "Docker publication inputs changed during composition"
        ) from None
    if changed:
        facade.close()
        raise ValueError("Docker publication inputs changed during composition")
    value = object.__new__(DockerPublicationCompositionV1)
    _register_composition(
        value,
        _DockerPublicationPinsV1(
            _COMPOSITION_TOKEN, facade, runs, repository, request,
            _request_binding(request), record,
            configuration, run, request.preparation.destination_ref,
            facade.publish, facade.close,
        ),
        _COMPOSITION_TOKEN,
    )
    return value


__all__ = ["DockerPublicationCompositionV1", "compose_docker_publication_v1"]
