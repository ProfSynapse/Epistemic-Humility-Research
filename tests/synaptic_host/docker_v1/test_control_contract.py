from dataclasses import replace
from enum import Enum
from hashlib import sha256
import pickle
import traceback

import pytest

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    DockerAbsenceContentV1,
    DockerLookupPurposeV1,
)

from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1,
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerWorkloadEnvironmentBindingV1,
    DockerAdmissionDispositionV1,
    DockerAdmissionResultV1,
    DockerCASDispositionV1,
    DockerCASResultV1,
    DockerControlContractErrorV1,
    DockerControlIntentV1,
    DockerControlOperationV1,
    DockerCreatePathBindingV1,
    DockerCreateSpecificationV1,
    DockerMutationLookupDispositionV1,
    DockerMutationLookupResultV1,
    DockerMutationAdmissionRequestV1,
    DockerMutationCASRequestV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
    DockerWorkloadEnvironmentBindingV1,
    DockerWorkloadEnvironmentEntryV1,
    docker_operation_id_v1,
    authenticate_absence_v1,
    authenticate_control_intent_v1,
    authenticate_create_path_binding_v1,
    authenticate_mutation_record_v1,
    authenticate_workload_environment_binding_v1,
)
from synaptic_host.docker_v1.control_private import (
    DockerPrivateWorkloadEnvironmentResolutionV1,
)
from synaptic_host.docker_v1.model import (
    DockerWSLPathPurposeV1,
    DockerWSLPathRequestV1,
)


SHA = "a" * 64


def _request(ref, purpose, path):
    return DockerWSLPathRequestV1.build(
        mapping_ref=ref, expected_mapping_digest=SHA,
        expected_distro="Ubuntu-22.04", purpose=purpose, posix_path=path,
    )


def _path_binding():
    return DockerCreatePathBindingV1.build(
        labels_digest=SHA, source_ref="source", artifact_ref="artifact",
        mount_resolution_digest=SHA,
        source_storage_mapping_proof_digest=SHA,
        artifact_storage_mapping_proof_digest=SHA,
        source_request=_request("source-map", DockerWSLPathPurposeV1.SOURCE_READ, "/source"),
        artifact_request=_request("artifact-map", DockerWSLPathPurposeV1.ARTIFACT_WRITE, "/artifacts"),
        source_read_only=True,
    )


def test_path_binding_exact_purposes_distinct_refs_and_recursive_mutation():
    binding = _path_binding()
    assert binding.source_request.purpose is DockerWSLPathPurposeV1.SOURCE_READ
    with pytest.raises(DockerControlContractErrorV1):
        replace(binding, source_ref="artifact")
    object.__setattr__(binding.source_request, "purpose", DockerWSLPathPurposeV1.ARTIFACT_WRITE)
    with pytest.raises(DockerControlContractErrorV1):
        replace(binding)


def test_environment_exact_set_sorting_empty_and_redaction():
    entries = (DockerWorkloadEnvironmentEntryV1.build("A", "secret-a"),
               DockerWorkloadEnvironmentEntryV1.build("B", ""))
    binding = DockerWorkloadEnvironmentBindingV1.build(SHA, ("A", "B"), entries)
    assert "secret-a" not in repr(binding)
    assert DockerWorkloadEnvironmentBindingV1.build(SHA, (), ()).requested_keys == ()
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(SHA, ("A",), entries)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(SHA, ("B", "A"), entries)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(SHA, ("A", "A"), (entries[0], entries[0]))


class EnvAuthority:
    authority_ref = "authority"
    key_ref = "key"
    def authenticate(self, value):
        return AuthenticatedDockerWorkloadEnvironmentBindingV1(
            DockerWorkloadEnvironmentBindingV1(
                value.content.workload_digest, tuple(value.content.requested_keys),
                tuple(DockerWorkloadEnvironmentEntryV1(
                    item.key, item.key_digest, item.value_digest, item.entry_digest
                ) for item in value.content.supplied_entries),
                value.content.binding_digest,
            ), value.authority_ref, value.key_ref, value.tag,
        )


