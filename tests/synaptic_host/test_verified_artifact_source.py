from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import synaptic_host.verified_artifact_source as source_module
from synaptic_host.publication_authority import create_publication_evidence_v1
from synaptic_host.verified_artifact_source import AuthenticatedVerifiedArtifactSourceV1
from synaptic_tuner.api.v1 import (
    ProjectContext,
    RunArtifactRequest,
    RunOutcome,
    RunsAPI,
    RunVerification,
    TrainingRunRef,
    TrainingRunState,
    VerifiedArtifact,
)


RUN = TrainingRunRef("run-1", "project-1")


class Stream:
    def __init__(self, run, artifact, maximum_bytes, data):
        self.run = run
        self.artifact = artifact
        self.maximum_bytes = maximum_bytes
        self.data = data

    def iter_bytes(self):
        if self.data:
            yield self.data


class Operations:
    def __init__(self, data: bytes = b"adapter") -> None:
        self.data = data
        self.artifact = VerifiedArtifact(
            "adapter", hashlib.sha256(data).hexdigest(), len(data)
        )
        self.state = TrainingRunState.SUCCEEDED
        self.verified = True
        self.show_calls = 0
        self.reverify_calls = 0
        self.artifact_calls = 0
        self.second_artifact = None
        self.stream = None

    def show(self, run):
        self.show_calls += 1
        artifact = self.second_artifact if self.show_calls >= 2 and self.second_artifact else self.artifact
        return RunOutcome("synaptic-run-outcome/v1", run, self.state, (artifact,))

    def reverify(self, run):
        self.reverify_calls += 1
        return RunVerification(run, self.verified, "2026-08-31T12:00:00Z")

    def artifacts(self, request):
        self.artifact_calls += 1
        return self.stream or Stream(
            request.run, self.artifact, request.maximum_bytes, self.data
        )


def _context(tmp_path: Path) -> ProjectContext:
    return ProjectContext.host(
        engine_root=tmp_path / "engine",
        project_root=tmp_path,
        state_root=tmp_path / ".synaptic/state",
    )


def _source(tmp_path: Path, operations: Operations):
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.verified_sources
    return (
        AuthenticatedVerifiedArtifactSourceV1(
            runs=RunsAPI(operations), issuer=issuer, verifier=verifier
        ),
        verifier,
    )


def test_describe_reverifies_unchanged_successful_inventory_and_authenticates(tmp_path: Path) -> None:
    operations = Operations()
    source, verifier = _source(tmp_path, operations)
    value = source.describe(RUN)
    assert value.run == RUN
    assert value.artifacts == (operations.artifact,)
    assert operations.show_calls == 2
    assert operations.reverify_calls == 1
    assert verifier.verify(
        "publication-verified-source/v1", value.payload, value.tag, value.key_ref
    )


def test_repeated_unchanged_describe_has_stable_source_identity(tmp_path: Path) -> None:
    operations = Operations()
    source, _ = _source(tmp_path, operations)
    first = source.describe(RUN)
    operations.show_calls = 0
    second = source.describe(RUN)
    assert first == second
    assert first.source_identity_digest == second.source_identity_digest


@pytest.mark.parametrize("state", [
    TrainingRunState.PLANNED,
    TrainingRunState.RUNNING,
    TrainingRunState.FAILED,
    TrainingRunState.RECONCILE_REQUIRED,
])
def test_describe_rejects_non_successful_runs(tmp_path: Path, state: TrainingRunState) -> None:
    operations = Operations()
    operations.state = state
    source, _ = _source(tmp_path, operations)
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.describe(RUN)
    assert operations.reverify_calls == 0


def test_describe_rejects_failed_reverification_or_inventory_change(tmp_path: Path) -> None:
    operations = Operations()
    operations.verified = False
    source, _ = _source(tmp_path, operations)
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.describe(RUN)

    operations = Operations()
    operations.second_artifact = VerifiedArtifact(
        "adapter", hashlib.sha256(b"changed").hexdigest(), 7
    )
    source, _ = _source(tmp_path / "other", operations)
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.describe(RUN)


def test_open_reconfirms_inventory_and_returns_exact_bound_stream(tmp_path: Path) -> None:
    operations = Operations()
    source, _ = _source(tmp_path, operations)
    request = RunArtifactRequest(RUN, "adapter", len(operations.data))
    stream = source.open(request)
    assert stream.run == RUN
    assert stream.artifact == operations.artifact
    assert b"".join(stream.iter_bytes()) == operations.data
    assert operations.show_calls == 1
    assert operations.artifact_calls == 1


def test_open_rejects_role_limit_or_stream_binding_drift(tmp_path: Path) -> None:
    operations = Operations()
    source, _ = _source(tmp_path, operations)
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.open(RunArtifactRequest(RUN, "missing", 100))
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.open(RunArtifactRequest(RUN, "adapter", 1))

    operations.stream = Stream(
        TrainingRunRef("other", "project-1"), operations.artifact,
        len(operations.data), operations.data,
    )
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.open(RunArtifactRequest(RUN, "adapter", len(operations.data)))


def test_exact_runs_api_and_authority_types_are_required(tmp_path: Path) -> None:
    authority = create_publication_evidence_v1(_context(tmp_path))
    verifier, issuer = authority.verifier, authority.verified_sources

    class RunsSubclass(RunsAPI):
        pass

    with pytest.raises(TypeError, match="exact RunsAPI"):
        AuthenticatedVerifiedArtifactSourceV1(
            runs=RunsSubclass(Operations()), issuer=issuer, verifier=verifier
        )
    with pytest.raises(TypeError, match="exact RunsAPI"):
        AuthenticatedVerifiedArtifactSourceV1(
            runs=object(), issuer=issuer, verifier=verifier
        )


def test_artifact_change_alters_verification_and_source_identity(tmp_path: Path) -> None:
    first, _ = _source(tmp_path / "first", Operations(b"a"))
    second, _ = _source(tmp_path / "second", Operations(b"b"))
    first_value = first.describe(RUN)
    second_value = second.describe(RUN)
    assert first_value.verification_digest != second_value.verification_digest
    assert first_value.source_identity_digest != second_value.source_identity_digest


def test_runs_callback_exception_is_closed(tmp_path: Path) -> None:
    operations = Operations()

    def broken(run):
        raise RuntimeError("RAW PROVIDER SECRET")

    operations.show = broken
    source, _ = _source(tmp_path, operations)
    with pytest.raises(ValueError, match="^verified artifact source is invalid$") as error:
        source.describe(RUN)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_runs_api_operations_substitution_cannot_mint_source_evidence(tmp_path: Path) -> None:
    honest = Operations(b"honest")
    source, _ = _source(tmp_path, honest)
    source._runs._operations = Operations(b"evil")
    with pytest.raises(ValueError, match="^verified artifact source is invalid$") as error:
        source.describe(RUN)
    assert error.value.__cause__ is None
    assert error.value.__context__ is None


def test_source_anchor_is_not_redefined_by_module_global_replacement(
    tmp_path: Path, monkeypatch,
) -> None:
    source, _ = _source(tmp_path, Operations(b"honest"))
    monkeypatch.setattr(source_module, "_get_source_pin", lambda owner: None)
    source._runs._operations = Operations(b"evil")
    with pytest.raises(ValueError, match="verified artifact source is invalid"):
        source.describe(RUN)
