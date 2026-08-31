from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from synaptic_host.artifact_destinations import DestinationAdapterInstallationV1
from synaptic_host.local_artifact_destination import (
    LocalArtifactDestinationCodeV1,
    LocalArtifactDestinationErrorV1,
    LocalArtifactDestinationV1,
    build_local_artifact_destination_registration_v1,
)
from synaptic_host.artifact_spool import LocalArtifactSpoolV1
from synaptic_host.local_io_v1.config import StorageRegistryV1
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import (
    LocalArtifactBindingV1,
    LocalCreateAuthorityV1,
    LocalDestinationBindingV1,
    LocalFileIdentityV1,
    LocalRootAuthorityV1,
    LocalSourceBindingV1,
    RetainedDirectoryV1,
    RecoveryResultV1,
    RecoveryStatusV1,
    digest_v1,
    root_authority_digest_v1,
)
from synaptic_host.publication_authority import create_publication_evidence_v1
from synaptic_tuner.api.v1 import ProjectContext, TrainingRunRef, VerifiedArtifact
from synaptic_tuner.api.v1.publication import (
    LookupOutcomeV1,
    LookupRecoveryPermitV1,
    MaterializedSourceV1,
    PublicationCommandV1,
    SpooledArtifactV1,
    TransferOwnershipV1,
)


_CONFIG = json.dumps({
    "control_root_ref": "artifact-control",
    "data_root_ref": "artifact-data",
    "schema_version": "synaptic-local-artifact-destination/v1",
}, sort_keys=True, separators=(",", ":")).encode()


def _identity(inode: int, size: int) -> LocalFileIdentityV1:
    return LocalFileIdentityV1(
        7, inode, stat.S_IFREG | 0o600, 1, size, size, size
    )


class _Storage:
    def __init__(self) -> None:
        self.trace = []
        self.bindings = {
            "artifact-data": object(),
            "artifact-control": object(),
        }

    def issue_root_permit(self, root_ref, *, authority_ref, key_ref, proof_digest):
        self.trace.append(("issue", root_ref, authority_ref, key_ref, proof_digest))
        if root_ref not in self.bindings:
            raise RuntimeError("closed fake unknown root")
        return object()

    def resolve(self, root_ref):
        self.trace.append(("resolve", root_ref))
        return self.bindings[root_ref]


