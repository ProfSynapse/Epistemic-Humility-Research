"""Project-owned durable publication state for the engine publication kernel."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from threading import Event, Lock, RLock, Thread, current_thread
from typing import Callable, Iterator

from synaptic_tuner.api.v1 import ProjectContext
from synaptic_tuner.api.v1.publication import (
    AuthenticatedLookupV1,
    AuthenticatedPublicationReceiptV1,
    AuthenticatedPublicationTombstoneV1,
    LookupRecoveryPermitV1,
    PublicationPhaseV1,
    PublicationRecordV1,
    PublicationTransitionKernelV1,
    RecoveryDecisionV1,
    TransferAdmissionV1,
    TransferDispositionV1,
    TransferOwnershipV1,
)


_LEASE_SECONDS = 30.0


def _closed_persistence_failure(cause: BaseException | None = None) -> None:
    """Raise the persistence failure, chaining `cause` when the caller has one.

    B-18 (section 27.4, site 6).  The parameter defaults to `None` for the
    three call sites that genuinely have no originating exception to name --
    after the metadata predicate, after a row count and after a missing row, all
    ordinary control flow.  Every caller that does have one passes it: the
    decorator below, and the decode handler in `_load_in`, whose bare call the
    27.2 correction found and 27.12 item 2 chained.
    """
    raise RuntimeError("host publication persistence failed") from cause


def _close_sqlite_errors(function):
    """Translate SQLite failures into the closed persistence failure.

    The raise falls outside the `except` block rather than inside it.  That is
    inherited structure and not a design choice -- it destroyed the cause until
    the B-18 fix -- and it puts the raise beyond the handler's `as` binding,
    which Python clears on handler exit.  So the handler copies the original
    into `cause`, and that bound copy is what carries the chain across the
    boundary rather than the translated error chaining from nothing.
    """
    @wraps(function)
    def closed(*args, **kwargs):
        owner = args[0]
        lock = getattr(owner, "_operation_lock", None)

        def invoke():
            if (getattr(owner, "_closed", False)
                    and function.__name__ != "_initialize"):
                raise RuntimeError("host publication store is closed")
            failed = False
            cause: BaseException | None = None
            try:
                return function(*args, **kwargs)
            except sqlite3.Error as error:
                failed = True
                cause = error
            if failed:
                _closed_persistence_failure(cause)
            raise AssertionError("unreachable")

        if lock is None:
            return invoke()
        with lock:
            return invoke()
    return closed


def _detach(value: PublicationRecordV1) -> PublicationRecordV1:
    if type(value) is not PublicationRecordV1:
        raise TypeError("record must be exact PublicationRecordV1")
    return PublicationRecordV1.from_canonical_bytes(value.canonical_bytes)


class SqlitePublicationStoreV1:
    """Transactional PublicationStorePortV1 with renewable process leases."""

    def __init__(
        self,
        database_path: Path,
        *,
        lease_time: Callable[[], float] = time.time,
        lease_seconds: float = _LEASE_SECONDS,
        session_ref: str | None = None,
    ) -> None:
        path = Path(database_path)
        if not path.is_absolute():
            raise ValueError("database_path must be absolute")
        if not callable(lease_time):
            raise TypeError("lease_time must be callable")
        if type(lease_seconds) not in (int, float) or isinstance(lease_seconds, bool):
            raise TypeError("lease_seconds must be a number")
        lease_seconds = float(lease_seconds)
        if not 3.0 <= lease_seconds <= 3600.0:
            raise ValueError("lease_seconds must be between 3 and 3600 seconds")
        if session_ref is None:
            session_ref = hashlib.sha256(os.urandom(32)).hexdigest()
        if (type(session_ref) is not str or len(session_ref) != 64
                or any(char not in "0123456789abcdef" for char in session_ref)):
            raise ValueError("session_ref must be a lowercase SHA-256 digest")
        self.database_path = path.resolve(strict=False)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lease_time = lease_time
        self._lease_seconds = lease_seconds
        self._session_ref = session_ref
        self._operation_lock = RLock()
        self._closed = False
        self._heartbeats: dict[str, tuple[Event, Thread]] = {}
        self._heartbeat_lock = Lock()
        self._initialize()

    @classmethod
    def from_context(
        cls, context: ProjectContext, **kwargs,
    ) -> "SqlitePublicationStoreV1":
        if not isinstance(context, ProjectContext) or context.mode != "host":
            raise ValueError("host project context is required")
        mutable_root = (context.project_root / ".synaptic").resolve(strict=False)
        state_root = context.state_root.resolve(strict=False)
        if not state_root.is_relative_to(mutable_root):
            raise ValueError("state root must remain below the host .synaptic directory")
        return cls(state_root / "training.sqlite3", **kwargs)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path, timeout=30, isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @contextmanager
    def _read_transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            yield connection
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @_close_sqlite_errors
    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS publication_records_v1 (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    publication_id TEXT NOT NULL UNIQUE,
                    command_digest TEXT NOT NULL,
                    destination_ref TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK (revision >= 0),
                    record_digest TEXT NOT NULL UNIQUE,
                    record_json BLOB NOT NULL,
                    ownership_id TEXT,
                    owner_session_ref TEXT,
                    lease_expires_at REAL,
                    CHECK ((ownership_id IS NULL) = (owner_session_ref IS NULL)),
                    CHECK ((ownership_id IS NULL) = (lease_expires_at IS NULL))
                );
                CREATE INDEX IF NOT EXISTS publication_records_v1_destination
                ON publication_records_v1(destination_ref, publication_id);
                CREATE TABLE IF NOT EXISTS publication_ownership_nonces_v1 (
                    nonce INTEGER PRIMARY KEY AUTOINCREMENT
                );
                """
            )
        finally:
            connection.close()

    @staticmethod
    def _decode(raw: bytes) -> PublicationRecordV1:
        return PublicationRecordV1.from_canonical_bytes(bytes(raw))

    @classmethod
    def _load_in(
        cls, connection: sqlite3.Connection, publication_id: str,
    ) -> tuple[PublicationRecordV1, sqlite3.Row] | None:
        row = connection.execute(
            """
            SELECT command_digest, destination_ref, phase, revision,
                   record_digest, record_json, ownership_id,
                   owner_session_ref, lease_expires_at
            FROM publication_records_v1 WHERE publication_id = ?
            """,
            (publication_id,),
        ).fetchone()
        if row is None:
            return None
        decode_cause: BaseException | None = None
        try:
            record = cls._decode(row["record_json"])
        except Exception as error:
            # 27.12 item 2.  The raise below runs outside this handler, where
            # the `as` binding is already gone, so bind a copy here: it is what
            # carries the decode failure into `__cause__`.
            decode_cause = error
        if decode_cause is not None:
            _closed_persistence_failure(decode_cause)
        metadata_matches = (
            record.command.publication_id == publication_id
            and row["command_digest"] == record.command.command_digest
            and row["destination_ref"] == record.command.destination_ref
            and row["phase"] == record.phase.value
            and type(row["revision"]) is int
            and row["revision"] == record.revision
            and row["record_digest"] == record.record_digest
        )
        if not metadata_matches:
            _closed_persistence_failure()
        return record, row

    @staticmethod
    def _insert_in(connection: sqlite3.Connection, record: PublicationRecordV1) -> None:
        connection.execute(
            """
            INSERT INTO publication_records_v1(
                publication_id, command_digest, destination_ref, phase,
                revision, record_digest, record_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.command.publication_id, record.command.command_digest,
                record.command.destination_ref, record.phase.value,
                record.revision, record.record_digest, record.canonical_bytes,
            ),
        )

    @staticmethod
    def _update_in(
        connection: sqlite3.Connection,
        prior: PublicationRecordV1,
        descendant: PublicationRecordV1,
        *,
        ownership_id: str | None,
        owner_session_ref: str | None,
        lease_expires_at: float | None,
    ) -> None:
        owned = _detach(descendant)
        cursor = connection.execute(
            """
            UPDATE publication_records_v1
            SET command_digest = ?, destination_ref = ?, phase = ?, revision = ?,
                record_digest = ?, record_json = ?, ownership_id = ?,
                owner_session_ref = ?, lease_expires_at = ?
            WHERE publication_id = ? AND record_digest = ?
            """,
            (
                owned.command.command_digest, owned.command.destination_ref,
                owned.phase.value, owned.revision, owned.record_digest,
                owned.canonical_bytes, ownership_id, owner_session_ref,
                lease_expires_at, owned.command.publication_id,
                prior.record_digest,
            ),
        )
        if cursor.rowcount != 1:
            _closed_persistence_failure()

    def _lease_expiry(self) -> float:
        now = self._lease_time()
        if type(now) not in (int, float) or isinstance(now, bool):
            raise TypeError("lease_time must return a number")
        return float(now) + self._lease_seconds

    def _row_active(self, row: sqlite3.Row, ownership_id: str | None = None) -> bool:
        observed = row["ownership_id"]
        expiry = row["lease_expires_at"]
        return (
            type(observed) is str
            and (ownership_id is None or observed == ownership_id)
            and type(expiry) is float
            and expiry > float(self._lease_time())
        )

    def _owned_active(self, row: sqlite3.Row, ownership_id: str) -> bool:
        return (
            row["owner_session_ref"] == self._session_ref
            and self._row_active(row, ownership_id)
        )

    def _start_heartbeat(self, ownership_id: str) -> None:
        event = Event()

        def renew() -> None:
            interval = self._lease_seconds / 3.0
            while not event.wait(interval):
                try:
                    with self._transaction() as connection:
                        observed_at = float(self._lease_time())
                        renewed_until = observed_at + self._lease_seconds
                        cursor = connection.execute(
                            """
                            UPDATE publication_records_v1 SET lease_expires_at = ?
                            WHERE ownership_id = ? AND owner_session_ref = ?
                              AND phase IN ('transferring', 'committed')
                              AND lease_expires_at > ?
                            """,
                            (
                                renewed_until, ownership_id,
                                self._session_ref, observed_at,
                            ),
                        )
                    if cursor.rowcount != 1:
                        break
                except Exception:
                    break
            with self._heartbeat_lock:
                current = self._heartbeats.get(ownership_id)
                if current is not None and current[0] is event:
                    self._heartbeats.pop(ownership_id, None)

        thread = Thread(
            target=renew, name=f"publication-lease-{ownership_id[:12]}",
            daemon=True,
        )
        with self._heartbeat_lock:
            if self._closed:
                return
            if ownership_id in self._heartbeats:
                return
            self._heartbeats[ownership_id] = (event, thread)
            try:
                thread.start()
            except BaseException:
                self._heartbeats.pop(ownership_id, None)
                raise

    def _stop_heartbeat(self, ownership_id: str) -> None:
        with self._heartbeat_lock:
            heartbeat = self._heartbeats.pop(ownership_id, None)
        if heartbeat is not None:
            event, thread = heartbeat
            event.set()
            if thread is not current_thread():
                thread.join()

    def close(self) -> None:
        """Stop and join every renewal thread owned by this store instance."""
        with self._operation_lock:
            with self._heartbeat_lock:
                self._closed = True
                heartbeats = tuple(self._heartbeats.values())
                for event, _ in heartbeats:
                    event.set()
            for _, thread in heartbeats:
                if thread is not current_thread():
                    thread.join()
            with self._heartbeat_lock:
                for ownership_id, heartbeat in tuple(self._heartbeats.items()):
                    if heartbeat in heartbeats:
                        self._heartbeats.pop(ownership_id, None)

    def __enter__(self) -> "SqlitePublicationStoreV1":
        if self._closed:
            raise RuntimeError("host publication store is closed")
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    @_close_sqlite_errors
    def claim(self, record: PublicationRecordV1):
        candidate = _detach(record)
        try:
            with self._transaction() as connection:
                loaded = self._load_in(
                    connection, candidate.command.publication_id,
                )
                current = None if loaded is None else loaded[0]
                result, created = PublicationTransitionKernelV1.claim(
                    current, candidate,
                )
                if created:
                    self._insert_in(connection, result)
                return _detach(result), created
        except sqlite3.Error:
            raise

    @_close_sqlite_errors
    def get(self, publication_id: str) -> PublicationRecordV1 | None:
        try:
            connection = self._connect()
            try:
                loaded = self._load_in(connection, publication_id)
            finally:
                connection.close()
        except sqlite3.Error:
            raise
        return None if loaded is None else _detach(loaded[0])

    @_close_sqlite_errors
    def compare_and_swap(
        self, expected_record_digest: str, descendant: PublicationRecordV1,
    ) -> bool:
        candidate = _detach(descendant)
        try:
            with self._transaction() as connection:
                loaded = self._load_in(
                    connection, candidate.command.publication_id,
                )
                current = None if loaded is None else loaded[0]
                result, changed = PublicationTransitionKernelV1.compare_and_swap(
                    current, expected_record_digest, candidate,
                )
                if changed:
                    self._update_in(
                        connection, current, result, ownership_id=None,
                        owner_session_ref=None, lease_expires_at=None,
                    )
                return changed
        except sqlite3.Error:
            raise

    @_close_sqlite_errors
    def begin_transfer(
        self, publication_id: str, expected_record_digest: str, timestamp: str,
    ) -> TransferAdmissionV1:
        try:
            with self._transaction() as connection:
                loaded = self._load_in(connection, publication_id)
                current = None if loaded is None else loaded[0]
                nonce = 1
                if (current is not None
                        and current.phase is PublicationPhaseV1.CLAIMED
                        and current.record_digest == expected_record_digest):
                    nonce = connection.execute(
                        "INSERT INTO publication_ownership_nonces_v1 DEFAULT VALUES"
                    ).lastrowid
                admission = PublicationTransitionKernelV1.begin_transfer(
                    current, publication_id, expected_record_digest, timestamp,
                    nonce,
                )
                if admission.disposition is TransferDispositionV1.ACQUIRED:
                    owner = admission.ownership
                    self._update_in(
                        connection, current, admission.record,
                        ownership_id=owner.ownership_id,
                        owner_session_ref=self._session_ref,
                        lease_expires_at=self._lease_expiry(),
                    )
        except sqlite3.Error:
            raise
        if admission.disposition is TransferDispositionV1.ACQUIRED:
            self._start_heartbeat(admission.ownership.ownership_id)
        return TransferAdmissionV1(
            admission.disposition, _detach(admission.record), admission.ownership,
        )

    @_close_sqlite_errors
    def complete_transfer(
        self, ownership: TransferOwnershipV1,
        receipt: AuthenticatedPublicationReceiptV1,
        verified: bool,
        timestamp: str,
    ) -> PublicationRecordV1:
        try:
            with self._transaction() as connection:
                loaded = self._load_in(connection, ownership.publication_id)
                current, row = (None, None) if loaded is None else loaded
                result = PublicationTransitionKernelV1.complete_transfer(
                    current, ownership, receipt, verified, timestamp,
                    ownership_active=(
                        row is not None
                        and self._owned_active(row, ownership.ownership_id)
                    ),
                )
                self._update_in(
                    connection, current, result,
                    ownership_id=None if verified else ownership.ownership_id,
                    owner_session_ref=None if verified else self._session_ref,
                    lease_expires_at=None if verified else self._lease_expiry(),
                )
        except sqlite3.Error:
            raise
        if verified:
            self._stop_heartbeat(ownership.ownership_id)
        return _detach(result)

    @_close_sqlite_errors
    def relinquish_uncertain(
        self, ownership: TransferOwnershipV1, timestamp: str,
    ) -> RecoveryDecisionV1:
        try:
            with self._transaction() as connection:
                loaded = self._load_in(connection, ownership.publication_id)
                current, row = (None, None) if loaded is None else loaded
                decision = PublicationTransitionKernelV1.relinquish_uncertain(
                    current, ownership, timestamp,
                    ownership_active=(
                        row is not None
                        and self._owned_active(row, ownership.ownership_id)
                    ),
                )
                self._update_in(
                    connection, current, decision.record, ownership_id=None,
                    owner_session_ref=None, lease_expires_at=None,
                )
        except sqlite3.Error:
            raise
        self._stop_heartbeat(ownership.ownership_id)
        return RecoveryDecisionV1(
            decision.disposition, _detach(decision.record), decision.permit,
        )

    @_close_sqlite_errors
    def recover_transfer(
        self, publication_id: str, command_digest: str, timestamp: str,
    ) -> RecoveryDecisionV1:
        try:
            with self._transaction() as connection:
                loaded = self._load_in(connection, publication_id)
                current, row = (None, None) if loaded is None else loaded
                decision = PublicationTransitionKernelV1.recover_transfer(
                    current, publication_id, command_digest, timestamp,
                    ownership_active=(
                        row is not None and self._row_active(row)
                    ),
                )
                if current is not None and decision.record != current:
                    self._update_in(
                        connection, current, decision.record, ownership_id=None,
                        owner_session_ref=None, lease_expires_at=None,
                    )
        except sqlite3.Error:
            raise
        return RecoveryDecisionV1(
            decision.disposition, _detach(decision.record), decision.permit,
        )

    @_close_sqlite_errors
    def finalize_recovery(
        self,
        permit: LookupRecoveryPermitV1,
        phase: PublicationPhaseV1,
        timestamp: str,
        outcome: AuthenticatedLookupV1,
        receipt: AuthenticatedPublicationReceiptV1 | None = None,
        tombstone: AuthenticatedPublicationTombstoneV1 | None = None,
    ) -> PublicationRecordV1:
        try:
            with self._transaction() as connection:
                loaded = self._load_in(connection, permit.publication_id)
                current = None if loaded is None else loaded[0]
                result = PublicationTransitionKernelV1.finalize_recovery(
                    current, permit, phase, timestamp, outcome,
                    receipt=receipt, tombstone=tombstone,
                )
                self._update_in(
                    connection, current, result, ownership_id=None,
                    owner_session_ref=None, lease_expires_at=None,
                )
        except sqlite3.Error:
            raise
        return _detach(result)

    @_close_sqlite_errors
    def list(
        self, destination_ref: str, limit: int,
    ) -> tuple[tuple[PublicationRecordV1, ...], bool]:
        if type(destination_ref) is not str or not destination_ref:
            raise ValueError("destination_ref is required")
        if type(limit) is not int or limit != 101:
            raise ValueError("publication list probe limit must be 101")
        try:
            with self._read_transaction() as connection:
                rows = connection.execute(
                    """
                    SELECT publication_id FROM publication_records_v1
                    ORDER BY publication_id ASC
                    """
                ).fetchall()
                values = []
                for row in rows:
                    loaded = self._load_in(connection, row["publication_id"])
                    if loaded is None:
                        _closed_persistence_failure()
                    if loaded[0].command.destination_ref == destination_ref:
                        values.append(_detach(loaded[0]))
        except sqlite3.Error:
            raise
        return tuple(values[:limit]), len(values) <= 100


__all__ = ["SqlitePublicationStoreV1"]
