from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from synaptic_tuner.api.v1.providers import ProviderCapabilities, ProviderDescriptor, ProviderRef
from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.foundation_v2.canonical import canonical_bytes, domain_digest
from tuner.execution.foundation_v2.commands import (
    CanonicalProviderPayloadV1,
    build_submit_command,
)
from tuner.execution.foundation_v2.executors import AdapterDescriptorV1, ExecutorDescriptorV1
from tuner.execution.foundation_v2.preparation import CanonicalPreparationV2
from tuner.execution.foundation_v2.references import ExecutionScopeV1
from tuner.execution.foundation_v2.references import StagePredecessorV2
from tuner.execution.coordinator_v1.model import ProviderExecutionBindingV1
from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerCommandBindingV1,
    AuthenticatedDockerSourceSealV1,
    DockerArtifactContractV1,
    DockerCommandBindingV1,
    DockerEffectIdentityV1,
    DockerImageV1,
    DockerProfileV1,
    DockerRootsV1,
    DockerRuntimeV1,
    DockerSourceSealContentV1,
    DockerSourceSealRequestV1,
    DockerWorkloadV1,
    PreparedDockerPlanV1,
    labels_for,
)

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleBindingV1,
    BundleLookupResultV1,
    BundleLookupStatusV1,
    BundleMemberCommandV1,
    BundleMemberEvidenceV1,
    BundleMountVerificationV1,
    bundle_companion_digest_v1,
    digest_v1,
)
from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.ports import (
    BundleBorrowAccessV1,
    BundleMountVerifyAccessV1,
    BundleSourceV1,
)
from synaptic_host.docker_v1.model import (
    AuthenticatedDockerSourceDeclarationV1,
    AuthenticatedDockerStageBundleBindingV1,
    AuthenticatedDockerStorageMappingV1,
    DockerSourceDeclarationV1,
    DockerStorageMappingV1,
    DockerStoragePurposeV1,
)
from synaptic_host.docker_v1.ports import DockerSourceResolutionV1
from synaptic_host.local_io_v1.filesystem import LocalFilesystemV1
from synaptic_host.local_io_v1.model import (
    BorrowPurposeV1,
    LocalFileIdentityV1,
    RetainedRootBorrowRequestV1,
    RootAccessV1,
)

from bundle_io_v1.conftest import Authenticator, SourceRegistry as BundleSourceRegistry, borrow
from local_io_v1.conftest import FakePosixFilesystemPortV1


D = tuple(character * 64 for character in "123456789abcdef")


def _profile(profile_ref: str) -> DockerProfileV1:
    provider = ProviderRef("docker", profile_ref)
    return DockerProfileV1.build(
        provider=provider,
        descriptor=ProviderDescriptor(
            "synaptic-provider-descriptor/v1", "docker", "Docker", "1.0.0",
            ProviderCapabilities(True, True, True, True, True, False),
        ),
        scope=ExecutionScopeV1("account", "namespace"),
        executor_descriptor=ExecutorDescriptorV1(
            "docker", "docker-executor-v1", "1.0.0"
        ),
        adapter_descriptor=AdapterDescriptorV1(
            "docker", "docker-reconcile-v1", "1.0.0"
        ),
        image=DockerImageV1("fixture-image", "sha256:" + "a" * 64),
        runtime=DockerRuntimeV1(
            2, 1_073_741_824, 3600,
            AcceleratorDeviceRequestV1("cpu", (), ()),
        ),
        workload=DockerWorkloadV1(("python", "run.py"), (), D[0]),
        roots=DockerRootsV1("dataset-source", "artifact-root"),
        artifacts=DockerArtifactContractV1(("result",), 1_048_576, 1_048_576),
        resource_digest=D[1], quote_digest=D[2], secret_requirements_digest=D[3],
    )


