from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256

import pytest

from tuner.execution.providers.docker_provider_v1.model import (
    DockerStartDispositionV1,
)
from synaptic_host.bundle_io_v1.model import digest_v1
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerExpectedCreateBindingV1,
    AuthenticatedDockerMutationRecordV1,
    DockerControlContractErrorV1, DockerControlIntentV1,
    DockerControlOperationV1, DockerExpectedCreatePublishRequestV1,
    DockerMutationAdmissionRequestV1, DockerMutationCASRequestV1,
    DockerMutationPhaseV1, DockerMutationRecordV1,
    DockerStartVerificationV1, docker_operation_id_v1,
)
from synaptic_host.docker_v1.control_model import (
    DockerContainerInspectResultV1, DockerContainerStatusV1,
    DockerStartExecutionResultV1,
    docker_start_execution_request_digest_v1,
)
from synaptic_host.docker_v1.memory import InMemoryDockerControlStoreV1
from synaptic_host.docker_v1.model import (
    DockerCLICommandV1, DockerCLIOutcomeV1, DockerCLIResultV1,
    DockerCLIVerbV1,
)
from synaptic_host.docker_v1.start import DockerHostStartV1

from .test_control import _one_id_fixture, _evidence, _rebuilt_container_result


SHA = "a" * 64


class Authority:
    authority_ref = "authority"
    key_ref = "key"

    def issue(self, content):
        if type(content) is DockerControlIntentV1:
            return AuthenticatedDockerControlIntentV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        if type(content) is DockerMutationRecordV1:
            return AuthenticatedDockerMutationRecordV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        raise AssertionError("unexpected issue")

    def authenticate(self, value):
        return value


def _record(authority, intent, phase, previous=None, container_ref=None):
    matrix = {
        DockerMutationPhaseV1.ADMITTED: (1, 0),
        DockerMutationPhaseV1.ATTEMPTED: (2, 1),
        DockerMutationPhaseV1.VERIFIED: (3, 1),
    }
    revision, attempts = matrix[phase]
    content = DockerMutationRecordV1.build(
        operation_id=intent.content.operation_id,
        operation=intent.content.operation,
        effect_id=intent.content.effect_id,
        control_intent_proof_digest=intent.proof_digest,
        phase=phase, revision=revision, attempt_count=attempts,
        previous_record_digest=previous,
        container_ref=container_ref,
        verification_result_digest=(SHA if phase is DockerMutationPhaseV1.VERIFIED else None),
    )
    return authority.issue(content)


def _seed_store(store, authority, expected, ref):
    store.publish_once(DockerExpectedCreatePublishRequestV1.build(
        expected.content.labels.command_digest,
        expected.content.labels.digest, expected,
    ))
    intent = expected.content.intent
    admitted = _record(authority, intent, DockerMutationPhaseV1.ADMITTED)
    store.admit(DockerMutationAdmissionRequestV1.build(
        admitted.content.operation_id, admitted
    ))
    attempted = _record(
        authority, intent, DockerMutationPhaseV1.ATTEMPTED,
        admitted.content.record_digest,
    )
    store.compare_and_swap(DockerMutationCASRequestV1.build(
        admitted.content.operation_id, admitted, attempted
    ))
    verified = _record(
        authority, intent, DockerMutationPhaseV1.VERIFIED,
        attempted.content.record_digest, ref,
    )
    store.compare_and_swap(DockerMutationCASRequestV1.build(
        attempted.content.operation_id, attempted, verified
    ))
    return verified


class TypedRunner:
    def __init__(self, created, started, *, mode="success"):
        self.created = created
        self.started = started
        self.mode = mode
        self.start_calls = 0
        self.inspect_calls = 0

    def inspect_container(self, _ref):
        self.inspect_calls += 1
        return self.created if self.inspect_calls == 1 else self.started

    def start_container(self, command, ref):
        self.start_calls += 1
        if self.mode in ("raise", "lost"):
            raise RuntimeError("raw-secret-start")
        outcome = (
            DockerCLIOutcomeV1.NONZERO_EXIT
            if self.mode == "nonzero" else DockerCLIOutcomeV1.SUCCESS
        )
        evidence = _evidence(command, outcome)
        request = docker_start_execution_request_digest_v1(
            ref, command.command_digest
        )
        return DockerStartExecutionResultV1.build(
            ref, request, command, evidence
        )


