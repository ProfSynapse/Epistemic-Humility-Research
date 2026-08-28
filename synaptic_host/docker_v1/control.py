from __future__ import annotations

from tuner.execution.providers.docker_provider_v1.model import (
    AuthenticatedDockerAbsenceV1,
    DockerAbsenceContentV1,
    DockerImageV1,
    DockerLabelsV1,
    DockerLookupDispositionV1,
    DockerLookupPurposeV1,
    DockerLookupRequestV1,
    DockerLookupResultV1,
    DockerRunPhaseV1,
)

from .control_contract import (
    AuthenticatedDockerExpectedCreateBindingV1,
    DockerControlContractErrorV1,
    DockerControlOperationV1,
    DockerMutationLookupDispositionV1,
    DockerMutationLookupResultV1,
    DockerMutationPhaseV1,
    authenticate_absence_v1,
    authenticate_control_intent_v1,
    authenticate_expected_create_binding_v1,
    authenticate_mutation_record_v1,
    authenticate_workload_environment_binding_v1,
    docker_operation_id_v1,
    snapshot_docker_labels_v1,
)
from .control_model import (
    DockerContainerInspectResultV1,
    DockerContainerStatusV1,
    DockerExactNameInventoryResultV1,
    DockerImageInspectResultV1,
)
from .model import DockerCLIOutcomeV1
from .verification import docker_create_projection_matches_v1


class DockerHostControlErrorV1(RuntimeError):
    def __init__(self):
        super().__init__("DOCKER_HOST_CONTROL_INDETERMINATE")


def _closed():
    raise DockerHostControlErrorV1() from None


def _snapshot_typed(value, expected_type, requested_target):
    try:
        if type(value) is not expected_type:
            raise ValueError
        rebuilt = expected_type(
            value.result_kind, value.target, value.request_digest,
            value.command, value.evidence, value.projection,
            value.result_digest,
        )
        if rebuilt.target != requested_target:
            raise ValueError
        if expected_type is DockerExactNameInventoryResultV1 and (
            rebuilt.projection is not None
            and (
                rebuilt.projection.container_name != requested_target
                or rebuilt.projection.query != f"name=^/{requested_target}$"
            )
        ):
            raise ValueError
        return rebuilt
    except BaseException:
        _closed()


def _indeterminate():
    return DockerLookupResultV1(DockerLookupDispositionV1.INDETERMINATE)


