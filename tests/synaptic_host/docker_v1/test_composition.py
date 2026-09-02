from dataclasses import fields
from pathlib import Path
from stat import S_IFSOCK
from threading import Thread
from types import SimpleNamespace

import pytest

from synaptic_host.docker_v1 import composition as subject
from synaptic_host.docker_v1.capability_assembly import (
    DockerCapabilityCleanupResultV1,
)
from synaptic_host.docker_v1.composition import (
    DockerHostCompositionCodeV1,
    DockerHostCompositionErrorV1,
    DockerHostCompositionRequestV1,
    compose_docker_host_v1,
)
from synaptic_host.docker_v1.facade import (
    DockerHostFacadeV1,
)
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
from synaptic_host.bundle_io_v1.model import BundleMemberCommandV1
from synaptic_host.docker_v1.binding import DockerWorkloadEnvironmentPolicyV1
from synaptic_host.docker_v1.model import (
    DockerCLIEnvironmentV1, DockerCLIPolicyV1, DockerLocalEndpointDescriptorV1,
)
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.security import FileHmacAuthenticator
from synaptic_tuner.api.v1.docker import DockerSameProcessLaunchV1
from synaptic_tuner.api.v1.planning import (
    ProviderPlanContextV1, ProviderPlanRef, TrainingPlan,
    TrainingPlanBasisV1,
)
from synaptic_tuner.api.v1.results import TrainingRunRef
from synaptic_tuner.api.v1.training_facade import TrainingPreflight

from bundle_io_v1.conftest import Authenticator
from local_io_v1.conftest import FakePosixFilesystemPortV1
from .conftest import D, _profile


class _Launch:
    class _Profile:
        class _Roots:
            source_ref = "source-ref"
            artifact_ref = "artifact-ref"

        roots = _Roots()

    profile = _Profile()


def _request_shell():
    request = DockerHostCompositionRequestV1.__new__(
        DockerHostCompositionRequestV1
    )
    for field in fields(DockerHostCompositionRequestV1):
        object.__setattr__(request, field.name, object())
    object.__setattr__(request, "launch", _Launch())
    object.__setattr__(request, "source_component", "source")
    object.__setattr__(request, "stage_destination_ref", "stage")
    return request


class _Live:
    def __init__(self, events, *, prepare_error=None, prepare_after=False):
        self.events = events
        self.prepare_error = prepare_error
        self.prepare_after = prepare_after
        self.abort_calls = 0
        self.prepare_calls = 0
        self.assembly = object()
        self.handoff = _Handoff(events)

    def prepare_handoff(self):
        self.events.append("prepare_handoff")
        self.prepare_calls += 1
        if self.prepare_error is not None:
            if self.prepare_after:
                self.handoff.prepared = True
            raise self.prepare_error
        self.handoff.prepared = True
        return self.handoff

    def abort(self):
        self.events.append("abort")
        self.abort_calls += 1
        return DockerCapabilityCleanupResultV1.build(0, 0, 0, ())


class _Handoff:
    def __init__(self, events, *, commit_error=None, commit_after=False):
        self.events = events
        self.commit_error = commit_error
        self.commit_after = commit_after
        self.prepared = False
        self.committed = False
        self.recover_calls = 0

    def commit_handoff(self):
        self.events.append("commit")
        if self.commit_error is not None:
            if self.commit_after:
                self.committed = True
            raise self.commit_error
        self.committed = True

    def recover_unpublished(self):
        self.events.append("recover")
        self.recover_calls += 1
        return DockerCapabilityCleanupResultV1.build(0, 0, 0, ())


def _install_builder(monkeypatch, live, events):
    class Builder:
        def __init__(self, **_kwargs):
            events.append("builder")

        def build(self):
            events.append("build")
            return live

    monkeypatch.setattr(subject, "DockerCapabilityAssemblyBuilderV1", Builder)


