from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace

import pytest

from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerExpectedCreateBindingV1,
    AuthenticatedDockerMutationRecordV1,
    DockerAdmissionDispositionV1,
    DockerCASDispositionV1,
    DockerControlContractErrorV1,
    DockerExpectedCreatePublishDispositionV1,
    DockerExpectedCreatePublishRequestV1,
    DockerMutationAdmissionRequestV1,
    DockerMutationCASRequestV1,
    DockerMutationLookupDispositionV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
)
from synaptic_host.docker_v1.memory import InMemoryDockerControlStoreV1
from synaptic_host.docker_v1.memory import InMemoryDockerStageBundleStoreV1
from synaptic_host.docker_v1.model import (
    AuthenticatedDockerStageBundleBindingV1,
    DockerHostSourceErrorV1,
)

from .test_control import _one_id_fixture
from .test_control_contract import _auth_record


def _expected():
    return _one_id_fixture()[3]


def _publish_request(candidate=None):
    candidate = candidate or _expected()
    labels = candidate.content.labels
    return DockerExpectedCreatePublishRequestV1.build(
        labels.command_digest, labels.digest, candidate
    )


def test_publish_resolve_sequential_matrix_and_alias_isolation():
    store = InMemoryDockerControlStoreV1()
    request = _publish_request()
    first = store.publish_once(request)
    assert first.disposition is DockerExpectedCreatePublishDispositionV1.PUBLISHED
    second = store.publish_once(_publish_request())
    assert second.disposition is DockerExpectedCreatePublishDispositionV1.EXISTING
    assert second.binding == first.binding
    assert second.binding is not first.binding
    resolved = store.resolve(request.engine_command_digest, request.labels_digest)
    assert resolved == request.candidate and resolved is not request.candidate
    alternate = AuthenticatedDockerExpectedCreateBindingV1(
        request.candidate.content, request.candidate.authority_ref,
        request.candidate.key_ref, "b" * 64,
    )
    conflict = store.publish_once(_publish_request(alternate))
    assert conflict.disposition is DockerExpectedCreatePublishDispositionV1.CONFLICT
    assert conflict.binding == request.candidate
    assert "raw-secret" not in repr(store)


def test_publish_concurrency_has_one_winner_and_converges():
    store = InMemoryDockerControlStoreV1()
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(
            lambda _index: store.publish_once(_publish_request()), range(32)
        ))
    assert sum(
        item.disposition is DockerExpectedCreatePublishDispositionV1.PUBLISHED
        for item in results
    ) == 1
    assert all(item.binding == results[0].binding for item in results)


def test_publish_request_wrong_key_and_nested_mutation_are_contract_errors():
    candidate = _expected()
    with pytest.raises(DockerControlContractErrorV1):
        DockerExpectedCreatePublishRequestV1.build(
            "f" * 64, candidate.content.labels.digest, candidate
        )
    request = _publish_request(candidate)
    object.__setattr__(candidate.content.labels, "effect_id", "changed")
    with pytest.raises(DockerControlContractErrorV1):
        InMemoryDockerControlStoreV1().publish_once(request)


def test_mutation_admit_lookup_and_cas_converge():
    store = InMemoryDockerControlStoreV1()
    admitted = _auth_record()
    request = DockerMutationAdmissionRequestV1.build(
        admitted.content.operation_id, admitted
    )
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _index: store.admit(request), range(32)))
    assert sum(
        item.disposition is DockerAdmissionDispositionV1.ADMITTED
        for item in results
    ) == 1
    lookup = store.lookup(admitted.content.operation_id)
    assert lookup.disposition is DockerMutationLookupDispositionV1.FOUND
    assert lookup.record == admitted and lookup.record is not admitted

    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, admitted.content.record_digest
    )
    cas = DockerMutationCASRequestV1.build(
        admitted.content.operation_id, admitted, attempted
    )
    with ThreadPoolExecutor(max_workers=16) as pool:
        changes = list(pool.map(
            lambda _index: store.compare_and_swap(cas), range(32)
        ))
    assert sum(
        item.disposition is DockerCASDispositionV1.APPLIED for item in changes
    ) == 1
    assert all(item.record == attempted for item in changes)


def test_mutation_admission_conflict_retains_first_intent():
    store = InMemoryDockerControlStoreV1()
    admitted = _auth_record()
    first_request = DockerMutationAdmissionRequestV1.build(
        admitted.content.operation_id, admitted
    )
    assert store.admit(first_request).disposition is DockerAdmissionDispositionV1.ADMITTED
    content = admitted.content
    conflict_content = DockerMutationRecordV1.build(
        operation_id=content.operation_id, operation=content.operation,
        effect_id=content.effect_id, control_intent_proof_digest="f" * 64,
        phase=content.phase, revision=content.revision,
        attempt_count=content.attempt_count, previous_record_digest=None,
        container_ref=None, verification_result_digest=None,
    )
    conflict = AuthenticatedDockerMutationRecordV1(
        conflict_content, admitted.authority_ref, admitted.key_ref, admitted.tag
    )
    result = store.admit(DockerMutationAdmissionRequestV1.build(
        content.operation_id, conflict
    ))
    assert result.disposition is DockerAdmissionDispositionV1.CONFLICT
    assert result.record == admitted