def _harness(*, mode="success", already_started=False, post_started=True):
    labels, ref, _, expected, running = _one_id_fixture()
    _, _, _, _, created = _one_id_fixture(
        status=DockerContainerStatusV1.CREATED
    )
    post = running if post_started else created
    pre = running if already_started else created
    authority = Authority()
    store = InMemoryDockerControlStoreV1()
    _seed_store(store, authority, expected, ref)
    runner = TypedRunner(pre, post, mode=mode)
    host = DockerHostStartV1(
        typed_runner=runner, mutation_repository=store,
        expected_catalog=store, expected_authority=authority,
        intent_authority=authority, environment_authority=authority,
        record_authority=authority,
    )
    return host, runner, store, labels, ref


def test_start_verification_nullable_execution_digest_and_mutation():
    values = dict(
        operation_id=SHA, attempted_record_digest=SHA,
        expected_proof_digest=SHA, verified_create_record_digest=SHA,
        start_execution_result_digest=None,
        pre_inspect_result_digest=SHA, post_inspect_result_digest=SHA,
        container_ref="1" * 64,
    )
    absent = DockerStartVerificationV1.build(**values)
    present = DockerStartVerificationV1.build(
        **(values | {"start_execution_result_digest": "b" * 64})
    )
    assert absent.verification_digest != present.verification_digest
    with pytest.raises(DockerControlContractErrorV1):
        replace(absent, container_ref="2" * 64)


def test_start_happy_path_only_post_inspection_proves_and_retry_zero_effect():
    host, runner, _store, labels, ref = _harness()
    first = host.start_once(ref, labels)
    assert first.disposition is DockerStartDispositionV1.STARTED
    assert runner.start_calls == 1
    runner.inspect_calls = 0
    runner.created = runner.started
    second = host.start_once(ref, labels)
    assert second.disposition is DockerStartDispositionV1.STARTED
    assert runner.start_calls == 1


def test_start_bounds_reinspection_for_delayed_running_visibility():
    host, runner, _store, labels, ref = _harness()

    def delayed_inspect(_ref):
        runner.inspect_calls += 1
        return runner.created if runner.inspect_calls <= 2 else runner.started

    runner.inspect_container = delayed_inspect
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.STARTED
    assert runner.start_calls == 1
    assert runner.inspect_calls == 3


@pytest.mark.parametrize("mode", ("success", "nonzero", "raise", "lost"))
def test_start_typed_result_never_substitutes_for_post_inspection(mode):
    host, runner, _store, labels, ref = _harness(
        mode=mode, post_started=False
    )
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 1


@pytest.mark.parametrize("mode", ("raise", "lost", "nonzero"))
def test_start_post_inspection_can_prove_lost_or_nonzero_effect(mode):
    host, runner, _store, labels, ref = _harness(mode=mode)
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.STARTED
    assert runner.start_calls == 1


def test_start_already_started_records_null_execution_and_zero_effect():
    host, runner, _store, labels, ref = _harness(already_started=True)
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.STARTED
    assert runner.start_calls == 0


