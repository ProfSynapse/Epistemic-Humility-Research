from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from threading import Event, Thread

import pytest

import synaptic_host.bundle_io_v1.bundle as bundle_module
from synaptic_host.bundle_io_v1.model import (
    MAX_BUNDLE_CHUNK_BYTES,
    MAX_BUNDLE_MANIFEST_BYTES,
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleLookupStatusV1,
    BundleMountVerificationV1,
    BundleMemberCommandV1,
    BundleSealCommandV1,
    bundle_companion_digest_v1,
)
from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.ports import (
    BundleBorrowAccessV1,
    BundleMountVerifyAccessV1,
    BundleSourceV1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import BorrowPurposeV1, RootAccessV1
from synaptic_host.local_io_v1.model import LocalIOCodeV1, LocalIOErrorV1

from .conftest import Authenticator, BindingAuthority, borrow


def private_handle(port, command):
    name = ".synaptic-bundle-" + command.command_digest[:32]
    return port.directories["dir-data"][name].directory_handle


def mount_access(access):
    return BundleMountVerifyAccessV1.build(
        access.destination_ref, access.verify_borrow, access.verify_root
    )


def authenticated_found(service, command, access):
    found = service.seal(command, access)
    assert found.status is BundleLookupStatusV1.FOUND
    return found, service._binding_authority.issue(found.binding)


_MUTATION_EVENTS = {
    "mkdir_at", "create_exclusive_at", "write", "fsync_file",
    "fsync_directory:data", "link_at", "unlink_at",
}


def test_verify_mount_is_authenticated_read_only_and_logically_bound(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found, authenticated = authenticated_found(service, command, access)
    before = len(port.trace)
    verification = service.verify_mount(
        command, mount_access(access), authenticated
    )
    assert type(verification) is BundleMountVerificationV1
    assert verification.read_only is True
    assert verification.binding_digest == found.binding.binding_digest
    assert verification.private_name == found.binding.private_name
    assert verification.logical_entries == tuple(
        (value.logical_name, value.physical_name, value.size, value.sha256)
        for value in found.binding.members
    )
    assert _MUTATION_EVENTS.isdisjoint(port.trace[before:])


@pytest.mark.parametrize("field,value", [
    ("authority_ref", "alternate-authority"),
    ("key_ref", "alternate-key"),
    ("tag", "0" * 64),
])
def test_verify_mount_rejects_alternate_or_forged_signer_before_fs(
    bundle_env, field, value
) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    _, authenticated = authenticated_found(service, command, access)
    forged = replace(authenticated, **{field: value})
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, mount_access(access), forged)
    assert caught.value.code is BundleIOCodeV1.AUTHENTICATION_FAILED
    assert tuple(port.trace) == before


def test_verify_mount_rejects_mutated_nested_binding_and_throwing_authority(
    bundle_env,
) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    _, authenticated = authenticated_found(service, command, access)
    before = tuple(port.trace)
    object.__setattr__(authenticated.content, "destination_ref", "rebound")
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, mount_access(access), authenticated)
    assert caught.value.code is BundleIOCodeV1.AUTHENTICATION_FAILED
    assert tuple(port.trace) == before


def test_verify_mount_rejects_boolean_authentication_result_before_fs(
    bundle_env,
) -> None:
    port, _, service, registry, command, access, _, _ = bundle_env
    _, authenticated = authenticated_found(service, command, access)

    class BooleanAuthority:
        authority_ref = service._binding_authority_ref
        key_ref = service._binding_key_ref

        def authenticate(self, value):
            return True

    boolean_service = ImmutableSourceBundleV1(
        service._port, registry, BooleanAuthority()
    )
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        boolean_service.verify_mount(
            command, mount_access(access), authenticated
        )
    assert caught.value.code is BundleIOCodeV1.AUTHENTICATION_FAILED
    assert tuple(port.trace) == before

    _, authenticated = authenticated_found(service, command, access)
    service._binding_authority.authenticate = lambda value: (_ for _ in ()).throw(
        RuntimeError("SENTINEL secret authority failure")
    )
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, mount_access(access), authenticated)
    assert caught.value.code is BundleIOCodeV1.AUTHENTICATION_FAILED
    assert "SENTINEL" not in str(caught.value)
    assert tuple(port.trace) == before


@pytest.mark.parametrize("field,value", [
    ("destination_ref", "rebound"),
    ("root_authority_digest", "0" * 64),
    ("access_digest", "0" * 64),
])
def test_verify_mount_rejects_mutated_least_authority_access_zero_fs(
    bundle_env, field, value
) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    _, authenticated = authenticated_found(service, command, access)
    verify_access = mount_access(access)
    object.__setattr__(verify_access, field, value)
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, verify_access, authenticated)
    assert caught.value.code is BundleIOCodeV1.ACCESS_INVALID
    assert tuple(port.trace) == before


