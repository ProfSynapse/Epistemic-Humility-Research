from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

import synaptic_host.docker_publication as publication
from synaptic_host.artifact_destinations import (
    artifact_destination_declaration_digest_v1,
    parse_artifact_destination_config_v1,
)
from synaptic_host.docker_execution import DockerPreparedRunRequestV1
from synaptic_host.docker_execution_state import (
    DockerRunMutationRecordV1, DockerRunPhaseV1, VerifiedDockerArtifactV1,
    verified_inventory_digest_v1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1, DockerControlOperationV1,
    DockerMutationPhaseV1, DockerMutationRecordV1, docker_operation_id_v1,
)
from synaptic_tuner.api.v1 import (
    ProjectContext, RunArtifactRequest, RunOperationCode, RunOperationError, RunsAPI,
    TrainingRunRef, TrainingRunState,
)


EFFECT = "submit-" + "1" * 64
RUN = TrainingRunRef("run", "project")
NOW = "2026-09-01T12:00:00Z"
ROLES = (
    "final_model", "tokenizer", "training_lineage", "training_metrics",
    "workload_record",
)
ROOT = Path(__file__).resolve().parents[2]


def _mutation(operation):
    record = DockerMutationRecordV1.build(
        operation_id=docker_operation_id_v1(operation, EFFECT),
        operation=operation, effect_id=EFFECT,
        control_intent_proof_digest=(
            "1" * 64 if operation is DockerControlOperationV1.CREATE else "2" * 64
        ),
        phase=DockerMutationPhaseV1.VERIFIED, revision=3, attempt_count=1,
        previous_record_digest="3" * 64, container_ref="a" * 64,
        verification_result_digest="4" * 64,
    )
    return AuthenticatedDockerMutationRecordV1(
        record, "authority", "key", record.record_digest
    )


def _verified(root: Path):
    data = root / "artifacts"
    data.mkdir(parents=True)
    descriptors = []
    for role in ROLES:
        payload = (role + "\n").encode()
        (data / f"{role}.bin").write_bytes(payload)
        descriptors.append(VerifiedDockerArtifactV1(
            role, f"{role}.bin", len(payload), hashlib.sha256(payload).hexdigest()
        ))
    artifacts = tuple(descriptors)
    return DockerRunMutationRecordV1.build(
        project_ref=RUN.project_ref, run_id=RUN.run_id, effect_id=EFFECT,
        preparation_digest="5" * 64,
        phase=DockerRunPhaseV1.ARTIFACTS_VERIFIED, revision=8,
        previous_record_digest="6" * 64,
        create_mutation=_mutation(DockerControlOperationV1.CREATE),
        start_mutation=_mutation(DockerControlOperationV1.START),
        reconcile_operation=None, container_ref="a" * 64,
        submitted_at=NOW, process_exit_code=0,
        process_observation_digest="7" * 64, diagnostic=None,
        verified_artifacts=artifacts,
        verified_inventory_digest=verified_inventory_digest_v1(artifacts),
    )


def _revised(record: DockerRunMutationRecordV1) -> DockerRunMutationRecordV1:
    values = {
        name: getattr(record, name)
        for name in DockerRunMutationRecordV1.__dataclass_fields__
        if name != "record_digest"
    }
    values["revision"] = record.revision + 1
    values["previous_record_digest"] = record.record_digest
    return DockerRunMutationRecordV1.build(**values)


class Repository:
    def __init__(self, record):
        self.record = record

    def load_docker_run_mutation(self, project_ref, run_id):
        assert (project_ref, run_id) == (RUN.project_ref, RUN.run_id)
        return self.record


def _runs(tmp_path):
    record = _verified(tmp_path)
    repository = Repository(record)
    request = SimpleNamespace(
        run_id=RUN.run_id, project_ref=RUN.project_ref,
        staging=SimpleNamespace(artifact_root=tmp_path),
    )
    operations = publication._DockerRunsOperationsV1(
        repository=repository, request=request, record=record, clock=lambda: NOW
    )
    return repository, RunsAPI(operations)


