from __future__ import annotations

import hashlib
import os
import re
import stat
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace

import pytest

import synaptic_host
from synaptic_host.artifact_spool import (
    LocalArtifactSpoolCleanupStatusV1,
    LocalArtifactSpoolCodeV1,
    LocalArtifactSpoolErrorV1,
    LocalArtifactSpoolV1,
    acquire_local_artifact_spool_v1,
)
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    LocalFileIdentityV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RootAccessV1,
    digest_v1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.posix import PosixRetainedDirfdPortV1
from synaptic_tuner.api.v1.results import VerifiedArtifact


_NAME = re.compile(r"^synaptic-spool-v1-[0-9a-f]{64}\.blob$")
_REF = re.compile(r"^local-spool-v1:[0-9a-f]{64}$")


@dataclass
class _Node:
    inode: int
    content: bytearray
    nlink: int = 1

    def identity(self) -> LocalFileIdentityV1:
        return LocalFileIdentityV1(
            7, self.inode, stat.S_IFREG | 0o600, self.nlink,
            len(self.content), len(self.content), len(self.content),
        )


class _Filesystem:
    def __init__(
        self,
        entries: dict[str, _Node] | None = None,
        *,
        fail_admission: bool = False,
    ) -> None:
        self.entries = {} if entries is None else entries
        self.trace = []
        self.next_inode = 100
        self.read_calls = 0
        self.after_fsync_file = None
        self.after_stat_path = None
        self.fail_admission = fail_admission
        self.fail_ops: set[str] = set()
        self.list_result = None
        self.short_write = False
        self.stat_path_calls = 0
        self.authority = SimpleNamespace(authority_digest="a" * 64)
        self.admission = object()
        self.borrow = object()
        self.root = object()

    def retain_single_root_authority(self, binding, *, purpose):
        self.trace.append("retain-authority")
        if "retain-authority" in self.fail_ops:
            raise RuntimeError("closed fake authority failure")
        return self.authority

    def acquire_single_root_admission(self, authority):
        self.trace.append("acquire-admission")
        if self.fail_admission:
            raise RuntimeError("closed fake admission failure")
        return self.admission

    def borrow_single_root(self, authority, admission, request):
        self.trace.append("borrow")
        if "borrow" in self.fail_ops:
            raise RuntimeError("closed fake borrow failure")
        return self.borrow

    def root_directory(self, borrow, *, purpose):
        self.trace.append("root-directory")
        if "root-directory" in self.fail_ops:
            raise RuntimeError("closed fake root failure")
        return self.root

    def list_borrowed_directory(self, borrow, root, maximum, *, purpose):
        self.trace.append("list")
        if "list" in self.fail_ops:
            raise RuntimeError("closed fake list failure")
        if self.list_result is not None:
            return self.list_result
        return tuple(sorted(self.entries)[:maximum])

    def stat_borrowed(self, borrow, root, name, *, purpose):
        self.trace.append("stat-path")
        self.stat_path_calls += 1
        if self.after_stat_path is not None:
            self.after_stat_path(name, self.stat_path_calls)
        if "stat-path" in self.fail_ops:
            raise RuntimeError("closed fake path stat failure")
        node = self.entries.get(name)
        return None if node is None else node.identity()

    def unlink_borrowed(self, borrow, root, name, *, purpose):
        self.trace.append("unlink:" + name)
        if "unlink" in self.fail_ops:
            raise RuntimeError("closed fake unlink failure")
        del self.entries[name]

    def fsync_borrowed_directory(self, borrow, root, *, purpose):
        self.trace.append("fsync-root")
        if "fsync-root" in self.fail_ops:
            raise RuntimeError("closed fake root fsync failure")

    def create_borrowed_file(self, borrow, root, name, *, purpose):
        self.trace.append("create:" + name)
        if name in self.entries:
            raise RuntimeError
        self.next_inode += 1
        node = _Node(self.next_inode, bytearray())
        self.entries[name] = node
        return SimpleNamespace(identity=node.identity(), name=name, position=0)

    def write_borrowed(self, borrow, file, payload, *, purpose):
        self.trace.append("write")
        if "write" in self.fail_ops:
            raise RuntimeError("closed fake write failure")
        written = len(payload) - 1 if self.short_write else len(payload)
        self.entries[file.name].content.extend(payload[:written])
        return written

    def fsync_borrowed_file(self, borrow, file, *, purpose):
        self.trace.append("fsync-file")
        if "fsync-file" in self.fail_ops:
            raise RuntimeError("closed fake file fsync failure")
        if self.after_fsync_file is not None:
            self.after_fsync_file(file.name)

    def stat_borrowed_file(self, borrow, file, *, purpose):
        self.trace.append("stat-file")
        if "stat-file" in self.fail_ops:
            raise RuntimeError("closed fake descriptor stat failure")
        return self.entries[file.name].identity()

    def close_borrowed_file(self, borrow, file, *, purpose):
        self.trace.append("close-file")
        if "close-file" in self.fail_ops:
            raise RuntimeError("closed fake close failure")

    def open_borrowed_read(self, borrow, root, name, *, purpose):
        node = self.entries[name]
        return SimpleNamespace(identity=node.identity(), name=name, position=0)

    def read_borrowed(self, borrow, file, maximum, *, purpose):
        self.read_calls += 1
        if "read" in self.fail_ops:
            raise RuntimeError("closed fake read failure")
        content = self.entries[file.name].content
        chunk = bytes(content[file.position:file.position + maximum])
        file.position += len(chunk)
        return chunk

    def release_borrow(self, borrow, *, purpose):
        self.trace.append("release-borrow")
        if "release-borrow" in self.fail_ops:
            raise RuntimeError("closed fake borrow release failure")

    def release_single_root_admission(self, authority, admission):
        self.trace.append("release-admission")
        if "release-admission" in self.fail_ops:
            raise RuntimeError("closed fake admission release failure")

    def release_single_root_authority(self, authority):
        self.trace.append("release-authority")
        if "release-authority" in self.fail_ops:
            raise RuntimeError("closed fake authority release failure")