class _Filesystem:
    def __init__(self) -> None:
        self.trace = []
        self.authority = None
        self.files: dict[str, bytes] = {}
        self.bindings: dict[str, LocalDestinationBindingV1] = {}
        self.statuses: dict[str, RecoveryStatusV1] = {}
        self.raw_results = {}
        self.next_inode = 100
        self.release_fails = False
        self.invalid_authority_digest = False

    def retain_root_authority(self, data, control):
        self.trace.append((
            "retain", data.root_ref, control.root_ref,
            data.root_permit.authority_ref, data.root_permit.key_ref,
            data.root_permit.proof_digest,
        ))
        if self.invalid_authority_digest:
            return SimpleNamespace(authority_digest="invalid")
        data_directory = RetainedDirectoryV1(
            "data-directory", LocalFileIdentityV1(
                7, 10, stat.S_IFDIR | 0o700, 1, 1, 1, 0
            )
        )
        control_directory = RetainedDirectoryV1(
            "control-directory", LocalFileIdentityV1(
                7, 11, stat.S_IFDIR | 0o700, 1, 1, 1, 0
            )
        )
        self.authority = LocalRootAuthorityV1(
            "root-authority", data, control, data_directory, control_directory,
            root_authority_digest_v1(
                data, control, data_directory.identity, control_directory.identity
            ),
        )
        return self.authority

    def release_root_authority(self, authority):
        self.trace.append("release")
        if self.release_fails:
            raise RuntimeError("closed fake release failure")

    def bind_destination(
        self, authority, relative_path, *, role, expected_size, expected_sha256
    ):
        assert "/" not in relative_path and "\\" not in relative_path
        binding = LocalDestinationBindingV1(
            authority.authority_digest, relative_path, role,
            expected_size, expected_sha256,
        )
        self.bindings[role] = binding
        return binding

    def authorize_create(self, authority, destination):
        self.trace.append("authorize:" + destination.role)
        mutation = digest_v1({
            "destination_digest": destination.destination_digest,
            "root_authority_digest": authority.authority_digest,
        })
        return LocalCreateAuthorityV1(
            "create-" + destination.role, authority.authority_digest,
            destination.destination_digest, mutation,
        )

    def _artifact(self, authority, destination):
        self.next_inode += 1
        return LocalArtifactBindingV1(
            destination.destination_digest, destination.relative_path,
            destination.role, destination.expected_size,
            destination.expected_sha256,
            _identity(self.next_inode, destination.expected_size),
        )

    def create_once(self, authority, create, destination, chunks):
        self.trace.append("create:" + destination.role)
        override = self.statuses.get(destination.role)
        if override is not None and override is not RecoveryStatusV1.FOUND:
            return RecoveryResultV1(override, create.mutation_id)
        payload = b"".join(chunks)
        if (
            len(payload) != destination.expected_size
            or hashlib.sha256(payload).hexdigest() != destination.expected_sha256
        ):
            return RecoveryResultV1(RecoveryStatusV1.INDETERMINATE, create.mutation_id)
        self.files[destination.relative_path] = payload
        artifact = self._artifact(authority, destination)
        return RecoveryResultV1(RecoveryStatusV1.FOUND, create.mutation_id, artifact)

    def recover_create(self, authority, destination):
        self.trace.append("recover:" + destination.role)
        if destination.role in self.raw_results:
            return self.raw_results[destination.role]
        mutation = digest_v1({
            "destination_digest": destination.destination_digest,
            "root_authority_digest": authority.authority_digest,
        })
        override = self.statuses.get(destination.role)
        if override is not None:
            artifact = (
                self._artifact(authority, destination)
                if override is RecoveryStatusV1.FOUND else None
            )
            return RecoveryResultV1(override, mutation, artifact)
        payload = self.files.get(destination.relative_path)
        if payload is None:
            return RecoveryResultV1(RecoveryStatusV1.DEFINITELY_ABSENT, mutation)
        return RecoveryResultV1(
            RecoveryStatusV1.FOUND, mutation, self._artifact(authority, destination)
        )

    def inspect_source(self, authority, relative_path, *, role, maximum_bytes):
        self.trace.append("inspect:" + role)
        payload = self.files[relative_path]
        if len(payload) > maximum_bytes:
            raise RuntimeError("closed fake bound failure")
        return LocalSourceBindingV1(
            authority.authority_digest, relative_path, role, len(payload),
            hashlib.sha256(payload).hexdigest(), _identity(999, len(payload)),
        )

    def iter_source(self, authority, source, *, chunk_size):
        payload = self.files[source.relative_path]
        for offset in range(0, len(payload), chunk_size):
            yield payload[offset:offset + chunk_size]


class _Spool:
    def __init__(self, artifacts: tuple[VerifiedArtifact, ...]) -> None:
        self.values = {
            "spool:" + item.role: (item, (item.role + "-payload").encode())
            for item in artifacts
        }
        self.trace = []

    def _iter_finished(self, reference, expected):
        self.trace.append("iter:" + reference)
        artifact, payload = self.values[reference]
        assert artifact == expected
        yield payload

    def _release_finished(self, reference):
        self.trace.append("release:" + reference)
        del self.values[reference]


_SPOOL_STATES = {}


def _spool_iter(self, reference, expected):
    yield from _SPOOL_STATES[id(self)]._iter_finished(reference, expected)


def _spool_release(self, reference):
    return _SPOOL_STATES[id(self)]._release_finished(reference)


def _artifact(role: str) -> VerifiedArtifact:
    payload = (role + "-payload").encode()
    return VerifiedArtifact(role, hashlib.sha256(payload).hexdigest(), len(payload))


def _evidence(tmp_path: Path):
    return create_publication_evidence_v1(ProjectContext.host(
        engine_root=tmp_path / "engine",
        project_root=tmp_path,
        state_root=tmp_path / ".synaptic" / "state",
    ))


def _command(evidence, artifacts):
    return PublicationCommandV1.build(
        run=TrainingRunRef("run-1", "project-1"),
        source_identity_digest="b" * 64,
        source_inventory=artifacts,
        destination_ref="local-default",
        destination_identity_digest="c" * 64,
        destination_authority_ref=evidence.verifier.authority_ref,
        destination_key_ref=evidence.verifier.key_ref,
        destination_configuration_digest="d" * 64,
        destination_policy_digest="e" * 64,
        maximum_artifact_bytes=1024,
        maximum_total_bytes=4096,
    )


