from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import (
    AuthenticatedSourceEvidenceV1, CanonicalDocument, ExecutionSourceV1,
    ProjectContext, SourceLock, TrainingRequest,
)
from synaptic_tuner.api.v1.modal import (
    ModalClientBinding,
    ModalDeploymentSelectionV1,
    ModalExecutionSourceResolutionV1,
    ModalProviderProfileV1,
    ModalRuntimeLockV1,
    ModalSecretProfileV1,
    VerifiedModalDeploymentIdentityV1,
)
from synaptic_host.modal_resolver import (
    ModalProviderStateV1,
    ModalTrainingIntentV1,
    StrictModalTrainingResolver,
)


def profile() -> ModalProviderProfileV1:
    return ModalProviderProfileV1(
        "modal-a10-v1", "synaptic-training-v1", "run_sft_v1", "1",
        "im-runtime-1",
        "engine://tuner/execution/providers/modal/modal-runtime-v1.lock.json",
        "synaptic-training-control-v1", "synaptic-training-artifacts-v1",
        (ModalSecretProfileV1(
            "synaptic-training-runtime-v1",
            ("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY"),
        ),),
    )


def state() -> ModalProviderStateV1:
    binding = ModalClientBinding("acct", "workspace", "main", "client", "1.5.4")
    selection = ModalDeploymentSelectionV1.from_profile(
        profile(), binding=binding,
        runtime_environment={
            "PATH": "/opt/conda/bin:/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
        }, timeout_seconds=3600,
    )
    return ModalProviderStateV1(profile(), binding, selection, "vo-control", "vo-artifact")


def training_input(dataset_ref: str) -> dict[str, object]:
    return {
        "schema_version": "synaptic-training-input/v1",
        "method": "sft",
        "provider_profile": "modal-a10-v1",
        "model": {
            "ref": "example/model", "revision": "a" * 40,
            "tokenizer_revision": "a" * 40,
        },
        "dataset": {"ref": dataset_ref},
        "sft": {
            "batch_size": 1, "gradient_accumulation_steps": 1,
            "learning_rate": 0.0002, "max_steps": 1,
            "max_seq_length": 128, "seed": 1, "save_steps": 1,
            "save_total_limit": 1, "lora_rank": 8, "lora_alpha": 16,
            "lora_dropout": 0.0, "lora_target_modules": ["q_proj"],
            "use_dora": False, "use_rslora": False,
            "init_lora_weights": True, "split_dataset": False,
        },
        "artifacts": {
            "required_kinds": ["training_lineage", "final_model"],
            "retain_checkpoints": False,
        },
    }


def test_provider_state_round_trip_is_exact_and_secret_free() -> None:
    value = state()
    encoded = json.dumps(value.to_dict(), sort_keys=True)
    assert "HF_TOKEN" in encoded
    assert "token-value" not in encoded
    assert ModalProviderStateV1.from_mapping(value.to_dict()) == value
    changed = value.to_dict()
    changed["selection"]["image_id"] = "im-substituted"
    with pytest.raises(ValueError, match="profile differs"):
        ModalProviderStateV1.from_mapping(changed)


def test_training_input_is_closed_and_requires_complete_runtime_hyperparameters() -> None:
    value = training_input("project://data/train.jsonl")
    parsed, policy = StrictModalTrainingResolver._request(value)
    assert parsed["method"] == "sft"
    assert policy.required_kinds == ("training_lineage", "final_model")
    changed = dict(value, wrapper_specific_fix=True)
    with pytest.raises(ValueError, match="unknown"):
        StrictModalTrainingResolver._request(changed)
    incomplete = dict(value)
    incomplete["sft"] = dict(value["sft"])
    incomplete["sft"].pop("lora_rank")
    with pytest.raises(ValueError, match="missing required"):
        StrictModalTrainingResolver._request(incomplete)


def test_config_loader_accepts_only_the_host_training_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    config = project / "training" / "smoke.json"
    engine.mkdir(parents=True)
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps(training_input("project://data/train.jsonl")))
    context = ProjectContext.host(
        engine_root=engine, project_root=project, config_root=project / "training"
    )
    loaded = StrictModalTrainingResolver.load_document(
        context, "project://training/smoke.json"
    )
    assert loaded.to_dict()["method"] == "sft"
    outside = project / "outside.json"
    outside.write_text("{}")
    with pytest.raises(ValueError, match="config root"):
        StrictModalTrainingResolver.load_document(
            context, "project://outside.json"
        )


def test_intent_quote_binds_run_budget_currency_and_expiry() -> None:
    value = ModalTrainingIntentV1(
        "ehr", "run-1", "2026-08-26T12:00:00Z", "modal-evidence-v1",
        "2026-08-26T12:05:00Z", 100, "usd", "effect-run-1",
        "slot-run-1", "nonce-run-1",
    )
    assert value.currency == "USD"
    assert len(value.quote_digest) == 64
    changed = ModalTrainingIntentV1(
        "ehr", "run-1", "2026-08-26T12:00:00Z", "modal-evidence-v1",
        "2026-08-26T12:05:00Z", 101, "usd", "effect-run-1",
        "slot-run-1", "nonce-run-1",
    )
    assert changed.quote_digest != value.quote_digest


class FakeInspector:
    def __init__(self, source_lock):
        self.source_lock = source_lock

    def inspect(self, *, context):
        return self.source_lock


