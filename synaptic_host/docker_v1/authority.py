"""Typed, domain-separated Docker-v1 authentication authorities."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from threading import RLock
from types import MappingProxyType
from weakref import WeakKeyDictionary

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleBindingV1,
    BundleIOCodeV1,
    checked_ref_v1,
    digest_v1,
)
from synaptic_host.security import FileHmacAuthenticator
from synaptic_tuner.api.v1.docker import DockerBindingAuthorityV1
from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    AuthenticatedDockerCommandBindingV1,
    AuthenticatedDockerSourceSealV1,
    DockerAbsenceContentV1,
    DockerCommandBindingV1,
    DockerEffectIdentityV1,
    DockerLabelsV1,
    PreparedDockerPlanV1,
    DockerSourceSealContentV1,
    validated_profile_snapshot,
)

from .control_contract import (
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerExpectedCreateBindingV1,
    AuthenticatedDockerMutationRecordV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerControlIntentV1,
    DockerCreatePathBindingV1,
    DockerExpectedCreateBindingV1,
    DockerMutationRecordV1,
    DockerWorkloadEnvironmentBindingV1,
)
from .model import (
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStageBundleBindingV1,
    AuthenticatedDockerStorageMappingV1,
    AuthenticatedDockerStoragePathMappingPairV1,
    AuthenticatedDockerWSLRootMappingV1,
    DockerSourceDeclarationV1,
    DockerStageBundleBindingV1,
    DockerStorageMappingV1,
    DockerStoragePathMappingPairV1,
    DockerWSLRootMappingV1,
    _storage_mapping_snapshot_v1,
    _wsl_mapping_snapshot_v1,
)
from synaptic_host.bundle_io_v1.ports import BundleMountVerifyAccessV1


def _closed_failure() -> ValueError:
    return ValueError("Docker authority operation failed")


@dataclass(frozen=True, slots=True)
class _KernelPinsV1:
    authority_ref: str
    key_ref: str
    authenticator: FileHmacAuthenticator
    key_path: Path
    purpose: str


@dataclass(frozen=True, slots=True)
class _AuthorityPinsV1:
    authority_type: type
    authority_ref: str
    key_ref: str
    kernel: object
    content_type: type
    envelope_type: type
    digest_attribute: str
    purpose: str
    pin_identity: object


@dataclass(frozen=True, slots=True)
class _PairPinsV1:
    storage: object
    storage_ref: str
    storage_key: str
    wsl: object
    wsl_ref: str
    wsl_key: str


class _DockerHmacKernelV1:
    __slots__ = (
        "authority_ref", "key_ref", "_authenticator", "_purpose",
        "__weakref__",
    )

    def __init__(
        self, *, authority_ref: str, authenticator: FileHmacAuthenticator,
        purpose: str,
    ) -> None:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def _check(self) -> None:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def _payload(self, content_digest: str) -> bytes:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def sign(self, content_digest: str) -> str:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def verify(self, content_digest: str, tag: str) -> bool:
        raise RuntimeError("sealed Docker authority runtime unavailable")


class _TypedEnvelopeAuthorityV1:
    __slots__ = ("authority_ref", "key_ref", "_kernel", "__weakref__")

    def __init__(
        self, *, authority_ref: str, authenticator: FileHmacAuthenticator
    ) -> None:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def _validated_pins(self) -> _AuthorityPinsV1:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def issue(self, value):
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def authenticate(self, value):
        raise RuntimeError("sealed Docker authority runtime unavailable")


class DockerSourceDeclarationHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerStageBundleRecordHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerStorageMappingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerWSLRootMappingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class BundleBindingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerSourceSealHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerCreatePathBindingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerWorkloadEnvironmentBindingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerControlIntentHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerMutationRecordHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerAbsenceHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerExpectedCreateBindingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    __slots__ = ()


class DockerCommandBindingHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    """Exact engine binding authority: issue an envelope, authenticate to bool."""

    __slots__ = ()

    def authenticate(self, value) -> bool:
        return super().authenticate(value) is not None


class DockerCommandBindingEnvelopeAuthorityViewV1:
    """Host envelope-returning view over the exact engine authority."""

    __slots__ = ("authority_ref", "key_ref", "_authority", "_authority_id")

    def __init__(self, authority: DockerBindingAuthorityV1) -> None:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def authenticate(self, value):
        raise RuntimeError("sealed Docker authority runtime unavailable")


class DockerEvidenceAuthorityViewV1:
    """Boolean engine evidence view over exact host envelope authorities."""

    __slots__ = (
        "_source", "_absence", "_source_id", "_absence_id",
        "_source_ref", "_source_key", "_absence_ref", "_absence_key",
    )

    def __init__(self, *, source_seal_authority, absence_authority) -> None:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def authenticate_source_seal(self, value) -> bool:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def authenticate_absence(self, value) -> bool:
        raise RuntimeError("sealed Docker authority runtime unavailable")


class DockerStoragePathMappingPairHmacAuthorityV1(_TypedEnvelopeAuthorityV1):
    """Authenticates the outer pair and both nested mapping envelopes."""

    __slots__ = (
        "_storage", "_wsl",
    )

    def __init__(
        self, *, authority_ref: str, authenticator: FileHmacAuthenticator,
        storage_mapping_authority, wsl_mapping_authority,
    ) -> None:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def _validated_pair_pins(self) -> _PairPinsV1:
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def _nested(self, value: DockerStoragePathMappingPairV1):
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def issue(self, value):
        raise RuntimeError("sealed Docker authority runtime unavailable")

    def authenticate(self, value):
        raise RuntimeError("sealed Docker authority runtime unavailable")


def _install_sealed_authority_runtime(
    *, kernel_type, authority_base, pair_type, authenticator_type,
    kernel_pin_type, authority_pin_type, pair_pin_type,
    command_view_type, evidence_view_type,
    labels_type, command_content_type, effect_identity_type, plan_type,
    command_envelope_type, storage_envelope_type, wsl_envelope_type,
    source_seal_envelope_type, absence_envelope_type,
    storage_content_type, wsl_content_type,
    verify_access_type,
    pair_content_type, pair_envelope_type, specifications,
    storage_snapshotter, wsl_snapshotter, profile_snapshotter,
    enum_type, dataclass_fields, dataclass_checker,
    digest_builder, reference_checker, failure_factory, path_type,
    authentication_failure_code,
) -> None:
    """Install operations closed over the original authority universe."""

    primitive_types = (str, int, float, bool, bytes, type(None))

    def snapshot(value):
        """Reconstruct through closure-pinned classes and helper capabilities."""
        try:
            if type(value) in primitive_types:
                return value
            if isinstance(value, enum_type):
                return value
            if type(value) is tuple:
                return tuple(snapshot(item) for item in value)
            if type(value) is labels_type:
                return labels_type(**{
                    item.name: getattr(value, item.name)
                    for item in dataclass_fields(value)
                })
            if type(value) is command_content_type:
                identity = value.identity
                if (
                    type(identity) is not effect_identity_type
                    or type(identity.plan) is not plan_type
                ):
                    raise ValueError
                plan = identity.plan
                plan = plan_type(
                    profile_snapshotter(plan.profile),
                    plan.project_ref, plan.run_id, plan.plan_fingerprint,
                    plan.source_digest, plan.preparation_digest,
                )
                identity = effect_identity_type(
                    identity.command_digest, identity.effect_id,
                    identity.effect_kind, plan,
                )
                rebuilt = command_content_type(
                    identity, bytes(value.command_bytes),
                    None if value.original_submit_command_bytes is None
                    else bytes(value.original_submit_command_bytes),
                    value.cancel_container_ref, value.cancel_reason_digest,
                    snapshot(value.cancel_submit_labels),
                    value.cancel_authorization_digest,
                )
                if rebuilt != value:
                    raise ValueError
                return rebuilt
            if type(value) is command_envelope_type:
                content = snapshot(value.content)
                rebuilt = command_envelope_type(
                    content, value.binding_digest, value.authority_ref,
                    value.key_ref, value.tag,
                )
                if rebuilt != value:
                    raise ValueError
                return rebuilt
            if type(value) is storage_content_type:
                temporary = storage_envelope_type(
                    value, "snapshot-authority", "snapshot-key", "0" * 64
                )
                rebuilt = storage_snapshotter(temporary)
                if (
                    type(rebuilt) is not storage_envelope_type
                    or type(rebuilt.content) is not storage_content_type
                ):
                    raise ValueError
                original_access = value.verify_access
                retained_access = rebuilt.content.verify_access
                if original_access is None:
                    if retained_access is not None:
                        raise ValueError
                elif (
                    type(original_access) is not verify_access_type
                    or type(retained_access) is not verify_access_type
                    or retained_access.verify_borrow
                    is not original_access.verify_borrow
                    or retained_access.verify_root is not original_access.verify_root
                ):
                    raise ValueError
                return rebuilt.content
            if type(value) is storage_envelope_type:
                rebuilt = storage_snapshotter(value)
                if (
                    type(rebuilt) is not storage_envelope_type
                    or type(rebuilt.content) is not storage_content_type
                ):
                    raise ValueError
                original_access = value.content.verify_access
                retained_access = rebuilt.content.verify_access
                if original_access is None:
                    if retained_access is not None:
                        raise ValueError
                elif (
                    type(original_access) is not verify_access_type
                    or type(retained_access) is not verify_access_type
                    or retained_access.verify_borrow
                    is not original_access.verify_borrow
                    or retained_access.verify_root is not original_access.verify_root
                ):
                    raise ValueError
                return rebuilt
            if type(value) is wsl_content_type:
                temporary = wsl_envelope_type(
                    value, "snapshot-authority", "snapshot-key", "0" * 64
                )
                rebuilt = wsl_snapshotter(temporary)
                if (
                    type(rebuilt) is not wsl_envelope_type
                    or type(rebuilt.content) is not wsl_content_type
                ):
                    raise ValueError
                return rebuilt.content
            if type(value) is wsl_envelope_type:
                rebuilt = wsl_snapshotter(value)
                if (
                    type(rebuilt) is not wsl_envelope_type
                    or type(rebuilt.content) is not wsl_content_type
                ):
                    raise ValueError
                return rebuilt
            if type(value) is pair_content_type:
                return pair_content_type(
                    value.storage_mapping, value.wsl_mapping, value.pair_digest
                )
            if type(value) is pair_envelope_type:
                return pair_envelope_type(
                    snapshot(value.content), value.authority_ref,
                    value.key_ref, value.tag,
                )
            if not dataclass_checker(value) or isinstance(value, type):
                raise ValueError
            rebuilt = type(value)(*(
                snapshot(getattr(value, item.name))
                for item in dataclass_fields(value)
            ))
            if rebuilt != value:
                raise ValueError
            return rebuilt
        except BaseException:
            raise failure_factory() from None

    def content_digest(value, attribute):
        try:
            digest = getattr(value, attribute)
            if type(digest) is not str or len(digest) != 64:
                raise ValueError
            int(digest, 16)
            return digest
        except BaseException:
            raise failure_factory() from None

    schema_by_type = MappingProxyType({
        authority_type: (
            content_type, envelope_type, digest_attribute, purpose
        )
        for (
            authority_type, content_type, envelope_type,
            digest_attribute, purpose,
        ) in specifications
    })

    def weak_store():
        values = WeakKeyDictionary()
        lock = RLock()

        def register(owner, value) -> None:
            with lock:
                if owner in values:
                    raise failure_factory()
                values[owner] = value

        def lookup(owner):
            with lock:
                return values.get(owner)

        return register, lookup

    register_kernel, lookup_kernel = weak_store()
    register_authority, lookup_authority = weak_store()
    register_pair, lookup_pair = weak_store()

    def validate_kernel(self):
        pins = lookup_kernel(self)
        if (
            type(pins) is not kernel_pin_type
            or type(self) is not kernel_type
            or type(self._authenticator) is not authenticator_type
            or self._authenticator is not pins.authenticator
            or self.authority_ref != pins.authority_ref
            or self.key_ref != pins.key_ref
            or self._purpose != pins.purpose
            or self._authenticator.key_ref != pins.key_ref
            or path_type(self._authenticator.key_path) != pins.key_path
        ):
            raise failure_factory()
        return pins

    def kernel_init(self, *, authority_ref, authenticator, purpose):
        try:
            reference_checker(authority_ref, authentication_failure_code)
            if type(authenticator) is not authenticator_type:
                raise ValueError
            reference_checker(
                authenticator.key_ref, authentication_failure_code
            )
            if (
                type(purpose) is not str
                or not purpose.isascii()
                or not purpose.startswith("synaptic-host-docker-")
                or not purpose.endswith("/v1")
            ):
                raise ValueError
            self.authority_ref = authority_ref
            self.key_ref = authenticator.key_ref
            self._authenticator = authenticator
            self._purpose = purpose
            register_kernel(self, kernel_pin_type(
                authority_ref, authenticator.key_ref, authenticator,
                path_type(authenticator.key_path), purpose,
            ))
            validate_kernel(self)
        except BaseException:
            raise failure_factory() from None

    def kernel_payload(self, content_digest):
        pins = validate_kernel(self)
        return digest_builder({
            "authority_ref": pins.authority_ref,
            "content_digest": content_digest,
            "key_ref": pins.key_ref,
            "schema_version": pins.purpose + "-payload",
        }).encode("ascii")

    def kernel_sign(self, content_digest):
        try:
            pins = validate_kernel(self)
            payload = kernel_payload(self, content_digest)
            validate_kernel(self)
            tag = pins.authenticator.sign(
                pins.purpose, payload, pins.key_ref
            )
            validate_kernel(self)
            if type(tag) is not bytes or len(tag) != 32:
                raise ValueError
            return tag.hex()
        except BaseException:
            raise failure_factory() from None

    def kernel_verify(self, content_digest, tag):
        try:
            pins = validate_kernel(self)
            if type(tag) is not str or len(tag) != 64:
                return False
            raw_tag = bytes.fromhex(tag)
            payload = kernel_payload(self, content_digest)
            validate_kernel(self)
            result = pins.authenticator.verify(
                pins.purpose, payload, raw_tag, pins.key_ref
            )
            validate_kernel(self)
            return result is True
        except BaseException:
            return False

    def authority_init(self, *, authority_ref, authenticator):
        schema = schema_by_type.get(type(self))
        if type(schema) is not tuple or len(schema) != 4:
            raise failure_factory()
        content_type, envelope_type, digest_attribute, purpose = schema
        kernel = object.__new__(kernel_type)
        kernel_init(
            kernel, authority_ref=authority_ref,
            authenticator=authenticator, purpose=purpose,
        )
        self.authority_ref = kernel.authority_ref
        self.key_ref = kernel.key_ref
        self._kernel = kernel
        identity = object()
        pins = authority_pin_type(
            type(self), self.authority_ref, self.key_ref, kernel,
            content_type, envelope_type, digest_attribute, purpose, identity,
        )
        register_authority(self, (pins, identity))
        validate_authority(self)

    def validate_authority(self):
        retained = lookup_authority(self)
        if type(retained) is not tuple or len(retained) != 2:
            raise failure_factory()
        pins, identity = retained
        expected = schema_by_type.get(type(self))
        if (
            type(pins) is not authority_pin_type
            or pins is not retained[0]
            or pins.pin_identity is not identity
            or type(self) is not pins.authority_type
            or self.authority_ref != pins.authority_ref
            or self.key_ref != pins.key_ref
            or self._kernel is not pins.kernel
            or expected is None
            or (
                pins.content_type, pins.envelope_type,
                pins.digest_attribute, pins.purpose,
            ) != expected
        ):
            raise failure_factory()
        kernel_pins = validate_kernel(pins.kernel)
        if kernel_pins.purpose != pins.purpose:
            raise failure_factory()
        return pins

    def authority_issue(self, value):
        try:
            pins = validate_authority(self)
            if type(value) is not pins.content_type:
                raise ValueError
            content = snapshot(value)
            validate_authority(self)
            digest = content_digest(content, pins.digest_attribute)
            tag = kernel_sign(pins.kernel, digest)
            validate_authority(self)
            content = snapshot(content)
            if content_digest(content, pins.digest_attribute) != digest:
                raise ValueError
            if pins.envelope_type is command_envelope_type:
                envelope = command_envelope_type(
                    content, content.binding_digest,
                    pins.authority_ref, pins.key_ref, tag,
                )
            else:
                envelope = pins.envelope_type(
                    content, pins.authority_ref, pins.key_ref, tag
                )
            retained = snapshot(envelope)
            validate_authority(self)
            if retained != envelope:
                raise ValueError
            return retained
        except BaseException:
            raise failure_factory() from None

    def authority_authenticate(self, value):
        try:
            pins = validate_authority(self)
            if type(value) is not pins.envelope_type:
                return None
            presented = snapshot(value)
            validate_authority(self)
            if (
                presented.authority_ref != pins.authority_ref
                or presented.key_ref != pins.key_ref
            ):
                return None
            digest = content_digest(
                presented.content, pins.digest_attribute
            )
            if not kernel_verify(pins.kernel, digest, presented.tag):
                return None
            validate_authority(self)
            retained = snapshot(presented)
            if retained != presented:
                return None
            validate_authority(self)
            return retained
        except BaseException:
            return None

    def pair_init(
        self, *, authority_ref, authenticator,
        storage_mapping_authority, wsl_mapping_authority,
    ):
        authority_init(
            self, authority_ref=authority_ref, authenticator=authenticator
        )
        try:
            for authority in (storage_mapping_authority, wsl_mapping_authority):
                if not callable(getattr(authority, "authenticate", None)):
                    raise ValueError
                reference_checker(
                    authority.authority_ref, authentication_failure_code,
                )
                reference_checker(
                    authority.key_ref, authentication_failure_code
                )
            self._storage = storage_mapping_authority
            self._wsl = wsl_mapping_authority
            register_pair(self, pair_pin_type(
                storage_mapping_authority,
                storage_mapping_authority.authority_ref,
                storage_mapping_authority.key_ref,
                wsl_mapping_authority,
                wsl_mapping_authority.authority_ref,
                wsl_mapping_authority.key_ref,
            ))
            validate_pair(self)
        except BaseException:
            raise failure_factory() from None

    def validate_pair(self):
        validate_authority(self)
        pins = lookup_pair(self)
        if (
            type(pins) is not pair_pin_type
            or self._storage is not pins.storage
            or self._wsl is not pins.wsl
            or getattr(pins.storage, "authority_ref", None)
            != pins.storage_ref
            or getattr(pins.storage, "key_ref", None) != pins.storage_key
            or getattr(pins.wsl, "authority_ref", None) != pins.wsl_ref
            or getattr(pins.wsl, "key_ref", None) != pins.wsl_key
        ):
            raise failure_factory()
        return pins

    def pair_nested(self, value):
        try:
            pins = validate_pair(self)
            candidate = snapshot(value)
            validate_pair(self)
            storage = pins.storage.authenticate(
                snapshot(candidate.storage_mapping)
            )
            validate_pair(self)
            wsl = pins.wsl.authenticate(
                snapshot(candidate.wsl_mapping)
            )
            validate_pair(self)
            if (
                type(storage) is not storage_envelope_type
                or type(wsl) is not wsl_envelope_type
                or storage != candidate.storage_mapping
                or wsl != candidate.wsl_mapping
            ):
                raise ValueError
            rebuilt = pair_content_type(
                storage, wsl, candidate.pair_digest
            )
            validate_pair(self)
            if rebuilt != candidate:
                raise ValueError
            return rebuilt
        except BaseException:
            raise failure_factory() from None

    def pair_issue(self, value):
        try:
            validate_pair(self)
            nested = pair_nested(self, value)
            validate_pair(self)
            issued = authority_issue(self, nested)
            validate_pair(self)
            rebuilt = snapshot(issued)
            if rebuilt != issued:
                raise ValueError
            validate_pair(self)
            return rebuilt
        except BaseException:
            raise failure_factory() from None

    def pair_authenticate(self, value):
        try:
            validate_pair(self)
            authenticated = authority_authenticate(self, value)
            validate_pair(self)
            if authenticated is None:
                return None
            nested = pair_nested(self, authenticated.content)
            validate_pair(self)
            rebuilt = pair_envelope_type(
                nested, authenticated.authority_ref,
                authenticated.key_ref, authenticated.tag,
            )
            if rebuilt != authenticated:
                return None
            validate_pair(self)
            return rebuilt
        except BaseException:
            return None

    def command_view_authenticate(self, value):
        try:
            if (
                id(self._authority) != self._authority_id
                or getattr(self._authority, "authority_ref", None)
                != self.authority_ref
                or getattr(self._authority, "key_ref", None) != self.key_ref
                or type(value) is not command_envelope_type
            ):
                return None
            presented = snapshot(value)
            result = self._authority.authenticate(snapshot(presented))
            if (
                result is not True
                or id(self._authority) != self._authority_id
                or getattr(self._authority, "authority_ref", None)
                != self.authority_ref
                or getattr(self._authority, "key_ref", None) != self.key_ref
            ):
                return None
            retained = snapshot(presented)
            return retained if retained == presented else None
        except BaseException:
            return None

    def command_view_init(self, authority):
        try:
            authority_ref = getattr(authority, "authority_ref", None)
            key_ref = getattr(authority, "key_ref", None)
            reference_checker(authority_ref, authentication_failure_code)
            reference_checker(key_ref, authentication_failure_code)
            if not callable(getattr(authority, "authenticate", None)):
                raise ValueError
            self.authority_ref = authority_ref
            self.key_ref = key_ref
            self._authority = authority
            self._authority_id = id(authority)
        except BaseException:
            raise failure_factory() from None

    def evidence_view_init(
        self, *, source_seal_authority, absence_authority,
    ):
        try:
            for authority in (source_seal_authority, absence_authority):
                if not callable(getattr(authority, "authenticate", None)):
                    raise ValueError
                reference_checker(
                    getattr(authority, "authority_ref", None),
                    authentication_failure_code,
                )
                reference_checker(
                    getattr(authority, "key_ref", None),
                    authentication_failure_code,
                )
            self._source = source_seal_authority
            self._absence = absence_authority
            self._source_id = id(source_seal_authority)
            self._absence_id = id(absence_authority)
            self._source_ref = source_seal_authority.authority_ref
            self._source_key = source_seal_authority.key_ref
            self._absence_ref = absence_authority.authority_ref
            self._absence_key = absence_authority.key_ref
        except BaseException:
            raise failure_factory() from None

    def evidence_source_authenticate(self, value):
        try:
            if (
                id(self._source) != self._source_id
                or getattr(self._source, "authority_ref", None)
                != self._source_ref
                or getattr(self._source, "key_ref", None) != self._source_key
            ):
                return False
            presented = snapshot(value)
            returned = self._source.authenticate(snapshot(presented))
            return (
                type(returned) is source_seal_envelope_type
                and returned == presented
                and id(self._source) == self._source_id
                and getattr(self._source, "authority_ref", None)
                == self._source_ref
                and getattr(self._source, "key_ref", None) == self._source_key
            )
        except BaseException:
            return False

    def evidence_absence_authenticate(self, value):
        try:
            if (
                id(self._absence) != self._absence_id
                or getattr(self._absence, "authority_ref", None)
                != self._absence_ref
                or getattr(self._absence, "key_ref", None) != self._absence_key
            ):
                return False
            presented = snapshot(value)
            returned = self._absence.authenticate(snapshot(presented))
            return (
                type(returned) is absence_envelope_type
                and returned == presented
                and id(self._absence) == self._absence_id
                and getattr(self._absence, "authority_ref", None)
                == self._absence_ref
                and getattr(self._absence, "key_ref", None) == self._absence_key
            )
        except BaseException:
            return False

    kernel_type.__init__ = kernel_init
    kernel_type._check = validate_kernel
    kernel_type._payload = kernel_payload
    kernel_type.sign = kernel_sign
    kernel_type.verify = kernel_verify
    authority_base.__init__ = authority_init
    authority_base._validated_pins = validate_authority
    authority_base.issue = authority_issue
    authority_base.authenticate = authority_authenticate
    pair_type.__init__ = pair_init
    pair_type._validated_pair_pins = validate_pair
    pair_type._nested = pair_nested
    pair_type.issue = pair_issue
    pair_type.authenticate = pair_authenticate
    command_view_type.__init__ = command_view_init
    command_view_type.authenticate = command_view_authenticate
    evidence_view_type.__init__ = evidence_view_init
    evidence_view_type.authenticate_source_seal = evidence_source_authenticate
    evidence_view_type.authenticate_absence = evidence_absence_authenticate


_install_sealed_authority_runtime(
    kernel_type=_DockerHmacKernelV1,
    authority_base=_TypedEnvelopeAuthorityV1,
    pair_type=DockerStoragePathMappingPairHmacAuthorityV1,
    authenticator_type=FileHmacAuthenticator,
    kernel_pin_type=_KernelPinsV1,
    authority_pin_type=_AuthorityPinsV1,
    pair_pin_type=_PairPinsV1,
    command_view_type=DockerCommandBindingEnvelopeAuthorityViewV1,
    evidence_view_type=DockerEvidenceAuthorityViewV1,
    labels_type=DockerLabelsV1,
    command_content_type=DockerCommandBindingV1,
    effect_identity_type=DockerEffectIdentityV1,
    plan_type=PreparedDockerPlanV1,
    command_envelope_type=AuthenticatedDockerCommandBindingV1,
    storage_envelope_type=AuthenticatedDockerStorageMappingV1,
    wsl_envelope_type=AuthenticatedDockerWSLRootMappingV1,
    source_seal_envelope_type=AuthenticatedDockerSourceSealV1,
    absence_envelope_type=AuthenticatedDockerAbsenceV1,
    storage_content_type=DockerStorageMappingV1,
    wsl_content_type=DockerWSLRootMappingV1,
    verify_access_type=BundleMountVerifyAccessV1,
    pair_content_type=DockerStoragePathMappingPairV1,
    pair_envelope_type=AuthenticatedDockerStoragePathMappingPairV1,
    specifications=(
        (
            DockerSourceDeclarationHmacAuthorityV1,
            DockerSourceDeclarationV1,
            AuthenticatedDockerSourceDeclarationV1,
            "declaration_digest",
            "synaptic-host-docker-source-declaration-authority/v1",
        ),
        (
            DockerStageBundleRecordHmacAuthorityV1,
            DockerStageBundleBindingV1,
            AuthenticatedDockerStageBundleBindingV1,
            "record_digest",
            "synaptic-host-docker-stage-bundle-record-authority/v1",
        ),
        (
            DockerStorageMappingHmacAuthorityV1,
            DockerStorageMappingV1,
            AuthenticatedDockerStorageMappingV1,
            "mapping_digest",
            "synaptic-host-docker-storage-mapping-authority/v1",
        ),
        (
            DockerWSLRootMappingHmacAuthorityV1,
            DockerWSLRootMappingV1,
            AuthenticatedDockerWSLRootMappingV1,
            "mapping_digest",
            "synaptic-host-docker-wsl-root-mapping-authority/v1",
        ),
        (
            BundleBindingHmacAuthorityV1, BundleBindingV1,
            AuthenticatedBundleBindingV1, "binding_digest",
            "synaptic-host-docker-bundle-binding-authority/v1",
        ),
        (
            DockerSourceSealHmacAuthorityV1, DockerSourceSealContentV1,
            AuthenticatedDockerSourceSealV1, "content_digest",
            "synaptic-host-docker-source-seal-authority/v1",
        ),
        (
            DockerCreatePathBindingHmacAuthorityV1,
            DockerCreatePathBindingV1,
            AuthenticatedDockerCreatePathBindingV1,
            "binding_digest",
            "synaptic-host-docker-create-path-binding-authority/v1",
        ),
        (
            DockerWorkloadEnvironmentBindingHmacAuthorityV1,
            DockerWorkloadEnvironmentBindingV1,
            AuthenticatedDockerWorkloadEnvironmentBindingV1,
            "binding_digest",
            "synaptic-host-docker-workload-environment-binding-authority/v1",
        ),
        (
            DockerControlIntentHmacAuthorityV1, DockerControlIntentV1,
            AuthenticatedDockerControlIntentV1, "intent_digest",
            "synaptic-host-docker-control-intent-authority/v1",
        ),
        (
            DockerMutationRecordHmacAuthorityV1, DockerMutationRecordV1,
            AuthenticatedDockerMutationRecordV1, "record_digest",
            "synaptic-host-docker-mutation-record-authority/v1",
        ),
        (
            DockerAbsenceHmacAuthorityV1, DockerAbsenceContentV1,
            AuthenticatedDockerAbsenceV1, "content_digest",
            "synaptic-host-docker-absence-authority/v1",
        ),
        (
            DockerExpectedCreateBindingHmacAuthorityV1,
            DockerExpectedCreateBindingV1,
            AuthenticatedDockerExpectedCreateBindingV1,
            "binding_digest",
            "synaptic-host-docker-expected-create-binding-authority/v1",
        ),
        (
            DockerCommandBindingHmacAuthorityV1, DockerCommandBindingV1,
            AuthenticatedDockerCommandBindingV1, "binding_digest",
            "synaptic-host-docker-command-binding-authority/v1",
        ),
        (
            DockerStoragePathMappingPairHmacAuthorityV1,
            DockerStoragePathMappingPairV1,
            AuthenticatedDockerStoragePathMappingPairV1,
            "pair_digest",
            "synaptic-host-docker-storage-path-mapping-pair-authority/v1",
        ),
    ),
    storage_snapshotter=_storage_mapping_snapshot_v1,
    wsl_snapshotter=_wsl_mapping_snapshot_v1,
    profile_snapshotter=validated_profile_snapshot,
    enum_type=Enum,
    dataclass_fields=fields,
    dataclass_checker=is_dataclass,
    digest_builder=digest_v1,
    reference_checker=checked_ref_v1,
    failure_factory=_closed_failure,
    path_type=Path,
    authentication_failure_code=BundleIOCodeV1.AUTHENTICATION_FAILED,
)


__all__: tuple[str, ...] = ()
