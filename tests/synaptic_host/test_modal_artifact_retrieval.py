import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

import pytest

from synaptic_tuner.api.v1 import (
    RunOutcome, RunVerification, RunsAPI, TrainingRunRef, TrainingRunState,
    VerifiedArtifact,
)

from synaptic_host import modal_artifact_retrieval
from synaptic_host.modal_artifact_retrieval import retrieve_verified_artifacts


RUN = TrainingRunRef("run-" + "a" * 32, "project-one")
PLAN = "b" * 64
ROLES = (
    "workload_record", "training_lineage", "training_metrics", "final_model", "tokenizer",
)
NAMES = (
    "workload-record.json", "training-lineage.json", "training-metrics.json",
    "final-model.bin", "tokenizer.bin",
)


@dataclass
class Stream:
    run: TrainingRunRef
    artifact: VerifiedArtifact
    maximum_bytes: int
    chunks: object

    def iter_bytes(self):
        return iter(self.chunks)


class Operations:
    def __init__(self, payloads=None):
        self.payloads = payloads or {role: (role + "\n").encode() for role in ROLES}
        self.inventory = tuple(
            VerifiedArtifact(role, hashlib.sha256(data).hexdigest(), len(data))
            for role, data in self.payloads.items()
        )
        self.show_count = 0
        self.stream_factory = lambda request, artifact: Stream(
            request.run, artifact, request.maximum_bytes, [self.payloads[request.role]],
        )

    def show(self, run):
        self.show_count += 1
        return RunOutcome("synaptic-run-outcome/v1", run, TrainingRunState.SUCCEEDED, self.inventory)

    def reverify(self, run):
        return RunVerification(run, True, "2026-09-09T00:00:00Z")

    def artifacts(self, request):
        artifact = next(item for item in self.inventory if item.role == request.role)
        return self.stream_factory(request, artifact)


def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / ".synaptic").mkdir(mode=0o700)
    return root


def target(root: Path) -> Path:
    return root / ".synaptic" / "retrievals" / RUN.run_id


