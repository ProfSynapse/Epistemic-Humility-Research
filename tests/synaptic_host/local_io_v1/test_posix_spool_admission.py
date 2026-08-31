from __future__ import annotations

import errno
import multiprocessing
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from synaptic_host.local_io_v1 import posix
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import (
    CapabilityStatusV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    digest_v1,
)
from synaptic_host.local_io_v1.posix import PosixRetainedDirfdPortV1, detect_posix_capability_v1


pytestmark = pytest.mark.skipif(
    os.name != "posix" or not sys.platform.startswith("linux"),
    reason="Linux publication admission only",
)


def _attempt(path: str, output) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(Path(path))
    try:
        lease = port.acquire_directory_admission(root)
    except LocalIOErrorV1 as error:
        output.put(error.code.value)
    else:
        output.put("acquired")
        port.release_directory_admission(root, lease)
    finally:
        port.close_directory(root)


def _hold_until_crash(path: str, ready) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(Path(path))
    port.acquire_directory_admission(root)
    ready.send("ready")
    ready.close()
    time.sleep(30)


def test_directory_admission_creates_no_entry_and_reacquires(tmp_path) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)
    first = port.acquire_directory_admission(root)
    assert list(tmp_path.iterdir()) == []
    assert port.validate_directory_admission(root, first) is first
    port.release_directory_admission(root, first)
    second = port.acquire_directory_admission(root)
    assert second.root_node == first.root_node
    port.release_directory_admission(root, second)
    port.close_directory(root)


def test_cross_process_contention_release_and_crash_recovery(tmp_path) -> None:
    context = multiprocessing.get_context("spawn")
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)
    lease = port.acquire_directory_admission(root)
    output = context.Queue()
    contender = context.Process(target=_attempt, args=(str(tmp_path), output))
    contender.start()
    assert output.get(timeout=10) == LocalIOCodeV1.ROOT_IN_USE.value
    contender.join(timeout=10)
    assert contender.exitcode == 0
    port.release_directory_admission(root, lease)

    receiver, sender = context.Pipe(duplex=False)
    holder = context.Process(target=_hold_until_crash, args=(str(tmp_path), sender))
    holder.start()
    assert receiver.poll(10) and receiver.recv() == "ready"
    holder.terminate()
    holder.join(timeout=10)
    assert not holder.is_alive()

    replacement = port.acquire_directory_admission(root)
    port.release_directory_admission(root, replacement)
    port.close_directory(root)


def test_exact_directory_and_lease_objects_are_required(tmp_path) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)
    lease = port.acquire_directory_admission(root)
    for directory, candidate in ((replace(root), lease), (root, replace(lease))):
        with pytest.raises(LocalIOErrorV1) as caught:
            port.validate_directory_admission(directory, candidate)
        assert caught.value.code is LocalIOCodeV1.ADMISSION_INVALID
    port.release_directory_admission(root, lease)
    port.close_directory(root)


def test_admission_descriptor_is_cloexec_and_exec_does_not_retain_lock(tmp_path) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)
    lease = port.acquire_directory_admission(root)
    live = port._PosixRetainedDirfdPortV1__admission_leases[lease.lease_ref]
    assert posix._fcntl.fcntl(live.descriptor, posix._fcntl.F_GETFD) & posix._fcntl.FD_CLOEXEC

    child = os.posix_spawn(
        sys.executable,
        [sys.executable, "-c", "import time; time.sleep(5)"],
        dict(os.environ),
    )
    try:
        port.release_directory_admission(root, lease)
        replacement_port = PosixRetainedDirfdPortV1()
        replacement_root = replacement_port.retain_directory(tmp_path)
        replacement = replacement_port.acquire_directory_admission(replacement_root)
        replacement_port.release_directory_admission(replacement_root, replacement)
        replacement_port.close_directory(replacement_root)
    finally:
        os.kill(child, 15)
        os.waitpid(child, 0)
        port.close_directory(root)


def test_release_close_failure_is_one_shot_and_reacquirable(tmp_path, monkeypatch) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)
    lease = port.acquire_directory_admission(root)
    descriptor = port._PosixRetainedDirfdPortV1__admission_leases[lease.lease_ref].descriptor
    real_close = posix.os.close
    calls = 0

    def close_after_effect(value: int) -> None:
        nonlocal calls
        real_close(value)
        if value == descriptor:
            calls += 1
            raise OSError(errno.EIO, "simulated Linux close failure")

    with monkeypatch.context() as patch:
        patch.setattr(posix.os, "close", close_after_effect)
        with pytest.raises(LocalIOErrorV1) as failed:
            port.release_directory_admission(root, lease)
        assert failed.value.code is LocalIOCodeV1.ADMISSION_RELEASE_FAILED
        with pytest.raises(LocalIOErrorV1) as replay:
            port.release_directory_admission(root, lease)
        assert replay.value.code is LocalIOCodeV1.ADMISSION_INVALID
        assert calls == 1

    replacement = port.acquire_directory_admission(root)
    port.release_directory_admission(root, replacement)
    port.close_directory(root)


def test_only_flock_contention_maps_to_root_in_use(tmp_path, monkeypatch) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)

    def denied(*_args) -> None:
        raise OSError(errno.EACCES, "denied")

    monkeypatch.setattr(posix._fcntl, "flock", denied)
    with pytest.raises(LocalIOErrorV1) as caught:
        port.acquire_directory_admission(root)
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    port.close_directory(root)


def test_idle_accidental_child_rejects_inherited_port_before_open(tmp_path) -> None:
    port = PosixRetainedDirfdPortV1()
    root = port.retain_directory(tmp_path)
    child = os.fork()
    if child == 0:
        try:
            port.acquire_directory_admission(root)
        except LocalIOErrorV1 as error:
            os._exit(0 if error.code is LocalIOCodeV1.ADMISSION_INVALID else 2)
        os._exit(3)
    _, status = os.waitpid(child, 0)
    assert os.waitstatus_to_exitcode(status) == 0
    port.close_directory(root)


def test_capability_predicates_and_exact_names(monkeypatch) -> None:
    capability = detect_posix_capability_v1()
    assert capability.status is CapabilityStatusV1.AVAILABLE
    assert {
        "directory-inode-admission", "nonblocking-directory-flock",
        "crash-released-admission", "exec-closed-admission",
    } <= set(capability.features)
    assert not {
        "fork-revoked-admission", "nonblocking-root-admission",
        "fork-safe-root-lease", "nonblocking-root-lease",
    } & set(capability.features)
    assert detect_posix_capability_v1(
        platform_name="darwin", os_name="posix"
    ).status is CapabilityStatusV1.UNAVAILABLE

    monkeypatch.setattr(posix._fcntl, "flock", None)
    assert detect_posix_capability_v1().status is CapabilityStatusV1.UNAVAILABLE


def test_high_level_linux_capability_is_globally_sorted_and_digest_bound() -> None:
    filesystem = LocalFilesystemV1(
        PosixRetainedDirfdPortV1(), object(), native_platform="linux"
    )
    capability = filesystem.capability()
    expected = tuple(sorted((
        "descriptor_relative",
        "exclusive_create",
        "retained_dirfd",
        "crash-released-admission",
        "directory-inode-admission",
        "exec-closed-admission",
        "nonblocking-directory-flock",
    )))
    assert capability.status is CapabilityStatusV1.AVAILABLE
    assert capability.features == expected
    assert capability.capability_digest == digest_v1({
        "features": list(expected),
        "platform_family": "posix",
        "status": CapabilityStatusV1.AVAILABLE.value,
    })