def test_missing_lookup_and_cas_are_nonmutating_and_invalid_inputs_propagate():
    store = InMemoryDockerControlStoreV1()
    admitted = _auth_record()
    attempted = _auth_record(
        DockerMutationPhaseV1.ATTEMPTED, admitted.content.record_digest
    )
    cas = DockerMutationCASRequestV1.build(
        admitted.content.operation_id, admitted, attempted
    )
    assert store.compare_and_swap(cas).disposition is DockerCASDispositionV1.INDETERMINATE
    assert store.lookup(admitted.content.operation_id).disposition is DockerMutationLookupDispositionV1.ABSENT
    with pytest.raises(DockerControlContractErrorV1):
        store.lookup("invalid")
    with pytest.raises(DockerControlContractErrorV1):
        store.publish_once(object())


def test_stage_store_authenticates_snapshots_and_converges_concurrently(
    mount_env,
):
    authority = mount_env["stage_authority"]
    candidate = authority.issue(mount_env["stage_record"])
    store = InMemoryDockerStageBundleStoreV1(authority=authority)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(
            lambda _index: store.put_if_absent(candidate), range(32)
        ))
    assert all(value == candidate for value in results)
    assert all(value is not candidate for value in results)
    assert all(
        value.content.effect_identity is not candidate.content.effect_identity
        for value in results
    )
    assert len({value.content.record_digest for value in results}) == 1
    returned = store.get_by_stage_effect_id(
        candidate.content.stage_effect_id
    )
    assert returned == candidate and returned is not candidate
    object.__setattr__(returned.content, "source_ref", "hostile-source")
    assert store.get_by_stage_effect_id(
        candidate.content.stage_effect_id
    ) == candidate
    assert store.get_by_stage_effect_id("unknown-stage-effect") is None


def test_stage_store_rejects_unauthenticated_and_conflicting_candidates(
    mount_env,
):
    candidate = mount_env["stage_authority"].issue(mount_env["stage_record"])

    class ExactEnvelopeAuthority:
        authority_ref = candidate.authority_ref
        key_ref = candidate.key_ref

        def authenticate(self, value):
            if (
                type(value) is not AuthenticatedDockerStageBundleBindingV1
                or value.authority_ref != self.authority_ref
                or value.key_ref != self.key_ref
            ):
                return None
            return AuthenticatedDockerStageBundleBindingV1(
                replace(value.content), value.authority_ref,
                value.key_ref, value.tag,
            )

    store = InMemoryDockerStageBundleStoreV1(
        authority=ExactEnvelopeAuthority()
    )
    assert store.put_if_absent(candidate) == candidate
    conflict = AuthenticatedDockerStageBundleBindingV1(
        candidate.content, candidate.authority_ref,
        candidate.key_ref, "f" * 64,
    )
    with pytest.raises(DockerHostSourceErrorV1):
        store.put_if_absent(conflict)
    with pytest.raises(DockerHostSourceErrorV1):
        store.put_if_absent(object())
    with pytest.raises(DockerHostSourceErrorV1):
        store.get_by_stage_effect_id("")
    assert "record_entries=1" in repr(store)


def test_stage_store_uses_untouched_baseline_before_publication(mount_env):
    candidate = mount_env["stage_authority"].issue(mount_env["stage_record"])

    class MutatingAuthority:
        authority_ref = candidate.authority_ref
        key_ref = candidate.key_ref

        def authenticate(self, value):
            object.__setattr__(value.content, "source_ref", "hostile-source")
            return value

    store = InMemoryDockerStageBundleStoreV1(
        authority=MutatingAuthority()
    )
    with pytest.raises(DockerHostSourceErrorV1):
        store.put_if_absent(candidate)
    assert "record_entries=0" in repr(store)
    assert store.get_by_stage_effect_id(
        candidate.content.stage_effect_id
    ) is None


def test_stage_store_lost_outbound_return_retains_recoverable_baseline(
    mount_env,
):
    candidate = mount_env["stage_authority"].issue(mount_env["stage_record"])

    class LoseSecondReturnAuthority:
        authority_ref = candidate.authority_ref
        key_ref = candidate.key_ref

        def __init__(self):
            self.calls = 0
            self.lose_second = True

        def authenticate(self, value):
            self.calls += 1
            if self.lose_second and self.calls == 2:
                return None
            return deepcopy(value)

    authority = LoseSecondReturnAuthority()
    store = InMemoryDockerStageBundleStoreV1(authority=authority)
    with pytest.raises(DockerHostSourceErrorV1):
        store.put_if_absent(candidate)
    assert "record_entries=1" in repr(store)
    authority.lose_second = False
    recovered = store.get_by_stage_effect_id(
        candidate.content.stage_effect_id
    )
    assert recovered == candidate and recovered is not candidate
    assert recovered.content is not candidate.content