def test_private_runs_api_exposes_only_exact_verified_run_and_one_shot_stream(tmp_path):
    _repository, runs = _runs(tmp_path)
    shown = runs.show(RUN)
    assert shown.state is TrainingRunState.SUCCEEDED
    assert tuple(item.role for item in shown.artifacts) == ROLES
    assert runs.reverify(RUN).verified is True
    artifact = shown.artifacts[0]
    stream = runs.artifacts(RunArtifactRequest(RUN, artifact.role, artifact.size_bytes))
    assert b"".join(stream.iter_bytes()) == (artifact.role + "\n").encode()
    with pytest.raises(ValueError, match="one-shot"):
        stream.iter_bytes()


def test_stream_rechecks_durable_aggregate_before_read(tmp_path):
    repository, runs = _runs(tmp_path)
    artifact = runs.show(RUN).artifacts[0]
    stream = runs.artifacts(RunArtifactRequest(RUN, artifact.role, artifact.size_bytes))
    repository.record = SimpleNamespace()
    with pytest.raises(RunOperationError) as error:
        next(stream.iter_bytes())
    assert error.value.code is RunOperationCode.ARTIFACTS_UNVERIFIED


def test_private_runs_api_rejects_a_different_verified_aggregate(tmp_path):
    repository, runs = _runs(tmp_path)
    repository.record = _revised(repository.record)
    with pytest.raises(RunOperationError) as error:
        runs.show(RUN)
    assert error.value.code is RunOperationCode.STATE_CONFLICT


def test_composition_is_factory_only():
    with pytest.raises(TypeError, match="factory-issued"):
        publication.DockerPublicationCompositionV1()
    forged = object.__new__(publication.DockerPublicationCompositionV1)
    with pytest.raises(ValueError, match="composition is invalid"):
        forged.close()


def test_stream_rejects_simulated_reparse_directory_without_symlink_privilege(
    tmp_path, monkeypatch,
):
    _repository, runs = _runs(tmp_path)
    artifact = runs.show(RUN).artifacts[0]
    stream = runs.artifacts(RunArtifactRequest(RUN, artifact.role, artifact.size_bytes))
    monkeypatch.setattr(
        publication, "_directory_snapshot",
        lambda _path: (_ for _ in ()).throw(ValueError("simulated reparse")),
    )
    with pytest.raises(ValueError, match="simulated reparse"):
        next(stream.iter_bytes())


@pytest.mark.parametrize(
    ("changed_call", "changed_field"),
    ((1, "st_ino"), (2, "st_ctime_ns")),
)
def test_stream_rejects_swap_restore_and_restored_mtime(
    tmp_path, monkeypatch, changed_call, changed_field,
):
    _repository, runs = _runs(tmp_path)
    artifact = runs.show(RUN).artifacts[0]
    stream = runs.artifacts(
        RunArtifactRequest(RUN, artifact.role, artifact.size_bytes)
    )
    original_fstat = publication.os.fstat
    calls = 0

    def unstable(descriptor):
        nonlocal calls
        current = original_fstat(descriptor)
        calls += 1
        if calls != changed_call:
            return current
        values = {
            "st_mode": current.st_mode,
            "st_size": current.st_size,
            "st_dev": current.st_dev,
            "st_ino": current.st_ino,
            "st_mtime_ns": current.st_mtime_ns,
            "st_ctime_ns": current.st_ctime_ns,
            "st_file_attributes": getattr(current, "st_file_attributes", 0),
        }
        values[changed_field] += 1
        return SimpleNamespace(**values)

    monkeypatch.setattr(publication.os, "fstat", unstable)
    with pytest.raises(RunOperationError) as error:
        b"".join(stream.iter_bytes())
    assert error.value.code is RunOperationCode.ARTIFACT_CONTENT_INVALID


