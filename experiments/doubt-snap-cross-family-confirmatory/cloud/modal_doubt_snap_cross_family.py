"""Thin Modal fan-out wrapper for tuner-backed doubt-snap cells.

This wrapper owns cloud process shape only. It clones the EHR repo at an exact
commit, initializes the pinned Synaptic-Tuner submodule, then runs one complete
cell: baseline mining/capture, FIT dose sweep, dose selection, held-out
steering, and scoring. Model work stays delegated to Synaptic-Tuner verbs.
Per-cell analysis directories are symlinked onto the Modal volume before GPU
work starts so tuner-level `--resume` can survive worker preemption.
"""

from __future__ import annotations

import os

import modal


REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
EXPERIMENT_SLUG = "doubt-snap-cross-family-confirmatory"
RUN_TAG = "doubt-snap-cross-family-r1"

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

app = modal.App("eh-doubt-snap-cross-family", image=image)
vol = modal.Volume.from_name("eh-doubt-snap-cross-family", create_if_missing=True)
VOL_MOUNT = "/vol/doubt_snap_cross_family"


@app.function(
    gpu="A100",
    timeout=8 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_one_cell(
    cell_id: str,
    repo_commit: str,
    only_step: str = "",
    from_step: str = "",
    batch_size: int = 8,
    dry_run: bool = False,
    smoke_only: bool = False,
) -> None:
    import re
    import json
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

    def sh(
        cmd: list[str],
        cwd: Path | None = None,
        check: bool = True,
        env: dict[str, str] | None = None,
    ) -> None:
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", " ".join(cmd))
        print(f"[modal-doubt-snap] $ {printable}", flush=True)
        merged_env = {**os.environ, **(env or {})}
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=merged_env)
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
        print(
            f"[modal-doubt-snap] dry run: would prepare, dose, materialize, steer, score {cell_id}",
            flush=True,
        )
        return

    import yaml

    matrix = yaml.safe_load((exp_dir / "model_matrix.yaml").read_text())
    cells = {c["cell_id"]: c for c in matrix["cells"]}
    if cell_id not in cells:
        raise RuntimeError(f"unknown cell_id: {cell_id}")
    cell = cells[cell_id]
    env = {
        "PYTHONPATH": f"{exp_dir}{os.pathsep}{os.environ.get('PYTHONPATH', '')}",
        "DOUBT_SNAP_RENDER_MODEL": cell["repo"],
        "DOUBT_SNAP_RENDER_REVISION": cell["revision"],
    }

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
    print(f"[modal-doubt-snap] live analysis dirs mounted at {live_root}", flush=True)

    stop_commits = threading.Event()

    def periodic_volume_commit() -> None:
        while not stop_commits.wait(60.0):
            try:
                vol.commit()
                print("[modal-doubt-snap] periodic volume commit", flush=True)
            except Exception as exc:  # pragma: no cover - defensive cloud logging
                print(f"[modal-doubt-snap] periodic volume commit failed: {exc}", flush=True)

    commit_thread = threading.Thread(target=periodic_volume_commit, daemon=True)
    commit_thread.start()

    def stop_periodic_commits() -> None:
        stop_commits.set()
        commit_thread.join(timeout=5.0)

    def commit_outputs(status_marker: dict[str, object] | None = None) -> None:
        if status_marker is not None:
            cdir = exp_dir / "analysis-committed" / cell_id
            cdir.mkdir(parents=True, exist_ok=True)
            (cdir / "modal_status.json").write_text(
                json.dumps(status_marker, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        dst = Path(VOL_MOUNT) / RUN_TAG / cell_id
        dst.mkdir(parents=True, exist_ok=True)
        for target_name, rel in (
            (
                "analysis-committed",
                Path("experiments") / EXPERIMENT_SLUG / "analysis-committed" / cell_id,
            ),
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
        print(f"[modal-doubt-snap] committed outputs to {dst}", flush=True)

    if smoke_only:
        smoke = exp_dir / "smoke_tuner_path.py"
        sh(
            [
                sys.executable,
                str(smoke),
                f"--cell-id={cell_id}",
                f"--batch-size={min(batch_size, 2)}",
            ],
            cwd=workspace,
            env=env,
        )
        dst = Path(VOL_MOUNT) / RUN_TAG / cell_id / "modal_harness_smoke"
        dst.mkdir(parents=True, exist_ok=True)
        src = exp_dir / "analysis" / cell_id / "modal_harness_smoke"
        target = dst / "analysis"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
        vol.commit()
        print(f"[modal-doubt-snap] committed smoke outputs to {dst}", flush=True)
        stop_periodic_commits()
        return

    prep = exp_dir / "prep_tuner_cell.py"
    sh(
        [
            sys.executable,
            str(prep),
            "prepare",
            f"--cell-id={cell_id}",
            f"--batch-size={batch_size}",
        ],
        cwd=workspace,
        env=env,
    )

    dose_cfg = exp_dir / "analysis" / cell_id / "steer_dose_fit.yaml"
    sh(
        [
            sys.executable,
            str(workspace / "synaptic-tuner" / "tuner.py"),
            "mechinterp",
            "steer",
            "--mi-config",
            str(dose_cfg),
            "--model",
            cell["repo"],
            "--model-revision",
            cell["revision"],
            "--i-know-this-runs-on-gpu",
        ],
        cwd=workspace,
        env=env,
    )
    dose_select_rc = sh(
        [sys.executable, str(prep), "select-dose", f"--cell-id={cell_id}"],
        cwd=workspace,
        env=env,
        check=False,
    )
    dose_fit_path = exp_dir / "analysis-committed" / cell_id / "dose_fit.json"
    dose_fit = json.loads(dose_fit_path.read_text(encoding="utf-8"))
    if dose_fit.get("selected_dose") is None:
        commit_outputs(
            {
                "cell_id": cell_id,
                "status": "failed",
                "failure_stage": "fit_dose_selection",
                "reason": "no_registered_candidate_dose_met_fit_selection_criteria",
                "dose_select_exit_code": dose_select_rc,
            }
        )
        print(
            f"[modal-doubt-snap] {cell_id}: no selected FIT dose; committed artifacts and stopping cell",
            flush=True,
        )
        stop_periodic_commits()
        return
    if dose_select_rc != 0:
        raise RuntimeError(f"select-dose failed ({dose_select_rc}) despite selected dose")

    materializer = exp_dir / "materialize_tuner_cells.py"
    sh(
        [
            sys.executable,
            str(materializer),
            f"--cell-id={cell_id}",
            f"--batch-size={batch_size}",
        ],
        cwd=workspace,
        env=env,
    )

    pipeline = exp_dir / "analysis" / cell_id / "pipeline.yaml"
    cmd = [
        sys.executable,
        str(workspace / "synaptic-tuner" / "tuner.py"),
        "mechinterp",
        "run",
        "--config",
        str(pipeline),
        "--provider",
        "local",
        "--yes",
        "--i-know-this-runs-on-gpu",
    ]
    if only_step:
        cmd.extend(["--only-step", only_step])
    if from_step:
        cmd.extend(["--from-step", from_step])
    sh(cmd, cwd=workspace, env=env)

    sh(
        [sys.executable, str(prep), "score-heldout", f"--cell-id={cell_id}"],
        cwd=workspace,
        env=env,
    )

    commit_outputs({"cell_id": cell_id, "status": "completed"})
    stop_periodic_commits()


@app.local_entrypoint()
def main(
    cell_ids: str,
    only_step: str = "",
    from_step: str = "",
    batch_size: int = 8,
    dry_run: bool = False,
    smoke_only: bool = False,
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
            only_step=only_step,
            from_step=from_step,
            batch_size=batch_size,
            dry_run=dry_run,
            smoke_only=smoke_only,
        )
        print(f"spawned {cid} only_step={only_step} from_step={from_step} smoke_only={smoke_only}", flush=True)
