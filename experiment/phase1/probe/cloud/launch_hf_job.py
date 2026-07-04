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
TUNER_REPO_URL = "https://github.com/ProfSynapse/Synaptic-Tuner.git"
DEFAULT_IMAGE = "pytorch/pytorch:2.9.0-cuda12.8-cudnn9-runtime"
# transformers pin: 5.12.1 is the post-cutoff-arch version validated locally in
# the unsloth-z image (Qwen3.5 / Gemma-4 loaders). Keep pinned; bump deliberately.
PIP_SPEC = "'transformers==5.12.1' accelerate safetensors scikit-learn 'huggingface_hub>=1.5'"
DEFAULT_RESULTS_REPO = "professorsynapse/epistemic-humility-cloud-results"

# Amendment AI verdict lane: the cells load the clean-SFT base 4-bit through
# unsloth (sensor-v2 serving lineage), so they need the pinned stable Unsloth
# image, not the plain pytorch base. Image + digest per cloud-lane.md.
AI_VERDICT_IMAGE = ("unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update@sha256:"
                    "5266c57be21059bfb407d80dc2f448868a5c2e2dbe7b2aa27780f48b48cbec39")
# The stable Unsloth image already carries unsloth + a matched transformers/
# torch/peft stack; only add the small CPU-side deps the cells import at the
# top level. Do NOT --upgrade the ML stack (cloud-lane.md: mid-session numpy/
# transformers upgrades have failed jobs).
AI_VERDICT_PIP_SPEC = "scikit-learn 'huggingface_hub>=1.5' pyyaml"
DEFAULT_STAGING_REPO = "professorsynapse/eh-ai-verdict-staging"


def build_command(args, extract_args: list[str]) -> list[str]:
    cell = " ".join([
        f"bash experiment/phase1/probe/cloud/{args.cell_script}",
        shlex.quote(args.model),
        shlex.quote(args.gate_rows),
        shlex.quote(args.results_repo),
        shlex.quote(args.run_tag),
        *[shlex.quote(a) for a in extract_args],
    ])
    steps = [
        "set -euo pipefail",
        "command -v git >/dev/null || (apt-get update -qq && apt-get install -yqq git)",
        f"pip install -q --no-cache-dir {PIP_SPEC}",
        f"git clone --filter=blob:none {REPO_URL} /tmp/repo",
        "cd /tmp/repo",
        f"git checkout --detach {shlex.quote(args.commit)}",
    ]
    if args.tuner_commit:
        # The tuner-batched engine shells out to the Synaptic Tuner public CLI;
        # clone it at a pinned commit next to the repo. Callers pass
        # `--tuner-dir /tmp/synaptic-tuner` in the extract passthrough args.
        steps += [
            f"git clone --filter=blob:none {TUNER_REPO_URL} /tmp/synaptic-tuner",
            f"git -C /tmp/synaptic-tuner checkout --detach {shlex.quote(args.tuner_commit)}",
        ]
    steps.append(cell)
    return ["/bin/bash", "-c", " && ".join(steps)]