def _prepared(profile):
    execution = ProviderExecutionBindingV1(
        profile.provider, profile.descriptor.descriptor_digest,
        profile.profile_digest, profile.scope, profile.executor_descriptor,
        profile.adapter_descriptor.digest, profile.resource_digest,
        profile.quote_digest, profile.secret_requirements_digest,
    )
    preparation = CanonicalPreparationV2.build(
        provider=profile.provider, scope=profile.scope,
        project_ref="project", run_id="run", plan_fingerprint=D[4],
        source_digest=D[8], workload_digest=profile.workload.workload_digest,
        runtime_digest=profile.runtime.digest,
        resource_digest=profile.resource_digest,
        artifact_contract_digest=profile.artifacts.digest,
        quote_digest=profile.quote_digest,
        secret_requirements_digest=profile.secret_requirements_digest,
        execution_binding_digest=execution.binding_digest,
    )
    return (
        PreparedDockerPlanV1(
            profile, "project", "run", D[4], D[8],
            preparation.preparation_digest,
        ),
        preparation,
    )


@pytest.fixture(params=("opaque/local-cpu", "opaque/registry-cpu"))
def source_env(request):
    profile = _profile(request.param)
    plan, _ = _prepared(profile)
    identity = DockerEffectIdentityV1(D[7], "stage-effect", "stage", plan)
    source_request = DockerSourceSealRequestV1(identity, "dataset-source", D[8])

    port = FakePosixFilesystemPortV1()
    base = Path.cwd() / ".fake-metadata" / "docker-source"
    data_path, control_path = base / "data", base / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    authenticator = Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(
        authenticator.binding(data_path, "docker-data"),
        authenticator.binding(control_path, "docker-control"),
    )
    create_borrow, create_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_DESTINATION_CREATE,
        RootAccessV1.READ_CREATE,
    )
    verify_borrow, verify_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_MOUNT_VERIFY,
        RootAccessV1.READ_ONLY,
    )
    access = BundleBorrowAccessV1.build(
        "docker-stage-destination", create_borrow, create_root,
        verify_borrow, verify_root,
    )
    members = (BundleMemberCommandV1("dataset/data.json", "dataset-source", 5, D[8]),)
    declaration = DockerSourceDeclarationV1.build(
        source_ref=source_request.source_ref,
        source_digest=source_request.source_digest,
        effect_identity_digest=identity.digest,
        prepared_plan_digest=plan.digest,
        profile_ref=profile.provider.profile_ref,
        purpose_ref="docker-stage-source",
        destination_ref=access.destination_ref,
        root_authority_digest=access.root_authority_digest,
        bundle_access_digest=access.access_digest,
        members=members,
    )
    return source_request, declaration, access


class DeclarationAuthority:
    authority_ref = "docker-declaration-authority"
    key_ref = "docker-declaration-key"

    def __init__(self):
        self.issue_calls = 0
        self.authenticate_calls = 0

    def _tag(self, content):
        return digest_v1({
            "authority_ref": self.authority_ref,
            "declaration_digest": content.declaration_digest,
            "key_ref": self.key_ref,
            "schema_version": "test-docker-declaration-tag/v1",
        })

    def issue(self, content):
        self.issue_calls += 1
        return AuthenticatedDockerSourceDeclarationV1(
            content, self.authority_ref, self.key_ref, self._tag(content)
        )

    def authenticate(self, value):
        self.authenticate_calls += 1
        try:
            if (
                type(value) is not AuthenticatedDockerSourceDeclarationV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
                or value.tag != self._tag(value.content)
            ):
                return None
            content = value.content
            rebuilt = DockerSourceDeclarationV1(
                content.source_ref, content.source_digest,
                content.effect_identity_digest, content.prepared_plan_digest,
                content.profile_ref, content.purpose_ref, content.destination_ref,
                content.root_authority_digest, content.bundle_access_digest,
                tuple(replace(member) for member in content.members),
                content.bundle_command_digest, content.declaration_digest,
            )
            return AuthenticatedDockerSourceDeclarationV1(
                rebuilt, self.authority_ref, self.key_ref, value.tag
            )
        except BaseException:
            return None


