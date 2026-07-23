#!/usr/bin/env python3
"""Run the local thinking-on Amendment B eval batch sequentially in Docker."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[4]
EVAL_DIR = REPO / "experiment" / "phase1" / "eval"
CONFIG_DIR = EVAL_DIR / "config"
DEFAULT_LOG_DIR = EVAL_DIR / "logs" / "thinking_eval_batch"
CONTAINER_REPO = "/workspace/repo"

FULL_THINKING_CONFIGS = (
    "eval_amendment_b_stated_confidence_selfaware_seed1_all_arms_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seed2_all_arms_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seed3_all_arms_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed1_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed2_sft_merged_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed2_sft_dpo_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed2_sft_kto_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed3_sft_merged_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed3_sft_dpo_thinking_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed3_sft_kto_thinking_local_4b.yaml",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def summary_exists(config_path: Path) -> bool:
    cfg = load_config(config_path)
    return (EVAL_DIR / cfg["results_dir"] / "comparisons" / "summary_table.csv").exists()


def docker_command(config_path: Path, *, image: str) -> list[str]:
    container_config = (
        f"{CONTAINER_REPO}/experiment/phase1/eval/config/{config_path.name}"
    )
    return [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "--ipc=host",
        "--entrypoint",
        "python3",
        "-e",
        f"HF_HOME={CONTAINER_REPO}/.cache/hf",
        "-e",
        f"HUGGINGFACE_HUB_CACHE={CONTAINER_REPO}/.cache/hf/hub",
        "-v",
        f"{REPO}:{CONTAINER_REPO}",
        "-w",
        CONTAINER_REPO,
        image,
        "experiment/phase1/eval/run_eval.py",
        "--config",
        container_config,
        "--live-vllm",
    ]


def append_status(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def run_config(
    config_path: Path,
    *,
    image: str,
    log_dir: Path,
    status_path: Path,
    force: bool,
) -> int:
    cfg = load_config(config_path)
    result_dir = EVAL_DIR / cfg["results_dir"]
    log_path = log_dir / f"{config_path.stem}.log"
    if summary_exists(config_path) and not force:
        append_status(
            status_path,
            {
                "time": utc_now(),
                "config": config_path.name,
                "results_dir": cfg["results_dir"],
                "status": "skipped_existing",
            },
        )
        return 0

    start = time.monotonic()
    append_status(
        status_path,
        {
            "time": utc_now(),
            "config": config_path.name,
            "results_dir": cfg["results_dir"],
            "status": "started",
            "log": str(log_path),
        },
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        proc = subprocess.run(
            docker_command(config_path, image=image),
            cwd=REPO,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    elapsed_sec = round(time.monotonic() - start, 3)
    status = "completed" if proc.returncode == 0 and summary_exists(config_path) else "failed"
    append_status(
        status_path,
        {
            "time": utc_now(),
            "config": config_path.name,
            "results_dir": cfg["results_dir"],
            "result_dir": str(result_dir),
            "status": status,
            "returncode": proc.returncode,
            "elapsed_sec": elapsed_sec,
            "log": str(log_path),
        },
    )
    return 0 if status == "completed" else proc.returncode or 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run thinking-on Amendment B local eval configs sequentially."
    )
    parser.add_argument("--image", default="unsloth/unsloth:latest")
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--status-path", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--config",
        action="append",
        help="Run only this config filename. May be repeated.",
    )
    args = parser.parse_args(argv)

    config_names = tuple(args.config) if args.config else FULL_THINKING_CONFIGS
    status_path = args.status_path or (
        args.log_dir / f"batch_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )
    append_status(
        status_path,
        {
            "time": utc_now(),
            "status": "batch_started",
            "config_count": len(config_names),
            "image": args.image,
        },
    )

    for name in config_names:
        rc = run_config(
            CONFIG_DIR / name,
            image=args.image,
            log_dir=args.log_dir,
            status_path=status_path,
            force=args.force,
        )
        if rc != 0:
            append_status(
                status_path,
                {"time": utc_now(), "status": "batch_failed", "failed_config": name},
            )
            return rc

    append_status(status_path, {"time": utc_now(), "status": "batch_completed"})
    print(status_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
