from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import knowledge_boundary_steer_readout as ks  # noqa: E402


def test_parse_confidence():
    assert ks.parse_confidence('{"answer": "x", "response_confidence": 0.81}') == pytest.approx(0.81)
    assert ks.parse_confidence('garbage "response_confidence": 0.4 trailing') == pytest.approx(0.4)
    assert ks.parse_confidence("no json here") is None
    assert ks.parse_confidence("") is None


def _row(alpha, label, refused, conf):
    ans = json.dumps({"answer": "I don't know the answer" if refused else "Paris",
                      "response_confidence": conf})
    return {"alpha": alpha, "label": label, "refused": refused, "generated_answer": ans}


def test_belief_monitor_signature():
    # Toward "known" (alpha<0): unknowns answered (low refusal), conf high.
    # Toward "unknown" (alpha>0): knowns abstained (high refusal), conf low.
    rows = []
    for _ in range(10):
        rows += [_row(-6, "unknown", False, 0.9), _row(-6, "known", False, 0.9)]
        rows += [_row(0, "unknown", True, 0.5), _row(0, "known", False, 0.7)]
        rows += [_row(6, "unknown", True, 0.3), _row(6, "known", True, 0.3)]
    res = ks.run_from_rows(rows)
    assert res["classification"] == "belief_monitor"


def test_anti_steer_inconsistent():
    # Belief-INCONSISTENT: toward "unknown" (alpha>0) refusal FALLS and confidence
    # RISES -- the wrong way for a knowledge dial (F-like anti-steer).
    rows = []
    for _ in range(10):
        rows += [_row(-6, "unknown", True, 0.3), _row(-6, "known", True, 0.3)]
        rows += [_row(0, "unknown", True, 0.5), _row(0, "known", False, 0.6)]
        rows += [_row(6, "unknown", False, 0.9), _row(6, "known", False, 0.9)]
    res = ks.run_from_rows(rows)
    assert res["classification"] == "anti_steer"


def test_inert():
    rows = []
    for _ in range(10):
        for a in (-6, 0, 6):
            rows += [_row(a, "unknown", True, 0.5), _row(a, "known", False, 0.5)]
    res = ks.run_from_rows(rows)
    assert res["classification"] == "inert"


def test_run_roundtrip(tmp_path):
    rows = []
    for _ in range(4):
        rows += [_row(-6, "unknown", False, 0.9), _row(6, "known", True, 0.3),
                 _row(0, "unknown", True, 0.5), _row(0, "known", False, 0.7)]
    p = tmp_path / "rows.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    res = ks.run(p)
    assert res["n_rows"] == len(rows)
    assert any(c["label"] == "unknown" for c in res["cells"])