class BindingAuthority:
    authority_ref = "bundle-binding-authority"
    key_ref = "bundle-binding-key"

    def __init__(self):
        self.issue_calls = 0
        self.authenticate_calls = 0

    def _tag(self, content):
        return digest_v1({
            "authority_ref": self.authority_ref,
            "binding_digest": content.binding_digest,
            "key_ref": self.key_ref,
            "schema_version": "test-bundle-binding-tag/v1",
        })

    def issue(self, content):
        self.issue_calls += 1
        return AuthenticatedBundleBindingV1(
            content, self.authority_ref, self.key_ref, self._tag(content)
        )

    def authenticate(self, value):
        self.authenticate_calls += 1
        try:
            if (
                type(value) is not AuthenticatedBundleBindingV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
                or value.tag != self._tag(value.content)
            ):
                return None
            return AuthenticatedBundleBindingV1(
                replace(value.content), self.authority_ref, self.key_ref, value.tag
            )
        except BaseException:
            return None


class SealAuthority:
    authority_ref = "docker-source-seal-authority"
    key_ref = "docker-source-seal-key"

    def __init__(self):
        self.issue_calls = 0
        self.authenticate_calls = 0

    def _tag(self, content):
        return domain_digest(
            "test-docker-source-seal-tag/v1",
            canonical_bytes({
                "authority_ref": self.authority_ref,
                "content_digest": content.content_digest,
                "key_ref": self.key_ref,
            }),
        )

    def issue(self, content):
        self.issue_calls += 1
        return AuthenticatedDockerSourceSealV1(
            content, self.authority_ref, self.key_ref, self._tag(content)
        )

    def authenticate(self, value):
        self.authenticate_calls += 1
        try:
            if (
                type(value) is not AuthenticatedDockerSourceSealV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
                or value.tag != self._tag(value.content)
            ):
                return None
            content = value.content
            return AuthenticatedDockerSourceSealV1(
                DockerSourceSealContentV1(
                    content.request_digest, content.effect_identity_digest,
                    content.source_ref, content.source_digest, content.read_only,
                    content.stage_ref, content.evidence_digest,
                ),
                self.authority_ref, self.key_ref, value.tag,
            )
        except BaseException:
            return None


def binding_for(command, root_authority_digest):
    member_identity = LocalFileIdentityV1(1, 11, 0o100600, 1, 1, 1, 5)
    member = BundleMemberEvidenceV1(
        command.members[0].logical_name, "member-0000", 5,
        command.members[0].sha256, member_identity,
    )
    members = (member,)
    manifest_identity = LocalFileIdentityV1(1, 12, 0o100600, 1, 1, 1, 100)
    marker_identity = LocalFileIdentityV1(1, 13, 0o100600, 2, 2, 1, 200)
    suffix = command.command_digest[:32]
    companion = ".synaptic-commit-companion-" + bundle_companion_digest_v1(
        command.command_digest, command.destination_ref, root_authority_digest
    )
    inventory_digest = digest_v1([member.canonical() for member in members])
    body = {
        "command_digest": command.command_digest,
        "companion_name": companion,
        "destination_ref": command.destination_ref,
        "inventory_digest": inventory_digest,
        "manifest_digest": D[9],
        "manifest_identity": manifest_identity.canonical(),
        "marker_identity": marker_identity.canonical(),
        "marker_name": "COMMIT-" + suffix,
        "members": [member.canonical()],
        "private_name": ".synaptic-bundle-" + suffix,
        "root_authority_digest": root_authority_digest,
        "schema_version": "synaptic-host-bundle-binding/v1",
    }
    return BundleBindingV1(
        command.command_digest, command.destination_ref, root_authority_digest,
        ".synaptic-bundle-" + suffix, "COMMIT-" + suffix, companion,
        D[9], inventory_digest, members, manifest_identity, marker_identity,
        digest_v1(body),
    )


