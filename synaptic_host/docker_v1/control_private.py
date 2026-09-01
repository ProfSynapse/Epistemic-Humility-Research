from __future__ import annotations

from threading import Lock
from typing import Protocol
import re

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.providers.docker_provider_v1.model import (
    DockerImageV1, DockerLabelsV1, DockerRuntimeV1, DockerWorkloadV1,
)

from .control_contract import (
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerControlContractCodeV1,
    DockerControlContractErrorV1,
    DockerWorkloadEnvironmentBindingV1,
    DockerWorkloadEnvironmentEntryV1,
    MAX_WORKLOAD_ENV_ENTRIES_V1,
    authenticate_workload_environment_binding_v1,
    docker_owned_label_values_v1,
    docker_safe_unc_v1,
)
from .control_model import (
    OWNED_LABEL_NAMES_V1, OWNED_LABEL_PREFIX_V1,
    DockerCreateExecutionResultV1,
    DockerStartExecutionResultV1,
    docker_start_execution_request_digest_v1,
)
from .model import (
    MAX_DOCKER_ARG_BYTES_V1, DockerCLICommandV1, DockerCLIVerbV1,
    DockerWindowsPathV1, DockerWSLPathPurposeV1,
)


MAX_PRIVATE_ENV_TOTAL_BYTES_V1 = (
    MAX_WORKLOAD_ENV_ENTRIES_V1 * MAX_DOCKER_ARG_BYTES_V1
)
_LOWER_HEX_64_V1 = re.compile(r"[0-9a-f]{64}\Z")


class DockerPrivateWorkloadEnvironmentResolutionV1:
    __slots__ = ("_binding", "_pairs")

    def __init__(self, binding, pairs):
        try:
            if type(binding) is not AuthenticatedDockerWorkloadEnvironmentBindingV1:
                raise ValueError
            pairs = tuple((key, value) for key, value in pairs)
            if len(pairs) > MAX_WORKLOAD_ENV_ENTRIES_V1:
                raise ValueError
            total = 0
            for key, value in pairs:
                if type(key) is not str or type(value) is not str:
                    raise ValueError
                size = len(f"{key}={value}".encode("utf-8"))
                if not 1 <= size <= MAX_DOCKER_ARG_BYTES_V1:
                    raise ValueError
                total += size
            if total > MAX_PRIVATE_ENV_TOTAL_BYTES_V1:
                raise ValueError
            self._binding = binding
            self._pairs = pairs
        except BaseException:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None

    def __repr__(self):
        return "DockerPrivateWorkloadEnvironmentResolutionV1(<redacted>)"

    __str__ = __repr__

    def __reduce__(self):
        raise DockerControlContractErrorV1(
            DockerControlContractCodeV1.INVALID
        ) from None

    def materialize_for_cli(self, authority):
        try:
            authenticated = authenticate_workload_environment_binding_v1(
                authority, self._binding
            )
            if type(authenticated) is not AuthenticatedDockerWorkloadEnvironmentBindingV1:
                raise ValueError
            binding = DockerWorkloadEnvironmentBindingV1(
                authenticated.content.workload_digest,
                tuple(authenticated.content.requested_keys),
                tuple(DockerWorkloadEnvironmentEntryV1(
                    item.key, item.key_digest, item.value_digest,
                    item.entry_digest,
                ) for item in authenticated.content.supplied_entries),
                authenticated.content.binding_digest,
            )
            expected = DockerWorkloadEnvironmentBindingV1.build(
                binding.workload_digest,
                tuple(key for key, _ in self._pairs),
                tuple(DockerWorkloadEnvironmentEntryV1.build(key, value)
                      for key, value in self._pairs),
            )
            if expected != binding:
                raise ValueError
            return tuple((key, value) for key, value in self._pairs)
        except BaseException:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.AUTHENTICATION_FAILED
            ) from None

    def authenticated_binding_snapshot(self, authority):
        try:
            authenticated = authenticate_workload_environment_binding_v1(
                authority, self._binding
            )
            if type(authenticated) is not AuthenticatedDockerWorkloadEnvironmentBindingV1:
                raise ValueError
            content = authenticated.content
            rebuilt = DockerWorkloadEnvironmentBindingV1(
                content.workload_digest, tuple(content.requested_keys),
                tuple(DockerWorkloadEnvironmentEntryV1(
                    item.key, item.key_digest, item.value_digest,
                    item.entry_digest,
                ) for item in content.supplied_entries),
                content.binding_digest,
            )
            return AuthenticatedDockerWorkloadEnvironmentBindingV1(
                rebuilt, authenticated.authority_ref, authenticated.key_ref,
                authenticated.tag,
            )
        except BaseException:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.AUTHENTICATION_FAILED
            ) from None


