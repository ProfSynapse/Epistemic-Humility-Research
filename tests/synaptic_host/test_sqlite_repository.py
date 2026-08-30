from __future__ import annotations

import base64
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import (
    EffectIdentity,
    EffectKind,
    EffectRecord,
    EffectState,
    EventCode,
    ExecutionScope,
    GrantBinding,
    LifecycleEvent,
    LifecyclePhase,
    MessageCode,
    ProjectContext,
    ReplayDisposition,
    RevisionConflict,
    RunAlreadyExists,
    EffectCollision,
)
from synaptic_tuner.api.v1.modal import (
    ModalDurablePreparationV1,
    ModalPreparedRunV1,
)
from tuner.execution.broker import MutationCommandV1
from tuner.execution.operation import ModalStageTargetV1, OperationBindingV1
from tuner.execution.providers.modal.binding import ModalClientBinding
from tuner.execution.providers.modal.contracts import (
    StageReceiptV1,
    canonical_json,
    operation_path,
    sha,
)
from tuner.execution.providers.modal.deployment_identity import modal_function_name
from tuner.execution.providers.modal.resolution import (
    ModalDeploymentSelectionV1,
    VerifiedModalDeploymentIdentityV1,
)
from tuner.execution.providers.modal.staging import prepare_modal_stage
from tuner.execution.providers.modal.training import (
    ModalPlanContextV1,
)
from tuner.execution.lifecycle import apply_event, initial_record
from synaptic_host import SqliteTrainingRepository

NOW = "2026-08-26T12:00:00Z"


def repository(tmp_path: Path) -> SqliteTrainingRepository:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    context = ProjectContext.host(engine_root=engine, project_root=project)
    return SqliteTrainingRepository.from_context(context, clock=lambda: NOW)


class _Authenticator:
    @staticmethod
    def sign(purpose: str, payload: bytes, key_ref: str) -> bytes:
        return sha(purpose.encode() + b"\0" + payload + b"\0" + key_ref.encode()).encode()


def _verified_deployment() -> VerifiedModalDeploymentIdentityV1:
    deployment_ref = "modal-deployment-" + "1" * 32
    selection = ModalDeploymentSelectionV1(
        account_ref="account-1",
        workspace_ref="workspace-1",
        environment_ref="environment-1",
        client_ref="client-1",
        app_name="synaptic-training-v1",
        function_name=modal_function_name(deployment_ref),
        deployment_ref=deployment_ref,
        image_digest="1" * 64,
        dependency_lock_digest="2" * 64,
        wrapper_digest="3" * 64,
        runtime_digest="4" * 64,
        python_version="3.11.15",
        python_executable="/opt/conda/bin/python",
        python_executable_digest="5" * 64,
        secret_requirements_digest="6" * 64,
        provider_runtime_requirements_digest="7" * 64,
        runtime_environment={"PATH": "/opt/conda/bin"},
    )
    unsigned = {
        "schema_version": "synaptic-verified-modal-deployment/v1",
        "selection": selection.to_dict(),
        "issuer_ref": "deployment-verifier",
        "evidence_ref": "deployment-evidence-1",
        "audience_ref": "project-1",
        "challenge_nonce": "deployment-nonce-1",
        "verified_at": "2026-08-26T11:59:00Z",
        "expires_at": "2026-08-26T12:10:00Z",
        "key_ref": "deployment-key-1",
    }
    return VerifiedModalDeploymentIdentityV1(
        selection=selection,
        issuer_ref=unsigned["issuer_ref"],
        evidence_ref=unsigned["evidence_ref"],
        audience_ref=unsigned["audience_ref"],
        challenge_nonce=unsigned["challenge_nonce"],
        verified_at=unsigned["verified_at"],
        expires_at=unsigned["expires_at"],
        key_ref=unsigned["key_ref"],
        tag_base64=base64.b64encode(b"authenticated-deployment").decode("ascii"),
        attestation_digest=sha(canonical_json(unsigned)),
    )


