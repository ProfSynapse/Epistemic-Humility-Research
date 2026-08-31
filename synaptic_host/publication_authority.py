"""Host-owned evidence authority for provider-neutral artifact publication."""

from __future__ import annotations

from dataclasses import dataclass, replace
import re
from threading import RLock
from weakref import WeakKeyDictionary

from synaptic_tuner.api.v1 import ProjectContext
from synaptic_tuner.api.v1.publication import (
    AuthenticatedDestinationInventoryV1,
    AuthenticatedDestinationV1,
    AuthenticatedLookupV1,
    AuthenticatedPublicationReceiptV1,
    AuthenticatedPublicationTombstoneV1,
    AuthenticatedVerifiedSourceV1,
)

from .security import FileHmacAuthenticator


_AUTHORITY_REF = "host-publication-v1"
_KEY_REF = "publication-evidence-v1"
_TAG = re.compile(r"^[0-9a-f]{64}$")
_PURPOSES = frozenset({
    "publication-destination/v1",
    "publication-verified-source/v1",
    "publication-receipt/v1",
    "publication-destination-inventory/v1",
    "publication-lookup/v1",
    "publication-tombstone/v1",
})
_CONSTRUCTION_TOKEN = object()


def _weak_pin_accessors():
    pins = WeakKeyDictionary()
    lock = RLock()

    def register(owner: object, value: object) -> None:
        with lock:
            pins[owner] = value

    def get(owner: object) -> object | None:
        with lock:
            return pins.get(owner)

    return register, get


_register_kernel_pin, _get_kernel_pin = _weak_pin_accessors()
_register_view_pin, _get_view_pin = _weak_pin_accessors()
_register_issuer_pin, _get_issuer_pin = _weak_pin_accessors()


@dataclass(frozen=True, slots=True)
class _KernelPinsV1:
    authenticator: FileHmacAuthenticator
    key_path: object
    continuity_payload: bytes
    continuity_tag: bytes
    sign_identity: object
    verify_identity: object


@dataclass(frozen=True, slots=True)
class _ViewPinsV1:
    kernel: object


@dataclass(frozen=True, slots=True)
class _IssuerPinsV1:
    kernel: object
    leaf_type: type
    issue_identity: object
    envelope_type: type
    purpose: str
    reconstruct: object
    kernel_issue: object
    kernel_verify: object
    kernel_issue_identity: object
    kernel_verify_identity: object


def _exact_text(value: object, name: str) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be nonempty exact text")
    return value


class _PublicationEvidenceKernelV1:
    __slots__ = (
        "_authenticator", "_key_path", "_continuity_payload", "_continuity_tag",
        "_sign_identity", "_verify_identity", "__weakref__",
    )

    def __init__(self, authenticator: FileHmacAuthenticator) -> None:
        if type(authenticator) is not FileHmacAuthenticator:
            raise TypeError("exact FileHmacAuthenticator is required")
        if authenticator.key_ref != _KEY_REF:
            raise ValueError("publication evidence key reference mismatch")
        self._authenticator = authenticator
        self._key_path = authenticator.key_path
        self._continuity_payload = b"synaptic-publication-evidence-key-continuity/v1"
        self._continuity_tag = authenticator.sign(
            "publication-authority-continuity/v1",
            self._continuity_payload,
            _KEY_REF,
        )
        self._sign_identity = authenticator.sign
        self._verify_identity = authenticator.verify
        self._register_pins(_KernelPinsV1(
            authenticator,
            self._key_path,
            self._continuity_payload,
            self._continuity_tag,
            self._sign_identity,
            self._verify_identity,
        ))

    def _register_pins(
        self, pins: _KernelPinsV1, _register=_register_kernel_pin
    ) -> None:
        _register(self, pins)

    def _intact(self, _get=_get_kernel_pin) -> bool:
        try:
            pins = _get(self)
            return (
                type(pins) is _KernelPinsV1
                and self._authenticator is pins.authenticator
                and type(self._authenticator) is FileHmacAuthenticator
                and self._authenticator.key_ref == _KEY_REF
                and self._key_path == pins.key_path
                and self._authenticator.key_path == pins.key_path
                and self._continuity_payload == pins.continuity_payload
                and self._continuity_tag == pins.continuity_tag
                and self._sign_identity == pins.sign_identity
                and self._verify_identity == pins.verify_identity
                and self._authenticator.sign == pins.sign_identity
                and self._authenticator.verify == pins.verify_identity
                and self._authenticator.verify(
                    "publication-authority-continuity/v1",
                    pins.continuity_payload,
                    pins.continuity_tag,
                    _KEY_REF,
                )
                is True
            )
        except BaseException:
            return False

    def issue(self, purpose: str, payload: bytes) -> str:
        purpose = _exact_text(purpose, "purpose")
        if purpose not in _PURPOSES or type(payload) is not bytes or not self._intact():
            raise ValueError("publication evidence request is invalid")
        tag = self._authenticator.sign(purpose, payload, _KEY_REF).hex()
        if _TAG.fullmatch(tag) is None:
            raise ValueError("publication evidence issuance failed")
        return tag

    def verify(self, purpose: str, payload: bytes, tag: str, key_ref: str) -> bool:
        try:
            return (
                type(purpose) is str
                and purpose in _PURPOSES
                and type(payload) is bytes
                and type(tag) is str
                and _TAG.fullmatch(tag) is not None
                and type(key_ref) is str
                and key_ref == _KEY_REF
                and self._intact()
                and self._authenticator.verify(
                    purpose, payload, bytes.fromhex(tag), key_ref
                )
                is True
            )
        except BaseException:
            return False


