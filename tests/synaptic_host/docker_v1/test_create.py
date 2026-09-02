from dataclasses import replace
from types import SimpleNamespace

import pytest
import synaptic_host.docker_v1.create as create_module

from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCreateDispositionV1, DockerImageV1, DockerLabelsV1, DockerRuntimeV1,
    DockerWorkloadV1,
    DockerLookupDispositionV1, DockerLookupPurposeV1, DockerLookupRequestV1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerCreatePathBindingV1,
    AuthenticatedDockerControlIntentV1,
    AuthenticatedDockerExpectedCreateBindingV1,
    AuthenticatedDockerMutationRecordV1,
    DockerAdmissionDispositionV1, DockerAdmissionResultV1,
    DockerCASDispositionV1, DockerCASResultV1,
    DockerControlContractErrorV1, DockerCreateVerificationV1,
    DockerCreateAdmissionV1,
    DockerExpectedCreatePublishDispositionV1,
    DockerExpectedCreatePublishResultV1,
    DockerMutationAdmissionRequestV1, DockerMutationCASRequestV1,
    DockerMutationLookupDispositionV1, DockerMutationLookupResultV1,
    DockerMutationPhaseV1, DockerMutationRecordV1,
    authenticate_control_intent_v1, authenticate_create_path_binding_v1,
    authenticate_expected_create_binding_v1, authenticate_mutation_record_v1,
    authenticate_workload_environment_binding_v1,
    docker_arguments_projection_digest_v1,
)
from synaptic_host.docker_v1.create import DockerHostCreateV1
from synaptic_host.docker_v1.model import DockerCLICommandV1, DockerCLIVerbV1
from synaptic_host.docker_v1.model import DockerCLIOutcomeV1
from synaptic_host.docker_v1.control_model import (
    DockerContainerInspectResultV1, DockerCreateExecutionResultV1,
    docker_create_execution_request_digest_v1,
)
from synaptic_host.docker_v1.verification import (
    docker_create_projection_matches_v1,
)

from .test_control import (
    Catalog, Repository as LookupRepository, TypedCLI, _control,
    _evidence, _inventory_result, _one_id_fixture,
    _rebuilt_container_result,
)
from .test_control_contract import _path_binding, _sanitized_create_result


SHA = "a" * 64


class Authority:
    authority_ref = "authority"
    key_ref = "key"
    def issue(self, value):
        raise AssertionError("invalid preflight reached issue")
    def authenticate(self, value):
        return value


class Never:
    def __getattr__(self, _name):
        raise AssertionError("invalid preflight reached dependency")


def _host():
    authority = Authority()
    never = Never()
    return DockerHostCreateV1(
        mount_resolver=never, path_binder=never, path_translator=never,
        environment_resolver=never, typed_runner=never,
        expected_publisher=never, mutation_repository=never,
        path_authority=authority, environment_authority=authority,
        intent_authority=authority, expected_authority=authority,
        record_authority=authority,
        endpoint_descriptor_digest=SHA, cli_policy_digest=SHA,
    )


def test_create_invalid_input_is_indeterminate_before_any_dependency():
    result = _host().create_once(
        labels=object(), image=object(), runtime=object(), workload=object(),
        source_ref="source", artifact_ref="artifact",
        working_directory="/artifacts/tmp",
    )
    assert result.disposition is DockerCreateDispositionV1.INDETERMINATE


def _preflight_capture(monkeypatch, *, arguments=("x",)):
    labels, _ref, _record, expected, _inspected = _one_id_fixture()
    specification = expected.content.create_specification
    host = object.__new__(DockerHostCreateV1)
    resolved = SimpleNamespace(
        resolution_digest=SHA, source_wsl_private_path="/source",
        artifact_wsl_root="/artifacts", source_read_only=True,
    )
    path_content = SimpleNamespace(
        labels_digest=labels.digest, source_ref="source",
        artifact_ref="artifact", mount_resolution_digest=SHA,
        source_request=SimpleNamespace(posix_path="/source"),
        artifact_request=SimpleNamespace(posix_path="/artifacts"),
    )
    path_binding = SimpleNamespace(content=path_content, proof_digest=SHA)
    object.__setattr__(host, "_resolve", lambda *_args: resolved)
    object.__setattr__(host, "_path_binder", SimpleNamespace(
        bind=lambda *_args: path_binding
    ))
    object.__setattr__(host, "_auth", lambda _r, _a, value, _f: value)
    object.__setattr__(host, "_path_authority", object())
    object.__setattr__(host, "_environment_authority", object())
    object.__setattr__(host, "_translate", lambda request: SimpleNamespace(
        unc_path=("source-unc" if request is path_content.source_request
                  else "artifact-unc"),
        path_digest=SHA,
    ))
    private_environment = SimpleNamespace(
        authenticated_binding_snapshot=lambda _authority:
            expected.content.environment_binding
    )
    object.__setattr__(host, "_environment_resolver", SimpleNamespace(
        resolve=lambda _workload: private_environment
    ))
    object.__setattr__(host, "_intent_authority", object())
    object.__setattr__(host, "_expected_authority", object())
    object.__setattr__(host, "_endpoint_descriptor_digest", SHA)
    object.__setattr__(host, "_cli_policy_digest", SHA)

    captured = {}

    class InvocationFactory:
        def build(self, **kwargs):
            captured["invocation"] = kwargs
            return SimpleNamespace(command_digest=SHA)

    class Stop(RuntimeError):
        pass

    def capture_specification(**kwargs):
        captured["specification"] = kwargs
        raise Stop

    monkeypatch.setattr(
        create_module, "DockerPrivateCreateInvocationFactoryV1",
        InvocationFactory,
    )
    monkeypatch.setattr(
        create_module.DockerCreateSpecificationV1, "build",
        capture_specification,
    )
    with pytest.raises(Stop):
        host._preflight(
            labels, SimpleNamespace(image_digest=specification.image_digest),
            SimpleNamespace(
                cpu_count=1, memory_bytes=1024,
                accelerator_devices=AcceleratorDeviceRequestV1("cpu", (), ()),
                digest=SHA,
            ),
            SimpleNamespace(arguments=arguments, workload_digest=SHA),
            "source", "artifact", "/artifacts/tmp",
        )
    return captured


