"""Strict host config and request resolution for the Modal v1 engine path."""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol

from synaptic_tuner.api.v1 import (
    ArtifactPolicy,
    CanonicalDocument,
    GitCliLocalSourceInspector,
    PathRef,
    ProjectContext,
    ResolvedTrainingComponents,
    ResourceSpec,
    RuntimeSpec,
    TrainingRequest,
    TrainingResolutionError,
)
from synaptic_tuner.api.v1.modal import (
    ModalClientBinding,
    ModalDeploymentSelectionV1,
    ModalExecutionSourceResolutionV1,
    ModalPlanContextV1,
    ModalProviderProfileV1,
    ModalRuntimeLockV1,
)

_SFT_KEYS = {
    "batch_size", "gradient_accumulation_steps", "learning_rate",
    "max_steps", "num_epochs", "max_seq_length", "seed", "save_steps",
    "save_total_limit", "lora_rank", "lora_alpha", "lora_dropout",
    "lora_target_modules", "use_dora", "use_rslora", "init_lora_weights",
    "split_dataset",
}
_REQUIRED_SFT_KEYS = _SFT_KEYS - {"max_steps", "num_epochs"}


def _closed(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ValueError(f"{label} contains missing or unknown fields")
    return dict(value)


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be canonical nonblank text")
    return value


def _canonical(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _read_json(path: Path, *, maximum_bytes: int = 1024 * 1024) -> dict[str, object]:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise ValueError("configuration must be a regular file")
    if not 0 < metadata.st_size <= maximum_bytes:
        raise ValueError("configuration exceeds its size bound")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("configuration must contain valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("configuration must contain a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class ModalProviderStateV1:
    """Host-owned exact provider lock; contains identities but no secret values."""

    profile: ModalProviderProfileV1
    binding: ModalClientBinding
    selection: ModalDeploymentSelectionV1
    control_volume_id: str
    artifact_volume_id: str

    def __post_init__(self) -> None:
        if type(self.profile) is not ModalProviderProfileV1:
            raise TypeError("profile must be ModalProviderProfileV1")
        if type(self.binding) is not ModalClientBinding:
            raise TypeError("binding must be ModalClientBinding")
        if type(self.selection) is not ModalDeploymentSelectionV1:
            raise TypeError("selection must be ModalDeploymentSelectionV1")
        for name in ("control_volume_id", "artifact_volume_id"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.control_volume_id == self.artifact_volume_id:
            raise ValueError("control and artifact volume identities must differ")
        selected_binding = ModalClientBinding(
            self.selection.account_ref, self.selection.workspace_ref,
            self.selection.environment_ref, self.selection.client_ref,
            self.selection.sdk_version,
        )
        if selected_binding != self.binding:
            raise ValueError("provider binding differs from deployment selection")
        if (
            self.selection.app_name != self.profile.app_name
            or self.selection.function_name != self.profile.function_name
            or self.selection.deployment_ref != self.profile.deployment_ref
        ):
            raise ValueError("provider profile differs from deployment selection")
        runtime = ModalRuntimeLockV1.packaged()
        runtime.validate_selection(self.selection)
        if (
            self.selection.secret_requirements_digest
            != self.profile.secret_requirements_digest
            or self.selection.provider_runtime_requirements_digest
            != self.profile.provider_runtime_requirements_digest(
                runtime,
                runtime_environment=self.selection.runtime_environment,
                accelerator=self.selection.accelerator,
                timeout_seconds=self.selection.timeout_seconds,
                max_retries=self.selection.max_retries,
            )
        ):
            raise ValueError("provider requirements differ from deployment selection")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ModalProviderStateV1":
        root = _closed(
            value,
            {"schema_version", "profile", "binding", "selection", "volumes"},
            "Modal provider state",
        )
        if root["schema_version"] != "synaptic-modal-provider-state/v1":
            raise ValueError("unsupported Modal provider state schema")
        binding = _closed(
            root["binding"],
            {"account_ref", "workspace_ref", "environment_ref", "client_ref", "sdk_version"},
            "Modal binding",
        )
        volumes = _closed(
            root["volumes"], {"control_volume_id", "artifact_volume_id"},
            "Modal volumes",
        )
        return cls(
            ModalProviderProfileV1.from_mapping(root["profile"]),
            ModalClientBinding(**binding),
            ModalDeploymentSelectionV1.from_dict(root["selection"]),
            **volumes,
        )

    @classmethod
    def load(cls, context: ProjectContext) -> "ModalProviderStateV1":
        if not isinstance(context, ProjectContext) or context.mode != "host":
            raise ValueError("host project context is required")
        return cls.from_mapping(
            _read_json(context.state_root / "modal" / "provider-state.json")
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "synaptic-modal-provider-state/v1",
            "profile": {
                "schema_version": "synaptic-modal-provider/v1",
                "profile": self.profile.profile,
                "deployment": {
                    "app_name": self.profile.app_name,
                    "function_name": self.profile.function_name,
                    "deployment_ref": self.profile.deployment_ref,
                },
                "runtime_lock": self.profile.runtime_lock_ref,
                "volumes": {
                    "control_ref": self.profile.control_volume_ref,
                    "artifact_ref": self.profile.artifact_volume_ref,
                },
                "secrets": [
                    {
                        "provider": "modal", "name": item.name,
                        "required_keys": list(item.required_keys),
                    }
                    for item in self.profile.secrets
                ],
            },
            "binding": {
                name: getattr(self.binding, name)
                for name in (
                    "account_ref", "workspace_ref", "environment_ref",
                    "client_ref", "sdk_version",
                )
            },
            "selection": self.selection.to_dict(),
            "volumes": {
                "control_volume_id": self.control_volume_id,
                "artifact_volume_id": self.artifact_volume_id,
            },
        }


@dataclass(frozen=True, slots=True)
class ModalTrainingIntentV1:
    project_ref: str
    run_id: str
    created_at: str
    key_ref: str
    quote_expires_at: str
    maximum_cost_minor_units: int
    currency: str
    effect_id: str
    artifact_slot_ref: str
    invocation_nonce: str
    generation: int = 1

    def __post_init__(self) -> None:
        for name in (
            "project_ref", "run_id", "created_at", "key_ref", "quote_expires_at",
            "currency", "effect_id", "artifact_slot_ref", "invocation_nonce",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if type(self.maximum_cost_minor_units) is not int or self.maximum_cost_minor_units < 0:
            raise ValueError("maximum cost must be a non-negative integer")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("currency must be a three-letter code")
        object.__setattr__(self, "currency", self.currency.upper())
        if type(self.generation) is not int or self.generation < 1:
            raise ValueError("generation must be a positive integer")

    @property
    def quote_digest(self) -> str:
        return hashlib.sha256(
            _canonical(
                {
                    "schema_version": "synaptic-host-cost-authorization/v1",
                    "project_ref": self.project_ref,
                    "run_id": self.run_id,
                    "expires_at": self.quote_expires_at,
                    "maximum_cost_minor_units": self.maximum_cost_minor_units,
                    "currency": self.currency,
                }
            )
        ).hexdigest()


class SourceFinalizer(Protocol):
    def finalize(self, source_lock, *, context, deployment, audience_ref): ...


class StrictModalTrainingResolver:
    """Resolve one strict project-local SFT input into immutable engine inputs."""

    def __init__(
        self,
        *,
        state: ModalProviderStateV1,
        intent: ModalTrainingIntentV1,
        finalizer: SourceFinalizer,
        source_inspector=None,
    ) -> None:
        self.state = state
        self.intent = intent
        self.finalizer = finalizer
        self.source_inspector = source_inspector or GitCliLocalSourceInspector()

    @staticmethod
    def load_document(context: ProjectContext, path_ref: str) -> CanonicalDocument:
        path = PathRef.parse(path_ref).resolve(
            context, from_cli=True, access="read", cloud=True, external_paths="deny"
        )
        if not path.resolve().is_relative_to(context.config_root.resolve()):
            raise ValueError("training configuration must live below the host config root")
        return CanonicalDocument.from_mapping(_read_json(path))

    @staticmethod
    def _request(value: Mapping[str, object]) -> tuple[dict[str, object], ArtifactPolicy]:
        root = _closed(
            value,
            {"schema_version", "method", "provider_profile", "model", "dataset", "sft", "artifacts"},
            "training input",
        )
        if root["schema_version"] != "synaptic-training-input/v1" or root["method"] != "sft":
            raise ValueError("unsupported training input schema or method")
        _text(root["provider_profile"], "provider_profile")
        model = _closed(root["model"], {"ref", "revision", "tokenizer_revision"}, "model")
        for name, value in model.items():
            _text(value, f"model.{name}")
        dataset = _closed(root["dataset"], {"ref"}, "dataset")
        dataset_ref = _text(dataset["ref"], "dataset.ref")
        if not dataset_ref.startswith("project://"):
            raise ValueError("Modal v1 requires a project:// dataset")
        sft = dict(root["sft"]) if isinstance(root["sft"], Mapping) else {}
        if not _REQUIRED_SFT_KEYS.issubset(sft) or not set(sft).issubset(_SFT_KEYS):
            raise ValueError("SFT hyperparameters are missing required keys or contain unknown keys")
        if ("max_steps" in sft) == ("num_epochs" in sft):
            raise ValueError("SFT requires exactly one of max_steps or num_epochs")
        if not isinstance(sft["lora_target_modules"], list) or not sft["lora_target_modules"]:
            raise ValueError("lora_target_modules must be a nonempty list")
        artifacts = _closed(root["artifacts"], {"required_kinds", "retain_checkpoints"}, "artifacts")
        if not isinstance(artifacts["required_kinds"], list):
            raise ValueError("artifact required_kinds must be a list")
        policy = ArtifactPolicy(
            tuple(artifacts["required_kinds"]), artifacts["retain_checkpoints"]
        )
        return root, policy

    def resolve(self, request: TrainingRequest, *, context: ProjectContext) -> ResolvedTrainingComponents:
        if not isinstance(request, TrainingRequest) or context.mode != "host":
            raise TypeError("canonical training request and host context are required")
        raw, artifact_policy = self._request(request.document.to_dict())
        if raw["provider_profile"] != self.state.profile.profile:
            raise TrainingResolutionError("training input selected a different provider profile")
        dataset_ref = raw["dataset"]["ref"]
        dataset_path = PathRef.parse(dataset_ref).resolve(
            context, access="read", cloud=True, external_paths="deny"
        )
        if not dataset_path.is_file() or dataset_path.is_symlink():
            raise TrainingResolutionError("dataset must be a regular project file")
        inspected = self.source_inspector.inspect(context=context)
        locked = replace(
            inspected,
            run_id=self.intent.run_id,
            created_at=self.intent.created_at,
            project={"id": self.intent.project_ref},
            configuration={"request_sha256": hashlib.sha256(request.document.canonical_json.encode()).hexdigest()},
        )
        audience = f"{self.intent.project_ref}/{self.intent.run_id}"
        finalized: ModalExecutionSourceResolutionV1 = self.finalizer.finalize(
            locked, context=context, deployment=self.state.selection,
            audience_ref=audience,
        )
        project_revision = finalized.execution_source.project_source.commit.lower()
        resolved_config = CanonicalDocument.from_mapping(
            {
                "schema_version": "synaptic-sft-config/v1",
                "method": "sft",
                "model": raw["model"],
                "dataset": {
                    "ref": dataset_ref,
                    "revision": project_revision,
                    "content_digest": _sha256_file(dataset_path),
                },
                "sft": raw["sft"],
            }
        )
        resources = ResourceSpec(
            self.state.selection.accelerator, 1,
            self.state.selection.timeout_seconds,
        )
        execution_context = ModalPlanContextV1(
            project_ref=self.intent.project_ref,
            profile=self.state.profile.profile,
            deployment=finalized.deployment,
            binding=self.state.binding,
            control_volume_id=self.state.control_volume_id,
            artifact_volume_id=self.state.artifact_volume_id,
            key_ref=self.intent.key_ref,
            quote_digest=self.intent.quote_digest,
            quote_expires_at=self.intent.quote_expires_at,
            maximum_cost_minor_units=self.intent.maximum_cost_minor_units,
            currency=self.intent.currency,
            effect_id=self.intent.effect_id,
            effect_key=self.intent.run_id,
            artifact_slot_ref=self.intent.artifact_slot_ref,
            invocation_nonce=self.intent.invocation_nonce,
            generation=self.intent.generation,
            resource_digest=ModalPlanContextV1.digest_resources(resources),
        )
        runtime = ModalRuntimeLockV1.packaged()
        return ResolvedTrainingComponents(
            execution_source=finalized.execution_source,
            execution_context=CanonicalDocument.from_mapping(execution_context.to_dict()),
            resolved_config=resolved_config,
            runtime=RuntimeSpec(
                runtime.registry_reference,
                runtime.locked_digest("dependency_lock"),
                runtime.python_version,
            ),
            resources=resources,
            artifact_policy=artifact_policy,
        )
