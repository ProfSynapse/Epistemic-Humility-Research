from __future__ import annotations

import json
import base64
from dataclasses import replace

import pytest

from synaptic_tuner.api.v1.providers import ProviderRef
from tuner.execution.foundation_v2.commands import (
    CanonicalProviderPayloadV1,
    build_submit_command,
)
from tuner.execution.foundation_v2.executors import ExecutorDescriptorV1
from tuner.execution.foundation_v2.preparation import CanonicalPreparationV2
from tuner.execution.foundation_v2.references import (
    ExecutionScopeV1,
    StagePredecessorV2,
)

from synaptic_host.docker_execution_state import (
    DockerRunMutationRecordV1,
    DockerRunPhaseV1,
    DockerReconcileOperationV1,
    DockerStageProjectionV1,
    ProviderPreparationRecordV1,
    VerifiedDockerArtifactV1,
    validate_docker_run_transition_v1,
    verified_inventory_digest_v1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1,
    DockerControlOperationV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
    docker_operation_id_v1,
)


NOW = "2026-09-01T12:00:00Z"


def _submit_command():
    provider = ProviderRef("docker", "profile")
    scope = ExecutionScopeV1("account", "namespace")
    prepared = CanonicalPreparationV2.build(
        provider=provider,
        scope=scope,
        project_ref="ehr",
        run_id="run-1",
        plan_fingerprint="8" * 64,
        source_digest="9" * 64,
        workload_digest="a" * 64,
        runtime_digest="b" * 64,
        resource_digest="c" * 64,
        artifact_contract_digest="d" * 64,
        quote_digest="e" * 64,
        secret_requirements_digest="f" * 64,
        execution_binding_digest="1" * 64,
    )
    predecessor = StagePredecessorV2(
        "docker", "profile", "account", "namespace", "ehr", "run-1",
        "8" * 64, prepared.preparation_digest, "a" * 64,
        "stage-effect", "2" * 64, "3" * 64,
    )
    return build_submit_command(
        prepared,
        "submit-nonce",
        CanonicalProviderPayloadV1.build(
            "docker", "submit-payload/v2", "a" * 64
        ),
        ExecutorDescriptorV1("docker", "executor", "1"),
        predecessor,
    )


SUBMIT_COMMAND = _submit_command()
EFFECT = SUBMIT_COMMAND.operation.effect.effect_id


def _authenticated(record: DockerMutationRecordV1) -> AuthenticatedDockerMutationRecordV1:
    return AuthenticatedDockerMutationRecordV1(
        record, "docker-test", "key-v1", record.record_digest
    )


def _low_level(
    operation: DockerControlOperationV1,
    phase: DockerMutationPhaseV1,
    *,
    container_ref: str = "a" * 64,
) -> AuthenticatedDockerMutationRecordV1:
    operation_id = docker_operation_id_v1(operation, EFFECT)
    admitted = DockerMutationRecordV1.build(
        operation_id=operation_id,
        operation=operation,
        effect_id=EFFECT,
        control_intent_proof_digest="1" * 64,
        phase=DockerMutationPhaseV1.ADMITTED,
        revision=1,
        attempt_count=0,
        previous_record_digest=None,
        container_ref=None,
        verification_result_digest=None,
    )
    if phase is DockerMutationPhaseV1.ADMITTED:
        return _authenticated(admitted)
    attempted = DockerMutationRecordV1.build(
        operation_id=operation_id,
        operation=operation,
        effect_id=EFFECT,
        control_intent_proof_digest="1" * 64,
        phase=DockerMutationPhaseV1.ATTEMPTED,
        revision=2,
        attempt_count=1,
        previous_record_digest=admitted.record_digest,
        container_ref=None,
        verification_result_digest=None,
    )
    if phase is DockerMutationPhaseV1.ATTEMPTED:
        return _authenticated(attempted)
    return _authenticated(DockerMutationRecordV1.build(
        operation_id=operation_id,
        operation=operation,
        effect_id=EFFECT,
        control_intent_proof_digest="1" * 64,
        phase=DockerMutationPhaseV1.VERIFIED,
        revision=3,
        attempt_count=1,
        previous_record_digest=attempted.record_digest,
        container_ref=container_ref,
        verification_result_digest="2" * 64,
    ))


