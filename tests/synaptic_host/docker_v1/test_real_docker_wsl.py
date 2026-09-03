from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
from threading import Thread
import time

import pytest

from synaptic_host.bundle_io_v1.model import BundleMemberCommandV1
from synaptic_host.docker_v1.authority import (
    BundleBindingHmacAuthorityV1,
    DockerAbsenceHmacAuthorityV1,
    DockerCommandBindingHmacAuthorityV1,
    DockerControlIntentHmacAuthorityV1,
    DockerCreatePathBindingHmacAuthorityV1,
    DockerExpectedCreateBindingHmacAuthorityV1,
    DockerMutationRecordHmacAuthorityV1,
    DockerSourceDeclarationHmacAuthorityV1,
    DockerSourceSealHmacAuthorityV1,
    DockerStageBundleRecordHmacAuthorityV1,
    DockerStorageMappingHmacAuthorityV1,
    DockerStoragePathMappingPairHmacAuthorityV1,
    DockerWSLRootMappingHmacAuthorityV1,
    DockerWorkloadEnvironmentBindingHmacAuthorityV1,
)
from synaptic_host.docker_prepared_composition import (
    DockerPreparedPlatformV1,
    compose_docker_prepared_platform_v1,
)
from synaptic_host.docker_v1.binding import DockerWorkloadEnvironmentPolicyV1
from synaptic_host.docker_v1.composition import (
    DockerHostCompositionRequestV1,
    compose_docker_host_v1,
)
from synaptic_host.docker_v1.cli import DockerCLIRunnerV1
from synaptic_host.docker_v1.control_private import (
    DockerPrivateStartInvocationV1,
)
from synaptic_host.docker_v1.model import (
    DockerCLIEnvironmentV1,
    DockerCLIPolicyV1, DockerLocalEndpointDescriptorV1,
)
from synaptic_host.docker_v1.start import DockerHostStartV1
from synaptic_host.local_io_v1.config import StorageRegistryV1
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.posix import PosixRetainedDirfdPortV1
from synaptic_host.security import FileHmacAuthenticator
from synaptic_tuner.api.v1.docker import (
    DockerSameProcessLaunchV1,
)
from synaptic_tuner.api.v1.planning import (
    ProviderPlanContextV1,
    ProviderPlanRef,
    TrainingPlan,
    TrainingPlanBasisV1,
)
from synaptic_tuner.api.v1.providers import (
    ProviderCapabilities,
    ProviderDescriptor,
    ProviderRef,
)
from synaptic_tuner.api.v1.results import TrainingRunRef
from synaptic_tuner.api.v1.training_facade import TrainingPreflight
from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.foundation_v2.executors import (
    AdapterDescriptorV1,
    ExecutorDescriptorV1,
)
from tuner.execution.foundation_v2.identities import EffectKind
from tuner.execution.foundation_v2.references import ExecutionScopeV1
from tuner.execution.providers.docker_provider_v1.model import (
    DockerArtifactContractV1,
    DockerImageV1,
    DockerProfileV1,
    DockerRootsV1,
    DockerRuntimeV1,
    DockerWorkloadV1,
    labels_for,
)


