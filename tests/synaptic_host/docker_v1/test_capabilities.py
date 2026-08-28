import pytest

from synaptic_host.bundle_io_v1.model import BundleIOCodeV1, BundleIOErrorV1
from synaptic_host.docker_v1.authority import (
    DockerStorageMappingHmacAuthorityV1,
    DockerStoragePathMappingPairHmacAuthorityV1,
    DockerWSLRootMappingHmacAuthorityV1,
)
from synaptic_host.docker_v1.capabilities import (
    DockerImmutableBundleSourceRegistryV1,
    DockerSingleLaunchSourceDeclarationResolverV1,
    ImmutableDockerStoragePathMappingPairRegistryV1,
)
from synaptic_host.docker_v1.model import (
    AuthenticatedDockerStoragePathMappingPairV1,
    DockerHostSourceErrorV1,
    DockerMountCodeV1,
    DockerMountErrorV1,
    DockerStoragePathMappingPairV1,
    DockerWSLPathPurposeV1,
    DockerWSLRootMappingV1,
)
from tuner.execution.providers.docker_provider_v1.model import (
    DockerEffectIdentityV1,
    DockerSourceSealRequestV1,
)

from .test_authority import _authenticator, _mapping_contents, _source_pair


def _resolver_from_real_environment(real_concurrency_env, authority=None):
    (
        request, previous_registry, declaration_authority, _bundle,
        _binding_authority, _seal_authority, _store, _port, sources,
    ) = real_concurrency_env
    previous = previous_registry.resolution
    authority = declaration_authority if authority is None else authority
    declaration = previous.declaration.content
    source = sources.values[request.source_ref]
    resolver = DockerSingleLaunchSourceDeclarationResolverV1(
        profile=request.identity.plan.profile,
        source=source,
        source_digest=declaration.source_digest,
        purpose_ref=declaration.purpose_ref,
        destination_ref=declaration.destination_ref,
        members=declaration.members,
        bundle_access=previous.bundle_access,
        declaration_authority=authority,
    )
    return request, previous, source, resolver, authority


def _authenticated_pairs(tmp_path, source_env):
    authenticator = _authenticator(tmp_path)
    storage = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    wsl = DockerWSLRootMappingHmacAuthorityV1(
        authority_ref="docker-wsl-authority", authenticator=authenticator
    )
    pair_authority = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="docker-pair-authority", authenticator=authenticator,
        storage_mapping_authority=storage, wsl_mapping_authority=wsl,
    )
    source_content = _source_pair(source_env, storage, wsl)
    _, artifact = _mapping_contents(source_env)
    artifact_content = DockerStoragePathMappingPairV1.build(
        storage.issue(artifact),
        wsl.issue(DockerWSLRootMappingV1.build(
            "artifact-mapping", "Ubuntu-22.04",
            DockerWSLPathPurposeV1.ARTIFACT_WRITE,
            "/mnt/synaptic/artifacts",
        )),
    )
    return (
        pair_authority.issue(source_content),
        pair_authority.issue(artifact_content),
        pair_authority,
    )


def test_single_launch_resolver_is_request_bound_and_preserves_access_identity(
    real_concurrency_env,
):
    request, previous, _source, resolver, authority = (
        _resolver_from_real_environment(real_concurrency_env)
    )
    issue_calls = authority.issue_calls
    authenticate_calls = authority.authenticate_calls
    resolved = resolver.resolve(request)
    assert resolved.declaration.content == previous.declaration.content
    assert authority.issue_calls == issue_calls + 1
    assert authority.authenticate_calls == authenticate_calls + 1
    assert resolved.bundle_access is not previous.bundle_access
    assert (
        resolved.bundle_access.create_borrow
        is previous.bundle_access.create_borrow
    )
    assert resolved.bundle_access.create_root is previous.bundle_access.create_root
    assert (
        resolved.bundle_access.verify_borrow
        is previous.bundle_access.verify_borrow
    )
    assert resolved.bundle_access.verify_root is previous.bundle_access.verify_root
    repeated = resolver.resolve(request)
    assert repeated == resolved and repeated is not resolved

    alternate_identity = DockerEffectIdentityV1(
        request.identity.command_digest, "another-stage-effect", "stage",
        request.identity.plan,
    )
    alternate = resolver.resolve(DockerSourceSealRequestV1(
        alternate_identity, request.source_ref, request.source_digest
    ))
    assert alternate.declaration.content.effect_identity_digest == alternate_identity.digest
    assert alternate.declaration.content.declaration_digest != (
        resolved.declaration.content.declaration_digest
    )


