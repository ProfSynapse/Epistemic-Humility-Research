from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import head_intervention_sign_curve as sc  # noqa: E402


def test_alpha_parsing():
    assert sc.alpha_of("no_vector_baseline") == 0.0
    assert sc.alpha_of("per_head_iti_alpha_+4") == 4.0
    assert sc.alpha_of("per_head_iti_alpha_-8") == -8.0


def _metrics(curve: dict[float, float]) -> dict:
    out = {}
    for alpha, refusal in curve.items():
        arm = "no_vector_baseline" if alpha == 0 else f"per_head_iti_alpha_{alpha:+g}"
        out[arm] = {"unknown_refusal_rate": refusal, "over_refusal_on_known": refusal - 5}
    return out


def test_directional_monotone():
    # The real A.4 shape: -F lowers refusal, +F raises it.
    m = _metrics({-8: 40.6, -4: 48.4, -2: 48.4, 0: 52.3, 4: 82.8})
    pts = sc.curve(m, refusal_metric="unknown_refusal_rate")
    res = sc.classify(pts)
    assert res["classification"] == "directional"
    assert "INVERTED" in res["verdict"]


def test_ood_collapse_u_shape():
    # Both extremes above baseline -> safe-default collapse.
    m = _metrics({-8: 70.0, -4: 60.0, 0: 50.0, 4: 62.0, 8: 72.0})
    res = sc.classify(sc.curve(m, refusal_metric="unknown_refusal_rate"))
    assert res["classification"] == "ood_collapse"


def test_run_on_summary(tmp_path):
    summary = {"metrics_by_arm": _metrics({-4: 45.0, 0: 50.0, 4: 80.0})}
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(summary), encoding="utf-8")
    res = sc.run(path)
    assert res["classification"] == "directional"
    assert [p["alpha"] for p in res["curve"]] == [-4.0, 0.0, 4.0]
