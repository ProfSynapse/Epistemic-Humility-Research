from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_xdataset_build_panel as bp  # noqa: E402


def _write_source(tmp_path: Path) -> Path:
    rows = []
    for i in range(10):
        rows.append({"question": f"known q {i}?", "unknown": False, "answer": [f"a{i}", f"b{i}"]})
    for i in range(8):
        rows.append({"question": f"unknown q {i}?", "unknown": True, "answer": None})
    p = tmp_path / "src.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return p


def test_load_source_labels_and_aliases(tmp_path):
    src = _write_source(tmp_path)
    rows = bp.load_source(src, question_field="question", unknown_field="unknown",
                          answer_field="answer")
    assert len(rows) == 18
    known = [r for r in rows if r["label"] == "known"]
    unknown = [r for r in rows if r["label"] == "unknown"]
    assert len(known) == 10 and len(unknown) == 8
    assert known[0]["aliases"] == ["a0", "b0"]
    assert unknown[0]["aliases"] == []


def test_balanced_subsample_deterministic(tmp_path):
    src = _write_source(tmp_path)
    rows = bp.load_source(src, question_field="question", unknown_field="unknown",
                          answer_field="answer")
    a = bp.balanced_subsample(rows, n_known=5, n_unknown=4, seed=7)
    b = bp.balanced_subsample(rows, n_known=5, n_unknown=4, seed=7)
    assert [r["question"] for r in a] == [r["question"] for r in b]
    assert sum(r["label"] == "known" for r in a) == 5
    assert sum(r["label"] == "unknown" for r in a) == 4


def test_balanced_subsample_overrequest_raises(tmp_path):
    src = _write_source(tmp_path)
    rows = bp.load_source(src, question_field="question", unknown_field="unknown",
                          answer_field="answer")
    with pytest.raises(bp.PanelBuildError):
        bp.balanced_subsample(rows, n_known=99, n_unknown=4, seed=0)


def test_run_emits_joinable_artifacts(tmp_path):
    src = _write_source(tmp_path)
    out = tmp_path / "panel"
    meta = bp.run(src, out, dataset="kuq", n_known=5, n_unknown=4, seed=0)
    assert meta["row_count"] == 9

    gen = [json.loads(l) for l in (out / "gen_rows.jsonl").read_text().splitlines()]
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["schema_version"] == bp.SCHEMA_VERSION
    assert manifest["scope"]["not_probe_pool_runner_ready"] is True
    assert manifest["row_count"] == 9

    gen_keys = {r["probe_pool_row_key"] for r in gen}
    man_keys = {r["row_key"] for r in manifest["rows"]}
    assert gen_keys == man_keys  # same row_key universe → joinable
    assert all(k.startswith("kuq::kuq::") for k in gen_keys)

    for r in manifest["rows"]:
        assert r["prompt"] == r["question"]
        assert r["strata"] and all(isinstance(s, str) and s for s in r["strata"])
        assert isinstance(r["stable_identity"], dict)
        assert r["label"] in {"known", "unknown"}


def test_manifest_matches_converter_contract(tmp_path):
    """Manifest rows must carry every field hs_selection.convert_selfaware_manifest_row needs."""
    src = _write_source(tmp_path)
    out = tmp_path / "panel"
    bp.run(src, out, dataset="kuq", n_known=5, n_unknown=4, seed=0)
    manifest = json.loads((out / "manifest.json").read_text())
    required = ["row_key", "stable_identity", "strata", "label", "question", "prompt"]
    for r in manifest["rows"]:
        for f in required:
            assert f in r, f"missing {f}"