def test_single_launch_resolver_rejects_request_or_authority_confusion(
    real_concurrency_env,
):
    request, _previous, _source, resolver, authority = (
        _resolver_from_real_environment(real_concurrency_env)
    )
    with pytest.raises(DockerHostSourceErrorV1):
        resolver.resolve(DockerSourceSealRequestV1(
            request.identity, request.source_ref, "f" * 64
        ))
    with pytest.raises(DockerHostSourceErrorV1):
        resolver.resolve(object())
    authority.key_ref = "changed-declaration-key"
    with pytest.raises(DockerHostSourceErrorV1):
        resolver.resolve(request)


def test_resolver_compares_callbacks_to_untouched_local_envelope(
    real_concurrency_env,
):
    request, _previous, _source, _resolver, base = (
        _resolver_from_real_environment(real_concurrency_env)
    )

    class MutatingIssueAuthority:
        authority_ref = base.authority_ref
        key_ref = base.key_ref

        def issue(self, content):
            returned = base.issue(content)
            object.__setattr__(content, "source_ref", "hostile-source")
            return returned

        def authenticate(self, value):
            return base.authenticate(value)

    _, _, _, issue_resolver, _ = _resolver_from_real_environment(
        real_concurrency_env, MutatingIssueAuthority()
    )
    with pytest.raises(DockerHostSourceErrorV1):
        issue_resolver.resolve(request)

    class MutatingAuthenticateAuthority:
        authority_ref = base.authority_ref
        key_ref = base.key_ref

        def issue(self, content):
            return base.issue(content)

        def authenticate(self, value):
            base.authenticate(value)
            object.__setattr__(value.content, "source_ref", "hostile-source")
            return value

    _, _, _, authenticate_resolver, _ = _resolver_from_real_environment(
        real_concurrency_env, MutatingAuthenticateAuthority()
    )
    with pytest.raises(DockerHostSourceErrorV1):
        authenticate_resolver.resolve(request)


def test_immutable_bundle_source_registry_preserves_exact_live_capabilities(
    real_concurrency_env,
):
    request, _registry, _declaration_authority, _bundle, _binding, _seal, (
        _store
    ), _port, sources = real_concurrency_env
    original = sources.values[request.source_ref]
    registry = DockerImmutableBundleSourceRegistryV1((original,))
    first = registry.resolve(request.source_ref)
    second = registry.resolve(request.source_ref)
    assert first == second == original
    assert first is not second and first is not original
    assert first.borrow is second.borrow is original.borrow
    assert first.directory is second.directory is original.directory
    object.__setattr__(first, "component", "hostile-component")
    assert registry.resolve(request.source_ref) == original
    with pytest.raises(BundleIOErrorV1) as caught:
        registry.resolve("unknown-source")
    assert caught.value.code is BundleIOCodeV1.SOURCE_INVALID
    with pytest.raises(BundleIOErrorV1):
        DockerImmutableBundleSourceRegistryV1((original, original))