class Bundle:
    def __init__(self):
        self.calls = []
        self.raise_error = False
        self.status = BundleLookupStatusV1.FOUND
        self.transform = lambda value: value

    def seal(self, command, access):
        self.calls.append((command, access))
        if self.raise_error:
            raise RuntimeError("secret bundle failure")
        binding = (
            binding_for(command, access.root_authority_digest)
            if self.status is BundleLookupStatusV1.FOUND else None
        )
        if binding is not None:
            binding = self.transform(binding)
        return BundleLookupResultV1(self.status, command.command_digest, binding)


class Registry:
    def __init__(self, resolution):
        self.resolution = resolution
        self.calls = 0

    def resolve(self, request):
        self.calls += 1
        return self.resolution


class StageRecordAuthority:
    authority_ref = "docker-stage-record-authority"
    key_ref = "docker-stage-record-key"

    def _tag(self, content):
        return digest_v1({
            "authority_ref": self.authority_ref,
            "effect_identity_digest": content.effect_identity_digest,
            "key_ref": self.key_ref,
            "record_digest": content.record_digest,
            "schema_version": "test-docker-stage-record-tag/v1",
        })

    def issue(self, content):
        return AuthenticatedDockerStageBundleBindingV1(
            content, self.authority_ref, self.key_ref, self._tag(content)
        )

    def authenticate(self, value):
        try:
            if (
                type(value) is not AuthenticatedDockerStageBundleBindingV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
                or value.tag != self._tag(value.content)
            ):
                return None
            return AuthenticatedDockerStageBundleBindingV1(
                replace(value.content), self.authority_ref,
                self.key_ref, value.tag,
            )
        except BaseException:
            return None


class Store:
    def __init__(self):
        self.values = {}
        self.get_calls = 0
        self.put_calls = 0
        self.fail_get = False
        self.fail_put_before = False
        self.lose_put_return = False
        self.stage_authority = StageRecordAuthority()

    def get_by_stage_effect_id(self, effect_id):
        self.get_calls += 1
        if self.fail_get:
            raise RuntimeError("secret store read")
        return self.values.get(effect_id)

    def put_if_absent(self, value):
        self.put_calls += 1
        if self.fail_put_before:
            raise RuntimeError("secret store write")
        retained = self.values.setdefault(value.content.stage_effect_id, value)
        if self.lose_put_return:
            raise RuntimeError("secret lost return")
        return retained


@pytest.fixture
def adapter_env(source_env):
    request, declaration, access = source_env
    declaration_authority = DeclarationAuthority()
    resolution = DockerSourceResolutionV1(
        declaration_authority.issue(declaration), access
    )
    registry = Registry(resolution)
    bundle = Bundle()
    binding_authority = BindingAuthority()
    seal_authority = SealAuthority()
    store = Store()
    return (
        request, registry, declaration_authority, bundle,
        binding_authority, seal_authority, store,
    )


