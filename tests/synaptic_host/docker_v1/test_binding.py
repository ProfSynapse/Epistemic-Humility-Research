from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import pickle

import pytest

from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.binding import (
    DockerAuthenticatedPairPathBinderV1,
    DockerEnvironmentResolutionCodeV1,
    DockerEnvironmentResolutionErrorV1,
    DockerExplicitWorkloadEnvironmentResolverV1,
    DockerWorkloadEnvironmentPolicyV1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerControlContractErrorV1,
    DockerCreatePathBindingV1,
    DockerWorkloadEnvironmentBindingV1,
)
from synaptic_host.docker_v1.model import ResolvedDockerMountsV1
from tuner.execution.providers.docker_provider_v1.model import DockerWorkloadV1

from .test_capabilities import _authenticated_pairs


SHA = "a" * 64


class _PathAuthority:
    authority_ref = "path-authority"
    key_ref = "path-key"

    def __init__(self):
        self.issue_transform = lambda value: value
        self.authenticate_transform = lambda value: value
        self.issue_calls = 0
        self.authenticate_calls = 0

    def issue(self, value):
        self.issue_calls += 1
        value = self.issue_transform(value)
        return AuthenticatedDockerCreatePathBindingV1(
            value, self.authority_ref, self.key_ref, "b" * 64
        )

    def authenticate(self, value):
        self.authenticate_calls += 1
        return self.authenticate_transform(value)


class _EnvironmentAuthority:
    authority_ref = "environment-authority"
    key_ref = "environment-key"

    def __init__(self):
        self.issue_transform = lambda value: value
        self.authenticate_transform = lambda value: value
        self.issue_calls = 0
        self.authenticate_calls = 0

    def issue(self, value):
        self.issue_calls += 1
        value = self.issue_transform(value)
        return AuthenticatedDockerWorkloadEnvironmentBindingV1(
            value, self.authority_ref, self.key_ref, "c" * 64
        )

    def authenticate(self, value):
        self.authenticate_calls += 1
        return self.authenticate_transform(value)


def _resolved(source, artifact, *, source_path=None, artifact_path=None):
    source_root = source.content.wsl_mapping.content.posix_root
    artifact_root = artifact.content.wsl_mapping.content.posix_root
    values = {
        "artifact_mapping_digest": artifact.content.storage_mapping.proof_digest,
        "artifact_wsl_root": artifact_root if artifact_path is None else artifact_path,
        "bundle_binding_digest": "1" * 64,
        "command_binding_digest": "2" * 64,
        "labels_digest": "3" * 64,
        "mount_verification_digest": "4" * 64,
        "source_mapping_digest": source.content.storage_mapping.proof_digest,
        "source_read_only": True,
        "source_wsl_private_path": source_root + "/private-bundle" if source_path is None else source_path,
        "stage_record_digest": "5" * 64,
    }
    body = dict(values, schema_version="synaptic-host-resolved-docker-mounts/v1")
    return ResolvedDockerMountsV1(
        values["source_wsl_private_path"], values["artifact_wsl_root"],
        values["command_binding_digest"], values["labels_digest"],
        values["stage_record_digest"], values["source_mapping_digest"],
        values["artifact_mapping_digest"], values["bundle_binding_digest"],
        values["mount_verification_digest"], True, digest_v1(body),
    )


def _binder(tmp_path, source_env, pair_authority=None, path_authority=None):
    source, artifact, authority = _authenticated_pairs(tmp_path, source_env)
    pair_authority = authority if pair_authority is None else pair_authority
    path_authority = _PathAuthority() if path_authority is None else path_authority
    binder = DockerAuthenticatedPairPathBinderV1(
        source_pair=source, artifact_pair=artifact,
        pair_authority=pair_authority, binding_authority=path_authority,
    )
    return binder, source, artifact, authority, path_authority


def test_pair_binder_derives_requests_proofs_and_preserves_source_identity(
    tmp_path, source_env,
):
    binder, source, artifact, _authority, _path = _binder(tmp_path, source_env)
    resolved = _resolved(source, artifact)
    result = binder.bind(resolved, "dataset-source", "artifact-root")
    content = result.content
    assert content.source_mapping_pair_proof_digest == source.proof_digest
    assert content.artifact_mapping_pair_proof_digest == artifact.proof_digest
    assert content.source_storage_mapping_proof_digest == source.content.storage_mapping.proof_digest
    assert content.artifact_storage_mapping_proof_digest == artifact.content.storage_mapping.proof_digest
    assert content.source_request.expected_mapping_digest == source.content.wsl_mapping.content.mapping_digest
    assert content.artifact_request.expected_mapping_digest == artifact.content.wsl_mapping.content.mapping_digest
    assert content.source_request.expected_distro == content.artifact_request.expected_distro


