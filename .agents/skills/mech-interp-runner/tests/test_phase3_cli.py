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
