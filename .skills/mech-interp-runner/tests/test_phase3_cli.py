from __future__ import annotations

import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import phase3_cli  # noqa: E402


def test_command_args_builds_sycophancy_generation_analysis():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "sycophancy-generation-analysis",
        "--generations",
        "a/generations.jsonl",
        "--generations",
        "b/generations.jsonl",
        "--output-root",
        "out",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_sycophancy_generation_analysis.py"
    assert out == [
        "--output-root",
        "out",
        "--generations",
        "a/generations.jsonl",
        "--generations",
        "b/generations.jsonl",
    ]


def test_command_args_builds_causal_sweep_flags():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "causal-sweep",
        "--config",
        "cfg.yaml",
        "--mode-filter",
        "logit_diagnostic",
        "--write-plan",
        "--materialize-configs",
        "--execute",
        "--allow-logit-diagnostic",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_causal_pilot_sweep.py"
    assert out == [
        "--config",
        "cfg.yaml",
        "--mode-filter",
        "logit_diagnostic",
        "--write-plan",
        "--materialize-configs",
        "--execute",
        "--allow-logit-diagnostic",
    ]


def test_command_args_builds_logit_cell_sign_score():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "logit-cell-sign-score",
        "--config",
        "score.yaml",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_logit_cell_sign_score.py"
    assert out == ["--config", "score.yaml"]


def test_command_args_builds_xdataset_build_panel():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "xdataset-build-panel",
        "--source", "datasets/kuq/knowns_unknowns.jsonl",
        "--dataset", "kuq",
        "--out-dir", "experiment/phase1/probe/xdataset/kuq_panel",
        "--n-known", "600",
        "--n-unknown", "400",
        "--seed", "0",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_xdataset_build_panel.py"
    assert out == [
        "--source", "datasets/kuq/knowns_unknowns.jsonl",
        "--dataset", "kuq",
        "--out-dir", "experiment/phase1/probe/xdataset/kuq_panel",
        "--n-known", "600",
        "--n-unknown", "400",
        "--seed", "0",
        "--question-field", "question",
        "--unknown-field", "unknown",
        "--answer-field", "answer",
    ]


def test_command_args_builds_xdataset_behavior():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "xdataset-behavior",
        "--generation", "experiment/phase1/probe/xdataset/kuq_generation/rows.jsonl",
        "--panel-rows", "experiment/phase1/probe/xdataset/kuq_panel/gen_rows.jsonl",
        "--out-dir", "experiment/phase1/probe/xdataset/kuq_behavior",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_xdataset_behavior_from_generation.py"
    assert out == [
        "--generation", "experiment/phase1/probe/xdataset/kuq_generation/rows.jsonl",
        "--panel-rows", "experiment/phase1/probe/xdataset/kuq_panel/gen_rows.jsonl",
        "--out-dir", "experiment/phase1/probe/xdataset/kuq_behavior",
    ]


def test_command_args_builds_residual_caution_direction():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "residual-caution-direction",
        "--extraction-dir", "probe/x/extraction__abc",
        "--behavior-rows", "probe/y/rows.jsonl",
        "--layer", "35",
        "--out", "probe/z/caution_direction_L35.json",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_residual_caution_direction.py"
    assert out == [
        "--extraction-dir", "probe/x/extraction__abc",
        "--behavior-rows", "probe/y/rows.jsonl",
        "--layer", "35",
        "--source", "h_lora",
        "--out", "probe/z/caution_direction_L35.json",
    ]


def test_command_args_builds_residual_read_trajectory_analysis():
    parser = phase3_cli.build_parser()
    args = parser.parse_args([
        "residual-read-trajectory-analysis",
        "--rows", "probe/t/rows.jsonl",
        "--out", "probe/t/analysis.json",
    ])

    script, out = phase3_cli.command_args(args)

    assert script == "experiment/phase1/probe/phase3_residual_read_trajectory.py"
    assert out == ["--rows", "probe/t/rows.jsonl", "--out", "probe/t/analysis.json"]


def test_subprocess_env_forces_utf8(monkeypatch):
    captured = {}
    monkeypatch.setenv("PYTHONIOENCODING", "cp1252")

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr(phase3_cli.subprocess, "run", fake_run)

    rc = phase3_cli.run_repo_python("script.py", ["--x", "1"])

    assert rc == 0
    assert captured["command"] == [sys.executable, "script.py", "--x", "1"]
    env = captured["kwargs"]["env"]
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["PYTHONUNBUFFERED"] == "1"
    assert Path(captured["kwargs"]["cwd"]).name == "Epistemic-Humility-Research"
    assert os.environ["PYTHONIOENCODING"] == "cp1252"
