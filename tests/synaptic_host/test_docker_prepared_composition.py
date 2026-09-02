from pathlib import Path, PurePosixPath
import subprocess
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
    compose_docker_prepared_platform_v1,
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


def _windows_platform(**changes):
    observed = {}
    endpoint = DockerLocalEndpointDescriptorV1.build(
        "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False,
    )

    def resolve(executable, context_ref, environment):
        observed.update(
            executable=executable, context_ref=context_ref,
            environment=dict(environment),
        )
        return endpoint

    arguments = {
        "docker_policy_ref": "docker-desktop-windows-v1",
        "wsl_distro": "Ubuntu-22.04",
        "drive_mount_root": "/mnt",
        "container_user": "1000:1000",
        "environment": {
            "PATH": "C:\\Docker", "SystemRoot": "C:\\Windows",
            "TEMP": "C:\\Temp", "TMP": "C:\\Temp",
            "WINDIR": "C:\\Windows", "HF_TOKEN": "must-not-forward",
        },
        "os_name": "nt",
        "executable_candidates": lambda _environment: (
            "C:\\Docker\\docker.exe",
        ),
        "endpoint_resolver": resolve,
    }
    arguments.update(changes)
    return compose_docker_prepared_platform_v1(**arguments), observed


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
        TypedRunner(), endpoint, policy, "Ubuntu-22.04", "/mnt", "1000:1000",
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
        TypedRunner(), endpoint, policy, "Ubuntu-22.04", "/mnt", "1000:1000",
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
                TypedRunner(), endpoint, policy, "Ubuntu-22.04", "/mnt", "1000:1000",
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
            TypedRunner(), endpoint, policy, "Ubuntu-22.04", "/mnt", "1000:1000",
        ),
    )
    authenticator.key_path.unlink()
    with pytest.raises(ValueError, match="private storage"):
        builder.prepare_admission(request)


def test_windows_factory_uses_absolute_cli_exact_endpoint_and_four_key_env():
    platform, observed = _windows_platform()
    assert platform.policy.executable == "C:\\Docker\\docker.exe"
    assert platform.endpoint.host == "npipe:////./pipe/dockerDesktopLinuxEngine"
    assert platform.endpoint.tls is False
    assert observed["context_ref"] == "desktop-linux"
    assert observed["environment"] == {
        "SystemRoot": "C:\\Windows", "TEMP": "C:\\Temp",
        "TMP": "C:\\Temp", "WINDIR": "C:\\Windows",
    }
    assert platform.policy.environment.entries == tuple(
        observed["environment"].items()
    )
    assert platform.typed_runner._popen is subprocess.Popen
    assert platform.distro == "Ubuntu-22.04"


def test_windows_factory_fails_closed_on_posix_or_ambiguous_cli():
    with pytest.raises(ValueError, match="Windows Docker Host"):
        _windows_platform(os_name="posix")
    with pytest.raises(ValueError, match="one absolute"):
        _windows_platform(executable_candidates=lambda _environment: (
            "C:\\One\\docker.exe", "C:\\Two\\docker.exe",
        ))


@pytest.mark.parametrize(
    "executable", ("C:\\Docker\\docker.exe", "C:\\Docker\\DOCKER.EXE"),
)
def test_windows_factory_accepts_exact_case_insensitive_docker_basename(
    executable,
):
    platform, observed = _windows_platform(
        executable_candidates=lambda _environment: (executable,),
    )
    assert platform.policy.executable == executable
    assert observed["executable"] == executable


@pytest.mark.parametrize(
    "executable",
    (
        "C:\\Docker\\notdocker.exe",
        "C:\\Docker\\mydocker.exe",
        "C:\\Docker\\docker.exe.bak",
    ),
)
def test_windows_factory_rejects_inexact_docker_basename_before_inspection(
    executable,
):
    inspected = []

    def forbidden(*_args):
        inspected.append(True)
        raise AssertionError("endpoint inspection crossed executable validation")

    with pytest.raises(ValueError, match="one absolute"):
        _windows_platform(
            executable_candidates=lambda _environment: (executable,),
            endpoint_resolver=forbidden,
        )
    assert inspected == []