def test_private_environment_is_opaque_unpickleable_and_rehashes():
    entry = DockerWorkloadEnvironmentEntryV1.build("TOKEN", "raw-secret")
    binding = DockerWorkloadEnvironmentBindingV1.build(SHA, ("TOKEN",), (entry,))
    authenticated = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        binding, "authority", "key", SHA
    )
    private = DockerPrivateWorkloadEnvironmentResolutionV1(
        authenticated, (("TOKEN", "raw-secret"),)
    )
    assert "raw-secret" not in repr(private) and "raw-secret" not in str(private)
    assert private.materialize_for_cli(EnvAuthority()) == (("TOKEN", "raw-secret"),)
    with pytest.raises(DockerControlContractErrorV1):
        pickle.dumps(private)
    object.__setattr__(entry, "value_digest", "b" * 64)
    with pytest.raises(DockerControlContractErrorV1) as caught:
        private.materialize_for_cli(EnvAuthority())
    assert "raw-secret" not in "".join(traceback.format_exception(caught.value))


def _spec(**changes):
    values = dict(
        labels_digest=SHA, owned_labels_projection_digest=SHA,
        container_name="synaptic-job", image_digest="sha256:" + "b" * 64,
        runtime_digest=SHA, workload_digest=SHA, argument_count=1,
        arguments_digest=SHA, environment_binding_proof_digest=SHA,
        mount_resolution_digest=SHA, path_binding_proof_digest=SHA,
        source_windows_path_digest=SHA, source_unc_digest=SHA,
        source_destination_digest=sha256(b"/source").hexdigest(),
        source_read_only=True, artifact_windows_path_digest=SHA,
        artifact_unc_digest=SHA,
        artifact_destination_digest=sha256(b"/artifacts").hexdigest(),
        artifact_read_write=True, network_mode="none",
        nano_cpus=1_000_000_000, memory_bytes=1,
    )
    values.update(changes)
    return DockerCreateSpecificationV1.build(**values)


@pytest.mark.parametrize("changes", (
    {"argument_count": 0}, {"argument_count": 65},
    {"nano_cpus": 999_999_999}, {"nano_cpus": 1_000_000_001},
    {"nano_cpus": 257_000_000_000}, {"memory_bytes": 0},
    {"memory_bytes": 2**50 + 1}, {"network_mode": "bridge"},
))
def test_create_spec_engine_bounds_and_fixed_destinations(changes):
    with pytest.raises(DockerControlContractErrorV1):
        _spec(**changes)
    valid = _spec(argument_count=64, nano_cpus=256_000_000_000, memory_bytes=2**50)
    assert valid.source_destination_digest == sha256(b"/source").hexdigest()


def _intent(operation=DockerControlOperationV1.CREATE, **changes):
    effect = "effect"
    values = dict(
        operation_id=docker_operation_id_v1(operation, effect), operation=operation,
        effect_id=effect, engine_command_digest=SHA, labels_digest=SHA,
        container_name="synaptic-job", create_specification_digest=SHA,
        cli_command_digest=SHA, container_ref=None,
        verified_create_record_digest=None,
    )
    if operation is DockerControlOperationV1.START:
        values.update(container_ref="c" * 64, verified_create_record_digest=SHA)
    values.update(changes)
    return DockerControlIntentV1.build(**values)


def _auth_record(phase=DockerMutationPhaseV1.ADMITTED, previous=SHA):
    intent = _intent()
    values = dict(
        operation_id=intent.operation_id, operation=intent.operation,
        effect_id=intent.effect_id,
        control_intent_proof_digest=SHA, phase=phase,
        revision=1, attempt_count=0, previous_record_digest=None,
        container_ref=None, verification_result_digest=None,
    )
    if phase is DockerMutationPhaseV1.ATTEMPTED:
        values.update(revision=2, attempt_count=1, previous_record_digest=previous)
    if phase is DockerMutationPhaseV1.VERIFIED:
        values.update(revision=3, attempt_count=1, previous_record_digest=previous,
                      container_ref="c" * 64, verification_result_digest=SHA)
    record = DockerMutationRecordV1.build(**values)
    return AuthenticatedDockerMutationRecordV1(record, "authority", "key", SHA)


def test_intent_create_start_matrix_and_substitution():
    assert _intent().container_ref is None
    assert _intent(DockerControlOperationV1.START).container_ref is not None
    with pytest.raises(DockerControlContractErrorV1):
        _intent(container_ref="c" * 64)
    with pytest.raises(DockerControlContractErrorV1):
        _intent(DockerControlOperationV1.START, verified_create_record_digest=None)


