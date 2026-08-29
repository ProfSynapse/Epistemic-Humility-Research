from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import (
    AuthenticatedSourceEvidenceV1, CanonicalDocument, ExecutionSourceV1,
    ProjectContext, SourceLock, TrainingInputV1, TrainingPlan, TrainingRequest,
    TrainingResolutionError,
)
from synaptic_tuner.api.v1.modal import (
    ModalClientBinding, ModalDeploymentSelectionV1,
    ModalExecutionSourceResolutionV1, ModalProviderProfileV1,
    ModalSecretProfileV1, VerifiedModalDeploymentIdentityV1,
    modal_function_name,
)
from synaptic_host.modal_provider import (
    ModalDeploymentJournalV1, ModalHostConfigV1, ModalProviderAuthorityV1,
    ModalTrainingPolicyV1,
)
from synaptic_host.modal_resolver import (
    ModalProviderStateV1, ModalTrainingIntentV1, ModalTrainingResolverV1,
)


def profile() -> ModalProviderProfileV1:
    deployment_ref = "modal-deployment-" + "1" * 32
    return ModalProviderProfileV1(
        "modal-a10-v1", "synaptic-training-v1",
        modal_function_name(deployment_ref), deployment_ref,
        "engine://tuner/execution/providers/modal/modal-runtime-v1.lock.json",
        "synaptic-training-control-v1", "synaptic-training-artifacts-v1",
        (ModalSecretProfileV1(
            "synaptic-training-runtime-v1",
            ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"),
        ),),
    )


def _volume_ref(binding: ModalClientBinding, name: str) -> str:
    payload = "\0".join((binding.account_ref, binding.environment_ref, name))
    return "modal-volume-" + hashlib.sha256(payload.encode()).hexdigest()[:32]


def state() -> ModalProviderStateV1:
    binding = ModalClientBinding("acct", "workspace", "main", "client", "1.5.4")
    selection = ModalDeploymentSelectionV1.from_profile(
        profile(), binding=binding,
        runtime_environment={
            "PATH": "/opt/conda/bin:/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8",
        }, timeout_seconds=3600,
    )
    return ModalProviderStateV1(
        profile(), binding, selection,
        _volume_ref(binding, profile().control_volume_ref),
        _volume_ref(binding, profile().artifact_volume_ref),
    )


def authority(*, load_in_4bit: bool = False) -> ModalProviderAuthorityV1:
    policy = ModalTrainingPolicyV1(
        "synaptic-modal-training-policy/v1", "modal", "modal-a10-v1",
        load_in_4bit,
    )
    selected = state().selection
    config = ModalHostConfigV1(
        "main", "modal-a10-v1", policy,
        profile().control_volume_ref, profile().artifact_volume_ref,
        "synaptic-training-runtime-v1",
        ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"),
        dict(selected.runtime_environment), 3600, 100, "USD",
    )
    journal = ModalDeploymentJournalV1(
        config.digest, selected.deployment_ref, selected.function_name, "create"
    )
    return ModalProviderAuthorityV1(config, policy, state(), journal)


def training_input(
    dataset_ref: str = "project://data/train.jsonl", *, seed: int = 1,
) -> TrainingInputV1:
    return TrainingInputV1.from_dict({
        "schema_version": "synaptic-training-input/v1", "method": "sft",
        "model": {
            "ref": "example/model", "revision": "a" * 40,
            "tokenizer_revision": "a" * 40,
        },
        "dataset": {"ref": dataset_ref},
        "hyperparameters": {
            "schema_version": "synaptic-sft-hyperparameters/v1",
            "batch_size": 1, "gradient_accumulation_steps": 1,
            "learning_rate": 0.0002,
            "duration": {"max_steps": 1, "num_epochs": None},
            "max_seq_length": 128, "seed": seed, "save_steps": 1,
            "save_total_limit": 1, "lora_rank": 8, "lora_alpha": 16,
            "lora_dropout": 0.0, "lora_target_modules": ["q_proj"],
            "use_dora": False, "use_rslora": False,
            "init_lora_weights": True, "split_dataset": False,
        },
        "artifacts": {
            "required_kinds": ["final_model", "training_lineage"],
            "retain_checkpoints": False,
        },
    })


def intent() -> ModalTrainingIntentV1:
    return ModalTrainingIntentV1(
        "ehr", "run-1", "2026-08-26T12:00:00Z", "modal-evidence-v1",
        "2026-08-26T12:05:00Z", 100, "USD", "effect-run-1",
        "slot-run-1", "nonce-run-1",
    )


def source_lock() -> SourceLock:
    return SourceLock.from_dict({
        "schema_version": "synaptic-source-lock/v1",
        "run_id": "local-inspection", "created_at": "2026-08-26T11:59:00Z",
        "mode": "superproject",
        "sources": {
            "project": {
                "url": "https://github.com/example/project.git", "commit": "b" * 40,
                "branch": "main", "dirty": False, "pushed": False,
            },
            "engine": {
                "url": "https://github.com/example/engine.git", "commit": "c" * 40,
                "branch": "main", "dirty": False, "pushed": False,
                "submodule_path": "synaptic-tuner", "gitlink_commit": "c" * 40,
            },
        },
        "project": {}, "configuration": {}, "plugins": [], "inputs": [],
        "runtime": {}, "outputs": {},
    })


class FakeInspector:
    def __init__(self, lock: SourceLock, callback=None) -> None:
        self.lock, self.callback, self.calls = lock, callback, 0

    def inspect(self, *, context):
        self.calls += 1
        if self.callback:
            self.callback()
        return self.lock


class FakeFinalizer:
    def __init__(self, callback=None) -> None:
        self.callback = callback
        self.locks: list[SourceLock] = []

    def finalize(self, source_lock, *, context, deployment, audience_ref):
        self.locks.append(source_lock)
        if self.callback:
            self.callback()
        payload = {
            "schema_version": "synaptic-verified-modal-deployment/v1",
            "selection": deployment.to_dict(), "issuer_ref": "modal-verifier",
            "evidence_ref": "deployment-proof", "audience_ref": audience_ref,
            "challenge_nonce": "deployment-nonce",
            "verified_at": "2026-08-26T12:00:00Z",
            "expires_at": "2026-08-26T12:10:00Z", "key_ref": "modal-evidence-v1",
        }
        verified = VerifiedModalDeploymentIdentityV1(
            selection=deployment, issuer_ref=payload["issuer_ref"],
            evidence_ref=payload["evidence_ref"], audience_ref=audience_ref,
            challenge_nonce=payload["challenge_nonce"],
            verified_at=payload["verified_at"], expires_at=payload["expires_at"],
            key_ref=payload["key_ref"], tag_base64=base64.b64encode(b"tag").decode(),
            attestation_digest=hashlib.sha256(json.dumps(
                payload, sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest(),
        )
        roots = {
            "engine": "/workspace/engine", "project": "/workspace/project",
            "artifacts": f"/workspace/run/{source_lock.run_id}/artifacts",
            "state": f"/workspace/run/{source_lock.run_id}/state",
            "tracking": f"/workspace/run/{source_lock.run_id}/tracking",
            "cache": f"/workspace/run/{source_lock.run_id}/cache",
            "tmp": f"/workspace/run/{source_lock.run_id}/tmp",
        }
        environment = {
            **dict(deployment.runtime_environment), "PYTHONNOUSERSITE": "1",
            "PYTHONSAFEPATH": "1", "PYTHONPATH": roots["engine"],
            "SYNAPTIC_ENGINE_ROOT": roots["engine"],
            "SYNAPTIC_PROJECT_ROOT": roots["project"],
            "SYNAPTIC_ARTIFACT_ROOT": roots["artifacts"],
            "SYNAPTIC_STATE_ROOT": roots["state"],
            "SYNAPTIC_TRACKING_ROOT": roots["tracking"],
            "SYNAPTIC_CACHE_ROOT": roots["cache"], "SYNAPTIC_TMP_ROOT": roots["tmp"],
            "HF_HOME": roots["cache"] + "/huggingface",
            "TRANSFORMERS_CACHE": roots["cache"] + "/transformers",
            "WANDB_DISABLED": "true",
        }
        evidence = AuthenticatedSourceEvidenceV1(
            project_url=source_lock.project_source.location.canonical_url,
            project_commit=source_lock.project_source.commit,
            engine_url=source_lock.engine_source.location.canonical_url,
            engine_commit=source_lock.engine_source.commit,
            engine_submodule_path=source_lock.engine_source.submodule_path,
            gitlink_commit=source_lock.engine_source.gitlink_commit,
            source_lock_binding=source_lock.binding,
            issuer_ref="git-verifier", evidence_ref="source-proof",
            audience_ref=audience_ref, challenge_nonce="source-nonce",
            verified_at="2026-08-26T12:00:00Z",
            expires_at="2026-08-26T12:10:00Z", key_ref="modal-evidence-v1",
            tag_base64="dGFn", attestation_digest="9" * 64,
        )
        execution = ExecutionSourceV1(
            run_id=source_lock.run_id, created_at=source_lock.created_at,
            project_source=source_lock.project_source,
            engine_source=source_lock.engine_source,
            engine_submodule_path=source_lock.engine_source.submodule_path,
            source_evidence=evidence,
            deployment_member_sha256=hashlib.sha256(json.dumps(
                verified.to_dict(), sort_keys=True, separators=(",", ":")
            ).encode()).hexdigest(),
            roots=roots, writable_capability_root="/workspace/run",
            python_implementation="cpython", python_version=deployment.python_version,
            python_executable=deployment.python_executable,
            python_executable_digest=deployment.python_executable_digest,
            environment=environment,
            secret_requirements_digest=deployment.secret_requirements_digest,
            provider_runtime_requirements_digest=deployment.provider_runtime_requirements_digest,
        )
        return ModalExecutionSourceResolutionV1(execution, verified)


def project(tmp_path: Path) -> tuple[ProjectContext, Path]:
    root, engine = tmp_path / "project", tmp_path / "project" / "synaptic-tuner"
    dataset = root / "data" / "train.jsonl"
    engine.mkdir(parents=True)
    dataset.parent.mkdir()
    dataset.write_text('{"text":"one"}\n', encoding="utf-8")
    return ProjectContext.host(engine_root=engine, project_root=root), dataset


def resolver(
    value: TrainingInputV1, finalizer: FakeFinalizer, *, inspector=None,
    provider=None, contract_digest="2" * 64, source_digest="3" * 64,
    ingress_digest="4" * 64,
) -> ModalTrainingResolverV1:
    return ModalTrainingResolverV1(
        training_input=value, input_type=TrainingInputV1,
        input_digest=value.input_digest(), contract_identity_digest=contract_digest,
        source_sha256=source_digest, ingress_digest=ingress_digest,
        provider_authority=provider or authority(), intent=intent(),
        finalizer=finalizer, source_inspector=inspector or FakeInspector(source_lock()),
    )


def request(value: TrainingInputV1) -> TrainingRequest:
    return TrainingRequest(CanonicalDocument.from_mapping(value.to_dict()))


def plan(components) -> TrainingPlan:
    return TrainingPlan(
        components.execution_source, components.execution_context,
        components.resolved_config,
        CanonicalDocument.from_mapping({"schema_version": "workload/v1"}),
        components.runtime, components.resources, components.artifact_policy,
    )


def test_provider_state_and_intent_contracts_remain_exact() -> None:
    value = state()
    assert ModalProviderStateV1.from_mapping(value.to_dict()) == value
    assert "token-value" not in json.dumps(value.to_dict(), sort_keys=True)
    assert len(intent().quote_digest) == 64


def test_old_resolver_and_parser_are_absent() -> None:
    import synaptic_host
    import synaptic_host.modal_resolver as module
    assert not hasattr(module, "StrictModalTrainingResolver")
    assert not hasattr(module.ModalTrainingResolverV1, "_request")
    assert not hasattr(module.ModalTrainingResolverV1, "load_document")
    assert "StrictModalTrainingResolver" not in synaptic_host.__all__
    assert synaptic_host.ModalTrainingResolverV1 is ModalTrainingResolverV1


def test_resolver_requires_exact_contract_type_and_digest() -> None:
    value, finalizer = training_input(), FakeFinalizer()
    arguments = dict(
        training_input=value, input_digest=value.input_digest(),
        contract_identity_digest="2" * 64, source_sha256="3" * 64,
        ingress_digest="4" * 64, provider_authority=authority(), intent=intent(),
        finalizer=finalizer,
    )
    with pytest.raises(TypeError, match="exact released"):
        ModalTrainingResolverV1(input_type=object, **arguments)
    with pytest.raises(ValueError, match="differs"):
        ModalTrainingResolverV1(
            input_type=TrainingInputV1, **{**arguments, "input_digest": "f" * 64}
        )
    class Lookalike:
        def input_digest(self):
            return value.input_digest()
    with pytest.raises(TypeError, match="exact released"):
        ModalTrainingResolverV1(
            input_type=TrainingInputV1,
            **{**arguments, "training_input": Lookalike()},
        )


def test_resolver_rejects_request_canonical_mismatch(tmp_path: Path) -> None:
    context, _ = project(tmp_path)
    baseline = training_input()
    with pytest.raises(TrainingResolutionError, match="differs"):
        resolver(baseline, FakeFinalizer()).resolve(
            request(training_input(seed=2)), context=context
        )


def test_resolver_revalidates_input_and_policy_after_callbacks(tmp_path: Path) -> None:
    context, _ = project(tmp_path)
    value = training_input()
    provider = authority()
    instance = resolver(value, FakeFinalizer(), provider=provider)
    original_seed = value.hyperparameters.seed
    object.__setattr__(value.hyperparameters, "seed", original_seed + 1)
    try:
        with pytest.raises(TrainingResolutionError, match="authority changed"):
            instance.resolve(request(training_input()), context=context)
    finally:
        object.__setattr__(value.hyperparameters, "seed", original_seed)

    second_context, _ = project(tmp_path / "policy")
    instance = resolver(value, FakeFinalizer(), provider=provider)
    original_policy = provider.training
    replacement_policy = ModalTrainingPolicyV1(
        original_policy.schema_version, original_policy.provider_ref,
        original_policy.profile_ref, True,
    )
    object.__setattr__(provider, "training", replacement_policy)
    try:
        with pytest.raises(TrainingResolutionError, match="authority changed"):
            instance.resolve(request(value), context=second_context)
    finally:
        object.__setattr__(provider, "training", original_policy)


def test_resolver_compiles_neutral_input_policy_artifacts_and_exact_provenance(
    tmp_path: Path,
) -> None:
    context, dataset = project(tmp_path)
    value, finalizer = training_input(), FakeFinalizer()
    before_modal = sys.modules.get("modal")
    resolved = resolver(value, finalizer).resolve(request(value), context=context)
    config = resolved.resolved_config.to_dict()
    assert config["model"] == {**value.model.to_dict(), "load_in_4bit": False}
    assert config["dataset"] == {
        "ref": value.dataset.ref, "revision": "b" * 40,
        "content_digest": hashlib.sha256(dataset.read_bytes()).hexdigest(),
    }
    assert config["sft"]["max_steps"] == 1
    assert "duration" not in config["sft"] and "schema_version" not in config["sft"]
    assert resolved.artifact_policy.required_kinds == value.artifacts.required_kinds
    assert resolved.artifact_policy.retain_checkpoints is False
    assert set(finalizer.locks[0].configuration) == {
        "training_input_digest", "training_contract_identity_digest",
        "training_source_sha256", "training_ingress_digest", "provider_policy_digest",
    }
    for document in (resolved.resolved_config.to_dict(), resolved.execution_context.to_dict()):
        assert not any(key in json.dumps(document) for key in finalizer.locks[0].configuration)
    assert resolved.execution_source.source_evidence.source_lock_binding == finalizer.locks[0].binding
    assert sys.modules.get("modal") is before_modal


def test_policy_is_the_only_quantization_source(tmp_path: Path) -> None:
    value = training_input()
    false_context, _ = project(tmp_path / "false")
    true_context, _ = project(tmp_path / "true")
    false = resolver(value, FakeFinalizer()).resolve(request(value), context=false_context)
    true = resolver(value, FakeFinalizer(), provider=authority(load_in_4bit=True)).resolve(
        request(value), context=true_context
    )
    assert false.resolved_config.to_dict()["model"]["load_in_4bit"] is False
    assert true.resolved_config.to_dict()["model"]["load_in_4bit"] is True


def test_num_epochs_duration_flattens_without_max_steps(tmp_path: Path) -> None:
    value = TrainingInputV1.from_dict({
        **training_input().to_dict(),
        "hyperparameters": {
            **training_input().hyperparameters.to_dict(),
            "duration": {"max_steps": None, "num_epochs": 2.5},
        },
    })
    context, _ = project(tmp_path)
    resolved = resolver(value, FakeFinalizer()).resolve(request(value), context=context)
    sft = resolved.resolved_config.to_dict()["sft"]
    assert sft["num_epochs"] == 2.5
    assert "max_steps" not in sft


def test_dataset_rejects_symlink_and_inspection_mutation(tmp_path: Path) -> None:
    context, dataset = project(tmp_path)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("outside", encoding="utf-8")
    link = dataset.parent / "linked.jsonl"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    linked = training_input("project://data/linked.jsonl")
    with pytest.raises(TrainingResolutionError):
        resolver(linked, FakeFinalizer()).resolve(request(linked), context=context)
    value = training_input()
    inspector = FakeInspector(
        source_lock(), callback=lambda: dataset.write_text("changed", encoding="utf-8")
    )
    with pytest.raises(TrainingResolutionError, match="changed"):
        resolver(value, FakeFinalizer(), inspector=inspector).resolve(
            request(value), context=context
        )


def test_dataset_rejects_finalizer_mutation(tmp_path: Path) -> None:
    context, dataset = project(tmp_path)
    value = training_input()
    finalizer = FakeFinalizer(
        callback=lambda: dataset.write_text("changed-finalizer", encoding="utf-8")
    )
    with pytest.raises(TrainingResolutionError, match="changed"):
        resolver(value, finalizer).resolve(request(value), context=context)


@pytest.mark.parametrize(
    "variant", ["training_input", "contract", "source", "ingress", "policy"],
)
def test_each_provenance_key_changes_authenticated_source_and_actual_plan_fingerprint(
    tmp_path: Path, variant: str,
) -> None:
    base_input = training_input()
    changed_input = training_input(seed=2) if variant == "training_input" else base_input
    baseline_finalizer, changed_finalizer = FakeFinalizer(), FakeFinalizer()
    baseline_context, _ = project(tmp_path / "baseline")
    changed_context, _ = project(tmp_path / "changed")
    baseline = resolver(base_input, baseline_finalizer).resolve(
        request(base_input), context=baseline_context
    )
    kwargs = {}
    if variant == "contract":
        kwargs["contract_digest"] = "a" * 64
    elif variant == "source":
        kwargs["source_digest"] = "a" * 64
    elif variant == "ingress":
        kwargs["ingress_digest"] = "a" * 64
    elif variant == "policy":
        kwargs["provider"] = authority(load_in_4bit=True)
    changed = resolver(changed_input, changed_finalizer, **kwargs).resolve(
        request(changed_input), context=changed_context
    )
    key = {
        "training_input": "training_input_digest",
        "contract": "training_contract_identity_digest",
        "source": "training_source_sha256",
        "ingress": "training_ingress_digest",
        "policy": "provider_policy_digest",
    }[variant]
    assert baseline_finalizer.locks[0].configuration[key] != changed_finalizer.locks[0].configuration[key]
    assert baseline.execution_source.source_evidence.source_lock_binding != changed.execution_source.source_evidence.source_lock_binding
    assert plan(baseline).fingerprint != plan(changed).fingerprint


@pytest.mark.parametrize(
    "field", ["input_digest", "contract_identity_digest", "source_sha256", "ingress_digest"],
)
def test_resolver_rejects_pre_call_authoritative_scalar_mutation(
    tmp_path: Path, field: str,
) -> None:
    context, _ = project(tmp_path)
    value = training_input()
    instance = resolver(value, FakeFinalizer())
    setattr(instance, field, "f" * 64)
    with pytest.raises(TrainingResolutionError, match="authority changed"):
        instance.resolve(request(value), context=context)


def test_resolver_rejects_collaborator_replacement_before_and_during_callbacks(
    tmp_path: Path,
) -> None:
    value = training_input()
    context, _ = project(tmp_path / "before")
    instance = resolver(value, FakeFinalizer())
    instance.source_inspector = FakeInspector(source_lock())
    with pytest.raises(TrainingResolutionError, match="authority changed"):
        instance.resolve(request(value), context=context)

    during_context, _ = project(tmp_path / "during")
    holder = {}
    inspector = FakeInspector(
        source_lock(), callback=lambda: setattr(holder["resolver"], "finalizer", FakeFinalizer())
    )
    instance = resolver(value, FakeFinalizer(), inspector=inspector)
    holder["resolver"] = instance
    with pytest.raises(TrainingResolutionError, match="authority changed"):
        instance.resolve(request(value), context=during_context)


@pytest.mark.parametrize("stage", ["inspector", "finalizer"])
@pytest.mark.parametrize(
    "field", ["input_digest", "contract_identity_digest", "source_sha256", "ingress_digest"],
)
def test_resolver_rechecks_every_scalar_immediately_after_each_callback(
    tmp_path: Path, stage: str, field: str,
) -> None:
    value = training_input()
    context, _ = project(tmp_path)
    holder = {}
    callback = lambda: setattr(holder["resolver"], field, "f" * 64)
    inspector = FakeInspector(source_lock(), callback=callback if stage == "inspector" else None)
    finalizer = FakeFinalizer(callback=callback if stage == "finalizer" else None)
    instance = resolver(value, finalizer, inspector=inspector)
    holder["resolver"] = instance
    with pytest.raises(TrainingResolutionError, match="authority changed"):
        instance.resolve(request(value), context=context)


class _ReducingFinalizer(FakeFinalizer):
    def finalize(self, source_lock, *, context, deployment, audience_ref):
        object.__setattr__(
            source_lock, "configuration",
            {"training_input_digest": source_lock.configuration["training_input_digest"]},
        )
        return super().finalize(
            source_lock, context=context, deployment=deployment, audience_ref=audience_ref
        )


class _SubstitutingLockFinalizer(FakeFinalizer):
    def finalize(self, source_lock, *, context, deployment, audience_ref):
        substituted = replace(
            source_lock,
            configuration={
                "training_input_digest": source_lock.configuration["training_input_digest"]
            },
        )
        return super().finalize(
            substituted, context=context, deployment=deployment, audience_ref=audience_ref
        )


@pytest.mark.parametrize("finalizer", [_ReducingFinalizer(), _SubstitutingLockFinalizer()])
def test_finalizer_cannot_reduce_or_substitute_the_five_key_lock(
    tmp_path: Path, finalizer: FakeFinalizer,
) -> None:
    context, _ = project(tmp_path)
    value = training_input()
    with pytest.raises(TrainingResolutionError, match="provenance|unauthenticated"):
        resolver(value, finalizer).resolve(request(value), context=context)


class _DeploymentSubstitutionFinalizer(FakeFinalizer):
    def finalize(self, source_lock, *, context, deployment, audience_ref):
        changed = ModalDeploymentSelectionV1.from_dict({
            **deployment.to_dict(), "timeout_seconds": 7200,
        })
        return super().finalize(
            source_lock, context=context, deployment=changed, audience_ref=audience_ref
        )


def test_returned_deployment_must_equal_authority_selection(tmp_path: Path) -> None:
    context, _ = project(tmp_path)
    value = training_input()
    with pytest.raises(TrainingResolutionError, match="unauthenticated"):
        resolver(value, _DeploymentSubstitutionFinalizer()).resolve(
            request(value), context=context
        )


def _assert_closed_failure(caught: pytest.ExceptionInfo[TrainingResolutionError]) -> None:
    assert str(caught.value) == "Modal training resolution failed"
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None
    assert "private-callback-value" not in str(caught.value)


@pytest.mark.parametrize("collaborator", ["inspector", "finalizer"])
def test_collaborator_exceptions_are_fresh_and_closed(
    tmp_path: Path, collaborator: str,
) -> None:
    class ExplodingInspector:
        def inspect(self, *, context):
            raise RuntimeError("private-callback-value")

    class ExplodingFinalizer:
        def finalize(self, *args, **kwargs):
            raise RuntimeError("private-callback-value")

    context, _ = project(tmp_path)
    value = training_input()
    instance = resolver(
        value,
        ExplodingFinalizer() if collaborator == "finalizer" else FakeFinalizer(),
        inspector=(
            ExplodingInspector() if collaborator == "inspector"
            else FakeInspector(source_lock())
        ),
    )
    with pytest.raises(TrainingResolutionError) as caught:
        instance.resolve(request(value), context=context)
    _assert_closed_failure(caught)


def test_descriptor_identity_rejects_opened_file_substitution(
    tmp_path: Path, monkeypatch,
) -> None:
    context, dataset = project(tmp_path)
    replacement = dataset.parent / "replacement.jsonl"
    replacement.write_text('{"text":"two"}\n', encoding="utf-8")
    real_open = os.open

    def substituted_open(path, flags, *args):
        if Path(path) == dataset:
            return real_open(replacement, flags, *args)
        return real_open(path, flags, *args)

    monkeypatch.setattr(os, "open", substituted_open)
    value = training_input()
    with pytest.raises(TrainingResolutionError) as caught:
        resolver(value, FakeFinalizer()).resolve(request(value), context=context)
    _assert_closed_failure(caught)


@pytest.mark.parametrize("operation", ["lstat", "open"])
def test_dataset_path_and_open_errors_are_fresh_and_closed(
    tmp_path: Path, monkeypatch, operation: str,
) -> None:
    context, dataset = project(tmp_path)
    if operation == "open":
        real_open = os.open

        def failing_open(path, flags, *args):
            if Path(path) == dataset:
                raise RuntimeError("private-callback-value")
            return real_open(path, flags, *args)

        monkeypatch.setattr(os, "open", failing_open)
    else:
        real_lstat = Path.lstat

        def failing_lstat(path):
            if path == dataset:
                raise RuntimeError("private-callback-value")
            return real_lstat(path)

        monkeypatch.setattr(Path, "lstat", failing_lstat)
    value = training_input()
    with pytest.raises(TrainingResolutionError) as caught:
        resolver(value, FakeFinalizer()).resolve(request(value), context=context)
    _assert_closed_failure(caught)


@pytest.mark.parametrize("operation", ["read", "fstat", "close"])
def test_descriptor_io_failures_are_fresh_and_closed(
    tmp_path: Path, monkeypatch, operation: str,
) -> None:
    context, dataset = project(tmp_path)
    target_descriptors: set[int] = set()
    real_open, real_read, real_fstat, real_close = os.open, os.read, os.fstat, os.close

    def tracking_open(path, flags, *args):
        descriptor = real_open(path, flags, *args)
        if Path(path) == dataset:
            target_descriptors.add(descriptor)
        return descriptor

    def failing_read(descriptor, count):
        if descriptor in target_descriptors and operation == "read":
            raise RuntimeError("private-callback-value")
        return real_read(descriptor, count)

    def failing_fstat(descriptor):
        if descriptor in target_descriptors and operation == "fstat":
            raise RuntimeError("private-callback-value")
        return real_fstat(descriptor)

    def failing_close(descriptor):
        if descriptor in target_descriptors and operation == "close":
            target_descriptors.remove(descriptor)
            real_close(descriptor)
            raise RuntimeError("private-callback-value")
        return real_close(descriptor)

    monkeypatch.setattr(os, "open", tracking_open)
    monkeypatch.setattr(os, "read", failing_read)
    monkeypatch.setattr(os, "fstat", failing_fstat)
    monkeypatch.setattr(os, "close", failing_close)
    value = training_input()
    with pytest.raises(TrainingResolutionError) as caught:
        resolver(value, FakeFinalizer()).resolve(request(value), context=context)
    _assert_closed_failure(caught)


def test_neutral_smoke_document_uses_released_training_input_contract() -> None:
    path = Path(__file__).parents[2] / "training" / "smokes" / "modal-sft.json"
    value = TrainingInputV1.from_json(path.read_text(encoding="utf-8"))
    assert value.method.value == "sft"
    assert value.hyperparameters.duration.max_steps == 1
    assert "provider_profile" not in value.to_dict()
