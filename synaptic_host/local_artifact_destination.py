"""Capability-only local artifact destination for publication engine adapters."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import RLock

from synaptic_tuner.api.v1 import VerifiedArtifact
from synaptic_tuner.api.v1.publication import (
    AuthenticatedDestinationInventoryV1,
    AuthenticatedLookupV1,
    AuthenticatedPublicationReceiptV1,
    AuthenticatedPublicationTombstoneV1,
    DestinationArtifactV1,
    DestinationInventoryV1,
    LookupOutcomeV1,
    LookupRecoveryPermitV1,
    MaterializedSourceV1,
    PublicationCommandV1,
    SpooledArtifactV1,
    TransferOwnershipV1,
)

from .artifact_destinations import (
    DestinationAdapterInstallationV1,
    DestinationAdapterRegistrationV1,
    ResolvedDestinationAdapterV1,
)
from .artifact_spool import LocalArtifactSpoolV1
from .local_io_v1.config import StorageRegistryV1
from .local_io_v1.filesystem import MAX_CHUNK_BYTES, LocalFilesystemV1
from .local_io_v1.model import (
    LocalArtifactBindingV1,
    LocalDestinationBindingV1,
    LocalRootAuthorityV1,
    LocalSourceBindingV1,
    RecoveryResultV1,
    RecoveryStatusV1,
    digest_v1,
    validate_recovery_result_v1,
)
from .publication_authority import PublicationEvidenceAuthorityV1


_ADAPTER_REF = "host.local/v1"
_CONFIG_SCHEMA = "synaptic-local-artifact-destination/v1"
_ZERO = "0" * 64
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
_MAX_EVIDENCE_BYTES = 1_048_576
_CONSTRUCTION_TOKEN = object()


class LocalArtifactDestinationCodeV1(str, Enum):
    INVALID = "LOCAL_ARTIFACT_DESTINATION_INVALID"
    CLOSED = "LOCAL_ARTIFACT_DESTINATION_CLOSED"
    CONFLICT = "LOCAL_ARTIFACT_DESTINATION_CONFLICT"
    INDETERMINATE = "LOCAL_ARTIFACT_DESTINATION_INDETERMINATE"
    IN_USE = "LOCAL_ARTIFACT_DESTINATION_IN_USE"
    IO_FAILED = "LOCAL_ARTIFACT_DESTINATION_IO_FAILED"


class LocalArtifactDestinationErrorV1(RuntimeError):
    __slots__ = ("code",)

    def __init__(self, code: LocalArtifactDestinationCodeV1) -> None:
        self.code = code
        super().__init__(code.value)


def _closed(code: LocalArtifactDestinationCodeV1) -> LocalArtifactDestinationErrorV1:
    return LocalArtifactDestinationErrorV1(code)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _domain(domain: str, value: object) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()


def _recorded_at_from_ownership_v1(ownership_id: str) -> str:
    """Map an ownership digest stably into 2000-01-01 through 2099-12-31 UTC."""

    if type(ownership_id) is not str or _DIGEST.fullmatch(ownership_id) is None:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    material = hashlib.sha256(
        b"synaptic-local-artifact-recorded-at/v1\0" + ownership_id.encode("ascii")
    ).digest()
    seconds = int.from_bytes(material[:8], "big") % (100 * 365 * 24 * 60 * 60)
    value = datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _artifact_component(command: PublicationCommandV1, artifact: VerifiedArtifact) -> str:
    return "synaptic-local-artifact-v1-" + _domain(
        "synaptic-local-artifact-component/v1",
        {
            "publication_id": command.publication_id,
            "role": artifact.role,
            "sha256": artifact.sha256,
            "size_bytes": artifact.size_bytes,
        },
    ) + ".blob"


def _parse_config(raw: bytes) -> tuple[str, str]:
    if type(raw) is not bytes or not raw or len(raw) > _MAX_EVIDENCE_BYTES:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if type(key) is not str or key in result:
                raise ValueError
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except Exception:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID) from None
    if (
        type(value) is not dict
        or set(value) != {"schema_version", "data_root_ref", "control_root_ref"}
        or value.get("schema_version") != _CONFIG_SCHEMA
        or _canonical(value) != raw
    ):
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    data_ref, control_ref = value.get("data_root_ref"), value.get("control_root_ref")
    if (
        type(data_ref) is not str or not data_ref
        or type(control_ref) is not str or not control_ref
        or data_ref == control_ref
    ):
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    return data_ref, control_ref


def _snapshot_command(value: object) -> PublicationCommandV1:
    if type(value) is not PublicationCommandV1:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    try:
        return replace(value)
    except BaseException:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID) from None


def _snapshot_source(value: object) -> MaterializedSourceV1:
    if type(value) is not MaterializedSourceV1:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    try:
        return MaterializedSourceV1(
            value.source_identity_digest,
            tuple(SpooledArtifactV1(
                VerifiedArtifact.from_dict(item.artifact.to_dict()), item.spool_ref
            ) for item in value.artifacts),
        )
    except BaseException:
        raise _closed(LocalArtifactDestinationCodeV1.INVALID) from None


def _registry_digest(results: tuple[RecoveryResultV1, ...]) -> str:
    return _domain("synaptic-local-artifact-mutation-registry/v1", {
        "entries": [
            {
                "artifact": None if item.artifact is None else {
                    "destination_digest": item.artifact.destination_digest,
                    "identity": item.artifact.identity.canonical(),
                    "relative_path": item.artifact.relative_path,
                    "role": item.artifact.role,
                    "sha256": item.artifact.sha256,
                    "size": item.artifact.size,
                },
                "mutation_id": item.mutation_id,
                "status": item.status.value,
            }
            for item in results
        ]
    })


class LocalArtifactDestinationV1:
    """One retained dual-root adapter implementing the engine destination port."""

    __slots__ = (
        "_filesystem", "_spool", "_evidence", "_authority", "_lock",
        "_lifecycle", "_active", "_retained_spool_refs",
    )

    def __init__(self, token, filesystem, spool, evidence, authority) -> None:
        if token is not _CONSTRUCTION_TOKEN:
            raise TypeError("local artifact destination is factory-created")
        self._filesystem = filesystem
        self._spool = spool
        self._evidence = evidence
        self._authority = authority
        self._lock = RLock()
        self._lifecycle = "OPEN"
        self._active = 0
        self._retained_spool_refs: dict[tuple[str, str], str] = {}

    def _enter(self) -> None:
        with self._lock:
            if self._lifecycle != "OPEN":
                raise _closed(LocalArtifactDestinationCodeV1.CLOSED)
            self._active += 1

    def _leave(self) -> None:
        with self._lock:
            self._active -= 1

    def _bindings(self, command: PublicationCommandV1):
        return tuple(
            (
                artifact,
                self._filesystem.bind_destination(
                    self._authority,
                    _artifact_component(command, artifact),
                    role=artifact.role,
                    expected_size=artifact.size_bytes,
                    expected_sha256=artifact.sha256,
                ),
            )
            for artifact in command.source_inventory
        )

    def _command(self, value: object) -> PublicationCommandV1:
        command = _snapshot_command(value)
        if (
            command.destination_authority_ref != self._evidence.verifier.authority_ref
            or command.destination_key_ref != self._evidence.verifier.key_ref
        ):
            raise _closed(LocalArtifactDestinationCodeV1.INVALID)
        return command

    def _validate_source(self, command, source, ownership):
        command = self._command(command)
        source = _snapshot_source(source)
        if type(ownership) is not TransferOwnershipV1:
            raise _closed(LocalArtifactDestinationCodeV1.INVALID)
        ownership = replace(ownership)
        if (
            source.source_identity_digest != command.source_identity_digest
            or source.inventory != command.source_inventory
            or ownership.publication_id != command.publication_id
            or ownership.command_digest != command.command_digest
            or ownership.mutation_id != command.mutation_id
        ):
            raise _closed(LocalArtifactDestinationCodeV1.INVALID)
        return command, source, ownership

    def _destination_artifact(
        self, expected: VerifiedArtifact, binding: LocalDestinationBindingV1,
        result: RecoveryResultV1,
    ) -> DestinationArtifactV1:
        try:
            expected_mutation_id = digest_v1({
                "destination_digest": binding.destination_digest,
                "root_authority_digest": self._authority.authority_digest,
            })
            checked = validate_recovery_result_v1(
                result, mutation_id=expected_mutation_id, destination=binding
            )
        except BaseException:
            raise _closed(LocalArtifactDestinationCodeV1.CONFLICT) from None
        artifact = checked.artifact
        if checked.status is not RecoveryStatusV1.FOUND or type(artifact) is not LocalArtifactBindingV1:
            code = (
                LocalArtifactDestinationCodeV1.INDETERMINATE
                if checked.status in {
                    RecoveryStatusV1.ACTIVE,
                    RecoveryStatusV1.INDETERMINATE,
                    RecoveryStatusV1.CAPABILITY_UNAVAILABLE,
                }
                else LocalArtifactDestinationCodeV1.CONFLICT
            )
            raise _closed(code)
        if (
            artifact.relative_path != binding.relative_path
            or artifact.role != expected.role
            or artifact.size != expected.size_bytes
            or artifact.sha256 != expected.sha256
        ):
            raise _closed(LocalArtifactDestinationCodeV1.CONFLICT)
        return DestinationArtifactV1(
            expected.role, binding.relative_path, expected.sha256, expected.size_bytes
        )

    def _inventory(self, command, ownership_id, artifacts):
        recorded_at = _recorded_at_from_ownership_v1(ownership_id)
        inventory = DestinationInventoryV1(tuple(artifacts))
        unsigned = AuthenticatedDestinationInventoryV1(
            inventory, command.publication_id, command.command_digest,
            command.mutation_id, ownership_id, recorded_at,
            self._evidence.destination_inventories.authority_ref,
            self._evidence.destination_inventories.key_ref, _ZERO,
        )
        return self._evidence.destination_inventories.issue(unsigned)

    def _receipt(self, command, claim_digest, ownership_id, artifacts):
        inventory = self._inventory(command, ownership_id, artifacts)
        unsigned = AuthenticatedPublicationReceiptV1(
            "synaptic-publication-receipt/v1", command.publication_id,
            command.command_digest, command.run, command.source_identity_digest,
            command.destination_ref, command.destination_identity_digest,
            command.mutation_id, claim_digest, ownership_id, inventory,
            _recorded_at_from_ownership_v1(ownership_id),
            self._evidence.receipts.authority_ref,
            self._evidence.receipts.key_ref, _ZERO,
        )
        return self._evidence.receipts.issue(unsigned)

    def publish_once(self, command, source, ownership):
        self._enter()
        try:
            command, source, ownership = self._validate_source(command, source, ownership)
            by_role = {item.artifact.role: item for item in source.artifacts}
            artifacts = []
            for expected, binding in self._bindings(command):
                spooled = by_role.get(expected.role)
                if spooled is None or spooled.artifact != expected:
                    raise _closed(LocalArtifactDestinationCodeV1.INVALID)
                with self._lock:
                    self._retained_spool_refs[
                        (command.publication_id, expected.role)
                    ] = spooled.spool_ref
                create = self._filesystem.authorize_create(self._authority, binding)
                result = self._filesystem.create_once(
                    self._authority, create, binding,
                    self._spool._iter_finished(spooled.spool_ref, expected),
                )
                artifacts.append(self._destination_artifact(expected, binding, result))
                self._spool._release_finished(spooled.spool_ref)
                with self._lock:
                    self._retained_spool_refs.pop(
                        (command.publication_id, expected.role), None
                    )
            return self._receipt(
                command, ownership.claim_digest, ownership.ownership_id, tuple(artifacts)
            )
        except LocalArtifactDestinationErrorV1:
            raise
        except BaseException:
            raise _closed(LocalArtifactDestinationCodeV1.IO_FAILED) from None
        finally:
            self._leave()

    def _lookup_evidence(
        self, command, permit, outcome, registry_digest,
        *, receipt=None, tombstone=None,
    ):
        unsigned = AuthenticatedLookupV1(
            "synaptic-publication-lookup/v1", outcome,
            command.publication_id, command.command_digest,
            command.destination_identity_digest, command.mutation_id,
            permit.fenced_ownership_id, permit.permit_id, registry_digest,
            permit.issued_at, tombstone, receipt,
            self._evidence.lookups.authority_ref,
            self._evidence.lookups.key_ref, _ZERO,
        )
        return self._evidence.lookups.issue(unsigned)

    def lookup(self, command, permit):
        self._enter()
        try:
            command = self._command(command)
            if type(permit) is not LookupRecoveryPermitV1:
                raise _closed(LocalArtifactDestinationCodeV1.INVALID)
            permit = replace(permit)
            if (
                permit.publication_id != command.publication_id
                or permit.command_digest != command.command_digest
                or permit.mutation_id != command.mutation_id
            ):
                raise _closed(LocalArtifactDestinationCodeV1.INVALID)
            bindings = self._bindings(command)
            results = tuple(
                self._filesystem.recover_create(self._authority, binding)
                for _artifact, binding in bindings
            )
            if any(type(item) is not RecoveryResultV1 for item in results):
                registry_digest = _domain(
                    "synaptic-local-artifact-invalid-registry/v1",
                    {"command_digest": command.command_digest},
                )
                return self._lookup_evidence(
                    command, permit, LookupOutcomeV1.CONFLICT, registry_digest
                )
            try:
                for (_expected, binding), result in zip(bindings, results):
                    validate_recovery_result_v1(
                        result,
                        mutation_id=digest_v1({
                            "destination_digest": binding.destination_digest,
                            "root_authority_digest": self._authority.authority_digest,
                        }),
                        destination=binding,
                    )
            except BaseException:
                registry_digest = _domain(
                    "synaptic-local-artifact-invalid-registry/v1",
                    {"command_digest": command.command_digest},
                )
                return self._lookup_evidence(
                    command, permit, LookupOutcomeV1.CONFLICT, registry_digest
                )
            registry_digest = _registry_digest(results)
            statuses = tuple(item.status for item in results)
            if any(status in {
                RecoveryStatusV1.ACTIVE,
                RecoveryStatusV1.INDETERMINATE,
                RecoveryStatusV1.CAPABILITY_UNAVAILABLE,
            } for status in statuses):
                return self._lookup_evidence(
                    command, permit, LookupOutcomeV1.INDETERMINATE, registry_digest
                )
            if all(status is RecoveryStatusV1.FOUND for status in statuses):
                artifacts = tuple(
                    self._destination_artifact(expected, binding, result)
                    for (expected, binding), result in zip(bindings, results)
                )
                for expected, _binding in bindings:
                    with self._lock:
                        spool_ref = self._retained_spool_refs.get(
                            (command.publication_id, expected.role)
                        )
                    if spool_ref is not None:
                        try:
                            self._spool._release_finished(spool_ref)
                        except BaseException:
                            pass
                        else:
                            with self._lock:
                                self._retained_spool_refs.pop(
                                    (command.publication_id, expected.role), None
                                )
                receipt = self._receipt(
                    command, permit.claim_digest,
                    permit.fenced_ownership_id, artifacts,
                )
                return self._lookup_evidence(
                    command, permit, LookupOutcomeV1.FOUND,
                    registry_digest, receipt=receipt,
                )
            if all(status is RecoveryStatusV1.DEFINITELY_ABSENT for status in statuses):
                evidence_digest = _domain(
                    "synaptic-local-artifact-absence-evidence/v1",
                    {"mutation_registry_digest": registry_digest,
                     "recovery_permit_id": permit.permit_id},
                )
                unsigned = AuthenticatedPublicationTombstoneV1(
                    "synaptic-publication-tombstone/v1",
                    command.publication_id, command.mutation_id,
                    command.command_digest, permit.claim_digest,
                    command.destination_ref, command.destination_identity_digest,
                    command.destination_configuration_digest,
                    command.destination_policy_digest,
                    command.destination_authority_ref,
                    command.destination_key_ref,
                    permit.fenced_ownership_id, permit.permit_id,
                    registry_digest, permit.issued_at, evidence_digest,
                    self._evidence.tombstones.authority_ref,
                    self._evidence.tombstones.key_ref, _ZERO,
                )
                tombstone = self._evidence.tombstones.issue(unsigned)
                return self._lookup_evidence(
                    command, permit, LookupOutcomeV1.DEFINITELY_ABSENT,
                    registry_digest, tombstone=tombstone,
                )
            return self._lookup_evidence(
                command, permit, LookupOutcomeV1.CONFLICT, registry_digest
            )
        except LocalArtifactDestinationErrorV1:
            raise
        except BaseException:
            raise _closed(LocalArtifactDestinationCodeV1.IO_FAILED) from None
        finally:
            self._leave()

    def iter_bytes(self, command, artifact, maximum_bytes):
        command = self._command(command)
        if (
            type(artifact) is not DestinationArtifactV1
            or type(maximum_bytes) is not int
            or maximum_bytes < artifact.size_bytes
            or maximum_bytes < 1
        ):
            raise _closed(LocalArtifactDestinationCodeV1.INVALID)
        expected = next(
            (item for item in command.source_inventory if item.role == artifact.role), None
        )
        if (
            expected is None
            or artifact.path != _artifact_component(command, expected)
            or artifact.sha256 != expected.sha256
            or artifact.size_bytes != expected.size_bytes
        ):
            raise _closed(LocalArtifactDestinationCodeV1.INVALID)

        def stream():
            self._enter()
            try:
                source = self._filesystem.inspect_source(
                    self._authority, artifact.path,
                    role=artifact.role, maximum_bytes=maximum_bytes,
                )
                if (
                    type(source) is not LocalSourceBindingV1
                    or source.role != artifact.role
                    or source.size != artifact.size_bytes
                    or source.sha256 != artifact.sha256
                ):
                    raise _closed(LocalArtifactDestinationCodeV1.CONFLICT)
                yield from self._filesystem.iter_source(
                    self._authority, source, chunk_size=MAX_CHUNK_BYTES
                )
            except GeneratorExit:
                raise
            except LocalArtifactDestinationErrorV1:
                raise
            except BaseException:
                raise _closed(LocalArtifactDestinationCodeV1.IO_FAILED) from None
            finally:
                self._leave()

        return stream()

    def _cleanup_owned(self) -> LocalArtifactDestinationCodeV1 | None:
        with self._lock:
            if self._lifecycle == "CLOSED":
                return None
            if self._lifecycle == "OPEN":
                self._lifecycle = "CLOSING"
            if self._active:
                return LocalArtifactDestinationCodeV1.IN_USE
        try:
            self._filesystem.release_root_authority(self._authority)
        except BaseException:
            code = LocalArtifactDestinationCodeV1.IO_FAILED
        else:
            code = None
        with self._lock:
            self._lifecycle = "CLOSED"
        return code


@dataclass(slots=True)
class _InstallationStateV1:
    lock: RLock
    adapters: list[LocalArtifactDestinationV1]
    open: bool = True
    result: bool | None = None
    terminal_failures: set[LocalArtifactDestinationCodeV1] = field(
        default_factory=set
    )


def build_local_artifact_destination_registration_v1(
    *,
    filesystem: LocalFilesystemV1,
    storage: StorageRegistryV1,
    spool: LocalArtifactSpoolV1,
    evidence: PublicationEvidenceAuthorityV1,
    permit_authority_ref: str,
    permit_key_ref: str,
    permit_proof_digest: str,
) -> DestinationAdapterInstallationV1:
    """Build one installed registration whose closure owns every created adapter."""

    if (
        type(filesystem) is not LocalFilesystemV1
        or type(storage) is not StorageRegistryV1
        or type(spool) is not LocalArtifactSpoolV1
        or type(evidence) is not PublicationEvidenceAuthorityV1
    ):
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    if (
        type(permit_authority_ref) is not str
        or _SAFE_REF.fullmatch(permit_authority_ref) is None
        or type(permit_key_ref) is not str
        or _SAFE_REF.fullmatch(permit_key_ref) is None
        or type(permit_proof_digest) is not str
        or _DIGEST.fullmatch(permit_proof_digest) is None
    ):
        raise _closed(LocalArtifactDestinationCodeV1.INVALID)
    state = _InstallationStateV1(RLock(), [])

    def factory(configuration: bytes) -> ResolvedDestinationAdapterV1:
        authority = None
        with state.lock:
            if not state.open:
                raise _closed(LocalArtifactDestinationCodeV1.CLOSED)
            try:
                data_ref, control_ref = _parse_config(configuration)
                storage.issue_root_permit(
                    data_ref, authority_ref=permit_authority_ref,
                    key_ref=permit_key_ref, proof_digest=permit_proof_digest,
                )
                storage.issue_root_permit(
                    control_ref, authority_ref=permit_authority_ref,
                    key_ref=permit_key_ref, proof_digest=permit_proof_digest,
                )
                data = storage.resolve(data_ref)
                control = storage.resolve(control_ref)
                authority = filesystem.retain_root_authority(data, control)
                if type(authority) is not LocalRootAuthorityV1:
                    raise _closed(LocalArtifactDestinationCodeV1.INVALID)
                adapter = LocalArtifactDestinationV1(
                    _CONSTRUCTION_TOKEN, filesystem, spool, evidence, authority
                )
                result = ResolvedDestinationAdapterV1(
                    adapter, (("local-root-authority", authority.authority_digest),)
                )
                state.adapters.append(adapter)
                return result
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException:
                if authority is not None:
                    try:
                        filesystem.release_root_authority(authority)
                    except BaseException:
                        pass
                raise _closed(LocalArtifactDestinationCodeV1.INVALID) from None

    registration = DestinationAdapterRegistrationV1(
        _ADAPTER_REF, _CONFIG_SCHEMA, LocalArtifactDestinationV1, factory
    )

    def cleanup_owned() -> bool:
        with state.lock:
            if state.result is not None:
                return state.result
            state.open = False
            failures = []
            for adapter in reversed(state.adapters):
                try:
                    code = adapter._cleanup_owned()
                except BaseException:
                    code = LocalArtifactDestinationCodeV1.IO_FAILED
                if code is not None:
                    failures.append(code)
            state.terminal_failures.update(
                code
                for code in failures
                if code is not LocalArtifactDestinationCodeV1.IN_USE
            )
            if LocalArtifactDestinationCodeV1.IN_USE in failures:
                raise _closed(LocalArtifactDestinationCodeV1.IN_USE)
            state.result = not state.terminal_failures
            return state.result

    return DestinationAdapterInstallationV1(registration, cleanup_owned)


__all__ = [
    "LocalArtifactDestinationCodeV1",
    "LocalArtifactDestinationErrorV1",
    "LocalArtifactDestinationV1",
    "build_local_artifact_destination_registration_v1",
]
