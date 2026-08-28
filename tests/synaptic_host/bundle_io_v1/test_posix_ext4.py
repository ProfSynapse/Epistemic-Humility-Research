from __future__ import annotations

import hashlib
import os
from pathlib import Path
from threading import Event, Thread

import pytest

from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.model import (
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleLookupStatusV1,
    BundleMemberCommandV1,
    BundleSealCommandV1,
    bundle_companion_digest_v1,
)
from synaptic_host.bundle_io_v1.ports import (
    BundleBorrowAccessV1,
    BundleMountVerifyAccessV1,
    BundleSourceV1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    LocalRootBindingV1,
    LocalRootPermitV1,
    RetainedRootBorrowRequestV1,
    RootAccessV1,
    digest_v1,
)
from synaptic_host.local_io_v1.posix import PosixRetainedDirfdPortV1

from .conftest import BindingAuthority


class _Sources:
    def __init__(self, values=()):
        self.values = dict(values)
        self.calls = []

    def resolve(self, source_ref):
        self.calls.append(source_ref)
        return self.values[source_ref]


def _filesystem_and_retainer():
    permits = {}

    class Authenticator:
        def authenticate(self, permit):
            return permit if permits.get(id(permit)) is permit else None

    def binding(ref, path):
        permit_ref = "permit-" + ref
        body = {
            "access": RootAccessV1.READ_CREATE.value,
            "absolute_root": str(path),
            "authority_ref": "bundle-ext4-authority",
            "key_ref": "bundle-ext4-key",
            "permit_ref": permit_ref,
            "root_ref": ref,
        }
        permit = LocalRootPermitV1(
            permit_ref, ref, path, RootAccessV1.READ_CREATE,
            "bundle-ext4-authority", "bundle-ext4-key",
            digest_v1(body), "0" * 64,
        )
        permits[id(permit)] = permit
        return LocalRootBindingV1(
            ref, str(path), path, RootAccessV1.READ_CREATE, permit_ref, permit
        )

    filesystem = LocalFilesystemV1(
        PosixRetainedDirfdPortV1(), Authenticator(), native_platform="linux"
    )

    def retain(data: Path, control: Path, label: str):
        return filesystem.retain_root_authority(
            binding(label + "-data", data),
            binding(label + "-control", control),
        )

    return filesystem, retain


def _borrow(filesystem, authority, purpose, access):
    value = filesystem.borrow_root(
        authority,
        RetainedRootBorrowRequestV1.build(
            authority.authority_digest, purpose, access
        ),
    )
    return value, filesystem.root_directory(value, purpose=purpose)


