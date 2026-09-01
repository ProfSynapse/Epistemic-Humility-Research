from __future__ import annotations

from types import SimpleNamespace
from pathlib import PurePosixPath
from dataclasses import replace
import os

import synaptic_host.docker_execution as docker_execution
import pytest

from synaptic_host.docker_execution import (
    DockerAggregateMutationRepositoryV1,
    DockerPreparedControlsV1,
    DockerPreparedRunOutcomeV1,
    DockerPreparedRunServiceV1,
)
from synaptic_host.docker_execution_state import (
    DockerRunMutationRecordV1,
    DockerRunPhaseV1,
)
from synaptic_host.docker_v1.control_contract import (
    AuthenticatedDockerMutationRecordV1,
    DockerControlOperationV1,
    DockerMutationCASRequestV1,
    DockerMutationPhaseV1,
    DockerMutationRecordV1,
    DockerMutationAdmissionRequestV1,
    docker_operation_id_v1,
)
from tuner.execution.providers.docker_provider_v1.model import (
    DockerCreateDispositionV1, DockerStartDispositionV1,
)


EFFECT = "submit-" + "1" * 64
NOW = "2026-09-01T12:00:00Z"


def _auth(record):
    return AuthenticatedDockerMutationRecordV1(
        record, "authority", "key", record.record_digest
    )


def _low(operation, phase, previous=None, container_ref=None):
    matrix = {
        DockerMutationPhaseV1.ADMITTED: (1, 0),
        DockerMutationPhaseV1.ATTEMPTED: (2, 1),
        DockerMutationPhaseV1.VERIFIED: (3, 1),
    }
    revision, count = matrix[phase]
    return _auth(DockerMutationRecordV1.build(
        operation_id=docker_operation_id_v1(operation, EFFECT),
        operation=operation,
        effect_id=EFFECT,
        control_intent_proof_digest=(
            "1" * 64 if operation is DockerControlOperationV1.CREATE
            else "2" * 64
        ),
        phase=phase,
        revision=revision,
        attempt_count=count,
        previous_record_digest=previous,
        container_ref=container_ref,
        verification_result_digest=(
            "3" * 64 if phase is DockerMutationPhaseV1.VERIFIED else None
        ),
    ))


def _initial():
    create = _low(
        DockerControlOperationV1.CREATE, DockerMutationPhaseV1.ADMITTED
    )
    return DockerRunMutationRecordV1.build(
        project_ref="project", run_id="run", effect_id=EFFECT,
        preparation_digest="4" * 64,
        phase=DockerRunPhaseV1.CREATE_ADMITTED,
        revision=1, previous_record_digest=None,
        create_mutation=create, start_mutation=None,
        reconcile_operation=None, container_ref=None, submitted_at=None,
        process_exit_code=None, process_observation_digest=None,
        diagnostic=None, verified_artifacts=(),
        verified_inventory_digest=None,
    )


class Repository:
    def __init__(self, value):
        self.value = value

    def load_docker_run_mutation(self, project_ref, run_id):
        assert (project_ref, run_id) == ("project", "run")
        return self.value

    def compare_and_swap_docker_run_mutation(
        self, replacement, *, expected_revision, expected_record_digest,
    ):
        assert expected_revision == self.value.revision
        assert expected_record_digest == self.value.record_digest
        from synaptic_host.docker_execution_state import (
            validate_docker_run_transition_v1,
        )
        validate_docker_run_transition_v1(self.value, replacement)
        self.value = replacement
        return replacement


def _cas(expected, replacement):
    return DockerMutationCASRequestV1.build(
        expected.content.operation_id, expected, replacement
    )


def test_aggregate_adapter_advances_exact_create_and_start_envelopes():
    repository = Repository(_initial())
    adapter = DockerAggregateMutationRepositoryV1(
        repository, project_ref="project", run_id="run", clock=lambda: NOW
    )
    admitted = repository.value.create_mutation
    attempted = _low(
        DockerControlOperationV1.CREATE,
        DockerMutationPhaseV1.ATTEMPTED,
        admitted.content.record_digest,
    )
    assert adapter.compare_and_swap(_cas(admitted, attempted)).record == attempted
    verified = _low(
        DockerControlOperationV1.CREATE,
        DockerMutationPhaseV1.VERIFIED,
        attempted.content.record_digest,
        "a" * 64,
    )
    assert adapter.compare_and_swap(_cas(attempted, verified)).record == verified
    assert repository.value.phase is DockerRunPhaseV1.CREATED

    start_admitted = _low(
        DockerControlOperationV1.START, DockerMutationPhaseV1.ADMITTED
    )
    from synaptic_host.docker_v1.control_contract import (
        DockerMutationAdmissionRequestV1,
    )
    admission = adapter.admit(DockerMutationAdmissionRequestV1.build(
        start_admitted.content.operation_id, start_admitted
    ))
    assert admission.record == start_admitted
    start_attempted = _low(
        DockerControlOperationV1.START,
        DockerMutationPhaseV1.ATTEMPTED,
        start_admitted.content.record_digest,
    )
    adapter.compare_and_swap(_cas(start_admitted, start_attempted))
    start_verified = _low(
        DockerControlOperationV1.START,
        DockerMutationPhaseV1.VERIFIED,
        start_attempted.content.record_digest,
        "a" * 64,
    )
    adapter.compare_and_swap(_cas(start_attempted, start_verified))
    assert repository.value.phase is DockerRunPhaseV1.SUBMITTED
    assert repository.value.container_ref == "a" * 64
    assert repository.value.submitted_at == NOW


