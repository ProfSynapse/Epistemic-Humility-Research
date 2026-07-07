"""Modal fan-out wrapper for doubt-snap-cross-family-confirmatory.

Launch only after the amendment is signed and the repo commit is pinned:

    export EHR_LAUNCH_OK=doubt-snap-cross-family-confirmatory
    export MODAL_COST_CAP_USD=<approved cap>
    modal run --detach cloud/modal_doubt_snap_cross_family.py \
      --cell-id=qwen35_4b --cell-id=ministral3_8b_instruct

This wrapper deliberately supports multiple `--cell-id` values. Each selected
cell is spawned as its own detached Modal function so model families run in
parallel. Inside the cell, the registered pipeline batches generation and hidden
state extraction according to `cell.yaml`.
"""

from __future__ import annotations

import os

import modal


REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
REPO_COMMIT = "REPLACE_WITH_SIGNED_COMMIT"
EXPERIMENT_SLUG = "doubt-snap-cross-family-confirmatory"
RUN_TAG = "doubt-snap-cross-family-r1"

IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
PIP = [
    "huggingface_hub>=0.34,<1.0",
    "pyyaml",
    "scikit-learn",
    "safetensors",
]
HOURS = 60 * 60

image = (
    modal.Image.from_registry(IMAGE, add_python=None)
    .entrypoint([])
    .pip_install(*PIP)
    .apt_install("git")
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-doubt-snap-cross-family", image=image)
vol = modal.Volume.from_name("eh-doubt-snap-cross-family-logs", create_if_missing=True)
VOL_MOUNT = "/vol/doubt_snap_cross_family"


@app.function(
    gpu="A10G",
    timeout=8 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_one_cell(cell_id: str, stage: str = "full", dry_run: bool = False) -> None:
    import re
    import subprocess
    import sys
    from pathlib import Path

    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT must be pinned to the signed commit before launch")

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

    workspace = Path("/workspace/ehr")

    def sh(cmd: list[str], cwd: Path | None = None, check: bool = True) -> None:
        printable = " ".join(cmd)
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", printable)
        print(f"[modal-doubt-snap] $ {printable}", flush=True)
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
        if check and result.returncode != 0:
            raise RuntimeError(f"command failed ({result.returncode})")

    if not (workspace / ".git").is_dir():
        sh(["git", "clone", REPO_URL, str(workspace)])
    sh(["git", "fetch", "--all", "--tags"], cwd=workspace, check=False)
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)

    exp_dir = workspace / "experiments" / EXPERIMENT_SLUG
    pipeline = exp_dir / "pipeline.py"
    cmd = [
        sys.executable,
        str(pipeline),
        "run-cell",
        f"--cell-id={cell_id}",
        f"--stage={stage}",
    ]
    if dry_run:
        cmd.append("--dry-run")
    sh(cmd, cwd=workspace)


@app.local_entrypoint()
def main(
    cell_id: list[str],
    stage: str = "full",
    dry_run: bool = False,
) -> None:
    if os.environ.get("EHR_LAUNCH_OK") != EXPERIMENT_SLUG:
        raise SystemExit(f"set EHR_LAUNCH_OK={EXPERIMENT_SLUG} before spawning")
    if not os.environ.get("MODAL_COST_CAP_USD"):
        raise SystemExit("set MODAL_COST_CAP_USD to the approved cap before spawning")
    if not cell_id:
        raise SystemExit("pass at least one --cell-id")
    for cid in cell_id:
        run_one_cell.spawn(cid, stage=stage, dry_run=dry_run)
        print(f"spawned {cid} stage={stage} dry_run={dry_run}", flush=True)
