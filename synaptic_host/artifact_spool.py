"""Capability-only local staging for provider-neutral artifact publication."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from threading import Condition, RLock

from synaptic_tuner.api.v1.results import VerifiedArtifact

from .local_io_v1.filesystem import MAX_CHUNK_BYTES, MAX_DIRECTORY_ENTRIES, LocalFilesystemV1
from .local_io_v1.model import (
    BorrowPurposeV1,
    BorrowedFileV1,
    LocalFileIdentityV1,
    LocalRootBindingV1,
    RetainedRootBorrowRequestV1,
    RootAccessV1,
    SingleRootPurposeV1,
)


_FILENAME_RE = re.compile(r"^synaptic-spool-v1-[0-9a-f]{64}\.blob$")
_REF_RE = re.compile(r"^local-spool-v1:[0-9a-f]{64}$")
_SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+\-]{0,255}$")
_MAX_ARTIFACT_BYTES = 2**63 - 1


class LocalArtifactSpoolCodeV1(str, Enum):
    INVALID = "LOCAL_ARTIFACT_SPOOL_INVALID"
    CLOSED = "LOCAL_ARTIFACT_SPOOL_CLOSED"
    LIMIT_EXCEEDED = "LOCAL_ARTIFACT_SPOOL_LIMIT_EXCEEDED"
    REFERENCE_UNKNOWN = "LOCAL_ARTIFACT_SPOOL_REFERENCE_UNKNOWN"
    CONTENT_CHANGED = "LOCAL_ARTIFACT_SPOOL_CONTENT_CHANGED"
    IN_USE = "LOCAL_ARTIFACT_SPOOL_IN_USE"
    IO_FAILED = "LOCAL_ARTIFACT_SPOOL_IO_FAILED"


class LocalArtifactSpoolErrorV1(RuntimeError):
    __slots__ = ("code",)

    def __init__(self, code: LocalArtifactSpoolCodeV1) -> None:
        object.__setattr__(self, "code", code)
        RuntimeError.__init__(self, code.value)


class LocalArtifactSpoolCleanupStatusV1(str, Enum):
    CLEANED = "CLEANED"
    CLEANED_WITH_FAILURES = "CLEANED_WITH_FAILURES"


@dataclass(frozen=True, slots=True)
class LocalArtifactSpoolCleanupResultV1:
    status: LocalArtifactSpoolCleanupStatusV1
    failure_codes: tuple[LocalArtifactSpoolCodeV1, ...]
    result_digest: str

    def __post_init__(self) -> None:
        if (
            type(self.status) is not LocalArtifactSpoolCleanupStatusV1
            or type(self.failure_codes) is not tuple
            or any(type(item) is not LocalArtifactSpoolCodeV1 for item in self.failure_codes)
            or self.failure_codes != tuple(sorted(self.failure_codes, key=lambda item: item.value))
            or self.status is LocalArtifactSpoolCleanupStatusV1.CLEANED
            and self.failure_codes
            or self.status is LocalArtifactSpoolCleanupStatusV1.CLEANED_WITH_FAILURES
            and not self.failure_codes
            or self.result_digest != _cleanup_digest(self.status, self.failure_codes)
        ):
            raise ValueError("invalid local artifact spool cleanup result")


def _canonical_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _domain_digest(domain: str, body: dict[str, object]) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical_bytes(body)).hexdigest()


def _cleanup_digest(
    status: LocalArtifactSpoolCleanupStatusV1,
    failure_codes: tuple[LocalArtifactSpoolCodeV1, ...],
) -> str:
    return _domain_digest("synaptic-local-artifact-spool-cleanup/v1", {
        "failure_codes": [item.value for item in failure_codes],
        "status": status.value,
    })


def _closed(code: LocalArtifactSpoolCodeV1) -> LocalArtifactSpoolErrorV1:
    return LocalArtifactSpoolErrorV1(code)


def _same_node(left: LocalFileIdentityV1, right: LocalFileIdentityV1) -> bool:
    return (
        left.device,
        left.inode,
        stat.S_IFMT(left.mode),
    ) == (
        right.device,
        right.inode,
        stat.S_IFMT(right.mode),
    )


def _valid_file(identity: object, *, size: int | None = None) -> bool:
    return (
        type(identity) is LocalFileIdentityV1
        and stat.S_ISREG(identity.mode)
        and identity.nlink == 1
        and (size is None or identity.size == size)
    )


@dataclass(slots=True)
class _LiveSinkV1:
    sink: object
    publication_id: str
    role: str
    maximum_bytes: int
    filename: str
    spool_ref: str
    file: BorrowedFileV1 | None
    initial_identity: LocalFileIdentityV1
    hasher: object
    size_bytes: int = 0
    state: str = "OPEN"


@dataclass(slots=True)
class _FinishedSpoolV1:
    spool_ref: str
    publication_id: str
    role: str
    filename: str
    identity: LocalFileIdentityV1
    size_bytes: int
    sha256: str
    state: str = "FINISHED"
    readers: int = 0


class _LocalSpoolSinkV1:
    __slots__ = ("_owner", "_spool_ref", "_terminal")

    def __init__(self, owner: "LocalArtifactSpoolV1", spool_ref: str) -> None:
        self._owner = owner
        self._spool_ref = spool_ref
        self._terminal: str | None = None

    def write(self, chunk: bytes) -> None:
        self._owner._write(self, chunk)

    def finish(self) -> str:
        return self._owner._finish(self)

    def abort(self) -> None:
        self._owner._abort(self)


class LocalArtifactSpoolV1:
    """Host-owned spool facade; destination access intentionally stays private."""

    __slots__ = (
        "_filesystem", "_authority", "_admission", "_borrow", "_root",
        "_instance_ref", "_lock", "_condition", "_lifecycle", "_live",
        "_finished", "_cleanup_result",
    )

    def __init__(self, filesystem, authority, admission, borrow, root) -> None:
        self._filesystem = filesystem
        self._authority = authority
        self._admission = admission
        self._borrow = borrow
        self._root = root
        self._instance_ref = secrets.token_hex(32)
        self._lock = RLock()
        self._condition = Condition(self._lock)
        self._lifecycle = "OPEN"
        self._live: dict[str, _LiveSinkV1] = {}
        self._finished: dict[str, _FinishedSpoolV1] = {}
        self._cleanup_result: LocalArtifactSpoolCleanupResultV1 | None = None

    def _startup_reclaim(self) -> None:
        purpose = BorrowPurposeV1.PUBLICATION_SPOOL
        names = self._filesystem.list_borrowed_directory(
            self._borrow, self._root, MAX_DIRECTORY_ENTRIES + 1, purpose=purpose
        )
        if type(names) is not tuple:
            raise _closed(LocalArtifactSpoolCodeV1.INVALID)
        if len(names) > MAX_DIRECTORY_ENTRIES:
            raise _closed(LocalArtifactSpoolCodeV1.LIMIT_EXCEEDED)
        validated: list[tuple[str, LocalFileIdentityV1]] = []
        for name in names:
            if type(name) is not str or _FILENAME_RE.fullmatch(name) is None:
                raise _closed(LocalArtifactSpoolCodeV1.INVALID)
            identity = self._filesystem.stat_borrowed(
                self._borrow, self._root, name, purpose=purpose
            )
            if not _valid_file(identity):
                raise _closed(LocalArtifactSpoolCodeV1.INVALID)
            validated.append((name, identity))
        for name, identity in validated:
            current = self._filesystem.stat_borrowed(
                self._borrow, self._root, name, purpose=purpose
            )
            if current != identity:
                raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
        for name, _identity in validated:
            self._filesystem.unlink_borrowed(
                self._borrow, self._root, name, purpose=purpose
            )
        self._filesystem.fsync_borrowed_directory(
            self._borrow, self._root, purpose=purpose
        )
        remaining = self._filesystem.list_borrowed_directory(
            self._borrow, self._root, 1, purpose=purpose
        )
        if type(remaining) is not tuple:
            raise _closed(LocalArtifactSpoolCodeV1.INVALID)
        if remaining:
            raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)

    def open(self, publication_id: str, role: str, maximum_bytes: int):
        if (
            type(publication_id) is not str
            or _SAFE_REF_RE.fullmatch(publication_id) is None
            or type(role) is not str
            or _SAFE_REF_RE.fullmatch(role) is None
            or type(maximum_bytes) is not int
            or not 0 <= maximum_bytes <= _MAX_ARTIFACT_BYTES
        ):
            raise _closed(LocalArtifactSpoolCodeV1.INVALID)
        with self._lock:
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            ownership_body = {
                "instance_ref": self._instance_ref,
                "nonce": secrets.token_hex(32),
                "publication_id": publication_id,
                "role": role,
            }
            filename = "synaptic-spool-v1-" + _domain_digest(
                "synaptic-local-spool-filename/v1", ownership_body
            ) + ".blob"
            spool_ref = "local-spool-v1:" + _domain_digest(
                "synaptic-local-spool-reference/v1", ownership_body
            )
            try:
                file = self._filesystem.create_borrowed_file(
                    self._borrow, self._root, filename,
                    purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                )
            except BaseException as error:
                if type(error) is LocalArtifactSpoolErrorV1:
                    raise
                raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED) from None
            sink = _LocalSpoolSinkV1(self, spool_ref)
            self._live[spool_ref] = _LiveSinkV1(
                sink, publication_id, role, maximum_bytes, filename, spool_ref,
                file, file.identity, hashlib.sha256(),
            )
            return sink

    def _live_record(self, sink: _LocalSpoolSinkV1) -> _LiveSinkV1:
        if type(sink) is not _LocalSpoolSinkV1 or sink._owner is not self:
            raise _closed(LocalArtifactSpoolCodeV1.INVALID)
        record = self._live.get(sink._spool_ref)
        if record is None or record.sink is not sink:
            raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
        return record

    def _write(self, sink: _LocalSpoolSinkV1, chunk: bytes) -> None:
        if type(chunk) is not bytes or not 1 <= len(chunk) <= MAX_CHUNK_BYTES:
            raise _closed(LocalArtifactSpoolCodeV1.LIMIT_EXCEEDED)
        with self._lock:
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            record = self._live_record(sink)
            if record.state != "OPEN" or record.file is None:
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            if record.size_bytes + len(chunk) > record.maximum_bytes:
                raise _closed(LocalArtifactSpoolCodeV1.LIMIT_EXCEEDED)
            try:
                count = self._filesystem.write_borrowed(
                    self._borrow, record.file, chunk,
                    purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                )
            except BaseException:
                raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED) from None
            if count != len(chunk):
                raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED)
            record.hasher.update(chunk)
            record.size_bytes += len(chunk)

    def _finish(self, sink: _LocalSpoolSinkV1) -> str:
        with self._lock:
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            record = self._live_record(sink)
            if record.state != "OPEN" or record.file is None:
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            record.state = "FINISHING"
            purpose = BorrowPurposeV1.PUBLICATION_SPOOL
            try:
                self._filesystem.fsync_borrowed_file(
                    self._borrow, record.file, purpose=purpose
                )
                descriptor_identity = self._filesystem.stat_borrowed_file(
                    self._borrow, record.file, purpose=purpose
                )
                if (
                    not _valid_file(descriptor_identity, size=record.size_bytes)
                    or not _same_node(descriptor_identity, record.initial_identity)
                ):
                    raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
                file = record.file
                record.file = None
                self._filesystem.close_borrowed_file(
                    self._borrow, file, purpose=purpose
                )
                path_identity = self._filesystem.stat_borrowed(
                    self._borrow, self._root, record.filename, purpose=purpose
                )
                if path_identity != descriptor_identity:
                    raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
                self._filesystem.fsync_borrowed_directory(
                    self._borrow, self._root, purpose=purpose
                )
                finished = _FinishedSpoolV1(
                    record.spool_ref, record.publication_id, record.role,
                    record.filename, descriptor_identity, record.size_bytes,
                    record.hasher.hexdigest(),
                )
                del self._live[record.spool_ref]
                self._finished[record.spool_ref] = finished
                sink._terminal = "FINISHED"
                return record.spool_ref
            except LocalArtifactSpoolErrorV1:
                record.state = "FAILED"
                raise
            except BaseException:
                record.state = "FAILED"
                raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED) from None

    def _abort_record(self, record: _LiveSinkV1) -> None:
        purpose = BorrowPurposeV1.PUBLICATION_SPOOL
        record.state = "ABORTING"
        try:
            if record.file is not None:
                file = record.file
                record.file = None
                self._filesystem.close_borrowed_file(
                    self._borrow, file, purpose=purpose
                )
            identity = self._filesystem.stat_borrowed(
                self._borrow, self._root, record.filename, purpose=purpose
            )
            if not _valid_file(identity) or not _same_node(identity, record.initial_identity):
                raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
            self._filesystem.unlink_borrowed(
                self._borrow, self._root, record.filename, purpose=purpose
            )
            self._filesystem.fsync_borrowed_directory(
                self._borrow, self._root, purpose=purpose
            )
            self._live.pop(record.spool_ref, None)
            record.sink._terminal = "ABORTED"
        except LocalArtifactSpoolErrorV1:
            record.state = "FAILED"
            raise
        except BaseException:
            record.state = "FAILED"
            raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED) from None

    def _abort(self, sink: _LocalSpoolSinkV1) -> None:
        with self._lock:
            if type(sink) is not _LocalSpoolSinkV1 or sink._owner is not self:
                raise _closed(LocalArtifactSpoolCodeV1.INVALID)
            if sink._terminal in {"ABORTED", "FINISHED"}:
                return
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            record = self._live_record(sink)
            self._abort_record(record)

    def _iter_finished(
        self, spool_ref: str, expected_artifact: VerifiedArtifact
    ) -> Iterator[bytes]:
        if type(spool_ref) is not str or _REF_RE.fullmatch(spool_ref) is None:
            raise _closed(LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN)
        if type(expected_artifact) is not VerifiedArtifact:
            raise _closed(LocalArtifactSpoolCodeV1.INVALID)
        try:
            expected = VerifiedArtifact.from_dict(expected_artifact.to_dict())
        except BaseException:
            raise _closed(LocalArtifactSpoolCodeV1.INVALID) from None
        with self._lock:
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            record = self._finished.get(spool_ref)
            if record is None or record.state != "FINISHED":
                raise _closed(LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN)
            if (
                expected.role != record.role
                or expected.size_bytes != record.size_bytes
                or expected.sha256 != record.sha256
            ):
                raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)

        def stream() -> Iterator[bytes]:
            file = None
            with self._lock:
                if self._lifecycle != "OPEN":
                    raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
                current = self._finished.get(spool_ref)
                if current is not record or current.state != "FINISHED":
                    raise _closed(LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN)
                if (
                    expected.role != current.role
                    or expected.size_bytes != current.size_bytes
                    or expected.sha256 != current.sha256
                ):
                    raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
                current.readers += 1
                try:
                    file = self._filesystem.open_borrowed_read(
                        self._borrow, self._root, current.filename,
                        purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                    )
                    if file.identity != current.identity:
                        raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
                except LocalArtifactSpoolErrorV1 as error:
                    if file is not None:
                        try:
                            self._filesystem.close_borrowed_file(
                                self._borrow, file,
                                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                            )
                        except BaseException:
                            error = _closed(LocalArtifactSpoolCodeV1.IO_FAILED)
                    current.readers -= 1
                    raise error
                except BaseException:
                    if file is not None:
                        try:
                            self._filesystem.close_borrowed_file(
                                self._borrow, file,
                                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                            )
                        except BaseException:
                            pass
                    current.readers -= 1
                    raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED) from None
            size = 0
            hasher = hashlib.sha256()
            failure: LocalArtifactSpoolErrorV1 | None = None
            try:
                while True:
                    chunk = self._filesystem.read_borrowed(
                        self._borrow, file, MAX_CHUNK_BYTES,
                        purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                    )
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > current.size_bytes:
                        raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
                    hasher.update(chunk)
                    yield chunk
                descriptor_identity = self._filesystem.stat_borrowed_file(
                    self._borrow, file, purpose=BorrowPurposeV1.PUBLICATION_SPOOL
                )
                path_identity = self._filesystem.stat_borrowed(
                    self._borrow, self._root, current.filename,
                    purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
                )
                if (
                    size != current.size_bytes
                    or hasher.hexdigest() != current.sha256
                    or descriptor_identity != current.identity
                    or path_identity != current.identity
                ):
                    raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
            except GeneratorExit:
                raise
            except LocalArtifactSpoolErrorV1 as error:
                failure = error
            except BaseException:
                failure = _closed(LocalArtifactSpoolCodeV1.IO_FAILED)
            finally:
                try:
                    self._filesystem.close_borrowed_file(
                        self._borrow, file, purpose=BorrowPurposeV1.PUBLICATION_SPOOL
                    )
                except BaseException:
                    if failure is None:
                        failure = _closed(LocalArtifactSpoolCodeV1.IO_FAILED)
                with self._lock:
                    current.readers -= 1
                    self._condition.notify_all()
            if failure is not None:
                raise failure

        return stream()

    def _release_finished_record(self, record: _FinishedSpoolV1) -> None:
        if record.readers:
            raise _closed(LocalArtifactSpoolCodeV1.IN_USE)
        record.state = "RELEASING"
        try:
            identity = self._filesystem.stat_borrowed(
                self._borrow, self._root, record.filename,
                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
            )
            if identity != record.identity:
                raise _closed(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
            self._filesystem.unlink_borrowed(
                self._borrow, self._root, record.filename,
                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
            )
            self._filesystem.fsync_borrowed_directory(
                self._borrow, self._root,
                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
            )
            self._finished.pop(record.spool_ref, None)
            record.state = "RELEASED"
        except LocalArtifactSpoolErrorV1:
            record.state = "FAILED"
            raise
        except BaseException:
            record.state = "FAILED"
            raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED) from None

    def _release_finished(self, spool_ref: str) -> None:
        if type(spool_ref) is not str or _REF_RE.fullmatch(spool_ref) is None:
            raise _closed(LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN)
        with self._lock:
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactSpoolCodeV1.CLOSED)
            record = self._finished.get(spool_ref)
            if record is None:
                raise _closed(LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN)
            if record.state != "FINISHED":
                raise _closed(LocalArtifactSpoolCodeV1.IO_FAILED)
            self._release_finished_record(record)

    def cleanup_owned(self) -> LocalArtifactSpoolCleanupResultV1:
        with self._condition:
            if self._cleanup_result is not None:
                return self._cleanup_result
            while self._lifecycle == "CLEANING":
                while self._cleanup_result is None:
                    self._condition.wait()
                if self._cleanup_result is not None:
                    return self._cleanup_result
            if self._lifecycle == "OPEN":
                self._lifecycle = "CLOSING"
            if any(record.readers for record in self._finished.values()):
                raise _closed(LocalArtifactSpoolCodeV1.IN_USE)
            self._lifecycle = "CLEANING"
        failures: list[LocalArtifactSpoolCodeV1] = []
        for record in tuple(self._live.values()):
            try:
                self._abort_record(record)
            except LocalArtifactSpoolErrorV1 as error:
                failures.append(error.code)
        for record in tuple(self._finished.values()):
            try:
                self._release_finished_record(record)
            except LocalArtifactSpoolErrorV1 as error:
                failures.append(error.code)
        try:
            if self._filesystem.list_borrowed_directory(
                self._borrow, self._root, 1,
                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
            ):
                failures.append(LocalArtifactSpoolCodeV1.CONTENT_CHANGED)
            self._filesystem.fsync_borrowed_directory(
                self._borrow, self._root,
                purpose=BorrowPurposeV1.PUBLICATION_SPOOL,
            )
        except BaseException:
            failures.append(LocalArtifactSpoolCodeV1.IO_FAILED)
        for operation in (
            lambda: self._filesystem.release_borrow(
                self._borrow, purpose=BorrowPurposeV1.PUBLICATION_SPOOL
            ),
            lambda: self._filesystem.release_single_root_admission(
                self._authority, self._admission
            ),
            lambda: self._filesystem.release_single_root_authority(self._authority),
        ):
            try:
                operation()
            except BaseException:
                failures.append(LocalArtifactSpoolCodeV1.IO_FAILED)
        unique = tuple(sorted(set(failures), key=lambda item: item.value))
        status = (
            LocalArtifactSpoolCleanupStatusV1.CLEANED
            if not unique else LocalArtifactSpoolCleanupStatusV1.CLEANED_WITH_FAILURES
        )
        result = LocalArtifactSpoolCleanupResultV1(
            status, unique, _cleanup_digest(status, unique)
        )
        with self._condition:
            self._cleanup_result = result
            self._lifecycle = (
                "CLOSED" if not unique else "CLOSED_WITH_FAILURES"
            )
            self._condition.notify_all()
            return self._cleanup_result


def acquire_local_artifact_spool_v1(
    filesystem: LocalFilesystemV1,
    binding: LocalRootBindingV1,
) -> LocalArtifactSpoolV1:
    """Acquire the dedicated spool root and publish a reconciled facade."""

    authority = admission = borrow = None
    failure_code = LocalArtifactSpoolCodeV1.IO_FAILED
    # B-18 (section 27.4, site 2).  The failure is re-raised after the cleanup
    # sequence, outside both handlers, so the original cannot be named there:
    # Python deletes an `except ... as` binding when its handler exits.  Each
    # handler copies the original into this separate name instead, and the
    # deferred raise chains from it.  The cleanup order is unchanged.
    cause: BaseException | None = None
    try:
        authority = filesystem.retain_single_root_authority(
            binding, purpose=SingleRootPurposeV1.PUBLICATION_SPOOL
        )
        admission = filesystem.acquire_single_root_admission(authority)
        request = RetainedRootBorrowRequestV1.build(
            authority.authority_digest,
            BorrowPurposeV1.PUBLICATION_SPOOL,
            RootAccessV1.READ_CREATE,
        )
        borrow = filesystem.borrow_single_root(authority, admission, request)
        root = filesystem.root_directory(
            borrow, purpose=BorrowPurposeV1.PUBLICATION_SPOOL
        )
        facade = LocalArtifactSpoolV1(filesystem, authority, admission, borrow, root)
        facade._startup_reclaim()
        return facade
    except LocalArtifactSpoolErrorV1 as error:
        failure_code = error.code
        cause = error
    except BaseException as error:
        failure_code = LocalArtifactSpoolCodeV1.IO_FAILED
        cause = error
    cleanup_failed = False
    if borrow is not None:
        try:
            filesystem.release_borrow(borrow, purpose=BorrowPurposeV1.PUBLICATION_SPOOL)
        except BaseException:
            cleanup_failed = True
    if admission is not None:
        try:
            filesystem.release_single_root_admission(authority, admission)
        except BaseException:
            cleanup_failed = True
    if authority is not None:
        try:
            filesystem.release_single_root_authority(authority)
        except BaseException:
            cleanup_failed = True
    if cleanup_failed:
        failure_code = LocalArtifactSpoolCodeV1.IO_FAILED
    raise _closed(failure_code) from cause


__all__ = [
    "LocalArtifactSpoolCleanupResultV1",
    "LocalArtifactSpoolCleanupStatusV1",
    "LocalArtifactSpoolCodeV1",
    "LocalArtifactSpoolErrorV1",
    "LocalArtifactSpoolV1",
    "acquire_local_artifact_spool_v1",
]