def test_composition_binds_verified_run_and_immutable_staged_configuration(
    tmp_path, monkeypatch,
):
    source_root = tmp_path / "stage" / "source"
    artifact_root = tmp_path / "stage" / "artifact"
    destination_path = source_root / "project" / "training" / "artifacts.json"
    storage_path = source_root / "control" / "storage.json"
    destination_path.parent.mkdir(parents=True)
    storage_path.parent.mkdir(parents=True)
    destination_bytes = (ROOT / "training" / "artifacts.json").read_bytes()
    storage_bytes = (ROOT / "training" / "storage.json").read_bytes()
    destination_path.write_bytes(destination_bytes)
    storage_path.write_bytes(storage_bytes)
    record = _verified(artifact_root)
    repository = Repository(record)
    destination = parse_artifact_destination_config_v1(destination_bytes).destinations[0]
    stage_projection = SimpleNamespace(
        staged_storage_configuration_digest=hashlib.sha256(storage_bytes).hexdigest()
    )
    preparation = SimpleNamespace(
        preparation_digest=record.preparation_digest,
        destination_ref=destination.destination_ref,
        destination_declaration_digest=(
            artifact_destination_declaration_digest_v1(destination)
        ),
        stage=stage_projection,
    )
    staging = SimpleNamespace(
        source_root=source_root, artifact_root=artifact_root,
        worker_bundle=SimpleNamespace(projection_sha256="8" * 64),
    )
    request = object.__new__(DockerPreparedRunRequestV1)
    for name, value in (
        ("project_ref", RUN.project_ref), ("run_id", RUN.run_id),
        ("preparation", preparation),
        ("prepared_plan", SimpleNamespace(digest="9" * 64)),
        ("staging", staging),
    ):
        object.__setattr__(request, name, value)
    engine_root = tmp_path / "project" / "synaptic-tuner"
    engine_root.mkdir(parents=True)
    context = ProjectContext.host(
        engine_root=engine_root, project_root=engine_root.parent
    )

    class Facade:
        closed = False

        def publish(self, _request):
            raise AssertionError("composition does not publish eagerly")

        def close(self):
            self.closed = True

    facade = Facade()
    captured = {}

    def compose(**values):
        captured.update(values)
        return facade

    def builder(**_values):
        raise AssertionError("the delegated composition owns builder invocation")

    monkeypatch.setattr(publication, "compose_host_publication_v1", compose)
    monkeypatch.setattr(publication, "HostPublicationFacadeV1", Facade)
    result = publication.compose_docker_publication_v1(
        context=context, repository=repository, request=request, clock=lambda: NOW,
        spool_root_ref="artifact-publication-spool",
        registration_builders=(builder,),
    )
    assert not hasattr(result, "__dict__")
    for exposed in (
        "facade", "runs", "run", "destination_ref", "preparation_digest",
        "record_digest", "_issue",
    ):
        assert not hasattr(result, exposed)
    assert captured["context"] == context
    assert captured["configuration"].destination_bytes == destination_bytes
    assert captured["configuration"].storage_bytes == storage_bytes
    assert captured["registration_builders"] == (builder,)

    original_source_root = staging.source_root
    staging.source_root = tmp_path / "redirected-source"
    with pytest.raises(ValueError, match="composition differs"):
        result.publish(request=request, record=record)
    staging.source_root = original_source_root

    destination_path.write_bytes(destination_bytes + b" ")
    with pytest.raises(ValueError, match="composition differs"):
        result.publish(request=request, record=record)
    destination_path.write_bytes(destination_bytes)

    repository.record = _revised(record)
    with pytest.raises(ValueError, match="composition differs"):
        result.publish(request=request, record=record)
    repository.record = record

    result.close()
    assert facade.closed is True
    with pytest.raises(ValueError, match="composition is closed"):
        result.publish(request=request, record=record)

    changed_facade = Facade()

    def compose_with_change(**_values):
        destination_path.write_bytes(destination_bytes + b" ")
        return changed_facade

    destination_path.write_bytes(destination_bytes)
    monkeypatch.setattr(
        publication, "compose_host_publication_v1", compose_with_change
    )
    with pytest.raises(ValueError, match="inputs changed during composition"):
        publication.compose_docker_publication_v1(
            context=context, repository=repository, request=request,
            clock=lambda: NOW, spool_root_ref="artifact-publication-spool",
            registration_builders=(builder,),
        )
    assert changed_facade.closed is True