def test_success_writes_exact_private_inventory_and_receipt(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    result = retrieve_verified_artifacts(
        project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
    )
    output = target(root)
    assert result["retrieval_root_ref"] == f"host-private://retrievals/{RUN.run_id}"
    assert result["artifact_count"] == 5
    assert result["model_load_verified"] is False
    assert sorted(path.name for path in output.iterdir()) == sorted((*NAMES, "receipt.json"))
    for role, name in zip(ROLES, NAMES):
        path = output / name
        assert path.read_bytes() == operations.payloads[role]
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert path.stat().st_nlink == 1
    receipt = json.loads((output / "receipt.json").read_text("ascii"))
    assert receipt["plan_fingerprint"] == PLAN
    assert receipt["inventory_digest"] == result["inventory_digest"]
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert operations.show_count == 2


@pytest.mark.parametrize(
    "bad", [None, b"", "text", b"x" * (1024 * 1024 + 1)],
    ids=("none", "empty", "nonbytes", "oversize"),
)
def test_hostile_stream_chunk_retains_partial_without_receipt(tmp_path: Path, bad) -> None:
    root = project(tmp_path)
    operations = Operations()
    operations.stream_factory = lambda request, artifact: Stream(
        request.run, artifact, request.maximum_bytes, [bad],
    )
    with pytest.raises((TypeError, ValueError)):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert target(root).is_dir()
    assert not (target(root) / "receipt.json").exists()


def test_content_mismatch_has_no_receipt(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    operations.stream_factory = lambda request, artifact: Stream(
        request.run, artifact, request.maximum_bytes, [b"wrong"],
    )
    with pytest.raises(ValueError):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()


def test_inventory_drift_after_download_has_no_receipt(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    original = operations.show

    def show(run):
        value = original(run)
        if operations.show_count == 2:
            changed = list(value.artifacts)
            first = changed[0]
            changed[0] = VerifiedArtifact(first.role, "c" * 64, first.size_bytes)
            return RunOutcome(value.schema_version, run, value.state, tuple(changed))
        return value

    operations.show = show
    with pytest.raises(ValueError):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()


def test_unverified_or_nonterminal_run_creates_nothing(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    operations.reverify = lambda run: RunVerification(run, False, "2026-09-09T00:00:00Z")
    with pytest.raises(ValueError):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not target(root).exists()


def test_existing_output_refuses_without_changing_bytes(tmp_path: Path) -> None:
    root = project(tmp_path)
    output = target(root)
    output.mkdir(parents=True, mode=0o700)
    output.parent.chmod(0o700)
    marker = output / "marker"
    marker.write_bytes(b"keep")
    before = marker.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(Operations()), run=RUN, plan_fingerprint=PLAN,
        )
    assert marker.read_bytes() == before


@pytest.mark.parametrize("leaf", ["retrievals", RUN.run_id])
def test_symlink_storage_is_refused(tmp_path: Path, leaf: str) -> None:
    root = project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    retrievals = root / ".synaptic" / "retrievals"
    if leaf == "retrievals":
        retrievals.symlink_to(outside, target_is_directory=True)
    else:
        retrievals.mkdir(mode=0o700)
        (retrievals / RUN.run_id).symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(Operations()), run=RUN, plan_fingerprint=PLAN,
        )
    assert list(outside.iterdir()) == []


def test_hardlink_substitution_during_stream_is_detected_without_receipt(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()

    def chunks():
        path = target(root) / NAMES[0]
        os.link(path, tmp_path / "stolen-link")
        yield operations.payloads[ROLES[0]]

    first = True
    def factory(request, artifact):
        nonlocal first
        value = chunks() if first else [operations.payloads[request.role]]
        first = False
        return Stream(request.run, artifact, request.maximum_bytes, value)

    operations.stream_factory = factory
    with pytest.raises(ValueError, match="identity changed"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()


def test_oversize_authenticated_inventory_creates_nothing(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    operations.inventory = (
        VerifiedArtifact(ROLES[0], "d" * 64, 64 * 1024 * 1024 + 1),
        *operations.inventory[1:],
    )
    with pytest.raises(ValueError, match="exceeds bounds"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not target(root).exists()


def test_run_directory_substitution_is_detected_without_receipt(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    first = True

    def factory(request, artifact):
        nonlocal first
        if first:
            first = False
            original = target(root)
            moved = original.with_name(original.name + ".moved")
            original.rename(moved)
            original.mkdir(mode=0o700)
        return Stream(request.run, artifact, request.maximum_bytes, [operations.payloads[request.role]])

    operations.stream_factory = factory
    with pytest.raises(ValueError, match="identity changed"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()
    assert not (target(root).with_name(target(root).name + ".moved") / "receipt.json").exists()


def test_failed_receipt_write_leaves_no_named_receipt(tmp_path: Path, monkeypatch) -> None:
    root = project(tmp_path)
    real_write = os.write

    def write(fd, value):
        if os.fstat(fd).st_nlink == 0:
            raise OSError("injected receipt failure")
        return real_write(fd, value)

    monkeypatch.setattr(modal_artifact_retrieval.os, "write", write)
    with pytest.raises(OSError, match="injected"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(Operations()), run=RUN, plan_fingerprint=PLAN,
        )
    assert target(root).is_dir()
    assert not (target(root) / "receipt.json").exists()


def test_last_stream_mutating_first_file_is_caught_by_final_reread(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()

    def factory(request, artifact):
        def chunks():
            if request.role == ROLES[-1]:
                with (target(root) / NAMES[0]).open("ab") as handle:
                    handle.write(b"hostile append")
            yield operations.payloads[request.role]
        return Stream(request.run, artifact, request.maximum_bytes, chunks())

    operations.stream_factory = factory
    with pytest.raises(ValueError):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()


def test_missing_otmpfile_support_refuses_before_artifact_streams(tmp_path: Path, monkeypatch) -> None:
    root = project(tmp_path)
    operations = Operations()
    operations.stream_factory = lambda *_args: (_ for _ in ()).throw(
        AssertionError("artifact stream reached")
    )
    real_open = os.open

    def opened(path, flags, *args, **kwargs):
        if flags & os.O_TMPFILE == os.O_TMPFILE:
            raise OSError("unsupported")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(modal_artifact_retrieval.os, "open", opened)
    with pytest.raises(ValueError, match="atomic receipt storage"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert target(root).is_dir()
    assert list(target(root).iterdir()) == []


def test_project_root_substitution_is_detected(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    original_factory = operations.stream_factory
    first = True

    def factory(request, artifact):
        nonlocal first
        if first:
            first = False
            moved = root.with_name("original-project")
            root.rename(moved)
            root.mkdir()
        return original_factory(request, artifact)

    operations.stream_factory = factory
    with pytest.raises(ValueError, match="project root identity changed"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )


def test_private_directory_mode_drift_is_detected_without_receipt(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    original_factory = operations.stream_factory
    first = True

    def factory(request, artifact):
        nonlocal first
        if first:
            first = False
            (root / ".synaptic" / "retrievals").chmod(0o755)
        return original_factory(request, artifact)

    operations.stream_factory = factory
    with pytest.raises(ValueError, match="not private"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()


def test_extra_local_file_before_receipt_is_refused(tmp_path: Path) -> None:
    root = project(tmp_path)
    operations = Operations()
    original_factory = operations.stream_factory

    def factory(request, artifact):
        def chunks():
            if request.role == ROLES[-1]:
                extra = target(root) / "unverified-extra"
                extra.write_bytes(b"x")
                extra.chmod(0o600)
            yield operations.payloads[request.role]
        return Stream(request.run, artifact, request.maximum_bytes, chunks())

    operations.stream_factory = factory
    with pytest.raises(ValueError, match="inventory changed"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(operations), run=RUN, plan_fingerprint=PLAN,
        )
    assert not (target(root) / "receipt.json").exists()


def test_post_link_fsync_failure_never_returns_success_but_marker_is_complete(
    tmp_path: Path, monkeypatch,
) -> None:
    root = project(tmp_path)
    real_fsync = os.fsync

    def fsync(fd):
        receipt = target(root) / "receipt.json"
        if receipt.exists() and stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("injected directory fsync failure")
        return real_fsync(fd)

    monkeypatch.setattr(modal_artifact_retrieval.os, "fsync", fsync)
    with pytest.raises(OSError, match="injected directory"):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(Operations()), run=RUN, plan_fingerprint=PLAN,
        )
    receipt = target(root) / "receipt.json"
    assert receipt.is_file()
    assert json.loads(receipt.read_text("ascii"))["artifact_count"] == 5


@pytest.mark.parametrize("attack", ("replacement", "symlink", "hardlink", "extra"))
def test_post_publication_receipt_namespace_attacks_refuse_success(
    tmp_path: Path, monkeypatch, attack: str,
) -> None:
    root = project(tmp_path)
    real_fsync = os.fsync
    attacked = False

    def fsync(fd):
        nonlocal attacked
        receipt = target(root) / "receipt.json"
        if not attacked and receipt.exists() and stat.S_ISDIR(os.fstat(fd).st_mode):
            attacked = True
            if attack == "replacement":
                receipt.unlink()
                receipt.write_bytes(b"{}\n")
                receipt.chmod(0o600)
            elif attack == "symlink":
                outside = tmp_path / "outside-receipt"
                outside.write_bytes(b"{}\n")
                outside.chmod(0o600)
                receipt.unlink()
                receipt.symlink_to(outside)
            elif attack == "hardlink":
                os.link(receipt, tmp_path / "receipt-hardlink")
            else:
                extra = target(root) / "extra-after-receipt"
                extra.write_bytes(b"x")
                extra.chmod(0o600)
        return real_fsync(fd)

    monkeypatch.setattr(modal_artifact_retrieval.os, "fsync", fsync)
    with pytest.raises((OSError, ValueError)):
        retrieve_verified_artifacts(
            project_root=root, runs=RunsAPI(Operations()), run=RUN,
            plan_fingerprint=PLAN,
        )
    assert attacked is True
