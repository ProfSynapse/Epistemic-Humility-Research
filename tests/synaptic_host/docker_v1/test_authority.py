from dataclasses import replace
from types import SimpleNamespace

import pytest

from synaptic_host.docker_v1 import authority as authority_module
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
    DockerStorageMappingHmacAuthorityV1,
    DockerStoragePathMappingPairHmacAuthorityV1,
    DockerStageBundleRecordHmacAuthorityV1,
    DockerWSLRootMappingHmacAuthorityV1,
    DockerWorkloadEnvironmentBindingHmacAuthorityV1,
)
from synaptic_host.docker_v1.control_contract import (
    DockerControlIntentV1,
    DockerControlOperationV1,
    DockerCreatePathBindingV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
    DockerWorkloadEnvironmentBindingV1,
    docker_operation_id_v1,
)
from synaptic_host.docker_v1.model import (
    AuthenticatedDockerStorageMappingV1,
    AuthenticatedDockerStoragePathMappingPairV1,
    DockerMountCodeV1,
    DockerMountErrorV1,
    DockerStorageMappingV1,
    DockerStoragePathMappingPairV1,
    DockerStoragePurposeV1,
    DockerWSLPathRequestV1,
    DockerWSLPathPurposeV1,
    DockerWSLRootMappingV1,
)
from synaptic_host.security import FileHmacAuthenticator
from tuner.execution.providers.docker_provider_v1.model import (
    DockerAbsenceContentV1,
    DockerLookupPurposeV1,
    DockerSourceSealContentV1,
)

from .test_control import _one_id_fixture


SHA = "a" * 64
_MISSING = object()


def _authenticator(tmp_path):
    value = FileHmacAuthenticator(
        tmp_path / "docker-authority.key", key_ref="docker-host-key"
    )
    value.key_path.parent.mkdir(parents=True, exist_ok=True)
    value.key_path.write_bytes(bytes(range(32)))
    return value


def _mapping_contents(source_env):
    _, _, access = source_env
    verify = BundleMountVerifyAccessV1.build(
        access.destination_ref, access.verify_borrow, access.verify_root
    )
    source = DockerStorageMappingV1.build(
        mapping_ref="source-mapping", declared_ref="dataset-source",
        purpose=DockerStoragePurposeV1.SOURCE_BUNDLE,
        wsl_root="/mnt/synaptic/source",
        root_authority_digest=access.root_authority_digest,
        destination_ref=access.destination_ref,
        access_digest=verify.access_digest, verify_access=verify,
    )
    artifact = DockerStorageMappingV1.build(
        mapping_ref="artifact-mapping", declared_ref="artifact-root",
        purpose=DockerStoragePurposeV1.ARTIFACT_OUTPUT,
        wsl_root="/mnt/synaptic/artifacts",
        root_authority_digest="b" * 64,
        destination_ref="artifact-destination", access_digest="c" * 64,
    )
    return source, artifact


def _pair_authorities(tmp_path):
    authenticator = _authenticator(tmp_path)
    storage = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    wsl = DockerWSLRootMappingHmacAuthorityV1(
        authority_ref="docker-wsl-authority", authenticator=authenticator
    )
    pair = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="docker-pair-authority", authenticator=authenticator,
        storage_mapping_authority=storage, wsl_mapping_authority=wsl,
    )
    return authenticator, storage, wsl, pair


def _source_pair(source_env, storage, wsl):
    source, _ = _mapping_contents(source_env)
    storage_envelope = storage.issue(source)
    wsl_envelope = wsl.issue(DockerWSLRootMappingV1.build(
        "source-mapping", "Ubuntu-22.04",
        DockerWSLPathPurposeV1.SOURCE_READ, "/mnt/synaptic/source",
    ))
    return DockerStoragePathMappingPairV1.build(
        storage_envelope, wsl_envelope
    )


def _substitute_reconstruction_globals():
    def hostile(*arguments, **keywords):
        raise RuntimeError("hostile reconstruction global")

    replacements = {
        "_snapshot": hostile,
        "_content_digest": hostile,
        "DockerLabelsV1": object,
        "DockerCommandBindingV1": object,
        "AuthenticatedDockerCommandBindingV1": object,
        "DockerEffectIdentityV1": object,
        "PreparedDockerPlanV1": object,
        "DockerStorageMappingV1": object,
        "AuthenticatedDockerStorageMappingV1": object,
        "DockerWSLRootMappingV1": object,
        "AuthenticatedDockerWSLRootMappingV1": object,
        "DockerStoragePathMappingPairV1": object,
        "AuthenticatedDockerStoragePathMappingPairV1": object,
        "AuthenticatedDockerSourceSealV1": object,
        "AuthenticatedDockerAbsenceV1": object,
        "_storage_mapping_snapshot_v1": hostile,
        "_wsl_mapping_snapshot_v1": hostile,
        "validated_profile_snapshot": hostile,
        "Enum": object,
        "fields": hostile,
        "is_dataclass": hostile,
        "_closed_failure": lambda: RuntimeError("hostile failure factory"),
    }
    originals = {
        name: getattr(authority_module, name, _MISSING)
        for name in replacements
    }
    for name, replacement in replacements.items():
        setattr(authority_module, name, replacement)
    return originals


def _restore_reconstruction_globals(originals):
    for name, original in originals.items():
        if original is _MISSING:
            delattr(authority_module, name)
        else:
            setattr(authority_module, name, original)


def _substitute_constructor_globals():
    def hostile_validator(*arguments, **keywords):
        return arguments[0] if arguments else None

    replacements = {
        "checked_ref_v1": hostile_validator,
        "BundleIOCodeV1": SimpleNamespace(AUTHENTICATION_FAILED=object()),
        "_closed_failure": lambda: RuntimeError(
            "hostile constructor failure factory"
        ),
    }
    originals = {
        name: getattr(authority_module, name, _MISSING)
        for name in replacements
    }
    for name, replacement in replacements.items():
        setattr(authority_module, name, replacement)
    return originals


def _assert_closed_constructor_failure(operation):
    with pytest.raises(
        ValueError, match="^Docker authority operation failed$"
    ) as caught:
        operation()
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    assert "hostile" not in str(caught.value)


def test_pair_is_structural_and_preserves_exact_live_verification_identity(
    tmp_path, source_env,
):
    _, storage, wsl, _ = _pair_authorities(tmp_path)
    value = _source_pair(source_env, storage, wsl)
    original = value.storage_mapping.content.verify_access
    assert value.storage_mapping.content.verify_access.verify_borrow is original.verify_borrow
    assert value.storage_mapping.content.verify_access.verify_root is original.verify_root
    assert value.pair_digest == DockerStoragePathMappingPairV1.build(
        value.storage_mapping, value.wsl_mapping
    ).pair_digest


def test_pair_accepts_exact_artifact_adjacency(tmp_path, source_env):
    _, storage, wsl, pair_authority = _pair_authorities(tmp_path)
    _, artifact = _mapping_contents(source_env)
    value = DockerStoragePathMappingPairV1.build(
        storage.issue(artifact),
        wsl.issue(DockerWSLRootMappingV1.build(
            "artifact-mapping", "Ubuntu-22.04",
            DockerWSLPathPurposeV1.ARTIFACT_WRITE,
            "/mnt/synaptic/artifacts",
        )),
    )
    authenticated = pair_authority.issue(value)
    assert pair_authority.authenticate(authenticated) == authenticated
    assert authenticated.content.storage_mapping.content.verify_access is None


@pytest.mark.parametrize(
    "mapping_ref,purpose,root",
    (
        ("other-mapping", DockerWSLPathPurposeV1.SOURCE_READ, "/mnt/synaptic/source"),
        ("source-mapping", DockerWSLPathPurposeV1.ARTIFACT_WRITE, "/mnt/synaptic/source"),
        ("source-mapping", DockerWSLPathPurposeV1.SOURCE_READ, "/mnt/other"),
    ),
)
def test_pair_rejects_nonadjacent_mapping_ref_purpose_or_root(
    tmp_path, source_env, mapping_ref, purpose, root,
):
    _, storage, wsl, _ = _pair_authorities(tmp_path)
    source, _ = _mapping_contents(source_env)
    with pytest.raises(DockerMountErrorV1) as caught:
        DockerStoragePathMappingPairV1.build(
            storage.issue(source),
            wsl.issue(DockerWSLRootMappingV1.build(
                mapping_ref, "Ubuntu-22.04", purpose, root,
            )),
        )
    assert caught.value.code is DockerMountCodeV1.MAPPING_CONFLICT


def test_pair_authority_authenticates_outer_and_both_nested_envelopes(
    tmp_path, source_env,
):
    _, storage, wsl, pair_authority = _pair_authorities(tmp_path)
    value = _source_pair(source_env, storage, wsl)
    authenticated = pair_authority.issue(value)
    assert pair_authority.authenticate(authenticated) == authenticated

    forged_storage = AuthenticatedDockerStorageMappingV1(
        value.storage_mapping.content,
        value.storage_mapping.authority_ref,
        value.storage_mapping.key_ref,
        "f" * 64,
    )
    forged_pair = DockerStoragePathMappingPairV1.build(
        forged_storage, value.wsl_mapping
    )
    with pytest.raises(ValueError, match="Docker authority operation failed"):
        pair_authority.issue(forged_pair)

    forged_outer = AuthenticatedDockerStoragePathMappingPairV1(
        authenticated.content, authenticated.authority_ref,
        authenticated.key_ref, "e" * 64,
    )
    assert pair_authority.authenticate(forged_outer) is None


def test_same_key_cannot_replay_across_authority_or_domain(tmp_path, source_env):
    authenticator, storage, _, _ = _pair_authorities(tmp_path)
    source, _ = _mapping_contents(source_env)
    issued = storage.issue(source)
    alternate = DockerStorageMappingHmacAuthorityV1(
        authority_ref="alternate-storage-authority",
        authenticator=authenticator,
    )
    assert alternate.authenticate(issued) is None
    wsl = DockerWSLRootMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    assert wsl._kernel._purpose != storage._kernel._purpose


def test_typed_authorities_reject_subclasses_and_reconstruct(tmp_path, source_env):
    authenticator = _authenticator(tmp_path)
    _, declaration, _ = source_env
    authority = DockerSourceDeclarationHmacAuthorityV1(
        authority_ref="docker-declaration-authority",
        authenticator=authenticator,
    )
    envelope = authority.issue(declaration)
    assert authority.authenticate(envelope) == envelope

    class DeclarationSubclass(type(declaration)):
        pass

    subclass = object.__new__(DeclarationSubclass)
    for name in declaration.__slots__:
        object.__setattr__(subclass, name, getattr(declaration, name))
    with pytest.raises(ValueError, match="Docker authority operation failed"):
        authority.issue(subclass)


def test_engine_binding_authority_and_host_view_share_one_signer(tmp_path, mount_env):
    engine = DockerCommandBindingHmacAuthorityV1(
        authority_ref="docker-command-authority",
        authenticator=_authenticator(tmp_path),
    )
    content = mount_env["catalog"].value.content
    envelope = engine.issue(content)
    assert engine.authenticate(envelope) is True
    host = DockerCommandBindingEnvelopeAuthorityViewV1(engine)
    assert host.authenticate(envelope) == envelope
    assert not hasattr(host, "issue")


def test_host_binding_view_accepts_only_exact_true(mount_env):
    envelope = mount_env["catalog"].value

    class TruthyAuthority:
        authority_ref = envelope.authority_ref
        key_ref = envelope.key_ref

        def authenticate(self, value):
            return 1

    assert DockerCommandBindingEnvelopeAuthorityViewV1(
        TruthyAuthority()
    ).authenticate(envelope) is None


def test_engine_evidence_view_boolean_authenticates_exact_envelopes(tmp_path):
    authenticator = _authenticator(tmp_path)
    source = DockerSourceSealHmacAuthorityV1(
        authority_ref="docker-source-seal-authority",
        authenticator=authenticator,
    )
    absence = DockerAbsenceHmacAuthorityV1(
        authority_ref="docker-absence-authority", authenticator=authenticator
    )
    view = DockerEvidenceAuthorityViewV1(
        source_seal_authority=source, absence_authority=absence
    )
    source_envelope = source.issue(DockerSourceSealContentV1(
        SHA, "b" * 64, "dataset-source", "c" * 64,
        True, "bundle-stage", "d" * 64,
    ))
    absence_envelope = absence.issue(DockerAbsenceContentV1(
        SHA, "b" * 64, DockerLookupPurposeV1.OBSERVE, 1, "c" * 64
    ))
    assert view.authenticate_source_seal(source_envelope) is True
    assert view.authenticate_absence(absence_envelope) is True
    assert view.authenticate_source_seal(replace(
        source_envelope, tag="f" * 64
    )) is False
    assert view.authenticate_absence(object()) is False


def test_empty_workload_environment_round_trip_and_key_identity_pin(tmp_path):
    authenticator = _authenticator(tmp_path)
    authority = DockerWorkloadEnvironmentBindingHmacAuthorityV1(
        authority_ref="docker-workload-environment-authority",
        authenticator=authenticator,
    )
    content = DockerWorkloadEnvironmentBindingV1.build(SHA, (), ())
    envelope = authority.issue(content)
    assert authority.authenticate(envelope) == envelope
    authenticator.key_ref = "changed-key"
    assert authority.authenticate(envelope) is None
    with pytest.raises(ValueError, match="Docker authority operation failed") as caught:
        authority.issue(content)
    assert caught.value.__cause__ is None
    assert "changed-key" not in str(caught.value)


def test_remaining_typed_host_authorities_round_trip(tmp_path, mount_env):
    authenticator = _authenticator(tmp_path)
    stage = mount_env["stage_record"]
    source_request = DockerWSLPathRequestV1.build(
        mapping_ref="source-mapping", expected_mapping_digest="b" * 64,
        expected_distro="Ubuntu-22.04",
        purpose=DockerWSLPathPurposeV1.SOURCE_READ,
        posix_path="/mnt/synaptic/source",
    )
    artifact_request = DockerWSLPathRequestV1.build(
        mapping_ref="artifact-mapping", expected_mapping_digest="c" * 64,
        expected_distro="Ubuntu-22.04",
        purpose=DockerWSLPathPurposeV1.ARTIFACT_WRITE,
        posix_path="/mnt/synaptic/artifacts",
    )
    path_binding = DockerCreatePathBindingV1.build(
        labels_digest="d" * 64,
        source_ref="dataset-source", artifact_ref="artifact-root",
        mount_resolution_digest="e" * 64,
        source_storage_mapping_proof_digest="1" * 64,
        artifact_storage_mapping_proof_digest="2" * 64,
        source_mapping_pair_proof_digest="8" * 64,
        artifact_mapping_pair_proof_digest="9" * 64,
        source_request=source_request, artifact_request=artifact_request,
        source_read_only=True,
    )
    operation = DockerControlOperationV1.CREATE
    operation_id = docker_operation_id_v1(operation, "submit-effect")
    intent = DockerControlIntentV1.build(
        operation_id=operation_id, operation=operation,
        effect_id="submit-effect", engine_command_digest="3" * 64,
        labels_digest="4" * 64, container_name="synaptic-container",
        create_specification_digest="5" * 64,
        cli_command_digest="6" * 64, cli_policy_digest="a" * 64,
        container_ref=None,
        verified_create_record_digest=None,
    )
    assert intent.cli_policy_digest == "a" * 64
    mutation = DockerMutationRecordV1.build(
        operation_id=operation_id, operation=operation,
        effect_id="submit-effect", control_intent_proof_digest="7" * 64,
        phase=DockerMutationPhaseV1.ADMITTED, revision=1, attempt_count=0,
        previous_record_digest=None, container_ref=None,
        verification_result_digest=None,
    )
    expected_create = _one_id_fixture()[3].content
    cases = (
        (
            DockerStageBundleRecordHmacAuthorityV1,
            "docker-stage-authority", stage,
        ),
        (
            BundleBindingHmacAuthorityV1,
            "docker-bundle-authority", stage.authenticated_binding.content,
        ),
        (
            DockerCreatePathBindingHmacAuthorityV1,
            "docker-create-path-authority", path_binding,
        ),
        (
            DockerControlIntentHmacAuthorityV1,
            "docker-control-intent-authority", intent,
        ),
        (
            DockerMutationRecordHmacAuthorityV1,
            "docker-mutation-authority", mutation,
        ),
        (
            DockerExpectedCreateBindingHmacAuthorityV1,
            "docker-expected-create-authority", expected_create,
        ),
    )
    for authority_type, authority_ref, content in cases:
        authority = authority_type(
            authority_ref=authority_ref, authenticator=authenticator
        )
        envelope = authority.issue(content)
        assert authority.authenticate(envelope) == envelope


def test_every_public_typed_signing_domain_is_unique():
    authority_types = (
        DockerSourceDeclarationHmacAuthorityV1,
        DockerStageBundleRecordHmacAuthorityV1,
        DockerCommandBindingHmacAuthorityV1,
        DockerStorageMappingHmacAuthorityV1,
        BundleBindingHmacAuthorityV1,
        DockerSourceSealHmacAuthorityV1,
        DockerWSLRootMappingHmacAuthorityV1,
        DockerCreatePathBindingHmacAuthorityV1,
        DockerWorkloadEnvironmentBindingHmacAuthorityV1,
        DockerControlIntentHmacAuthorityV1,
        DockerMutationRecordHmacAuthorityV1,
        DockerAbsenceHmacAuthorityV1,
        DockerExpectedCreateBindingHmacAuthorityV1,
        DockerStoragePathMappingPairHmacAuthorityV1,
    )
    purposes = (
        "synaptic-host-docker-source-declaration-authority/v1",
        "synaptic-host-docker-stage-bundle-record-authority/v1",
        "synaptic-host-docker-command-binding-authority/v1",
        "synaptic-host-docker-storage-mapping-authority/v1",
        "synaptic-host-docker-bundle-binding-authority/v1",
        "synaptic-host-docker-source-seal-authority/v1",
        "synaptic-host-docker-wsl-root-mapping-authority/v1",
        "synaptic-host-docker-create-path-binding-authority/v1",
        "synaptic-host-docker-workload-environment-binding-authority/v1",
        "synaptic-host-docker-control-intent-authority/v1",
        "synaptic-host-docker-mutation-record-authority/v1",
        "synaptic-host-docker-absence-authority/v1",
        "synaptic-host-docker-expected-create-binding-authority/v1",
        "synaptic-host-docker-storage-path-mapping-pair-authority/v1",
    )
    assert all(authority_type.__dictoffset__ == 0 for authority_type in authority_types)
    assert len(purposes) == len(set(purposes)) == len(authority_types)
    assert all(
        purpose.startswith("synaptic-host-docker-")
        and purpose.endswith("/v1")
        for purpose in purposes
    )


def test_hostile_exact_authenticator_results_fail_closed(tmp_path):
    authenticator = _authenticator(tmp_path)
    authority = DockerWorkloadEnvironmentBindingHmacAuthorityV1(
        authority_ref="docker-workload-environment-authority",
        authenticator=authenticator,
    )
    content = DockerWorkloadEnvironmentBindingV1.build(SHA, (), ())
    envelope = authority.issue(content)
    authenticator.verify = lambda *arguments: 1
    assert authority.authenticate(envelope) is None

    def mutate_during_sign(*arguments):
        authenticator.key_ref = "hostile-key"
        return b"x" * 32

    authenticator.key_ref = authority.key_ref
    authenticator.sign = mutate_during_sign
    with pytest.raises(ValueError, match="Docker authority operation failed") as caught:
        authority.issue(content)
    assert caught.value.__cause__ is None
    assert "hostile-key" not in str(caught.value)


@pytest.mark.parametrize(
    "mutation",
    (
        "authority_ref", "key_ref", "kernel", "authenticator_key",
        "authenticator_path", "purpose",
    ),
)
def test_pair_revalidates_complete_outer_trust_after_each_nested_callback(
    tmp_path, source_env, mutation,
):
    authenticator = _authenticator(tmp_path)
    storage = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    wsl = DockerWSLRootMappingHmacAuthorityV1(
        authority_ref="docker-wsl-authority", authenticator=authenticator
    )

    class MutatingStorageView:
        authority_ref = storage.authority_ref
        key_ref = storage.key_ref
        armed = False
        outer = None

        def authenticate(self, value):
            returned = storage.authenticate(value)
            if self.armed:
                if mutation == "authority_ref":
                    self.outer.authority_ref = "mutated-pair-authority"
                elif mutation == "key_ref":
                    self.outer.key_ref = "mutated-pair-key"
                elif mutation == "kernel":
                    self.outer._kernel = object()
                elif mutation == "authenticator_key":
                    authenticator.key_ref = "mutated-authenticator-key"
                elif mutation == "authenticator_path":
                    authenticator.key_path = (
                        authenticator.key_path.parent / "mutated-authority.key"
                    )
                else:
                    self.outer._kernel._purpose = (
                        "synaptic-host-docker-mutated-pair-authority/v1"
                    )
            return returned

    nested = MutatingStorageView()
    outer = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="docker-pair-authority", authenticator=authenticator,
        storage_mapping_authority=nested, wsl_mapping_authority=wsl,
    )
    nested.outer = outer
    value = _source_pair(source_env, storage, wsl)
    authenticated = outer.issue(value)
    nested.armed = True
    assert outer.authenticate(authenticated) is None


