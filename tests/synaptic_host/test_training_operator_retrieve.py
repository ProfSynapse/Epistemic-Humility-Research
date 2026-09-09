"""Retrieval uses its own launcher authority and never the submit path."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from synaptic_host import training_operator
from synaptic_host.sqlite_repository import SqliteTrainingRepository


RUN_ID = "run-" + "a" * 32
ARGV = ["training", "retrieve", "--run-id", RUN_ID]


def _context(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir(parents=True)
    return SimpleNamespace(
        project_root=project,
        engine_root=project / "synaptic-tuner",
        state_root=project / ".synaptic" / "state",
    )


def test_retrieval_grammar_is_exact() -> None:
    assert training_operator._parse(ARGV) == ("retrieve", RUN_ID)
    for invalid in (
        ARGV + ["--destination", "/tmp/output"], ARGV[:-1],
        ["training", "retrieve", "--run-id", "../outside"],
        ["training", "retrieve", "--run-id", RUN_ID, "--force"],
    ):
        assert training_operator._parse(invalid) is None


def test_retrieval_authority_does_not_accept_reconcile_digest() -> None:
    assert training_operator._request_digest("retrieve", RUN_ID) != (
        training_operator._request_digest("reconcile", RUN_ID)
    )
    context = SimpleNamespace(project_root=Path("/project"), engine_root=Path("/engine"))
    token = object()
    with patch("synaptic_host.launcher._consume_isolated_child_authority_v1",
               return_value=None) as consume, \
         patch.object(training_operator, "_read_existing_pair") as read:
        result = training_operator._retrieve(
            context, "project-one", RUN_ID, token, token_id="test-id",
            token_secret="test-secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-09T00:00:00Z",
        )
    assert result["code"] == "AUTHORITY_INVALID"
    consume.assert_called_once_with(
        token, ingress_digest=training_operator._request_digest("retrieve", RUN_ID),
        contract_identity_digest=training_operator._CONTRACT_DIGEST,
    )
    read.assert_not_called()


def test_retrieval_routes_through_locked_launcher(tmp_path: Path, capsys) -> None:
    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    manifest = SimpleNamespace(project_id="project-one")
    token = object()
    with patch.object(training_operator, "_project_context", return_value=(manifest, context)), \
         patch("synaptic_host.launcher.ensure_and_reexec", return_value=token) as launcher, \
         patch.object(training_operator, "_retrieve",
                      return_value=training_operator._result("OK", run_id=RUN_ID)) as retrieve, \
         patch.object(training_operator, "_reconcile") as reconcile:
        assert training_operator.main(ARGV, project_root=tmp_path, engine_root=tmp_path) == 0
    launcher.assert_called_once_with(
        project_root=tmp_path, engine_root=tmp_path, argv=ARGV,
        ingress_digest=training_operator._request_digest("retrieve", RUN_ID),
        contract_identity_digest=training_operator._CONTRACT_DIGEST,
    )
    assert retrieve.call_args.args[3] is token
    reconcile.assert_not_called()
    assert json.loads(capsys.readouterr().out)["code"] == "OK"


def test_retrieval_failure_has_no_provider_exception_text(tmp_path: Path, capsys) -> None:
    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    manifest = SimpleNamespace(project_id="project-one")
    with patch.object(training_operator, "_project_context", return_value=(manifest, context)), \
         patch("synaptic_host.launcher.ensure_and_reexec", return_value=object()), \
         patch.object(training_operator, "_retrieve", side_effect=ValueError("private-provider-response")):
        assert training_operator.main(ARGV, project_root=tmp_path, engine_root=tmp_path) == 4
    output = capsys.readouterr()
    assert json.loads(output.out)["code"] == "OPERATION_UNAVAILABLE"
    assert "private-provider-response" not in output.out + output.err
    assert output.err == ""


@pytest.mark.parametrize("code", ["RUN_MISSING", "CREDENTIALS_UNAVAILABLE", "AUTHORITY_INVALID"])
def test_retrieval_admission_refuses_without_importing_sink(tmp_path: Path, code: str) -> None:
    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    with patch.object(training_operator, "_authorized_run",
                      return_value=training_operator._result(code, run_id=RUN_ID)):
        result = training_operator._retrieve(
            context, "project-one", RUN_ID, object(), token_id="test-id",
            token_secret="test-secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-09T00:00:00Z",
        )
    assert result["code"] == code


def test_unverified_run_refuses_before_provider_and_mutable_repository(tmp_path: Path) -> None:
    from synaptic_tuner.api.v1 import LifecyclePhase, VerificationStatus

    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    record = SimpleNamespace(phase=LifecyclePhase.RUNNING, verification=VerificationStatus.NOT_READY)
    with patch("synaptic_host.launcher._consume_isolated_child_authority_v1",
               return_value=(tmp_path, tmp_path, "test-id", "test-secret")), \
         patch.object(training_operator, "_read_existing_pair",
                      return_value=(record, object(), object())), \
         patch.object(training_operator, "_validate_released_source"), \
         patch("synaptic_host.modal_provider.ModalProviderAuthorityV1.load") as provider, \
         patch("synaptic_host.sqlite_repository.SqliteTrainingRepository.from_context") as repository:
        result = training_operator._retrieve(
            context, "project-one", RUN_ID, object(), token_id="test-id",
            token_secret="test-secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-09T00:00:00Z",
        )
    assert result["code"] == "RUN_NOT_VERIFIED"
    provider.assert_not_called()
    repository.assert_not_called()


def test_read_repository_rechecks_exact_pair_and_rejects_drift() -> None:
    context = object()
    effect = SimpleNamespace(effect_id="effect-one")
    record = SimpleNamespace(canonical_bytes=b"record-one")
    prepared = SimpleNamespace(
        canonical_bytes=b"preparation-one",
        operation=SimpleNamespace(effect=effect),
    )
    repository = training_operator._ReadOnlyModalRunRepository(
        context, "project-one", RUN_ID, record, prepared
    )
    with patch.object(
        training_operator, "_read_existing_pair",
        return_value=(record, prepared, object()),
    ) as read:
        assert repository.load("project-one", RUN_ID) is record
        assert repository.load_modal_preparation("project-one", RUN_ID) is prepared
        assert repository.load_modal_preparation_by_effect("effect-one") is prepared
    assert read.call_count == 3

    changed = SimpleNamespace(canonical_bytes=b"record-two")
    with patch.object(
        training_operator, "_read_existing_pair",
        return_value=(changed, prepared, object()),
    ):
        with pytest.raises(ValueError, match="changed during retrieval"):
            repository.load("project-one", RUN_ID)


def test_verified_retrieval_admission_never_constructs_mutable_ports(tmp_path: Path) -> None:
    from synaptic_tuner.api.v1 import LifecyclePhase, VerificationStatus

    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    record = SimpleNamespace(
        phase=LifecyclePhase.SUCCEEDED, verification=VerificationStatus.VERIFIED,
        canonical_bytes=b"record",
    )
    prepared = SimpleNamespace(
        canonical_bytes=b"preparation",
        operation=SimpleNamespace(effect=SimpleNamespace(effect_id="effect-one")),
    )
    authority = SimpleNamespace(config=object(), state=object())
    auth = SimpleNamespace(private_storage_verified=True)
    facade = object()
    session = SimpleNamespace(facade=lambda _state: facade)
    with patch("synaptic_host.launcher._consume_isolated_child_authority_v1",
               return_value=(tmp_path, tmp_path, "test-id", "test-secret")), \
         patch.object(training_operator, "_read_existing_pair",
                      return_value=(record, prepared, object())), \
         patch.object(training_operator, "_validate_released_source"), \
         patch("synaptic_host.modal_provider.ModalProviderAuthorityV1.load", return_value=authority), \
         patch("synaptic_host.security.FileHmacAuthenticator.from_context", return_value=auth), \
         patch("synaptic_host.modal_provider.build_worker_authenticator", return_value=auth), \
         patch("synaptic_host.modal_training.EvidenceKeyRouterV1", return_value=auth), \
         patch("synaptic_host.modal_provider.ExplicitModalHostSession.from_credentials", return_value=session), \
         patch("synaptic_host.sqlite_repository.SqliteTrainingRepository.from_context") as mutable, \
         patch("synaptic_tuner.api.v1.HostPorts") as ports:
        admitted = training_operator._authorized_run(
            context, "project-one", RUN_ID, object(), verb="retrieve",
            token_id="test-id", token_secret="test-secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-09T00:00:00Z",
        )
    assert type(admitted[3]) is training_operator._ReadOnlyModalRunRepository
    assert admitted[4] is auth and admitted[5] is facade
    mutable.assert_not_called()
    ports.assert_not_called()


def test_read_repository_rejects_misrouting_without_ledger_read() -> None:
    prepared = SimpleNamespace(
        canonical_bytes=b"preparation",
        operation=SimpleNamespace(effect=SimpleNamespace(effect_id="effect-one")),
    )
    repository = training_operator._ReadOnlyModalRunRepository(
        object(), "project-one", RUN_ID,
        SimpleNamespace(canonical_bytes=b"record"), prepared,
    )
    with patch.object(training_operator, "_read_existing_pair") as read:
        with pytest.raises(ValueError, match="misrouted"):
            repository.load("other-project", RUN_ID)
        with pytest.raises(ValueError, match="misrouted"):
            repository.load_modal_preparation("project-one", "run-" + "b" * 32)
        with pytest.raises(ValueError, match="misrouted"):
            repository.load_modal_preparation_by_effect("effect-other")
    read.assert_not_called()


def test_actual_retrieve_assembles_only_narrow_read_factory(tmp_path: Path) -> None:
    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    record = SimpleNamespace(canonical_bytes=b"record")
    prepared = SimpleNamespace(
        canonical_bytes=b"preparation",
        public_plan_fingerprint="f" * 64,
        operation=SimpleNamespace(effect=SimpleNamespace(effect_id="effect-one")),
    )
    authority = SimpleNamespace(state=SimpleNamespace(profile=object()))
    repository, authenticator, facade, reads = object(), object(), object(), object()
    modal_api = SimpleNamespace(
        compose_modal_verified_run_reads=lambda **kwargs: (
            calls.append(kwargs) or reads
        )
    )
    api = SimpleNamespace(
        RunsAPI=lambda value: ("runs", value),
        TrainingRunRef=lambda run_id, project_ref: (run_id, project_ref),
    )
    calls = []
    receipt = {"retrieval_ref": "local"}
    original_import = training_operator.importlib.import_module

    def imported(name):
        if name == "synaptic_tuner.api.v1":
            return api
        if name == "synaptic_tuner.api.v1.modal":
            return modal_api
        return original_import(name)

    with patch.object(
        training_operator, "_authorized_run",
        return_value=(record, prepared, authority, repository, authenticator, facade),
    ), patch.object(
        training_operator.importlib, "import_module", side_effect=imported,
    ), patch(
        "synaptic_host.modal_artifact_retrieval.retrieve_verified_artifacts",
        return_value=receipt,
    ) as sink, patch(
        "synaptic_host.sqlite_repository.SqliteTrainingRepository.from_context"
    ) as mutable:
        result = training_operator._retrieve(
            context, "project-one", RUN_ID, object(), token_id="test-id",
            token_secret="test-secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-09T00:00:00Z",
        )

    assert result["code"] == "OK"
    assert len(calls) == 1
    assert {key: value for key, value in calls[0].items() if key != "clock"} == {
        "context": context, "repository": repository,
        "authenticator": authenticator, "modal_reads": facade,
    }
    assert callable(calls[0]["clock"])
    sink.assert_called_once()
    mutable.assert_not_called()


def test_read_repository_real_ledger_sidecar_refuses_without_mutation(tmp_path: Path) -> None:
    context = _context(tmp_path)
    context.state_root.mkdir(parents=True, mode=0o700)
    (context.project_root / ".synaptic").chmod(0o700)
    context.state_root.chmod(0o700)
    database = context.state_root / "training.sqlite3"
    SqliteTrainingRepository(database, clock=lambda: "2026-09-09T00:00:00Z")
    database.chmod(0o600)
    before = database.read_bytes()
    members = tuple(sorted(path.name for path in context.state_root.iterdir()))
    assert training_operator._read_existing_pair(
        context, "project-one", RUN_ID
    ) is None
    assert database.read_bytes() == before
    assert tuple(sorted(path.name for path in context.state_root.iterdir())) == members

    prepared = SimpleNamespace(
        canonical_bytes=b"preparation",
        operation=SimpleNamespace(effect=SimpleNamespace(effect_id="effect-one")),
    )
    repository = training_operator._ReadOnlyModalRunRepository(
        context, "project-one", RUN_ID,
        SimpleNamespace(canonical_bytes=b"record"), prepared,
    )
    sidecar = Path(str(database) + "-wal")
    sidecar.write_bytes(b"stale")
    with pytest.raises(ValueError, match="active sidecar state"):
        repository.load("project-one", RUN_ID)
    assert database.read_bytes() == before
