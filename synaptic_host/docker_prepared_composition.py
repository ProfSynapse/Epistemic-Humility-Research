"""Production composition root for one already-prepared Docker training run."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from threading import Thread
import time
from typing import Callable

from tuner.execution.foundation_v2.commands import SubmitCommandV2, parse_exact_command
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCommandBindingV1, DockerEffectIdentityV1, labels_for,
)

from .docker_execution import (
    DockerPreparedControlFactoryV1, DockerPreparedControlsV1,
    DockerPreparedRunRequestV1, DockerPreparedRunServiceV1,
    _DockerPreparedArtifactVerifierV1,
)
from .docker_v1.authority import (
    DockerAbsenceHmacAuthorityV1,
    DockerControlIntentHmacAuthorityV1,
    DockerCreatePathBindingHmacAuthorityV1,
    DockerExpectedCreateBindingHmacAuthorityV1,
    DockerMutationRecordHmacAuthorityV1,
    DockerWorkloadEnvironmentBindingHmacAuthorityV1,
)
from .docker_v1.binding import (
    DockerExplicitWorkloadEnvironmentResolverV1,
    DockerWorkloadEnvironmentPolicyV1,
)
from .docker_v1.control import DockerHostControlV1
from .docker_v1.control_contract import (
    DockerCreateAdmissionV1,
    DockerExpectedCreatePublishDispositionV1,
    DockerExpectedCreatePublishRequestV1,
)
from .docker_v1.create import DockerHostCreateV1
from .docker_v1.cli import DockerCLIRunnerV1
from .docker_v1.interop import (
    DockerPrivateWSLInteropChannelV1,
    DockerWSLExecutableBindingV1,
    DockerWSLInteropPopenFactoryV1,
)
from .docker_v1.memory import InMemoryDockerControlStoreV1
from .docker_v1.model import (
    DockerCLIEnvironmentV1,
    DockerCLIPolicyV1,
    DockerLocalEndpointDescriptorV1,
)
from .docker_v1.prepared import DockerPreparedMountAdapterV1
from .docker_v1.start import DockerHostStartV1
from .security import FileHmacAuthenticator


@dataclass(frozen=True, slots=True)
class DockerPreparedPlatformV1:
    typed_runner: object
    endpoint: DockerLocalEndpointDescriptorV1
    policy: DockerCLIPolicyV1
    distro: str

    def __post_init__(self) -> None:
        if (
            not callable(getattr(self.typed_runner, "create_container", None))
            or not callable(getattr(self.typed_runner, "inspect_container", None))
            or not callable(getattr(self.typed_runner, "start_container", None))
            or type(self.endpoint) is not DockerLocalEndpointDescriptorV1
            or type(self.policy) is not DockerCLIPolicyV1
            or self.policy.endpoint != self.endpoint
            or type(self.distro) is not str or not self.distro
        ):
            raise ValueError("prepared Docker platform is invalid")

    @property
    def endpoint_descriptor_digest(self) -> str:
        return self.endpoint.descriptor_digest

    @property
    def cli_policy_digest(self) -> str:
        return self.policy.policy_digest


def compose_docker_prepared_platform_v1(
    *, environment: dict[str, str] | None = None,
    lstat=os.lstat, popen_factory=subprocess.Popen,
    monotonic=time.monotonic, thread_factory=Thread,
) -> DockerPreparedPlatformV1:
    """Bind the fixed local Docker Desktop endpoint to one immutable stage."""

    values = os.environ if environment is None else environment
    required = ("SystemRoot", "TEMP", "TMP", "WINDIR")
    cli_environment = DockerCLIEnvironmentV1.build(
        tuple((key, values[key]) for key in required)
    )
    endpoint = DockerLocalEndpointDescriptorV1.build(
        "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False,
    )
    policy = DockerCLIPolicyV1.build(
        "/Docker/host/bin/docker.exe", endpoint, cli_environment,
    )
    interop_path = values.get("WSL_INTEROP")
    if type(interop_path) is not str or not interop_path:
        raise ValueError("WSL interoperability channel is unavailable")
    executable = DockerWSLExecutableBindingV1.build(policy.executable)
    channel = DockerPrivateWSLInteropChannelV1.acquire(
        interop_path, lstat=lstat,
    )
    popen = DockerWSLInteropPopenFactoryV1(
        executable=executable, environment=cli_environment, channel=channel,
        popen_factory=popen_factory,
    )
    runner = DockerCLIRunnerV1(
        policy, popen_factory=popen, monotonic=monotonic,
        thread_factory=thread_factory,
    )
    distro = values.get("WSL_DISTRO_NAME")
    if type(distro) is not str or not distro:
        raise ValueError("WSL distribution identity is unavailable")
    return DockerPreparedPlatformV1(runner, endpoint, policy, distro)


class _UnavailableMutationRepositoryV1:
    def __getattr__(self, _name):
        raise RuntimeError("mutation repository is unavailable during preparation")


class DockerPreparedControlBuilderV1:
    def __init__(
        self, *, authenticator: FileHmacAuthenticator,
        platform: DockerPreparedPlatformV1,
    ) -> None:
        if (
            type(authenticator) is not FileHmacAuthenticator
            or type(platform) is not DockerPreparedPlatformV1
            or authenticator.key_ref != "docker-control-v1"
            or authenticator.private_storage_verified is not True
        ):
            raise TypeError("exact Docker prepared composition dependencies required")
        self._authenticator = authenticator
        self._platform = platform
        self._path = DockerCreatePathBindingHmacAuthorityV1(
            authority_ref="docker-prepared-path-v1", authenticator=authenticator
        )
        self._environment = DockerWorkloadEnvironmentBindingHmacAuthorityV1(
            authority_ref="docker-prepared-environment-v1", authenticator=authenticator
        )
        self._intent = DockerControlIntentHmacAuthorityV1(
            authority_ref="docker-prepared-intent-v1", authenticator=authenticator
        )
        self._expected = DockerExpectedCreateBindingHmacAuthorityV1(
            authority_ref="docker-prepared-expected-v1", authenticator=authenticator
        )
        self._record = DockerMutationRecordHmacAuthorityV1(
            authority_ref="docker-prepared-mutation-v1", authenticator=authenticator
        )
        self._absence = DockerAbsenceHmacAuthorityV1(
            authority_ref="docker-prepared-absence-v1", authenticator=authenticator
        )

    def _assemble(self, *, request, mutation_repository, binding, labels):
        platform = self._platform
        if (
            self._authenticator.key_ref != "docker-control-v1"
            or self._authenticator.private_storage_verified is not True
            or type(request) is not DockerPreparedRunRequestV1
            or request.preparation.endpoint_descriptor_digest
            != platform.endpoint_descriptor_digest
            or request.preparation.cli_policy_digest != platform.cli_policy_digest
        ):
            raise ValueError("prepared Docker platform differs from durability")
        mount = DockerPreparedMountAdapterV1(
            request=request, binding=binding, labels=labels,
            distro=platform.distro, path_authority=self._path,
        )
        environment = tuple(request.staging.worker_bundle.dispatch.environment)
        keys = tuple(sorted(key for key, _value in environment))
        policy = DockerWorkloadEnvironmentPolicyV1.build(
            allowed_keys=keys, base_values=tuple(sorted(environment)),
        )
        environment_resolver = DockerExplicitWorkloadEnvironmentResolverV1(
            policy=policy, overrides=(), authority=self._environment,
        )
        catalog = InMemoryDockerControlStoreV1()
        create = DockerHostCreateV1(
            mount_resolver=mount, path_binder=mount, path_translator=mount,
            environment_resolver=environment_resolver,
            typed_runner=platform.typed_runner, expected_publisher=catalog,
            mutation_repository=mutation_repository,
            path_authority=self._path, environment_authority=self._environment,
            intent_authority=self._intent, expected_authority=self._expected,
            record_authority=self._record,
            endpoint_descriptor_digest=platform.endpoint_descriptor_digest,
            cli_policy_digest=platform.cli_policy_digest,
        )
        admission = create.prepare_admission(
            labels=labels, image=request.prepared_plan.profile.image,
            runtime=request.prepared_plan.profile.runtime,
            workload=request.prepared_plan.profile.workload,
            source_ref=request.prepared_plan.profile.roots.source_ref,
            artifact_ref=request.prepared_plan.profile.roots.artifact_ref,
            working_directory=request.staging.worker_bundle.dispatch.cwd.as_posix(),
        )
        published = catalog.publish_once(DockerExpectedCreatePublishRequestV1.build(
            labels.command_digest, labels.digest, admission.expected_create,
        ))
        if published.disposition not in {
            DockerExpectedCreatePublishDispositionV1.PUBLISHED,
            DockerExpectedCreatePublishDispositionV1.EXISTING,
        } or published.binding != admission.expected_create:
            raise ValueError("prepared Docker expected-create catalog rejected admission")
        start = DockerHostStartV1(
            typed_runner=platform.typed_runner,
            mutation_repository=mutation_repository,
            expected_catalog=catalog, expected_authority=self._expected,
            intent_authority=self._intent,
            environment_authority=self._environment,
            record_authority=self._record,
            endpoint_descriptor_digest=platform.endpoint_descriptor_digest,
            cli_policy_digest=platform.cli_policy_digest,
        )
        control = DockerHostControlV1(
            typed_cli=platform.typed_runner,
            mutation_repository=mutation_repository,
            mutation_record_authority=self._record,
            expected_catalog=catalog, expected_authority=self._expected,
            intent_authority=self._intent,
            environment_authority=self._environment,
            absence_authority=self._absence,
            cli_policy_digest=platform.cli_policy_digest,
        )
        return admission, DockerPreparedControlsV1(
            labels, admission.expected_create, create, start, control,
            platform.typed_runner,
        )

    def build(self, *, request, mutation_repository, binding, labels):
        return self._assemble(
            request=request, mutation_repository=mutation_repository,
            binding=binding, labels=labels,
        )[1]

    def prepare_admission(
        self, request: DockerPreparedRunRequestV1,
    ) -> DockerCreateAdmissionV1:
        command = parse_exact_command(request.preparation.submit_command_bytes)
        if type(command) is not SubmitCommandV2:
            raise ValueError("durable Docker command is not submit")
        identity = DockerEffectIdentityV1(
            command.digest, command.operation.effect.effect_id, "submit",
            request.prepared_plan,
        )
        binding = DockerCommandBindingV1(identity, command.canonical_bytes)
        return self._assemble(
            request=request, mutation_repository=_UnavailableMutationRepositoryV1(),
            binding=binding, labels=labels_for(identity),
        )[0]


class DockerPreparedCompositionV1:
    def __init__(
        self, *, repository: object, builder: DockerPreparedControlBuilderV1,
        clock: Callable[[], str], publication: object | None = None,
    ) -> None:
        if (
            type(builder) is not DockerPreparedControlBuilderV1
            or not callable(clock)
            or not callable(getattr(repository, "load_docker_run_mutation", None))
        ):
            raise ValueError("prepared Docker composition is invalid")
        self._builder = builder
        self._service = DockerPreparedRunServiceV1(
            repository=repository,
            control_factory=DockerPreparedControlFactoryV1(builder),
            artifact_verifier=_DockerPreparedArtifactVerifierV1(),
            clock=clock, publication=publication,
        )

    def prepare_admission(self, request):
        return self._builder.prepare_admission(request)

    def submit(self, request):
        return self._service.submit(request)

    def reconcile(self, request):
        return self._service.reconcile(request)


__all__ = [
    "DockerPreparedCompositionV1", "DockerPreparedControlBuilderV1",
    "DockerPreparedPlatformV1", "compose_docker_prepared_platform_v1",
]