class DockerPrivateCreateInvocationV1:
    __slots__ = ("_command", "_container_name", "_consumed", "_lock")

    def __init__(self, command, container_name):
        try:
            if type(command) is not DockerCLICommandV1 or type(container_name) is not str:
                raise ValueError
            self._command = DockerCLICommandV1(
                command.verb, tuple(command.arguments), command.command_digest
            )
            self._container_name = container_name
            self._consumed = False
            self._lock = Lock()
        except BaseException:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None

    def __repr__(self):
        return "DockerPrivateCreateInvocationV1(<redacted>)"

    __str__ = __repr__

    def __reduce__(self):
        raise DockerControlContractErrorV1(
            DockerControlContractCodeV1.INVALID
        ) from None

    __copy__ = __reduce__

    def __deepcopy__(self, _memo):
        return self.__reduce__()

    @property
    def command_digest(self):
        return self._command.command_digest

    @property
    def container_name(self):
        return self._container_name

    def execute_once(self, runner):
        failed = False
        try:
            with self._lock:
                if self._consumed:
                    raise ValueError
                self._consumed = True
        except BaseException:
            failed = True
        if failed:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None
        try:
            result = runner.create_container(
                self._command, self._container_name
            )
        except BaseException:
            failed = True
        if failed:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None
        try:
            if type(result) is not DockerCreateExecutionResultV1:
                raise ValueError
            rebuilt = DockerCreateExecutionResultV1(
                result.result_kind, result.target, result.request_digest,
                result.command_digest, result.evidence, result.projection,
                result.result_digest,
            )
            if (
                rebuilt.target != self._container_name
                or rebuilt.command_digest != self._command.command_digest
            ):
                raise ValueError
        except BaseException:
            failed = True
        if failed:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None
        return rebuilt


class DockerPrivateStartInvocationV1:
    __slots__ = ("_command", "_container_ref", "_consumed", "_lock")

    def __init__(self, command, container_ref):
        try:
            if (
                type(command) is not DockerCLICommandV1
                or command.verb is not DockerCLIVerbV1.START
                or type(container_ref) is not str
                or _LOWER_HEX_64_V1.fullmatch(container_ref) is None
                or command.arguments != (container_ref,)
            ):
                raise ValueError
            self._command = DockerCLICommandV1(
                command.verb, tuple(command.arguments), command.command_digest
            )
            self._container_ref = container_ref
            docker_start_execution_request_digest_v1(
                container_ref, self._command.command_digest
            )
            self._consumed = False
            self._lock = Lock()
        except BaseException:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None

    def __repr__(self):
        return "DockerPrivateStartInvocationV1(<redacted>)"

    __str__ = __repr__

    def __reduce__(self):
        raise DockerControlContractErrorV1(
            DockerControlContractCodeV1.INVALID
        ) from None

    __copy__ = __reduce__

    def __deepcopy__(self, _memo):
        return self.__reduce__()

    @property
    def command_digest(self):
        return self._command.command_digest

    @property
    def container_ref(self):
        return self._container_ref

    @property
    def request_digest(self):
        return docker_start_execution_request_digest_v1(
            self._container_ref, self._command.command_digest
        )

    def execute_once(self, runner):
        failed = False
        try:
            with self._lock:
                if self._consumed:
                    raise ValueError
                self._consumed = True
        except BaseException:
            failed = True
        if failed:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None
        try:
            result = runner.start_container(
                self._command, self._container_ref
            )
        except BaseException:
            failed = True
        if failed:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None
        try:
            if type(result) is not DockerStartExecutionResultV1:
                raise ValueError
            rebuilt = DockerStartExecutionResultV1(
                result.result_kind, result.target, result.request_digest,
                result.command, result.command_digest, result.evidence,
                result.result_digest,
            )
            if (
                rebuilt.target != self._container_ref
                or rebuilt.command_digest != self._command.command_digest
                or rebuilt.request_digest != self.request_digest
            ):
                raise ValueError
        except BaseException:
            failed = True
        if failed:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None
        return rebuilt


