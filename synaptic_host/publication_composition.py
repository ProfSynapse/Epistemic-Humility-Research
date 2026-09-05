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
from .local_io_v1.filesystem import LocalFilesystemV1, PosixFilesystemPortV1
from .publication_authority import create_publication_evidence_v1
from .publication_store import SqlitePublicationStoreV1
from .security import FileHmacAuthenticator
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


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


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


def _ensure_declared_private_roots(
    storage: StorageRegistryV1, context: ProjectContext,
) -> None:
    """Create the declared creatable storage roots that live under `.synaptic`.

    Section 27.3 of `docs/architecture/prepared-path-alpine-diagnostic.md`.  The
    storage document declares `read_create` roots below the Host's private
    storage root, but nothing on the publish path ever created them, so the
    first `retain_single_root_authority` on an absent directory refused with
    `LOCAL_IO_ROOT_CHANGED` (B-18).  This creates exactly the absent ones.

    Two deliberate limits.  It never creates `.synaptic` itself: the evidence
    authority mints that chain one statement earlier through the B-11 repair,
    and a missing parent here means the caller ran out of order, so it is
    reported rather than papered over.  And it never repairs, validates, or
    narrows a root that already exists -- an existing directory is skipped
    whatever its mode or ACL, which leaves B-11 the sole owner of repair.

    Roots outside `.synaptic` (the project's training inputs and outputs) stay
    the operator's to create; only the private subtree is ours.
    """
    private_root = _lexical_absolute(context.project_root / ".synaptic")
    absent: list[Path] = []
    # Declared roots, not bindings: `list_roots` refuses until every root holds
    # a permit, and this necessarily runs before the first one is issued.
    for declared in storage.list_declared_roots():
        if not declared.access.creatable:
            continue
        resolved = _lexical_absolute(declared.absolute_root)
        if resolved == private_root or not _within(resolved, private_root):
            continue
        if resolved.exists():
            continue
        absent.append(resolved)
    if not absent:
        return
    if not private_root.is_dir():
        raise _failed(
            "host publication private storage root is missing: " + str(private_root)
        )
    for root in sorted(absent):
        _create_private_chain(root, private_root)


def _within(path: Path, ancestor: Path) -> bool:
    """Report whether `path` lies inside `ancestor`, lexically.

    The `os.path.commonpath` shape is the one `security.py` uses to confine the
    Docker control key below the private storage root.
    """
    try:
        return os.path.commonpath((str(path), str(ancestor))) == str(ancestor)
    except ValueError:
        return False


def _create_private_chain(root: Path, private_root: Path) -> None:
    """Create `root` itself, and only `root`.

    Y1 (section 27.12).  The `19c11400` amendment withdrew step 3's "parents
    first", leaving step 3 requiring only the root, so the ancestor walk is
    gone.  The one future it could have fired in is a future 27.3 already
    refused: it would create an intermediate directory no declaration names,
    carrying a private DACL, that nothing retains and nothing validates.  A
    declared root nested below `.synaptic` whose parent is absent is a gap in
    the declaring document, so it is reported here by a named error -- the shape
    the caller uses for an absent `.synaptic` -- and never silently completed.

    Creation goes through the same primitive the private storage chain uses, so
    a root created here carries the private mode (POSIX `0o700`) or the
    protected DACL (Windows) from birth.
    """
    parent = root.parent
    if parent != private_root and not parent.is_dir():
        raise _failed(
            "host publication private storage root parent is missing: "
            + str(parent)
        )
    FileHmacAuthenticator._create_private_directory(root)


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


def _local_filesystem_port_v1() -> PosixFilesystemPortV1:
    """Build the retained-handle port for the running platform.

    Two branches, one real port each. This is not a compatibility layer: it
    adds no re-export, no dual signature, no deprecated wrapper and no
    degradation path, and neither branch can serve the other platform. On an
    unsupported platform the constructed port raises CAPABILITY_UNAVAILABLE,
    which is the behaviour before this closure. The pattern mirrors the
    os.name branches already used in security.py.

    The imports are branch-local on purpose: a POSIX process must never import
    the ctypes.WinDLL bindings and a Windows process must never import fcntl.
    """
    if os.name == "nt":
        from .local_io_v1.windows import WindowsRetainedHandlePortV1

        return WindowsRetainedHandlePortV1()
    from .local_io_v1.posix import PosixRetainedDirfdPortV1

    return PosixRetainedDirfdPortV1()


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
        _ensure_declared_private_roots(storage, context)
        filesystem = LocalFilesystemV1(_local_filesystem_port_v1(), storage)
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
    except BaseException as error:
        # B-18 (section 27.4, site 1).  The rollback runs first, exactly as
        # before; only the cause changes.  `from error` keeps the deepest
        # in-package frame reachable for the 22.14 renderer, which is what run
        # 13's cut 6 needed and did not have.
        _rollback(store, tuple(installations), spool)
        raise _failed("host publication composition failed") from error


__all__ = [
    "HostPublicationFacadeV1",
    "PublicationConfigurationDocumentsV1",
    "compose_host_publication_v1",
]