class PublicationEvidenceVerifierV1:
    """The sole public generic evidence surface required by the engine."""

    __slots__ = ("authority_ref", "key_ref", "_kernel", "__weakref__")

    def __init__(self, token: object, kernel: _PublicationEvidenceKernelV1) -> None:
        if token is not _CONSTRUCTION_TOKEN or type(kernel) is not _PublicationEvidenceKernelV1:
            raise TypeError("publication verifier must be factory-created")
        self.authority_ref = _AUTHORITY_REF
        self.key_ref = _KEY_REF
        self._kernel = kernel
        self._register_pins(_ViewPinsV1(kernel))

    def _register_pins(self, pins: _ViewPinsV1, _register=_register_view_pin) -> None:
        _register(self, pins)

    def _intact(self, _get=_get_view_pin) -> bool:
        pins = _get(self)
        return type(pins) is _ViewPinsV1 and self._kernel is pins.kernel

    def verify(self, purpose: str, payload: bytes, tag: str, key_ref: str) -> bool:
        if (
            self.authority_ref != _AUTHORITY_REF
            or self.key_ref != _KEY_REF
            or type(self._kernel) is not _PublicationEvidenceKernelV1
            or not self._intact()
        ):
            return False
        return self._kernel.verify(purpose, payload, tag, key_ref)


class DestinationEvidenceIssuerV1:
    __slots__ = ("authority_ref", "key_ref", "_kernel", "__weakref__")

    def __init__(self, token: object, kernel: _PublicationEvidenceKernelV1) -> None:
        if token is not _CONSTRUCTION_TOKEN or type(kernel) is not _PublicationEvidenceKernelV1:
            raise TypeError("destination issuer must be factory-created")
        self.authority_ref = _AUTHORITY_REF
        self.key_ref = _KEY_REF
        self._kernel = kernel
        self._register_pins(_ViewPinsV1(kernel))

    def _register_pins(self, pins: _ViewPinsV1, _register=_register_view_pin) -> None:
        _register(self, pins)

    def _intact(self, _get=_get_view_pin) -> bool:
        pins = _get(self)
        return type(pins) is _ViewPinsV1 and self._kernel is pins.kernel

    def issue(self, value: AuthenticatedDestinationV1) -> AuthenticatedDestinationV1:
        if type(value) is not AuthenticatedDestinationV1:
            raise TypeError("exact destination descriptor is required")
        baseline = replace(value)
        if (
            baseline.authority_ref != self.authority_ref
            or baseline.key_ref != self.key_ref
            or type(self._kernel) is not _PublicationEvidenceKernelV1
            or not self._intact()
        ):
            raise ValueError("destination authority binding is invalid")
        issued = replace(
            baseline,
            tag=self._kernel.issue("publication-destination/v1", baseline.payload),
        )
        if replace(value) != baseline:
            raise ValueError("destination descriptor changed during issuance")
        return issued


