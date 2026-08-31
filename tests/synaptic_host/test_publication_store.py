from __future__ import annotations

from pathlib import Path
import sqlite3
import time
from threading import Event, Thread, current_thread

import pytest

from synaptic_host.publication_store import SqlitePublicationStoreV1
from synaptic_tuner.api.v1 import TrainingRunRef, VerifiedArtifact
from synaptic_tuner.api.v1.publication import (
    PublicationPhaseV1,
    PublicationRecordV1,
    RecoveryDispositionV1,
    TransferDispositionV1,
)
from tuner.execution.coordinator_v1.publication import PublicationCommandV1


def _command(run_id: str = "run-1") -> PublicationCommandV1:
    return PublicationCommandV1.build(
        run=TrainingRunRef(run_id, "project-1"),
        source_identity_digest="1" * 64,
        source_inventory=(VerifiedArtifact("adapter", "2" * 64, 7),),
        destination_ref="local-primary",
        destination_identity_digest="3" * 64,
        destination_configuration_digest="4" * 64,
        destination_policy_digest="5" * 64,
        maximum_artifact_bytes=1024,
        maximum_total_bytes=4096,
        destination_authority_ref="host-authority",
        destination_key_ref="host-key",
    )


def test_claim_get_list_cas_and_reopen_are_durable(tmp_path: Path) -> None:
    database = (tmp_path / "project" / ".synaptic" / "state" / "training.sqlite3").resolve()
    store = SqlitePublicationStoreV1(database, session_ref="a" * 64)
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")

    assert store.claim(claim) == (claim, True)
    assert store.claim(claim) == (claim, False)
    assert store.get(claim.command.publication_id) == claim
    records, complete = store.list("local-primary", 101)
    assert records == (claim,)
    assert complete is True

    failed = claim.transition(
        PublicationPhaseV1.FAILED_BEFORE_EFFECT,
        "2026-08-30T12:00:01Z",
    )
    assert store.compare_and_swap(claim.record_digest, failed) is True
    assert store.compare_and_swap(claim.record_digest, failed) is False
    reopened = SqlitePublicationStoreV1(database, session_ref="b" * 64)
    assert reopened.get(claim.command.publication_id) == failed


def test_active_lease_blocks_recovery_then_expiry_fences_after_restart(
    tmp_path: Path,
) -> None:
    database = (tmp_path / "training.sqlite3").resolve()
    now = [0.0]
    first = SqlitePublicationStoreV1(
        database, lease_time=lambda: now[0], lease_seconds=30,
        session_ref="a" * 64,
    )
    second = SqlitePublicationStoreV1(
        database, lease_time=lambda: now[0], lease_seconds=30,
        session_ref="b" * 64,
    )
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    first.claim(claim)
    admission = first.begin_transfer(
        claim.command.publication_id, claim.record_digest,
        "2026-08-30T12:00:01Z",
    )
    assert admission.disposition is TransferDispositionV1.ACQUIRED

    active = second.recover_transfer(
        claim.command.publication_id, claim.command.command_digest,
        "2026-08-30T12:00:02Z",
    )
    assert active.disposition is RecoveryDispositionV1.ACTIVE
    now[0] = 31.0
    recoverable = second.recover_transfer(
        claim.command.publication_id, claim.command.command_digest,
        "2026-08-30T12:00:03Z",
    )
    assert recoverable.disposition is RecoveryDispositionV1.PERMITTED
    assert recoverable.record.phase is PublicationPhaseV1.AMBIGUOUS
    assert SqlitePublicationStoreV1(
        database, session_ref="c" * 64,
    ).get(claim.command.publication_id) == recoverable.record


def test_corrupt_persisted_record_is_closed_for_reads_and_mutations(
    tmp_path: Path,
) -> None:
    database = (tmp_path / "training.sqlite3").resolve()
    store = SqlitePublicationStoreV1(database, session_ref="a" * 64)
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    store.claim(claim)
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "UPDATE publication_records_v1 SET record_json = ? WHERE publication_id = ?",
            (b"{}", claim.command.publication_id),
        )
        connection.commit()
    finally:
        connection.close()

    for operation in (
        lambda: store.get(claim.command.publication_id),
        lambda: store.begin_transfer(
            claim.command.publication_id, claim.record_digest,
            "2026-08-30T12:00:01Z",
        ),
    ):
        with pytest.raises(
            RuntimeError, match="^host publication persistence failed$",
        ) as captured:
            operation()
        assert captured.value.__cause__ is None
        assert captured.value.__context__ is None


@pytest.mark.parametrize(
    ("column", "value"),
    (("phase", "verified"), ("destination_ref", "hidden-destination")),
)
def test_list_closes_index_metadata_drift(
    tmp_path: Path, column: str, value: str,
) -> None:
    database = (tmp_path / "training.sqlite3").resolve()
    store = SqlitePublicationStoreV1(database, session_ref="a" * 64)
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    store.claim(claim)
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            f"UPDATE publication_records_v1 SET {column} = ? WHERE publication_id = ?",
            (value, claim.command.publication_id),
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(
        RuntimeError, match="^host publication persistence failed$",
    ) as captured:
        store.list("local-primary", 101)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_sqlite_error_is_closed_without_exception_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SqlitePublicationStoreV1(
        (tmp_path / "training.sqlite3").resolve(), session_ref="a" * 64,
    )

    def fail_connect():
        raise sqlite3.OperationalError("private database detail")

    monkeypatch.setattr(store, "_connect", fail_connect)
    with pytest.raises(
        RuntimeError, match="^host publication persistence failed$",
    ) as captured:
        store.get("1" * 64)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_expired_lease_cannot_be_resurrected_by_delayed_heartbeat(
    tmp_path: Path,
) -> None:
    database = (tmp_path / "training.sqlite3").resolve()
    now = [0.0]
    first = SqlitePublicationStoreV1(
        database, lease_time=lambda: now[0], lease_seconds=3,
        session_ref="a" * 64,
    )
    second = SqlitePublicationStoreV1(
        database, lease_time=lambda: now[0], lease_seconds=3,
        session_ref="b" * 64,
    )
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    first.claim(claim)
    first.begin_transfer(
        claim.command.publication_id, claim.record_digest,
        "2026-08-30T12:00:01Z",
    )
    now[0] = 4.0
    time.sleep(1.2)
    recovered = second.recover_transfer(
        claim.command.publication_id, claim.command.command_digest,
        "2026-08-30T12:00:02Z",
    )
    assert recovered.disposition is RecoveryDispositionV1.PERMITTED
    assert recovered.record.phase is PublicationPhaseV1.AMBIGUOUS
    first.close()
    second.close()


