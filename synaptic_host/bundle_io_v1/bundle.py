from __future__ import annotations

import hashlib
import json
from dataclasses import replace

from synaptic_host.local_io_v1.filesystem import RetainedRootBorrowPortV1
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    LocalFileIdentityV1,
    LocalIOCodeV1,
    LocalIOErrorV1,
    stat_is_regular_single_v1,
)

from .model import (
    MAX_BUNDLE_CHUNK_BYTES,
    MAX_BUNDLE_MANIFEST_BYTES,
    BundleBindingV1,
    BundleIOCodeV1,
    BundleIOErrorV1,
    BundleLookupResultV1,
    BundleLookupStatusV1,
    BundleMemberCommandV1,
    BundleMemberEvidenceV1,
    BundleSealCommandV1,
    bundle_companion_digest_v1,
    canonical_bytes_v1,
    digest_v1,
    hardlink_pair_identity_v1,
)
from .ports import BundleBorrowAccessV1, BundleSourceRegistryPortV1, BundleSourceV1


CREATE = BorrowPurposeV1.BUNDLE_DESTINATION_CREATE
VERIFY = BorrowPurposeV1.BUNDLE_MOUNT_VERIFY
SOURCE = BorrowPurposeV1.BUNDLE_SOURCE_READ


def _error(code: BundleIOCodeV1) -> BundleIOErrorV1:
    return BundleIOErrorV1(code)


def _result(status, command, binding=None):
    return BundleLookupResultV1(status, command.command_digest, binding)


def _copy_identity(value: LocalFileIdentityV1) -> LocalFileIdentityV1:
    if type(value) is not LocalFileIdentityV1:
        raise _error(BundleIOCodeV1.CONFLICT)
    try:
        return replace(value)
    except BaseException:
        raise _error(BundleIOCodeV1.CONFLICT) from None


def _identity(value: object) -> LocalFileIdentityV1:
    fields = {"changed_ns", "device", "inode", "mode", "modified_ns", "nlink", "size"}
    if type(value) is not dict or set(value) != fields:
        raise _error(BundleIOCodeV1.CONFLICT)
    try:
        return LocalFileIdentityV1(**value)
    except BaseException:
        raise _error(BundleIOCodeV1.CONFLICT) from None


def _parse_canonical(raw: bytes, maximum: int) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > maximum:
        raise _error(BundleIOCodeV1.CONFLICT)

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise _error(BundleIOCodeV1.CONFLICT)
            result[key] = value
        return result

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=unique)
    except BundleIOErrorV1:
        raise
    except BaseException:
        raise _error(BundleIOCodeV1.CONFLICT) from None
    if type(value) is not dict or canonical_bytes_v1(value) != raw:
        raise _error(BundleIOCodeV1.CONFLICT)
    return value


def _runtime_pair_error(error: LocalIOErrorV1) -> BundleIOErrorV1:
    if error.code in {
        LocalIOCodeV1.HARDLINK_UNSAFE,
        LocalIOCodeV1.PATH_CHANGED,
        LocalIOCodeV1.PATH_INVALID,
    }:
        return _error(BundleIOCodeV1.CONFLICT)
    return _error(BundleIOCodeV1.INDETERMINATE)