def test_pair_binder_concurrent_calls_converge_on_exact_binding(
    tmp_path, source_env,
):
    binder, source, artifact, _authority, _path = _binder(tmp_path, source_env)
    resolved = _resolved(source, artifact)
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(
            lambda _index: binder.bind(
                resolved, "dataset-source", "artifact-root"
            ),
            range(32),
        ))
    assert all(value == results[0] for value in results)


@pytest.mark.parametrize("attack", ("roles", "source-ref", "artifact-ref", "containment", "artifact-path"))
def test_pair_binder_rejects_role_ref_and_component_confusion(
    tmp_path, source_env, attack,
):
    binder, source, artifact, authority, path = _binder(tmp_path, source_env)
    if attack == "roles":
        with pytest.raises(DockerControlContractErrorV1):
            DockerAuthenticatedPairPathBinderV1(
                source_pair=artifact, artifact_pair=source,
                pair_authority=authority, binding_authority=path,
            )
        return
    source_ref = "wrong-source" if attack == "source-ref" else "dataset-source"
    artifact_ref = "wrong-artifact" if attack == "artifact-ref" else "artifact-root"
    source_path = source.content.wsl_mapping.content.posix_root if attack == "containment" else None
    artifact_path = source.content.wsl_mapping.content.posix_root if attack == "artifact-path" else None
    with pytest.raises(DockerControlContractErrorV1):
        binder.bind(
            _resolved(source, artifact, source_path=source_path, artifact_path=artifact_path),
            source_ref, artifact_ref,
        )


def test_pair_binder_reauth_detects_callback_live_identity_and_pin_mutation(
    tmp_path, source_env,
):
    source, artifact, base = _authenticated_pairs(tmp_path, source_env)

    class MutatingAuthority:
        authority_ref = base.authority_ref
        key_ref = base.key_ref
        binder = None
        mutate = False

        def authenticate(self, value):
            returned = base.authenticate(value)
            if self.mutate:
                access = self.binder._source.content.storage_mapping.content.verify_access
                object.__setattr__(access, "verify_borrow", replace(access.verify_borrow))
            return returned

    authority = MutatingAuthority()
    binder = DockerAuthenticatedPairPathBinderV1(
        source_pair=source, artifact_pair=artifact,
        pair_authority=authority, binding_authority=_PathAuthority(),
    )
    authority.binder = binder
    authority.mutate = True
    with pytest.raises(DockerControlContractErrorV1):
        binder.bind(_resolved(source, artifact), "dataset-source", "artifact-root")

    clean, source, artifact, _base, _path = _binder(tmp_path, source_env)
    clean._pair_authority.key_ref = "changed-key"
    with pytest.raises(DockerControlContractErrorV1):
        clean.bind(_resolved(source, artifact), "dataset-source", "artifact-root")


@pytest.mark.parametrize(
    "collision", ("pair-digest", "declared-ref", "storage-ref", "wsl-ref")
)
def test_pair_binder_constructor_rejects_direct_colliding_envelopes(
    tmp_path, source_env, collision,
):
    source, artifact, authority = _authenticated_pairs(tmp_path, source_env)
    if collision == "pair-digest":
        object.__setattr__(
            artifact.content, "pair_digest", source.content.pair_digest
        )
    elif collision == "declared-ref":
        object.__setattr__(
            artifact.content.storage_mapping.content,
            "declared_ref",
            source.content.storage_mapping.content.declared_ref,
        )
    elif collision == "storage-ref":
        object.__setattr__(
            artifact.content.storage_mapping.content,
            "mapping_ref",
            source.content.storage_mapping.content.mapping_ref,
        )
    else:
        object.__setattr__(
            artifact.content.wsl_mapping.content,
            "mapping_ref",
            source.content.wsl_mapping.content.mapping_ref,
        )
    with pytest.raises(DockerControlContractErrorV1):
        DockerAuthenticatedPairPathBinderV1(
            source_pair=source, artifact_pair=artifact,
            pair_authority=authority, binding_authority=_PathAuthority(),
        )


def test_pair_binder_rejects_pre_call_equal_looking_live_identity_replacement(
    tmp_path, source_env,
):
    binder, source, artifact, _authority, _path = _binder(tmp_path, source_env)
    access = binder._source.content.storage_mapping.content.verify_access
    object.__setattr__(access, "verify_borrow", replace(access.verify_borrow))
    with pytest.raises(DockerControlContractErrorV1):
        binder.bind(_resolved(source, artifact), "dataset-source", "artifact-root")


