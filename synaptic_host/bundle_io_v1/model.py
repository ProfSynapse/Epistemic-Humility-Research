from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum

from synaptic_host.local_io_v1.model import (
    LocalFileIdentityV1,
    canonical_relative_components_v1,
    stat_is_regular_single_v1,
)


MAX_BUNDLE_MEMBERS = 128
MAX_BUNDLE_MEMBER_BYTES = 1 << 30
MAX_BUNDLE_TOTAL_BYTES = 4 << 30
MAX_BUNDLE_MANIFEST_BYTES = 1 << 20
MAX_BUNDLE_CHUNK_BYTES = 1 << 20
_REF = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}")
_SHA256 = re.compile(r"[0-9a-f]{64}")


class BundleIOCodeV1(str, Enum):
    COMMAND_INVALID = "BUNDLE_IO_COMMAND_INVALID"
    SOURCE_INVALID = "BUNDLE_IO_SOURCE_INVALID"
    ACCESS_INVALID = "BUNDLE_IO_ACCESS_INVALID"
    STREAM_INVALID = "BUNDLE_IO_STREAM_INVALID"
    EFFECT_FAILED = "BUNDLE_IO_EFFECT_FAILED"
    INDETERMINATE = "BUNDLE_IO_INDETERMINATE"
    CONFLICT = "BUNDLE_IO_CONFLICT"
    BOUND_EXCEEDED = "BUNDLE_IO_BOUND_EXCEEDED"


class BundleIOErrorV1(RuntimeError):
    def __init__(self, code: BundleIOCodeV1) -> None:
        self.code = code
        super().__init__(code.value)


class BundleLookupStatusV1(str, Enum):
    FOUND = "found"
    DEFINITELY_ABSENT = "definitely_absent"
    INDETERMINATE = "indeterminate"
    CONFLICT = "conflict"


def _fail(code: BundleIOCodeV1) -> None:
    raise BundleIOErrorV1(code)


def checked_ref_v1(value: object, code: BundleIOCodeV1) -> str:
    if type(value) is not str or _REF.fullmatch(value) is None:
        _fail(code)
    return value


def checked_sha_v1(value: object, code: BundleIOCodeV1) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        _fail(code)
    return value


def canonical_bytes_v1(value: object) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError):
        raise BundleIOErrorV1(BundleIOCodeV1.COMMAND_INVALID) from None


def digest_v1(value: object) -> str:
    return hashlib.sha256(canonical_bytes_v1(value)).hexdigest()


def identity_canonical_v1(identity: LocalFileIdentityV1) -> dict[str, int]:
    if type(identity) is not LocalFileIdentityV1:
        _fail(BundleIOCodeV1.CONFLICT)
    return identity.canonical()


def hardlink_pair_identity_v1(identity: LocalFileIdentityV1) -> bool:
    return (
        type(identity) is LocalFileIdentityV1
        and (identity.mode & 0o170000) == 0o100000
        and identity.nlink == 2
        and 0 <= identity.size <= MAX_BUNDLE_MANIFEST_BYTES
    )


def bundle_companion_digest_v1(
    command_digest: str, destination_ref: str, root_authority_digest: str
) -> str:
    checked_sha_v1(command_digest, BundleIOCodeV1.COMMAND_INVALID)
    checked_ref_v1(destination_ref, BundleIOCodeV1.COMMAND_INVALID)
    checked_sha_v1(root_authority_digest, BundleIOCodeV1.ACCESS_INVALID)
    return digest_v1({
        "command_digest": command_digest,
        "destination_ref": destination_ref,
        "root_authority_digest": root_authority_digest,
        "schema_version": "synaptic-host-bundle-companion/v1",
    })


@dataclass(frozen=True, slots=True)
class BundleMemberCommandV1:
    logical_name: str
    source_ref: str
    size: int
    sha256: str

    def __post_init__(self) -> None:
        try:
            components = canonical_relative_components_v1(self.logical_name)
        except BaseException:
            _fail(BundleIOCodeV1.COMMAND_INVALID)
        if "/".join(components) != self.logical_name:
            _fail(BundleIOCodeV1.COMMAND_INVALID)
        checked_ref_v1(self.source_ref, BundleIOCodeV1.COMMAND_INVALID)
        if type(self.size) is not int or not 0 <= self.size <= MAX_BUNDLE_MEMBER_BYTES:
            _fail(BundleIOCodeV1.BOUND_EXCEEDED)
        checked_sha_v1(self.sha256, BundleIOCodeV1.COMMAND_INVALID)

    def canonical(self) -> dict[str, object]:
        return {
            "logical_name": self.logical_name,
            "sha256": self.sha256,
            "size": self.size,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True, slots=True)
