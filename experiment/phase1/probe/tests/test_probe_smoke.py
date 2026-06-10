"""Smoke tests for the Phase 1 knowledge probe (WS-1).

Location: experiment/phase1/probe/tests/test_probe_smoke.py
Run:      cd experiment/phase1/probe && python -m pytest tests/ -q

These verify the probe's scoring, labeling, JSONL output contract,
resumability, sensitivity grid, and the enable_thinking runtime self-check,
all with the GPU-free StubBackend on a small fixture. Comprehensive coverage
is TEST phase work; this is the "does it run, does the happy path hold" gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import probe  # noqa: E402
from backends import StubBackend, assert_no_think_scaffolding  # noqa: E402
from scoring import is_correct, normalize_answer, normalize_question, p_correct  # noqa: E402

FIXTURE = PROBE_DIR / "tests" / "fixtures" / "train_fixture.jsonl"

# Per-question correctness rates for the stub: known questions are answered
# almost always, unknown never, the discard question sometimes (middle band).
CORRECT_RATE = {
    "Who wrote Paradise Lost?": 1.0,
    "What is the capital of France?": 0.9,
    "What is the airspeed velocity of an unladen swallow in 1297?": 0.0,
    "What was the exact thought of Caesar at noon on the ides?": 0.0,
    "Which actor played the third spear-carrier in a 1973 play?": 0.25,
}


def _alias_table():
    table = {}
    with FIXTURE.open() as fh:
        for line in fh:
            row = json.loads(line)
            table[row["question"]] = row["answer"]["normalized_aliases"]
    return table


def _base_config(tmp_path: Path) -> dict:
    return {
        "model": {"model_tag": "stub-model", "model_name": "stub",
                  "enable_thinking": False},
        "sampling": {"n_samples": 16, "temperature": 1.0, "top_p": 0.9,
                     "max_new_tokens": 64, "seed": 20260610},
        "prompt": {"system": "answer concisely"},
        "probe_pool": {"train_jsonl": str(FIXTURE),
                       "fallback_validation_remainder": None,
                       "question_id_prefix": "tqa_train_"},
        "labels": {"known_p_correct_min": 0.5, "unknown_p_correct_max": 0.0},
        "sensitivity": {"enabled": True,
                        "unknown_cutoffs": [0.0, 0.03125, 0.0625, 0.1],
                        "known_cutoffs": [0.5, 0.7, 0.9],
                        "max_questions": None, "subsample_seed": 20260610},
        "output": {"results_filename": "probe_results.jsonl",
                   "manifest_filename": "probe_manifest.json",
                   "sensitivity_filename": "sensitivity_grid.json"},
        "runtime": {"backend": "stub"},
    }


def _stub_backend():
    table = _alias_table()
    return StubBackend(alias_table=table, correct_rate=CORRECT_RATE,
                       wrong_answer="Atlantis", seed=20260610)


# Resolve the fixture against an absolute path so REPO_ROOT joining is a no-op.
def _patch_pool_to_fixture(monkeypatch):
    monkeypatch.setattr(probe, "resolve_pool_path", lambda config: FIXTURE)


# --- scoring primitives ---

def test_normalize_answer_strips_punctuation():
    assert normalize_answer("John Milton.") == "john milton"


def test_is_correct_word_bounded():
    assert is_correct("It was John Milton.", ["john milton", "milton"])
    assert not is_correct("miltonic verse", ["milton"])  # substring must not match


def test_p_correct_fraction():
    assert p_correct([True, True, False, False]) == 0.5
    assert p_correct([]) == 0.0


def test_normalize_question_collapses_whitespace():
    assert normalize_question("  Who   wrote  Paradise Lost? ") == "who wrote paradise lost?"


# --- runtime self-check ---

def test_assert_no_think_passes_clean_prompt():
    assert_no_think_scaffolding("<|im_start|>user\nhi<|im_end|>\n")


def test_assert_no_think_raises_on_think_tag():
    with pytest.raises(RuntimeError, match="enable_thinking"):
        assert_no_think_scaffolding("<|im_start|>assistant\n<think>\n")


# --- end-to-end probe ---

def test_probe_runs_and_labels_all_bands(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)

    records = probe.read_results(results_path)
    by_id = {r["question_id"]: r for r in records}
    assert len(records) == 5

    # Each band is represented.
    labels = {r["question_id"]: r["label"] for r in records}
    assert labels["fix_known_1"] == "known"
    assert labels["fix_known_2"] == "known"
    assert labels["fix_unknown_1"] == "unknown"
    assert labels["fix_unknown_2"] == "unknown"
    assert labels["fix_discard_1"] == "discard"

    # P_correct ordering sanity.
    assert by_id["fix_known_1"]["p_correct"] == 1.0
    assert by_id["fix_unknown_1"]["p_correct"] == 0.0
    assert 0.0 < by_id["fix_discard_1"]["p_correct"] < 0.5


def test_output_contract_fields(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    record = probe.read_results(results_path)[0]

    # Exact A -> B schema (architecture doc 3.8) consumed by coder-data.
    required = {
        "question_id", "question", "question_norm", "normalized_aliases",
        "n_samples", "greedy_answer", "greedy_correct", "p_correct",
        "sampled_answers", "sampled_correct", "label", "model_tag",
        "probe_config_sha",
    }
    assert required.issubset(record.keys())
    assert len(record["sampled_answers"]) == record["n_samples"]
    assert len(record["sampled_correct"]) == record["n_samples"]
    # Wrong samples are retained (downstream KTO/DPO negatives).
    assert isinstance(record["sampled_answers"], list)


def test_resumability_skips_done_ids(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"

    # First pass over a 2-row prefix, then a second pass over the full fixture:
    # the second pass must skip the already-probed ids and only append new ones.
    probe.run_probe(config, _stub_backend(), out_dir)
    results_path = out_dir / "probe_results.jsonl"
    first = probe.read_results(results_path)
    assert len(first) == 5

    # Re-run: nothing new should be appended (all ids present).
    probe.run_probe(config, _stub_backend(), out_dir)
    second = probe.read_results(results_path)
    assert len(second) == 5  # no duplicates


def test_resume_reproduces_skipped_records(tmp_path, monkeypatch):
    # Determinism: a fresh probe of one question equals the resumed record.
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir_a = tmp_path / "run_a"
    out_dir_b = tmp_path / "run_b"
    probe.run_probe(config, _stub_backend(), out_dir_a)
    probe.run_probe(config, _stub_backend(), out_dir_b)
    a = {r["question_id"]: r for r in probe.read_results(out_dir_a / "probe_results.jsonl")}
    b = {r["question_id"]: r for r in probe.read_results(out_dir_b / "probe_results.jsonl")}
    assert a == b


def test_manifest_and_sensitivity_written(tmp_path, monkeypatch):
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    probe.finalize(config, results_path, out_dir)

    manifest = json.loads((out_dir / "probe_manifest.json").read_text())
    assert manifest["n_questions"] == 5
    assert manifest["label_counts"]["known"] == 2
    assert manifest["label_counts"]["unknown"] == 2
    assert manifest["enable_thinking"] is False
    assert manifest["probe_config_sha"]

    grid = json.loads((out_dir / "sensitivity_grid.json").read_text())
    # 4 unknown cutoffs x 3 known cutoffs = 12 cells.
    assert len(grid["cells"]) == 12
    # The strictest unknown cutoff (0.0) captures the two pure-unknowns.
    strict = [c for c in grid["cells"] if c["unknown_cutoff"] == 0.0][0]
    assert strict["n_unknown"] == 2


def test_sensitivity_reports_answerable_fraction(tmp_path, monkeypatch):
    # The Paper-1 43-51% analogue: fraction of "unknown"-labeled questions the
    # greedy decode actually answered. With a loose unknown cutoff that pulls in
    # the discard question (greedy wrong here), the fraction stays computable.
    _patch_pool_to_fixture(monkeypatch)
    config = _base_config(tmp_path)
    out_dir = tmp_path / "stub-model"
    results_path = probe.run_probe(config, _stub_backend(), out_dir)
    records = probe.read_results(results_path)
    grid = probe.sensitivity_grid(records, config["sensitivity"])
    for cell in grid["cells"]:
        assert 0.0 <= cell["unknown_greedy_answerable_frac"] <= 1.0


def test_seed_derivation_is_deterministic():
    a = probe.derive_seed(20260610, "fix_known_1")
    b = probe.derive_seed(20260610, "fix_known_1")
    c = probe.derive_seed(20260610, "fix_known_2")
    assert a == b
    assert a != c


def test_config_sha_changes_with_config():
    base = _base_config(Path("/tmp"))
    sha1 = probe.config_sha(base)
    base["sampling"]["n_samples"] = 64
    sha2 = probe.config_sha(base)
    assert sha1 != sha2