# ---------------------------------------------------------------------------
# S6 — publication wiring on the prepared Docker activation path (Gap A).
# Section 9.2 tests 8 and 9 of
# docs/architecture/native-windows-publication-closure.md.
#
# Test 8 has two halves, proven at two different evidence levels because
# `_activate_docker_training_v1` cannot execute on this host: its only harness
# (`clean_project` in tests/synaptic_host/test_docker_training.py) shells out
# to `git clone --shared` against the submodule gitlink and exits 128, which is
# also why five `test_docker_staging.py` tests fail at baseline.
#
#   * RECEIVING half — a real publication reaches the composition and the
#     prepared path publishes with it and stays unpublished without it — is
#     proven BEHAVIOURALLY, against the real `DockerPreparedCompositionV1`, the
#     real `DockerPublicationCompositionV1` and the real `reconcile`. Only the
#     host publication facade (spool, store, filesystem) is a stand-in, exactly
#     as in the passing `test_docker_publication.py` composition test.
#   * CONSTRUCTING half — the publication is built only inside the
#     ARTIFACTS_VERIFIED branch (test 8) and closed in a `finally` (test 9) —
#     is proven STATICALLY, by parsing the shipped source of
#     `synaptic_host/docker_training.py`.
#
# Both static assertions are counter-tested against a deliberately sabotaged
# copy of the real source. A structural guard never shown to fail is not
# evidence.
# ---------------------------------------------------------------------------

import ast
import hashlib
import inspect
import json

import synaptic_host.docker_publication as _s6_publication
import synaptic_host.docker_training as _s6_training
from synaptic_host.artifact_destinations import (
    artifact_destination_declaration_digest_v1,
    parse_artifact_destination_config_v1,
)
from synaptic_host.docker_execution_state import (
    DockerRunMutationRecordV1, DockerRunPhaseV1, VerifiedDockerArtifactV1,
    verified_inventory_digest_v1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1, DockerControlOperationV1,
    DockerMutationPhaseV1, DockerMutationRecordV1, docker_operation_id_v1,
)
from synaptic_tuner.api.v1 import (
    PublicationRef, PublicationResult, PublicationState, TrainingRunRef,
)


_S6_ROOT = Path(__file__).resolve().parents[2]
_S6_EFFECT = "submit-" + "1" * 64
_S6_NOW = "2026-09-01T12:00:00Z"
_S6_RUN = TrainingRunRef("run", "project")
_S6_PUBLICATION_ID = "publication-" + "9" * 32
_S6_ROLES = (
    "final_model", "tokenizer", "training_lineage", "training_metrics",
    "workload_record",
)


def _s6_mutation(operation):
    record = DockerMutationRecordV1.build(
        operation_id=docker_operation_id_v1(operation, _S6_EFFECT),
        operation=operation, effect_id=_S6_EFFECT,
        control_intent_proof_digest=(
            "1" * 64 if operation is DockerControlOperationV1.CREATE else "2" * 64
        ),
        phase=DockerMutationPhaseV1.VERIFIED, revision=3, attempt_count=1,
        previous_record_digest="3" * 64, container_ref="a" * 64,
        verification_result_digest="4" * 64,
    )
    return AuthenticatedDockerMutationRecordV1(
        record, "authority", "key", record.record_digest
    )