@pytest.mark.parametrize("phase", ("issue", "authenticate"))
def test_pair_binder_rejects_output_callback_mutation(tmp_path, source_env, phase):
    path = _PathAuthority()
    binder, source, artifact, _base, _ = _binder(
        tmp_path, source_env, path_authority=path
    )
    if phase == "issue":
        path.issue_transform = lambda value: replace(value, labels_digest="f" * 64)
    else:
        path.authenticate_transform = lambda value: replace(value, tag="f" * 64)
    with pytest.raises(DockerControlContractErrorV1):
        binder.bind(_resolved(source, artifact), "dataset-source", "artifact-root")


@pytest.mark.parametrize("phase", ("issue", "authenticate"))
def test_pair_binder_checks_source_identity_around_each_output_callback(
    tmp_path, source_env, phase,
):
    path = _PathAuthority()
    binder, source, artifact, _base, _ = _binder(
        tmp_path, source_env, path_authority=path
    )
    access = binder._source.content.storage_mapping.content.verify_access
    original = access.verify_borrow

    def swap(value):
        object.__setattr__(access, "verify_borrow", replace(original))
        return value

    if phase == "issue":
        path.issue_transform = swap

        def restore(value):
            object.__setattr__(access, "verify_borrow", original)
            return value

        path.authenticate_transform = restore
    else:
        path.authenticate_transform = swap
    with pytest.raises(DockerControlContractErrorV1):
        binder.bind(_resolved(source, artifact), "dataset-source", "artifact-root")
    if phase == "issue":
        assert path.authenticate_calls == 0


def _workload(*keys):
    return DockerWorkloadV1(("run",), tuple(sorted(keys)), SHA)


def _policy():
    return DockerWorkloadEnvironmentPolicyV1.build(
        allowed_keys=("BASE", "DENIED", "EXTRA", "OVERRIDE", "SECRET"),
        denied_keys=("DENIED",),
        secret_keys=("SECRET",),
        base_values=(("BASE", "base-value"), ("EXTRA", "not-requested")),
    )


def test_environment_resolver_is_explicit_excludes_unrequested_and_reuses_exact_binding():
    authority = _EnvironmentAuthority()
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=_policy(),
        overrides=(("EXTRA", "extra-override"), ("OVERRIDE", "override-value")),
        authority=authority,
    )
    assert "override-value" not in repr(resolver)
    with pytest.raises(DockerEnvironmentResolutionErrorV1):
        pickle.dumps(resolver)
    workload = _workload("BASE", "OVERRIDE")
    private = resolver.resolve(workload)
    assert private.materialize_for_cli(authority) == (
        ("BASE", "base-value"),
        ("OVERRIDE", "override-value"),
    )
    assert "override-value" not in repr(private)
    existing = private.authenticated_binding_snapshot(authority)
    replay = resolver.resolve(workload, existing)
    assert replay.materialize_for_cli(authority) == private.materialize_for_cli(authority)
    with pytest.raises(DockerEnvironmentResolutionErrorV1):
        resolver.resolve(_workload("BASE"), existing)


def test_environment_failure_precedence_is_global_and_deterministic():
    authority = _EnvironmentAuthority()
    policy = DockerWorkloadEnvironmentPolicyV1.build(
        allowed_keys=("A_MISSING", "B_SECRET", "Z_DENIED"),
        denied_keys=("Z_DENIED",), secret_keys=("B_SECRET",),
    )
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=policy, authority=authority
    )
    cases = (
        ((_workload("A_MISSING", "B_SECRET", "Y_UNALLOWED", "Z_DENIED")), DockerEnvironmentResolutionCodeV1.DENIED),
        ((_workload("A_MISSING", "B_SECRET", "Y_UNALLOWED")), DockerEnvironmentResolutionCodeV1.UNALLOWED),
        ((_workload("A_MISSING", "B_SECRET")), DockerEnvironmentResolutionCodeV1.SECRET_TRANSPORT_UNAVAILABLE),
        ((_workload("A_MISSING")), DockerEnvironmentResolutionCodeV1.MISSING),
    )
    for workload, code in cases:
        with pytest.raises(DockerEnvironmentResolutionErrorV1) as caught:
            resolver.resolve(workload)
        assert caught.value.code is code


@pytest.mark.parametrize(
    "factory",
    (
        lambda: DockerWorkloadEnvironmentPolicyV1.build(allowed_keys=("lower",)),
        lambda: DockerWorkloadEnvironmentPolicyV1.build(allowed_keys=("É",)),
        lambda: DockerWorkloadEnvironmentPolicyV1.build(allowed_keys=("A\n",)),
        lambda: DockerWorkloadEnvironmentPolicyV1.build(allowed_keys=("A" * 129,)),
        lambda: DockerWorkloadEnvironmentPolicyV1.build(
            allowed_keys=("SECRET",), secret_keys=("SECRET",),
            base_values=(("SECRET", "forbidden"),),
        ),
    ),
)
def test_environment_ascii_case_nfc_control_and_byte_bounds(factory):
    with pytest.raises((DockerControlContractErrorV1, DockerEnvironmentResolutionErrorV1)):
        factory()