def _binding() -> LocalRootBindingV1:
    path = Path.cwd() / ".fake-metadata" / "artifact-publication-spool"
    body = {
        "access": RootAccessV1.READ_CREATE.value,
        "absolute_root": str(path),
        "authority_ref": "authority",
        "key_ref": "key",
        "permit_ref": "permit",
        "root_ref": "spool-root",
    }
    permit = LocalRootPermitV1(
        "permit", "spool-root", path, RootAccessV1.READ_CREATE,
        "authority", "key", digest_v1(body), "0" * 64,
    )
    return LocalRootBindingV1(
        "spool-root", "project://artifact-publication-spool", path,
        RootAccessV1.READ_CREATE, permit.permit_ref, permit,
    )


def _binding_at(path: Path) -> LocalRootBindingV1:
    body = {
        "access": RootAccessV1.READ_CREATE.value,
        "absolute_root": str(path),
        "authority_ref": "authority-linux",
        "key_ref": "key-linux",
        "permit_ref": "permit-linux",
        "root_ref": "spool-root-linux",
    }
    permit = LocalRootPermitV1(
        "permit-linux", "spool-root-linux", path, RootAccessV1.READ_CREATE,
        "authority-linux", "key-linux", digest_v1(body), "0" * 64,
    )
    return LocalRootBindingV1(
        "spool-root-linux", "project://artifact-publication-spool", path,
        RootAccessV1.READ_CREATE, permit.permit_ref, permit,
    )


class _Authenticator:
    def authenticate(self, permit):
        return permit


def _finished(filesystem: _Filesystem, payload=b"artifact"):
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())
    sink = spool.open("publication-1", "adapter", len(payload))
    sink.write(payload)
    reference = sink.finish()
    artifact = VerifiedArtifact(
        "adapter", hashlib.sha256(payload).hexdigest(), len(payload)
    )
    return spool, sink, reference, artifact


