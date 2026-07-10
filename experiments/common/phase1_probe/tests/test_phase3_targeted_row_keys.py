from __future__ import annotations

import json
import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_targeted_row_keys as trk  # noqa: E402


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_targeted_row_key_selector_respects_quotas_and_exclusions(tmp_path, monkeypatch):
    monkeypatch.setattr(trk, "PROBE_DIR", tmp_path)
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({
        "known_question_keys": ["known_low", "known_high", "known_excluded"],
        "unknown_question_keys": ["unknown_wrong", "unknown_refusal"],
    }), encoding="utf-8")
    results = tmp_path / "probe_results.jsonl"
    _write_jsonl(results, [
        {
            "probe_pool_row_key": "known_low",
            "label": "known",
            "question": "known low?",
            "greedy_answer": "I do not know.",
            "greedy_correct": True,
            "p_correct": 0.75,
            "probe_config_sha": "sha",
        },
        {
            "probe_pool_row_key": "known_high",
            "label": "known",
            "question": "known high?",
            "greedy_answer": "A correct answer.",
            "greedy_correct": True,
            "p_correct": 1.0,
            "probe_config_sha": "sha",
        },
        {
            "probe_pool_row_key": "known_excluded",
            "label": "known",
            "question": "excluded?",
            "greedy_answer": "I do not know.",
            "greedy_correct": True,
            "p_correct": 0.5,
            "probe_config_sha": "sha",
        },
        {
            "probe_pool_row_key": "unknown_wrong",
            "label": "unknown",
            "question": "unknown wrong?",
            "greedy_answer": "A fabricated answer.",
            "greedy_correct": False,
            "p_correct": 0.0,
            "probe_config_sha": "sha",
        },
        {
            "probe_pool_row_key": "unknown_refusal",
            "label": "unknown",
            "question": "unknown refusal?",
            "greedy_answer": "There is no definitive record.",
            "greedy_correct": False,
            "p_correct": 0.0,
            "probe_config_sha": "sha",
        },
    ])
    excluded = tmp_path / "excluded.txt"
    excluded.write_text("known_excluded\n", encoding="utf-8")
    config = {
        "purpose": "unit test",
        "inputs": {
            "questions_frozen": "frozen.json",
            "probe_results": "probe_results.jsonl",
            "expected_probe_config_sha": "sha",
            "exclude_row_keys_sources": ["excluded.txt"],
        },
        "sampling": {"seed": 1},
        "quotas": {
            "known_low_confidence_or_refusal": 2,
            "known_high_confidence_correct": 1,
            "unknown_answered_wrong_like": 1,
            "unknown_refusal_like": 1,
        },
        "output": {
            "row_keys_file": "out/keys.txt",
            "rows_jsonl": "out/rows.jsonl",
            "manifest": "out/manifest.json",
        },
    }

    rows, manifest = trk.select_rows(config)
    keys = [row["probe_pool_row_key"] for row in rows]

    assert keys == ["known_low", "known_high", "unknown_wrong", "unknown_refusal"]
    assert manifest["bucket_summaries"]["known_low_confidence_or_refusal"] == {
        "available": 1,
        "selected": 1,
        "quota": 2,
    }
    assert manifest["selected_label_counts"] == {"known": 2, "unknown": 2}

    key_path, rows_path, manifest_path = trk.write_outputs(config, rows, manifest)
    assert key_path.read_text(encoding="utf-8").splitlines() == keys
    assert rows_path.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["total_selected"] == 4