@pytest.fixture(params=("opaque/local-cpu", "opaque/registry-cpu"))
def real_concurrency_env(request):
    payload = b"alpha"
    payload_sha = hashlib.sha256(payload).hexdigest()
    profile = _profile(request.param)
    plan, _ = _prepared(profile)
    identity = DockerEffectIdentityV1(D[7], "stage-effect", "stage", plan)
    source_request = DockerSourceSealRequestV1(identity, "dataset-source", D[8])

    port = FakePosixFilesystemPortV1()
    base = Path.cwd() / ".fake-metadata" / "docker-source-real"
    data_path, control_path = base / "data", base / "control"
    port.add_root(data_path, "data")
    port.add_root(control_path, "control")
    port.add_file("dir-data", "dataset-source", payload)
    authenticator = Authenticator()
    filesystem = LocalFilesystemV1(port, authenticator, native_platform="linux")
    authority = filesystem.retain_root_authority(
        authenticator.binding(data_path, "docker-real-data"),
        authenticator.binding(control_path, "docker-real-control"),
    )
    create_borrow, create_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_DESTINATION_CREATE,
        RootAccessV1.READ_CREATE,
    )
    verify_borrow, verify_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_MOUNT_VERIFY,
        RootAccessV1.READ_ONLY,
    )
    source_borrow, source_root = borrow(
        filesystem, authority, BorrowPurposeV1.BUNDLE_SOURCE_READ,
        RootAccessV1.READ_ONLY,
    )
    access = BundleBorrowAccessV1.build(
        "docker-stage-destination", create_borrow, create_root,
        verify_borrow, verify_root,
    )
    members = (
        BundleMemberCommandV1(
            "dataset/data.json", "dataset-source", len(payload), payload_sha
        ),
    )
    declaration = DockerSourceDeclarationV1.build(
        source_ref=source_request.source_ref,
        source_digest=source_request.source_digest,
        effect_identity_digest=identity.digest,
        prepared_plan_digest=plan.digest,
        profile_ref=profile.provider.profile_ref,
        purpose_ref="docker-stage-source",
        destination_ref=access.destination_ref,
        root_authority_digest=access.root_authority_digest,
        bundle_access_digest=access.access_digest,
        members=members,
    )
    declaration_authority = DeclarationAuthority()
    registry = Registry(DockerSourceResolutionV1(
        declaration_authority.issue(declaration), access
    ))
    sources = BundleSourceRegistry()
    sources.values["dataset-source"] = BundleSourceV1.build(
        "dataset-source", source_borrow, source_root, "dataset-source"
    )
    binding_authority = BindingAuthority()
    bundle = ImmutableSourceBundleV1(filesystem, sources, binding_authority)
    seal_authority = SealAuthority()
    store = Store()
    return (
        source_request, registry, declaration_authority, bundle,
        binding_authority, seal_authority, store, port, sources,
    )


class CommandAuthority:
    authority_ref = "docker-command-authority"
    key_ref = "docker-command-key"

    def __init__(self):
        self.calls = 0

    def _tag(self, content):
        return domain_digest(
            "test-docker-command-binding-tag/v1",
            canonical_bytes({
                "authority_ref": self.authority_ref,
                "binding_digest": content.binding_digest,
                "key_ref": self.key_ref,
            }),
        )

    def issue(self, content):
        return AuthenticatedDockerCommandBindingV1(
            content, content.binding_digest, self.authority_ref,
            self.key_ref, self._tag(content),
        )

    def authenticate(self, value):
        self.calls += 1
        try:
            if (
                type(value) is not AuthenticatedDockerCommandBindingV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
                or value.tag != self._tag(value.content)
            ):
                return None
            return AuthenticatedDockerCommandBindingV1(
                replace(value.content), value.binding_digest,
                self.authority_ref, self.key_ref, value.tag,
            )
        except BaseException:
            return None


class CommandCatalog:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def resolve(self, command_digest):
        self.calls.append(command_digest)
        return self.value


class MappingAuthority:
    authority_ref = "docker-mapping-authority"
    key_ref = "docker-mapping-key"

    def _tag(self, content):
        return digest_v1({
            "authority_ref": self.authority_ref,
            "key_ref": self.key_ref,
            "mapping_digest": content.mapping_digest,
            "schema_version": "test-docker-mapping-tag/v1",
        })

    def issue(self, content):
        return AuthenticatedDockerStorageMappingV1(
            content, self.authority_ref, self.key_ref, self._tag(content)
        )

    def authenticate(self, value):
        try:
            if (
                type(value) is not AuthenticatedDockerStorageMappingV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
                or value.tag != self._tag(value.content)
            ):
                return None
            return AuthenticatedDockerStorageMappingV1(
                replace(value.content), self.authority_ref,
                self.key_ref, value.tag,
            )
        except BaseException:
            return None


class MappingRegistry:
    def __init__(self, source, artifact):
        self.source = source
        self.artifact = artifact
        self.calls = []

    def resolve_source(self, source_ref):
        self.calls.append(("source", source_ref))
        return self.source

    def resolve_artifact(self, artifact_ref):
        self.calls.append(("artifact", artifact_ref))
        return self.artifact


