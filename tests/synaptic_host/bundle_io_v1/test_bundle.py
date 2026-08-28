from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from threading import Event, Thread

import pytest

from synaptic_host.bundle_io_v1.model import (
    MAX_BUNDLE_CHUNK_BYTES,
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleLookupStatusV1,
    BundleMemberCommandV1,
    BundleSealCommandV1,
    bundle_companion_digest_v1,
)
from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.ports import BundleBorrowAccessV1, BundleSourceV1
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import BorrowPurposeV1, RootAccessV1
from synaptic_host.local_io_v1.model import LocalIOCodeV1, LocalIOErrorV1

from .conftest import Authenticator, borrow


def private_handle(port, command):
    name = ".synaptic-bundle-" + command.command_digest[:32]
    return port.directories["dir-data"][name].directory_handle


def test_seal_is_deterministic_and_replay_is_store_only(bundle_env) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.FOUND
    assert result.binding.command_digest == command.command_digest
    assert tuple(member.logical_name for member in result.binding.members) == (
        "logical/0", "logical/1"
    )
    before = tuple(port.trace)
    before_sources = tuple(registry.calls)
    replay = service.seal(command, access)
    assert replay == result
    assert tuple(registry.calls) == before_sources
    assert "mkdir_at" not in port.trace[len(before):]
    assert "create_exclusive_at" not in port.trace[len(before):]


