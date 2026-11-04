"""Regression checks for instrument-failure classification and frozen evidence."""
import dataclasses
import shutil

import pytest
import yaml

from conftest import EXPERIMENT, SLUG, git_commit_public, make_inputs, synthetic_drill
from hs20_nwe import adjudication as A, integrity, stages, weights
from hs20_nwe.budget import Ledger
from hs20_nwe.config import Cell, Layout
from hs20_nwe.util import HarnessError, sha256_file, write_json, write_jsonl


def test_only_budget_refusals_can_shrink_candidate_family(cell):
    result = weights.parse_validation(cell, {"success": False, "error": {"code": "budget", "message": "too large"}})
    assert not result.valid
    for code in ("base_hash_mismatch", "binding", "schema", "path", "payload", "index", "nonfinite"):
        with pytest.raises(HarnessError, match="INSTRUMENT_REFUSAL"):
            weights.parse_validation(cell, {"success": False, "error": {"code": code}})


def test_smoke_and_full_rows_are_distinct_in_shared_cap(project, cell):
    full, smoke = Layout(project.root, SLUG), Layout(project.root, SLUG, tag="kill")
    for layout, n in ((smoke, 12), (full, 64)):
        path = layout.local("runlog/decoy_baseline.jsonl")
        write_jsonl(path, [{"row_key": str(i)} for i in range(n)])
        Ledger(cell, layout).record_outputs("decoy_baseline", path)
    assert Ledger(cell, full).generated_rows() == 76
    Ledger(cell, smoke).record_outputs("decoy_baseline", smoke.local("runlog/decoy_baseline.jsonl"))
    assert Ledger(cell, full).generated_rows() == 76


def test_heldout_refuses_before_generation_without_export_proof(project, cell, monkeypatch):
    ctx = stages.Ctx(project.root, cell, Layout(project.root, SLUG), gpu_ack=True)
    monkeypatch.setattr(stages, "require_selected", lambda *a: {"winner": "selected"})
    with pytest.raises(HarnessError, match="EXPORT_PARITY"):
        stages.gen_heldout(ctx)
    assert not ctx.ledger.entries()


def test_private_logs_are_not_git_commitments(project, cell, tmp_path):
    from test_adjudication import cores, decoys, grade
    layout = Layout(project.root, SLUG)
    A.build_pool(cell, layout, cores(), decoys(), salt="test")
    A.commit_pool(layout)
    path = grade(layout, "shard_000", tmp_path)
    with pytest.raises(HarnessError, match="PUBLIC_NOT_IN_GIT"):
        A.commit_hash(layout, "shard_000", path)
    git_commit_public(layout, "adjudication_pool_manifest.json")
    A.commit_hash(layout, "shard_000", path)
    with pytest.raises(HarnessError, match="PUBLIC_NOT_IN_GIT"):
        A._require_graded_committed(A.Pool(layout), "shard_000", path)


def test_spot_acceptance_is_computed_and_cannot_be_overridden(project, cell):
    layout = Layout(project.root, SLUG)
    pack = [{"opaque_id": str(i), "grader_label": True} for i in range(30)]
    write_jsonl(A.Pool(layout).root / "spot_pack.private.jsonl", pack)
    decisions = [{"opaque_id": str(i), "lead_is_abstention": i < 27} for i in range(30)]
    write_json(__import__("hs20_nwe.commitments", fromlist=["public_path"]).public_path(layout, "run_binding.json"), {"fixture": True})
    assert A.record_spot_check(cell, layout, decisions)["accepted"]
    decisions[26]["lead_is_abstention"] = False
    with pytest.raises(HarnessError, match="SPOT_CHECK_FINAL"):
        A.record_spot_check(cell, layout, decisions)
    with pytest.raises(HarnessError, match="SPOT_CHECK_FINAL"):
        A.record_spot_check(cell, layout, decisions, accepted=True)
    report = A.apply(cell, layout, {}) if A.Pool(layout).manifest.exists() else None
    assert report is None


def test_self_attested_kill_marker_is_refused_and_journals_are_checked(project, cell):
    layout = Layout(project.root, SLUG)
    assert not integrity.verify_drill(cell, layout, {"passed": True})
    evidence = synthetic_drill(cell, layout)
    assert integrity.verify_drill(cell, layout, evidence)
    layout.to_local(evidence["drills"][0]["after_journal"]).write_text('{}\n')
    assert not integrity.verify_drill(cell, layout, evidence)


