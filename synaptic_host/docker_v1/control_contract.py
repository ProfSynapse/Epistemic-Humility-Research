from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import re
import unicodedata

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    DockerAbsenceContentV1,
    DockerLabelsV1,
)
from synaptic_host.bundle_io_v1.model import (
    BundleIOCodeV1,
    checked_ref_v1,
    checked_sha_v1,
    digest_v1,
)
from .model import (
    MAX_DOCKER_ARG_BYTES_V1,
    MAX_WINDOWS_PATH_BYTES_V1, MAX_WSL_COMPONENT_BYTES_V1,
    DockerWSLPathPurposeV1,
    DockerWSLPathRequestV1,
)
from .control_model import (
    OWNED_LABEL_NAMES_V1,
    DockerLabelProjectionV1,
)

_CONTAINER_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
_CONTAINER_REF = re.compile(r"[0-9a-f]{64}\Z")
MAX_WORKLOAD_ENV_ENTRIES_V1 = 64


def docker_device_requests_projection_digest_v1(value):
    """Digest a bounded, immutable projection of Docker DeviceRequests."""
    try:
        if type(value) is not tuple or len(value) > 8:
            raise ValueError
        projected = []
        for item in value:
            if type(item) is not tuple or len(item) != 5:
                raise ValueError
            driver, count, device_ids, capabilities, options = item
            if (
                type(driver) is not str
                or not 1 <= len(driver.encode("utf-8")) <= 64
                or type(count) is not int
                or not -(2**31) <= count <= 2**31 - 1
                or type(device_ids) is not tuple
                or not 1 <= len(device_ids) <= 8
                or any(
                    type(device_id) is not str
                    or not 1 <= len(device_id.encode("utf-8")) <= 64
                    for device_id in device_ids
                )
                or type(capabilities) is not tuple
                or not 1 <= len(capabilities) <= 8
                or any(
                    type(group) is not tuple
                    or not 1 <= len(group) <= 8
                    or any(
                        type(capability) is not str
                        or not 1 <= len(capability.encode("utf-8")) <= 64
                        for capability in group
                    )
                    for group in capabilities
                )
                or type(options) is not tuple
                or len(options) > 16
                or tuple(sorted(options)) != options
                or len({key for key, _ in options}) != len(options)
                or any(
                    type(key) is not str
                    or type(option) is not str
                    or not 1 <= len(key.encode("utf-8")) <= 64
                    or len(option.encode("utf-8")) > 256
                    for key, option in options
                )
            ):
                raise ValueError
            projected.append({
                "Capabilities": [list(group) for group in capabilities],
                "Count": count,
                "DeviceIDs": list(device_ids),
                "Driver": driver,
                "Options": dict(options),
            })
        return digest_v1({
            "device_requests": projected,
            "schema_version": "synaptic-host-docker-device-requests-projection/v1",
        })
    except BaseException:
        _fail()


def docker_accelerator_device_requests_digest_v1(value):
    """Map the released provider-neutral request to exact Docker evidence."""
    try:
        if type(value) is not AcceleratorDeviceRequestV1:
            raise ValueError
        rebuilt = AcceleratorDeviceRequestV1(
            value.kind, tuple(value.device_indices), tuple(value.capabilities)
        )
        if rebuilt != value:
            raise ValueError
        if rebuilt == AcceleratorDeviceRequestV1("cpu", (), ()):
            projection = ()
        elif rebuilt == AcceleratorDeviceRequestV1(
            "nvidia", (0,), ("gpu",)
        ):
            projection = (("nvidia", 0, ("0",), (("gpu",),), ()),)
        else:
            raise ValueError
        return docker_device_requests_projection_digest_v1(projection)
    except DockerControlContractErrorV1:
        raise
    except BaseException:
        _fail()