def test_pair_registry_is_single_authenticated_source_for_every_projection(
    tmp_path, source_env,
):
    source_pair, artifact_pair, authority = _authenticated_pairs(
        tmp_path, source_env
    )

    class CountingAuthority:
        authority_ref = authority.authority_ref
        key_ref = authority.key_ref

        def __init__(self):
            self.calls = 0

        def authenticate(self, value):
            self.calls += 1
            return authority.authenticate(value)

    counting = CountingAuthority()
    registry = ImmutableDockerStoragePathMappingPairRegistryV1(
        source_pair=source_pair, artifact_pair=artifact_pair,
        authority=counting,
    )
    initial_calls = counting.calls
    source_outer = registry.resolve_source_pair("dataset-source")
    artifact_outer = registry.resolve_artifact_pair("artifact-root")
    source = registry.resolve_source("dataset-source")
    artifact = registry.resolve_artifact("artifact-root")
    source_wsl = registry.resolve(
        "source-mapping",
        source_outer.content.wsl_mapping.content.mapping_digest,
    )
    artifact_wsl = registry.resolve(
        "artifact-mapping",
        artifact_outer.content.wsl_mapping.content.mapping_digest,
    )
    assert counting.calls == initial_calls + 6
    assert source_outer == source_pair and source_outer is not source_pair
    assert artifact_outer == artifact_pair and artifact_outer is not artifact_pair
    assert source == source_pair.content.storage_mapping
    assert artifact == artifact_pair.content.storage_mapping
    assert source_wsl == source_pair.content.wsl_mapping
    assert artifact_wsl == artifact_pair.content.wsl_mapping
    original_access = source_pair.content.storage_mapping.content.verify_access
    retained_access = source.content.verify_access
    assert retained_access.verify_borrow is original_access.verify_borrow
    assert retained_access.verify_root is original_access.verify_root
    object.__setattr__(source_outer.content, "pair_digest", "f" * 64)
    assert registry.resolve_source_pair("dataset-source") == source_pair
    assert registry.resolve("unknown-mapping", "a" * 64) is None
    assert registry.resolve("source-mapping", "f" * 64) is None


def test_pair_registry_rejects_role_confusion_forgery_and_unknown_required_keys(
    tmp_path, source_env,
):
    source_pair, artifact_pair, authority = _authenticated_pairs(
        tmp_path, source_env
    )
    with pytest.raises(DockerMountErrorV1) as caught:
        ImmutableDockerStoragePathMappingPairRegistryV1(
            source_pair=artifact_pair, artifact_pair=source_pair,
            authority=authority,
        )
    assert caught.value.code is DockerMountCodeV1.MAPPING_CONFLICT

    forged = AuthenticatedDockerStoragePathMappingPairV1(
        source_pair.content, source_pair.authority_ref,
        source_pair.key_ref, "f" * 64,
    )
    with pytest.raises(DockerMountErrorV1) as caught:
        ImmutableDockerStoragePathMappingPairRegistryV1(
            source_pair=forged, artifact_pair=artifact_pair,
            authority=authority,
        )
    assert caught.value.code is DockerMountCodeV1.AUTHENTICATION_FAILED

    registry = ImmutableDockerStoragePathMappingPairRegistryV1(
        source_pair=source_pair, artifact_pair=artifact_pair,
        authority=authority,
    )
    with pytest.raises(DockerMountErrorV1) as caught:
        registry.resolve_source_pair("unknown-source")
    assert caught.value.code is DockerMountCodeV1.MAPPING_INDETERMINATE
    with pytest.raises(DockerMountErrorV1):
        registry.resolve_artifact("unknown-artifact")


def test_pair_registry_compares_callback_to_untouched_pair_baseline(
    tmp_path, source_env,
):
    source_pair, artifact_pair, base = _authenticated_pairs(
        tmp_path, source_env
    )

    class MutatingPairAuthority:
        authority_ref = base.authority_ref
        key_ref = base.key_ref

        def __init__(self, armed):
            self.armed = armed

        def authenticate(self, value):
            returned = base.authenticate(value)
            if self.armed:
                object.__setattr__(value.content, "pair_digest", "f" * 64)
                return value
            return returned

    with pytest.raises(DockerMountErrorV1) as caught:
        ImmutableDockerStoragePathMappingPairRegistryV1(
            source_pair=source_pair, artifact_pair=artifact_pair,
            authority=MutatingPairAuthority(True),
        )
    assert caught.value.code is DockerMountCodeV1.AUTHENTICATION_FAILED

    authority = MutatingPairAuthority(False)
    registry = ImmutableDockerStoragePathMappingPairRegistryV1(
        source_pair=source_pair, artifact_pair=artifact_pair,
        authority=authority,
    )
    authority.armed = True
    with pytest.raises(DockerMountErrorV1) as caught:
        registry.resolve_source_pair("dataset-source")
    assert caught.value.code is DockerMountCodeV1.AUTHENTICATION_FAILED
    authority.armed = False
    assert registry.resolve_source_pair("dataset-source") == source_pair
