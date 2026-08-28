from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from threading import Event, Thread

import pytest

from synaptic_host.local_io_v1.filesystem import (
    LocalFilesystemV1,
    MAX_CHUNK_BYTES,
)
from synaptic_host.local_io_v1.config import StorageRegistryV1
from synaptic_host.local_io_v1.model import (
    BorrowedDirectoryV1,
    BorrowedFileV1,
    BorrowedHardlinkPairV1,
    BorrowPurposeV1,
    CreateJournalRecordV1,
    CreatePhaseV1,
    LocalArtifactBindingV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    LocalRootAuthorityV1,
    LocalSourceBindingV1,
    RecoveryResultV1,
    RetainedDirectoryV1,
    RetainedRootBorrowRequestV1,
    RetainedRootBorrowV1,
    RecoveryStatusV1,
    RootAccessV1,
    MAX_BORROWED_HARDLINK_PAIR_BYTES,
    validate_recovery_result_v1,
    journal_record_bytes_v1,
    parse_journal_record_v1,
    digest_v1,
    root_authority_digest_v1,
)

from .conftest import FakePosixFilesystemPortV1


class _Authenticator:
    def __init__(self) -> None:
        self.permits: dict[int, LocalRootPermitV1] = {}
        self.calls = 0

    def allow(self, permit: LocalRootPermitV1) -> None:
        self.permits[id(permit)] = permit

    def authenticate(self, permit: LocalRootPermitV1):
        self.calls += 1
        return permit if self.permits.get(id(permit)) is permit else None


def _binding(
    path: Path, ref: str, access: RootAccessV1, authenticator: _Authenticator
) -> LocalRootBindingV1:
    absolute = path.absolute()
    permit_ref = "permit-" + ref
    canonical = {
        "access": access.value,
        "absolute_root": str(absolute),
        "authority_ref": "authority-test",
        "key_ref": "key-test",
        "permit_ref": permit_ref,
        "root_ref": ref,
    }
    from synaptic_host.local_io_v1.model import digest_v1

    permit = LocalRootPermitV1(
        permit_ref, ref, absolute, access, "authority-test", "key-test",
        digest_v1(canonical), "0" * 64,
    )
    authenticator.allow(permit)
    return LocalRootBindingV1(
        ref, f"project://{ref}", absolute, access, permit_ref, permit
    )


def _composition(profile: str = "opaque-local-like"):
    port = FakePosixFilesystemPortV1()
    fake_base = Path.cwd() / ".fake-metadata" / profile
    data_path = fake_base / "data"
    control_path = fake_base / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    authenticator = _Authenticator()
    data = _binding(data_path, profile, RootAccessV1.READ_CREATE, authenticator)
    control = _binding(control_path, profile + "-control", RootAccessV1.READ_CREATE, authenticator)
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(data, control)
    return port, filesystem, authority


def _composition_with_data_access(access: RootAccessV1):
    port = FakePosixFilesystemPortV1()
    fake_base = Path.cwd() / ".fake-metadata" / ("access-" + access.value)
    data_path = fake_base / "data"
    control_path = fake_base / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    authenticator = _Authenticator()
    data = _binding(data_path, "data-access", access, authenticator)
    control = _binding(
        control_path, "control-access", RootAccessV1.READ_CREATE, authenticator
    )
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    return port, filesystem, filesystem.retain_root_authority(data, control)


DESTINATION_PURPOSE = BorrowPurposeV1.BUNDLE_DESTINATION_CREATE
SOURCE_PURPOSE = BorrowPurposeV1.BUNDLE_SOURCE_READ
VERIFY_PURPOSE = BorrowPurposeV1.BUNDLE_MOUNT_VERIFY


def _borrow(filesystem, authority, access=RootAccessV1.READ_CREATE,
            purpose=DESTINATION_PURPOSE):
    request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, purpose, access
    )
    borrow = filesystem.borrow_root(authority, request)
    return borrow, filesystem.root_directory(borrow, purpose=purpose)


def _add_hardlink_pair(port, first="commit", second="companion", payload=b"marker"):
    node = port.add_file("dir-data", first, payload, nlink=2)
    port.directories["dir-data"][second] = node
    return node


def test_borrow_full_descriptor_relative_lifecycle_and_opaque_dtos() -> None:
    port, filesystem, authority = _composition()
    borrow, root = _borrow(filesystem, authority)
    assert not any(hasattr(borrow, name) for name in ("port", "permit", "absolute_root", "handle_ref"))
    assert not any(hasattr(root, name) for name in ("port", "permit", "absolute_root", "handle_ref"))

    assert filesystem.mkdir_borrowed(borrow, root, "bundle", purpose=DESTINATION_PURPOSE)
    directory = filesystem.open_borrowed_directory(
        borrow, root, "bundle", purpose=DESTINATION_PURPOSE
    )
    writable = filesystem.create_borrowed_file(
        borrow, directory, "private", purpose=DESTINATION_PURPOSE
    )
    assert filesystem.write_borrowed(
        borrow, writable, b"payload", purpose=DESTINATION_PURPOSE
    ) == 7
    assert filesystem.stat_borrowed_file(
        borrow, writable, purpose=DESTINATION_PURPOSE
    ).size == 7
    filesystem.fsync_borrowed_file(borrow, writable, purpose=DESTINATION_PURPOSE)
    filesystem.close_borrowed_file(borrow, writable, purpose=DESTINATION_PURPOSE)
    filesystem.link_borrowed(
        borrow, directory, "private", "committed", purpose=DESTINATION_PURPOSE
    )
    filesystem.fsync_borrowed_directory(borrow, directory, purpose=DESTINATION_PURPOSE)
    assert set(filesystem.list_borrowed_directory(
        borrow, directory, 3, purpose=DESTINATION_PURPOSE
    )) == {"private", "committed"}
    assert filesystem.stat_borrowed(
        borrow, directory, "committed", purpose=DESTINATION_PURPOSE
    ).size == 7
    filesystem.unlink_borrowed(
        borrow, directory, "private", purpose=DESTINATION_PURPOSE
    )
    filesystem.close_borrowed_directory(
        borrow, directory, purpose=DESTINATION_PURPOSE
    )
    filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)

    read_borrow, read_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    read_directory = filesystem.open_borrowed_directory(
        read_borrow, read_root, "bundle", purpose=SOURCE_PURPOSE
    )
    reopened_identity = filesystem.stat_borrowed(
        read_borrow, read_root, "bundle", purpose=SOURCE_PURPOSE
    )
    assert (reopened_identity.device, reopened_identity.inode) == (
        read_directory.identity.device,
        read_directory.identity.inode,
    )
    readable = filesystem.open_borrowed_read(
        read_borrow, read_directory, "committed", purpose=SOURCE_PURPOSE
    )
    assert filesystem.read_borrowed(
        read_borrow, readable, 16, purpose=SOURCE_PURPOSE
    ) == b"payload"
    assert filesystem.read_borrowed(
        read_borrow, readable, 16, purpose=SOURCE_PURPOSE
    ) == b""
    filesystem.close_borrowed_file(
        read_borrow, readable, purpose=SOURCE_PURPOSE
    )
    filesystem.close_borrowed_directory(
        read_borrow, read_directory, purpose=SOURCE_PURPOSE
    )
    filesystem.release_borrow(read_borrow, purpose=SOURCE_PURPOSE)
    filesystem.release_root_authority(authority)
    assert not port.live_directories and not port.live_files


def test_borrow_dto_schema_digests_reject_field_substitution() -> None:
    _, filesystem, authority = _composition()
    request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, DESTINATION_PURPOSE, RootAccessV1.READ_CREATE
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        replace(request, purpose=SOURCE_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    borrow = filesystem.borrow_root(authority, request)
    root = filesystem.root_directory(borrow, purpose=DESTINATION_PURPOSE)
    with pytest.raises(LocalIOErrorV1):
        replace(borrow, access=RootAccessV1.READ_ONLY)
    with pytest.raises(LocalIOErrorV1):
        replace(root, path_components=("foreign",), owns_handle=True)
    filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong"),
        ("root_authority_digest", "f" * 64),
        ("purpose", SOURCE_PURPOSE),
        ("access", RootAccessV1.READ_ONLY),
        ("request_digest", "f" * 64),
    ],
)
def test_mutated_borrow_request_fails_before_authentication_or_port(
    field, value
) -> None:
    port, filesystem, authority = _composition()
    request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, DESTINATION_PURPOSE, RootAccessV1.READ_CREATE
    )
    object.__setattr__(request, field, value)
    before_trace = tuple(port.trace)
    before_auth = filesystem._permit_authenticator.calls
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.borrow_root(authority, request)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before_trace
    assert filesystem._permit_authenticator.calls == before_auth
    assert not filesystem._live_borrows


def _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth):
    assert tuple(port.trace) == before_trace
    assert filesystem._permit_authenticator.calls == before_auth


def test_borrow_mutate_and_recompute_cannot_rewrite_issuance_snapshot() -> None:
    port, filesystem, authority = _composition("borrow-snapshot")
    borrow, root = _borrow(filesystem, authority)
    original = (
        borrow.purpose,
        borrow.access,
        borrow.request_digest,
        borrow.borrow_digest,
    )
    object.__setattr__(borrow, "purpose", SOURCE_PURPOSE)
    object.__setattr__(borrow, "access", RootAccessV1.READ_ONLY)
    object.__setattr__(borrow, "request_digest", digest_v1({
        "access": borrow.access.value,
        "purpose": borrow.purpose.value,
        "root_authority_digest": borrow.root_authority_digest,
        "schema_version": "synaptic-host-root-borrow-request/v1",
    }))
    object.__setattr__(
        borrow, "borrow_digest", digest_v1(borrow.canonical_without_digest())
    )
    before_trace = tuple(port.trace)
    before_auth = filesystem._permit_authenticator.calls
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, root, 1, purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)

    for field, value in zip(
        ("purpose", "access", "request_digest", "borrow_digest"), original
    ):
        object.__setattr__(borrow, field, value)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, root, 1, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)


@pytest.mark.parametrize("child_kind", ["root", "directory", "file"])
def test_child_mutate_and_recompute_is_permanently_fenced_before_auth_or_port(
    child_kind,
) -> None:
    port, filesystem, authority = _composition("child-snapshot-" + child_kind)
    borrow, root = _borrow(filesystem, authority)
    target = root
    call = lambda: filesystem.list_borrowed_directory(
        borrow, root, 1, purpose=DESTINATION_PURPOSE
    )
    if child_kind == "directory":
        assert filesystem.mkdir_borrowed(
            borrow, root, "child", purpose=DESTINATION_PURPOSE
        )
        target = filesystem.open_borrowed_directory(
            borrow, root, "child", purpose=DESTINATION_PURPOSE
        )
        call = lambda: filesystem.list_borrowed_directory(
            borrow, target, 1, purpose=DESTINATION_PURPOSE
        )
    elif child_kind == "file":
        target = filesystem.create_borrowed_file(
            borrow, root, "private", purpose=DESTINATION_PURPOSE
        )
        call = lambda: filesystem.stat_borrowed_file(
            borrow, target, purpose=DESTINATION_PURPOSE
        )

    if child_kind == "file":
        original = (target.readable, target.writable, target.file_digest)
        object.__setattr__(target, "readable", True)
        object.__setattr__(target, "writable", False)
        object.__setattr__(
            target, "file_digest", digest_v1(target.canonical_without_digest())
        )
    else:
        original = (target.identity, target.directory_digest)
        changed = LocalFileIdentityV1(
            target.identity.device,
            target.identity.inode,
            target.identity.mode,
            target.identity.nlink,
            target.identity.changed_ns + 1,
            target.identity.modified_ns,
            target.identity.size,
        )
        object.__setattr__(target, "identity", changed)
        object.__setattr__(
            target,
            "directory_digest",
            digest_v1(target.canonical_without_digest()),
        )
    before_trace = tuple(port.trace)
    before_auth = filesystem._permit_authenticator.calls
    with pytest.raises(LocalIOErrorV1) as caught:
        call()
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)

    if child_kind == "file":
        for field, value in zip(("readable", "writable", "file_digest"), original):
            object.__setattr__(target, field, value)
    else:
        object.__setattr__(target, "identity", original[0])
        object.__setattr__(target, "directory_digest", original[1])
    with pytest.raises(LocalIOErrorV1) as caught:
        call()
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)