def _prepared_run(
    *, run_id: str = "run-1", effect_id: str = "effect-submit-1"
) -> ModalPreparedRunV1:
    binding = ModalClientBinding(
        "account-1", "workspace-1", "environment-1", "client-1", "1.5.4"
    )
    deployment = _verified_deployment()
    resource_digest = "8" * 64
    quote_digest = "9" * 64
    target = ModalStageTargetV1(
        f"slot-{run_id}",
        "control-volume-1",
        "artifact-volume-1",
        operation_path(effect_id, "output"),
        1,
        "stage-key-1",
    )
    effect = EffectIdentity(
        effect_id,
        f"operation-{run_id}",
        EffectKind.SUBMIT,
        ExecutionScope("modal", "account-1", "environment-1"),
    )
    operation = OperationBindingV1(
        project_ref="ehr",
        run_id=run_id,
        effect=effect,
        grant_ref=f"grant-{run_id}",
        plan_fingerprint="a" * 64,
        execution_source_digest="b" * 64,
        workload_digest="c" * 64,
        deployment_attestation_digest=deployment.attestation_digest,
        artifact_contract_digest="d" * 64,
        log_policy_digest="e" * 64,
        invocation_intent_digest="f" * 64,
        resource_digest=resource_digest,
        quote_digest=quote_digest,
        secret_requirements_digest="1" * 64,
        invocation_arguments_digest="2" * 64,
        invocation_nonce=f"nonce-{run_id}",
        stage_target=target,
    )
    context = ModalPlanContextV1(
        project_ref="ehr",
        profile="modal-a10-v1",
        deployment=deployment,
        binding=binding,
        control_volume_id=target.control_volume_id,
        artifact_volume_id=target.artifact_volume_id,
        key_ref=target.key_ref,
        quote_digest=quote_digest,
        quote_expires_at="2026-08-26T12:10:00Z",
        maximum_cost_minor_units=100,
        currency="USD",
        effect_id=effect.effect_id,
        effect_key=effect.effect_key,
        artifact_slot_ref=target.artifact_slot_ref,
        invocation_nonce=operation.invocation_nonce,
        generation=target.generation,
        resource_digest=resource_digest,
    )
    stage = prepare_modal_stage(operation, binding, b"exact-modal-bundle", _Authenticator())
    preparation = ModalDurablePreparationV1(
        operation.plan_fingerprint, context, operation, stage
    )
    grant = GrantBinding.from_operation(
        operation,
        issued_at="2026-08-26T11:59:00Z",
        expires_at="2026-08-26T12:10:00Z",
    )
    record = initial_record(project_ref="ehr", run_id=run_id, occurred_at=NOW)
    record = apply_event(
        record,
        LifecycleEvent(
            EventCode.AUTHORITY_ACCEPTED,
            NOW,
            MessageCode.AUTHORITY_BOUND,
            grant_binding=grant,
        ),
    )
    record = apply_event(
        record,
        LifecycleEvent(EventCode.PREPARATION_STARTED, NOW, MessageCode.PREPARING),
    )
    record = apply_event(
        record,
        LifecycleEvent(EventCode.PREPARATION_COMPLETED, NOW, MessageCode.READY),
    )
    return ModalPreparedRunV1(record, preparation)


def _stored_pair(
    value: SqliteTrainingRepository, pair: ModalPreparedRunV1
) -> tuple[object, object]:
    return (
        value.load(pair.record.project_ref, pair.record.run_id),
        value.load_modal_preparation(pair.record.project_ref, pair.record.run_id),
    )


def test_database_lives_under_the_host_state_root_and_reopens(tmp_path: Path) -> None:
    value = repository(tmp_path)
    assert value.database_path == (
        tmp_path / "project" / ".synaptic" / "state" / "training.sqlite3"
    ).resolve()
    record = initial_record(project_ref="ehr", run_id="run-1", occurred_at=NOW)
    value.create(record)
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert reopened.load("ehr", "run-1") == record