def test_public_surface_opaque_derivation_finish_iter_release_and_cleanup() -> None:
    filesystem = _Filesystem()
    spool, sink, reference, artifact = _finished(filesystem)
    assert type(spool) is LocalArtifactSpoolV1
    assert _REF.fullmatch(reference)
    assert len(filesystem.entries) == 1
    filename = next(iter(filesystem.entries))
    assert _NAME.fullmatch(filename)
    assert "publication" not in filename and "adapter" not in filename
    assert b"".join(spool._iter_finished(reference, artifact)) == b"artifact"
    spool._release_finished(reference)
    with pytest.raises(LocalArtifactSpoolErrorV1) as replay:
        spool._release_finished(reference)
    assert replay.value.code is LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN
    cleaned = spool.cleanup_owned()
    assert cleaned.status is LocalArtifactSpoolCleanupStatusV1.CLEANED
    assert spool.cleanup_owned() is cleaned
    assert filesystem.trace[-3:] == [
        "release-borrow", "release-admission", "release-authority"
    ]
    assert not hasattr(spool, "close")
    assert not hasattr(spool, "iter_finished")
    assert not hasattr(spool, "release_finished")
    assert sink.__class__.__name__.startswith("_LocalSpoolSink")


def test_bounds_abort_and_closed_rejection() -> None:
    filesystem = _Filesystem()
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())
    sink = spool.open("publication-2", "model", 3)
    with pytest.raises(LocalArtifactSpoolErrorV1) as bounded:
        sink.write(b"four")
    assert bounded.value.code is LocalArtifactSpoolCodeV1.LIMIT_EXCEEDED
    sink.write(b"one")
    sink.abort()
    sink.abort()
    assert filesystem.entries == {}
    spool.cleanup_owned()
    with pytest.raises(LocalArtifactSpoolErrorV1) as closed:
        spool.open("publication-2", "model", 1)
    assert closed.value.code is LocalArtifactSpoolCodeV1.CLOSED


def test_finish_rejects_path_substitution_and_cleanup_owns_exact_file() -> None:
    filesystem = _Filesystem()
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())
    sink = spool.open("publication-3", "adapter", 1)
    sink.write(b"x")

    def substitute(name):
        filesystem.entries[name] = _Node(999, bytearray(b"x"))

    filesystem.after_fsync_file = substitute
    with pytest.raises(LocalArtifactSpoolErrorV1) as changed:
        sink.finish()
    assert changed.value.code is LocalArtifactSpoolCodeV1.CONTENT_CHANGED
    result = spool.cleanup_owned()
    assert result.status is LocalArtifactSpoolCleanupStatusV1.CLEANED_WITH_FAILURES


def test_expected_artifact_mismatch_rejects_before_read() -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    wrong = VerifiedArtifact("model", artifact.sha256, artifact.size_bytes)
    with pytest.raises(LocalArtifactSpoolErrorV1) as changed:
        spool._iter_finished(reference, wrong)
    assert changed.value.code is LocalArtifactSpoolCodeV1.CONTENT_CHANGED
    assert filesystem.read_calls == 0
    spool.cleanup_owned()


def test_unstarted_finished_iterator_owns_no_reader_or_descriptor() -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    iterator = spool._iter_finished(reference, artifact)
    spool._release_finished(reference)
    with pytest.raises(LocalArtifactSpoolErrorV1) as unknown:
        next(iterator)
    assert unknown.value.code is LocalArtifactSpoolCodeV1.REFERENCE_UNKNOWN
    assert filesystem.read_calls == 0
    assert spool.cleanup_owned().status is LocalArtifactSpoolCleanupStatusV1.CLEANED


def test_active_reader_cleanup_is_nonterminal_and_retry_converges() -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    live = spool.open("publication-live", "model", 1)
    deferred = spool._iter_finished(reference, artifact)
    reader = spool._iter_finished(reference, artifact)
    assert next(reader) == b"artifact"
    before = tuple(filesystem.trace)

    with pytest.raises(LocalArtifactSpoolErrorV1) as in_use:
        spool.cleanup_owned()
    assert in_use.value.code is LocalArtifactSpoolCodeV1.IN_USE
    assert tuple(filesystem.trace) == before
    for operation in (
        lambda: spool.open("publication-new", "model", 1),
        lambda: live.write(b"x"),
        live.finish,
        lambda: spool._iter_finished(reference, artifact),
        lambda: next(deferred),
    ):
        with pytest.raises(LocalArtifactSpoolErrorV1) as closed:
            operation()
        assert closed.value.code is LocalArtifactSpoolCodeV1.CLOSED

    reader.close()
    cleaned = spool.cleanup_owned()
    assert cleaned.status is LocalArtifactSpoolCleanupStatusV1.CLEANED
    assert spool.cleanup_owned() is cleaned
    assert filesystem.trace.count("release-borrow") == 1