def test_mutation_phase_matrix_and_downgrade():
    for phase in DockerMutationPhaseV1:
        assert _auth_record(phase).content.phase is phase
    verified = _auth_record(DockerMutationPhaseV1.VERIFIED).content
    with pytest.raises(DockerControlContractErrorV1):
        replace(verified, phase=DockerMutationPhaseV1.ADMITTED)


@pytest.mark.parametrize("disposition", tuple(DockerAdmissionDispositionV1))
def test_admission_result_matrix(disposition):
    candidate = _auth_record()
    request = DockerMutationAdmissionRequestV1.build(
        candidate.content.operation_id, candidate
    )
    required = disposition is not DockerAdmissionDispositionV1.INDETERMINATE
    if disposition is DockerAdmissionDispositionV1.CONFLICT:
        content = candidate.content
        conflicting = DockerMutationRecordV1.build(
            operation_id=content.operation_id, operation=content.operation,
            effect_id=content.effect_id,
            control_intent_proof_digest="b" * 64,
            phase=content.phase, revision=content.revision,
            attempt_count=content.attempt_count,
            previous_record_digest=content.previous_record_digest,
            container_ref=content.container_ref,
            verification_result_digest=content.verification_result_digest,
        )
        record = AuthenticatedDockerMutationRecordV1(
            conflicting, "authority", "key", SHA
        )
    else:
        record = candidate if required else None
    result = DockerAdmissionResultV1.build(request, disposition, record)
    assert (result.record is not None) is required
    with pytest.raises(DockerControlContractErrorV1):
        DockerAdmissionResultV1.build(
            request, disposition, None if required else candidate
        )


def test_cas_and_lookup_matrices_and_exact_operation():
    record = _auth_record()
    replacement = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, record.content.record_digest
    )
    request = DockerMutationCASRequestV1.build(
        record.content.operation_id, record, replacement
    )
    for disposition in (DockerCASDispositionV1.APPLIED, DockerCASDispositionV1.CURRENT):
        returned = replacement if disposition is DockerCASDispositionV1.APPLIED else record
        assert DockerCASResultV1.build(request, disposition, returned).record is returned
    assert DockerCASResultV1.build(request, DockerCASDispositionV1.INDETERMINATE, None).record is None
    found = DockerMutationLookupResultV1.build(
        record.content.operation_id, DockerMutationLookupDispositionV1.FOUND, record
    )
    assert found.record is record
    for disposition in (DockerMutationLookupDispositionV1.ABSENT,
                        DockerMutationLookupDispositionV1.INDETERMINATE):
        assert DockerMutationLookupResultV1.build(SHA, disposition, None).record is None
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationLookupResultV1.build(SHA, DockerMutationLookupDispositionV1.FOUND, record)


class EchoAuthority:
    def __init__(self, authority_ref="authority", key_ref="key"):
        self.authority_ref = authority_ref
        self.key_ref = key_ref
    def authenticate(self, value):
        return value


def test_alternate_signers_fail_for_every_authenticated_contract():
    path = AuthenticatedDockerCreatePathBindingV1(
        _path_binding(), "authority", "key", SHA
    )
    env_content = DockerWorkloadEnvironmentBindingV1.build(SHA, (), ())
    env = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        env_content, "authority", "key", SHA
    )
    intent = AuthenticatedDockerControlIntentV1(
        _intent(), "authority", "key", SHA
    )
    record = _auth_record()
    absence_content = DockerAbsenceContentV1(
        SHA, SHA, DockerLookupPurposeV1.OBSERVE, 1, SHA
    )
    absence = AuthenticatedDockerAbsenceV1(
        absence_content, "authority", "key", SHA
    )
    cases = (
        (authenticate_create_path_binding_v1, path),
        (authenticate_workload_environment_binding_v1, env),
        (authenticate_control_intent_v1, intent),
        (authenticate_mutation_record_v1, record),
        (authenticate_absence_v1, absence),
    )
    for authenticate, envelope in cases:
        assert authenticate(EchoAuthority(), envelope) == envelope
        with pytest.raises(DockerControlContractErrorV1):
            authenticate(EchoAuthority("alternate", "key"), envelope)


