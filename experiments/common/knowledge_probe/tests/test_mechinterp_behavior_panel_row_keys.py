from __future__ import annotations

import json
import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import behavior_panel_row_keys as builder  # noqa: E402


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_behavior_panel_row_key_builder_respects_quotas_and_exclusions(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "PROBE_DIR", tmp_path)
    rows_path = tmp_path / "rows.jsonl"
    _write_jsonl(
        rows_path,
        [
            {"row_key": "kr1", "label": "known", "behavior_cell": "known_refused"},
            {"row_key": "kr2", "label": "known", "behavior_cell": "known_refused"},
            {"row_key": "kc1", "label": "known", "behavior_cell": "known_correct_answered"},
            {"row_key": "uw1", "label": "unknown", "behavior_cell": "unknown_refused"},
            {"row_key": "uw2", "label": "unknown", "behavior_cell": "unknown_refused"},
        ],
    )
    excluded_path = tmp_path / "excluded.txt"
    excluded_path.write_text("kr1\n", encoding="utf-8")
    config = {
        "purpose": "unit test",
        "inputs": {
            "rows": "rows.jsonl",
            "exclude_row_keys_sources": ["excluded.txt"],
        },
        "quotas": {
            "known_refused": 1,
            "known_correct_answered": 1,
            "unknown_refused": 2,
        },
        "output": {
            "row_keys_file": "out/keys.txt",
            "rows_jsonl": "out/rows.jsonl",
            "manifest": "out/manifest.json",
        },
    }

    selected, manifest = builder.select_rows(config)
    keys = [builder.row_key(row) for row in selected]

    assert keys == ["kr2", "kc1", "uw1", "uw2"]
    assert manifest["bucket_summaries"]["known_refused"] == {
        "available": 1,
        "selected": 1,
        "quota": 1,
    }
    assert manifest["selected_behavior_cell_counts"] == {
        "known_refused": 1,
        "known_correct_answered": 1,
        "unknown_refused": 2,
    }

    key_path, rows_out, manifest_path = builder.write_outputs(config, selected, manifest)
    assert key_path.read_text(encoding="utf-8").splitlines() == keys
    assert rows_out.exists()
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["total_selected"] == 4
