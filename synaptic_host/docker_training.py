"""Host-owned, effect-free Docker training admission."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import sqlite3
import subprocess
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from synaptic_tuner.api.v1 import (
    ArtifactPolicy,
    AuthenticatedSourceEvidenceV1,
    CanonicalDocument,
    ExecutionSourceV1,
    GitCliLocalSourceInspector,
    ProjectContext,
    ResolvedTrainingComponents,
    ResourceSpec,
    RuntimeSpec,
    SourceLock,
    TrainingInputV1,
    TrainingPlan,
    TrainingRequest,
    compile_training_plan_v1,
    validate_source_lock_provenance_v1,
)
from synaptic_tuner.api.v1.sources import GitSource
from tuner.project.manifest import load_project_manifest

from .artifact_destinations import (
    ArtifactDestinationDeclarationV1,
    parse_artifact_destination_config_v1,
    artifact_destination_declaration_digest_v1,
)
from .docker_provider import DockerProviderProfileV1
from .security import ScopedGitRemoteReader


_ARTIFACT_ROLES = (
    "final_model", "tokenizer", "training_lineage", "training_metrics",
    "workload_record",
)


_EXECUTION_CONTEXT_SCHEMA = "synaptic-docker-admission-context/v1"
_PROVENANCE_KEYS = (
    "training_input_digest",
    "training_contract_identity_digest",
    "training_source_sha256",
    "training_ingress_digest",
    "provider_policy_digest",
)
_DESCRIPTOR_FIELDS = (
    "kind", "ref", "path", "git_object_id", "size_bytes", "sha256",
)
_BRANCH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")
_EVIDENCE_PURPOSE = b"source-lock-evidence/v1\0"


def _sha(domain: bytes, value: bytes) -> str:
    return hashlib.sha256(domain + b"\0" + value).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _project_path(reference: str) -> str:
    prefix = "project://"
    if type(reference) is not str or not reference.startswith(prefix):
        raise ValueError("Docker admission requires a project reference")
    value = reference[len(prefix):]
    if (
        not value or value.startswith(("/", "\\")) or "\\" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ValueError("project reference is invalid")
    return value


def _descriptor(kind: str, reference: str, blob) -> dict[str, object]:
    result = {
        "kind": kind,
        "ref": reference,
        "path": blob.path,
        "git_object_id": blob.git_object_id,
        "size_bytes": blob.size_bytes,
        "sha256": blob.sha256,
    }
    if tuple(result) != _DESCRIPTOR_FIELDS:
        raise ValueError("committed descriptor is malformed")
    return result


@dataclass(frozen=True, slots=True)
class _SourceProofV1:
    project_source: GitSource
    engine_source: GitSource
    verified_at: str


def _commit_time(repository: Path, commit: str) -> str:
    try:
        raw = subprocess.run(
            ("git", "-C", str(repository), "show", "-s", "--format=%cI", commit),
            check=True, capture_output=True, timeout=30,
        ).stdout.decode("ascii").strip()
        value = datetime.fromisoformat(raw).astimezone(timezone.utc)
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
        raise ValueError("project commit timestamp is unavailable") from None
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _docker_durable_rows_exist(context: ProjectContext) -> bool:
    database = context.state_root / "training.sqlite3"
    if not database.exists():
        return False
    connection = None
    try:
        connection = sqlite3.connect(
            f"file:{database.as_posix()}?mode=ro", uri=True, timeout=5,
        )
        tables = frozenset(
            row[0] for row in connection.execute(
                """SELECT name FROM sqlite_master
                   WHERE type = 'table' AND name IN (
                       'provider_preparations', 'docker_run_mutations'
                   )"""
            )
        )
        expected = frozenset({"provider_preparations", "docker_run_mutations"})
        if not tables:
            return False
        if tables != expected:
            raise ValueError
        return connection.execute(
            """SELECT EXISTS(
                   SELECT 1 FROM provider_preparations
                   UNION ALL SELECT 1 FROM docker_run_mutations
               )"""
        ).fetchone()[0] == 1
    except (OSError, sqlite3.Error, TypeError, ValueError):
        raise ValueError("Docker durability state is unavailable") from None
    finally:
        if connection is not None:
            connection.close()


@dataclass(frozen=True, slots=True)
class _AdmissionSnapshotV1:
    training_input: TrainingInputV1
    input_digest: str
    contract_identity_digest: str
    ingress_digest: str
    project_root: Path
    engine_root: Path
    config_ref: str
    config_blob: object
    profile: DockerProviderProfileV1
    profile_blob: object
    destination: ArtifactDestinationDeclarationV1
    destination_blob: object
    dataset_ref: str
    dataset_blob: object
    manifest_blob: object
    storage_blob: object


@dataclass(frozen=True, slots=True)
class _VerifiedAdmissionV1:
    snapshot: _AdmissionSnapshotV1
    source_lock: SourceLock
    source_evidence: AuthenticatedSourceEvidenceV1


class _AdmissionSessionV1:
    """Live one-use proof and evidence session for one admission call."""

    __slots__ = (
        "_reader", "_clock", "_key", "_proof", "_verified", "_consumed",
        "_post_verified", "_closed", "_payload", "_tag", "_provenance",
    )

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("Docker admission session is factory-issued")

    def _verified_remote_source(self, source) -> GitSource:
        branch = source.branch
        if type(branch) is not str or _BRANCH.fullmatch(branch) is None:
            raise ValueError("source lacks an exact upstream branch")
        ref = "refs/heads/" + branch
        raw = self._reader.read_ref(
            canonical_url=source.location.canonical_url, exact_ref=ref,
        )
        expected = f"{source.commit.lower()}\t{ref}\n".encode("ascii")
        if type(raw) is not bytes or raw != expected:
            raise ValueError("remote ref does not equal the locked commit")
        return GitSource(
            location=source.location, commit=source.commit, branch=source.branch,
            dirty=source.dirty, pushed=True,
            submodule_path=source.submodule_path,
            gitlink_commit=source.gitlink_commit,
        )

    def prove(self, *, context: ProjectContext, expected_project_commit: str) -> None:
        if self._closed or self._proof is not None:
            raise ValueError("Docker admission source proof is not reusable")
        inspected = GitCliLocalSourceInspector().inspect(context=context)
        if type(inspected) is not SourceLock:
            raise TypeError("source inspector returned a noncanonical lock")
        if inspected.project_source.dirty or inspected.engine_source.dirty:
            raise ValueError("Docker admission requires clean sources")
        if inspected.project_source.commit.lower() != expected_project_commit.lower():
            raise ValueError("project source differs from the committed ingress")
        if (
            inspected.engine_source.commit.lower()
            != str(inspected.engine_source.gitlink_commit).lower()
        ):
            raise ValueError("engine source differs from the committed gitlink")
        project_source = self._verified_remote_source(inspected.project_source)
        engine_source = self._verified_remote_source(inspected.engine_source)
        self._proof = _SourceProofV1(
            project_source, engine_source,
            _commit_time(context.project_root, project_source.commit),
        )

    def bind(self, snapshot: _AdmissionSnapshotV1) -> None:
        if self._closed or self._proof is None or self._verified is not None:
            raise ValueError("Docker admission session is not bindable")
        proof = self._proof
        if proof.project_source.commit.lower() != snapshot.config_blob.source_commit:
            raise ValueError("committed snapshot differs from source proof")
        provenance = {
            "training_input_digest": snapshot.input_digest,
            "training_contract_identity_digest": snapshot.contract_identity_digest,
            "training_source_sha256": snapshot.config_blob.sha256,
            "training_ingress_digest": snapshot.ingress_digest,
            "provider_policy_digest": snapshot.profile.digest,
        }
        if tuple(provenance) != _PROVENANCE_KEYS:
            raise ValueError("source provenance configuration is malformed")
        source_lock = SourceLock(
            run_id="admission-" + snapshot.ingress_digest[:24],
            mode="superproject",
            project_source=proof.project_source,
            engine_source=proof.engine_source,
            project={
                "manifest": _descriptor(
                    "project-manifest", "project://synaptic.yaml",
                    snapshot.manifest_blob,
                ),
            },
            configuration=dict(provenance),
            plugins=(),
            inputs=(
                _descriptor("training-config", snapshot.config_ref, snapshot.config_blob),
                _descriptor("training-dataset", snapshot.dataset_ref, snapshot.dataset_blob),
            ),
            runtime={
                "provider_ref": "docker",
                "profile_ref": snapshot.profile.profile_ref,
                "provider_policy_digest": snapshot.profile.digest,
                "provider_profile": _descriptor(
                    "docker-provider-profile",
                    "project://training/providers/docker.json",
                    snapshot.profile_blob,
                ),
                "storage_configuration_digest": snapshot.storage_blob.sha256,
                "storage_configuration": _descriptor(
                    "host-storage-configuration",
                    "project://training/storage.json",
                    snapshot.storage_blob,
                ),
            },
            outputs={
                "destination_ref": snapshot.destination.destination_ref,
                "destination_declaration_digest": artifact_destination_declaration_digest_v1(
                    snapshot.destination
                ),
                "destination_registry": _descriptor(
                    "artifact-destination-registry",
                    "project://training/artifacts.json",
                    snapshot.destination_blob,
                ),
            },
            created_at=proof.verified_at,
        )
        expires_at = (
            datetime.strptime(proof.verified_at, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            ) + timedelta(minutes=10)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence = AuthenticatedSourceEvidenceV1(
            project_url=proof.project_source.location.canonical_url,
            project_commit=proof.project_source.commit,
            engine_url=proof.engine_source.location.canonical_url,
            engine_commit=proof.engine_source.commit,
            engine_submodule_path=proof.engine_source.submodule_path,
            gitlink_commit=proof.engine_source.gitlink_commit,
            source_lock_binding=source_lock.binding,
            issuer_ref="host-docker-admission-v1",
            evidence_ref="admission-" + snapshot.ingress_digest[:24],
            audience_ref="docker/" + snapshot.ingress_digest[:32],
            challenge_nonce="challenge-" + snapshot.ingress_digest[24:48],
            verified_at=proof.verified_at,
            expires_at=expires_at,
            key_ref="process-docker-admission-v1",
            tag_base64="dGFn",
            attestation_digest="0" * 64,
        )
        payload = evidence.authenticated_payload
        tag = hmac.digest(self._key, _EVIDENCE_PURPOSE + payload, hashlib.sha256)
        evidence = replace(
            evidence,
            tag_base64=base64.b64encode(tag).decode("ascii"),
            attestation_digest=hashlib.sha256(payload).hexdigest(),
        )
        if not evidence.binds(source_lock):
            raise ValueError("source evidence does not bind the complete source lock")
        self._payload = payload
        self._tag = tag
        self._provenance = dict(provenance)
        self._verified = _VerifiedAdmissionV1(snapshot, source_lock, evidence)

    def consume(
        self, request: TrainingRequest, *, context: ProjectContext,
    ) -> _VerifiedAdmissionV1:
        if self._closed or self._consumed or self._verified is None:
            raise ValueError("Docker admission session was already consumed")
        verified = self._verified
        snapshot = verified.snapshot
        if (
            type(request) is not TrainingRequest
            or type(context) is not ProjectContext
            or context.mode != "host"
            or context.project_root != snapshot.project_root
            or context.engine_root != snapshot.engine_root
            or request.document != CanonicalDocument.from_mapping(
                snapshot.training_input.to_dict()
            )
        ):
            raise ValueError("request differs from the authenticated ingress")
        self._consumed = True
        return verified

    def verify_plan(self, plan: TrainingPlan) -> None:
        if (
            self._closed or not self._consumed or self._post_verified
            or self._verified is None or type(plan) is not TrainingPlan
        ):
            raise ValueError("Docker admission plan verification is unavailable")
        verified = self._verified
        evidence = verified.source_evidence
        payload = evidence.authenticated_payload
        expected = hmac.digest(self._key, _EVIDENCE_PURPOSE + payload, hashlib.sha256)
        if (
            payload != self._payload
            or not hmac.compare_digest(expected, self._tag)
            or not hmac.compare_digest(evidence.tag, self._tag)
            or evidence.attestation_digest != hashlib.sha256(payload).hexdigest()
            or not evidence.binds(verified.source_lock)
            or plan.execution_source.source_evidence != evidence
            or plan.execution_source.project_source != verified.source_lock.project_source
            or plan.execution_source.engine_source != verified.source_lock.engine_source
        ):
            raise ValueError("Docker admission evidence changed during compilation")
        validate_source_lock_provenance_v1(
            plan.execution_source, verified.source_lock, dict(self._provenance),
        )
        self._post_verified = True

    def close(self) -> None:
        self._key = b""
        self._payload = b""
        self._tag = b""
        self._closed = True


def _issue_admission_session_v1(
    reader: ScopedGitRemoteReader, clock: Callable[[], str],
    evidence_seed: str,
) -> _AdmissionSessionV1:
    if (
        type(reader) is not ScopedGitRemoteReader or not callable(clock)
        or type(evidence_seed) is not str
        or re.fullmatch(r"[0-9a-f]{64}", evidence_seed) is None
    ):
        raise TypeError("scoped remote reader and clock are required")
    value = object.__new__(_AdmissionSessionV1)
    value._reader = reader
    value._clock = clock
    value._key = hashlib.sha256(
        b"synaptic-docker-admission-evidence/v1\0"
        + evidence_seed.encode("ascii")
    ).digest()
    value._proof = None
    value._verified = None
    value._consumed = False
    value._post_verified = False
    value._closed = False
    value._payload = b""
    value._tag = b""
    value._provenance = {}
    return value


@dataclass(frozen=True, slots=True)
class DockerAdmissionResolverV1:
    session: _AdmissionSessionV1

    def __post_init__(self) -> None:
        if type(self.session) is not _AdmissionSessionV1:
            raise TypeError("exact Docker admission session is required")

    def resolve(
        self, request: TrainingRequest, *, context: ProjectContext,
    ) -> ResolvedTrainingComponents:
        verified = self.session.consume(request, context=context)
        snapshot = verified.snapshot
        source_lock = verified.source_lock
        profile = snapshot.profile
        roots = {
            "engine": "/source/engine", "project": "/source/project",
            "artifacts": "/artifacts/artifacts", "state": "/artifacts/state",
            "tracking": "/artifacts/tracking", "cache": "/artifacts/cache",
            "tmp": "/artifacts/tmp",
        }
        environment = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
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
        source = ExecutionSourceV1(
            run_id=source_lock.run_id, created_at=source_lock.created_at,
            project_source=source_lock.project_source,
            engine_source=source_lock.engine_source,
            engine_submodule_path=source_lock.engine_source.submodule_path,
            source_evidence=verified.source_evidence,
            deployment_member_sha256=_sha(
                b"docker-admission-deployment", source_lock.canonical_bytes,
            ),
            roots=roots, writable_capability_root="/artifacts",
            python_implementation=profile.python_implementation,
            python_version=profile.python_version,
            python_executable=profile.python_executable,
            python_executable_digest=profile.python_executable_digest,
            environment=environment,
            secret_requirements_digest=hashlib.sha256(_canonical({
                "schema_version": "synaptic-docker-secret-requirements/v1",
                "secrets": [],
            })).hexdigest(),
            provider_runtime_requirements_digest=profile.digest,
        )
        hyperparameters = snapshot.training_input.hyperparameters.to_dict()
        hyperparameters.pop("schema_version")
        duration = hyperparameters.pop("duration")
        limit_name = "max_steps" if duration["max_steps"] is not None else "num_epochs"
        hyperparameters[limit_name] = duration[limit_name]
        resolved = CanonicalDocument.from_mapping({
            "schema_version": "synaptic-sft-config/v1",
            "method": snapshot.training_input.method.value,
            "model": {
                **snapshot.training_input.model.to_dict(),
                "load_in_4bit": profile.load_in_4bit,
            },
            "dataset": {
                "ref": snapshot.dataset_ref,
                "revision": source_lock.project_source.commit.lower(),
                "content_digest": snapshot.dataset_blob.sha256,
            },
            "sft": hyperparameters,
        })
        execution_context = CanonicalDocument.from_mapping({
            "schema_version": _EXECUTION_CONTEXT_SCHEMA,
            "provider_ref": "docker", "profile_ref": profile.profile_ref,
            "provider_policy_digest": profile.digest,
            "docker_policy_ref": profile.docker_policy_ref,
            "workload_transport": profile.workload_transport,
            "source_mode": profile.source_mode, "network_mode": profile.network_mode,
            "destination": {
                "destination_ref": snapshot.destination.destination_ref,
                "configuration_digest": snapshot.destination.configuration_digest,
                "policy_digest": snapshot.destination.policy.policy_digest,
            },
            "admission_only": False,
        })
        return ResolvedTrainingComponents(
            execution_source=source, execution_context=execution_context,
            resolved_config=resolved,
            runtime=RuntimeSpec(
                profile.image, profile.dependency_lock_digest, profile.python_version,
            ),
            resources=ResourceSpec(
                profile.accelerators[0], 1, profile.timeout_seconds_maximum,
            ),
            artifact_policy=ArtifactPolicy(
                _ARTIFACT_ROLES,
                snapshot.training_input.artifacts.retain_checkpoints,
            ),
        )


def execute_docker_training_admission_v1(
    ingress, *, project_root: Path, engine_root: Path,
    remote_reader: ScopedGitRemoteReader | None = None,
):
    """Compile one canonical plan and return the Slice 1B capability result."""

    from .cli import (
        TrainingRunCommandCodeV2,
        TrainingRunCommandResultV2,
        _authenticate_training_run_ingress_v1,
        _failure,
        _read_committed_git_blob_v1,
    )

    baseline = _authenticate_training_run_ingress_v1(ingress)
    if baseline is None:
        return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
    (
        provider_ref, config_ref, destination_ref, input_digest,
        source_sha256, contract_identity_digest, ingress_digest,
        bound_project, bound_engine, config_blob,
    ) = baseline

    def fail(code):
        return _failure(
            code, provider_ref=provider_ref, config_ref=config_ref,
            destination_ref=destination_ref, input_digest=input_digest,
        )

    if provider_ref != "docker":
        return fail(TrainingRunCommandCodeV2.PROVIDER_UNAVAILABLE)
    try:
        project = Path(project_root).resolve(strict=True)
        engine = Path(engine_root).resolve(strict=True)
        if project != bound_project or engine != bound_engine:
            raise ValueError
        manifest = load_project_manifest(project / "synaptic.yaml")
        if manifest.path.parent.resolve(strict=True) != project:
            raise ValueError
        context = manifest.create_context(engine_root=engine, invocation_cwd=project)
        session = _issue_admission_session_v1(
            remote_reader or ScopedGitRemoteReader(), _utc_now,
            ingress_digest,
        )
    except BaseException:
        return fail(TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE)

    try:
        try:
            session.prove(
                context=context, expected_project_commit=config_blob.source_commit,
            )
        except BaseException:
            return fail(TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE)
        try:
            current_config = _read_committed_git_blob_v1(
                project, _project_path(config_ref), maximum_bytes=65536,
                expected_commit=config_blob.source_commit,
            )
            if current_config != config_blob or current_config.content != config_blob.content:
                raise ValueError
            profile_blob = _read_committed_git_blob_v1(
                project, "training/providers/docker.json", maximum_bytes=65536,
                expected_commit=config_blob.source_commit,
            )
            profile = DockerProviderProfileV1.from_bytes(profile_blob.content)
        except BaseException:
            return fail(TrainingRunCommandCodeV2.COMPOSITION_UNAVAILABLE)
        try:
            destination_blob = _read_committed_git_blob_v1(
                project, "training/artifacts.json", maximum_bytes=1_048_576,
                expected_commit=config_blob.source_commit,
            )
            destinations = parse_artifact_destination_config_v1(
                destination_blob.content
            )
            matches = tuple(
                item for item in destinations.destinations
                if item.destination_ref == destination_ref
            )
            if destination_ref == "provider-staging" or len(matches) != 1:
                raise ValueError
            destination = matches[0]
            if (
                profile.maximum_artifact_bytes
                > destination.policy.maximum_artifact_bytes
                or profile.maximum_total_bytes
                > destination.policy.maximum_total_bytes
            ):
                raise ValueError
        except BaseException:
            return fail(TrainingRunCommandCodeV2.DESTINATION_INVALID)
        try:
            dataset_ref = ingress.training_input.dataset.ref
            dataset_blob = _read_committed_git_blob_v1(
                project, _project_path(dataset_ref), maximum_bytes=67_108_864,
                expected_commit=config_blob.source_commit,
            )
            manifest_blob = _read_committed_git_blob_v1(
                project, "synaptic.yaml", maximum_bytes=1_048_576,
                expected_commit=config_blob.source_commit,
            )
            storage_blob = _read_committed_git_blob_v1(
                project, "training/storage.json", maximum_bytes=1_048_576,
                expected_commit=config_blob.source_commit,
            )
            snapshot = _AdmissionSnapshotV1(
                ingress.training_input, input_digest, contract_identity_digest,
                ingress_digest, project, engine, config_ref, config_blob, profile,
                profile_blob, destination, destination_blob, dataset_ref,
                dataset_blob, manifest_blob, storage_blob,
            )
            session.bind(snapshot)
            plan = compile_training_plan_v1(
                training_input=ingress.training_input, context=context,
                resolver=DockerAdmissionResolverV1(session),
            )
            if type(plan) is not TrainingPlan:
                raise TypeError("engine returned a noncanonical training plan")
            session.verify_plan(plan)
        except BaseException:
            return fail(TrainingRunCommandCodeV2.RESOLUTION_UNAVAILABLE)
        try:
            result = _activate_docker_training_v1(
                plan=plan, source_lock=session._verified.source_lock,
                snapshot=snapshot, context=context,
                project_ref=manifest.project_id, clock=_utc_now,
            )
        except BaseException:
            return fail(TrainingRunCommandCodeV2.START_UNAVAILABLE)
        if type(result) is not TrainingRunCommandResultV2:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        return result
    finally:
        session.close()


def _activate_docker_training_v1(
    *, plan: TrainingPlan, source_lock: SourceLock,
    snapshot: _AdmissionSnapshotV1, context: ProjectContext,
    project_ref: str, clock: Callable[[], str], model_inventory: tuple = (),
):
    """Prepare or advance one deterministic Docker run by one safe service cut."""

    from synaptic_tuner.api.v1 import TrainingRunRef
    from synaptic_tuner.api.v1.providers import (
        ProviderCapabilities, ProviderDescriptor, ProviderRef,
    )
    from synaptic_tuner.api.v1.training import AcceleratorDeviceRequestV1
    from tuner.execution.foundation_v2.canonical import canonical_bytes
    from tuner.execution.foundation_v2.commands import (
        CanonicalProviderPayloadV1, build_stage_command, build_submit_command,
    )
    from tuner.execution.foundation_v2.executors import (
        AdapterDescriptorV1, ExecutorDescriptorV1,
    )
    from tuner.execution.foundation_v2.references import (
        ExecutionScopeV1, StagePredecessorV2,
    )
    from tuner.execution.providers.docker_provider_v1.model import (
        DockerArtifactContractV1, DockerImageV1, DockerProfileV1,
        DockerRootsV1, DockerRuntimeV1, DockerWorkloadV1,
    )
    from tuner.execution.providers.docker_provider_v1.preparation import (
        DockerTrainingPreparationBridgeV1,
    )
    from .cli import (
        TrainingRunCommandCodeV2, TrainingRunCommandResultV2,
        TrainingRunCommandStatusV2,
    )
    from .docker_execution import DockerPreparedRunRequestV1
    from .docker_execution_state import (
        DockerRunMutationRecordV1, DockerRunPhaseV1,
        ProviderPreparationRecordV1,
    )
    from .docker_prepared_composition import (
        DockerPreparedCompositionV1, DockerPreparedControlBuilderV1,
        compose_docker_prepared_platform_v1,
    )
    from .docker_staging import (
        DockerModelInventoryEntryV1, stage_docker_worker_v1,
    )
    from .security import FileHmacAuthenticator
    from .sqlite_repository import EffectCollision, SqliteTrainingRepository

    if (
        type(model_inventory) is not tuple
        or any(type(item) is not DockerModelInventoryEntryV1 for item in model_inventory)
    ):
        raise ValueError("prewarmed Docker model inventory is invalid")
    authenticator = FileHmacAuthenticator.for_docker(
        context, durable_rows_exist=_docker_durable_rows_exist(context),
    )
    staging = stage_docker_worker_v1(
        plan=plan, source_lock=source_lock, context=context,
        storage_configuration=snapshot.storage_blob.content,
        model_inventory=model_inventory,
    )
    provider = ProviderRef("docker", snapshot.profile.profile_ref)
    scope = ExecutionScopeV1("local", snapshot.profile.profile_ref)
    executor = ExecutorDescriptorV1("docker", "docker-local", "1")
    adapter = AdapterDescriptorV1("docker", "docker-local", "1")
    image_ref, image_digest = snapshot.profile.image.rsplit("@", 1)
    resource_digest = hashlib.sha256(canonical_bytes({
        "accelerator": plan.resources.accelerator,
        "accelerator_count": plan.resources.accelerator_count,
        "timeout_seconds": plan.resources.timeout_seconds,
    })).hexdigest()
    quote_digest = hashlib.sha256(canonical_bytes({
        "schema_version": "synaptic-docker-local-quote/v1",
        "currency": "USD", "amount": "0",
    })).hexdigest()
    secret_digest = hashlib.sha256(canonical_bytes({
        "schema_version": "synaptic-docker-secret-requirements/v1",
        "secrets": [],
    })).hexdigest()
    bundle = staging.worker_bundle
    profile = DockerProfileV1.build(
        provider=provider,
        descriptor=ProviderDescriptor(
            "synaptic-provider-descriptor/v1", "docker", "Docker", "1.0.0",
            ProviderCapabilities(True, True, False, True, True, False),
        ),
        scope=scope, executor_descriptor=executor, adapter_descriptor=adapter,
        image=DockerImageV1(image_ref, image_digest),
        runtime=DockerRuntimeV1(
            snapshot.profile.cpu_count, snapshot.profile.memory_bytes_maximum,
            plan.resources.timeout_seconds,
            AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",)),
        ),
        workload=DockerWorkloadV1(
            tuple(bundle.dispatch.argv),
            tuple(sorted(dict(bundle.dispatch.environment))),
            bundle.workload_sha256,
        ),
        roots=DockerRootsV1(
            staging.projection.source_stage_ref,
            staging.projection.artifact_stage_ref,
        ),
        artifacts=DockerArtifactContractV1(
            _ARTIFACT_ROLES, snapshot.profile.maximum_artifact_bytes,
            snapshot.profile.maximum_total_bytes,
        ),
        resource_digest=resource_digest, quote_digest=quote_digest,
        secret_requirements_digest=secret_digest,
    )
    run = TrainingRunRef(source_lock.run_id, project_ref)
    bridge = DockerTrainingPreparationBridgeV1(profile)
    source_digest = source_lock.binding.source_lock_digest
    preparation = bridge.prepare(plan, run, source_digest)
    prepared = bridge.prepared(
        preparation=preparation, plan=plan, run=run,
        source_digest=source_digest,
    )
    expected_bundle = bridge._expected(plan, run, source_digest)[2]
    if expected_bundle != bundle:
        raise ValueError("staged worker bundle differs from the Docker bridge")
    payload = CanonicalProviderPayloadV1.build(
        "docker", "stage-payload/v2", bundle.workload_sha256,
    )
    stage_command = build_stage_command(
        preparation, "docker-stage", payload, executor,
    )
    predecessor = StagePredecessorV2(
        "docker", snapshot.profile.profile_ref, scope.account_ref,
        scope.namespace_ref, run.project_ref, run.run_id, plan.fingerprint,
        preparation.preparation_digest, bundle.workload_sha256,
        stage_command.operation.effect.effect_id,
        staging.projection.source_manifest_digest,
        staging.projection.worker_projection_digest,
    )
    submit = build_submit_command(
        preparation, "docker-submit",
        CanonicalProviderPayloadV1.build(
            "docker", "submit-payload/v2", bundle.workload_sha256,
        ),
        executor, predecessor,
    )
    repository = SqliteTrainingRepository.from_context(context, clock=clock)
    existing_preparation = repository.load_docker_preparation(
        run.project_ref, run.run_id,
    )
    platform = compose_docker_prepared_platform_v1()
    builder = DockerPreparedControlBuilderV1(
        authenticator=authenticator, platform=platform,
    )
    provisional = ProviderPreparationRecordV1.build(
        project_ref=run.project_ref, run_id=run.run_id,
        plan_fingerprint=plan.fingerprint,
        effect_id=submit.operation.effect.effect_id,
        source_lock_digest=source_digest,
        prepared_docker_plan_digest=prepared.digest,
        endpoint_descriptor_digest=platform.endpoint_descriptor_digest,
        cli_policy_digest=platform.cli_policy_digest,
        destination_ref=snapshot.destination.destination_ref,
        destination_declaration_digest=artifact_destination_declaration_digest_v1(
            snapshot.destination
        ),
        submit_command_bytes=submit.canonical_bytes,
        stage=staging.projection, prepared_at=source_lock.created_at,
    )
    request = DockerPreparedRunRequestV1(
        run.project_ref, run.run_id, provisional, prepared, staging,
    )
    composition = DockerPreparedCompositionV1(
        repository=repository, builder=builder, clock=clock,
    )
    admission = composition.prepare_admission(request)
    initial = DockerRunMutationRecordV1.initial(
        provisional, admission.create_mutation,
    )
    if existing_preparation is None:
        try:
            repository.create_docker_prepared_run(provisional, initial)
        except EffectCollision:
            existing_preparation = repository.load_docker_preparation(
                run.project_ref, run.run_id,
            )
    if existing_preparation is not None and existing_preparation != provisional:
        raise ValueError("durable Docker command differs from replay")
    current = repository.load_docker_run_mutation(run.project_ref, run.run_id)
    if current is None:
        raise ValueError("durable Docker aggregate is unavailable")
    if current.phase in {
        DockerRunPhaseV1.CREATE_ADMITTED, DockerRunPhaseV1.CREATE_ATTEMPTED,
        DockerRunPhaseV1.CREATED,
    }:
        outcome = composition.submit(request)
    else:
        outcome = composition.reconcile(request)
    submitted = (
        outcome.container_ref is not None and outcome.submitted_at is not None
    )
    code = (
        TrainingRunCommandCodeV2.SUBMITTED if submitted
        else TrainingRunCommandCodeV2.RECONCILE_REQUIRED
    )
    return TrainingRunCommandResultV2(
        "synaptic-training-run-command-result/v2",
        TrainingRunCommandStatusV2.SUBMITTED if submitted
        else TrainingRunCommandStatusV2.RECONCILE_REQUIRED,
        code, "docker", snapshot.config_ref,
        snapshot.destination.destination_ref, snapshot.input_digest,
        run.project_ref, run.run_id, plan.fingerprint,
        submit.operation.effect.effect_id,
        outcome.container_ref if submitted else None,
        outcome.submitted_at if submitted else None,
    )


__all__ = ["DockerAdmissionResolverV1", "execute_docker_training_admission_v1"]