def test_close_stops_all_owned_heartbeat_threads(tmp_path: Path) -> None:
    store = SqlitePublicationStoreV1(
        (tmp_path / "training.sqlite3").resolve(), lease_seconds=3,
        session_ref="a" * 64,
    )
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    store.claim(claim)
    store.begin_transfer(
        claim.command.publication_id, claim.record_digest,
        "2026-08-30T12:00:01Z",
    )
    assert store._heartbeats
    store.close()
    assert store._heartbeats == {}


def test_initialization_sqlite_error_is_closed_without_links(tmp_path: Path) -> None:
    class BrokenStore(SqlitePublicationStoreV1):
        def _connect(self):
            raise sqlite3.OperationalError("private initialization detail")

    with pytest.raises(
        RuntimeError, match="^host publication persistence failed$",
    ) as captured:
        BrokenStore(
            (tmp_path / "training.sqlite3").resolve(),
            session_ref="a" * 64,
        )
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None


def test_close_waits_for_blocked_heartbeat_to_finish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SqlitePublicationStoreV1(
        (tmp_path / "training.sqlite3").resolve(), lease_seconds=3,
        session_ref="a" * 64,
    )
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    store.claim(claim)
    original_connect = store._connect
    entered, release = Event(), Event()

    def blocked_connect():
        if current_thread().name.startswith("publication-lease-"):
            entered.set()
            assert release.wait(timeout=5)
        return original_connect()

    monkeypatch.setattr(store, "_connect", blocked_connect)
    store.begin_transfer(
        claim.command.publication_id, claim.record_digest,
        "2026-08-30T12:00:01Z",
    )
    assert entered.wait(timeout=3)
    closer = Thread(target=store.close)
    closer.start()
    time.sleep(0.1)
    assert closer.is_alive()
    release.set()
    closer.join(timeout=5)
    assert not closer.is_alive()
    assert store._heartbeats == {}


def test_close_and_heartbeat_start_are_linearized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SqlitePublicationStoreV1(
        (tmp_path / "training.sqlite3").resolve(), lease_seconds=3,
        session_ref="a" * 64,
    )
    claim = PublicationRecordV1.claim(_command(), "2026-08-30T12:00:00Z")
    store.claim(claim)
    original_start = store._start_heartbeat
    entered, release = Event(), Event()

    def blocked_start(ownership_id: str):
        entered.set()
        assert release.wait(timeout=5)
        original_start(ownership_id)

    monkeypatch.setattr(store, "_start_heartbeat", blocked_start)
    starter = Thread(target=lambda: store.begin_transfer(
        claim.command.publication_id, claim.record_digest,
        "2026-08-30T12:00:01Z",
    ))
    starter.start()
    assert entered.wait(timeout=5)
    closer = Thread(target=store.close)
    closer.start()
    time.sleep(0.1)
    assert closer.is_alive()
    release.set()
    starter.join(timeout=5)
    closer.join(timeout=5)
    assert not starter.is_alive() and not closer.is_alive()
    assert store._heartbeats == {}
    with pytest.raises(RuntimeError, match="store is closed"):
        store.get(claim.command.publication_id)


def test_list_returns_one_atomic_sqlite_snapshot_during_concurrent_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = (tmp_path / "training.sqlite3").resolve()
    first = SqlitePublicationStoreV1(database, session_ref="a" * 64)
    second = SqlitePublicationStoreV1(database, session_ref="b" * 64)
    claim_a = PublicationRecordV1.claim(
        _command("run-a"), "2026-08-30T12:00:00Z",
    )
    claim_b = PublicationRecordV1.claim(
        _command("run-b"), "2026-08-30T12:00:00Z",
    )
    first.claim(claim_a)
    original_load = first._load_in
    entered, release = Event(), Event()

    def blocked_load(connection, publication_id):
        entered.set()
        assert release.wait(timeout=5)
        return original_load(connection, publication_id)

    monkeypatch.setattr(first, "_load_in", blocked_load)
    observed, failures = [], []

    def read_page():
        try:
            observed.append(first.list("local-primary", 101))
        except BaseException as exc:
            failures.append(exc)

    reader = Thread(target=read_page)
    reader.start()
    assert entered.wait(timeout=5)
    second.claim(claim_b)
    failed_a = claim_a.transition(
        PublicationPhaseV1.FAILED_BEFORE_EFFECT,
        "2026-08-30T12:00:01Z",
    )
    assert second.compare_and_swap(claim_a.record_digest, failed_a) is True
    release.set()
    reader.join(timeout=5)
    assert not reader.is_alive()
    assert failures == []
    assert observed == [((claim_a,), True)]
    first.close()
    second.close()