def _s6_verified_record(artifact_root: Path):
    """One real ARTIFACTS_VERIFIED aggregate — the only phase that publishes."""

    artifact_root.mkdir(parents=True)
    descriptors = []
    for role in _S6_ROLES:
        payload = (role + "\n").encode()
        (artifact_root / f"{role}.bin").write_bytes(payload)
        descriptors.append(VerifiedDockerArtifactV1(
            role, f"{role}.bin", len(payload),
            hashlib.sha256(payload).hexdigest(),
        ))
    artifacts = tuple(descriptors)
    return DockerRunMutationRecordV1.build(
        project_ref=_S6_RUN.project_ref, run_id=_S6_RUN.run_id,
        effect_id=_S6_EFFECT, preparation_digest="5" * 64,
        phase=DockerRunPhaseV1.ARTIFACTS_VERIFIED, revision=8,
        previous_record_digest="6" * 64,
        create_mutation=_s6_mutation(DockerControlOperationV1.CREATE),
        start_mutation=_s6_mutation(DockerControlOperationV1.START),
        reconcile_operation=None, container_ref="a" * 64,
        submitted_at=_S6_NOW, process_exit_code=0,
        process_observation_digest="7" * 64, diagnostic=None,
        verified_artifacts=artifacts,
        verified_inventory_digest=verified_inventory_digest_v1(artifacts),
    )


class _S6Repository:
    def __init__(self, record):
        self.record = record

    def load_docker_run_mutation(self, _project_ref, _run_id):
        return self.record

    def compare_and_swap_docker_run_mutation(self, *_args, **_kwargs):
        raise AssertionError("the publish cut mutated durability")


class _S6Facade:
    """Stand-in for the host publication facade the spool would provide."""

    def __init__(self):
        self.publish_calls = []
        self.closed = 0

    def publish(self, request):
        self.publish_calls.append(request)
        return PublicationResult(
            "synaptic-publication-result/v1",
            PublicationRef(_S6_PUBLICATION_ID, request.destination_ref),
            _S6_RUN, PublicationState.VERIFIED,
        )

    def close(self):
        self.closed += 1


def _s6_publication_request(tmp_path: Path, record):
    """The exact prepared request `compose_docker_publication_v1` binds to."""

    source_root = tmp_path / "stage" / "source"
    destination_path = source_root / "project" / "training" / "artifacts.json"
    storage_path = source_root / "control" / "storage.json"
    destination_path.parent.mkdir(parents=True)
    storage_path.parent.mkdir(parents=True)
    destination_bytes = (_S6_ROOT / "training" / "artifacts.json").read_bytes()
    storage_bytes = (_S6_ROOT / "training" / "storage.json").read_bytes()
    destination_path.write_bytes(destination_bytes)
    storage_path.write_bytes(storage_bytes)
    destination = parse_artifact_destination_config_v1(
        destination_bytes
    ).destinations[0]
    preparation = SimpleNamespace(
        preparation_digest=record.preparation_digest,
        destination_ref=destination.destination_ref,
        destination_declaration_digest=(
            artifact_destination_declaration_digest_v1(destination)
        ),
        stage=SimpleNamespace(
            staged_storage_configuration_digest=hashlib.sha256(
                storage_bytes
            ).hexdigest()
        ),
    )
    request = object.__new__(DockerPreparedRunRequestV1)
    for name, value in (
        ("project_ref", _S6_RUN.project_ref), ("run_id", _S6_RUN.run_id),
        ("preparation", preparation),
        ("prepared_plan", SimpleNamespace(digest="9" * 64)),
        ("staging", SimpleNamespace(
            source_root=source_root,
            artifact_root=tmp_path / "stage" / "artifact",
            worker_bundle=SimpleNamespace(projection_sha256="8" * 64),
        )),
    ):
        object.__setattr__(request, name, value)
    return request, destination.destination_ref


def _s6_prepared_composition(tmp_path: Path, repository, *, publication):
    """A real prepared composition, optionally carrying a real publication."""

    _unused, endpoint, policy = _request(tmp_path / "prepared")
    project = tmp_path / "host"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    builder = DockerPreparedControlBuilderV1(
        authenticator=FileHmacAuthenticator.for_docker(
            ProjectContext.host(engine_root=engine, project_root=project),
            durable_rows_exist=False,
        ),
        platform=DockerPreparedPlatformV1(
            TypedRunner(), endpoint, policy, "Ubuntu-22.04", "/mnt", "1000:1000",
        ),
    )
    return DockerPreparedCompositionV1(
        repository=repository, builder=builder, clock=lambda: _S6_NOW,
        publication=publication,
    )


