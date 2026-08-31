"""Concrete retained-dirfd POSIX adapter for host local I/O v1."""

from __future__ import annotations

import os
import errno
import re
import secrets
import stat
import sys
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .filesystem import MAX_DIRECTORY_ENTRIES, OpenFileV1
from .model import (
    LocalAdmissionRootNodeV1,
    CapabilityStatusV1,
    CreateJournalRecordV1,
    JournalPublishResultV1,
    JournalPublishStatusV1,
    JournalSnapshotStatusV1,
    JournalSnapshotV1,
    LocalFileIdentityV1,
    LocalFilesystemCapabilityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    RetainedDirectoryAdmissionV1,
    RetainedDirectoryV1,
    canonical_relative_components_v1,
    canonical_posix_root_component_v1,
    checked_sha256,
    digest_v1,
    journal_record_bytes_v1,
    parse_journal_record_v1,
)

try:
    import fcntl as _fcntl
except ImportError:  # native Windows remains metadata-only
    _fcntl = None


@dataclass(slots=True)
class _LiveDirectoryAdmissionV1:
    lease: RetainedDirectoryAdmissionV1
    directory: RetainedDirectoryV1
    descriptor: int
    root_key: tuple[int, int, int, str]
    state: str = "ACTIVE"


_FEATURES = tuple(sorted((
    "crash-released-admission",
    "directory-inode-admission",
    "dirfd-open", "dirfd-stat", "exclusive-create", "fsync",
    "exec-closed-admission",
    "hardlink-at", "nofollow", "retained-handles", "scandir-fd",
    "nonblocking-directory-flock",
)))


def detect_posix_capability_v1(
    *, platform_name: str | None = None, os_name: str | None = None
) -> LocalFilesystemCapabilityV1:
    platform_value = sys.platform if platform_name is None else platform_name
    os_value = os.name if os_name is None else os_name
    family = "windows" if platform_value.startswith("win") or os_value == "nt" else (
        "posix" if os_value == "posix" else "other"
    )
    available = False
    if family == "posix" and platform_value.startswith("linux"):
        required = (
            "close", "fstat", "fsync", "getpid", "link", "mkdir", "open",
            "register_at_fork", "scandir", "stat", "unlink",
        )
        dirfd_functions = tuple(
            getattr(os, name, None) for name in ("open", "stat", "link", "unlink", "mkdir")
        )
        supports_dir_fd = getattr(os, "supports_dir_fd", ())
        supports_follow_symlinks = getattr(os, "supports_follow_symlinks", ())
        available = (
            all(callable(getattr(os, name, None)) for name in required)
            and all(type(getattr(os, name, None)) is int for name in (
                "O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_RDONLY",
            ))
            and all(function in supports_dir_fd for function in dirfd_functions)
            and os.stat in supports_follow_symlinks
            and os.link in supports_follow_symlinks
            and _fcntl is not None
            and callable(getattr(_fcntl, "flock", None))
            and type(getattr(_fcntl, "LOCK_EX", None)) is int
            and type(getattr(_fcntl, "LOCK_NB", None)) is int
        )
    status = CapabilityStatusV1.AVAILABLE if available else CapabilityStatusV1.UNAVAILABLE
    features = _FEATURES if available else ()
    canonical = {"features": list(features), "platform_family": family, "status": status.value}
    return LocalFilesystemCapabilityV1(family, status, features, digest_v1(canonical))