def test_preflight_keeps_raw_workdir_private_and_seals_only_digest(monkeypatch):
    captured = _preflight_capture(monkeypatch)
    assert captured["invocation"]["working_directory"] == "/artifacts/tmp"
    assert "working_directory_digest" not in captured["invocation"]
    assert captured["specification"]["working_directory_digest"] == (
        __import__("hashlib").sha256(b"/artifacts/tmp").hexdigest()
    )
    assert "working_directory" not in captured["specification"]


def test_preflight_specification_still_counts_and_digests_the_whole_argv(
    monkeypatch,
):
    # B-4 (architecture section 17.7): the create argv gains the
    # "--entrypoint env" pair, but the specification is built over
    # workload.arguments, so argument_count and arguments_digest do not move.
    # verification.py compares these against Config.Cmd from docker inspect,
    # which is still the complete workload argv.
    arguments = ("/opt/conda/bin/python3", "train.py", "--epochs", "1")
    captured = _preflight_capture(monkeypatch, arguments=arguments)
    assert captured["specification"]["argument_count"] == len(arguments)
    assert captured["specification"]["arguments_digest"] == (
        docker_arguments_projection_digest_v1(arguments)
    )
    assert captured["invocation"]["workload"].arguments == arguments


def test_shared_verifier_accepts_exact_fixture_and_rejects_config_drift():
    labels, ref, _record, expected, inspected = _one_id_fixture()
    environment = expected.content.environment_binding
    assert docker_create_projection_matches_v1(
        labels, expected, environment, inspected.projection, ref,
        inspected.evidence,
    )
    drifted = inspected.projection
    object.__setattr__(drifted, "memory_bytes", 2048)
    assert not docker_create_projection_matches_v1(
        labels, expected, environment, drifted, ref, inspected.evidence
    )

    labels, ref, _record, expected, inspected = _one_id_fixture()
    object.__setattr__(
        inspected.projection, "working_directory_digest", "e" * 64
    )
    assert not docker_create_projection_matches_v1(
        labels, expected, expected.content.environment_binding,
        inspected.projection, ref, inspected.evidence,
    )


def test_create_verification_is_self_digested_and_rejects_mutation():
    values = dict(
        operation_id=SHA, attempted_record_digest=SHA,
        expected_proof_digest=SHA, create_result_digest=None,
        inventory_result_digest=SHA, post_resolution_digest=SHA,
        post_path_binding_proof_digest=SHA,
        source_windows_path_digest=SHA, source_unc_digest=SHA,
        artifact_windows_path_digest=SHA, artifact_unc_digest=SHA,
        inspect_result_digest=SHA, container_ref="1" * 64,
    )
    verification = DockerCreateVerificationV1.build(**values)
    with pytest.raises(DockerControlContractErrorV1):
        replace(verification, container_ref="2" * 64)


class RecordAuthority:
    authority_ref = "authority"
    key_ref = "key"
    def issue(self, content):
        return AuthenticatedDockerMutationRecordV1(
            content, self.authority_ref, self.key_ref, SHA
        )
    def authenticate(self, value):
        return value


def _record(expected, phase, previous=None, container_ref=None):
    labels = expected.content.labels
    intent = expected.content.intent
    matrix = {
        DockerMutationPhaseV1.ADMITTED: (1, 0),
        DockerMutationPhaseV1.ATTEMPTED: (2, 1),
        DockerMutationPhaseV1.VERIFIED: (3, 1),
    }
    revision, attempts = matrix[phase]
    content = DockerMutationRecordV1.build(
        operation_id=intent.content.operation_id,
        operation=intent.content.operation, effect_id=labels.effect_id,
        control_intent_proof_digest=intent.proof_digest, phase=phase,
        revision=revision, attempt_count=attempts,
        previous_record_digest=previous, container_ref=container_ref,
        verification_result_digest=(SHA if phase is DockerMutationPhaseV1.VERIFIED else None),
    )
    return AuthenticatedDockerMutationRecordV1(content, "authority", "key", SHA)


