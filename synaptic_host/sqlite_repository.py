"""Host-owned SQLite durability for Synaptic Tuner training operations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator

from synaptic_tuner.api.v1 import (
    AttemptAdmission,
    AttemptDisposition,
    AuthorizationMismatch,
    EffectCollision,
    EffectDisposition,
    EffectRecord,
    EffectState,
    EventCode,
    InvalidTransition,
    LifecycleEvent,
    LifecyclePhase,
    LifecycleRecord,
    LifecycleRunPage,
    MessageCode,
    ProjectContext,
    ReplayDisposition,
    RevisionConflict,
    RunAlreadyExists,
    RunNotFound,
    apply_lifecycle_event,
)
from synaptic_tuner.api.v1.modal import (
    ModalDurablePreparationV1,
    ModalPreparedRunV1,
    ModalTrainingRepository,
)

from .docker_execution_state import (
    DockerRunMutationRecordV1,
    ProviderPreparationRecordV1,
    validate_docker_run_transition_v1,
)

_SCHEMA_VERSION_V1 = "synaptic-host-sqlite/v1"
_SCHEMA_VERSION = "synaptic-host-sqlite/v2"

_BASE_TABLE_COLUMNS = {
    "schema_meta": ("key", "value"),
    "lifecycle_records": (
        "sequence", "project_ref", "run_id", "revision", "record_json",
    ),
    "consumed_grants": ("grant_ref", "project_ref", "run_id"),
    "modal_preparations": (
        "project_ref", "run_id", "effect_id", "preparation_json",
    ),
    "evidence_replay": (
        "purpose", "issuer_ref", "evidence_ref", "challenge_nonce",
        "audience_ref", "payload_digest", "expires_at",
    ),
}
_DOCKER_TABLE_COLUMNS = {
    "provider_preparations": (
        "project_ref", "run_id", "plan_fingerprint", "preparation_digest",
        "record_json",
    ),
    "docker_run_mutations": (
        "project_ref", "run_id", "effect_id", "preparation_digest", "phase",
        "revision", "record_digest", "record_json",
    ),
}
_COEXISTING_TABLES = frozenset({
    "publication_records_v1", "publication_ownership_nonces_v1",
})


def _utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _closed_prepared_run_failure() -> None:
    raise RuntimeError("host prepared-run persistence failed") from None


class SqliteTrainingRepository(ModalTrainingRepository):
    """Atomic lifecycle, Modal preparation, and replay persistence."""

    def __init__(self, database_path: Path, *, clock: Callable[[], str]) -> None:
        path = Path(database_path)
        if not path.is_absolute():
            raise ValueError("database_path must be absolute")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self.database_path = path.resolve(strict=False)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._initialize()

    @classmethod
    def from_context(
        cls, context: ProjectContext, *, clock: Callable[[], str]
    ) -> "SqliteTrainingRepository":
        if not isinstance(context, ProjectContext) or context.mode != "host":
            raise ValueError("host project context is required")
        mutable_root = (context.project_root / ".synaptic").resolve(strict=False)
        state_root = context.state_root.resolve(strict=False)
        if not state_root.is_relative_to(mutable_root):
            raise ValueError("state root must remain below the host .synaptic directory")
        return cls(state_root / "training.sqlite3", clock=clock)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            isolation_level=None,
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

    def _initialize(self) -> None:
        connection = self._connect()
        try:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("BEGIN IMMEDIATE")
            tables = {
                str(row["name"])
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
                if row["name"] != "sqlite_sequence"
            }
            unknown = tables - (
                frozenset(_BASE_TABLE_COLUMNS)
                | frozenset(_DOCKER_TABLE_COLUMNS)
                | _COEXISTING_TABLES
            )
            if unknown:
                raise RuntimeError("unsupported Synaptic host database schema")
            existing = None
            if "schema_meta" in tables:
                self._require_table_shapes(connection, _BASE_TABLE_COLUMNS)
                rows = connection.execute(
                    "SELECT key, value FROM schema_meta"
                ).fetchall()
                if len(rows) != 1 or rows[0]["key"] != "schema_version":
                    raise RuntimeError("unsupported Synaptic host database schema")
                existing = rows[0]["value"]
            elif tables - _COEXISTING_TABLES:
                raise RuntimeError("unsupported Synaptic host database schema")

            if existing is None:
                self._create_base_schema(connection)
                self._create_docker_schema(connection)
                connection.execute(
                    "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?)",
                    (_SCHEMA_VERSION,),
                )
            elif existing == _SCHEMA_VERSION_V1:
                if tables & frozenset(_DOCKER_TABLE_COLUMNS):
                    raise RuntimeError("unsupported Synaptic host database schema")
                self._create_docker_schema(connection)
                connection.execute(
                    "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
                    (_SCHEMA_VERSION,),
                )
            elif existing == _SCHEMA_VERSION:
                self._require_table_shapes(connection, _DOCKER_TABLE_COLUMNS)
            else:
                raise RuntimeError("unsupported Synaptic host database schema")

            self._require_table_shapes(connection, _BASE_TABLE_COLUMNS)
            self._require_table_shapes(connection, _DOCKER_TABLE_COLUMNS)
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    @staticmethod
    def _require_table_shapes(
        connection: sqlite3.Connection,
        expected: dict[str, tuple[str, ...]],
    ) -> None:
        for table, columns in expected.items():
            observed = tuple(
                str(row["name"])
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            )
            if observed != columns:
                raise RuntimeError("unsupported Synaptic host database schema")

    @staticmethod
    def _create_base_schema(connection: sqlite3.Connection) -> None:
        statements = (
            """CREATE TABLE schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )""",
            """CREATE TABLE lifecycle_records (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_ref TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    revision INTEGER NOT NULL CHECK (revision >= 1),
                    record_json BLOB NOT NULL,
                    UNIQUE (project_ref, run_id)
                )""",
            """CREATE TABLE consumed_grants (
                    grant_ref TEXT PRIMARY KEY,
                    project_ref TEXT NOT NULL,
                    run_id TEXT NOT NULL
                )""",
            """CREATE TABLE modal_preparations (
                    project_ref TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    effect_id TEXT NOT NULL UNIQUE,
                    preparation_json BLOB NOT NULL,
                    PRIMARY KEY (project_ref, run_id),
                    FOREIGN KEY (project_ref, run_id)
                        REFERENCES lifecycle_records(project_ref, run_id)
                        ON DELETE RESTRICT
                )""",
            """CREATE TABLE evidence_replay (
                    purpose TEXT NOT NULL,
                    issuer_ref TEXT NOT NULL,
                    evidence_ref TEXT NOT NULL,
                    challenge_nonce TEXT NOT NULL,
                    audience_ref TEXT NOT NULL,
                    payload_digest TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (purpose, challenge_nonce)
                )""",
            )
        for statement in statements:
            connection.execute(statement)

    @staticmethod
    def _create_docker_schema(connection: sqlite3.Connection) -> None:
        connection.execute(
            """CREATE TABLE provider_preparations (
                project_ref TEXT NOT NULL,
                run_id TEXT NOT NULL,
                plan_fingerprint TEXT NOT NULL,
                preparation_digest TEXT NOT NULL UNIQUE,
                record_json BLOB NOT NULL,
                PRIMARY KEY (project_ref, run_id),
                FOREIGN KEY (project_ref, run_id)
                    REFERENCES lifecycle_records(project_ref, run_id)
                    ON DELETE RESTRICT
            )"""
        )
        connection.execute(
            """CREATE TABLE docker_run_mutations (
                project_ref TEXT NOT NULL,
                run_id TEXT NOT NULL,
                effect_id TEXT NOT NULL UNIQUE,
                preparation_digest TEXT NOT NULL,
                phase TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK (revision >= 1),
                record_digest TEXT NOT NULL UNIQUE,
                record_json BLOB NOT NULL,
                PRIMARY KEY (project_ref, run_id),
                FOREIGN KEY (project_ref, run_id)
                    REFERENCES provider_preparations(project_ref, run_id)
                    ON DELETE RESTRICT
            )"""
        )

    @staticmethod
    def _decode(value: bytes) -> LifecycleRecord:
        return LifecycleRecord.from_canonical_bytes(bytes(value))

    @classmethod
    def _load_in(
        cls, connection: sqlite3.Connection, project_ref: str, run_id: str
    ) -> tuple[int, LifecycleRecord] | None:
        row = connection.execute(
            """
            SELECT sequence, record_json
            FROM lifecycle_records
            WHERE project_ref = ? AND run_id = ?
            """,
            (project_ref, run_id),
        ).fetchone()
        if row is None:
            return None
        return int(row["sequence"]), cls._decode(row["record_json"])

    @staticmethod
    def _update_in(
        connection: sqlite3.Connection,
        record: LifecycleRecord,
        *,
        expected_revision: int,
    ) -> None:
        cursor = connection.execute(
            """
            UPDATE lifecycle_records
            SET revision = ?, record_json = ?
            WHERE project_ref = ? AND run_id = ? AND revision = ?
            """,
            (
                record.revision,
                record.canonical_bytes,
                record.project_ref,
                record.run_id,
                expected_revision,
            ),
        )
        if cursor.rowcount != 1:
            raise RevisionConflict("revision")

    def create(self, record: LifecycleRecord) -> LifecycleRecord:
        if not isinstance(record, LifecycleRecord):
            raise TypeError("record must be LifecycleRecord")
        try:
            with self._transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO lifecycle_records(
                        project_ref, run_id, revision, record_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        record.project_ref,
                        record.run_id,
                        record.revision,
                        record.canonical_bytes,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise RunAlreadyExists("run already exists") from exc
        return record

    def load(self, project_ref: str, run_id: str) -> LifecycleRecord | None:
        connection = self._connect()
        try:
            loaded = self._load_in(connection, project_ref, run_id)
            return None if loaded is None else loaded[1]
        finally:
            connection.close()

    def append(
        self,
        project_ref: str,
        run_id: str,
        *,
        expected_revision: int,
        event: LifecycleEvent,
    ) -> LifecycleRecord:
        with self._transaction() as connection:
            loaded = self._load_in(connection, project_ref, run_id)
            if loaded is None:
                raise RunNotFound("run was not found")
            old = loaded[1]
            if old.revision != expected_revision:
                raise RevisionConflict("revision")
            new = apply_lifecycle_event(old, event)
            self._update_in(connection, new, expected_revision=expected_revision)
            return new

    def compare_and_consume_attempt(
        self,
        project_ref: str,
        run_id: str,
        *,
        expected_revision: int,
        grant_ref: str,
        canonical_command: object,
    ) -> AttemptAdmission:
        raw = getattr(canonical_command, "canonical_bytes", None)
        command_digest = getattr(canonical_command, "digest", None)
        effect_identity = getattr(canonical_command, "effect", None)
        if not isinstance(raw, bytes) or not isinstance(command_digest, str):
            raise TypeError("canonical command is required")
        with self._transaction() as connection:
            loaded = self._load_in(connection, project_ref, run_id)
            if loaded is None:
                raise RunNotFound("run was not found")
            old = loaded[1]
            for effect in old.effects:
                same_identity = effect.identity.effect_id == effect_identity.effect_id
                same_key = (
                    effect.identity.kind is effect_identity.kind
                    and effect.identity.effect_key == effect_identity.effect_key
                )
                if same_identity or same_key:
                    if (
                        effect.command_digest == command_digest
                        and effect.canonical_command == raw
                    ):
                        return AttemptAdmission(
                            old, effect, AttemptDisposition.LOOKUP_ONLY
                        )
                    raise EffectCollision("canonical command collision")
            if old.revision != expected_revision:
                raise RevisionConflict("revision")
            grant = old.grant_binding
            consumed = connection.execute(
                "SELECT 1 FROM consumed_grants WHERE grant_ref = ?", (grant_ref,)
            ).fetchone()
            now_text = self.clock()
            now = _utc(now_text)
            command = canonical_command
            matches = grant is not None and all(
                (
                    grant.grant_ref == grant_ref,
                    consumed is None,
                    grant.project_ref == project_ref,
                    grant.operation_key == command.effect.effect_key,
                    grant.effect_kind is command.effect.kind,
                    grant.scope == command.effect.scope,
                    grant.plan_fingerprint == command.plan_fingerprint,
                    grant.source_digest == command.source_digest,
                    grant.workload_digest == command.workload_digest,
                    grant.artifact_slot_ref == command.artifact_slot_ref,
                    grant.allowed_secret_refs_digest == command.allowed_secret_refs_digest,
                    grant.quote_digest == command.quote_digest,
                    grant.resource_digest == command.resource_digest,
                    grant.operation_binding_digest == command.operation_binding_digest,
                    _utc(grant.issued_at) <= now < _utc(grant.expires_at),
                )
            )
            if not matches:
                raise AuthorizationMismatch("grant mismatch or expired")
            if command.effect.kind.value == "cancel" and not any(
                effect.identity.kind.value == "submit"
                and effect.state is EffectState.FOUND
                and effect.provider_job_ref == command.target_provider_job_ref
                for effect in old.effects
            ):
                raise AuthorizationMismatch("unconfirmed cancel target")
            effect = EffectRecord(
                command.effect,
                grant.fingerprint,
                EffectState.ATTEMPTED,
                grant_ref=grant_ref,
                command_digest=command_digest,
                canonical_command=raw,
                attempt_count=1,
            )
            event = LifecycleEvent(
                EventCode.EFFECT_ATTEMPTED,
                now_text,
                MessageCode.EFFECT_MUTATION_ATTEMPTED,
                effect=effect,
            )
            new = apply_lifecycle_event(old, event)
            connection.execute(
                """
                INSERT INTO consumed_grants(grant_ref, project_ref, run_id)
                VALUES (?, ?, ?)
                """,
                (grant_ref, project_ref, run_id),
            )
            self._update_in(connection, new, expected_revision=expected_revision)
            return AttemptAdmission(new, effect, AttemptDisposition.EXECUTE_NOW)

    def record_attempt_outcome(
        self,
        project_ref: str,
        run_id: str,
        *,
        expected_revision: int,
        command_digest: str,
        observation: object,
    ) -> LifecycleRecord:
        with self._transaction() as connection:
            loaded = self._load_in(connection, project_ref, run_id)
            if loaded is None:
                raise RunNotFound("run was not found")
            old = loaded[1]
            if old.revision != expected_revision:
                raise RevisionConflict("revision")
            effect = next(
                (item for item in old.effects if item.identity == observation.identity),
                None,
            )
            if effect is None or effect.command_digest != command_digest:
                raise EffectCollision("outcome binding mismatch")
            wanted = {
                EffectDisposition.FOUND: EffectState.FOUND,
                EffectDisposition.DEFINITELY_ABSENT: EffectState.DEFINITELY_ABSENT,
                EffectDisposition.INDETERMINATE: EffectState.INDETERMINATE,
            }[observation.disposition]
            if effect.state in {EffectState.FOUND, EffectState.DEFINITELY_ABSENT}:
                identical = (
                    effect.state is wanted
                    and effect.provider_job_ref == observation.provider_job_ref
                    and effect.receipt_digest == observation.receipt_digest
                )
                if identical:
                    return old
                raise InvalidTransition("closed outcome conflict")
            if effect.state not in {EffectState.ATTEMPTED, EffectState.INDETERMINATE}:
                raise InvalidTransition("effect is not outcome-recordable")
            updated = replace(
                effect,
                state=wanted,
                provider_job_ref=observation.provider_job_ref,
                receipt_digest=observation.receipt_digest,
            )
            code, message = {
                EffectState.FOUND: (EventCode.EFFECT_FOUND, MessageCode.EFFECT_CONFIRMED),
                EffectState.DEFINITELY_ABSENT: (
                    EventCode.EFFECT_DEFINITELY_ABSENT,
                    MessageCode.EFFECT_ABSENT,
                ),
                EffectState.INDETERMINATE: (
                    EventCode.EFFECT_INDETERMINATE,
                    MessageCode.EFFECT_OUTCOME_UNKNOWN,
                ),
            }[wanted]
            new = apply_lifecycle_event(
                old, LifecycleEvent(code, self.clock(), message, effect=updated)
            )
            self._update_in(connection, new, expected_revision=expected_revision)
            return new

    def list_runs(
        self,
        project_ref: str,
        *,
        limit: int,
        cursor: str | None = None,
    ) -> LifecycleRunPage:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        try:
            after = 0 if cursor is None else int(cursor)
        except (TypeError, ValueError) as exc:
            raise ValueError("cursor must be a sequence integer") from exc
        if after < 0 or (cursor is not None and str(after) != cursor):
            raise ValueError("cursor must be a canonical sequence integer")
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT sequence, record_json
                FROM lifecycle_records
                WHERE project_ref = ? AND sequence > ?
                ORDER BY sequence ASC
                LIMIT ?
                """,
                (project_ref, after, limit + 1),
            ).fetchall()
        finally:
            connection.close()
        visible = rows[:limit]
        next_cursor = str(visible[-1]["sequence"]) if len(rows) > limit else None
        return LifecycleRunPage(
            tuple(self._decode(row["record_json"]) for row in visible), next_cursor
        )

    @staticmethod
    def _insert_modal_preparation_in(
        connection: sqlite3.Connection, value: ModalPreparedRunV1
    ) -> None:
        connection.execute(
            """
            INSERT INTO modal_preparations(
                project_ref, run_id, effect_id, preparation_json
            ) VALUES (?, ?, ?, ?)
            """,
            (
                value.record.project_ref,
                value.record.run_id,
                value.preparation.operation.effect.effect_id,
                value.preparation.canonical_bytes,
            ),
        )

    def create_modal_prepared_run(self, value: ModalPreparedRunV1) -> None:
        """Atomically create one exact revision-4 run and Modal preparation."""

        detachment_failed = False
        try:
            if type(value) is not ModalPreparedRunV1:
                raise TypeError
            detached = ModalPreparedRunV1(
                LifecycleRecord.from_canonical_bytes(value.record.canonical_bytes),
                ModalDurablePreparationV1.from_canonical_bytes(
                    value.preparation.canonical_bytes
                ),
            )
            if detached != value:
                raise ValueError
        except Exception:
            detachment_failed = True
        if detachment_failed:
            _closed_prepared_run_failure()

        disposition = "created"
        transaction_failed = False
        try:
            with self._transaction() as connection:
                if self._load_in(
                    connection, detached.record.project_ref, detached.record.run_id
                ) is not None:
                    disposition = "run_exists"
                else:
                    collision = connection.execute(
                        """
                        SELECT 1 FROM modal_preparations
                        WHERE effect_id = ?
                        """,
                        (detached.preparation.operation.effect.effect_id,),
                    ).fetchone()
                    if collision is not None:
                        disposition = "effect_collision"
                    else:
                        connection.execute(
                            """
                            INSERT INTO lifecycle_records(
                                project_ref, run_id, revision, record_json
                            ) VALUES (?, ?, ?, ?)
                            """,
                            (
                                detached.record.project_ref,
                                detached.record.run_id,
                                detached.record.revision,
                                detached.record.canonical_bytes,
                            ),
                        )
                        self._insert_modal_preparation_in(connection, detached)
        except Exception:
            transaction_failed = True
        if transaction_failed:
            _closed_prepared_run_failure()
        if disposition == "run_exists":
            raise RunAlreadyExists("run already exists") from None
        if disposition == "effect_collision":
            raise EffectCollision("Modal preparation collision") from None

    def load_modal_preparation(
        self, project_ref: str, run_id: str
    ) -> ModalDurablePreparationV1 | None:
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT preparation_json FROM modal_preparations
                WHERE project_ref = ? AND run_id = ?
                """,
                (project_ref, run_id),
            ).fetchone()
        finally:
            connection.close()
        return (
            None
            if row is None
            else ModalDurablePreparationV1.from_canonical_bytes(
                bytes(row["preparation_json"])
            )
        )

    def load_modal_preparation_by_effect(
        self, effect_id: str
    ) -> ModalDurablePreparationV1 | None:
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT preparation_json FROM modal_preparations
                WHERE effect_id = ?
                """,
                (effect_id,),
            ).fetchone()
        finally:
            connection.close()
        return (
            None
            if row is None
            else ModalDurablePreparationV1.from_canonical_bytes(
                bytes(row["preparation_json"])
            )
        )

    @staticmethod
    def _decode_docker_preparation(raw: bytes) -> ProviderPreparationRecordV1:
        try:
            return ProviderPreparationRecordV1.from_canonical_bytes(bytes(raw))
        except Exception:
            raise RuntimeError("host Docker persistence is invalid") from None

    @staticmethod
    def _decode_docker_mutation(raw: bytes) -> DockerRunMutationRecordV1:
        try:
            return DockerRunMutationRecordV1.from_canonical_bytes(bytes(raw))
        except Exception:
            raise RuntimeError("host Docker persistence is invalid") from None

    @classmethod
    def _load_docker_preparation_in(
        cls,
        connection: sqlite3.Connection,
        project_ref: str,
        run_id: str,
    ) -> ProviderPreparationRecordV1 | None:
        row = connection.execute(
            """SELECT plan_fingerprint, preparation_digest, record_json
               FROM provider_preparations
               WHERE project_ref = ? AND run_id = ?""",
            (project_ref, run_id),
        ).fetchone()
        if row is None:
            return None
        record = cls._decode_docker_preparation(row["record_json"])
        if (
            record.project_ref != project_ref
            or record.run_id != run_id
            or record.plan_fingerprint != row["plan_fingerprint"]
            or record.preparation_digest != row["preparation_digest"]
        ):
            raise RuntimeError("host Docker persistence is invalid")
        return record

    @classmethod
    def _load_docker_mutation_in(
        cls,
        connection: sqlite3.Connection,
        project_ref: str,
        run_id: str,
    ) -> DockerRunMutationRecordV1 | None:
        row = connection.execute(
            """SELECT effect_id, preparation_digest, phase, revision,
                      record_digest, record_json
               FROM docker_run_mutations
               WHERE project_ref = ? AND run_id = ?""",
            (project_ref, run_id),
        ).fetchone()
        if row is None:
            return None
        record = cls._decode_docker_mutation(row["record_json"])
        if (
            record.project_ref != project_ref
            or record.run_id != run_id
            or record.effect_id != row["effect_id"]
            or record.preparation_digest != row["preparation_digest"]
            or record.phase.value != row["phase"]
            or record.revision != row["revision"]
            or record.record_digest != row["record_digest"]
        ):
            raise RuntimeError("host Docker persistence is invalid")
        return record

    def create_docker_prepared_run(
        self,
        preparation: ProviderPreparationRecordV1,
        initial_mutation: DockerRunMutationRecordV1,
    ) -> None:
        """Atomically persist one immutable preparation and admitted create."""

        if (
            type(preparation) is not ProviderPreparationRecordV1
            or type(initial_mutation) is not DockerRunMutationRecordV1
            or initial_mutation.project_ref != preparation.project_ref
            or initial_mutation.run_id != preparation.run_id
            or initial_mutation.effect_id != preparation.effect_id
            or initial_mutation.preparation_digest != preparation.preparation_digest
            or initial_mutation.revision != 1
            or initial_mutation
            != DockerRunMutationRecordV1.initial(
                preparation, initial_mutation.create_mutation
            )
        ):
            raise ValueError("Docker prepared run pair is invalid")
        try:
            with self._transaction() as connection:
                connection.execute(
                    """INSERT INTO provider_preparations(
                           project_ref, run_id, plan_fingerprint,
                           preparation_digest, record_json
                       ) VALUES (?, ?, ?, ?, ?)""",
                    (
                        preparation.project_ref,
                        preparation.run_id,
                        preparation.plan_fingerprint,
                        preparation.preparation_digest,
                        preparation.canonical_bytes,
                    ),
                )
                connection.execute(
                    """INSERT INTO docker_run_mutations(
                           project_ref, run_id, effect_id, preparation_digest,
                           phase, revision, record_digest, record_json
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        initial_mutation.project_ref,
                        initial_mutation.run_id,
                        initial_mutation.effect_id,
                        initial_mutation.preparation_digest,
                        initial_mutation.phase.value,
                        initial_mutation.revision,
                        initial_mutation.record_digest,
                        initial_mutation.canonical_bytes,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise EffectCollision("Docker preparation collision") from exc

    def load_docker_preparation(
        self, project_ref: str, run_id: str
    ) -> ProviderPreparationRecordV1 | None:
        connection = self._connect()
        try:
            return self._load_docker_preparation_in(connection, project_ref, run_id)
        finally:
            connection.close()

    def load_docker_run_mutation(
        self, project_ref: str, run_id: str
    ) -> DockerRunMutationRecordV1 | None:
        connection = self._connect()
        try:
            return self._load_docker_mutation_in(connection, project_ref, run_id)
        finally:
            connection.close()

    def compare_and_swap_docker_run_mutation(
        self,
        replacement: DockerRunMutationRecordV1,
        *,
        expected_revision: int,
        expected_record_digest: str,
    ) -> DockerRunMutationRecordV1:
        """Advance one aggregate only from the exact prior revision and digest."""

        if type(replacement) is not DockerRunMutationRecordV1:
            raise TypeError("replacement must be DockerRunMutationRecordV1")
        if (
            replacement.revision != expected_revision + 1
            or replacement.previous_record_digest != expected_record_digest
        ):
            raise RevisionConflict("Docker mutation revision")
        with self._transaction() as connection:
            current = self._load_docker_mutation_in(
                connection, replacement.project_ref, replacement.run_id
            )
            if current is None:
                raise RunNotFound("Docker run mutation was not found")
            if (
                current.revision != expected_revision
                or current.record_digest != expected_record_digest
                or current.effect_id != replacement.effect_id
                or current.preparation_digest != replacement.preparation_digest
            ):
                raise RevisionConflict("Docker mutation revision")
            try:
                validate_docker_run_transition_v1(current, replacement)
            except ValueError:
                raise InvalidTransition("Docker mutation transition") from None
            cursor = connection.execute(
                """UPDATE docker_run_mutations
                   SET phase = ?, revision = ?, record_digest = ?, record_json = ?
                   WHERE project_ref = ? AND run_id = ?
                     AND revision = ? AND record_digest = ?""",
                (
                    replacement.phase.value,
                    replacement.revision,
                    replacement.record_digest,
                    replacement.canonical_bytes,
                    replacement.project_ref,
                    replacement.run_id,
                    expected_revision,
                    expected_record_digest,
                ),
            )
            if cursor.rowcount != 1:
                raise RevisionConflict("Docker mutation revision")
            persisted = self._load_docker_mutation_in(
                connection, replacement.project_ref, replacement.run_id
            )
            if persisted != replacement:
                raise RuntimeError("host Docker persistence is invalid")
            return persisted

    def admit(
        self,
        *,
        purpose: str,
        issuer_ref: str,
        evidence_ref: str,
        challenge_nonce: str,
        audience_ref: str,
        payload_digest: str,
        expires_at: str,
    ) -> ReplayDisposition:
        values = (
            purpose,
            issuer_ref,
            evidence_ref,
            challenge_nonce,
            audience_ref,
            payload_digest,
            expires_at,
        )
        with self._transaction() as connection:
            prior = connection.execute(
                """
                SELECT purpose, issuer_ref, evidence_ref, challenge_nonce,
                       audience_ref, payload_digest, expires_at
                FROM evidence_replay
                WHERE purpose = ? AND challenge_nonce = ?
                """,
                (purpose, challenge_nonce),
            ).fetchone()
            if prior is not None:
                observed = tuple(prior[key] for key in prior.keys())
                return (
                    ReplayDisposition.IDEMPOTENT
                    if observed == values
                    else ReplayDisposition.COLLISION
                )
            connection.execute(
                """
                INSERT INTO evidence_replay(
                    purpose, issuer_ref, evidence_ref, challenge_nonce,
                    audience_ref, payload_digest, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            return ReplayDisposition.ADMITTED