class VerifiedSourceEvidenceIssuerV1:
    __slots__ = ("authority_ref", "key_ref", "_kernel", "__weakref__")

    def __init__(self, token: object, kernel: _PublicationEvidenceKernelV1) -> None:
        if token is not _CONSTRUCTION_TOKEN or type(kernel) is not _PublicationEvidenceKernelV1:
            raise TypeError("source issuer must be factory-created")
        self.authority_ref = _AUTHORITY_REF
        self.key_ref = _KEY_REF
        self._kernel = kernel
        self._register_pins(_ViewPinsV1(kernel))

    def _register_pins(self, pins: _ViewPinsV1, _register=_register_view_pin) -> None:
        _register(self, pins)

    def _intact(self, _get=_get_view_pin) -> bool:
        pins = _get(self)
        return type(pins) is _ViewPinsV1 and self._kernel is pins.kernel

    def issue(self, value: AuthenticatedVerifiedSourceV1) -> AuthenticatedVerifiedSourceV1:
        if type(value) is not AuthenticatedVerifiedSourceV1:
            raise TypeError("exact verified source descriptor is required")
        baseline = replace(value)
        if (
            baseline.authority_ref != self.authority_ref
            or baseline.key_ref != self.key_ref
            or type(self._kernel) is not _PublicationEvidenceKernelV1
            or not self._intact()
        ):
            raise ValueError("verified source authority binding is invalid")
        issued = replace(
            baseline,
            tag=self._kernel.issue("publication-verified-source/v1", baseline.payload),
        )
        if replace(value) != baseline:
            raise ValueError("verified source descriptor changed during issuance")
        return issued


def _sealed_type_contract():
    sealed: set[type] = set()

    class SealedType(type):
        def __setattr__(cls, name: str, value: object) -> None:
            if cls in sealed:
                raise TypeError("sealed publication evidence type cannot be modified")
            super().__setattr__(name, value)

        def __delattr__(cls, name: str) -> None:
            if cls in sealed:
                raise TypeError("sealed publication evidence type cannot be modified")
            super().__delattr__(name)

    def seal(*values: type) -> None:
        sealed.update(values)

    return SealedType, seal


_SealedIssuerType, _seal_issuer_types = _sealed_type_contract()


class _TypedPublicationEvidenceIssuerV1(metaclass=_SealedIssuerType):
    __slots__ = ("authority_ref", "key_ref", "_kernel", "__weakref__")

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("publication evidence issuer must be factory-created")


def _canonical_reconstructor(envelope_type: type):
    def reconstruct(value: object) -> object:
        return envelope_type.from_canonical_bytes(value.canonical_bytes)

    return reconstruct


def _replace_reconstructor(envelope_type: type):
    def reconstruct(value: object) -> object:
        result = replace(value)
        if type(result) is not envelope_type:
            raise ValueError("publication evidence reconstruction failed")
        return result

    return reconstruct


def _typed_issue(envelope_type: type, purpose: str, reconstruct: object):
    get_pin = _get_issuer_pin
    kernel_type = _PublicationEvidenceKernelV1
    pins_type = _IssuerPinsV1
    authority_ref = _AUTHORITY_REF
    key_ref = _KEY_REF

    def issue(self: object, value: object) -> object:
        if type(value) is not envelope_type:
            raise TypeError("exact publication evidence envelope is required")
        pins = get_pin(self)
        if (
            type(pins) is not pins_type
            or type(self) is not pins.leaf_type
            or pins.envelope_type is not envelope_type
            or pins.purpose != purpose
            or pins.reconstruct is not reconstruct
            or pins.leaf_type.__dict__.get("issue") is not pins.issue_identity
            or kernel_type.__dict__.get("issue") is not pins.kernel_issue_identity
            or kernel_type.__dict__.get("verify") is not pins.kernel_verify_identity
            or self.authority_ref != authority_ref
            or self.key_ref != key_ref
            or self._kernel is not pins.kernel
            or type(pins.kernel) is not kernel_type
        ):
            raise ValueError("publication evidence issuer integrity is invalid")
        baseline = replace(value)
        if baseline.authority_ref != authority_ref or baseline.key_ref != key_ref:
            raise ValueError("publication evidence authority binding is invalid")
        try:
            issued = replace(
                baseline, tag=pins.kernel_issue(purpose, baseline.payload)
            )
            if replace(value) != baseline:
                raise ValueError("publication evidence envelope changed during issuance")
            if not pins.kernel_verify(purpose, issued.payload, issued.tag, issued.key_ref):
                raise ValueError("publication evidence authentication failed")
            result = reconstruct(issued)
            if (
                type(result) is not envelope_type
                or result != issued
                or not pins.kernel_verify(
                    purpose, result.payload, result.tag, result.key_ref
                )
            ):
                raise ValueError("publication evidence reconstruction failed")
            return result
        except (KeyboardInterrupt, SystemExit):
            raise
        except ValueError:
            raise
        except BaseException:
            raise ValueError("publication evidence issuance failed") from None

    return issue