class Publisher:
    def __init__(self, events, disposition, cross_request=False):
        self.events = events
        self.disposition = disposition
        self.cross_request = cross_request
    def publish_once(self, request):
        self.events.append("publish")
        if self.disposition == "raise":
            raise RuntimeError("raw-secret-publish")
        if self.cross_request:
            other = DockerExpectedCreatePublishRequestV1.build(
                OTHER_LABELS.command_digest, OTHER_LABELS.digest,
                OTHER_EXPECTED,
            )
            if self.cross_request == "mutate":
                for name in other.__dataclass_fields__:
                    object.__setattr__(request, name, getattr(other, name))
                other = request
            return DockerExpectedCreatePublishResultV1.build(
                other, DockerExpectedCreatePublishDispositionV1.PUBLISHED,
                OTHER_EXPECTED,
            )
        if self.disposition is DockerExpectedCreatePublishDispositionV1.INDETERMINATE:
            binding = None
        elif self.disposition is DockerExpectedCreatePublishDispositionV1.CONFLICT:
            binding = AuthenticatedDockerExpectedCreateBindingV1(
                request.candidate.content, request.candidate.authority_ref,
                request.candidate.key_ref, "b" * 64,
            )
        else:
            binding = request.candidate
        return DockerExpectedCreatePublishResultV1.build(
            request, self.disposition, binding
        )


class Repository:
    def __init__(self, events, *, existing_phase=None,
                 attempt_disposition=DockerCASDispositionV1.APPLIED,
                 final_disposition=DockerCASDispositionV1.APPLIED,
                 admission_disposition=DockerAdmissionDispositionV1.ADMITTED,
                 raise_at=None, final_lookup=False, cross_at=None):
        self.events = events
        self.existing_phase = existing_phase
        self.attempt_disposition = attempt_disposition
        self.final_disposition = final_disposition
        self.admission_disposition = admission_disposition
        self.raise_at = raise_at
        self.final_lookup = final_lookup
        self.cross_at = cross_at
        self.latest_verified = None
    def admit(self, request):
        self.events.append("admit")
        if self.raise_at == "admit":
            raise RuntimeError("raw-secret-admit")
        if self.cross_at in ("admit", "mutate_admit"):
            other = _record(OTHER_EXPECTED, DockerMutationPhaseV1.ADMITTED)
            other_request = DockerMutationAdmissionRequestV1.build(
                other.content.operation_id, other
            )
            if self.cross_at == "mutate_admit":
                for name in other_request.__dataclass_fields__:
                    object.__setattr__(request, name, getattr(other_request, name))
                other_request = request
            return DockerAdmissionResultV1.build(
                other_request, DockerAdmissionDispositionV1.ADMITTED, other
            )
        record = request.candidate
        disposition = self.admission_disposition
        if self.latest_verified is not None:
            record = self.latest_verified
            disposition = DockerAdmissionDispositionV1.EXISTING
        elif self.existing_phase is not None:
            if self.existing_phase is DockerMutationPhaseV1.ADMITTED:
                record = request.candidate
            elif self.existing_phase is DockerMutationPhaseV1.ATTEMPTED:
                record = _record(
                    HARNESS_EXPECTED, self.existing_phase,
                    request.candidate.content.record_digest,
                )
            else:
                attempted = _record(
                    HARNESS_EXPECTED, DockerMutationPhaseV1.ATTEMPTED,
                    request.candidate.content.record_digest,
                )
                record = _record(
                    HARNESS_EXPECTED, DockerMutationPhaseV1.VERIFIED,
                    attempted.content.record_digest, HARNESS_REF,
                )
            disposition = DockerAdmissionDispositionV1.EXISTING
        if disposition is DockerAdmissionDispositionV1.CONFLICT:
            content = request.candidate.content
            changed = DockerMutationRecordV1.build(
                operation_id=content.operation_id, operation=content.operation,
                effect_id=content.effect_id,
                control_intent_proof_digest="f" * 64,
                phase=content.phase, revision=content.revision,
                attempt_count=content.attempt_count,
                previous_record_digest=None, container_ref=None,
                verification_result_digest=None,
            )
            record = AuthenticatedDockerMutationRecordV1(
                changed, "authority", "key", SHA
            )
        return DockerAdmissionResultV1.build(request, disposition, (
            None if disposition is DockerAdmissionDispositionV1.INDETERMINATE else record
        ))
    def compare_and_swap(self, request):
        phase = request.replacement.content.phase
        self.events.append("attempt_cas" if phase is DockerMutationPhaseV1.ATTEMPTED else "final_cas")
        boundary = "attempt_cas" if phase is DockerMutationPhaseV1.ATTEMPTED else "final_cas"
        if self.cross_at in (boundary, "mutate_" + boundary):
            other_admitted = _record(OTHER_EXPECTED, DockerMutationPhaseV1.ADMITTED)
            other_attempted = _record(
                OTHER_EXPECTED, DockerMutationPhaseV1.ATTEMPTED,
                other_admitted.content.record_digest,
            )
            if phase is DockerMutationPhaseV1.ATTEMPTED:
                other_request = DockerMutationCASRequestV1.build(
                    other_admitted.content.operation_id,
                    other_admitted, other_attempted,
                )
                returned = other_attempted
            else:
                other_verified = _record(
                    OTHER_EXPECTED, DockerMutationPhaseV1.VERIFIED,
                    other_attempted.content.record_digest, HARNESS_REF,
                )
                other_request = DockerMutationCASRequestV1.build(
                    other_attempted.content.operation_id,
                    other_attempted, other_verified,
                )
                returned = other_verified
            if self.cross_at == "mutate_" + boundary:
                for name in other_request.__dataclass_fields__:
                    object.__setattr__(request, name, getattr(other_request, name))
                other_request = request
            return DockerCASResultV1.build(
                other_request, DockerCASDispositionV1.APPLIED, returned
            )
        if (
            phase is DockerMutationPhaseV1.VERIFIED
            and self.raise_at == "final_cas" and self.final_lookup
        ):
            self.latest_verified = request.replacement
        if self.raise_at == ("attempt_cas" if phase is DockerMutationPhaseV1.ATTEMPTED else "final_cas"):
            raise RuntimeError("raw-secret-cas")
        disposition = self.attempt_disposition if phase is DockerMutationPhaseV1.ATTEMPTED else self.final_disposition
        if phase is DockerMutationPhaseV1.VERIFIED:
            self.latest_verified = request.replacement
        if disposition is DockerCASDispositionV1.APPLIED:
            record = request.replacement
        elif disposition is DockerCASDispositionV1.CURRENT:
            record = request.replacement
        else:
            record = None
        return DockerCASResultV1.build(request, disposition, record)
    def lookup(self, operation_id):
        self.events.append("lookup")
        record = self.latest_verified if self.final_lookup else None
        return DockerMutationLookupResultV1.build(
            operation_id,
            (DockerMutationLookupDispositionV1.FOUND if record else DockerMutationLookupDispositionV1.ABSENT),
            record,
        )