def test_mutated_internal_issuance_snapshot_cannot_be_restored_by_visible_dto() -> None:
    port, filesystem, authority = _composition("registry-snapshot")
    borrow, root = _borrow(filesystem, authority)
    issued_ref = filesystem._directory_object_refs[id(root)]
    issuance = filesystem._directory_issuance[issued_ref]
    filesystem._directory_issuance[issued_ref] = replace(
        issuance, owns_handle=not issuance.owns_handle
    )
    before_trace = tuple(port.trace)
    before_auth = filesystem._permit_authenticator.calls
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, root, 1, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)

    filesystem._directory_issuance[issued_ref] = issuance
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, root, 1, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)


def test_combined_borrow_directory_and_file_mutation_fails_before_boundary_calls() -> None:
    port, filesystem, authority = _composition("combined-snapshot")
    borrow, root = _borrow(filesystem, authority)
    file = filesystem.create_borrowed_file(
        borrow, root, "private", purpose=DESTINATION_PURPOSE
    )
    object.__setattr__(borrow, "purpose", SOURCE_PURPOSE)
    object.__setattr__(borrow, "access", RootAccessV1.READ_ONLY)
    object.__setattr__(borrow, "request_digest", digest_v1({
        "access": borrow.access.value,
        "purpose": borrow.purpose.value,
        "root_authority_digest": borrow.root_authority_digest,
        "schema_version": "synaptic-host-root-borrow-request/v1",
    }))
    object.__setattr__(
        borrow, "borrow_digest", digest_v1(borrow.canonical_without_digest())
    )
    changed_root = LocalFileIdentityV1(
        root.identity.device, root.identity.inode, root.identity.mode,
        root.identity.nlink, root.identity.changed_ns + 1,
        root.identity.modified_ns, root.identity.size,
    )
    object.__setattr__(root, "identity", changed_root)
    object.__setattr__(
        root, "directory_digest", digest_v1(root.canonical_without_digest())
    )
    object.__setattr__(file, "readable", True)
    object.__setattr__(file, "writable", False)
    object.__setattr__(file, "file_digest", digest_v1(file.canonical_without_digest()))
    before_trace = tuple(port.trace)
    before_auth = filesystem._permit_authenticator.calls
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed_file(borrow, file, purpose=SOURCE_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    _assert_zero_boundary_calls(port, filesystem, before_trace, before_auth)


def test_admitted_file_effect_uses_captured_refs_and_exact_pin_counters() -> None:
    port, filesystem, authority = _composition("admitted-file")
    port.add_file("dir-data", "first", b"first")
    port.add_file("dir-data", "second", b"second")
    first_borrow, first_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    second_borrow, second_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    first_file = filesystem.open_borrowed_read(
        first_borrow, first_root, "first", purpose=SOURCE_PURPOSE
    )
    second_file = filesystem.open_borrowed_read(
        second_borrow, second_root, "second", purpose=SOURCE_PURPOSE
    )
    first_borrow_ref = filesystem._borrow_object_refs[id(first_borrow)]
    second_borrow_ref = filesystem._borrow_object_refs[id(second_borrow)]
    first_file_ref = filesystem._file_object_refs[id(first_file)]
    second_file_ref = filesystem._file_object_refs[id(second_file)]
    entered = Event()
    resume = Event()
    values = []
    errors = []

    def hold_read():
        entered.set()
        assert resume.wait(2)

    def run_read():
        try:
            values.append(filesystem.read_borrowed(
                first_borrow, first_file, 16, purpose=SOURCE_PURPOSE
            ))
        except BaseException as error:
            errors.append(error)

    port.callbacks["read"] = hold_read
    thread = Thread(target=run_read)
    thread.start()
    assert entered.wait(2)
    object.__setattr__(first_borrow, "borrow_ref", second_borrow_ref)
    object.__setattr__(first_file, "file_ref", second_file_ref)
    assert filesystem._borrow_inflight[first_borrow_ref] == 1
    assert filesystem._borrow_inflight[second_borrow_ref] == 0
    assert filesystem._borrow_file_inflight[first_file_ref] == 1
    assert filesystem._borrow_file_inflight[second_file_ref] == 0
    filesystem.close_borrowed_file(
        second_borrow, second_file, purpose=SOURCE_PURPOSE
    )
    filesystem.release_borrow(second_borrow, purpose=SOURCE_PURPOSE)
    resume.set()
    thread.join(2)
    assert not errors and values == [b"first"]
    assert filesystem._borrow_inflight[first_borrow_ref] == 0
    assert filesystem._borrow_file_inflight[first_file_ref] == 0
    object.__setattr__(first_borrow, "borrow_ref", first_borrow_ref)
    object.__setattr__(first_file, "file_ref", first_file_ref)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed_file(
            first_borrow, first_file, purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID


def test_admitted_directory_effect_cannot_transfer_borrow_or_directory_pins() -> None:
    port, filesystem, authority = _composition("admitted-directory")
    first_borrow, first_root = _borrow(filesystem, authority)
    second_borrow, second_root = _borrow(filesystem, authority)
    assert filesystem.mkdir_borrowed(
        first_borrow, first_root, "child", purpose=DESTINATION_PURPOSE
    )
    child = filesystem.open_borrowed_directory(
        first_borrow, first_root, "child", purpose=DESTINATION_PURPOSE
    )
    first_borrow_ref = filesystem._borrow_object_refs[id(first_borrow)]
    second_borrow_ref = filesystem._borrow_object_refs[id(second_borrow)]
    child_ref = filesystem._directory_object_refs[id(child)]
    second_root_ref = filesystem._directory_object_refs[id(second_root)]
    entered = Event()
    resume = Event()
    values = []
    errors = []

    def hold_list():
        entered.set()
        assert resume.wait(2)

    def run_list():
        try:
            values.append(filesystem.list_borrowed_directory(
                first_borrow, child, 2, purpose=DESTINATION_PURPOSE
            ))
        except BaseException as error:
            errors.append(error)

    port.callbacks["list_names_at"] = hold_list
    thread = Thread(target=run_list)
    thread.start()
    assert entered.wait(2)
    object.__setattr__(first_borrow, "borrow_ref", second_borrow_ref)
    object.__setattr__(child, "directory_ref", second_root_ref)
    assert filesystem._borrow_inflight[first_borrow_ref] == 1
    assert filesystem._borrow_inflight[second_borrow_ref] == 0
    assert filesystem._borrow_directory_inflight[child_ref] == 1
    assert filesystem._borrow_directory_inflight[second_root_ref] == 0
    filesystem.release_borrow(second_borrow, purpose=DESTINATION_PURPOSE)
    resume.set()
    thread.join(2)
    assert not errors and values == [()]
    assert filesystem._borrow_inflight[first_borrow_ref] == 0
    assert filesystem._borrow_directory_inflight[child_ref] == 0
    object.__setattr__(first_borrow, "borrow_ref", first_borrow_ref)
    object.__setattr__(child, "directory_ref", child_ref)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            first_borrow, child, 2, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID


def test_admitted_verification_ignores_late_path_identity_and_access_mutation() -> None:
    port, filesystem, authority = _composition("admitted-verification")
    port.add_file("dir-data", "source", b"payload")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    file = filesystem.open_borrowed_read(
        borrow, root, "source", purpose=SOURCE_PURPOSE
    )
    original = (
        borrow.access,
        file.path_components,
        file.identity,
    )

    def mutate_during_verification():
        object.__setattr__(borrow, "access", RootAccessV1.CREATE_ONLY)
        object.__setattr__(file, "path_components", ("other",))
        object.__setattr__(file, "identity", LocalFileIdentityV1(
            file.identity.device,
            file.identity.inode + 100,
            file.identity.mode,
            file.identity.nlink,
            file.identity.changed_ns,
            file.identity.modified_ns,
            file.identity.size,
        ))

    port.callbacks["stat_at:source"] = mutate_during_verification
    assert filesystem.read_borrowed(
        borrow, file, 16, purpose=SOURCE_PURPOSE
    ) == b"payload"
    for field, value in zip(("access",), original[:1]):
        object.__setattr__(borrow, field, value)
    object.__setattr__(file, "path_components", original[1])
    object.__setattr__(file, "identity", original[2])
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed_file(borrow, file, purpose=SOURCE_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID


def test_admitted_close_uses_captured_refs_for_exact_cleanup() -> None:
    port, filesystem, authority = _composition("admitted-close")
    port.add_file("dir-data", "first", b"first")
    port.add_file("dir-data", "second", b"second")
    first_borrow, first_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    second_borrow, second_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    first_file = filesystem.open_borrowed_read(
        first_borrow, first_root, "first", purpose=SOURCE_PURPOSE
    )
    second_file = filesystem.open_borrowed_read(
        second_borrow, second_root, "second", purpose=SOURCE_PURPOSE
    )
    first_borrow_ref = filesystem._borrow_object_refs[id(first_borrow)]
    second_borrow_ref = filesystem._borrow_object_refs[id(second_borrow)]
    first_file_ref = filesystem._file_object_refs[id(first_file)]
    second_file_ref = filesystem._file_object_refs[id(second_file)]
    entered = Event()
    resume = Event()
    errors = []

    def hold_close():
        entered.set()
        assert resume.wait(2)

    def run_close():
        try:
            filesystem.close_borrowed_file(
                first_borrow, first_file, purpose=SOURCE_PURPOSE
            )
        except BaseException as error:
            errors.append(error)

    port.callbacks["close_file"] = hold_close
    thread = Thread(target=run_close)
    thread.start()
    assert entered.wait(2)
    object.__setattr__(first_borrow, "borrow_ref", second_borrow_ref)
    object.__setattr__(first_file, "file_ref", second_file_ref)
    assert first_file_ref in filesystem._closing_borrow_files
    assert second_file_ref not in filesystem._closing_borrow_files
    assert filesystem._borrow_inflight[first_borrow_ref] == 1
    assert filesystem._borrow_inflight[second_borrow_ref] == 0
    assert filesystem._borrow_file_inflight[first_file_ref] == 0
    assert filesystem._borrow_file_inflight[second_file_ref] == 0
    resume.set()
    thread.join(2)
    assert not errors
    assert first_file_ref not in filesystem._borrow_files
    assert first_file_ref not in filesystem._file_issuance
    assert first_file_ref not in filesystem._borrow_file_inflight
    assert first_file_ref not in filesystem._closing_borrow_files
    assert second_file_ref in filesystem._borrow_files
    assert filesystem._borrow_inflight[second_borrow_ref] == 0
    assert filesystem._borrow_file_inflight[second_file_ref] == 0
    object.__setattr__(first_borrow, "borrow_ref", first_borrow_ref)
    object.__setattr__(first_file, "file_ref", first_file_ref)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed_file(
            first_borrow, first_file, purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    filesystem.close_borrowed_file(
        second_borrow, second_file, purpose=SOURCE_PURPOSE
    )
    filesystem.release_borrow(second_borrow, purpose=SOURCE_PURPOSE)


def test_blocked_authenticator_cannot_escalate_captured_source_authority() -> None:
    port, filesystem, authority = _composition("blocked-auth-capture")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    borrow_ref = filesystem._borrow_object_refs[id(borrow)]
    root_ref = filesystem._directory_object_refs[id(root)]
    original_purpose = borrow.purpose
    original_access = borrow.access
    authenticator = filesystem._permit_authenticator
    original_authenticate = authenticator.authenticate
    entered = Event()
    resume = Event()
    errors = []
    before_entries = tuple(port.directories["dir-data"])
    before_trace = tuple(port.trace)

    def blocked_authenticate(permit):
        entered.set()
        assert resume.wait(2)
        return original_authenticate(permit)

    def run_mkdir():
        try:
            filesystem.mkdir_borrowed(
                borrow, root, "forbidden", purpose=SOURCE_PURPOSE
            )
        except BaseException as error:
            errors.append(error)

    authenticator.authenticate = blocked_authenticate
    thread = Thread(target=run_mkdir)
    thread.start()
    assert entered.wait(2)
    object.__setattr__(borrow, "purpose", DESTINATION_PURPOSE)
    object.__setattr__(borrow, "access", RootAccessV1.READ_CREATE)
    resume.set()
    thread.join(2)
    authenticator.authenticate = original_authenticate
    assert len(errors) == 1
    assert type(errors[0]) is LocalIOErrorV1
    assert errors[0].code is LocalIOCodeV1.ACCESS_MISMATCH
    assert "mkdir_at" not in port.trace[len(before_trace):]
    assert tuple(port.directories["dir-data"]) == before_entries
    assert filesystem._borrow_inflight[borrow_ref] == 0
    assert filesystem._borrow_directory_inflight[root_ref] == 0
    object.__setattr__(borrow, "purpose", original_purpose)
    object.__setattr__(borrow, "access", original_access)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, root, 2, purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID


def test_capture_uses_issuance_ancestry_after_visible_child_mutation() -> None:
    port, filesystem, authority = _composition("capture-issuance-ancestry")
    borrow, root = _borrow(filesystem, authority)
    assert filesystem.mkdir_borrowed(
        borrow, root, "child", purpose=DESTINATION_PURPOSE
    )
    child = filesystem.open_borrowed_directory(
        borrow, root, "child", purpose=DESTINATION_PURPOSE
    )
    original_path = child.path_components
    original_locked = filesystem._directory_locked
    entered = Event()
    resume = Event()
    values = []
    errors = []

    def blocked_directory_locked(candidate_borrow, candidate_directory):
        result = original_locked(candidate_borrow, candidate_directory)
        if candidate_directory is child:
            entered.set()
            assert resume.wait(2)
        return result

    def run_list():
        try:
            values.append(filesystem.list_borrowed_directory(
                borrow, child, 2, purpose=DESTINATION_PURPOSE
            ))
        except BaseException as error:
            errors.append(error)

    filesystem._directory_locked = blocked_directory_locked
    thread = Thread(target=run_list)
    thread.start()
    assert entered.wait(2)
    object.__setattr__(child, "path_components", ("substituted",))
    resume.set()
    thread.join(2)
    filesystem._directory_locked = original_locked
    assert not errors and values == [()]
    object.__setattr__(child, "path_components", original_path)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, child, 2, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID


def test_hardlink_pair_happy_read_eof_stat_close_and_release() -> None:
    port, filesystem, authority = _composition("hardlink-pair-happy")
    payload = b"marker-payload"
    identity = _add_hardlink_pair(port, payload=payload).identity()
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    with pytest.raises(LocalIOErrorV1) as ordinary:
        filesystem.open_borrowed_read(
            borrow, root, "commit", purpose=VERIFY_PURPOSE
        )
    assert ordinary.value.code is LocalIOCodeV1.PATH_CHANGED
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "companion", "commit", purpose=VERIFY_PURPOSE
    )
    assert type(pair) is BorrowedHardlinkPairV1
    assert (pair.first_component, pair.second_component) == ("commit", "companion")
    assert pair.first_identity == pair.second_identity == identity
    assert filesystem.stat_borrowed_hardlink_pair(
        borrow, pair, purpose=VERIFY_PURPOSE
    ) == identity
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 6, purpose=VERIFY_PURPOSE
    ) == payload[:6]
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, MAX_BORROWED_HARDLINK_PAIR_BYTES, purpose=VERIFY_PURPOSE
    ) == payload[6:]
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b""
    filesystem.close_borrowed_hardlink_pair(
        borrow, pair, purpose=VERIFY_PURPOSE
    )
    filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)