class FakeFinalizer:
    def finalize(self, source_lock, *, context, deployment, audience_ref):
        payload = {
            "schema_version": "synaptic-verified-modal-deployment/v1",
            "selection": deployment.to_dict(),
            "issuer_ref": "modal-verifier",
            "evidence_ref": "deployment-proof",
            "audience_ref": audience_ref,
            "challenge_nonce": "deployment-nonce",
            "verified_at": "2026-08-26T12:00:00Z",
            "expires_at": "2026-08-26T12:10:00Z",
            "key_ref": "modal-evidence-v1",
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        verified = VerifiedModalDeploymentIdentityV1(
            selection=deployment,
            issuer_ref=payload["issuer_ref"],
            evidence_ref=payload["evidence_ref"],
            audience_ref=audience_ref,
            challenge_nonce=payload["challenge_nonce"],
            verified_at=payload["verified_at"],
            expires_at=payload["expires_at"],
            key_ref=payload["key_ref"],
            tag_base64=base64.b64encode(b"tag").decode(),
            attestation_digest=hashlib.sha256(encoded).hexdigest(),
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
            **dict(deployment.runtime_environment),
            "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
            "PYTHONPATH": roots["engine"],
            "SYNAPTIC_ENGINE_ROOT": roots["engine"],
            "SYNAPTIC_PROJECT_ROOT": roots["project"],
            "SYNAPTIC_ARTIFACT_ROOT": roots["artifacts"],
            "SYNAPTIC_STATE_ROOT": roots["state"],
            "SYNAPTIC_TRACKING_ROOT": roots["tracking"],
            "SYNAPTIC_CACHE_ROOT": roots["cache"],
            "SYNAPTIC_TMP_ROOT": roots["tmp"],
            "HF_HOME": roots["cache"] + "/huggingface",
            "TRANSFORMERS_CACHE": roots["cache"] + "/transformers",
            "WANDB_DISABLED": "true",
        }
        source_evidence = AuthenticatedSourceEvidenceV1(
            project_url=source_lock.project_source.location.canonical_url,
            project_commit=source_lock.project_source.commit,
            engine_url=source_lock.engine_source.location.canonical_url,
            engine_commit=source_lock.engine_source.commit,
            engine_submodule_path=source_lock.engine_source.submodule_path,
            gitlink_commit=source_lock.engine_source.gitlink_commit,
            issuer_ref="git-verifier", evidence_ref="source-proof",
            audience_ref=audience_ref, challenge_nonce="source-nonce",
            verified_at="2026-08-26T12:00:00Z",
            expires_at="2026-08-26T12:10:00Z",
            key_ref="modal-evidence-v1", tag_base64="dGFn",
            attestation_digest="9" * 64,
        )
        source = ExecutionSourceV1(
            run_id=source_lock.run_id, created_at=source_lock.created_at,
            project_source=source_lock.project_source,
            engine_source=source_lock.engine_source,
            engine_submodule_path=source_lock.engine_source.submodule_path,
            source_evidence=source_evidence,
            deployment_member_sha256=hashlib.sha256(
                json.dumps(
                    verified.to_dict(), sort_keys=True, separators=(",", ":")
                ).encode()
            ).hexdigest(),
            roots=roots, python_implementation="cpython",
            python_version=deployment.python_version,
            python_executable=deployment.python_executable,
            python_executable_digest=deployment.python_executable_digest,
            environment=environment,
            secret_requirements_digest=deployment.secret_requirements_digest,
            provider_runtime_requirements_digest=deployment.provider_runtime_requirements_digest,
        )
        return ModalExecutionSourceResolutionV1(source, verified)


def test_resolver_binds_dataset_source_provider_budget_and_resources(tmp_path: Path) -> None:
    project = tmp_path / "project"
    engine = project / "synaptic-tuner"
    dataset = project / "data" / "train.jsonl"
    engine.mkdir(parents=True)
    dataset.parent.mkdir()
    dataset.write_text('{"text":"one"}\n', encoding="utf-8")
    context = ProjectContext.host(engine_root=engine, project_root=project)
    source_lock = SourceLock.from_dict({
        "schema_version": "synaptic-source-lock/v1",
        "run_id": "local-inspection", "created_at": "2026-08-26T11:59:00Z",
        "mode": "superproject",
        "sources": {
            "project": {"url": "https://github.com/example/project.git", "commit": "b" * 40, "branch": "main", "dirty": False, "pushed": False},
            "engine": {"url": "https://github.com/example/engine.git", "commit": "c" * 40, "branch": "main", "dirty": False, "pushed": False, "submodule_path": "synaptic-tuner", "gitlink_commit": "c" * 40},
        },
        "project": {}, "configuration": {}, "plugins": [], "inputs": [],
        "runtime": {}, "outputs": {},
    })
    intent = ModalTrainingIntentV1(
        "ehr", "run-1", "2026-08-26T12:00:00Z", "modal-evidence-v1",
        "2026-08-26T12:05:00Z", 100, "USD", "effect-run-1",
        "slot-run-1", "nonce-run-1",
    )
    resolver = StrictModalTrainingResolver(
        state=state(), intent=intent, finalizer=FakeFinalizer(),
        source_inspector=FakeInspector(source_lock),
    )
    request = TrainingRequest(CanonicalDocument.from_mapping(
        training_input("project://data/train.jsonl")
    ))
    resolved = resolver.resolve(request, context=context)
    config = resolved.resolved_config.to_dict()
    assert config["dataset"]["revision"] == "b" * 40
    assert config["dataset"]["content_digest"] == hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert resolved.execution_source.run_id == "run-1"
    assert resolved.resources.accelerator == "A10"
    assert resolved.execution_context.to_dict()["authority"]["quote_digest"] == intent.quote_digest