def _new_typed_issuer(
    leaf_type: type,
    kernel: _PublicationEvidenceKernelV1,
    envelope_type: type,
    purpose: str,
    reconstruct: object,
) -> object:
    value = object.__new__(leaf_type)
    object.__setattr__(value, "authority_ref", _AUTHORITY_REF)
    object.__setattr__(value, "key_ref", _KEY_REF)
    object.__setattr__(value, "_kernel", kernel)
    issue_identity = leaf_type.__dict__.get("issue")
    _register_issuer_pin(value, _IssuerPinsV1(
        kernel, leaf_type, issue_identity, envelope_type, purpose, reconstruct,
        kernel.issue, kernel.verify,
        _PublicationEvidenceKernelV1.__dict__["issue"],
        _PublicationEvidenceKernelV1.__dict__["verify"],
    ))
    return value


_INVENTORY_RECONSTRUCT = _canonical_reconstructor(AuthenticatedDestinationInventoryV1)
_RECEIPT_RECONSTRUCT = _canonical_reconstructor(AuthenticatedPublicationReceiptV1)
_LOOKUP_RECONSTRUCT = _replace_reconstructor(AuthenticatedLookupV1)
_TOMBSTONE_RECONSTRUCT = _canonical_reconstructor(AuthenticatedPublicationTombstoneV1)


class DestinationInventoryEvidenceIssuerV1(_TypedPublicationEvidenceIssuerV1):
    __slots__ = ()
    issue = _typed_issue(
        AuthenticatedDestinationInventoryV1,
        "publication-destination-inventory/v1",
        _INVENTORY_RECONSTRUCT,
    )


class PublicationReceiptEvidenceIssuerV1(_TypedPublicationEvidenceIssuerV1):
    __slots__ = ()
    issue = _typed_issue(
        AuthenticatedPublicationReceiptV1,
        "publication-receipt/v1",
        _RECEIPT_RECONSTRUCT,
    )


class PublicationLookupEvidenceIssuerV1(_TypedPublicationEvidenceIssuerV1):
    __slots__ = ()
    issue = _typed_issue(
        AuthenticatedLookupV1, "publication-lookup/v1", _LOOKUP_RECONSTRUCT
    )


class PublicationTombstoneEvidenceIssuerV1(_TypedPublicationEvidenceIssuerV1):
    __slots__ = ()
    issue = _typed_issue(
        AuthenticatedPublicationTombstoneV1,
        "publication-tombstone/v1",
        _TOMBSTONE_RECONSTRUCT,
    )


_seal_issuer_types(
    _TypedPublicationEvidenceIssuerV1,
    DestinationInventoryEvidenceIssuerV1,
    PublicationReceiptEvidenceIssuerV1,
    PublicationLookupEvidenceIssuerV1,
    PublicationTombstoneEvidenceIssuerV1,
)


@dataclass(frozen=True, slots=True)
class _AuthorityPinsV1:
    seal: object
    members: tuple[object, ...]
    descriptors: tuple[object, ...]


