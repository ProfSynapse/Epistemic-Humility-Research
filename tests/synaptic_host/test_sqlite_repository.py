from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import (
    EventCode,
    LifecycleEvent,
    LifecyclePhase,
    MessageCode,
    ProjectContext,
    ReplayDisposition,
    RevisionConflict,
)
from tuner.execution.lifecycle import initial_record
from synaptic_host import SqliteTrainingRepository

NOW = "2026-08-26T12:00:00Z"


def repository(tmp_path: Path) -> SqliteTrainingRepository:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    engine.mkdir(parents=True)
    context = ProjectContext.host(engine_root=engine, project_root=project)
    return SqliteTrainingRepository.from_context(context, clock=lambda: NOW)


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