def preparation() -> ProviderPreparationRecordV1:
    stage = DockerStageProjectionV1(
        "host-stage://" + "a" * 64 + "/source",
        "2" * 64,
        "host-artifact://" + "a" * 64,
        "3" * 64,
        "4" * 64,
        "5" * 64,
        "tuner/runtime/manifests/offline-sft-worker-v1.json",
        "1" * 64,
        "2" * 64,
        "6" * 64,
        "7" * 64,
    )
    return ProviderPreparationRecordV1.build(
        project_ref="ehr",
        run_id="run-1",
        plan_fingerprint="8" * 64,
        effect_id=EFFECT,
        source_lock_digest="9" * 64,
        prepared_docker_plan_digest="a" * 64,
        endpoint_descriptor_digest="b" * 64,
        cli_policy_digest="c" * 64,
        destination_ref="local-default",
        destination_declaration_digest="d" * 64,
        submit_command_bytes=SUBMIT_COMMAND.canonical_bytes,
        stage=stage,
        prepared_at=NOW,
    )


def _aggregate(
    phase: DockerRunPhaseV1,
    *,
    revision: int,
    previous: str | None,
) -> DockerRunMutationRecordV1:
    create_phase = {
        DockerRunPhaseV1.CREATE_ADMITTED: DockerMutationPhaseV1.ADMITTED,
        DockerRunPhaseV1.CREATE_ATTEMPTED: DockerMutationPhaseV1.ATTEMPTED,
    }.get(phase, DockerMutationPhaseV1.VERIFIED)
    start_phase = {
        DockerRunPhaseV1.START_ADMITTED: DockerMutationPhaseV1.ADMITTED,
        DockerRunPhaseV1.START_ATTEMPTED: DockerMutationPhaseV1.ATTEMPTED,
    }.get(phase)
    if phase in {
        DockerRunPhaseV1.SUBMITTED,
        DockerRunPhaseV1.PROCESS_SUCCEEDED,
        DockerRunPhaseV1.PROCESS_FAILED,
        DockerRunPhaseV1.ARTIFACTS_VERIFIED,
    }:
        start_phase = DockerMutationPhaseV1.VERIFIED
    closed = phase in {
        DockerRunPhaseV1.PROCESS_SUCCEEDED,
        DockerRunPhaseV1.PROCESS_FAILED,
        DockerRunPhaseV1.ARTIFACTS_VERIFIED,
    }
    artifacts = ()
    inventory_digest = None
    if phase is DockerRunPhaseV1.ARTIFACTS_VERIFIED:
        artifacts = tuple(
            VerifiedDockerArtifactV1(role, f"{role}.json", 1, str(index) * 64)
            for index, role in enumerate(
                (
                    "final_model", "tokenizer", "training_lineage",
                    "training_metrics", "workload_record",
                ),
                start=1,
            )
        )
        inventory_digest = verified_inventory_digest_v1(artifacts)
    return DockerRunMutationRecordV1.build(
        project_ref="ehr",
        run_id="run-1",
        effect_id=EFFECT,
        preparation_digest=preparation().preparation_digest,
        phase=phase,
        revision=revision,
        previous_record_digest=previous,
        create_mutation=_low_level(DockerControlOperationV1.CREATE, create_phase),
        start_mutation=(
            None
            if start_phase is None
            else _low_level(DockerControlOperationV1.START, start_phase)
        ),
        reconcile_operation=None,
        container_ref=(
            "a" * 64
            if phase in {
                DockerRunPhaseV1.SUBMITTED,
                DockerRunPhaseV1.PROCESS_SUCCEEDED,
                DockerRunPhaseV1.PROCESS_FAILED,
                DockerRunPhaseV1.ARTIFACTS_VERIFIED,
            }
            else None
        ),
        submitted_at=(
            NOW
            if phase in {
                DockerRunPhaseV1.SUBMITTED,
                DockerRunPhaseV1.PROCESS_SUCCEEDED,
                DockerRunPhaseV1.PROCESS_FAILED,
                DockerRunPhaseV1.ARTIFACTS_VERIFIED,
            }
            else None
        ),
        process_exit_code=(
            1 if phase is DockerRunPhaseV1.PROCESS_FAILED else 0 if closed else None
        ),
        process_observation_digest="e" * 64 if closed else None,
        diagnostic="PROCESS_NONZERO" if phase is DockerRunPhaseV1.PROCESS_FAILED else None,
        verified_artifacts=artifacts,
        verified_inventory_digest=inventory_digest,
    )