def test_real_ext4_bundle_retained_pair_recovery_and_hostile_links(
    bundle_ext4_root: Path, monkeypatch,
) -> None:
    destination = bundle_ext4_root / "destination"
    destination_control = bundle_ext4_root / "destination-control"
    source = bundle_ext4_root / "source"
    source_control = bundle_ext4_root / "source-control"
    for path in (destination, destination_control, source, source_control):
        path.mkdir()
    payload = b"real-ext4-source"
    (source / "input.bin").write_bytes(payload)

    filesystem, retain = _filesystem_and_retainer()
    destination_authority = retain(
        destination, destination_control, "destination"
    )
    source_authority = retain(source, source_control, "source")
    create, create_root = _borrow(
        filesystem, destination_authority,
        BorrowPurposeV1.BUNDLE_DESTINATION_CREATE, RootAccessV1.READ_CREATE,
    )
    verify, verify_root = _borrow(
        filesystem, destination_authority,
        BorrowPurposeV1.BUNDLE_MOUNT_VERIFY, RootAccessV1.READ_ONLY,
    )
    source_borrow, source_root = _borrow(
        filesystem, source_authority,
        BorrowPurposeV1.BUNDLE_SOURCE_READ, RootAccessV1.READ_ONLY,
    )
    access = BundleBorrowAccessV1.build(
        "ext4-destination", create, create_root, verify, verify_root
    )
    member = BundleMemberCommandV1(
        "logical/input", "source", len(payload), hashlib.sha256(payload).hexdigest()
    )
    command = BundleSealCommandV1.build(
        "ext4-profile", "source-seal", access.destination_ref, (member,)
    )
    sources = _Sources({
        "source": BundleSourceV1.build(
            "source", source_borrow, source_root, "input.bin"
        )
    }.items())
    binding_authority = BindingAuthority()
    service = ImmutableSourceBundleV1(
        filesystem, sources, binding_authority
    )
    first_claimed = Event()
    release_first = Event()
    waiter_registered = Event()
    outcomes = []
    errors = []
    original_mkdir = filesystem.mkdir_borrowed
    held = False

    def pause_first_claim(*args, **kwargs):
        nonlocal held
        claimed = original_mkdir(*args, **kwargs)
        if claimed and not held:
            held = True
            first_claimed.set()
            assert release_first.wait(5)
        return claimed

    def seal_once():
        try:
            outcomes.append(service.seal(command, access))
        except BaseException as error:
            errors.append(error)

    monkeypatch.setattr(filesystem, "mkdir_borrowed", pause_first_claim)
    first = Thread(target=seal_once)
    second = Thread(target=seal_once)
    first.start()
    assert first_claimed.wait(5)
    key = bundle_companion_digest_v1(
        command.command_digest, command.destination_ref,
        access.root_authority_digest,
    )
    with service._guard_lock:
        entry = service._seal_guards[key]
        original_lock = entry[0]

        class RegisteredLock:
            def __enter__(self):
                waiter_registered.set()
                return original_lock.__enter__()

            def __exit__(self, exception_type, exception, traceback):
                return original_lock.__exit__(
                    exception_type, exception, traceback
                )

        entry[0] = RegisteredLock()
    second.start()
    assert waiter_registered.wait(5)
    assert sources.calls == []
    assert service.lookup(command, access).status is BundleLookupStatusV1.INDETERMINATE
    release_first.set()
    first.join(5)
    second.join(5)
    assert not first.is_alive() and not second.is_alive()
    assert errors == []
    assert len(outcomes) == 2 and outcomes[0] == outcomes[1]
    found = outcomes[0]
    assert found.status is BundleLookupStatusV1.FOUND
    assert sources.calls == ["source"]
    assert service._seal_guards == {}
    assert set(path.name for path in destination.iterdir()) == {
        found.binding.private_name,
        found.binding.marker_name,
        found.binding.companion_name,
    }
    marker_stat = (destination / found.binding.marker_name).stat()
    companion_stat = (destination / found.binding.companion_name).stat()
    assert marker_stat.st_ino == companion_stat.st_ino
    assert marker_stat.st_nlink == companion_stat.st_nlink == 2

    fresh_fs, fresh_retain = _filesystem_and_retainer()
    fresh_authority = fresh_retain(
        destination, destination_control, "destination"
    )
    fresh_create, fresh_create_root = _borrow(
        fresh_fs, fresh_authority,
        BorrowPurposeV1.BUNDLE_DESTINATION_CREATE, RootAccessV1.READ_CREATE,
    )
    fresh_verify, fresh_verify_root = _borrow(
        fresh_fs, fresh_authority,
        BorrowPurposeV1.BUNDLE_MOUNT_VERIFY, RootAccessV1.READ_ONLY,
    )
    fresh_access = BundleBorrowAccessV1.build(
        command.destination_ref, fresh_create, fresh_create_root,
        fresh_verify, fresh_verify_root,
    )
    fresh = ImmutableSourceBundleV1(
        fresh_fs, _Sources(), BindingAuthority()
    )
    authenticated = binding_authority.issue(found.binding)
    mount_access = BundleMountVerifyAccessV1.build(
        command.destination_ref, fresh_verify, fresh_verify_root
    )
    verification = fresh.verify_mount(command, mount_access, authenticated)
    assert verification.binding_digest == found.binding.binding_digest
    assert verification.read_only is True
    assert fresh.lookup(
        command, fresh_access, expected=found.binding
    ).status is BundleLookupStatusV1.INDETERMINATE
    assert fresh.seal(command, fresh_access) == found

    outcomes = []
    threads = [Thread(target=lambda: outcomes.append(
        fresh.seal(command, fresh_access).status
    )) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(5)
    assert outcomes == [BundleLookupStatusV1.FOUND] * 2

    third = destination / "fixture-third-link"
    os.link(destination / found.binding.marker_name, third)
    with pytest.raises(BundleIOErrorV1) as caught:
        fresh.verify_mount(command, mount_access, authenticated)
    assert caught.value.code is BundleIOCodeV1.CONFLICT
    assert fresh.lookup(command, fresh_access).status is BundleLookupStatusV1.CONFLICT
    third.unlink()
    assert fresh.lookup(command, fresh_access).status is BundleLookupStatusV1.INDETERMINATE

    companion = destination / found.binding.companion_name
    companion.unlink()
    companion.write_bytes((destination / found.binding.marker_name).read_bytes())
    assert fresh.lookup(command, fresh_access).status is BundleLookupStatusV1.CONFLICT