class Invocation:
    def __init__(self, events, mode="success"):
        self.events = events
        self.mode = mode
        self.calls = 0
    def execute_once(self, _runner):
        self.events.append("create")
        self.calls += 1
        if self.mode == "raise":
            raise RuntimeError("raw-secret-create")
        command = DockerCLICommandV1.build(DockerCLIVerbV1.PS)
        if self.mode == "nonzero":
            request = docker_create_execution_request_digest_v1(
                HARNESS_LABELS.container_name, command.command_digest
            )
            return DockerCreateExecutionResultV1.build(
                HARNESS_LABELS.container_name, request,
                command.command_digest,
                _evidence(command, DockerCLIOutcomeV1.NONZERO_EXIT), None,
            )
        return _sanitized_create_result(
            command, HARNESS_LABELS.container_name,
            ("2" * 64 if self.mode == "mismatch" else HARNESS_REF),
        )


class TypedRunner:
    def __init__(self, events, inventory_count=1, inspect_result=None):
        self.events = events
        self.inventory_count = inventory_count
        self.inspect_result = inspect_result or HARNESS_INSPECTED
    def inventory_exact_name(self, _name):
        self.events.append("inventory")
        refs = tuple(str(index + 1) * 64 for index in range(self.inventory_count))
        if self.inventory_count == 1:
            refs = (HARNESS_REF,)
        return _inventory_result(HARNESS_LABELS, refs)
    def inspect_container(self, _ref):
        self.events.append("inspect")
        return self.inspect_result


HARNESS_LABELS, HARNESS_REF, _, HARNESS_EXPECTED, HARNESS_INSPECTED = _one_id_fixture()
OTHER_LABELS = DockerLabelsV1(
    "f" * 64, HARNESS_LABELS.provider_id, HARNESS_LABELS.profile_ref,
    HARNESS_LABELS.account_ref, HARNESS_LABELS.namespace_ref,
    HARNESS_LABELS.project_ref, HARNESS_LABELS.run_id,
    HARNESS_LABELS.plan_fingerprint, HARNESS_LABELS.preparation_digest,
    "other-effect", "submit", HARNESS_LABELS.effect_identity_digest,
    HARNESS_LABELS.adapter_descriptor_digest,
)
_, _, _, OTHER_EXPECTED, _ = _one_id_fixture(labels=OTHER_LABELS)


