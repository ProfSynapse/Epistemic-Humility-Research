from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import pytest

from synaptic_tuner.api.v1.providers import ProviderCapabilities, ProviderDescriptor, ProviderRef
from synaptic_tuner.api.v1 import ProjectContext
from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.foundation_v2.commands import CanonicalProviderPayloadV1, build_submit_command
from tuner.execution.foundation_v2.executors import AdapterDescriptorV1, ExecutorDescriptorV1
from tuner.execution.foundation_v2.preparation import CanonicalPreparationV2
from tuner.execution.foundation_v2.references import ExecutionScopeV1, StagePredecessorV2
from tuner.execution.providers.docker_provider_v1.model import (
    DockerArtifactContractV1, DockerCommandBindingV1, DockerEffectIdentityV1,
    DockerImageV1, DockerProfileV1, DockerRootsV1, DockerRuntimeV1,
    DockerWorkloadV1, PreparedDockerPlanV1,
)

from synaptic_host.docker_prepared_composition import (
    DockerPreparedCompositionV1,
    DockerPreparedControlBuilderV1,
    DockerPreparedPlatformV1,
)
from synaptic_host.docker_v1.control_contract import DockerCreateAdmissionV1
from synaptic_host.docker_v1.model import (
    DockerCLIEnvironmentV1, DockerCLIPolicyV1,
    DockerLocalEndpointDescriptorV1,
)
from synaptic_host.docker_execution import DockerPreparedRunRequestV1
from synaptic_host.docker_execution_state import DockerStageProjectionV1
from synaptic_host.docker_staging import DockerStagingResultV1
from synaptic_host.security import FileHmacAuthenticator


class TypedRunner:
    def create_container(self, *_args, **_kwargs):
        raise AssertionError("preparation executed Docker")

    def start_container(self, *_args, **_kwargs):
        raise AssertionError("preparation executed Docker")

    def inspect_container(self, *_args, **_kwargs):
        raise AssertionError("preparation inspected Docker")

    def inventory_exact_name(self, *_args, **_kwargs):
        raise AssertionError("preparation inventoried Docker")


class Repository:
    def load_docker_run_mutation(self, *_args):
        return None

    def compare_and_swap_docker_run_mutation(self, *_args, **_kwargs):
        raise AssertionError("preparation mutated durability")


def _request(tmp_path: Path):
    stage_key = "a" * 64
    source_ref = f"host-stage://{stage_key}/source"
    artifact_ref = f"host-stage://{stage_key}/artifacts"
    provider = ProviderRef("docker", "prepared-test")
    scope = ExecutionScopeV1("local", "test")
    workload = DockerWorkloadV1(("python", "/source/worker.py"), (), "1" * 64)
    profile = DockerProfileV1.build(
        provider=provider,
        descriptor=ProviderDescriptor(
            "synaptic-provider-descriptor/v1", "docker", "Docker", "1.0.0",
            ProviderCapabilities(True, True, True, True, True, False),
        ),
        scope=scope,
        executor_descriptor=ExecutorDescriptorV1("docker", "executor", "1"),
        adapter_descriptor=AdapterDescriptorV1("docker", "adapter", "1"),
        image=DockerImageV1("image", "sha256:" + "2" * 64),
        runtime=DockerRuntimeV1(
            1, 1024, 60, AcceleratorDeviceRequestV1("cpu", (), ())
        ),
        workload=workload,
        roots=DockerRootsV1(source_ref, artifact_ref),
        artifacts=DockerArtifactContractV1(
            ("final_model", "tokenizer", "training_lineage", "training_metrics", "workload_record"),
            1024, 5120,
        ),
        resource_digest="3" * 64, quote_digest="4" * 64,
        secret_requirements_digest="5" * 64,
    )
    preparation = CanonicalPreparationV2.build(
        provider=provider, scope=scope, project_ref="project", run_id="run",
        plan_fingerprint="6" * 64, source_digest="7" * 64,
        workload_digest=workload.workload_digest,
        runtime_digest=profile.runtime.digest, resource_digest=profile.resource_digest,
        artifact_contract_digest=profile.artifacts.digest,
        quote_digest=profile.quote_digest,
        secret_requirements_digest=profile.secret_requirements_digest,
        execution_binding_digest="8" * 64,
    )
    prepared = PreparedDockerPlanV1(
        profile, "project", "run", "6" * 64, "7" * 64,
        preparation.preparation_digest,
    )
    predecessor = StagePredecessorV2(
        "docker", "prepared-test", "local", "test", "project", "run",
        "6" * 64, preparation.preparation_digest, workload.workload_digest,
        "stage-effect", "9" * 64, "a" * 64,
    )
    command = build_submit_command(
        preparation, "submit",
        CanonicalProviderPayloadV1.build("docker", "submit-payload/v2", workload.workload_digest),
        profile.executor_descriptor, predecessor,
    )
    stage = (tmp_path / "docker" / "stages" / stage_key).resolve()
    source = stage / "source"; source.mkdir(parents=True)
    artifacts = stage / "artifacts"; artifacts.mkdir()
    projection = DockerStageProjectionV1(
        source_ref, "b" * 64, artifact_ref, "c" * 64,
        "d" * 64, "e" * 64,
        "tuner/runtime/manifests/offline-sft-worker-v1.json", "f" * 64,
        "1" * 64, "2" * 64, "3" * 64,
    )
    staging = object.__new__(DockerStagingResultV1)
    object.__setattr__(staging, "projection", projection)
    object.__setattr__(staging, "source_root", source)
    object.__setattr__(staging, "artifact_root", artifacts)
    object.__setattr__(staging, "worker_bundle", SimpleNamespace(
        dispatch=SimpleNamespace(cwd=PurePosixPath("/artifacts/tmp"), environment=())
    ))
    endpoint = DockerLocalEndpointDescriptorV1.build(
        "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False,
    )
    environment = DockerCLIEnvironmentV1.build((
        ("SystemRoot", "C:\\Windows"), ("TEMP", "C:\\Temp"),
        ("TMP", "C:\\Temp"), ("WINDIR", "C:\\Windows"),
    ))
    policy = DockerCLIPolicyV1.build(
        "/Docker/host/bin/docker.exe", endpoint, environment,
    )
    record = SimpleNamespace(
        submit_command_bytes=command.canonical_bytes,
        preparation_digest="4" * 64,
        endpoint_descriptor_digest=endpoint.descriptor_digest,
        cli_policy_digest=policy.policy_digest,
    )
    request = object.__new__(DockerPreparedRunRequestV1)
    object.__setattr__(request, "preparation", record)
    object.__setattr__(request, "prepared_plan", prepared)
    object.__setattr__(request, "staging", staging)
    return request, endpoint, policy