def test_append_is_atomic_and_revision_checked(tmp_path: Path) -> None:
    value = repository(tmp_path)
    record = value.create(
        initial_record(project_ref="ehr", run_id="run-1", occurred_at=NOW)
    )
    event = LifecycleEvent(
        EventCode.AUTHORIZATION_REJECTED,
        NOW,
        MessageCode.AUTHORIZATION_MISMATCH,
    )
    changed = value.append(
        "ehr", "run-1", expected_revision=record.revision, event=event
    )
    assert changed.phase is LifecyclePhase.FAILED
    with pytest.raises(RevisionConflict):
        value.append(
            "ehr", "run-1", expected_revision=record.revision, event=event
        )
    assert value.load("ehr", "run-1") == changed


def test_concurrent_compare_and_append_allows_only_one_revision(tmp_path: Path) -> None:
    value = repository(tmp_path)
    record = value.create(
        initial_record(project_ref="ehr", run_id="run-1", occurred_at=NOW)
    )
    event = LifecycleEvent(
        EventCode.AUTHORIZATION_REJECTED,
        NOW,
        MessageCode.AUTHORIZATION_MISMATCH,
    )

    def append_once(_: int) -> str:
        try:
            value.append(
                "ehr", "run-1", expected_revision=record.revision, event=event
            )
            return "committed"
        except RevisionConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(append_once, range(2)))
    assert sorted(outcomes) == ["committed", "conflict"]


def test_run_listing_uses_stable_database_sequence_cursors(tmp_path: Path) -> None:
    value = repository(tmp_path)
    for index in range(3):
        value.create(
            initial_record(
                project_ref="ehr", run_id=f"run-{index}", occurred_at=NOW
            )
        )
    first = value.list_runs("ehr", limit=2)
    second = value.list_runs("ehr", limit=2, cursor=first.next_cursor)
    assert [item.run_id for item in first.items] == ["run-0", "run-1"]
    assert first.next_cursor is not None
    assert [item.run_id for item in second.items] == ["run-2"]
    assert second.next_cursor is None


def test_evidence_replay_is_durable_idempotent_and_collision_closed(
    tmp_path: Path,
) -> None:
    value = repository(tmp_path)
    evidence = {
        "purpose": "modal-source-evidence/v1",
        "issuer_ref": "git-verifier",
        "evidence_ref": "proof-1",
        "challenge_nonce": "nonce-1",
        "audience_ref": "ehr/run-1",
        "payload_digest": "a" * 64,
        "expires_at": "2026-08-26T12:05:00Z",
    }
    assert value.admit(**evidence) is ReplayDisposition.ADMITTED
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert reopened.admit(**evidence) is ReplayDisposition.IDEMPOTENT
    changed = dict(evidence, payload_digest="b" * 64)
    assert reopened.admit(**changed) is ReplayDisposition.COLLISION


def test_attempted_modal_effect_remains_durable_after_repository_reopen(
    tmp_path: Path,
) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()
    expectation = pair.preparation.stage.expectation
    receipt = StageReceiptV1(
        expectation.effect.effect_id,
        expectation.operation_binding_digest,
        expectation.control_volume_id,
        expectation.artifact_volume_id,
        expectation.claim_digest,
        expectation.bundle_digest,
    )
    command = MutationCommandV1.from_stage(pair.preparation.operation, receipt)
    grant = pair.record.grant_binding
    assert grant is not None
    effect = EffectRecord(
        pair.preparation.operation.effect,
        grant.fingerprint,
        state=EffectState.ATTEMPTED,
        grant_ref=grant.grant_ref,
        command_digest=command.digest,
        canonical_command=command.canonical_bytes,
        attempt_count=1,
    )
    record = apply_event(
        pair.record,
        LifecycleEvent(
            EventCode.EFFECT_ATTEMPTED,
            NOW,
            MessageCode.EFFECT_MUTATION_ATTEMPTED,
            effect=effect,
        ),
    )
    value.create(record)

    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    loaded = reopened.load("ehr", "run-1")
    assert loaded == record
    assert loaded.effects[0].state is EffectState.ATTEMPTED


