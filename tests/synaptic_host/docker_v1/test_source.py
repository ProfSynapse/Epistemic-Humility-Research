from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest

from tuner.execution.providers.docker_provider_v1.model import (
    DockerLookupDispositionV1,
    DockerSourceSealLookupRequestV1,
    DockerSourceSealRequestV1,
)

from synaptic_host.bundle_io_v1.model import (
    BundleBindingV1,
    BundleLookupStatusV1,
    bundle_companion_digest_v1,
    digest_v1,
)
from synaptic_host.docker_v1.model import (
    DockerHostSourceCodeV1,
    DockerHostSourceErrorV1,
    DockerSourceDeclarationV1,
    DockerStageBundleBindingV1,
)
from synaptic_host.docker_v1.source import DockerBundleSourceSealAdapterV1

from .conftest import D


def _adapter(env):
    _, registry, declaration_authority, bundle, binding_authority, seal_authority, store = env
    return DockerBundleSourceSealAdapterV1(
        declarations=registry,
        declaration_authority=declaration_authority,
        bundle=bundle,
        binding_authority=binding_authority,
        source_seal_authority=seal_authority,
        stage_record_authority=store.stage_authority,
        store=store,
    )


def _rebuild_binding(
    binding, *, destination_ref=None, root_authority_digest=None,
    member_changes=None,
):
    destination_ref = destination_ref or binding.destination_ref
    root_authority_digest = root_authority_digest or binding.root_authority_digest
    member = binding.members[0]
    changes = dict(member_changes or {})
    if "size" in changes:
        changes["identity"] = replace(member.identity, size=changes["size"])
    member = replace(member, **changes)
    members = (member,)
    companion_name = ".synaptic-commit-companion-" + bundle_companion_digest_v1(
        binding.command_digest, destination_ref, root_authority_digest
    )
    inventory_digest = digest_v1([member.canonical()])
    body = {
        "command_digest": binding.command_digest,
        "companion_name": companion_name,
        "destination_ref": destination_ref,
        "inventory_digest": inventory_digest,
        "manifest_digest": binding.manifest_digest,
        "manifest_identity": binding.manifest_identity.canonical(),
        "marker_identity": binding.marker_identity.canonical(),
        "marker_name": binding.marker_name,
        "members": [member.canonical()],
        "private_name": binding.private_name,
        "root_authority_digest": root_authority_digest,
        "schema_version": "synaptic-host-bundle-binding/v1",
    }
    return BundleBindingV1(
        binding.command_digest, destination_ref, root_authority_digest,
        binding.private_name, binding.marker_name, companion_name,
        binding.manifest_digest, inventory_digest, members,
        binding.manifest_identity, binding.marker_identity, digest_v1(body),
    )


def test_stage_seal_retains_exact_authenticated_binding(adapter_env):
    request, registry, _, bundle, _, seal_authority, store = adapter_env
    seal = _adapter(adapter_env).seal_read_only(request)
    retained = store.values[request.identity.effect_id].content
    assert registry.calls == 1
    assert len(bundle.calls) == 1
    assert retained.source_seal == seal
    assert seal.content.request_digest == request.digest
    assert seal.content.effect_identity_digest == request.identity.digest
    assert seal.content.source_ref == request.source_ref
    assert seal.content.source_digest == request.source_digest
    assert seal.content.evidence_digest == retained.authenticated_binding_digest
    assert seal.content.stage_ref == "bundle-" + retained.authenticated_binding_digest
    assert seal_authority.authenticate(seal) == seal


