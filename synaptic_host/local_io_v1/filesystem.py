"""Retained-handle POSIX local I/O orchestration.

There is deliberately no concrete operating-system adapter here.  The host
injects a narrowly typed POSIX port; native Windows is metadata-only and fails
before the injected port can be touched.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import stat
import sys
from contextlib import contextmanager
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from threading import Lock, RLock
from typing import Protocol

from .model import (
    CreateJournalRecordV1,
    CreatePhaseV1,
    LocalArtifactBindingV1,
    BorrowedDirectoryV1,
    BorrowedFileV1,
    BorrowedHardlinkPairV1,
    BorrowPurposeV1,
    LocalFilesystemCapabilityV1,
    LocalCreateAuthorityV1,
    LocalDestinationBindingV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootAuthorityV1,
    LocalSingleRootAuthorityV1,
    LocalSingleRootAdmissionV1,
    LocalRootBindingV1,
    LocalSourceBindingV1,
    MAX_BORROWED_HARDLINK_PAIR_BYTES,
    JournalPublishResultV1,
    JournalPublishStatusV1,
    JournalSnapshotStatusV1,
    JournalSnapshotV1,
    CapabilityStatusV1,
    RecoveryResultV1,
    RetainedDirectoryAdmissionV1,
    RecoveryStatusV1,
    RetainedDirectoryV1,
    RetainedRootBorrowRequestV1,
    RetainedRootBorrowV1,
    RootAccessV1,
    SingleRootPurposeV1,
    RootPermitAuthenticatorV1,
    canonical_relative_components_v1,
    checked_handle,
    checked_ref,
    checked_sha256,
    checked_size,
    digest_v1,
    root_authority_digest_v1,
    single_root_authority_digest_v1,
    validate_recovery_result_v1,
)


MAX_CHUNK_BYTES = 1_048_576
MAX_FILE_BYTES = 1 << 40
MAX_DIRECTORY_ENTRIES = 4096
MAX_JOURNAL_RECORDS = 4
_POSIX_PLATFORMS = ("linux", "darwin", "freebsd", "openbsd", "netbsd")


@dataclass(frozen=True, slots=True)
class OpenFileV1:
    handle_ref: str
    identity: LocalFileIdentityV1

    def __post_init__(self) -> None:
        checked_handle(self.handle_ref)
        if type(self.identity) is not LocalFileIdentityV1:
            raise LocalIOErrorV1(LocalIOCodeV1.IO_FAILED)


def _identity_issuance_v1(identity: LocalFileIdentityV1) -> tuple[int, ...]:
    return (
        identity.device,
        identity.inode,
        identity.mode,
        identity.nlink,
        identity.changed_ns,
        identity.modified_ns,
        identity.size,
    )


@dataclass(frozen=True, slots=True)
class _BorrowIssuanceV1:
    schema_version: str
    request_schema_version: str
    borrow_ref: str
    request_digest: str
    root_authority_digest: str
    authority_ref: str
    data_root_ref: str
    data_binding_digest: str
    purpose: str
    access: str
    borrow_digest: str

    def seal(self) -> str:
        return digest_v1({
            "access": self.access,
            "authority_ref": self.authority_ref,
            "borrow_digest": self.borrow_digest,
            "borrow_ref": self.borrow_ref,
            "data_binding_digest": self.data_binding_digest,
            "data_root_ref": self.data_root_ref,
            "purpose": self.purpose,
            "request_digest": self.request_digest,
            "request_schema_version": self.request_schema_version,
            "root_authority_digest": self.root_authority_digest,
            "schema_version": self.schema_version,
        })


@dataclass(frozen=True, slots=True)
class _DirectoryIssuanceV1:
    schema_version: str
    borrow_ref: str
    borrow_digest: str
    directory_ref: str
    path_components: tuple[str, ...]
    owns_handle: bool
    identity: tuple[int, ...]
    directory_digest: str

    def seal(self) -> str:
        return digest_v1({
            "borrow_digest": self.borrow_digest,
            "borrow_ref": self.borrow_ref,
            "directory_digest": self.directory_digest,
            "directory_ref": self.directory_ref,
            "identity": list(self.identity),
            "owns_handle": self.owns_handle,
            "path_components": list(self.path_components),
            "schema_version": self.schema_version,
        })


@dataclass(frozen=True, slots=True)
class _FileIssuanceV1:
    schema_version: str
    borrow_ref: str
    borrow_digest: str
    file_ref: str
    parent_path: tuple[str, ...]
    component: str
    path_components: tuple[str, ...]
    readable: bool
    writable: bool
    identity: tuple[int, ...]
    file_digest: str

    def seal(self) -> str:
        return digest_v1({
            "borrow_digest": self.borrow_digest,
            "borrow_ref": self.borrow_ref,
            "component": self.component,
            "file_digest": self.file_digest,
            "file_ref": self.file_ref,
            "identity": list(self.identity),
            "parent_path": list(self.parent_path),
            "path_components": list(self.path_components),
            "readable": self.readable,
            "schema_version": self.schema_version,
            "writable": self.writable,
        })


@dataclass(frozen=True, slots=True)
class _HardlinkPairIssuanceV1:
    schema_version: str
    borrow_ref: str
    borrow_digest: str
    pair_ref: str
    parent_ref: str
    parent_components: tuple[str, ...]
    first_component: str
    second_component: str
    identity: tuple[int, ...]
    pair_digest: str

    def seal(self) -> str:
        return digest_v1({
            "borrow_digest": self.borrow_digest,
            "borrow_ref": self.borrow_ref,
            "first_component": self.first_component,
            "identity": list(self.identity),
            "pair_digest": self.pair_digest,
            "pair_ref": self.pair_ref,
            "parent_components": list(self.parent_components),
            "parent_ref": self.parent_ref,
            "schema_version": self.schema_version,
            "second_component": self.second_component,
        })


@dataclass(frozen=True, slots=True)
class _AdmittedDirectoryV1:
    issued_ref: str
    object_id: int
    borrow_ref: str
    path_components: tuple[str, ...]
    owns_handle: bool
    identity: tuple[int, ...]
    raw: RetainedDirectoryV1


@dataclass(frozen=True, slots=True)
class _AdmittedFileV1:
    issued_ref: str
    object_id: int
    borrow_ref: str
    parent_path: tuple[str, ...]
    component: str
    readable: bool
    writable: bool
    identity: tuple[int, ...]
    raw: OpenFileV1


@dataclass(frozen=True, slots=True)
class _AdmittedEffectV1:
    borrow_ref: str
    purpose: str
    access: str
    absolute_root: str
    root_identity: tuple[int, ...]
    directories: tuple[_AdmittedDirectoryV1, ...]
    files: tuple[_AdmittedFileV1, ...]


@dataclass(slots=True)
class _LiveSingleRootAuthorityV1:
    authority: LocalSingleRootAuthorityV1


@dataclass(slots=True)
class _LiveSingleRootAdmissionV1:
    admission: LocalSingleRootAdmissionV1
    authority: LocalSingleRootAuthorityV1
    lease: RetainedDirectoryAdmissionV1


@dataclass(slots=True)
class _PublicationBorrowBindingV1:
    borrow: RetainedRootBorrowV1
    authority: LocalSingleRootAuthorityV1
    admission: LocalSingleRootAdmissionV1


@dataclass(frozen=True, slots=True)
class _AdmittedHardlinkPairV1:
    issued_ref: str
    object_id: int
    borrow_ref: str
    parent_ref: str
    parent_components: tuple[str, ...]
    first_component: str
    second_component: str
    identity: tuple[int, ...]
    first_raw: OpenFileV1
    second_raw: OpenFileV1


@dataclass(frozen=True, slots=True)
class _HardlinkPairQuarantineV1:
    quarantine_ref: str
    borrow_ref: str
    parent_ref: str
    first_raw: OpenFileV1 | None
    second_raw: OpenFileV1 | None


@dataclass(slots=True)
class _HardlinkPairStreamStateV1:
    expected_size: int
    cumulative_offset: int = 0
    eof_proven: bool = False
    poisoned: bool = False
    read_lock: Lock | None = None

    def __post_init__(self) -> None:
        if self.read_lock is None:
            self.read_lock = Lock()


class PosixFilesystemPortV1(Protocol):
    def retain_directory(self, absolute_path: Path) -> RetainedDirectoryV1: ...
    def open_directory_at(self, directory: RetainedDirectoryV1, component: str) -> RetainedDirectoryV1: ...
    def close_directory(self, directory: RetainedDirectoryV1) -> None: ...
    def list_names_at(self, directory: RetainedDirectoryV1, maximum: int) -> tuple[str, ...]: ...
    def stat_at(self, directory: RetainedDirectoryV1, component: str) -> LocalFileIdentityV1 | None: ...
    def open_read_at(self, directory: RetainedDirectoryV1, component: str) -> OpenFileV1: ...
    def create_exclusive_at(self, directory: RetainedDirectoryV1, component: str) -> OpenFileV1: ...
    def mkdir_at(self, directory: RetainedDirectoryV1, component: str) -> bool: ...
    def read(self, file: OpenFileV1, maximum: int) -> bytes: ...
    def write(self, file: OpenFileV1, payload: bytes) -> int: ...
    def stat_file(self, file: OpenFileV1) -> LocalFileIdentityV1: ...
    def close_file(self, file: OpenFileV1) -> None: ...
    def fsync_file(self, file: OpenFileV1) -> None: ...
    def fsync_directory(self, directory: RetainedDirectoryV1) -> None: ...
    def link_at(self, directory: RetainedDirectoryV1, source: str, destination: str) -> None: ...
    def unlink_at(self, directory: RetainedDirectoryV1, component: str) -> None: ...
    def acquire_directory_admission(self, directory: RetainedDirectoryV1) -> RetainedDirectoryAdmissionV1: ...
    def validate_directory_admission(self, directory: RetainedDirectoryV1,
                                     lease: RetainedDirectoryAdmissionV1) -> RetainedDirectoryAdmissionV1: ...
    def release_directory_admission(self, directory: RetainedDirectoryV1,
                                    lease: RetainedDirectoryAdmissionV1) -> None: ...
    def publish_journal(
        self,
        control: RetainedDirectoryV1,
        mutation_id: str,
        expected_previous_digest: str | None,
        record: CreateJournalRecordV1,
    ) -> JournalPublishResultV1: ...
    def snapshot_journal(
        self, control: RetainedDirectoryV1, mutation_id: str, maximum: int
    ) -> JournalSnapshotV1: ...


class RetainedRootBorrowPortV1(Protocol):
    def borrow_root(self, authority: LocalRootAuthorityV1,
                    request: RetainedRootBorrowRequestV1) -> RetainedRootBorrowV1: ...
    def root_directory(self, borrow: RetainedRootBorrowV1, *, purpose: BorrowPurposeV1) -> BorrowedDirectoryV1: ...
    def release_borrow(self, borrow: RetainedRootBorrowV1, *, purpose: BorrowPurposeV1) -> None: ...
    def open_borrowed_directory(self, borrow: RetainedRootBorrowV1,
                                parent: BorrowedDirectoryV1, component: str,
                                *, purpose: BorrowPurposeV1) -> BorrowedDirectoryV1: ...
    def close_borrowed_directory(self, borrow: RetainedRootBorrowV1,
                                 directory: BorrowedDirectoryV1, *, purpose: BorrowPurposeV1) -> None: ...
    def list_borrowed_directory(self, borrow: RetainedRootBorrowV1,
                                directory: BorrowedDirectoryV1, maximum: int,
                                *, purpose: BorrowPurposeV1) -> tuple[str, ...]: ...
    def stat_borrowed(self, borrow: RetainedRootBorrowV1,
                      directory: BorrowedDirectoryV1, component: str,
                      *, purpose: BorrowPurposeV1) -> LocalFileIdentityV1 | None: ...
    def mkdir_borrowed(self, borrow: RetainedRootBorrowV1,
                       directory: BorrowedDirectoryV1, component: str,
                       *, purpose: BorrowPurposeV1) -> bool: ...
    def open_borrowed_read(self, borrow: RetainedRootBorrowV1,
                           directory: BorrowedDirectoryV1, component: str,
                           *, purpose: BorrowPurposeV1) -> BorrowedFileV1: ...
    def create_borrowed_file(self, borrow: RetainedRootBorrowV1,
                             directory: BorrowedDirectoryV1, component: str,
                             *, purpose: BorrowPurposeV1) -> BorrowedFileV1: ...
    def read_borrowed(self, borrow: RetainedRootBorrowV1, file: BorrowedFileV1,
                      maximum: int, *, purpose: BorrowPurposeV1) -> bytes: ...
    def write_borrowed(self, borrow: RetainedRootBorrowV1, file: BorrowedFileV1,
                       payload: bytes, *, purpose: BorrowPurposeV1) -> int: ...
    def stat_borrowed_file(self, borrow: RetainedRootBorrowV1,
                           file: BorrowedFileV1, *, purpose: BorrowPurposeV1) -> LocalFileIdentityV1: ...
    def fsync_borrowed_file(self, borrow: RetainedRootBorrowV1,
                            file: BorrowedFileV1, *, purpose: BorrowPurposeV1) -> None: ...
    def close_borrowed_file(self, borrow: RetainedRootBorrowV1,
                            file: BorrowedFileV1, *, purpose: BorrowPurposeV1) -> None: ...
    def open_borrowed_hardlink_pair(
        self, borrow: RetainedRootBorrowV1, parent: BorrowedDirectoryV1,
        first_component: str, second_component: str, *, purpose: BorrowPurposeV1,
    ) -> BorrowedHardlinkPairV1: ...
    def read_borrowed_hardlink_pair(
        self, borrow: RetainedRootBorrowV1, pair: BorrowedHardlinkPairV1,
        maximum: int, *, purpose: BorrowPurposeV1,
    ) -> bytes: ...
    def stat_borrowed_hardlink_pair(
        self, borrow: RetainedRootBorrowV1, pair: BorrowedHardlinkPairV1,
        *, purpose: BorrowPurposeV1,
    ) -> LocalFileIdentityV1: ...
    def close_borrowed_hardlink_pair(
        self, borrow: RetainedRootBorrowV1, pair: BorrowedHardlinkPairV1,
        *, purpose: BorrowPurposeV1,
    ) -> None: ...
    def fsync_borrowed_directory(self, borrow: RetainedRootBorrowV1,
                                 directory: BorrowedDirectoryV1, *, purpose: BorrowPurposeV1) -> None: ...
    def link_borrowed(self, borrow: RetainedRootBorrowV1,
                      directory: BorrowedDirectoryV1, source: str, destination: str,
                      *, purpose: BorrowPurposeV1) -> None: ...
    def unlink_borrowed(self, borrow: RetainedRootBorrowV1,
                        directory: BorrowedDirectoryV1, component: str,
                        *, purpose: BorrowPurposeV1) -> None: ...


def _closed(code: LocalIOCodeV1) -> LocalIOErrorV1:
    return LocalIOErrorV1(code)


def _is_directory(identity: LocalFileIdentityV1) -> bool:
    return stat.S_ISDIR(identity.mode) and not stat.S_ISLNK(identity.mode)


def _is_regular_single(identity: LocalFileIdentityV1) -> bool:
    return stat.S_ISREG(identity.mode) and not stat.S_ISLNK(identity.mode) and identity.nlink == 1


def _is_regular_pair(identity: LocalFileIdentityV1) -> bool:
    return (
        type(identity) is LocalFileIdentityV1
        and stat.S_ISREG(identity.mode)
        and not stat.S_ISLNK(identity.mode)
        and identity.nlink == 2
        and 0 <= identity.size <= MAX_BORROWED_HARDLINK_PAIR_BYTES
    )


def _same_node(left: LocalFileIdentityV1, right: LocalFileIdentityV1) -> bool:
    return (
        left.device,
        left.inode,
        left.mode,
        left.modified_ns,
        left.size,
    ) == (
        right.device,
        right.inode,
        right.mode,
        right.modified_ns,
        right.size,
    )


def _same_borrow_node(left: LocalFileIdentityV1, right: LocalFileIdentityV1) -> bool:
    return (
        type(left) is LocalFileIdentityV1
        and type(right) is LocalFileIdentityV1
        and (left.device, left.inode, left.mode & 0o170000)
        == (right.device, right.inode, right.mode & 0o170000)
    )


def _journal_record(
    *,
    mutation_id: str,
    destination_digest: str,
    phase: CreatePhaseV1,
    previous: CreateJournalRecordV1 | None,
    staging_name: str,
    identity: LocalFileIdentityV1 | None,
) -> CreateJournalRecordV1:
    sequence = list(CreatePhaseV1).index(phase)
    canonical = {
        "destination_digest": destination_digest,
        "file_identity": None if identity is None else identity.canonical(),
        "mutation_id": mutation_id,
        "phase": phase.value,
        "previous_digest": None if previous is None else previous.record_digest,
        "sequence": sequence,
        "staging_name": staging_name,
    }
    return CreateJournalRecordV1(
        mutation_id=mutation_id,
        destination_digest=destination_digest,
        phase=phase,
        sequence=sequence,
        previous_digest=None if previous is None else previous.record_digest,
        staging_name=staging_name,
        file_identity=identity,
        record_digest=digest_v1(canonical),
    )


class LocalFilesystemV1:
    """One host-local coordinator over a retained-handle POSIX port."""

    def __init__(
        self,
        port: PosixFilesystemPortV1 | None,
        permit_authenticator: RootPermitAuthenticatorV1,
        *,
        native_platform: str | None = None,
    ) -> None:
        self._port = port
        self._permit_authenticator = permit_authenticator
        self._platform = sys.platform if native_platform is None else native_platform
        self._authority_counter = 0
        self._create_counter = 0
        self._live_roots: dict[str, LocalRootAuthorityV1] = {}
        self._single_root_counter = 0
        self._live_single_roots: dict[str, _LiveSingleRootAuthorityV1] = {}
        self._admission_counter = 0
        self._admission_process_id = os.getpid()
        self._admission_process_ref = "process-" + secrets.token_hex(16)
        self._fork_invalid = False
        self._live_admissions: dict[str, _LiveSingleRootAdmissionV1] = {}
        self._live_create: dict[str, tuple[LocalCreateAuthorityV1, LocalDestinationBindingV1]] = {}
        self._active_mutations: set[str] = set()
        self._borrow_counter = 0
        self._borrow_directory_counter = 0
        self._borrow_file_counter = 0
        self._borrow_pair_counter = 0
        self._borrow_lock = RLock()
        self._live_borrows: dict[
            str, tuple[RetainedRootBorrowV1, LocalRootAuthorityV1 | LocalSingleRootAuthorityV1]
        ] = {}
        self._borrow_admissions: dict[str, _PublicationBorrowBindingV1] = {}
        self._borrow_directories: dict[
            str, tuple[BorrowedDirectoryV1, str, RetainedDirectoryV1]
        ] = {}
        self._borrow_files: dict[str, tuple[BorrowedFileV1, str, OpenFileV1]] = {}
        self._borrow_pairs: dict[
            str, tuple[BorrowedHardlinkPairV1, str, str, OpenFileV1, OpenFileV1]
        ] = {}
        self._borrow_pair_quarantine: dict[str, _HardlinkPairQuarantineV1] = {}
        self._borrow_pair_streams: dict[str, _HardlinkPairStreamStateV1] = {}
        self._borrow_inflight: dict[str, int] = {}
        self._borrow_directory_inflight: dict[str, int] = {}
        self._borrow_file_inflight: dict[str, int] = {}
        self._borrow_pair_inflight: dict[str, int] = {}
        self._closing_borrow_directories: set[str] = set()
        self._closing_borrow_files: set[str] = set()
        self._closing_borrow_pairs: set[str] = set()
        self._borrow_issuance: dict[str, _BorrowIssuanceV1] = {}
        self._directory_issuance: dict[str, _DirectoryIssuanceV1] = {}
        self._file_issuance: dict[str, _FileIssuanceV1] = {}
        self._pair_issuance: dict[str, _HardlinkPairIssuanceV1] = {}
        self._borrow_issuance_seals: dict[str, str] = {}
        self._directory_issuance_seals: dict[str, str] = {}
        self._file_issuance_seals: dict[str, str] = {}
        self._pair_issuance_seals: dict[str, str] = {}
        self._borrow_object_refs: dict[int, str] = {}
        self._directory_object_refs: dict[int, str] = {}
        self._file_object_refs: dict[int, str] = {}
        self._pair_object_refs: dict[int, str] = {}
        self._invalid_borrow_issuance: set[str] = set()
        self._invalid_directory_issuance: set[str] = set()
        self._invalid_file_issuance: set[str] = set()
        self._invalid_pair_issuance: set[str] = set()
        if callable(getattr(os, "register_at_fork", None)):
            def after_fork_child() -> None:
                self._fork_invalid = True
                self._borrow_lock = RLock()
                self._live_single_roots = {}
                self._live_admissions = {}
                self._borrow_admissions = {}

            os.register_at_fork(after_in_child=after_fork_child)

    def _require_construction_process(self) -> None:
        try:
            current_pid = os.getpid()
        except BaseException:
            raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE) from None
        if self._fork_invalid or current_pid != self._admission_process_id:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)

    def capability(self) -> LocalFilesystemCapabilityV1:
        available = self._platform in _POSIX_PLATFORMS and self._port is not None
        platform_family = "posix" if self._platform in _POSIX_PLATFORMS else (
            "windows" if self._platform.startswith("win") else "other"
        )
        status = CapabilityStatusV1.AVAILABLE if available else CapabilityStatusV1.UNAVAILABLE
        feature_values = (
            "descriptor_relative", "exclusive_create", "retained_dirfd",
        ) if available else ()
        if available and self._platform.startswith("linux"):
            feature_values += (
                "crash-released-admission",
                "directory-inode-admission",
                "exec-closed-admission",
                "nonblocking-directory-flock",
            )
        features = tuple(sorted(feature_values))
        canonical = {
            "features": list(features),
            "platform_family": platform_family,
            "status": status.value,
        }
        return LocalFilesystemCapabilityV1(platform_family, status, features, digest_v1(canonical))

    def _require_posix(self) -> None:
        self._require_construction_process()
        if self._platform not in _POSIX_PLATFORMS or self._port is None:
            raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)

    def _require_linux_admission(self) -> None:
        self._require_posix()
        if not self._platform.startswith("linux"):
            raise _closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)

    def retain_root_authority(
        self,
        data_binding: LocalRootBindingV1,
        control_binding: LocalRootBindingV1,
    ) -> LocalRootAuthorityV1:
        self._require_posix()
        if type(data_binding) is not LocalRootBindingV1 or type(control_binding) is not LocalRootBindingV1:
            raise _closed(LocalIOCodeV1.ROOT_INVALID)
        self._authenticate_binding(data_binding)
        self._authenticate_binding(control_binding)
        if not control_binding.access.creatable or not control_binding.access.readable:
            raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
        if data_binding.binding_digest == control_binding.binding_digest:
            raise _closed(LocalIOCodeV1.ROOT_INVALID)
        data: RetainedDirectoryV1 | None = None
        control: RetainedDirectoryV1 | None = None
        try:
            data = self._port.retain_directory(data_binding.absolute_root)
            if type(data) is not RetainedDirectoryV1 or not _is_directory(data.identity):
                raise _closed(LocalIOCodeV1.ROOT_CHANGED)
            control = self._port.retain_directory(control_binding.absolute_root)
            if type(control) is not RetainedDirectoryV1 or not _is_directory(control.identity):
                raise _closed(LocalIOCodeV1.ROOT_CHANGED)
            if (data.identity.device, data.identity.inode) == (
                control.identity.device, control.identity.inode
            ):
                raise _closed(LocalIOCodeV1.ROOT_INVALID)
        except LocalIOErrorV1:
            if control is not None:
                try:
                    self._port.close_directory(control)
                except BaseException:
                    pass
            if data is not None:
                try:
                    self._port.close_directory(data)
                except BaseException:
                    pass
            raise
        except BaseException:
            if control is not None:
                try:
                    self._port.close_directory(control)
                except BaseException:
                    pass
            if data is not None:
                try:
                    self._port.close_directory(data)
                except BaseException:
                    pass
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        self._authority_counter += 1
        authority_ref = f"root-authority-{self._authority_counter}"
        result = LocalRootAuthorityV1(
            authority_ref,
            data_binding,
            control_binding,
            data,
            control,
            root_authority_digest_v1(
                data_binding, control_binding, data.identity, control.identity
            ),
        )
        with self._borrow_lock:
            self._live_roots[authority_ref] = result
        return result

    def _authenticate_binding(self, binding: LocalRootBindingV1) -> None:
        permit = binding.root_permit
        if permit is None:
            raise _closed(LocalIOCodeV1.ROOT_UNAUTHORIZED)
        try:
            authenticated = self._permit_authenticator.authenticate(permit)
        except BaseException:
            raise _closed(LocalIOCodeV1.ROOT_UNAUTHORIZED) from None
        if authenticated is not permit:
            raise _closed(LocalIOCodeV1.ROOT_UNAUTHORIZED)

    def retain_single_root_authority(
        self,
        binding: LocalRootBindingV1,
        *,
        purpose: SingleRootPurposeV1,
    ) -> LocalSingleRootAuthorityV1:
        self._require_linux_admission()
        if os.getpid() != self._admission_process_id:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        if (
            type(binding) is not LocalRootBindingV1
            or purpose is not SingleRootPurposeV1.PUBLICATION_SPOOL
            or binding.access is not RootAccessV1.READ_CREATE
        ):
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        self._authenticate_binding(binding)
        directory = None
        try:
            directory = self._port.retain_directory(binding.absolute_root)
            if type(directory) is not RetainedDirectoryV1 or not _is_directory(directory.identity):
                raise _closed(LocalIOCodeV1.ROOT_CHANGED)
        except LocalIOErrorV1:
            if directory is not None:
                try:
                    self._port.close_directory(directory)
                except BaseException:
                    pass
            raise
        except BaseException:
            if directory is not None:
                try:
                    self._port.close_directory(directory)
                except BaseException:
                    pass
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        with self._borrow_lock:
            self._single_root_counter += 1
            authority_ref = f"single-root-authority-{self._single_root_counter}"
            authority = LocalSingleRootAuthorityV1(
                authority_ref,
                binding,
                directory,
                purpose,
                single_root_authority_digest_v1(binding, directory.identity, purpose),
            )
            self._live_single_roots[authority_ref] = _LiveSingleRootAuthorityV1(authority)
            return authority

    def release_single_root_authority(self, authority: LocalSingleRootAuthorityV1) -> None:
        self._require_linux_admission()
        with self._borrow_lock:
            self._validate_single_root_authority(authority)
            if any(item.authority is authority for item in self._live_admissions.values()):
                raise _closed(LocalIOCodeV1.BORROW_IN_USE)
            if any(parent is authority for _, parent in self._live_borrows.values()):
                raise _closed(LocalIOCodeV1.BORROW_IN_USE)
            del self._live_single_roots[authority.authority_ref]
        try:
            self._port.close_directory(authority.data_directory)
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _validate_single_root_authority(self, authority: LocalSingleRootAuthorityV1) -> None:
        self._require_construction_process()
        if type(authority) is not LocalSingleRootAuthorityV1:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        if authority.authority_digest != single_root_authority_digest_v1(
            authority.data_binding, authority.data_directory.identity, authority.purpose
        ):
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        state = self._live_single_roots.get(authority.authority_ref)
        if state is None or state.authority is not authority:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)

    def acquire_single_root_admission(
        self, authority: LocalSingleRootAuthorityV1
    ) -> LocalSingleRootAdmissionV1:
        self._require_linux_admission()
        with self._borrow_lock:
            self._validate_single_root_authority(authority)
            self._authenticate_binding(authority.data_binding)
            if authority.purpose is not SingleRootPurposeV1.PUBLICATION_SPOOL:
                raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
            if any(item.authority is authority for item in self._live_admissions.values()):
                raise _closed(LocalIOCodeV1.ROOT_IN_USE)
            lease = self._port.acquire_directory_admission(authority.data_directory)
            if (
                type(lease) is not RetainedDirectoryAdmissionV1
                or lease.process_id != os.getpid()
                or lease.process_id != self._admission_process_id
            ):
                try:
                    self._port.release_directory_admission(authority.data_directory, lease)
                except BaseException:
                    pass
                raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
            self._admission_counter += 1
            admission_ref = f"single-root-admission-{self._admission_counter}"
            body = {
                "admission_ref": admission_ref,
                "authority_digest": authority.authority_digest,
                "lease_digest": lease.lease_digest,
                "process_id": self._admission_process_id,
                "process_instance_ref": self._admission_process_ref,
                "purpose": authority.purpose.value,
                "schema": "synaptic-host-single-root-admission/v1",
            }
            admission = LocalSingleRootAdmissionV1(
                admission_ref, authority.authority_digest, lease.lease_digest,
                authority.purpose, self._admission_process_id,
                self._admission_process_ref, digest_v1(body),
            )
            self._live_admissions[admission_ref] = _LiveSingleRootAdmissionV1(
                admission, authority, lease
            )
            return admission

    def _validate_single_root_admission(
        self,
        authority: LocalSingleRootAuthorityV1,
        admission: LocalSingleRootAdmissionV1,
    ) -> RetainedDirectoryAdmissionV1:
        self._require_construction_process()
        if type(admission) is not LocalSingleRootAdmissionV1:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        state = self._live_admissions.get(admission.admission_ref)
        if (
            state is None or state.admission is not admission or state.authority is not authority
            or admission.authority_digest != authority.authority_digest
            or admission.purpose is not authority.purpose
            or admission.process_id != os.getpid()
            or admission.process_id != self._admission_process_id
            or admission.process_instance_ref != self._admission_process_ref
            or admission.lease_digest != state.lease.lease_digest
        ):
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        try:
            validated = self._port.validate_directory_admission(
                authority.data_directory, state.lease
            )
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        if validated is not state.lease:
            raise _closed(LocalIOCodeV1.ADMISSION_INVALID)
        return state.lease

    def release_single_root_admission(
        self,
        authority: LocalSingleRootAuthorityV1,
        admission: LocalSingleRootAdmissionV1,
    ) -> None:
        self._require_linux_admission()
        with self._borrow_lock:
            self._validate_single_root_authority(authority)
            lease = self._validate_single_root_admission(authority, admission)
            if any(parent is authority for _, parent in self._live_borrows.values()):
                raise _closed(LocalIOCodeV1.BORROW_IN_USE)
            try:
                self._port.release_directory_admission(authority.data_directory, lease)
            finally:
                del self._live_admissions[admission.admission_ref]

    def _validate_borrow_authority(
        self, authority: LocalRootAuthorityV1 | LocalSingleRootAuthorityV1
    ) -> None:
        if type(authority) is LocalRootAuthorityV1:
            self._validate_authority(authority)
        elif type(authority) is LocalSingleRootAuthorityV1:
            self._validate_single_root_authority(authority)
        else:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)

    def release_root_authority(self, authority: LocalRootAuthorityV1) -> None:
        self._require_posix()
        with self._borrow_lock:
            self._validate_authority(authority)
            if any(parent is authority for _, parent in self._live_borrows.values()):
                raise _closed(LocalIOCodeV1.BORROW_IN_USE)
            del self._live_roots[authority.authority_ref]
        failed = False
        for directory in (authority.data_directory, authority.control_directory):
            try:
                self._port.close_directory(directory)
            except BaseException:
                failed = True
        if failed:
            raise _closed(LocalIOCodeV1.IO_FAILED)

    def _validate_authority(self, authority: LocalRootAuthorityV1) -> None:
        if type(authority) is not LocalRootAuthorityV1:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        # Reconstructing the immutable DTO repeats its structural digest check.
        if authority.authority_digest != root_authority_digest_v1(
            authority.data_binding,
            authority.control_binding,
            authority.data_directory.identity,
            authority.control_directory.identity,
        ):
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        if self._live_roots.get(authority.authority_ref) is not authority:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)

    @staticmethod
    def _borrow_access_allows(parent: RootAccessV1, requested: RootAccessV1) -> bool:
        return (
            (not requested.readable or parent.readable)
            and (not requested.creatable or parent.creatable)
        )

    def _record_borrow_issuance(
        self,
        borrow: RetainedRootBorrowV1,
        authority: LocalRootAuthorityV1 | LocalSingleRootAuthorityV1,
    ) -> None:
        issuance = _BorrowIssuanceV1(
            borrow.schema_version,
            "synaptic-host-root-borrow-request/v1",
            borrow.borrow_ref,
            borrow.request_digest,
            borrow.root_authority_digest,
            authority.authority_ref,
            authority.data_binding.root_ref,
            authority.data_binding.binding_digest,
            borrow.purpose.value,
            borrow.access.value,
            borrow.borrow_digest,
        )
        self._borrow_issuance[borrow.borrow_ref] = issuance
        self._borrow_issuance_seals[borrow.borrow_ref] = issuance.seal()
        self._borrow_object_refs[id(borrow)] = borrow.borrow_ref

    def _record_directory_issuance(
        self,
        directory: BorrowedDirectoryV1,
        borrow_ref: str,
    ) -> None:
        issuance = _DirectoryIssuanceV1(
            directory.schema_version,
            borrow_ref,
            directory.borrow_digest,
            directory.directory_ref,
            tuple(directory.path_components),
            directory.owns_handle,
            _identity_issuance_v1(directory.identity),
            directory.directory_digest,
        )
        self._directory_issuance[directory.directory_ref] = issuance
        self._directory_issuance_seals[directory.directory_ref] = issuance.seal()
        self._directory_object_refs[id(directory)] = directory.directory_ref

    def _record_file_issuance(
        self, file: BorrowedFileV1, borrow_ref: str
    ) -> None:
        issuance = _FileIssuanceV1(
            file.schema_version,
            borrow_ref,
            file.borrow_digest,
            file.file_ref,
            tuple(file.path_components[:-1]),
            file.path_components[-1],
            tuple(file.path_components),
            file.readable,
            file.writable,
            _identity_issuance_v1(file.identity),
            file.file_digest,
        )
        self._file_issuance[file.file_ref] = issuance
        self._file_issuance_seals[file.file_ref] = issuance.seal()
        self._file_object_refs[id(file)] = file.file_ref

    def _record_pair_issuance(
        self,
        pair: BorrowedHardlinkPairV1,
        borrow_ref: str,
        parent_ref: str,
    ) -> None:
        issuance = _HardlinkPairIssuanceV1(
            pair.schema_version,
            borrow_ref,
            pair.borrow_digest,
            pair.pair_ref,
            parent_ref,
            tuple(pair.parent_components),
            pair.first_component,
            pair.second_component,
            _identity_issuance_v1(pair.first_identity),
            pair.pair_digest,
        )
        self._pair_issuance[pair.pair_ref] = issuance
        self._pair_issuance_seals[pair.pair_ref] = issuance.seal()
        self._pair_object_refs[id(pair)] = pair.pair_ref

    def borrow_root(
        self,
        authority: LocalRootAuthorityV1,
        request: RetainedRootBorrowRequestV1,
    ) -> RetainedRootBorrowV1:
        self._require_posix()
        if type(request) is not RetainedRootBorrowRequestV1:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        try:
            request_valid = (
                type(authority) is LocalRootAuthorityV1
                and request.schema_version
                == "synaptic-host-root-borrow-request/v1"
                and request.root_authority_digest == authority.authority_digest
                and type(request.purpose) is BorrowPurposeV1
                and type(request.access) is RootAccessV1
                and request.request_digest
                == digest_v1(request.canonical_without_digest())
                and (
                    request.purpose is BorrowPurposeV1.BUNDLE_DESTINATION_CREATE
                    and request.access.creatable
                    or request.purpose
                    in {
                        BorrowPurposeV1.BUNDLE_SOURCE_READ,
                        BorrowPurposeV1.BUNDLE_MOUNT_VERIFY,
                    }
                    and request.access.readable
                )
            )
        except BaseException:
            request_valid = False
        if not request_valid:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        with self._borrow_lock:
            self._validate_authority(authority)
            self._authenticate_binding(authority.data_binding)
            if (
                request.root_authority_digest != authority.authority_digest
                or not self._borrow_access_allows(authority.data_binding.access, request.access)
            ):
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            return self._issue_borrow_locked(authority, request)

    def borrow_single_root(
        self,
        authority: LocalSingleRootAuthorityV1,
        admission: LocalSingleRootAdmissionV1,
        request: RetainedRootBorrowRequestV1,
    ) -> RetainedRootBorrowV1:
        self._require_posix()
        try:
            valid = (
                type(authority) is LocalSingleRootAuthorityV1
                and type(admission) is LocalSingleRootAdmissionV1
                and type(request) is RetainedRootBorrowRequestV1
                and authority.purpose is SingleRootPurposeV1.PUBLICATION_SPOOL
                and request.purpose is BorrowPurposeV1.PUBLICATION_SPOOL
                and request.access is RootAccessV1.READ_CREATE
                and request.root_authority_digest == authority.authority_digest
                and request.request_digest == digest_v1(request.canonical_without_digest())
            )
        except BaseException:
            valid = False
        if not valid:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        with self._borrow_lock:
            self._validate_single_root_authority(authority)
            self._validate_single_root_admission(authority, admission)
            self._authenticate_binding(authority.data_binding)
            self._validate_single_root_admission(authority, admission)
            return self._issue_borrow_locked(authority, request, admission=admission)

    def _issue_borrow_locked(
        self,
        authority: LocalRootAuthorityV1 | LocalSingleRootAuthorityV1,
        request: RetainedRootBorrowRequestV1,
        admission: LocalSingleRootAdmissionV1 | None = None,
    ) -> RetainedRootBorrowV1:
            self._borrow_counter += 1
            borrow_ref = f"root-borrow-{self._borrow_counter}"
            body = {
                "access": request.access.value,
                "borrow_ref": borrow_ref,
                "purpose": request.purpose.value,
                "request_digest": request.request_digest,
                "root_authority_digest": authority.authority_digest,
                "schema_version": "synaptic-host-root-borrow/v1",
            }
            borrow = RetainedRootBorrowV1(
                "synaptic-host-root-borrow/v1", borrow_ref, request.request_digest,
                authority.authority_digest, request.purpose, request.access,
                digest_v1(body),
            )
            self._live_borrows[borrow_ref] = (borrow, authority)
            if admission is not None:
                if type(authority) is not LocalSingleRootAuthorityV1:
                    raise _closed(LocalIOCodeV1.BORROW_INVALID)
                self._borrow_admissions[borrow_ref] = _PublicationBorrowBindingV1(
                    borrow, authority, admission
                )
            self._borrow_inflight[borrow_ref] = 0
            self._record_borrow_issuance(borrow, authority)
            self._borrow_directory_counter += 1
            directory_ref = f"borrow-dir-{self._borrow_directory_counter}"
            directory_body = {
                "borrow_digest": borrow.borrow_digest,
                "directory_ref": directory_ref,
                "identity": authority.data_directory.identity.canonical(),
                "owns_handle": False,
                "path_components": [],
                "schema_version": "synaptic-host-borrowed-directory/v1",
            }
            root = BorrowedDirectoryV1(
                "synaptic-host-borrowed-directory/v1", borrow.borrow_digest,
                directory_ref, (), False, authority.data_directory.identity,
                digest_v1(directory_body),
            )
            self._borrow_directories[directory_ref] = (
                root, borrow_ref, authority.data_directory
            )
            self._borrow_directory_inflight[directory_ref] = 0
            self._record_directory_issuance(root, borrow_ref)
            return borrow

    def _borrow_locked(self, borrow: RetainedRootBorrowV1, purpose: BorrowPurposeV1):
        self._require_construction_process()
        if (
            type(borrow) is not RetainedRootBorrowV1
            or type(purpose) is not BorrowPurposeV1
        ):
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        issued_ref = self._borrow_object_refs.get(id(borrow))
        try:
            issuance = self._borrow_issuance.get(issued_ref)
            state = self._live_borrows.get(issued_ref)
            authority = None if state is None else state[1]
            publication_binding = self._borrow_admissions.get(issued_ref)
            request_projection = {
                "access": borrow.access.value,
                "purpose": borrow.purpose.value,
                "root_authority_digest": borrow.root_authority_digest,
                "schema_version": "synaptic-host-root-borrow-request/v1",
            }
            valid = (
                issued_ref is not None
                and issued_ref not in self._invalid_borrow_issuance
                and issuance is not None
                and state is not None
                and state[0] is borrow
                and issuance.seal() == self._borrow_issuance_seals.get(issued_ref)
                and borrow.schema_version == issuance.schema_version
                and borrow.borrow_ref == issuance.borrow_ref == issued_ref
                and borrow.request_digest == issuance.request_digest
                and borrow.root_authority_digest == issuance.root_authority_digest
                and borrow.purpose.value == issuance.purpose
                and borrow.access.value == issuance.access
                and borrow.borrow_digest == issuance.borrow_digest
                and borrow.request_digest == digest_v1(request_projection)
                and borrow.borrow_digest
                == digest_v1(borrow.canonical_without_digest())
                and authority.authority_ref == issuance.authority_ref
                and authority.authority_digest == issuance.root_authority_digest
                and authority.data_binding.root_ref == issuance.data_root_ref
                and authority.data_binding.binding_digest
                == issuance.data_binding_digest
                and borrow.purpose is purpose
                and (
                    type(authority) is LocalRootAuthorityV1
                    and publication_binding is None
                    or type(authority) is LocalSingleRootAuthorityV1
                    and os.getpid() == self._admission_process_id
                    and type(publication_binding) is _PublicationBorrowBindingV1
                    and publication_binding.borrow is borrow
                    and publication_binding.authority is authority
                )
            )
        except BaseException:
            valid = False
            state = None
        if not valid:
            if issued_ref is not None:
                self._invalid_borrow_issuance.add(issued_ref)
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        if type(authority) is LocalSingleRootAuthorityV1:
            self._validate_single_root_authority(authority)
            self._validate_single_root_admission(authority, publication_binding.admission)
        return state

    def _revalidate_borrow_boundary(
        self, borrow: RetainedRootBorrowV1, purpose: BorrowPurposeV1
    ) -> None:
        if purpose is not BorrowPurposeV1.PUBLICATION_SPOOL:
            return
        self._require_construction_process()
        with self._borrow_lock:
            self._borrow_locked(borrow, purpose)

    def _directory_locked(self, borrow: RetainedRootBorrowV1,
                          directory: BorrowedDirectoryV1) -> RetainedDirectoryV1:
        if type(directory) is not BorrowedDirectoryV1:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        issued_ref = self._directory_object_refs.get(id(directory))
        try:
            issuance = self._directory_issuance.get(issued_ref)
            state = self._borrow_directories.get(issued_ref)
            valid = (
                issued_ref is not None
                and issued_ref not in self._invalid_directory_issuance
                and issuance is not None
                and state is not None
                and state[0] is directory
                and issuance.seal()
                == self._directory_issuance_seals.get(issued_ref)
                and directory.schema_version == issuance.schema_version
                and directory.borrow_digest == issuance.borrow_digest
                and directory.directory_ref == issuance.directory_ref == issued_ref
                and tuple(directory.path_components) == issuance.path_components
                and directory.owns_handle is issuance.owns_handle
                and _identity_issuance_v1(directory.identity) == issuance.identity
                and directory.directory_digest == issuance.directory_digest
                and directory.directory_digest
                == digest_v1(directory.canonical_without_digest())
                and issuance.borrow_ref == borrow.borrow_ref
                and directory.borrow_digest == borrow.borrow_digest
                and issued_ref not in self._closing_borrow_directories
                and _same_borrow_node(directory.identity, state[2].identity)
            )
        except BaseException:
            valid = False
            state = None
        if not valid:
            if issued_ref is not None:
                self._invalid_directory_issuance.add(issued_ref)
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        return state[2]

    def _file_locked(self, borrow: RetainedRootBorrowV1,
                     file: BorrowedFileV1) -> OpenFileV1:
        if type(file) is not BorrowedFileV1:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        issued_ref = self._file_object_refs.get(id(file))
        try:
            issuance = self._file_issuance.get(issued_ref)
            state = self._borrow_files.get(issued_ref)
            valid = (
                issued_ref is not None
                and issued_ref not in self._invalid_file_issuance
                and issuance is not None
                and state is not None
                and state[0] is file
                and issuance.seal() == self._file_issuance_seals.get(issued_ref)
                and file.schema_version == issuance.schema_version
                and file.borrow_digest == issuance.borrow_digest
                and file.file_ref == issuance.file_ref == issued_ref
                and tuple(file.path_components[:-1]) == issuance.parent_path
                and file.path_components[-1] == issuance.component
                and tuple(file.path_components) == issuance.path_components
                and file.readable is issuance.readable
                and file.writable is issuance.writable
                and _identity_issuance_v1(file.identity) == issuance.identity
                and file.file_digest == issuance.file_digest
                and file.file_digest == digest_v1(file.canonical_without_digest())
                and issuance.borrow_ref == borrow.borrow_ref
                and file.borrow_digest == borrow.borrow_digest
                and issued_ref not in self._closing_borrow_files
                and _same_borrow_node(file.identity, state[2].identity)
            )
        except BaseException:
            valid = False
            state = None
        if not valid:
            if issued_ref is not None:
                self._invalid_file_issuance.add(issued_ref)
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        return state[2]

    def _pair_locked(
        self, borrow: RetainedRootBorrowV1, pair: BorrowedHardlinkPairV1
    ) -> tuple[OpenFileV1, OpenFileV1]:
        if type(pair) is not BorrowedHardlinkPairV1:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        issued_ref = self._pair_object_refs.get(id(pair))
        try:
            issuance = self._pair_issuance.get(issued_ref)
            state = self._borrow_pairs.get(issued_ref)
            valid = (
                issued_ref is not None
                and issued_ref not in self._invalid_pair_issuance
                and issued_ref not in self._closing_borrow_pairs
                and issuance is not None
                and state is not None
                and state[0] is pair
                and state[1] == borrow.borrow_ref == issuance.borrow_ref
                and state[2] == issuance.parent_ref
                and issuance.seal() == self._pair_issuance_seals.get(issued_ref)
                and pair.schema_version == issuance.schema_version
                and pair.borrow_digest == borrow.borrow_digest == issuance.borrow_digest
                and pair.pair_ref == issuance.pair_ref == issued_ref
                and tuple(pair.parent_components) == issuance.parent_components
                and pair.first_component == issuance.first_component
                and pair.second_component == issuance.second_component
                and _identity_issuance_v1(pair.first_identity) == issuance.identity
                and pair.first_identity == pair.second_identity
                and pair.pair_digest == issuance.pair_digest
                and pair.pair_digest == digest_v1(pair.canonical_without_digest())
                and _identity_issuance_v1(state[3].identity) == issuance.identity
                and _identity_issuance_v1(state[4].identity) == issuance.identity
            )
        except BaseException:
            valid = False
            state = None
        if not valid:
            if issued_ref is not None:
                self._invalid_pair_issuance.add(issued_ref)
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        return state[3], state[4]

    def _validate_pair_purpose_locked(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        parent: BorrowedDirectoryV1 | None = None,
        pair: BorrowedHardlinkPairV1 | None = None,
    ) -> None:
        issued_ref = self._borrow_object_refs.get(id(borrow))
        issuance = self._borrow_issuance.get(issued_ref)
        if issuance is None:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        try:
            issued_purpose = BorrowPurposeV1(issuance.purpose)
        except BaseException:
            raise _closed(LocalIOCodeV1.BORROW_INVALID) from None
        self._borrow_locked(borrow, issued_purpose)
        if (
            issuance.purpose != BorrowPurposeV1.BUNDLE_MOUNT_VERIFY.value
            or issuance.access
            not in {RootAccessV1.READ_ONLY.value, RootAccessV1.READ_CREATE.value}
            or purpose is not BorrowPurposeV1.BUNDLE_MOUNT_VERIFY
        ):
            raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
        if parent is not None:
            self._directory_locked(borrow, parent)
        if pair is not None:
            self._pair_locked(borrow, pair)

    def _capture_pair_locked(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        pair: BorrowedHardlinkPairV1,
    ) -> tuple[_AdmittedEffectV1, _AdmittedHardlinkPairV1, LocalRootAuthorityV1]:
        self._pair_locked(borrow, pair)
        issued_ref = self._pair_object_refs[id(pair)]
        issuance = self._pair_issuance[issued_ref]
        parent_state = self._borrow_directories.get(issuance.parent_ref)
        if (
            parent_state is None
            or parent_state[1] != issuance.borrow_ref
            or self._directory_issuance.get(issuance.parent_ref) is None
        ):
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        context, authority = self._capture_effect_locked(
            borrow, purpose, (parent_state[0],), ()
        )
        state = self._borrow_pairs[issued_ref]
        admitted = _AdmittedHardlinkPairV1(
            issued_ref,
            id(pair),
            issuance.borrow_ref,
            issuance.parent_ref,
            issuance.parent_components,
            issuance.first_component,
            issuance.second_component,
            issuance.identity,
            state[3],
            state[4],
        )
        return context, admitted, authority

    def _directory_ancestry_locked(
        self, borrow: RetainedRootBorrowV1, path: tuple[str, ...]
    ) -> None:
        for depth in range(0, len(path) + 1):
            prefix = path[:depth]
            matches = [
                item[0]
                for item in self._borrow_directories.values()
                if item[1] == borrow.borrow_ref
                and item[0].path_components == prefix
            ]
            if len(matches) != 1:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            self._directory_locked(borrow, matches[0])

    def _capture_effect_locked(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        directories: tuple[BorrowedDirectoryV1, ...],
        files: tuple[BorrowedFileV1, ...],
    ) -> tuple[_AdmittedEffectV1, LocalRootAuthorityV1]:
        _, authority = self._borrow_locked(borrow, purpose)
        borrow_ref = self._borrow_object_refs[id(borrow)]
        borrow_issuance = self._borrow_issuance[borrow_ref]
        requested_paths: set[tuple[str, ...]] = {()}
        for directory in directories:
            self._directory_locked(borrow, directory)
            issued_ref = self._directory_object_refs[id(directory)]
            issuance = self._directory_issuance[issued_ref]
            if issuance.borrow_ref != borrow_ref:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            path = issuance.path_components
            requested_paths.update(path[:depth] for depth in range(len(path) + 1))
        for file in files:
            self._file_locked(borrow, file)
            issued_ref = self._file_object_refs[id(file)]
            issuance = self._file_issuance[issued_ref]
            if issuance.borrow_ref != borrow_ref:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            parent_path = issuance.parent_path
            requested_paths.update(
                parent_path[:depth] for depth in range(len(parent_path) + 1)
            )

        admitted_directories: list[_AdmittedDirectoryV1] = []
        for path in sorted(requested_paths, key=lambda value: (len(value), value)):
            matches = [
                (issued_ref, issuance)
                for issued_ref, issuance in self._directory_issuance.items()
                if issuance.borrow_ref == borrow_ref
                and issuance.path_components == path
            ]
            if len(matches) != 1:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            issued_ref, issuance = matches[0]
            state = self._borrow_directories.get(issued_ref)
            if (
                issued_ref in self._invalid_directory_issuance
                or issued_ref in self._closing_borrow_directories
                or state is None
                or state[1] != borrow_ref
                or self._directory_object_refs.get(id(state[0])) != issued_ref
                or issuance.seal()
                != self._directory_issuance_seals.get(issued_ref)
                or (
                    state[2].identity.device,
                    state[2].identity.inode,
                    state[2].identity.mode & 0o170000,
                )
                != (
                    issuance.identity[0],
                    issuance.identity[1],
                    issuance.identity[2] & 0o170000,
                )
            ):
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            admitted_directories.append(_AdmittedDirectoryV1(
                issued_ref,
                id(state[0]),
                issuance.borrow_ref,
                issuance.path_components,
                issuance.owns_handle,
                tuple(issuance.identity),
                state[2],
            ))

        admitted_files: list[_AdmittedFileV1] = []
        for file in files:
            issued_ref = self._file_object_refs[id(file)]
            issuance = self._file_issuance[issued_ref]
            state = self._borrow_files.get(issued_ref)
            if (
                issued_ref in self._invalid_file_issuance
                or issued_ref in self._closing_borrow_files
                or state is None
                or state[1] != borrow_ref
                or self._file_object_refs.get(id(state[0])) != issued_ref
                or issuance.seal() != self._file_issuance_seals.get(issued_ref)
            ):
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            admitted_files.append(_AdmittedFileV1(
                issued_ref,
                id(file),
                issuance.borrow_ref,
                issuance.parent_path,
                issuance.component,
                issuance.readable,
                issuance.writable,
                tuple(issuance.identity),
                state[2],
            ))

        root = next(
            item for item in admitted_directories if not item.path_components
        )
        context = _AdmittedEffectV1(
            borrow_ref,
            borrow_issuance.purpose,
            borrow_issuance.access,
            str(authority.data_binding.absolute_root),
            root.identity,
            tuple(admitted_directories),
            tuple(admitted_files),
        )
        return context, authority

    @staticmethod
    def _context_directory(
        context: _AdmittedEffectV1, issued_ref: str
    ) -> _AdmittedDirectoryV1:
        matches = [item for item in context.directories if item.issued_ref == issued_ref]
        if len(matches) != 1:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        return matches[0]

    @staticmethod
    def _context_file(
        context: _AdmittedEffectV1, issued_ref: str
    ) -> _AdmittedFileV1:
        matches = [item for item in context.files if item.issued_ref == issued_ref]
        if len(matches) != 1:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        return matches[0]

    def _poison_mutated_visible_locked(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        directories: tuple[BorrowedDirectoryV1, ...],
        files: tuple[BorrowedFileV1, ...],
    ) -> None:
        try:
            self._borrow_locked(borrow, purpose)
        except BaseException:
            pass
        for directory in directories:
            try:
                self._directory_locked(borrow, directory)
            except BaseException:
                pass
        for file in files:
            try:
                self._file_locked(borrow, file)
            except BaseException:
                pass

    def _poison_mutated_pair_locked(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        pair: BorrowedHardlinkPairV1,
    ) -> None:
        try:
            self._borrow_locked(borrow, purpose)
        except BaseException:
            pass
        try:
            self._pair_locked(borrow, pair)
        except BaseException:
            pass

    @staticmethod
    def _purpose_allows_context(context: _AdmittedEffectV1, action: str) -> bool:
        if action in {"metadata", "close"}:
            return True
        if action == "read":
            return (
                context.purpose
                in {
                    BorrowPurposeV1.BUNDLE_SOURCE_READ.value,
                    BorrowPurposeV1.BUNDLE_MOUNT_VERIFY.value,
                    BorrowPurposeV1.PUBLICATION_SPOOL.value,
                }
                and context.access
                in {RootAccessV1.READ_ONLY.value, RootAccessV1.READ_CREATE.value}
            )
        if action in {"mutation", "durability"}:
            return (
                context.purpose in {
                    BorrowPurposeV1.BUNDLE_DESTINATION_CREATE.value,
                    BorrowPurposeV1.PUBLICATION_SPOOL.value,
                }
                and context.access
                in {RootAccessV1.CREATE_ONLY.value, RootAccessV1.READ_CREATE.value}
            )
        return False

    def _reauthenticate_effect(self, context: _AdmittedEffectV1) -> None:
        reopened = None
        try:
            reopened = self._port.retain_directory(Path(context.absolute_root))
            if (
                type(reopened) is not RetainedDirectoryV1
                or (
                    reopened.identity.device,
                    reopened.identity.inode,
                    reopened.identity.mode & 0o170000,
                )
                != (
                    context.root_identity[0],
                    context.root_identity[1],
                    context.root_identity[2] & 0o170000,
                )
                or reopened.identity.changed_ns < context.root_identity[4]
            ):
                raise _closed(LocalIOCodeV1.ROOT_CHANGED)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.ROOT_CHANGED) from None
        finally:
            if reopened is not None:
                try:
                    self._port.close_directory(reopened)
                except BaseException:
                    raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _verify_admitted_effect(self, context: _AdmittedEffectV1) -> None:
        directories_by_path = {
            item.path_components: item for item in context.directories
        }
        for directory in context.directories:
            if not directory.path_components:
                continue
            child_path = directory.path_components
            parent_path = child_path[:-1]
            parent = directories_by_path.get(parent_path)
            if parent is None:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            actual = self._port.stat_at(parent.raw, child_path[-1])
            if (
                type(actual) is not LocalFileIdentityV1
                or (
                    actual.device, actual.inode, actual.mode & 0o170000
                )
                != (
                    directory.identity[0],
                    directory.identity[1],
                    directory.identity[2] & 0o170000,
                )
                or actual.changed_ns < directory.identity[4]
            ):
                raise _closed(LocalIOCodeV1.PATH_CHANGED)
        for file in context.files:
            parent = directories_by_path.get(file.parent_path)
            if parent is None:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            path_identity = self._port.stat_at(parent.raw, file.component)
            handle_identity = self._port.stat_file(file.raw)
            issued_identity = file.identity
            exact_read_identity = (
                type(path_identity) is LocalFileIdentityV1
                and type(handle_identity) is LocalFileIdentityV1
                and _identity_issuance_v1(path_identity) == issued_identity
                and _identity_issuance_v1(handle_identity) == issued_identity
            )
            evolving_write_identity = (
                type(path_identity) is LocalFileIdentityV1
                and type(handle_identity) is LocalFileIdentityV1
                and (
                    path_identity.device,
                    path_identity.inode,
                    path_identity.mode & 0o170000,
                )
                == (
                    issued_identity[0],
                    issued_identity[1],
                    issued_identity[2] & 0o170000,
                )
                and path_identity == handle_identity
                and path_identity.changed_ns >= issued_identity[4]
                and _is_regular_single(path_identity)
            )
            if not (exact_read_identity if file.readable else evolving_write_identity):
                raise _closed(LocalIOCodeV1.PATH_CHANGED)

    def _verify_admitted_pair(
        self,
        context: _AdmittedEffectV1,
        pair: _AdmittedHardlinkPairV1,
    ) -> LocalFileIdentityV1:
        parent = next(
            (directory for directory in context.directories
             if directory.issued_ref == pair.parent_ref),
            None,
        )
        if parent is None:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        first_path = self._port.stat_at(parent.raw, pair.first_component)
        second_path = self._port.stat_at(parent.raw, pair.second_component)
        first_handle = self._port.stat_file(pair.first_raw)
        second_handle = self._port.stat_file(pair.second_raw)
        values = (first_path, second_path, first_handle, second_handle)
        if (
            any(type(value) is not LocalFileIdentityV1 for value in values)
            or any(_identity_issuance_v1(value) != pair.identity for value in values)
            or any(not _is_regular_pair(value) for value in values)
        ):
            raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
        return first_handle

    @contextmanager
    def _pin_pair(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        pair: BorrowedHardlinkPairV1,
    ):
        context = None
        admitted_pair = None
        pinned = False
        try:
            with self._borrow_lock:
                self._validate_pair_purpose_locked(
                    borrow, purpose, pair=pair
                )
                context, admitted_pair, authority = self._capture_pair_locked(
                    borrow, purpose, pair
                )
                if (
                    context.purpose != BorrowPurposeV1.BUNDLE_MOUNT_VERIFY.value
                    or context.access
                    not in {RootAccessV1.READ_ONLY.value, RootAccessV1.READ_CREATE.value}
                ):
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                self._validate_borrow_authority(authority)
                self._authenticate_binding(authority.data_binding)
                self._borrow_inflight[context.borrow_ref] += 1
                for directory in context.directories:
                    self._borrow_directory_inflight[directory.issued_ref] += 1
                self._borrow_pair_inflight[admitted_pair.issued_ref] += 1
                pinned = True
            self._reauthenticate_effect(context)
            self._verify_admitted_effect(context)
            self._verify_admitted_pair(context, admitted_pair)
            yield context, admitted_pair
        finally:
            if context is not None and admitted_pair is not None:
                with self._borrow_lock:
                    if pinned:
                        if admitted_pair.issued_ref in self._borrow_pair_inflight:
                            self._borrow_pair_inflight[admitted_pair.issued_ref] -= 1
                        for directory in context.directories:
                            if directory.issued_ref in self._borrow_directory_inflight:
                                self._borrow_directory_inflight[directory.issued_ref] -= 1
                        if context.borrow_ref in self._borrow_inflight:
                            self._borrow_inflight[context.borrow_ref] -= 1
                    self._poison_mutated_pair_locked(borrow, purpose, pair)

    @contextmanager
    def _pin_borrow(
        self,
        borrow: RetainedRootBorrowV1,
        purpose: BorrowPurposeV1,
        *,
        action: str = "metadata",
        directories: tuple[BorrowedDirectoryV1, ...] = (),
        files: tuple[BorrowedFileV1, ...] = (),
    ):
        context = None
        pinned = False
        try:
            self._require_construction_process()
            with self._borrow_lock:
                context, authority = self._capture_effect_locked(
                    borrow, purpose, directories, files
                )
                self._validate_borrow_authority(authority)
                self._authenticate_binding(authority.data_binding)
                if not self._purpose_allows_context(context, action):
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                self._borrow_inflight[context.borrow_ref] += 1
                for directory in context.directories:
                    self._borrow_directory_inflight[directory.issued_ref] += 1
                for file in context.files:
                    self._borrow_file_inflight[file.issued_ref] += 1
                pinned = True
            self._reauthenticate_effect(context)
            self._revalidate_borrow_boundary(borrow, purpose)
            self._verify_admitted_effect(context)
            self._revalidate_borrow_boundary(borrow, purpose)
            yield context
        finally:
            if context is not None:
                with self._borrow_lock:
                    if pinned:
                        for file in context.files:
                            if file.issued_ref in self._borrow_file_inflight:
                                self._borrow_file_inflight[file.issued_ref] -= 1
                        for directory in context.directories:
                            if directory.issued_ref in self._borrow_directory_inflight:
                                self._borrow_directory_inflight[directory.issued_ref] -= 1
                        if context.borrow_ref in self._borrow_inflight:
                            self._borrow_inflight[context.borrow_ref] -= 1
                    self._poison_mutated_visible_locked(
                        borrow, purpose, directories, files
                    )

    def root_directory(self, borrow: RetainedRootBorrowV1, *, purpose: BorrowPurposeV1) -> BorrowedDirectoryV1:
        self._require_construction_process()
        with self._borrow_lock:
            self._borrow_locked(borrow, purpose)
            roots = [item[0] for item in self._borrow_directories.values()
                     if item[1] == borrow.borrow_ref and not item[0].owns_handle]
            if len(roots) != 1:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            self._directory_locked(borrow, roots[0])
            return roots[0]

    def release_borrow(self, borrow: RetainedRootBorrowV1, *, purpose: BorrowPurposeV1) -> None:
        self._require_construction_process()
        with self._borrow_lock:
            self._borrow_locked(borrow, purpose)
            has_children = any(
                item[1] == borrow.borrow_ref and item[0].owns_handle
                for item in self._borrow_directories.values()
            ) or any(item[1] == borrow.borrow_ref for item in self._borrow_files.values()) \
                or any(item[1] == borrow.borrow_ref for item in self._borrow_pairs.values()) \
                or any(item.borrow_ref == borrow.borrow_ref for item in self._borrow_pair_quarantine.values())
            if self._borrow_inflight[borrow.borrow_ref] or has_children:
                raise _closed(LocalIOCodeV1.BORROW_IN_USE)
            root_refs = [key for key, item in self._borrow_directories.items()
                         if item[1] == borrow.borrow_ref]
            if len(root_refs) != 1:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            root = self._borrow_directories[root_refs[0]][0]
            self._directory_locked(borrow, root)
            del self._directory_object_refs[id(root)]
            self._directory_issuance.pop(root_refs[0], None)
            self._directory_issuance_seals.pop(root_refs[0], None)
            self._invalid_directory_issuance.discard(root_refs[0])
            del self._borrow_directory_inflight[root_refs[0]]
            del self._borrow_directories[root_refs[0]]
            issued_ref = self._borrow_object_refs.pop(id(borrow))
            self._borrow_issuance.pop(issued_ref, None)
            self._borrow_issuance_seals.pop(issued_ref, None)
            self._invalid_borrow_issuance.discard(issued_ref)
            del self._borrow_inflight[borrow.borrow_ref]
            del self._live_borrows[borrow.borrow_ref]
            self._borrow_admissions.pop(borrow.borrow_ref, None)

    @staticmethod
    def _borrow_component(component: str) -> str:
        parts = canonical_relative_components_v1(component)
        if len(parts) != 1:
            raise _closed(LocalIOCodeV1.PATH_INVALID)
        return parts[0]

    def _new_borrowed_directory(
        self,
        context: _AdmittedEffectV1,
        parent: _AdmittedDirectoryV1,
        component: str,
        raw: RetainedDirectoryV1,
    ):
        with self._borrow_lock:
            issuance = self._borrow_issuance.get(context.borrow_ref)
            if (
                issuance is None
                or context.borrow_ref in self._invalid_borrow_issuance
            ):
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            self._borrow_directory_counter += 1
            ref = f"borrow-dir-{self._borrow_directory_counter}"
            path = parent.path_components + (component,)
            body = {"borrow_digest": issuance.borrow_digest, "directory_ref": ref,
                    "identity": raw.identity.canonical(),
                    "owns_handle": True, "path_components": list(path),
                    "schema_version": "synaptic-host-borrowed-directory/v1"}
            value = BorrowedDirectoryV1(
                "synaptic-host-borrowed-directory/v1", issuance.borrow_digest,
                ref, path, True, raw.identity, digest_v1(body),
            )
            self._borrow_directories[ref] = (value, context.borrow_ref, raw)
            self._borrow_directory_inflight[ref] = 0
            self._record_directory_issuance(value, context.borrow_ref)
            return value

    def open_borrowed_directory(self, borrow, parent, component, *, purpose):
        component = self._borrow_component(component)
        raw = None
        try:
            with self._pin_borrow(
                borrow, purpose, action="metadata", directories=(parent,)
            ) as context:
                try:
                    admitted_parent = context.directories[-1]
                    raw_parent = admitted_parent.raw
                    raw = self._port.open_directory_at(raw_parent, component)
                    path_identity = self._port.stat_at(raw_parent, component)
                    if (
                        type(raw) is not RetainedDirectoryV1
                        or not _is_directory(raw.identity)
                        or path_identity != raw.identity
                    ):
                        raise _closed(LocalIOCodeV1.PATH_CHANGED)
                    result = self._new_borrowed_directory(
                        context, admitted_parent, component, raw
                    )
                    raw = None
                    return result
                finally:
                    if raw is not None and type(raw) is RetainedDirectoryV1:
                        try:
                            self._port.close_directory(raw)
                        except BaseException:
                            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def close_borrowed_directory(self, borrow, directory, *, purpose):
        self._require_construction_process()
        context = None
        target = None
        admitted = False
        succeeded = False
        try:
            with self._borrow_lock:
                context, authority = self._capture_effect_locked(
                    borrow, purpose, (directory,), ()
                )
                target = context.directories[-1]
                self._validate_borrow_authority(authority)
                self._authenticate_binding(authority.data_binding)
                if not self._purpose_allows_context(context, "close"):
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                if not target.owns_handle:
                    raise _closed(LocalIOCodeV1.BORROW_INVALID)
                prefix = target.path_components
                if (
                    self._borrow_directory_inflight[target.issued_ref]
                    or any(
                        issuance.borrow_ref == context.borrow_ref
                        and issuance.directory_ref != target.issued_ref
                        and issuance.path_components[:len(prefix)] == prefix
                        for issuance in self._directory_issuance.values()
                    )
                    or any(
                        issuance.borrow_ref == context.borrow_ref
                        and issuance.path_components[:len(prefix)] == prefix
                        for issuance in self._file_issuance.values()
                    )
                    or any(
                        issuance.borrow_ref == context.borrow_ref
                        and issuance.parent_components[:len(prefix)] == prefix
                        for issuance in self._pair_issuance.values()
                    )
                    or any(
                        quarantine.borrow_ref == context.borrow_ref
                        and quarantine.parent_ref == target.issued_ref
                        for quarantine in self._borrow_pair_quarantine.values()
                    )
                ):
                    raise _closed(LocalIOCodeV1.BORROW_IN_USE)
                self._closing_borrow_directories.add(target.issued_ref)
                self._borrow_inflight[context.borrow_ref] += 1
                admitted = True
            self._reauthenticate_effect(context)
            self._revalidate_borrow_boundary(borrow, purpose)
            self._verify_admitted_effect(context)
            self._revalidate_borrow_boundary(borrow, purpose)
            self._port.close_directory(target.raw)
            succeeded = True
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            with self._borrow_lock:
                if context is not None and target is not None:
                    self._poison_mutated_visible_locked(
                        borrow, purpose, (directory,), ()
                    )
                    if succeeded:
                        self._directory_object_refs.pop(target.object_id, None)
                        self._directory_issuance.pop(target.issued_ref, None)
                        self._directory_issuance_seals.pop(target.issued_ref, None)
                        self._invalid_directory_issuance.discard(target.issued_ref)
                        self._borrow_directory_inflight.pop(target.issued_ref, None)
                        self._borrow_directories.pop(target.issued_ref, None)
                    self._closing_borrow_directories.discard(target.issued_ref)
                    if admitted and context.borrow_ref in self._borrow_inflight:
                        self._borrow_inflight[context.borrow_ref] -= 1

    def list_borrowed_directory(self, borrow, directory, maximum, *, purpose):
        if type(maximum) is not int or not 0 <= maximum <= MAX_DIRECTORY_ENTRIES + 1:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        try:
            with self._pin_borrow(
                borrow, purpose, action="metadata", directories=(directory,)
            ) as context:
                raw = context.directories[-1].raw
                values = self._port.list_names_at(raw, maximum)
                if (
                    type(values) is not tuple
                    or len(values) > maximum
                    or any(type(value) is not str for value in values)
                ):
                    raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
                try:
                    if any(self._borrow_component(value) != value for value in values):
                        raise _closed(LocalIOCodeV1.PATH_INVALID)
                except LocalIOErrorV1:
                    raise _closed(LocalIOCodeV1.PATH_INVALID) from None
                return values
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def stat_borrowed(self, borrow, directory, component, *, purpose):
        component = self._borrow_component(component)
        try:
            with self._pin_borrow(
                borrow, purpose, action="metadata", directories=(directory,)
            ) as context:
                raw = context.directories[-1].raw
                value = self._port.stat_at(raw, component)
                if value is not None and type(value) is not LocalFileIdentityV1:
                    raise _closed(LocalIOCodeV1.IO_FAILED)
                return value
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def mkdir_borrowed(self, borrow, directory, component, *, purpose):
        component = self._borrow_component(component)
        try:
            with self._pin_borrow(
                borrow, purpose, action="mutation", directories=(directory,)
            ) as context:
                raw = context.directories[-1].raw
                result = self._port.mkdir_at(raw, component)
                if type(result) is not bool:
                    raise _closed(LocalIOCodeV1.IO_FAILED)
                return result
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _new_borrowed_file(
        self,
        context: _AdmittedEffectV1,
        directory: _AdmittedDirectoryV1,
        component: str,
        raw: OpenFileV1,
        *,
        readable: bool,
    ):
        if type(raw) is not OpenFileV1 or not _is_regular_single(raw.identity):
            raise _closed(LocalIOCodeV1.PATH_CHANGED)
        with self._borrow_lock:
            issuance = self._borrow_issuance.get(context.borrow_ref)
            if (
                issuance is None
                or context.borrow_ref in self._invalid_borrow_issuance
            ):
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            self._borrow_file_counter += 1
            ref = f"borrow-file-{self._borrow_file_counter}"
            path = directory.path_components + (component,)
            body = {
                "borrow_digest": issuance.borrow_digest,
                "file_ref": ref,
                "identity": raw.identity.canonical(),
                "path_components": list(path),
                "readable": readable,
                "schema_version": "synaptic-host-borrowed-file/v1",
                "writable": not readable,
            }
            value = BorrowedFileV1(
                "synaptic-host-borrowed-file/v1", issuance.borrow_digest, ref,
                path, readable, not readable, raw.identity, digest_v1(body),
            )
            self._borrow_files[ref] = (value, context.borrow_ref, raw)
            self._borrow_file_inflight[ref] = 0
            self._record_file_issuance(value, context.borrow_ref)
            return value

    def open_borrowed_read(self, borrow, directory, component, *, purpose):
        component = self._borrow_component(component)
        raw = None
        try:
            with self._pin_borrow(
                borrow, purpose, action="read", directories=(directory,)
            ) as context:
                try:
                    admitted_directory = context.directories[-1]
                    raw_directory = admitted_directory.raw
                    raw = self._port.open_read_at(raw_directory, component)
                    if type(raw) is not OpenFileV1:
                        raise _closed(LocalIOCodeV1.PATH_CHANGED)
                    path_identity = self._port.stat_at(raw_directory, component)
                    if path_identity != raw.identity:
                        raise _closed(LocalIOCodeV1.PATH_CHANGED)
                    result = self._new_borrowed_file(
                        context, admitted_directory, component, raw, readable=True
                    )
                    raw = None
                    return result
                finally:
                    if raw is not None and type(raw) is OpenFileV1:
                        try:
                            self._port.close_file(raw)
                        except BaseException:
                            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def create_borrowed_file(self, borrow, directory, component, *, purpose):
        component = self._borrow_component(component)
        raw = None
        try:
            with self._pin_borrow(
                borrow, purpose, action="mutation", directories=(directory,)
            ) as context:
                try:
                    admitted_directory = context.directories[-1]
                    raw_directory = admitted_directory.raw
                    raw = self._port.create_exclusive_at(raw_directory, component)
                    if type(raw) is not OpenFileV1:
                        raise _closed(LocalIOCodeV1.PATH_CHANGED)
                    path_identity = self._port.stat_at(raw_directory, component)
                    if path_identity != raw.identity:
                        raise _closed(LocalIOCodeV1.PATH_CHANGED)
                    result = self._new_borrowed_file(
                        context, admitted_directory, component, raw, readable=False
                    )
                    raw = None
                    return result
                finally:
                    if raw is not None and type(raw) is OpenFileV1:
                        try:
                            self._port.close_file(raw)
                        except BaseException:
                            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        except FileExistsError:
            raise _closed(LocalIOCodeV1.DESTINATION_EXISTS) from None
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def read_borrowed(self, borrow, file, maximum, *, purpose):
        if type(maximum) is not int or not 1 <= maximum <= MAX_CHUNK_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        try:
            with self._pin_borrow(
                borrow, purpose, action="read", files=(file,)
            ) as context:
                admitted_file = context.files[0]
                raw = admitted_file.raw
                if not admitted_file.readable:
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                value = self._port.read(raw, maximum)
                if type(value) is not bytes or len(value) > maximum:
                    raise _closed(LocalIOCodeV1.STREAM_INVALID)
                return value
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def write_borrowed(self, borrow, file, payload, *, purpose):
        if type(payload) is not bytes or not 1 <= len(payload) <= MAX_CHUNK_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        try:
            with self._pin_borrow(
                borrow, purpose, action="mutation", files=(file,)
            ) as context:
                admitted_file = context.files[0]
                raw = admitted_file.raw
                if not admitted_file.writable:
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                count = self._port.write(raw, payload)
                if type(count) is not int or count != len(payload):
                    raise _closed(LocalIOCodeV1.STREAM_INVALID)
                return count
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def stat_borrowed_file(self, borrow, file, *, purpose):
        try:
            with self._pin_borrow(
                borrow, purpose, action="metadata", files=(file,)
            ) as context:
                raw = context.files[0].raw
                value = self._port.stat_file(raw)
                if type(value) is not LocalFileIdentityV1:
                    raise _closed(LocalIOCodeV1.IO_FAILED)
                return value
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def fsync_borrowed_file(self, borrow, file, *, purpose):
        try:
            with self._pin_borrow(
                borrow, purpose, action="durability", files=(file,)
            ) as context:
                admitted_file = context.files[0]
                raw = admitted_file.raw
                if not admitted_file.writable:
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                self._port.fsync_file(raw)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def close_borrowed_file(self, borrow, file, *, purpose):
        self._require_construction_process()
        context = None
        target = None
        admitted = False
        succeeded = False
        try:
            with self._borrow_lock:
                context, authority = self._capture_effect_locked(
                    borrow, purpose, (), (file,)
                )
                target = context.files[0]
                self._validate_borrow_authority(authority)
                self._authenticate_binding(authority.data_binding)
                if not self._purpose_allows_context(context, "close"):
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                if self._borrow_file_inflight[target.issued_ref]:
                    raise _closed(LocalIOCodeV1.BORROW_IN_USE)
                self._closing_borrow_files.add(target.issued_ref)
                self._borrow_inflight[context.borrow_ref] += 1
                admitted = True
            self._reauthenticate_effect(context)
            self._revalidate_borrow_boundary(borrow, purpose)
            self._verify_admitted_effect(context)
            self._revalidate_borrow_boundary(borrow, purpose)
            self._port.close_file(target.raw)
            succeeded = True
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            with self._borrow_lock:
                if context is not None and target is not None:
                    self._poison_mutated_visible_locked(
                        borrow, purpose, (), (file,)
                    )
                    if succeeded:
                        self._file_object_refs.pop(target.object_id, None)
                        self._file_issuance.pop(target.issued_ref, None)
                        self._file_issuance_seals.pop(target.issued_ref, None)
                        self._invalid_file_issuance.discard(target.issued_ref)
                        self._borrow_file_inflight.pop(target.issued_ref, None)
                        self._borrow_files.pop(target.issued_ref, None)
                    self._closing_borrow_files.discard(target.issued_ref)
                    if admitted and context.borrow_ref in self._borrow_inflight:
                        self._borrow_inflight[context.borrow_ref] -= 1

    def _quarantine_pair_handles(
        self,
        quarantine_ref: str,
        borrow_ref: str,
        parent_ref: str,
        first_raw: OpenFileV1 | None,
        second_raw: OpenFileV1 | None,
    ) -> None:
        with self._borrow_lock:
            self._borrow_pair_quarantine[quarantine_ref] = _HardlinkPairQuarantineV1(
                quarantine_ref, borrow_ref, parent_ref, first_raw, second_raw
            )

    def _close_pair_raws(
        self, first_raw: OpenFileV1 | None, second_raw: OpenFileV1 | None
    ) -> tuple[bool, bool]:
        failures = [False, False]
        for index, raw in enumerate((first_raw, second_raw)):
            if raw is None:
                continue
            try:
                self._port.close_file(raw)
            except BaseException:
                failures[index] = True
        return failures[0], failures[1]

    def open_borrowed_hardlink_pair(
        self, borrow, parent, first_component, second_component, *, purpose
    ):
        first_component = self._borrow_component(first_component)
        second_component = self._borrow_component(second_component)
        if first_component == second_component:
            raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
        first_component, second_component = sorted(
            (first_component, second_component)
        )
        first_raw = None
        second_raw = None
        attempt_ref = None
        borrow_ref = None
        parent_ref = None
        registered = False
        try:
            with self._borrow_lock:
                self._validate_pair_purpose_locked(
                    borrow, purpose, parent=parent
                )
            with self._pin_borrow(
                borrow, purpose, action="read", directories=(parent,)
            ) as context:
                if (
                    context.purpose != BorrowPurposeV1.BUNDLE_MOUNT_VERIFY.value
                    or context.access
                    not in {RootAccessV1.READ_ONLY.value, RootAccessV1.READ_CREATE.value}
                ):
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                admitted_parent = context.directories[-1]
                borrow_ref = context.borrow_ref
                parent_ref = admitted_parent.issued_ref
                with self._borrow_lock:
                    self._borrow_pair_counter += 1
                    attempt_ref = f"borrow-pair-{self._borrow_pair_counter}"
                raw_parent = admitted_parent.raw
                p1 = self._port.stat_at(raw_parent, first_component)
                p2 = self._port.stat_at(raw_parent, second_component)
                if (
                    type(p1) is not LocalFileIdentityV1
                    or type(p2) is not LocalFileIdentityV1
                    or p1 != p2
                    or not _is_regular_pair(p1)
                ):
                    raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                first_raw = self._port.open_read_at(raw_parent, first_component)
                m1 = self._port.stat_file(first_raw)
                second_raw = self._port.open_read_at(raw_parent, second_component)
                m2 = self._port.stat_file(second_raw)
                a1 = self._port.stat_at(raw_parent, first_component)
                a2 = self._port.stat_at(raw_parent, second_component)
                identities = (
                    p1, p2, first_raw.identity, m1,
                    second_raw.identity, m2, a1, a2,
                )
                if (
                    any(type(identity) is not LocalFileIdentityV1 for identity in identities)
                    or any(identity != p1 for identity in identities)
                    or not _is_regular_pair(p1)
                ):
                    raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                borrow_issuance = self._borrow_issuance.get(context.borrow_ref)
                if borrow_issuance is None:
                    raise _closed(LocalIOCodeV1.BORROW_INVALID)
                body = {
                    "borrow_digest": borrow_issuance.borrow_digest,
                    "first_component": first_component,
                    "first_identity": p1.canonical(),
                    "pair_ref": attempt_ref,
                    "parent_components": list(admitted_parent.path_components),
                    "schema_version": "synaptic-host-borrowed-hardlink-pair/v1",
                    "second_component": second_component,
                    "second_identity": p1.canonical(),
                }
                pair = BorrowedHardlinkPairV1(
                    "synaptic-host-borrowed-hardlink-pair/v1",
                    borrow_issuance.borrow_digest,
                    attempt_ref,
                    admitted_parent.path_components,
                    first_component,
                    second_component,
                    p1,
                    p1,
                    digest_v1(body),
                )
                with self._borrow_lock:
                    if (
                        context.borrow_ref in self._invalid_borrow_issuance
                        or admitted_parent.issued_ref in self._invalid_directory_issuance
                    ):
                        raise _closed(LocalIOCodeV1.BORROW_INVALID)
                    try:
                        self._borrow_pairs[attempt_ref] = (
                            pair, context.borrow_ref, admitted_parent.issued_ref,
                            first_raw, second_raw,
                        )
                        self._borrow_pair_inflight[attempt_ref] = 0
                        self._borrow_pair_streams[attempt_ref] = (
                            _HardlinkPairStreamStateV1(p1.size)
                        )
                        self._record_pair_issuance(
                            pair, context.borrow_ref, admitted_parent.issued_ref
                        )
                        registered = True
                    except BaseException:
                        self._pair_object_refs.pop(id(pair), None)
                        self._pair_issuance.pop(attempt_ref, None)
                        self._pair_issuance_seals.pop(attempt_ref, None)
                        self._borrow_pair_inflight.pop(attempt_ref, None)
                        self._borrow_pair_streams.pop(attempt_ref, None)
                        self._borrow_pairs.pop(attempt_ref, None)
                        raise
                first_raw = None
                second_raw = None
                return pair
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            if not registered and (first_raw is not None or second_raw is not None):
                first_failed, second_failed = self._close_pair_raws(first_raw, second_raw)
                if first_failed or second_failed:
                    self._quarantine_pair_handles(
                        attempt_ref or "borrow-pair-quarantine",
                        borrow_ref or "borrow-invalid",
                        parent_ref or "borrow-dir-invalid",
                        first_raw if first_failed else None,
                        second_raw if second_failed else None,
                    )

    def read_borrowed_hardlink_pair(
        self, borrow, pair, maximum, *, purpose
    ):
        if type(maximum) is not int or not 1 <= maximum <= MAX_BORROWED_HARDLINK_PAIR_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        with self._borrow_lock:
            self._validate_pair_purpose_locked(borrow, purpose, pair=pair)
            pair_ref = self._pair_object_refs[id(pair)]
            stream = self._borrow_pair_streams.get(pair_ref)
            if stream is None:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            if stream.poisoned:
                raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
            if stream.eof_proven:
                raise _closed(LocalIOCodeV1.STREAM_INVALID)
            read_lock = stream.read_lock
        if read_lock is None:
            raise _closed(LocalIOCodeV1.BORROW_INVALID)
        try:
            with read_lock:
                with self._borrow_lock:
                    if (
                        self._borrow_pair_streams.get(pair_ref) is not stream
                        or stream.poisoned
                    ):
                        raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                    if stream.eof_proven:
                        raise _closed(LocalIOCodeV1.STREAM_INVALID)
                with self._pin_pair(borrow, purpose, pair) as (context, admitted):
                    first = self._port.read(admitted.first_raw, maximum)
                    second = self._port.read(admitted.second_raw, maximum)
                    if (
                        type(first) is not bytes
                        or type(second) is not bytes
                        or len(first) > maximum
                        or len(second) > maximum
                        or first != second
                    ):
                        raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                    self._verify_admitted_pair(context, admitted)
                    with self._borrow_lock:
                        if not first:
                            if stream.cumulative_offset != stream.expected_size:
                                raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                            stream.eof_proven = True
                            return b""
                        if (
                            stream.cumulative_offset >= stream.expected_size
                            or stream.cumulative_offset + len(first)
                            > stream.expected_size
                        ):
                            raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                        stream.cumulative_offset += len(first)
                        return first
        except LocalIOErrorV1:
            with self._borrow_lock:
                self._poison_exact_pair_stream_locked(pair_ref, stream)
            raise
        except BaseException:
            with self._borrow_lock:
                self._poison_exact_pair_stream_locked(pair_ref, stream)
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _poison_exact_pair_stream_locked(
        self,
        pair_ref: str,
        stream: _HardlinkPairStreamStateV1,
    ) -> None:
        if self._borrow_pair_streams.get(pair_ref) is stream:
            stream.poisoned = True

    def stat_borrowed_hardlink_pair(self, borrow, pair, *, purpose):
        with self._borrow_lock:
            pair_ref = self._pair_object_refs.get(id(pair))
            if pair_ref is None:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            stream = self._borrow_pair_streams.get(pair_ref)
            if stream is None:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            read_lock = stream.read_lock
        try:
            if read_lock is None:
                raise _closed(LocalIOCodeV1.BORROW_INVALID)
            with read_lock:
                with self._borrow_lock:
                    if (
                        self._borrow_pair_streams.get(pair_ref) is not stream
                        or self._pair_object_refs.get(id(pair)) != pair_ref
                    ):
                        raise _closed(LocalIOCodeV1.BORROW_INVALID)
                    if stream.poisoned:
                        raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                    self._validate_pair_purpose_locked(
                        borrow, purpose, pair=pair
                    )
                with self._pin_pair(borrow, purpose, pair) as (context, admitted):
                    value = self._verify_admitted_pair(context, admitted)
                with self._borrow_lock:
                    if (
                        self._borrow_pair_streams.get(pair_ref) is not stream
                        or self._pair_object_refs.get(id(pair)) != pair_ref
                    ):
                        raise _closed(LocalIOCodeV1.BORROW_INVALID)
                    if stream.poisoned:
                        raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
                return value
        except LocalIOErrorV1:
            with self._borrow_lock:
                self._poison_exact_pair_stream_locked(pair_ref, stream)
            raise
        except BaseException:
            with self._borrow_lock:
                self._poison_exact_pair_stream_locked(pair_ref, stream)
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def close_borrowed_hardlink_pair(self, borrow, pair, *, purpose):
        context = None
        admitted = None
        semantic_error = None
        admitted_close = False
        first_failed = False
        second_failed = False
        try:
            with self._borrow_lock:
                self._validate_pair_purpose_locked(
                    borrow, purpose, pair=pair
                )
                context, admitted, authority = self._capture_pair_locked(
                    borrow, purpose, pair
                )
                if (
                    context.purpose != BorrowPurposeV1.BUNDLE_MOUNT_VERIFY.value
                    or context.access
                    not in {RootAccessV1.READ_ONLY.value, RootAccessV1.READ_CREATE.value}
                ):
                    raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
                self._validate_authority(authority)
                self._authenticate_binding(authority.data_binding)
                if self._borrow_pair_inflight[admitted.issued_ref]:
                    raise _closed(LocalIOCodeV1.BORROW_IN_USE)
                stream = self._borrow_pair_streams.get(admitted.issued_ref)
                if stream is None:
                    raise _closed(LocalIOCodeV1.BORROW_INVALID)
                self._closing_borrow_pairs.add(admitted.issued_ref)
                self._borrow_inflight[context.borrow_ref] += 1
                admitted_close = True
                if stream.poisoned or not stream.eof_proven:
                    semantic_error = _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
            try:
                self._reauthenticate_effect(context)
                self._verify_admitted_effect(context)
                self._verify_admitted_pair(context, admitted)
            except LocalIOErrorV1 as error:
                if semantic_error is None:
                    semantic_error = error
            except BaseException:
                semantic_error = _closed(LocalIOCodeV1.IO_FAILED)
            first_failed, second_failed = self._close_pair_raws(
                admitted.first_raw, admitted.second_raw
            )
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            if context is not None and admitted is not None:
                with self._borrow_lock:
                    self._poison_mutated_pair_locked(borrow, purpose, pair)
                    if admitted_close:
                        self._pair_object_refs.pop(admitted.object_id, None)
                        self._pair_issuance.pop(admitted.issued_ref, None)
                        self._pair_issuance_seals.pop(admitted.issued_ref, None)
                        self._invalid_pair_issuance.discard(admitted.issued_ref)
                        self._borrow_pair_inflight.pop(admitted.issued_ref, None)
                        self._borrow_pair_streams.pop(admitted.issued_ref, None)
                        self._borrow_pairs.pop(admitted.issued_ref, None)
                        self._closing_borrow_pairs.discard(admitted.issued_ref)
                        if first_failed or second_failed:
                            self._borrow_pair_quarantine[admitted.issued_ref] = (
                                _HardlinkPairQuarantineV1(
                                    admitted.issued_ref,
                                    context.borrow_ref,
                                    admitted.parent_ref,
                                    admitted.first_raw if first_failed else None,
                                    admitted.second_raw if second_failed else None,
                                )
                            )
                        if context.borrow_ref in self._borrow_inflight:
                            self._borrow_inflight[context.borrow_ref] -= 1
        if first_failed or second_failed:
            raise _closed(LocalIOCodeV1.IO_FAILED)
        if semantic_error is not None:
            raise semantic_error

    def fsync_borrowed_directory(self, borrow, directory, *, purpose):
        try:
            with self._pin_borrow(
                borrow, purpose, action="durability", directories=(directory,)
            ) as context:
                raw = context.directories[-1].raw
                self._port.fsync_directory(raw)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def link_borrowed(self, borrow, directory, source, destination, *, purpose):
        source = self._borrow_component(source)
        destination = self._borrow_component(destination)
        if source == destination:
            raise _closed(LocalIOCodeV1.PATH_INVALID)
        try:
            with self._pin_borrow(
                borrow, purpose, action="mutation", directories=(directory,)
            ) as context:
                raw = context.directories[-1].raw
                self._port.link_at(raw, source, destination)
        except FileExistsError:
            raise _closed(LocalIOCodeV1.DESTINATION_EXISTS) from None
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def unlink_borrowed(self, borrow, directory, component, *, purpose):
        component = self._borrow_component(component)
        try:
            with self._pin_borrow(
                borrow, purpose, action="mutation", directories=(directory,)
            ) as context:
                raw = context.directories[-1].raw
                self._port.unlink_at(raw, component)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _open_parent(
        self, authority: LocalRootAuthorityV1, relative_path: str
    ) -> tuple[RetainedDirectoryV1, str, list[RetainedDirectoryV1]]:
        parts = canonical_relative_components_v1(relative_path)
        current = authority.data_directory
        opened: list[RetainedDirectoryV1] = []
        try:
            for component in parts[:-1]:
                self._reject_collision(current, component, may_be_missing=False)
                before = self._port.stat_at(current, component)
                if type(before) is not LocalFileIdentityV1 or not _is_directory(before):
                    raise _closed(LocalIOCodeV1.PATH_CHANGED)
                child = self._port.open_directory_at(current, component)
                after = self._port.stat_at(current, component)
                if (
                    type(child) is not RetainedDirectoryV1
                    or not _is_directory(child.identity)
                    or after != before
                    or child.identity != before
                ):
                    raise _closed(LocalIOCodeV1.PATH_CHANGED)
                opened.append(child)
                current = child
            return current, parts[-1], opened
        except LocalIOErrorV1:
            self._close_directories(opened)
            raise
        except BaseException:
            self._close_directories(opened)
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _reject_collision(
        self, directory: RetainedDirectoryV1, component: str, *, may_be_missing: bool
    ) -> bool:
        try:
            names = self._port.list_names_at(directory, MAX_DIRECTORY_ENTRIES + 1)
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        if type(names) is not tuple or len(names) > MAX_DIRECTORY_ENTRIES or any(type(name) is not str for name in names):
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        import unicodedata

        try:
            for name in names:
                if canonical_relative_components_v1(name) != (name,):
                    raise _closed(LocalIOCodeV1.PATH_COLLISION)
        except LocalIOErrorV1:
            raise _closed(LocalIOCodeV1.PATH_COLLISION) from None
        folded = unicodedata.normalize("NFC", component).casefold()
        matches = [name for name in names if unicodedata.normalize("NFC", name).casefold() == folded]
        if len(matches) > 1 or (matches and matches[0] != component):
            raise _closed(LocalIOCodeV1.PATH_COLLISION)
        if not matches and not may_be_missing:
            raise _closed(LocalIOCodeV1.PATH_INVALID)
        return bool(matches)

    def _close_directories(
        self, directories: list[RetainedDirectoryV1], *, strict: bool = False
    ) -> None:
        failed = False
        for directory in reversed(directories):
            try:
                self._port.close_directory(directory)
            except BaseException:
                failed = True
        if failed and strict:
            raise _closed(LocalIOCodeV1.IO_FAILED)

    def _read_opened(
        self,
        opened: OpenFileV1,
        *,
        maximum_bytes: int,
        require_single_link: bool = True,
    ) -> tuple[int, str, LocalFileIdentityV1]:
        if (
            type(opened) is not OpenFileV1
            or not stat.S_ISREG(opened.identity.mode)
            or stat.S_ISLNK(opened.identity.mode)
        ):
            raise _closed(LocalIOCodeV1.SOURCE_INVALID)
        if require_single_link and opened.identity.nlink != 1:
            raise _closed(LocalIOCodeV1.HARDLINK_UNSAFE)
        digest = hashlib.sha256()
        total = 0
        try:
            while True:
                chunk = self._port.read(opened, MAX_CHUNK_BYTES)
                if type(chunk) is not bytes or len(chunk) > MAX_CHUNK_BYTES:
                    raise _closed(LocalIOCodeV1.STREAM_INVALID)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum_bytes:
                    raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
                digest.update(chunk)
            after = self._port.stat_file(opened)
            if type(after) is not LocalFileIdentityV1 or after != opened.identity or total != after.size:
                raise _closed(LocalIOCodeV1.SOURCE_CHANGED)
            return total, digest.hexdigest(), after
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def _reopen_logical_leaf(
        self,
        parent: RetainedDirectoryV1,
        name: str,
        expected: LocalFileIdentityV1,
    ) -> None:
        reopened: OpenFileV1 | None = None
        try:
            before = self._port.stat_at(parent, name)
            if before != expected:
                raise _closed(LocalIOCodeV1.PATH_CHANGED)
            reopened = self._port.open_read_at(parent, name)
            after = self._port.stat_at(parent, name)
            if (
                type(reopened) is not OpenFileV1
                or reopened.identity != expected
                or after != expected
                or not _is_regular_single(reopened.identity)
                or self._port.stat_file(reopened) != expected
            ):
                raise _closed(LocalIOCodeV1.PATH_CHANGED)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.SOURCE_CHANGED) from None
        finally:
            if reopened is not None:
                try:
                    self._port.close_file(reopened)
                except BaseException:
                    raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def inspect_source(
        self,
        authority: LocalRootAuthorityV1,
        relative_path: str,
        *,
        role: str,
        maximum_bytes: int = MAX_FILE_BYTES,
    ) -> LocalSourceBindingV1:
        self._require_posix()
        self._validate_authority(authority)
        if not authority.data_binding.access.readable:
            raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
        checked_ref(role, LocalIOCodeV1.SOURCE_INVALID)
        if type(maximum_bytes) is not int or not 0 <= maximum_bytes <= MAX_FILE_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        parent, name, directories = self._open_parent(authority, relative_path)
        opened: OpenFileV1 | None = None
        try:
            self._reject_collision(parent, name, may_be_missing=False)
            before = self._port.stat_at(parent, name)
            opened = self._port.open_read_at(parent, name)
            after_open = self._port.stat_at(parent, name)
            if type(before) is not LocalFileIdentityV1 or opened.identity != before or after_open != before:
                raise _closed(LocalIOCodeV1.PATH_CHANGED)
            size, sha256, identity = self._read_opened(opened, maximum_bytes=maximum_bytes)
            self._reopen_logical_leaf(parent, name, identity)
            return LocalSourceBindingV1(
                authority.authority_digest,
                "/".join(canonical_relative_components_v1(relative_path)),
                role,
                size,
                sha256,
                identity,
            )
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            if opened is not None:
                try:
                    self._port.close_file(opened)
                except BaseException:
                    raise _closed(LocalIOCodeV1.IO_FAILED) from None
            self._close_directories(directories, strict=True)

    def iter_source(
        self,
        authority: LocalRootAuthorityV1,
        source: LocalSourceBindingV1,
        *,
        chunk_size: int = MAX_CHUNK_BYTES,
    ) -> Iterator[bytes]:
        self._require_posix()
        self._validate_authority(authority)
        if type(source) is not LocalSourceBindingV1 or source.authority_digest != authority.authority_digest:
            raise _closed(LocalIOCodeV1.SOURCE_INVALID)
        if type(chunk_size) is not int or not 1 <= chunk_size <= MAX_CHUNK_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        parent, name, directories = self._open_parent(authority, source.relative_path)
        opened: OpenFileV1 | None = None
        digest = hashlib.sha256()
        total = 0
        try:
            self._reject_collision(parent, name, may_be_missing=False)
            before = self._port.stat_at(parent, name)
            opened = self._port.open_read_at(parent, name)
            after_open = self._port.stat_at(parent, name)
            if (
                type(before) is not LocalFileIdentityV1
                or type(opened) is not OpenFileV1
                or before != source.identity
                or opened.identity != source.identity
                or after_open != source.identity
                or not _is_regular_single(opened.identity)
            ):
                raise _closed(LocalIOCodeV1.SOURCE_CHANGED)
            while True:
                chunk = self._port.read(opened, chunk_size)
                if type(chunk) is not bytes or len(chunk) > chunk_size:
                    raise _closed(LocalIOCodeV1.STREAM_INVALID)
                if not chunk:
                    break
                total += len(chunk)
                if total > source.size:
                    raise _closed(LocalIOCodeV1.SOURCE_CHANGED)
                digest.update(chunk)
                yield chunk
            after = self._port.stat_file(opened)
            if (
                type(after) is not LocalFileIdentityV1
                or after != source.identity
                or total != source.size
                or digest.hexdigest() != source.sha256
            ):
                raise _closed(LocalIOCodeV1.SOURCE_CHANGED)
            self._reopen_logical_leaf(parent, name, source.identity)
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            if opened is not None:
                try:
                    self._port.close_file(opened)
                except BaseException:
                    raise _closed(LocalIOCodeV1.IO_FAILED) from None
            self._close_directories(directories, strict=True)

    def bind_destination(
        self,
        authority: LocalRootAuthorityV1,
        relative_path: str,
        *,
        role: str,
        expected_size: int,
        expected_sha256: str,
    ) -> LocalDestinationBindingV1:
        # Metadata-only: safe on every platform and makes no port call.
        self._validate_authority(authority)
        if not authority.data_binding.access.creatable:
            raise _closed(LocalIOCodeV1.ACCESS_MISMATCH)
        canonical = "/".join(canonical_relative_components_v1(relative_path))
        checked_ref(role, LocalIOCodeV1.DESTINATION_INVALID)
        size = checked_size(expected_size, LocalIOCodeV1.DESTINATION_INVALID)
        if size > MAX_FILE_BYTES:
            raise _closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        sha256 = checked_sha256(expected_sha256, LocalIOCodeV1.DESTINATION_INVALID)
        return LocalDestinationBindingV1(authority.authority_digest, canonical, role, size, sha256)

    def authorize_create(
        self, authority: LocalRootAuthorityV1, destination: LocalDestinationBindingV1
    ) -> LocalCreateAuthorityV1:
        # Issuance is local metadata, but an effectful use is still POSIX-gated.
        self._validate_authority(authority)
        if type(destination) is not LocalDestinationBindingV1 or destination.authority_digest != authority.authority_digest:
            raise _closed(LocalIOCodeV1.DESTINATION_INVALID)
        self._create_counter += 1
        authority_ref = f"create-authority-{self._create_counter}"
        mutation_id = digest_v1({
            "destination_digest": destination.destination_digest,
            "root_authority_digest": authority.authority_digest,
        })
        issued = LocalCreateAuthorityV1(
            authority_ref, authority.authority_digest, destination.destination_digest, mutation_id
        )
        self._live_create[authority_ref] = (issued, destination)
        return issued

    def _append_phase(
        self,
        authority: LocalRootAuthorityV1,
        record: CreateJournalRecordV1,
    ) -> JournalPublishStatusV1:
        try:
            result = self._port.publish_journal(
                authority.control_directory,
                record.mutation_id,
                record.previous_digest,
                record,
            )
            if (
                type(result) is not JournalPublishResultV1
                or result.mutation_id != record.mutation_id
                or result.record_digest != record.record_digest
                or type(result.published_record) is not CreateJournalRecordV1
                or result.published_record != record
            ):
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
            return result.status
        except LocalIOErrorV1:
            raise
        except BaseException:
            raise _closed(LocalIOCodeV1.IO_FAILED) from None

    def create_once(
        self,
        root_authority: LocalRootAuthorityV1,
        create_authority: LocalCreateAuthorityV1,
        destination: LocalDestinationBindingV1,
        chunks: Iterable[bytes],
    ) -> RecoveryResultV1:
        self._require_posix()
        self._validate_authority(root_authority)
        if type(create_authority) is not LocalCreateAuthorityV1 or type(destination) is not LocalDestinationBindingV1:
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        issued = self._live_create.pop(create_authority.authority_ref, None)
        if issued != (create_authority, destination):
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)
        if (
            create_authority.root_authority_digest != root_authority.authority_digest
            or create_authority.destination_digest != destination.destination_digest
            or destination.authority_digest != root_authority.authority_digest
        ):
            raise _closed(LocalIOCodeV1.AUTHORITY_INVALID)

        staging_name = ".synaptic-" + create_authority.mutation_id[:32]
        claimed = _journal_record(
            mutation_id=create_authority.mutation_id,
            destination_digest=destination.destination_digest,
            phase=CreatePhaseV1.CLAIMED,
            previous=None,
            staging_name=staging_name,
            identity=None,
        )
        try:
            if self._append_phase(root_authority, claimed) is not JournalPublishStatusV1.PUBLISHED:
                return self.recover_create(root_authority, destination)
        except LocalIOErrorV1:
            return RecoveryResultV1(RecoveryStatusV1.INDETERMINATE, create_authority.mutation_id)

        self._active_mutations.add(create_authority.mutation_id)
        parent: RetainedDirectoryV1 | None = None
        directories: list[RetainedDirectoryV1] = []
        opened: OpenFileV1 | None = None
        try:
            parent, final_name, directories = self._open_parent(root_authority, destination.relative_path)
            if self._reject_collision(parent, final_name, may_be_missing=True):
                return RecoveryResultV1(RecoveryStatusV1.CONFLICT, create_authority.mutation_id)
            if self._reject_collision(parent, staging_name, may_be_missing=True):
                return RecoveryResultV1(RecoveryStatusV1.CONFLICT, create_authority.mutation_id)

            opened = self._port.create_exclusive_at(parent, staging_name)
            if type(opened) is not OpenFileV1 or not _is_regular_single(opened.identity):
                raise _closed(LocalIOCodeV1.IO_FAILED)
            digest = hashlib.sha256()
            total = 0
            try:
                for chunk in chunks:
                    if type(chunk) is not bytes or not chunk or len(chunk) > MAX_CHUNK_BYTES:
                        raise _closed(LocalIOCodeV1.STREAM_INVALID)
                    total += len(chunk)
                    if total > destination.expected_size:
                        raise _closed(LocalIOCodeV1.STREAM_INVALID)
                    digest.update(chunk)
                    offset = 0
                    while offset < len(chunk):
                        written = self._port.write(opened, chunk[offset:])
                        if type(written) is not int or not 0 < written <= len(chunk) - offset:
                            raise _closed(LocalIOCodeV1.IO_FAILED)
                        offset += written
            except LocalIOErrorV1:
                raise
            except BaseException:
                raise _closed(LocalIOCodeV1.STREAM_INVALID) from None
            if total != destination.expected_size or digest.hexdigest() != destination.expected_sha256:
                raise _closed(LocalIOCodeV1.STREAM_INVALID)
            self._port.fsync_file(opened)
            self._port.close_file(opened)
            opened = None

            verified = self._port.open_read_at(parent, staging_name)
            try:
                size, sha256, durable_identity = self._read_opened(
                    verified, maximum_bytes=destination.expected_size
                )
            finally:
                self._port.close_file(verified)
            if size != destination.expected_size or sha256 != destination.expected_sha256:
                raise _closed(LocalIOCodeV1.STREAM_INVALID)
            file_durable = _journal_record(
                mutation_id=create_authority.mutation_id,
                destination_digest=destination.destination_digest,
                phase=CreatePhaseV1.FILE_DURABLE,
                previous=claimed,
                staging_name=staging_name,
                identity=durable_identity,
            )
            if self._append_phase(root_authority, file_durable) is not JournalPublishStatusV1.PUBLISHED:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)

            self._port.link_at(parent, staging_name, final_name)
            self._port.fsync_directory(parent)
            final_linked = self._port.stat_at(parent, final_name)
            staging_linked = self._port.stat_at(parent, staging_name)
            if (
                type(final_linked) is not LocalFileIdentityV1
                or type(staging_linked) is not LocalFileIdentityV1
                or not _same_node(final_linked, staging_linked)
                or final_linked.nlink != 2
                or final_linked.changed_ns < durable_identity.changed_ns
            ):
                raise _closed(LocalIOCodeV1.IO_FAILED)
            linked = _journal_record(
                mutation_id=create_authority.mutation_id,
                destination_digest=destination.destination_digest,
                phase=CreatePhaseV1.LINKED,
                previous=file_durable,
                staging_name=staging_name,
                identity=final_linked,
            )
            if self._append_phase(root_authority, linked) is not JournalPublishStatusV1.PUBLISHED:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)

            self._port.unlink_at(parent, staging_name)
            self._port.fsync_directory(parent)
            final_identity = self._port.stat_at(parent, final_name)
            if type(final_identity) is not LocalFileIdentityV1 or not _is_regular_single(final_identity):
                raise _closed(LocalIOCodeV1.IO_FAILED)
            if final_identity.changed_ns < final_linked.changed_ns:
                raise _closed(LocalIOCodeV1.IO_FAILED)
            committed = _journal_record(
                mutation_id=create_authority.mutation_id,
                destination_digest=destination.destination_digest,
                phase=CreatePhaseV1.COMMITTED,
                previous=linked,
                staging_name=staging_name,
                identity=final_identity,
            )
            if self._append_phase(root_authority, committed) is not JournalPublishStatusV1.PUBLISHED:
                raise _closed(LocalIOCodeV1.JOURNAL_INVALID)
            artifact = LocalArtifactBindingV1(
                destination.destination_digest,
                destination.relative_path,
                destination.role,
                destination.expected_size,
                destination.expected_sha256,
                final_identity,
            )
            return validate_recovery_result_v1(
                RecoveryResultV1(
                    RecoveryStatusV1.FOUND,
                    create_authority.mutation_id,
                    artifact,
                ),
                mutation_id=create_authority.mutation_id,
                destination=destination,
            )
        except BaseException:
            return RecoveryResultV1(RecoveryStatusV1.INDETERMINATE, create_authority.mutation_id)
        finally:
            if opened is not None:
                try:
                    self._port.close_file(opened)
                except BaseException:
                    pass
            self._close_directories(directories)
            self._active_mutations.discard(create_authority.mutation_id)

    def _validated_journal(
        self,
        root_authority: LocalRootAuthorityV1,
        destination: LocalDestinationBindingV1,
        mutation_id: str,
    ) -> tuple[CreateJournalRecordV1, ...] | RecoveryStatusV1:
        try:
            snapshot = self._port.snapshot_journal(
                root_authority.control_directory, mutation_id, MAX_JOURNAL_RECORDS + 1
            )
        except BaseException:
            return RecoveryStatusV1.INDETERMINATE
        if type(snapshot) is not JournalSnapshotV1 or snapshot.mutation_id != mutation_id:
            return RecoveryStatusV1.CONFLICT
        if snapshot.status is JournalSnapshotStatusV1.CONFLICT:
            return RecoveryStatusV1.CONFLICT
        if snapshot.status is JournalSnapshotStatusV1.INDETERMINATE:
            return RecoveryStatusV1.INDETERMINATE
        records = snapshot.records
        expected_snapshot = digest_v1({
            "mutation_id": mutation_id,
            "record_digests": [record.record_digest for record in records],
            "status": snapshot.status.value,
        })
        if snapshot.snapshot_digest != expected_snapshot or len(records) > MAX_JOURNAL_RECORDS:
            return RecoveryStatusV1.CONFLICT
        previous: CreateJournalRecordV1 | None = None
        for index, record in enumerate(records):
            if (
                type(record) is not CreateJournalRecordV1
                or record.sequence != index
                or record.phase is not list(CreatePhaseV1)[index]
                or record.mutation_id != mutation_id
                or record.destination_digest != destination.destination_digest
                or record.staging_name != ".synaptic-" + mutation_id[:32]
                or record.previous_digest != (None if previous is None else previous.record_digest)
                or record.record_digest != digest_v1(record.canonical_without_digest())
                or (previous is not None and record.staging_name != previous.staging_name)
            ):
                return RecoveryStatusV1.CONFLICT
            if previous is not None and previous.file_identity is not None:
                if record.file_identity is None or not _same_node(previous.file_identity, record.file_identity):
                    return RecoveryStatusV1.CONFLICT
            if record.phase is CreatePhaseV1.FILE_DURABLE:
                if record.file_identity is None or not _is_regular_single(record.file_identity):
                    return RecoveryStatusV1.CONFLICT
            elif record.phase is CreatePhaseV1.LINKED:
                if (
                    record.file_identity is None
                    or not stat.S_ISREG(record.file_identity.mode)
                    or record.file_identity.nlink != 2
                    or previous is None
                    or previous.file_identity is None
                    or record.file_identity.changed_ns < previous.file_identity.changed_ns
                ):
                    return RecoveryStatusV1.CONFLICT
            elif record.phase is CreatePhaseV1.COMMITTED:
                if (
                    record.file_identity is None
                    or not _is_regular_single(record.file_identity)
                    or previous is None
                    or previous.file_identity is None
                    or record.file_identity.changed_ns < previous.file_identity.changed_ns
                ):
                    return RecoveryStatusV1.CONFLICT
            previous = record
        return records

    def _verify_final(
        self,
        parent: RetainedDirectoryV1,
        final_name: str,
        destination: LocalDestinationBindingV1,
    ) -> LocalFileIdentityV1 | None:
        opened: OpenFileV1 | None = None
        try:
            opened = self._port.open_read_at(parent, final_name)
            size, sha256, identity = self._read_opened(
                opened,
                maximum_bytes=destination.expected_size,
                require_single_link=False,
            )
            if size != destination.expected_size or sha256 != destination.expected_sha256:
                return None
            return identity
        except BaseException:
            return None
        finally:
            if opened is not None:
                try:
                    self._port.close_file(opened)
                except BaseException:
                    pass

    def recover_create(
        self,
        root_authority: LocalRootAuthorityV1,
        destination: LocalDestinationBindingV1,
    ) -> RecoveryResultV1:
        self._require_posix()
        self._validate_authority(root_authority)
        if type(destination) is not LocalDestinationBindingV1 or destination.authority_digest != root_authority.authority_digest:
            raise _closed(LocalIOCodeV1.DESTINATION_INVALID)
        mutation_id = digest_v1({
            "destination_digest": destination.destination_digest,
            "root_authority_digest": root_authority.authority_digest,
        })
        if mutation_id in self._active_mutations:
            return RecoveryResultV1(RecoveryStatusV1.ACTIVE, mutation_id)
        records = self._validated_journal(root_authority, destination, mutation_id)
        if type(records) is RecoveryStatusV1:
            return RecoveryResultV1(records, mutation_id)
        latest = None if not records else records[-1]
        parent: RetainedDirectoryV1 | None = None
        directories: list[RetainedDirectoryV1] = []
        try:
            parent, final_name, directories = self._open_parent(root_authority, destination.relative_path)
            self._reject_collision(parent, final_name, may_be_missing=True)
            final_identity = self._port.stat_at(parent, final_name)
            staging_name = (
                ".synaptic-" + mutation_id[:32]
                if latest is None
                else latest.staging_name
            )
            self._reject_collision(parent, staging_name, may_be_missing=True)
            staging_identity = self._port.stat_at(parent, staging_name)
            if latest is None:
                status = (
                    RecoveryStatusV1.DEFINITELY_ABSENT
                    if final_identity is None and staging_identity is None
                    else RecoveryStatusV1.CONFLICT
                )
                return validate_recovery_result_v1(
                    RecoveryResultV1(status, mutation_id),
                    mutation_id=mutation_id,
                    destination=destination,
                )
            if latest.phase is CreatePhaseV1.CLAIMED:
                # A durable claim can belong to an owner that is live in another
                # reconstructed composition.  Absence of materialization is not
                # proof that the admitted mutation will not proceed.
                if final_identity is not None:
                    return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
                if staging_identity is None:
                    return RecoveryResultV1(RecoveryStatusV1.INDETERMINATE, mutation_id)
                return RecoveryResultV1(
                    RecoveryStatusV1.INDETERMINATE
                    if _is_regular_single(staging_identity)
                    else RecoveryStatusV1.CONFLICT,
                    mutation_id,
                )
            if latest.phase is CreatePhaseV1.FILE_DURABLE:
                evidence = latest.file_identity
                if evidence is None:
                    return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
                if final_identity is None:
                    status = (
                        RecoveryStatusV1.INDETERMINATE
                        if staging_identity == evidence
                        else RecoveryStatusV1.CONFLICT
                    )
                    return RecoveryResultV1(status, mutation_id)
                if staging_identity is None:
                    return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
                valid_unrecorded_link = (
                    _same_node(evidence, final_identity)
                    and _same_node(final_identity, staging_identity)
                    and final_identity == staging_identity
                    and final_identity.nlink == 2
                    and final_identity.changed_ns >= evidence.changed_ns
                )
                return RecoveryResultV1(
                    RecoveryStatusV1.INDETERMINATE if valid_unrecorded_link else RecoveryStatusV1.CONFLICT,
                    mutation_id,
                )
            if final_identity is None:
                return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
            if latest.file_identity is None or not _same_node(latest.file_identity, final_identity):
                return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
            if latest.phase is CreatePhaseV1.LINKED:
                if staging_identity is not None:
                    if (
                        staging_identity != final_identity
                        or final_identity != latest.file_identity
                        or final_identity.nlink != 2
                    ):
                        return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
                    return RecoveryResultV1(RecoveryStatusV1.INDETERMINATE, mutation_id)
                if (
                    not _is_regular_single(final_identity)
                    or final_identity.changed_ns < latest.file_identity.changed_ns
                ):
                    return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
            elif (
                staging_identity is not None
                or not _is_regular_single(final_identity)
                or final_identity != latest.file_identity
            ):
                return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
            verified = self._verify_final(parent, final_name, destination)
            if verified is None or verified != final_identity:
                return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
            artifact = LocalArtifactBindingV1(
                destination.destination_digest,
                destination.relative_path,
                destination.role,
                destination.expected_size,
                destination.expected_sha256,
                verified,
            )
            return validate_recovery_result_v1(
                RecoveryResultV1(RecoveryStatusV1.FOUND, mutation_id, artifact),
                mutation_id=mutation_id,
                destination=destination,
            )
        except LocalIOErrorV1:
            return RecoveryResultV1(RecoveryStatusV1.CONFLICT, mutation_id)
        except BaseException:
            return RecoveryResultV1(RecoveryStatusV1.INDETERMINATE, mutation_id)
        finally:
            self._close_directories(directories)