def test_preparation_and_initial_aggregate_round_trip_exactly() -> None:
    prepared = preparation()
    assert ProviderPreparationRecordV1.from_canonical_bytes(
        prepared.canonical_bytes
    ) == prepared
    initial = DockerRunMutationRecordV1.initial(
        prepared,
        _low_level(DockerControlOperationV1.CREATE, DockerMutationPhaseV1.ADMITTED),
    )
    assert initial.phase is DockerRunPhaseV1.CREATE_ADMITTED
    assert initial.revision == 1
    assert DockerRunMutationRecordV1.from_canonical_bytes(
        initial.canonical_bytes
    ) == initial
    document = json.loads(prepared.canonical_bytes)
    assert document["submit_command_base64"] == base64.b64encode(
        SUBMIT_COMMAND.canonical_bytes
    ).decode("ascii")
    assert prepared.submit_command_digest == SUBMIT_COMMAND.digest


@pytest.mark.parametrize(
    "encoded",
    ("", "YQ", "YQ===", "Y Q==", "YQ==\n", "-_=="),
)
def test_preparation_rejects_noncanonical_submit_command_base64(encoded) -> None:
    document = json.loads(preparation().canonical_bytes)
    document["submit_command_base64"] = encoded
    raw = json.dumps(
        document, sort_keys=True, separators=(",", ":")
    ).encode()
    with pytest.raises(ValueError, match="submit_command_base64"):
        ProviderPreparationRecordV1.from_canonical_bytes(raw)


def test_preparation_rejects_old_shape_and_command_identity_drift() -> None:
    document = json.loads(preparation().canonical_bytes)
    del document["submit_command_base64"]
    raw = json.dumps(
        document, sort_keys=True, separators=(",", ":")
    ).encode()
    with pytest.raises(ValueError, match="missing or unknown"):
        ProviderPreparationRecordV1.from_canonical_bytes(raw)
    with pytest.raises(ValueError, match="bind the preparation"):
        replace(preparation(), project_ref="other-project")
    with pytest.raises(ValueError, match="bytes are invalid"):
        replace(preparation(), submit_command_bytes=b"x" * 262_145)


def test_submitted_and_exact_five_artifact_terminal_records_are_closed() -> None:
    submitted = _aggregate(DockerRunPhaseV1.SUBMITTED, revision=6, previous="f" * 64)
    verified = _aggregate(
        DockerRunPhaseV1.ARTIFACTS_VERIFIED,
        revision=8,
        previous=submitted.record_digest,
    )
    assert tuple(item.role for item in verified.verified_artifacts) == (
        "final_model", "tokenizer", "training_lineage", "training_metrics",
        "workload_record",
    )
    assert DockerRunMutationRecordV1.from_canonical_bytes(
        verified.canonical_bytes
    ) == verified


def test_mutation_records_reject_digest_substitution_and_partial_inventory() -> None:
    initial = DockerRunMutationRecordV1.initial(
        preparation(),
        _low_level(DockerControlOperationV1.CREATE, DockerMutationPhaseV1.ADMITTED),
    )
    with pytest.raises(ValueError, match="record_digest"):
        replace(initial, record_digest="0" * 64)
    with pytest.raises(ValueError, match="exactly five roles"):
        DockerRunMutationRecordV1.build(
            **{
                name: getattr(
                    _aggregate(
                        DockerRunPhaseV1.ARTIFACTS_VERIFIED,
                        revision=8,
                        previous="f" * 64,
                    ),
                    name,
                )
                for name in DockerRunMutationRecordV1.__dataclass_fields__
                if name not in {"record_digest", "verified_artifacts"}
            },
            verified_artifacts=(),
        )


def test_exact_authenticated_mutation_transition_chain() -> None:
    initial = DockerRunMutationRecordV1.initial(
        preparation(),
        _low_level(DockerControlOperationV1.CREATE, DockerMutationPhaseV1.ADMITTED),
    )
    phases = (
        DockerRunPhaseV1.CREATE_ATTEMPTED,
        DockerRunPhaseV1.CREATED,
        DockerRunPhaseV1.START_ADMITTED,
        DockerRunPhaseV1.START_ATTEMPTED,
        DockerRunPhaseV1.SUBMITTED,
        DockerRunPhaseV1.PROCESS_SUCCEEDED,
        DockerRunPhaseV1.ARTIFACTS_VERIFIED,
    )
    current = initial
    for revision, phase in enumerate(phases, start=2):
        replacement = _aggregate(
            phase, revision=revision, previous=current.record_digest
        )
        validate_docker_run_transition_v1(current, replacement)
        current = replacement