def test_verify_mount_rejects_exact_other_command_before_fs(bundle_env) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    _, authenticated = authenticated_found(service, command, access)
    other = BundleSealCommandV1.build(
        command.profile_ref, "other-purpose", command.destination_ref,
        command.members,
    )
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(other, mount_access(access), authenticated)
    assert caught.value.code is BundleIOCodeV1.CONFLICT
    assert tuple(port.trace) == before


def test_verify_mount_rejects_valid_cross_root_relabel_before_fs(bundle_env) -> None:
    port, filesystem, service, _, command, access, _, authenticator = bundle_env
    _, authenticated = authenticated_found(service, command, access)
    base = Path.cwd() / ".fake-metadata" / "bundle-io-other"
    data = base / "data"
    control = base / "control"
    port.add_root(data, "other-data")
    port.add_root(control, "other-control")
    other_authority = filesystem.retain_root_authority(
        authenticator.binding(data, "other-bundle-data"),
        authenticator.binding(control, "other-bundle-control"),
    )
    other_borrow, other_root = borrow(
        filesystem, other_authority, BorrowPurposeV1.BUNDLE_MOUNT_VERIFY,
        RootAccessV1.READ_ONLY,
    )
    relabeled = BundleMountVerifyAccessV1.build(
        command.destination_ref, other_borrow, other_root
    )
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, relabeled, authenticated)
    assert caught.value.code is BundleIOCodeV1.CONFLICT
    assert tuple(port.trace) == before