def _transaction_host(*, publish=DockerExpectedCreatePublishDispositionV1.PUBLISHED,
                      existing_phase=None,
                      admission=DockerAdmissionDispositionV1.ADMITTED,
                      attempt=DockerCASDispositionV1.APPLIED,
                      final=DockerCASDispositionV1.APPLIED,
                      create_mode="success", inventory_count=1,
                      raise_at=None, final_lookup=False, inspect_result=None,
                      cross_at=None):
    events = []
    authority = RecordAuthority()
    invocation = Invocation(events, create_mode)
    repository = Repository(
        events, existing_phase=existing_phase,
        attempt_disposition=attempt, final_disposition=final,
        admission_disposition=admission, raise_at=raise_at,
        final_lookup=final_lookup, cross_at=cross_at,
    )
    typed = TypedRunner(events, inventory_count, inspect_result)
    never = Never()
    host = DockerHostCreateV1(
        mount_resolver=never, path_binder=never, path_translator=never,
        environment_resolver=never, typed_runner=typed,
        expected_publisher=Publisher(
            events, publish,
            ("mutate" if cross_at == "mutate_publish" else cross_at == "publish"),
        ),
        mutation_repository=repository, path_authority=authority,
        environment_authority=authority, intent_authority=authority,
        expected_authority=authority, record_authority=authority,
        endpoint_descriptor_digest=SHA, cli_policy_digest=SHA,
    )
    preflight = {
        "labels": HARNESS_LABELS,
        "image": DockerImageV1("image", HARNESS_EXPECTED.content.create_specification.image_digest),
        "runtime": DockerRuntimeV1(
            1, 1024, 60, AcceleratorDeviceRequestV1("cpu", (), ())
        ),
        "workload": DockerWorkloadV1(("x",), ("TOKEN",), SHA),
        "source_ref": "source", "artifact_ref": "artifact",
        "working_directory": "/artifacts/tmp",
        "resolved": SimpleNamespace(resolution_digest=SHA),
        "path_binding": SimpleNamespace(proof_digest=SHA),
        "source_path": SimpleNamespace(path_digest=SHA, unc_path="source-path"),
        "artifact_path": SimpleNamespace(path_digest=SHA, unc_path="artifact-path"),
        "environment": HARNESS_EXPECTED.content.environment_binding,
        "invocation": invocation,
        "specification": HARNESS_EXPECTED.content.create_specification,
        "operation_id": HARNESS_EXPECTED.content.intent.content.operation_id,
        "auth_intent": HARNESS_EXPECTED.content.intent,
        "expected": HARNESS_EXPECTED,
    }
    host._preflight = lambda *_args: preflight
    host._fixture_preflight = preflight
    return host, events, invocation


def _call(host):
    return host.create_once(
        labels=HARNESS_LABELS,
        image=DockerImageV1("image", HARNESS_EXPECTED.content.create_specification.image_digest),
        runtime=DockerRuntimeV1(
            1, 1024, 60, AcceleratorDeviceRequestV1("cpu", (), ())
        ),
        workload=DockerWorkloadV1(("x",), ("TOKEN",), SHA),
        source_ref="source", artifact_ref="artifact",
        working_directory="/artifacts/tmp",
    )


def _prepare_call(host):
    return host.prepare_admission(
        labels=HARNESS_LABELS,
        image=DockerImageV1(
            "image", HARNESS_EXPECTED.content.create_specification.image_digest
        ),
        runtime=DockerRuntimeV1(
            1, 1024, 60, AcceleratorDeviceRequestV1("cpu", (), ())
        ),
        workload=DockerWorkloadV1(("x",), ("TOKEN",), SHA),
        source_ref="source", artifact_ref="artifact",
        working_directory="/artifacts/tmp",
    )


def test_prepare_admission_is_effect_free_and_matches_create_candidate():
    host, events, invocation = _transaction_host()
    admission = _prepare_call(host)
    assert type(admission) is DockerCreateAdmissionV1
    assert admission.expected_create == HARNESS_EXPECTED
    assert admission.create_mutation == _record(
        HARNESS_EXPECTED, DockerMutationPhaseV1.ADMITTED
    )
    assert events == []
    assert invocation.calls == 0


def test_create_happy_path_has_exact_transaction_order_and_one_create():
    host, events, invocation = _transaction_host()
    result = _call(host)
    assert result.disposition is DockerCreateDispositionV1.CREATED
    assert events == [
        "publish", "admit", "attempt_cas", "create", "inventory",
        "inspect", "final_cas",
    ]
    assert invocation.calls == 1


def test_repeated_reconstructed_create_never_executes_second_create():
    host, events, invocation = _transaction_host()
    assert _call(host).disposition is DockerCreateDispositionV1.CREATED
    assert _call(host).disposition is DockerCreateDispositionV1.CREATED
    assert invocation.calls == 1
    assert events.count("create") == 1


