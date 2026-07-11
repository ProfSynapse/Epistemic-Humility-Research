"""Modal harness -- H9 held-out extraction + generation + grading on AI-TRUE.

DRAFT SKELETON. Process shape (detached app, Volume checkpoint daemon, DONE
marker, launch guard) ported from
    experiments/j-space-localization-qwen3-4b/cloud/modal_jlens.py
and the repo-clone-at-pinned-commit shape from
    experiments/doubt-snap-cross-family-confirmatory/cloud/modal_doubt_snap_cross_family.py

WHAT IS DIFFERENT FROM BOTH EXEMPLARS: the AI-TRUE checkpoint is LOCAL (a
clean-SFT merged-16bit base + a GRPO LoRA adapter), not a hub repo. This harness
pulls the base and adapter from a PRIVATE HF staging repo the user uploads once
before launch (STAGING_REPO below), the same containment posture j-lens uses for
its source pool. Model weights are not dataset/question text, so staging them is
not a containment violation. No submodule is initialized (this is plain
transformers extraction + generation, not a tuner cell).

WHAT THE CONTAINER PRODUCES (written to the Modal Volume; pulled back with
`modal volume get eh-h9-holdout-logs ckpt/<RUN_TAG> <dest>`; no external upload
of outputs):
  - per-row pre-generation-anchor extraction (.safetensors, all 37 layers)
  - rows_graded.jsonl (behavior labels from the byte-identical AL A0 grader)
  - extraction + generation manifests
These are gitignored locally once pulled; only ID-manifests, fitted-JSON, and
the aggregate gate report ever get committed (see the experiment .gitignore).

LAUNCH SAFETY GATE (same pattern as the exemplars): refuses to spawn unless the
launch confirmation, the pre-registered cost cap, and the signed commit are all
set:
    export EHR_LAUNCH_OK=h9-propensity-reading-gate
    export MODAL_COST_CAP_USD=15
    export EHR_REPO_COMMIT=<signed commit sha>
    export HF_TOKEN=<token with read on the private staging repo>
    modal run --detach cloud/modal_h9_holdout.py
THE AGENT THAT WROTE THIS DID NOT RUN modal run: launch is reserved for the lead
after the user approves the spend (AMENDMENT.md section 7). This is prep only.

COST (AMENDMENT.md section 6.3): ~15 GPU-min active compute on a 3090 for 500
rows scales to ~20-30 GPU-min on an A10G + ~5-10 min checkpoint pull/load;
~$1-2 expected against a $15 cap.
"""
from __future__ import annotations

import os

import modal

REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
EXPERIMENT_SLUG = "h9-propensity-reading-gate"
RUN_TAG = "h9-holdout-r1"
MODAL_GPU = os.environ.get("H9_MODAL_GPU", "A10G")

# Private HF staging repo holding the AI-TRUE base + adapter (user uploads once
# before launch; see AMENDMENT.md section 6.2). Weights only, no question text.
STAGING_REPO = "professorsynapse/eh-h9-aitrue-staging"
BASE_SUBDIR = "base/merged-16bit"        # merged-16bit clean-SFT base
ADAPTER_SUBDIR = "adapter/final_model"   # amendment_ai_grpo_true_seed1 LoRA

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120
DEFAULT_TIMEOUT_HOURS = 2                 # generous for 500 rows + checkpoint pull
ASSUMED_A10G_USD_PER_HOUR = 1.50