def test_internal_outcome_has_exact_derived_state_and_no_publication():
    outcome = DockerPreparedRunOutcomeV1.from_record(_initial())
    assert outcome.pending is True
    assert outcome.failed is False
    assert outcome.reconcile_required is False
    assert outcome.published is False
    assert outcome.publication_id is outcome.publication_state is None


def test_process_observation_cli_uncertainty_is_closed_and_digest_free():
    class Runner:
        def inspect_container(self, _container_ref):
            raise OSError("unavailable")

    request = SimpleNamespace(preparation=SimpleNamespace(
        cli_policy_digest="1" * 64,
        preparation_digest="2" * 64,
    ))
    controls = object.__new__(DockerPreparedControlsV1)
    object.__setattr__(controls, "labels", object())
    object.__setattr__(controls, "expected_create", SimpleNamespace(
        content=SimpleNamespace(environment_binding=object())
    ))
    object.__setattr__(controls, "create", object())
    object.__setattr__(controls, "start", object())
    object.__setattr__(controls, "control", object())
    object.__setattr__(controls, "typed_runner", Runner())
    observation = docker_execution._observe_docker_process_v1(
        request=request, controls=controls, container_ref="a" * 64,
    )
    assert observation.kind.value == "UNCERTAIN"
    assert observation.exit_code is observation.observation_digest is None
    assert observation.diagnostic == "PROCESS_OBSERVATION_UNAVAILABLE"


def test_prepared_controls_reject_noncanonical_capabilities():
    with pytest.raises(ValueError, match="prepared Docker controls"):
        DockerPreparedControlsV1(
            labels=object(), expected_create=object(), create=object(),
            start=object(), control=object(), typed_runner=object(),
        )


def test_outcome_rejects_publication_fields_in_slice_a():
    outcome = DockerPreparedRunOutcomeV1.from_record(_initial())
    with pytest.raises(TypeError, match="factory-issued"):
        replace(outcome, publication_id="not-admitted")


def test_internal_result_constructor_matrices_are_closed():
    with pytest.raises(ValueError, match="observation matrix"):
        docker_execution._DockerProcessObservationV1(
            docker_execution._DockerProcessObservationKindV1.FAILED,
            0, "5" * 64, "PROCESS_EXIT_NONZERO",
        )
    artifact = docker_execution.VerifiedDockerArtifactV1(
        "final_model", "model.tar", 1, "6" * 64
    )
    with pytest.raises(ValueError, match="verification matrix"):
        docker_execution._DockerArtifactVerificationV1(
            docker_execution._DockerArtifactVerificationKindV1.INVALID,
            (artifact,), None, "ARTIFACT_INTEGRITY_INVALID",
        )
    with pytest.raises(ValueError, match="verification matrix"):
        docker_execution._DockerArtifactVerificationV1(
            docker_execution._DockerArtifactVerificationKindV1.UNCERTAIN,
            (), "7" * 64, "ARTIFACT_READ_UNAVAILABLE",
        )


def test_verified_artifact_result_rejects_sha_shaped_wrong_inventory_digest():
    artifacts = tuple(
        docker_execution.VerifiedDockerArtifactV1(
            role, f"{role}.bin", 1, str(index) * 64,
        )
        for index, role in enumerate((
            "final_model", "tokenizer", "training_lineage",
            "training_metrics", "workload_record",
        ), start=1)
    )
    canonical = docker_execution.verified_inventory_digest_v1(artifacts)
    wrong = "f" * 64 if canonical != "f" * 64 else "e" * 64
    with pytest.raises(ValueError, match="inventory digest"):
        docker_execution._DockerArtifactVerificationV1(
            docker_execution._DockerArtifactVerificationKindV1.VERIFIED,
            artifacts, wrong, None,
        )


