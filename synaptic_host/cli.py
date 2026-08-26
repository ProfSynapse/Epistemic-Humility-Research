"""Clean host CLI for provider lifecycle and config-first training."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from synaptic_tuner.api.v1 import (
    HostPorts, ProjectContext, RunRef, TrainingAPI, TrainingSubmission,
)
from synaptic_tuner.api.v1.modal import (
    ModalVerificationPolicyV1,
    compose_modal_source_finalizer,
    compose_modal_training_operations,
)

from .modal_provider import ExplicitModalHostSession, ModalHostConfigV1
from .modal_resolver import ModalProviderStateV1, ModalTrainingIntentV1, StrictModalTrainingResolver
from .security import BoundedGrantProvider, FileHmacAuthenticator, ScopedGitRemoteReader, utc_now
from .sqlite_repository import SqliteTrainingRepository


class UnavailableRuns:
    def __getattr__(self, name):
        raise RuntimeError("run operation is not composed for this command")


class UnavailableSecrets:
    def resolve(self, reference):
        raise RuntimeError("literal secret resolution is not available")


class DeferredResolver:
    def resolve(self, request, *, context):
        raise RuntimeError("request resolution is not available for outcome observation")


def _context() -> ProjectContext:
    project = Path(__file__).resolve().parents[1]
    return ProjectContext.host(
        engine_root=project / "synaptic-tuner",
        project_root=project,
        invocation_cwd=Path.cwd(),
        manifest_path=project / "synaptic.yaml",
        config_root=project / "training",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="synaptic")
    commands = parser.add_subparsers(dest="command", required=True)
    provider = commands.add_parser("provider")
    provider_commands = provider.add_subparsers(dest="provider_command", required=True)
    deploy = provider_commands.add_parser("deploy")
    deploy.add_argument("--adopt-empty", action="store_true")
    provider_commands.add_parser("upgrade")
    provider_commands.add_parser("preflight")
    training = commands.add_parser("training")
    training_commands = training.add_subparsers(dest="training_command", required=True)
    start = training_commands.add_parser("start")
    start.add_argument("--config", required=True)
    preflight = training_commands.add_parser("preflight")
    preflight.add_argument("--config", required=True)
    outcome = training_commands.add_parser("outcome")
    outcome.add_argument("--run-id", required=True)
    reverify = training_commands.add_parser("reverify")
    reverify.add_argument("--run-id", required=True)
    return parser


def _json(value: dict[str, object]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))


def _sdk_session(context: ProjectContext, config: ModalHostConfigV1):
    sdk = importlib.import_module("modal")
    token_id = os.environ.get("MODAL_TOKEN_ID", "")
    token_secret = os.environ.get("MODAL_TOKEN_SECRET", "")
    if token_id or token_secret:
        return ExplicitModalHostSession.from_credentials(
            sdk=sdk, config=config, token_id=token_id, token_secret=token_secret
        )
    return ExplicitModalHostSession.from_client(
        sdk=sdk, config=config, client=sdk.Client.from_env()
    )


def _hf_token() -> str:
    value = os.environ.get("HF_TOKEN", "").strip()
    if value:
        return value
    path = Path.home() / ".cache" / "huggingface" / "token"
    if path.is_file() and not path.is_symlink():
        value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError("HF token is unavailable from the environment or host cache")
    return value


def _provider_deploy(context: ProjectContext, *, adopt_empty: bool = False) -> int:
    config = ModalHostConfigV1.load(context)
    session = _sdk_session(context, config)
    auth = FileHmacAuthenticator.from_context(context)
    state = session.deploy(
        context=context, authenticator=auth,
        adopt_empty=adopt_empty,
        hf_token=_hf_token(),
    )
    _json({
        "schema_version": "synaptic-command-result/v1",
        "status": "deployed", "profile": state.profile.profile,
        "deployment_ref": state.selection.deployment_ref,
        "function_name": state.selection.function_name,
    })
    return 0


def _provider_preflight(context: ProjectContext) -> int:
    config = ModalHostConfigV1.load(context)
    state = ModalProviderStateV1.load(context)
    session = _sdk_session(context, config)
    facade = session.facade(state)
    scope = facade.bound_scope()
    proof = facade.capability_proof(state.binding)
    observed = facade.inspect_deployment(
        app_name=state.profile.app_name, function_name=state.profile.function_name
    )
    ready = proof.complete and observed == state.selection
    _json({
        "schema_version": "synaptic-command-result/v1",
        "status": "ready" if ready else "not_ready",
        "profile": state.profile.profile,
        "scope": {"account_ref": scope[0], "workspace_ref": scope[1], "environment_ref": scope[2], "client_ref": scope[3]},
    })
    return 0 if ready else 2


def _provider_upgrade(context: ProjectContext) -> int:
    config = ModalHostConfigV1.load(context)
    session = _sdk_session(context, config)
    state = session.upgrade(
        context=context,
        authenticator=FileHmacAuthenticator.from_context(context),
    )
    _json({
        "schema_version": "synaptic-command-result/v1",
        "status": "upgraded", "profile": state.profile.profile,
        "deployment_ref": state.selection.deployment_ref,
        "function_name": state.selection.function_name,
    })
    return 0


def _intent(config: ModalHostConfigV1) -> ModalTrainingIntentV1:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    suffix = secrets.token_hex(6)
    run_id = "modal-sft-" + now.strftime("%Y%m%dT%H%M%SZ") + "-" + suffix
    return ModalTrainingIntentV1(
        project_ref="epistemic-humility-research",
        run_id=run_id,
        created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        key_ref="modal-evidence-v1",
        quote_expires_at=(now + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        maximum_cost_minor_units=config.maximum_cost_minor_units,
        currency=config.currency,
        effect_id="effect-" + suffix,
        artifact_slot_ref="artifacts-" + suffix,
        invocation_nonce="invoke-" + secrets.token_hex(16),
    )


def _operations(
    context: ProjectContext,
    *,
    config: ModalHostConfigV1,
    state: ModalProviderStateV1,
    session,
    resolver,
    audience_ref: str,
):
    auth = FileHmacAuthenticator.from_context(context)
    auth.initialize()
    repository = SqliteTrainingRepository.from_context(context, clock=utc_now)
    grants = BoundedGrantProvider(
        maximum_cost_minor_units=config.maximum_cost_minor_units,
        currency=config.currency, clock=utc_now,
    )
    ports = HostPorts(
        lifecycle=repository,
        runs=UnavailableRuns(),
        grants=grants,
        secrets=UnavailableSecrets(),
        evidence_replay=repository,
        authenticator=auth,
        clock=utc_now,
        git_remote=ScopedGitRemoteReader(),
        modal_reads=session.facade(state),
        training_resolver=resolver,
    )
    operations = compose_modal_training_operations(
        context=context, host_ports=ports, provider_config=state.profile
    )
    return TrainingAPI(operations), ports, repository


def _training_api(context: ProjectContext, path_ref: str):
    config = ModalHostConfigV1.load(context)
    state = ModalProviderStateV1.load(context)
    session = _sdk_session(context, config)
    intent = _intent(config)
    audience = f"{intent.project_ref}/{intent.run_id}"
    auth = FileHmacAuthenticator.from_context(context)
    auth.initialize()
    repository = SqliteTrainingRepository.from_context(context, clock=utc_now)
    grants = BoundedGrantProvider(
        maximum_cost_minor_units=config.maximum_cost_minor_units,
        currency=config.currency, clock=utc_now,
    )
    preliminary = HostPorts(
        lifecycle=repository, runs=UnavailableRuns(), grants=grants,
        secrets=UnavailableSecrets(), evidence_replay=repository,
        authenticator=auth, clock=utc_now, git_remote=ScopedGitRemoteReader(),
        modal_reads=session.facade(state), training_resolver=DeferredResolver(),
    )
    policy = ModalVerificationPolicyV1(
        audience_ref=audience,
        source_issuer_ref="host-git-verifier-v1",
        deployment_issuer_ref="host-modal-verifier-v1",
        source_key_ref=auth.key_ref,
        deployment_key_ref=auth.key_ref,
        challenge_factory=lambda purpose: "challenge-" + secrets.token_hex(24),
        evidence_ref_factory=lambda purpose: "evidence-" + secrets.token_hex(24),
    )
    resolver = StrictModalTrainingResolver(
        state=state, intent=intent,
        finalizer=compose_modal_source_finalizer(preliminary, policy),
    )
    ports = HostPorts(
        lifecycle=repository, runs=UnavailableRuns(), grants=grants,
        secrets=UnavailableSecrets(), evidence_replay=repository,
        authenticator=auth, clock=utc_now, git_remote=preliminary.git_remote,
        modal_reads=preliminary.modal_reads, training_resolver=resolver,
    )
    operations = compose_modal_training_operations(
        context=context, host_ports=ports, provider_config=state.profile
    )
    document = resolver.load_document(context, path_ref)
    return TrainingAPI(operations), ports, document, intent


def _training_preflight(context: ProjectContext, path_ref: str, *, start: bool) -> int:
    api, ports, document, intent = _training_api(context, path_ref)
    request = api.load(document)
    plan = api.plan(api.resolve(request))
    checked = api.preflight(plan)
    if not checked.ready:
        _json({
            "schema_version": "synaptic-command-result/v1",
            "status": "not_ready", "run_id": intent.run_id,
            "errors": [error.code.value for error in checked.errors],
        })
        return 2
    if not start:
        _json({
            "schema_version": "synaptic-command-result/v1",
            "status": "ready", "run_id": intent.run_id,
            "plan_fingerprint": plan.fingerprint,
            "expires_at": checked.expires_at,
        })
        return 0
    grant = ports.grants.authorize(checked.authorization)
    submission = api.start(plan, checked, grant)
    _json({
        "schema_version": "synaptic-command-result/v1",
        "status": "submitted", "run_id": submission.run.run_id,
        "project_ref": submission.run.project_ref,
        "plan_fingerprint": submission.plan_fingerprint,
        "submitted_at": submission.submitted_at,
    })
    return 0


def _training_outcome(
    context: ProjectContext, run_id: str, *, reverify: bool = False
) -> int:
    config = ModalHostConfigV1.load(context)
    state = ModalProviderStateV1.load(context)
    session = _sdk_session(context, config)
    repository = SqliteTrainingRepository.from_context(context, clock=utc_now)
    record = repository.load("epistemic-humility-research", run_id)
    preparation = repository.load_modal_preparation("epistemic-humility-research", run_id)
    if record is None or preparation is None:
        raise ValueError("run was not found")
    api, _, _ = _operations(
        context, config=config, state=state, session=session,
        resolver=DeferredResolver(), audience_ref=f"epistemic-humility-research/{run_id}",
    )
    submission = TrainingSubmission(
        RunRef(run_id, "epistemic-humility-research"),
        preparation.public_plan_fingerprint, record.updated_at,
    )
    outcome = api.reverify(submission) if reverify else api.outcome(submission)
    _json({
        "schema_version": "synaptic-command-result/v1",
        "status": outcome.status.state.value,
        "run_id": run_id,
        "success": outcome.success,
        "artifacts": [
            {"artifact_id": item.artifact_id, "kind": item.kind, "state": item.state.value}
            for item in outcome.artifacts
        ],
    })
    return 0 if outcome.success else 3


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    parsed = _parser().parse_args(arguments)
    context = _context()
    if parsed.command == "provider":
        if parsed.provider_command == "deploy":
            return _provider_deploy(context, adopt_empty=parsed.adopt_empty)
        if parsed.provider_command == "upgrade":
            return _provider_upgrade(context)
        return _provider_preflight(context)
    if parsed.training_command == "start":
        return _training_preflight(context, parsed.config, start=True)
    if parsed.training_command == "preflight":
        return _training_preflight(context, parsed.config, start=False)
    return _training_outcome(
        context, parsed.run_id, reverify=parsed.training_command == "reverify"
    )


if __name__ == "__main__":
    raise SystemExit(main())