def test_identical_replay_and_reconstructed_adapter_are_store_only(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    first = _adapter(adapter_env)
    seal = first.seal_read_only(request)
    initial = (registry.calls, len(bundle.calls), store.put_calls)
    assert first.seal_read_only(request) == seal
    assert _adapter(adapter_env).seal_read_only(request) == seal
    assert (registry.calls, len(bundle.calls), store.put_calls) == initial


def test_lookup_is_store_only_and_never_reseals(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    adapter = _adapter(adapter_env)
    absent = adapter.lookup(DockerSourceSealLookupRequestV1(request, 1))
    assert absent.disposition is DockerLookupDispositionV1.INDETERMINATE
    assert registry.calls == 0 and bundle.calls == []
    seal = adapter.seal_read_only(request)
    before = (registry.calls, len(bundle.calls), store.put_calls)
    found = _adapter(adapter_env).lookup(DockerSourceSealLookupRequestV1(request, 2))
    assert found.disposition is DockerLookupDispositionV1.FOUND
    assert found.seal == seal
    assert (registry.calls, len(bundle.calls), store.put_calls) == before


def test_lost_insert_return_recovers_only_from_retained_record(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    store.lose_put_return = True
    seal = _adapter(adapter_env).seal_read_only(request)
    assert seal == store.values[request.identity.effect_id].content.source_seal
    assert registry.calls == 1 and len(bundle.calls) == 1 and store.put_calls == 1


def test_store_read_uncertainty_before_effect_is_closed_and_zero_effect(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    store.fail_get = True
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.STORE_INDETERMINATE
    assert str(caught.value) == caught.value.code.value
    assert registry.calls == 0 and bundle.calls == [] and store.put_calls == 0


@pytest.mark.parametrize(
    "request_change",
    (
        {"source_ref": "other-source"},
        {"source_digest": "a" * 64},
    ),
)
def test_request_must_match_prepared_source_before_store_read(
    adapter_env, request_change
):
    request, registry, declaration_authority, bundle, binding_authority, seal_authority, store = adapter_env
    admitted = DockerSourceSealRequestV1(
        request.identity,
        request_change.get("source_ref", request.source_ref),
        request_change.get("source_digest", request.source_digest),
    )
    authority_before = (
        declaration_authority.authenticate_calls,
        binding_authority.issue_calls, binding_authority.authenticate_calls,
        seal_authority.issue_calls, seal_authority.authenticate_calls,
    )
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(admitted)
    assert caught.value.code is DockerHostSourceCodeV1.REQUEST_INVALID
    assert store.get_calls == 0 and store.put_calls == 0
    assert registry.calls == 0 and bundle.calls == []
    assert (
        declaration_authority.authenticate_calls,
        binding_authority.issue_calls, binding_authority.authenticate_calls,
        seal_authority.issue_calls, seal_authority.authenticate_calls,
    ) == authority_before


def test_lost_store_write_without_durable_record_is_indeterminate(adapter_env):
    request, _, _, bundle, _, _, store = adapter_env
    store.fail_put_before = True
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.STORE_INDETERMINATE
    assert len(bundle.calls) == 1 and store.put_calls == 1


def test_conflicting_retained_stage_rejects_before_declaration_or_bundle(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    _adapter(adapter_env).seal_read_only(request)
    before = (registry.calls, len(bundle.calls), store.put_calls)
    conflicting = DockerSourceSealRequestV1(
        replace(request.identity, command_digest="a" * 64),
        request.source_ref, request.source_digest,
    )
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(conflicting)
    assert caught.value.code is DockerHostSourceCodeV1.STORE_CONFLICT
    assert (registry.calls, len(bundle.calls), store.put_calls) == before


@pytest.mark.parametrize(
    ("status", "code"),
    (
        (BundleLookupStatusV1.CONFLICT, DockerHostSourceCodeV1.BUNDLE_CONFLICT),
        (BundleLookupStatusV1.INDETERMINATE, DockerHostSourceCodeV1.BUNDLE_INDETERMINATE),
        (BundleLookupStatusV1.DEFINITELY_ABSENT, DockerHostSourceCodeV1.BUNDLE_INDETERMINATE),
    ),
)
def test_only_durable_found_may_issue_stage_evidence(adapter_env, status, code):
    request, _, _, bundle, _, _, store = adapter_env
    bundle.status = status
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is code
    assert store.put_calls == 0 and store.values == {}


def test_bundle_exception_is_closed_without_raw_text(adapter_env):
    request, _, _, bundle, _, _, store = adapter_env
    bundle.raise_error = True
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.BUNDLE_INDETERMINATE
    assert "secret" not in str(caught.value)
    assert store.put_calls == 0


@pytest.mark.parametrize(
    "substitution",
    (
        {"destination_ref": "other-destination"},
        {"root_authority_digest": "a" * 64},
        {"member_changes": {"logical_name": "dataset/other.json"}},
        {"member_changes": {"physical_name": "member-9999"}},
        {"member_changes": {"size": 6}},
        {"member_changes": {"sha256": "a" * 64}},
    ),
)
def test_bundle_result_substitution_is_rejected_before_evidence_issue(
    adapter_env, substitution
):
    request, _, _, bundle, binding_authority, seal_authority, store = adapter_env
    bundle.transform = lambda binding: _rebuild_binding(binding, **substitution)
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.BUNDLE_CONFLICT
    assert binding_authority.issue_calls == 0
    assert seal_authority.issue_calls == 0
    assert store.put_calls == 0 and store.values == {}


def test_authenticated_declaration_mismatch_is_zero_bundle_effect(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    declaration = registry.resolution.declaration
    object.__setattr__(declaration.content, "source_digest", "a" * 64)
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.DECLARATION_CONFLICT
    assert bundle.calls == [] and store.put_calls == 0


def test_declaration_authentication_failure_is_zero_bundle_effect(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    envelope = registry.resolution.declaration
    registry.resolution = replace(
        registry.resolution,
        declaration=replace(envelope, tag="f" * 64),
    )
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.AUTHENTICATION_FAILED
    assert bundle.calls == [] and store.put_calls == 0


def test_forged_request_mutation_is_rejected_before_store(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    object.__setattr__(request.identity, "effect_kind", "submit")
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.REQUEST_INVALID
    assert store.get_calls == 0 and registry.calls == 0 and bundle.calls == []


def test_alternate_valid_binding_signer_is_rejected(adapter_env):
    request, _, _, _, authority, _, _ = adapter_env
    adapter = _adapter(adapter_env)
    authority.authority_ref = "alternate-binding-authority"
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        adapter.seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.AUTHENTICATION_FAILED


def test_replay_reauthenticates_retained_declaration_envelope(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    adapter = _adapter(adapter_env)
    adapter.seal_read_only(request)
    original = store.values[request.identity.effect_id].content
    forged_declaration = replace(
        original.authenticated_declaration, tag="f" * 64
    )
    rebuilt = DockerStageBundleBindingV1.build(
        effect_identity=original.effect_identity,
        source_seal_request_digest=original.source_seal_request_digest,
        source_ref=original.source_ref,
        source_digest=original.source_digest,
        authenticated_declaration=forged_declaration,
        bundle_command_digest=original.bundle_command_digest,
        authenticated_binding=original.authenticated_binding,
        source_seal=original.source_seal,
    )
    store.values[request.identity.effect_id] = store.stage_authority.issue(rebuilt)
    before = (registry.calls, len(bundle.calls), store.put_calls)
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.AUTHENTICATION_FAILED
    assert (registry.calls, len(bundle.calls), store.put_calls) == before
    observed = _adapter(adapter_env).lookup(
        DockerSourceSealLookupRequestV1(request, 2)
    )
    assert observed.disposition is DockerLookupDispositionV1.INDETERMINATE


def test_replay_authenticates_outer_stage_record_before_nested_evidence(
    adapter_env
):
    request, registry, _, bundle, _, _, store = adapter_env
    _adapter(adapter_env).seal_read_only(request)
    envelope = store.values[request.identity.effect_id]
    store.values[request.identity.effect_id] = replace(envelope, tag="f" * 64)
    before = (registry.calls, len(bundle.calls), store.put_calls)
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.AUTHENTICATION_FAILED
    assert (registry.calls, len(bundle.calls), store.put_calls) == before


def test_validly_signed_rebuilt_declaration_cannot_relabel_retained_record(
    adapter_env
):
    request, registry, declaration_authority, bundle, _, _, store = adapter_env
    _adapter(adapter_env).seal_read_only(request)
    original = store.values[request.identity.effect_id].content
    content = original.authenticated_declaration.content
    relabeled = DockerSourceDeclarationV1.build(
        source_ref=content.source_ref,
        source_digest=content.source_digest,
        effect_identity_digest=content.effect_identity_digest,
        prepared_plan_digest=content.prepared_plan_digest,
        profile_ref=content.profile_ref,
        purpose_ref="relabeled-purpose",
        destination_ref=content.destination_ref,
        root_authority_digest=content.root_authority_digest,
        bundle_access_digest=content.bundle_access_digest,
        members=content.members,
    )
    rebuilt = DockerStageBundleBindingV1.build(
        effect_identity=original.effect_identity,
        source_seal_request_digest=original.source_seal_request_digest,
        source_ref=original.source_ref,
        source_digest=original.source_digest,
        authenticated_declaration=declaration_authority.issue(relabeled),
        bundle_command_digest=original.bundle_command_digest,
        authenticated_binding=original.authenticated_binding,
        source_seal=original.source_seal,
    )
    store.values[request.identity.effect_id] = store.stage_authority.issue(rebuilt)
    before = (registry.calls, len(bundle.calls), store.put_calls)
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        _adapter(adapter_env).seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.STORE_CONFLICT
    assert (registry.calls, len(bundle.calls), store.put_calls) == before


def test_concurrent_replay_has_one_bundle_effect_and_one_insert(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    adapter = _adapter(adapter_env)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: adapter.seal_read_only(request), range(16)))
    assert all(value == results[0] for value in results)
    assert registry.calls == 1 and len(bundle.calls) == 1 and store.put_calls == 1
    assert adapter._stage_guards == {}


def test_two_adapters_converge_through_one_immutable_bundle_commit(
    real_concurrency_env
):
    (
        request, registry, declaration_authority, real_bundle,
        binding_authority, seal_authority, store, port, sources,
    ) = real_concurrency_env
    barrier = Barrier(2)

    class ConcurrentBundle:
        def __init__(self):
            self.calls = 0

        def seal(self, command, access):
            self.calls += 1
            barrier.wait(timeout=2)
            return real_bundle.seal(command, access)

    bundle = ConcurrentBundle()
    env = (
        request, registry, declaration_authority, bundle,
        binding_authority, seal_authority, store,
    )
    first, second = _adapter(env), _adapter(env)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (
            pool.submit(first.seal_read_only, request),
            pool.submit(second.seal_read_only, request),
        )
        results = tuple(future.result(timeout=5) for future in futures)
    assert results[0] == results[1]
    assert bundle.calls == 2
    assert port.calls.get("link_at", 0) == 1
    assert sources.calls.count("dataset-source") == 1
    assert store.put_calls == 2
    assert len(store.values) == 1
    assert real_bundle._seal_guards == {}
    retained = store.values[request.identity.effect_id].content
    assert retained.source_seal == results[0]
    assert retained.authenticated_declaration == registry.resolution.declaration
    assert retained.authenticated_binding.content.destination_ref == (
        registry.resolution.declaration.content.destination_ref
    )


class _AcquireFailure:
    def acquire(self):
        raise RuntimeError("secret acquire")

    def release(self):
        raise AssertionError("not acquired")


def test_guard_acquisition_failure_does_not_leak_refcount(adapter_env):
    request, _, _, _, _, _, _ = adapter_env
    adapter = _adapter(adapter_env)
    entry = [_AcquireFailure(), 0]
    adapter._stage_guards[request.identity.effect_id] = entry
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        adapter.seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.STORE_INDETERMINATE
    assert adapter._stage_guards == {}
    assert _adapter(adapter_env).seal_read_only(request).content.source_digest == D[8]


class _ReleaseFailure:
    def __init__(self):
        self.held = False

    def acquire(self):
        self.held = True
        return True

    def release(self):
        self.held = False
        raise RuntimeError("secret release")


def test_guard_release_failure_does_not_hide_durable_replay(adapter_env):
    request, registry, _, bundle, _, _, store = adapter_env
    adapter = _adapter(adapter_env)
    lock = _ReleaseFailure()
    adapter._stage_guards[request.identity.effect_id] = [lock, 0]
    with pytest.raises(DockerHostSourceErrorV1) as caught:
        adapter.seal_read_only(request)
    assert caught.value.code is DockerHostSourceCodeV1.STORE_INDETERMINATE
    assert lock.held is False and adapter._stage_guards == {}
    assert request.identity.effect_id in store.values
    before = (registry.calls, len(bundle.calls), store.put_calls)
    assert _adapter(adapter_env).seal_read_only(request) == store.values[
        request.identity.effect_id
    ].content.source_seal
    assert (registry.calls, len(bundle.calls), store.put_calls) == before
