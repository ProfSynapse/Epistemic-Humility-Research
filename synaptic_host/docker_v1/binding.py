"""Authenticated path binding and explicit workload environment policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import unicodedata

from tuner.execution.providers.docker_provider_v1.model import DockerWorkloadV1

from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerControlContractCodeV1,
    DockerControlContractErrorV1,
    DockerCreatePathBindingV1,
    MAX_WORKLOAD_ENV_ENTRIES_V1,
    DockerWorkloadEnvironmentBindingV1,
    DockerWorkloadEnvironmentEntryV1,
)
from synaptic_host.docker_v1.control_private import (
    DockerPrivateWorkloadEnvironmentResolutionV1,
)
from synaptic_host.docker_v1.model import (
    AuthenticatedDockerStoragePathMappingPairV1,
    DockerStoragePathMappingPairV1,
    DockerStoragePurposeV1,
    DockerWSLPathPurposeV1,
    DockerWSLPathRequestV1,
    ResolvedDockerMountsV1,
)


_ENV_KEY = re.compile(r"[A-Z_][A-Z0-9_]*\Z")
_MAX_ENV_KEY_BYTES = 128
_MAX_ENV_VALUE_BYTES = 4096


def _closed(code=DockerControlContractCodeV1.INVALID):
    raise DockerControlContractErrorV1(code) from None


def _snapshot_pair(value):
    try:
        if type(value) is not AuthenticatedDockerStoragePathMappingPairV1:
            raise ValueError
        content = DockerStoragePathMappingPairV1(
            value.content.storage_mapping,
            value.content.wsl_mapping,
            value.content.pair_digest,
        )
        rebuilt = AuthenticatedDockerStoragePathMappingPairV1(
            content, value.authority_ref, value.key_ref, value.tag
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)


def _snapshot_binding(value):
    try:
        if type(value) is not DockerCreatePathBindingV1:
            raise ValueError
        rebuilt = DockerCreatePathBindingV1(
            value.labels_digest,
            value.source_ref,
            value.artifact_ref,
            value.mount_resolution_digest,
            value.source_storage_mapping_proof_digest,
            value.artifact_storage_mapping_proof_digest,
            value.source_mapping_pair_proof_digest,
            value.artifact_mapping_pair_proof_digest,
            DockerWSLPathRequestV1(
                *(
                    getattr(value.source_request, name)
                    for name in value.source_request.__dataclass_fields__
                )
            ),
            DockerWSLPathRequestV1(
                *(
                    getattr(value.artifact_request, name)
                    for name in value.artifact_request.__dataclass_fields__
                )
            ),
            value.source_read_only,
            value.binding_digest,
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)


def _snapshot_binding_envelope(value):
    try:
        if type(value) is not AuthenticatedDockerCreatePathBindingV1:
            raise ValueError
        rebuilt = AuthenticatedDockerCreatePathBindingV1(
            _snapshot_binding(value.content),
            value.authority_ref,
            value.key_ref,
            value.tag,
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)


def _source_identity(pair):
    access = pair.content.storage_mapping.content.verify_access
    if access is None:
        return None
    return access.verify_borrow, access.verify_root


def _components(path):
    if type(path) is not str or not path.startswith("/"):
        _closed()
    return tuple(part for part in path.split("/") if part)


class DockerAuthenticatedPairPathBinderV1:
    """Create path bindings only from two pinned authenticated mapping pairs."""

    __slots__ = (
        "_source", "_artifact", "_pair_authority", "_pair_authority_pin",
        "_pair_refs", "_binding_authority", "_binding_authority_pin",
        "_binding_refs", "_source_verify_borrow", "_source_verify_root",
    )

    def __init__(
        self, *, source_pair, artifact_pair, pair_authority, binding_authority
    ):
        try:
            if (
                type(source_pair)
                is not AuthenticatedDockerStoragePathMappingPairV1
                or type(artifact_pair)
                is not AuthenticatedDockerStoragePathMappingPairV1
                or source_pair.content.pair_digest
                == artifact_pair.content.pair_digest
                or source_pair.content.storage_mapping.content.declared_ref
                == artifact_pair.content.storage_mapping.content.declared_ref
                or source_pair.content.storage_mapping.content.mapping_ref
                == artifact_pair.content.storage_mapping.content.mapping_ref
                or source_pair.content.wsl_mapping.content.mapping_ref
                == artifact_pair.content.wsl_mapping.content.mapping_ref
            ):
                raise ValueError
            source = _snapshot_pair(source_pair)
            artifact = _snapshot_pair(artifact_pair)
            if (
                source.content.storage_mapping.content.purpose
                is not DockerStoragePurposeV1.SOURCE_BUNDLE
                or source.content.wsl_mapping.content.purpose
                is not DockerWSLPathPurposeV1.SOURCE_READ
                or artifact.content.storage_mapping.content.purpose
                is not DockerStoragePurposeV1.ARTIFACT_OUTPUT
                or artifact.content.wsl_mapping.content.purpose
                is not DockerWSLPathPurposeV1.ARTIFACT_WRITE
                or _source_identity(source) is None
                or source.content.wsl_mapping.content.distro
                != artifact.content.wsl_mapping.content.distro
                or source.content.pair_digest == artifact.content.pair_digest
                or source.content.storage_mapping.content.declared_ref
                == artifact.content.storage_mapping.content.declared_ref
                or source.content.storage_mapping.content.mapping_ref
                == artifact.content.storage_mapping.content.mapping_ref
                or source.content.wsl_mapping.content.mapping_ref
                == artifact.content.wsl_mapping.content.mapping_ref
            ):
                raise ValueError
            source_identity = _source_identity(source)
            pair_refs = (pair_authority.authority_ref, pair_authority.key_ref)
            binding_refs = (
                binding_authority.authority_ref, binding_authority.key_ref
            )
            if any(type(value) is not str for value in pair_refs + binding_refs):
                raise ValueError
            self._source = source
            self._artifact = artifact
            self._pair_authority = pair_authority
            self._pair_authority_pin = pair_authority
            self._pair_refs = pair_refs
            self._binding_authority = binding_authority
            self._binding_authority_pin = binding_authority
            self._binding_refs = binding_refs
            self._source_verify_borrow = source_identity[0]
            self._source_verify_root = source_identity[1]
            self._source_identity_exact()
            self._authenticate_pair(source)
            self._source_identity_exact()
            if _snapshot_pair(self._artifact) != artifact:
                raise ValueError
            self._authenticate_pair(artifact)
            self._source_identity_exact()
            current_source = _snapshot_pair(self._source)
            if current_source != source:
                raise ValueError
            current_identity = _source_identity(current_source)
            source_identity = _source_identity(source)
            if (
                current_identity[0] is not source_identity[0]
                or current_identity[1] is not source_identity[1]
            ):
                raise ValueError
        except DockerControlContractErrorV1:
            raise
        except BaseException:
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)

    def _source_identity_exact(self):
        identity = _source_identity(self._source)
        if (
            identity is None
            or identity[0] is not self._source_verify_borrow
            or identity[1] is not self._source_verify_root
        ):
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        return identity

    def _pair_authority_exact(self):
        return (
            self._pair_authority is self._pair_authority_pin
            and (
                self._pair_authority.authority_ref,
                self._pair_authority.key_ref,
            )
            == self._pair_refs
        )

    def _binding_authority_exact(self):
        return (
            self._binding_authority is self._binding_authority_pin
            and (
                self._binding_authority.authority_ref,
                self._binding_authority.key_ref,
            )
            == self._binding_refs
        )

    def _authenticate_pair(self, expected):
        if not self._pair_authority_exact():
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        baseline = _snapshot_pair(expected)
        identity = _source_identity(baseline)
        presented = _snapshot_pair(baseline)
        try:
            returned = self._pair_authority.authenticate(presented)
        except BaseException:
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        returned = _snapshot_pair(returned)
        if (
            not self._pair_authority_exact()
            or returned != baseline
            or returned.proof_digest != baseline.proof_digest
            or _source_identity(returned) != identity
        ):
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        if identity is not None:
            returned_identity = _source_identity(returned)
            if (
                returned_identity[0] is not identity[0]
                or returned_identity[1] is not identity[1]
            ):
                _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        return returned

    def _issue_and_authenticate(self, expected):
        self._source_identity_exact()
        if not self._binding_authority_exact():
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        baseline = _snapshot_binding(expected)
        self._source_identity_exact()
        try:
            issued = self._binding_authority.issue(_snapshot_binding(baseline))
        except BaseException:
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        self._source_identity_exact()
        issued = _snapshot_binding_envelope(issued)
        if (
            not self._binding_authority_exact()
            or issued.content != baseline
            or (issued.authority_ref, issued.key_ref) != self._binding_refs
        ):
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        issued_baseline = _snapshot_binding_envelope(issued)
        self._source_identity_exact()
        try:
            returned = self._binding_authority.authenticate(
                _snapshot_binding_envelope(issued_baseline)
            )
        except BaseException:
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        self._source_identity_exact()
        returned = _snapshot_binding_envelope(returned)
        if (
            not self._binding_authority_exact()
            or returned != issued_baseline
            or returned.content != baseline
        ):
            _closed(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
        self._source_identity_exact()
        return returned

    def bind(self, resolved, source_ref, artifact_ref):
        try:
            self._source_identity_exact()
            if type(resolved) is not ResolvedDockerMountsV1:
                raise ValueError
            resolved = ResolvedDockerMountsV1(
                *(
                    getattr(resolved, name)
                    for name in resolved.__dataclass_fields__
                )
            )
            source_baseline = _snapshot_pair(self._source)
            artifact_baseline = _snapshot_pair(self._artifact)
            source_identity = _source_identity(source_baseline)
            source = self._authenticate_pair(source_baseline)
            self._source_identity_exact()
            if _snapshot_pair(self._artifact) != artifact_baseline:
                raise ValueError
            artifact = self._authenticate_pair(artifact_baseline)
            self._source_identity_exact()
            current_source = _snapshot_pair(self._source)
            current_artifact = _snapshot_pair(self._artifact)
            if (
                current_source != source_baseline
                or current_artifact != artifact_baseline
            ):
                raise ValueError
            current_identity = _source_identity(current_source)
            if (
                current_identity[0] is not source_identity[0]
                or current_identity[1] is not source_identity[1]
            ):
                raise ValueError
            source_storage = source.content.storage_mapping
            source_wsl = source.content.wsl_mapping.content
            artifact_storage = artifact.content.storage_mapping
            artifact_wsl = artifact.content.wsl_mapping.content
            source_root = _components(source_wsl.posix_root)
            source_path = _components(resolved.source_wsl_private_path)
            artifact_root = _components(artifact_wsl.posix_root)
            resolved_artifact = _components(resolved.artifact_wsl_root)
            if (
                type(source_ref) is not str
                or type(artifact_ref) is not str
                or source_ref == artifact_ref
                or source.content.storage_mapping.content.declared_ref
                != source_ref
                or artifact.content.storage_mapping.content.declared_ref
                != artifact_ref
                or resolved.source_mapping_digest
                != source_storage.proof_digest
                or resolved.artifact_mapping_digest
                != artifact_storage.proof_digest
                or resolved.source_read_only is not True
                or source_wsl.distro != artifact_wsl.distro
                or source_path[:len(source_root)] != source_root
                or len(source_path) <= len(source_root)
                or resolved_artifact != artifact_root
                or source_root[:len(artifact_root)] == artifact_root
                or artifact_root[:len(source_root)] == source_root
            ):
                raise ValueError
            source_request = DockerWSLPathRequestV1.build(
                mapping_ref=source_wsl.mapping_ref,
                expected_mapping_digest=source_wsl.mapping_digest,
                expected_distro=source_wsl.distro,
                purpose=DockerWSLPathPurposeV1.SOURCE_READ,
                posix_path=resolved.source_wsl_private_path,
            )
            artifact_request = DockerWSLPathRequestV1.build(
                mapping_ref=artifact_wsl.mapping_ref,
                expected_mapping_digest=artifact_wsl.mapping_digest,
                expected_distro=artifact_wsl.distro,
                purpose=DockerWSLPathPurposeV1.ARTIFACT_WRITE,
                posix_path=resolved.artifact_wsl_root,
            )
            expected = DockerCreatePathBindingV1.build(
                labels_digest=resolved.labels_digest,
                source_ref=source_ref,
                artifact_ref=artifact_ref,
                mount_resolution_digest=resolved.resolution_digest,
                source_storage_mapping_proof_digest=source_storage.proof_digest,
                artifact_storage_mapping_proof_digest=artifact_storage.proof_digest,
                source_mapping_pair_proof_digest=source.proof_digest,
                artifact_mapping_pair_proof_digest=artifact.proof_digest,
                source_request=source_request,
                artifact_request=artifact_request,
                source_read_only=True,
            )
            returned = self._issue_and_authenticate(expected)
            self._source_identity_exact()
            final_source = _snapshot_pair(self._source)
            final_artifact = _snapshot_pair(self._artifact)
            final_identity = _source_identity(final_source)
            if (
                final_source != source_baseline
                or final_artifact != artifact_baseline
                or final_identity[0] is not source_identity[0]
                or final_identity[1] is not source_identity[1]
                or not self._pair_authority_exact()
            ):
                raise ValueError
            return returned
        except DockerControlContractErrorV1:
            raise
        except BaseException:
            _closed()


def _checked_key(value):
    if (
        type(value) is not str
        or unicodedata.normalize("NFC", value) != value
        or not value.isascii()
        or _ENV_KEY.fullmatch(value) is None
        or len(value.encode("ascii")) > _MAX_ENV_KEY_BYTES
    ):
        _closed()
    return value


def _checked_value(key, value):
    try:
        if (
            type(value) is not str
            or unicodedata.normalize("NFC", value) != value
            or not value.isascii()
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
            or len(f"{key}={value}".encode("ascii")) > _MAX_ENV_VALUE_BYTES
        ):
            raise ValueError
        return value
    except BaseException:
        _closed()


def _pairs(value):
    try:
        value = tuple(value)
        pairs = tuple((_checked_key(key), _checked_value(key, item)) for key, item in value)
        if tuple(sorted(pairs)) != pairs or len({key for key, _ in pairs}) != len(pairs):
            raise ValueError
        return pairs
    except DockerControlContractErrorV1:
        raise
    except BaseException:
        _closed()


@dataclass(frozen=True, slots=True)
class DockerWorkloadEnvironmentPolicyV1:
    allowed_keys: tuple[str, ...]
    denied_keys: tuple[str, ...]
    secret_keys: tuple[str, ...]
    base_values: tuple[tuple[str, str], ...]
    policy_digest: str

    def canonical_without_digest(self):
        return {
            "allowed_keys": list(self.allowed_keys),
            "base_values": [
                {"key": key, "value_digest": digest_v1({"value": value})}
                for key, value in self.base_values
            ],
            "denied_keys": list(self.denied_keys),
            "schema": "synaptic-host-docker-workload-environment-policy/v1",
            "secret_keys": list(self.secret_keys),
        }

    def __post_init__(self):
        try:
            allowed = tuple(_checked_key(value) for value in self.allowed_keys)
            denied = tuple(_checked_key(value) for value in self.denied_keys)
            secret = tuple(_checked_key(value) for value in self.secret_keys)
            base = _pairs(self.base_values)
            if (
                any(type(value) is not tuple for value in (
                    self.allowed_keys, self.denied_keys, self.secret_keys,
                    self.base_values,
                ))
                or any(
                    len(value) > MAX_WORKLOAD_ENV_ENTRIES_V1
                    for value in (
                        allowed, denied, secret, base,
                    )
                )
                or allowed != tuple(sorted(set(allowed)))
                or denied != tuple(sorted(set(denied)))
                or secret != tuple(sorted(set(secret)))
                or not set(secret).issubset(allowed)
                or any(key not in allowed or key in denied or key in secret for key, _ in base)
                or self.policy_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except DockerControlContractErrorV1:
            raise
        except BaseException:
            _closed()

    @classmethod
    def build(cls, *, allowed_keys, denied_keys=(), secret_keys=(), base_values=()):
        allowed_keys = tuple(allowed_keys)
        denied_keys = tuple(denied_keys)
        secret_keys = tuple(secret_keys)
        base_values = tuple(base_values)
        temporary = cls.__new__(cls)
        object.__setattr__(temporary, "allowed_keys", allowed_keys)
        object.__setattr__(temporary, "denied_keys", denied_keys)
        object.__setattr__(temporary, "secret_keys", secret_keys)
        object.__setattr__(temporary, "base_values", base_values)
        object.__setattr__(temporary, "policy_digest", "0" * 64)
        return cls(
            allowed_keys, denied_keys, secret_keys, base_values,
            digest_v1(temporary.canonical_without_digest()),
        )


class DockerEnvironmentResolutionCodeV1(str, Enum):
    DENIED = "DOCKER_ENVIRONMENT_DENIED"
    UNALLOWED = "DOCKER_ENVIRONMENT_UNALLOWED"
    SECRET_TRANSPORT_UNAVAILABLE = "ENV_SECRET_TRANSPORT_UNAVAILABLE"
    MISSING = "DOCKER_ENVIRONMENT_MISSING"
    INVALID = "DOCKER_ENVIRONMENT_INVALID"
    AUTHENTICATION_FAILED = "DOCKER_ENVIRONMENT_AUTHENTICATION_FAILED"


class DockerEnvironmentResolutionErrorV1(RuntimeError):
    __slots__ = ("code",)

    def __init__(self, code):
        if type(code) is not DockerEnvironmentResolutionCodeV1:
            code = DockerEnvironmentResolutionCodeV1.INVALID
        RuntimeError.__init__(self, code.value)
        object.__setattr__(self, "code", code)

    def __setattr__(self, name, value):
        if name == "code":
            raise AttributeError("immutable environment resolution error")
        BaseException.__setattr__(self, name, value)


def _env_fail(code):
    raise DockerEnvironmentResolutionErrorV1(code) from None


def _snapshot_environment_content(value):
    try:
        if type(value) is not DockerWorkloadEnvironmentBindingV1:
            raise ValueError
        rebuilt = DockerWorkloadEnvironmentBindingV1(
            value.workload_digest,
            tuple(value.requested_keys),
            tuple(
                DockerWorkloadEnvironmentEntryV1(
                    item.key, item.key_digest, item.value_digest,
                    item.entry_digest,
                )
                for item in value.supplied_entries
            ),
            value.binding_digest,
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)


def _snapshot_environment_envelope(value):
    try:
        if type(value) is not AuthenticatedDockerWorkloadEnvironmentBindingV1:
            raise ValueError
        rebuilt = AuthenticatedDockerWorkloadEnvironmentBindingV1(
            _snapshot_environment_content(value.content),
            value.authority_ref,
            value.key_ref,
            value.tag,
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)


class DockerExplicitWorkloadEnvironmentResolverV1:
    """Resolve only explicit inputs; never consult the host process environment."""

    __slots__ = (
        "_policy", "_policy_pin", "_policy_baseline", "_overrides",
        "_overrides_pin", "_overrides_baseline", "_authority",
        "_authority_pin", "_authority_refs",
    )

    def __init__(self, *, policy, overrides=(), authority):
        try:
            if type(policy) is not DockerWorkloadEnvironmentPolicyV1:
                raise ValueError
            policy = DockerWorkloadEnvironmentPolicyV1(
                tuple(policy.allowed_keys),
                tuple(policy.denied_keys),
                tuple(policy.secret_keys),
                tuple(policy.base_values),
                policy.policy_digest,
            )
            overrides = _pairs(overrides)
            allowed = set(policy.allowed_keys)
            denied = set(policy.denied_keys)
            secret_keys = set(policy.secret_keys)
            if (
                len(overrides) > MAX_WORKLOAD_ENV_ENTRIES_V1
                or any(
                    key not in allowed or key in denied or key in secret_keys
                    for key, _ in overrides
                )
            ):
                raise ValueError
            refs = authority.authority_ref, authority.key_ref
            if any(type(value) is not str for value in refs):
                raise ValueError
            policy_baseline = DockerWorkloadEnvironmentPolicyV1(
                tuple(policy.allowed_keys),
                tuple(policy.denied_keys),
                tuple(policy.secret_keys),
                tuple(policy.base_values),
                policy.policy_digest,
            )
            overrides_baseline = tuple(list(overrides))
            self._policy = policy
            self._policy_pin = policy
            self._policy_baseline = policy_baseline
            self._overrides = overrides
            self._overrides_pin = overrides
            self._overrides_baseline = overrides_baseline
            self._authority = authority
            self._authority_pin = authority
            self._authority_refs = refs
        except DockerEnvironmentResolutionErrorV1:
            raise
        except BaseException:
            _env_fail(DockerEnvironmentResolutionCodeV1.INVALID)

    def __repr__(self):
        return "DockerExplicitWorkloadEnvironmentResolverV1(<redacted>)"

    __str__ = __repr__

    def __reduce__(self):
        _env_fail(DockerEnvironmentResolutionCodeV1.INVALID)

    __copy__ = __reduce__

    def __deepcopy__(self, _memo):
        return self.__reduce__()

    def _authority_exact(self):
        return (
            self._authority is self._authority_pin
            and (self._authority.authority_ref, self._authority.key_ref)
            == self._authority_refs
        )

    def _configuration_exact(self):
        try:
            policy = self._policy
            if (
                type(policy) is not DockerWorkloadEnvironmentPolicyV1
                or policy is not self._policy_pin
                or policy != self._policy_baseline
            ):
                raise ValueError
            rebuilt_policy = DockerWorkloadEnvironmentPolicyV1(
                tuple(policy.allowed_keys),
                tuple(policy.denied_keys),
                tuple(policy.secret_keys),
                tuple(policy.base_values),
                policy.policy_digest,
            )
            overrides = self._overrides
            if (
                rebuilt_policy != self._policy_baseline
                or type(overrides) is not tuple
                or overrides is not self._overrides_pin
                or overrides != self._overrides_baseline
                or _pairs(overrides) != self._overrides_baseline
            ):
                raise ValueError
        except BaseException:
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)

    def _authenticate(self, expected):
        self._configuration_exact()
        if not self._authority_exact():
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)
        baseline = _snapshot_environment_envelope(expected)
        self._configuration_exact()
        try:
            returned = self._authority.authenticate(
                _snapshot_environment_envelope(baseline)
            )
        except BaseException:
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)
        self._configuration_exact()
        returned = _snapshot_environment_envelope(returned)
        if not self._authority_exact() or returned != baseline:
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)
        self._configuration_exact()
        return returned

    def _issue(self, expected):
        self._configuration_exact()
        if not self._authority_exact():
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)
        baseline = _snapshot_environment_content(expected)
        self._configuration_exact()
        try:
            issued = self._authority.issue(_snapshot_environment_content(baseline))
        except BaseException:
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)
        self._configuration_exact()
        issued = _snapshot_environment_envelope(issued)
        if (
            not self._authority_exact()
            or issued.content != baseline
            or (issued.authority_ref, issued.key_ref) != self._authority_refs
        ):
            _env_fail(DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED)
        self._configuration_exact()
        return self._authenticate(issued)

    def resolve(self, workload, existing_binding=None):
        try:
            self._configuration_exact()
            if type(workload) is not DockerWorkloadV1:
                raise ValueError
            workload = DockerWorkloadV1(
                tuple(workload.arguments),
                tuple(workload.environment_keys),
                workload.workload_digest,
            )
            requested = tuple(_checked_key(key) for key in workload.environment_keys)
            if requested != tuple(sorted(set(requested))):
                raise ValueError
            allowed = set(self._policy.allowed_keys)
            denied = set(self._policy.denied_keys)
            secret_keys = set(self._policy.secret_keys)
            overrides = dict(self._overrides)
            base = dict(self._policy.base_values)
            if any(key in denied for key in requested):
                _env_fail(DockerEnvironmentResolutionCodeV1.DENIED)
            if any(key not in allowed for key in requested):
                _env_fail(DockerEnvironmentResolutionCodeV1.UNALLOWED)
            if any(key in secret_keys for key in requested):
                _env_fail(
                    DockerEnvironmentResolutionCodeV1.SECRET_TRANSPORT_UNAVAILABLE
                )
            missing = tuple(
                key for key in requested
                if key not in secret_keys and key not in overrides and key not in base
            )
            if missing:
                _env_fail(DockerEnvironmentResolutionCodeV1.MISSING)
            pairs = tuple(
                (
                    key,
                    overrides[key] if key in overrides
                    else base[key],
                )
                for key in requested
            )
            entries = tuple(
                DockerWorkloadEnvironmentEntryV1.build(key, value)
                for key, value in pairs
            )
            expected = DockerWorkloadEnvironmentBindingV1.build(
                workload.workload_digest, requested, entries
            )
            if existing_binding is None:
                authenticated = self._issue(expected)
            else:
                authenticated = self._authenticate(existing_binding)
                if authenticated.content != expected:
                    _env_fail(
                        DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED
                    )
            self._configuration_exact()
            return DockerPrivateWorkloadEnvironmentResolutionV1(
                authenticated, pairs
            )
        except DockerEnvironmentResolutionErrorV1:
            raise
        except BaseException:
            _env_fail(DockerEnvironmentResolutionCodeV1.INVALID)


__all__: tuple[str, ...] = ()
