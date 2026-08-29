"""Strict host config and request resolution for the Modal v1 engine path."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol

from synaptic_tuner.api.v1 import (
    ArtifactPolicy,
    AuthenticatedSourceEvidenceV1,
    CanonicalDocument,
    ExecutionSourceV1,
    GitCliLocalSourceInspector,
    PathRef,
    ProjectContext,
    ResolvedTrainingComponents,
    ResourceSpec,
    RuntimeSpec,
    SourceLock,
    TrainingInputV1,
    TrainingMethodV1,
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
    VerifiedModalDeploymentIdentityV1,
)

_PROVENANCE_KEYS = (
    "training_input_digest",
    "training_contract_identity_digest",
    "training_source_sha256",
    "training_ingress_digest",
    "provider_policy_digest",
)


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


def _digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True, slots=True)
class _DatasetSnapshotV1:
    identity: tuple[int, int, int, int, int, int, int, int]
    digest: str


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int, int]:
    return (
        metadata.st_dev, metadata.st_ino, metadata.st_mode,
        getattr(metadata, "st_uid", 0), getattr(metadata, "st_gid", 0),
        metadata.st_nlink, metadata.st_size, metadata.st_mtime_ns,
    )


def _is_reparse(metadata: os.stat_result) -> bool:
    return bool(
        getattr(metadata, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _closed_resolution_failure() -> None:
    raise TrainingResolutionError("Modal training resolution failed") from None


def _require_no_reparse_components(path: Path) -> None:
    selected = path.absolute()
    current = Path(selected.anchor)
    for component in selected.parts[1:]:
        current = current / component
        metadata = current.lstat()
        if current.is_symlink() or _is_reparse(metadata):
            raise OSError


def _dataset_snapshot(path: Path) -> _DatasetSnapshotV1:
    """Hash the exact opened file and prove its stable path/descriptor identity."""

    descriptor: int | None = None
    result: _DatasetSnapshotV1 | None = None
    failed = False
    try:
        _require_no_reparse_components(path)
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or _is_reparse(before):
            raise OSError
        flags = os.O_RDONLY
        flags |= getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOINHERIT", 0)
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        baseline = _file_identity(before)
        if (
            not stat.S_ISREG(opened.st_mode)
            or _is_reparse(opened)
            or _file_identity(opened) != baseline
        ):
            raise OSError
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        after_descriptor = os.fstat(descriptor)
        _require_no_reparse_components(path)
        after_path = path.lstat()
        if (
            _file_identity(after_descriptor) != baseline
            or _file_identity(after_path) != baseline
            or _is_reparse(after_path)
        ):
            raise OSError
        result = _DatasetSnapshotV1(baseline, digest.hexdigest())
    except Exception:
        failed = True
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except Exception:
                failed = True
    if failed or result is None:
        _closed_resolution_failure()
    return result


def _resolve_dataset(context: ProjectContext, reference: str) -> Path:
    if type(reference) is not str or not reference.startswith("project://"):
        raise TrainingResolutionError("Modal v1 requires a project:// dataset")
    relative = reference[len("project://"):]
    if not relative:
        raise TrainingResolutionError("dataset reference is empty")
    components = relative.split("/")
    lexical = context.project_root.joinpath(*components)
    resolved: Path | None = None
    failed = False
    try:
        _require_no_reparse_components(lexical)
        resolved = PathRef.parse(reference).resolve(
            context, access="read", cloud=True, external_paths="deny"
        )
        if (
            resolved != lexical.resolve(strict=False)
            or not resolved.is_relative_to(context.project_root.resolve(strict=False))
        ):
            raise TrainingResolutionError("dataset must remain beneath the project root")
    except Exception:
        failed = True
    if failed or resolved is None:
        _closed_resolution_failure()
    return resolved


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


@dataclass(frozen=True, slots=True)
class _ResolverBaselineV1:
    training_input: TrainingInputV1
    input_document: str
    input_digest: str
    contract_identity_digest: str
    source_sha256: str
    ingress_digest: str
    provider_authority: object
    config: object
    state: ModalProviderStateV1
    journal: object
    policy: object
    policy_digest: str
    authority_document: bytes
    selection_identity: ModalDeploymentSelectionV1
    selection: ModalDeploymentSelectionV1
    selection_document: bytes
    intent: ModalTrainingIntentV1
    intent_values: tuple[object, ...]
    inspector: object
    finalizer: object


class ModalTrainingResolverV1:
    """Compile one authenticated provider-neutral training input for Modal."""

    __slots__ = (
        "training_input", "input_type", "input_digest", "contract_identity_digest",
        "ingress_digest", "source_sha256", "provider_authority", "intent",
        "finalizer", "source_inspector", "_baseline",
    )

    def __init__(
        self,
        *,
        training_input: TrainingInputV1,
        input_type: type[TrainingInputV1],
        input_digest: str,
        contract_identity_digest: str,
        ingress_digest: str,
        source_sha256: str,
        provider_authority,
        intent: ModalTrainingIntentV1,
        finalizer: SourceFinalizer,
        source_inspector=None,
    ) -> None:
        from .modal_provider import ModalProviderAuthorityV1

        if input_type is not TrainingInputV1 or type(training_input) is not TrainingInputV1:
            raise TypeError("exact released TrainingInputV1 contract is required")
        if type(provider_authority) is not ModalProviderAuthorityV1:
            raise TypeError("exact ModalProviderAuthorityV1 is required")
        if type(intent) is not ModalTrainingIntentV1:
            raise TypeError("exact ModalTrainingIntentV1 is required")
        canonical = training_input.canonical_json()
        if training_input.input_digest() != _digest(input_digest, "training_input_digest"):
            raise ValueError("training input digest differs from its canonical value")
        self.training_input = training_input
        self.input_type = input_type
        self.input_digest = input_digest
        self.contract_identity_digest = _digest(
            contract_identity_digest, "training_contract_identity_digest"
        )
        self.ingress_digest = _digest(ingress_digest, "training_ingress_digest")
        self.source_sha256 = _digest(source_sha256, "training_source_sha256")
        self.provider_authority = provider_authority
        self.intent = intent
        self.finalizer = finalizer
        self.source_inspector = source_inspector or GitCliLocalSourceInspector()
        authority_document = _canonical({
            "config": provider_authority.config.to_dict(),
            "state": provider_authority.state.to_dict(),
            "journal": provider_authority.journal.to_dict(),
        })
        selection = ModalDeploymentSelectionV1.from_dict(
            provider_authority.state.selection.to_dict()
        )
        self._baseline = _ResolverBaselineV1(
            training_input=training_input,
            input_document=canonical,
            input_digest=input_digest,
            contract_identity_digest=self.contract_identity_digest,
            source_sha256=self.source_sha256,
            ingress_digest=self.ingress_digest,
            provider_authority=provider_authority,
            config=provider_authority.config,
            state=provider_authority.state,
            journal=provider_authority.journal,
            policy=provider_authority.training,
            policy_digest=provider_authority.training.digest,
            authority_document=authority_document,
            selection_identity=provider_authority.state.selection,
            selection=selection,
            selection_document=_canonical(selection.to_dict()),
            intent=intent,
            intent_values=tuple(
            getattr(intent, name)
            for name in (
                "project_ref", "run_id", "created_at", "key_ref", "quote_expires_at",
                "maximum_cost_minor_units", "currency", "effect_id", "artifact_slot_ref",
                "invocation_nonce", "generation",
            )
            ),
            inspector=self.source_inspector,
            finalizer=finalizer,
        )

    def _check_baselines(self) -> None:
        from .modal_provider import ModalProviderAuthorityV1

        valid = False
        try:
            baseline = self._baseline
            valid = (
                type(baseline) is _ResolverBaselineV1
                and self.input_type is TrainingInputV1
                and type(self.training_input) is TrainingInputV1
                and self.training_input is baseline.training_input
                and self.training_input.canonical_json() == baseline.input_document
                and self.training_input.input_digest() == baseline.input_digest
                and type(self.input_digest) is str
                and self.input_digest == baseline.input_digest
                and type(self.contract_identity_digest) is str
                and self.contract_identity_digest == baseline.contract_identity_digest
                and type(self.source_sha256) is str
                and self.source_sha256 == baseline.source_sha256
                and type(self.ingress_digest) is str
                and self.ingress_digest == baseline.ingress_digest
                and type(self.provider_authority) is ModalProviderAuthorityV1
                and self.provider_authority is baseline.provider_authority
                and self.provider_authority.config is baseline.config
                and self.provider_authority.state is baseline.state
                and self.provider_authority.journal is baseline.journal
                and self.provider_authority.training is baseline.policy
                and self.provider_authority.training.digest == baseline.policy_digest
                and _canonical({
                    "config": self.provider_authority.config.to_dict(),
                    "state": self.provider_authority.state.to_dict(),
                    "journal": self.provider_authority.journal.to_dict(),
                }) == baseline.authority_document
                and self.provider_authority.state.selection is baseline.selection_identity
                and _canonical(
                    self.provider_authority.state.selection.to_dict()
                ) == baseline.selection_document
                and self.intent is baseline.intent
                and tuple(
                    getattr(self.intent, name)
                    for name in (
                        "project_ref", "run_id", "created_at", "key_ref",
                        "quote_expires_at", "maximum_cost_minor_units", "currency",
                        "effect_id", "artifact_slot_ref", "invocation_nonce", "generation",
                    )
                ) == baseline.intent_values
                and self.source_inspector is baseline.inspector
                and self.finalizer is baseline.finalizer
            )
        except Exception:
            valid = False
        if not valid:
            raise TrainingResolutionError("resolver authority changed during resolution")

    @staticmethod
    def _clone_lock(source_lock: SourceLock) -> SourceLock:
        clone: SourceLock | None = None
        try:
            document = json.loads(source_lock.canonical_bytes.decode("utf-8"))
            if type(document) is dict:
                clone = SourceLock.from_dict(document)
        except Exception:
            clone = None
        if clone is None:
            _closed_resolution_failure()
        return clone

    @staticmethod
    def _require_lock_baseline(
        source_lock: SourceLock, canonical_bytes: bytes, binding: object,
    ) -> None:
        valid = False
        try:
            valid = (
                type(source_lock) is SourceLock
                and source_lock.canonical_bytes == canonical_bytes
                and source_lock.binding == binding
            )
        except Exception:
            valid = False
        if not valid:
            raise TrainingResolutionError("source finalizer changed the training provenance")

    @staticmethod
    def _canonical_resolution(
        value: object,
        *,
        source_lock: SourceLock,
        selection_document: bytes,
    ) -> ModalExecutionSourceResolutionV1:
        result: ModalExecutionSourceResolutionV1 | None = None
        try:
            if type(value) is not ModalExecutionSourceResolutionV1:
                raise TypeError
            if (
                type(value.execution_source) is not ExecutionSourceV1
                or type(value.deployment) is not VerifiedModalDeploymentIdentityV1
                or type(value.deployment.selection) is not ModalDeploymentSelectionV1
            ):
                raise TypeError
            deployment = VerifiedModalDeploymentIdentityV1.from_dict(
                value.deployment.to_dict()
            )
            execution = ExecutionSourceV1.from_dict(value.execution_source.to_dict())
            if _canonical(deployment.selection.to_dict()) != selection_document:
                raise ValueError
            evidence = execution.source_evidence
            if (
                type(evidence) is not AuthenticatedSourceEvidenceV1
                or evidence.source_lock_binding != source_lock.binding
                or not evidence.binds(source_lock)
                or execution.project_source.location.canonical_url
                != source_lock.project_source.location.canonical_url
                or execution.project_source.commit.lower()
                != source_lock.project_source.commit.lower()
                or execution.engine_source.location.canonical_url
                != source_lock.engine_source.location.canonical_url
                or execution.engine_source.commit.lower()
                != source_lock.engine_source.commit.lower()
                or execution.engine_source.gitlink_commit
                != source_lock.engine_source.gitlink_commit
                or execution.engine_submodule_path
                != source_lock.engine_source.submodule_path
            ):
                raise ValueError
            result = ModalExecutionSourceResolutionV1(execution, deployment)
        except Exception:
            result = None
        if result is None:
            raise TrainingResolutionError(
                "source finalizer returned an unauthenticated resolution"
            ) from None
        return result

    def resolve(self, request: TrainingRequest, *, context: ProjectContext) -> ResolvedTrainingComponents:
        if type(request) is not TrainingRequest or type(context) is not ProjectContext or context.mode != "host":
            raise TypeError("canonical training request and host context are required")
        self._check_baselines()
        baseline = self._baseline
        expected_request = CanonicalDocument.from_mapping(baseline.training_input.to_dict())
        if (
            type(request.document) is not CanonicalDocument
            or request.document.canonical_json != expected_request.canonical_json
        ):
            raise TrainingResolutionError("request differs from the authenticated training input")
        if baseline.training_input.method is not TrainingMethodV1.SFT:
            raise TrainingResolutionError("Modal v1 supports only SFT")
        dataset_ref = baseline.training_input.dataset.ref
        self._check_baselines()
        dataset_path = _resolve_dataset(context, dataset_ref)
        dataset_baseline = _dataset_snapshot(dataset_path)
        self._check_baselines()
        inspected = None
        inspector_failed = False
        try:
            inspected = baseline.inspector.inspect(context=context)
        except Exception:
            inspector_failed = True
        if inspector_failed:
            _closed_resolution_failure()
        self._check_baselines()
        if type(inspected) is not SourceLock:
            raise TrainingResolutionError("source inspector returned an invalid source lock")
        if _dataset_snapshot(dataset_path) != dataset_baseline:
            raise TrainingResolutionError("dataset changed during source inspection")
        self._check_baselines()
        configuration = {
            "training_input_digest": baseline.input_digest,
            "training_contract_identity_digest": baseline.contract_identity_digest,
            "training_source_sha256": baseline.source_sha256,
            "training_ingress_digest": baseline.ingress_digest,
            "provider_policy_digest": baseline.policy_digest,
        }
        if tuple(configuration) != _PROVENANCE_KEYS:
            raise TrainingResolutionError("training provenance configuration is malformed")
        locked = replace(
            inspected,
            run_id=baseline.intent.run_id,
            created_at=baseline.intent.created_at,
            project={"id": baseline.intent.project_ref},
            configuration=configuration,
        )
        sealed_lock = self._clone_lock(locked)
        sealed_lock_bytes = sealed_lock.canonical_bytes
        sealed_binding = sealed_lock.binding
        presented_lock = self._clone_lock(sealed_lock)
        presented_selection = ModalDeploymentSelectionV1.from_dict(
            baseline.selection.to_dict()
        )
        audience = f"{baseline.intent.project_ref}/{baseline.intent.run_id}"
        self._check_baselines()
        finalized = None
        finalizer_failed = False
        try:
            finalized = baseline.finalizer.finalize(
                presented_lock, context=context, deployment=presented_selection,
                audience_ref=audience,
            )
        except Exception:
            finalizer_failed = True
        if finalizer_failed:
            _closed_resolution_failure()
        self._check_baselines()
        self._require_lock_baseline(presented_lock, sealed_lock_bytes, sealed_binding)
        selection_unchanged = False
        try:
            selection_unchanged = (
                _canonical(presented_selection.to_dict())
                == baseline.selection_document
            )
        except Exception:
            selection_unchanged = False
        if not selection_unchanged:
            raise TrainingResolutionError("source finalizer changed the deployment selection")
        if _dataset_snapshot(dataset_path) != dataset_baseline:
            raise TrainingResolutionError("dataset changed during source finalization")
        self._check_baselines()
        finalized = self._canonical_resolution(
            finalized, source_lock=sealed_lock,
            selection_document=baseline.selection_document,
        )
        project_revision = finalized.execution_source.project_source.commit.lower()
        hyperparameters = baseline.training_input.hyperparameters.to_dict()
        hyperparameters.pop("schema_version")
        duration = hyperparameters.pop("duration")
        if (duration["max_steps"] is None) == (duration["num_epochs"] is None):
            raise TrainingResolutionError("SFT duration must contain exactly one limit")
        hyperparameters[
            "max_steps" if duration["max_steps"] is not None else "num_epochs"
        ] = duration["max_steps"] if duration["max_steps"] is not None else duration["num_epochs"]
        resolved_config = CanonicalDocument.from_mapping(
            {
                "schema_version": "synaptic-sft-config/v1",
                "method": "sft",
                "model": {
                    **baseline.training_input.model.to_dict(),
                    "load_in_4bit": baseline.policy.load_in_4bit,
                },
                "dataset": {
                    "ref": dataset_ref,
                    "revision": project_revision,
                    "content_digest": dataset_baseline.digest,
                },
                "sft": hyperparameters,
            }
        )
        resources = ResourceSpec(
            baseline.selection.accelerator, 1, baseline.selection.timeout_seconds,
        )
        execution_context = ModalPlanContextV1(
            project_ref=baseline.intent.project_ref,
            profile=baseline.state.profile.profile,
            deployment=finalized.deployment,
            binding=baseline.state.binding,
            control_volume_id=baseline.state.control_volume_id,
            artifact_volume_id=baseline.state.artifact_volume_id,
            key_ref=baseline.intent.key_ref,
            quote_digest=baseline.intent.quote_digest,
            quote_expires_at=baseline.intent.quote_expires_at,
            maximum_cost_minor_units=baseline.intent.maximum_cost_minor_units,
            currency=baseline.intent.currency,
            effect_id=baseline.intent.effect_id,
            effect_key=baseline.intent.run_id,
            artifact_slot_ref=baseline.intent.artifact_slot_ref,
            invocation_nonce=baseline.intent.invocation_nonce,
            generation=baseline.intent.generation,
            resource_digest=ModalPlanContextV1.digest_resources(resources),
        )
        runtime = ModalRuntimeLockV1.packaged()
        result = ResolvedTrainingComponents(
            execution_source=finalized.execution_source,
            execution_context=CanonicalDocument.from_mapping(execution_context.to_dict()),
            resolved_config=resolved_config,
            runtime=RuntimeSpec(
                runtime.registry_reference,
                runtime.locked_digest("dependency_lock"),
                runtime.python_version,
            ),
            resources=resources,
            artifact_policy=ArtifactPolicy(
                baseline.training_input.artifacts.required_kinds,
                baseline.training_input.artifacts.retain_checkpoints,
            ),
        )
        if _dataset_snapshot(dataset_path) != dataset_baseline:
            raise TrainingResolutionError("dataset changed before resolution return")
        self._check_baselines()
        return result