def test_prepared_activation_publishes_only_when_a_publication_is_wired(
    tmp_path: Path, monkeypatch,
):
    """Test 8, receiving half: the wiring is what makes the publish cut real."""

    record = _s6_verified_record(tmp_path / "stage" / "artifact")
    repository = _S6Repository(record)
    request, destination_ref = _s6_publication_request(tmp_path, record)

    # Gap A, re-expressed after M-8. Reaching the verified cut without a
    # publication no longer looks like a completed run: the cut reports
    # RECONCILE_REQUIRED with a diagnostic and publishes nothing, and the
    # aggregate keeps ARTIFACTS_VERIFIED so a wired retry still publishes.
    # (The old pin asserted phase ARTIFACTS_VERIFIED here, which was
    # indistinguishable from a correct pre-publish cut -- that was the defect.)
    unwired = _s6_prepared_composition(
        tmp_path / "unwired", repository, publication=None,
    )
    unpublished = unwired.reconcile(request)
    assert unpublished.phase is DockerRunPhaseV1.RECONCILE_REQUIRED
    assert unpublished.diagnostic == "PUBLICATION_COMPOSITION_ABSENT"
    assert unpublished.published is False
    assert unpublished.publication_id is None
    # `_S6Repository.compare_and_swap_docker_run_mutation` raises, so reaching
    # this line at all proves the cut took no durable write.
    assert repository.record.phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED

    # S6 wired: a real DockerPublicationCompositionV1 reaches the composition.
    facade = _S6Facade()
    monkeypatch.setattr(
        _s6_publication, "compose_host_publication_v1",
        lambda **_values: facade,
    )
    monkeypatch.setattr(_s6_publication, "HostPublicationFacadeV1", _S6Facade)
    publication = _s6_publication.compose_docker_publication_v1(
        context=ProjectContext.host(
            engine_root=tmp_path / "ctx" / "synaptic-tuner",
            project_root=tmp_path / "ctx",
        ),
        repository=repository, request=request, clock=lambda: _S6_NOW,
        spool_root_ref=_s6_training._PUBLICATION_SPOOL_ROOT_REF,
        registration_builders=(
            lambda **_values: (_ for _ in ()).throw(
                AssertionError("the facade owns builder invocation")
            ),
        ),
    )
    wired = _s6_prepared_composition(
        tmp_path / "wired", repository, publication=publication,
    )
    published = wired.reconcile(request)

    assert published.published is True
    assert published.publication_id == _S6_PUBLICATION_ID
    assert published.publication_state == "verified"
    # The publish cut ran once, against the destination the preparation names.
    assert len(facade.publish_calls) == 1
    assert facade.publish_calls[0].destination_ref == destination_ref
    assert facade.publish_calls[0].run == _S6_RUN
    # Closing is the caller's job: reconcile must not have done it.
    assert facade.closed == 0
    publication.close()
    assert facade.closed == 1


def test_prepared_composition_rejects_a_publication_it_did_not_compose(
    tmp_path: Path,
):
    """The wiring cannot smuggle a look-alike publication into the run."""

    record = _s6_verified_record(tmp_path / "stage" / "artifact")

    class LookAlike:
        def publish(self, *, request, record):
            raise AssertionError("a forged publication published")

        def close(self):
            raise AssertionError("a forged publication closed")

    with pytest.raises(ValueError, match="publication composition is invalid"):
        _s6_prepared_composition(
            tmp_path, _S6Repository(record), publication=LookAlike(),
        )


def test_publication_spool_root_ref_matches_the_declared_storage_root():
    """The Host-side spool name is the one training/storage.json declares."""

    declared = json.loads(
        (_S6_ROOT / "training" / "storage.json").read_text(encoding="utf-8")
    )
    roots = {item["root_ref"] for item in declared["roots"]}
    assert _s6_training._PUBLICATION_SPOOL_ROOT_REF in roots
    assert _s6_training._PUBLICATION_SPOOL_ROOT_REF == (
        "artifact-publication-spool"
    )