def test_concurrent_reader_release_cleanup_race_is_bounded() -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    reader = spool._iter_finished(reference, artifact)
    assert next(reader) == b"artifact"
    gate = Barrier(3)

    def release() -> LocalArtifactSpoolCodeV1:
        gate.wait(timeout=5)
        try:
            spool._release_finished(reference)
        except LocalArtifactSpoolErrorV1 as error:
            return error.code
        raise AssertionError("release unexpectedly succeeded with an active reader")

    def cleanup() -> LocalArtifactSpoolCodeV1:
        gate.wait(timeout=5)
        try:
            spool.cleanup_owned()
        except LocalArtifactSpoolErrorV1 as error:
            return error.code
        raise AssertionError("cleanup unexpectedly succeeded with an active reader")

    with ThreadPoolExecutor(max_workers=2) as pool:
        released = pool.submit(release)
        cleaned = pool.submit(cleanup)
        gate.wait(timeout=5)
        release_code = released.result(timeout=5)
        cleanup_code = cleaned.result(timeout=5)
    assert release_code in {
        LocalArtifactSpoolCodeV1.IN_USE,
        LocalArtifactSpoolCodeV1.CLOSED,
    }
    assert cleanup_code is LocalArtifactSpoolCodeV1.IN_USE
    assert not any(item.startswith("unlink:") for item in filesystem.trace)
    assert "release-borrow" not in filesystem.trace
    reader.close()
    assert spool.cleanup_owned().status is LocalArtifactSpoolCleanupStatusV1.CLEANED


def test_iter_finished_independently_rejects_same_size_content_mutation() -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    filename = next(iter(filesystem.entries))
    filesystem.entries[filename].content[:] = b"mutated!"
    with pytest.raises(LocalArtifactSpoolErrorV1) as changed:
        b"".join(spool._iter_finished(reference, artifact))
    assert changed.value.code is LocalArtifactSpoolCodeV1.CONTENT_CHANGED
    assert filesystem.read_calls > 0
    assert spool.cleanup_owned().status is LocalArtifactSpoolCleanupStatusV1.CLEANED


def test_startup_two_phase_validation_and_stale_reclamation() -> None:
    valid_a = "synaptic-spool-v1-" + "1" * 64 + ".blob"
    valid_b = "synaptic-spool-v1-" + "2" * 64 + ".blob"
    filesystem = _Filesystem({
        valid_a: _Node(1, bytearray(b"a")),
        valid_b: _Node(2, bytearray(b"b")),
    })
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())
    assert filesystem.entries == {}
    assert filesystem.trace.index("fsync-root") > max(
        index for index, value in enumerate(filesystem.trace)
        if value.startswith("unlink:")
    )
    spool.cleanup_owned()

    invalid = _Filesystem({
        valid_a: _Node(1, bytearray(b"a")),
        "unexpected": _Node(2, bytearray(b"b")),
    })
    with pytest.raises(LocalArtifactSpoolErrorV1):
        acquire_local_artifact_spool_v1(invalid, _binding())
    assert set(invalid.entries) == {valid_a, "unexpected"}
    assert invalid.trace[-3:] == [
        "release-borrow", "release-admission", "release-authority"
    ]


@pytest.mark.parametrize(
    "listing, expected_code",
    [
        (
            tuple(
                f"synaptic-spool-v1-{index:064x}.blob"
                for index in range(4097)
            ),
            LocalArtifactSpoolCodeV1.LIMIT_EXCEEDED,
        ),
        ((object(),), LocalArtifactSpoolCodeV1.INVALID),
        ([], LocalArtifactSpoolCodeV1.INVALID),
    ],
)
def test_startup_rejects_overflow_and_unexpected_results_without_deletion(
    listing, expected_code
) -> None:
    filesystem = _Filesystem()
    filesystem.list_result = listing
    with pytest.raises(LocalArtifactSpoolErrorV1) as rejected:
        acquire_local_artifact_spool_v1(filesystem, _binding())
    assert rejected.value.code is expected_code
    assert not any(item.startswith("unlink:") for item in filesystem.trace)