class PosixRetainedDirfdPortV1:
    """Real adapter whose effects remain relative to authenticated live handles."""

    def __init__(self) -> None:
        self.capability = detect_posix_capability_v1()
        if self.capability.status is not CapabilityStatusV1.AVAILABLE:
            raise LocalIOErrorV1(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
        self._directories: dict[str, tuple[int, RetainedDirectoryV1]] = {}
        self._files: dict[str, tuple[int, OpenFileV1]] = {}
        self._journal_lock = threading.Lock()
        self._admission_process_id = os.getpid()
        self._admission_process_ref = "process-" + secrets.token_hex(16)
        self.__fork_invalid = False
        def after_fork_child() -> None:
            self.__fork_invalid = True
            for descriptor in self.__admission_fd_snapshot:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            self.__admission_leases = {}
            self.__admission_fd_snapshot = ()
            self.__admission_lock = threading.Lock()

        os.register_at_fork(after_in_child=after_fork_child)
        self.__admission_leases: dict[str, _LiveDirectoryAdmissionV1] = {}
        self.__admission_fd_snapshot: tuple[int, ...] = ()
        self.__admission_lock = threading.Lock()

    def _require_construction_process(self) -> None:
        try:
            current_pid = os.getpid()
        except BaseException:
            raise self._closed(LocalIOCodeV1.CAPABILITY_UNAVAILABLE) from None
        if self.__fork_invalid or current_pid != self._admission_process_id:
            raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)

    @staticmethod
    def _closed(code: LocalIOCodeV1 = LocalIOCodeV1.IO_FAILED) -> LocalIOErrorV1:
        return LocalIOErrorV1(code)

    @staticmethod
    def _identity(value: os.stat_result) -> LocalFileIdentityV1:
        return LocalFileIdentityV1(
            device=int(value.st_dev), inode=int(value.st_ino), mode=int(value.st_mode),
            nlink=int(value.st_nlink), changed_ns=int(value.st_ctime_ns),
            modified_ns=int(value.st_mtime_ns), size=int(value.st_size),
        )

    @staticmethod
    def _component(value: str) -> str:
        try:
            parts = canonical_relative_components_v1(value)
        except LocalIOErrorV1:
            raise LocalIOErrorV1(LocalIOCodeV1.PATH_INVALID) from None
        if len(parts) != 1:
            raise LocalIOErrorV1(LocalIOCodeV1.PATH_INVALID)
        return parts[0]

    @staticmethod
    def _root_component(directory_fd: int, value: str) -> str:
        try:
            component = canonical_posix_root_component_v1(value)
            names: list[str] = []
            with os.scandir(directory_fd) as entries:
                for entry in entries:
                    names.append(canonical_posix_root_component_v1(entry.name))
                    if len(names) > MAX_DIRECTORY_ENTRIES:
                        raise LocalIOErrorV1(LocalIOCodeV1.LIMIT_EXCEEDED)
        except LocalIOErrorV1:
            raise
        except OSError:
            raise LocalIOErrorV1(LocalIOCodeV1.ROOT_CHANGED) from None
        folded = unicodedata.normalize("NFC", component).casefold()
        matches = [name for name in names if unicodedata.normalize("NFC", name).casefold() == folded]
        if matches != [component]:
            raise LocalIOErrorV1(LocalIOCodeV1.ROOT_CHANGED)
        return component

    @staticmethod
    def _same_retained_node(left: LocalFileIdentityV1, right: LocalFileIdentityV1) -> bool:
        return (left.device, left.inode, left.mode) == (right.device, right.inode, right.mode)

    def _directory(self, value: RetainedDirectoryV1) -> int:
        self._require_construction_process()
        if type(value) is not RetainedDirectoryV1:
            raise self._closed(LocalIOCodeV1.AUTHORITY_INVALID)
        retained = self._directories.get(value.handle_ref)
        if retained is None or retained[1] is not value:
            raise self._closed(LocalIOCodeV1.AUTHORITY_INVALID)
        try:
            current = self._identity(os.fstat(retained[0]))
        except OSError:
            raise self._closed() from None
        if not self._same_retained_node(value.identity, current) or not stat.S_ISDIR(current.mode):
            raise self._closed(LocalIOCodeV1.AUTHORITY_INVALID)
        return retained[0]

    def _file(self, value: OpenFileV1) -> int:
        self._require_construction_process()
        if type(value) is not OpenFileV1:
            raise self._closed(LocalIOCodeV1.AUTHORITY_INVALID)
        retained = self._files.get(value.handle_ref)
        if retained is None or retained[1] is not value:
            raise self._closed(LocalIOCodeV1.AUTHORITY_INVALID)
        return retained[0]

    def _retain_dirfd(self, descriptor: int) -> RetainedDirectoryV1:
        try:
            identity = self._identity(os.fstat(descriptor))
            if not stat.S_ISDIR(identity.mode) or stat.S_ISLNK(identity.mode):
                raise self._closed(LocalIOCodeV1.ROOT_INVALID)
            handle = "dir-" + secrets.token_hex(16)
            result = RetainedDirectoryV1(handle, identity)
            self._directories[handle] = (descriptor, result)
            return result
        except LocalIOErrorV1:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
        except OSError:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise self._closed() from None

    def _retain_file(self, descriptor: int) -> OpenFileV1:
        try:
            identity = self._identity(os.fstat(descriptor))
            handle = "file-" + secrets.token_hex(16)
            result = OpenFileV1(handle, identity)
            self._files[handle] = (descriptor, result)
            return result
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise self._closed() from None

    def retain_directory(self, absolute_path: Path) -> RetainedDirectoryV1:
        self._require_construction_process()
        if not isinstance(absolute_path, Path) or not absolute_path.is_absolute():
            raise self._closed(LocalIOCodeV1.ROOT_INVALID)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
        current: int | None = None
        try:
            parts = absolute_path.parts
            if not parts or parts[0] != "/":
                raise self._closed(LocalIOCodeV1.ROOT_INVALID)
            current = os.open("/", flags)
            for component in parts[1:]:
                checked = self._root_component(current, component)
                before = self._identity(os.stat(checked, dir_fd=current, follow_symlinks=False))
                if not stat.S_ISDIR(before.mode) or stat.S_ISLNK(before.mode):
                    raise self._closed(LocalIOCodeV1.ROOT_CHANGED)
                child = os.open(checked, flags, dir_fd=current)
                opened = self._identity(os.fstat(child))
                after = self._identity(os.stat(checked, dir_fd=current, follow_symlinks=False))
                if opened != before or after != before:
                    os.close(child)
                    raise self._closed(LocalIOCodeV1.ROOT_CHANGED)
                os.close(current)
                current = child
            retained_fd = current
            current = None
            result = self._retain_dirfd(retained_fd)
            return result
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed(LocalIOCodeV1.ROOT_INVALID) from None
        finally:
            if current is not None:
                try:
                    os.close(current)
                except OSError:
                    pass

    def open_directory_at(self, directory: RetainedDirectoryV1, component: str) -> RetainedDirectoryV1:
        descriptor = self._directory(directory)
        name = self._component(component)
        try:
            child = os.open(
                name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            return self._retain_dirfd(child)
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed(LocalIOCodeV1.PATH_INVALID) from None

    def close_directory(self, directory: RetainedDirectoryV1) -> None:
        descriptor = self._directory(directory)
        del self._directories[directory.handle_ref]
        try:
            os.close(descriptor)
        except OSError:
            raise self._closed() from None

    def list_names_at(self, directory: RetainedDirectoryV1, maximum: int) -> tuple[str, ...]:
        descriptor = self._directory(directory)
        if type(maximum) is not int or not 0 <= maximum <= MAX_DIRECTORY_ENTRIES + 1:
            raise self._closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        names: list[str] = []
        try:
            with os.scandir(descriptor) as entries:
                for entry in entries:
                    names.append(entry.name)
                    if len(names) > maximum:
                        break
            return tuple(names)
        except OSError:
            raise self._closed() from None

    def stat_at(self, directory: RetainedDirectoryV1, component: str) -> LocalFileIdentityV1 | None:
        descriptor = self._directory(directory)
        name = self._component(component)
        try:
            return self._identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False))
        except FileNotFoundError:
            return None
        except OSError:
            raise self._closed() from None

    def open_read_at(self, directory: RetainedDirectoryV1, component: str) -> OpenFileV1:
        descriptor = self._directory(directory)
        name = self._component(component)
        try:
            opened = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=descriptor)
            return self._retain_file(opened)
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed(LocalIOCodeV1.SOURCE_INVALID) from None

    def create_exclusive_at(self, directory: RetainedDirectoryV1, component: str) -> OpenFileV1:
        descriptor = self._directory(directory)
        name = self._component(component)
        try:
            opened = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                0o600,
                dir_fd=descriptor,
            )
            return self._retain_file(opened)
        except FileExistsError:
            raise self._closed(LocalIOCodeV1.DESTINATION_EXISTS) from None
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed() from None

    @staticmethod
    def _admission_node(value: os.stat_result) -> LocalAdmissionRootNodeV1:
        file_type = stat.S_IFMT(int(value.st_mode))
        body = {"device": int(value.st_dev), "file_type": file_type,
                "inode": int(value.st_ino),
                "schema": "synaptic-host-admission-root-node/v1"}
        return LocalAdmissionRootNodeV1(
            int(value.st_dev), int(value.st_ino), file_type, digest_v1(body)
        )

    @staticmethod
    def _admission_root_key(
        node: LocalAdmissionRootNodeV1,
    ) -> tuple[int, int, int, str]:
        return node.device, node.inode, node.file_type, node.node_digest

    def _refresh_admission_fd_snapshot_locked(self) -> None:
        self.__admission_fd_snapshot = tuple(
            value.descriptor for value in self.__admission_leases.values()
            if value.state in {"ACTIVE", "RELEASING"}
        )

    def acquire_directory_admission(
        self, directory: RetainedDirectoryV1
    ) -> RetainedDirectoryAdmissionV1:
        self._require_construction_process()
        directory_fd = self._directory(directory)
        descriptor: int | None = None
        try:
            retained_node = self._admission_node(os.fstat(directory_fd))
        except OSError:
            raise self._closed(LocalIOCodeV1.IO_FAILED) from None
        try:
            descriptor = os.open(
                ".", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=directory_fd,
            )
            opened_node = self._admission_node(os.fstat(descriptor))
            if opened_node != retained_node:
                raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
            try:
                _fcntl.flock(descriptor, _fcntl.LOCK_EX | _fcntl.LOCK_NB)
            except OSError as error:
                if error.errno in {errno.EAGAIN, errno.EWOULDBLOCK}:
                    raise self._closed(LocalIOCodeV1.ROOT_IN_USE) from None
                raise self._closed(LocalIOCodeV1.IO_FAILED) from None
            if self._admission_node(os.fstat(descriptor)) != retained_node:
                raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
            lease_ref = "directory-admission-" + secrets.token_hex(16)
            body = {"lease_ref": lease_ref, "root_node_digest": retained_node.node_digest,
                    "process_id": self._admission_process_id,
                    "process_instance_ref": self._admission_process_ref,
                    "schema": "synaptic-host-retained-directory-admission/v1"}
            lease = RetainedDirectoryAdmissionV1(
                lease_ref, retained_node, self._admission_process_id,
                self._admission_process_ref, digest_v1(body),
            )
            with self.__admission_lock:
                if any(
                    value.root_key == self._admission_root_key(retained_node)
                    and value.state in {"ACTIVE", "RELEASING"}
                    for value in self.__admission_leases.values()
                ):
                    raise self._closed(LocalIOCodeV1.ROOT_IN_USE)
                self.__admission_leases[lease_ref] = _LiveDirectoryAdmissionV1(
                    lease,
                    directory,
                    descriptor,
                    self._admission_root_key(retained_node),
                )
                self._refresh_admission_fd_snapshot_locked()
            descriptor = None
            return lease
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed(LocalIOCodeV1.IO_FAILED) from None
        except BaseException:
            raise self._closed(LocalIOCodeV1.IO_FAILED) from None
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def validate_directory_admission(
        self, directory: RetainedDirectoryV1, lease: RetainedDirectoryAdmissionV1
    ) -> RetainedDirectoryAdmissionV1:
        self._require_construction_process()
        if type(directory) is not RetainedDirectoryV1 or type(lease) is not RetainedDirectoryAdmissionV1:
            raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
        with self.__admission_lock:
            live = self.__admission_leases.get(lease.lease_ref)
            if (
                live is None
                or live.state != "ACTIVE"
                or live.lease is not lease
                or live.directory is not directory
            ):
                raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
            try:
                directory_fd = self._directory(directory)
                if (
                    self._admission_node(os.fstat(directory_fd))
                    != lease.root_node
                    or self._admission_node(os.fstat(live.descriptor))
                    != lease.root_node
                ):
                    raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
            except OSError:
                raise self._closed(LocalIOCodeV1.IO_FAILED) from None
        return lease

    def release_directory_admission(
        self, directory: RetainedDirectoryV1, lease: RetainedDirectoryAdmissionV1
    ) -> None:
        self._require_construction_process()
        if type(directory) is not RetainedDirectoryV1 or type(lease) is not RetainedDirectoryAdmissionV1:
            raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
        with self.__admission_lock:
            live = self.__admission_leases.get(lease.lease_ref)
            if (
                live is None
                or live.state != "ACTIVE"
                or live.lease is not lease
                or live.directory is not directory
            ):
                raise self._closed(LocalIOCodeV1.ADMISSION_INVALID)
            self._directory(directory)
            live.state = "RELEASING"
        failed = False
        try:
            os.close(live.descriptor)
        except OSError:
            failed = True
        finally:
            with self.__admission_lock:
                current = self.__admission_leases.get(lease.lease_ref)
                if current is live:
                    live.state = "RELEASED_WITH_FAILURE" if failed else "RELEASED"
                    del self.__admission_leases[lease.lease_ref]
                    self._refresh_admission_fd_snapshot_locked()
        if failed:
            raise self._closed(LocalIOCodeV1.ADMISSION_RELEASE_FAILED)

    def mkdir_at(self, directory: RetainedDirectoryV1, component: str) -> bool:
        descriptor = self._directory(directory)
        name = self._component(component)
        try:
            os.mkdir(name, 0o700, dir_fd=descriptor)
            return True
        except FileExistsError:
            return False
        except OSError:
            raise self._closed() from None

    def read(self, file: OpenFileV1, maximum: int) -> bytes:
        descriptor = self._file(file)
        if type(maximum) is not int or not 0 < maximum <= 1_048_576:
            raise self._closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        try:
            return os.read(descriptor, maximum)
        except OSError:
            raise self._closed() from None

    def write(self, file: OpenFileV1, payload: bytes) -> int:
        descriptor = self._file(file)
        if type(payload) is not bytes or not payload or len(payload) > 1_048_576:
            raise self._closed(LocalIOCodeV1.STREAM_INVALID)
        try:
            return os.write(descriptor, payload)
        except OSError:
            raise self._closed() from None

    def stat_file(self, file: OpenFileV1) -> LocalFileIdentityV1:
        try:
            return self._identity(os.fstat(self._file(file)))
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed() from None

    def close_file(self, file: OpenFileV1) -> None:
        descriptor = self._file(file)
        del self._files[file.handle_ref]
        try:
            os.close(descriptor)
        except OSError:
            raise self._closed() from None

    def fsync_file(self, file: OpenFileV1) -> None:
        try:
            os.fsync(self._file(file))
        except OSError:
            raise self._closed() from None

    def fsync_directory(self, directory: RetainedDirectoryV1) -> None:
        try:
            os.fsync(self._directory(directory))
        except OSError:
            raise self._closed() from None

    def link_at(self, directory: RetainedDirectoryV1, source: str, destination: str) -> None:
        descriptor = self._directory(directory)
        source_name, destination_name = self._component(source), self._component(destination)
        try:
            os.link(
                source_name, destination_name, src_dir_fd=descriptor,
                dst_dir_fd=descriptor, follow_symlinks=False,
            )
        except FileExistsError:
            raise self._closed(LocalIOCodeV1.DESTINATION_EXISTS) from None
        except OSError:
            raise self._closed() from None

    def unlink_at(self, directory: RetainedDirectoryV1, component: str) -> None:
        try:
            os.unlink(self._component(component), dir_fd=self._directory(directory))
        except OSError:
            raise self._closed() from None

    def _journal_name(self, mutation_id: str) -> str:
        checked_sha256(mutation_id, LocalIOCodeV1.JOURNAL_INVALID)
        return ".journal-" + mutation_id

    def _open_journal_dir(self, control: RetainedDirectoryV1, mutation_id: str, *, create: bool) -> int | None:
        control_fd = self._directory(control)
        name = self._journal_name(mutation_id)
        if create:
            created = False
            try:
                os.mkdir(name, 0o700, dir_fd=control_fd)
                created = True
            except FileExistsError:
                pass
            except OSError:
                raise self._closed() from None
            if created:
                try:
                    os.fsync(control_fd)
                except OSError:
                    raise self._closed() from None
        try:
            return os.open(
                name, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=control_fd,
            )
        except FileNotFoundError:
            return None
        except OSError:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID) from None

    @staticmethod
    def _record_name(record: CreateJournalRecordV1) -> str:
        return f"{record.sequence}-{record.phase.value}.json"

    def _read_record_at(self, directory_fd: int, name: str) -> CreateJournalRecordV1:
        descriptor: int | None = None
        reopened: int | None = None
        try:
            descriptor = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory_fd)
            info = self._identity(os.fstat(descriptor))
            if not stat.S_ISREG(info.mode) or info.nlink != 1 or info.size > 16_384:
                raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(4096, 16_385 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > 16_384:
                    raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
            after = self._identity(os.fstat(descriptor))
            logical = self._identity(os.stat(name, dir_fd=directory_fd, follow_symlinks=False))
            if after != info or logical != info:
                raise self._closed(LocalIOCodeV1.JOURNAL_CONFLICT)
            payload = b"".join(chunks)
            reopened = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory_fd)
            reopened_info = self._identity(os.fstat(reopened))
            if reopened_info != info:
                raise self._closed(LocalIOCodeV1.JOURNAL_CONFLICT)
            replay_chunks: list[bytes] = []
            replay_total = 0
            while True:
                chunk = os.read(reopened, min(4096, 16_385 - replay_total))
                if not chunk:
                    break
                replay_chunks.append(chunk)
                replay_total += len(chunk)
                if replay_total > 16_384:
                    raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
            replay_after = self._identity(os.fstat(reopened))
            replay_logical = self._identity(os.stat(name, dir_fd=directory_fd, follow_symlinks=False))
            if replay_after != info or replay_logical != info or b"".join(replay_chunks) != payload:
                raise self._closed(LocalIOCodeV1.JOURNAL_CONFLICT)
            return parse_journal_record_v1(payload)
        except LocalIOErrorV1:
            raise
        except OSError:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID) from None
        finally:
            if reopened is not None:
                try:
                    os.close(reopened)
                except OSError:
                    pass
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass

    def _read_journal_fd(
        self, directory_fd: int, maximum: int
    ) -> tuple[tuple[CreateJournalRecordV1, ...], bool]:
        names: list[str] = []
        try:
            with os.scandir(directory_fd) as entries:
                for entry in entries:
                    names.append(entry.name)
                    if len(names) > maximum + 4:
                        raise self._closed(LocalIOCodeV1.LIMIT_EXCEEDED)
        except OSError:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID) from None
        names.sort()
        private = [name for name in names if re.fullmatch(r"\.private-[0-9a-f]{32}", name)]
        canonical = [name for name in names if name not in private]
        if len(private) > 4 or len(canonical) > maximum or len(names) > maximum + 4:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
        records = tuple(self._read_record_at(directory_fd, name) for name in canonical)
        if canonical != [self._record_name(record) for record in records]:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
        return records, bool(private)

    @staticmethod
    def _publish_result(
        status: JournalPublishStatusV1, record: CreateJournalRecordV1
    ) -> JournalPublishResultV1:
        return JournalPublishResultV1(
            status, record.mutation_id, record.record_digest, record
        )

    def publish_journal(
        self,
        control: RetainedDirectoryV1,
        mutation_id: str,
        expected_previous_digest: str | None,
        record: CreateJournalRecordV1,
    ) -> JournalPublishResultV1:
        self._require_construction_process()
        if type(record) is not CreateJournalRecordV1 or record.mutation_id != mutation_id:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
        with self._journal_lock:
            directory_fd = self._open_journal_dir(control, mutation_id, create=True)
            if directory_fd is None:
                raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
            descriptor: int | None = None
            temporary = ".private-" + secrets.token_hex(16)
            temporary_created = False
            try:
                records, has_private = self._read_journal_fd(directory_fd, 4)
                if has_private:
                    return self._publish_result(JournalPublishStatusV1.CONFLICT, record)
                previous = None if not records else records[-1].record_digest
                if previous != expected_previous_digest or len(records) != record.sequence:
                    if record.sequence < len(records) and records[record.sequence] == record:
                        return self._publish_result(JournalPublishStatusV1.EXISTS_IDENTICAL, record)
                    return self._publish_result(JournalPublishStatusV1.CONFLICT, record)
                descriptor = os.open(
                    temporary,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory_fd,
                )
                temporary_created = True
                payload = journal_record_bytes_v1(record)
                offset = 0
                while offset < len(payload):
                    written = os.write(descriptor, payload[offset:])
                    if written <= 0:
                        raise self._closed()
                    offset += written
                os.fsync(descriptor)
                os.close(descriptor)
                descriptor = None
                try:
                    os.link(
                        temporary,
                        self._record_name(record),
                        src_dir_fd=directory_fd,
                        dst_dir_fd=directory_fd,
                        follow_symlinks=False,
                    )
                    published = True
                except FileExistsError:
                    published = False
                os.fsync(directory_fd)
                os.unlink(temporary, dir_fd=directory_fd)
                temporary_created = False
                os.fsync(directory_fd)
                canonical = self._read_record_at(directory_fd, self._record_name(record))
                if canonical != record:
                    return self._publish_result(JournalPublishStatusV1.CONFLICT, record)
                return self._publish_result(
                    JournalPublishStatusV1.PUBLISHED if published else JournalPublishStatusV1.EXISTS_IDENTICAL,
                    canonical,
                )
            except LocalIOErrorV1:
                raise
            except OSError:
                raise self._closed() from None
            finally:
                if descriptor is not None:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
                if temporary_created:
                    try:
                        os.unlink(temporary, dir_fd=directory_fd)
                        os.fsync(directory_fd)
                    except OSError:
                        pass
                try:
                    os.close(directory_fd)
                except OSError:
                    pass

    def snapshot_journal(
        self, control: RetainedDirectoryV1, mutation_id: str, maximum: int
    ) -> JournalSnapshotV1:
        self._require_construction_process()
        if type(maximum) is not int or not 0 <= maximum <= 5:
            raise self._closed(LocalIOCodeV1.JOURNAL_INVALID)
        directory_fd = self._open_journal_dir(control, mutation_id, create=False)
        if directory_fd is None:
            status = JournalSnapshotStatusV1.ABSENT
            records: tuple[CreateJournalRecordV1, ...] = ()
            return JournalSnapshotV1(
                status,
                mutation_id,
                records,
                digest_v1({"mutation_id": mutation_id, "record_digests": [], "status": status.value}),
            )
        try:
            try:
                records, has_private = self._read_journal_fd(directory_fd, maximum)
            except LocalIOErrorV1:
                status = JournalSnapshotStatusV1.CONFLICT
                records = ()
            else:
                status = (
                    JournalSnapshotStatusV1.INDETERMINATE
                    if has_private or not records
                    else (JournalSnapshotStatusV1.FOUND if records else JournalSnapshotStatusV1.ABSENT)
                )
                if has_private or not records:
                    records = ()
            return JournalSnapshotV1(
                status,
                mutation_id,
                records,
                digest_v1({
                    "mutation_id": mutation_id,
                    "record_digests": [record.record_digest for record in records],
                    "status": status.value,
                }),
            )
        finally:
            try:
                os.close(directory_fd)
            except OSError:
                pass