class MountVerifier:
    def __init__(self):
        self.calls = []
        self.raise_error = None
        self.transform = lambda value: value

    def verify_mount(self, command, access, expected_authenticated_binding):
        self.calls.append((command, access, expected_authenticated_binding))
        if self.raise_error is not None:
            raise self.raise_error
        return self.transform(BundleMountVerificationV1.build(
            expected_authenticated_binding.content, access.access_digest
        ))


@pytest.fixture
def mount_env(adapter_env):
    from synaptic_host.docker_v1.source import DockerBundleSourceSealAdapterV1

    (
        stage_request, source_registry, declaration_authority, bundle,
        binding_authority, seal_authority, stage_store,
    ) = adapter_env
    source_adapter = DockerBundleSourceSealAdapterV1(
        declarations=source_registry,
        declaration_authority=declaration_authority,
        bundle=bundle,
        binding_authority=binding_authority,
        source_seal_authority=seal_authority,
        stage_record_authority=stage_store.stage_authority,
        store=stage_store,
    )
    source_adapter.seal_read_only(stage_request)
    stage_envelope = stage_store.values[stage_request.identity.effect_id]
    stage_record = stage_envelope.content
    profile = stage_request.identity.plan.profile
    plan, preparation = _prepared(profile)
    predecessor = StagePredecessorV2(
        profile.provider.provider_id, profile.provider.profile_ref,
        profile.scope.account_ref, profile.scope.namespace_ref,
        plan.project_ref, plan.run_id, plan.plan_fingerprint,
        plan.preparation_digest, profile.workload.workload_digest,
        stage_record.stage_effect_id, D[10], D[11],
    )
    payload = CanonicalProviderPayloadV1.build(
        profile.provider.provider_id, "submit-payload/v2",
        profile.workload.workload_digest,
    )
    command = build_submit_command(
        preparation, "submit-effect", payload,
        profile.executor_descriptor, predecessor,
    )
    identity = DockerEffectIdentityV1(
        command.digest, command.operation.effect.effect_id, "submit", plan
    )
    binding = DockerCommandBindingV1(identity, command.canonical_bytes)
    command_authority = CommandAuthority()
    catalog = CommandCatalog(command_authority.issue(binding))
    labels = labels_for(identity)
    access = source_registry.resolution.bundle_access
    verify_access = BundleMountVerifyAccessV1.build(
        access.destination_ref, access.verify_borrow, access.verify_root
    )
    source_mapping = DockerStorageMappingV1.build(
        mapping_ref="source-mapping", declared_ref=profile.roots.source_ref,
        purpose=DockerStoragePurposeV1.SOURCE_BUNDLE,
        wsl_root="/mnt/synaptic/source", root_authority_digest=access.root_authority_digest,
        destination_ref=access.destination_ref,
        access_digest=verify_access.access_digest,
        verify_access=verify_access,
    )
    artifact_mapping = DockerStorageMappingV1.build(
        mapping_ref="artifact-mapping", declared_ref=profile.roots.artifact_ref,
        purpose=DockerStoragePurposeV1.ARTIFACT_OUTPUT,
        wsl_root="/mnt/synaptic/artifacts", root_authority_digest=D[12],
        destination_ref="artifact-destination", access_digest=D[13],
    )
    mapping_authority = MappingAuthority()
    mappings = MappingRegistry(
        mapping_authority.issue(source_mapping),
        mapping_authority.issue(artifact_mapping),
    )
    verifier = MountVerifier()
    return {
        "labels": labels, "image": profile.image, "runtime": profile.runtime,
        "workload": profile.workload, "source_ref": profile.roots.source_ref,
        "artifact_ref": profile.roots.artifact_ref, "catalog": catalog,
        "command_authority": command_authority, "stage_store": stage_store,
        "declaration_authority": declaration_authority,
        "binding_authority": binding_authority,
        "seal_authority": seal_authority, "mappings": mappings,
        "mapping_authority": mapping_authority, "verifier": verifier,
        "stage_authority": stage_store.stage_authority,
        "stage_envelope": stage_envelope,
        "stage_record": stage_record, "command": command,
    }