def test_lookup_clean_private_only_and_marker_only_classifications(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    assert service.lookup(command, access).status is BundleLookupStatusV1.DEFINITELY_ABSENT
    private_name = ".synaptic-bundle-" + command.command_digest[:32]
    port.add_directory("dir-data", private_name)
    assert service.lookup(command, access).status is BundleLookupStatusV1.INDETERMINATE
    del port.directories["dir-data"][private_name]
    port.add_file("dir-data", "COMMIT-" + command.command_digest[:32], b"foreign")
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT


def test_lost_link_return_is_proven_with_retained_companion(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    port.lose_after["link_at"] = 1
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.FOUND
    companion = result.binding.companion_name
    assert companion in port.directories["dir-data"]
    assert port.directories["dir-data"][companion].nlink == 2
    observed = service.lookup(command, access, expected=result.binding)
    assert observed.status is BundleLookupStatusV1.INDETERMINATE
    assert observed.binding is None
    assert port.calls.get("link_at", 0) == 1


@pytest.mark.parametrize("event", ["write", "fsync_file", "fsync_directory:data"])
def test_precommit_crashes_leave_private_state_indeterminate(bundle_env, event) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    port.fail_before[event] = 1
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.INDETERMINATE
    assert service.lookup(command, access).status is BundleLookupStatusV1.INDETERMINATE
    assert "COMMIT-" + command.command_digest[:32] not in port.directories["dir-data"]


def test_extra_missing_tampered_and_hardlinked_members_fail_closed(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.FOUND
    handle = private_handle(port, command)
    port.add_file(handle, "extra", b"x")
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT
    del port.directories[handle]["extra"]
    node = port.directories[handle]["member-0000"]
    node.content[:] = b"ALPHA"
    node.changed_ns += 1
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT
    node.content[:] = b"alpha"
    node.nlink = 2
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT


def test_forged_command_and_cross_destination_are_zero_effect(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    before = tuple(port.trace)
    object.__setattr__(command, "destination_ref", "rebound")
    with pytest.raises(BundleIOErrorV1) as caught:
        service.seal(command, access)
    assert caught.value.code is BundleIOCodeV1.COMMAND_INVALID
    assert tuple(port.trace) == before


def test_concurrent_no_replace_has_one_materializer(bundle_env) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    entered = Event()
    resume = Event()
    outcomes = []

    def hold_first_create():
        entered.set()
        assert resume.wait(2)

    def run():
        outcomes.append(service.seal(command, access).status)

    port.callbacks["mkdir_at"] = hold_first_create
    first = Thread(target=run)
    second = Thread(target=run)
    first.start()
    assert entered.wait(2)
    second.start()
    resume.set()
    first.join(2)
    second.join(2)
    assert BundleLookupStatusV1.FOUND in outcomes
    assert set(outcomes) <= {
        BundleLookupStatusV1.FOUND, BundleLookupStatusV1.INDETERMINATE
    }
    assert registry.calls.count("source-a") == 1
    assert registry.calls.count("source-b") == 1


def test_expected_binding_detects_marker_identity_substitution(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    marker = "COMMIT-" + command.command_digest[:32]
    node = port.directories["dir-data"][marker]
    replacement = port._new_inode(node.mode, bytes(node.content))
    port.directories["dir-data"][marker] = replacement
    assert service.lookup(command, access, expected=found.binding).status is BundleLookupStatusV1.CONFLICT


def test_mutated_expected_binding_and_nested_member_are_conflict(bundle_env) -> None:
    _, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    object.__setattr__(found.binding.members[0], "logical_name", "rebound")
    assert service.lookup(
        command, access, expected=found.binding
    ).status is BundleLookupStatusV1.CONFLICT


def test_missing_member_and_marker_tamper_fail_closed(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    assert service.seal(command, access).status is BundleLookupStatusV1.FOUND
    handle = private_handle(port, command)
    missing = port.directories[handle].pop("member-0001")
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT
    port.directories[handle]["member-0001"] = missing
    marker_name = "COMMIT-" + command.command_digest[:32]
    marker = port.directories["dir-data"][marker_name]
    marker.content[0] = marker.content[0] ^ 1
    marker.changed_ns += 1
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT


def test_large_member_creation_and_recovery_are_chunk_bounded(bundle_env) -> None:
    port, _, service, registry, _, access, _, _ = bundle_env
    payload = b"z" * (MAX_BUNDLE_CHUNK_BYTES + 17)
    port.add_file("dir-data", "large-source", payload)
    template = registry.values["source-a"]
    registry.values["large-source"] = BundleSourceV1.build(
        "large-source", template.borrow, template.directory, "large-source"
    )
    member = BundleMemberCommandV1(
        "logical/large", "large-source", len(payload),
        hashlib.sha256(payload).hexdigest(),
    )
    command = BundleSealCommandV1.build(
        "opaque-profile", "source-seal", access.destination_ref, (member,)
    )
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.FOUND
    assert service.lookup(
        command, access, expected=result.binding
    ).status is BundleLookupStatusV1.INDETERMINATE
    assert port.calls["read"] >= 6


def test_deterministic_companion_is_root_destination_and_command_bound(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    expected_digest = bundle_companion_digest_v1(
        command.command_digest, command.destination_ref,
        access.root_authority_digest,
    )
    expected_name = ".synaptic-commit-companion-" + expected_digest
    assert service._names(command, access)[2] == expected_name
    found = service.seal(command, access)
    assert found.status is BundleLookupStatusV1.FOUND
    assert found.binding.companion_name == expected_name
    assert not any("unlink" in event for event in port.trace)
    changed_destination = BundleSealCommandV1.build(
        command.profile_ref, command.purpose_ref, "other-destination",
        command.members,
    )
    assert bundle_companion_digest_v1(
        changed_destination.command_digest, changed_destination.destination_ref,
        access.root_authority_digest,
    ) != expected_digest


@pytest.mark.parametrize(
    "field,value",
    [
        ("destination_ref", "rebound"),
        ("root_authority_digest", "0" * 64),
        ("access_digest", "0" * 64),
    ],
)
def test_access_mutation_is_rejected_before_port_or_source(bundle_env, field, value) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    before_port = tuple(port.trace)
    before_sources = tuple(registry.calls)
    object.__setattr__(access, field, value)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.seal(command, access)
    assert caught.value.code is BundleIOCodeV1.ACCESS_INVALID
    assert tuple(port.trace) == before_port
    assert tuple(registry.calls) == before_sources


def test_final_marker_is_exact_retained_hardlink_pair(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    marker = port.directories["dir-data"][found.binding.marker_name]
    companion = port.directories["dir-data"][found.binding.companion_name]
    assert marker is companion
    assert marker.nlink == 2
    assert found.binding.marker_identity.nlink == 2
    root_names = set(port.directories["dir-data"])
    assert found.binding.private_name in root_names
    assert found.binding.marker_name in root_names
    assert found.binding.companion_name in root_names


@pytest.mark.parametrize("attack", ["third-link", "substitute-companion", "missing-companion"])
def test_final_pair_hostile_states_are_conflict(bundle_env, attack) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    companion_name = found.binding.companion_name
    if attack == "third-link":
        node = port.directories["dir-data"][companion_name]
        node.nlink = 3
        port.directories["dir-data"]["third-link"] = node
    elif attack == "substitute-companion":
        original = port.directories["dir-data"][companion_name]
        port.directories["dir-data"][companion_name] = port._new_inode(
            original.mode, bytes(original.content)
        )
    else:
        del port.directories["dir-data"][companion_name]
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT


def test_foreign_deterministic_companion_is_preserved_without_materialization(bundle_env) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    companion = service._names(command, access)[2]
    foreign = port.add_file("dir-data", companion, b"foreign")
    before_sources = tuple(registry.calls)
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.INDETERMINATE
    assert port.directories["dir-data"][companion] is foreign
    assert tuple(registry.calls) == before_sources


@pytest.mark.parametrize("failure", ["read", "stat_file", "close_file"])
def test_pair_read_stat_and_close_uncertainty_is_not_found(bundle_env, failure) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    assert service.seal(command, access).status is BundleLookupStatusV1.FOUND
    port.fail_before[failure] = port.calls.get(failure, 0) + 1
    assert service.lookup(command, access).status is not BundleLookupStatusV1.FOUND


def test_fresh_filesystem_and_reissued_borrows_recover_identical_binding(bundle_env) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    assert found.status is BundleLookupStatusV1.FOUND

    authenticator = Authenticator()
    base = Path.cwd() / ".fake-metadata" / "bundle-io"
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(
        authenticator.binding(base / "data", "bundle-data"),
        authenticator.binding(base / "control", "bundle-control"),
    )
    create_borrow, create_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_DESTINATION_CREATE,
        RootAccessV1.READ_CREATE,
    )
    verify_borrow, verify_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_MOUNT_VERIFY,
        RootAccessV1.READ_ONLY,
    )
    fresh_access = BundleBorrowAccessV1.build(
        command.destination_ref, create_borrow, create_root,
        verify_borrow, verify_root,
    )
    fresh = ImmutableSourceBundleV1(filesystem, registry)
    observed = fresh.lookup(command, fresh_access, expected=found.binding)
    assert observed.status is BundleLookupStatusV1.INDETERMINATE
    before_link = port.calls.get("link_at", 0)
    replay = fresh.seal(command, fresh_access)
    assert replay == found
    assert port.calls.get("link_at", 0) == before_link
    assert fresh._names(command, fresh_access)[2] == found.binding.companion_name


def test_mutated_source_is_closed_before_source_file_effect(bundle_env) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    source = registry.values["source-a"]
    object.__setattr__(source, "source_digest", "0" * 64)
    before_open = port.calls.get("open_read_at", 0)
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.INDETERMINATE
    assert port.calls.get("open_read_at", 0) == before_open


def test_private_directory_close_uncertainty_dominates(bundle_env, monkeypatch) -> None:
    _, filesystem, service, _, command, access, _, _ = bundle_env
    original = filesystem.close_borrowed_directory

    def lost_close(borrow, directory, *, purpose):
        original(borrow, directory, purpose=purpose)
        if directory.path_components and directory.path_components[-1].startswith(
            ".synaptic-bundle-"
        ):
            raise LocalIOErrorV1(LocalIOCodeV1.IO_FAILED)

    monkeypatch.setattr(filesystem, "close_borrowed_directory", lost_close)
    result = service.seal(command, access)
    assert result.status is BundleLookupStatusV1.INDETERMINATE


@pytest.mark.parametrize("operation", ["read", "stat", "close"])
def test_exact_pair_boundary_failure_cannot_return_found(
    bundle_env, monkeypatch, operation
) -> None:
    _, filesystem, service, _, command, access, _, _ = bundle_env
    assert service.seal(command, access).status is BundleLookupStatusV1.FOUND
    method_name = {
        "read": "read_borrowed_hardlink_pair",
        "stat": "stat_borrowed_hardlink_pair",
        "close": "close_borrowed_hardlink_pair",
    }[operation]
    original = getattr(filesystem, method_name)

    def fail(*args, **kwargs):
        if operation == "close":
            original(*args, **kwargs)
        raise LocalIOErrorV1(LocalIOCodeV1.IO_FAILED)

    monkeypatch.setattr(filesystem, method_name, fail)
    assert service.lookup(command, access).status is BundleLookupStatusV1.INDETERMINATE


def test_postlink_prefsync_failure_recovers_without_relink(bundle_env) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    port.fail_before["fsync_directory:data"] = 3
    first = service.seal(command, access)
    assert first.status is BundleLookupStatusV1.INDETERMINATE
    links = port.calls.get("link_at", 0)
    before_sources = tuple(registry.calls)
    observed = service.lookup(command, access)
    assert observed.status is BundleLookupStatusV1.INDETERMINATE
    recovered = service.seal(command, access)
    assert recovered.status is BundleLookupStatusV1.FOUND
    assert port.calls.get("link_at", 0) == links == 1
    assert tuple(registry.calls) == before_sources


def test_public_lookup_is_verify_only_and_never_attests_durability(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    assert found.status is BundleLookupStatusV1.FOUND
    before = {
        name: port.calls.get(name, 0)
        for name in (
            "mkdir_at", "create_exclusive_at", "write", "link_at",
            "fsync_file", "fsync_directory:data",
        )
    }
    observed = service.lookup(command, access, expected=found.binding)
    assert observed.status is BundleLookupStatusV1.INDETERMINATE
    assert observed.binding is None
    assert {
        name: port.calls.get(name, 0) for name in before
    } == before


@pytest.mark.parametrize(
    "payload",
    [
        b'{"command_digest":"duplicate","command_digest":"duplicate"}',
        b'{"schema_version":"synaptic-host-bundle-commit/v1"} ',
        b"{",
    ],
)
def test_noncanonical_truncated_and_duplicate_marker_is_conflict(bundle_env, payload) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found = service.seal(command, access)
    node = port.directories["dir-data"][found.binding.marker_name]
    node.content[:] = payload
    node.changed_ns += 1
    node.modified_ns += 1
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT
