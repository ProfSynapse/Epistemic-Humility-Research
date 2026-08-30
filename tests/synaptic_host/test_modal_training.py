from __future__ import annotations

import json
import hashlib
import sqlite3
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from synaptic_host.cli import (
    TrainingRunCommandCodeV2,
    TrainingRunIngressV1,
)
import synaptic_host.cli as cli
import synaptic_host.modal_training as modal_training
import synaptic_host.modal_resolver as modal_resolver_module
from synaptic_tuner.api.v1.training_input_loader import (
    load_training_input_contract_v1,
)
from synaptic_tuner.api.v1 import ProjectContext, SourceLock
from synaptic_tuner.api.v1.modal import (
    ModalClientBinding, ModalDeploymentSelectionV1, ModalProviderProfileV1,
    ModalSecretProfileV1, modal_function_name,
)
from synaptic_host.modal_provider import (
    ExplicitModalHostSession, ModalDeploymentJournalV1, ModalHostConfigV1,
    ModalProviderAuthorityV1, ModalTrainingPolicyV1,
)
from synaptic_host.modal_resolver import ModalProviderStateV1
from synaptic_host.sqlite_repository import SqliteTrainingRepository
from tuner.execution.providers.modal.facade import ExplicitModal154ReadFacade
import tuner.execution.providers.modal.composition as modal_composition
from tests.execution.providers.test_modal_sdk154_adapter import (
    FakeCall as EngineFakeCall, FakeFunction as EngineFakeFunction,
    FakeFunctionCall as EngineFakeFunctionCall, FakeVolume as EngineFakeVolume,
    SDK as EngineFakeSdk,
)
from tuner.execution.contracts import (
    EffectIdentity,
    EffectKind,
    EffectRecord,
    EffectState,
    EventCode,
    ExecutionScope,
    LifecycleEvent,
    LifecyclePhase,
    LifecycleRecord,
    MessageCode,
    VerificationStatus,
)


ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / "synaptic-tuner"
NOW = "2026-08-30T12:00:00Z"


@pytest.fixture(autouse=True)
def _restore_engine_contract_cache():
    prior = cli._ENGINE_CONTRACT_CACHE
    try:
        yield
    finally:
        cli._ENGINE_CONTRACT_CACHE = prior


def _document() -> dict[str, object]:
    return {
        "schema_version": "synaptic-training-input/v1",
        "method": "sft",
        "model": {
            "ref": "unsloth/tiny-model", "revision": "main",
            "tokenizer_revision": "main",
        },
        "dataset": {"ref": "project://training/dataset.jsonl"},
        "hyperparameters": {
            "schema_version": "synaptic-sft-hyperparameters/v1",
            "batch_size": 1, "gradient_accumulation_steps": 1,
            "learning_rate": 0.0002,
            "duration": {"max_steps": 2, "num_epochs": None},
            "max_seq_length": 128, "seed": 7, "save_steps": 1,
            "save_total_limit": 1, "lora_rank": 8, "lora_alpha": 16,
            "lora_dropout": 0.0,
            "lora_target_modules": ["q_proj", "v_proj"],
            "use_dora": False, "use_rslora": False,
            "init_lora_weights": True, "split_dataset": False,
        },
        "artifacts": {
            "required_kinds": ["final_model"], "retain_checkpoints": False,
        },
    }


def _ingress(
    tmp_path: Path, document: dict[str, object] | None = None,
) -> tuple[TrainingRunIngressV1, Path]:
    project = tmp_path / "project"
    training = project / "training"
    training.mkdir(parents=True)
    (training / "input.json").write_text(
        json.dumps(document or _document(), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    (training / "dataset.jsonl").write_text('{}\n', encoding="utf-8")
    (project / "synaptic.yaml").write_text("schema_version: test\n", encoding="utf-8")
    source = (training / "input.json").read_bytes()
    bundle = load_training_input_contract_v1()
    training_input = bundle.parse_json(source.decode("utf-8"))
    input_digest = training_input.input_digest()
    source_sha256 = hashlib.sha256(source).hexdigest()
    contract_identity_digest = bundle.identity.identity_digest
    body = {
        "schema_version": "synaptic-training-run-ingress/v1",
        "provider_ref": "modal",
        "config_ref": "project://training/input.json",
        "destination_ref": "provider-staging",
        "input_digest": input_digest,
        "source_sha256": source_sha256,
        "contract_identity_digest": contract_identity_digest,
    }
    canonical = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    envelope_digest = hashlib.sha256(
        b"synaptic-training-run-ingress/v1\0" + canonical
    ).hexdigest()
    cli._ENGINE_CONTRACT_CACHE = (ENGINE, None, {}, bundle)
    value = cli._issue_training_run_ingress_v1(
        "modal", "project://training/input.json", "provider-staging",
        training_input, input_digest, source_sha256, contract_identity_digest,
        envelope_digest, bundle,
    )
    assert type(value) is TrainingRunIngressV1, (
        getattr(value, "code", None), getattr(value, "status", None)
    )
    return value, project


class _FakeAuthenticator:
    key_ref = "modal-key-v1"

    @classmethod
    def from_context(cls, _context):
        return cls()

    def initialize(self) -> None:
        pass


class _FakeGrants:
    fail = False

    def __init__(self, **_kwargs):
        self.authorizations = 0

    def authorize(self, _authorization):
        self.authorizations += 1
        if type(self).fail:
            raise RuntimeError("private authorization failure")
        return object()


class _FakeSession:
    def __init__(self):
        self.restored: list[str] = []

    def facade(self, _state):
        return object()

    def restore_function_call(self, reference: str):
        self.restored.append(reference)
        return SimpleNamespace(object_id=reference)


class _FakeOperations:
    def __init__(self):
        self.started = 0
        self.fail_at: str | None = None
        self.preflight_ready = True

    def load(self, document):
        if self.fail_at == "load":
            raise RuntimeError("private load failure")
        return document

    def resolve(self, request):
        if self.fail_at == "resolve":
            raise RuntimeError("private resolve failure")
        return request

    def plan(self, _resolved):
        if self.fail_at == "plan":
            raise RuntimeError("private plan failure")
        return SimpleNamespace(fingerprint="a" * 64)

    def preflight(self, _plan):
        if self.fail_at == "preflight":
            raise RuntimeError("private preflight failure")
        return SimpleNamespace(
            ready=self.preflight_ready, authorization=object()
        )

    def start(self, _plan, _preflight, _grant):
        self.started += 1
        if self.fail_at == "start":
            raise RuntimeError("private start failure")


def _install_fakes(monkeypatch: pytest.MonkeyPatch, project: Path):
    _FakeGrants.fail = False
    operations = _FakeOperations()
    session = _FakeSession()
    repository = SimpleNamespace()
    context = SimpleNamespace(project_root=project, engine_root=ENGINE)
    manifest = SimpleNamespace(
        path=project / "synaptic.yaml", project_id="ehr-training",
        create_context=lambda **_kwargs: context,
    )
    config = SimpleNamespace(maximum_cost_minor_units=100, currency="USD")
    state = SimpleNamespace(profile=object())
    authority = SimpleNamespace(config=config, state=state)

    monkeypatch.setattr(modal_training, "load_project_manifest", lambda _path: manifest)
    monkeypatch.setattr(
        modal_training.ModalProviderAuthorityV1, "load",
        classmethod(lambda _cls, _context: authority),
    )
    monkeypatch.setattr(modal_training, "FileHmacAuthenticator", _FakeAuthenticator)
    monkeypatch.setattr(modal_training, "BoundedGrantProvider", _FakeGrants)
    monkeypatch.setattr(modal_training, "ScopedGitRemoteReader", lambda: object())
    monkeypatch.setattr(
        modal_training.ExplicitModalHostSession, "from_credentials",
        classmethod(lambda _cls, **_kwargs: session),
    )
    monkeypatch.setattr(
        modal_training.SqliteTrainingRepository, "from_context",
        classmethod(lambda _cls, *_args, **_kwargs: repository),
    )
    monkeypatch.setattr(
        modal_training, "compose_modal_source_finalizer",
        lambda *_args, **_kwargs: object(),
    )
    monkeypatch.setattr(modal_training, "ModalTrainingResolverV1", lambda **_kwargs: object())
    monkeypatch.setattr(
        modal_training, "compose_modal_training_operations",
        lambda **_kwargs: operations,
    )
    return operations, session, repository


def _submitted(**arguments):
    return modal_training._operation_result(
        TrainingRunCommandCodeV2.SUBMITTED,
        arguments["baseline"],
        project_ref=arguments["project_ref"], run_id=arguments["run_id"],
        plan_fingerprint="a" * 64,
        effect_id=arguments["effect_id"], provider_job_ref="fc-durable-1",
        submitted_at=NOW,
    )


def _reconcile(**arguments):
    return modal_training._operation_result(
        TrainingRunCommandCodeV2.RECONCILE_REQUIRED,
        arguments["baseline"],
        project_ref=arguments["project_ref"], run_id=arguments["run_id"],
        plan_fingerprint="a" * 64,
        effect_id=arguments["effect_id"],
    )


def test_start_returns_submitted_only_after_durable_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    calls = 0

    def classify(**arguments):
        nonlocal calls
        calls += 1
        return None if calls == 1 else _submitted(**arguments)

    monkeypatch.setattr(modal_training, "_classify_durable", classify)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.SUBMITTED
    assert result.project_ref == "ehr-training"
    assert result.provider_job_ref == "fc-durable-1"
    assert operations.started == 1
    assert calls == 2


def test_existing_durable_submission_never_spawns_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    monkeypatch.setattr(modal_training, "_classify_durable", _submitted)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.SUBMITTED
    assert operations.started == 0


def test_start_interruption_with_durable_attempt_requires_reconcile_and_no_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    operations.fail_at = "start"
    calls = 0

    def classify(**arguments):
        nonlocal calls
        calls += 1
        return None if calls == 1 else _reconcile(**arguments)

    monkeypatch.setattr(modal_training, "_classify_durable", classify)
    first = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert first.code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
    assert operations.started == 1

    monkeypatch.setattr(modal_training, "_classify_durable", _reconcile)
    second = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert second.code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
    assert operations.started == 1


@pytest.mark.parametrize(
    ("stage", "code"),
    [
        ("resolve", TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE),
        ("preflight", TrainingRunCommandCodeV2.PREFLIGHT_REJECTED),
    ],
)
def test_pre_start_failures_are_closed_and_expose_no_operation_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str,
    code: TrainingRunCommandCodeV2,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    operations.fail_at = stage
    monkeypatch.setattr(modal_training, "_classify_durable", lambda **_kwargs: None)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is code
    assert result.project_ref is result.run_id is result.plan_fingerprint is None
    assert result.effect_id is result.provider_job_ref is result.submitted_at is None


def test_genuine_not_ready_preflight_with_exact_absence_stays_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    operations.preflight_ready = False
    durable_reads = 0

    def absent(**_kwargs):
        nonlocal durable_reads
        durable_reads += 1
        return None

    monkeypatch.setattr(modal_training, "_classify_durable", absent)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.PREFLIGHT_REJECTED
    assert durable_reads == 2  # initial durable-first gate + one rejection read
    assert operations.started == 0


def test_not_ready_preflight_converges_to_exact_concurrent_durable_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    operations.preflight_ready = False
    durable_reads = 0

    def concurrent_pair(**arguments):
        nonlocal durable_reads
        durable_reads += 1
        return None if durable_reads == 1 else _reconcile(**arguments)

    monkeypatch.setattr(modal_training, "_classify_durable", concurrent_pair)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
    assert durable_reads == 2
    assert operations.started == 0


@pytest.mark.parametrize("raises", [False, True])
def test_preflight_ingress_mutation_fails_before_convergence_or_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, raises: bool,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, session, _repository = _install_fakes(monkeypatch, project)
    durable_reads = 0

    def absent(**_kwargs):
        nonlocal durable_reads
        durable_reads += 1
        return None

    def mutate(_plan):
        object.__setattr__(ingress, "input_digest", "f" * 64)
        if raises:
            raise RuntimeError("private preflight failure")
        return SimpleNamespace(ready=False, authorization=object())

    monkeypatch.setattr(modal_training, "_classify_durable", absent)
    monkeypatch.setattr(operations, "preflight", mutate)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert durable_reads == 1
    assert session.restored == []
    assert operations.started == 0


def test_convergence_mutation_fails_before_return_or_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, session, _repository = _install_fakes(monkeypatch, project)
    operations.preflight_ready = False
    durable_reads = 0

    def mutate_after_classification(**arguments):
        nonlocal durable_reads
        durable_reads += 1
        if durable_reads == 1:
            return None
        object.__setattr__(ingress, "input_digest", "f" * 64)
        return modal_training._DurableFoundV1(
            arguments["project_ref"], arguments["run_id"], "a" * 64,
            arguments["effect_id"], "fc-must-not-restore", NOW,
        )

    monkeypatch.setattr(
        modal_training, "_classify_durable", mutate_after_classification
    )
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert durable_reads == 2
    assert session.restored == []
    assert operations.started == 0


@pytest.mark.parametrize("phase", ["initial", "preflight"])
@pytest.mark.parametrize("raises", [False, True])
def test_restore_ingress_mutation_closes_before_operation_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    phase: str, raises: bool,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, session, _repository = _install_fakes(monkeypatch, project)
    if phase == "preflight":
        operations.preflight_ready = False
    durable_reads = 0
    restore_attempts = 0

    def durable_found(**arguments):
        nonlocal durable_reads
        durable_reads += 1
        if phase == "preflight" and durable_reads == 1:
            return None
        return modal_training._DurableFoundV1(
            arguments["project_ref"], arguments["run_id"], "a" * 64,
            arguments["effect_id"], "fc-mutating-restore", NOW,
        )

    def mutate_restore(_reference):
        nonlocal restore_attempts
        restore_attempts += 1
        object.__setattr__(ingress, "input_digest", "f" * 64)
        if raises:
            raise RuntimeError("private restore failure")
        return SimpleNamespace(object_id="fc-mutating-restore")

    monkeypatch.setattr(modal_training, "_classify_durable", durable_found)
    monkeypatch.setattr(session, "restore_function_call", mutate_restore)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.INTERNAL_FAILURE
    assert restore_attempts == 1
    assert durable_reads == (1 if phase == "initial" else 2)
    assert operations.started == 0


def test_missing_credentials_has_zero_sdk_or_composition_effect(
    tmp_path: Path,
) -> None:
    ingress, project = _ingress(tmp_path)
    effects: list[str] = []
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="", token_secret="secret",
        sdk_loader=lambda: effects.append("sdk"), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.CREDENTIALS_UNAVAILABLE
    assert effects == []
    assert "secret" not in repr(result)


def test_authorization_failure_is_closed_before_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ingress, project = _ingress(tmp_path)
    operations, _session, _repository = _install_fakes(monkeypatch, project)
    _FakeGrants.fail = True
    monkeypatch.setattr(modal_training, "_classify_durable", lambda **_kwargs: None)
    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: object(), clock=lambda: NOW,
    )
    assert result.code is TrainingRunCommandCodeV2.AUTHORIZATION_UNAVAILABLE
    assert result.project_ref is result.run_id is result.plan_fingerprint is None
    assert operations.started == 0


class _PairRepository:
    def __init__(self, record=None, preparation=None, *, fail=False):
        self.record, self.preparation, self.fail = record, preparation, fail

    def load(self, _project_ref, _run_id):
        if self.fail:
            raise RuntimeError("private database path")
        return self.record

    def load_modal_preparation(self, _project_ref, _run_id):
        return self.preparation


def test_exact_absence_is_the_only_fresh_durable_classification() -> None:
    result = modal_training._classify_durable(
        repository=_PairRepository(), authority=object(), ingress=object(),
        context=object(),
        baseline=("modal", "config", "provider-staging", "e" * 64),
        project_ref="project-1", run_id="run-1", effect_id="effect-1",
    )
    assert result is None


@pytest.mark.parametrize("repository", [
    _PairRepository(record=object()),
    _PairRepository(preparation=object()),
    _PairRepository(fail=True),
])
def test_partial_legacy_or_unreadable_durable_state_fails_closed(repository) -> None:
    result = modal_training._classify_durable(
        repository=repository, authority=object(), ingress=object(), context=object(),
        baseline=("modal", "config", "provider-staging", "e" * 64),
        project_ref="project-1", run_id="run-1", effect_id="effect-1",
    )
    assert result.code is TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
    assert result.project_ref is result.run_id is result.plan_fingerprint is None


@pytest.mark.parametrize("repository", [
    _PairRepository(record=object()),
    _PairRepository(preparation=object()),
    _PairRepository(fail=True),
])
def test_partial_or_unreadable_state_precedes_sdk_session_and_clock(
    tmp_path, monkeypatch, repository,
) -> None:
    ingress, project = _ingress(tmp_path)
    _install_fakes(monkeypatch, project)
    monkeypatch.setattr(
        modal_training.SqliteTrainingRepository, "from_context",
        classmethod(lambda _cls, *_args, **_kwargs: repository),
    )
    effects = []

    def forbidden(name):
        effects.append(name)
        raise AssertionError(name)

    result = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=ENGINE,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: forbidden("sdk"),
        clock=lambda: forbidden("clock"),
    )
    assert result.code is TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
    assert effects == []


def test_fresh_capabilities_are_256_bit_and_domain_separated() -> None:
    values = iter((b"a" * 32, b"b" * 32))
    first = modal_training._fresh_capability(
        "challenge-source", "project-1", "run-1", lambda _size: next(values)
    )
    second = modal_training._fresh_capability(
        "evidence-source", "project-1", "run-1", lambda _size: next(values)
    )
    assert first != second
    assert first.startswith("challenge-source-")
    with pytest.raises(ValueError):
        modal_training._fresh_capability(
            "challenge-source", "project-1", "run-1", lambda _size: b"short"
        )


def _integration_authority() -> ModalProviderAuthorityV1:
    deployment_ref = "modal-deployment-" + "1" * 32
    profile = ModalProviderProfileV1(
        "modal-a10-v1", "synaptic-training-v1",
        modal_function_name(deployment_ref), deployment_ref,
        "engine://tuner/execution/providers/modal/modal-runtime-v1.lock.json",
        "control-name", "artifact-name",
        (ModalSecretProfileV1(
            "runtime-secrets", ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY")
        ),),
    )
    binding = ModalClientBinding("acct", "workspace", "main", "client", "1.5.4")
    selection = ModalDeploymentSelectionV1.from_profile(
        profile, binding=binding,
        runtime_environment={
            "PATH": "/opt/conda/bin:/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
        }, timeout_seconds=3600,
    )
    volume = lambda name: "modal-volume-" + hashlib.sha256(
        "\0".join((binding.account_ref, binding.environment_ref, name)).encode()
    ).hexdigest()[:32]
    state = ModalProviderStateV1(
        profile, binding, selection,
        volume(profile.control_volume_ref), volume(profile.artifact_volume_ref),
    )
    policy = ModalTrainingPolicyV1(
        "synaptic-modal-training-policy/v1", "modal", "modal-a10-v1", False,
    )
    config = ModalHostConfigV1(
        "main", "modal-a10-v1", policy,
        profile.control_volume_ref, profile.artifact_volume_ref,
        "runtime-secrets", ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"),
        dict(selection.runtime_environment), 3600, 100, "USD",
    )
    return ModalProviderAuthorityV1(
        config, policy, state,
        ModalDeploymentJournalV1(
            config.digest, selection.deployment_ref, selection.function_name, "create"
        ),
    )


def _integration_source() -> SourceLock:
    return SourceLock.from_dict({
        "schema_version": "synaptic-source-lock/v1",
        "run_id": "local-inspection", "created_at": NOW,
        "mode": "superproject",
        "sources": {
            "project": {
                "url": "https://github.com/example/project.git",
                "commit": "b" * 40, "branch": "main", "dirty": False,
                "pushed": False,
            },
            "engine": {
                "url": "https://github.com/example/engine.git",
                "commit": "c" * 40, "branch": "main", "dirty": False,
                "pushed": False, "submodule_path": "synaptic-tuner",
                "gitlink_commit": "c" * 40,
            },
        },
        "project": {}, "configuration": {}, "plugins": [], "inputs": [],
        "runtime": {}, "outputs": {},
    })


class _IntegrationInspector:
    calls = 0
    contexts = []
    expected_context = None

    def inspect(self, *, context):
        assert type(context) is ProjectContext
        expected_context = type(self).expected_context
        if expected_context is not None:
            assert context is expected_context
        type(self).calls += 1
        type(self).contexts.append(context)
        return _integration_source()


class _IntegrationRemote:
    calls = 0

    def read_ref(self, *, canonical_url, exact_ref):
        type(self).calls += 1
        commit = "b" * 40 if canonical_url.endswith("project.git") else "c" * 40
        return f"{commit}\t{exact_ref}\n".encode("ascii")


class _IntegrationSession:
    def __init__(self, authority, facade):
        self.authority, self._facade, self.restores = authority, facade, 0

    def facade(self, state):
        assert state is self.authority.state
        return self._facade

    def restore_function_call(self, reference):
        self.restores += 1
        return EngineFakeFunctionCall.from_id(reference, client=self._facade.client)


def _integration_fixture(tmp_path, monkeypatch):
    document = _document()
    document["model"] = {
        "ref": "unsloth/tiny-model", "revision": "a" * 40,
        "tokenizer_revision": "a" * 40,
    }
    ingress, project = _ingress(tmp_path, document)
    (project / "synaptic.yaml").write_text(
        "schema_version: synaptic-project/v1\n"
        "project: {id: ehr-training, name: EHR Training}\n"
        "engine: {requires: '>=1', api: v1}\n",
        encoding="utf-8",
    )
    engine = project / "synaptic-tuner"
    engine.mkdir()
    authority = _integration_authority()
    state = authority.state
    EngineFakeVolume.calls = []
    EngineFakeFunction.calls = []
    EngineFakeFunction.spawn_calls = []
    EngineFakeFunctionCall.calls = []
    EngineFakeVolume.registry = {
        state.profile.control_volume_ref: EngineFakeVolume(state.control_volume_id),
        state.profile.artifact_volume_ref: EngineFakeVolume(state.artifact_volume_id),
    }
    client = object()
    facade = ExplicitModal154ReadFacade(
        state.binding, sdk=EngineFakeSdk, client=client,
        scope_observer=lambda supplied: (
            state.binding.account_ref, state.binding.workspace_ref,
            state.binding.environment_ref, state.binding.client_ref,
        ) if supplied is client else (),
        deployment_observer=lambda **_kwargs: state.selection,
        volume_names={
            state.control_volume_id: state.profile.control_volume_ref,
            state.artifact_volume_id: state.profile.artifact_volume_ref,
        },
    )
    session = _IntegrationSession(authority, facade)
    monkeypatch.setattr(
        modal_training.ModalProviderAuthorityV1, "load",
        classmethod(lambda _cls, _context: authority),
    )
    monkeypatch.setattr(
        modal_training.ExplicitModalHostSession, "from_credentials",
        classmethod(lambda _cls, **_kwargs: session),
    )
    monkeypatch.setattr(modal_training, "ScopedGitRemoteReader", _IntegrationRemote)
    monkeypatch.setattr(
        modal_composition, "GitCliLocalSourceInspector", _IntegrationInspector,
    )
    monkeypatch.setattr(
        modal_resolver_module, "GitCliLocalSourceInspector", _IntegrationInspector,
    )
    monkeypatch.setattr(
        modal_training, "GitCliLocalSourceInspector", _IntegrationInspector,
    )
    _IntegrationInspector.calls = _IntegrationRemote.calls = 0
    _IntegrationInspector.contexts = []
    _IntegrationInspector.expected_context = None
    return ingress, project, engine, authority, session


def _effect(repository, project_ref, run_id, effect_id):
    record = repository.load(project_ref, run_id)
    assert record is not None
    matches = [item for item in record.effects if item.identity.effect_id == effect_id]
    assert len(matches) == 1
    return matches[0]


def test_durable_static_validation_uses_exact_host_context_and_run_adjacency(
    tmp_path, monkeypatch,
) -> None:
    ingress, project, engine, authority, _session = _integration_fixture(
        tmp_path, monkeypatch
    )
    created = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=engine,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: EngineFakeSdk, clock=lambda: NOW,
    )
    assert created.code is TrainingRunCommandCodeV2.SUBMITTED
    context = modal_training.load_project_manifest(
        project / "synaptic.yaml"
    ).create_context(engine_root=engine, invocation_cwd=project)
    repository = SqliteTrainingRepository.from_context(context, clock=lambda: NOW)
    preparation = repository.load_modal_preparation(
        "ehr-training",
        modal_training._identity("run", "ehr-training", ingress.envelope_digest),
    )
    _IntegrationInspector.contexts = []
    _IntegrationInspector.expected_context = context
    assert modal_training._durable_static_matches(
        preparation, authority, ingress, context
    )
    assert _IntegrationInspector.contexts == [context]

    original = modal_training.ModalDurablePreparationV1.detached_execution_source

    def wrong_run(value):
        return replace(original(value), run_id="different-run")

    monkeypatch.setattr(
        modal_training.ModalDurablePreparationV1,
        "detached_execution_source",
        wrong_run,
    )
    _IntegrationInspector.contexts = []
    assert not modal_training._durable_static_matches(
        preparation, authority, ingress, context
    )
    assert _IntegrationInspector.contexts == []


def test_real_engine_sqlite_attempt_is_durable_before_spawn_and_replay_bypasses(
    tmp_path, monkeypatch,
) -> None:
    ingress, project, engine, _authority, session = _integration_fixture(
        tmp_path, monkeypatch
    )
    project_ref = "ehr-training"
    run_id = modal_training._identity("run", project_ref, ingress.envelope_digest)
    effect_id = modal_training._identity("effect", project_ref, ingress.envelope_digest)
    observations = []
    original_spawn = EngineFakeFunction.spawn

    def spawn(self, *args):
        EngineFakeFunction.spawn_calls.append(args)
        reopened = SqliteTrainingRepository(
            project / ".synaptic" / "state" / "training.sqlite3",
            clock=lambda: NOW,
        )
        effect = _effect(reopened, project_ref, run_id, effect_id)
        observations.append(effect.state)
        assert effect.state is EffectState.ATTEMPTED
        return EngineFakeCall("fc-integration-1")

    monkeypatch.setattr(EngineFakeFunction, "spawn", spawn)
    try:
        first = modal_training.execute_modal_training_run_v2(
            ingress, project_root=project, engine_root=engine,
            token_id="token-id", token_secret="token-secret",
            sdk_loader=lambda: EngineFakeSdk, clock=lambda: NOW,
        )
        debug_repository = SqliteTrainingRepository(
            project / ".synaptic" / "state" / "training.sqlite3", clock=lambda: NOW,
        )
        debug_preparation = debug_repository.load_modal_preparation(project_ref, run_id)
        debug_context = modal_training.load_project_manifest(
            project / "synaptic.yaml"
        ).create_context(engine_root=engine, invocation_cwd=project)
        assert first.code is TrainingRunCommandCodeV2.SUBMITTED, (
            session.restores,
            modal_training._durable_static_matches(
                debug_preparation, _authority, ingress, debug_context
            ),
            debug_preparation.context.deployment.selection == _authority.state.selection,
            debug_preparation.context.binding == _authority.state.binding,
        )
        reopened = SqliteTrainingRepository(
            project / ".synaptic" / "state" / "training.sqlite3",
            clock=lambda: "2026-08-30T12:01:00Z",
        )
        found = _effect(reopened, project_ref, run_id, effect_id)
        assert found.state is EffectState.FOUND
        assert found.provider_job_ref == "fc-integration-1"
        counters = (_IntegrationInspector.calls, _IntegrationRemote.calls, len(EngineFakeFunction.spawn_calls))
        second = modal_training.execute_modal_training_run_v2(
            ingress, project_root=project, engine_root=engine,
            token_id="token-id", token_secret="token-secret",
            sdk_loader=lambda: EngineFakeSdk,
            clock=lambda: "2026-08-30T12:01:00Z",
        )
        assert second.code is TrainingRunCommandCodeV2.SUBMITTED
        assert _IntegrationInspector.calls == counters[0] + 1
        assert (_IntegrationRemote.calls, len(EngineFakeFunction.spawn_calls)) == counters[1:]
        assert session.restores == 2
        assert observations == [EffectState.ATTEMPTED]
    finally:
        monkeypatch.setattr(EngineFakeFunction, "spawn", original_spawn)


@pytest.mark.parametrize("field", [
    "input_digest",
    "contract_identity_digest",
    "source_sha256",
    "envelope_digest",
    "provider_policy_digest",
])
def test_each_persisted_provenance_change_requires_reconciliation(
    tmp_path, monkeypatch, field,
) -> None:
    ingress, project, engine, authority, _session = _integration_fixture(
        tmp_path, monkeypatch
    )
    created = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=engine,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: EngineFakeSdk, clock=lambda: NOW,
    )
    assert created.code is TrainingRunCommandCodeV2.SUBMITTED
    project_ref = "ehr-training"
    original_envelope = ingress.envelope_digest
    run_id = modal_training._identity("run", project_ref, original_envelope)
    effect_id = modal_training._identity("effect", project_ref, original_envelope)
    context = modal_training.load_project_manifest(
        project / "synaptic.yaml"
    ).create_context(engine_root=engine, invocation_cwd=project)
    repository = SqliteTrainingRepository.from_context(context, clock=lambda: NOW)
    baseline = modal_training._authenticate_training_run_ingress_v1(ingress)
    assert baseline is not None
    if field == "provider_policy_digest":
        target, name, replacement = authority.training, "load_in_4bit", True
    else:
        target, name, replacement = ingress, field, "f" * 64
    prior = object.__getattribute__(target, name)
    object.__setattr__(target, name, replacement)
    try:
        result = modal_training._classify_durable(
            repository=repository, authority=authority, ingress=ingress,
            context=context, baseline=baseline, project_ref=project_ref,
            run_id=run_id, effect_id=effect_id,
        )
    finally:
        object.__setattr__(target, name, prior)
    assert result.code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
    assert result.project_ref == project_ref
    assert result.run_id == run_id
    assert result.effect_id == effect_id


def test_sqlite_replay_with_plan_fingerprint_mismatch_fails_before_sdk(
    tmp_path, monkeypatch,
) -> None:
    ingress, project, engine, _authority, _session = _integration_fixture(
        tmp_path, monkeypatch
    )
    created = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=engine,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: EngineFakeSdk, clock=lambda: NOW,
    )
    assert created.code is TrainingRunCommandCodeV2.SUBMITTED
    database = project / ".synaptic" / "state" / "training.sqlite3"
    with sqlite3.connect(database) as connection:
        raw = connection.execute(
            "SELECT preparation_json FROM modal_preparations"
        ).fetchone()[0]
        document = json.loads(bytes(raw))
        document["public_plan_fingerprint"] = "f" * 64
        poisoned = json.dumps(
            document, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        connection.execute(
            "UPDATE modal_preparations SET preparation_json = ?", (poisoned,)
        )
    effects = []
    replay = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=engine,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: effects.append("sdk"),
        clock=lambda: NOW,
    )
    assert replay.code is TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE
    assert effects == []


def test_real_engine_sqlite_interrupted_spawn_is_never_retried(
    tmp_path, monkeypatch,
) -> None:
    ingress, project, engine, _authority, _session = _integration_fixture(
        tmp_path, monkeypatch
    )
    manifest = modal_training.load_project_manifest(project / "synaptic.yaml")
    context = manifest.create_context(engine_root=engine, invocation_cwd=project)
    authenticator = modal_training.FileHmacAuthenticator.from_context(context)
    authenticator.initialize()
    SqliteTrainingRepository.from_context(context, clock=lambda: NOW)
    project_ref = "ehr-training"
    run_id = modal_training._identity("run", project_ref, ingress.envelope_digest)
    effect_id = modal_training._identity("effect", project_ref, ingress.envelope_digest)
    calls = 0

    def spawn(_self, *_args):
        nonlocal calls
        calls += 1
        reopened = SqliteTrainingRepository(
            project / ".synaptic" / "state" / "training.sqlite3", clock=lambda: NOW,
        )
        assert _effect(reopened, project_ref, run_id, effect_id).state is EffectState.ATTEMPTED
        raise RuntimeError("private provider interruption")

    monkeypatch.setattr(EngineFakeFunction, "spawn", spawn)
    first = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=engine,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: EngineFakeSdk, clock=lambda: NOW,
    )
    second = modal_training.execute_modal_training_run_v2(
        ingress, project_root=project, engine_root=engine,
        token_id="token-id", token_secret="token-secret",
        sdk_loader=lambda: EngineFakeSdk, clock=lambda: "2026-08-30T12:01:00Z",
    )
    assert first.code is second.code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
    assert calls == 1


@pytest.mark.parametrize("_iteration", range(5))
def test_real_engine_sqlite_concurrent_wrappers_converge_to_one_spawn(
    tmp_path, monkeypatch, _iteration,
) -> None:
    import threading

    ingress, project, engine, _authority, _session = _integration_fixture(
        tmp_path, monkeypatch
    )
    manifest = modal_training.load_project_manifest(project / "synaptic.yaml")
    context = manifest.create_context(engine_root=engine, invocation_cwd=project)
    authenticator = modal_training.FileHmacAuthenticator.from_context(context)
    authenticator.initialize()
    SqliteTrainingRepository.from_context(context, clock=lambda: NOW)
    project_ref = "ehr-training"
    run_id = modal_training._identity("run", project_ref, ingress.envelope_digest)
    effect_id = modal_training._identity("effect", project_ref, ingress.envelope_digest)
    start_barrier = threading.Barrier(2)
    spawn_entered = threading.Event()
    release_spawn = threading.Event()
    calls = 0

    def spawn(_self, *_args):
        nonlocal calls
        calls += 1
        reopened = SqliteTrainingRepository(
            project / ".synaptic" / "state" / "training.sqlite3", clock=lambda: NOW,
        )
        assert _effect(reopened, project_ref, run_id, effect_id).state is EffectState.ATTEMPTED
        spawn_entered.set()
        assert release_spawn.wait(10)
        return EngineFakeCall("fc-concurrent-1")

    monkeypatch.setattr(EngineFakeFunction, "spawn", spawn)

    def invoke():
        start_barrier.wait()
        return modal_training.execute_modal_training_run_v2(
            ingress, project_root=project, engine_root=engine,
            token_id="token-id", token_secret="token-secret",
            sdk_loader=lambda: EngineFakeSdk, clock=lambda: NOW,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (pool.submit(invoke), pool.submit(invoke))
        assert spawn_entered.wait(10)
        completed, _pending = wait(futures, timeout=10, return_when=FIRST_COMPLETED)
        assert len(completed) == 1
        assert next(iter(completed)).result().code is TrainingRunCommandCodeV2.RECONCILE_REQUIRED
        release_spawn.set()
        results = tuple(future.result(timeout=10) for future in futures)
    assert calls == 1
    assert {result.code for result in results} == {
        TrainingRunCommandCodeV2.RECONCILE_REQUIRED,
        TrainingRunCommandCodeV2.SUBMITTED,
    }
    reopened = SqliteTrainingRepository(
        project / ".synaptic" / "state" / "training.sqlite3", clock=lambda: NOW,
    )
    found = _effect(reopened, project_ref, run_id, effect_id)
    assert found.state is EffectState.FOUND
    assert found.provider_job_ref == "fc-concurrent-1"
