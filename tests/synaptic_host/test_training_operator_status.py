import io
import json
import os
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from synaptic_host import training_operator
from synaptic_host import sqlite_repository
from synaptic_host.sqlite_repository import (
    SqliteTrainingRepository, _BASE_TABLE_COLUMNS, _DOCKER_TABLE_COLUMNS,
    _SCHEMA_VERSION,
)


RUN_ID = "run-" + "1" * 32


def _context(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir(parents=True)
    return SimpleNamespace(
        project_root=project,
        engine_root=project / "synaptic-tuner",
        state_root=project / ".synaptic" / "state",
    )


def test_missing_status_does_not_create_private_state(tmp_path: Path) -> None:
    context = _context(tmp_path)
    assert training_operator._local_status(context, "project-one", RUN_ID) == {
        "schema_version": "synaptic-training-operator-result/v1",
        "code": "RUN_MISSING",
        "run_id": RUN_ID,
    }
    assert not (context.project_root / ".synaptic").exists()


def test_status_opens_an_existing_database_read_only(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    SqliteTrainingRepository(database, clock=lambda: "2026-09-08T00:00:00Z")
    database.chmod(0o600)
    before = database.read_bytes()
    members = tuple(sorted(path.name for path in context.state_root.iterdir()))
    assert training_operator._local_status(context, "project-one", RUN_ID)["code"] == "RUN_MISSING"
    assert database.read_bytes() == before
    assert tuple(sorted(path.name for path in context.state_root.iterdir())) == members


def test_correct_column_names_without_production_constraints_are_rejected(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    connection = sqlite3.connect(database)
    for table, columns in {**_BASE_TABLE_COLUMNS, **_DOCKER_TABLE_COLUMNS}.items():
        connection.execute(
            f"CREATE TABLE {table} ({','.join(name + ' BLOB' for name in columns)})"
        )
    connection.execute("INSERT INTO schema_meta VALUES(?,?)", ("schema_version", _SCHEMA_VERSION))
    for sequence in (1, 2):
        connection.execute(
            "INSERT INTO lifecycle_records VALUES(?,?,?,?,?)",
            (sequence, "project-one", RUN_ID, 1, b"bad"),
        )
        connection.execute(
            "INSERT INTO modal_preparations VALUES(?,?,?,?)",
            ("project-one", RUN_ID, "effect", b"bad"),
        )
    connection.commit()
    connection.close()
    database.chmod(0o600)
    before = database.read_bytes()
    try:
        training_operator._read_existing_pair(context, "project-one", RUN_ID)
    except ValueError as error:
        assert str(error) == "training ledger schema is invalid"
    else:
        raise AssertionError("wrong-shape ledger was accepted")
    assert database.read_bytes() == before


def test_wrong_shape_and_partial_ledgers_are_not_missing_runs(tmp_path: Path) -> None:
    for partial in (False, True):
        context = _context(tmp_path / str(partial))
        context.state_root.mkdir(parents=True, mode=0o700)
        (context.project_root / ".synaptic").chmod(0o700)
        context.state_root.chmod(0o700)
        database = context.state_root / "training.sqlite3"
        connection = sqlite3.connect(database)
        if partial:
            for table, columns in {**_BASE_TABLE_COLUMNS, **_DOCKER_TABLE_COLUMNS}.items():
                connection.execute(
                    f"CREATE TABLE {table} ({','.join(name + ' BLOB' for name in columns)})"
                )
            connection.execute(
                "INSERT INTO schema_meta VALUES(?,?)", ("schema_version", _SCHEMA_VERSION)
            )
            connection.execute(
                "INSERT INTO lifecycle_records VALUES(?,?,?,?,?)",
                (1, "project-one", RUN_ID, 1, b"bad"),
            )
        else:
            connection.execute("CREATE TABLE lifecycle_records(run_id BLOB)")
        connection.commit()
        connection.close()
        database.chmod(0o600)
        try:
            training_operator._read_existing_pair(context, "project-one", RUN_ID)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid ledger was reported as a missing run")


def test_active_or_crash_sidecar_is_unavailable_not_missing(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    SqliteTrainingRepository(database, clock=lambda: "2026-09-08T00:00:00Z")
    database.chmod(0o600)
    Path(str(database) + "-wal").write_bytes(b"stale")
    try:
        training_operator._local_status(context, "project-one", RUN_ID)
    except ValueError as error:
        assert str(error) == "training ledger has active sidecar state"
    else:
        raise AssertionError("sidecar-backed ledger was reported as missing")


def test_oversized_snapshot_fails_closed(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    SqliteTrainingRepository(database, clock=lambda: "2026-09-08T00:00:00Z")
    database.chmod(0o600)
    with patch.object(sqlite_repository, "_MAX_OPERATOR_SNAPSHOT_BYTES", 1):
        try:
            training_operator._read_existing_pair(context, "project-one", RUN_ID)
        except ValueError as error:
            assert str(error) == "training ledger snapshot is unavailable"
        else:
            raise AssertionError("oversized ledger snapshot was accepted")


def test_unavailable_sqlite_deserialize_fails_closed(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    SqliteTrainingRepository(database, clock=lambda: "2026-09-08T00:00:00Z")
    database.chmod(0o600)
    closed = False

    class UnsupportedConnection:
        def deserialize(self, _image):
            raise AttributeError("deserialize unavailable")

        def close(self):
            nonlocal closed
            closed = True

    with patch.object(
        sqlite_repository.sqlite3, "connect", return_value=UnsupportedConnection(),
    ):
        try:
            training_operator._read_existing_pair(context, "project-one", RUN_ID)
        except ValueError as error:
            assert str(error) == "training ledger schema is invalid"
        else:
            raise AssertionError("missing SQLite deserialize support was accepted")
    assert closed


def test_trigger_and_view_schema_objects_are_rejected(tmp_path: Path) -> None:
    definitions = (
        """CREATE TRIGGER hidden_lifecycle_trigger
           AFTER INSERT ON lifecycle_records BEGIN
             DELETE FROM lifecycle_records WHERE sequence = NEW.sequence;
           END""",
        "CREATE VIEW hidden_lifecycle_view AS SELECT * FROM lifecycle_records",
    )
    for index, definition in enumerate(definitions):
        context = _context(tmp_path / str(index))
        context.state_root.mkdir(parents=True, mode=0o700)
        (context.project_root / ".synaptic").chmod(0o700)
        context.state_root.chmod(0o700)
        database = context.state_root / "training.sqlite3"
        SqliteTrainingRepository(database, clock=lambda: "2026-09-08T00:00:00Z")
        connection = sqlite3.connect(database)
        connection.execute(definition)
        connection.commit()
        connection.close()
        database.chmod(0o600)
        try:
            training_operator._read_existing_pair(context, "project-one", RUN_ID)
        except ValueError as error:
            assert str(error) == "training ledger schema is invalid"
        else:
            raise AssertionError("executable or hidden schema object was accepted")


def test_noncanonical_blobs_are_rejected() -> None:
    try:
        training_operator._decode_existing_pair(b"{}", b"{}", "project-one", RUN_ID)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("noncanonical durable blobs were accepted")


def test_public_prepared_run_validator_rejects_cross_record_pair() -> None:
    event = SimpleNamespace(occurred_at="2026-09-08T00:00:00Z", grant_binding=object())
    record = SimpleNamespace(
        run_id=RUN_ID, project_ref="project-one", events=(event,) * 4, effects=(),
    )
    effect = SimpleNamespace(effect_id="effect-one")
    prepared = SimpleNamespace(
        operation=SimpleNamespace(
            project_ref="project-one", run_id=RUN_ID, effect=effect,
            plan_fingerprint="a" * 64,
        ),
        public_plan_fingerprint="a" * 64,
    )
    modal_type = SimpleNamespace(from_canonical_bytes=lambda _raw: prepared)
    class Lifecycle:
        @staticmethod
        def from_canonical_bytes(_raw):
            return record

        def __new__(cls, *args):
            return SimpleNamespace(args=args)

    api = SimpleNamespace(
        LifecycleRecord=Lifecycle, LifecyclePhase=SimpleNamespace(READY="ready"),
        VerificationStatus=SimpleNamespace(NOT_READY="not-ready"),
        MessageCode=SimpleNamespace(READY="ready"),
    )
    modal_api = SimpleNamespace(
        ModalDurablePreparationV1=modal_type,
        ModalPreparedRunV1=lambda *_args: (_ for _ in ()).throw(
            ValueError("cross-record preparation")
        ),
    )
    original = training_operator.importlib.import_module
    def load(name):
        return api if name == "synaptic_tuner.api.v1" else modal_api \
            if name == "synaptic_tuner.api.v1.modal" else original(name)
    with patch.object(training_operator.importlib, "import_module", side_effect=load):
        try:
            training_operator._decode_existing_pair(b"record", b"prepared", "project-one", RUN_ID)
        except ValueError as error:
            assert str(error) == "cross-record preparation"
        else:
            raise AssertionError("cross-record durable pair was accepted")


def test_redirected_private_ancestor_is_rejected(tmp_path: Path) -> None:
    context = _context(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    (context.project_root / ".synaptic").symlink_to(outside, target_is_directory=True)
    try:
        training_operator._read_existing_pair(context, "project-one", RUN_ID)
    except ValueError:
        pass
    else:
        raise AssertionError("redirected private ancestor was accepted")
    assert not (outside / "state").exists()


def test_path_swap_and_restore_cannot_change_descriptor_snapshot(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    SqliteTrainingRepository(database, clock=lambda: "2026-09-08T00:00:00Z")
    database.chmod(0o600)
    real_connect = sqlite3.connect
    swapped = False

    def swap_during_connect(target, *args, **kwargs):
        nonlocal swapped
        assert target == ":memory:"
        connection = real_connect(target, *args, **kwargs)
        if swapped:
            return connection
        swapped = True
        held = context.state_root / "held.sqlite3"
        replacement = context.state_root / "replacement.sqlite3"
        replacement.write_bytes(b"not a SQLite database")
        replacement.chmod(0o600)
        os.replace(database, held)
        os.replace(replacement, database)
        try:
            return connection
        finally:
            os.replace(database, replacement)
            os.replace(held, database)

    with patch.object(
        sqlite_repository.sqlite3, "connect", side_effect=swap_during_connect,
    ):
        value = training_operator._read_existing_pair(context, "project-one", RUN_ID)
    assert value is None
    assert swapped


def test_local_status_is_explicitly_not_provider_refreshed() -> None:
    record = SimpleNamespace(phase=SimpleNamespace(value="queued"), revision=7,
                             updated_at="2026-09-08T00:00:00Z")
    prepared = SimpleNamespace(public_plan_fingerprint="a" * 64)
    effect = SimpleNamespace(identity=SimpleNamespace(effect_id="effect-one"),
                             provider_job_ref="fc-one")
    with patch.object(training_operator, "_read_existing_pair",
                      return_value=(record, prepared, effect)):
        value = training_operator._local_status(object(), "project-one", RUN_ID)
    assert value["observation"] == "local_ledger"
    assert value["provider_refreshed"] is False
    assert value["phase"] == "queued"


def test_status_main_never_enters_the_modal_launcher(tmp_path: Path) -> None:
    context = _context(tmp_path)
    manifest = SimpleNamespace(project_id="project-one")
    output = io.StringIO()
    with patch.object(training_operator, "_project_context", return_value=(manifest, context)), \
         patch.object(training_operator, "_local_status",
                      return_value=training_operator._result("RUN_MISSING", run_id=RUN_ID)), \
         patch("synaptic_host.launcher.ensure_and_reexec") as launcher, \
         patch("sys.stdout", output):
        status = training_operator.main(
            ["training", "status", "--run-id", RUN_ID],
            project_root=tmp_path, engine_root=tmp_path,
        )
    assert status == 2
    assert json.loads(output.getvalue())["code"] == "RUN_MISSING"
    launcher.assert_not_called()