def test_success_prepares_handoff_facade_then_commits_and_returns(
    monkeypatch,
):
    events = []
    live = _Live(events)
    _install_builder(monkeypatch, live, events)
    facade, adapter = object(), object()

    def prepare(request, supplied_live):
        assert request is not None and supplied_live is live
        events.append("prepare")
        assert live.prepare_calls == 0
        return adapter

    monkeypatch.setattr(subject, "_prepare", prepare)
    monkeypatch.setattr(subject, "DockerHostFacadeV1", lambda supplied, handoff: (
        events.append("facade"),
        facade if supplied is adapter and handoff is live.handoff else None,
    )[1])
    returned = compose_docker_host_v1(_request_shell())
    assert returned is facade
    assert events == [
        "builder", "build", "prepare", "prepare_handoff", "facade", "commit"
    ]
    assert live.abort_calls == 0 and live.prepare_calls == 1
    assert live.handoff.committed is True


@pytest.mark.parametrize("cut,error_type", (
    ("builder", RuntimeError), ("build", KeyboardInterrupt),
    ("prepare", SystemExit), ("prepare-before", KeyboardInterrupt),
    ("prepare-after", SystemExit), ("facade", RuntimeError),
    ("commit-before", KeyboardInterrupt), ("commit-after", SystemExit),
))
def test_each_publication_failure_cut_recovers_through_exact_held_authority(
    monkeypatch, cut, error_type,
):
    events = []
    live = _Live(events,
        prepare_error=error_type("secret-prepare")
        if cut.startswith("prepare-") else None,
        prepare_after=cut == "prepare-after",
    )
    if cut.startswith("commit-"):
        live.handoff.commit_error = error_type("secret-commit")
        live.handoff.commit_after = cut == "commit-after"

    class Builder:
        def __init__(self, **_kwargs):
            events.append("builder")
            if cut == "builder":
                raise RuntimeError("secret-builder")

        def build(self):
            events.append("build")
            if cut == "build":
                raise RuntimeError("secret-build")
            return live

    monkeypatch.setattr(subject, "DockerCapabilityAssemblyBuilderV1", Builder)

    def prepare(_request, _live):
        events.append("prepare")
        if cut == "prepare":
            raise error_type("secret-prepare")
        return object()

    monkeypatch.setattr(subject, "_prepare", prepare)
    def facade(_adapter, _handoff):
        events.append("facade")
        if cut == "facade":
            raise error_type("secret-facade")
        return object()
    monkeypatch.setattr(subject, "DockerHostFacadeV1", facade)
    with pytest.raises(DockerHostCompositionErrorV1) as caught:
        compose_docker_host_v1(_request_shell())
    assert caught.value.code is DockerHostCompositionCodeV1.COMPOSITION_FAILED
    assert caught.value.args == ()
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "secret" not in repr(caught.value)
    expected_aborts = 1 if cut in {
        "prepare", "prepare-before", "prepare-after"
    } else 0
    assert live.abort_calls == expected_aborts
    expected_recoveries = 1 if cut in {
        "facade", "commit-before", "commit-after"
    } else 0
    assert live.handoff.recover_calls == expected_recoveries


def test_cleanup_failure_is_sanitized_and_never_retried(monkeypatch):
    events = []
    live = _Live(events)
    live.handoff.commit_error = RuntimeError("secret")

    def failed_abort():
        live.abort_calls += 1
        raise SystemExit("secret-cleanup")

    live.handoff.recover_unpublished = failed_abort
    _install_builder(monkeypatch, live, events)
    monkeypatch.setattr(subject, "_prepare", lambda *_args: object())
    monkeypatch.setattr(subject, "DockerHostFacadeV1", lambda *_args: object())
    with pytest.raises(DockerHostCompositionErrorV1) as caught:
        compose_docker_host_v1(_request_shell())
    assert caught.value.code is DockerHostCompositionCodeV1.CLEANUP_FAILED
    assert caught.value.args == ()
    assert live.abort_calls == 1


def test_invalid_request_and_error_subclasses_are_closed():
    with pytest.raises(DockerHostCompositionErrorV1) as caught:
        compose_docker_host_v1(object())
    assert caught.value.code is DockerHostCompositionCodeV1.INPUT_INVALID
    assert caught.value.args == ()
    with pytest.raises(TypeError):
        class Derived(DockerHostCompositionErrorV1):
            pass


def test_composition_has_one_prepare_commit_and_no_detached_publication():
    source = open(subject.__file__, encoding="utf-8").read()
    function = source[source.index("def compose_docker_host_v1"):]
    assert function.count("live_build.prepare_handoff()") == 1
    assert function.count("handoff.commit_handoff()") == 1
    assert "transfer()" not in function
    assert ".ownership =" not in function
    assert function.index("live_build.prepare_handoff()") < function.index(
        "DockerHostFacadeV1(adapter, handoff)"
    ) < function.index("handoff.commit_handoff()") < function.index(
        "return facade"
    )