def test_create_modal_prepared_run_commits_exact_detached_pair_and_reopens(
    tmp_path: Path,
) -> None:
    presented: list[ModalPreparedRunV1] = []

    class CapturingRepository(SqliteTrainingRepository):
        @staticmethod
        def _insert_modal_preparation_in(connection, value) -> None:
            presented.append(value)
            SqliteTrainingRepository._insert_modal_preparation_in(connection, value)

    original = repository(tmp_path)
    value = CapturingRepository(original.database_path, clock=lambda: NOW)
    pair = _prepared_run()

    assert not hasattr(value, "commit_modal_preparation")
    value.create_modal_prepared_run(pair)

    assert presented == [pair]
    assert presented[0] is not pair
    assert presented[0].record is not pair.record
    assert presented[0].preparation is not pair.preparation
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert _stored_pair(reopened, pair) == (pair.record, pair.preparation)
    assert (
        reopened.load_modal_preparation_by_effect(
            pair.preparation.operation.effect.effect_id
        )
        == pair.preparation
    )


def test_create_modal_prepared_run_rejects_noncanonical_input_without_rows(
    tmp_path: Path,
) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(object())

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert _stored_pair(value, pair) == (None, None)


def test_failure_between_atomic_inserts_rolls_back_both_rows(tmp_path: Path) -> None:
    pair = _prepared_run()

    class FailingPreparationRepository(SqliteTrainingRepository):
        @staticmethod
        def _insert_modal_preparation_in(_connection, _value) -> None:
            raise sqlite3.OperationalError("private preparation failure")

    original = repository(tmp_path)
    value = FailingPreparationRepository(original.database_path, clock=lambda: NOW)
    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(pair)

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert _stored_pair(reopened, pair) == (None, None)


@pytest.mark.parametrize("failure_type", (RunAlreadyExists, EffectCollision))
def test_insert_failure_cannot_spoof_a_classified_collision(
    tmp_path: Path, failure_type: type[Exception],
) -> None:
    pair = _prepared_run()

    class SpoofingRepository(SqliteTrainingRepository):
        @staticmethod
        def _insert_modal_preparation_in(_connection, _value) -> None:
            raise failure_type("private spoofed classification")

    original = repository(tmp_path)
    value = SpoofingRepository(original.database_path, clock=lambda: NOW)
    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(pair)

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert _stored_pair(reopened, pair) == (None, None)


def test_concurrent_exact_prepared_run_creators_admit_only_one(tmp_path: Path) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    def create(_: int) -> str:
        try:
            value.create_modal_prepared_run(pair)
            return "created"
        except RunAlreadyExists:
            return "exists"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(create, range(2)))

    assert sorted(outcomes) == ["created", "exists"]
    assert _stored_pair(value, pair) == (pair.record, pair.preparation)


def test_concurrent_effect_collision_keeps_one_complete_pair(tmp_path: Path) -> None:
    value = repository(tmp_path)
    first = _prepared_run(run_id="run-1", effect_id="shared-effect")
    second = _prepared_run(run_id="run-2", effect_id="shared-effect")

    def create(pair: ModalPreparedRunV1) -> str:
        try:
            value.create_modal_prepared_run(pair)
            return "created"
        except EffectCollision:
            return "collision"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(create, (first, second)))

    assert sorted(outcomes) == ["collision", "created"]
    stored = (_stored_pair(value, first), _stored_pair(value, second))
    assert stored.count((first.record, first.preparation)) + stored.count(
        (second.record, second.preparation)
    ) == 1
    assert stored.count((None, None)) == 1


def test_existing_run_key_precedes_conflicting_preparation_identity(
    tmp_path: Path,
) -> None:
    value = repository(tmp_path)
    original = _prepared_run(run_id="run-1", effect_id="effect-1")
    conflicting = _prepared_run(run_id="run-1", effect_id="effect-2")
    value.create_modal_prepared_run(original)

    with pytest.raises(RunAlreadyExists, match="^run already exists$") as error:
        value.create_modal_prepared_run(conflicting)

    assert type(error.value) is RunAlreadyExists
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert _stored_pair(value, original) == (original.record, original.preparation)


def test_existing_effect_identity_maps_to_exact_effect_collision(
    tmp_path: Path,
) -> None:
    value = repository(tmp_path)
    original = _prepared_run(run_id="run-1", effect_id="shared-effect")
    conflicting = _prepared_run(run_id="run-2", effect_id="shared-effect")
    value.create_modal_prepared_run(original)

    with pytest.raises(EffectCollision, match="^Modal preparation collision$") as error:
        value.create_modal_prepared_run(conflicting)

    assert type(error.value) is EffectCollision
    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    assert _stored_pair(value, original) == (original.record, original.preparation)
    assert _stored_pair(value, conflicting) == (None, None)