def _ownership(command):
    return TransferOwnershipV1(
        command.publication_id, command.command_digest, command.mutation_id,
        "f" * 64, "1" * 64, 1, "2026-08-31T12:00:00Z",
    )


def _permit(command, ownership):
    return LookupRecoveryPermitV1(
        command.publication_id, command.command_digest, command.mutation_id,
        ownership.claim_digest, ownership.ownership_id, "2" * 64, 2,
        "2026-08-31T12:01:00Z",
    )


def _installed(tmp_path: Path, monkeypatch, artifacts=None, *, invoke_factory=True):
    artifacts = (_artifact("adapter"),) if artifacts is None else artifacts
    fake_filesystem = _Filesystem()
    filesystem = LocalFilesystemV1(None, object(), native_platform="linux")
    for name in (
        "retain_root_authority", "release_root_authority", "bind_destination",
        "authorize_create", "create_once", "recover_create", "inspect_source",
        "iter_source",
    ):
        setattr(filesystem, name, getattr(fake_filesystem, name))
    storage_path = tmp_path / "storage.json"
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_text(json.dumps({
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {
                "root_ref": "artifact-data", "location": "project://data",
                "access": "read_create", "permit_ref": "permit-data",
            },
            {
                "root_ref": "artifact-control", "location": "project://control",
                "access": "read_create", "permit_ref": "permit-control",
            },
        ],
    }), encoding="utf-8")
    storage = StorageRegistryV1.load(storage_path, project_root=tmp_path.resolve())
    fake_spool, evidence = _Spool(artifacts), _evidence(tmp_path)
    spool = object.__new__(LocalArtifactSpoolV1)
    _SPOOL_STATES[id(spool)] = fake_spool
    monkeypatch.setattr(LocalArtifactSpoolV1, "_iter_finished", _spool_iter)
    monkeypatch.setattr(LocalArtifactSpoolV1, "_release_finished", _spool_release)
    installation = build_local_artifact_destination_registration_v1(
        filesystem=filesystem, storage=storage, spool=spool, evidence=evidence,
        permit_authority_ref="composition-authority",
        permit_key_ref="composition-key",
        permit_proof_digest="9" * 64,
    )
    resolved = installation.registration.factory(_CONFIG) if invoke_factory else None
    return (
        installation, None if resolved is None else resolved.adapter, fake_filesystem, storage,
        fake_spool, evidence, artifacts,
    )