def _authority_contract():
    pins = WeakKeyDictionary()
    lock = RLock()
    member_names = (
        "verifier", "destinations", "verified_sources", "destination_inventories",
        "receipts", "lookups", "tombstones",
    )
    expected_types = (
        PublicationEvidenceVerifierV1,
        DestinationEvidenceIssuerV1,
        VerifiedSourceEvidenceIssuerV1,
        DestinationInventoryEvidenceIssuerV1,
        PublicationReceiptEvidenceIssuerV1,
        PublicationLookupEvidenceIssuerV1,
        PublicationTombstoneEvidenceIssuerV1,
    )
    get_view_pin = _get_view_pin
    get_issuer_pin = _get_issuer_pin
    view_pins_type = _ViewPinsV1
    issuer_pins_type = _IssuerPinsV1
    authority_ref = _AUTHORITY_REF
    key_ref = _KEY_REF

    def members(owner: object) -> tuple[object, ...]:
        with lock:
            value = pins.get(owner)
        if (
            type(value) is not _AuthorityPinsV1
            or type(owner) is not PublicationEvidenceAuthorityV1
            or owner._seal is not value.seal
            or tuple(PublicationEvidenceAuthorityV1.__dict__.get(name) for name in member_names)
            != value.descriptors
        ):
            raise ValueError("publication evidence authority integrity is invalid")
        return value.members

    def member(index: int):
        def get(owner: object) -> object:
            return members(owner)[index]
        return property(get)

    class PublicationEvidenceAuthorityV1(metaclass=_SealedIssuerType):
        __slots__ = ("_seal", "__weakref__")

        verifier = member(0)
        destinations = member(1)
        verified_sources = member(2)
        destination_inventories = member(3)
        receipts = member(4)
        lookups = member(5)
        tombstones = member(6)

        def __init__(self, *args: object, **kwargs: object) -> None:
            raise TypeError("publication evidence authority must be factory-created")

    PublicationEvidenceAuthorityV1.__name__ = "PublicationEvidenceAuthorityV1"
    PublicationEvidenceAuthorityV1.__qualname__ = "PublicationEvidenceAuthorityV1"
    _seal_issuer_types(PublicationEvidenceAuthorityV1)

    def create(values: tuple[object, ...]) -> PublicationEvidenceAuthorityV1:
        if (
            type(values) is not tuple
            or tuple(type(value) for value in values) != expected_types
        ):
            raise TypeError("exact publication evidence authority members are required")
        kernel = values[0]._kernel
        view_values = values[:3]
        typed_values = values[3:]
        if any(
            type(pin := get_view_pin(value)) is not view_pins_type
            or pin.kernel is not kernel
            or value._kernel is not kernel
            or value.authority_ref != authority_ref
            or value.key_ref != key_ref
            for value in view_values
        ) or any(
            type(pin := get_issuer_pin(value)) is not issuer_pins_type
            or pin.kernel is not kernel
            or value._kernel is not kernel
            or value.authority_ref != authority_ref
            or value.key_ref != key_ref
            for value in typed_values
        ):
            raise ValueError("publication evidence authority members are invalid")
        value = object.__new__(PublicationEvidenceAuthorityV1)
        seal = object()
        object.__setattr__(value, "_seal", seal)
        descriptors = tuple(
            PublicationEvidenceAuthorityV1.__dict__[name] for name in member_names
        )
        with lock:
            pins[value] = _AuthorityPinsV1(seal, values, descriptors)
        return value

    return PublicationEvidenceAuthorityV1, create


PublicationEvidenceAuthorityV1, _create_publication_authority = _authority_contract()


def create_publication_evidence_v1(
    context: ProjectContext,
) -> PublicationEvidenceAuthorityV1:
    if type(context) is not ProjectContext or context.mode != "host":
        raise ValueError("exact host project context is required")
    state_root = context.state_root.resolve(strict=False)
    mutable_root = (context.project_root / ".synaptic").resolve(strict=False)
    if not state_root.is_relative_to(mutable_root):
        raise ValueError("publication evidence must use project-owned mutable state")
    authenticator = FileHmacAuthenticator(
        state_root / "publication" / "evidence-hmac.key", key_ref=_KEY_REF
    )
    authenticator.initialize()
    kernel = _PublicationEvidenceKernelV1(authenticator)
    return _create_publication_authority((
        PublicationEvidenceVerifierV1(_CONSTRUCTION_TOKEN, kernel),
        DestinationEvidenceIssuerV1(_CONSTRUCTION_TOKEN, kernel),
        VerifiedSourceEvidenceIssuerV1(_CONSTRUCTION_TOKEN, kernel),
        _new_typed_issuer(
            DestinationInventoryEvidenceIssuerV1, kernel,
            AuthenticatedDestinationInventoryV1,
            "publication-destination-inventory/v1", _INVENTORY_RECONSTRUCT,
        ),
        _new_typed_issuer(
            PublicationReceiptEvidenceIssuerV1, kernel,
            AuthenticatedPublicationReceiptV1,
            "publication-receipt/v1", _RECEIPT_RECONSTRUCT,
        ),
        _new_typed_issuer(
            PublicationLookupEvidenceIssuerV1, kernel, AuthenticatedLookupV1,
            "publication-lookup/v1", _LOOKUP_RECONSTRUCT,
        ),
        _new_typed_issuer(
            PublicationTombstoneEvidenceIssuerV1, kernel,
            AuthenticatedPublicationTombstoneV1,
            "publication-tombstone/v1", _TOMBSTONE_RECONSTRUCT,
        ),
    ))


__all__ = [
    "DestinationEvidenceIssuerV1",
    "DestinationInventoryEvidenceIssuerV1",
    "PublicationEvidenceAuthorityV1",
    "PublicationEvidenceVerifierV1",
    "PublicationLookupEvidenceIssuerV1",
    "PublicationReceiptEvidenceIssuerV1",
    "PublicationTombstoneEvidenceIssuerV1",
    "VerifiedSourceEvidenceIssuerV1",
    "create_publication_evidence_v1",
]
