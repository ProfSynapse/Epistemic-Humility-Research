from __future__ import annotations

from typing import Protocol

from .control_contract import (
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerControlContractCodeV1,
    DockerControlContractErrorV1,
    DockerWorkloadEnvironmentBindingV1,
    DockerWorkloadEnvironmentEntryV1,
    MAX_WORKLOAD_ENV_ENTRIES_V1,
    authenticate_workload_environment_binding_v1,
)
from .model import MAX_DOCKER_ARG_BYTES_V1


MAX_PRIVATE_ENV_TOTAL_BYTES_V1 = (
    MAX_WORKLOAD_ENV_ENTRIES_V1 * MAX_DOCKER_ARG_BYTES_V1
)


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


class DockerPrivateWorkloadEnvironmentResolverPortV1(Protocol):
    def resolve(self, workload) -> DockerPrivateWorkloadEnvironmentResolutionV1: ...


__all__: tuple[str, ...] = ()
