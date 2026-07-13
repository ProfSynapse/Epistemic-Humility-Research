"""Thin, capture-only Modal fan-out wrapper for jspace-family-atlas.

READ-ONLY mapping instrument: this wrapper never runs `mechinterp steer`,
never opens a write law, and never mutates the fleet's own volume namespace.
Per cell it:

1. Clones the EHR repo at an exact pinned commit and inits the pinned
   Synaptic-Tuner submodule (same pattern as
   doubt-snap-cross-family-confirmatory/cloud/modal_doubt_snap_cross_family
   .py).
2. Mounts the fleet's `eh-doubt-snap-cross-family` volume READ-ONLY as the
   source of `split_rows_private.jsonl` for the requested cell -- no writes
   are ever issued to that volume from this wrapper.
3. Mounts this experiment's own `eh-jspace-family-atlas` volume read-write,
   and symlinks this cell's `analysis/` and `analysis-committed/` dirs onto
   it before any GPU work starts, exactly like the fleet wrapper, so
   `batch-capture --resume` survives worker preemption.
4. Runs `capture_atlas_cell.py capture` (GPU: full-depth anchor capture),
   then `profile_and_read_panel.py score` (CPU: eff_dim_frac profile + read
   panel), then copies committed outputs back to the volume.

Launch guards mirror the fleet wrapper: EHR_LAUNCH_OK, MODAL_COST_CAP_USD,
and EHR_REPO_COMMIT (>=12 chars) must all be set before a function spawns.
This wrapper builds launch-readiness only; nothing in this repo runs it
without the lead relaying explicit user approval for the Modal spend.
"""

from __future__ import annotations

import os

import modal


REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
EXPERIMENT_SLUG = "jspace-family-atlas"
RUN_TAG = "jspace-family-atlas-r1"
MODAL_GPU = os.environ.get("JSPACE_ATLAS_MODAL_GPU", "A10G")

FLEET_VOLUME_NAME = "eh-doubt-snap-cross-family"
FLEET_RUN_TAG = "doubt-snap-cross-family-r1"
FLEET_VOL_MOUNT = "/vol/doubt_snap_cross_family_source"

IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
PIP = [
    "git+https://github.com/huggingface/transformers.git",
    "pyyaml",
    "pydantic",
    "safetensors",
    "scikit-learn",
    "accelerate",
]
HOURS = 60 * 60

