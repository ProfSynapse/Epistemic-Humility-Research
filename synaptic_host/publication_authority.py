"""Host-owned evidence authority for provider-neutral artifact publication."""

from __future__ import annotations

from dataclasses import dataclass, replace
import re
from threading import RLock
from weakref import WeakKeyDictionary

from synaptic_tuner.api.v1 import ProjectContext
from synaptic_tuner.api.v1.publication import (
    AuthenticatedDestinationV1,
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


def create_publication_evidence_v1(
    context: ProjectContext,
) -> tuple[
    PublicationEvidenceVerifierV1,
    DestinationEvidenceIssuerV1,
    VerifiedSourceEvidenceIssuerV1,
]:
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
    return (
        PublicationEvidenceVerifierV1(_CONSTRUCTION_TOKEN, kernel),
        DestinationEvidenceIssuerV1(_CONSTRUCTION_TOKEN, kernel),
        VerifiedSourceEvidenceIssuerV1(_CONSTRUCTION_TOKEN, kernel),
    )


__all__ = [
    "DestinationEvidenceIssuerV1",
    "PublicationEvidenceVerifierV1",
    "VerifiedSourceEvidenceIssuerV1",
    "create_publication_evidence_v1",
]