def test_start_invalid_ref_and_labels_fail_before_dependencies():
    host, runner, _store, labels, _ref = _harness()
    result = host.start_once("A" * 64, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.inspect_calls == 0 and runner.start_calls == 0


@pytest.mark.parametrize("attack", ("config", "label", "environment", "mount"))
def test_start_exact_create_projection_mismatch_is_collision_before_mutation(attack):
    host, runner, store, labels, ref = _harness()
    runner.created = _rebuilt_container_result(runner.created, attack)
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.COLLISION
    assert runner.start_calls == 0
    lookup = store.lookup(docker_operation_id_v1(
        DockerControlOperationV1.START, labels.effect_id
    ))
    assert lookup.record is None


def test_existing_attempted_with_created_state_never_retries_start():
    host, runner, _store, labels, ref = _harness(post_started=False)
    assert host.start_once(ref, labels).disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 1
    runner.start_calls = 0
    runner.inspect_calls = 0
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 0


@pytest.mark.parametrize("role", ("expected", "intent", "environment", "record"))
def test_start_post_construction_authority_pin_swap_fails_closed(role):
    host, runner, _store, labels, ref = _harness()
    authority = getattr(host, "_" + role + "_authority")
    authority.authority_ref = "changed"
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 0
    del authority.authority_ref


@pytest.mark.parametrize("role", ("expected", "intent", "environment", "record"))
def test_start_rejects_same_pin_alternate_authority_object_with_zero_effect(role):
    host, runner, _store, labels, ref = _harness()
    alternate = Authority()
    setattr(host, "_" + role + "_authority", alternate)
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 0


class MidCallSwapAuthority(Authority):
    def __init__(self, role, swap_on):
        self.role = role
        self.swap_on = swap_on
        self.host = None

    def _swap(self):
        setattr(self.host, "_" + self.role + "_authority", Authority())

    def authenticate(self, value):
        if self.swap_on == "authenticate":
            self._swap()
        return value

    def issue(self, content):
        result = super().issue(content)
        if self.swap_on == "issue":
            self._swap()
        return result


@pytest.mark.parametrize("role", ("expected", "intent", "environment", "record"))
def test_start_rejects_mid_auth_role_object_swap_with_zero_effect(role):
    _host, runner, store, labels, ref = _harness()
    authority = MidCallSwapAuthority(role, "authenticate")
    roots = {name: (authority if name == role else Authority()) for name in (
        "expected", "intent", "environment", "record"
    )}
    host = DockerHostStartV1(
        typed_runner=runner, mutation_repository=store, expected_catalog=store,
        expected_authority=roots["expected"], intent_authority=roots["intent"],
        environment_authority=roots["environment"],
        record_authority=roots["record"],
    )
    authority.host = host
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 0


@pytest.mark.parametrize("role", ("intent", "record"))
def test_start_rejects_mid_issue_role_object_swap_with_zero_effect(role):
    _host, runner, store, labels, ref = _harness()
    authority = MidCallSwapAuthority(role, "issue")
    roots = {name: (authority if name == role else Authority()) for name in (
        "expected", "intent", "environment", "record"
    )}
    host = DockerHostStartV1(
        typed_runner=runner, mutation_repository=store, expected_catalog=store,
        expected_authority=roots["expected"], intent_authority=roots["intent"],
        environment_authority=roots["environment"],
        record_authority=roots["record"],
    )
    authority.host = host
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.INDETERMINATE
    assert runner.start_calls == 0


class LostCASRepository:
    def __init__(self, store, phase):
        self.store = store
        self.phase = phase

    def lookup(self, operation_id):
        return self.store.lookup(operation_id)

    def admit(self, request):
        return self.store.admit(request)

    def compare_and_swap(self, request):
        result = self.store.compare_and_swap(request)
        if request.replacement.content.phase is self.phase:
            raise RuntimeError("raw-secret-lost-cas")
        return result


@pytest.mark.parametrize(
    "phase", (DockerMutationPhaseV1.ATTEMPTED, DockerMutationPhaseV1.VERIFIED)
)
def test_start_lost_cas_converges_only_from_durable_state(phase):
    host, runner, store, labels, ref = _harness(
        already_started=(phase is DockerMutationPhaseV1.ATTEMPTED)
    )
    host._repository = LostCASRepository(store, phase)
    result = host.start_once(ref, labels)
    assert result.disposition is DockerStartDispositionV1.STARTED
    if phase is DockerMutationPhaseV1.ATTEMPTED:
        assert runner.start_calls == 0
    final = store.lookup(docker_operation_id_v1(
        DockerControlOperationV1.START, labels.effect_id
    ))
    assert final.record.content.phase is DockerMutationPhaseV1.VERIFIED


def test_32_hosts_shared_store_issue_exactly_one_start_and_converge():
    host, runner, store, labels, ref = _harness()
    authority = Authority()
    hosts = [DockerHostStartV1(
        typed_runner=runner, mutation_repository=store,
        expected_catalog=store, expected_authority=authority,
        intent_authority=authority, environment_authority=authority,
        record_authority=authority,
    ) for _ in range(32)]
    with ThreadPoolExecutor(max_workers=32) as pool:
        results = list(pool.map(lambda item: item.start_once(ref, labels), hosts))
    assert runner.start_calls == 1
    assert all(
        result.disposition is DockerStartDispositionV1.STARTED
        for result in results
    )
    final = store.lookup(docker_operation_id_v1(
        DockerControlOperationV1.START, labels.effect_id
    ))
    assert final.record.content.phase is DockerMutationPhaseV1.VERIFIED
