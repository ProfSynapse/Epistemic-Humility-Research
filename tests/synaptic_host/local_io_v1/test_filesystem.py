from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1, MAX_CHUNK_BYTES
from synaptic_host.local_io_v1.config import StorageRegistryV1
from synaptic_host.local_io_v1.model import (
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
    RecoveryStatusV1,
    RootAccessV1,
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

    def allow(self, permit: LocalRootPermitV1) -> None:
        self.permits[id(permit)] = permit

    def authenticate(self, permit: LocalRootPermitV1):
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
    data_path = Path("C:/metadata") / profile / "data"
    control_path = Path("C:/metadata") / profile / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    authenticator = _Authenticator()
    data = _binding(data_path, profile, RootAccessV1.READ_CREATE, authenticator)
    control = _binding(control_path, profile + "-control", RootAccessV1.READ_CREATE, authenticator)
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(data, control)
    return port, filesystem, authority


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
    path = Path("C:/metadata/same")
    port.add_root(path, "data")
    authenticator = _Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    data = _binding(path, "data", RootAccessV1.READ_CREATE, authenticator)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.retain_root_authority(data, data)
    assert caught.value.code is LocalIOCodeV1.ROOT_INVALID
    control_path = Path("C:/metadata/control")
    port.add_root(control_path, "control")
    read_only = _binding(control_path, "control", RootAccessV1.READ_ONLY, authenticator)
    with pytest.raises(LocalIOErrorV1) as caught:
        filesystem.retain_root_authority(data, read_only)
    assert caught.value.code is LocalIOCodeV1.ACCESS_MISMATCH


def test_pair_acquisition_failure_closes_returned_data_handle() -> None:
    port = FakePosixFilesystemPortV1()
    data_path = Path("C:/metadata/pair-data")
    control_path = Path("C:/metadata/pair-control")
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