# --- static structure of the activation branch (tests 8 and 9) --------------


_S6_ACTIVATION = "_activate_docker_training_v1"
_S6_COMPOSE = "compose_docker_publication_v1"


def _s6_callee_name(node):
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _s6_activation_node(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == _S6_ACTIVATION:
            return node
    return None


def _s6_closes(statements, binding: str) -> bool:
    return any(
        isinstance(node, ast.Try) and any(
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "close"
            and isinstance(item.func.value, ast.Name)
            and item.func.value.id == binding
            for final in node.finalbody
            for item in ast.walk(final)
        )
        for statement in statements
        for node in ast.walk(statement)
    )


def _s6_wiring_findings(source: str) -> tuple[str, ...]:
    """Report every way the activation could leak or mis-gate a publication."""

    activation = _s6_activation_node(ast.parse(source))
    if activation is None:
        return ("activation function is absent",)
    constructions = [
        node for node in ast.walk(activation)
        if isinstance(node, ast.Call)
        and _s6_callee_name(node.func) == _S6_COMPOSE
    ]
    if len(constructions) != 1:
        return (
            "expected exactly one publication construction, found "
            f"{len(constructions)}",
        )
    call = constructions[0]
    findings = []

    gate = None
    for node in ast.walk(activation):
        if not isinstance(node, ast.If):
            continue
        mentions = any(
            isinstance(item, ast.Attribute)
            and item.attr == "ARTIFACTS_VERIFIED"
            for item in ast.walk(node.test)
        )
        if mentions and any(
            call is item or call in set(ast.walk(item)) for item in node.body
        ):
            gate = node
            break
    if gate is None:
        findings.append(
            "publication is constructed outside the ARTIFACTS_VERIFIED branch"
        )

    binding = next(
        (
            node.targets[0].id for node in ast.walk(activation)
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and call in set(ast.walk(node.value))
        ),
        None,
    )
    if binding is None:
        findings.append("publication construction is not bound to a name")
    elif not _s6_closes(gate.body if gate is not None else activation.body,
                        binding):
        findings.append("publication is not closed in a finally")

    spool = next(
        (word for word in call.keywords if word.arg == "spool_root_ref"), None
    )
    if spool is None or not (
        isinstance(spool.value, ast.Name)
        and spool.value.id == "_PUBLICATION_SPOOL_ROOT_REF"
    ):
        findings.append("spool_root_ref is not the module constant")
    return tuple(findings)


def test_activation_gates_and_closes_the_publication_it_constructs():
    """Tests 8 (constructing half) and 9, against the shipped source."""

    assert _s6_wiring_findings(inspect.getsource(_s6_training)) == ()


def _s6_sabotage(transform) -> str:
    """Rewrite the real activation with `transform`, then re-render it."""

    tree = ast.parse(inspect.getsource(_s6_training))
    transform(_s6_activation_node(tree))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def test_wiring_checker_detects_eager_publication_construction():
    """Counter-test: hoisting the construction out of the branch is caught."""

    def hoist(activation):
        for node in ast.walk(activation):
            if not isinstance(node, ast.If):
                continue
            for index, statement in enumerate(list(node.body)):
                if any(
                    isinstance(item, ast.Call)
                    and _s6_callee_name(item.func) == _S6_COMPOSE
                    for item in ast.walk(statement)
                ):
                    node.body.pop(index)
                    activation.body.insert(0, statement)
                    return
        raise AssertionError("no publication construction to hoist")

    assert (
        "publication is constructed outside the ARTIFACTS_VERIFIED branch"
        in _s6_wiring_findings(_s6_sabotage(hoist))
    )


def test_wiring_checker_detects_a_dropped_finally_close():
    """Counter-test: dropping the finally is caught, not silently accepted."""

    def drop_finally(activation):
        for node in ast.walk(activation):
            for _field, value in ast.iter_fields(node):
                if not isinstance(value, list):
                    continue
                for index, statement in enumerate(list(value)):
                    if isinstance(statement, ast.Try) and statement.finalbody:
                        value[index:index + 1] = statement.body
                        return
        raise AssertionError("no finally to drop")

    assert "publication is not closed in a finally" in _s6_wiring_findings(
        _s6_sabotage(drop_finally)
    )


# --------------------------------------------------------------------------
# TEST phase additions: three further counter-tests for the wiring checker.
#
# The checker reports three distinct findings (gate, finally-close, spool
# constant) but the CODE phase counter-tested only two of them. An assertion
# arm that has never been shown to fire is not evidence, so the spool arm gets
# one here. The other two additions attack the finally-close arm with the
# mutations a real refactor would produce, rather than with the wholesale
# deletion the existing counter-test uses: a checker that only noticed a
# missing Try would pass those and still miss a leaked lease.
# --------------------------------------------------------------------------


def test_wiring_checker_detects_a_hardcoded_spool_root_ref():
    """Counter-test for the third finding, which CODE left unexercised.

    Replacing the module constant with a string literal that happens to hold
    the same value must still be reported: the point of the constant is that
    training/storage.json and the activation cannot drift apart silently, and
    a literal defeats that without changing behaviour today.
    """

    def hardcode(activation):
        for node in ast.walk(activation):
            if not isinstance(node, ast.Call):
                continue
            if _s6_callee_name(node.func) != _S6_COMPOSE:
                continue
            for word in node.keywords:
                if word.arg == "spool_root_ref":
                    word.value = ast.Constant(value="artifact-publication-spool")
                    return
        raise AssertionError("no spool_root_ref keyword to hardcode")

    assert "spool_root_ref is not the module constant" in _s6_wiring_findings(
        _s6_sabotage(hardcode)
    )


def test_wiring_checker_detects_a_close_moved_out_of_the_finally():
    """Counter-test: close present, but in the try body instead of the finally.

    This is the realistic refactor mistake, and it is strictly harder to catch
    than dropping the Try wholesale: the close call is still there, still on
    the right binding, and the Try still exists. Only a checker that inspects
    placement rather than presence reports it. If the finally is skipped
    because reconcile raised, the spool admission lease is stranded for the
    life of the process, which is the exact failure ruling (e) exists to stop.
    """

    def move_close_into_try(activation):
        for node in ast.walk(activation):
            for _field, value in ast.iter_fields(node):
                if not isinstance(value, list):
                    continue
                for index, statement in enumerate(list(value)):
                    if not isinstance(statement, ast.Try) or not statement.finalbody:
                        continue
                    # Unwrap the Try but KEEP the close call, now running only
                    # on the success path. This is what distinguishes the
                    # mutation from the CODE-phase one, which deletes it.
                    value[index:index + 1] = (
                        list(statement.body) + list(statement.finalbody)
                    )
                    return
        raise AssertionError("no finally body to move")

    findings = _s6_wiring_findings(_s6_sabotage(move_close_into_try))
    assert "publication is not closed in a finally" in findings


def test_wiring_checker_detects_a_close_demoted_to_an_except_handler():
    """Counter-test: closing only on the error path leaks on the happy path.

    An `except` that closes looks defensive and reads as correct, but it
    releases the spool admission lease only when reconcile raises. Every
    successful publish would then strand the lease.
    """

    def demote_close_to_except(activation):
        for node in ast.walk(activation):
            for _field, value in ast.iter_fields(node):
                if not isinstance(value, list):
                    continue
                for statement in value:
                    if not isinstance(statement, ast.Try) or not statement.finalbody:
                        continue
                    moved = statement.finalbody
                    statement.finalbody = []
                    statement.handlers = [
                        ast.ExceptHandler(
                            type=None, name=None,
                            body=list(moved) + [ast.Raise(exc=None, cause=None)],
                        )
                    ]
                    return
        raise AssertionError("no finally body to demote")

    assert "publication is not closed in a finally" in _s6_wiring_findings(
        _s6_sabotage(demote_close_to_except)
    )