def test_submit_performs_create_then_start_on_separate_calls_only():
    repository = Repository(_initial())
    calls = []

    class Create:
        def __init__(self, adapter):
            self.adapter = adapter

        def create_once(self, **_kwargs):
            calls.append("create")
            admitted = repository.value.create_mutation
            attempted = _low(
                DockerControlOperationV1.CREATE,
                DockerMutationPhaseV1.ATTEMPTED,
                admitted.content.record_digest,
            )
            self.adapter.compare_and_swap(_cas(admitted, attempted))
            verified = _low(
                DockerControlOperationV1.CREATE,
                DockerMutationPhaseV1.VERIFIED,
                attempted.content.record_digest, "a" * 64,
            )
            self.adapter.compare_and_swap(_cas(attempted, verified))
            return SimpleNamespace(disposition=DockerCreateDispositionV1.CREATED)

    class Start:
        def __init__(self, adapter):
            self.adapter = adapter

        def start_once(self, _container_ref, _labels):
            calls.append("start")
            admitted = _low(
                DockerControlOperationV1.START,
                DockerMutationPhaseV1.ADMITTED,
            )
            self.adapter.admit(DockerMutationAdmissionRequestV1.build(
                admitted.content.operation_id, admitted
            ))
            attempted = _low(
                DockerControlOperationV1.START,
                DockerMutationPhaseV1.ATTEMPTED,
                admitted.content.record_digest,
            )
            self.adapter.compare_and_swap(_cas(admitted, attempted))
            verified = _low(
                DockerControlOperationV1.START,
                DockerMutationPhaseV1.VERIFIED,
                attempted.content.record_digest, "a" * 64,
            )
            self.adapter.compare_and_swap(_cas(attempted, verified))
            return SimpleNamespace(disposition=DockerStartDispositionV1.STARTED)

    class Factory:
        def build(self, _request, adapter):
            return SimpleNamespace(
                labels=object(), create=Create(adapter), start=Start(adapter),
            )

    class Verifier:
        def verify(self, **_kwargs):
            raise AssertionError("artifact verification is not admitted")

    profile = SimpleNamespace(
        image=object(), runtime=object(), workload=object(),
        roots=SimpleNamespace(source_ref="source", artifact_ref="artifact"),
    )
    request = SimpleNamespace(
        project_ref="project", run_id="run",
        preparation=SimpleNamespace(preparation_digest="4" * 64),
        prepared_plan=SimpleNamespace(profile=profile),
        staging=SimpleNamespace(worker_bundle=SimpleNamespace(
            dispatch=SimpleNamespace(cwd=PurePosixPath("/artifacts/tmp"))
        )),
    )
    service = DockerPreparedRunServiceV1(
        repository=repository, control_factory=Factory(),
        artifact_verifier=Verifier(), clock=lambda: NOW, publication=None,
    )
    assert service.submit(request).phase is DockerRunPhaseV1.CREATED
    assert calls == ["create"]
    assert service.submit(request).phase is DockerRunPhaseV1.SUBMITTED
    assert calls == ["create", "start"]


def test_artifact_directory_chain_rejects_files_and_links(tmp_path):
    verifier = docker_execution._DockerPreparedArtifactVerifierV1()
    root = tmp_path / "artifacts-root"
    root.mkdir()
    (root / "state").write_bytes(b"not-a-directory")
    with pytest.raises(ValueError, match="artifact directory"):
        verifier._directory_chain(root, ("state",))

    (root / "state").unlink()
    target = root / "target"
    target.mkdir()
    try:
        (root / "state").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable")
    with pytest.raises(ValueError, match="artifact directory"):
        verifier._directory_chain(root, ("state",))


def test_exit_zero_persists_success_before_next_call_reads_artifacts(monkeypatch):
    repository = Repository(_initial())
    adapter = DockerAggregateMutationRepositoryV1(
        repository, project_ref="project", run_id="run", clock=lambda: NOW
    )
    create_admitted = repository.value.create_mutation
    create_attempted = _low(
        DockerControlOperationV1.CREATE, DockerMutationPhaseV1.ATTEMPTED,
        create_admitted.content.record_digest,
    )
    adapter.compare_and_swap(_cas(create_admitted, create_attempted))
    create_verified = _low(
        DockerControlOperationV1.CREATE, DockerMutationPhaseV1.VERIFIED,
        create_attempted.content.record_digest, "a" * 64,
    )
    adapter.compare_and_swap(_cas(create_attempted, create_verified))
    start_admitted = _low(
        DockerControlOperationV1.START, DockerMutationPhaseV1.ADMITTED
    )
    adapter.admit(DockerMutationAdmissionRequestV1.build(
        start_admitted.content.operation_id, start_admitted
    ))
    start_attempted = _low(
        DockerControlOperationV1.START, DockerMutationPhaseV1.ATTEMPTED,
        start_admitted.content.record_digest,
    )
    adapter.compare_and_swap(_cas(start_admitted, start_attempted))
    start_verified = _low(
        DockerControlOperationV1.START, DockerMutationPhaseV1.VERIFIED,
        start_attempted.content.record_digest, "a" * 64,
    )
    adapter.compare_and_swap(_cas(start_attempted, start_verified))

    monkeypatch.setattr(
        docker_execution, "_observe_docker_process_v1",
        lambda **_kwargs: docker_execution._DockerProcessObservationV1(
            docker_execution._DockerProcessObservationKindV1.SUCCEEDED,
            0, "5" * 64, None,
        ),
    )

    class Factory:
        calls = 0

        def build(self, _request, _adapter):
            self.calls += 1
            return SimpleNamespace()

    class Verifier:
        calls = 0

        def verify(self, **_kwargs):
            self.calls += 1
            return docker_execution._DockerArtifactVerificationV1(
                docker_execution._DockerArtifactVerificationKindV1.UNCERTAIN,
                (), None, "ARTIFACT_READ_UNAVAILABLE",
            )

    verifier = Verifier()
    request = SimpleNamespace(
        project_ref="project", run_id="run",
        preparation=SimpleNamespace(preparation_digest="4" * 64),
    )
    factory = Factory()
    service = DockerPreparedRunServiceV1(
        repository=repository, control_factory=factory,
        artifact_verifier=verifier, clock=lambda: NOW, publication=None,
    )
    first = service.reconcile(request)
    assert first.phase is DockerRunPhaseV1.PROCESS_SUCCEEDED
    assert verifier.calls == 0
    second = service.reconcile(request)
    assert second.phase is DockerRunPhaseV1.PROCESS_SUCCEEDED
    assert verifier.calls == 1
    assert factory.calls == 1