_IMAGE_DIGEST = (
    "sha256:d9e853e87e55526f6b2917df91a2115c36dd7c696a35be12163d44e6e2a4b6bc"
)
_DOCKER_EXE = Path("/Docker/host/bin/docker.exe")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_storage(project: Path, roots: tuple[str, ...]) -> Path:
    document = {
        "schema_version": "synaptic-host-storage/v1",
        "roots": [
            {
                "access": "read_create",
                "location": f"project://{name}",
                "permit_ref": f"permit-{name}",
                "root_ref": name,
            }
            for name in roots
        ],
    }
    path = project / "storage.json"
    path.write_text(
        json.dumps(document, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return path


def _profile(payload: bytes) -> DockerProfileV1:
    provider = ProviderRef("docker", "offline-alpine-cpu")
    workload = DockerWorkloadV1(
        (
            "sh",
            "-c",
            "cat /source/member-0000 > /artifacts/result; sleep 2",
        ),
        (),
        _sha(b"alpine-copy-workload-v1"),
    )
    return DockerProfileV1.build(
        provider=provider,
        descriptor=ProviderDescriptor(
            "synaptic-provider-descriptor/v1",
            "docker",
            "Docker",
            "1.0.0",
            ProviderCapabilities(True, True, True, True, True, False),
        ),
        scope=ExecutionScopeV1("local", "offline-smoke"),
        executor_descriptor=ExecutorDescriptorV1(
            "docker", "docker-executor-v1", "1.0.0"
        ),
        adapter_descriptor=AdapterDescriptorV1(
            "docker", "docker-reconcile-v1", "1.0.0"
        ),
        image=DockerImageV1("alpine:3.20", _IMAGE_DIGEST),
        runtime=DockerRuntimeV1(
            1, 67_108_864, 30,
            AcceleratorDeviceRequestV1("cpu", (), ()),
        ),
        workload=workload,
        roots=DockerRootsV1("source-root", "artifact-root"),
        artifacts=DockerArtifactContractV1(
            ("result",), maximum_artifact_bytes=1_048_576,
            maximum_total_bytes=1_048_576,
        ),
        resource_digest=_sha(b"offline-local-resource"),
        quote_digest=_sha(b"offline-zero-cost"),
        secret_requirements_digest=_sha(b"offline-no-secrets"),
    )


def _request(tmp_path: Path) -> tuple[DockerHostCompositionRequestV1, Path, bytes]:
    project = tmp_path / "project"
    roots = (
        "source-data", "source-control", "stage-data", "stage-control",
        "artifact-data", "artifact-control",
    )
    for name in roots:
        (project / name).mkdir(parents=True)
    payload = b"real-docker-wsl-offline-proof\n"
    (project / "source-data" / "dataset-source").write_bytes(payload)

    storage = StorageRegistryV1.load(
        _write_storage(project, roots), project_root=project
    )
    permit_digest = _sha(b"real-docker-wsl-root-permits")
    for name in roots:
        storage.issue_root_permit(
            name,
            authority_ref="docker-root-authority",
            key_ref="docker-root-key",
            proof_digest=permit_digest,
        )
    filesystem = LocalFilesystemV1(PosixRetainedDirfdPortV1(), storage)

    profile = _profile(payload)
    source_digest = _sha(payload)
    basis = TrainingPlanBasisV1(
        "synaptic-training-plan-basis/v1",
        "offline-docker-request",
        "offline-docker-project",
        source_digest,
        _sha(b"offline-dataset"),
        profile.workload.workload_digest,
        profile.runtime.digest,
        profile.artifacts.digest,
    )
    context = ProviderPlanContextV1(
        "synaptic-provider-plan-context/v1",
        profile.provider,
        basis.basis_digest,
        profile.descriptor.descriptor_digest,
        profile.profile_digest,
    )
    plan = TrainingPlan(
        "synaptic-training-plan/v2",
        basis,
        ProviderPlanRef(context.provider_context_digest),
    )
    launch = DockerSameProcessLaunchV1(
        profile,
        context,
        plan,
        TrainingRunRef("offline-docker-run", "offline-docker-project"),
        TrainingPreflight(
            plan.plan_fingerprint,
            True,
            "2026-08-31T00:00:00Z",
            "2099-01-01T00:00:00Z",
        ),
    )

    authenticator = FileHmacAuthenticator(
        project / "docker-hmac.key", key_ref="docker-hmac-key"
    )
    authenticator.key_path.write_bytes(bytes(range(32)))

    def authority(authority_type, name):
        return authority_type(
            authority_ref=f"docker-{name}-authority",
            authenticator=authenticator,
        )

    storage_authority = authority(
        DockerStorageMappingHmacAuthorityV1, "storage"
    )
    wsl_authority = authority(DockerWSLRootMappingHmacAuthorityV1, "wsl")
    pair_authority = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="docker-pair-authority",
        authenticator=authenticator,
        storage_mapping_authority=storage_authority,
        wsl_mapping_authority=wsl_authority,
    )
    environment = DockerCLIEnvironmentV1.build((
        ("SystemRoot", "C:\\Windows"),
        ("TEMP", "C:\\Temp"),
        ("TMP", "C:\\Temp"),
        ("WINDIR", "C:\\Windows"),
    ))
    interop = os.environ["WSL_INTEROP"]
    request = DockerHostCompositionRequestV1(
        launch=launch,
        filesystem=filesystem,
        source_data_binding=storage.resolve("source-data"),
        source_control_binding=storage.resolve("source-control"),
        source_component="dataset-source",
        stage_data_binding=storage.resolve("stage-data"),
        stage_control_binding=storage.resolve("stage-control"),
        stage_destination_ref="stage-destination",
        artifact_data_binding=storage.resolve("artifact-data"),
        artifact_control_binding=storage.resolve("artifact-control"),
        source_purpose_ref="docker-stage-source",
        source_members=(BundleMemberCommandV1(
            "data.json", profile.roots.source_ref, len(payload), source_digest
        ),),
        source_mapping_ref="source-mapping",
        source_wsl_root=str((project / "stage-data").resolve()),
        artifact_mapping_ref="artifact-mapping",
        artifact_wsl_root=str((project / "artifact-data").resolve()),
        artifact_destination_ref="artifact-destination",
        wsl_distro="Ubuntu-22.04",
        container_user="1000:1000",
        environment_policy=DockerWorkloadEnvironmentPolicyV1.build(
            allowed_keys=()
        ),
        environment_overrides=(),
        cli_policy=DockerCLIPolicyV1.build(
            str(_DOCKER_EXE),
            DockerLocalEndpointDescriptorV1.build(
                "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False
            ),
            environment,
            timeout_ms=30_000,
            terminate_grace_ms=1_000,
            stdout_limit=1_048_576,
            stderr_limit=1_048_576,
            combined_limit=2_097_152,
        ),
        wsl_interop_path=interop,
        lstat=os.lstat,
        popen_factory=subprocess.Popen,
        monotonic=time.monotonic,
        thread_factory=Thread,
        declaration_authority=authority(
            DockerSourceDeclarationHmacAuthorityV1, "declaration"
        ),
        stage_record_authority=authority(
            DockerStageBundleRecordHmacAuthorityV1, "stage"
        ),
        storage_mapping_authority=storage_authority,
        wsl_mapping_authority=wsl_authority,
        bundle_binding_authority=authority(
            BundleBindingHmacAuthorityV1, "bundle"
        ),
        source_seal_authority=authority(
            DockerSourceSealHmacAuthorityV1, "source-seal"
        ),
        path_binding_authority=authority(
            DockerCreatePathBindingHmacAuthorityV1, "path"
        ),
        environment_authority=authority(
            DockerWorkloadEnvironmentBindingHmacAuthorityV1, "environment"
        ),
        intent_authority=authority(
            DockerControlIntentHmacAuthorityV1, "intent"
        ),
        mutation_record_authority=authority(
            DockerMutationRecordHmacAuthorityV1, "record"
        ),
        absence_authority=authority(
            DockerAbsenceHmacAuthorityV1, "absence"
        ),
        expected_authority=authority(
            DockerExpectedCreateBindingHmacAuthorityV1, "expected"
        ),
        command_binding_authority=authority(
            DockerCommandBindingHmacAuthorityV1, "command"
        ),
        pair_authority=pair_authority,
    )
    return request, project / "artifact-data" / "result", payload


def _docker(*arguments: str, timeout: int = 30) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (str(_DOCKER_EXE), "--host", "npipe:////./pipe/dockerDesktopLinuxEngine", *arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


@pytest.mark.skipif(
    os.name != "posix"
    or "WSL_INTEROP" not in os.environ
    or not _DOCKER_EXE.is_file(),
    reason="real Docker Desktop WSL integration",
)
def test_released_facade_starts_real_offline_pinned_container(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    request, artifact_path, payload = _request(tmp_path)
    trace: dict[str, object] = {"inspects": []}
    original_inspect = DockerCLIRunnerV1.inspect_container
    original_start_container = DockerCLIRunnerV1.start_container
    original_execute_start = DockerPrivateStartInvocationV1.execute_once
    original_start = DockerHostStartV1.start_once
    original_recover_start = DockerHostStartV1._recover

    def traced_inspect(self, container_ref):
        try:
            result = original_inspect(self, container_ref)
        except BaseException as error:
            code = getattr(getattr(error, "code", None), "value", None)
            trace["inspects"].append({
                "error": type(error).__name__, "code": code
            })
            raise
        projection = result.projection
        state = None if projection is None else projection.state
        trace["inspects"].append({
            "outcome": result.evidence.outcome.value,
            "status": None if state is None else state.status.value,
            "running": None if state is None else state.running,
            "started": None if state is None else state.started,
            "exit_code": None if state is None else state.exit_code,
        })
        return result

    def traced_start(self, container_ref, labels):
        result = original_start(self, container_ref, labels)
        trace["start"] = {
            "disposition": result.disposition.value,
            "container_ref": result.container_ref,
        }
        return result

    def traced_recover_start(
        self, preflight, current, start_result, already_verified=False
    ):
        try:
            result = original_recover_start(
                self, preflight, current, start_result, already_verified
            )
        except BaseException as error:
            trace["start_recover"] = {"error": type(error).__name__}
            raise
        trace["start_recover"] = {"disposition": result.disposition.value}
        return result

    def traced_start_container(self, command, container_ref):
        try:
            result = original_start_container(self, command, container_ref)
        except BaseException as error:
            trace["start_container"] = {"error": type(error).__name__}
            raise
        trace["start_container"] = {
            "outcome": result.evidence.outcome.value,
            "exit_code": result.evidence.exit_code,
            "stdout_size": result.evidence.stdout_size,
            "stderr_size": result.evidence.stderr_size,
        }
        return result

    def traced_execute_start(self, runner):
        try:
            result = original_execute_start(self, runner)
        except BaseException as error:
            trace["start_invocation"] = {"error": type(error).__name__}
            raise
        trace["start_invocation"] = {"result": type(result).__name__}
        return result

    monkeypatch.setattr(DockerCLIRunnerV1, "inspect_container", traced_inspect)
    monkeypatch.setattr(
        DockerCLIRunnerV1, "start_container", traced_start_container
    )
    monkeypatch.setattr(
        DockerPrivateStartInvocationV1, "execute_once", traced_execute_start
    )
    monkeypatch.setattr(DockerHostStartV1, "start_once", traced_start)
    monkeypatch.setattr(DockerHostStartV1, "_recover", traced_recover_start)
    facade = compose_docker_host_v1(request)
    container_ref = None
    try:
        try:
            workflow = facade.start_run()
        except BaseException as error:
            binding = facade.effect_binding(EffectKind.SUBMIT)
            container_ref = labels_for(binding.content.identity).container_name
            inspected = _docker("inspect", container_ref)
            logs = _docker("logs", container_ref)
            pytest.fail(
                "real Docker facade rejected a started workload\n"
                f"host_trace={json.dumps(trace, sort_keys=True)}\n"
                f"inspect_rc={inspected.returncode}\n"
                f"inspect={inspected.stdout.decode('utf-8', 'replace')}\n"
                f"inspect_stderr={inspected.stderr.decode('utf-8', 'replace')}\n"
                f"logs_rc={logs.returncode}\n"
                f"logs={logs.stdout.decode('utf-8', 'replace')}\n"
                f"logs_stderr={logs.stderr.decode('utf-8', 'replace')}\n"
                f"facade_error={type(error).__name__}"
            )
        assert workflow.phase.value == "queued"
        assert workflow.provider_run_ref is not None
        container_ref = workflow.provider_run_ref.reference.provider_job_ref
        waited = _docker("wait", container_ref)
        assert waited.returncode == 0, waited.stderr.decode("utf-8", "replace")
        assert waited.stdout.strip() == b"0"
        assert artifact_path.read_bytes() == payload
    finally:
        if container_ref is None:
            try:
                binding = facade.effect_binding(EffectKind.SUBMIT)
                container_ref = labels_for(binding.content.identity).container_name
            except BaseException:
                container_ref = None
        facade.close()
        if container_ref is not None:
            removed = _docker("rm", "--force", container_ref)
            assert removed.returncode == 0, removed.stderr.decode(
                "utf-8", "replace"
            )


# ---------------------------------------------------------------------------
# E4 — B-13, architecture section 22.10, the EXECUTION half of the standing
# rule.  Every other test of the prepared composition supplies the child, so
# none of them can fail on a defect whose whole content is what a real
# `docker.exe` does when a key is absent.  This one launches the real binary
# under the exact shipped four-key environment.
# ---------------------------------------------------------------------------


_SHIPPED_ENVIRONMENT_KEYS = ("SystemRoot", "TEMP", "TMP", "WINDIR")


@pytest.mark.skipif(
    os.name != "nt", reason="real docker.exe under the Windows Host environment"
)
def test_real_windows_composition_under_the_shipped_four_key_environment():
    """E4 — compose against a real `docker.exe` and assert, never skip, on the
    daemon.

    Three outcomes, and only the first is a skip:

    * the composition's OWN executable-candidate rule finds no single
      `docker.exe` -> skip.  The rule is EXERCISED rather than mirrored, so the
      skip condition cannot drift from the thing under test.
    * the daemon does not answer on the pipe -> the 22.6 `ValueError`.  Daemon
      down is an expected outcome and is asserted.  A skip here would
      reintroduce exactly the blindness B-13 was hiding in.
    * the daemon answers -> a `DockerPreparedPlatformV1` bound to the
      constructed endpoint.
    """

    missing = [key for key in ("PATH", *_SHIPPED_ENVIRONMENT_KEYS)
               if key not in os.environ]
    assert not missing, f"the Windows Host is missing {missing}"
    values = {key: os.environ[key]
              for key in ("PATH", *_SHIPPED_ENVIRONMENT_KEYS)}
    try:
        platform = compose_docker_prepared_platform_v1(
            docker_policy_ref="docker-desktop-windows-v1",
            wsl_distro="Ubuntu-22.04",
            drive_mount_root="/mnt",
            container_user="1000:1000",
            environment=values,
        )
    except ValueError as error:
        if str(error) == "one absolute Windows Docker executable is required":
            pytest.skip("no single docker.exe on PATH (composition's own rule)")
        assert str(error) == "Docker desktop-linux daemon is unavailable"
        return
    assert type(platform) is DockerPreparedPlatformV1
    assert platform.endpoint.host == "npipe:////./pipe/dockerDesktopLinuxEngine"
    assert platform.endpoint.tls is False
    assert tuple(
        key for key, _ in platform.policy.environment.entries
    ) == _SHIPPED_ENVIRONMENT_KEYS
