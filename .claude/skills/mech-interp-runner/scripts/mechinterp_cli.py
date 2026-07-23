#!/usr/bin/env python3
"""Small CLI router for Epistemic-Humility mech-interp workflows.

The purpose is to make common analyses repeatable without hand-writing long
Windows-host commands. This script delegates to checked-in repo scripts and
sets a UTF-8 subprocess environment so JSONL/Unicode output does not trip over
Windows console defaults.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    """Return the repository root containing this skill tree."""
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "AGENTS.md").is_file() and (parent / "experiment").is_dir():
            return parent
    raise RuntimeError(f"could not find repo root from {path}")


def rel(path: str) -> str:
    """Normalize a repo-relative path for Python subprocess arguments."""
    return Path(path).as_posix()


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    return env


def run_repo_python(script: str, args: list[str], *, dry_run: bool = False) -> int:
    return run_python_args([rel(script), *args], dry_run=dry_run)


def run_python_args(args: list[str], *, dry_run: bool = False) -> int:
    root = repo_root()
    command = [sys.executable, *args]
    if dry_run:
        print(" ".join(command))
        return 0
    completed = subprocess.run(
        command,
        cwd=str(root),
        env=_env(),
        text=True,
        check=False,
    )
    return completed.returncode


def _add_config(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True, help="Repo-relative config path")


def _add_dry_run(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="Print command without running it")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sycophancy-eval-analysis", help="Analyze answer-sycophancy scored rows")
    p.add_argument("--results-dir", help="Results dir containing *__sycophancy_answer/scored_rows.jsonl")
    p.add_argument("--scored-rows", action="append", help="Explicit scored_rows.jsonl path")
    p.add_argument("--eval-set", default="sycophancy_answer")
    p.add_argument("--output-root", required=True)
    _add_dry_run(p)

    p = sub.add_parser("sycophancy-generation-analysis", help="Analyze sycophancy generation replay")
    p.add_argument("--generations", action="append", required=True, help="generations.jsonl path")
    p.add_argument("--output-root", required=True)
    _add_dry_run(p)

    p = sub.add_parser("sycophancy-row-manifest", help="Build the sycophancy hidden-state row manifest")
    _add_dry_run(p)

    p = sub.add_parser("behavior-axis-scan", help="Run layerwise behavior-axis scan")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("behavior-axis-directions", help="Export behavior-axis directions")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("direction-transforms", help="Run direction transform config")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("gold-behavior-panel", help="Materialize scored generation behavior panel")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("calibrated-plane", help="Run calibrated-expression plane analysis")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("multicell-readout", help="Run multiclass hidden-state behavior-cell readout")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("logit-cell-analysis", help="Aggregate logit diagnostics by behavior cell")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("logit-cell-sign-score", help="Rank behavior-cell logit summaries by target signs")
    _add_config(p)
    _add_dry_run(p)

    p = sub.add_parser("causal-sweep", help="Plan/materialize/execute a causal pilot sweep")
    _add_config(p)
    p.add_argument("--mode-filter", action="append")
    p.add_argument("--write-plan", action="store_true")
    p.add_argument("--materialize-configs", action="store_true")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--allow-generation", action="store_true")
    p.add_argument("--allow-logit-diagnostic", action="store_true")
    _add_dry_run(p)

    p = sub.add_parser("aggregate", help="Aggregate causal pilot run manifests")
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    _add_dry_run(p)

    p = sub.add_parser("xdataset-build-panel",
                       help="Build a cross-dataset transfer panel (gen rows + extraction manifest)")
    p.add_argument("--source", required=True, help="known/unknown source JSONL (repo-relative)")
    p.add_argument("--dataset", required=True, help="short dataset id / row_key prefix, e.g. kuq")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--n-known", type=int, required=True)
    p.add_argument("--n-unknown", type=int, required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--question-field", default="question")
    p.add_argument("--unknown-field", default="unknown")
    p.add_argument("--answer-field", default="answer")
    _add_dry_run(p)

    p = sub.add_parser("xdataset-behavior",
                       help="Assemble cross-dataset behavior rows from a baseline (alpha=0) generation")
    p.add_argument("--generation", required=True, help="generation rows.jsonl (repo-relative)")
    p.add_argument("--panel-rows", required=True, help="panel gen_rows.jsonl for question/aliases join")
    p.add_argument("--out-dir", required=True)
    _add_dry_run(p)

    p = sub.add_parser("residual-caution-direction",
                       help="Fit the raw mass-mean caution direction for the residual read-trajectory (GPU-free)")
    p.add_argument("--extraction-dir", required=True, help="dir of per-row *_h_lora.safetensors")
    p.add_argument("--behavior-rows", required=True, help="rows.jsonl with probe_pool_row_key + behavior_cell")
    p.add_argument("--layer", type=int, default=35, help="hidden_states layer (default 35)")
    p.add_argument("--source", default="h_lora", choices=["h_lora", "h_base", "delta"])
    p.add_argument("--out", required=True, help="output caution_direction JSON path")
    _add_dry_run(p)

    p = sub.add_parser("residual-read-trajectory-analysis",
                       help="Re-run the GPU-free pre/post-lexical analysis over a trajectory rows.jsonl")
    p.add_argument("--rows", required=True, help="runner rows.jsonl with per-row trajectory summaries")
    p.add_argument("--out", required=True)
    _add_dry_run(p)

    p = sub.add_parser("validate", help="Run the focused mech-interp non-GPU validation set")
    p.add_argument("--quick", action="store_true", help="Only run CLI/unit tests for the skill wrapper")
    _add_dry_run(p)
    return parser


def command_args(args: argparse.Namespace) -> tuple[str, list[str]]:
    command = args.command
    if command == "sycophancy-eval-analysis":
        if not args.results_dir and not args.scored_rows:
            raise SystemExit("provide --results-dir or at least one --scored-rows")
        out = ["--eval-set", args.eval_set, "--output-root", args.output_root]
        if args.results_dir:
            out.extend(["--results-dir", args.results_dir])
        for path in args.scored_rows or []:
            out.extend(["--scored-rows", path])
        return "archive/experiment/phase1/eval/analysis/sycophancy_answer_analysis.py", out
    if command == "sycophancy-generation-analysis":
        out: list[str] = ["--output-root", args.output_root]
        for path in args.generations:
            out.extend(["--generations", path])
        return "experiments/common/mechinterp/sycophancy_generation_analysis.py", out
    if command == "sycophancy-row-manifest":
        return "experiments/common/mechinterp/sycophancy_answer_row_manifest.py", []
    if command == "behavior-axis-scan":
        return "experiments/common/mechinterp/behavior_axis_scan.py", ["--config", args.config]
    if command == "behavior-axis-directions":
        return "experiments/common/mechinterp/behavior_axis_directions.py", ["--config", args.config]
    if command == "direction-transforms":
        return "experiments/common/mechinterp/direction_transforms.py", ["--config", args.config]
    if command == "gold-behavior-panel":
        return "experiments/common/mechinterp/gold_behavior_panel.py", ["--config", args.config]
    if command == "calibrated-plane":
        return "experiments/common/mechinterp/calibrated_expression_plane.py", ["--config", args.config]
    if command == "multicell-readout":
        return "experiments/common/mechinterp/multicell_readout.py", ["--config", args.config]
    if command == "logit-cell-analysis":
        return "experiments/common/mechinterp/logit_cell_analysis.py", ["--config", args.config]
    if command == "logit-cell-sign-score":
        return "experiments/common/mechinterp/logit_cell_sign_score.py", ["--config", args.config]
    if command == "causal-sweep":
        out = ["--config", args.config]
        for mode_filter in args.mode_filter or []:
            out.extend(["--mode-filter", mode_filter])
        for flag in (
            "write_plan",
            "materialize_configs",
            "execute",
            "allow_generation",
            "allow_logit_diagnostic",
        ):
            if getattr(args, flag):
                out.append("--" + flag.replace("_", "-"))
        return "experiments/common/mechinterp/causal_pilot_sweep.py", out
    if command == "aggregate":
        return "experiments/common/mechinterp/causal_pilot_aggregate.py", [
            "--root",
            args.root,
            "--out",
            args.out,
        ]
    if command == "xdataset-build-panel":
        return "experiments/common/mechinterp/xdataset_build_panel.py", [
            "--source", args.source,
            "--dataset", args.dataset,
            "--out-dir", args.out_dir,
            "--n-known", str(args.n_known),
            "--n-unknown", str(args.n_unknown),
            "--seed", str(args.seed),
            "--question-field", args.question_field,
            "--unknown-field", args.unknown_field,
            "--answer-field", args.answer_field,
        ]
    if command == "xdataset-behavior":
        return "experiments/common/mechinterp/xdataset_behavior_from_generation.py", [
            "--generation", args.generation,
            "--panel-rows", args.panel_rows,
            "--out-dir", args.out_dir,
        ]
    if command == "residual-caution-direction":
        return "experiments/common/mechinterp/residual_caution_direction.py", [
            "--extraction-dir", args.extraction_dir,
            "--behavior-rows", args.behavior_rows,
            "--layer", str(args.layer),
            "--source", args.source,
            "--out", args.out,
        ]
    if command == "residual-read-trajectory-analysis":
        return "experiments/common/mechinterp/residual_read_trajectory.py", [
            "--rows", args.rows,
            "--out", args.out,
        ]
    raise SystemExit(f"unsupported command {command!r}")


def run_validate(*, quick: bool, dry_run: bool) -> int:
    if quick:
        return run_python_args(
            [
                "-m",
                "pytest",
                ".skills/mech-interp-runner/tests/test_mechinterp_cli.py",
                "-q",
            ],
            dry_run=dry_run,
        )
    commands = [
        [
            "-m",
            "pytest",
            "experiments/common/knowledge_probe/tests/test_mechinterp_causal_pilot_sweep.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_causal_pilot_runner.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_sycophancy_answer_row_manifest.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_sycophancy_generation_analysis.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_sae_behavior_feature_analysis.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_behavior_axis_scan.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_multicell_readout.py",
            "experiments/common/knowledge_probe/tests/test_hidden_state_probe.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_xdataset_build_panel.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_xdataset_behavior_from_generation.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_residual_read_trajectory.py",
            "experiments/common/knowledge_probe/tests/test_mechinterp_residual_caution_direction.py",
            "-q",
        ],
        [
            "-m",
            "py_compile",
            "experiments/common/mechinterp/causal_pilot_sweep.py",
            "experiments/common/mechinterp/causal_pilot_runner.py",
            "experiments/common/mechinterp/sycophancy_answer_row_manifest.py",
            "experiments/common/mechinterp/sycophancy_generation_analysis.py",
            "experiments/common/mechinterp/sae_behavior_feature_analysis.py",
            "experiments/common/mechinterp/behavior_axis_scan.py",
            "experiments/common/mechinterp/multicell_readout.py",
            "experiments/common/knowledge_probe/hidden_state_probe.py",
            "experiments/common/mechinterp/xdataset_build_panel.py",
            "experiments/common/mechinterp/xdataset_behavior_from_generation.py",
            "experiments/common/mechinterp/residual_caution_direction.py",
            "experiments/common/mechinterp/residual_read_trajectory.py",
            "experiments/common/mechinterp/residual_read_trajectory_runner.py",
        ],
        ["bin/sync_skills.py", "--check"],
    ]
    for command in commands:
        if command[0].endswith(".py"):
            rc = run_repo_python(command[0], command[1:], dry_run=dry_run)
        else:
            rc = run_python_args(command, dry_run=dry_run)
        if rc:
            return rc
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return run_validate(quick=args.quick, dry_run=args.dry_run)
    script, out_args = command_args(args)
    return run_repo_python(script, out_args, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