def test_requested_secret_fails_before_issue_digest_or_private_pairs():
    authority = _EnvironmentAuthority()
    authority.issue_transform = lambda _value: pytest.fail(
        "secret reached environment binding issue"
    )
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=DockerWorkloadEnvironmentPolicyV1.build(
            allowed_keys=("SECRET",), secret_keys=("SECRET",)
        ),
        authority=authority,
    )
    with pytest.raises(DockerEnvironmentResolutionErrorV1) as caught:
        resolver.resolve(_workload("SECRET"))
    assert caught.value.code is DockerEnvironmentResolutionCodeV1.SECRET_TRANSPORT_UNAVAILABLE
    assert "raw-secret" not in repr(caught.value)


def test_environment_override_wins_same_key_base_and_is_concurrent_deterministic():
    authority = _EnvironmentAuthority()
    policy = DockerWorkloadEnvironmentPolicyV1.build(
        allowed_keys=("SAME",), base_values=(("SAME", "base"),)
    )
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=policy, overrides=(("SAME", "override"),), authority=authority
    )
    workload = _workload("SAME")

    def resolve(_index):
        private = resolver.resolve(workload)
        binding = private.authenticated_binding_snapshot(authority)
        return private.materialize_for_cli(authority), binding.content.binding_digest

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(resolve, range(32)))
    assert all(value == results[0] for value in results)
    assert results[0][0] == (("SAME", "override"),)


def test_environment_maximum_cardinality_accepts_exact_limit_and_rejects_overflow():
    keys = tuple(f"K{index:02d}" for index in range(64))
    pairs = tuple((key, f"value-{index}") for index, key in enumerate(keys))
    authority = _EnvironmentAuthority()
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=DockerWorkloadEnvironmentPolicyV1.build(allowed_keys=keys),
        overrides=pairs,
        authority=authority,
    )
    private = resolver.resolve(_workload(*keys))
    assert len(private.materialize_for_cli(authority)) == 64
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentPolicyV1.build(
            allowed_keys=keys + ("K64",)
        )


def test_environment_override_rejects_policy_secret_key_at_construction():
    policy = DockerWorkloadEnvironmentPolicyV1.build(
        allowed_keys=("SECRET",), secret_keys=("SECRET",)
    )
    with pytest.raises(DockerEnvironmentResolutionErrorV1):
        DockerExplicitWorkloadEnvironmentResolverV1(
            policy=policy, overrides=(("SECRET", "forbidden"),),
            authority=_EnvironmentAuthority(),
        )


@pytest.mark.parametrize("target", ("policy", "overrides"))
def test_environment_resolver_rejects_issue_callback_configuration_swap_before_authenticate(
    target,
):
    authority = _EnvironmentAuthority()
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=_policy(), overrides=(("OVERRIDE", "override-value"),),
        authority=authority,
    )
    original = getattr(resolver, f"_{target}")

    def swap(value):
        if target == "policy":
            replacement = DockerWorkloadEnvironmentPolicyV1(
                tuple(original.allowed_keys), tuple(original.denied_keys),
                tuple(original.secret_keys), tuple(original.base_values),
                original.policy_digest,
            )
        else:
            replacement = tuple(list(original))
        object.__setattr__(resolver, f"_{target}", replacement)
        return value

    def restore(value):
        object.__setattr__(resolver, f"_{target}", original)
        return value

    authority.issue_transform = swap
    authority.authenticate_transform = restore
    with pytest.raises(DockerEnvironmentResolutionErrorV1) as caught:
        resolver.resolve(_workload("OVERRIDE"))
    assert caught.value.code is DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED
    assert authority.authenticate_calls == 0


@pytest.mark.parametrize("target", ("policy", "overrides"))
def test_environment_resolver_rejects_authenticate_callback_configuration_swap(
    target,
):
    authority = _EnvironmentAuthority()
    resolver = DockerExplicitWorkloadEnvironmentResolverV1(
        policy=_policy(), overrides=(("OVERRIDE", "override-value"),),
        authority=authority,
    )
    original = getattr(resolver, f"_{target}")

    def swap(value):
        if target == "policy":
            replacement = DockerWorkloadEnvironmentPolicyV1(
                tuple(original.allowed_keys), tuple(original.denied_keys),
                tuple(original.secret_keys), tuple(original.base_values),
                original.policy_digest,
            )
        else:
            replacement = tuple(list(original))
        object.__setattr__(resolver, f"_{target}", replacement)
        return value

    authority.authenticate_transform = swap
    with pytest.raises(DockerEnvironmentResolutionErrorV1) as caught:
        resolver.resolve(_workload("OVERRIDE"))
    assert caught.value.code is DockerEnvironmentResolutionCodeV1.AUTHENTICATION_FAILED
