from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path

import pytest

import synaptic_host.local_io_v1.posix as posix_module
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1, _journal_record
from synaptic_host.local_io_v1.config import StorageRegistryV1
from synaptic_host.local_io_v1.model import (
    CapabilityStatusV1,
    BorrowPurposeV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RecoveryStatusV1,
    RetainedDirectoryV1,
    RetainedRootBorrowRequestV1,
    RootAccessV1,
    CreatePhaseV1,
    JournalPublishStatusV1,
    digest_v1,
)
from synaptic_host.local_io_v1.posix import (
    PosixRetainedDirfdPortV1,
    detect_posix_capability_v1,
)


def test_capability_detection_is_canonical_and_windows_adapter_construction_is_zero_call(monkeypatch) -> None:
    capability = detect_posix_capability_v1(platform_name="win32", os_name="nt")
    assert capability.platform_family == "windows"
    assert capability.status is CapabilityStatusV1.UNAVAILABLE
    assert capability.features == ()

    class NoCallWindowsOS:
        name = "nt"

        def __getattr__(self, name):
            raise AssertionError(f"unexpected operating-system access: {name}")

    monkeypatch.setattr(posix_module, "os", NoCallWindowsOS())
    with pytest.raises(LocalIOErrorV1) as caught:
        posix_module.PosixRetainedDirfdPortV1()
    assert caught.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE


def test_real_posix_retained_dirfd_lifecycle_and_handle_antiforgery(
    b42_ext4_root: Path, monkeypatch
) -> None:
    data_path = b42_ext4_root / "data"
    control_path = b42_ext4_root / "control"
    data_path.mkdir()
    control_path.mkdir()
    (data_path / "input.bin").write_bytes(b"payload")

    port = PosixRetainedDirfdPortV1()
    permits: dict[int, LocalRootPermitV1] = {}

    class Authenticator:
        def authenticate(self, permit):
            return permit if permits.get(id(permit)) is permit else None

    def binding(ref: str, path: Path) -> LocalRootBindingV1:
        permit_ref = "permit-" + ref
        canonical = {
            "access": RootAccessV1.READ_CREATE.value,
            "absolute_root": str(path),
            "authority_ref": "ext4-authority",
            "key_ref": "ext4-key",
            "permit_ref": permit_ref,
            "root_ref": ref,
        }
        permit = LocalRootPermitV1(
            permit_ref, ref, path, RootAccessV1.READ_CREATE,
            "ext4-authority", "ext4-key", digest_v1(canonical), "0" * 64,
        )
        permits[id(permit)] = permit
        return LocalRootBindingV1(
            ref, str(path), path, RootAccessV1.READ_CREATE,
            permit_ref, permit,
        )

    authenticator = Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    data = binding("opaque-ext4-data", data_path)
    control = binding("opaque-ext4-control", control_path)
    root = filesystem.retain_root_authority(data, control)
    source = filesystem.inspect_source(root, "input.bin", role="opaque-role")
    assert b"".join(filesystem.iter_source(root, source, chunk_size=3)) == b"payload"
    replacement = data_path / "replacement.bin"
    replacement.write_bytes(b"payload")
    replacement.replace(data_path / "input.bin")
    with pytest.raises(LocalIOErrorV1) as caught:
        list(filesystem.iter_source(root, source, chunk_size=3))
    assert caught.value.code is LocalIOCodeV1.SOURCE_CHANGED

    destination = filesystem.bind_destination(
        root,
        "artifact.bin",
        role="opaque-role",
        expected_size=7,
        expected_sha256=hashlib.sha256(b"payload").hexdigest(),
    )
    create = filesystem.authorize_create(root, destination)
    result = filesystem.create_once(root, create, destination, [b"pay", b"load"])
    assert result.status is RecoveryStatusV1.FOUND
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.FOUND
    assert (data_path / "artifact.bin").read_bytes() == b"payload"
    replay = filesystem.authorize_create(root, destination)
    assert filesystem.create_once(root, replay, destination, [b"payload"]).status is RecoveryStatusV1.FOUND

    forged = RetainedDirectoryV1(root.data_directory.handle_ref, root.data_directory.identity)
    with pytest.raises(LocalIOErrorV1) as caught:
        port.list_names_at(forged, 10)
    assert caught.value.code is LocalIOCodeV1.AUTHORITY_INVALID

    subdirectory = data_path / "child"
    subdirectory.mkdir()
    child = port.open_directory_at(root.data_directory, "child")
    port.close_directory(child)
    with pytest.raises(LocalIOErrorV1) as caught:
        port.list_names_at(child, 10)
    assert caught.value.code is LocalIOCodeV1.AUTHORITY_INVALID

    borrow = filesystem.borrow_root(
        root,
        RetainedRootBorrowRequestV1.build(
            root.authority_digest,
            BorrowPurposeV1.BUNDLE_DESTINATION_CREATE,
            RootAccessV1.READ_CREATE,
        ),
    )
    destination_purpose = BorrowPurposeV1.BUNDLE_DESTINATION_CREATE
    borrowed_root = filesystem.root_directory(borrow, purpose=destination_purpose)
    assert filesystem.mkdir_borrowed(
        borrow, borrowed_root, "borrow-bundle", purpose=destination_purpose
    )
    borrowed_directory = filesystem.open_borrowed_directory(
        borrow, borrowed_root, "borrow-bundle", purpose=destination_purpose
    )
    writable = filesystem.create_borrowed_file(
        borrow, borrowed_directory, "private", purpose=destination_purpose
    )
    assert filesystem.write_borrowed(
        borrow, writable, b"borrowed", purpose=destination_purpose
    ) == 8
    filesystem.fsync_borrowed_file(borrow, writable, purpose=destination_purpose)
    filesystem.close_borrowed_file(borrow, writable, purpose=destination_purpose)
    filesystem.link_borrowed(
        borrow, borrowed_directory, "private", "committed", purpose=destination_purpose
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.link_borrowed(
            borrow, borrowed_directory, "private", "committed", purpose=destination_purpose
        )
    assert caught.value.code is LocalIOCodeV1.DESTINATION_EXISTS
    filesystem.fsync_borrowed_directory(
        borrow, borrowed_directory, purpose=destination_purpose
    )
    filesystem.unlink_borrowed(
        borrow, borrowed_directory, "private", purpose=destination_purpose
    )
    filesystem.close_borrowed_directory(
        borrow, borrowed_directory, purpose=destination_purpose
    )
    filesystem.release_borrow(borrow, purpose=destination_purpose)

    source_purpose = BorrowPurposeV1.BUNDLE_SOURCE_READ
    source_borrow = filesystem.borrow_root(
        root,
        RetainedRootBorrowRequestV1.build(
            root.authority_digest, source_purpose, RootAccessV1.READ_ONLY
        ),
    )
    source_root = filesystem.root_directory(source_borrow, purpose=source_purpose)
    source_directory = filesystem.open_borrowed_directory(
        source_borrow, source_root, "borrow-bundle", purpose=source_purpose
    )
    reopened_identity = filesystem.stat_borrowed(
        source_borrow, source_root, "borrow-bundle", purpose=source_purpose
    )
    assert (reopened_identity.device, reopened_identity.inode) == (
        source_directory.identity.device,
        source_directory.identity.inode,
    )
    readable = filesystem.open_borrowed_read(
        source_borrow, source_directory, "committed", purpose=source_purpose
    )
    entered = threading.Event()
    resume = threading.Event()
    raw_read = port.read

    def blocked_read(file, maximum):
        entered.set()
        assert resume.wait(5)
        return raw_read(file, maximum)

    monkeypatch.setattr(port, "read", blocked_read)
    payloads = []
    thread = threading.Thread(target=lambda: payloads.append(
        filesystem.read_borrowed(
            source_borrow, readable, 16, purpose=source_purpose
        )
    ))
    thread.start()
    assert entered.wait(5)
    for close in (
        lambda: filesystem.close_borrowed_file(
            source_borrow, readable, purpose=source_purpose
        ),
        lambda: filesystem.close_borrowed_directory(
            source_borrow, source_directory, purpose=source_purpose
        ),
        lambda: filesystem.release_borrow(source_borrow, purpose=source_purpose),
        lambda: filesystem.release_root_authority(root),
    ):
        with pytest.raises(LocalIOErrorV1) as caught:
            close()
        assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    resume.set()
    thread.join(5)
    assert payloads == [b"borrowed"]
    monkeypatch.setattr(port, "read", raw_read)
    assert filesystem.read_borrowed(
        source_borrow, readable, 16, purpose=source_purpose
    ) == b""
    filesystem.close_borrowed_file(
        source_borrow, readable, purpose=source_purpose
    )

    os.symlink("committed", data_path / "borrow-bundle" / "symlink")
    os.link(
        data_path / "borrow-bundle" / "committed",
        data_path / "borrow-bundle" / "hardlink",
    )
    for name in ("symlink", "committed"):
        with pytest.raises(LocalIOErrorV1):
            filesystem.open_borrowed_read(
                source_borrow, source_directory, name, purpose=source_purpose
            )
    os.unlink(data_path / "borrow-bundle" / "hardlink")
    filesystem.close_borrowed_directory(
        source_borrow, source_directory, purpose=source_purpose
    )
    filesystem.release_borrow(source_borrow, purpose=source_purpose)

    verify_purpose = BorrowPurposeV1.BUNDLE_MOUNT_VERIFY
    verify_borrow = filesystem.borrow_root(
        root,
        RetainedRootBorrowRequestV1.build(
            root.authority_digest, verify_purpose, RootAccessV1.READ_ONLY
        ),
    )
    verify_root = filesystem.root_directory(verify_borrow, purpose=verify_purpose)
    replaced_root = b42_ext4_root / "data-replaced"
    data_path.rename(replaced_root)
    data_path.mkdir()
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed(
            verify_borrow, verify_root, "borrow-bundle", purpose=verify_purpose
        )
    assert caught.value.code is LocalIOCodeV1.ROOT_CHANGED
    filesystem.release_borrow(verify_borrow, purpose=verify_purpose)
    filesystem.release_root_authority(root)


def test_real_ext4_hardlink_pair_read_and_hostile_revalidation(
    b42_ext4_root: Path,
) -> None:
    data_path = b42_ext4_root / "pair-data"
    control_path = b42_ext4_root / "pair-control"
    data_path.mkdir()
    control_path.mkdir()
    payload = b"canonical-marker"
    (data_path / "COMMIT-pair").write_bytes(payload)
    os.link(data_path / "COMMIT-pair", data_path / "companion-pair")

    port = PosixRetainedDirfdPortV1()
    permits: dict[int, LocalRootPermitV1] = {}

    class Authenticator:
        def authenticate(self, permit):
            return permit if permits.get(id(permit)) is permit else None

    def binding(ref: str, path: Path) -> LocalRootBindingV1:
        permit_ref = "permit-" + ref
        canonical = {
            "access": RootAccessV1.READ_CREATE.value,
            "absolute_root": str(path),
            "authority_ref": "pair-authority",
            "key_ref": "pair-key",
            "permit_ref": permit_ref,
            "root_ref": ref,
        }
        permit = LocalRootPermitV1(
            permit_ref, ref, path, RootAccessV1.READ_CREATE,
            "pair-authority", "pair-key", digest_v1(canonical), "0" * 64,
        )
        permits[id(permit)] = permit
        return LocalRootBindingV1(
            ref, str(path), path, RootAccessV1.READ_CREATE, permit_ref, permit
        )

    filesystem = LocalFilesystemV1(port, Authenticator(), native_platform="linux")
    authority = filesystem.retain_root_authority(
        binding("pair-data", data_path), binding("pair-control", control_path)
    )
    purpose = BorrowPurposeV1.BUNDLE_MOUNT_VERIFY
    borrow = filesystem.borrow_root(
        authority,
        RetainedRootBorrowRequestV1.build(
            authority.authority_digest, purpose, RootAccessV1.READ_ONLY
        ),
    )
    root = filesystem.root_directory(borrow, purpose=purpose)
    with pytest.raises(LocalIOErrorV1):
        filesystem.open_borrowed_read(
            borrow, root, "COMMIT-pair", purpose=purpose
        )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "companion-pair", "COMMIT-pair", purpose=purpose
    )
    assert filesystem.stat_borrowed_hardlink_pair(
        borrow, pair, purpose=purpose
    ).nlink == 2
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 7, purpose=purpose
    ) == payload[:7]
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1024, purpose=purpose
    ) == payload[7:]
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=purpose
    ) == b""
    filesystem.close_borrowed_hardlink_pair(borrow, pair, purpose=purpose)

    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "COMMIT-pair", "companion-pair", purpose=purpose
    )
    os.link(data_path / "COMMIT-pair", data_path / "third-link")
    with pytest.raises(LocalIOErrorV1) as third:
        filesystem.stat_borrowed_hardlink_pair(borrow, pair, purpose=purpose)
    assert third.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    with pytest.raises(LocalIOErrorV1):
        filesystem.close_borrowed_hardlink_pair(borrow, pair, purpose=purpose)
    os.unlink(data_path / "third-link")

    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "COMMIT-pair", "companion-pair", purpose=purpose
    )
    replacement = data_path / "replacement"
    replacement.write_bytes(payload)
    replacement.replace(data_path / "companion-pair")
    with pytest.raises(LocalIOErrorV1) as replaced:
        filesystem.stat_borrowed_hardlink_pair(borrow, pair, purpose=purpose)
    assert replaced.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    with pytest.raises(LocalIOErrorV1):
        filesystem.close_borrowed_hardlink_pair(borrow, pair, purpose=purpose)
    filesystem.release_borrow(borrow, purpose=purpose)
    filesystem.release_root_authority(authority)


