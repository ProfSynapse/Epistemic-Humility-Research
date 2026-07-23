from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import head_read_sign_consistency as rsc  # noqa: E402


def _row(label, refused, correct, reads):
    return {"label": label, "refused": refused, "correct": correct,
            "prompt_read_per_head": reads}


def test_group_of():
    assert rsc.group_of(_row("unknown", True, False, {})) == "refused"
    assert rsc.group_of(_row("unknown", False, False, {})) == "answered_wrong"
    assert rsc.group_of(_row("unknown", False, True, {})) is None  # answered-correct excluded
    assert rsc.group_of(_row("known", False, False, {})) is None


def test_unanimous():
    rows = []
    for _ in range(5):
        rows.append(_row("unknown", False, False, {"L1H1": 2.0, "L2H2": 1.0}))  # wrong reads high
        rows.append(_row("unknown", True, False, {"L1H1": 0.0, "L2H2": 0.0}))  # refuse reads low
    res = rsc.run_from_rows(rows)
    assert res["classification"] == "unanimous"
    assert res["detail"]["n_pos"] == 2 and res["detail"]["n_neg"] == 0
    assert all(h["sign"] == "+" for h in res["per_head"])


def test_split():
    rows = []
    for _ in range(5):
        rows.append(_row("unknown", False, False, {"L1H1": 2.0, "L2H2": 0.0}))
        rows.append(_row("unknown", True, False, {"L1H1": 0.0, "L2H2": 2.0}))  # head2 inverted
    res = rsc.run_from_rows(rows)
    assert res["classification"] == "split"
    assert res["detail"]["n_pos"] == 1 and res["detail"]["n_neg"] == 1


def test_run_roundtrip(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for _ in range(3):
            fh.write(json.dumps(_row("unknown", False, False, {"L1H1": 3.0})) + "\n")
            fh.write(json.dumps(_row("unknown", True, False, {"L1H1": 1.0})) + "\n")
    res = rsc.run(rows_path)
    assert res["classification"] == "unanimous"
    assert res["n_answered_wrong"] == 3 and res["n_refused"] == 3


def test_needs_both_groups():
    rows = [_row("unknown", False, False, {"L1H1": 1.0}) for _ in range(3)]
    with pytest.raises(rsc.ReadSignError):
        rsc.run_from_rows(rows)