def test_process_success_can_close_only_as_exact_artifact_failure() -> None:
    succeeded = _aggregate(
        DockerRunPhaseV1.PROCESS_SUCCEEDED, revision=7, previous="f" * 64
    )
    values = {
        name: getattr(succeeded, name)
        for name in DockerRunMutationRecordV1.__dataclass_fields__
        if name not in {
            "record_digest", "phase", "revision", "previous_record_digest",
            "diagnostic",
        }
    }
    failed = DockerRunMutationRecordV1.build(
        **values,
        phase=DockerRunPhaseV1.PROCESS_FAILED,
        revision=8,
        previous_record_digest=succeeded.record_digest,
        diagnostic="ARTIFACT_INTEGRITY_INVALID",
    )
    validate_docker_run_transition_v1(succeeded, failed)
    with pytest.raises(ValueError, match="artifact verification failure"):
        validate_docker_run_transition_v1(
            succeeded, replace(
                failed,
                process_observation_digest="0" * 64,
                record_digest=DockerRunMutationRecordV1.build(
                    **{
                        name: getattr(failed, name)
                        for name in DockerRunMutationRecordV1.__dataclass_fields__
                        if name not in {"record_digest", "process_observation_digest"}
                    },
                    process_observation_digest="0" * 64,
                ).record_digest,
            )
        )

    process_dead = DockerRunMutationRecordV1.build(
        **values,
        phase=DockerRunPhaseV1.PROCESS_FAILED,
        revision=8,
        previous_record_digest=succeeded.record_digest,
        diagnostic="PROCESS_DEAD",
    )
    validate_docker_run_transition_v1(succeeded, process_dead)
    with pytest.raises(ValueError, match="closed diagnostic"):
        DockerRunMutationRecordV1.build(
            **values,
            phase=DockerRunPhaseV1.PROCESS_FAILED,
            revision=8,
            previous_record_digest=succeeded.record_digest,
            diagnostic="ARBITRARY_ZERO_EXIT_FAILURE",
        )


def test_reconcile_matrix_and_unaffected_envelopes_are_exact() -> None:
    attempted = _aggregate(
        DockerRunPhaseV1.CREATE_ATTEMPTED, revision=2, previous="f" * 64
    )
    reconcile = DockerRunMutationRecordV1.build(
        **{
            name: getattr(attempted, name)
            for name in DockerRunMutationRecordV1.__dataclass_fields__
            if name not in {
                "record_digest", "phase", "revision", "previous_record_digest",
                "reconcile_operation", "diagnostic",
            }
        },
        phase=DockerRunPhaseV1.RECONCILE_REQUIRED,
        revision=3,
        previous_record_digest=attempted.record_digest,
        reconcile_operation=DockerReconcileOperationV1.LOOKUP_CREATE,
        diagnostic="CREATE_LOOKUP_REQUIRED",
    )
    validate_docker_run_transition_v1(attempted, reconcile)
    created = _aggregate(
        DockerRunPhaseV1.CREATED, revision=4, previous=reconcile.record_digest
    )
    validate_docker_run_transition_v1(reconcile, created)

    submitted = _aggregate(
        DockerRunPhaseV1.SUBMITTED, revision=4, previous=reconcile.record_digest
    )
    with pytest.raises(ValueError, match="reconciliation continuity"):
        validate_docker_run_transition_v1(reconcile, submitted)

    start_admitted = _aggregate(
        DockerRunPhaseV1.START_ADMITTED, revision=4, previous="e" * 64
    )
    start_attempted = _aggregate(
        DockerRunPhaseV1.START_ATTEMPTED,
        revision=5,
        previous=start_admitted.record_digest,
    )
    altered_create = AuthenticatedDockerMutationRecordV1(
        start_attempted.create_mutation.content,
        start_attempted.create_mutation.authority_ref,
        start_attempted.create_mutation.key_ref,
        "f" * 64,
    )
    altered = DockerRunMutationRecordV1.build(
        **{
            name: getattr(start_attempted, name)
            for name in DockerRunMutationRecordV1.__dataclass_fields__
            if name not in {"record_digest", "create_mutation"}
        },
        create_mutation=altered_create,
    )
    with pytest.raises(ValueError, match="only the start envelope"):
        validate_docker_run_transition_v1(start_admitted, altered)


def test_obsolete_unenveloped_candidate_json_fails_closed() -> None:
    initial = DockerRunMutationRecordV1.initial(
        preparation(),
        _low_level(DockerControlOperationV1.CREATE, DockerMutationPhaseV1.ADMITTED),
    )
    document = json.loads(initial.canonical_bytes)
    document["create_mutation"] = document["create_mutation"]["content"]
    obsolete = json.dumps(
        document, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    with pytest.raises(ValueError, match="authenticated Docker mutation"):
        DockerRunMutationRecordV1.from_canonical_bytes(obsolete)