def test_private_alternate_signer_never_releases_raw_value():
    raw = "raw-secret-private-value"
    entry = DockerWorkloadEnvironmentEntryV1.build("TOKEN", raw)
    binding = DockerWorkloadEnvironmentBindingV1.build(SHA, ("TOKEN",), (entry,))
    envelope = AuthenticatedDockerWorkloadEnvironmentBindingV1(
        binding, "authority", "key", SHA
    )
    private = DockerPrivateWorkloadEnvironmentResolutionV1(
        envelope, (("TOKEN", raw),)
    )
    with pytest.raises(DockerControlContractErrorV1) as caught:
        private.materialize_for_cli(EchoAuthority("alternate", "key"))
    assert raw not in "".join(traceback.format_exception(caught.value))


def test_environment_exact_64_and_utf8_token_boundaries():
    pairs = tuple(sorted((f"K{i}", "v") for i in range(64)))
    entries = tuple(DockerWorkloadEnvironmentEntryV1.build(*pair) for pair in pairs)
    binding = DockerWorkloadEnvironmentBindingV1.build(
        SHA, tuple(key for key, _ in pairs), entries
    )
    assert len(binding.supplied_entries) == 64
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentBindingV1.build(
            SHA, binding.requested_keys + ("Z",),
            entries + (DockerWorkloadEnvironmentEntryV1.build("Z", "v"),),
        )
    DockerWorkloadEnvironmentEntryV1.build("K", "v" * 4094)
    with pytest.raises(DockerControlContractErrorV1):
        DockerWorkloadEnvironmentEntryV1.build("K", "v" * 4095)
    DockerPrivateWorkloadEnvironmentResolutionV1(
        AuthenticatedDockerWorkloadEnvironmentBindingV1(
            DockerWorkloadEnvironmentBindingV1.build(
                SHA, ("K",),
                (DockerWorkloadEnvironmentEntryV1.build("K", "v" * 4094),),
            ), "authority", "key", SHA,
        ), (("K", "v" * 4094),)
    )


def test_bool_counters_container_names_and_refs_fail_closed():
    with pytest.raises(DockerControlContractErrorV1):
        _auth_record().content.__class__.build(
            operation_id=_intent().operation_id,
            operation=DockerControlOperationV1.CREATE,
            effect_id="effect",
            control_intent_proof_digest=SHA,
            phase=DockerMutationPhaseV1.ADMITTED,
            revision=True, attempt_count=0, previous_record_digest=None,
            container_ref=None, verification_result_digest=None,
        )
    with pytest.raises(DockerControlContractErrorV1):
        _spec(container_name="bad/name")
    with pytest.raises(DockerControlContractErrorV1):
        _intent(DockerControlOperationV1.START, container_ref="C" * 64)


def test_foreign_disposition_enum_is_rejected():
    class Foreign(str, Enum):
        ABSENT = "ABSENT"
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationLookupResultV1.build(SHA, Foreign.ABSENT, None)


def _record_from(base, **changes):
    content = base.content
    values = dict(
        operation_id=content.operation_id,
        operation=content.operation,
        effect_id=content.effect_id,
        control_intent_proof_digest=content.control_intent_proof_digest,
        phase=content.phase,
        revision=content.revision,
        attempt_count=content.attempt_count,
        previous_record_digest=content.previous_record_digest,
        container_ref=content.container_ref,
        verification_result_digest=content.verification_result_digest,
    )
    values.update(changes)
    record = DockerMutationRecordV1.build(**values)
    return AuthenticatedDockerMutationRecordV1(
        record, changes.get("authority_ref", base.authority_ref),
        changes.get("key_ref", base.key_ref), SHA,
    )