class DockerHostControlV1:
    def __init__(
        self, *, typed_cli, mutation_repository, mutation_record_authority,
        expected_catalog, expected_authority, intent_authority,
        environment_authority, absence_authority,
    ):
        try:
            dependencies = (
                typed_cli, mutation_repository, mutation_record_authority,
                expected_catalog, expected_authority, intent_authority,
                environment_authority, absence_authority,
            )
            if any(value is None for value in dependencies):
                raise ValueError
            for authority in (
                mutation_record_authority, expected_authority,
                intent_authority, environment_authority, absence_authority,
            ):
                if type(authority.authority_ref) is not str or type(authority.key_ref) is not str:
                    raise ValueError
            self._typed_cli = typed_cli
            self._repository = mutation_repository
            self._record_authority = mutation_record_authority
            self._catalog = expected_catalog
            self._expected_authority = expected_authority
            self._intent_authority = intent_authority
            self._environment_authority = environment_authority
            self._absence_authority = absence_authority
            self._record_pins = (
                mutation_record_authority.authority_ref,
                mutation_record_authority.key_ref,
            )
            self._expected_pins = (
                expected_authority.authority_ref, expected_authority.key_ref
            )
            self._intent_pins = (
                intent_authority.authority_ref, intent_authority.key_ref
            )
            self._environment_pins = (
                environment_authority.authority_ref,
                environment_authority.key_ref,
            )
            self._absence_pins = (
                absence_authority.authority_ref, absence_authority.key_ref
            )
        except BaseException:
            _closed()

    def require_present(self, image):
        try:
            if type(image) is not DockerImageV1:
                raise ValueError
            image = DockerImageV1(
                image.image_ref, image.image_digest, image.presence_policy
            )
            result = _snapshot_typed(
                self._typed_cli.inspect_image(image.image_digest),
                DockerImageInspectResultV1, image.image_digest,
            )
            if result.evidence.outcome is DockerCLIOutcomeV1.SUCCESS:
                return result.projection.image_digest == image.image_digest
            if (
                result.evidence.outcome is DockerCLIOutcomeV1.NONZERO_EXIT
                and result.projection is None
            ):
                return False
            raise ValueError
        except DockerHostControlErrorV1:
            raise
        except BaseException:
            _closed()

    def lookup(self, request):
        try:
            request = self._snapshot_request(request)
        except BaseException:
            return _indeterminate()
        labels = request.labels
        if (
            labels.effect_kind != "submit"
            or request.purpose not in (
                DockerLookupPurposeV1.RECONCILE_SUBMIT,
                DockerLookupPurposeV1.OBSERVE,
            )
        ):
            return _indeterminate()
        try:
            inventory = _snapshot_typed(
                self._typed_cli.inventory_exact_name(labels.container_name),
                DockerExactNameInventoryResultV1, labels.container_name,
            )
            if inventory.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS:
                return _indeterminate()
            refs = inventory.projection.container_refs
            if len(refs) > 1:
                return DockerLookupResultV1(DockerLookupDispositionV1.MULTIPLE)
            operation_id = docker_operation_id_v1(
                DockerControlOperationV1.CREATE, labels.effect_id
            )
            repository_result = self._repository.lookup(operation_id)
            repository_result = DockerMutationLookupResultV1(
                repository_result.operation_id, repository_result.disposition,
                repository_result.record, repository_result.result_digest,
            )
            if repository_result.operation_id != operation_id:
                return _indeterminate()
            if not refs:
                return self._lookup_absent(
                    request, inventory, repository_result
                )
            return self._lookup_one(
                request, inventory, repository_result, refs[0]
            )
        except BaseException:
            return _indeterminate()

    @staticmethod
    def _snapshot_request(value):
        if type(value) is not DockerLookupRequestV1:
            raise ValueError
        labels = snapshot_docker_labels_v1(value.labels)
        if type(value.generation) is not int:
            raise ValueError
        return DockerLookupRequestV1(labels, value.purpose, value.generation)

    def _lookup_absent(self, request, inventory, repository_result):
        if repository_result.disposition is not DockerMutationLookupDispositionV1.ABSENT:
            return _indeterminate()
        baseline = (
            request.digest, request.labels.digest, request.purpose,
            request.generation, inventory.result_digest,
        )
        expected = DockerAbsenceContentV1(*baseline)
        issued_content = DockerAbsenceContentV1(*baseline)
        self._require_pins(self._absence_authority, self._absence_pins)
        issued = self._absence_authority.issue(issued_content)
        self._require_pins(self._absence_authority, self._absence_pins)
        issued_snapshot = self._snapshot_absence(issued)
        if (
            issued_snapshot.content != expected
            or issued_snapshot.content.content_digest != expected.content_digest
            or (issued_snapshot.authority_ref, issued_snapshot.key_ref)
            != self._absence_pins
        ):
            return _indeterminate()
        authenticated = self._authenticate_role(
            self._absence_authority, self._absence_pins, issued_snapshot,
            authenticate_absence_v1,
        )
        authenticated_snapshot = self._snapshot_absence(authenticated)
        if (
            authenticated_snapshot != issued_snapshot
            or authenticated_snapshot.content != expected
            or authenticated_snapshot.content.content_digest
            != expected.content_digest
        ):
            return _indeterminate()
        return DockerLookupResultV1(
            DockerLookupDispositionV1.DEFINITELY_ABSENT,
            absence=authenticated_snapshot,
        )

    @staticmethod
    def _snapshot_absence(value):
        if type(value) is not AuthenticatedDockerAbsenceV1:
            raise ValueError
        content = value.content
        if type(content) is not DockerAbsenceContentV1:
            raise ValueError
        rebuilt_content = DockerAbsenceContentV1(
            content.request_digest, content.labels_digest, content.purpose,
            content.generation, content.evidence_digest,
        )
        return AuthenticatedDockerAbsenceV1(
            rebuilt_content, value.authority_ref, value.key_ref, value.tag
        )

    def _lookup_one(self, request, inventory, repository_result, container_ref):
        if repository_result.disposition is not DockerMutationLookupDispositionV1.FOUND:
            return _indeterminate()
        record = self._authenticate_role(
            self._record_authority, self._record_pins,
            repository_result.record, authenticate_mutation_record_v1,
        )
        content = record.content
        if (
            content.operation is not DockerControlOperationV1.CREATE
            or content.effect_id != request.labels.effect_id
            or content.operation_id != repository_result.operation_id
            or content.phase not in (
                DockerMutationPhaseV1.ATTEMPTED,
                DockerMutationPhaseV1.VERIFIED,
            )
            or (
                content.phase is DockerMutationPhaseV1.VERIFIED
                and content.container_ref != container_ref
            )
        ):
            return _indeterminate()
        raw_expected = self._catalog.resolve(
            request.labels.command_digest, request.labels.digest
        )
        expected = self._authenticate_role(
            self._expected_authority, self._expected_pins, raw_expected,
            authenticate_expected_create_binding_v1,
        )
        intent = self._authenticate_role(
            self._intent_authority, self._intent_pins,
            expected.content.intent, authenticate_control_intent_v1,
        )
        environment = self._authenticate_role(
            self._environment_authority, self._environment_pins,
            expected.content.environment_binding,
            authenticate_workload_environment_binding_v1,
        )
        if (
            expected.content.labels != request.labels
            or record.content.control_intent_proof_digest != intent.proof_digest
        ):
            return _indeterminate()
        inspected = _snapshot_typed(
            self._typed_cli.inspect_container(container_ref),
            DockerContainerInspectResultV1, container_ref,
        )
        if inspected.evidence.outcome is not DockerCLIOutcomeV1.SUCCESS:
            return _indeterminate()
        projection = inspected.projection
        if not self._matches(
            request.labels, expected, environment, projection, container_ref
        ):
            return _indeterminate()
        phase = self._phase(projection.state, request.purpose)
        if phase is None:
            return _indeterminate()
        return DockerLookupResultV1(
            DockerLookupDispositionV1.FOUND,
            labels=snapshot_docker_labels_v1(request.labels),
            container_ref=container_ref,
            phase=phase,
        )

    @staticmethod
    def _require_pins(authority, pins):
        if (authority.authority_ref, authority.key_ref) != pins:
            raise ValueError

    @classmethod
    def _authenticate_role(cls, authority, pins, value, authenticate):
        cls._require_pins(authority, pins)
        if (value.authority_ref, value.key_ref) != pins:
            raise ValueError
        returned = authenticate(authority, value)
        cls._require_pins(authority, pins)
        if (
            (returned.authority_ref, returned.key_ref) != pins
            or returned != value
        ):
            raise ValueError
        return returned

    @staticmethod
    def _matches(labels, expected, environment, projection, container_ref):
        return docker_create_projection_matches_v1(
            labels, expected, environment, projection, container_ref
        )

    @staticmethod
    def _phase(state, purpose):
        if state.status is DockerContainerStatusV1.CREATED:
            return (
                DockerRunPhaseV1.CREATED
                if purpose is DockerLookupPurposeV1.OBSERVE else None
            )
        if state.status is DockerContainerStatusV1.RUNNING:
            return DockerRunPhaseV1.RUNNING
        if state.status is DockerContainerStatusV1.EXITED:
            return (
                DockerRunPhaseV1.SUCCEEDED
                if state.exit_code == 0 else DockerRunPhaseV1.FAILED
            )
        if state.status is DockerContainerStatusV1.DEAD:
            return DockerRunPhaseV1.FAILED
        return None


__all__: tuple[str, ...] = ()
