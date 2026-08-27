"""Retained-handle POSIX local I/O orchestration.

There is deliberately no concrete operating-system adapter here.  The host
injects a narrowly typed POSIX port; native Windows is metadata-only and fails
before the injected port can be touched.
"""

from __future__ import annotations

import hashlib
import stat
import sys
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .model import (
    CreateJournalRecordV1,
    CreatePhaseV1,
    LocalArtifactBindingV1,
    LocalFilesystemCapabilityV1,
    LocalCreateAuthorityV1,
    LocalDestinationBindingV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootAuthorityV1,
    LocalRootBindingV1,
    LocalSourceBindingV1,
    JournalPublishResultV1,
    JournalPublishStatusV1,
    JournalSnapshotStatusV1,
    JournalSnapshotV1,
    CapabilityStatusV1,
    RecoveryResultV1,
    RecoveryStatusV1,
    RetainedDirectoryV1,
    RootAccessV1,
    RootPermitAuthenticatorV1,
    canonical_relative_components_v1,
    checked_handle,
    checked_ref,
    checked_sha256,
    checked_size,
    digest_v1,
    root_authority_digest_v1,
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


def _closed(code: LocalIOCodeV1) -> LocalIOErrorV1:
    return LocalIOErrorV1(code)


def _is_directory(identity: LocalFileIdentityV1) -> bool:
    return stat.S_ISDIR(identity.mode) and not stat.S_ISLNK(identity.mode)


def _is_regular_single(identity: LocalFileIdentityV1) -> bool:
    return stat.S_ISREG(identity.mode) and not stat.S_ISLNK(identity.mode) and identity.nlink == 1


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
        self._live_create: dict[str, tuple[LocalCreateAuthorityV1, LocalDestinationBindingV1]] = {}
        self._active_mutations: set[str] = set()

    def capability(self) -> LocalFilesystemCapabilityV1:
        available = self._platform in _POSIX_PLATFORMS and self._port is not None
        platform_family = "posix" if self._platform in _POSIX_PLATFORMS else (
            "windows" if self._platform.startswith("win") else "other"
        )
        status = CapabilityStatusV1.AVAILABLE if available else CapabilityStatusV1.UNAVAILABLE
        features = (
            "descriptor_relative",
            "exclusive_create",
            "retained_dirfd",
        ) if available else ()
        canonical = {
            "features": list(features),
            "platform_family": platform_family,
            "status": status.value,
        }
        return LocalFilesystemCapabilityV1(platform_family, status, features, digest_v1(canonical))

    def _require_posix(self) -> None:
        if self._platform not in _POSIX_PLATFORMS or self._port is None:
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

    def release_root_authority(self, authority: LocalRootAuthorityV1) -> None:
        self._require_posix()
        self._validate_authority(authority)
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