@pytest.mark.parametrize(
    "kwargs,expected,calls",
    (
        ({"publish": DockerExpectedCreatePublishDispositionV1.INDETERMINATE}, DockerCreateDispositionV1.INDETERMINATE, 0),
        ({"publish": DockerExpectedCreatePublishDispositionV1.CONFLICT}, DockerCreateDispositionV1.COLLISION, 0),
        ({"admission": DockerAdmissionDispositionV1.INDETERMINATE}, DockerCreateDispositionV1.INDETERMINATE, 0),
        ({"admission": DockerAdmissionDispositionV1.CONFLICT}, DockerCreateDispositionV1.COLLISION, 0),
        ({"attempt": DockerCASDispositionV1.INDETERMINATE}, DockerCreateDispositionV1.CREATED, 0),
        ({"existing_phase": DockerMutationPhaseV1.ATTEMPTED}, DockerCreateDispositionV1.CREATED, 0),
        ({"existing_phase": DockerMutationPhaseV1.VERIFIED}, DockerCreateDispositionV1.CREATED, 0),
        ({"inventory_count": 0}, DockerCreateDispositionV1.INDETERMINATE, 1),
        ({"inventory_count": 2}, DockerCreateDispositionV1.COLLISION, 1),
    ),
)
def test_create_disposition_and_recovery_matrix(kwargs, expected, calls):
    host, _events, invocation = _transaction_host(**kwargs)
    assert _call(host).disposition is expected
    assert invocation.calls == calls


@pytest.mark.parametrize(
    "raise_at,expected",
    (
        ("admit", DockerCreateDispositionV1.INDETERMINATE),
        ("attempt_cas", DockerCreateDispositionV1.CREATED),
        ("final_cas", DockerCreateDispositionV1.INDETERMINATE),
    ),
)
def test_create_lost_dependency_returns_are_recovered_or_indeterminate(
    raise_at, expected,
):
    host, events, invocation = _transaction_host(raise_at=raise_at)
    result = _call(host)
    assert result.disposition is expected
    assert "raw-secret" not in repr(result)
    assert invocation.calls <= 1


def test_create_lost_final_cas_returns_created_only_via_exact_final_lookup():
    host, events, invocation = _transaction_host(
        raise_at="final_cas", final_lookup=True
    )
    assert _call(host).disposition is DockerCreateDispositionV1.CREATED
    assert events[-2:] == ["final_cas", "lookup"]
    assert invocation.calls == 1


@pytest.mark.parametrize(
    "mode,expected",
    (
        ("raise", DockerCreateDispositionV1.CREATED),
        ("nonzero", DockerCreateDispositionV1.COLLISION),
        ("mismatch", DockerCreateDispositionV1.COLLISION),
    ),
)
def test_create_result_outcomes_are_recovered_exactly(mode, expected):
    host, _events, invocation = _transaction_host(create_mode=mode)
    assert _call(host).disposition is expected
    assert invocation.calls == 1


@pytest.mark.parametrize("attack", ("config", "label", "environment", "mount"))
def test_create_exact_daemon_config_mismatch_is_collision(attack):
    inspected = _rebuilt_container_result(HARNESS_INSPECTED, attack)
    host, _events, _invocation = _transaction_host(inspect_result=inspected)
    assert _call(host).disposition is DockerCreateDispositionV1.COLLISION


@pytest.mark.parametrize(
    "field",
    ("resolved", "path_binding", "source_path", "artifact_path"),
)
def test_create_post_path_resolution_drift_is_indeterminate(field):
    host, _events, _invocation = _transaction_host()
    initial = host._fixture_preflight
    drifted = dict(initial)
    if field == "resolved":
        drifted[field] = SimpleNamespace(resolution_digest="f" * 64)
    elif field == "path_binding":
        drifted[field] = SimpleNamespace(proof_digest="f" * 64)
    else:
        original = initial[field]
        drifted[field] = SimpleNamespace(
            path_digest="f" * 64, unc_path=original.unc_path
        )
    calls = iter((initial, drifted))
    host._preflight = lambda *_args: next(calls)
    assert _call(host).disposition is DockerCreateDispositionV1.INDETERMINATE


def test_create_authority_pin_swap_after_construction_fails_before_admit():
    host, events, invocation = _transaction_host()
    host._record_authority.key_ref = "changed"
    result = _call(host)
    assert result.disposition is DockerCreateDispositionV1.INDETERMINATE
    assert events == []
    assert invocation.calls == 0


@pytest.mark.parametrize("malformed", (False, True))
def test_create_inspect_disappearance_or_malformed_is_indeterminate(malformed):
    if malformed:
        inspected = object()
    else:
        command = HARNESS_INSPECTED.command
        inspected = DockerContainerInspectResultV1.build(
            HARNESS_REF, HARNESS_INSPECTED.request_digest, command,
            _evidence(command, DockerCLIOutcomeV1.NONZERO_EXIT), None,
        )
    host, _events, invocation = _transaction_host(inspect_result=inspected)
    assert _call(host).disposition is DockerCreateDispositionV1.INDETERMINATE
    assert invocation.calls == 1


class MidCallPinAuthority(RecordAuthority):
    def __init__(self):
        self.authenticate_calls = 0
    def authenticate(self, value):
        self.authenticate_calls += 1
        self.key_ref = "changed"
        return value