def test_hardlink_pair_wrong_purpose_is_zero_raw_open() -> None:
    port, filesystem, authority = _composition("hardlink-pair-purpose")
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    before = port.calls.get("open_read_at", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_hardlink_pair(
            borrow, root, "commit", "companion", purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.ACCESS_MISMATCH
    assert port.calls.get("open_read_at", 0) == before


@pytest.mark.parametrize(
    "mutation",
    ["third-link", "different", "directory", "symlink", "oversized"],
)
def test_hardlink_pair_hostile_admission_is_closed_before_raw_open(mutation) -> None:
    port, filesystem, authority = _composition("hardlink-pair-hostile-" + mutation)
    node = _add_hardlink_pair(port)
    if mutation == "third-link":
        node.nlink = 3
    elif mutation == "different":
        port.directories["dir-data"]["companion"] = port.add_file(
            "dir-data", "other", b"marker", nlink=2
        )
    elif mutation == "directory":
        handle = port.add_directory("dir-data", "pair-dir")
        port.directories["dir-data"]["companion"] = port.directory_nodes[handle]
    elif mutation == "symlink":
        node.mode = stat.S_IFLNK | 0o700
    else:
        node.content = bytearray(MAX_BORROWED_HARDLINK_PAIR_BYTES + 1)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    before = port.calls.get("open_read_at", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_hardlink_pair(
            borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert port.calls.get("open_read_at", 0) == before


def test_hardlink_pair_live_fences_parent_and_borrow_and_detects_third_link() -> None:
    port, filesystem, authority = _composition("hardlink-pair-fence")
    node = _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    with pytest.raises(LocalIOErrorV1) as release:
        filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)
    assert release.value.code is LocalIOCodeV1.BORROW_IN_USE
    node.nlink = 3
    with pytest.raises(LocalIOErrorV1) as unsafe:
        filesystem.stat_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert unsafe.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    with pytest.raises(LocalIOErrorV1):
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    with pytest.raises(LocalIOErrorV1):
        filesystem.stat_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )


def test_hardlink_pair_dto_mutation_and_forged_equal_value_fail_closed() -> None:
    port, filesystem, authority = _composition("hardlink-pair-forgery")
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    forged = replace(pair)
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed_hardlink_pair(
            borrow, forged, purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before
    object.__setattr__(pair, "first_component", "other")
    with pytest.raises(LocalIOErrorV1):
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 1, purpose=VERIFY_PURPOSE
        )


def test_hardlink_pair_mismatched_bytes_and_close_failure_quarantine() -> None:
    port, filesystem, authority = _composition("hardlink-pair-quarantine")
    _add_hardlink_pair(port, payload=b"abcdef")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    first_ref = filesystem._borrow_pairs[pair.pair_ref][3].handle_ref
    port.files[first_ref] = (port.files[first_ref][0], 1)
    with pytest.raises(LocalIOErrorV1) as mismatch:
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 3, purpose=VERIFY_PURPOSE
        )
    assert mismatch.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    port.fail_before["close_file"] = port.calls.get("close_file", 0) + 1
    before_close_calls = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as closed:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert closed.value.code is LocalIOCodeV1.IO_FAILED
    assert port.calls.get("close_file", 0) == before_close_calls + 2
    with pytest.raises(LocalIOErrorV1) as release:
        filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)
    assert release.value.code is LocalIOCodeV1.BORROW_IN_USE


@pytest.mark.parametrize("boundary", ["first-path", "second-path", "first-open", "first-fstat"])
def test_hardlink_pair_admission_races_fail_closed(boundary) -> None:
    port, filesystem, authority = _composition("hardlink-pair-race-" + boundary)
    _add_hardlink_pair(port)

    def substitute():
        port.directories["dir-data"]["companion"] = port._new_inode(
            stat.S_IFREG | 0o600, b"marker"
        )
        port.directories["dir-data"]["companion"].nlink = 2

    callback = {
        "first-path": "stat_at:commit",
        "second-path": "stat_at:companion",
        "first-open": "open_read_at",
        "first-fstat": "stat_file",
    }[boundary]
    port.callbacks[callback] = substitute
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_hardlink_pair(
            borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert not filesystem._borrow_pairs


def test_hardlink_pair_concurrent_read_fences_close_then_releases() -> None:
    port, filesystem, authority = _composition("hardlink-pair-concurrent")
    _add_hardlink_pair(port, payload=b"payload")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    entered = Event()
    resume = Event()
    values = []

    def hold_read():
        entered.set()
        assert resume.wait(2)

    def run_read():
        values.append(filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 7, purpose=VERIFY_PURPOSE
        ))

    port.callbacks["read"] = hold_read
    thread = Thread(target=run_read)
    thread.start()
    assert entered.wait(2)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    resume.set()
    thread.join(2)
    assert values == [b"payload"]
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b""
    filesystem.close_borrowed_hardlink_pair(
        borrow, pair, purpose=VERIFY_PURPOSE
    )
    filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)


def test_hardlink_pair_registration_failure_closes_both_and_cleanup_failure_quarantines() -> None:
    port, filesystem, authority = _composition("hardlink-pair-registration")
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    original = filesystem._record_pair_issuance

    def fail_registration(*args):
        raise RuntimeError("SENTINEL registration")

    filesystem._record_pair_issuance = fail_registration
    before_close = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_hardlink_pair(
            borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert port.calls.get("close_file", 0) == before_close + 2
    assert not filesystem._borrow_pairs
    filesystem._record_pair_issuance = original

    _add_hardlink_pair(port, "next-a", "next-b")
    filesystem._record_pair_issuance = fail_registration
    port.fail_before["close_file"] = port.calls.get("close_file", 0) + 1
    with pytest.raises(LocalIOErrorV1):
        filesystem.open_borrowed_hardlink_pair(
            borrow, root, "next-a", "next-b", purpose=VERIFY_PURPOSE
        )
    assert filesystem._borrow_pair_quarantine
    with pytest.raises(LocalIOErrorV1) as release:
        filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)
    assert release.value.code is LocalIOCodeV1.BORROW_IN_USE


@pytest.mark.parametrize("after_step", range(1, 9))
def test_hardlink_pair_every_admission_boundary_rejects_name_replacement(after_step) -> None:
    port, filesystem, authority = _composition(f"hardlink-pair-step-{after_step}")
    _add_hardlink_pair(port)
    originals = {
        "stat_at": port.stat_at,
        "open_read_at": port.open_read_at,
        "stat_file": port.stat_file,
    }
    step = 0
    mutated = False

    def advance():
        nonlocal step, mutated
        step += 1
        if step == after_step:
            replacement = port._new_inode(stat.S_IFREG | 0o600, b"marker")
            replacement.nlink = 2
            port.directories["dir-data"]["companion"] = replacement
            mutated = True

    def stat_at(directory, component):
        result = originals["stat_at"](directory, component)
        advance()
        return result

    def open_read_at(directory, component):
        result = originals["open_read_at"](directory, component)
        advance()
        return result

    def stat_file(file):
        result = originals["stat_file"](file)
        advance()
        return result

    port.stat_at = stat_at
    port.open_read_at = open_read_at
    port.stat_file = stat_file
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    if after_step < 8:
        with pytest.raises(LocalIOErrorV1) as caught:
            filesystem.open_borrowed_hardlink_pair(
                borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
            )
        assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
        assert not filesystem._borrow_pairs
    else:
        pair = filesystem.open_borrowed_hardlink_pair(
            borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
        )
        before_read = port.calls.get("read", 0)
        with pytest.raises(LocalIOErrorV1) as caught:
            filesystem.read_borrowed_hardlink_pair(
                borrow, pair, 1, purpose=VERIFY_PURPOSE
            )
        assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
        assert port.calls.get("read", 0) == before_read
        with pytest.raises(LocalIOErrorV1):
            filesystem.close_borrowed_hardlink_pair(
                borrow, pair, purpose=VERIFY_PURPOSE
            )
    assert mutated


def test_hardlink_pair_parent_close_and_issuance_tamper_are_fenced() -> None:
    port, filesystem, authority = _composition("hardlink-pair-parent")
    child_handle = port.add_directory("dir-data", "child")
    node = port.add_file(child_handle, "commit", b"marker", nlink=2)
    port.directories[child_handle]["companion"] = node
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    parent = filesystem.open_borrowed_directory(
        borrow, root, "child", purpose=VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, parent, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    with pytest.raises(LocalIOErrorV1) as close_parent:
        filesystem.close_borrowed_directory(
            borrow, parent, purpose=VERIFY_PURPOSE
        )
    assert close_parent.value.code is LocalIOCodeV1.BORROW_IN_USE
    filesystem._pair_issuance_seals[pair.pair_ref] = "0" * 64
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as tampered:
        filesystem.stat_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert tampered.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before


def test_hardlink_pair_second_close_failure_also_quarantines() -> None:
    port, filesystem, authority = _composition("hardlink-pair-second-close")
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    before = port.calls.get("close_file", 0)
    port.fail_before["close_file"] = before + 2
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert port.calls.get("close_file", 0) == before + 2
    assert pair.pair_ref in filesystem._borrow_pair_quarantine


def test_hardlink_pair_wrong_purpose_leaves_entire_port_trace_unchanged() -> None:
    port, filesystem, authority = _composition("hardlink-pair-zero-trace")
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_hardlink_pair(
            borrow, root, "commit", "companion", purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.ACCESS_MISMATCH
    assert tuple(port.trace) == before


@pytest.mark.parametrize("failure", ["early-eof", "overrun", "data-after-size"])
def test_hardlink_pair_stream_failures_permanently_poison_to_close_only(failure) -> None:
    port, filesystem, authority = _composition("hardlink-pair-stream-" + failure)
    _add_hardlink_pair(port, payload=b"abcdef")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    state = filesystem._borrow_pairs[pair.pair_ref]
    if failure == "early-eof":
        for raw in state[3:5]:
            node, _ = port.files[raw.handle_ref]
            port.files[raw.handle_ref] = (node, len(node.content))
    elif failure == "overrun":
        port.read = lambda file, maximum: b"x" * maximum
    else:
        assert filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 6, purpose=VERIFY_PURPOSE
        ) == b"abcdef"
        port.read = lambda file, maximum: b"x"
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 7, purpose=VERIFY_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as reread:
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 1, purpose=VERIFY_PURPOSE
        )
    assert reread.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    with pytest.raises(LocalIOErrorV1) as restat:
        filesystem.stat_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert restat.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert tuple(port.trace) == before
    with pytest.raises(LocalIOErrorV1) as close:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert close.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)


