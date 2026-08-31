from __future__ import annotations

import re

from tuner.execution.providers.docker_provider_v1.model import (
    DockerStartDispositionV1, DockerStartResultV1,
)

from .control import _snapshot_typed
from .control_contract import (
    DockerAdmissionDispositionV1, DockerAdmissionResultV1,
    DockerCASDispositionV1, DockerCASResultV1,
    DockerControlIntentV1, DockerControlOperationV1,
    DockerMutationAdmissionRequestV1, DockerMutationCASRequestV1,
    DockerMutationLookupDispositionV1, DockerMutationLookupResultV1,
    DockerMutationPhaseV1, DockerMutationRecordV1,
    DockerStartVerificationV1,
    authenticate_control_intent_v1,
    authenticate_expected_create_binding_v1,
    authenticate_mutation_record_v1,
    authenticate_workload_environment_binding_v1,
    docker_operation_id_v1, snapshot_docker_labels_v1,
    _snapshot_authenticated, _snapshot_contract_content,
)
from .control_model import DockerContainerInspectResultV1
from .control_private import DockerPrivateStartInvocationV1
from .model import (
    DockerCLICommandV1, DockerCLIOutcomeV1, DockerCLIVerbV1,
)
from .verification import docker_create_projection_matches_v1


_CONTAINER_REF = re.compile(r"[0-9a-f]{64}\Z")


class _ProjectionCollisionV1(Exception):
    pass


def _indeterminate():
    return DockerStartResultV1(DockerStartDispositionV1.INDETERMINATE)


def _collision():
    return DockerStartResultV1(DockerStartDispositionV1.COLLISION)


def _started(labels, container_ref):
    return DockerStartResultV1(
        DockerStartDispositionV1.STARTED, labels, container_ref
    )


def _admission_snapshot(value):
    return DockerMutationAdmissionRequestV1(
        value.operation_id, _snapshot_authenticated(value.candidate),
        value.request_digest,
    )


def _cas_snapshot(value):
    return DockerMutationCASRequestV1(
        value.operation_id, _snapshot_authenticated(value.expected),
        _snapshot_authenticated(value.replacement), value.request_digest,
    )