def test_pair_issue_closes_when_nested_callback_mutates_outer_identity(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    storage = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    wsl = DockerWSLRootMappingHmacAuthorityV1(
        authority_ref="docker-wsl-authority", authenticator=authenticator
    )

    class MutatingStorageView:
        authority_ref = storage.authority_ref
        key_ref = storage.key_ref
        outer = None

        def authenticate(self, value):
            returned = storage.authenticate(value)
            self.outer.authority_ref = "mutated-pair-authority"
            return returned

    nested = MutatingStorageView()
    outer = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="docker-pair-authority", authenticator=authenticator,
        storage_mapping_authority=nested, wsl_mapping_authority=wsl,
    )
    nested.outer = outer
    with pytest.raises(ValueError, match="Docker authority operation failed"):
        outer.issue(_source_pair(source_env, storage, wsl))


def test_exact_authority_schema_is_literal_pinned_and_subclasses_reject(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    storage = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    assert not hasattr(storage, "__dict__")
    with pytest.raises(AttributeError):
        storage._content_type = DockerWSLRootMappingV1

    class UnsupportedStorageAuthority(DockerStorageMappingHmacAuthorityV1):
        pass

    with pytest.raises(ValueError, match="Docker authority operation failed"):
        UnsupportedStorageAuthority(
            authority_ref="unsupported-authority", authenticator=authenticator
        )

    changes = {
        "_content_type": DockerWSLRootMappingV1,
        "_envelope_type": type(_pair_authorities(tmp_path)[2].issue(
            DockerWSLRootMappingV1.build(
                "source-mapping", "Ubuntu-22.04",
                DockerWSLPathPurposeV1.SOURCE_READ,
                "/mnt/synaptic/source",
            )
        )),
        "_digest_attribute": "mapping_digest",
        "_purpose": "synaptic-host-docker-wsl-root-mapping-authority/v1",
    }
    try:
        for name, value in changes.items():
            setattr(DockerStorageMappingHmacAuthorityV1, name, value)
        newly_constructed = DockerStorageMappingHmacAuthorityV1(
            authority_ref="new-storage-authority", authenticator=authenticator
        )
        assert storage.authenticate(storage.issue(source)) is not None
        assert newly_constructed.authenticate(
            newly_constructed.issue(source)
        ) is not None
        wsl_content = DockerWSLRootMappingV1.build(
            "source-mapping", "Ubuntu-22.04",
            DockerWSLPathPurposeV1.SOURCE_READ, "/mnt/synaptic/source",
        )
        with pytest.raises(ValueError, match="Docker authority operation failed"):
            storage.issue(wsl_content)
        with pytest.raises(ValueError, match="Docker authority operation failed"):
            newly_constructed.issue(wsl_content)
    finally:
        for name in changes:
            delattr(DockerStorageMappingHmacAuthorityV1, name)


def test_live_class_mutation_during_sign_cannot_change_constructed_schema(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    original_sign = authenticator.sign

    def mutate_class_then_sign(*arguments):
        DockerStorageMappingHmacAuthorityV1._content_type = DockerWSLRootMappingV1
        DockerStorageMappingHmacAuthorityV1._purpose = (
            "synaptic-host-docker-wsl-root-mapping-authority/v1"
        )
        return original_sign(*arguments)

    authenticator.sign = mutate_class_then_sign
    try:
        envelope = authority.issue(source)
        assert type(envelope) is AuthenticatedDockerStorageMappingV1
    finally:
        del DockerStorageMappingHmacAuthorityV1._content_type
        del DockerStorageMappingHmacAuthorityV1._purpose


def test_kernel_domain_mutation_during_sign_and_verify_fails_closed(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    envelope = authority.issue(source)
    expected_purpose = "synaptic-host-docker-storage-mapping-authority/v1"

    original_verify = authenticator.verify

    def mutate_domain_during_verify(*arguments):
        result = original_verify(*arguments)
        authority._kernel._purpose = (
            "synaptic-host-docker-wsl-root-mapping-authority/v1"
        )
        return result

    authenticator.verify = mutate_domain_during_verify
    assert authority.authenticate(envelope) is None

    authority._kernel._purpose = expected_purpose
    original_sign = authenticator.sign

    def mutate_domain_during_sign(*arguments):
        result = original_sign(*arguments)
        authority._kernel._purpose = (
            "synaptic-host-docker-wsl-root-mapping-authority/v1"
        )
        return result

    authenticator.sign = mutate_domain_during_sign
    with pytest.raises(ValueError, match="Docker authority operation failed"):
        authority.issue(source)


def test_replacing_global_authority_lookup_cannot_substitute_trust_anchor(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    envelope = authority.issue(source)
    fake_token = object()
    forged = authority_module._AuthorityPinsV1(
        DockerStorageMappingHmacAuthorityV1,
        authority.authority_ref, authority.key_ref, authority._kernel,
        DockerWSLRootMappingV1,
        authority_module.AuthenticatedDockerWSLRootMappingV1,
        "mapping_digest",
        "synaptic-host-docker-wsl-root-mapping-authority/v1",
        fake_token,
    )
    authority_module._lookup_authority_pins = lambda value: (
        forged, fake_token
    )
    try:
        assert authority.authenticate(envelope) == envelope
        assert authority.authenticate(authority.issue(source)) is not None
        with pytest.raises(ValueError, match="Docker authority operation failed"):
            authority.issue(DockerWSLRootMappingV1.build(
                "source-mapping", "Ubuntu-22.04",
                DockerWSLPathPurposeV1.SOURCE_READ,
                "/mnt/synaptic/source",
            ))
    finally:
        del authority_module._lookup_authority_pins


def test_global_schema_and_class_rebinding_before_construction_are_inert(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    original_storage_type = DockerStorageMappingHmacAuthorityV1
    fake_schema = SimpleNamespace(
        content_type=DockerWSLRootMappingV1,
        envelope_type=authority_module.AuthenticatedDockerWSLRootMappingV1,
        digest_attribute="mapping_digest",
        purpose="synaptic-host-docker-wsl-root-mapping-authority/v1",
    )
    authority_module._AUTHORITY_SCHEMAS = {
        original_storage_type: fake_schema
    }
    authority_module._EnvelopeSchemaV1 = type(fake_schema)
    authority_module.DockerStorageMappingHmacAuthorityV1 = (
        DockerWSLRootMappingHmacAuthorityV1
    )
    try:
        object.__setattr__(
            fake_schema, "purpose",
            "synaptic-host-docker-mutated-shared-schema/v1",
        )
        authority = original_storage_type(
            authority_ref="docker-storage-authority",
            authenticator=authenticator,
        )
        envelope = authority.issue(source)
        assert type(envelope) is AuthenticatedDockerStorageMappingV1
        assert authority.authenticate(envelope) == envelope
        with pytest.raises(ValueError, match="Docker authority operation failed"):
            authority.issue(DockerWSLRootMappingV1.build(
                "source-mapping", "Ubuntu-22.04",
                DockerWSLPathPurposeV1.SOURCE_READ,
                "/mnt/synaptic/source",
            ))
    finally:
        del authority_module._AUTHORITY_SCHEMAS
        del authority_module._EnvelopeSchemaV1
        authority_module.DockerStorageMappingHmacAuthorityV1 = (
            original_storage_type
        )


def test_callback_time_global_pin_and_schema_substitution_is_inert(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    envelope = authority.issue(source)
    original_sign = authenticator.sign
    original_verify = authenticator.verify

    def substitute_globals():
        fake = SimpleNamespace(
            content_type=DockerWSLRootMappingV1,
            envelope_type=authority_module.AuthenticatedDockerWSLRootMappingV1,
            digest_attribute="mapping_digest",
            purpose="synaptic-host-docker-wsl-root-mapping-authority/v1",
        )
        authority_module._AUTHORITY_SCHEMAS = {
            DockerStorageMappingHmacAuthorityV1: fake
        }
        authority_module._lookup_authority_pins = lambda value: (fake, object())
        authority_module._EnvelopeSchemaV1 = type(fake)
        object.__setattr__(
            fake, "purpose",
            "synaptic-host-docker-mutated-shared-schema/v1",
        )

    def substitute_during_sign(*arguments):
        result = original_sign(*arguments)
        substitute_globals()
        return result

    authenticator.sign = substitute_during_sign
    issued = authority.issue(source)
    assert type(issued) is AuthenticatedDockerStorageMappingV1

    def substitute_during_verify(*arguments):
        result = original_verify(*arguments)
        substitute_globals()
        return result

    authenticator.verify = substitute_during_verify
    try:
        assert authority.authenticate(envelope) == envelope
        assert authority.authenticate(issued) == issued
        later = DockerStorageMappingHmacAuthorityV1(
            authority_ref="later-storage-authority",
            authenticator=authenticator,
        )
        assert later.authenticate(later.issue(source)) is not None
        with pytest.raises(ValueError, match="Docker authority operation failed"):
            authority.issue(DockerWSLRootMappingV1.build(
                "source-mapping", "Ubuntu-22.04",
                DockerWSLPathPurposeV1.SOURCE_READ,
                "/mnt/synaptic/source",
            ))
    finally:
        del authority_module._AUTHORITY_SCHEMAS
        del authority_module._lookup_authority_pins
        del authority_module._EnvelopeSchemaV1


def test_replacing_module_pin_type_does_not_change_original_pin_identity(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    envelope = authority.issue(source)
    original_pin_type = authority_module._AuthorityPinsV1
    authority_module._AuthorityPinsV1 = SimpleNamespace
    try:
        assert authority.authenticate(envelope) == envelope
        later = DockerStorageMappingHmacAuthorityV1(
            authority_ref="later-storage-authority",
            authenticator=authenticator,
        )
        assert later.authenticate(later.issue(source)) is not None
    finally:
        authority_module._AuthorityPinsV1 = original_pin_type


def test_reconstruction_dispatch_is_sealed_before_authority_construction(
    tmp_path, source_env, mount_env,
):
    source, _ = _mapping_contents(source_env)
    verify = source.verify_access
    originals = _substitute_reconstruction_globals()
    try:
        authenticator = _authenticator(tmp_path)
        storage = DockerStorageMappingHmacAuthorityV1(
            authority_ref="docker-storage-authority",
            authenticator=authenticator,
        )
        wsl = DockerWSLRootMappingHmacAuthorityV1(
            authority_ref="docker-wsl-authority", authenticator=authenticator
        )
        pair = DockerStoragePathMappingPairHmacAuthorityV1(
            authority_ref="docker-pair-authority",
            authenticator=authenticator,
            storage_mapping_authority=storage,
            wsl_mapping_authority=wsl,
        )
        value = DockerStoragePathMappingPairV1.build(
            storage.issue(source),
            wsl.issue(DockerWSLRootMappingV1.build(
                "source-mapping", "Ubuntu-22.04",
                DockerWSLPathPurposeV1.SOURCE_READ,
                "/mnt/synaptic/source",
            )),
        )
        issued = pair.issue(value)
        authenticated = pair.authenticate(issued)
        assert authenticated == issued
        retained = authenticated.content.storage_mapping.content.verify_access
        assert retained.verify_borrow is verify.verify_borrow
        assert retained.verify_root is verify.verify_root

        engine = DockerCommandBindingHmacAuthorityV1(
            authority_ref="docker-command-authority",
            authenticator=authenticator,
        )
        command = engine.issue(mount_env["catalog"].value.content)
        assert engine.authenticate(command) is True
        assert DockerCommandBindingEnvelopeAuthorityViewV1(
            engine
        ).authenticate(command) == command

        source_seal = DockerSourceSealHmacAuthorityV1(
            authority_ref="docker-source-seal-authority",
            authenticator=authenticator,
        )
        absence = DockerAbsenceHmacAuthorityV1(
            authority_ref="docker-absence-authority",
            authenticator=authenticator,
        )
        evidence = DockerEvidenceAuthorityViewV1(
            source_seal_authority=source_seal, absence_authority=absence
        )
        source_seal_envelope = source_seal.issue(DockerSourceSealContentV1(
            SHA, "b" * 64, "dataset-source", "c" * 64,
            True, "bundle-stage", "d" * 64,
        ))
        absence_envelope = absence.issue(DockerAbsenceContentV1(
            SHA, "b" * 64, DockerLookupPurposeV1.OBSERVE, 1, "c" * 64
        ))
        assert evidence.authenticate_source_seal(source_seal_envelope) is True
        assert evidence.authenticate_absence(absence_envelope) is True
    finally:
        _restore_reconstruction_globals(originals)


def test_callback_time_reconstruction_substitution_preserves_live_identity(
    tmp_path, source_env,
):
    source, _ = _mapping_contents(source_env)
    verify = source.verify_access
    authenticator = _authenticator(tmp_path)
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    baseline = authority.issue(source)
    original_sign = authenticator.sign
    original_verify = authenticator.verify
    substitutions = []

    def substitute_after_sign(*arguments):
        result = original_sign(*arguments)
        substitutions.append(_substitute_reconstruction_globals())
        return result

    def substitute_after_verify(*arguments):
        result = original_verify(*arguments)
        substitutions.append(_substitute_reconstruction_globals())
        return result

    try:
        authenticator.sign = substitute_after_sign
        issued = authority.issue(source)
        assert issued.content.verify_access.verify_borrow is verify.verify_borrow
        assert issued.content.verify_access.verify_root is verify.verify_root

        authenticator.sign = original_sign
        authenticator.verify = substitute_after_verify
        authenticated = authority.authenticate(baseline)
        assert authenticated == baseline
        assert authenticated.content.verify_access.verify_borrow is verify.verify_borrow
        assert authenticated.content.verify_access.verify_root is verify.verify_root
    finally:
        for originals in reversed(substitutions):
            _restore_reconstruction_globals(originals)


def test_nested_pair_callback_substitution_uses_sealed_dispatcher(
    tmp_path, source_env,
):
    authenticator = _authenticator(tmp_path)
    storage = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority", authenticator=authenticator
    )
    wsl = DockerWSLRootMappingHmacAuthorityV1(
        authority_ref="docker-wsl-authority", authenticator=authenticator
    )
    value = _source_pair(source_env, storage, wsl)
    verify = value.storage_mapping.content.verify_access
    substitutions = []

    class SubstitutingStorageView:
        authority_ref = storage.authority_ref
        key_ref = storage.key_ref

        def authenticate(self, envelope):
            result = storage.authenticate(envelope)
            substitutions.append(_substitute_reconstruction_globals())
            return result

    pair = DockerStoragePathMappingPairHmacAuthorityV1(
        authority_ref="docker-pair-authority", authenticator=authenticator,
        storage_mapping_authority=SubstitutingStorageView(),
        wsl_mapping_authority=wsl,
    )
    try:
        issued = pair.issue(value)
        authenticated = pair.authenticate(issued)
        assert authenticated == issued
        retained = authenticated.content.storage_mapping.content.verify_access
        assert retained.verify_borrow is verify.verify_borrow
        assert retained.verify_root is verify.verify_root
    finally:
        for originals in reversed(substitutions):
            _restore_reconstruction_globals(originals)


def test_sealed_failure_factory_normalizes_reconstruction_failure(
    tmp_path,
):
    authority = DockerStorageMappingHmacAuthorityV1(
        authority_ref="docker-storage-authority",
        authenticator=_authenticator(tmp_path),
    )
    originals = _substitute_reconstruction_globals()
    try:
        with pytest.raises(
            ValueError, match="^Docker authority operation failed$"
        ) as caught:
            authority.issue(object())
        assert caught.value.__cause__ is None
        assert caught.value.__suppress_context__ is True
        assert "hostile" not in str(caught.value)
    finally:
        _restore_reconstruction_globals(originals)


def test_all_constructor_trust_decisions_ignore_rebound_module_globals(
    tmp_path, source_env, mount_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    originals = _substitute_constructor_globals()
    try:
        storage = DockerStorageMappingHmacAuthorityV1(
            authority_ref="docker-storage-authority",
            authenticator=authenticator,
        )
        wsl = DockerWSLRootMappingHmacAuthorityV1(
            authority_ref="docker-wsl-authority", authenticator=authenticator
        )
        pair = DockerStoragePathMappingPairHmacAuthorityV1(
            authority_ref="docker-pair-authority",
            authenticator=authenticator,
            storage_mapping_authority=storage,
            wsl_mapping_authority=wsl,
        )
        pair_envelope = pair.issue(_source_pair(source_env, storage, wsl))
        assert pair.authenticate(pair_envelope) == pair_envelope
        assert storage.authenticate(storage.issue(source)) is not None

        engine = DockerCommandBindingHmacAuthorityV1(
            authority_ref="docker-command-authority",
            authenticator=authenticator,
        )
        command = engine.issue(mount_env["catalog"].value.content)
        command_view = DockerCommandBindingEnvelopeAuthorityViewV1(engine)
        assert command_view.authenticate(command) == command

        source_seal = DockerSourceSealHmacAuthorityV1(
            authority_ref="docker-source-seal-authority",
            authenticator=authenticator,
        )
        absence = DockerAbsenceHmacAuthorityV1(
            authority_ref="docker-absence-authority",
            authenticator=authenticator,
        )
        evidence = DockerEvidenceAuthorityViewV1(
            source_seal_authority=source_seal, absence_authority=absence
        )
        source_envelope = source_seal.issue(DockerSourceSealContentV1(
            SHA, "b" * 64, "dataset-source", "c" * 64,
            True, "bundle-stage", "d" * 64,
        ))
        absence_envelope = absence.issue(DockerAbsenceContentV1(
            SHA, "b" * 64, DockerLookupPurposeV1.OBSERVE, 1, "c" * 64
        ))
        assert evidence.authenticate_source_seal(source_envelope) is True
        assert evidence.authenticate_absence(absence_envelope) is True
    finally:
        _restore_reconstruction_globals(originals)


def test_all_installed_constructors_reject_invalid_refs_after_rebinding(
    tmp_path,
):
    authenticator = _authenticator(tmp_path)
    originals = _substitute_constructor_globals()
    valid = SimpleNamespace(
        authority_ref="valid-authority", key_ref="valid-key",
        authenticate=lambda value: value,
    )
    invalid = SimpleNamespace(
        authority_ref="", key_ref="valid-key",
        authenticate=lambda value: value,
    )
    try:
        _assert_closed_constructor_failure(lambda: (
            DockerStorageMappingHmacAuthorityV1(
                authority_ref="", authenticator=authenticator
            )
        ))
        _assert_closed_constructor_failure(lambda: (
            DockerCommandBindingEnvelopeAuthorityViewV1(invalid)
        ))
        _assert_closed_constructor_failure(lambda: DockerEvidenceAuthorityViewV1(
            source_seal_authority=invalid, absence_authority=valid
        ))
        _assert_closed_constructor_failure(
            lambda: DockerStoragePathMappingPairHmacAuthorityV1(
                authority_ref="docker-pair-authority",
                authenticator=authenticator,
                storage_mapping_authority=invalid,
                wsl_mapping_authority=valid,
            )
        )
    finally:
        _restore_reconstruction_globals(originals)


def test_callback_substitution_cannot_change_later_constructor_semantics(
    tmp_path, source_env, mount_env,
):
    authenticator = _authenticator(tmp_path)
    source, _ = _mapping_contents(source_env)
    first = DockerStorageMappingHmacAuthorityV1(
        authority_ref="first-storage-authority", authenticator=authenticator
    )
    original_sign = authenticator.sign
    substitutions = []

    def substitute_after_sign(*arguments):
        result = original_sign(*arguments)
        substitutions.append(_substitute_constructor_globals())
        return result

    try:
        authenticator.sign = substitute_after_sign
        assert first.issue(source).content == source
        authenticator.sign = original_sign

        later = DockerStorageMappingHmacAuthorityV1(
            authority_ref="later-storage-authority",
            authenticator=authenticator,
        )
        assert later.authenticate(later.issue(source)) is not None
        engine = DockerCommandBindingHmacAuthorityV1(
            authority_ref="later-command-authority",
            authenticator=authenticator,
        )
        command = engine.issue(mount_env["catalog"].value.content)
        assert DockerCommandBindingEnvelopeAuthorityViewV1(
            engine
        ).authenticate(command) == command

        invalid = SimpleNamespace(
            authority_ref="", key_ref="valid-key",
            authenticate=lambda value: value,
        )
        _assert_closed_constructor_failure(lambda: (
            DockerCommandBindingEnvelopeAuthorityViewV1(invalid)
        ))
    finally:
        for originals in reversed(substitutions):
            _restore_reconstruction_globals(originals)