def test_public_result_surface_does_not_wrap_or_export_raw_controls():
    assert subject.__all__ == ()
    request_names = {field.name for field in fields(DockerHostCompositionRequestV1)}
    assert not {
        "cloud", "cloud_run", "ownership", "attachment_cell",
        "runtime_adapter", "container", "process",
    } & request_names


def _real_request(tmp_path, *, include_port=False):
    profile = _profile("opaque/local-cpu")
    basis = TrainingPlanBasisV1(
        "synaptic-training-plan-basis/v1", "request", "project",
        D[8], D[1], profile.workload.workload_digest,
        profile.runtime.digest, profile.artifacts.digest,
    )
    context = ProviderPlanContextV1(
        "synaptic-provider-plan-context/v1", profile.provider,
        basis.basis_digest, profile.descriptor.descriptor_digest,
        profile.profile_digest,
    )
    plan = TrainingPlan(
        "synaptic-training-plan/v2", basis,
        ProviderPlanRef(context.provider_context_digest),
    )
    launch = DockerSameProcessLaunchV1(
        profile, context, plan, TrainingRunRef("run", "project"),
        TrainingPreflight(
            plan.plan_fingerprint, True,
            "2026-08-27T00:00:00Z", "2026-08-29T00:00:00Z",
        ),
    )
    port = FakePosixFilesystemPortV1()
    binding_authenticator = Authenticator()
    labels = (
        "source-data", "source-control", "stage-data", "stage-control",
        "artifact-data", "artifact-control",
    )
    bindings = {}
    for label in labels:
        path = Path.cwd() / ".fake-metadata" / "composition" / label
        port.add_root(path, label)
        bindings[label] = binding_authenticator.binding(path, label)
    filesystem = LocalFilesystemV1(
        port, binding_authenticator, native_platform="linux"
    )
    hmac = FileHmacAuthenticator(
        tmp_path / "composition.key", key_ref="composition-key"
    )
    hmac.key_path.parent.mkdir(parents=True, exist_ok=True)
    hmac.key_path.write_bytes(bytes(range(32)))

    def authority(authority_type, name):
        return authority_type(
            authority_ref=f"composition-{name}-authority",
            authenticator=hmac,
        )

    storage = authority(DockerStorageMappingHmacAuthorityV1, "storage")
    wsl = authority(DockerWSLRootMappingHmacAuthorityV1, "wsl")
    pair = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="composition-pair-authority", authenticator=hmac,
        storage_mapping_authority=storage, wsl_mapping_authority=wsl,
    )
    environment = DockerCLIEnvironmentV1.build((
        ("SystemRoot", "C:\\Windows"), ("TEMP", "C:\\Temp"),
        ("TMP", "C:\\Temp"), ("WINDIR", "C:\\Windows"),
    ))
    cli_policy = DockerCLIPolicyV1.build(
        "C:\\Program Files\\Docker\\docker.exe", DockerLocalEndpointDescriptorV1.build(
            "desktop-linux", "npipe:////./pipe/dockerDesktopLinuxEngine", False),
        environment, timeout_ms=100, terminate_grace_ms=10,
        stdout_limit=100, stderr_limit=100, combined_limit=200,
    )
    socket = SimpleNamespace(
        st_dev=1, st_ino=2, st_mode=S_IFSOCK | 0o600,
        st_uid=1000, st_gid=1000, st_nlink=1,
    )
    request = DockerHostCompositionRequestV1(
        launch=launch, filesystem=filesystem,
        source_data_binding=bindings["source-data"],
        source_control_binding=bindings["source-control"],
        source_component="dataset-source",
        stage_data_binding=bindings["stage-data"],
        stage_control_binding=bindings["stage-control"],
        stage_destination_ref="stage-destination",
        artifact_data_binding=bindings["artifact-data"],
        artifact_control_binding=bindings["artifact-control"],
        source_purpose_ref="docker-stage-source",
        source_members=(BundleMemberCommandV1(
            "dataset/data.json", profile.roots.source_ref, 5, D[8]
        ),),
        source_mapping_ref="source-mapping",
        source_wsl_root="/mnt/synaptic/source",
        artifact_mapping_ref="artifact-mapping",
        artifact_wsl_root="/mnt/synaptic/artifacts",
        artifact_destination_ref="artifact-destination",
        wsl_distro="Ubuntu-22.04",
        container_user="1000:1000",
        environment_policy=DockerWorkloadEnvironmentPolicyV1.build(
            allowed_keys=()
        ),
        environment_overrides=(), cli_policy=cli_policy,
        wsl_interop_path="/run/WSL/42_interop",
        lstat=lambda _path: socket,
        popen_factory=lambda *_args, **_kwargs: object(),
        monotonic=lambda: 0.0, thread_factory=Thread,
        declaration_authority=authority(
            DockerSourceDeclarationHmacAuthorityV1, "declaration"
        ),
        stage_record_authority=authority(
            DockerStageBundleRecordHmacAuthorityV1, "stage"
        ),
        storage_mapping_authority=storage, wsl_mapping_authority=wsl,
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
        pair_authority=pair,
    )
    return (request, port) if include_port else request