def test_mount_verify_access_rejects_create_purpose_without_port_calls(bundle_env) -> None:
    port, _, _, _, _, access, _, _ = bundle_env
    before = tuple(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        BundleMountVerifyAccessV1.build(
            access.destination_ref, access.create_borrow, access.create_root
        )
    assert caught.value.code is BundleIOCodeV1.ACCESS_INVALID
    assert tuple(port.trace) == before


@pytest.mark.parametrize(
    "tamper",
    ["extra", "missing", "member-content", "member-hardlink", "third-marker-link"],
)
def test_verify_mount_detects_namespace_content_and_identity_tamper(
    bundle_env, tamper
) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found, authenticated = authenticated_found(service, command, access)
    private = private_handle(port, command)
    if tamper == "extra":
        port.add_file(private, "extra", b"x")
    elif tamper == "missing":
        del port.directories[private]["member-0000"]
    elif tamper == "member-content":
        port.directories[private]["member-0000"].content[:] = b"ALPHA"
    elif tamper == "member-hardlink":
        port.directories[private]["member-0000"].nlink = 2
    else:
        port.directories["dir-data"][found.binding.marker_name].nlink = 3
    before = len(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, mount_access(access), authenticated)
    assert caught.value.code is BundleIOCodeV1.CONFLICT
    assert _MUTATION_EVENTS.isdisjoint(port.trace[before:])


@pytest.mark.parametrize("failure,offset", [
    ("close_directory", 1),
    ("close_file", 1),
    ("close_file", 4),
])
def test_verify_mount_close_uncertainty_dominates_and_never_mutates(
    bundle_env, failure, offset
) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    _, authenticated = authenticated_found(service, command, access)
    port.fail_before[failure] = port.calls.get(failure, 0) + offset
    before = len(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, mount_access(access), authenticated)
    assert caught.value.code is BundleIOCodeV1.INDETERMINATE
    assert _MUTATION_EVENTS.isdisjoint(port.trace[before:])


@pytest.mark.parametrize("target", ["marker", "manifest", "member"])
def test_oversized_retained_content_is_bound_for_verify_and_conflict_for_legacy(
    bundle_env, target
) -> None:
    port, _, service, _, command, access, _, _ = bundle_env
    found, authenticated = authenticated_found(service, command, access)
    private = private_handle(port, command)
    if target == "marker":
        node = port.directories["dir-data"][found.binding.marker_name]
        node.content.extend(b"x" * (MAX_BUNDLE_MANIFEST_BYTES + 1))
    elif target == "manifest":
        node = port.directories[private]["MANIFEST.json"]
        node.content.extend(b"x" * (MAX_BUNDLE_MANIFEST_BYTES + 1))
    else:
        node = port.directories[private]["member-0000"]
        node.content.extend(b"x")
    before = len(port.trace)
    with pytest.raises(BundleIOErrorV1) as caught:
        service.verify_mount(command, mount_access(access), authenticated)
    assert caught.value.code is BundleIOCodeV1.BOUND_EXCEEDED
    assert _MUTATION_EVENTS.isdisjoint(port.trace[before:])
    before = len(port.trace)
    assert service.lookup(command, access).status is BundleLookupStatusV1.CONFLICT
    assert _MUTATION_EVENTS.isdisjoint(port.trace[before:])
    before = len(port.trace)
    assert service.seal(command, access).status is BundleLookupStatusV1.CONFLICT
    assert _MUTATION_EVENTS.isdisjoint(port.trace[before:])


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
    fresh = ImmutableSourceBundleV1(
        filesystem, registry, BindingAuthority()
    )
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


def test_concurrent_replay_linearizes_exact_durability_proof(
    bundle_env, monkeypatch
) -> None:
    _, filesystem, service, _, command, access, _, _ = bundle_env
    assert service.seal(command, access).status is BundleLookupStatusV1.FOUND
    original = filesystem.open_borrowed_hardlink_pair
    entered = Event()
    resume = Event()
    calls = []
    outcomes = []

    def blocked_first(*args, **kwargs):
        calls.append("open")
        if len(calls) == 1:
            entered.set()
            assert resume.wait(2)
        return original(*args, **kwargs)

    def replay():
        outcomes.append(service.seal(command, access).status)

    monkeypatch.setattr(filesystem, "open_borrowed_hardlink_pair", blocked_first)
    first = Thread(target=replay)
    second = Thread(target=replay)
    first.start()
    assert entered.wait(2)
    second.start()
    assert calls == ["open"]
    resume.set()
    first.join(2)
    second.join(2)
    assert not first.is_alive()
    assert not second.is_alive()
    assert outcomes == [BundleLookupStatusV1.FOUND] * 2


def test_durability_guards_do_not_serialize_distinct_bindings(bundle_env) -> None:
    _, _, service, _, _, _, _, _ = bundle_env
    first_entered = Event()
    second_entered = Event()
    resume = Event()

    def hold(key, entered):
        with service._durability_guard(key):
            entered.set()
            assert resume.wait(2)

    first = Thread(target=hold, args=("a" * 64, first_entered))
    second = Thread(target=hold, args=("b" * 64, second_entered))
    first.start()
    assert first_entered.wait(2)
    second.start()
    assert second_entered.wait(2)
    resume.set()
    first.join(2)
    second.join(2)
    assert service._seal_guards == {}


def test_durability_guard_acquisition_failure_cleans_registry_and_recovers(
    bundle_env, monkeypatch
) -> None:
    _, _, service, _, _, _, _, _ = bundle_env
    key = "c" * 64

    class FailingAcquire:
        release_calls = 0

        def __enter__(self):
            raise RuntimeError("closed acquisition failure")

        def __exit__(self, exception_type, exception, traceback):
            self.release_calls += 1

    failing = FailingAcquire()
    with monkeypatch.context() as patch:
        patch.setattr(bundle_module, "Lock", lambda: failing)
        with pytest.raises(RuntimeError, match="closed acquisition failure"):
            with service._durability_guard(key):
                raise AssertionError("unreachable body")
    assert failing.release_calls == 0
    assert service._seal_guards == {}
    with service._durability_guard(key):
        pass
    assert service._seal_guards == {}


def test_durability_guard_body_exception_releases_and_recovers(bundle_env) -> None:
    _, _, service, _, _, _, _, _ = bundle_env
    key = "d" * 64
    with pytest.raises(RuntimeError, match="closed body failure"):
        with service._durability_guard(key):
            raise RuntimeError("closed body failure")
    assert service._seal_guards == {}
    with service._durability_guard(key):
        pass
    assert service._seal_guards == {}


def test_durability_guard_release_failure_still_cleans_registry(
    bundle_env, monkeypatch
) -> None:
    _, _, service, _, _, _, _, _ = bundle_env
    key = "e" * 64

    class FailingRelease:
        release_calls = 0

        def __enter__(self):
            return self

        def __exit__(self, exception_type, exception, traceback):
            self.release_calls += 1
            raise RuntimeError("closed release failure")

    failing = FailingRelease()
    with monkeypatch.context() as patch:
        patch.setattr(bundle_module, "Lock", lambda: failing)
        with pytest.raises(RuntimeError, match="closed release failure"):
            with service._durability_guard(key):
                pass
    assert failing.release_calls == 1
    assert service._seal_guards == {}
    with service._durability_guard(key):
        pass
    assert service._seal_guards == {}


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