def test_real_ext4_race_hardlink_leftover_and_no_replace_contract(b42_ext4_root: Path) -> None:
    data_path = b42_ext4_root / "hostile data"
    control_path = b42_ext4_root / "hostile control"
    data_path.mkdir()
    control_path.mkdir()
    (data_path / "nested").mkdir()
    (data_path / "nested" / "input").write_bytes(b"payload")

    config_path = b42_ext4_root / "hostile-storage.json"
    config_path.write_text(json.dumps({
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {"root_ref": "data", "location": str(data_path), "access": "read_create", "permit_ref": "permit-data"},
            {"root_ref": "control", "location": str(control_path), "access": "read_create", "permit_ref": "permit-control"},
        ],
    }), encoding="utf-8")

    def registry() -> StorageRegistryV1:
        result = StorageRegistryV1.load(config_path, project_root=b42_ext4_root)
        for ref in ("data", "control"):
            result.issue_root_permit(
                ref, authority_ref="ext4-authority", key_ref="ext4-key", proof_digest="0" * 64
            )
        return result

    port = PosixRetainedDirfdPortV1()
    first_registry = registry()
    filesystem = LocalFilesystemV1(port, first_registry, native_platform="linux")
    root = filesystem.retain_root_authority(
        first_registry.resolve("data"), first_registry.resolve("control")
    )

    source = filesystem.inspect_source(root, "nested/input", role="role")
    os.rename(data_path / "nested", data_path / "nested-old")
    (data_path / "nested").mkdir()
    (data_path / "nested" / "input").write_bytes(b"payload")
    with pytest.raises(LocalIOErrorV1):
        list(filesystem.iter_source(root, source))

    (data_path / "hardlink-source").write_bytes(b"payload")
    os.link(data_path / "hardlink-source", data_path / "hardlink-alias")
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(root, "hardlink-source", role="role")
    assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE

    sentinel = data_path / "preexisting"
    sentinel.write_bytes(b"sentinel")
    os.link(sentinel, data_path / "preexisting-alias")
    preexisting = filesystem.bind_destination(
        root, "preexisting", role="role", expected_size=7,
        expected_sha256=hashlib.sha256(b"payload").hexdigest(),
    )
    result = filesystem.create_once(
        root, filesystem.authorize_create(root, preexisting), preexisting, [b"payload"]
    )
    assert result.status is RecoveryStatusV1.CONFLICT
    assert sentinel.read_bytes() == b"sentinel"
    assert (data_path / "preexisting-alias").read_bytes() == b"sentinel"

    destination = filesystem.bind_destination(
        root, "leftover-artifact", role="role", expected_size=7,
        expected_sha256=hashlib.sha256(b"payload").hexdigest(),
    )
    mutation_id = filesystem.authorize_create(root, destination).mutation_id
    journal_directory = control_path / (".journal-" + mutation_id)
    journal_directory.mkdir()
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.INDETERMINATE
    (journal_directory / (".private-" + "a" * 32)).write_bytes(b"partial")
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.INDETERMINATE

    concurrent_mutation = digest_v1({"concurrent": mutation_id})
    staging_name = ".synaptic-" + concurrent_mutation[:32]
    record = _journal_record(
        mutation_id=concurrent_mutation,
        destination_digest=destination.destination_digest,
        phase=CreatePhaseV1.CLAIMED,
        previous=None,
        staging_name=staging_name,
        identity=None,
    )
    barrier = threading.Barrier(2)

    class RacingPort(PosixRetainedDirfdPortV1):
        def _read_journal_fd(self, directory_fd, maximum):
            value = super()._read_journal_fd(directory_fd, maximum)
            if maximum == 4 and value == ((), False):
                barrier.wait(timeout=5)
            return value

    first_race_port = RacingPort()
    second_race_port = RacingPort()
    first_control = first_race_port.retain_directory(control_path)
    second_control = second_race_port.retain_directory(control_path)
    results = []

    def publish(adapter, control) -> None:
        results.append(adapter.publish_journal(control, concurrent_mutation, None, record))

    threads = [
        threading.Thread(target=publish, args=(first_race_port, first_control)),
        threading.Thread(target=publish, args=(second_race_port, second_control)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sorted(result.status.value for result in results) == sorted([
        JournalPublishStatusV1.PUBLISHED.value,
        JournalPublishStatusV1.EXISTS_IDENTICAL.value,
    ])
    marker_directory = control_path / (".journal-" + concurrent_mutation)
    marker_names = sorted(path.name for path in marker_directory.iterdir())
    assert marker_names == ["0-claimed.json"]
    assert (marker_directory / marker_names[0]).stat().st_nlink == 1
    first_race_port.close_directory(first_control)
    second_race_port.close_directory(second_control)

    durable = filesystem.bind_destination(
        root, "durable", role="role", expected_size=7,
        expected_sha256=hashlib.sha256(b"payload").hexdigest(),
    )
    assert filesystem.create_once(
        root, filesystem.authorize_create(root, durable), durable, [b"payload"]
    ).status is RecoveryStatusV1.FOUND
    second_registry = registry()
    replay_port = PosixRetainedDirfdPortV1()
    replay_filesystem = LocalFilesystemV1(replay_port, second_registry, native_platform="linux")
    replay_root = replay_filesystem.retain_root_authority(
        second_registry.resolve("data"), second_registry.resolve("control")
    )
    assert replay_root.data_directory.identity.canonical() != root.data_directory.identity.canonical()
    assert replay_root.control_directory.identity.canonical() != root.control_directory.identity.canonical()
    assert (
        replay_root.data_directory.identity.device,
        replay_root.data_directory.identity.inode,
        replay_root.data_directory.identity.mode & 0o170000,
    ) == (
        root.data_directory.identity.device,
        root.data_directory.identity.inode,
        root.data_directory.identity.mode & 0o170000,
    )
    assert replay_root.authority_digest == root.authority_digest
    assert replay_filesystem.recover_create(replay_root, durable).status is RecoveryStatusV1.FOUND
    replay_filesystem.release_root_authority(replay_root)

    displaced = b42_ext4_root / "hostile data displaced"
    os.rename(data_path, displaced)
    data_path.mkdir()
    replacement_registry = registry()
    replacement_port = PosixRetainedDirfdPortV1()
    replacement_filesystem = LocalFilesystemV1(
        replacement_port, replacement_registry, native_platform="linux"
    )
    replacement_root = replacement_filesystem.retain_root_authority(
        replacement_registry.resolve("data"), replacement_registry.resolve("control")
    )
    assert replacement_root.authority_digest != root.authority_digest
    with pytest.raises(LocalIOErrorV1) as caught:
        replacement_filesystem.recover_create(replacement_root, durable)
    assert caught.value.code is LocalIOCodeV1.DESTINATION_INVALID
    replacement_filesystem.release_root_authority(replacement_root)
    filesystem.release_root_authority(root)