def test_foreign_key_rejects_preparation_without_lifecycle(tmp_path: Path) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    with pytest.raises(sqlite3.IntegrityError):
        with value._transaction() as connection:
            value._insert_modal_preparation_in(connection, pair)

    assert _stored_pair(value, pair) == (None, None)


def test_connection_failure_is_closed_and_leaves_no_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    def fail_connect():
        raise sqlite3.OperationalError("private connection detail")

    monkeypatch.setattr(value, "_connect", fail_connect)
    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(pair)

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert _stored_pair(reopened, pair) == (None, None)


class _OperationFaultConnection:
    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        failure_point: str,
        fail_rollback: bool = False,
    ) -> None:
        self._connection = connection
        self._failure_point = failure_point
        self._fail_rollback = fail_rollback

    @property
    def in_transaction(self) -> bool:
        return self._connection.in_transaction

    def execute(self, statement: str, parameters=()):
        canonical = " ".join(statement.split())
        if self._failure_point == "begin" and canonical == "BEGIN IMMEDIATE":
            raise sqlite3.OperationalError("private begin detail")
        if (
            self._failure_point == "first_insert"
            and "INSERT INTO lifecycle_records" in canonical
        ):
            raise sqlite3.OperationalError("private first insert detail")
        if self._fail_rollback and canonical == "ROLLBACK":
            raise sqlite3.OperationalError("private rollback detail")
        return self._connection.execute(statement, parameters)

    def close(self) -> None:
        self._connection.close()


@pytest.mark.parametrize("failure_point", ("begin", "first_insert"))
def test_transaction_operation_failure_is_closed_without_exception_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    def connect():
        connection = sqlite3.connect(
            value.database_path, timeout=30, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return _OperationFaultConnection(
            connection, failure_point=failure_point
        )

    monkeypatch.setattr(value, "_connect", connect)
    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(pair)

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert _stored_pair(reopened, pair) == (None, None)


def test_rollback_failure_is_closed_without_exception_links(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    def connect():
        connection = sqlite3.connect(
            value.database_path, timeout=30, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return _OperationFaultConnection(
            connection, failure_point="first_insert", fail_rollback=True
        )

    monkeypatch.setattr(value, "_connect", connect)
    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(pair)

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    assert _stored_pair(reopened, pair) == (None, None)


class _CommitFaultConnection:
    def __init__(self, connection: sqlite3.Connection, *, after_commit: bool) -> None:
        self._connection = connection
        self._after_commit = after_commit

    @property
    def in_transaction(self) -> bool:
        return self._connection.in_transaction

    def execute(self, statement: str, parameters=()):
        if statement == "COMMIT":
            if self._after_commit:
                self._connection.execute(statement)
            raise sqlite3.OperationalError("private commit outcome")
        return self._connection.execute(statement, parameters)

    def close(self) -> None:
        self._connection.close()


@pytest.mark.parametrize("after_commit", (False, True))
def test_commit_failure_is_closed_and_never_exposes_a_partial_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    after_commit: bool,
) -> None:
    value = repository(tmp_path)
    pair = _prepared_run()

    def connect():
        connection = sqlite3.connect(
            value.database_path, timeout=30, isolation_level=None
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return _CommitFaultConnection(connection, after_commit=after_commit)

    monkeypatch.setattr(value, "_connect", connect)
    with pytest.raises(RuntimeError, match="^host prepared-run persistence failed$") as error:
        value.create_modal_prepared_run(pair)

    assert error.value.__cause__ is None
    assert error.value.__context__ is None
    reopened = SqliteTrainingRepository(value.database_path, clock=lambda: NOW)
    observed = _stored_pair(reopened, pair)
    assert observed in ((None, None), (pair.record, pair.preparation))
    assert observed == (
        (pair.record, pair.preparation) if after_commit else (None, None)
    )
