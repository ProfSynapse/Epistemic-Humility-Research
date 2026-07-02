#!/usr/bin/env python3
"""Local launcher: submit one cross-model readout cell as an HF Job.

Uses the huggingface_hub Python Jobs API directly (the `hf jobs` CLI is broken
in this workspace's env: typer version mismatch). Builds a bootstrap command
that installs deps, clones the PUBLIC repo at a pinned commit, and hands off
to experiment/phase1/probe/cloud/hf_jobs_cell.sh.

Every launch is a cost-incurring cloud action: requires explicit user approval
naming model/rows/lane in the current conversation before running this.

HF_TOKEN must be in the environment (inject process-locally from the root
.env; never print it). It is forwarded to the job as a secret for the final
result upload only.

Example (the Y-lane plumbing smoke):
  python3 experiment/phase1/probe/cloud/launch_hf_job.py \\
      --model Qwen/Qwen3.5-0.8B-Base \\
      --gate-rows experiment/phase1/probe/pools/selfaware_gate_rows_smoke300.jsonl \\
      --commit <sha-on-public-remote> \\
      --run-tag smoke-qwen3.5-0.8b-base \\
      --timeout 45m \\
      -- --n-answerable 150 --max-attempts 450 --wrong-floor 5 --hallucination-floor 10
"""
from __future__ import annotations

import argparse
import os
import shlex
import sys

REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
DEFAULT_IMAGE = "pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
# transformers pin: 5.12.1 is the post-cutoff-arch version validated locally in
# the unsloth-z image (Qwen3.5 / Gemma-4 loaders). Keep pinned; bump deliberately.
PIP_SPEC = "'transformers==5.12.1' accelerate safetensors scikit-learn 'huggingface_hub>=1.5'"
DEFAULT_RESULTS_REPO = "professorsynapse/epistemic-humility-cloud-results"


def build_command(args, extract_args: list[str]) -> list[str]:
    cell = " ".join([
        "bash experiment/phase1/probe/cloud/hf_jobs_cell.sh",
        shlex.quote(args.model),
        shlex.quote(args.gate_rows),
        shlex.quote(args.results_repo),
        shlex.quote(args.run_tag),
        *[shlex.quote(a) for a in extract_args],
    ])
    script = " && ".join([
        "set -euo pipefail",
        "command -v git >/dev/null || (apt-get update -qq && apt-get install -yqq git)",
        f"pip install -q --no-cache-dir {PIP_SPEC}",
        f"git clone --filter=blob:none {REPO_URL} /tmp/repo",
        "cd /tmp/repo",
        f"git checkout --detach {shlex.quote(args.commit)}",
        cell,
    ])
    return ["/bin/bash", "-c", script]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--gate-rows", required=True,
                    help="repo-relative path to a tracked gate-rows pool file")
    ap.add_argument("--commit", required=True,
                    help="commit sha pinning the clone; MUST be pushed to the public remote")
    ap.add_argument("--run-tag", required=True)
    ap.add_argument("--results-repo", default=DEFAULT_RESULTS_REPO)
    ap.add_argument("--image", default=DEFAULT_IMAGE)
    ap.add_argument("--flavor", default="a10g-small")
    ap.add_argument("--timeout", default="45m")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the job spec (sans secret) and exit without submitting")
    args, extract_args = ap.parse_known_args()
    if extract_args and extract_args[0] == "--":
        extract_args = extract_args[1:]

    tok = os.environ.get("HF_TOKEN")
    if not tok and not args.dry_run:
        print("FATAL: HF_TOKEN not in environment", file=sys.stderr)
        return 2

    command = build_command(args, extract_args)
    print(f"[launch] image={args.image} flavor={args.flavor} timeout={args.timeout}")
    print(f"[launch] command: {command[2]}")
    if args.dry_run:
        print("[launch] dry-run: not submitted")
        return 0

    from huggingface_hub import HfApi

    api = HfApi(token=tok)
    job = api.run_job(
        image=args.image,
        command=command,
        flavor=args.flavor,
        timeout=args.timeout,
        secrets={"HF_TOKEN": tok},
        env={"HF_HUB_ENABLE_HF_TRANSFER": "0"},
    )
    print(f"[launch] job id: {job.id}")
    print(f"[launch] url:    {getattr(job, 'url', '(see hf.co/jobs)')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