def build_ai_verdict_command(args) -> list[str]:
    """Amendment AI verdict cell: hf_jobs_ai_verdict.sh (extract | generate).

    Positional contract matches the wrapper:
      <stage> <surface|-> <arm_tag> <staging_repo> <base_model>
      <adapter_repo|-> <adapter_revision|-> <pool_path_in_repo>
    """
    cell = " ".join([
        "bash experiment/phase1/probe/cloud/hf_jobs_ai_verdict.sh",
        shlex.quote(args.stage),
        shlex.quote(args.surface or "-"),
        shlex.quote(args.arm_tag),
        shlex.quote(args.staging_repo),
        shlex.quote(args.base_model),
        shlex.quote(args.adapter_repo or "-"),
        shlex.quote(args.adapter_revision or "-"),
        shlex.quote(args.pool_in_repo),
    ])
    steps = [
        "set -euo pipefail",
        "command -v git >/dev/null || (apt-get update -qq && apt-get install -yqq git)",
        # Unsloth image already has the ML stack; add only CPU-side deps
        # (no --upgrade; cloud-lane.md).
        f"pip install -q --no-cache-dir {AI_VERDICT_PIP_SPEC}",
        f"git clone --filter=blob:none {REPO_URL} /tmp/repo",
        "cd /tmp/repo",
        f"git checkout --detach {shlex.quote(args.commit)}",
        cell,
    ]
    return ["/bin/bash", "-c", " && ".join(steps)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=None,
                    help="serving base (required for the X/readout lane)")
    ap.add_argument("--gate-rows", default=None,
                    help="repo-relative path to a tracked gate-rows pool file "
                         "(X/readout lane)")
    ap.add_argument("--commit", required=True,
                    help="commit sha pinning the clone; MUST be pushed to the public remote")
    ap.add_argument("--run-tag", default=None,
                    help="run tag (X/readout lane; the AI lane derives its own)")

    # --- Amendment AI verdict lane (extract | generate) ---
    ai = ap.add_argument_group("amendment AI verdict lane")
    ai.add_argument("--ai-verdict", action="store_true",
                    help="launch an Amendment AI verdict cell "
                         "(hf_jobs_ai_verdict.sh) instead of the X/readout cell")
    ai.add_argument("--stage", choices=["extract", "generate"],
                    help="AI verdict stage")
    ai.add_argument("--surface", choices=["union", "holdout"],
                    help="AI verdict extract surface (omit for --stage generate)")
    ai.add_argument("--arm-tag", choices=["true", "permuted"],
                    help="which arm this cell is for (namespaces the staging upload)")
    ai.add_argument("--base-model",
                    help="clean-SFT merged base HF repo id (AI lane)")
    ai.add_argument("--adapter-repo", default=None,
                    help="trained LoRA adapter HF repo id (AI lane; the arm under eval)")
    ai.add_argument("--adapter-revision", default=None,
                    help="adapter repo revision/commit to pin (AI lane)")
    ai.add_argument("--staging-repo", default=DEFAULT_STAGING_REPO,
                    help="private staging dataset repo for AI verdict IO")
    ai.add_argument("--pool-in-repo",
                    help="path (inside the staging repo) of the input pool jsonl")
    ap.add_argument("--cell-script", default="hf_jobs_cell.sh",
                    choices=["hf_jobs_cell.sh", "hf_jobs_arm_b.sh"],
                    help="in-job wrapper: hf_jobs_cell.sh = extract->score "
                         "readout cell; hf_jobs_arm_b.sh = Arm B CoT-injection "
                         "cell (run_arm_b.py)")
    ap.add_argument("--results-repo", default=DEFAULT_RESULTS_REPO)
    ap.add_argument("--image", default=DEFAULT_IMAGE)
    ap.add_argument("--flavor", default="a10g-small")
    ap.add_argument("--timeout", default="45m")
    ap.add_argument("--tuner-commit", default=None,
                    help="pin and clone Synaptic Tuner at this sha (pushed to its "
                         "public remote) for --engine tuner-batched cells")
    ap.add_argument("--log-push-interval", type=int, default=None,
                    help="seconds between durable log pushes in-job (default 600; "
                         "use 120 for short batched cells)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the job spec (sans secret) and exit without submitting")
    args, extract_args = ap.parse_known_args()
    if extract_args and extract_args[0] == "--":
        extract_args = extract_args[1:]

    if args.ai_verdict:
        required = {"--stage": args.stage, "--arm-tag": args.arm_tag,
                    "--base-model": args.base_model,
                    "--pool-in-repo": args.pool_in_repo}
        missing = [k for k, v in required.items() if not v]
        if args.stage == "extract" and not args.surface:
            missing.append("--surface (required for --stage extract)")
        if missing:
            print(f"FATAL: --ai-verdict requires: {', '.join(missing)}",
                  file=sys.stderr)
            return 2
        if args.image == DEFAULT_IMAGE:      # not overridden -> use the AI image
            args.image = AI_VERDICT_IMAGE
    else:
        missing = [k for k, v in (("--model", args.model),
                                  ("--gate-rows", args.gate_rows),
                                  ("--run-tag", args.run_tag)) if not v]
        if missing:
            print(f"FATAL: the X/readout lane requires: {', '.join(missing)}",
                  file=sys.stderr)
            return 2

    tok = os.environ.get("HF_TOKEN")
    if not tok and not args.dry_run:
        print("FATAL: HF_TOKEN not in environment", file=sys.stderr)
        return 2

    command = (build_ai_verdict_command(args) if args.ai_verdict
               else build_command(args, extract_args))
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
        env={"HF_HUB_ENABLE_HF_TRANSFER": "0",
             **({"LOG_PUSH_INTERVAL": str(args.log_push_interval)}
                if args.log_push_interval else {})},
    )
    print(f"[launch] job id: {job.id}")
    print(f"[launch] url:    {getattr(job, 'url', '(see hf.co/jobs)')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