class InPlaceIssueAuthority(RecordAuthority):
    def __init__(self):
        self.issue_calls = 0
        self.mutated_observed = False
    def issue(self, content):
        self.issue_calls += 1
        if type(content) is DockerMutationRecordV1:
            object.__setattr__(content, "effect_id", "mutated")
            self.mutated_observed = content.effect_id == "mutated"
            return AuthenticatedDockerMutationRecordV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        if type(content) is type(HARNESS_EXPECTED.content.intent.content):
            object.__setattr__(content, "effect_id", "mutated")
            self.mutated_observed = content.effect_id == "mutated"
            return AuthenticatedDockerControlIntentV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        object.__setattr__(content, "binding_digest", "f" * 64)
        self.mutated_observed = content.binding_digest == "f" * 64
        return AuthenticatedDockerExpectedCreateBindingV1(
            content, self.authority_ref, self.key_ref, SHA
        )


def _pin_test_authority(host, role, authority):
    setattr(host, f"_{role}_authority", authority)
    host._authority_instances[role] = authority
    host._pins[role] = (authority.authority_ref, authority.key_ref)


@pytest.mark.parametrize(
    "role,value,authenticate",
    (
        (
            "path",
            AuthenticatedDockerCreatePathBindingV1(
                _path_binding(), "authority", "key", SHA
            ),
            authenticate_create_path_binding_v1,
        ),
        (
            "environment", HARNESS_EXPECTED.content.environment_binding,
            authenticate_workload_environment_binding_v1,
        ),
        (
            "intent", HARNESS_EXPECTED.content.intent,
            authenticate_control_intent_v1,
        ),
        (
            "expected", HARNESS_EXPECTED,
            authenticate_expected_create_binding_v1,
        ),
        (
            "record", _record(HARNESS_EXPECTED, DockerMutationPhaseV1.ADMITTED),
            authenticate_mutation_record_v1,
        ),
    ),
)
def test_create_every_auth_role_rejects_mid_call_pin_change(
    role, value, authenticate,
):
    host, _events, invocation = _transaction_host()
    authority = MidCallPinAuthority()
    _pin_test_authority(host, role, authority)
    with pytest.raises((ValueError, DockerControlContractErrorV1)):
        host._auth(role, authority, value, authenticate)
    assert authority.authenticate_calls == 1
    assert authority.key_ref == "changed"
    assert invocation.calls == 0


@pytest.mark.parametrize(
    "role,content,authenticate",
    (
        (
            "intent", HARNESS_EXPECTED.content.intent.content,
            authenticate_control_intent_v1,
        ),
        (
            "expected", HARNESS_EXPECTED.content,
            authenticate_expected_create_binding_v1,
        ),
        (
            "record",
            _record(HARNESS_EXPECTED, DockerMutationPhaseV1.ADMITTED).content,
            authenticate_mutation_record_v1,
        ),
    ),
)
def test_create_every_issue_role_rejects_in_place_alias_mutation(
    role, content, authenticate,
):
    host, _events, invocation = _transaction_host()
    authority = InPlaceIssueAuthority()
    _pin_test_authority(host, role, authority)
    with pytest.raises((ValueError, DockerControlContractErrorV1)):
        host._issue(role, authority, content, authenticate)
    assert authority.issue_calls == 1
    assert authority.mutated_observed
    assert invocation.calls == 0


class MidCallObjectSwapAuthority(RecordAuthority):
    def __init__(self, host, role):
        self.host = host
        self.role = role
        self.authenticate_calls = 0
        self.issue_calls = 0

    def authenticate(self, value):
        self.authenticate_calls += 1
        setattr(self.host, f"_{self.role}_authority", RecordAuthority())
        return value

    def issue(self, content):
        self.issue_calls += 1
        if type(content) is DockerMutationRecordV1:
            value = AuthenticatedDockerMutationRecordV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        elif type(content) is type(HARNESS_EXPECTED.content.intent.content):
            value = AuthenticatedDockerControlIntentV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        else:
            value = AuthenticatedDockerExpectedCreateBindingV1(
                content, self.authority_ref, self.key_ref, SHA
            )
        setattr(self.host, f"_{self.role}_authority", RecordAuthority())
        return value


@pytest.mark.parametrize(
    "role,value,authenticate",
    (
        ("path", AuthenticatedDockerCreatePathBindingV1(
            _path_binding(), "authority", "key", SHA
        ), authenticate_create_path_binding_v1),
        ("environment", HARNESS_EXPECTED.content.environment_binding,
         authenticate_workload_environment_binding_v1),
        ("intent", HARNESS_EXPECTED.content.intent,
         authenticate_control_intent_v1),
        ("expected", HARNESS_EXPECTED,
         authenticate_expected_create_binding_v1),
        ("record", _record(HARNESS_EXPECTED, DockerMutationPhaseV1.ADMITTED),
         authenticate_mutation_record_v1),
    ),
)
def test_create_every_auth_role_rejects_mid_call_live_object_swap(
    role, value, authenticate,
):
    host, _events, invocation = _transaction_host()
    authority = MidCallObjectSwapAuthority(host, role)
    _pin_test_authority(host, role, authority)
    with pytest.raises(ValueError):
        host._auth(role, authority, value, authenticate)
    assert authority.authenticate_calls == 1
    assert getattr(host, f"_{role}_authority") is not authority
    assert invocation.calls == 0