def test_cas_request_rejects_invalid_transition_graph_and_substitutions():
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, admitted.content.record_digest
    )
    DockerMutationCASRequestV1.build(
        admitted.content.operation_id, admitted, attempted
    )

    invalid = []
    invalid.append(_auth_record(DockerMutationPhaseV1.ATTEMPTED, SHA))
    invalid.append(_record_from(
        admitted, phase=DockerMutationPhaseV1.VERIFIED,
        revision=3, attempt_count=1,
        previous_record_digest=admitted.content.record_digest,
        container_ref="c" * 64, verification_result_digest=SHA,
    ))
    invalid.append(_record_from(
        attempted, phase=DockerMutationPhaseV1.ADMITTED,
        revision=1, attempt_count=0, previous_record_digest=None,
        container_ref=None, verification_result_digest=None,
    ))
    invalid.append(_record_from(
        attempted, previous_record_digest=attempted.content.record_digest,
    ))
    invalid.append(_record_from(
        attempted, control_intent_proof_digest="b" * 64,
    ))
    invalid.append(AuthenticatedDockerMutationRecordV1(
        attempted.content, "alternate", "key", SHA
    ))
    start_id = docker_operation_id_v1(DockerControlOperationV1.START, "effect")
    invalid.append(_record_from(
        attempted, operation=DockerControlOperationV1.START,
        operation_id=start_id,
    ))
    for replacement in invalid:
        with pytest.raises(DockerControlContractErrorV1):
            DockerMutationCASRequestV1.build(
                admitted.content.operation_id, admitted, replacement
            )

    attempted_again = _record_from(
        attempted, previous_record_digest=attempted.content.record_digest
    )
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationCASRequestV1.build(
            attempted.content.operation_id, attempted, attempted_again
        )
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationCASRequestV1.build(
            attempted.content.operation_id, attempted, admitted
        )


@pytest.mark.parametrize("which", ("expected", "replacement"))
def test_cas_request_recursively_rejects_mutated_records(which):
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, admitted.content.record_digest
    )
    target = admitted if which == "expected" else attempted
    object.__setattr__(target.content, "attempt_count", 99)
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationCASRequestV1.build(
            admitted.content.operation_id, admitted, attempted
        )


def test_record_rejects_create_operation_id_relabelled_as_start():
    content = _auth_record().content
    with pytest.raises(DockerControlContractErrorV1):
        DockerMutationRecordV1.build(
            operation_id=content.operation_id,
            operation=DockerControlOperationV1.START,
            effect_id=content.effect_id,
            control_intent_proof_digest=content.control_intent_proof_digest,
            phase=content.phase, revision=content.revision,
            attempt_count=content.attempt_count,
            previous_record_digest=None, container_ref=None,
            verification_result_digest=None,
        )


@pytest.mark.parametrize("key,value", (("BAD\ud800", "value"), ("KEY", "BAD\ud800")))
def test_environment_lone_surrogates_fail_causally_closed(key, value):
    with pytest.raises(DockerControlContractErrorV1) as caught:
        DockerWorkloadEnvironmentEntryV1.build(key, value)
    assert caught.value.code.value == "DOCKER_CONTROL_CONTRACT_INVALID"
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
    assert "UnicodeEncodeError" not in "".join(traceback.format_exception(caught.value))


def test_attempted_to_verified_cas_happy_path_reconstructs_exactly():
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED,
        admitted.content.record_digest,
    )
    verified = _auth_record(
        DockerMutationPhaseV1.VERIFIED,
        attempted.content.record_digest,
    )
    request = DockerMutationCASRequestV1.build(
        attempted.content.operation_id,
        attempted,
        verified,
    )
    rebuilt_request = DockerMutationCASRequestV1(
        request.operation_id,
        request.expected,
        request.replacement,
        request.request_digest,
    )
    assert rebuilt_request == request
    result = DockerCASResultV1.build(
        request, DockerCASDispositionV1.APPLIED, verified
    )
    rebuilt_result = DockerCASResultV1(
        result.request,
        result.disposition,
        result.record,
        result.result_digest,
    )
    assert rebuilt_result == result


def test_effect_id_only_relabel_rejects_canonical_operation_id_binding():
    original = _auth_record().content
    with pytest.raises(DockerControlContractErrorV1) as caught:
        DockerMutationRecordV1.build(
            operation_id=original.operation_id,
            operation=original.operation,
            effect_id="different-effect",
            control_intent_proof_digest=original.control_intent_proof_digest,
            phase=original.phase,
            revision=original.revision,
            attempt_count=original.attempt_count,
            previous_record_digest=original.previous_record_digest,
            container_ref=original.container_ref,
            verification_result_digest=original.verification_result_digest,
        )
    assert caught.value.code.value == "DOCKER_CONTROL_CONTRACT_INVALID"
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True