def test_hardlink_pair_requires_terminal_eof_and_rejects_read_after_eof() -> None:
    port, filesystem, authority = _composition("hardlink-pair-terminal-eof")
    _add_hardlink_pair(port, payload=b"abc")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 3, purpose=VERIFY_PURPOSE
    ) == b"abc"
    with pytest.raises(LocalIOErrorV1) as premature:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert premature.value.code is LocalIOCodeV1.HARDLINK_UNSAFE

    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 3, purpose=VERIFY_PURPOSE
    ) == b"abc"
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b""
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as replay:
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 1, purpose=VERIFY_PURPOSE
        )
    assert replay.value.code is LocalIOCodeV1.STREAM_INVALID
    assert tuple(port.trace) == before
    filesystem.close_borrowed_hardlink_pair(
        borrow, pair, purpose=VERIFY_PURPOSE
    )


@pytest.mark.parametrize("failure", ["exception", "mismatch"])
def test_hardlink_pair_failure_after_first_chunk_is_permanent(failure) -> None:
    port, filesystem, authority = _composition("hardlink-pair-late-" + failure)
    _add_hardlink_pair(port, payload=b"abcdef")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 3, purpose=VERIFY_PURPOSE
    ) == b"abc"
    if failure == "exception":
        port.fail_before["read"] = port.calls.get("read", 0) + 1
    else:
        second_raw = filesystem._borrow_pairs[pair.pair_ref][4]
        node, offset = port.files[second_raw.handle_ref]
        port.files[second_raw.handle_ref] = (node, offset + 1)
    with pytest.raises(LocalIOErrorV1):
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 3, purpose=VERIFY_PURPOSE
        )
    with pytest.raises(LocalIOErrorV1) as poisoned:
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 1, purpose=VERIFY_PURPOSE
        )
    assert poisoned.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    with pytest.raises(LocalIOErrorV1):
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )


def test_hardlink_pair_two_concurrent_reads_are_serialized_lockstep() -> None:
    port, filesystem, authority = _composition("hardlink-pair-serialized")
    _add_hardlink_pair(port, payload=b"abcdef")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    entered = Event()
    resume = Event()
    results = []

    def hold_first():
        entered.set()
        assert resume.wait(2)

    def run():
        results.append(filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 3, purpose=VERIFY_PURPOSE
        ))

    before = port.calls.get("read", 0)
    port.callbacks["read"] = hold_first
    first = Thread(target=run)
    second = Thread(target=run)
    first.start()
    assert entered.wait(2)
    second.start()
    assert port.calls.get("read", 0) == before + 1
    resume.set()
    first.join(2)
    second.join(2)
    assert results == [b"abc", b"def"]
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b""
    filesystem.close_borrowed_hardlink_pair(
        borrow, pair, purpose=VERIFY_PURPOSE
    )


def test_hardlink_pair_concurrent_close_is_exclusive() -> None:
    port, filesystem, authority = _composition("hardlink-pair-close-close")
    _add_hardlink_pair(port, payload=b"x")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b"x"
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b""
    entered = Event()
    resume = Event()
    errors = []
    before_close = port.calls.get("close_file", 0)

    def hold_close():
        entered.set()
        assert resume.wait(2)

    def close():
        try:
            filesystem.close_borrowed_hardlink_pair(
                borrow, pair, purpose=VERIFY_PURPOSE
            )
        except BaseException as error:
            errors.append(error)

    port.callbacks["close_file"] = hold_close
    first = Thread(target=close)
    first.start()
    assert entered.wait(2)
    second = Thread(target=close)
    second.start()
    second.join(2)
    resume.set()
    first.join(2)
    assert len(errors) == 1
    assert type(errors[0]) is LocalIOErrorV1
    assert errors[0].code is LocalIOCodeV1.BORROW_INVALID
    assert port.calls.get("close_file", 0) == before_close + 2


@pytest.mark.parametrize(
    "failure",
    ["third-link", "name-substitution", "malformed-stat", "raw-exception"],
)
def test_hardlink_pair_stat_failure_permanently_poisons_exact_stream(failure) -> None:
    port, filesystem, authority = _composition("hardlink-pair-stat-" + failure)
    node = _add_hardlink_pair(port, payload=b"marker")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    original_stat_file = port.stat_file
    original_companion = port.directories["dir-data"]["companion"]
    expected_code = LocalIOCodeV1.HARDLINK_UNSAFE
    if failure == "third-link":
        node.nlink = 3
    elif failure == "name-substitution":
        foreign = port.add_file(
            "dir-data", "foreign-pair-member", b"marker", nlink=2
        )
        port.directories["dir-data"]["companion"] = foreign
    elif failure == "malformed-stat":
        port.stat_file = lambda raw: object()
    else:
        port.fail_before["stat_file"] = port.calls.get("stat_file", 0) + 1
        expected_code = LocalIOCodeV1.IO_FAILED

    with pytest.raises(LocalIOErrorV1) as failed:
        filesystem.stat_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert failed.value.code is expected_code

    node.nlink = 2
    port.directories["dir-data"]["companion"] = original_companion
    port.stat_file = original_stat_file
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as restat:
        filesystem.stat_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert restat.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    with pytest.raises(LocalIOErrorV1) as reread:
        filesystem.read_borrowed_hardlink_pair(
            borrow, pair, 1, purpose=VERIFY_PURPOSE
        )
    assert reread.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert tuple(port.trace) == before

    before_close = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as closed:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert closed.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert port.calls.get("close_file", 0) == before_close + 2


def test_hardlink_pair_stat_waits_for_poisoning_read_then_is_zero_effect() -> None:
    port, filesystem, authority = _composition("hardlink-pair-stat-read-race")
    _add_hardlink_pair(port, payload=b"abcdef")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    entered = Event()
    resume = Event()
    stat_started = Event()
    read_errors = []
    stat_errors = []

    def hold_first_read():
        entered.set()
        assert resume.wait(2)

    def read_pair():
        try:
            filesystem.read_borrowed_hardlink_pair(
                borrow, pair, 3, purpose=VERIFY_PURPOSE
            )
        except BaseException as error:
            read_errors.append(error)

    def stat_pair():
        stat_started.set()
        try:
            filesystem.stat_borrowed_hardlink_pair(
                borrow, pair, purpose=VERIFY_PURPOSE
            )
        except BaseException as error:
            stat_errors.append(error)

    port.callbacks["read"] = hold_first_read
    reader = Thread(target=read_pair)
    reader.start()
    assert entered.wait(2)
    second_raw = filesystem._borrow_pairs[pair.pair_ref][4]
    second_node, second_offset = port.files[second_raw.handle_ref]
    port.files[second_raw.handle_ref] = (second_node, second_offset + 1)
    stat_counts = {
        name: port.calls.get(name, 0)
        for name in ("stat_at:commit", "stat_at:companion", "stat_file")
    }
    statter = Thread(target=stat_pair)
    statter.start()
    assert stat_started.wait(2)
    assert {
        name: port.calls.get(name, 0) for name in stat_counts
    } == stat_counts
    resume.set()
    reader.join(2)
    statter.join(2)
    assert not reader.is_alive()
    assert not statter.is_alive()
    assert len(read_errors) == len(stat_errors) == 1
    assert type(read_errors[0]) is LocalIOErrorV1
    assert type(stat_errors[0]) is LocalIOErrorV1
    assert read_errors[0].code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert stat_errors[0].code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert {
        name: port.calls.get(name, 0) for name in stat_counts
    } == stat_counts

    before_close = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as closed:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert closed.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert port.calls.get("close_file", 0) == before_close + 2


