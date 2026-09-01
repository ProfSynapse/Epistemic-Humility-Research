"""Closed destination configuration and immutable publication registry."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import re
from threading import RLock
from types import FunctionType, MethodType
import unicodedata
from weakref import WeakKeyDictionary

from synaptic_tuner.api.v1.publication import AuthenticatedDestinationV1

from .publication_authority import (
    DestinationEvidenceIssuerV1,
    PublicationEvidenceVerifierV1,
)


_CONFIG_SCHEMA = "synaptic-host-artifact-destinations/v1"
_DESTINATION_SCHEMA = "synaptic-host-artifact-destination/v1"
_ENGINE_SCHEMA = "synaptic-publication-destination/v1"
_ZERO = "0" * 64
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_CONFIG_BYTES = 1_048_576
_MAX_DESTINATIONS = 100
_MAX_AUTHORITY_BINDINGS = 32
_MAX_DEPTH = 16
_BANNED_KEYS = frozenset({
    "access_key", "access_token", "api_key", "credential", "credentials",
    "password", "private_key", "secret", "token",
})
_BANNED_SUFFIXES = ("_access_key", "_api_key", "_password", "_private_key", "_secret", "_token")
_BANNED_COMPACT = frozenset({
    "accesskey", "accesstoken", "apikey", "credential", "credentials",
    "password", "privatekey", "secret", "token",
})
_BANNED_COMPACT_SUFFIXES = ("accesskey", "accesstoken", "apikey", "password", "privatekey", "secret", "token")


def _text(value: object, name: str, maximum: int = 256) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be nonempty exact text")
    if len(value.encode("utf-8")) > maximum:
        raise ValueError(f"{name} exceeds {maximum} UTF-8 bytes")
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ValueError(f"{name} contains prohibited characters")
    return value


def _fields(value: object, expected: frozenset[str], name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise TypeError(f"{name} must be an exact object")
    keys = tuple(dict.keys(value))
    if any(type(key) is not str for key in keys) or frozenset(keys) != expected:
        raise ValueError(f"{name} fields are invalid")
    return {key: dict.__getitem__(value, key) for key in keys}


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise ValueError("destination configuration has duplicate or invalid fields")
        result[key] = value
    return result


def _configuration(value: object, *, depth: int = 0) -> object:
    if depth > _MAX_DEPTH:
        raise ValueError("destination configuration is too deeply nested")
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        return _text(value, "configuration text", 4096)
    if type(value) is list:
        return [_configuration(item, depth=depth + 1) for item in value]
    if type(value) is dict:
        result = {}
        for key in sorted(dict.keys(value)):
            key = _text(key, "configuration field")
            normalized = key.casefold().replace("-", "_")
            compact = "".join(character for character in normalized if character != "_")
            if (
                normalized in _BANNED_KEYS
                or normalized.endswith(_BANNED_SUFFIXES)
                or compact in _BANNED_COMPACT
                or compact.endswith(_BANNED_COMPACT_SUFFIXES)
            ):
                raise ValueError("credentials and secrets are prohibited in destination configuration")
            result[key] = _configuration(dict.__getitem__(value, key), depth=depth + 1)
        return result
    raise TypeError("destination configuration contains an unsupported value")


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def artifact_destination_declaration_digest_v1(
    declaration: "ArtifactDestinationDeclarationV1",
) -> str:
    declaration = _snapshot_declaration(declaration)
    return hashlib.sha256(
        b"synaptic-destination-declaration/v1\0" + _canonical({
            "destination_ref": declaration.destination_ref,
            "display_name": declaration.display_name,
            "adapter_ref": declaration.adapter_ref,
            "configuration_schema_version": declaration.configuration_schema_version,
            "configuration_digest": declaration.configuration_digest,
            "policy_digest": declaration.policy.policy_digest,
        })
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class ArtifactDestinationPolicyV1:
    maximum_artifact_bytes: int
    maximum_total_bytes: int

    def __post_init__(self) -> None:
        for name in ("maximum_artifact_bytes", "maximum_total_bytes"):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 2**63 - 1:
                raise ValueError(f"{name} is invalid")
        if self.maximum_artifact_bytes > self.maximum_total_bytes:
            raise ValueError("destination byte limits are invalid")

    @property
    def policy_digest(self) -> str:
        return _sha({
            "maximum_artifact_bytes": self.maximum_artifact_bytes,
            "maximum_total_bytes": self.maximum_total_bytes,
        })


@dataclass(frozen=True, slots=True)
class ArtifactDestinationDeclarationV1:
    destination_ref: str
    display_name: str
    adapter_ref: str
    configuration_schema_version: str
    configuration_bytes: bytes
    policy: ArtifactDestinationPolicyV1

    def __post_init__(self) -> None:
        _text(self.destination_ref, "destination_ref")
        _text(self.display_name, "display_name")
        _text(self.adapter_ref, "adapter_ref")
        _text(self.configuration_schema_version, "configuration schema version")
        if type(self.configuration_bytes) is not bytes or not self.configuration_bytes:
            raise TypeError("canonical configuration bytes are required")
        if type(self.policy) is not ArtifactDestinationPolicyV1:
            raise TypeError("exact destination policy is required")
        try:
            parsed = json.loads(self.configuration_bytes.decode("utf-8"), object_pairs_hook=_pairs)
        except Exception:
            raise ValueError("canonical destination configuration is invalid") from None
        normalized = _configuration(parsed)
        if type(normalized) is not dict or _canonical(normalized) != self.configuration_bytes:
            raise ValueError("destination configuration bytes are not canonical")
        if normalized.get("schema_version") != self.configuration_schema_version:
            raise ValueError("destination configuration schema is not bound")

    @property
    def configuration_digest(self) -> str:
        parsed = json.loads(self.configuration_bytes.decode("utf-8"), object_pairs_hook=_pairs)
        return _sha({"adapter_ref": self.adapter_ref, "configuration": parsed})


@dataclass(frozen=True, slots=True)
class ArtifactDestinationConfigV1:
    destinations: tuple[ArtifactDestinationDeclarationV1, ...]

    def __post_init__(self) -> None:
        if (
            type(self.destinations) is not tuple
            or not self.destinations
            or len(self.destinations) > _MAX_DESTINATIONS
            or any(type(item) is not ArtifactDestinationDeclarationV1 for item in self.destinations)
        ):
            raise ValueError("destinations must contain 1 through 100 exact declarations")
        refs = tuple(item.destination_ref for item in self.destinations)
        if refs != tuple(sorted(refs)) or len(refs) != len(set(refs)):
            raise ValueError("destination references must be unique and ascending")


@dataclass(frozen=True, slots=True)
class DestinationAdapterRegistrationV1:
    adapter_ref: str
    configuration_schema_version: str
    adapter_type: type
    factory: FunctionType

    def __post_init__(self) -> None:
        _text(self.adapter_ref, "adapter_ref")
        _text(self.configuration_schema_version, "configuration schema version")
        if type(self.adapter_type) is not type or type(self.factory) is not FunctionType:
            raise TypeError("adapter type and exact function factory are required")


@dataclass(frozen=True, slots=True)
class DestinationAdapterInstallationV1:
    """Provider-neutral registration plus its terminal owned cleanup."""

    registration: DestinationAdapterRegistrationV1
    cleanup: FunctionType

    def __post_init__(self) -> None:
        if type(self.registration) is not DestinationAdapterRegistrationV1:
            raise TypeError("exact adapter registration is required")
        if type(self.cleanup) is not FunctionType:
            raise TypeError("exact adapter cleanup function is required")

    def cleanup_owned(self) -> bool:
        result = self.cleanup()
        if type(result) is not bool:
            raise TypeError("adapter cleanup must return an exact boolean")
        return result


@dataclass(frozen=True, slots=True)
class ResolvedDestinationAdapterV1:
    adapter: object
    authority_bindings: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if self.adapter is None or type(self.authority_bindings) is not tuple:
            raise ValueError("resolved destination adapter binding is invalid")
        refs = []
        for item in self.authority_bindings:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
                or _DIGEST.fullmatch(item[1]) is None
            ):
                raise ValueError("resolved destination adapter binding is invalid")
            refs.append(_text(item[0], "resolved authority role"))
        if not refs or tuple(refs) != tuple(sorted(refs)) or len(refs) != len(set(refs)):
            raise ValueError("resolved destination authority bindings must be unique and ascending")

def _snapshot_policy(value: ArtifactDestinationPolicyV1) -> ArtifactDestinationPolicyV1:
    if type(value) is not ArtifactDestinationPolicyV1:
        raise TypeError("exact destination policy is required")
    return ArtifactDestinationPolicyV1(
        value.maximum_artifact_bytes, value.maximum_total_bytes
    )


def _snapshot_declaration(
    value: ArtifactDestinationDeclarationV1,
) -> ArtifactDestinationDeclarationV1:
    if type(value) is not ArtifactDestinationDeclarationV1:
        raise TypeError("exact destination declaration is required")
    return ArtifactDestinationDeclarationV1(
        value.destination_ref,
        value.display_name,
        value.adapter_ref,
        value.configuration_schema_version,
        bytes(value.configuration_bytes),
        _snapshot_policy(value.policy),
    )


def _snapshot_registration(
    value: DestinationAdapterRegistrationV1,
) -> DestinationAdapterRegistrationV1:
    if type(value) is not DestinationAdapterRegistrationV1:
        raise TypeError("exact adapter registration is required")
    return DestinationAdapterRegistrationV1(
        value.adapter_ref,
        value.configuration_schema_version,
        value.adapter_type,
        value.factory,
    )


def _discover_adapter_callbacks(adapter: object) -> tuple[object, object, object]:
    try:
        callbacks = tuple(
            getattr(adapter, name)
            for name in ("publish_once", "lookup", "iter_bytes")
        )
    except BaseException:
        pass
    else:
        if all(callable(callback) for callback in callbacks):
            return callbacks  # type: ignore[return-value]
        raise TypeError("destination adapter is incomplete")
    raise ValueError("destination adapter callback access failed") from None


def _same_adapter_callback(current: object, pinned: object) -> bool:
    if type(current) is MethodType and type(pinned) is MethodType:
        return current.__self__ is pinned.__self__ and current.__func__ is pinned.__func__
    return current is pinned


def _reconstruct_resolved_binding(
    result: object,
    _binding_type=ResolvedDestinationAdapterV1,
    _digest_pattern=_DIGEST,
    _text_check=_text,
    _binding_limit=_MAX_AUTHORITY_BINDINGS,
) -> tuple[object, tuple[tuple[str, str], ...]]:
    if type(result) is not _binding_type:
        raise TypeError("destination adapter factory returned an invalid binding")
    invalid = False
    snapshot_values: list[tuple[str, str]] = []
    try:
        adapter = object.__getattribute__(result, "adapter")
        bindings = object.__getattribute__(result, "authority_bindings")
        if (
            type(bindings) is not tuple
            or not bindings
            or len(bindings) > _binding_limit
        ):
            raise ValueError
        for item in bindings:
            if (
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not str
                or _digest_pattern.fullmatch(item[1]) is None
            ):
                raise ValueError
            role = _text_check(item[0], "resolved authority role", 256)
            snapshot_values.append((role, str(item[1])))
    except BaseException:
        invalid = True
        adapter = None
    if invalid:
        raise ValueError("resolved destination adapter binding is invalid") from None
    snapshot = tuple(snapshot_values)
    roles = tuple(item[0] for item in snapshot)
    if roles != tuple(sorted(roles)) or len(roles) != len(set(roles)):
        raise ValueError("resolved destination adapter binding is invalid")
    return adapter, snapshot


def _construct_adapter(
    factory: FunctionType,
    configuration: bytes,
    declared_configuration_digest: str,
    _digest_pattern=_DIGEST,
    _digest=_sha,
    _callback_probe=_discover_adapter_callbacks,
    _binding_snapshot=_reconstruct_resolved_binding,
) -> tuple[object, str, tuple[object, object, object]]:
    try:
        result = factory(configuration)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        pass
    else:
        if (
            type(declared_configuration_digest) is not str
            or _digest_pattern.fullmatch(declared_configuration_digest) is None
        ):
            raise ValueError("resolved destination adapter binding is invalid")
        adapter, snapshot = _binding_snapshot(result)
        callbacks = _callback_probe(adapter)
        post_failed = False
        try:
            post_adapter, post_snapshot = _binding_snapshot(result)
        except BaseException:
            post_failed = True
            post_adapter, post_snapshot = None, ()
        if post_failed or post_adapter is not adapter or post_snapshot != snapshot:
            raise ValueError("resolved destination adapter binding changed")
        return adapter, _digest({
            "declared_configuration_digest": declared_configuration_digest,
            "resolved_authorities": [
                {"role": role, "authority_digest": digest}
                for role, digest in snapshot
            ],
        }), callbacks
    raise ValueError("destination adapter construction failed") from None


def parse_artifact_destination_config_v1(raw: bytes) -> ArtifactDestinationConfigV1:
    """Parse an immutable destination registry snapshot."""

    if type(raw) is not bytes:
        raise TypeError("destination configuration bytes are required")
    if not raw or len(raw) > _MAX_CONFIG_BYTES:
        raise ValueError("destination configuration size is invalid")
    try:
        root = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except Exception:
        raise ValueError("destination configuration JSON is invalid") from None
    root = _fields(root, frozenset({"schema_version", "destinations"}), "destination registry")
    if root["schema_version"] != _CONFIG_SCHEMA or type(root["destinations"]) is not list:
        raise ValueError("destination registry schema is invalid")
    declarations = []
    for raw_destination in root["destinations"]:
        value = _fields(
            raw_destination,
            frozenset({"schema_version", "destination_ref", "display_name", "adapter_ref", "configuration", "policy"}),
            "destination",
        )
        if value["schema_version"] != _DESTINATION_SCHEMA:
            raise ValueError("destination schema is invalid")
        config = _configuration(value["configuration"])
        if type(config) is not dict:
            raise TypeError("destination configuration must be an exact object")
        schema = _text(config.get("schema_version"), "configuration schema version")
        policy_fields = _fields(
            value["policy"],
            frozenset({"maximum_artifact_bytes", "maximum_total_bytes"}),
            "destination policy",
        )
        declarations.append(ArtifactDestinationDeclarationV1(
            _text(value["destination_ref"], "destination_ref"),
            _text(value["display_name"], "display_name"),
            _text(value["adapter_ref"], "adapter_ref"),
            schema,
            _canonical(config),
            ArtifactDestinationPolicyV1(
                policy_fields["maximum_artifact_bytes"],  # type: ignore[arg-type]
                policy_fields["maximum_total_bytes"],  # type: ignore[arg-type]
            ),
        ))
    return ArtifactDestinationConfigV1(tuple(declarations))


def load_artifact_destination_config_v1(path: Path) -> ArtifactDestinationConfigV1:
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError("absolute destination configuration path is required")
    return parse_artifact_destination_config_v1(path.read_bytes())


@dataclass(frozen=True, slots=True)
class _BoundDestinationV1:
    declaration: ArtifactDestinationDeclarationV1
    descriptor: AuthenticatedDestinationV1
    adapter: object
    adapter_type: type
    resolved_configuration_digest: str
    publish_once: object
    lookup: object
    iter_bytes: object


@dataclass(frozen=True, slots=True)
class _RegistryPinsV1:
    bindings: tuple[_BoundDestinationV1, ...]
    registrations: tuple[DestinationAdapterRegistrationV1, ...]
    issuer: DestinationEvidenceIssuerV1
    verifier: PublicationEvidenceVerifierV1
    binding_baselines: tuple[tuple[object, ...], ...]
    callback_probe: object
    callback_match: object


def _registry_pin_accessors():
    pins = WeakKeyDictionary()
    lock = RLock()

    def register(owner: object, value: _RegistryPinsV1) -> None:
        with lock:
            pins[owner] = value

    def get(owner: object) -> object | None:
        with lock:
            return pins.get(owner)

    return register, get


_register_registry_pin, _get_registry_pin = _registry_pin_accessors()


class ImmutableArtifactDestinationRegistryV1:
    __slots__ = (
        "_bindings", "_registrations", "_issuer", "_verifier",
        "_issuer_issue", "_verifier_verify", "__weakref__",
    )

    def __init__(
        self,
        *,
        config: ArtifactDestinationConfigV1,
        registrations: tuple[DestinationAdapterRegistrationV1, ...],
        issuer: DestinationEvidenceIssuerV1,
        verifier: PublicationEvidenceVerifierV1,
    ) -> None:
        if type(config) is not ArtifactDestinationConfigV1:
            raise TypeError("exact destination configuration is required")
        if (
            type(registrations) is not tuple
            or not registrations
            or any(type(item) is not DestinationAdapterRegistrationV1 for item in registrations)
        ):
            raise TypeError("exact immutable adapter registrations are required")
        refs = tuple(item.adapter_ref for item in registrations)
        if refs != tuple(sorted(refs)) or len(refs) != len(set(refs)):
            raise ValueError("adapter registrations must be unique and ascending")
        if type(issuer) is not DestinationEvidenceIssuerV1 or type(verifier) is not PublicationEvidenceVerifierV1:
            raise TypeError("exact publication evidence boundaries are required")
        if (issuer.authority_ref, issuer.key_ref) != (verifier.authority_ref, verifier.key_ref):
            raise ValueError("publication evidence boundaries do not match")
        registration_baselines = tuple(_snapshot_registration(item) for item in registrations)
        self._registrations = registration_baselines
        self._issuer = issuer
        self._verifier = verifier
        self._issuer_issue = issuer.issue
        self._verifier_verify = verifier.verify
        callback_probe = _discover_adapter_callbacks
        callback_match = _same_adapter_callback
        by_ref = {item.adapter_ref: item for item in registration_baselines}
        bindings = []
        for supplied_declaration in config.destinations:
            declaration = _snapshot_declaration(supplied_declaration)
            registration = by_ref.get(declaration.adapter_ref)
            if registration is None or registration.configuration_schema_version != declaration.configuration_schema_version:
                raise ValueError("destination adapter registration is missing or incompatible")
            declaration_baseline = _snapshot_declaration(declaration)
            registration_baseline = _snapshot_registration(registration)
            adapter, resolved_configuration_digest, callbacks = _construct_adapter(
                registration.factory,
                bytes(declaration.configuration_bytes),
                declaration.configuration_digest,
            )
            if (
                _snapshot_declaration(supplied_declaration) != declaration_baseline
                or _snapshot_declaration(declaration) != declaration_baseline
                or _snapshot_registration(registration) != registration_baseline
            ):
                raise ValueError("destination declaration changed during adapter construction")
            if type(adapter) is not registration.adapter_type:
                raise TypeError("destination adapter factory returned an invalid type")
            unsigned = AuthenticatedDestinationV1(
                _ENGINE_SCHEMA,
                declaration.destination_ref,
                declaration.display_name,
                resolved_configuration_digest,
                declaration.policy.policy_digest,
                declaration.policy.maximum_artifact_bytes,
                declaration.policy.maximum_total_bytes,
                issuer.authority_ref,
                issuer.key_ref,
                _ZERO,
            )
            descriptor = issuer.issue(unsigned)
            if not verifier.verify(
                "publication-destination/v1", descriptor.payload,
                descriptor.tag, descriptor.key_ref,
            ):
                raise ValueError("destination descriptor authentication failed")
            bindings.append(_BoundDestinationV1(
                declaration, descriptor, adapter, registration.adapter_type,
                resolved_configuration_digest,
                callbacks[0], callbacks[1], callbacks[2],
            ))
        self._bindings = tuple(bindings)
        baselines = tuple(
            (
                item,
                _snapshot_declaration(item.declaration),
                replace(item.descriptor),
                item.adapter,
                item.adapter_type,
                item.resolved_configuration_digest,
                item.publish_once,
                item.lookup,
                item.iter_bytes,
            )
            for item in self._bindings
        )
        self._register_pins(_RegistryPinsV1(
            self._bindings,
            self._registrations,
            self._issuer,
            self._verifier,
            baselines,
            callback_probe,
            callback_match,
        ))

    def _register_pins(
        self, pins: _RegistryPinsV1, _register=_register_registry_pin
    ) -> None:
        _register(self, pins)

    def _pins(self, _get=_get_registry_pin) -> _RegistryPinsV1:
        pins = _get(self)
        if (
            type(pins) is not _RegistryPinsV1
            or self._bindings is not pins.bindings
            or self._registrations is not pins.registrations
            or self._issuer is not pins.issuer
            or self._verifier is not pins.verifier
            or self._issuer.issue != self._issuer_issue
            or self._verifier.verify != self._verifier_verify
        ):
            raise ValueError("destination registry binding changed")
        return pins

    def _bound(
        self, binding: _BoundDestinationV1, baseline: tuple[object, ...],
        callback_probe: object, callback_match: object,
    ) -> tuple[AuthenticatedDestinationV1, object]:
        (
            pinned_binding, pinned_declaration, pinned_descriptor,
            pinned_adapter, pinned_adapter_type, pinned_configuration_digest,
            pinned_publish,
            pinned_lookup, pinned_iter,
        ) = baseline
        callbacks = callback_probe(binding.adapter)
        if (
            type(binding) is not _BoundDestinationV1
            or binding is not pinned_binding
            or _snapshot_declaration(binding.declaration) != pinned_declaration
            or replace(binding.descriptor) != pinned_descriptor
            or binding.adapter is not pinned_adapter
            or binding.adapter_type is not pinned_adapter_type
            or binding.resolved_configuration_digest != pinned_configuration_digest
            or type(binding.adapter) is not pinned_adapter_type
            or any(
                not callback_match(current, pinned)
                for current, pinned in zip(
                    callbacks, (pinned_publish, pinned_lookup, pinned_iter)
                )
            )
        ):
            raise ValueError("destination registry binding changed")
        descriptor = replace(binding.descriptor)
        declaration = binding.declaration
        if (
            descriptor.destination_ref != declaration.destination_ref
            or descriptor.display_name != declaration.display_name
            or descriptor.configuration_digest != binding.resolved_configuration_digest
            or descriptor.policy_digest != declaration.policy.policy_digest
            or not self._verifier.verify(
                "publication-destination/v1", descriptor.payload,
                descriptor.tag, descriptor.key_ref,
            )
        ):
            raise ValueError("destination registry descriptor changed")
        return descriptor, binding.adapter

    def resolve(self, destination_ref: str) -> tuple[AuthenticatedDestinationV1, object]:
        destination_ref = _text(destination_ref, "destination_ref")
        pins = self._pins()
        matches = tuple(
            (item, pins.binding_baselines[index])
            for index, item in enumerate(pins.bindings)
            if item.declaration.destination_ref == destination_ref
        )
        if len(matches) != 1:
            raise KeyError("destination was not found")
        return self._bound(*matches[0], pins.callback_probe, pins.callback_match)

    def list(self, limit: int) -> tuple[tuple[AuthenticatedDestinationV1, ...], bool]:
        if type(limit) is not int or not 1 <= limit <= _MAX_DESTINATIONS + 1:
            raise ValueError("destination list limit is invalid")
        pins = self._pins()
        descriptors = tuple(
            self._bound(
                item, pins.binding_baselines[index],
                pins.callback_probe, pins.callback_match,
            )[0]
            for index, item in enumerate(pins.bindings)
        )
        return descriptors[:limit], len(descriptors) <= limit


__all__ = [
    "ArtifactDestinationConfigV1",
    "ArtifactDestinationDeclarationV1",
    "ArtifactDestinationPolicyV1",
    "DestinationAdapterInstallationV1",
    "DestinationAdapterRegistrationV1",
    "ImmutableArtifactDestinationRegistryV1",
    "ResolvedDestinationAdapterV1",
    "artifact_destination_declaration_digest_v1",
    "load_artifact_destination_config_v1",
    "parse_artifact_destination_config_v1",
]