def test_registration_authorizes_exact_roots_and_binds_authority(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, storage, _spool, _evidence_value, _ = _installed(
        tmp_path, monkeypatch
    )
    assert type(adapter) is LocalArtifactDestinationV1
    assert installation.registration.adapter_ref == "host.local/v1"
    assert filesystem.trace == [(
        "retain", "artifact-data", "artifact-control", "composition-authority",
        "composition-key", "9" * 64,
    )]
    assert storage.resolve("artifact-data").root_permit is not None


def test_publish_and_found_lookup_reconstruct_byte_identical_receipt(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, _storage, spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    ownership = _ownership(command)
    source = MaterializedSourceV1(
        command.source_identity_digest,
        tuple(SpooledArtifactV1(item, "spool:" + item.role) for item in artifacts),
    )
    receipt = adapter.publish_once(command, source, ownership)
    assert spool.values == {}
    assert tuple(item.role for item in receipt.inventory.inventory.artifacts) == ("adapter",)
    path = receipt.inventory.inventory.artifacts[0].path
    assert "/" not in path and "\\" not in path
    assert command.publication_id not in path
    permit = _permit(command, ownership)
    lookup = adapter.lookup(command, permit)
    assert lookup.outcome is LookupOutcomeV1.FOUND
    assert lookup.receipt == receipt
    assert lookup.receipt.canonical_bytes == receipt.canonical_bytes
    assert evidence.verifier.verify(
        "publication-receipt/v1", receipt.payload, receipt.tag, receipt.key_ref
    )
    installation.cleanup_owned()


def test_absent_lookup_issues_authenticated_tombstone(tmp_path, monkeypatch) -> None:
    installation, adapter, _filesystem, _storage, _spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    ownership = _ownership(command)
    lookup = adapter.lookup(command, _permit(command, ownership))
    assert lookup.outcome is LookupOutcomeV1.DEFINITELY_ABSENT
    assert lookup.tombstone is not None and lookup.receipt is None
    assert lookup.tombstone.mutation_registry_digest == lookup.mutation_registry_digest
    assert evidence.verifier.verify(
        "publication-tombstone/v1", lookup.tombstone.payload,
        lookup.tombstone.tag, lookup.tombstone.key_ref,
    )
    installation.cleanup_owned()


@pytest.mark.parametrize(
    "statuses, outcome",
    [
        ((RecoveryStatusV1.FOUND, RecoveryStatusV1.DEFINITELY_ABSENT), LookupOutcomeV1.CONFLICT),
        ((RecoveryStatusV1.CONFLICT, RecoveryStatusV1.CONFLICT), LookupOutcomeV1.CONFLICT),
        ((RecoveryStatusV1.ACTIVE, RecoveryStatusV1.FOUND), LookupOutcomeV1.INDETERMINATE),
        ((RecoveryStatusV1.INDETERMINATE, RecoveryStatusV1.DEFINITELY_ABSENT), LookupOutcomeV1.INDETERMINATE),
    ],
)
def test_lookup_classifies_exact_recovery_set(tmp_path, monkeypatch, statuses, outcome) -> None:
    artifacts = (_artifact("adapter"), _artifact("model"))
    installation, adapter, filesystem, _storage, _spool, evidence, _ = _installed(
        tmp_path, monkeypatch, artifacts
    )
    command = _command(evidence, artifacts)
    filesystem.statuses = dict(zip(("adapter", "model"), statuses))
    lookup = adapter.lookup(command, _permit(command, _ownership(command)))
    assert lookup.outcome is outcome
    assert lookup.receipt is None and lookup.tombstone is None
    installation.cleanup_owned()


def test_publish_indeterminate_retains_spool_reference(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, _storage, spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    filesystem.statuses["adapter"] = RecoveryStatusV1.INDETERMINATE
    source = MaterializedSourceV1(
        command.source_identity_digest,
        (SpooledArtifactV1(artifacts[0], "spool:adapter"),),
    )
    with pytest.raises(LocalArtifactDestinationErrorV1) as failed:
        adapter.publish_once(command, source, _ownership(command))
    assert failed.value.code is LocalArtifactDestinationCodeV1.INDETERMINATE
    assert "spool:adapter" in spool.values
    installation.cleanup_owned()


def test_found_recovery_releases_same_session_retained_spool(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, _storage, spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    ownership = _ownership(command)
    filesystem.statuses["adapter"] = RecoveryStatusV1.INDETERMINATE
    source = MaterializedSourceV1(
        command.source_identity_digest,
        (SpooledArtifactV1(artifacts[0], "spool:adapter"),),
    )
    with pytest.raises(LocalArtifactDestinationErrorV1):
        adapter.publish_once(command, source, ownership)
    filesystem.statuses["adapter"] = RecoveryStatusV1.FOUND
    lookup = adapter.lookup(command, _permit(command, ownership))
    assert lookup.outcome is LookupOutcomeV1.FOUND
    assert "spool:adapter" not in spool.values
    assert spool.trace[-1] == "release:spool:adapter"
    installation.cleanup_owned()


def test_iter_bytes_uses_inspection_and_rejects_wrong_artifact(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, _storage, _spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    source = MaterializedSourceV1(
        command.source_identity_digest,
        (SpooledArtifactV1(artifacts[0], "spool:adapter"),),
    )
    receipt = adapter.publish_once(command, source, _ownership(command))
    artifact = receipt.inventory.inventory.artifacts[0]
    assert b"".join(adapter.iter_bytes(command, artifact, artifact.size_bytes)) == b"adapter-payload"
    with pytest.raises(LocalArtifactDestinationErrorV1):
        adapter.iter_bytes(command, replace(artifact, path="wrong"), artifact.size_bytes)
    filesystem.files[artifact.path] = b"mutated-payload"
    with pytest.raises(LocalArtifactDestinationErrorV1) as changed:
        b"".join(adapter.iter_bytes(command, artifact, artifact.size_bytes))
    assert changed.value.code is LocalArtifactDestinationCodeV1.CONFLICT
    installation.cleanup_owned()


def test_factory_rollback_and_cleanup_are_sanitized_and_cached(tmp_path, monkeypatch) -> None:
    installed = _installed(tmp_path, monkeypatch, invoke_factory=False)
    installation, _adapter, filesystem = installed[:3]
    filesystem.invalid_authority_digest = True
    with pytest.raises(LocalArtifactDestinationErrorV1):
        installation.registration.factory(_CONFIG)
    assert filesystem.trace[-1] == "release"

    healthy = _installed(tmp_path / "healthy", monkeypatch)
    healthy_installation, _adapter, healthy_filesystem = healthy[:3]
    healthy_filesystem.release_fails = True
    result = healthy_installation.cleanup_owned()
    assert result is False
    assert healthy_installation.cleanup_owned() is False
    assert healthy_filesystem.trace.count("release") == 1


def test_closed_installation_rejects_late_factory(tmp_path, monkeypatch) -> None:
    installation, _adapter, _filesystem, _storage, _spool, _evidence_value, _ = _installed(
        tmp_path, monkeypatch
    )
    assert installation.cleanup_owned() is True
    with pytest.raises(LocalArtifactDestinationErrorV1) as closed:
        installation.registration.factory(_CONFIG)
    assert closed.value.code is LocalArtifactDestinationCodeV1.CLOSED


def test_cleanup_with_active_reader_is_nonterminal_and_retryable(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, _storage, _spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    source = MaterializedSourceV1(
        command.source_identity_digest,
        (SpooledArtifactV1(artifacts[0], "spool:adapter"),),
    )
    receipt = adapter.publish_once(command, source, _ownership(command))
    artifact = receipt.inventory.inventory.artifacts[0]
    reader = adapter.iter_bytes(command, artifact, artifact.size_bytes)
    assert next(reader) == b"adapter-payload"
    with pytest.raises(LocalArtifactDestinationErrorV1) as active:
        installation.cleanup_owned()
    assert active.value.code is LocalArtifactDestinationCodeV1.IN_USE
    assert "release" not in filesystem.trace
    reader.close()
    cleaned = installation.cleanup_owned()
    assert cleaned is True
    assert installation.cleanup_owned() is True
    assert filesystem.trace.count("release") == 1


def test_builder_rejects_nonexact_dependencies_immediately(tmp_path, monkeypatch) -> None:
    installed = _installed(tmp_path, monkeypatch, invoke_factory=False)
    _installation, _adapter, _fake_filesystem, storage, _fake_spool, evidence, _ = installed
    filesystem = LocalFilesystemV1(None, object(), native_platform="linux")
    spool = object.__new__(LocalArtifactSpoolV1)
    common = {
        "filesystem": filesystem,
        "storage": storage,
        "spool": spool,
        "evidence": evidence,
        "permit_authority_ref": "composition-authority",
        "permit_key_ref": "composition-key",
        "permit_proof_digest": "9" * 64,
    }
    for name in ("filesystem", "storage", "spool", "evidence"):
        values = dict(common)
        values[name] = object()
        with pytest.raises(LocalArtifactDestinationErrorV1) as invalid:
            build_local_artifact_destination_registration_v1(**values)
        assert invalid.value.code is LocalArtifactDestinationCodeV1.INVALID


def test_malformed_recovery_is_authenticated_conflict(tmp_path, monkeypatch) -> None:
    installation, adapter, filesystem, _storage, _spool, evidence, artifacts = _installed(
        tmp_path, monkeypatch
    )
    command = _command(evidence, artifacts)
    filesystem.raw_results["adapter"] = object()
    lookup = adapter.lookup(command, _permit(command, _ownership(command)))
    assert lookup.outcome is LookupOutcomeV1.CONFLICT
    assert evidence.verifier.verify(
        "publication-lookup/v1", lookup.payload, lookup.tag, lookup.key_ref
    )
    installation.cleanup_owned()


def test_installation_cleans_every_factory_created_adapter_once(tmp_path, monkeypatch) -> None:
    installed = _installed(tmp_path, monkeypatch)
    installation, _adapter, filesystem = installed[:3]
    assert type(installation) is DestinationAdapterInstallationV1
    second = installation.registration.factory(_CONFIG)
    assert type(second.adapter) is LocalArtifactDestinationV1
    result = installation.cleanup_owned()
    assert result is True
    assert filesystem.trace.count("release") == 2
    assert installation.cleanup_owned() is True
    assert filesystem.trace.count("release") == 2