image = (
    modal.Image.from_registry(IMAGE, add_python=None)
    .entrypoint([])
    .pip_install(*PIP)
    .apt_install("git")
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-jspace-family-atlas", image=image)
vol = modal.Volume.from_name("eh-jspace-family-atlas", create_if_missing=True)
fleet_vol = modal.Volume.from_name(FLEET_VOLUME_NAME, create_if_missing=False)
VOL_MOUNT = "/vol/jspace_family_atlas"


@app.function(
    gpu=MODAL_GPU,
    timeout=4 * HOURS,
    volumes={VOL_MOUNT: vol, FLEET_VOL_MOUNT: fleet_vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_one_cell(
    cell_id: str,
    repo_commit: str,
    batch_size: int = 8,
    dry_run: bool = False,
) -> None:
    import re
    import shutil
    import subprocess
    import sys
    import threading
    from pathlib import Path

    if not repo_commit or len(repo_commit) < 12:
        raise RuntimeError("EHR_REPO_COMMIT must pin the signed commit before launch")

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

    workspace = Path("/workspace/ehr")

    def sh(cmd: list[str], cwd: Path | None = None, check: bool = True) -> int:
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", " ".join(cmd))
        print(f"[modal-jspace-atlas] $ {printable}", flush=True)
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=os.environ.copy())
        if check and result.returncode != 0:
            raise RuntimeError(f"command failed ({result.returncode})")
        return result.returncode

    if not (workspace / ".git").is_dir():
        sh(["git", "clone", REPO_URL, str(workspace)])
    sh(["git", "fetch", "--all", "--tags"], cwd=workspace, check=False)
    sh(["git", "checkout", repo_commit], cwd=workspace)
    sh(["git", "submodule", "update", "--init", "synaptic-tuner"], cwd=workspace)

    exp_dir = workspace / "experiments" / EXPERIMENT_SLUG
    if dry_run:
        print(f"[modal-jspace-atlas] dry run: would capture + score {cell_id}", flush=True)
        return

    live_root = Path(VOL_MOUNT) / RUN_TAG / "_live" / cell_id

    def link_live_dir(link: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_symlink():
            if link.resolve() == target.resolve():
                return
            link.unlink()
        elif link.exists():
            if link.is_dir():
                shutil.copytree(link, target, dirs_exist_ok=True)
                shutil.rmtree(link)
            else:
                shutil.copy2(link, target / link.name)
                link.unlink()
        link.symlink_to(target, target_is_directory=True)

    link_live_dir(exp_dir / "analysis" / cell_id, live_root / "analysis")
    link_live_dir(exp_dir / "analysis-committed" / cell_id, live_root / "analysis-committed")
    vol.commit()
    print(f"[modal-jspace-atlas] live analysis dirs mounted at {live_root}", flush=True)

    stop_commits = threading.Event()

    def periodic_volume_commit() -> None:
        while not stop_commits.wait(60.0):
            try:
                vol.commit()
                print("[modal-jspace-atlas] periodic volume commit", flush=True)
            except Exception as exc:  # pragma: no cover - defensive cloud logging
                print(f"[modal-jspace-atlas] periodic volume commit failed: {exc}", flush=True)

    commit_thread = threading.Thread(target=periodic_volume_commit, daemon=True)
    commit_thread.start()

    def stop_periodic_commits() -> None:
        stop_commits.set()
        commit_thread.join(timeout=5.0)

    def commit_outputs() -> None:
        dst = Path(VOL_MOUNT) / RUN_TAG / cell_id
        dst.mkdir(parents=True, exist_ok=True)
        for target_name, rel in (
            ("analysis-committed", Path("experiments") / EXPERIMENT_SLUG / "analysis-committed" / cell_id),
            ("analysis", Path("experiments") / EXPERIMENT_SLUG / "analysis" / cell_id),
        ):
            src = workspace / rel
            if not src.exists():
                continue
            target = dst / target_name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src, target)
        vol.commit()
        print(f"[modal-jspace-atlas] committed outputs to {dst}", flush=True)

    # Fleet's row pool is READ-ONLY input; this path is never written to.
    row_pool = (
        Path(FLEET_VOL_MOUNT)
        / FLEET_RUN_TAG
        / "_live"
        / cell_id
        / "analysis"
        / "split_rows_private.jsonl"
    )
    if not row_pool.is_file():
        stop_periodic_commits()
        raise RuntimeError(
            f"fleet row pool not found at {row_pool}; the fleet's "
            f"{FLEET_VOLUME_NAME} volume must have a completed prepare step "
            f"for cell {cell_id!r} before the atlas can capture it."
        )

    capture_script = exp_dir / "capture_atlas_cell.py"
    sh(
        [
            sys.executable,
            str(capture_script),
            "capture",
            f"--cell-id={cell_id}",
            f"--row-pool={row_pool}",
            f"--batch-size={batch_size}",
        ],
        cwd=workspace,
    )

    score_script = exp_dir / "profile_and_read_panel.py"
    sh(
        [sys.executable, str(score_script), "score", f"--cell-id={cell_id}"],
        cwd=workspace,
    )

    commit_outputs()
    stop_periodic_commits()


@app.local_entrypoint()
def main(
    cell_ids: str,
    batch_size: int = 8,
    dry_run: bool = False,
) -> None:
    if os.environ.get("EHR_LAUNCH_OK") != EXPERIMENT_SLUG:
        raise SystemExit(f"set EHR_LAUNCH_OK={EXPERIMENT_SLUG} before spawning")
    if not os.environ.get("MODAL_COST_CAP_USD"):
        raise SystemExit("set MODAL_COST_CAP_USD to the approved cap before spawning")
    if not os.environ.get("EHR_REPO_COMMIT"):
        raise SystemExit("set EHR_REPO_COMMIT to the signed commit sha before spawning")
    ids = [c.strip() for c in cell_ids.split(",") if c.strip()]
    if not ids:
        raise SystemExit("pass at least one --cell-ids value")
    for cid in ids:
        run_one_cell.spawn(
            cid,
            os.environ["EHR_REPO_COMMIT"],
            batch_size=batch_size,
            dry_run=dry_run,
        )
        print(f"spawned {cid} batch_size={batch_size} dry_run={dry_run}", flush=True)