image = (
    modal.Image.from_registry(
        "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update", add_python=None
    )
    .entrypoint([])
    .pip_install(
        "git+https://github.com/huggingface/transformers.git",
        "peft", "pyyaml", "safetensors", "scikit-learn", "accelerate",
        "huggingface_hub>=0.34,<1.0",
    )
    .apt_install("git")
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-h9-propensity-reading-gate", image=image)
vol = modal.Volume.from_name("eh-h9-holdout-logs", create_if_missing=True)
VOL_MOUNT = "/vol/h9logs"
CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"


@app.function(
    gpu=MODAL_GPU,
    timeout=DEFAULT_TIMEOUT_HOURS * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_h9_holdout(repo_commit: str) -> dict:
    import re
    import shutil
    import subprocess
    import sys
    import threading
    import time

    if not repo_commit or len(repo_commit) < 12:
        raise RuntimeError("EHR_REPO_COMMIT must pin the signed commit before launch")

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"
    out = f"/tmp/{RUN_TAG}"
    os.makedirs(out, exist_ok=True)
    os.makedirs(CKPT, exist_ok=True)

    def sh(cmd, cwd=None, check=True):
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", " ".join(cmd))
        print(f"[modal-h9] $ {printable}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode})")
        return r.returncode

    def checkpoint_once(tag=""):
        try:
            for fn in os.listdir(out):
                src = os.path.join(out, fn)
                if os.path.isfile(src):
                    tmp = os.path.join(CKPT, fn) + ".tmp"
                    shutil.copyfile(src, tmp)
                    os.replace(tmp, os.path.join(CKPT, fn))
            vol.commit()
            print(f"[modal-h9] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-h9] checkpoint FAILED (non-fatal) {tag}: {e}", flush=True)

    stop_ckpt = threading.Event()

    def _ckpt_loop():
        while not stop_ckpt.wait(CKPT_INTERVAL_SEC):
            checkpoint_once(tag="(periodic)")

    ckpt_thread = threading.Thread(target=_ckpt_loop, daemon=True)
    ckpt_thread.start()

    # 1. clone repo at the pinned signed commit (idempotent on retry).
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "--all", "--tags"], cwd=workspace, check=False)
    sh(["git", "checkout", repo_commit], cwd=workspace)

    exp_dir = os.path.join(workspace, "experiments", EXPERIMENT_SLUG)
    sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
       check=False)

    t0 = time.time()

    # 2. fetch the AI-TRUE base + adapter from the private staging repo.
    #    TODO(sign): hf_hub_download / snapshot_download of STAGING_REPO subdirs
    #    BASE_SUBDIR and ADAPTER_SUBDIR into container-local paths (never a repo
    #    path). Same call shape as modal_jlens.py's private-pool fetch.
    #
    # 3. run the H9 GPU harness (extraction + generation + grading) on the 500
    #    held-out rows. TODO(sign): call the in-repo harness entrypoint (a
    #    harness-builder task after signing), e.g.:
    #      python experiments/h9-propensity-reading-gate/gpu_extract_gen.py \
    #        --ids analysis-committed/holdout_draw/holdout_ids.jsonl \
    #        --base <base_local> --adapter <adapter_local> \
    #        --anchor prompt_len-1 --all-layers \
    #        --max-new-tokens 96 --greedy --out <out>
    #    Extraction: pre-generation anchor (prompt_len-1), all 37 layers,
    #    batch_size 1, forward-only. Generation: greedy, max_new_tokens 96,
    #    AL A0 system prompt. Grading: byte-identical AL A0 grader.
    #
    #    NOTE: holdout question TEXT is joined in at container time from the
    #    private staging pool keyed by row_key (never committed to the repo),
    #    mirroring the AL staging join (runpod_al_true_a0.sh). The committed
    #    holdout_ids.jsonl carries row_key + source + gold label only.
    raise NotImplementedError(
        "modal_h9_holdout draft skeleton: wire the staging fetch (step 2) and "
        "the GPU harness call (step 3) per the TODO(sign) blocks before launch."
    )

    t_total = time.time() - t0  # noqa: F841 (reached once steps 2-3 are wired)
    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    checkpoint_once(tag="(final)")
    with open(f"{CKPT}/DONE", "w") as fh:
        fh.write(f"run_tag={RUN_TAG}\n")
    vol.commit()
    return {"status": "completed"}


@app.local_entrypoint()
def main():
    launch_ok = os.environ.get("EHR_LAUNCH_OK")
    if launch_ok != EXPERIMENT_SLUG:
        raise SystemExit(
            f"[modal-h9] refusing to launch: set EHR_LAUNCH_OK={EXPERIMENT_SLUG!r} "
            f"(lead approval, relayed after user sign-off), got {launch_ok!r}.")
    cap_raw = os.environ.get("MODAL_COST_CAP_USD")
    if not cap_raw:
        raise SystemExit(
            "[modal-h9] refusing to launch: set MODAL_COST_CAP_USD (e.g. 15); "
            "this script does not hardcode a cap.")
    try:
        cap_usd = float(cap_raw)
    except ValueError:
        raise SystemExit(f"[modal-h9] MODAL_COST_CAP_USD={cap_raw!r} is not a number")
    repo_commit = os.environ.get("EHR_REPO_COMMIT")
    if not repo_commit:
        raise SystemExit("[modal-h9] set EHR_REPO_COMMIT to the signed commit sha")

    print(f"[modal-h9] cost cap ${cap_usd:.2f}; launching held-out extraction + "
          f"generation + grading on {MODAL_GPU}, run_tag={RUN_TAG}")
    print(f"[modal-h9] repo@{repo_commit[:12]} staging={STAGING_REPO}")
    call = run_h9_holdout.spawn(repo_commit)
    print(f"[modal-h9] spawned {call.object_id}; client exiting. Monitor: "
          f"modal app logs, or `modal volume get eh-h9-holdout-logs "
          f"ckpt/{RUN_TAG} <dest>` for progress/results.")
