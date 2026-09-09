import ast
import inspect
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from synaptic_host import training_operator
from synaptic_host import launcher


RUN_A = "run-" + "a" * 32
RUN_B = "run-" + "b" * 32


def test_operator_request_digest_binds_verb_and_run() -> None:
    reconcile = training_operator._request_digest("reconcile", RUN_A)
    assert reconcile != training_operator._request_digest("status", RUN_A)
    assert reconcile != training_operator._request_digest("reconcile", RUN_B)
    assert len(reconcile) == 64


def test_wrong_or_consumed_authority_refuses_before_ledger_or_provider() -> None:
    context = SimpleNamespace(project_root=Path("/project"), engine_root=Path("/engine"))
    with patch("synaptic_host.launcher._consume_isolated_child_authority_v1",
               return_value=None) as consume, \
         patch.object(training_operator, "_read_existing_pair") as read:
        result = training_operator._reconcile(
            context, "project-one", RUN_A, object(), token_id="id",
            token_secret="secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-08T00:00:00Z",
        )
    assert result["code"] == "AUTHORITY_INVALID"
    consume.assert_called_once_with(
        consume.call_args.args[0],
        ingress_digest=training_operator._request_digest("reconcile", RUN_A),
        contract_identity_digest=training_operator._CONTRACT_DIGEST,
    )
    read.assert_not_called()


def test_invalid_schema_stops_before_provider_and_mutable_repository() -> None:
    context = SimpleNamespace(project_root=Path("/project"), engine_root=Path("/engine"))
    with patch(
        "synaptic_host.launcher._consume_isolated_child_authority_v1",
        return_value=(context.project_root, context.engine_root, "id", "secret"),
    ), patch.object(
        training_operator, "_read_existing_pair",
        side_effect=ValueError("training ledger schema is invalid"),
    ), patch(
        "synaptic_host.modal_provider.ModalProviderAuthorityV1.load"
    ) as provider_authority, patch(
        "synaptic_host.sqlite_repository.SqliteTrainingRepository.from_context"
    ) as mutable_repository:
        try:
            training_operator._reconcile(
                context, "project-one", RUN_A, object(), token_id="id",
                token_secret="secret", sdk_loader=lambda: (_ for _ in ()).throw(
                    AssertionError("provider SDK loaded")
                ), clock=lambda: "2026-09-08T00:00:00Z",
            )
        except ValueError as error:
            assert str(error) == "training ledger schema is invalid"
        else:
            raise AssertionError("invalid schema reached reconcile mutation setup")
    provider_authority.assert_not_called()
    mutable_repository.assert_not_called()


def test_actual_launcher_authority_rejects_replay_dimensions_and_second_consume() -> None:
    root = Path.cwd().resolve()
    proof = "f" * 64
    environment = {
        launcher._MARKER: "1", launcher._INGRESS_DIGEST: "a" * 64,
        launcher._CONTRACT_IDENTITY_DIGEST: training_operator._CONTRACT_DIGEST,
        launcher._RUNTIME_PROOF_DIGEST: proof,
        "MODAL_TOKEN_ID": "id", "MODAL_TOKEN_SECRET": "secret",
    }
    with patch.dict(os.environ, environment, clear=True), \
         patch.object(launcher, "_runtime_proof", return_value=({}, proof)), \
         patch.object(launcher, "launcher_python", return_value=Path(launcher.sys.executable)):
        issue, _authenticate, consume = launcher._install_isolated_child_authority_v1()

        reconcile_a = training_operator._request_digest("reconcile", RUN_A)
        def token(digest=reconcile_a, contract=training_operator._CONTRACT_DIGEST):
            os.environ[launcher._INGRESS_DIGEST] = digest
            os.environ[launcher._CONTRACT_IDENTITY_DIGEST] = contract
            return issue(
                project_root=root, engine_root=root, ingress_digest=digest,
                contract_identity_digest=contract, proof_digest=proof,
            )

        wrong_verb = token(training_operator._request_digest("status", RUN_A))
        assert consume(
            wrong_verb, ingress_digest=reconcile_a,
            contract_identity_digest=training_operator._CONTRACT_DIGEST,
        ) is None
        wrong_run = token(training_operator._request_digest("reconcile", RUN_B))
        assert consume(
            wrong_run, ingress_digest=reconcile_a,
            contract_identity_digest=training_operator._CONTRACT_DIGEST,
        ) is None
        wrong_contract = token(reconcile_a, "d" * 64)
        assert consume(
            wrong_contract, ingress_digest=reconcile_a,
            contract_identity_digest=training_operator._CONTRACT_DIGEST,
        ) is None
        current = token()
        assert consume(
            current, ingress_digest=reconcile_a,
            contract_identity_digest=training_operator._CONTRACT_DIGEST,
        ) == (root, root, "id", "secret")
        assert consume(
            current, ingress_digest=reconcile_a,
            contract_identity_digest=training_operator._CONTRACT_DIGEST,
        ) is None


