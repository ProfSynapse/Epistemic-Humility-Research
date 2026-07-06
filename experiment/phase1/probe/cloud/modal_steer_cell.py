"""Generic Modal wrapper for a declarative steer-cell (any amendment).

ONE parameterized wrapper: it clones the research repo at a pinned commit, then
runs experiment/phase1/probe/steering/steer_cell.py against a config that lives
inside the repo at that commit, checkpointing the untracked provenance to a Modal
Volume and uploading the small result artifacts to a staging dataset. No
per-amendment constants live in this file; everything comes from the launch
flags. This is the hardened pattern from modal_al_true_a0.py / modal_ak_stage1.py
(detach-survivable app, retries, idempotent clone-at-pin, xet guards, Volume DONE
marker, incremental commits) with the cell-specific bits parameterized.

Launch DETACHED so the app survives client death:

  HF_TOKEN=... modal run --detach modal_steer_cell.py \
    --config experiment/phase1/probe/steering/configs/my_cell.yaml \
    --repo-commit <40-hex> \
    --staging-prefix professorsynapse/eh-<amendment>-staging \
    --arm primary --gpu A10G

The --config path is interpreted INSIDE the cloned repo at --repo-commit, so the
exact signed cell.yaml (whose sha the amendment pinned) is what runs. Pass --arm
to run one arm, or omit it to run every arm (each arm needs a passed smoke on
record; pass --smoke to run the smoke pass that records it, or --force-no-smoke).
"""
from __future__ import annotations

import os

import modal

REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"

# Pinned Unsloth serving image + small CPU deps, matching the AL/AK wrappers. The
# xet CAS backend is disabled in the image env (see modal_al_true_a0.py for why:
# hf_xet stalls without timeout on multi-GB pulls). huggingface_hub kept <1.0.
STEER_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
STEER_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml"]

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120

image = (
    modal.Image.from_registry(STEER_IMAGE, add_python=None)
    .entrypoint([])  # clear the supervisord entrypoint so our fn runs
    .pip_install(*STEER_PIP)
    .apt_install("git")
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-steer-cell", image=image)
vol = modal.Volume.from_name("eh-steer-cell-logs", create_if_missing=True)
VOL_MOUNT = "/vol/steerlogs"


@app.function(
    timeout=6 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=3, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_cell(config_path: str, repo_commit: str, staging_prefix: str,
             arm: str | None, smoke: bool, force_no_smoke: bool,
             run_tag: str):
    import shutil
    import subprocess
    import sys
    import threading
    import time

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"

    def sh(cmd, cwd=None, check=True):
        print(f"[modal-steer] $ {' '.join(cmd)}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}")
        return r.returncode

    ckpt = f"{VOL_MOUNT}/ckpt/{run_tag}"

    def _copy_tree_into(src, dst):
        n = 0
        if not os.path.isdir(src):
            return 0
        for root, _dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            tgt = dst if rel == "." else os.path.join(dst, rel)
            os.makedirs(tgt, exist_ok=True)
            for fn in files:
                shutil.copyfile(os.path.join(root, fn), os.path.join(tgt, fn))
                n += 1
        return n

    # --- idempotent clone at the pinned commit (survives a container respawn) --
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "origin", repo_commit], cwd=workspace, check=False)
    sh(["git", "checkout", repo_commit], cwd=workspace)

    probe = os.path.join(workspace, "experiment/phase1/probe")
    steer = os.path.join(probe, "steering/steer_cell.py")
    upload = os.path.join(probe, "cloud/upload_result.py")
    cfg_in_repo = os.path.join(workspace, config_path)
    if not os.path.isfile(cfg_in_repo):
        raise RuntimeError(f"config not found at pinned commit: {config_path}")

    # the runner writes under analysis/steer_cells/<name>/ (untracked); resolve
    # its out_dir via `plan` so we mirror the right subtree.
    plan = subprocess.run(
        [sys.executable, steer, "plan", "--config", cfg_in_repo],
        cwd=probe, capture_output=True, text=True)
    print(plan.stdout, flush=True)
    import json as _json
    out_dir = _json.loads(plan.stdout)["out_dir"]

    # restore any prior provenance so the runner's resume skips completed rows
    restored = _copy_tree_into(f"{ckpt}/out", out_dir)
    print(f"[modal-steer] restored {restored} files from {ckpt}", flush=True)

    def checkpoint_once(tag=""):
        try:
            _copy_tree_into(out_dir, f"{ckpt}/out")
            vol.commit()
            print(f"[modal-steer] checkpoint {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 - never let a checkpoint kill the run
            print(f"[modal-steer] checkpoint FAILED (non-fatal) {tag}: {e}",
                  flush=True)

    stop = threading.Event()

    def _loop():
        while not stop.wait(CKPT_INTERVAL_SEC):
            checkpoint_once(tag="(periodic)")

    th = threading.Thread(target=_loop, daemon=True)
    th.start()

    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    cmd = [sys.executable, steer, "run", "--config", cfg_in_repo]
    if arm:
        cmd += ["--arm", arm]
    if smoke:
        cmd += ["--smoke"]
    if force_no_smoke:
        cmd += ["--force-no-smoke"]
    t0 = time.time()
    rc = sh(cmd, cwd=probe, check=False)
    checkpoint_once(tag="(post-run)")

    # upload the small artifacts (manifest, per-arm rows, readback, gates report)
    for root, _dirs, files in os.walk(out_dir):
        for fn in files:
            if fn.endswith((".json", ".jsonl")):
                rel = os.path.relpath(os.path.join(root, fn), out_dir)
                sh([sys.executable, upload, "--repo", staging_prefix,
                    "--path-prefix", f"{run_tag}/{os.path.dirname(rel) or 'root'}",
                    "--file", os.path.join(root, fn)], check=False)

    stop.set()
    th.join(timeout=30)
    checkpoint_once(tag="(final)")
    try:
        os.makedirs(ckpt, exist_ok=True)
        with open(f"{ckpt}/DONE", "w") as fh:
            fh.write(f"run_tag={run_tag} rc={rc} sec={time.time()-t0:.1f}\n")
        vol.commit()
    except Exception as e:  # noqa: BLE001
        print(f"[modal-steer] DONE marker failed (non-fatal): {e}", flush=True)

    print(f"[modal-steer] DONE rc={rc} {time.time()-t0:.0f}s", flush=True)
    return {"status": "completed" if rc == 0 else "nonzero", "rc": rc}


@app.local_entrypoint()
def main(config: str, repo_commit: str, staging_prefix: str,
         arm: str = "", smoke: bool = False, force_no_smoke: bool = False,
         gpu: str = "A10G", run_tag: str = ""):
    if not run_tag:
        # derive a stable tag from the config stem + commit prefix
        stem = os.path.splitext(os.path.basename(config))[0]
        run_tag = f"steer-{stem}-{repo_commit[:8]}"
    fn = run_cell.with_options(gpu=gpu)
    print(f"[modal-steer] launching {run_tag} on {gpu}, repo@{repo_commit[:12]} "
          f"config={config} arm={arm or '(all)'} smoke={smoke}")
    result = fn.remote(config, repo_commit, staging_prefix,
                       arm or None, smoke, force_no_smoke, run_tag)
    print(f"[modal-steer] result: {result}")
