"""Host-owned composition and lifecycle for artifact publication."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from threading import Condition, Lock, get_ident
from types import FunctionType
from typing import Callable

from synaptic_tuner.api.v1 import (
    DestinationPage,
    ProjectContext,
    PublicationPage,
    PublicationRef,
    PublicationRequest,
    PublicationResult,
    PublicationVerification,
    RunsAPI,
)
from synaptic_tuner.api.v1.publication import PublicationOperationsV1

from .artifact_destinations import (
    DestinationAdapterRegistrationV1,
    DestinationAdapterInstallationV1,
    ImmutableArtifactDestinationRegistryV1,
    parse_artifact_destination_config_v1,
)
from .artifact_spool import (
    LocalArtifactSpoolCleanupStatusV1,
    LocalArtifactSpoolV1,
    acquire_local_artifact_spool_v1,
)
from .local_io_v1.config import StorageRegistryV1
from .local_io_v1.filesystem import LocalFilesystemV1
from .local_io_v1.posix import PosixRetainedDirfdPortV1
from .publication_authority import create_publication_evidence_v1
from .publication_store import SqlitePublicationStoreV1
from .verified_artifact_source import AuthenticatedVerifiedArtifactSourceV1


_PERMIT_DOMAIN = b"synaptic-host-publication-storage-permit/v1\0"
_MAX_DESTINATION_CONFIG_BYTES = 1_048_576
_MAX_STORAGE_CONFIG_BYTES = 65_536
_DOCUMENT_CHUNK_BYTES = 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_OPEN = "OPEN"
_CLOSING = "CLOSING"
_CLOSED = "CLOSED"


def _failed(message: str) -> RuntimeError:
    return RuntimeError(message)


def _host_context(value: ProjectContext) -> ProjectContext:
    if type(value) is not ProjectContext or value.mode != "host":
        raise ValueError("exact Host project context is required")
    return value


def _document_snapshot(value: os.stat_result, maximum: int) -> tuple[object, ...]:
    attributes = getattr(value, "st_file_attributes", 0)
    if (
        not stat.S_ISREG(value.st_mode)
        or stat.S_ISLNK(value.st_mode)
        or attributes & _REPARSE
        or not 0 < value.st_size <= maximum
    ):
        raise ValueError("publication configuration document is invalid")
    return (
        value.st_dev,
        value.st_ino,
        stat.S_IFMT(value.st_mode),
        value.st_size,
        bool(attributes & _REPARSE),
        getattr(value, "st_mtime_ns", None),
        getattr(value, "st_ctime_ns", None),
    )


def _read_configuration_document(path: Path, maximum: int) -> bytes:
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError("absolute publication configuration path is required")
    try:
        before = path.lstat()
        baseline = _document_snapshot(before, maximum)
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            opened = _document_snapshot(os.fstat(descriptor), maximum)
            if opened[:-1] != baseline[:-1]:
                raise ValueError("publication configuration changed before read")
            chunks = bytearray()
            while len(chunks) <= maximum:
                chunk = os.read(
                    descriptor,
                    min(_DOCUMENT_CHUNK_BYTES, maximum + 1 - len(chunks)),
                )
                if not chunk:
                    break
                chunks.extend(chunk)
            if _document_snapshot(os.fstat(descriptor), maximum) != opened:
                raise ValueError("publication configuration changed during read")
        finally:
            os.close(descriptor)
        if _document_snapshot(path.lstat(), maximum) != baseline:
            raise ValueError("publication configuration changed after read")
        if len(chunks) != before.st_size or len(chunks) > maximum:
            raise ValueError("publication configuration byte count changed")
        return bytes(chunks)
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException:
        raise ValueError("publication configuration document is invalid") from None


@dataclass(frozen=True, slots=True)
class PublicationConfigurationDocumentsV1:
    destination_bytes: bytes
    storage_bytes: bytes
    destination_digest: str = ""
    storage_digest: str = ""

    def __post_init__(self) -> None:
        if (
            type(self.destination_bytes) is not bytes
            or not 0 < len(self.destination_bytes) <= _MAX_DESTINATION_CONFIG_BYTES
            or type(self.storage_bytes) is not bytes
            or not 0 < len(self.storage_bytes) <= _MAX_STORAGE_CONFIG_BYTES
            or self.destination_digest not in {
                "", hashlib.sha256(self.destination_bytes).hexdigest()
            }
            or self.storage_digest not in {
                "", hashlib.sha256(self.storage_bytes).hexdigest()
            }
        ):
            raise ValueError("publication configuration documents are invalid")
        object.__setattr__(
            self, "destination_digest",
            hashlib.sha256(self.destination_bytes).hexdigest(),
        )
        object.__setattr__(
            self, "storage_digest", hashlib.sha256(self.storage_bytes).hexdigest()
        )

    @classmethod
    def from_paths(
        cls, *, destination_path: Path, storage_path: Path,
    ) -> "PublicationConfigurationDocumentsV1":
        return cls(
            _read_configuration_document(
                destination_path, _MAX_DESTINATION_CONFIG_BYTES
            ),
            _read_configuration_document(storage_path, _MAX_STORAGE_CONFIG_BYTES),
        )


def _permit_proof_digest(
    context: ProjectContext, storage_config_bytes: bytes,
) -> str:
    identity = json.dumps(
        {
            "engine_root": str(context.engine_root),
            "manifest_path": (
                None if context.manifest_path is None else str(context.manifest_path)
            ),
            "mode": context.mode,
            "path_mode": context.path_mode,
            "project_root": str(context.project_root),
            "state_root": str(context.state_root),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(_PERMIT_DOMAIN)
    digest.update(len(identity).to_bytes(8, "big"))
    digest.update(identity)
    digest.update(len(storage_config_bytes).to_bytes(8, "big"))
    digest.update(storage_config_bytes)
    return digest.hexdigest()


def _installation_type():
    return DestinationAdapterInstallationV1


def _spool_type():
    return LocalArtifactSpoolV1


def _cleanup_installation(value: object) -> bool:
    try:
        result = value.cleanup_owned()
        return type(result) is bool and result is True
    except BaseException:
        return False


def _cleanup_spool(value: object) -> bool:
    try:
        result = value.cleanup_owned()
        return (
            type(result.status) is LocalArtifactSpoolCleanupStatusV1
            and result.status is LocalArtifactSpoolCleanupStatusV1.CLEANED
        )
    except BaseException:
        return False


class HostPublicationFacadeV1:
    """Five-method publication facade with a terminal owned-resource lifecycle."""

    __slots__ = (
        "__operations",
        "__store",
        "__installations",
        "__spool",
        "__condition",
        "__state",
        "__active_calls",
        "__thread_depths",
        "__cleanup_claimed",
        "__cleanup_owner_thread_id",
        "__cleanup_failed",
    )

    def __init__(
        self,
        operations: PublicationOperationsV1,
        store: SqlitePublicationStoreV1,
        installations: tuple[DestinationAdapterInstallationV1, ...],
        spool: object,
    ) -> None:
        if type(operations) is not PublicationOperationsV1:
            raise TypeError("exact publication operations are required")
        if type(store) is not SqlitePublicationStoreV1:
            raise TypeError("exact publication store is required")
        installation_type = _installation_type()
        if (
            type(installations) is not tuple
            or any(type(item) is not installation_type for item in installations)
        ):
            raise TypeError("exact installation tuple is required")
        if type(spool) is not _spool_type():
            raise TypeError("exact publication spool is required")
        self.__operations = operations
        self.__store = store
        self.__installations = installations
        self.__spool = spool
        self.__condition = Condition(Lock())
        self.__state = _OPEN
        self.__active_calls = 0
        self.__thread_depths: dict[int, int] = {}
        self.__cleanup_claimed = False
        self.__cleanup_owner_thread_id: int | None = None
        self.__cleanup_failed: bool | None = None

    def _enter(self) -> None:
        thread_id = get_ident()
        with self.__condition:
            if self.__state != _OPEN:
                raise _failed("host publication facade is closed")
            self.__active_calls += 1
            self.__thread_depths[thread_id] = (
                self.__thread_depths.get(thread_id, 0) + 1
            )

    def _leave(self) -> None:
        thread_id = get_ident()
        cleanup_owner = False
        with self.__condition:
            depth = self.__thread_depths.get(thread_id, 0)
            if depth <= 0 or self.__active_calls <= 0:
                raise RuntimeError("host publication lease state is invalid")
            if depth == 1:
                del self.__thread_depths[thread_id]
            else:
                self.__thread_depths[thread_id] = depth - 1
            self.__active_calls -= 1
            if self.__active_calls == 0:
                self.__condition.notify_all()
                if self.__state == _CLOSING and not self.__cleanup_claimed:
                    self.__cleanup_claimed = True
                    self.__cleanup_owner_thread_id = thread_id
                    cleanup_owner = True
        if cleanup_owner:
            self._finish_cleanup()

    def _call(self, callback: Callable[..., object], *args: object):
        self._enter()
        try:
            return callback(*args)
        finally:
            self._leave()

    def destinations(self) -> DestinationPage:
        return self._call(self.__operations.destinations)

    def publications(self, destination_ref: str) -> PublicationPage:
        return self._call(self.__operations.publications, destination_ref)

    def publish(self, request: PublicationRequest) -> PublicationResult:
        return self._call(self.__operations.publish, request)

    def verify(self, publication: PublicationRef) -> PublicationVerification:
        return self._call(self.__operations.verify, publication)

    def _finish_cleanup(self) -> bool:
        with self.__condition:
            if (
                not self.__cleanup_claimed
                or self.__cleanup_owner_thread_id != get_ident()
                or self.__state != _CLOSING
            ):
                raise RuntimeError("host publication cleanup ownership is invalid")
        failed = False
        try:
            try:
                self.__store.close()
            except BaseException:
                failed = True
            for installation in reversed(self.__installations):
                if not _cleanup_installation(installation):
                    failed = True
            if not _cleanup_spool(self.__spool):
                failed = True
        finally:
            with self.__condition:
                self.__cleanup_failed = failed
                self.__cleanup_owner_thread_id = None
                self.__state = _CLOSED
                self.__condition.notify_all()
        return failed

    def close(self) -> None:
        thread_id = get_ident()
        cleanup_owner = False
        failed = False
        with self.__condition:
            if self.__state == _OPEN:
                self.__state = _CLOSING
            if self.__state == _CLOSED:
                failed = bool(self.__cleanup_failed)
            elif (
                self.__cleanup_claimed
                and self.__cleanup_owner_thread_id == thread_id
            ):
                return
            elif self.__thread_depths.get(thread_id, 0) > 0:
                return
            else:
                while self.__state != _CLOSED:
                    if self.__active_calls == 0 and not self.__cleanup_claimed:
                        self.__cleanup_claimed = True
                        self.__cleanup_owner_thread_id = thread_id
                        cleanup_owner = True
                        break
                    self.__condition.wait()
                if self.__state == _CLOSED:
                    failed = bool(self.__cleanup_failed)
        if cleanup_owner:
            failed = self._finish_cleanup()
        if failed:
            raise _failed("host publication cleanup failed")


def _rollback(
    store: SqlitePublicationStoreV1 | None,
    installations: tuple[DestinationAdapterInstallationV1, ...],
    spool: object | None,
) -> bool:
    failed = False
    if store is not None:
        try:
            store.close()
        except BaseException:
            failed = True
    for installation in reversed(installations):
        if not _cleanup_installation(installation):
            failed = True
    if spool is not None and not _cleanup_spool(spool):
        failed = True
    return failed


def compose_host_publication_v1(
    *,
    context: ProjectContext,
    runs: RunsAPI,
    configuration: PublicationConfigurationDocumentsV1,
    spool_root_ref: str,
    clock: Callable[[], str],
    registration_builders: tuple[FunctionType, ...],
) -> HostPublicationFacadeV1:
    """Compose configured Host publication without exporting owned capabilities."""

    context = _host_context(context)
    if type(configuration) is not PublicationConfigurationDocumentsV1:
        raise TypeError("exact publication configuration documents are required")
    if type(runs) is not RunsAPI:
        raise TypeError("exact RunsAPI is required")
    if type(spool_root_ref) is not str or not spool_root_ref:
        raise ValueError("exact spool root reference is required")
    if not callable(clock):
        raise TypeError("clock must be callable")
    if (
        type(registration_builders) is not tuple
        or not registration_builders
        or any(type(builder) is not FunctionType for builder in registration_builders)
    ):
        raise TypeError("exact registration builder functions are required")

    spool = None
    store = None
    installations: list[DestinationAdapterInstallationV1] = []
    try:
        destination_config = parse_artifact_destination_config_v1(
            configuration.destination_bytes
        )
        storage = StorageRegistryV1.from_bytes(
            configuration.storage_bytes, project_root=context.project_root
        )
        evidence = create_publication_evidence_v1(context)
        filesystem = LocalFilesystemV1(PosixRetainedDirfdPortV1(), storage)
        permit_proof_digest = _permit_proof_digest(
            context, configuration.storage_bytes
        )
        storage.issue_root_permit(
            spool_root_ref,
            authority_ref=evidence.verifier.authority_ref,
            key_ref=evidence.verifier.key_ref,
            proof_digest=permit_proof_digest,
        )
        spool = acquire_local_artifact_spool_v1(
            filesystem, storage.resolve(spool_root_ref)
        )
        installation_type = _installation_type()
        for builder in registration_builders:
            installation = builder(
                filesystem=filesystem,
                storage=storage,
                spool=spool,
                evidence=evidence,
                permit_authority_ref=evidence.verifier.authority_ref,
                permit_key_ref=evidence.verifier.key_ref,
                permit_proof_digest=permit_proof_digest,
            )
            if type(installation) is not installation_type:
                raise TypeError("registration builder returned an invalid installation")
            installations.append(installation)
        registrations = tuple(
            sorted(
                (item.registration for item in installations),
                key=lambda item: item.adapter_ref,
            )
        )
        if any(type(item) is not DestinationAdapterRegistrationV1 for item in registrations):
            raise TypeError("installation returned an invalid registration")
        registry = ImmutableArtifactDestinationRegistryV1(
            config=destination_config,
            registrations=registrations,
            issuer=evidence.destinations,
            verifier=evidence.verifier,
        )
        sources = AuthenticatedVerifiedArtifactSourceV1(
            runs=runs,
            issuer=evidence.verified_sources,
            verifier=evidence.verifier,
        )
        store = SqlitePublicationStoreV1.from_context(context)
        operations = PublicationOperationsV1(
            store=store,
            destinations=registry,
            sources=sources,
            spool=spool,
            authority=evidence.verifier,
            clock=clock,
        )
        return HostPublicationFacadeV1(
            operations, store, tuple(installations), spool
        )
    except (KeyboardInterrupt, SystemExit):
        _rollback(store, tuple(installations), spool)
        raise
    except BaseException:
        _rollback(store, tuple(installations), spool)
        raise _failed("host publication composition failed") from None


__all__ = [
    "HostPublicationFacadeV1",
    "PublicationConfigurationDocumentsV1",
    "compose_host_publication_v1",
]