def test_binding_detects_source_threshold_model_and_population_drift(project, cell, monkeypatch):
    make_inputs(project, cell)
    directory = project.root / "experiments" / SLUG
    directory.mkdir(parents=True)
    for name in ("cell.yaml", "gates.yaml"):
        shutil.copy(EXPERIMENT / name, directory / name)
    shutil.copytree(EXPERIMENT / "hs20_nwe", directory / "hs20_nwe", ignore=shutil.ignore_patterns('__pycache__'))
    layout = Layout(project.root, SLUG)
    model = layout.local("base_model/synthetic.safetensors")
    model.parent.mkdir(parents=True)
    model.write_bytes(b'synthetic checkpoint')
    document = yaml.safe_load((directory / "cell.yaml").read_text())
    document["model"]["files_sha256"] = {model.name: sha256_file(model)}
    (directory / "cell.yaml").write_text(yaml.safe_dump(document))
    cell = Cell.load(directory)
    (directory / "experiment.yaml").write_text(yaml.safe_dump({"instrument": {"runtime_image_digest": "sha256:fixture"}}))
    monkeypatch.setenv("EHR_RUNTIME_IMAGE_DIGEST", "sha256:fixture")
    write_json(layout.local("runtime_attestation.json"), {"derived_image": "sha256:fixture", "base_layers_verified": True})
    monkeypatch.setattr("engine_host.engine_identity.inspect_engine", lambda root: {"wheel_sha256": cell.cell["engine"]["wheel_sha256"]})
    ctx = stages.Ctx(project.root, cell, layout)
    stages.materialize(ctx, layout.local("inputs"))
    integrity.bind(cell, layout)
    with pytest.raises(HarnessError, match="PUBLIC_NOT_IN_GIT"):
        integrity.verify(cell, layout)
    git_commit_public(layout, "run_binding.json")
    assert integrity.verify(cell, layout, full_model=True)["passed"]
    for path in (directory / "hs20_nwe/selection.py", model, layout.local("materialize/fit_l.jsonl")):
        original = path.read_bytes()
        path.write_bytes(original + b' ')
        assert not integrity.report(cell, layout)["passed"]
        path.write_bytes(original)
    changed = dataclasses.replace(cell, cell_sha256="changed")
    assert not integrity.report(changed, layout)["passed"]


def test_pipeline_gpu_ack_is_a_global_argument(project, cell):
    from hs20_nwe.pipeline import build
    for stage in build(cell, Layout(project.root, SLUG))["stages"]:
        command = stage["command"]
        if "--gpu-ack" in command:
            assert command.index("--gpu-ack") < command.index("stage")


def test_unsigned_scored_run_is_refused(project, cell, monkeypatch):
    monkeypatch.setattr(integrity, "verify", lambda *a: {"passed": True})
    ctx = stages.Ctx(project.root, cell, Layout(project.root, SLUG))
    monkeypatch.setattr(stages, "_evidence", lambda ctx: {})
    monkeypatch.setattr(stages.yaml, "safe_load", lambda text: {"status": "draft"})
    with pytest.raises(HarnessError, match="RUN_ADMISSION"):
        stages.require_run_admission(ctx)


def test_baseline_cannot_run_directly_before_sign(project, cell, monkeypatch):
    monkeypatch.setattr(integrity, "verify", lambda *a: {"passed": True})
    ctx = stages.Ctx(project.root, cell, Layout(project.root, SLUG))
    monkeypatch.setattr(stages, "_evidence", lambda ctx: {})
    monkeypatch.setattr(stages.yaml, "safe_load", lambda text: {"status": "draft"})
    with pytest.raises(HarnessError, match="RUN_ADMISSION"):
        stages.gen_static(ctx)


def test_drill_evidence_cannot_cross_bindings_or_choose_its_own_count(project, cell):
    from hs20_nwe.commitments import public_path
    layout = Layout(project.root, SLUG)
    evidence = synthetic_drill(cell, layout)
    assert integrity.verify_drill(cell, layout, evidence)
    evidence["drills"][0]["expected_rows"] += 1
    assert not integrity.verify_drill(cell, layout, evidence)
    evidence["drills"][0]["expected_rows"] -= 1
    write_json(public_path(layout, "run_binding.json"), {"changed": True})
    assert not integrity.verify_drill(cell, layout, evidence)