class DockerHostStartV1:
    def __init__(
        self, *, typed_runner, mutation_repository, expected_catalog,
        expected_authority, intent_authority, environment_authority,
        record_authority,
    ):
        dependencies = (
            typed_runner, mutation_repository, expected_catalog,
            expected_authority, intent_authority, environment_authority,
            record_authority,
        )
        if any(value is None for value in dependencies):
            raise ValueError
        self._typed_runner = typed_runner
        self._repository = mutation_repository
        self._catalog = expected_catalog
        self._expected_authority = expected_authority
        self._intent_authority = intent_authority
        self._environment_authority = environment_authority
        self._record_authority = record_authority
        self._pins = {
            "expected": self._pin(expected_authority),
            "intent": self._pin(intent_authority),
            "environment": self._pin(environment_authority),
            "record": self._pin(record_authority),
        }
        self._authority_instances = {
            "expected": expected_authority,
            "intent": intent_authority,
            "environment": environment_authority,
            "record": record_authority,
        }
        self._authority_fields = {
            "expected": "_expected_authority",
            "intent": "_intent_authority",
            "environment": "_environment_authority",
            "record": "_record_authority",
        }

    @staticmethod
    def _pin(authority):
        return (authority.authority_ref, authority.key_ref)

    def _auth(self, role, authority, value, authenticate):
        pins = self._pins[role]
        pinned = self._authority_instances[role]
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != pins
        ):
            raise ValueError
        presented = _snapshot_authenticated(value)
        if (presented.authority_ref, presented.key_ref) != pins:
            raise ValueError
        returned = authenticate(authority, presented)
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != pins
        ):
            raise ValueError
        returned = _snapshot_authenticated(returned)
        if returned != presented or (returned.authority_ref, returned.key_ref) != pins:
            raise ValueError
        return returned

    def _issue(self, role, authority, content, authenticate):
        baseline = _snapshot_contract_content(content)
        pinned = self._authority_instances[role]
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != self._pins[role]
        ):
            raise ValueError
        issued = authority.issue(_snapshot_contract_content(baseline))
        if (
            authority is not pinned
            or getattr(self, self._authority_fields[role]) is not pinned
            or self._pin(authority) != self._pins[role]
        ):
            raise ValueError
        issued = self._auth(role, authority, issued, authenticate)
        if issued.content != baseline:
            raise ValueError
        return issued

    def start_once(self, container_ref, labels):
        try:
            labels = snapshot_docker_labels_v1(labels)
            if (
                labels.effect_kind != "submit"
                or type(container_ref) is not str
                or _CONTAINER_REF.fullmatch(container_ref) is None
            ):
                raise ValueError
            preflight = self._preflight(container_ref, labels)
            admitted = self._admitted(preflight)
            request = DockerMutationAdmissionRequestV1.build(
                admitted.content.operation_id, admitted
            )
            baseline = _admission_snapshot(request)
            raw = self._repository.admit(_admission_snapshot(baseline))
            result = DockerAdmissionResultV1(
                raw.request, raw.disposition, raw.record, raw.result_digest
            )
            if result.request != baseline:
                return _indeterminate()
            if result.disposition is DockerAdmissionDispositionV1.CONFLICT:
                return _collision()
            if result.disposition is DockerAdmissionDispositionV1.INDETERMINATE:
                return _indeterminate()
            current = self._auth(
                "record", self._record_authority, result.record,
                authenticate_mutation_record_v1,
            )
            if (
                result.disposition is DockerAdmissionDispositionV1.ADMITTED
                and current != baseline.candidate
            ):
                return _indeterminate()
            if not self._record_matches(current, preflight):
                return _collision()
            if current.content.phase is DockerMutationPhaseV1.VERIFIED:
                return self._recover(preflight, current, None, True)
            attempted = current
            start_result = None
            if current.content.phase is DockerMutationPhaseV1.ADMITTED:
                attempted_candidate = self._attempted(current)
                cas_request = DockerMutationCASRequestV1.build(
                    current.content.operation_id, current, attempted_candidate
                )
                cas_baseline = _cas_snapshot(cas_request)
                try:
                    raw_cas = self._repository.compare_and_swap(
                        _cas_snapshot(cas_baseline)
                    )
                except BaseException:
                    raw_cas = None
                if raw_cas is None:
                    return self._recover(preflight, attempted_candidate, None)
                cas = DockerCASResultV1(
                    raw_cas.request, raw_cas.disposition, raw_cas.record,
                    raw_cas.result_digest,
                )
                if cas.request != cas_baseline:
                    return _indeterminate()
                if cas.disposition is DockerCASDispositionV1.APPLIED:
                    attempted = self._auth(
                        "record", self._record_authority, cas.record,
                        authenticate_mutation_record_v1,
                    )
                    if attempted != cas_baseline.replacement:
                        return _indeterminate()
                    if not preflight["pre_inspected"].projection.state.started:
                        try:
                            start_result = preflight["invocation"].execute_once(
                                self._typed_runner
                            )
                        except BaseException:
                            start_result = None
                elif cas.disposition is DockerCASDispositionV1.CURRENT:
                    attempted = self._auth(
                        "record", self._record_authority, cas.record,
                        authenticate_mutation_record_v1,
                    )
                    if attempted.content.phase is DockerMutationPhaseV1.VERIFIED:
                        if not self._record_matches(attempted, preflight):
                            return _collision()
                        return self._recover(preflight, attempted, None, True)
                else:
                    return _indeterminate()
            elif current.content.phase is not DockerMutationPhaseV1.ATTEMPTED:
                return _indeterminate()
            if not self._record_matches(attempted, preflight):
                return _collision()
            return self._recover(preflight, attempted, start_result)
        except _ProjectionCollisionV1:
            return _collision()
        except BaseException:
            return _indeterminate()

    def _preflight(self, container_ref, labels):
        raw_expected = self._catalog.resolve(
            labels.command_digest, labels.digest
        )
        expected = self._auth(
            "expected", self._expected_authority, raw_expected,
            authenticate_expected_create_binding_v1,
        )
        if expected.content.labels != labels:
            raise ValueError
        create_intent = self._auth(
            "intent", self._intent_authority, expected.content.intent,
            authenticate_control_intent_v1,
        )
        environment = self._auth(
            "environment", self._environment_authority,
            expected.content.environment_binding,
            authenticate_workload_environment_binding_v1,
        )
        create_operation_id = docker_operation_id_v1(
            DockerControlOperationV1.CREATE, labels.effect_id
        )
        raw_lookup = self._repository.lookup(create_operation_id)
        lookup = DockerMutationLookupResultV1(
            raw_lookup.operation_id, raw_lookup.disposition,
            raw_lookup.record, raw_lookup.result_digest,
        )
        if (
            lookup.operation_id != create_operation_id
            or lookup.disposition is not DockerMutationLookupDispositionV1.FOUND
        ):
            raise ValueError
        create_record = self._auth(
            "record", self._record_authority, lookup.record,
            authenticate_mutation_record_v1,
        )
        if (
            create_intent.content.operation is not DockerControlOperationV1.CREATE
            or create_intent.content.operation_id != create_operation_id
            or create_intent.content.effect_id != labels.effect_id
            or create_intent.content.engine_command_digest != labels.command_digest
            or create_intent.content.labels_digest != labels.digest
            or create_intent.content.create_specification_digest
            != expected.content.create_specification.specification_digest
            or create_intent.content.container_name != labels.container_name
            or create_record.content.operation is not DockerControlOperationV1.CREATE
            or create_record.content.operation_id != create_operation_id
            or create_record.content.effect_id != labels.effect_id
            or create_record.content.phase is not DockerMutationPhaseV1.VERIFIED
            or create_record.content.control_intent_proof_digest
            != create_intent.proof_digest
            or create_record.content.container_ref != container_ref
        ):
            raise ValueError
        pre_inspected = _snapshot_typed(
            self._typed_runner.inspect_container(container_ref),
            DockerContainerInspectResultV1, container_ref,
        )
        if pre_inspected.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS:
            raise ValueError
        if not docker_create_projection_matches_v1(
            labels, expected, environment, pre_inspected.projection,
            container_ref,
        ):
            raise _ProjectionCollisionV1
        command = DockerCLICommandV1.build(
            DockerCLIVerbV1.START, (container_ref,)
        )
        invocation = DockerPrivateStartInvocationV1(command, container_ref)
        operation_id = docker_operation_id_v1(
            DockerControlOperationV1.START, labels.effect_id
        )
        intent_content = DockerControlIntentV1.build(
            operation_id=operation_id,
            operation=DockerControlOperationV1.START,
            effect_id=labels.effect_id,
            engine_command_digest=labels.command_digest,
            labels_digest=labels.digest,
            container_name=labels.container_name,
            create_specification_digest=(
                expected.content.create_specification.specification_digest
            ),
            cli_command_digest=command.command_digest,
            container_ref=container_ref,
            verified_create_record_digest=create_record.content.record_digest,
        )
        auth_intent = self._issue(
            "intent", self._intent_authority, intent_content,
            authenticate_control_intent_v1,
        )
        return locals()

    def _admitted(self, preflight):
        intent = preflight["auth_intent"]
        content = DockerMutationRecordV1.build(
            operation_id=intent.content.operation_id,
            operation=DockerControlOperationV1.START,
            effect_id=intent.content.effect_id,
            control_intent_proof_digest=intent.proof_digest,
            phase=DockerMutationPhaseV1.ADMITTED, revision=1,
            attempt_count=0, previous_record_digest=None,
            container_ref=None, verification_result_digest=None,
        )
        return self._issue(
            "record", self._record_authority, content,
            authenticate_mutation_record_v1,
        )

    def _attempted(self, current):
        content = current.content
        replacement = DockerMutationRecordV1.build(
            operation_id=content.operation_id, operation=content.operation,
            effect_id=content.effect_id,
            control_intent_proof_digest=content.control_intent_proof_digest,
            phase=DockerMutationPhaseV1.ATTEMPTED, revision=2,
            attempt_count=1,
            previous_record_digest=content.record_digest,
            container_ref=None, verification_result_digest=None,
        )
        return self._issue(
            "record", self._record_authority, replacement,
            authenticate_mutation_record_v1,
        )

    @staticmethod
    def _record_matches(record, preflight):
        content = record.content
        intent = preflight["auth_intent"]
        return (
            content.operation is DockerControlOperationV1.START
            and content.operation_id == intent.content.operation_id
            and content.effect_id == intent.content.effect_id
            and content.control_intent_proof_digest == intent.proof_digest
        )

    def _recover(self, preflight, current, start_result, already_verified=False):
        container_ref = preflight["container_ref"]
        inspected = _snapshot_typed(
            self._typed_runner.inspect_container(container_ref),
            DockerContainerInspectResultV1, container_ref,
        )
        if inspected.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS:
            return _indeterminate()
        if not docker_create_projection_matches_v1(
            preflight["labels"], preflight["expected"],
            preflight["environment"], inspected.projection, container_ref,
        ):
            return _collision()
        if not inspected.projection.state.started:
            return _indeterminate()
        if already_verified:
            if current.content.container_ref != container_ref:
                return _collision()
            return _started(preflight["labels"], container_ref)
        verification = DockerStartVerificationV1.build(
            operation_id=current.content.operation_id,
            attempted_record_digest=current.content.record_digest,
            expected_proof_digest=preflight["expected"].proof_digest,
            verified_create_record_digest=(
                preflight["create_record"].content.record_digest
            ),
            start_execution_result_digest=(
                None if start_result is None else start_result.result_digest
            ),
            pre_inspect_result_digest=preflight["pre_inspected"].result_digest,
            post_inspect_result_digest=inspected.result_digest,
            container_ref=container_ref,
        )
        content = current.content
        verified_content = DockerMutationRecordV1.build(
            operation_id=content.operation_id, operation=content.operation,
            effect_id=content.effect_id,
            control_intent_proof_digest=content.control_intent_proof_digest,
            phase=DockerMutationPhaseV1.VERIFIED, revision=3,
            attempt_count=1,
            previous_record_digest=content.record_digest,
            container_ref=container_ref,
            verification_result_digest=verification.verification_digest,
        )
        verified = self._issue(
            "record", self._record_authority, verified_content,
            authenticate_mutation_record_v1,
        )
        request = DockerMutationCASRequestV1.build(
            content.operation_id, current, verified
        )
        baseline = _cas_snapshot(request)
        try:
            raw = self._repository.compare_and_swap(_cas_snapshot(baseline))
        except BaseException:
            raw = None
        if raw is None:
            return self._lookup_verified(preflight, verified)
        result = DockerCASResultV1(
            raw.request, raw.disposition, raw.record, raw.result_digest
        )
        if result.request != baseline:
            return _indeterminate()
        if result.disposition is DockerCASDispositionV1.APPLIED:
            durable = self._auth(
                "record", self._record_authority, result.record,
                authenticate_mutation_record_v1,
            )
            if durable != verified or result.request.replacement != baseline.replacement:
                return _indeterminate()
            return _started(preflight["labels"], container_ref)
        if result.disposition is DockerCASDispositionV1.CURRENT:
            durable = self._auth(
                "record", self._record_authority, result.record,
                authenticate_mutation_record_v1,
            )
            if (
                self._record_matches(durable, preflight)
                and durable.content.phase is DockerMutationPhaseV1.VERIFIED
                and durable.content.container_ref == container_ref
            ):
                return _started(preflight["labels"], container_ref)
        return _indeterminate()

    def _lookup_verified(self, preflight, verified):
        raw = self._repository.lookup(verified.content.operation_id)
        lookup = DockerMutationLookupResultV1(
            raw.operation_id, raw.disposition, raw.record, raw.result_digest
        )
        if (
            lookup.operation_id != verified.content.operation_id
            or lookup.disposition is not DockerMutationLookupDispositionV1.FOUND
        ):
            return _indeterminate()
        durable = self._auth(
            "record", self._record_authority, lookup.record,
            authenticate_mutation_record_v1,
        )
        if durable != verified:
            return _indeterminate()
        return _started(preflight["labels"], preflight["container_ref"])


__all__: tuple[str, ...] = ()
