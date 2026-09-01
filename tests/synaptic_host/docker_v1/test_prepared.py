from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
from pathlib import PurePosixPath
from types import SimpleNamespace

import pytest

from tuner.execution.foundation_v2.commands import (
    CanonicalProviderPayloadV1, build_submit_command,
)
from tuner.execution.foundation_v2.references import StagePredecessorV2
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCommandBindingV1, DockerEffectIdentityV1, labels_for,
    DockerRootsV1,
)

from synaptic_host.docker_execution import DockerPreparedRunRequestV1
from synaptic_host.docker_execution_state import DockerStageProjectionV1
from synaptic_host.docker_staging import DockerStagingResultV1
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerCreatePathBindingV1,
)
from synaptic_host.docker_v1.prepared import DockerPreparedMountAdapterV1

from .conftest import D, _prepared, _profile


class PathAuthority:
    authority_ref = "prepared-path-authority"
    key_ref = "docker-control-v1"

    def issue(self, content):
        return AuthenticatedDockerCreatePathBindingV1(
            content, self.authority_ref, self.key_ref, "a" * 64
        )

    def authenticate(self, value):
        return value


def _adapter(tmp_path: Path, *, lstat=os.lstat):
    stage_key = "a" * 64
    source_ref = f"host-stage://{stage_key}/source"
    artifact_ref = f"host-stage://{stage_key}/artifacts"
    profile = replace(
        _profile("opaque/local-cpu"),
        roots=DockerRootsV1(source_ref, artifact_ref),
    )
    prepared, preparation = _prepared(profile)
    predecessor = StagePredecessorV2(
        profile.provider.provider_id, profile.provider.profile_ref,
        profile.scope.account_ref, profile.scope.namespace_ref,
        prepared.project_ref, prepared.run_id, prepared.plan_fingerprint,
        prepared.preparation_digest, profile.workload.workload_digest,
        "stage-effect", D[10], D[11],
    )
    command = build_submit_command(
        preparation, "submit-effect",
        CanonicalProviderPayloadV1.build(
            "docker", "submit-payload/v2", profile.workload.workload_digest
        ),
        profile.executor_descriptor, predecessor,
    )
    identity = DockerEffectIdentityV1(
        command.digest, command.operation.effect.effect_id, "submit", prepared
    )
    binding = DockerCommandBindingV1(identity, command.canonical_bytes)
    labels = labels_for(identity)
    stage = (tmp_path / "docker" / "stages" / stage_key).resolve()
    source = stage / "source"
    artifacts = stage / "artifacts"
    stage.mkdir(parents=True)
    source.mkdir()
    artifacts.mkdir()
    projection = DockerStageProjectionV1(
        profile.roots.source_ref, "1" * 64,
        profile.roots.artifact_ref, "2" * 64, "3" * 64, "4" * 64,
        "tuner/runtime/manifests/offline-sft-worker-v1.json", "5" * 64,
        "6" * 64, "7" * 64, "8" * 64,
    )
    staging = object.__new__(DockerStagingResultV1)
    object.__setattr__(staging, "projection", projection)
    object.__setattr__(staging, "source_root", source)
    object.__setattr__(staging, "artifact_root", artifacts)
    object.__setattr__(staging, "worker_bundle", SimpleNamespace(
        dispatch=SimpleNamespace(cwd=PurePosixPath("/artifacts/tmp"), environment=())
    ))
    request = object.__new__(DockerPreparedRunRequestV1)
    object.__setattr__(request, "prepared_plan", prepared)
    object.__setattr__(request, "staging", staging)
    object.__setattr__(request, "preparation", type("Preparation", (), {
        "submit_command_bytes": command.canonical_bytes,
        "preparation_digest": "9" * 64,
    })())
    adapter = DockerPreparedMountAdapterV1(
        request=request, binding=binding, labels=labels,
        distro="Ubuntu-22.04", path_authority=PathAuthority(), lstat=lstat,
    )
    return adapter, profile, labels


def test_prepared_adapter_binds_exact_staged_roots(tmp_path: Path):
    adapter, profile, labels = _adapter(tmp_path)
    resolved = adapter.resolve_create_mounts(
        labels=labels, image=profile.image, runtime=profile.runtime,
        workload=profile.workload, source_ref=profile.roots.source_ref,
        artifact_ref=profile.roots.artifact_ref,
    )
    assert resolved.source_read_only is True
    binding = adapter.bind(
        resolved, profile.roots.source_ref, profile.roots.artifact_ref
    )
    assert binding.content.source_request.posix_path.endswith(
        "/docker/stages/" + "a" * 64 + "/source"
    )
    assert binding.content.artifact_request.posix_path.endswith(
        "/docker/stages/" + "a" * 64 + "/artifacts"
    )
    assert adapter.translate(binding.content.source_request).unc_path.endswith(
        "\\docker\\stages\\" + "a" * 64 + "\\source"
    )


def test_prepared_adapter_rejects_root_replacement(tmp_path: Path):
    adapter, profile, labels = _adapter(tmp_path)
    source = adapter._request.staging.source_root
    source.rmdir()
    source.mkdir()
    with pytest.raises(ValueError, match="identity changed"):
        adapter.resolve_create_mounts(
            labels=labels, image=profile.image, runtime=profile.runtime,
            workload=profile.workload, source_ref=profile.roots.source_ref,
            artifact_ref=profile.roots.artifact_ref,
        )


def test_prepared_adapter_rejects_different_stage_keys(tmp_path: Path):
    adapter, _profile_value, labels = _adapter(tmp_path)
    staging = adapter._request.staging
    projection = replace(
        staging.projection,
        artifact_stage_ref=f"host-stage://{'b' * 64}/artifacts",
    )
    object.__setattr__(staging, "projection", projection)
    with pytest.raises(ValueError, match="topology"):
        DockerPreparedMountAdapterV1(
            request=adapter._request, binding=adapter._binding, labels=labels,
            distro="Ubuntu-22.04", path_authority=PathAuthority(),
        )


def test_prepared_adapter_rejects_simulated_reparse_ancestor(tmp_path: Path):
    def reparse_lstat(path):
        observed = os.lstat(path)
        attributes = (
            getattr(observed, "st_file_attributes", 0)
            | (0x400 if Path(path).name == "stages" else 0)
        )
        return SimpleNamespace(
            st_mode=observed.st_mode, st_dev=observed.st_dev,
            st_ino=observed.st_ino, st_file_attributes=attributes,
        )

    with pytest.raises(ValueError, match="untrusted directory"):
        _adapter(tmp_path, lstat=reparse_lstat)