@pytest.mark.parametrize("failure_index", [1, 2])
def test_nested_hardlink_pair_close_quarantine_fences_parent_borrow_and_root(failure_index) -> None:
    port, filesystem, authority = _composition(f"hardlink-pair-nested-q-{failure_index}")
    child_handle = port.add_directory("dir-data", "child")
    node = port.add_file(child_handle, "commit", b"x", nlink=2)
    port.directories[child_handle]["companion"] = node
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    parent = filesystem.open_borrowed_directory(
        borrow, root, "child", purpose=VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, parent, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b"x"
    assert filesystem.read_borrowed_hardlink_pair(
        borrow, pair, 1, purpose=VERIFY_PURPOSE
    ) == b""
    before = port.calls.get("close_file", 0)
    port.fail_before["close_file"] = before + failure_index
    with pytest.raises(LocalIOErrorV1) as closed:
        filesystem.close_borrowed_hardlink_pair(
            borrow, pair, purpose=VERIFY_PURPOSE
        )
    assert closed.value.code is LocalIOCodeV1.IO_FAILED
    assert port.calls.get("close_file", 0) == before + 2
    with pytest.raises(LocalIOErrorV1) as parent_close:
        filesystem.close_borrowed_directory(
            borrow, parent, purpose=VERIFY_PURPOSE
        )
    assert parent_close.value.code is LocalIOCodeV1.BORROW_IN_USE
    with pytest.raises(LocalIOErrorV1) as borrow_release:
        filesystem.release_borrow(borrow, purpose=VERIFY_PURPOSE)
    assert borrow_release.value.code is LocalIOCodeV1.BORROW_IN_USE
    with pytest.raises(LocalIOErrorV1) as root_release:
        filesystem.release_root_authority(authority)
    assert root_release.value.code is LocalIOCodeV1.BORROW_IN_USE


@pytest.mark.parametrize("endpoint", ["missing", "identical"])
def test_hardlink_pair_missing_or_identical_endpoint_rejects_before_open(endpoint) -> None:
    port, filesystem, authority = _composition("hardlink-pair-endpoint-" + endpoint)
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    before = port.calls.get("open_read_at", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_hardlink_pair(
            borrow,
            root,
            "commit",
            "missing" if endpoint == "missing" else "commit",
            purpose=VERIFY_PURPOSE,
        )
    assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE
    assert port.calls.get("open_read_at", 0) == before


def test_hardlink_pair_read_request_bound_is_zero_effect() -> None:
    port, filesystem, authority = _composition("hardlink-pair-read-bound")
    _add_hardlink_pair(port)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    pair = filesystem.open_borrowed_hardlink_pair(
        borrow, root, "commit", "companion", purpose=VERIFY_PURPOSE
    )
    before = tuple(port.trace)
    for maximum in (0, MAX_BORROWED_HARDLINK_PAIR_BYTES + 1):
        with pytest.raises(LocalIOErrorV1) as caught:
            filesystem.read_borrowed_hardlink_pair(
                borrow, pair, maximum, purpose=VERIFY_PURPOSE
            )
        assert caught.value.code is LocalIOCodeV1.LIMIT_EXCEEDED
    assert tuple(port.trace) == before


@pytest.mark.parametrize(
    ("parent_access", "requested_access"),
    [
        (RootAccessV1.READ_ONLY, RootAccessV1.CREATE_ONLY),
        (RootAccessV1.CREATE_ONLY, RootAccessV1.READ_ONLY),
        (RootAccessV1.READ_ONLY, RootAccessV1.READ_CREATE),
    ],
)
def test_borrow_access_cannot_be_amplified(parent_access, requested_access) -> None:
    port, filesystem, authority = _composition_with_data_access(parent_access)
    before = tuple(port.trace)
    purpose = (
        SOURCE_PURPOSE
        if requested_access is RootAccessV1.READ_ONLY
        else DESTINATION_PURPOSE
    )
    request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, purpose, requested_access
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.borrow_root(authority, request)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before


def test_borrow_access_matrix_and_wrong_purpose_fail_before_port_calls() -> None:
    port, filesystem, authority = _composition()
    port.add_file("dir-data", "source", b"source")
    read_request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, SOURCE_PURPOSE, RootAccessV1.READ_ONLY
    )
    read_borrow = filesystem.borrow_root(authority, read_request)
    root = filesystem.root_directory(read_borrow, purpose=SOURCE_PURPOSE)
    opened = filesystem.open_borrowed_read(
        read_borrow, root, "source", purpose=SOURCE_PURPOSE
    )
    assert filesystem.read_borrowed(
        read_borrow, opened, 32, purpose=SOURCE_PURPOSE
    ) == b"source"
    filesystem.close_borrowed_file(read_borrow, opened, purpose=SOURCE_PURPOSE)
    for call in (
        lambda: filesystem.mkdir_borrowed(read_borrow, root, "x", purpose=SOURCE_PURPOSE),
        lambda: filesystem.create_borrowed_file(read_borrow, root, "x", purpose=SOURCE_PURPOSE),
        lambda: filesystem.fsync_borrowed_directory(read_borrow, root, purpose=SOURCE_PURPOSE),
        lambda: filesystem.unlink_borrowed(read_borrow, root, "source", purpose=SOURCE_PURPOSE),
    ):
        before = tuple(port.trace)
        with pytest.raises(LocalIOErrorV1) as caught:
            call()
        assert caught.value.code is LocalIOCodeV1.ACCESS_MISMATCH
        assert tuple(port.trace) == before
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed(read_borrow, root, "source", purpose="wrong")
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before

    port, filesystem, authority = _composition_with_data_access(
        RootAccessV1.CREATE_ONLY
    )
    create_borrow, create_root = _borrow(
        filesystem, authority, RootAccessV1.CREATE_ONLY, DESTINATION_PURPOSE
    )
    assert filesystem.stat_borrowed(
        create_borrow, create_root, "missing", purpose=DESTINATION_PURPOSE
    ) is None
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_read(
            create_borrow, create_root, "missing", purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.ACCESS_MISMATCH
    assert tuple(port.trace) == before

    port, filesystem, authority = _composition("verify-purpose")
    port.add_file("dir-data", "mounted", b"verified")
    verify_borrow, verify_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, VERIFY_PURPOSE
    )
    verify_file = filesystem.open_borrowed_read(
        verify_borrow, verify_root, "mounted", purpose=VERIFY_PURPOSE
    )
    assert filesystem.read_borrowed(
        verify_borrow, verify_file, 32, purpose=VERIFY_PURPOSE
    ) == b"verified"
    filesystem.close_borrowed_file(
        verify_borrow, verify_file, purpose=VERIFY_PURPOSE
    )
    filesystem.release_borrow(verify_borrow, purpose=VERIFY_PURPOSE)


def test_borrow_exact_objects_children_and_parent_lifecycle_are_fenced() -> None:
    port, filesystem, authority = _composition()
    borrow, root = _borrow(filesystem, authority)
    for forged in (replace(borrow), RetainedRootBorrowV1(
        borrow.schema_version, borrow.borrow_ref, borrow.request_digest,
        borrow.root_authority_digest, borrow.purpose, borrow.access,
        borrow.borrow_digest,
    )):
        before = tuple(port.trace)
        with pytest.raises(LocalIOErrorV1) as caught:
            filesystem.root_directory(forged, purpose=DESTINATION_PURPOSE)
        assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
        assert tuple(port.trace) == before
    assert filesystem.mkdir_borrowed(borrow, root, "child", purpose=DESTINATION_PURPOSE)
    child = filesystem.open_borrowed_directory(
        borrow, root, "child", purpose=DESTINATION_PURPOSE
    )
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.release_root_authority(authority)
    assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    assert tuple(port.trace) == before
    forged_child = replace(child)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.close_borrowed_directory(
            borrow, forged_child, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before
    filesystem.close_borrowed_directory(borrow, child, purpose=DESTINATION_PURPOSE)
    filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)


def test_borrow_effect_pin_blocks_release_during_underlying_call() -> None:
    port, filesystem, authority = _composition()
    borrow, root = _borrow(filesystem, authority)
    entered = Event()
    resume = Event()
    outcome = []

    def hold_effect():
        entered.set()
        assert resume.wait(2)

    def mutate():
        outcome.append(filesystem.mkdir_borrowed(
            borrow, root, "child", purpose=DESTINATION_PURPOSE
        ))

    port.callbacks["mkdir_at"] = hold_effect
    thread = Thread(target=mutate)
    thread.start()
    assert entered.wait(2)
    for action in (
        lambda: filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE),
        lambda: filesystem.release_root_authority(authority),
    ):
        with pytest.raises(LocalIOErrorV1) as caught:
            action()
        assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    resume.set()
    thread.join(2)
    assert not thread.is_alive()
    assert outcome == [True]
    filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)