def test_startup_identity_change_has_zero_delete_effects() -> None:
    name = "synaptic-spool-v1-" + "a" * 64 + ".blob"
    filesystem = _Filesystem({name: _Node(1, bytearray(b"stale"))})

    def substitute(current_name, call):
        if call == 2:
            filesystem.entries[current_name] = _Node(2, bytearray(b"stale"))

    filesystem.after_stat_path = substitute
    with pytest.raises(LocalArtifactSpoolErrorV1) as changed:
        acquire_local_artifact_spool_v1(filesystem, _binding())
    assert changed.value.code is LocalArtifactSpoolCodeV1.CONTENT_CHANGED
    assert not any(item.startswith("unlink:") for item in filesystem.trace)


@pytest.mark.parametrize("mode", ["short", "failure"])
def test_write_failure_retains_exact_cleanup_ownership(mode) -> None:
    filesystem = _Filesystem()
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())
    sink = spool.open("publication-write", "adapter", 3)
    if mode == "short":
        filesystem.short_write = True
    else:
        filesystem.fail_ops.add("write")
    with pytest.raises(LocalArtifactSpoolErrorV1) as failed:
        sink.write(b"abc")
    assert failed.value.code is LocalArtifactSpoolCodeV1.IO_FAILED
    filesystem.fail_ops.discard("write")
    assert spool.cleanup_owned().status is LocalArtifactSpoolCleanupStatusV1.CLEANED
    assert filesystem.entries == {}


def test_finish_uses_exact_durability_order() -> None:
    filesystem = _Filesystem()
    spool, _sink, _reference, _artifact = _finished(filesystem)
    ordered = ["fsync-file", "stat-file", "close-file", "stat-path", "fsync-root"]
    finish_start = filesystem.trace.index("fsync-file")
    positions = [filesystem.trace.index(item, finish_start) for item in ordered]
    assert positions == sorted(positions)
    spool.cleanup_owned()


@pytest.mark.parametrize(
    "operation",
    ["fsync-file", "stat-file", "close-file", "stat-path", "fsync-root"],
)
def test_finish_failures_are_closed_and_cleanup_releases_in_order(operation) -> None:
    filesystem = _Filesystem()
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())
    sink = spool.open("publication-finish", "adapter", 1)
    sink.write(b"x")
    filesystem.fail_ops.add(operation)
    with pytest.raises(LocalArtifactSpoolErrorV1) as failed:
        sink.finish()
    assert failed.value.code is LocalArtifactSpoolCodeV1.IO_FAILED
    spool.cleanup_owned()
    assert filesystem.trace[-3:] == [
        "release-borrow", "release-admission", "release-authority"
    ]


@pytest.mark.parametrize("payload", [b"art", b"artifact-extended"])
def test_iter_rejects_truncated_or_extended_file(payload) -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    filename = next(iter(filesystem.entries))
    filesystem.entries[filename].content[:] = payload
    with pytest.raises(LocalArtifactSpoolErrorV1) as changed:
        b"".join(spool._iter_finished(reference, artifact))
    assert changed.value.code is LocalArtifactSpoolCodeV1.CONTENT_CHANGED
    spool.cleanup_owned()


@pytest.mark.parametrize("operation", ["read", "stat-file", "stat-path", "close-file"])
def test_iter_operational_failures_are_sanitized(operation) -> None:
    filesystem = _Filesystem()
    spool, _sink, reference, artifact = _finished(filesystem)
    filesystem.fail_ops.add(operation)
    with pytest.raises(LocalArtifactSpoolErrorV1) as failed:
        b"".join(spool._iter_finished(reference, artifact))
    assert failed.value.code is LocalArtifactSpoolCodeV1.IO_FAILED
    filesystem.fail_ops.discard(operation)
    spool.cleanup_owned()


