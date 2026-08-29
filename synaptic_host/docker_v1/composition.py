"""Closed production composition for the same-process Docker host facade."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from synaptic_tuner.api.v1.docker import (
    DockerCoordinatorHostPortsV1,
    DockerSameProcessBindingStoreV1,
    DockerSameProcessLaunchV1,
    compose_docker_same_process_coordinator_v1,
)
from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.model import BundleMemberCommandV1
from synaptic_host.bundle_io_v1.ports import BundleMountVerifyAccessV1
from synaptic_host.docker_v1.authority import (
    BundleBindingHmacAuthorityV1,
    DockerAbsenceHmacAuthorityV1,
    DockerCommandBindingEnvelopeAuthorityViewV1,
    DockerCommandBindingHmacAuthorityV1,
    DockerControlIntentHmacAuthorityV1,
    DockerCreatePathBindingHmacAuthorityV1,
    DockerEvidenceAuthorityViewV1,
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
from synaptic_host.docker_v1.binding import (
    DockerAuthenticatedPairPathBinderV1,
    DockerExplicitWorkloadEnvironmentResolverV1,
    DockerWorkloadEnvironmentPolicyV1,
)
from synaptic_host.docker_v1.capabilities import (
    DockerImmutableBundleSourceRegistryV1,
    DockerSingleLaunchSourceDeclarationResolverV1,
    ImmutableDockerStoragePathMappingPairRegistryV1,
)
from synaptic_host.docker_v1.capability_assembly import (
    DockerCapabilityAssemblyBuilderV1,
    DockerCapabilityAssemblyErrorV1,
    DockerCapabilityCleanupResultV1,
    DockerCapabilityCleanupStatusV1,
)
from synaptic_host.docker_v1.cli import DockerCLIRunnerV1
from synaptic_host.docker_v1.control import DockerHostControlV1
from synaptic_host.docker_v1.control_private import (
    DockerPrivateCreateInvocationFactoryV1,
)
from synaptic_host.docker_v1.create import DockerHostCreateV1
from synaptic_host.docker_v1.facade import (
    DockerHostFacadeV1,
    DockerPrivateFacadeRuntimeAdapterV1,
)
from synaptic_host.docker_v1.interop import (
    DockerPrivateWSLInteropChannelV1,
    DockerWSLExecutableBindingV1,
    DockerWSLInteropPopenFactoryV1,
)
from synaptic_host.docker_v1.memory import (
    InMemoryDockerControlStoreV1,
    InMemoryDockerStageBundleStoreV1,
)
from synaptic_host.docker_v1.model import (
    DockerCLIPolicyV1,
    DockerStorageMappingV1,
    DockerStoragePathMappingPairV1,
    DockerStoragePurposeV1,
    DockerWSLPathPurposeV1,
    DockerWSLRootMappingV1,
)
from synaptic_host.docker_v1.mounts import DockerSubmitMountResolverV1
from synaptic_host.docker_v1.paths import DockerWSLPathTranslatorV1
from synaptic_host.docker_v1.source import DockerBundleSourceSealAdapterV1
from synaptic_host.docker_v1.start import DockerHostStartV1
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import LocalRootBindingV1


class DockerHostCompositionCodeV1(str, Enum):
    INPUT_INVALID = "DOCKER_HOST_COMPOSITION_INPUT_INVALID"
    COMPOSITION_FAILED = "DOCKER_HOST_COMPOSITION_FAILED"
    CLEANUP_FAILED = "DOCKER_HOST_COMPOSITION_CLEANUP_FAILED"


class DockerHostCompositionErrorV1(RuntimeError):
    __slots__ = ("code",)

    def __init__(self, code):
        if type(code) is not DockerHostCompositionCodeV1:
            code = DockerHostCompositionCodeV1.COMPOSITION_FAILED
        RuntimeError.__init__(self)
        object.__setattr__(self, "code", code)

    def __setattr__(self, name, value):
        if name == "code":
            raise AttributeError
        BaseException.__setattr__(self, name, value)

    def __init_subclass__(cls, **_kwargs):
        raise TypeError("Docker host composition error is final")


def _fail(code):
    raise DockerHostCompositionErrorV1(code) from None


_AUTHORITY_TYPES = (
    DockerSourceDeclarationHmacAuthorityV1,
    DockerStageBundleRecordHmacAuthorityV1,
    DockerStorageMappingHmacAuthorityV1,
    DockerWSLRootMappingHmacAuthorityV1,
    BundleBindingHmacAuthorityV1,
    DockerSourceSealHmacAuthorityV1,
    DockerCreatePathBindingHmacAuthorityV1,
    DockerWorkloadEnvironmentBindingHmacAuthorityV1,
    DockerControlIntentHmacAuthorityV1,
    DockerMutationRecordHmacAuthorityV1,
    DockerAbsenceHmacAuthorityV1,
    DockerExpectedCreateBindingHmacAuthorityV1,
    DockerCommandBindingHmacAuthorityV1,
    DockerStoragePathMappingPairHmacAuthorityV1,
)


@dataclass(frozen=True, slots=True)
class DockerHostCompositionRequestV1:
    launch: DockerSameProcessLaunchV1
    filesystem: LocalFilesystemV1
    source_data_binding: LocalRootBindingV1
    source_control_binding: LocalRootBindingV1
    source_component: str
    stage_data_binding: LocalRootBindingV1
    stage_control_binding: LocalRootBindingV1
    stage_destination_ref: str
    artifact_data_binding: LocalRootBindingV1
    artifact_control_binding: LocalRootBindingV1
    source_purpose_ref: str
    source_members: tuple[BundleMemberCommandV1, ...]
    source_mapping_ref: str
    source_wsl_root: str
    artifact_mapping_ref: str
    artifact_wsl_root: str
    artifact_destination_ref: str
    wsl_distro: str
    environment_policy: DockerWorkloadEnvironmentPolicyV1
    environment_overrides: tuple[tuple[str, str], ...]
    cli_policy: DockerCLIPolicyV1
    wsl_interop_path: str
    lstat: object
    popen_factory: object
    monotonic: object
    thread_factory: object
    declaration_authority: DockerSourceDeclarationHmacAuthorityV1
    stage_record_authority: DockerStageBundleRecordHmacAuthorityV1
    storage_mapping_authority: DockerStorageMappingHmacAuthorityV1
    wsl_mapping_authority: DockerWSLRootMappingHmacAuthorityV1
    bundle_binding_authority: BundleBindingHmacAuthorityV1
    source_seal_authority: DockerSourceSealHmacAuthorityV1
    path_binding_authority: DockerCreatePathBindingHmacAuthorityV1
    environment_authority: DockerWorkloadEnvironmentBindingHmacAuthorityV1
    intent_authority: DockerControlIntentHmacAuthorityV1
    mutation_record_authority: DockerMutationRecordHmacAuthorityV1
    absence_authority: DockerAbsenceHmacAuthorityV1
    expected_authority: DockerExpectedCreateBindingHmacAuthorityV1
    command_binding_authority: DockerCommandBindingHmacAuthorityV1
    pair_authority: DockerStoragePathMappingPairHmacAuthorityV1

    def __post_init__(self):
        failed = False
        try:
            roots = (
                self.source_data_binding, self.source_control_binding,
                self.stage_data_binding, self.stage_control_binding,
                self.artifact_data_binding, self.artifact_control_binding,
            )
            authorities = (
                self.declaration_authority, self.stage_record_authority,
                self.storage_mapping_authority, self.wsl_mapping_authority,
                self.bundle_binding_authority, self.source_seal_authority,
                self.path_binding_authority, self.environment_authority,
                self.intent_authority, self.mutation_record_authority,
                self.absence_authority, self.expected_authority,
                self.command_binding_authority, self.pair_authority,
            )
            strings = (
                self.source_component, self.stage_destination_ref,
                self.source_purpose_ref, self.source_mapping_ref,
                self.source_wsl_root, self.artifact_mapping_ref,
                self.artifact_wsl_root, self.artifact_destination_ref,
                self.wsl_distro, self.wsl_interop_path,
            )
            if (
                type(self.launch) is not DockerSameProcessLaunchV1
                or type(self.filesystem) is not LocalFilesystemV1
                or any(type(value) is not LocalRootBindingV1 for value in roots)
                or type(self.source_members) is not tuple
                or not self.source_members
                or any(type(value) is not BundleMemberCommandV1
                       for value in self.source_members)
                or any(type(value) is not str or not value for value in strings)
                or type(self.environment_policy)
                is not DockerWorkloadEnvironmentPolicyV1
                or type(self.environment_overrides) is not tuple
                or any(type(value) is not tuple or len(value) != 2
                       for value in self.environment_overrides)
                or type(self.cli_policy) is not DockerCLIPolicyV1
                or any(not callable(value) for value in (
                    self.lstat, self.popen_factory, self.monotonic,
                    self.thread_factory,
                ))
                or any(type(value) is not expected for value, expected in zip(
                    authorities, _AUTHORITY_TYPES, strict=True
                ))
            ):
                raise ValueError
        except DockerHostCompositionErrorV1:
            raise
        except BaseException:
            failed = True
        if failed:
            _fail(DockerHostCompositionCodeV1.INPUT_INVALID)


class _DockerControlAdapterV1:
    __slots__ = ("_create", "_start", "_lookup")

    def __init__(self, create, start, lookup):
        self._create, self._start, self._lookup = create, start, lookup

    def create_once(self, **kwargs):
        return self._create.create_once(**kwargs)

    def start_once(self, container_ref, labels):
        return self._start.start_once(container_ref, labels)

    def lookup(self, request):
        return self._lookup.lookup(request)


def _issue_pair(request, assembly, *, source):
    if source:
        access = BundleMountVerifyAccessV1.build(
            assembly.stage_access.destination_ref,
            assembly.stage_access.verify_borrow,
            assembly.stage_access.verify_root,
        )
        storage = DockerStorageMappingV1.build(
            mapping_ref=request.source_mapping_ref,
            declared_ref=request.launch.profile.roots.source_ref,
            purpose=DockerStoragePurposeV1.SOURCE_BUNDLE,
            wsl_root=request.source_wsl_root,
            root_authority_digest=assembly.stage_access.root_authority_digest,
            destination_ref=assembly.stage_access.destination_ref,
            access_digest=access.access_digest,
            verify_access=access,
        )
        wsl = DockerWSLRootMappingV1.build(
            request.source_mapping_ref, request.wsl_distro,
            DockerWSLPathPurposeV1.SOURCE_READ, request.source_wsl_root,
        )
    else:
        storage = DockerStorageMappingV1.build(
            mapping_ref=request.artifact_mapping_ref,
            declared_ref=request.launch.profile.roots.artifact_ref,
            purpose=DockerStoragePurposeV1.ARTIFACT_OUTPUT,
            wsl_root=request.artifact_wsl_root,
            root_authority_digest=(
                assembly.artifact_root_authority.authority_digest
            ),
            destination_ref=request.artifact_destination_ref,
            access_digest=assembly.artifact_access_digest,
        )
        wsl = DockerWSLRootMappingV1.build(
            request.artifact_mapping_ref, request.wsl_distro,
            DockerWSLPathPurposeV1.ARTIFACT_WRITE,
            request.artifact_wsl_root,
        )
    storage_envelope = request.storage_mapping_authority.issue(storage)
    wsl_envelope = request.wsl_mapping_authority.issue(wsl)
    pair = DockerStoragePathMappingPairV1.build(
        storage_envelope, wsl_envelope
    )
    return request.pair_authority.issue(pair)


def _prepare(request, live_build):
    assembly = live_build.assembly
    source_pair = _issue_pair(request, assembly, source=True)
    artifact_pair = _issue_pair(request, assembly, source=False)
    mapping_registry = ImmutableDockerStoragePathMappingPairRegistryV1(
        source_pair=source_pair, artifact_pair=artifact_pair,
        authority=request.pair_authority,
    )

    source_registry = DockerImmutableBundleSourceRegistryV1((assembly.source,))
    bundle = ImmutableSourceBundleV1(
        request.filesystem, source_registry,
        request.bundle_binding_authority,
    )
    declarations = DockerSingleLaunchSourceDeclarationResolverV1(
        profile=request.launch.profile,
        source=assembly.source,
        source_digest=request.launch.plan.basis.source_digest,
        purpose_ref=request.source_purpose_ref,
        destination_ref=assembly.stage_access.destination_ref,
        members=request.source_members,
        bundle_access=assembly.stage_access,
        declaration_authority=request.declaration_authority,
    )
    stage_store = InMemoryDockerStageBundleStoreV1(
        authority=request.stage_record_authority
    )
    source_seals = DockerBundleSourceSealAdapterV1(
        declarations=declarations,
        declaration_authority=request.declaration_authority,
        bundle=bundle,
        binding_authority=request.bundle_binding_authority,
        source_seal_authority=request.source_seal_authority,
        stage_record_authority=request.stage_record_authority,
        store=stage_store,
    )

    binding_store = DockerSameProcessBindingStoreV1(
        request.command_binding_authority
    )
    command_envelopes = DockerCommandBindingEnvelopeAuthorityViewV1(
        request.command_binding_authority
    )
    mount_resolver = DockerSubmitMountResolverV1(
        command_catalog=binding_store,
        command_authority=command_envelopes,
        stage_store=stage_store,
        stage_record_authority=request.stage_record_authority,
        declaration_authority=request.declaration_authority,
        binding_authority=request.bundle_binding_authority,
        source_seal_authority=request.source_seal_authority,
        mapping_registry=mapping_registry,
        mapping_authority=request.storage_mapping_authority,
        bundle_verifier=bundle,
    )
    path_binder = DockerAuthenticatedPairPathBinderV1(
        source_pair=source_pair, artifact_pair=artifact_pair,
        pair_authority=request.pair_authority,
        binding_authority=request.path_binding_authority,
    )
    path_translator = DockerWSLPathTranslatorV1(
        registry=mapping_registry, authority=request.wsl_mapping_authority
    )
    environment_resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=request.environment_policy,
        overrides=request.environment_overrides,
        authority=request.environment_authority,
    )

    executable = DockerWSLExecutableBindingV1.build(
        request.cli_policy.executable
    )
    channel = DockerPrivateWSLInteropChannelV1.acquire(
        request.wsl_interop_path, lstat=request.lstat
    )
    popen = DockerWSLInteropPopenFactoryV1(
        executable=executable,
        environment=request.cli_policy.environment,
        channel=channel,
        popen_factory=request.popen_factory,
    )
    typed_cli = DockerCLIRunnerV1(
        request.cli_policy,
        popen_factory=popen,
        monotonic=request.monotonic,
        thread_factory=request.thread_factory,
    )

    control_store = InMemoryDockerControlStoreV1()
    create = DockerHostCreateV1(
        mount_resolver=mount_resolver,
        path_binder=path_binder,
        path_translator=path_translator,
        environment_resolver=environment_resolver,
        typed_runner=typed_cli,
        expected_publisher=control_store,
        mutation_repository=control_store,
        path_authority=request.path_binding_authority,
        environment_authority=request.environment_authority,
        intent_authority=request.intent_authority,
        expected_authority=request.expected_authority,
        record_authority=request.mutation_record_authority,
    )
    start = DockerHostStartV1(
        typed_runner=typed_cli,
        mutation_repository=control_store,
        expected_catalog=control_store,
        expected_authority=request.expected_authority,
        intent_authority=request.intent_authority,
        environment_authority=request.environment_authority,
        record_authority=request.mutation_record_authority,
    )
    inventory = DockerHostControlV1(
        typed_cli=typed_cli,
        mutation_repository=control_store,
        mutation_record_authority=request.mutation_record_authority,
        expected_catalog=control_store,
        expected_authority=request.expected_authority,
        intent_authority=request.intent_authority,
        environment_authority=request.environment_authority,
        absence_authority=request.absence_authority,
    )
    control = _DockerControlAdapterV1(create, start, inventory)
    evidence = DockerEvidenceAuthorityViewV1(
        source_seal_authority=request.source_seal_authority,
        absence_authority=request.absence_authority,
    )
    ports = DockerCoordinatorHostPortsV1(
        binding_store=binding_store,
        binding_authority=request.command_binding_authority,
        image_inventory=inventory,
        source_seals=source_seals,
        control=control,
        evidence_authority=evidence,
    )
    runtime = compose_docker_same_process_coordinator_v1(
        request.launch, ports
    )
    adapter = DockerPrivateFacadeRuntimeAdapterV1(
        start=runtime.start,
        reconcile=runtime.reconcile,
        binding=runtime.binding,
    )
    return adapter


def _abort(live_build):
    try:
        result = live_build.abort()
        return (
            type(result) is not DockerCapabilityCleanupResultV1
            or result.status is not DockerCapabilityCleanupStatusV1.CLEANED
        )
    except BaseException:
        return True


def _recover(handoff):
    try:
        result = handoff.recover_unpublished()
        return (
            type(result) is not DockerCapabilityCleanupResultV1
            or result.status is not DockerCapabilityCleanupStatusV1.CLEANED
        )
    except BaseException:
        return True


def compose_docker_host_v1(request):
    if type(request) is not DockerHostCompositionRequestV1:
        _fail(DockerHostCompositionCodeV1.INPUT_INVALID)
    live_build = None
    handoff = None
    preparation_failure = None
    try:
        builder = DockerCapabilityAssemblyBuilderV1(
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
        live_build = builder.build()
        adapter = _prepare(request, live_build)
    except BaseException as error:
        cleanup_failed = False
        if live_build is not None:
            cleanup_failed = _abort(live_build)
        elif type(error) is DockerCapabilityAssemblyErrorV1:
            result = error.cleanup_result
            cleanup_failed = (
                type(result) is DockerCapabilityCleanupResultV1
                and result.status
                is DockerCapabilityCleanupStatusV1.CLEANUP_FAILED
            )
        preparation_failure = (
            DockerHostCompositionCodeV1.CLEANUP_FAILED
            if cleanup_failed
            else DockerHostCompositionCodeV1.COMPOSITION_FAILED
        )
    if preparation_failure is not None:
        _fail(preparation_failure)
    publication_failure = None
    try:
        handoff = live_build.prepare_handoff()
        facade = DockerHostFacadeV1(adapter, handoff)
        handoff.commit_handoff()
    except BaseException:
        cleanup_failed = (
            _abort(live_build) if handoff is None
            else _recover(handoff)
        )
        publication_failure = (
            DockerHostCompositionCodeV1.CLEANUP_FAILED
            if cleanup_failed
            else DockerHostCompositionCodeV1.COMPOSITION_FAILED
        )
    if publication_failure is not None:
        _fail(publication_failure)
    return facade


__all__: tuple[str, ...] = ()
