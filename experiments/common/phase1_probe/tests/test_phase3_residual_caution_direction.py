from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import phase3_residual_caution_direction as rcd  # noqa: E402
import phase3_residual_read_trajectory as rrt  # noqa: E402


def _write_rows(path: Path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def test_load_known_split_partitions_by_cell(tmp_path):
    rows = [
        {"probe_pool_row_key": "k1", "label": "known", "behavior_cell": rrt.KNOWN_REFUSED},
        {"probe_pool_row_key": "k2", "label": "known", "behavior_cell": rrt.KNOWN_ANSWERED},
        {"probe_pool_row_key": "k3", "label": "known", "behavior_cell": "known_answered_wrong"},
        {"probe_pool_row_key": "u1", "label": "unknown", "behavior_cell": "unknown_refused"},
    ]
    p = tmp_path / "rows.jsonl"
    _write_rows(p, rows)
    refused, answered = rcd.load_known_split(p)
    assert refused == ["k1"]
    assert answered == ["k2"]  # known_answered_wrong excluded; unknown excluded


def test_load_known_split_degenerate_raises(tmp_path):
    rows = [{"probe_pool_row_key": "k1", "label": "known", "behavior_cell": rrt.KNOWN_REFUSED}]
    p = tmp_path / "rows.jsonl"
    _write_rows(p, rows)
    with pytest.raises(rrt.ResidualReadTrajectoryError):
        rcd.load_known_split(p)
