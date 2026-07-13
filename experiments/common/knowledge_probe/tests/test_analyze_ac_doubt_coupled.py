from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import analyze_ac_doubt_coupled as ac  # noqa: E402

KR, KA, UR = ac.KR, ac.KA, ac.UR


def _write_rows(path: Path, spec):
    """spec: list of (cell, key, {arm: (refused, correct)})."""
    with path.open("w", encoding="utf-8") as f:
        for cell, key, arms in spec:
            for arm, (refused, correct) in arms.items():
                f.write(json.dumps({
                    "probe_pool_row_key": key, "arm_id": arm,
                    "behavior_cell": cell, "refused": refused,
                    "correct": correct}) + "\n")


def _uniform_arms(refused_by_arm):
    return {arm: (refused, False) for arm, refused in refused_by_arm.items()}


def _make_dataset(tmp_path, kr_derefusal, ur_derefusal, n=20):
    """Baseline refuses everything in kr/ur; interventional arms de-refuse the
    first round(rate*n) rows per cell. KA: everyone answers correctly."""
    spec = []
    for cell, de in ((KR, kr_derefusal), (UR, ur_derefusal)):
        for i in range(n):
            arms = {"baseline": (True, False)}
            for arm in ac.INTERVENTIONAL:
                arms[arm] = (i >= round(de[arm] * n), False)
            spec.append((cell, f"{cell}::{i}", arms))
    for i in range(n):
        spec.append((KA, f"{KA}::{i}",
                     {arm: (False, True) for arm in ac.ARMS}))
    rows = tmp_path / "rows.jsonl"
    _write_rows(rows, spec)
    gain_map = tmp_path / "gains.json"
    gains = {f"{cell}::{i}": {"cell": cell, "z": 0.0, "gain": -1.0}
             for cell in (KR, KA, UR) for i in range(n)}
    gain_map.write_text(json.dumps({"gains": gains}), encoding="utf-8")
    return rows, gain_map


def test_selectivity_gap_math(tmp_path):
    rows, gains = _make_dataset(
        tmp_path,
        kr_derefusal={"coupled": 0.5, "permuted": 0.2, "ablate": 0.4},
        ur_derefusal={"coupled": 0.1, "permuted": 0.2, "ablate": 0.4})
    out = ac.analyze(rows, gains, n_boot=200, seed=1)
    g = out["selectivity_gaps"]
    assert g["coupled"] == pytest.approx(0.4)
    assert g["permuted"] == pytest.approx(0.0)
    assert g["ablate"] == pytest.approx(0.0)
    assert out["ac_g1"]["margin"] == pytest.approx(0.4)


def test_g1_pass_and_falsifier_flag(tmp_path):
    rows, gains = _make_dataset(
        tmp_path,
        kr_derefusal={"coupled": 1.0, "permuted": 0.0, "ablate": 0.0},
        ur_derefusal={"coupled": 0.0, "permuted": 0.0, "ablate": 0.0})
    out = ac.analyze(rows, gains, n_boot=500, seed=1)
    assert out["ac_g1"]["pass"] is True
    assert out["falsifier_fired"] is False

    (tmp_path / "flat").mkdir(exist_ok=True)
    rows2, gains2 = _make_dataset(
        tmp_path / "flat",
        kr_derefusal={"coupled": 0.3, "permuted": 0.3, "ablate": 0.3},
        ur_derefusal={"coupled": 0.3, "permuted": 0.3, "ablate": 0.3})
    out2 = ac.analyze(rows2, gains2, n_boot=500, seed=1)
    assert out2["ac_g1"]["margin"] == pytest.approx(0.0)
    assert out2["ac_g1"]["pass"] is False
    assert out2["falsifier_fired"] is True


def test_specificity_guard_fails_on_ka_refusal_rise(tmp_path):
    rows, gains = _make_dataset(
        tmp_path,
        kr_derefusal={"coupled": 0.5, "permuted": 0.0, "ablate": 0.0},
        ur_derefusal={"coupled": 0.0, "permuted": 0.0, "ablate": 0.0},
        n=10)
    # rewrite KA so coupled refuses 2/10 (rise 0.2 > 0.05)
    lines = []
    for line in rows.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["behavior_cell"] == KA and r["arm_id"] == "coupled" and \
                r["probe_pool_row_key"].endswith(("::0", "::1")):
            r["refused"], r["correct"] = True, False
        lines.append(json.dumps(r))
    rows.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = ac.analyze(rows, gains, n_boot=200, seed=1)
    assert out["specificity_guard"]["ka_refusal_rise"] == pytest.approx(0.2)
    assert out["specificity_guard"]["pass"] is False


def test_bootstrap_is_seed_deterministic(tmp_path):
    rows, gains = _make_dataset(
        tmp_path,
        kr_derefusal={"coupled": 0.6, "permuted": 0.3, "ablate": 0.4},
        ur_derefusal={"coupled": 0.2, "permuted": 0.3, "ablate": 0.4})
    a = ac.analyze(rows, gains, n_boot=300, seed=7)
    b = ac.analyze(rows, gains, n_boot=300, seed=7)
    assert a["ac_g1"]["ci95"] == b["ac_g1"]["ci95"]


def test_missing_arm_raises(tmp_path):
    rows = tmp_path / "rows.jsonl"
    _write_rows(rows, [(KR, "k0", _uniform_arms(
        {"baseline": True, "coupled": False, "permuted": True}))])  # no ablate
    gains = tmp_path / "gains.json"
    gains.write_text(json.dumps({"gains": {}}), encoding="utf-8")
    with pytest.raises(ac.ACAnalysisError, match="missing arms"):
        ac.load_rows(rows)


def test_missing_gain_map_row_raises(tmp_path):
    rows, gains = _make_dataset(
        tmp_path,
        kr_derefusal={"coupled": 0.5, "permuted": 0.5, "ablate": 0.5},
        ur_derefusal={"coupled": 0.5, "permuted": 0.5, "ablate": 0.5},
        n=4)
    gains.write_text(json.dumps({"gains": {}}), encoding="utf-8")
    with pytest.raises(ac.ACAnalysisError, match="missing from gain map"):
        ac.analyze(rows, gains, n_boot=50, seed=1)