class BundleSealCommandV1:
    profile_ref: str
    purpose_ref: str
    destination_ref: str
    members: tuple[BundleMemberCommandV1, ...]
    command_digest: str

    def __post_init__(self) -> None:
        checked_ref_v1(self.profile_ref, BundleIOCodeV1.COMMAND_INVALID)
        checked_ref_v1(self.purpose_ref, BundleIOCodeV1.COMMAND_INVALID)
        checked_ref_v1(self.destination_ref, BundleIOCodeV1.COMMAND_INVALID)
        if (
            type(self.members) is not tuple
            or not 1 <= len(self.members) <= MAX_BUNDLE_MEMBERS
            or any(type(member) is not BundleMemberCommandV1 for member in self.members)
        ):
            _fail(BundleIOCodeV1.COMMAND_INVALID)
        names = tuple(member.logical_name for member in self.members)
        if names != tuple(sorted(names)) or len(set(names)) != len(names):
            _fail(BundleIOCodeV1.COMMAND_INVALID)
        if sum(member.size for member in self.members) > MAX_BUNDLE_TOTAL_BYTES:
            _fail(BundleIOCodeV1.BOUND_EXCEEDED)
        checked_sha_v1(self.command_digest, BundleIOCodeV1.COMMAND_INVALID)
        if self.command_digest != digest_v1(self.canonical_without_digest()):
            _fail(BundleIOCodeV1.COMMAND_INVALID)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "destination_ref": self.destination_ref,
            "members": [member.canonical() for member in self.members],
            "profile_ref": self.profile_ref,
            "purpose_ref": self.purpose_ref,
            "schema_version": "synaptic-host-bundle-seal-command/v1",
        }

    @classmethod
    def build(cls, profile_ref, purpose_ref, destination_ref, members):
        body = {
            "destination_ref": destination_ref,
            "members": [member.canonical() for member in members],
            "profile_ref": profile_ref,
            "purpose_ref": purpose_ref,
            "schema_version": "synaptic-host-bundle-seal-command/v1",
        }
        return cls(profile_ref, purpose_ref, destination_ref, members, digest_v1(body))


@dataclass(frozen=True, slots=True)
class BundleMemberEvidenceV1:
    logical_name: str
    physical_name: str
    size: int
    sha256: str
    identity: LocalFileIdentityV1

    def __post_init__(self) -> None:
        BundleMemberCommandV1(self.logical_name, "evidence", self.size, self.sha256)
        if type(self.physical_name) is not str or re.fullmatch(
            r"member-[0-9]{4}", self.physical_name
        ) is None:
            _fail(BundleIOCodeV1.CONFLICT)
        if (
            type(self.identity) is not LocalFileIdentityV1
            or not stat_is_regular_single_v1(self.identity)
            or self.identity.size != self.size
        ):
            _fail(BundleIOCodeV1.CONFLICT)

    def canonical(self) -> dict[str, object]:
        return {
            "identity": identity_canonical_v1(self.identity),
            "logical_name": self.logical_name,
            "physical_name": self.physical_name,
            "sha256": self.sha256,
            "size": self.size,
        }


@dataclass(frozen=True, slots=True)
class BundleBindingV1:
    command_digest: str
    destination_ref: str
    root_authority_digest: str
    private_name: str
    marker_name: str
    companion_name: str
    manifest_digest: str
    inventory_digest: str
    members: tuple[BundleMemberEvidenceV1, ...]
    manifest_identity: LocalFileIdentityV1
    marker_identity: LocalFileIdentityV1
    binding_digest: str

    def __post_init__(self) -> None:
        checked_sha_v1(self.command_digest, BundleIOCodeV1.CONFLICT)
        checked_ref_v1(self.destination_ref, BundleIOCodeV1.CONFLICT)
        checked_sha_v1(self.root_authority_digest, BundleIOCodeV1.CONFLICT)
        checked_sha_v1(self.manifest_digest, BundleIOCodeV1.CONFLICT)
        checked_sha_v1(self.inventory_digest, BundleIOCodeV1.CONFLICT)
        suffix = self.command_digest[:32]
        if self.private_name != ".synaptic-bundle-" + suffix:
            _fail(BundleIOCodeV1.CONFLICT)
        if self.marker_name != "COMMIT-" + suffix:
            _fail(BundleIOCodeV1.CONFLICT)
        companion_digest = bundle_companion_digest_v1(
            self.command_digest, self.destination_ref, self.root_authority_digest
        )
        if self.companion_name != ".synaptic-commit-companion-" + companion_digest:
            _fail(BundleIOCodeV1.CONFLICT)
        if type(self.members) is not tuple or not self.members:
            _fail(BundleIOCodeV1.CONFLICT)
        if not stat_is_regular_single_v1(self.manifest_identity):
            _fail(BundleIOCodeV1.CONFLICT)
        if not hardlink_pair_identity_v1(self.marker_identity):
            _fail(BundleIOCodeV1.CONFLICT)
        checked_sha_v1(self.binding_digest, BundleIOCodeV1.CONFLICT)
        if self.inventory_digest != digest_v1([member.canonical() for member in self.members]):
            _fail(BundleIOCodeV1.CONFLICT)
        if self.binding_digest != digest_v1(self.canonical_without_digest()):
            _fail(BundleIOCodeV1.CONFLICT)

    def canonical_without_digest(self) -> dict[str, object]:
        return {
            "command_digest": self.command_digest,
            "companion_name": self.companion_name,
            "destination_ref": self.destination_ref,
            "inventory_digest": self.inventory_digest,
            "manifest_digest": self.manifest_digest,
            "manifest_identity": identity_canonical_v1(self.manifest_identity),
            "marker_identity": identity_canonical_v1(self.marker_identity),
            "marker_name": self.marker_name,
            "members": [member.canonical() for member in self.members],
            "private_name": self.private_name,
            "root_authority_digest": self.root_authority_digest,
            "schema_version": "synaptic-host-bundle-binding/v1",
        }


@dataclass(frozen=True, slots=True)
class BundleLookupResultV1:
    status: BundleLookupStatusV1
    command_digest: str
    binding: BundleBindingV1 | None = None

    def __post_init__(self) -> None:
        if type(self.status) is not BundleLookupStatusV1:
            _fail(BundleIOCodeV1.CONFLICT)
        checked_sha_v1(self.command_digest, BundleIOCodeV1.CONFLICT)
        if (self.status is BundleLookupStatusV1.FOUND) != (
            type(self.binding) is BundleBindingV1
        ):
            _fail(BundleIOCodeV1.CONFLICT)
        if self.binding is not None and self.binding.command_digest != self.command_digest:
            _fail(BundleIOCodeV1.CONFLICT)