def test_reconcile_source_calls_only_public_training_outcome() -> None:
    tree = ast.parse(inspect.getsource(training_operator._reconcile))
    attributes = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)]
    assert "outcome" in attributes
    assert "start" not in attributes
    assert "preflight" not in attributes
    assert "authorize" not in attributes


def test_released_source_validation_rejects_a_changed_commit() -> None:
    def source(commit, *, dirty=False, submodule=False):
        return SimpleNamespace(
            location=SimpleNamespace(canonical_url="https://example.test/repo.git"),
            commit=commit, dirty=dirty,
            submodule_path="synaptic-tuner" if submodule else None,
            gitlink_commit=commit if submodule else None,
        )

    locked = SimpleNamespace(
        run_id=RUN_A, project_source=source("1" * 40),
        engine_source=source("2" * 40, submodule=True),
    )
    inspected = SimpleNamespace(
        mode="superproject", project_source=source("3" * 40),
        engine_source=source("2" * 40, submodule=True),
    )
    api = SimpleNamespace(
        GitCliLocalSourceInspector=lambda: SimpleNamespace(
            inspect=lambda **_kwargs: inspected
        )
    )
    prepared = SimpleNamespace(
        operation=SimpleNamespace(run_id=RUN_A),
        detached_execution_source=lambda: locked,
    )
    with patch.object(training_operator.importlib, "import_module", return_value=api):
        try:
            training_operator._validate_released_source(object(), prepared)
        except ValueError as error:
            assert str(error) == "released source differs from the durable Modal run"
        else:
            raise AssertionError("changed released source was accepted")


def test_reconcile_main_enters_launcher_with_operator_binding(tmp_path: Path) -> None:
    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    manifest = SimpleNamespace(project_id="project-one")
    token = object()
    with patch.object(training_operator, "_project_context", return_value=(manifest, context)), \
         patch("synaptic_host.launcher.ensure_and_reexec", return_value=token) as enter, \
         patch.object(training_operator, "_reconcile",
                      return_value=training_operator._result("OK", run_id=RUN_A)) as reconcile:
        assert training_operator.main(
            ["training", "reconcile", "--run-id", RUN_A],
            project_root=tmp_path, engine_root=tmp_path,
        ) == 0
    enter.assert_called_once_with(
        project_root=tmp_path, engine_root=tmp_path,
        argv=["training", "reconcile", "--run-id", RUN_A],
        ingress_digest=training_operator._request_digest("reconcile", RUN_A),
        contract_identity_digest=training_operator._CONTRACT_DIGEST,
    )
    assert reconcile.call_args.args[3] is token


def test_reconcile_behavior_calls_outcome_without_mutation_entrypoints(tmp_path: Path) -> None:
    class ForbiddenOperations:
        def start(self, *_args):
            raise AssertionError("start reached")
        def preflight(self, *_args):
            raise AssertionError("preflight reached")
        def authorize(self, *_args):
            raise AssertionError("authorize reached")
        def outcome(self, submission):
            return SimpleNamespace(
                status=SimpleNamespace(state=SimpleNamespace(value="running"),
                                       updated_at="2026-09-08T00:00:00Z"),
                artifacts=(), submission=submission,
            )

    context = SimpleNamespace(project_root=tmp_path, engine_root=tmp_path)
    prepared = SimpleNamespace(public_plan_fingerprint="a" * 64)
    record = object()
    authority = SimpleNamespace(
        config=SimpleNamespace(maximum_cost_minor_units=1, currency="USD"),
        state=SimpleNamespace(profile=object()),
    )
    auth = SimpleNamespace(initialize=lambda: None)
    session = SimpleNamespace(facade=lambda _state: object())
    operations = ForbiddenOperations()
    with patch("synaptic_host.launcher._consume_isolated_child_authority_v1",
               return_value=(tmp_path, tmp_path, "id", "secret")), \
         patch.object(training_operator, "_read_existing_pair",
                      return_value=(record, prepared, object())), \
         patch.object(training_operator, "_validate_released_source"), \
         patch.object(training_operator, "_submission", return_value=object()), \
         patch("synaptic_host.modal_provider.ModalProviderAuthorityV1.load",
               return_value=authority), \
         patch("synaptic_host.modal_provider.ExplicitModalHostSession.from_credentials",
               return_value=session), \
         patch("synaptic_host.modal_provider.build_worker_authenticator",
               return_value=auth), \
         patch("synaptic_host.security.FileHmacAuthenticator.from_context",
               return_value=auth), \
         patch("synaptic_host.modal_training.EvidenceKeyRouterV1",
               return_value=object()), \
         patch("synaptic_host.sqlite_repository.SqliteTrainingRepository.from_context",
               return_value=object()), \
         patch("synaptic_tuner.api.v1.modal.compose_modal_training_operations",
               return_value=operations):
        value = training_operator._reconcile(
            context, "project-one", RUN_A, object(), token_id="id",
            token_secret="secret", sdk_loader=lambda: object(),
            clock=lambda: "2026-09-08T00:00:00Z",
        )
    assert value["code"] == "OK"
    assert value["state"] == "running"