def test_real_released_graph_composes_without_process_or_transfer_gap(tmp_path):
    request = _real_request(tmp_path)
    builder = subject.DockerCapabilityAssemblyBuilderV1(
        filesystem=request.filesystem,
        source_data_binding=request.source_data_binding,
        source_control_binding=request.source_control_binding,
        source_ref=request.launch.profile.roots.source_ref,
        source_component=request.source_component,
        stage_data_binding=request.stage_data_binding,
        stage_control_binding=request.stage_control_binding,
        stage_destination_ref=request.stage_destination_ref,
        artifact_data_binding=request.artifact_data_binding,
        artifact_control_binding=request.artifact_control_binding,
    )
    live = builder.build()
    try:
        subject._prepare(request, live)
    except BaseException:
        live.abort()
        raise
    live.abort()
    facade = compose_docker_host_v1(_real_request(tmp_path / "second"))
    assert type(facade) is DockerHostFacadeV1
    assert facade.lifecycle_state.value == "OPEN"
    closed = facade.close()
    assert closed.code.value == "CLEANED"


@pytest.mark.parametrize("cut", (
    "_issue_pair",
    "ImmutableDockerStoragePathMappingPairRegistryV1",
    "DockerImmutableBundleSourceRegistryV1", "ImmutableSourceBundleV1",
    "DockerSingleLaunchSourceDeclarationResolverV1",
    "InMemoryDockerStageBundleStoreV1", "DockerBundleSourceSealAdapterV1",
    "DockerSameProcessBindingStoreV1",
    "DockerCommandBindingEnvelopeAuthorityViewV1",
    "DockerSubmitMountResolverV1", "DockerAuthenticatedPairPathBinderV1",
    "DockerWSLPathTranslatorV1",
    "DockerExplicitWorkloadEnvironmentResolverV1",
    "DockerWSLExecutableBindingV1", "DockerPrivateWSLInteropChannelV1",
    "DockerWSLInteropPopenFactoryV1", "DockerCLIRunnerV1",
    "InMemoryDockerControlStoreV1", "DockerHostCreateV1",
    "DockerHostStartV1", "DockerHostControlV1", "_DockerControlAdapterV1",
    "DockerEvidenceAuthorityViewV1", "DockerCoordinatorHostPortsV1",
    "compose_docker_same_process_coordinator_v1",
    "DockerPrivateFacadeRuntimeAdapterV1",
))
def test_every_pretransfer_graph_construction_cut_aborts_all_capabilities(
    tmp_path, monkeypatch, cut,
):
    request, port = _real_request(tmp_path / cut, include_port=True)

    def explode(*_args, **_kwargs):
        raise KeyboardInterrupt("secret-construction-cut")

    if cut in {"DockerWSLExecutableBindingV1",
               "DockerPrivateWSLInteropChannelV1"}:
        class Explode:
            build = staticmethod(explode)
            acquire = staticmethod(explode)

        replacement = Explode
    else:
        replacement = explode
    monkeypatch.setattr(subject, cut, replacement)
    with pytest.raises(DockerHostCompositionErrorV1) as caught:
        compose_docker_host_v1(request)
    assert caught.value.code is DockerHostCompositionCodeV1.COMPOSITION_FAILED
    assert caught.value.args == ()
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert port.live_directories == {}