def test_read_regular_rejects_open_handle_and_post_read_identity_drift(
    tmp_path, monkeypatch,
):
    path = tmp_path / "member.bin"
    path.write_bytes(b"abcd")
    real_fstat = os.fstat
    calls = 0

    def drift_after_read(descriptor):
        nonlocal calls
        current = real_fstat(descriptor)
        if current.st_size != 4:
            return current
        calls += 1
        if calls == 2:
            return SimpleNamespace(
                st_dev=current.st_dev, st_ino=current.st_ino + 1,
                st_mode=current.st_mode, st_size=current.st_size,
                st_file_attributes=getattr(current, "st_file_attributes", 0),
                st_mtime_ns=current.st_mtime_ns,
                st_ctime_ns=current.st_ctime_ns,
            )
        return current

    monkeypatch.setattr(os, "fstat", drift_after_read)
    with pytest.raises(ValueError, match="changed during read"):
        docker_execution._DockerPreparedArtifactVerifierV1._read_regular(path, 8)


def test_read_regular_rejects_in_place_mutation_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "member.bin"
    path.write_bytes(b"abcd")
    real_fstat = os.fstat
    calls = 0

    def mutated_metadata(descriptor):
        nonlocal calls
        current = real_fstat(descriptor)
        if current.st_size != 4:
            return current
        calls += 1
        if calls == 2:
            return SimpleNamespace(
                st_dev=current.st_dev, st_ino=current.st_ino,
                st_mode=current.st_mode, st_size=current.st_size,
                st_file_attributes=getattr(current, "st_file_attributes", 0),
                st_mtime_ns=current.st_mtime_ns + 1,
                st_ctime_ns=current.st_ctime_ns,
            )
        return current

    monkeypatch.setattr(os, "fstat", mutated_metadata)
    with pytest.raises(ValueError, match="changed during read"):
        docker_execution._DockerPreparedArtifactVerifierV1._read_regular(path, 8)


@pytest.mark.parametrize(
    "error,expected_kind,expected_diagnostic",
    (
        (ValueError("confirmed invalid"), "INVALID", "ARTIFACT_INVENTORY_INVALID"),
        (PermissionError("unstable read"), "UNCERTAIN", "ARTIFACT_READ_UNAVAILABLE"),
    ),
)
def test_inventory_read_failure_classification_is_deterministic(
    tmp_path, monkeypatch, error, expected_kind, expected_diagnostic,
):
    root = tmp_path / "root"
    (root / "state").mkdir(parents=True)
    request = SimpleNamespace(
        staging=SimpleNamespace(
            artifact_root=root,
            worker_bundle=SimpleNamespace(workload_fingerprint="1" * 64),
        ),
        prepared_plan=SimpleNamespace(profile=SimpleNamespace(
            artifacts=SimpleNamespace(
                maximum_artifact_bytes=1024, maximum_total_bytes=4096,
            )
        )),
    )
    monkeypatch.setattr(
        docker_execution._DockerPreparedArtifactVerifierV1,
        "_read_regular", staticmethod(lambda *_args, **_kwargs: (_ for _ in ()).throw(error)),
    )
    result = docker_execution._DockerPreparedArtifactVerifierV1().verify(
        request=request, process_observation_digest="2" * 64,
    )
    assert result.kind.value == expected_kind
    assert result.diagnostic == expected_diagnostic