def docker_safe_unc_v1(value):
    try:
        if (
            type(value) is not str
            or unicodedata.normalize("NFC", value) != value
            or not value.startswith("\\\\wsl.localhost\\")
            or "/" in value
            or len(value.encode("utf-8")) > MAX_WINDOWS_PATH_BYTES_V1
            or any(char in value for char in (",", '"', "\r", "\n", "\x00"))
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError
        components = value.split("\\")
        if (
            not 1 <= len(components[4:]) <= 128
            or any(not component for component in components[3:])
        ):
            raise ValueError
        distro = components[3]
        if (
            not 1 <= len(distro) <= 64 or not distro[0].isalnum()
            or any(not (char.isascii() and (char.isalnum() or char in "._-"))
                   for char in distro)
        ):
            raise ValueError
        reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
        reserved.update({f"COM{number}" for number in range(1, 10)})
        reserved.update({f"LPT{number}" for number in range(1, 10)})
        reserved.update({f"COM{number}" for number in "¹²³"})
        reserved.update({f"LPT{number}" for number in "¹²³"})
        for component in components[4:]:
            base = component.split(".", 1)[0].rstrip(" .").upper()
            if (
                component in (".", "..") or component.endswith((" ", "."))
                or len(component.encode("utf-8")) > MAX_WSL_COMPONENT_BYTES_V1
                or any(char in '<>:"|?*' for char in component)
                or base in reserved
            ):
                raise ValueError
        return value
    except BaseException:
        _fail()


class DockerControlContractCodeV1(str, Enum):
    INVALID = "DOCKER_CONTROL_CONTRACT_INVALID"
    AUTHENTICATION_FAILED = "DOCKER_CONTROL_CONTRACT_AUTHENTICATION_FAILED"


class DockerControlContractErrorV1(RuntimeError):
    def __init__(self, code):
        if type(code) is not DockerControlContractCodeV1:
            raise TypeError("exact control contract code required")
        self.code = code
        super().__init__(code.value)


def _fail(code=DockerControlContractCodeV1.INVALID):
    raise DockerControlContractErrorV1(code) from None


def _sha(value):
    try:
        checked_sha_v1(value, BundleIOCodeV1.COMMAND_INVALID)
        return value
    except BaseException:
        _fail()


def _ref(value):
    try:
        checked_ref_v1(value, BundleIOCodeV1.COMMAND_INVALID)
        return value
    except BaseException:
        _fail()


def _plain_sha(value):
    if type(value) is not str:
        _fail()
    return sha256(value.encode("utf-8")).hexdigest()


def _snapshot_path_request(value):
    try:
        if type(value) is not DockerWSLPathRequestV1:
            raise ValueError
        rebuilt = DockerWSLPathRequestV1(
            value.mapping_ref,
            value.expected_mapping_digest,
            value.expected_distro,
            value.purpose,
            value.posix_path,
            value.request_digest,
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _fail()


@dataclass(frozen=True, slots=True)
class DockerCreatePathBindingV1:
    labels_digest: str
    source_ref: str
    artifact_ref: str
    mount_resolution_digest: str
    source_storage_mapping_proof_digest: str
    artifact_storage_mapping_proof_digest: str
    source_mapping_pair_proof_digest: str
    artifact_mapping_pair_proof_digest: str
    source_request: DockerWSLPathRequestV1
    artifact_request: DockerWSLPathRequestV1
    source_read_only: bool
    binding_digest: str

    def canonical_without_digest(self):
        return {
            "artifact_ref": self.artifact_ref,
            "artifact_request_digest": self.artifact_request.request_digest,
            "artifact_mapping_pair_proof_digest": self.artifact_mapping_pair_proof_digest,
            "artifact_storage_mapping_proof_digest": self.artifact_storage_mapping_proof_digest,
            "labels_digest": self.labels_digest,
            "mount_resolution_digest": self.mount_resolution_digest,
            "schema_version": "synaptic-host-docker-create-path-binding/v1",
            "source_read_only": self.source_read_only,
            "source_ref": self.source_ref,
            "source_request_digest": self.source_request.request_digest,
            "source_mapping_pair_proof_digest": self.source_mapping_pair_proof_digest,
            "source_storage_mapping_proof_digest": self.source_storage_mapping_proof_digest,
        }

    def __post_init__(self):
        source = _snapshot_path_request(self.source_request)
        artifact = _snapshot_path_request(self.artifact_request)
        for value in (
            self.labels_digest, self.mount_resolution_digest,
            self.source_storage_mapping_proof_digest,
            self.artifact_storage_mapping_proof_digest,
            self.source_mapping_pair_proof_digest,
            self.artifact_mapping_pair_proof_digest,
            self.binding_digest,
        ):
            _sha(value)
        _ref(self.source_ref)
        _ref(self.artifact_ref)
        if (
            self.source_ref == self.artifact_ref
            or source.purpose is not DockerWSLPathPurposeV1.SOURCE_READ
            or artifact.purpose is not DockerWSLPathPurposeV1.ARTIFACT_WRITE
            or source.request_digest == artifact.request_digest
            or self.source_read_only is not True
            or self.binding_digest != digest_v1(self.canonical_without_digest())
        ):
            _fail()

    @classmethod
    def build(cls, **values):
        temporary = dict(values)
        body = {
            "artifact_ref": temporary["artifact_ref"],
            "artifact_request_digest": temporary["artifact_request"].request_digest,
            "artifact_mapping_pair_proof_digest": temporary["artifact_mapping_pair_proof_digest"],
            "artifact_storage_mapping_proof_digest": temporary["artifact_storage_mapping_proof_digest"],
            "labels_digest": temporary["labels_digest"],
            "mount_resolution_digest": temporary["mount_resolution_digest"],
            "schema_version": "synaptic-host-docker-create-path-binding/v1",
            "source_read_only": temporary["source_read_only"],
            "source_ref": temporary["source_ref"],
            "source_request_digest": temporary["source_request"].request_digest,
            "source_mapping_pair_proof_digest": temporary["source_mapping_pair_proof_digest"],
            "source_storage_mapping_proof_digest": temporary["source_storage_mapping_proof_digest"],
        }
        return cls(**values, binding_digest=digest_v1(body))


_ENV_KEY = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass(frozen=True, slots=True)
class DockerWorkloadEnvironmentEntryV1:
    key: str
    key_digest: str
    value_digest: str
    entry_digest: str

    def canonical_without_digest(self):
        return {
            "key": self.key,
            "key_digest": self.key_digest,
            "schema_version": "synaptic-host-docker-workload-env-entry/v1",
            "value_digest": self.value_digest,
        }

    def __post_init__(self):
        if (
            type(self.key) is not str
            or _ENV_KEY.fullmatch(self.key) is None
            or len(self.key.encode("utf-8")) > 128
            or self.key_digest != _plain_sha(self.key)
        ):
            _fail()
        _sha(self.value_digest)
        _sha(self.entry_digest)
        if self.entry_digest != digest_v1(self.canonical_without_digest()):
            _fail()

    @classmethod
    def build(cls, key, value):
        try:
            if (
                type(key) is not str
                or type(value) is not str
                or not 1 <= len(f"{key}={value}".encode("utf-8"))
                <= MAX_DOCKER_ARG_BYTES_V1
            ):
                raise ValueError
            key_digest = _plain_sha(key)
            value_digest = _plain_sha(value)
            body = {
                "key": key,
                "key_digest": key_digest,
                "schema_version": "synaptic-host-docker-workload-env-entry/v1",
                "value_digest": value_digest,
            }
            return cls(key, key_digest, value_digest, digest_v1(body))
        except BaseException:
            _fail()


def _snapshot_env_entry(value):
    try:
        rebuilt = DockerWorkloadEnvironmentEntryV1(
            value.key, value.key_digest, value.value_digest, value.entry_digest
        )
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _fail()


@dataclass(frozen=True, slots=True)
class DockerWorkloadEnvironmentBindingV1:
    workload_digest: str
    requested_keys: tuple[str, ...]
    supplied_entries: tuple[DockerWorkloadEnvironmentEntryV1, ...]
    binding_digest: str

    def canonical_without_digest(self):
        return {
            "requested_keys": list(self.requested_keys),
            "schema_version": "synaptic-host-docker-workload-env-binding/v1",
            "supplied_entry_digests": [item.entry_digest for item in self.supplied_entries],
            "workload_digest": self.workload_digest,
        }

    def __post_init__(self):
        try:
            entries = tuple(_snapshot_env_entry(item) for item in self.supplied_entries)
            if (
                type(self.requested_keys) is not tuple
                or type(self.supplied_entries) is not tuple
                or not 0 <= len(self.requested_keys) <= MAX_WORKLOAD_ENV_ENTRIES_V1
                or tuple(sorted(set(self.requested_keys))) != self.requested_keys
                or tuple(sorted(entries, key=lambda item: item.key)) != entries
                or tuple(item.key for item in entries) != self.requested_keys
            ):
                raise ValueError
            _sha(self.workload_digest)
            _sha(self.binding_digest)
            if self.binding_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except DockerControlContractErrorV1:
            raise
        except BaseException:
            _fail()

    @classmethod
    def build(cls, workload_digest, requested_keys, supplied_entries):
        requested_keys = tuple(requested_keys)
        supplied_entries = tuple(supplied_entries)
        body = {
            "requested_keys": list(requested_keys),
            "schema_version": "synaptic-host-docker-workload-env-binding/v1",
            "supplied_entry_digests": [item.entry_digest for item in supplied_entries],
            "workload_digest": workload_digest,
        }
        return cls(workload_digest, requested_keys, supplied_entries, digest_v1(body))


def _snapshot_contract_content(value):
    try:
        if type(value) is DockerCreatePathBindingV1:
            return DockerCreatePathBindingV1(
                value.labels_digest, value.source_ref, value.artifact_ref,
                value.mount_resolution_digest,
                value.source_storage_mapping_proof_digest,
                value.artifact_storage_mapping_proof_digest,
                value.source_mapping_pair_proof_digest,
                value.artifact_mapping_pair_proof_digest,
                _snapshot_path_request(value.source_request),
                _snapshot_path_request(value.artifact_request),
                value.source_read_only, value.binding_digest,
            )
        if type(value) is DockerWorkloadEnvironmentBindingV1:
            return DockerWorkloadEnvironmentBindingV1(
                value.workload_digest, tuple(value.requested_keys),
                tuple(_snapshot_env_entry(item) for item in value.supplied_entries),
                value.binding_digest,
            )
        if type(value) is DockerControlIntentV1:
            return DockerControlIntentV1(
                value.operation_id, value.operation, value.effect_id,
                value.engine_command_digest, value.labels_digest,
                value.container_name, value.create_specification_digest,
                value.cli_command_digest, value.cli_policy_digest, value.container_ref,
                value.verified_create_record_digest, value.intent_digest,
            )
        if type(value) is DockerMutationRecordV1:
            return DockerMutationRecordV1(
                value.operation_id, value.operation, value.effect_id,
                value.control_intent_proof_digest, value.phase,
                value.revision, value.attempt_count,
                value.previous_record_digest, value.container_ref,
                value.verification_result_digest, value.record_digest,
            )
        if type(value) is DockerExpectedCreateBindingV1:
            return DockerExpectedCreateBindingV1(
                snapshot_docker_labels_v1(value.labels),
                DockerCreateSpecificationV1(
                    *(getattr(value.create_specification, name)
                      for name in value.create_specification.__dataclass_fields__)
                ),
                _snapshot_authenticated(value.intent),
                _snapshot_authenticated(value.environment_binding),
                value.binding_digest,
            )
        raise ValueError
    except DockerControlContractErrorV1:
        raise
    except BaseException:
        _fail()


def _envelope_post(value, content_type, content_digest):
    if type(value.content) is not content_type:
        _fail(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
    rebuilt = _snapshot_contract_content(value.content)
    if rebuilt != value.content:
        _fail(DockerControlContractCodeV1.AUTHENTICATION_FAILED)
    _ref(value.authority_ref)
    _ref(value.key_ref)
    _sha(value.tag)
    content_digest(value.content)


def _envelope_proof(value, content_digest, schema):
    return digest_v1({
        "authority_ref": value.authority_ref,
        "content_digest": content_digest(value.content),
        "key_ref": value.key_ref,
        "schema_version": schema,
        "tag": value.tag,
    })


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerCreatePathBindingV1:
    content: DockerCreatePathBindingV1
    authority_ref: str
    key_ref: str
    tag: str
    def __post_init__(self):
        _envelope_post(self, DockerCreatePathBindingV1, lambda x: x.binding_digest)
    @property
    def proof_digest(self):
        return _envelope_proof(self, lambda x: x.binding_digest, "synaptic-host-auth-create-path-binding/v1")


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerWorkloadEnvironmentBindingV1:
    content: DockerWorkloadEnvironmentBindingV1
    authority_ref: str
    key_ref: str
    tag: str
    def __post_init__(self):
        _envelope_post(self, DockerWorkloadEnvironmentBindingV1, lambda x: x.binding_digest)
    @property
    def proof_digest(self):
        return _envelope_proof(self, lambda x: x.binding_digest, "synaptic-host-auth-workload-env-binding/v1")


SOURCE_DESTINATION_V1 = "/source"
ARTIFACT_DESTINATION_V1 = "/artifacts"


@dataclass(frozen=True, slots=True)
class DockerCreateSpecificationV1:
    labels_digest: str
    owned_labels_projection_digest: str
    container_name: str
    image_digest: str
    runtime_digest: str
    workload_digest: str
    argument_count: int
    arguments_digest: str
    working_directory_digest: str
    environment_binding_proof_digest: str
    mount_resolution_digest: str
    path_binding_proof_digest: str
    source_windows_path_digest: str
    source_unc_digest: str
    source_destination_digest: str
    source_read_only: bool
    artifact_windows_path_digest: str
    artifact_unc_digest: str
    artifact_destination_digest: str
    artifact_read_write: bool
    network_mode: str
    nano_cpus: int
    memory_bytes: int
    device_requests_digest: str
    endpoint_descriptor_digest: str
    specification_digest: str

    def canonical_without_digest(self):
        return {name: getattr(self, name) for name in self.__dataclass_fields__
                if name != "specification_digest"} | {
            "schema_version": "synaptic-host-docker-create-specification/v1"
        }

    def __post_init__(self):
        for name in (
            "labels_digest", "owned_labels_projection_digest",
            "runtime_digest", "workload_digest", "arguments_digest",
            "working_directory_digest",
            "environment_binding_proof_digest", "mount_resolution_digest",
            "path_binding_proof_digest", "source_windows_path_digest",
            "source_unc_digest", "source_destination_digest",
            "artifact_windows_path_digest", "artifact_unc_digest",
            "artifact_destination_digest", "device_requests_digest",
            "endpoint_descriptor_digest",
            "specification_digest",
        ):
            _sha(getattr(self, name))
        if (
            type(self.container_name) is not str
            or _CONTAINER_NAME.fullmatch(self.container_name) is None
        ):
            _fail()
        if (
            type(self.image_digest) is not str
            or re.fullmatch(r"sha256:[0-9a-f]{64}", self.image_digest) is None
            or self.source_destination_digest != _plain_sha(SOURCE_DESTINATION_V1)
            or self.artifact_destination_digest != _plain_sha(ARTIFACT_DESTINATION_V1)
            or self.source_read_only is not True
            or self.artifact_read_write is not True
            or self.network_mode != "none"
            or type(self.argument_count) is not int
            or not 1 <= self.argument_count <= 64
            or type(self.nano_cpus) is not int
            or not 1_000_000_000 <= self.nano_cpus <= 256_000_000_000
            or self.nano_cpus % 1_000_000_000 != 0
            or type(self.memory_bytes) is not int
            or not 1 <= self.memory_bytes <= 2**50
            or self.specification_digest != digest_v1(self.canonical_without_digest())
        ):
            _fail()

    @classmethod
    def build(cls, **values):
        body = dict(values)
        body["schema_version"] = "synaptic-host-docker-create-specification/v1"
        return cls(**values, specification_digest=digest_v1(body))


class DockerControlOperationV1(str, Enum):
    CREATE = "CREATE"
    START = "START"


def docker_operation_id_v1(operation, effect_id):
    if type(operation) is not DockerControlOperationV1:
        _fail()
    _ref(effect_id)
    return digest_v1({"effect_id": effect_id, "operation": operation.value,
                      "schema_version": "synaptic-host-docker-operation-id/v1"})


@dataclass(frozen=True, slots=True)
class DockerControlIntentV1:
    operation_id: str
    operation: DockerControlOperationV1
    effect_id: str
    engine_command_digest: str
    labels_digest: str
    container_name: str
    create_specification_digest: str
    cli_command_digest: str
    cli_policy_digest: str
    container_ref: str | None
    verified_create_record_digest: str | None
    intent_digest: str

    def canonical_without_digest(self):
        return {name: getattr(self, name).value if name == "operation" else getattr(self, name)
                for name in self.__dataclass_fields__ if name != "intent_digest"} | {
            "schema_version": "synaptic-host-docker-control-intent/v1"
        }

    def __post_init__(self):
        for value in (self.operation_id, self.engine_command_digest,
                      self.labels_digest, self.create_specification_digest,
                      self.cli_command_digest, self.cli_policy_digest,
                      self.intent_digest):
            _sha(value)
        _ref(self.effect_id)
        if (
            type(self.container_name) is not str
            or _CONTAINER_NAME.fullmatch(self.container_name) is None
        ):
            _fail()
        if self.operation_id != docker_operation_id_v1(self.operation, self.effect_id):
            _fail()
        if self.operation is DockerControlOperationV1.CREATE:
            if self.container_ref is not None or self.verified_create_record_digest is not None:
                _fail()
        elif self.operation is DockerControlOperationV1.START:
            if (
                type(self.container_ref) is not str
                or _CONTAINER_REF.fullmatch(self.container_ref) is None
            ):
                _fail()
            _sha(self.verified_create_record_digest)
        else:
            _fail()
        if self.intent_digest != digest_v1(self.canonical_without_digest()):
            _fail()

    @classmethod
    def build(cls, **values):
        body = {name: value.value if name == "operation" else value
                for name, value in values.items()}
        body["schema_version"] = "synaptic-host-docker-control-intent/v1"
        return cls(**values, intent_digest=digest_v1(body))


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerControlIntentV1:
    content: DockerControlIntentV1
    authority_ref: str
    key_ref: str
    tag: str
    def __post_init__(self):
        _envelope_post(self, DockerControlIntentV1, lambda x: x.intent_digest)
    @property
    def proof_digest(self):
        return _envelope_proof(self, lambda x: x.intent_digest, "synaptic-host-auth-control-intent/v1")


@dataclass(frozen=True, slots=True)
class DockerExpectedCreateBindingV1:
    labels: DockerLabelsV1
    create_specification: DockerCreateSpecificationV1
    intent: AuthenticatedDockerControlIntentV1
    environment_binding: AuthenticatedDockerWorkloadEnvironmentBindingV1
    binding_digest: str

    def canonical_without_digest(self):
        return {
            "create_specification_digest": self.create_specification.specification_digest,
            "environment_binding_proof_digest": self.environment_binding.proof_digest,
            "intent_proof_digest": self.intent.proof_digest,
            "labels_digest": self.labels.digest,
            "schema_version": "synaptic-host-docker-expected-create-binding/v1",
        }

    def __post_init__(self):
        try:
            labels = snapshot_docker_labels_v1(self.labels)
            specification = DockerCreateSpecificationV1(
                *(getattr(self.create_specification, name)
                  for name in self.create_specification.__dataclass_fields__)
            )
            intent = _snapshot_authenticated(self.intent)
            environment = _snapshot_authenticated(self.environment_binding)
            if (
                labels.effect_kind != "submit"
                or specification.labels_digest != labels.digest
                or specification.container_name != labels.container_name
                or specification.environment_binding_proof_digest
                != environment.proof_digest
                or specification.workload_digest != environment.content.workload_digest
                or intent.content.operation is not DockerControlOperationV1.CREATE
                or intent.content.effect_id != labels.effect_id
                or intent.content.engine_command_digest != labels.command_digest
                or intent.content.labels_digest != labels.digest
                or intent.content.container_name != labels.container_name
                or intent.content.create_specification_digest
                != specification.specification_digest
                or intent.content.container_ref is not None
                or intent.content.verified_create_record_digest is not None
                or self.binding_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except BaseException:
            _fail()

    @classmethod
    def build(cls, labels, create_specification, intent, environment_binding):
        body = {
            "create_specification_digest": create_specification.specification_digest,
            "environment_binding_proof_digest": environment_binding.proof_digest,
            "intent_proof_digest": intent.proof_digest,
            "labels_digest": labels.digest,
            "schema_version": "synaptic-host-docker-expected-create-binding/v1",
        }
        return cls(labels, create_specification, intent, environment_binding, digest_v1(body))


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerExpectedCreateBindingV1:
    content: DockerExpectedCreateBindingV1
    authority_ref: str
    key_ref: str
    tag: str

    def __post_init__(self):
        _envelope_post(self, DockerExpectedCreateBindingV1, lambda x: x.binding_digest)

    @property
    def proof_digest(self):
        return _envelope_proof(
            self, lambda x: x.binding_digest,
            "synaptic-host-auth-expected-create-binding/v1",
        )


class DockerExpectedCreatePublishDispositionV1(str, Enum):
    PUBLISHED = "PUBLISHED"
    EXISTING = "EXISTING"
    CONFLICT = "CONFLICT"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class DockerExpectedCreatePublishRequestV1:
    engine_command_digest: str
    labels_digest: str
    candidate: AuthenticatedDockerExpectedCreateBindingV1
    request_digest: str

    def canonical_without_digest(self):
        return {
            "candidate_proof_digest": self.candidate.proof_digest,
            "engine_command_digest": self.engine_command_digest,
            "labels_digest": self.labels_digest,
            "schema_version": "synaptic-host-docker-expected-publish-request/v1",
        }

    def __post_init__(self):
        try:
            _sha(self.engine_command_digest)
            _sha(self.labels_digest)
            _sha(self.request_digest)
            candidate = _snapshot_authenticated(self.candidate)
            labels = candidate.content.labels
            if (
                type(candidate) is not AuthenticatedDockerExpectedCreateBindingV1
                or self.engine_command_digest != labels.command_digest
                or self.labels_digest != labels.digest
                or self.request_digest != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except BaseException:
            _fail()

    @classmethod
    def build(cls, engine_command_digest, labels_digest, candidate):
        body = {
            "candidate_proof_digest": candidate.proof_digest,
            "engine_command_digest": engine_command_digest,
            "labels_digest": labels_digest,
            "schema_version": "synaptic-host-docker-expected-publish-request/v1",
        }
        return cls(
            engine_command_digest, labels_digest, candidate, digest_v1(body)
        )


@dataclass(frozen=True, slots=True)
class DockerExpectedCreatePublishResultV1:
    request: DockerExpectedCreatePublishRequestV1
    disposition: DockerExpectedCreatePublishDispositionV1
    binding: AuthenticatedDockerExpectedCreateBindingV1 | None
    result_digest: str

    def canonical_without_digest(self):
        return {
            "binding_proof_digest": (
                None if self.binding is None else self.binding.proof_digest
            ),
            "disposition": self.disposition.value,
            "request_digest": self.request.request_digest,
            "schema_version": "synaptic-host-docker-expected-publish-result/v1",
        }

    def __post_init__(self):
        try:
            request = DockerExpectedCreatePublishRequestV1(
                self.request.engine_command_digest, self.request.labels_digest,
                _snapshot_authenticated(self.request.candidate),
                self.request.request_digest,
            )
            if type(self.disposition) is not DockerExpectedCreatePublishDispositionV1:
                raise ValueError
            binding = (
                None if self.binding is None
                else _snapshot_authenticated(self.binding)
            )
            required = self.disposition is not DockerExpectedCreatePublishDispositionV1.INDETERMINATE
            if (binding is not None) != required:
                raise ValueError
            if binding is not None:
                labels = binding.content.labels
                if (
                    labels.command_digest != request.engine_command_digest
                    or labels.digest != request.labels_digest
                ):
                    raise ValueError
                same = binding == request.candidate
                if self.disposition in (
                    DockerExpectedCreatePublishDispositionV1.PUBLISHED,
                    DockerExpectedCreatePublishDispositionV1.EXISTING,
                ) and not same:
                    raise ValueError
                if self.disposition is DockerExpectedCreatePublishDispositionV1.CONFLICT and same:
                    raise ValueError
            _sha(self.result_digest)
            if self.result_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except BaseException:
            _fail()

    @classmethod
    def build(cls, request, disposition, binding):
        body = {
            "binding_proof_digest": (
                None if binding is None else binding.proof_digest
            ),
            "disposition": disposition.value,
            "request_digest": request.request_digest,
            "schema_version": "synaptic-host-docker-expected-publish-result/v1",
        }
        return cls(request, disposition, binding, digest_v1(body))


@dataclass(frozen=True, slots=True)
class DockerCreateVerificationV1:
    operation_id: str
    attempted_record_digest: str
    expected_proof_digest: str
    create_result_digest: str | None
    inventory_result_digest: str
    post_resolution_digest: str
    post_path_binding_proof_digest: str
    source_windows_path_digest: str
    source_unc_digest: str
    artifact_windows_path_digest: str
    artifact_unc_digest: str
    inspect_result_digest: str
    container_ref: str
    verification_digest: str

    def canonical_without_digest(self):
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "verification_digest"
        } | {"schema_version": "synaptic-host-docker-create-verification/v1"}

    def __post_init__(self):
        try:
            for name in self.__dataclass_fields__:
                value = getattr(self, name)
                if name == "create_result_digest" and value is None:
                    continue
                _sha(value)
            if _CONTAINER_REF.fullmatch(self.container_ref) is None:
                raise ValueError
            if self.verification_digest != digest_v1(self.canonical_without_digest()):
                raise ValueError
        except BaseException:
            _fail()

    @classmethod
    def build(cls, **values):
        body = dict(values)
        body["schema_version"] = "synaptic-host-docker-create-verification/v1"
        return cls(**values, verification_digest=digest_v1(body))


@dataclass(frozen=True, slots=True)
class DockerStartVerificationV1:
    operation_id: str
    attempted_record_digest: str
    expected_proof_digest: str
    verified_create_record_digest: str
    start_execution_result_digest: str | None
    pre_inspect_result_digest: str
    post_inspect_result_digest: str
    container_ref: str
    verification_digest: str

    def canonical_without_digest(self):
        return {
            name: getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "verification_digest"
        } | {"schema_version": "synaptic-host-docker-start-verification/v1"}

    def __post_init__(self):
        try:
            for name in self.__dataclass_fields__:
                value = getattr(self, name)
                if name == "start_execution_result_digest" and value is None:
                    continue
                _sha(value)
            if (
                _CONTAINER_REF.fullmatch(self.container_ref) is None
                or self.verification_digest
                != digest_v1(self.canonical_without_digest())
            ):
                raise ValueError
        except BaseException:
            _fail()

    @classmethod
    def build(cls, **values):
        body = dict(values)
        body["schema_version"] = "synaptic-host-docker-start-verification/v1"
        return cls(**values, verification_digest=digest_v1(body))


class DockerMutationPhaseV1(str, Enum):
    ADMITTED = "ADMITTED"
    ATTEMPTED = "ATTEMPTED"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True, slots=True)
class DockerMutationRecordV1:
    operation_id: str
    operation: DockerControlOperationV1
    effect_id: str
    control_intent_proof_digest: str
    phase: DockerMutationPhaseV1
    revision: int
    attempt_count: int
    previous_record_digest: str | None
    container_ref: str | None
    verification_result_digest: str | None
    record_digest: str

    def canonical_without_digest(self):
        return {name: getattr(self, name).value if name in ("operation", "phase") else getattr(self, name)
                for name in self.__dataclass_fields__ if name != "record_digest"} | {
            "schema_version": "synaptic-host-docker-mutation-record/v1"
        }

    def __post_init__(self):
        _sha(self.operation_id)
        _sha(self.control_intent_proof_digest)
        _sha(self.record_digest)
        _ref(self.effect_id)
        matrix = {
            DockerMutationPhaseV1.ADMITTED: (1, 0, False, False),
            DockerMutationPhaseV1.ATTEMPTED: (2, 1, True, False),
            DockerMutationPhaseV1.VERIFIED: (3, 1, True, True),
        }
        if (
            type(self.phase) is not DockerMutationPhaseV1
            or type(self.operation) is not DockerControlOperationV1
            or type(self.revision) is not int
            or type(self.attempt_count) is not int
        ):
            _fail()
        if self.operation_id != docker_operation_id_v1(
            self.operation, self.effect_id
        ):
            _fail()
        expected = matrix[self.phase]
        has_previous = self.previous_record_digest is not None
        has_evidence = self.container_ref is not None and self.verification_result_digest is not None
        if (self.revision, self.attempt_count, has_previous, has_evidence) != expected:
            _fail()
        if self.phase is not DockerMutationPhaseV1.VERIFIED and (
            self.container_ref is not None
            or self.verification_result_digest is not None
        ):
            _fail()
        if has_previous:
            _sha(self.previous_record_digest)
        if self.container_ref is not None:
            if (
                type(self.container_ref) is not str
                or _CONTAINER_REF.fullmatch(self.container_ref) is None
            ):
                _fail()
        if self.verification_result_digest is not None:
            _sha(self.verification_result_digest)
        if self.record_digest != digest_v1(self.canonical_without_digest()):
            _fail()

    @classmethod
    def build(cls, **values):
        body = {name: value.value if name in ("operation", "phase") else value
                for name, value in values.items()}
        body["schema_version"] = "synaptic-host-docker-mutation-record/v1"
        return cls(**values, record_digest=digest_v1(body))


@dataclass(frozen=True, slots=True)
class AuthenticatedDockerMutationRecordV1:
    content: DockerMutationRecordV1
    authority_ref: str
    key_ref: str
    tag: str
    def __post_init__(self):
        _envelope_post(self, DockerMutationRecordV1, lambda x: x.record_digest)
    @property
    def proof_digest(self):
        return _envelope_proof(self, lambda x: x.record_digest, "synaptic-host-auth-mutation-record/v1")


def _snapshot_authenticated(value):
    try:
        if type(value) is AuthenticatedDockerCreatePathBindingV1:
            return AuthenticatedDockerCreatePathBindingV1(
                _snapshot_contract_content(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
        if type(value) is AuthenticatedDockerWorkloadEnvironmentBindingV1:
            return AuthenticatedDockerWorkloadEnvironmentBindingV1(
                _snapshot_contract_content(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
        if type(value) is AuthenticatedDockerControlIntentV1:
            return AuthenticatedDockerControlIntentV1(
                _snapshot_contract_content(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
        if type(value) is AuthenticatedDockerMutationRecordV1:
            return AuthenticatedDockerMutationRecordV1(
                _snapshot_contract_content(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
        if type(value) is AuthenticatedDockerExpectedCreateBindingV1:
            return AuthenticatedDockerExpectedCreateBindingV1(
                _snapshot_contract_content(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )
        if type(value) is AuthenticatedDockerAbsenceV1:
            content = DockerAbsenceContentV1(
                value.content.request_digest, value.content.labels_digest,
                value.content.purpose, value.content.generation,
                value.content.evidence_digest,
            )
            return AuthenticatedDockerAbsenceV1(
                content, value.authority_ref, value.key_ref, value.tag
            )
        raise ValueError
    except BaseException:
        _fail(DockerControlContractCodeV1.AUTHENTICATION_FAILED)


def _authenticate_exact(authority, value, envelope_type):
    try:
        if (
            type(value) is not envelope_type
            or type(authority.authority_ref) is not str
            or type(authority.key_ref) is not str
        ):
            raise ValueError
        presented = _snapshot_authenticated(value)
        if (
            presented.authority_ref != authority.authority_ref
            or presented.key_ref != authority.key_ref
        ):
            raise ValueError
        returned = authority.authenticate(presented)
        returned = _snapshot_authenticated(returned)
        if (
            type(returned) is not envelope_type
            or returned.authority_ref != authority.authority_ref
            or returned.key_ref != authority.key_ref
            or returned != presented
        ):
            raise ValueError
        return returned
    except BaseException:
        _fail(DockerControlContractCodeV1.AUTHENTICATION_FAILED)


def authenticate_create_path_binding_v1(authority, value):
    return _authenticate_exact(authority, value, AuthenticatedDockerCreatePathBindingV1)


def authenticate_workload_environment_binding_v1(authority, value):
    return _authenticate_exact(
        authority, value, AuthenticatedDockerWorkloadEnvironmentBindingV1
    )


def authenticate_control_intent_v1(authority, value):
    return _authenticate_exact(authority, value, AuthenticatedDockerControlIntentV1)


def authenticate_mutation_record_v1(authority, value):
    return _authenticate_exact(authority, value, AuthenticatedDockerMutationRecordV1)


def authenticate_absence_v1(authority, value):
    return _authenticate_exact(authority, value, AuthenticatedDockerAbsenceV1)


def authenticate_expected_create_binding_v1(authority, value):
    return _authenticate_exact(
        authority, value, AuthenticatedDockerExpectedCreateBindingV1
    )


def snapshot_docker_labels_v1(value):
    try:
        if type(value) is not DockerLabelsV1:
            raise ValueError
        rebuilt = DockerLabelsV1(**value.to_dict())
        if rebuilt != value:
            raise ValueError
        return rebuilt
    except BaseException:
        _fail()


def docker_owned_label_projections_v1(labels):
    labels = snapshot_docker_labels_v1(labels)
    values = docker_owned_label_values_v1(labels)
    return tuple(
        DockerLabelProjectionV1.build(name, _plain_sha(value))
        for name, value in zip(OWNED_LABEL_NAMES_V1, values, strict=True)
    )


def docker_owned_label_values_v1(labels):
    labels = snapshot_docker_labels_v1(labels)
    raw = labels.to_dict()
    values = tuple(
        raw[name.replace("-", "_")] for name in OWNED_LABEL_NAMES_V1[:-2]
    )
    return values + (labels.digest, "1")


def docker_arguments_projection_digest_v1(arguments):
    try:
        arguments = tuple(arguments)
        if any(type(value) is not str for value in arguments):
            raise ValueError
        return digest_v1({
            "arguments": [_plain_sha(value) for value in arguments],
            "schema_version": "synaptic-host-docker-argv-projection/v1",
        })
    except BaseException:
        _fail()


def docker_owned_labels_projection_digest_v1(labels):
    projections = docker_owned_label_projections_v1(labels)
    return digest_v1({
        "projection_digests": [item.projection_digest for item in projections],
        "schema_version": "synaptic-host-docker-owned-labels-projection/v1",
    })


class DockerAdmissionDispositionV1(str, Enum):
    ADMITTED = "ADMITTED"
    EXISTING = "EXISTING"
    CONFLICT = "CONFLICT"
    INDETERMINATE = "INDETERMINATE"
class DockerCASDispositionV1(str, Enum):
    APPLIED = "APPLIED"
    CURRENT = "CURRENT"
    INDETERMINATE = "INDETERMINATE"
class DockerMutationLookupDispositionV1(str, Enum):
    FOUND = "FOUND"
    ABSENT = "ABSENT"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True, slots=True)
class DockerMutationAdmissionRequestV1:
    operation_id: str
    candidate: AuthenticatedDockerMutationRecordV1
    request_digest: str

    def canonical_without_digest(self):
        return {
            "candidate_proof_digest": self.candidate.proof_digest,
            "operation_id": self.operation_id,
            "schema_version": "synaptic-host-docker-mutation-admission-request/v1",
        }

    def __post_init__(self):
        _sha(self.operation_id)
        _sha(self.request_digest)
        candidate = _snapshot_authenticated(self.candidate)
        if (
            type(candidate) is not AuthenticatedDockerMutationRecordV1
            or candidate.content.operation_id != self.operation_id
            or candidate.content.phase is not DockerMutationPhaseV1.ADMITTED
            or self.request_digest != digest_v1(self.canonical_without_digest())
        ):
            _fail()

    @classmethod
    def build(cls, operation_id, candidate):
        body = {
            "candidate_proof_digest": candidate.proof_digest,
            "operation_id": operation_id,
            "schema_version": "synaptic-host-docker-mutation-admission-request/v1",
        }
        return cls(operation_id, candidate, digest_v1(body))


@dataclass(frozen=True, slots=True)
class DockerMutationCASRequestV1:
    operation_id: str
    expected: AuthenticatedDockerMutationRecordV1
    replacement: AuthenticatedDockerMutationRecordV1
    request_digest: str

    @property
    def expected_record_digest(self):
        return self.expected.content.record_digest

    def canonical_without_digest(self):
        return {
            "expected_proof_digest": self.expected.proof_digest,
            "operation_id": self.operation_id,
            "replacement_proof_digest": self.replacement.proof_digest,
            "schema_version": "synaptic-host-docker-mutation-cas-request/v1",
        }

    def __post_init__(self):
        _sha(self.operation_id)
        _sha(self.request_digest)
        expected = _snapshot_authenticated(self.expected)
        replacement = _snapshot_authenticated(self.replacement)
        transitions = {
            (DockerMutationPhaseV1.ADMITTED, 1, 0):
                (DockerMutationPhaseV1.ATTEMPTED, 2, 1),
            (DockerMutationPhaseV1.ATTEMPTED, 2, 1):
                (DockerMutationPhaseV1.VERIFIED, 3, 1),
        }
        if (
            type(expected) is not AuthenticatedDockerMutationRecordV1
            or type(replacement) is not AuthenticatedDockerMutationRecordV1
            or expected.content.operation_id != self.operation_id
            or replacement.content.operation_id != self.operation_id
            or expected.content.operation is not replacement.content.operation
            or expected.content.control_intent_proof_digest
            != replacement.content.control_intent_proof_digest
            or expected.authority_ref != replacement.authority_ref
            or expected.key_ref != replacement.key_ref
            or replacement.content.previous_record_digest
            != expected.content.record_digest
            or transitions.get((
                expected.content.phase, expected.content.revision,
                expected.content.attempt_count,
            )) != (
                replacement.content.phase, replacement.content.revision,
                replacement.content.attempt_count,
            )
            or self.request_digest != digest_v1(self.canonical_without_digest())
        ):
            _fail()

    @classmethod
    def build(cls, operation_id, expected, replacement):
        body = {
            "expected_proof_digest": expected.proof_digest,
            "operation_id": operation_id,
            "replacement_proof_digest": replacement.proof_digest,
            "schema_version": "synaptic-host-docker-mutation-cas-request/v1",
        }
        return cls(operation_id, expected, replacement, digest_v1(body))


def _record_result_post(value, required):
    try:
        if (value.record is not None) != required:
            raise ValueError
        if value.record is not None:
            if type(value.record) is not AuthenticatedDockerMutationRecordV1:
                raise ValueError
            rebuilt = AuthenticatedDockerMutationRecordV1(
                _snapshot_contract_content(value.record.content),
                value.record.authority_ref, value.record.key_ref,
                value.record.tag,
            )
            if rebuilt != value.record:
                raise ValueError
        _sha(value.result_digest)
        if value.result_digest != digest_v1(value.canonical_without_digest()):
            raise ValueError
    except DockerControlContractErrorV1:
        raise
    except BaseException:
        _fail()


@dataclass(frozen=True, slots=True)
class DockerAdmissionResultV1:
    request: DockerMutationAdmissionRequestV1
    disposition: DockerAdmissionDispositionV1
    record: AuthenticatedDockerMutationRecordV1 | None
    result_digest: str
    def canonical_without_digest(self):
        return {"disposition": self.disposition.value, "record_proof_digest": None if self.record is None else self.record.proof_digest, "request_digest": self.request.request_digest, "schema_version":"synaptic-host-docker-admission-result/v1"}
    def __post_init__(self):
        try:
            request = DockerMutationAdmissionRequestV1(
                self.request.operation_id, _snapshot_authenticated(self.request.candidate),
                self.request.request_digest,
            )
            if type(self.disposition) is not DockerAdmissionDispositionV1:
                raise ValueError
            required = self.disposition is not DockerAdmissionDispositionV1.INDETERMINATE
            _record_result_post(self, required)
            if self.record is not None:
                candidate = request.candidate.content
                returned = self.record.content
                if returned.operation_id != request.operation_id:
                    raise ValueError
                if self.disposition is DockerAdmissionDispositionV1.ADMITTED and (
                    self.record.proof_digest != request.candidate.proof_digest
                    or returned.phase is not DockerMutationPhaseV1.ADMITTED
                ):
                    raise ValueError
                if self.disposition is DockerAdmissionDispositionV1.EXISTING and (
                    returned.control_intent_proof_digest
                    != candidate.control_intent_proof_digest
                ):
                    raise ValueError
                if self.disposition is DockerAdmissionDispositionV1.CONFLICT and (
                    returned.control_intent_proof_digest
                    == candidate.control_intent_proof_digest
                ):
                    raise ValueError
        except BaseException:
            _fail()
    @classmethod
    def build(cls, request, disposition, record):
        body = {"disposition": disposition.value, "record_proof_digest": None if record is None else record.proof_digest, "request_digest": request.request_digest, "schema_version":"synaptic-host-docker-admission-result/v1"}
        return cls(request, disposition, record, digest_v1(body))


@dataclass(frozen=True, slots=True)
class DockerCASResultV1:
    request: DockerMutationCASRequestV1
    disposition: DockerCASDispositionV1
    record: AuthenticatedDockerMutationRecordV1 | None
    result_digest: str
    def canonical_without_digest(self):
        return {"disposition": self.disposition.value, "record_proof_digest": None if self.record is None else self.record.proof_digest, "request_digest":self.request.request_digest,"schema_version":"synaptic-host-docker-cas-result/v1"}
    def __post_init__(self):
        try:
            request = DockerMutationCASRequestV1(
                self.request.operation_id,
                _snapshot_authenticated(self.request.expected),
                _snapshot_authenticated(self.request.replacement),
                self.request.request_digest,
            )
            if type(self.disposition) is not DockerCASDispositionV1:
                raise ValueError
            required = self.disposition is not DockerCASDispositionV1.INDETERMINATE
            _record_result_post(self, required)
            if self.record is not None:
                if self.record.content.operation_id != request.operation_id:
                    raise ValueError
                if (
                    self.disposition is DockerCASDispositionV1.APPLIED
                    and self.record.proof_digest != request.replacement.proof_digest
                ):
                    raise ValueError
        except BaseException:
            _fail()
    @classmethod
    def build(cls, request, disposition, record):
        body = {"disposition": disposition.value, "record_proof_digest": None if record is None else record.proof_digest, "request_digest":request.request_digest,"schema_version":"synaptic-host-docker-cas-result/v1"}
        return cls(request, disposition, record, digest_v1(body))


@dataclass(frozen=True, slots=True)
class DockerMutationLookupResultV1:
    operation_id: str
    disposition: DockerMutationLookupDispositionV1
    record: AuthenticatedDockerMutationRecordV1 | None
    result_digest: str
    def canonical_without_digest(self):
        return {"disposition":self.disposition.value,"operation_id":self.operation_id,"record_proof_digest":None if self.record is None else self.record.proof_digest,"schema_version":"synaptic-host-docker-mutation-lookup/v1"}
    def __post_init__(self):
        _sha(self.operation_id)
        if type(self.disposition) is not DockerMutationLookupDispositionV1:
            _fail()
        _record_result_post(self, self.disposition is DockerMutationLookupDispositionV1.FOUND)
        if (
            self.record is not None
            and self.record.content.operation_id != self.operation_id
        ):
            _fail()
    @classmethod
    def build(cls, operation_id, disposition, record):
        body = {"disposition":disposition.value,"operation_id":operation_id,"record_proof_digest":None if record is None else record.proof_digest,"schema_version":"synaptic-host-docker-mutation-lookup/v1"}
        return cls(operation_id, disposition, record, digest_v1(body))


__all__: tuple[str, ...] = ()