@pytest.mark.parametrize(
    "operation, expected_releases",
    [
        ("retain-authority", ()),
        ("borrow", ("release-admission", "release-authority")),
        (
            "root-directory",
            ("release-borrow", "release-admission", "release-authority"),
        ),
        ("list", ("release-borrow", "release-admission", "release-authority")),
    ],
)
def test_factory_rolls_back_only_acquired_capabilities(operation, expected_releases) -> None:
    filesystem = _Filesystem()
    filesystem.fail_ops.add(operation)
    with pytest.raises(LocalArtifactSpoolErrorV1) as failed:
        acquire_local_artifact_spool_v1(filesystem, _binding())
    assert failed.value.code is LocalArtifactSpoolCodeV1.IO_FAILED
    releases = tuple(item for item in filesystem.trace if item.startswith("release-"))
    assert releases == expected_releases


def test_cleanup_collects_multiple_failures_and_preserves_release_order() -> None:
    filesystem = _Filesystem()
    spool, _sink, _reference, _artifact = _finished(filesystem)
    filesystem.fail_ops.update({
        "unlink", "release-borrow", "release-admission", "release-authority"
    })
    result = spool.cleanup_owned()
    assert result.status is LocalArtifactSpoolCleanupStatusV1.CLEANED_WITH_FAILURES
    assert result.failure_codes
    assert filesystem.trace[-3:] == [
        "release-borrow", "release-admission", "release-authority"
    ]
    assert spool.cleanup_owned() is result


def test_admission_loser_never_scans_and_releases_only_owned_authority() -> None:
    filesystem = _Filesystem(fail_admission=True)
    with pytest.raises(LocalArtifactSpoolErrorV1) as failed:
        acquire_local_artifact_spool_v1(filesystem, _binding())
    assert failed.value.code is LocalArtifactSpoolCodeV1.IO_FAILED
    assert filesystem.trace == [
        "retain-authority", "acquire-admission", "release-authority"
    ]


def test_bounded_concurrent_sinks_are_independent() -> None:
    filesystem = _Filesystem()
    spool = acquire_local_artifact_spool_v1(filesystem, _binding())

    def materialize(index: int) -> tuple[str, VerifiedArtifact, bytes]:
        payload = f"artifact-{index}".encode("ascii")
        sink = spool.open(f"publication-{index}", "adapter", len(payload))
        sink.write(payload)
        reference = sink.finish()
        return reference, VerifiedArtifact(
            "adapter", hashlib.sha256(payload).hexdigest(), len(payload)
        ), payload

    with ThreadPoolExecutor(max_workers=8) as pool:
        artifacts = list(pool.map(materialize, range(16)))
    assert len({reference for reference, _artifact, _payload in artifacts}) == 16
    for reference, artifact, payload in artifacts:
        assert b"".join(spool._iter_finished(reference, artifact)) == payload
        spool._release_finished(reference)
    assert spool.cleanup_owned().status is LocalArtifactSpoolCleanupStatusV1.CLEANED


def test_concurrent_cleanup_converges_and_lazy_exports_are_narrow() -> None:
    filesystem = _Filesystem()
    spool, _sink, _reference, _artifact = _finished(filesystem)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _index: spool.cleanup_owned(), range(32)))
    assert all(result is results[0] for result in results)
    assert filesystem.trace.count("release-borrow") == 1
    assert synaptic_host.LocalArtifactSpoolV1 is LocalArtifactSpoolV1
    assert "_LocalSpoolSinkV1" not in synaptic_host.__all__


@pytest.mark.skipif(os.name != "posix", reason="real retained-dirfd integration")
def test_real_linux_capability_lifecycle(tmp_path) -> None:
    filesystem = LocalFilesystemV1(
        PosixRetainedDirfdPortV1(), _Authenticator(), native_platform="linux"
    )
    spool = acquire_local_artifact_spool_v1(filesystem, _binding_at(tmp_path))
    sink = spool.open("publication-linux", "adapter", 7)
    sink.write(b"payload")
    reference = sink.finish()
    artifact = VerifiedArtifact(
        "adapter", hashlib.sha256(b"payload").hexdigest(), 7
    )
    assert b"".join(spool._iter_finished(reference, artifact)) == b"payload"
    spool._release_finished(reference)
    assert spool.cleanup_owned().status is LocalArtifactSpoolCleanupStatusV1.CLEANED
    assert tuple(tmp_path.iterdir()) == ()
