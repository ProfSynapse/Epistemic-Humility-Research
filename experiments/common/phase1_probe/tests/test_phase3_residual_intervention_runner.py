"""Offline tests for phase3_residual_intervention_runner.run_config's
batching + resume orchestration (Amendment AC engine work, task: per-row
alpha vectors for couple arms).

CPU-only: ModelHarness and score_generation are monkeypatched, so no model
loads and no GPU. Covers:
  - batch_size > 1 routes through generate_batch with the couple arm's
    per-row alpha VECTOR aligned to the chunk's rows (scalar for a 1-row
    tail chunk — the hook's sequential contract)
  - batch_size 1 (default) keeps the historical per-row generate path
  - records carry each row's own resolved arm_alpha
  - resume skips completed units under an unchanged fingerprint
  - the fingerprint is unchanged for sequential runs and differs for
    batched runs (a batched run must not resume a sequential partial)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import phase3_residual_intervention_runner as runner  # noqa: E402

GAINS = {"r1": 0.5, "r2": -1.0, "r3": 2.0}


def _write_inputs(tmp_path: Path, *, batch_size: int | None) -> Path:
    direction = tmp_path / "direction.json"
    direction.write_text(json.dumps(
        {"layer": 3, "theta": [1.0, 0.0, 0.0, 0.0], "sigma": 1.0}))
    rows = tmp_path / "rows.jsonl"
    rows.write_text("".join(
        json.dumps({"probe_pool_row_key": k, "question": f"Q-{k}?",
                    "label": "known", "behavior_cell": "known_refused"}) + "\n"
        for k in GAINS))
    gain_map = tmp_path / "gain_map.json"
    gain_map.write_text(json.dumps(
        {"gains": {k: {"gain": v} for k, v in GAINS.items()}}))
    sweep: dict = {"max_new_tokens": 8}
    if batch_size is not None:
        sweep["batch_size"] = batch_size
    config = {
        "caution_direction": str(direction),
        "rows": str(rows),
        "arms": [
            {"arm_id": "baseline", "mode": "baseline"},
            {"arm_id": "coupled", "mode": "couple",
             "gain_map": str(gain_map), "gain_key": "gains"},
        ],
        "sweep": sweep,
        "output": {"root": str(tmp_path / "out")},
    }
    import yaml
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def _install_fakes(monkeypatch, calls: list):
    class FakeHarness:
        def __init__(self, config):
            pass

        def generate(self, question, *, spec, arm, max_new_tokens):
            calls.append(("generate", [question], arm.get("arm_id"),
                          arm.get("alpha")))
            return f"answer to {question}"

        def generate_batch(self, questions, *, spec, arm, max_new_tokens):
            calls.append(("generate_batch", list(questions),
                          arm.get("arm_id"), arm.get("alpha")))
            return [f"answer to {q}" for q in questions]

    monkeypatch.setattr(runner, "ModelHarness", FakeHarness)
    monkeypatch.setattr(runner, "score_generation",
                        lambda row, answer: {"refused": False, "correct": True})


def _read_records(cfg_path: Path) -> list[dict]:
    import yaml
    out_root = Path(yaml.safe_load(cfg_path.read_text())["output"]["root"])
    return [json.loads(x) for x in
            (out_root / "rows.jsonl").read_text().splitlines()]


def test_batched_couple_arm_carries_per_row_alpha_vector(tmp_path, monkeypatch):
    cfg = _write_inputs(tmp_path, batch_size=2)
    calls: list = []
    _install_fakes(monkeypatch, calls)
    summary = runner.run_config(cfg)
    assert summary["units_generated"] == 6  # 2 arms x 3 rows

    coupled = [c for c in calls if c[2] == "coupled"]
    assert [c[0] for c in coupled] == ["generate_batch", "generate_batch"]
    # full chunk: alpha VECTOR aligned to (r1, r2); 1-row tail: scalar.
    assert coupled[0][1] == ["Q-r1?", "Q-r2?"]
    assert coupled[0][3] == [GAINS["r1"], GAINS["r2"]]
    assert coupled[1][1] == ["Q-r3?"]
    assert coupled[1][3] == GAINS["r3"]
    # baseline batches too, arm alpha untouched (scalar 0.0).
    baseline = [c for c in calls if c[2] == "baseline"]
    assert all(c[0] == "generate_batch" and c[3] == 0.0 for c in baseline)

    # each record carries ITS row's resolved alpha.
    recs = {(r["arm_id"], r["probe_pool_row_key"]): r for r in _read_records(cfg)}
    for k, gain in GAINS.items():
        assert recs[("coupled", k)]["arm_alpha"] == gain
        assert recs[("baseline", k)]["arm_alpha"] == 0.0


def test_default_batch_size_keeps_sequential_generate(tmp_path, monkeypatch):
    cfg = _write_inputs(tmp_path, batch_size=None)
    calls: list = []
    _install_fakes(monkeypatch, calls)
    runner.run_config(cfg)
    assert all(c[0] == "generate" for c in calls)
    coupled_alphas = [c[3] for c in calls if c[2] == "coupled"]
    assert coupled_alphas == [GAINS["r1"], GAINS["r2"], GAINS["r3"]]


def test_resume_skips_completed_units(tmp_path, monkeypatch):
    cfg = _write_inputs(tmp_path, batch_size=2)
    calls: list = []
    _install_fakes(monkeypatch, calls)
    runner.run_config(cfg)
    calls.clear()
    summary = runner.run_config(cfg)  # same config -> same fingerprint
    assert calls == []  # nothing regenerated
    assert summary["units_generated"] == 0
    assert len(_read_records(cfg)) == 6  # prior records preserved


def test_bad_batch_size_raises(tmp_path, monkeypatch):
    cfg = _write_inputs(tmp_path, batch_size=0)
    _install_fakes(monkeypatch, [])
    with pytest.raises(runner.ResidualInterventionRunError, match="batch_size"):
        runner.run_config(cfg)


def test_resolve_model_ref():
    # existing repo-relative dir -> absolute; hub id / missing path untouched
    rel = "experiments/common/phase1_probe"
    resolved = runner.resolve_model_ref(rel)
    assert Path(resolved).is_absolute() and resolved.endswith(rel)
    assert runner.resolve_model_ref("unsloth/Qwen3-4B") == "unsloth/Qwen3-4B"
    assert runner.resolve_model_ref(None) is None


def test_fingerprint_sequential_stable_batched_differs():
    config = {"model": {"model_name": "m"}, "rows": "r.jsonl"}
    kw = dict(direction={"layer": 3, "sigma": 1.0},
              arms=[{"arm_id": "baseline", "mode": "baseline", "alpha": 0.0}],
              max_new_tokens=8)
    fp_default = runner._config_fingerprint(config, **kw)
    fp_seq = runner._config_fingerprint(config, batch_size=1, **kw)
    fp_batched = runner._config_fingerprint(config, batch_size=8, **kw)
    assert fp_default == fp_seq  # historical sequential fingerprints intact
    assert fp_batched != fp_seq
