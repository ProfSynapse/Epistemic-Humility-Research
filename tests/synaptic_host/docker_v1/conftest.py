from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from synaptic_tuner.api.v1.providers import ProviderCapabilities, ProviderDescriptor, ProviderRef
from tuner.execution.foundation_v2.canonical import canonical_bytes, domain_digest
from tuner.execution.foundation_v2.executors import AdapterDescriptorV1, ExecutorDescriptorV1
from tuner.execution.foundation_v2.references import ExecutionScopeV1
from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerSourceSealV1,
    DockerArtifactContractV1,
    DockerEffectIdentityV1,
    DockerImageV1,
    DockerProfileV1,
    DockerRootsV1,
    DockerRuntimeV1,
    DockerSourceSealContentV1,
    DockerSourceSealRequestV1,
    DockerWorkloadV1,
    PreparedDockerPlanV1,
)

from synaptic_host.bundle_io_v1.model import (
    AuthenticatedBundleBindingV1,
    BundleBindingV1,
    BundleLookupResultV1,
    BundleLookupStatusV1,
    BundleMemberCommandV1,
    BundleMemberEvidenceV1,
    bundle_companion_digest_v1,
    digest_v1,
)
from synaptic_host.bundle_io_v1.bundle import ImmutableSourceBundleV1
from synaptic_host.bundle_io_v1.ports import BundleBorrowAccessV1, BundleSourceV1
from synaptic_host.docker_v1.model import (
    AuthenticatedDockerSourceDeclarationV1,
    DockerSourceDeclarationV1,
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
        runtime=DockerRuntimeV1(2, 1_073_741_824, 3600),
        workload=DockerWorkloadV1(("python", "run.py"), (), D[0]),
        roots=DockerRootsV1("dataset-source", "artifact-root"),
        artifacts=DockerArtifactContractV1(("result",), 1_048_576, 1_048_576),
        resource_digest=D[1], quote_digest=D[2], secret_requirements_digest=D[3],
    )


@pytest.fixture(params=("opaque/local-cpu", "opaque/registry-cpu"))
def source_env(request):
    profile = _profile(request.param)
    plan = PreparedDockerPlanV1(
        profile, "project", "run", D[4], D[8], D[6]
    )
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


class Store:
    def __init__(self):
        self.values = {}
        self.get_calls = 0
        self.put_calls = 0
        self.fail_get = False
        self.fail_put_before = False
        self.lose_put_return = False

    def get_by_stage_effect_id(self, effect_id):
        self.get_calls += 1
        if self.fail_get:
            raise RuntimeError("secret store read")
        return self.values.get(effect_id)

    def put_if_absent(self, value):
        self.put_calls += 1
        if self.fail_put_before:
            raise RuntimeError("secret store write")
        retained = self.values.setdefault(value.stage_effect_id, value)
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
    plan = PreparedDockerPlanV1(
        profile, "project", "run", D[4], D[8], D[6]
    )
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