class DockerPrivateCreateInvocationFactoryV1:
    def build(
        self, *, labels, image, runtime, workload, source_path,
        artifact_path, environment, environment_authority,
    ):
        try:
            if (
                type(labels) is not DockerLabelsV1
                or type(image) is not DockerImageV1
                or type(runtime) is not DockerRuntimeV1
                or type(workload) is not DockerWorkloadV1
                or type(source_path) is not DockerWindowsPathV1
                or type(artifact_path) is not DockerWindowsPathV1
                or type(environment) is not DockerPrivateWorkloadEnvironmentResolutionV1
            ):
                raise ValueError
            labels = DockerLabelsV1(**labels.to_dict())
            if labels.effect_kind != "submit":
                raise ValueError
            image = DockerImageV1(
                image.image_ref, image.image_digest, image.presence_policy
            )
            runtime = DockerRuntimeV1(
                runtime.cpu_count, runtime.memory_bytes, runtime.timeout_seconds,
                AcceleratorDeviceRequestV1(
                    runtime.accelerator_devices.kind,
                    tuple(runtime.accelerator_devices.device_indices),
                    tuple(runtime.accelerator_devices.capabilities),
                ),
                runtime.network_mode,
            )
            workload = DockerWorkloadV1(
                tuple(workload.arguments), tuple(workload.environment_keys),
                workload.workload_digest,
            )
            source_path = DockerWindowsPathV1(
                source_path.mapping_ref, source_path.mapping_digest,
                source_path.purpose, source_path.distro,
                source_path.posix_path, source_path.unc_path,
                source_path.path_digest,
            )
            artifact_path = DockerWindowsPathV1(
                artifact_path.mapping_ref, artifact_path.mapping_digest,
                artifact_path.purpose, artifact_path.distro,
                artifact_path.posix_path, artifact_path.unc_path,
                artifact_path.path_digest,
            )
            if (
                source_path.purpose is not DockerWSLPathPurposeV1.SOURCE_READ
                or artifact_path.purpose is not DockerWSLPathPurposeV1.ARTIFACT_WRITE
                or source_path.unc_path == artifact_path.unc_path
            ):
                raise ValueError
            binding = environment.authenticated_binding_snapshot(
                environment_authority
            )
            pairs = environment.materialize_for_cli(environment_authority)
            if (
                binding.content.workload_digest != workload.workload_digest
                or binding.content.requested_keys != workload.environment_keys
                or tuple(key for key, _ in pairs) != workload.environment_keys
            ):
                raise ValueError
            arguments = [
                "--name", labels.container_name, "--pull", "never",
                "--network", "none", "--cpus", str(runtime.cpu_count),
                "--memory", str(runtime.memory_bytes),
            ]
            if runtime.accelerator_devices.kind == "nvidia":
                arguments.extend(("--gpus", "driver=nvidia,device=0"))
            values = docker_owned_label_values_v1(labels)
            for name, value in zip(OWNED_LABEL_NAMES_V1, values, strict=True):
                arguments.extend((
                    "--label", f"{OWNED_LABEL_PREFIX_V1}{name}={value}"
                ))
            arguments.extend((
                "--mount",
                f"type=bind,source={docker_safe_unc_v1(source_path.unc_path)},destination=/source,readonly",
                "--mount",
                f"type=bind,source={docker_safe_unc_v1(artifact_path.unc_path)},destination=/artifacts",
            ))
            for key, value in pairs:
                arguments.extend(("--env", f"{key}={value}"))
            arguments.append(image.image_digest)
            arguments.extend(workload.arguments)
            command = DockerCLICommandV1.build(
                DockerCLIVerbV1.CREATE, tuple(arguments)
            )
            return DockerPrivateCreateInvocationV1(
                command, labels.container_name
            )
        except BaseException:
            raise DockerControlContractErrorV1(
                DockerControlContractCodeV1.INVALID
            ) from None


class DockerPrivateWorkloadEnvironmentResolverPortV1(Protocol):
    def resolve(self, workload) -> DockerPrivateWorkloadEnvironmentResolutionV1: ...


__all__: tuple[str, ...] = ()
