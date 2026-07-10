from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import xdataset_behavior_from_generation as bg  # noqa: E402


def test_derive_cell_all_branches():
    assert bg.derive_behavior_cell("known", refused=True, correct=False) == bg.KNOWN_REFUSED
    assert bg.derive_behavior_cell("known", refused=False, correct=True) == bg.KNOWN_ANSWERED
    assert bg.derive_behavior_cell("known", refused=False, correct=False) == bg.KNOWN_WRONG
    assert bg.derive_behavior_cell("unknown", refused=True, correct=False) == bg.UNKNOWN_REFUSED
    assert bg.derive_behavior_cell("unknown", refused=False, correct=False) == bg.UNKNOWN_WRONG


def test_derive_cell_bad_label():
    with pytest.raises(bg.BehaviorAssemblyError):
        bg.derive_behavior_cell("maybe", refused=False, correct=False)


def _setup(tmp_path: Path):
    panel = tmp_path / "gen_rows.jsonl"
    panel.write_text("".join(json.dumps(r) + "\n" for r in [
        {"probe_pool_row_key": "kuq::kuq::000000::kuq-1", "label": "known",
         "question": "capital of France?", "aliases": ["Paris"]},
        {"probe_pool_row_key": "kuq::kuq::000001::kuq-2", "label": "known",
         "question": "2+2?", "aliases": ["4"]},
        {"probe_pool_row_key": "kuq::kuq::000002::kuq-3", "label": "unknown",
         "question": "are dogs better than cats?", "aliases": []},
    ]), encoding="utf-8")

    gen = tmp_path / "generation.jsonl"
    gen.write_text("".join(json.dumps(r) + "\n" for r in [
        # baseline records (kept)
        {"arm_id": "no_vector_baseline", "control": "no_vector_baseline", "alpha": 0.0,
         "probe_pool_row_key": "kuq::kuq::000000::kuq-1", "label": "known",
         "generated_answer": "{}", "refused": True, "correct": False},
        {"arm_id": "no_vector_baseline", "control": "no_vector_baseline", "alpha": 0.0,
         "probe_pool_row_key": "kuq::kuq::000001::kuq-2", "label": "known",
         "generated_answer": "{}", "refused": False, "correct": True},
        {"arm_id": "no_vector_baseline", "control": "no_vector_baseline", "alpha": 0.0,
         "probe_pool_row_key": "kuq::kuq::000002::kuq-3", "label": "unknown",
         "generated_answer": "{}", "refused": True, "correct": False},
        # a non-baseline arm record (must be ignored)
        {"arm_id": "per_head_iti_alpha_-4", "control": "per_head_iti", "alpha": -4.0,
         "probe_pool_row_key": "kuq::kuq::000000::kuq-1", "label": "known",
         "generated_answer": "{}", "refused": False, "correct": True},
    ]), encoding="utf-8")
    return gen, panel


def test_assemble_joins_and_derives(tmp_path):
    gen, panel = _setup(tmp_path)
    rows, summary = bg.assemble(gen, panel)
    assert summary["n_behavior_rows"] == 3
    assert summary["n_generation_baseline"] == 3  # the per_head arm dropped
    assert summary["n_known_refused"] == 1
    by_key = {r["probe_pool_row_key"]: r for r in rows}
    assert by_key["kuq::kuq::000000::kuq-1"]["behavior_cell"] == bg.KNOWN_REFUSED
    assert by_key["kuq::kuq::000000::kuq-1"]["question"] == "capital of France?"
    assert by_key["kuq::kuq::000001::kuq-2"]["behavior_cell"] == bg.KNOWN_ANSWERED
    assert by_key["kuq::kuq::000002::kuq-3"]["behavior_cell"] == bg.UNKNOWN_REFUSED


def test_run_writes_rows_and_summary(tmp_path):
    gen, panel = _setup(tmp_path)
    out = tmp_path / "behavior"
    summary = bg.run(gen, panel, out)
    written = [json.loads(l) for l in (out / "rows.jsonl").read_text().splitlines()]
    assert len(written) == 3
    for r in written:
        assert {"probe_pool_row_key", "label", "behavior_cell", "question"} <= set(r)


def test_assemble_requires_baseline_records(tmp_path):
    _, panel = _setup(tmp_path)
    gen = tmp_path / "only_steered.jsonl"
    gen.write_text(json.dumps({"arm_id": "per_head_iti_alpha_-4", "control": "per_head_iti",
                               "probe_pool_row_key": "kuq::kuq::000000::kuq-1", "label": "known",
                               "refused": False, "correct": True}) + "\n", encoding="utf-8")
    with pytest.raises(bg.BehaviorAssemblyError):
        bg.assemble(gen, panel)
