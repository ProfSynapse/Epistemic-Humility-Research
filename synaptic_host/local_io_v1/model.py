"""Immutable host-owned contracts for retained local filesystem access."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class LocalIOCodeV1(str, Enum):
    CONFIG_INVALID = "LOCAL_IO_CONFIG_INVALID"
    CONFIG_IO_FAILED = "LOCAL_IO_CONFIG_IO_FAILED"
    ROOT_UNKNOWN = "LOCAL_IO_ROOT_UNKNOWN"
    ROOT_UNAUTHORIZED = "LOCAL_IO_ROOT_UNAUTHORIZED"
    ROOT_INVALID = "LOCAL_IO_ROOT_INVALID"
    PATH_INVALID = "LOCAL_IO_PATH_INVALID"
    PATH_COLLISION = "LOCAL_IO_PATH_COLLISION"
    SOURCE_INVALID = "LOCAL_IO_SOURCE_INVALID"
    SOURCE_CHANGED = "LOCAL_IO_SOURCE_CHANGED"
    DESTINATION_INVALID = "LOCAL_IO_DESTINATION_INVALID"
    DESTINATION_EXISTS = "LOCAL_IO_DESTINATION_EXISTS"
    STREAM_INVALID = "LOCAL_IO_STREAM_INVALID"
    LIMIT_EXCEEDED = "LOCAL_IO_LIMIT_EXCEEDED"
    AUTHORITY_INVALID = "LOCAL_IO_AUTHORITY_INVALID"
    JOURNAL_INVALID = "LOCAL_IO_JOURNAL_INVALID"
    IO_FAILED = "LOCAL_IO_IO_FAILED"
    CAPABILITY_UNAVAILABLE = "LOCAL_IO_CAPABILITY_UNAVAILABLE"
    ROOT_CHANGED = "LOCAL_IO_ROOT_CHANGED"
    ACCESS_MISMATCH = "LOCAL_IO_ACCESS_MISMATCH"
    PATH_CHANGED = "LOCAL_IO_PATH_CHANGED"
    HARDLINK_UNSAFE = "LOCAL_IO_HARDLINK_UNSAFE"
    JOURNAL_CONFLICT = "LOCAL_IO_JOURNAL_CONFLICT"
    RECOVERY_REQUIRED = "LOCAL_IO_RECOVERY_REQUIRED"


class LocalIOErrorV1(RuntimeError):
    """Closed error: only the stable code is observable."""

    def __init__(self, code: LocalIOCodeV1) -> None:
        self.code = code
        super().__init__(code.value)


_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}")
_HANDLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {
    f"{prefix}{index}" for prefix in ("COM", "LPT") for index in range(1, 10)
}
_MAX_PATH_BYTES = 4096
_MAX_COMPONENT_BYTES = 240
_MAX_COMPONENTS = 128


def _fail(code: LocalIOCodeV1) -> None:
    raise LocalIOErrorV1(code)


def checked_ref(value: object, code: LocalIOCodeV1 = LocalIOCodeV1.CONFIG_INVALID) -> str:
    if type(value) is not str or _REF.fullmatch(value) is None:
        _fail(code)
    return value


def checked_handle(value: object) -> str:
    if type(value) is not str or _HANDLE.fullmatch(value) is None:
        _fail(LocalIOCodeV1.IO_FAILED)
    return value


def checked_sha256(value: object, code: LocalIOCodeV1 = LocalIOCodeV1.STREAM_INVALID) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        _fail(code)
    return value


def checked_size(value: object, code: LocalIOCodeV1 = LocalIOCodeV1.STREAM_INVALID) -> int:
    if type(value) is not int or value < 0:
        _fail(code)
    return value


def canonical_relative_components_v1(value: object) -> tuple[str, ...]:
    """Apply one portable component policy to config and effectful requests."""
    if type(value) is not str or not value:
        _fail(LocalIOCodeV1.PATH_INVALID)
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        _fail(LocalIOCodeV1.PATH_INVALID)
    if (
        len(encoded) > _MAX_PATH_BYTES
        or value != value.strip()
        or value.startswith("/")
        or "\\" in value
        or "\x00" in value
        or any(character.isspace() or unicodedata.category(character) in {"Cc", "Cf"} for character in value)
    ):
        _fail(LocalIOCodeV1.PATH_INVALID)
    parts = tuple(value.split("/"))
    if not parts or len(parts) > _MAX_COMPONENTS:
        _fail(LocalIOCodeV1.PATH_INVALID)
    for part in parts:
        base = part.split(".", 1)[0].upper()
        if (
            not part
            or len(part.encode("utf-8")) > _MAX_COMPONENT_BYTES
            or part in (".", "..")
            or unicodedata.normalize("NFC", part) != part
            or part.endswith((".", " "))
            or ":" in part
            or base in _RESERVED
        ):
            _fail(LocalIOCodeV1.PATH_INVALID)
    return parts


def canonical_posix_root_component_v1(value: object) -> str:
    """Validate one authorized POSIX root component without artifact-name policy."""
    if type(value) is not str or not value or value in {".", ".."} or "/" in value or "\x00" in value:
        _fail(LocalIOCodeV1.ROOT_INVALID)
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        _fail(LocalIOCodeV1.ROOT_INVALID)
    if (
        len(encoded) > 255
        or unicodedata.normalize("NFC", value) != value
        or any(unicodedata.category(character) in {"Cc", "Cf"} for character in value)
    ):
        _fail(LocalIOCodeV1.ROOT_INVALID)
    return value


def canonical_posix_root_components_v1(value: object) -> tuple[str, ...]:
    if type(value) is not str or not value or value.startswith("/") or "\\" in value:
        _fail(LocalIOCodeV1.ROOT_INVALID)
    try:
        if len(value.encode("utf-8")) > 4096:
            _fail(LocalIOCodeV1.ROOT_INVALID)
    except UnicodeError:
        _fail(LocalIOCodeV1.ROOT_INVALID)
    parts = tuple(value.split("/"))
    if len(parts) > 128:
        _fail(LocalIOCodeV1.ROOT_INVALID)
    return tuple(canonical_posix_root_component_v1(part) for part in parts)


def canonical_bytes_v1(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        raise LocalIOErrorV1(LocalIOCodeV1.JOURNAL_INVALID) from None


def digest_v1(value: object) -> str:
    return hashlib.sha256(canonical_bytes_v1(value)).hexdigest()


class RootAccessV1(str, Enum):
    READ_ONLY = "read_only"
    CREATE_ONLY = "create_only"
    READ_CREATE = "read_create"

    @property
    def readable(self) -> bool:
        return self in (RootAccessV1.READ_ONLY, RootAccessV1.READ_CREATE)

    @property
    def creatable(self) -> bool:
        return self in (RootAccessV1.CREATE_ONLY, RootAccessV1.READ_CREATE)


class CapabilityStatusV1(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class LocalFilesystemCapabilityV1:
    platform_family: str
    status: CapabilityStatusV1
    features: tuple[str, ...]
    capability_digest: str

    def __post_init__(self) -> None:
        if type(self.platform_family) is not str or self.platform_family not in {"posix", "windows", "other"}:
            _fail(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
        if type(self.status) is not CapabilityStatusV1 or type(self.features) is not tuple:
            _fail(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
        if tuple(sorted(set(self.features))) != self.features or any(type(item) is not str for item in self.features):
            _fail(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
        checked_sha256(self.capability_digest, LocalIOCodeV1.CAPABILITY_UNAVAILABLE)
        if self.capability_digest != digest_v1(self.canonical_without_digest()):
            _fail(LocalIOCodeV1.CAPABILITY_UNAVAILABLE)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "features": list(self.features),
            "platform_family": self.platform_family,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class LocalRootPermitV1:
    permit_ref: str
    root_ref: str
    absolute_root: Path
    access: RootAccessV1
    authority_ref: str
    key_ref: str
    permit_digest: str
    proof_digest: str

    def __post_init__(self) -> None:
        for value in (self.permit_ref, self.root_ref, self.authority_ref, self.key_ref):
            checked_ref(value, LocalIOCodeV1.ROOT_UNAUTHORIZED)
        if not isinstance(self.absolute_root, Path) or not self.absolute_root.is_absolute():
            _fail(LocalIOCodeV1.ROOT_UNAUTHORIZED)
        if type(self.access) is not RootAccessV1:
            _fail(LocalIOCodeV1.ROOT_UNAUTHORIZED)
        checked_sha256(self.permit_digest, LocalIOCodeV1.ROOT_UNAUTHORIZED)
        checked_sha256(self.proof_digest, LocalIOCodeV1.ROOT_UNAUTHORIZED)
        if self.permit_digest != digest_v1(self.canonical_without_proof()):
            _fail(LocalIOCodeV1.ROOT_UNAUTHORIZED)

    def canonical_without_proof(self) -> dict[str, object]:
        return {
            "access": self.access.value,
            "absolute_root": str(self.absolute_root),
            "authority_ref": self.authority_ref,
            "key_ref": self.key_ref,
            "permit_ref": self.permit_ref,
            "root_ref": self.root_ref,
        }


class RootPermitAuthenticatorV1(Protocol):
    def authenticate(self, permit: LocalRootPermitV1) -> LocalRootPermitV1 | None: ...


@dataclass(frozen=True, slots=True)
class LocalRootBindingV1:
    root_ref: str
    location_ref: str
    absolute_root: Path
    access: RootAccessV1
    authorization_ref: str
    root_permit: LocalRootPermitV1

    def __post_init__(self) -> None:
        checked_ref(self.root_ref)
        if type(self.location_ref) is not str or not self.location_ref:
            _fail(LocalIOCodeV1.CONFIG_INVALID)
        if not isinstance(self.absolute_root, Path) or not self.absolute_root.is_absolute():
            _fail(LocalIOCodeV1.CONFIG_INVALID)
        if type(self.access) is not RootAccessV1:
            _fail(LocalIOCodeV1.CONFIG_INVALID)
        checked_ref(self.authorization_ref)
        if self.location_ref.startswith("project://"):
            canonical_posix_root_components_v1(self.location_ref[len("project://") :])
        if type(self.root_permit) is not LocalRootPermitV1:
            _fail(LocalIOCodeV1.ROOT_UNAUTHORIZED)
        if (
            self.authorization_ref != self.root_permit.permit_ref
            or self.root_ref != self.root_permit.root_ref
            or self.absolute_root != self.root_permit.absolute_root
            or self.access is not self.root_permit.access
        ):
            _fail(LocalIOCodeV1.ROOT_UNAUTHORIZED)

    @property
    def binding_digest(self) -> str:
        return digest_v1({
            "access": self.access.value,
            "authorization_ref": self.authorization_ref,
            "location_ref": self.location_ref,
            "permit_authority_ref": self.root_permit.authority_ref,
            "permit_key_ref": self.root_permit.key_ref,
            "root_ref": self.root_ref,
        })


@dataclass(frozen=True, slots=True)
class LocalFileIdentityV1:
    device: int
    inode: int
    mode: int
    nlink: int
    changed_ns: int
    modified_ns: int
    size: int

    def __post_init__(self) -> None:
        for value in (self.device, self.inode, self.mode, self.nlink, self.changed_ns, self.modified_ns, self.size):
            if type(value) is not int or value < 0:
                _fail(LocalIOCodeV1.IO_FAILED)
        if self.nlink < 1:
            _fail(LocalIOCodeV1.IO_FAILED)

    def canonical(self) -> dict[str, int]:
        return {
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "changed_ns": self.changed_ns,
            "modified_ns": self.modified_ns,
            "nlink": self.nlink,
            "size": self.size,
        }


@dataclass(frozen=True, slots=True)
class RetainedDirectoryV1:
    handle_ref: str
    identity: LocalFileIdentityV1

    def __post_init__(self) -> None:
        checked_handle(self.handle_ref)
        if type(self.identity) is not LocalFileIdentityV1:
            _fail(LocalIOCodeV1.IO_FAILED)


@dataclass(frozen=True, slots=True)
class LocalRootAuthorityV1:
    authority_ref: str
    data_binding: LocalRootBindingV1
    control_binding: LocalRootBindingV1
    data_directory: RetainedDirectoryV1
    control_directory: RetainedDirectoryV1
    authority_digest: str

    def __post_init__(self) -> None:
        checked_ref(self.authority_ref, LocalIOCodeV1.AUTHORITY_INVALID)
        if type(self.data_binding) is not LocalRootBindingV1 or type(self.control_binding) is not LocalRootBindingV1:
            _fail(LocalIOCodeV1.AUTHORITY_INVALID)
        if type(self.data_directory) is not RetainedDirectoryV1 or type(self.control_directory) is not RetainedDirectoryV1:
            _fail(LocalIOCodeV1.AUTHORITY_INVALID)
        checked_sha256(self.authority_digest, LocalIOCodeV1.AUTHORITY_INVALID)
        if self.authority_digest != digest_v1(self.canonical_without_digest()):
            _fail(LocalIOCodeV1.AUTHORITY_INVALID)

    def canonical_without_digest(self) -> dict[str, Any]:
        return {
            "control_binding_digest": self.control_binding.binding_digest,
            "control_identity": self.control_directory.identity.canonical(),
            "data_binding_digest": self.data_binding.binding_digest,
            "data_identity": self.data_directory.identity.canonical(),
        }


@dataclass(frozen=True, slots=True)
class LocalSourceBindingV1:
    authority_digest: str
    relative_path: str
    role: str
    size: int
    sha256: str
    identity: LocalFileIdentityV1

    def __post_init__(self) -> None:
        checked_sha256(self.authority_digest, LocalIOCodeV1.SOURCE_INVALID)
        checked_ref(self.role, LocalIOCodeV1.SOURCE_INVALID)
        checked_size(self.size, LocalIOCodeV1.SOURCE_INVALID)
        checked_sha256(self.sha256, LocalIOCodeV1.SOURCE_INVALID)
        if (
            type(self.relative_path) is not str
            or "/".join(canonical_relative_components_v1(self.relative_path)) != self.relative_path
        ):
            _fail(LocalIOCodeV1.SOURCE_INVALID)
        if (
            type(self.identity) is not LocalFileIdentityV1
            or not stat_is_regular_single_v1(self.identity)
            or self.identity.size != self.size
        ):
            _fail(LocalIOCodeV1.SOURCE_INVALID)


@dataclass(frozen=True, slots=True)
class LocalDestinationBindingV1:
    authority_digest: str
    relative_path: str
    role: str
    expected_size: int
    expected_sha256: str

    def __post_init__(self) -> None:
        checked_sha256(self.authority_digest, LocalIOCodeV1.DESTINATION_INVALID)
        checked_ref(self.role, LocalIOCodeV1.DESTINATION_INVALID)
        checked_size(self.expected_size, LocalIOCodeV1.DESTINATION_INVALID)
        checked_sha256(self.expected_sha256, LocalIOCodeV1.DESTINATION_INVALID)
        if (
            type(self.relative_path) is not str
            or "/".join(canonical_relative_components_v1(self.relative_path)) != self.relative_path
        ):
            _fail(LocalIOCodeV1.DESTINATION_INVALID)

    @property
    def destination_digest(self) -> str:
        return digest_v1({
            "authority_digest": self.authority_digest,
            "expected_sha256": self.expected_sha256,
            "expected_size": self.expected_size,
            "relative_path": self.relative_path,
            "role": self.role,
        })


@dataclass(frozen=True, slots=True)
class LocalCreateAuthorityV1:
    authority_ref: str
    root_authority_digest: str
    destination_digest: str
    mutation_id: str

    def __post_init__(self) -> None:
        checked_ref(self.authority_ref, LocalIOCodeV1.AUTHORITY_INVALID)
        checked_sha256(self.root_authority_digest, LocalIOCodeV1.AUTHORITY_INVALID)
        checked_sha256(self.destination_digest, LocalIOCodeV1.AUTHORITY_INVALID)
        checked_sha256(self.mutation_id, LocalIOCodeV1.AUTHORITY_INVALID)


@dataclass(frozen=True, slots=True)
class LocalArtifactBindingV1:
    destination_digest: str
    relative_path: str
    role: str
    size: int
    sha256: str
    identity: LocalFileIdentityV1

    def __post_init__(self) -> None:
        checked_sha256(self.destination_digest, LocalIOCodeV1.DESTINATION_INVALID)
        checked_ref(self.role, LocalIOCodeV1.DESTINATION_INVALID)
        checked_size(self.size, LocalIOCodeV1.DESTINATION_INVALID)
        checked_sha256(self.sha256, LocalIOCodeV1.DESTINATION_INVALID)
        if (
            type(self.relative_path) is not str
            or "/".join(canonical_relative_components_v1(self.relative_path)) != self.relative_path
            or type(self.identity) is not LocalFileIdentityV1
            or self.identity.size != self.size
            or not stat_is_regular_single_v1(self.identity)
        ):
            _fail(LocalIOCodeV1.DESTINATION_INVALID)


class CreatePhaseV1(str, Enum):
    CLAIMED = "claimed"
    FILE_DURABLE = "file_durable"
    LINKED = "linked"
    COMMITTED = "committed"


class JournalPublishStatusV1(str, Enum):
    PUBLISHED = "published"
    EXISTS_IDENTICAL = "exists_identical"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class JournalPublishResultV1:
    status: JournalPublishStatusV1
    mutation_id: str
    record_digest: str
    published_record: CreateJournalRecordV1

    def __post_init__(self) -> None:
        if type(self.status) is not JournalPublishStatusV1:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.mutation_id, LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.record_digest, LocalIOCodeV1.JOURNAL_INVALID)
        if (
            type(self.published_record) is not CreateJournalRecordV1
            or self.published_record.mutation_id != self.mutation_id
            or self.published_record.record_digest != self.record_digest
        ):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)


class JournalSnapshotStatusV1(str, Enum):
    ABSENT = "absent"
    FOUND = "found"
    INDETERMINATE = "indeterminate"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class JournalSnapshotV1:
    status: JournalSnapshotStatusV1
    mutation_id: str
    records: tuple[CreateJournalRecordV1, ...]
    snapshot_digest: str

    def __post_init__(self) -> None:
        if type(self.status) is not JournalSnapshotStatusV1:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.mutation_id, LocalIOCodeV1.JOURNAL_INVALID)
        if type(self.records) is not tuple or len(self.records) > 4:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        if (
            (self.status is JournalSnapshotStatusV1.ABSENT and self.records)
            or (self.status is JournalSnapshotStatusV1.FOUND and not self.records)
            or (self.status in {JournalSnapshotStatusV1.CONFLICT, JournalSnapshotStatusV1.INDETERMINATE} and self.records)
        ):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.snapshot_digest, LocalIOCodeV1.JOURNAL_INVALID)
        expected = digest_v1({
            "mutation_id": self.mutation_id,
            "record_digests": [record.record_digest for record in self.records],
            "status": self.status.value,
        })
        if self.snapshot_digest != expected:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)


class RecoveryStatusV1(str, Enum):
    ACTIVE = "active"
    FOUND = "found"
    DEFINITELY_ABSENT = "definitely_absent"
    INDETERMINATE = "indeterminate"
    CONFLICT = "conflict"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"


@dataclass(frozen=True, slots=True)
class CreateJournalRecordV1:
    mutation_id: str
    destination_digest: str
    phase: CreatePhaseV1
    sequence: int
    previous_digest: str | None
    staging_name: str
    file_identity: LocalFileIdentityV1 | None
    record_digest: str

    def __post_init__(self) -> None:
        checked_sha256(self.mutation_id, LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.destination_digest, LocalIOCodeV1.JOURNAL_INVALID)
        if type(self.phase) is not CreatePhaseV1 or type(self.sequence) is not int or not 0 <= self.sequence <= 3:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        if self.sequence != list(CreatePhaseV1).index(self.phase):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        if self.sequence == 0:
            if self.previous_digest is not None or self.file_identity is not None:
                _fail(LocalIOCodeV1.JOURNAL_INVALID)
        else:
            checked_sha256(self.previous_digest, LocalIOCodeV1.JOURNAL_INVALID)
        if self.phase is not CreatePhaseV1.CLAIMED and type(self.file_identity) is not LocalFileIdentityV1:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        if (
            type(self.staging_name) is not str
            or self.staging_name != ".synaptic-" + self.mutation_id[:32]
        ):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        if self.file_identity is not None:
            if self.phase in {CreatePhaseV1.FILE_DURABLE, CreatePhaseV1.COMMITTED}:
                if not stat_is_regular_single_v1(self.file_identity):
                    _fail(LocalIOCodeV1.JOURNAL_INVALID)
            elif self.phase is CreatePhaseV1.LINKED:
                if not ((self.file_identity.mode & 0o170000) == 0o100000 and self.file_identity.nlink == 2):
                    _fail(LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.record_digest, LocalIOCodeV1.JOURNAL_INVALID)
        if self.record_digest != digest_v1(self.canonical_without_digest()):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "destination_digest": self.destination_digest,
            "file_identity": None if self.file_identity is None else self.file_identity.canonical(),
            "mutation_id": self.mutation_id,
            "phase": self.phase.value,
            "previous_digest": self.previous_digest,
            "sequence": self.sequence,
            "staging_name": self.staging_name,
        }


@dataclass(frozen=True, slots=True)
class RecoveryResultV1:
    status: RecoveryStatusV1
    mutation_id: str
    artifact: LocalArtifactBindingV1 | None = None

    def __post_init__(self) -> None:
        if type(self.status) is not RecoveryStatusV1:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        checked_sha256(self.mutation_id, LocalIOCodeV1.JOURNAL_INVALID)
        if (self.status is RecoveryStatusV1.FOUND) != (type(self.artifact) is LocalArtifactBindingV1):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)


def journal_record_bytes_v1(record: CreateJournalRecordV1) -> bytes:
    if type(record) is not CreateJournalRecordV1:
        _fail(LocalIOCodeV1.JOURNAL_INVALID)
    return canonical_bytes_v1({**record.canonical_without_digest(), "record_digest": record.record_digest})


def parse_journal_record_v1(raw: bytes) -> CreateJournalRecordV1:
    if type(raw) is not bytes or not raw or len(raw) > 16_384:
        _fail(LocalIOCodeV1.JOURNAL_INVALID)

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _fail(LocalIOCodeV1.JOURNAL_INVALID)
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=unique)
    except LocalIOErrorV1:
        raise
    except (UnicodeError, TypeError, ValueError):
        raise LocalIOErrorV1(LocalIOCodeV1.JOURNAL_INVALID) from None
    fields = {
        "destination_digest", "file_identity", "mutation_id", "phase",
        "previous_digest", "record_digest", "sequence", "staging_name",
    }
    if type(value) is not dict or set(value) != fields or canonical_bytes_v1(value) != raw:
        _fail(LocalIOCodeV1.JOURNAL_INVALID)
    identity_value = value["file_identity"]
    identity = None
    if identity_value is not None:
        identity_fields = {"changed_ns", "device", "inode", "mode", "modified_ns", "nlink", "size"}
        if type(identity_value) is not dict or set(identity_value) != identity_fields:
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
        try:
            identity = LocalFileIdentityV1(
                device=identity_value["device"], inode=identity_value["inode"],
                mode=identity_value["mode"], nlink=identity_value["nlink"],
                changed_ns=identity_value["changed_ns"], modified_ns=identity_value["modified_ns"],
                size=identity_value["size"],
            )
            phase = CreatePhaseV1(value["phase"])
        except (TypeError, ValueError):
            raise LocalIOErrorV1(LocalIOCodeV1.JOURNAL_INVALID) from None
    else:
        try:
            phase = CreatePhaseV1(value["phase"])
        except (TypeError, ValueError):
            raise LocalIOErrorV1(LocalIOCodeV1.JOURNAL_INVALID) from None
    return CreateJournalRecordV1(
        mutation_id=value["mutation_id"], destination_digest=value["destination_digest"],
        phase=phase, sequence=value["sequence"], previous_digest=value["previous_digest"],
        staging_name=value["staging_name"], file_identity=identity,
        record_digest=value["record_digest"],
    )


def validate_recovery_result_v1(
    result: RecoveryResultV1,
    *,
    mutation_id: str,
    destination: LocalDestinationBindingV1,
) -> RecoveryResultV1:
    if type(result) is not RecoveryResultV1 or result.mutation_id != mutation_id:
        _fail(LocalIOCodeV1.JOURNAL_INVALID)
    if result.status is RecoveryStatusV1.FOUND:
        artifact = result.artifact
        if (
            type(artifact) is not LocalArtifactBindingV1
            or artifact.destination_digest != destination.destination_digest
            or artifact.relative_path != destination.relative_path
            or artifact.role != destination.role
            or artifact.size != destination.expected_size
            or artifact.sha256 != destination.expected_sha256
            or not stat_is_regular_single_v1(artifact.identity)
        ):
            _fail(LocalIOCodeV1.JOURNAL_INVALID)
    elif result.artifact is not None:
        _fail(LocalIOCodeV1.JOURNAL_INVALID)
    return result


def stat_is_regular_single_v1(identity: LocalFileIdentityV1) -> bool:
    # Avoid importing platform adapters into the model; POSIX file type bits are stable.
    return type(identity) is LocalFileIdentityV1 and (identity.mode & 0o170000) == 0o100000 and identity.nlink == 1