class ImmutableSourceBundleV1:
    """Host-only immutable source bundle over retained borrow capabilities."""

    def __init__(self, borrow_port: RetainedRootBorrowPortV1,
                 sources: BundleSourceRegistryPortV1) -> None:
        self._port = borrow_port
        self._sources = sources

    @staticmethod
    def _snapshot_command(command) -> BundleSealCommandV1:
        if type(command) is not BundleSealCommandV1:
            raise _error(BundleIOCodeV1.COMMAND_INVALID)
        try:
            members = tuple(replace(member) for member in command.members)
            return BundleSealCommandV1(
                command.profile_ref, command.purpose_ref, command.destination_ref,
                members, command.command_digest,
            )
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise _error(BundleIOCodeV1.COMMAND_INVALID) from None

    @staticmethod
    def _snapshot_access(access) -> BundleBorrowAccessV1:
        if type(access) is not BundleBorrowAccessV1:
            raise _error(BundleIOCodeV1.ACCESS_INVALID)
        try:
            create_borrow = replace(access.create_borrow)
            verify_borrow = replace(access.verify_borrow)
            create_root = replace(
                access.create_root, identity=_copy_identity(access.create_root.identity)
            )
            verify_root = replace(
                access.verify_root, identity=_copy_identity(access.verify_root.identity)
            )
            BundleBorrowAccessV1(
                access.destination_ref, access.root_authority_digest,
                create_borrow, create_root, verify_borrow, verify_root,
                access.access_digest,
            )
            return BundleBorrowAccessV1(
                access.destination_ref, access.root_authority_digest,
                access.create_borrow, access.create_root,
                access.verify_borrow, access.verify_root,
                access.access_digest,
            )
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise _error(BundleIOCodeV1.ACCESS_INVALID) from None

    @classmethod
    def _validate(cls, command, access):
        command = cls._snapshot_command(command)
        access = cls._snapshot_access(access)
        if access.destination_ref != command.destination_ref:
            raise _error(BundleIOCodeV1.ACCESS_INVALID)
        return command, access

    @staticmethod
    def _snapshot_source(source, expected_ref: str) -> BundleSourceV1:
        if type(source) is not BundleSourceV1:
            raise _error(BundleIOCodeV1.SOURCE_INVALID)
        try:
            borrow = replace(source.borrow)
            directory = replace(
                source.directory, identity=_copy_identity(source.directory.identity)
            )
            BundleSourceV1(
                source.source_ref, borrow, directory, source.component,
                source.source_digest,
            )
            snapshot = BundleSourceV1(
                source.source_ref, source.borrow, source.directory,
                source.component, source.source_digest,
            )
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise _error(BundleIOCodeV1.SOURCE_INVALID) from None
        if snapshot.source_ref != expected_ref:
            raise _error(BundleIOCodeV1.SOURCE_INVALID)
        return snapshot

    @staticmethod
    def _snapshot_binding(binding) -> BundleBindingV1:
        if type(binding) is not BundleBindingV1:
            raise _error(BundleIOCodeV1.CONFLICT)
        try:
            members = tuple(
                replace(member, identity=_copy_identity(member.identity))
                for member in binding.members
            )
            return BundleBindingV1(
                binding.command_digest, binding.destination_ref,
                binding.root_authority_digest, binding.private_name,
                binding.marker_name, binding.companion_name,
                binding.manifest_digest, binding.inventory_digest, members,
                _copy_identity(binding.manifest_identity),
                _copy_identity(binding.marker_identity),
                binding.binding_digest,
            )
        except BundleIOErrorV1:
            raise
        except BaseException:
            raise _error(BundleIOCodeV1.CONFLICT) from None

    @staticmethod
    def _names(command, access):
        suffix = command.command_digest[:32]
        companion = bundle_companion_digest_v1(
            command.command_digest, command.destination_ref,
            access.root_authority_digest,
        )
        return (
            ".synaptic-bundle-" + suffix,
            "COMMIT-" + suffix,
            ".synaptic-commit-companion-" + companion,
        )

    def _read_single(self, borrow, directory, component, *, purpose, maximum,
                     expected_identity=None):
        opened = None
        primary = None
        result = None
        try:
            before = self._port.stat_borrowed(
                borrow, directory, component, purpose=purpose
            )
            if (
                type(before) is not LocalFileIdentityV1
                or not stat_is_regular_single_v1(before)
                or before.size > maximum
                or (expected_identity is not None and before != expected_identity)
            ):
                raise _error(BundleIOCodeV1.CONFLICT)
            opened = self._port.open_borrowed_read(
                borrow, directory, component, purpose=purpose
            )
            chunks = []
            size = 0
            while True:
                chunk = self._port.read_borrowed(
                    borrow, opened, MAX_BUNDLE_CHUNK_BYTES, purpose=purpose
                )
                if type(chunk) is not bytes or len(chunk) > MAX_BUNDLE_CHUNK_BYTES:
                    raise _error(BundleIOCodeV1.STREAM_INVALID)
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum or size > before.size:
                    raise _error(BundleIOCodeV1.STREAM_INVALID)
                chunks.append(chunk)
            after_handle = self._port.stat_borrowed_file(
                borrow, opened, purpose=purpose
            )
            after_path = self._port.stat_borrowed(
                borrow, directory, component, purpose=purpose
            )
            if size != before.size or before != after_handle or before != after_path:
                raise _error(BundleIOCodeV1.CONFLICT)
            result = (b"".join(chunks), before)
        except BaseException as error:
            primary = error
        if opened is not None:
            try:
                self._port.close_borrowed_file(borrow, opened, purpose=purpose)
            except BaseException:
                raise _error(BundleIOCodeV1.INDETERMINATE) from None
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            if isinstance(primary, LocalIOErrorV1):
                raise _runtime_pair_error(primary)
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    def _hash_single(self, borrow, directory, component, *, purpose, maximum,
                     expected_identity):
        opened = None
        primary = None
        result = None
        try:
            before = self._port.stat_borrowed(
                borrow, directory, component, purpose=purpose
            )
            if (
                type(before) is not LocalFileIdentityV1
                or not stat_is_regular_single_v1(before)
                or before != expected_identity
                or before.size > maximum
            ):
                raise _error(BundleIOCodeV1.CONFLICT)
            opened = self._port.open_borrowed_read(
                borrow, directory, component, purpose=purpose
            )
            digest = hashlib.sha256()
            size = 0
            while True:
                chunk = self._port.read_borrowed(
                    borrow, opened, MAX_BUNDLE_CHUNK_BYTES, purpose=purpose
                )
                if type(chunk) is not bytes or len(chunk) > MAX_BUNDLE_CHUNK_BYTES:
                    raise _error(BundleIOCodeV1.STREAM_INVALID)
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum or size > before.size:
                    raise _error(BundleIOCodeV1.STREAM_INVALID)
                digest.update(chunk)
            after_handle = self._port.stat_borrowed_file(
                borrow, opened, purpose=purpose
            )
            after_path = self._port.stat_borrowed(
                borrow, directory, component, purpose=purpose
            )
            if size != before.size or before != after_handle or before != after_path:
                raise _error(BundleIOCodeV1.CONFLICT)
            result = digest.hexdigest(), before
        except BaseException as error:
            primary = error
        if opened is not None:
            try:
                self._port.close_borrowed_file(borrow, opened, purpose=purpose)
            except BaseException:
                raise _error(BundleIOCodeV1.INDETERMINATE) from None
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            if isinstance(primary, LocalIOErrorV1):
                raise _runtime_pair_error(primary)
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    def _write_payload(self, access, directory, component, payload):
        opened = None
        primary = None
        result = None
        try:
            opened = self._port.create_borrowed_file(
                access.create_borrow, directory, component, purpose=CREATE
            )
            offset = 0
            while offset < len(payload):
                chunk = payload[offset:offset + MAX_BUNDLE_CHUNK_BYTES]
                written = self._port.write_borrowed(
                    access.create_borrow, opened, chunk, purpose=CREATE
                )
                if type(written) is not int or written != len(chunk):
                    raise _error(BundleIOCodeV1.INDETERMINATE)
                offset += written
            self._port.fsync_borrowed_file(
                access.create_borrow, opened, purpose=CREATE
            )
            identity = self._port.stat_borrowed_file(
                access.create_borrow, opened, purpose=CREATE
            )
            if (
                type(identity) is not LocalFileIdentityV1
                or not stat_is_regular_single_v1(identity)
                or identity.size != len(payload)
            ):
                raise _error(BundleIOCodeV1.INDETERMINATE)
            result = identity
        except BaseException as error:
            primary = error
        if opened is not None:
            try:
                self._port.close_borrowed_file(
                    access.create_borrow, opened, purpose=CREATE
                )
            except BaseException:
                raise _error(BundleIOCodeV1.INDETERMINATE) from None
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    def _copy_member(self, member, physical, access, private):
        try:
            resolved = self._sources.resolve(member.source_ref)
        except BaseException:
            raise _error(BundleIOCodeV1.SOURCE_INVALID) from None
        source = self._snapshot_source(resolved, member.source_ref)
        source_file = None
        destination_file = None
        primary = None
        result = None
        try:
            before = self._port.stat_borrowed(
                source.borrow, source.directory, source.component, purpose=SOURCE
            )
            if (
                type(before) is not LocalFileIdentityV1
                or not stat_is_regular_single_v1(before)
                or before.size != member.size
            ):
                raise _error(BundleIOCodeV1.SOURCE_INVALID)
            source_file = self._port.open_borrowed_read(
                source.borrow, source.directory, source.component, purpose=SOURCE
            )
            destination_file = self._port.create_borrowed_file(
                access.create_borrow, private, physical, purpose=CREATE
            )
            digest = hashlib.sha256()
            size = 0
            while True:
                chunk = self._port.read_borrowed(
                    source.borrow, source_file, MAX_BUNDLE_CHUNK_BYTES,
                    purpose=SOURCE,
                )
                if type(chunk) is not bytes or len(chunk) > MAX_BUNDLE_CHUNK_BYTES:
                    raise _error(BundleIOCodeV1.STREAM_INVALID)
                if not chunk:
                    break
                size += len(chunk)
                if size > member.size:
                    raise _error(BundleIOCodeV1.STREAM_INVALID)
                digest.update(chunk)
                written = self._port.write_borrowed(
                    access.create_borrow, destination_file, chunk, purpose=CREATE
                )
                if type(written) is not int or written != len(chunk):
                    raise _error(BundleIOCodeV1.INDETERMINATE)
            after_source = self._port.stat_borrowed_file(
                source.borrow, source_file, purpose=SOURCE
            )
            after_path = self._port.stat_borrowed(
                source.borrow, source.directory, source.component, purpose=SOURCE
            )
            if (
                size != member.size
                or digest.hexdigest() != member.sha256
                or before != after_source
                or before != after_path
            ):
                raise _error(BundleIOCodeV1.STREAM_INVALID)
            self._port.fsync_borrowed_file(
                access.create_borrow, destination_file, purpose=CREATE
            )
            destination_identity = self._port.stat_borrowed_file(
                access.create_borrow, destination_file, purpose=CREATE
            )
            result = BundleMemberEvidenceV1(
                member.logical_name, physical, size, digest.hexdigest(),
                destination_identity,
            )
        except BaseException as error:
            primary = error
        close_failed = False
        for borrow, opened, purpose in (
            (source.borrow, source_file, SOURCE),
            (access.create_borrow, destination_file, CREATE),
        ):
            if opened is not None:
                try:
                    self._port.close_borrowed_file(borrow, opened, purpose=purpose)
                except BaseException:
                    close_failed = True
        if close_failed:
            raise _error(BundleIOCodeV1.INDETERMINATE)
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    @staticmethod
    def _manifest(command, access, members):
        raw = canonical_bytes_v1({
            "command_digest": command.command_digest,
            "destination_ref": command.destination_ref,
            "members": [member.canonical() for member in members],
            "root_authority_digest": access.root_authority_digest,
            "schema_version": "synaptic-host-bundle-manifest/v1",
        })
        if len(raw) > MAX_BUNDLE_MANIFEST_BYTES:
            raise _error(BundleIOCodeV1.BOUND_EXCEEDED)
        return raw

    @staticmethod
    def _marker(command, access, private_name, companion_name, manifest_digest,
                inventory_digest, manifest_identity):
        raw = canonical_bytes_v1({
            "command_digest": command.command_digest,
            "companion_name": companion_name,
            "destination_ref": command.destination_ref,
            "inventory_digest": inventory_digest,
            "manifest_digest": manifest_digest,
            "manifest_identity": manifest_identity.canonical(),
            "private_name": private_name,
            "root_authority_digest": access.root_authority_digest,
            "schema_version": "synaptic-host-bundle-commit/v1",
        })
        if len(raw) > MAX_BUNDLE_MANIFEST_BYTES:
            raise _error(BundleIOCodeV1.BOUND_EXCEEDED)
        return raw

    @staticmethod
    def _binding(command, access, private_name, marker_name, companion_name,
                 manifest_digest, members, manifest_identity, marker_identity):
        inventory = digest_v1([member.canonical() for member in members])
        body = {
            "command_digest": command.command_digest,
            "companion_name": companion_name,
            "destination_ref": command.destination_ref,
            "inventory_digest": inventory,
            "manifest_digest": manifest_digest,
            "manifest_identity": manifest_identity.canonical(),
            "marker_identity": marker_identity.canonical(),
            "marker_name": marker_name,
            "members": [member.canonical() for member in members],
            "private_name": private_name,
            "root_authority_digest": access.root_authority_digest,
            "schema_version": "synaptic-host-bundle-binding/v1",
        }
        return BundleBindingV1(
            command.command_digest, command.destination_ref,
            access.root_authority_digest, private_name, marker_name,
            companion_name, manifest_digest, inventory, members,
            manifest_identity, marker_identity, digest_v1(body),
        )

    def _inspect_private(self, command, access, private_name):
        private = None
        primary = None
        result = None
        try:
            private = self._port.open_borrowed_directory(
                access.verify_borrow, access.verify_root, private_name,
                purpose=VERIFY,
            )
            expected_names = tuple(
                [f"member-{index:04d}" for index in range(len(command.members))]
                + ["MANIFEST.json"]
            )
            names = self._port.list_borrowed_directory(
                access.verify_borrow, private, len(expected_names) + 1,
                purpose=VERIFY,
            )
            if type(names) is not tuple or tuple(sorted(names)) != tuple(sorted(expected_names)):
                raise _error(BundleIOCodeV1.CONFLICT)
            manifest_raw, manifest_identity = self._read_single(
                access.verify_borrow, private, "MANIFEST.json", purpose=VERIFY,
                maximum=MAX_BUNDLE_MANIFEST_BYTES,
            )
            manifest = _parse_canonical(manifest_raw, MAX_BUNDLE_MANIFEST_BYTES)
            if set(manifest) != {
                "command_digest", "destination_ref", "members",
                "root_authority_digest", "schema_version",
            } or manifest.get("command_digest") != command.command_digest or (
                manifest.get("destination_ref") != command.destination_ref
                or manifest.get("root_authority_digest")
                != access.root_authority_digest
                or manifest.get("schema_version")
                != "synaptic-host-bundle-manifest/v1"
            ):
                raise _error(BundleIOCodeV1.CONFLICT)
            raw_members = manifest.get("members")
            if type(raw_members) is not list or len(raw_members) != len(command.members):
                raise _error(BundleIOCodeV1.CONFLICT)
            evidence = []
            for index, (raw_member, expected) in enumerate(
                zip(raw_members, command.members)
            ):
                if type(raw_member) is not dict or set(raw_member) != {
                    "identity", "logical_name", "physical_name", "sha256", "size"
                }:
                    raise _error(BundleIOCodeV1.CONFLICT)
                item = BundleMemberEvidenceV1(
                    raw_member["logical_name"], raw_member["physical_name"],
                    raw_member["size"], raw_member["sha256"],
                    _identity(raw_member["identity"]),
                )
                if (
                    item.logical_name != expected.logical_name
                    or item.physical_name != f"member-{index:04d}"
                    or item.size != expected.size
                    or item.sha256 != expected.sha256
                ):
                    raise _error(BundleIOCodeV1.CONFLICT)
                content_digest, _ = self._hash_single(
                    access.verify_borrow, private, item.physical_name,
                    purpose=VERIFY, maximum=item.size,
                    expected_identity=item.identity,
                )
                if content_digest != item.sha256:
                    raise _error(BundleIOCodeV1.CONFLICT)
                evidence.append(item)
            result = (
                tuple(evidence), hashlib.sha256(manifest_raw).hexdigest(),
                manifest_identity,
            )
        except BaseException as error:
            primary = error
        if private is not None:
            try:
                self._port.close_borrowed_directory(
                    access.verify_borrow, private, purpose=VERIFY
                )
            except BaseException:
                raise _error(BundleIOCodeV1.INDETERMINATE) from None
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            if isinstance(primary, LocalIOErrorV1):
                raise _runtime_pair_error(primary)
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    def _materialize_private(self, command, access, private_name):
        private = None
        primary = None
        result = None
        try:
            private = self._port.open_borrowed_directory(
                access.create_borrow, access.create_root, private_name,
                purpose=CREATE,
            )
            members = tuple(
                self._copy_member(member, f"member-{index:04d}", access, private)
                for index, member in enumerate(command.members)
            )
            manifest_raw = self._manifest(command, access, members)
            manifest_identity = self._write_payload(
                access, private, "MANIFEST.json", manifest_raw
            )
            self._port.fsync_borrowed_directory(
                access.create_borrow, private, purpose=CREATE
            )
            result = members, manifest_raw, manifest_identity
        except BaseException as error:
            primary = error
        if private is not None:
            try:
                self._port.close_borrowed_directory(
                    access.create_borrow, private, purpose=CREATE
                )
            except BaseException:
                raise _error(BundleIOCodeV1.INDETERMINATE) from None
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    def _read_pair(self, access, marker_name, companion_name, maximum,
                   *, fsync_root):
        pair = None
        primary = None
        result = None
        first, second = sorted((marker_name, companion_name))
        try:
            pair = self._port.open_borrowed_hardlink_pair(
                access.verify_borrow, access.verify_root, first, second,
                purpose=VERIFY,
            )
            if pair.first_component != first or pair.second_component != second:
                raise _error(BundleIOCodeV1.CONFLICT)
            chunks = []
            size = 0
            while True:
                chunk = self._port.read_borrowed_hardlink_pair(
                    access.verify_borrow, pair, MAX_BUNDLE_CHUNK_BYTES,
                    purpose=VERIFY,
                )
                if type(chunk) is not bytes or len(chunk) > MAX_BUNDLE_CHUNK_BYTES:
                    raise _error(BundleIOCodeV1.CONFLICT)
                if not chunk:
                    break
                size += len(chunk)
                if size > maximum or size > pair.first_identity.size:
                    raise _error(BundleIOCodeV1.CONFLICT)
                chunks.append(chunk)
            identity = self._port.stat_borrowed_hardlink_pair(
                access.verify_borrow, pair, purpose=VERIFY
            )
            if size != pair.first_identity.size or not hardlink_pair_identity_v1(identity):
                raise _error(BundleIOCodeV1.CONFLICT)
            if fsync_root:
                self._port.fsync_borrowed_directory(
                    access.create_borrow, access.create_root, purpose=CREATE
                )
                after_fsync = self._port.stat_borrowed_hardlink_pair(
                    access.verify_borrow, pair, purpose=VERIFY
                )
                if after_fsync != identity:
                    raise _error(BundleIOCodeV1.CONFLICT)
            result = (b"".join(chunks), identity)
        except BaseException as error:
            primary = error
        if pair is not None:
            try:
                self._port.close_borrowed_hardlink_pair(
                    access.verify_borrow, pair, purpose=VERIFY
                )
            except BaseException:
                raise _error(BundleIOCodeV1.INDETERMINATE) from None
        if primary is not None:
            if isinstance(primary, BundleIOErrorV1):
                raise primary
            if isinstance(primary, LocalIOErrorV1):
                raise _runtime_pair_error(primary)
            raise _error(BundleIOCodeV1.INDETERMINATE) from None
        return result

    def _observe(self, command, access, *, expected=None):
        private_name, marker_name, companion_name = self._names(command, access)
        try:
            private_identity = self._port.stat_borrowed(
                access.verify_borrow, access.verify_root, private_name,
                purpose=VERIFY,
            )
            marker_identity = self._port.stat_borrowed(
                access.verify_borrow, access.verify_root, marker_name,
                purpose=VERIFY,
            )
            companion_identity = self._port.stat_borrowed(
                access.verify_borrow, access.verify_root, companion_name,
                purpose=VERIFY,
            )
        except BaseException:
            return _result(BundleLookupStatusV1.INDETERMINATE, command)
        if private_identity is None and marker_identity is None and companion_identity is None:
            return _result(BundleLookupStatusV1.DEFINITELY_ABSENT, command)
        if private_identity is None:
            return _result(
                BundleLookupStatusV1.CONFLICT if marker_identity is not None
                else BundleLookupStatusV1.INDETERMINATE,
                command,
            )
        if marker_identity is None and companion_identity is None:
            return _result(BundleLookupStatusV1.INDETERMINATE, command)
        try:
            members, manifest_digest, manifest_identity = self._inspect_private(
                command, access, private_name
            )
            inventory = digest_v1([member.canonical() for member in members])
            marker_raw = self._marker(
                command, access, private_name, companion_name, manifest_digest,
                inventory, manifest_identity,
            )
            if marker_identity is None:
                if companion_identity is None:
                    return _result(BundleLookupStatusV1.INDETERMINATE, command)
                companion_raw, _ = self._read_single(
                    access.verify_borrow, access.verify_root, companion_name,
                    purpose=VERIFY, maximum=MAX_BUNDLE_MANIFEST_BYTES,
                    expected_identity=companion_identity,
                )
                return _result(
                    BundleLookupStatusV1.INDETERMINATE
                    if companion_raw == marker_raw else BundleLookupStatusV1.CONFLICT,
                    command,
                )
            if companion_identity is None:
                return _result(BundleLookupStatusV1.CONFLICT, command)
            first_raw, first_identity = self._read_pair(
                access, marker_name, companion_name,
                MAX_BUNDLE_MANIFEST_BYTES, fsync_root=False,
            )
            if first_raw != marker_raw:
                return _result(BundleLookupStatusV1.CONFLICT, command)
            second_raw, second_identity = self._read_pair(
                access, marker_name, companion_name,
                MAX_BUNDLE_MANIFEST_BYTES, fsync_root=False,
            )
            if second_raw != marker_raw or second_identity != first_identity:
                return _result(BundleLookupStatusV1.CONFLICT, command)
            binding = self._binding(
                command, access, private_name, marker_name, companion_name,
                manifest_digest, members, manifest_identity, second_identity,
            )
            if expected is not None:
                try:
                    if self._snapshot_binding(expected) != binding:
                        return _result(BundleLookupStatusV1.CONFLICT, command)
                except BaseException:
                    return _result(BundleLookupStatusV1.CONFLICT, command)
            return _result(BundleLookupStatusV1.FOUND, command, binding)
        except BundleIOErrorV1 as error:
            return _result(
                BundleLookupStatusV1.CONFLICT
                if error.code is BundleIOCodeV1.CONFLICT
                else BundleLookupStatusV1.INDETERMINATE,
                command,
            )
        except BaseException:
            return _result(BundleLookupStatusV1.INDETERMINATE, command)

    def lookup(self, command, access, *, expected=None):
        command, access = self._validate(command, access)
        observed = self._observe(command, access, expected=expected)
        if observed.status is BundleLookupStatusV1.FOUND:
            # Exact namespace structure is observable, but lookup owns no
            # durability authority and therefore cannot attest FOUND.
            return _result(BundleLookupStatusV1.INDETERMINATE, command)
        return observed

    def _durable_finalize(self, command, access, structural_binding):
        private_name, marker_name, companion_name = self._names(command, access)
        marker_raw = self._marker(
            command, access, private_name, companion_name,
            structural_binding.manifest_digest,
            structural_binding.inventory_digest,
            structural_binding.manifest_identity,
        )
        try:
            first_raw, first_identity = self._read_pair(
                access, marker_name, companion_name,
                MAX_BUNDLE_MANIFEST_BYTES, fsync_root=True,
            )
            if first_raw != marker_raw:
                return _result(BundleLookupStatusV1.CONFLICT, command)
            second_raw, second_identity = self._read_pair(
                access, marker_name, companion_name,
                MAX_BUNDLE_MANIFEST_BYTES, fsync_root=False,
            )
            if second_raw != marker_raw or second_identity != first_identity:
                return _result(BundleLookupStatusV1.CONFLICT, command)
            binding = self._binding(
                command, access, private_name, marker_name, companion_name,
                structural_binding.manifest_digest,
                structural_binding.members,
                structural_binding.manifest_identity,
                second_identity,
            )
            if binding != structural_binding:
                return _result(BundleLookupStatusV1.CONFLICT, command)
            return _result(BundleLookupStatusV1.FOUND, command, binding)
        except BundleIOErrorV1 as error:
            return _result(
                BundleLookupStatusV1.CONFLICT
                if error.code is BundleIOCodeV1.CONFLICT
                else BundleLookupStatusV1.INDETERMINATE,
                command,
            )
        except BaseException:
            return _result(BundleLookupStatusV1.INDETERMINATE, command)

    def seal(self, command, access):
        command, access = self._validate(command, access)
        private_name, marker_name, companion_name = self._names(command, access)
        existing = self._observe(command, access)
        if existing.status is BundleLookupStatusV1.FOUND:
            return self._durable_finalize(command, access, existing.binding)
        if existing.status is not BundleLookupStatusV1.DEFINITELY_ABSENT:
            return existing
        claimed = False
        try:
            claimed = self._port.mkdir_borrowed(
                access.create_borrow, access.create_root, private_name,
                purpose=CREATE,
            )
            if type(claimed) is not bool:
                raise _error(BundleIOCodeV1.INDETERMINATE)
            if not claimed:
                observed = self._observe(command, access)
                if observed.status is BundleLookupStatusV1.FOUND:
                    return self._durable_finalize(
                        command, access, observed.binding
                    )
                return observed
            members, manifest_raw, manifest_identity = self._materialize_private(
                command, access, private_name
            )
            inventory = digest_v1([member.canonical() for member in members])
            marker_raw = self._marker(
                command, access, private_name, companion_name,
                hashlib.sha256(manifest_raw).hexdigest(), inventory,
                manifest_identity,
            )
            prelink = self._write_payload(
                access, access.create_root, companion_name, marker_raw
            )
            verified_raw, verified_identity = self._read_single(
                access.verify_borrow, access.verify_root, companion_name,
                purpose=VERIFY, maximum=MAX_BUNDLE_MANIFEST_BYTES,
                expected_identity=prelink,
            )
            if verified_raw != marker_raw:
                raise _error(BundleIOCodeV1.CONFLICT)
            self._port.fsync_borrowed_directory(
                access.create_borrow, access.create_root, purpose=CREATE
            )
            try:
                self._port.link_borrowed(
                    access.create_borrow, access.create_root, companion_name,
                    marker_name, purpose=CREATE,
                )
            except BaseException:
                pass
            observed = self._observe(command, access)
            if observed.status is not BundleLookupStatusV1.FOUND:
                return observed
            result = self._durable_finalize(command, access, observed.binding)
            if result.status is BundleLookupStatusV1.FOUND:
                pair_identity = result.binding.marker_identity
                if (
                    pair_identity.device != verified_identity.device
                    or pair_identity.inode != verified_identity.inode
                    or (pair_identity.mode & 0o170000)
                    != (verified_identity.mode & 0o170000)
                    or pair_identity.size != verified_identity.size
                    or pair_identity.modified_ns != verified_identity.modified_ns
                    or pair_identity.changed_ns < verified_identity.changed_ns
                ):
                    return _result(BundleLookupStatusV1.CONFLICT, command)
            return result
        except BaseException:
            return _result(
                BundleLookupStatusV1.INDETERMINATE if claimed
                else BundleLookupStatusV1.CONFLICT,
                command,
            )


__all__: tuple[str, ...] = ()