def test_child_pins_fence_file_close_and_descendant_creation_close_races() -> None:
    port, filesystem, authority = _composition("child-pin")
    port.add_file("dir-data", "source", b"payload")
    read_borrow, read_root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    readable = filesystem.open_borrowed_read(
        read_borrow, read_root, "source", purpose=SOURCE_PURPOSE
    )
    entered = Event()
    resume = Event()
    values = []

    def hold_read():
        entered.set()
        assert resume.wait(2)

    port.callbacks["read"] = hold_read
    thread = Thread(target=lambda: values.append(filesystem.read_borrowed(
        read_borrow, readable, 16, purpose=SOURCE_PURPOSE
    )))
    thread.start()
    assert entered.wait(2)
    for action in (
        lambda: filesystem.close_borrowed_file(
            read_borrow, readable, purpose=SOURCE_PURPOSE
        ),
        lambda: filesystem.release_borrow(read_borrow, purpose=SOURCE_PURPOSE),
        lambda: filesystem.release_root_authority(authority),
    ):
        with pytest.raises(LocalIOErrorV1) as caught:
            action()
        assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    resume.set()
    thread.join(2)
    assert values == [b"payload"]
    filesystem.close_borrowed_file(read_borrow, readable, purpose=SOURCE_PURPOSE)
    filesystem.release_borrow(read_borrow, purpose=SOURCE_PURPOSE)

    create_borrow, create_root = _borrow(filesystem, authority)
    assert filesystem.mkdir_borrowed(
        create_borrow, create_root, "parent", purpose=DESTINATION_PURPOSE
    )
    parent = filesystem.open_borrowed_directory(
        create_borrow, create_root, "parent", purpose=DESTINATION_PURPOSE
    )
    assert filesystem.mkdir_borrowed(
        create_borrow, parent, "child", purpose=DESTINATION_PURPOSE
    )
    entered.clear()
    resume.clear()

    def hold_open():
        entered.set()
        assert resume.wait(2)

    opened = []
    port.callbacks["open_directory_at"] = hold_open
    thread = Thread(target=lambda: opened.append(
        filesystem.open_borrowed_directory(
            create_borrow, parent, "child", purpose=DESTINATION_PURPOSE
        )
    ))
    thread.start()
    assert entered.wait(2)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.close_borrowed_directory(
            create_borrow, parent, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    resume.set()
    thread.join(2)
    assert len(opened) == 1
    entered.clear()
    resume.clear()

    def hold_close():
        entered.set()
        assert resume.wait(2)

    port.callbacks["close_directory"] = hold_close
    thread = Thread(target=lambda: filesystem.close_borrowed_directory(
        create_borrow, opened[0], purpose=DESTINATION_PURPOSE
    ))
    thread.start()
    assert entered.wait(2)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.close_borrowed_directory(
            create_borrow, parent, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_IN_USE
    resume.set()
    thread.join(2)
    assert not thread.is_alive()
    filesystem.close_borrowed_directory(
        create_borrow, parent, purpose=DESTINATION_PURPOSE
    )
    filesystem.release_borrow(create_borrow, purpose=DESTINATION_PURPOSE)


def test_borrow_foreign_and_reconstructed_children_fail_before_port_calls() -> None:
    port, filesystem, authority = _composition()
    borrow, root = _borrow(filesystem, authority)
    writable = filesystem.create_borrowed_file(
        borrow, root, "private", purpose=DESTINATION_PURPOSE
    )
    forged_file = replace(writable)
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.write_borrowed(
            borrow, forged_file, b"x", purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before

    other_port, other_filesystem, other_authority = _composition("foreign")
    other_borrow, other_root = _borrow(other_filesystem, other_authority)
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed(borrow, other_root, "x", purpose=DESTINATION_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before
    with pytest.raises(LocalIOErrorV1):
        filesystem.root_directory(other_borrow, purpose=DESTINATION_PURPOSE)
    assert tuple(port.trace) == before

    filesystem.close_borrowed_file(borrow, writable, purpose=DESTINATION_PURPOSE)
    other_filesystem.release_borrow(other_borrow, purpose=DESTINATION_PURPOSE)

    original_access = borrow.access
    before = tuple(port.trace)
    object.__setattr__(borrow, "access", RootAccessV1.READ_ONLY)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed(borrow, root, "x", purpose=DESTINATION_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before
    object.__setattr__(borrow, "access", original_access)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID


def test_borrow_identity_rewrap_path_and_root_replacement_fail_closed() -> None:
    port, filesystem, authority = _composition("identity")
    borrow, root = _borrow(filesystem, authority)
    assert filesystem.mkdir_borrowed(
        borrow, root, "child", purpose=DESTINATION_PURPOSE
    )
    child = filesystem.open_borrowed_directory(
        borrow, root, "child", purpose=DESTINATION_PURPOSE
    )
    substitute = LocalFileIdentityV1(
        child.identity.device, child.identity.inode + 100, child.identity.mode,
        child.identity.nlink, child.identity.changed_ns, child.identity.modified_ns,
        child.identity.size,
    )
    body = child.canonical_without_digest()
    body["identity"] = substitute.canonical()
    forged = BorrowedDirectoryV1(
        child.schema_version, child.borrow_digest, child.directory_ref,
        child.path_components, child.owns_handle, substitute, digest_v1(body),
    )
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, forged, 1, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert tuple(port.trace) == before

    port.add_directory("dir-data", "child")
    before_list = port.calls.get("list_names_at", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, child, 1, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.PATH_CHANGED
    assert port.calls.get("list_names_at", 0) == before_list

    port, filesystem, authority = _composition("root-replacement")
    borrow, root = _borrow(filesystem, authority)
    port.add_root(authority.data_binding.absolute_root, "replacement-data")
    before_stat = port.calls.get("stat_at:any", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.stat_borrowed(
            borrow, root, "any", purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.ROOT_CHANGED
    assert port.calls.get("stat_at:any", 0) == before_stat


def test_borrow_file_path_substitution_is_rejected_before_read() -> None:
    port, filesystem, authority = _composition("file-replacement")
    port.add_file("dir-data", "source", b"first")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    file = filesystem.open_borrowed_read(
        borrow, root, "source", purpose=SOURCE_PURPOSE
    )
    port.add_file("dir-data", "source", b"second")
    before = port.calls.get("read", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.read_borrowed(borrow, file, 16, purpose=SOURCE_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.PATH_CHANGED
    assert port.calls.get("read", 0) == before


@pytest.mark.parametrize(
    ("mode", "nlink"),
    [(stat.S_IFLNK | 0o700, 1), (stat.S_IFREG | 0o600, 2)],
)
def test_borrow_read_rejects_symlink_and_hardlink_and_closes_open_handle(
    mode, nlink
) -> None:
    port, filesystem, authority = _composition("hostile-read")
    port.add_file("dir-data", "hostile", b"payload", mode=mode, nlink=nlink)
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    before_close = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_read(
            borrow, root, "hostile", purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.PATH_CHANGED
    assert port.calls.get("close_file", 0) == before_close + 1
    assert not port.live_files


def test_post_open_registration_failure_closes_exact_handles_once(monkeypatch) -> None:
    port, filesystem, authority = _composition("registration-cleanup")
    borrow, root = _borrow(filesystem, authority)
    assert filesystem.mkdir_borrowed(
        borrow, root, "child", purpose=DESTINATION_PURPOSE
    )
    original_directory_registration = filesystem._new_borrowed_directory
    monkeypatch.setattr(
        filesystem,
        "_new_borrowed_directory",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            LocalIOErrorV1(LocalIOCodeV1.BORROW_INVALID)
        ),
    )
    before_close = port.calls.get("close_directory", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_directory(
            borrow, root, "child", purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert port.calls.get("close_directory", 0) == before_close + 2
    # One close is root reauthentication; the second owns the returned child.
    monkeypatch.setattr(
        filesystem, "_new_borrowed_directory", original_directory_registration
    )

    original_file_registration = filesystem._new_borrowed_file
    monkeypatch.setattr(
        filesystem,
        "_new_borrowed_file",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            LocalIOErrorV1(LocalIOCodeV1.BORROW_INVALID)
        ),
    )
    before_close = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.create_borrowed_file(
            borrow, root, "private", purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.BORROW_INVALID
    assert port.calls.get("close_file", 0) == before_close + 1
    assert not port.live_files
    monkeypatch.setattr(filesystem, "_new_borrowed_file", original_file_registration)


def test_malformed_open_returns_fail_closed_without_wrapper_registration(
    monkeypatch,
) -> None:
    port, filesystem, authority = _composition("malformed-open")
    port.add_file("dir-data", "source", b"payload")
    borrow, root = _borrow(
        filesystem, authority, RootAccessV1.READ_ONLY, SOURCE_PURPOSE
    )
    monkeypatch.setattr(port, "open_read_at", lambda *args: object())
    before_close = port.calls.get("close_file", 0)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.open_borrowed_read(
            borrow, root, "source", purpose=SOURCE_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.PATH_CHANGED
    assert port.calls.get("close_file", 0) == before_close
    assert not filesystem._borrow_files


def test_post_create_cleanup_failure_is_closed(monkeypatch) -> None:
    port, filesystem, authority = _composition("cleanup-failure")
    borrow, root = _borrow(filesystem, authority)
    monkeypatch.setattr(
        filesystem,
        "_new_borrowed_file",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            LocalIOErrorV1(LocalIOCodeV1.BORROW_INVALID)
        ),
    )
    port.fail_before["close_file"] = port.calls.get("close_file", 0) + 1
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.create_borrowed_file(
            borrow, root, "private", purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert "SENTINEL" not in str(caught.value)


def test_borrow_pin_is_released_after_closed_underlying_failure() -> None:
    port, filesystem, authority = _composition()
    borrow, root = _borrow(filesystem, authority)
    port.fail_before["mkdir_at"] = 1
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.mkdir_borrowed(borrow, root, "child", purpose=DESTINATION_PURPOSE)
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert "SENTINEL" not in str(caught.value)
    filesystem.release_borrow(borrow, purpose=DESTINATION_PURPOSE)


def test_windows_borrow_is_capability_unavailable_without_port_call() -> None:
    _, filesystem, authority = _composition()
    filesystem._platform = "win32"
    request = RetainedRootBorrowRequestV1.build(
        authority.authority_digest, SOURCE_PURPOSE, RootAccessV1.READ_ONLY
    )
    before = tuple(filesystem._port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.borrow_root(authority, request)
    assert caught.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE
    assert tuple(filesystem._port.trace) == before


def test_borrow_closed_errors_and_reauthentication_are_zero_call() -> None:
    port, filesystem, authority = _composition()
    borrow, root = _borrow(filesystem, authority)
    filesystem._permit_authenticator.permits.clear()
    before = tuple(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.list_borrowed_directory(
            borrow, root, 1, purpose=DESTINATION_PURPOSE
        )
    assert caught.value.code is LocalIOCodeV1.ROOT_UNAUTHORIZED
    assert tuple(port.trace) == before
    assert "SENTINEL" not in str(caught.value)


@pytest.mark.parametrize("profile", ["opaque-local-like", "opaque-registry-like"])
def test_two_opaque_profiles_use_identical_retained_source_flow(profile: str) -> None:
    port, filesystem, authority = _composition(profile)
    payload = (profile.encode("ascii") + b"/") * 90_000
    port.add_file("dir-data", "input.bin", payload)
    source = filesystem.inspect_source(authority, "input.bin", role="configured-role")
    assert b"".join(filesystem.iter_source(authority, source, chunk_size=97_531)) == payload
    assert source.sha256 == hashlib.sha256(payload).hexdigest()
    assert source.identity.nlink == 1


def test_nested_source_traversal_is_handle_relative_and_closes_child() -> None:
    port, filesystem, authority = _composition()
    child = port.add_directory("dir-data", "nested")
    port.add_file(child, "input", b"payload")
    source = filesystem.inspect_source(authority, "nested/input", role="role")
    assert source.size == 7
    assert "open_directory_at" in port.trace
    assert "close_directory" in port.trace


def test_symlink_source_is_rejected_without_skipping_nonregular_coverage() -> None:
    port, filesystem, authority = _composition()
    port.add_file("dir-data", "link", b"payload", mode=stat.S_IFLNK | 0o777)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "link", role="role")
    assert caught.value.code is LocalIOCodeV1.SOURCE_INVALID


def test_nonregular_source_is_independently_rejected() -> None:
    port, filesystem, authority = _composition()
    port.add_file("dir-data", "socket", b"", mode=stat.S_IFSOCK | 0o600)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "socket", role="role")
    assert caught.value.code is LocalIOCodeV1.SOURCE_INVALID


@pytest.mark.parametrize(
    ("mode", "nlink", "identity_size", "declared_size"),
    [
        (stat.S_IFSOCK | 0o600, 1, 7, 7),
        (stat.S_IFLNK | 0o777, 1, 7, 7),
        (0, 1, 7, 7),
        (stat.S_IFREG | 0o600, 2, 7, 7),
        (stat.S_IFREG | 0o600, 1, 8, 7),
    ],
)
def test_source_binding_rejects_inexact_identity_before_any_port_call(
    mode: int, nlink: int, identity_size: int, declared_size: int
) -> None:
    port = FakePosixFilesystemPortV1()
    identity = LocalFileIdentityV1(1, 2, mode, nlink, 1, 1, identity_size)
    baseline = list(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        LocalSourceBindingV1(
            "0" * 64, "input", "role", declared_size,
            hashlib.sha256(b"payload").hexdigest(), identity,
        )
    assert caught.value.code is LocalIOCodeV1.SOURCE_INVALID
    assert port.trace == baseline


def test_source_binding_accepts_exact_regular_single_link_identity_without_port_call() -> None:
    port = FakePosixFilesystemPortV1()
    identity = LocalFileIdentityV1(1, 2, stat.S_IFREG | 0o600, 1, 1, 1, 7)
    source = LocalSourceBindingV1(
        "0" * 64, "input", "role", 7,
        hashlib.sha256(b"payload").hexdigest(), identity,
    )
    assert source.identity is identity
    assert port.trace == []


def test_multiply_linked_source_is_rejected() -> None:
    port, filesystem, authority = _composition()
    port.add_file("dir-data", "input", b"payload", nlink=2)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "input", role="role")
    assert caught.value.code is LocalIOCodeV1.HARDLINK_UNSAFE


def test_casefold_collision_and_port_failure_are_closed() -> None:
    port, filesystem, authority = _composition()
    port.add_file("dir-data", "Input", b"payload")
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "input", role="role")
    assert caught.value.code is LocalIOCodeV1.PATH_COLLISION
    assert "Input" not in str(caught.value)

    port, filesystem, authority = _composition()
    port.fail_before["list_names_at"] = 1
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "SENTINEL", role="role")
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert "SENTINEL" not in str(caught.value)


def test_source_eof_identity_recheck_detects_change() -> None:
    port, filesystem, authority = _composition()
    node = port.add_file("dir-data", "input", b"payload")
    source = filesystem.inspect_source(authority, "input", role="role")
    node.modified_ns += 1
    with pytest.raises(LocalIOErrorV1) as caught:
        list(filesystem.iter_source(authority, source))
    assert caught.value.code is LocalIOCodeV1.SOURCE_CHANGED


def test_source_changed_ns_and_logical_leaf_substitution_fail_at_eof() -> None:
    port, filesystem, authority = _composition()
    node = port.add_file("dir-data", "input", b"payload")
    source = filesystem.inspect_source(authority, "input", role="role")
    node.changed_ns += 1
    with pytest.raises(LocalIOErrorV1) as caught:
        list(filesystem.iter_source(authority, source))
    assert caught.value.code is LocalIOCodeV1.SOURCE_CHANGED

    port, filesystem, authority = _composition()
    port.add_file("dir-data", "input", b"payload")
    port.callbacks["stat_file"] = lambda: port.add_file("dir-data", "input", b"payload")
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "input", role="role")
    assert caught.value.code is LocalIOCodeV1.PATH_CHANGED


def test_forged_and_closed_retained_handles_are_rejected() -> None:
    port, filesystem, authority = _composition()
    port.add_file("dir-data", "input", b"payload")
    forged_directory = RetainedDirectoryV1(
        authority.data_directory.handle_ref, authority.data_directory.identity
    )
    forged = LocalRootAuthorityV1(
        authority.authority_ref,
        authority.data_binding,
        authority.control_binding,
        forged_directory,
        authority.control_directory,
        authority.authority_digest,
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(forged, "input", role="role")
    assert caught.value.code is LocalIOCodeV1.AUTHORITY_INVALID
    assert "SENTINEL" not in str(caught.value)

    port.close_directory(authority.data_directory)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(authority, "input", role="role")
    assert caught.value.code is LocalIOCodeV1.IO_FAILED


def _destination(filesystem, authority, payload=b"payload"):
    return filesystem.bind_destination(
        authority,
        "artifact.bin",
        role="arbitrary-role",
        expected_size=len(payload),
        expected_sha256=hashlib.sha256(payload).hexdigest(),
    )


def test_create_only_exact_durability_order_and_single_use_authority() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.trace.clear()
    result = filesystem.create_once(root, create, destination, [b"pay", b"load"])
    assert result.status is RecoveryStatusV1.FOUND
    assert bytes(port.directories["dir-data"]["artifact.bin"].content) == b"payload"
    assert ".synaptic-" not in " ".join(port.directories["dir-data"])
    phases = ("claimed", "file_durable", "linked", "committed")
    for index, phase in enumerate(phases):
        start = port.trace.index(f"append_journal:{phase}")
        expected = [
            f"append_journal:{phase}",
            *(["journal_control_fsync"] if index == 0 else []),
            "journal_temp_create",
            "journal_temp_write",
            "journal_temp_fsync",
            "journal_link",
            "journal_directory_fsync",
            "journal_temp_unlink",
            "journal_directory_fsync",
            "journal_reopen",
        ]
        assert port.trace[start : start + len(expected)] == expected
    assert port.trace.index("fsync_file") < port.trace.index("append_journal:file_durable")
    assert port.trace.index("link_at") < port.trace.index("append_journal:linked")
    assert port.trace.index("unlink_at") < port.trace.index("append_journal:committed")
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.create_once(root, create, destination, [b"payload"])
    assert caught.value.code is LocalIOCodeV1.AUTHORITY_INVALID


def test_replay_uses_journal_and_never_creates_twice() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    first = filesystem.authorize_create(root, destination)
    assert filesystem.create_once(root, first, destination, [b"payload"]).status is RecoveryStatusV1.FOUND
    second = filesystem.authorize_create(root, destination)
    result = filesystem.create_once(root, second, destination, [b"payload"])
    assert result.status is RecoveryStatusV1.FOUND
    assert port.calls["create_exclusive_at"] == 1
    assert port.calls["link_at"] == 1


def test_deterministic_concurrent_replay_has_one_mutator() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    first = filesystem.authorize_create(root, destination)
    second = filesystem.authorize_create(root, destination)
    raced = []
    port.callbacks["create_exclusive_at"] = lambda: raced.append(
        filesystem.create_once(root, second, destination, [b"payload"])
    )
    assert filesystem.create_once(root, first, destination, [b"payload"]).status is RecoveryStatusV1.FOUND
    assert raced[0].status is RecoveryStatusV1.ACTIVE
    assert port.calls["create_exclusive_at"] == 1
    assert port.calls["link_at"] == 1


def test_reconstructed_root_authority_replays_same_durable_identity() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    assert filesystem.create_once(root, create, destination, [b"payload"]).status is RecoveryStatusV1.FOUND
    reconstructed = LocalFilesystemV1(port, filesystem._permit_authenticator, native_platform="linux")
    retained_again = reconstructed.retain_root_authority(root.data_binding, root.control_binding)
    assert retained_again.authority_digest == root.authority_digest
    assert reconstructed.recover_create(retained_again, destination).status is RecoveryStatusV1.FOUND


def test_root_authority_digest_excludes_volatile_metadata_permissions_and_handles() -> None:
    _, _, root = _composition()
    data = root.data_directory.identity
    control = root.control_directory.identity
    volatile_data = LocalFileIdentityV1(
        data.device, data.inode, stat.S_IFDIR | 0o777, data.nlink + 9,
        data.changed_ns + 100, data.modified_ns + 200, data.size + 300,
    )
    volatile_control = LocalFileIdentityV1(
        control.device, control.inode, stat.S_IFDIR | 0o711, control.nlink + 7,
        control.changed_ns + 50, control.modified_ns + 60, control.size + 70,
    )
    digest = root_authority_digest_v1(
        root.data_binding, root.control_binding, volatile_data, volatile_control
    )
    assert digest == root.authority_digest
    reconstructed = LocalRootAuthorityV1(
        "different-live-handle",
        root.data_binding,
        root.control_binding,
        RetainedDirectoryV1("different-data-handle", volatile_data),
        RetainedDirectoryV1("different-control-handle", volatile_control),
        digest,
    )
    assert reconstructed.authority_digest == root.authority_digest
    assert set(reconstructed.canonical_without_digest()) == {
        "schema", "data_binding_digest", "control_binding_digest", "data_node", "control_node"
    }


def test_root_authority_digest_changes_on_node_or_binding_and_rejects_wrong_type_alias() -> None:
    _, _, root = _composition()
    data = root.data_directory.identity
    control = root.control_directory.identity
    moved = LocalFileIdentityV1(
        data.device, data.inode + 100, data.mode, data.nlink,
        data.changed_ns, data.modified_ns, data.size,
    )
    assert root_authority_digest_v1(
        root.data_binding, root.control_binding, moved, control
    ) != root.authority_digest
    moved_device = LocalFileIdentityV1(
        data.device + 1, data.inode, data.mode, data.nlink,
        data.changed_ns, data.modified_ns, data.size,
    )
    assert root_authority_digest_v1(
        root.data_binding, root.control_binding, moved_device, control
    ) != root.authority_digest
    _, _, other = _composition("different-binding")
    assert root_authority_digest_v1(
        other.data_binding, root.control_binding, data, control
    ) != root.authority_digest
    non_directory = LocalFileIdentityV1(
        data.device, data.inode, stat.S_IFREG | 0o600, 1,
        data.changed_ns, data.modified_ns, data.size,
    )
    with pytest.raises(LocalIOErrorV1) as caught:
        root_authority_digest_v1(root.data_binding, root.control_binding, non_directory, control)
    assert caught.value.code is LocalIOCodeV1.ROOT_INVALID
    with pytest.raises(LocalIOErrorV1) as caught:
        root_authority_digest_v1(root.data_binding, root.control_binding, data, data)
    assert caught.value.code is LocalIOCodeV1.ROOT_INVALID


def test_same_path_root_replacement_changes_digest_and_rejects_old_evidence_zero_call() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    assert filesystem.create_once(root, create, destination, [b"payload"]).status is RecoveryStatusV1.FOUND
    port.directory_nodes["dir-data"].inode += 10_000
    reconstructed = LocalFilesystemV1(port, filesystem._permit_authenticator, native_platform="linux")
    replaced_root = reconstructed.retain_root_authority(root.data_binding, root.control_binding)
    assert replaced_root.authority_digest != root.authority_digest
    baseline = list(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        reconstructed.recover_create(replaced_root, destination)
    assert caught.value.code is LocalIOCodeV1.DESTINATION_INVALID
    assert port.trace == baseline


def test_live_mutation_recovery_is_active_and_lookup_free() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    observed = []

    def recover_during_create():
        before = port.calls.get("read_journal", 0)
        observed.append(filesystem.recover_create(root, destination))
        assert port.calls.get("read_journal", 0) == before

    port.callbacks["create_exclusive_at"] = recover_during_create
    assert filesystem.create_once(root, create, destination, [b"payload"]).status is RecoveryStatusV1.FOUND
    assert observed[0].status is RecoveryStatusV1.ACTIVE


@pytest.mark.parametrize(
    ("lost_event", "occurrence", "expected"),
    [
        ("append_journal:claimed", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_control_fsync", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_create", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_write", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_fsync", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_link", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_directory_fsync", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_unlink", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_directory_fsync", 2, RecoveryStatusV1.INDETERMINATE),
        ("journal_reopen", 1, RecoveryStatusV1.INDETERMINATE),
        ("create_exclusive_at", 1, RecoveryStatusV1.INDETERMINATE),
        ("fsync_file", 1, RecoveryStatusV1.INDETERMINATE),
        ("append_journal:file_durable", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_fsync", 2, RecoveryStatusV1.INDETERMINATE),
        ("journal_link", 2, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_unlink", 2, RecoveryStatusV1.INDETERMINATE),
        ("journal_reopen", 2, RecoveryStatusV1.INDETERMINATE),
        ("link_at", 1, RecoveryStatusV1.INDETERMINATE),
        ("fsync_directory:data", 1, RecoveryStatusV1.INDETERMINATE),
        ("append_journal:linked", 1, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_fsync", 3, RecoveryStatusV1.INDETERMINATE),
        ("journal_link", 3, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_unlink", 3, RecoveryStatusV1.INDETERMINATE),
        ("journal_reopen", 3, RecoveryStatusV1.INDETERMINATE),
        ("unlink_at", 1, RecoveryStatusV1.FOUND),
        ("fsync_directory:data", 2, RecoveryStatusV1.FOUND),
        ("append_journal:committed", 1, RecoveryStatusV1.FOUND),
        ("journal_temp_fsync", 4, RecoveryStatusV1.INDETERMINATE),
        ("journal_link", 4, RecoveryStatusV1.INDETERMINATE),
        ("journal_temp_unlink", 4, RecoveryStatusV1.FOUND),
        ("journal_reopen", 4, RecoveryStatusV1.FOUND),
    ],
)
def test_every_create_crash_window_recovers_lookup_only(lost_event, occurrence, expected) -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.lose_after[lost_event] = occurrence
    assert filesystem.create_once(root, create, destination, [b"payload"]).status is RecoveryStatusV1.INDETERMINATE
    port.lose_after.clear()
    reconstructed = LocalFilesystemV1(port, filesystem._permit_authenticator, native_platform="linux")
    recovered_root = reconstructed.retain_root_authority(root.data_binding, root.control_binding)
    before = (port.calls.get("create_exclusive_at", 0), port.calls.get("link_at", 0), port.calls.get("unlink_at", 0))
    recovered = reconstructed.recover_create(recovered_root, destination)
    after = (port.calls.get("create_exclusive_at", 0), port.calls.get("link_at", 0), port.calls.get("unlink_at", 0))
    assert recovered.status is expected
    assert after == before


def test_malformed_journal_and_wrong_hardlink_are_conflicts() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.lose_after["append_journal:linked"] = 1
    filesystem.create_once(root, create, destination, [b"payload"])
    port.lose_after.clear()
    staging = ".synaptic-" + create.mutation_id[:32]
    port.add_file("dir-data", staging, b"other")
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.CONFLICT

    records = port.journals[create.mutation_id]
    port.journals[create.mutation_id] = [records[1]]
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.CONFLICT


def test_claimed_without_effect_is_uncertain_and_only_no_journal_is_absence() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.DEFINITELY_ABSENT
    create = filesystem.authorize_create(root, destination)
    port.lose_after["append_journal:claimed"] = 1
    filesystem.create_once(root, create, destination, [b"payload"])
    port.lose_after.clear()
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.INDETERMINATE


@pytest.mark.parametrize("materialized", ["final", "staging"])
def test_empty_journal_never_reports_absence_when_material_exists(materialized: str) -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    mutation = filesystem.authorize_create(root, destination).mutation_id
    name = "artifact.bin" if materialized == "final" else ".synaptic-" + mutation[:32]
    port.add_file("dir-data", name, b"payload")
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.CONFLICT


def test_linked_recovery_requires_staging_absent_and_single_final_link() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.lose_after["append_journal:linked"] = 1
    filesystem.create_once(root, create, destination, [b"payload"])
    port.lose_after.clear()
    staging = ".synaptic-" + create.mutation_id[:32]
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.INDETERMINATE
    port.unlink_at(root.data_directory, staging)
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.FOUND
    port.directories["dir-data"]["artifact.bin"].nlink = 2
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.CONFLICT


def test_recovery_validator_rejects_nonexact_artifact_type() -> None:
    _, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    mutation_id = filesystem.authorize_create(root, destination).mutation_id
    with pytest.raises(LocalIOErrorV1) as caught:
        RecoveryResultV1(RecoveryStatusV1.FOUND, mutation_id, object())  # type: ignore[arg-type]
    assert caught.value.code is LocalIOCodeV1.JOURNAL_INVALID


def test_artifact_and_phase_dtos_reject_structurally_inexact_evidence() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    identity = port.add_file("dir-data", "evidence", b"payload").identity()
    with pytest.raises(LocalIOErrorV1) as caught:
        LocalArtifactBindingV1(
            destination.destination_digest, destination.relative_path, destination.role,
            8, destination.expected_sha256, identity,
        )
    assert caught.value.code is LocalIOCodeV1.DESTINATION_INVALID

    mutation_id = filesystem.authorize_create(root, destination).mutation_id
    canonical = {
        "destination_digest": destination.destination_digest,
        "file_identity": identity.canonical(),
        "mutation_id": mutation_id,
        "phase": CreatePhaseV1.LINKED.value,
        "previous_digest": "0" * 64,
        "sequence": 2,
        "staging_name": ".synaptic-" + mutation_id[:32],
    }
    with pytest.raises(LocalIOErrorV1) as caught:
        CreateJournalRecordV1(
            mutation_id, destination.destination_digest, CreatePhaseV1.LINKED, 2,
            "0" * 64, ".synaptic-" + mutation_id[:32], identity, digest_v1(canonical),
        )
    assert caught.value.code is LocalIOCodeV1.JOURNAL_INVALID

    wrong_staging = ".synaptic-" + ("f" * 64)[:32]
    claimed_canonical = {
        "destination_digest": destination.destination_digest,
        "file_identity": None,
        "mutation_id": mutation_id,
        "phase": CreatePhaseV1.CLAIMED.value,
        "previous_digest": None,
        "sequence": 0,
        "staging_name": wrong_staging,
    }
    with pytest.raises(LocalIOErrorV1) as caught:
        CreateJournalRecordV1(
            mutation_id, destination.destination_digest, CreatePhaseV1.CLAIMED, 0,
            None, wrong_staging, None, digest_v1(claimed_canonical),
        )
    assert caught.value.code is LocalIOCodeV1.JOURNAL_INVALID


def test_journal_codec_is_canonical_bounded_and_rejects_hostile_bytes() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    assert filesystem.create_once(root, create, destination, [b"payload"]).status is RecoveryStatusV1.FOUND
    for record in port.journals[create.mutation_id]:
        raw = journal_record_bytes_v1(record)
        assert parse_journal_record_v1(raw) == record
        with pytest.raises(LocalIOErrorV1) as caught:
            parse_journal_record_v1(b" " + raw)
        assert caught.value.code is LocalIOCodeV1.JOURNAL_INVALID
    for raw in (b"{}", b"x" * 16_385, b'{"sequence":0,"sequence":0}'):
        with pytest.raises(LocalIOErrorV1) as caught:
            parse_journal_record_v1(raw)
        assert caught.value.code is LocalIOCodeV1.JOURNAL_INVALID


def test_windows_is_metadata_only_and_all_effects_make_zero_port_calls() -> None:
    port, posix, root = _composition()
    destination = _destination(posix, root)
    source_node = port.add_file("dir-data", "input", b"payload")
    from synaptic_host.local_io_v1.model import LocalSourceBindingV1

    source = LocalSourceBindingV1(
        root.authority_digest,
        "input",
        "role",
        7,
        hashlib.sha256(b"payload").hexdigest(),
        source_node.identity(),
    )
    windows = LocalFilesystemV1(port, posix._permit_authenticator, native_platform="win32")
    baseline = list(port.trace)
    for operation in (
        lambda: windows.retain_root_authority(root.data_binding, root.control_binding),
        lambda: windows.inspect_source(root, "input", role="role"),
        lambda: list(windows.iter_source(root, source)),
        lambda: windows.recover_create(root, destination),
    ):
        with pytest.raises(LocalIOErrorV1) as caught:
            operation()
        assert caught.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE
        assert port.trace == baseline


def test_native_windows_composition_needs_no_port_and_reports_truthful_capability() -> None:
    authenticator = _Authenticator()
    windows = LocalFilesystemV1(None, authenticator, native_platform="win32")
    capability = windows.capability()
    assert capability.platform_family == "windows"
    assert capability.status.value == "unavailable"
    assert capability.features == ()
    with pytest.raises(LocalIOErrorV1) as caught:
        windows.retain_root_authority(object(), object())  # type: ignore[arg-type]
    assert caught.value.code is LocalIOCodeV1.CAPABILITY_UNAVAILABLE


def test_source_close_failure_is_closed_instead_of_returning_evidence() -> None:
    port, filesystem, root = _composition()
    port.add_file("dir-data", "input", b"payload")
    port.fail_before["close_file"] = 1
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(root, "input", role="role")
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert "SENTINEL" not in str(caught.value)


def test_control_root_is_separate_and_requires_read_create_access() -> None:
    port = FakePosixFilesystemPortV1()
    path = Path.cwd() / ".fake-metadata" / "same"
    port.add_root(path, "data")
    authenticator = _Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    data = _binding(path, "data", RootAccessV1.READ_CREATE, authenticator)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.retain_root_authority(data, data)
    assert caught.value.code is LocalIOCodeV1.ROOT_INVALID
    control_path = Path.cwd() / ".fake-metadata" / "control"
    port.add_root(control_path, "control")
    read_only = _binding(control_path, "control", RootAccessV1.READ_ONLY, authenticator)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.retain_root_authority(data, read_only)
    assert caught.value.code is LocalIOCodeV1.ACCESS_MISMATCH


def test_pair_acquisition_failure_closes_returned_data_handle() -> None:
    port = FakePosixFilesystemPortV1()
    data_path = Path.cwd() / ".fake-metadata" / "pair-data"
    control_path = Path.cwd() / ".fake-metadata" / "pair-control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    authenticator = _Authenticator()
    data = _binding(data_path, "pair-data", RootAccessV1.READ_CREATE, authenticator)
    control = _binding(control_path, "pair-control", RootAccessV1.READ_CREATE, authenticator)
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    port.fail_before["retain_directory"] = 2
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.retain_root_authority(data, control)
    assert caught.value.code is LocalIOCodeV1.IO_FAILED
    assert not port.live_directories
    assert port.calls.get("close_directory") == 1


def test_fake_root_registration_is_explicit_absolute_and_portable(tmp_path: Path) -> None:
    port = FakePosixFilesystemPortV1()
    with pytest.raises(ValueError, match="absolute fake root required"):
        port.add_root(Path("relative-fake-root"), "relative")

    data_path = (tmp_path / "portable-data").absolute()
    control_path = (tmp_path / "portable-control").absolute()
    port.add_root(data_path, "portable-data")
    port.add_root(control_path, "portable-control")
    authenticator = _Authenticator()
    data = _binding(data_path, "portable-data", RootAccessV1.READ_CREATE, authenticator)
    control = _binding(control_path, "portable-control", RootAccessV1.READ_CREATE, authenticator)
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(data, control)
    assert authority.data_binding.absolute_root == data_path
    assert authority.control_binding.absolute_root == control_path
    assert port.roots[str(data_path)] == "dir-portable-data"

    with pytest.raises(KeyError):
        port.retain_directory((tmp_path / "unregistered").absolute())


def test_released_and_foreign_live_authorities_fail_before_port_calls() -> None:
    port, filesystem, root = _composition()
    foreign = LocalFilesystemV1(port, filesystem._permit_authenticator, native_platform="linux")
    baseline = list(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        foreign.bind_destination(
            root,
            "artifact",
            role="role",
            expected_size=0,
            expected_sha256=hashlib.sha256(b"").hexdigest(),
        )
    assert caught.value.code is LocalIOCodeV1.AUTHORITY_INVALID
    assert port.trace == baseline
    filesystem.release_root_authority(root)
    baseline = list(port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.bind_destination(
            root,
            "artifact",
            role="role",
            expected_size=0,
            expected_sha256=hashlib.sha256(b"").hexdigest(),
        )
    assert caught.value.code is LocalIOCodeV1.AUTHORITY_INVALID
    assert port.trace == baseline


def test_bindings_are_immutable_and_cross_authority_requests_are_rejected_before_port_calls() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    with pytest.raises(FrozenInstanceError):
        destination.relative_path = "changed"  # type: ignore[misc]

    other_port, other_filesystem, other_root = _composition("opaque-other")
    baseline = list(other_port.trace)
    with pytest.raises(LocalIOErrorV1) as caught:
        other_filesystem.authorize_create(other_root, destination)
    assert caught.value.code is LocalIOCodeV1.DESTINATION_INVALID
    assert other_port.trace == baseline


@pytest.mark.parametrize(
    "path",
    ["../escape", "/absolute", "a\\b", "a//b", "a/./b", "file:stream", "CON", "lpt9.txt", "trailing.", "e\u0301"],
)
def test_one_windows_safe_component_policy_applies_to_destinations(path: str) -> None:
    _, filesystem, root = _composition()
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.bind_destination(
            root,
            path,
            role="role",
            expected_size=0,
            expected_sha256=hashlib.sha256(b"").hexdigest(),
        )
    assert caught.value.code is LocalIOCodeV1.PATH_INVALID


@pytest.mark.parametrize(
    "path",
    [
        "a\u200bb",
        "a\tb",
        "a\u00a0b",
        "x" * 256,
        "é" * 128,
        "/".join("x" for _ in range(129)),
    ],
)
def test_component_unicode_utf8_and_count_bounds_are_closed(path: str) -> None:
    _, filesystem, root = _composition()
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.bind_destination(
            root, path, role="role", expected_size=0,
            expected_sha256=hashlib.sha256(b"").hexdigest(),
        )
    assert caught.value.code is LocalIOCodeV1.PATH_INVALID


def test_artifact_component_bound_is_exactly_240_utf8_bytes() -> None:
    _, filesystem, root = _composition()
    accepted = filesystem.bind_destination(
        root, "x" * 240, role="role", expected_size=0,
        expected_sha256=hashlib.sha256(b"").hexdigest(),
    )
    assert accepted.relative_path == "x" * 240
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.bind_destination(
            root, "x" * 241, role="role", expected_size=0,
            expected_sha256=hashlib.sha256(b"").hexdigest(),
        )
    assert caught.value.code is LocalIOCodeV1.PATH_INVALID


def test_directory_enumeration_stops_at_bound_before_any_leaf_open() -> None:
    port, filesystem, root = _composition()
    for index in range(4097):
        port.add_file("dir-data", f"entry-{index}", b"")
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(root, "missing", role="role")
    assert caught.value.code is LocalIOCodeV1.LIMIT_EXCEEDED
    assert port.calls.get("open_read_at", 0) == 0


def test_parent_component_replacement_between_stat_and_open_fails_closed() -> None:
    port, filesystem, root = _composition()
    port.add_directory("dir-data", "nested")
    port.callbacks["stat_at:nested"] = lambda: port.add_directory("dir-data", "nested")
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.inspect_source(root, "nested/input", role="role")
    assert caught.value.code is LocalIOCodeV1.PATH_CHANGED


@pytest.mark.parametrize("mode,nlink", [(stat.S_IFSOCK | 0o600, 1), (stat.S_IFREG | 0o600, 2)])
def test_claimed_malformed_or_multilink_staging_is_conflict(mode: int, nlink: int) -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.lose_after["append_journal:claimed"] = 1
    filesystem.create_once(root, create, destination, [b"payload"])
    port.lose_after.clear()
    port.add_file("dir-data", ".synaptic-" + create.mutation_id[:32], b"payload", mode=mode, nlink=nlink)
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.CONFLICT


def test_private_journal_leftover_is_indeterminate_and_changed_ns_may_be_equal() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.lose_after["journal_temp_create"] = 1
    filesystem.create_once(root, create, destination, [b"payload"])
    port.lose_after.clear()
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.INDETERMINATE

    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)
    port.lose_after["append_journal:linked"] = 1
    filesystem.create_once(root, create, destination, [b"payload"])
    port.lose_after.clear()
    staging = ".synaptic-" + create.mutation_id[:32]
    linked_changed_ns = port.journals[create.mutation_id][-1].file_identity.changed_ns
    port.unlink_at(root.data_directory, staging)
    port.directories["dir-data"]["artifact.bin"].changed_ns = linked_changed_ns
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.FOUND


def test_existing_empty_journal_is_indeterminate() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    mutation_id = filesystem.authorize_create(root, destination).mutation_id
    port.journals[mutation_id] = []
    assert filesystem.recover_create(root, destination).status is RecoveryStatusV1.INDETERMINATE


def test_fresh_registry_and_filesystem_converge_on_durable_replay(tmp_path: Path) -> None:
    config_path = tmp_path / "storage.json"
    config_path.write_text(json.dumps({
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {"root_ref": "data", "location": "project://data root", "access": "read_create", "permit_ref": "permit-data"},
            {"root_ref": "control", "location": "project://control root", "access": "read_create", "permit_ref": "permit-control"},
        ],
    }), encoding="utf-8")
    data_path = (tmp_path / "data root").absolute()
    control_path = (tmp_path / "control root").absolute()
    port = FakePosixFilesystemPortV1()
    port.add_root(data_path, "registry-data")
    port.add_root(control_path, "registry-control")

    def registry() -> StorageRegistryV1:
        result = StorageRegistryV1.load(config_path, project_root=tmp_path.absolute())
        for ref in ("data", "control"):
            result.issue_root_permit(
                ref, authority_ref="authority", key_ref="key", proof_digest="0" * 64
            )
        return result

    first_registry = registry()
    first = LocalFilesystemV1(port, first_registry, native_platform="linux")
    first_root = first.retain_root_authority(
        first_registry.resolve("data"), first_registry.resolve("control")
    )
    destination = _destination(first, first_root)
    assert first.create_once(
        first_root, first.authorize_create(first_root, destination), destination, [b"payload"]
    ).status is RecoveryStatusV1.FOUND
    current_data = port.directory_nodes["dir-registry-data"].identity()
    current_control = port.directory_nodes["dir-registry-control"].identity()
    assert current_data.canonical() != first_root.data_directory.identity.canonical()
    assert current_control.canonical() != first_root.control_directory.identity.canonical()
    assert (current_data.device, current_data.inode, current_data.mode & 0o170000) == (
        first_root.data_directory.identity.device,
        first_root.data_directory.identity.inode,
        first_root.data_directory.identity.mode & 0o170000,
    )

    second_registry = registry()
    assert first_registry.resolve("data").root_permit is not second_registry.resolve("data").root_permit
    second = LocalFilesystemV1(port, second_registry, native_platform="linux")
    second_root = second.retain_root_authority(
        second_registry.resolve("data"), second_registry.resolve("control")
    )
    assert second_root.authority_digest == first_root.authority_digest
    second_destination = _destination(second, second_root)
    assert second_destination.destination_digest == destination.destination_digest
    assert second.authorize_create(second_root, second_destination).mutation_id == (
        digest_v1({
            "destination_digest": destination.destination_digest,
            "root_authority_digest": first_root.authority_digest,
        })
    )
    assert second.recover_create(second_root, destination).status is RecoveryStatusV1.FOUND


def test_chunk_bounds_and_iterator_exception_are_closed_after_claim() -> None:
    port, filesystem, root = _composition()
    destination = _destination(filesystem, root)
    create = filesystem.authorize_create(root, destination)

    def broken():
        yield b"pay"
        raise RuntimeError("SENTINEL iterator")

    result = filesystem.create_once(root, create, destination, broken())
    assert result.status is RecoveryStatusV1.INDETERMINATE
    assert "SENTINEL" not in str(result)

    port, filesystem, root = _composition()
    payload = b"x" * (MAX_CHUNK_BYTES + 1)
    destination = _destination(filesystem, root, payload)
    create = filesystem.authorize_create(root, destination)
    assert filesystem.create_once(root, create, destination, [payload]).status is RecoveryStatusV1.INDETERMINATE
