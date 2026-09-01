"""Host-owned, effect-free Docker training admission."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
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

from .artifact_destinations import (
    ArtifactDestinationDeclarationV1,
    parse_artifact_destination_config_v1,
)
from .docker_provider import DockerProviderProfileV1
from .security import ScopedGitRemoteReader


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


def _destination_declaration_digest(
    declaration: ArtifactDestinationDeclarationV1,
) -> str:
    return _sha(b"synaptic-destination-declaration/v1", _canonical({
        "destination_ref": declaration.destination_ref,
        "display_name": declaration.display_name,
        "adapter_ref": declaration.adapter_ref,
        "configuration_schema_version": declaration.configuration_schema_version,
        "configuration_digest": declaration.configuration_digest,
        "policy_digest": declaration.policy.policy_digest,
    }))


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
            project_source, engine_source, self._clock(),
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
            },
            outputs={
                "destination_ref": snapshot.destination.destination_ref,
                "destination_declaration_digest": _destination_declaration_digest(
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
            evidence_ref="admission-" + secrets.token_hex(12),
            audience_ref="docker/" + snapshot.ingress_digest[:32],
            challenge_nonce="challenge-" + secrets.token_hex(12),
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
) -> _AdmissionSessionV1:
    if type(reader) is not ScopedGitRemoteReader or not callable(clock):
        raise TypeError("scoped remote reader and clock are required")
    value = object.__new__(_AdmissionSessionV1)
    value._reader = reader
    value._clock = clock
    value._key = secrets.token_bytes(32)
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
        capability = "/workspace/run/" + source_lock.run_id
        roots = {
            "engine": "/workspace/engine", "project": "/workspace/project",
            "artifacts": capability + "/artifacts", "state": capability + "/state",
            "tracking": capability + "/tracking", "cache": capability + "/cache",
            "tmp": capability + "/tmp",
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
            roots=roots, writable_capability_root=capability,
            python_implementation=profile.python_implementation,
            python_version=profile.python_version,
            python_executable=profile.python_executable,
            python_executable_digest=profile.python_executable_digest,
            environment=environment,
            secret_requirements_digest=_sha(b"docker-secret-requirements", b"[]"),
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
            "admission_only": True,
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
                snapshot.training_input.artifacts.required_kinds,
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
        context = ProjectContext.host(
            engine_root=engine, project_root=project,
            invocation_cwd=project, config_root=project / "training",
        )
        session = _issue_admission_session_v1(
            remote_reader or ScopedGitRemoteReader(), _utc_now,
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
            snapshot = _AdmissionSnapshotV1(
                ingress.training_input, input_digest, contract_identity_digest,
                ingress_digest, project, engine, config_ref, config_blob, profile,
                profile_blob, destination, destination_blob, dataset_ref,
                dataset_blob, manifest_blob,
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
        result = fail(TrainingRunCommandCodeV2.CAPABILITY_UNSUPPORTED)
        if type(result) is not TrainingRunCommandResultV2:
            return _failure(TrainingRunCommandCodeV2.INTERNAL_FAILURE)
        return result
    finally:
        session.close()


__all__ = ["DockerAdmissionResolverV1", "execute_docker_training_admission_v1"]
