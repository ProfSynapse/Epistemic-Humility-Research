from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

PROBE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = PROBE_DIR.parents[2]
if REPO_ROOT.name == "experiments":
    REPO_ROOT = REPO_ROOT.parent
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
for _dir in (PROBE_DIR, EVAL_DIR):
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))

pytest.importorskip("scorers", reason="eval scorers must be importable")
import phase3_head_intervention_runner as runner  # noqa: E402


def _steering_artifact(path: Path) -> None:
    artifact = {
        "artifact_type": "phase3_head_steering_directions",
        "directions": [
            {"layer": 1, "head": 0, "head_dim": 2, "theta": [1.0, 0.0], "sigma": 1.0},
        ],
    }
    path.write_text(json.dumps(artifact), encoding="utf-8")


def _rows(path: Path) -> None:
    rows = [
        {"probe_pool_row_key": "u1", "label": "unknown", "question": "Q-unknown-1", "aliases": ["zeta"]},
        {"probe_pool_row_key": "k1", "label": "known", "question": "Q-known-1", "aliases": ["paris"]},
    ]
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


class _StubHarness:
    """Returns a refusal under steering (by_block non-empty), an answer at baseline."""

    def __init__(self, config):  # noqa: D401
        self.calls = []

    def generate(self, question, *, by_block, max_new_tokens):
        steered = bool(by_block)
        self.calls.append((question, steered))
        if steered:
            return '{"answer": "I don\'t know the answer", "response_confidence": 0.1}'
        return '{"answer": "paris", "response_confidence": 0.9}'