@pytest.mark.parametrize(
    "role,content,authenticate",
    (
        ("intent", HARNESS_EXPECTED.content.intent.content,
         authenticate_control_intent_v1),
        ("expected", HARNESS_EXPECTED.content,
         authenticate_expected_create_binding_v1),
        ("record", _record(HARNESS_EXPECTED, DockerMutationPhaseV1.ADMITTED).content,
         authenticate_mutation_record_v1),
    ),
)
def test_create_every_issue_role_rejects_mid_call_live_object_swap(
    role, content, authenticate,
):
    host, _events, invocation = _transaction_host()
    authority = MidCallObjectSwapAuthority(host, role)
    _pin_test_authority(host, role, authority)
    with pytest.raises(ValueError):
        host._issue(role, authority, content, authenticate)
    assert authority.issue_calls == 1
    assert authority.authenticate_calls == 0
    assert getattr(host, f"_{role}_authority") is not authority
    assert invocation.calls == 0


@pytest.mark.parametrize(
    "role", ("path", "environment", "intent", "expected", "record")
)
def test_create_rejects_same_pin_alternate_authority_object(role):
    host, _events, invocation = _transaction_host()
    alternate = Authority()
    setattr(host, f"_{role}_authority", alternate)
    pinned = host._authority_instances[role]
    with pytest.raises(ValueError):
        host._auth(
            role, alternate, HARNESS_EXPECTED.content.environment_binding
            if role == "environment" else (
                HARNESS_EXPECTED.content.intent if role == "intent" else
                _record(HARNESS_EXPECTED, DockerMutationPhaseV1.ADMITTED)
                if role == "record" else HARNESS_EXPECTED
            ),
            authenticate_workload_environment_binding_v1
            if role == "environment" else (
                authenticate_control_intent_v1 if role == "intent" else
                authenticate_mutation_record_v1 if role == "record" else
                authenticate_expected_create_binding_v1
            ),
        )
    assert invocation.calls == 0
    assert pinned is not alternate


@pytest.mark.parametrize(
    "boundary,expected_events",
    (
        ("publish", ["publish"]),
        ("admit", ["publish", "admit"]),
        ("attempt_cas", ["publish", "admit", "attempt_cas"]),
        (
            "final_cas",
            ["publish", "admit", "attempt_cas", "create", "inventory", "inspect", "final_cas"],
        ),
    ),
)
def test_create_self_consistent_cross_request_result_is_rejected_at_boundary(
    boundary, expected_events,
):
    host, events, invocation = _transaction_host(cross_at=boundary)
    result = _call(host)
    assert result.disposition is DockerCreateDispositionV1.INDETERMINATE
    assert events == expected_events
    assert invocation.calls == (1 if boundary == "final_cas" else 0)


@pytest.mark.parametrize(
    "boundary",
    ("publish", "admit", "attempt_cas", "final_cas"),
)
def test_create_dependency_cannot_redefine_request_by_in_place_mutation(boundary):
    host, _events, invocation = _transaction_host(cross_at="mutate_" + boundary)
    assert _call(host).disposition is DockerCreateDispositionV1.INDETERMINATE
    assert invocation.calls == (1 if boundary == "final_cas" else 0)


def test_create_unexpected_verifier_fault_is_indeterminate_not_collision(monkeypatch):
    def fault(*_args):
        raise RuntimeError("raw-secret-verifier")
    monkeypatch.setattr(
        "synaptic_host.docker_v1.create.docker_create_projection_matches_v1",
        fault,
    )
    host, events, _invocation = _transaction_host()
    result = _call(host)
    assert result.disposition is DockerCreateDispositionV1.INDETERMINATE
    assert events[-1] == "inspect" and "final_cas" not in events
    assert "raw-secret" not in repr(result)


def test_lookup_unexpected_verifier_fault_is_indeterminate(monkeypatch):
    def fault(*_args):
        raise RuntimeError("raw-secret-verifier")
    monkeypatch.setattr(
        "synaptic_host.docker_v1.control.docker_create_projection_matches_v1",
        fault,
    )
    labels, ref, repository_result, expected, inspected = _one_id_fixture()
    result = _control(
        TypedCLI(
            inventory_result=_inventory_result(labels, (ref,)),
            container_result=inspected,
        ),
        LookupRepository(repository_result), Catalog(expected),
    ).lookup(DockerLookupRequestV1(
        labels, DockerLookupPurposeV1.OBSERVE, 1
    ))
    assert result.disposition is DockerLookupDispositionV1.INDETERMINATE