def test_composition_prepares_exact_initial_admission_without_effects(tmp_path: Path):
    request, endpoint, policy = _request(tmp_path)
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    authenticator = FileHmacAuthenticator.for_docker(
        ProjectContext.host(engine_root=engine, project_root=project),
        durable_rows_exist=False,
    )
    platform = DockerPreparedPlatformV1(
        TypedRunner(), endpoint, policy, "Ubuntu-22.04",
    )
    assert platform.endpoint is endpoint
    assert platform.policy is policy
    assert platform.endpoint_descriptor_digest == endpoint.descriptor_digest
    assert platform.cli_policy_digest == policy.policy_digest
    builder = DockerPreparedControlBuilderV1(
        authenticator=authenticator, platform=platform,
    )
    composition = DockerPreparedCompositionV1(
        repository=Repository(), builder=builder,
        clock=lambda: "2026-09-01T12:00:00Z",
    )
    admission = composition.prepare_admission(request)
    assert type(admission) is DockerCreateAdmissionV1
    assert admission.create_mutation.content.phase.value == "ADMITTED"
    assert admission.expected_create.content.labels.effect_kind == "submit"


def test_builder_rejects_durable_platform_digest_drift_before_effects(tmp_path: Path):
    request, endpoint, policy = _request(tmp_path)
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    authenticator = FileHmacAuthenticator.for_docker(
        ProjectContext.host(engine_root=engine, project_root=project),
        durable_rows_exist=False,
    )
    platform = DockerPreparedPlatformV1(
        TypedRunner(), endpoint, policy, "Ubuntu-22.04",
    )
    builder = DockerPreparedControlBuilderV1(
        authenticator=authenticator, platform=platform,
    )
    object.__setattr__(
        request.preparation, "endpoint_descriptor_digest", "0" * 64,
    )
    with pytest.raises(ValueError, match="differs from durability"):
        builder.prepare_admission(request)


def test_builder_rejects_wrong_authenticator_key_reference(tmp_path: Path):
    _request_value, endpoint, policy = _request(tmp_path)
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    authenticator = FileHmacAuthenticator.for_docker(
        ProjectContext.host(engine_root=engine, project_root=project),
        durable_rows_exist=False,
    )
    authenticator.key_ref = "wrong-key"
    with pytest.raises(TypeError, match="exact Docker"):
        DockerPreparedControlBuilderV1(
            authenticator=authenticator,
            platform=DockerPreparedPlatformV1(
                TypedRunner(), endpoint, policy, "Ubuntu-22.04",
            ),
        )


def test_builder_live_rejects_lost_private_key_before_effects(tmp_path: Path):
    request, endpoint, policy = _request(tmp_path)
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    authenticator = FileHmacAuthenticator.for_docker(
        ProjectContext.host(engine_root=engine, project_root=project),
        durable_rows_exist=False,
    )
    builder = DockerPreparedControlBuilderV1(
        authenticator=authenticator,
        platform=DockerPreparedPlatformV1(
            TypedRunner(), endpoint, policy, "Ubuntu-22.04",
        ),
    )
    authenticator.key_path.unlink()
    with pytest.raises(ValueError, match="private storage"):
        builder.prepare_admission(request)