def test_sweep_runs_baseline_and_steered_arms(tmp_path, monkeypatch):
    steering = tmp_path / "steering.json"
    rows = tmp_path / "rows.jsonl"
    _steering_artifact(steering)
    _rows(rows)
    output_root = tmp_path / "out"

    config = {
        "model": {"model_name": "unused-stub"},
        "prompt": {"system": "sys"},
        "steering_directions": str(steering),
        "rows": str(rows),
        "sweep": {"alphas": [-4.0, 0.0], "max_new_tokens": 8, "max_rows": 2},
        "output": {"root": str(output_root)},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    monkeypatch.setattr(runner, "ModelHarness", _StubHarness)
    # absolute paths in config -> resolve_path returns them as-is
    summary = runner.run_config(config_path)

    assert summary["ok"] is True
    assert summary["num_target_heads"] == 1
    arms = summary["metrics_by_arm"]
    assert "no_vector_baseline" in arms
    steered_arm = next(k for k in arms if k.startswith("per_head_iti_alpha"))

    # Baseline answered the known question (paris) -> over-refusal 0; steered refused everything.
    assert arms["no_vector_baseline"]["over_refusal_on_known"] == 0.0
    assert arms[steered_arm]["over_refusal_on_known"] == 100.0
    # Steered drove unknown refusal to 100%.
    assert arms[steered_arm]["unknown_refusal_rate"] == 100.0

    # Per-row results were written for both arms x both rows = 4 rows.
    written = [json.loads(l) for l in (output_root / "rows.jsonl").read_text().splitlines() if l.strip()]
    assert len(written) == 4


class _CountingHarness(_StubHarness):
    """Class-level call counter so a resumed run can prove it skipped completed units."""

    total_calls = 0

    def generate(self, question, *, by_block, max_new_tokens):
        _CountingHarness.total_calls += 1
        return super().generate(question, by_block=by_block, max_new_tokens=max_new_tokens)


def _basic_config(tmp_path):
    steering = tmp_path / "steering.json"
    rows = tmp_path / "rows.jsonl"
    _steering_artifact(steering)
    _rows(rows)
    output_root = tmp_path / "out"
    config = {
        "model": {"model_name": "stub"},
        "prompt": {"system": "sys"},
        "steering_directions": str(steering),
        "rows": str(rows),
        "sweep": {"alphas": [-4.0, 0.0], "max_new_tokens": 8, "max_rows": 2},
        "output": {"root": str(output_root)},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path, output_root


def test_resume_skips_completed_units(tmp_path, monkeypatch):
    config_path, output_root = _basic_config(tmp_path)
    monkeypatch.setattr(runner, "ModelHarness", _CountingHarness)

    _CountingHarness.total_calls = 0
    first = runner.run_config(config_path)
    assert first["units_generated"] == 4  # 2 alphas x 2 rows
    assert _CountingHarness.total_calls == 4
    assert (output_root / "checkpoint.json").is_file()

    # Re-run unchanged: everything resumes, model is never asked to generate again.
    _CountingHarness.total_calls = 0
    second = runner.run_config(config_path)
    assert second["units_generated"] == 0
    assert second["units_resumed"] == 4
    assert _CountingHarness.total_calls == 0
    # Metrics identical to the full run.
    assert second["metrics_by_arm"] == first["metrics_by_arm"]


def test_resume_after_truncated_tail(tmp_path, monkeypatch):
    config_path, output_root = _basic_config(tmp_path)
    output_root.mkdir(parents=True, exist_ok=True)
    # Simulate a process killed mid-write: 1 clean row + a truncated JSON line.
    rows_file = output_root / "rows.jsonl"
    good = {
        "arm_id": "no_vector_baseline", "control": "no_vector_baseline", "alpha": 0.0,
        "probe_pool_row_key": "k1", "label": "known", "generated_answer": "{}",
        "refused": False, "correct": True, "truthful": True,
    }
    rows_file.write_text(json.dumps(good) + "\n" + '{"arm_id": "no_vector_base', encoding="utf-8")
    # Matching checkpoint so resume is allowed.
    config = yaml.safe_load(config_path.read_text())
    fp = runner._config_fingerprint(config, alphas=[-4.0, 0.0], max_new_tokens=8)
    (output_root / "checkpoint.json").write_text(json.dumps({"fingerprint": fp}), encoding="utf-8")

    monkeypatch.setattr(runner, "ModelHarness", _CountingHarness)
    _CountingHarness.total_calls = 0
    summary = runner.run_config(config_path)
    # 1 unit kept (the clean row), truncated tail dropped -> 3 regenerated.
    assert summary["units_resumed"] == 1
    assert summary["units_generated"] == 3
    written = [json.loads(l) for l in rows_file.read_text().splitlines() if l.strip()]
    assert len(written) == 4  # clean file, no truncated tail


def test_fresh_discards_prior_rows(tmp_path, monkeypatch):
    config_path, output_root = _basic_config(tmp_path)
    monkeypatch.setattr(runner, "ModelHarness", _CountingHarness)
    runner.run_config(config_path)
    _CountingHarness.total_calls = 0
    summary = runner.run_config(config_path, fresh=True)
    assert summary["units_generated"] == 4
    assert _CountingHarness.total_calls == 4


def test_fingerprint_mismatch_refuses_resume(tmp_path, monkeypatch):
    config_path, output_root = _basic_config(tmp_path)
    monkeypatch.setattr(runner, "ModelHarness", _CountingHarness)
    runner.run_config(config_path)
    # Change the sweep -> fingerprint changes -> resume must refuse.
    config = yaml.safe_load(config_path.read_text())
    config["sweep"]["alphas"] = [-2.0, 0.0]
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(runner.HeadInterventionRunError, match="fingerprint"):
        runner.run_config(config_path)


def test_sweep_requires_baseline_alpha(tmp_path):
    steering = tmp_path / "steering.json"
    rows = tmp_path / "rows.jsonl"
    _steering_artifact(steering)
    _rows(rows)
    config = {
        "model": {"model_name": "x"},
        "steering_directions": str(steering),
        "rows": str(rows),
        "sweep": {"alphas": [-4.0, 4.0]},
        "output": {"root": str(tmp_path / "out")},
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(runner.HeadInterventionRunError, match="must include 0.0"):
        runner.run_config(config_path)
