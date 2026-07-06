"""Modal port of the TODO item-11 GPU batching-equivalence self-check.

Runs experiment/phase1/probe/steering/gpu_equivalence_cell.py on an A10G against
the DEPLOYED Qwen3-4B clean-SFT->GRPO-v2 lineage (merged-16bit base + grpo-v2
LoRA at a pinned revision), at the caution_perp direction's best_layer. It
verifies the batched final-position + per-element-alpha SteeringHook edit matches
the one-prompt-at-a-time reference to the model's bf16 numeric floor. A PASS
un-gates Amendment AK Stage 2 (the batching-engine parity mandate, AK §3.2).

Modeled directly on modal_ak_stage1.py: detached app, entrypoint([]) fix, the
AL/AK image pins + xet mitigation, repo-clone-at-pinned-commit, .spawn() (not
.remote()) so a dying client has no in-flight input to cancel. This job is ~5
min, so no Volume checkpoint daemon; it just uploads the result JSON + a log tail
to the private staging dataset and writes a DONE marker line.

Launch DETACHED so the app survives client death:
    modal run --detach modal_item11_equivalence.py
(HF_TOKEN must be exported in the launching env; forwarded as a scoped Secret.)

The shipped direction JSON (unit-normalized caution_perp preimage, best_layer=34)
travels inside the repo clone at the pinned commit, under
experiment/phase1/probe/steering/directions/qwen3-4b-grpo-v2/direction_caution.json
(+ .npy). Both HF model repos below are PRIVATE; HF_TOKEN must have read access.
"""

import os

import modal

# --- parity constants (from modal_ak_stage1.py) ---
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
# Pin to the lab-diagnostics-bundle commit that carries this app + the shipped
# direction JSON + the confidence_steer adapter support. Filled at push time.
REPO_COMMIT = "1f538c73164b64f3ff36397346aaf507a2934d87"  # r1 fix: delta-based equivalence cell
STAGING_REPO = "professorsynapse/eh-al-prep-staging"

# Deployed clean-SFT->GRPO-v2 seed1 lineage (the production steering surface).
BASE_MODEL = "professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit"
ADAPTER_REPO = "professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora"
ADAPTER_REV = "8914081dfcec4f1f025f2dbe4195d4f7aa8d210e"

# Shipped direction (unit-normalized caution_perp preimage, best_layer=34).
DIRECTION_IN_REPO = ("experiment/phase1/probe/steering/directions/"
                     "qwen3-4b-grpo-v2/direction_caution.json")
FLOOR = 1e-2  # bf16 batched-vs-unbatched numeric floor; cell exits nonzero above.

AI_VERDICT_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
AI_VERDICT_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml", "peft"]

HOURS = 60 * 60

image = (
    modal.Image.from_registry(AI_VERDICT_IMAGE, add_python=None)
    .entrypoint([])
    .pip_install(*AI_VERDICT_PIP)
    .apt_install("git")
    # HF_HUB_DISABLE_XET=1 is load-bearing (see AK/AL comment): the xet CAS
    # backend stalls without timeout on multi-GB pulls; route through the classic
    # resolve endpoint. hf_transfer off too (unsloth force-enables; no-op once
    # xet is off).
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-item11-equivalence", image=image)

vol = modal.Volume.from_name("eh-item11-logs", create_if_missing=True)
VOL_MOUNT = "/vol/item11logs"
RUN_TAG = "item11-gpu-equivalence-r1"


@app.function(
    gpu="A10G",
    timeout=1 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_equivalence():
    import shutil
    import subprocess
    import sys
    import time

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"

    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT is a placeholder; pin the pushed commit "
                           "before launch")

    def sh(cmd, cwd=None, check=True):
        print(f"[modal-item11] $ {' '.join(cmd)}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}")
        return r.returncode

    out = f"/tmp/{RUN_TAG}"
    os.makedirs(out, exist_ok=True)
    boot_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    job_log = f"{out}/job_log_{boot_id}.txt"
    result_json = f"{out}/result.json"

    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    # 1. clone repo at the pinned commit (ships the cell + direction JSON).
    # Idempotent: a retry lands on a warm container where the clone exists.
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "origin"], cwd=workspace, check=False)
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)

    probe = os.path.join(workspace, "experiment/phase1/probe")
    cell = os.path.join(probe, "steering/gpu_equivalence_cell.py")
    direction = os.path.join(workspace, DIRECTION_IN_REPO)
    upload = os.path.join(probe, "cloud/upload_result.py")

    if not os.path.isfile(direction):
        raise RuntimeError(f"shipped direction not found at pinned commit: "
                           f"{direction}")

    # 2. run the cell (guard flag REQUIRED; adapter attached; nonzero on FAIL)
    t0 = time.time()
    log_fh = open(job_log, "w")
    log_fh.write(f"run_tag={RUN_TAG} boot={boot_id}\n"
                 f"base={BASE_MODEL} adapter={ADAPTER_REPO}@{ADAPTER_REV}\n"
                 f"direction={DIRECTION_IN_REPO} floor={FLOOR}\n"
                 f"repo@{REPO_COMMIT}\n\n")
    log_fh.flush()
    cmd = [sys.executable, cell,
           "--model", BASE_MODEL,
           "--adapter", ADAPTER_REPO,
           "--adapter-revision", ADAPTER_REV,
           "--direction", direction,
           "--device", "cuda", "--dtype", "bfloat16",
           "--floor", str(FLOOR),
           "--result-json", result_json,
           "--i-know-this-runs-on-gpu"]
    print(f"[modal-item11] $ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True)
    print(proc.stdout, flush=True)
    log_fh.write(proc.stdout)
    cell_rc = proc.returncode
    t_run = time.time() - t0
    log_fh.write(f"\ncell_returncode={cell_rc} run_sec={t_run:.1f}\n")

    passed = cell_rc == 0 and os.path.isfile(result_json)
    log_fh.write(f"DONE run_tag={RUN_TAG} boot={boot_id} "
                 f"passed={passed} run_sec={t_run:.1f}\n")
    log_fh.close()
    print(f"[modal-item11] DONE passed={passed} cell_rc={cell_rc} "
          f"run={t_run:.0f}s", flush=True)

    # 3. upload result JSON + log tail to the private staging dataset
    for f in (result_json, job_log):
        if os.path.isfile(f):
            sh([sys.executable, upload, "--repo", STAGING_REPO,
                "--path-prefix", RUN_TAG, "--file", f], check=False)

    # 4. Volume copy + DONE marker
    for src, name in ((result_json, "result.json"),
                      (job_log, os.path.basename(job_log))):
        if os.path.isfile(src):
            shutil.copyfile(src, f"{VOL_MOUNT}/{name}")
    with open(f"{VOL_MOUNT}/DONE", "w") as fh:
        fh.write(f"run_tag={RUN_TAG} boot={boot_id} passed={passed} "
                 f"run_sec={t_run:.1f}\n")
    vol.commit()
    print("[modal-item11] DONE marker written to volume", flush=True)

    if not passed:
        raise RuntimeError(
            f"item-11 equivalence FAILED (cell_rc={cell_rc}); divergence above "
            f"floor {FLOOR} or no result JSON. See {job_log}.")
    return {"status": "completed", "passed": passed,
            "run_sec": round(t_run, 1)}


@app.local_entrypoint()
def main():
    print(f"[modal-item11] launching item-11 equivalence on A10G, "
          f"run_tag={RUN_TAG}")
    print(f"[modal-item11] repo@{REPO_COMMIT[:12]} base={BASE_MODEL} "
          f"adapter={ADAPTER_REPO}@{ADAPTER_REV[:8]}")
    # .spawn(), not .remote(): the client exits right after scheduling, so a
    # dying client (graceful signal or not) has no in-flight input to cancel.
    # Requires --detach so the app outlives the client. Monitor via
    # `modal app logs` + the Volume DONE marker.
    call = run_equivalence.spawn()
    print(f"[modal-item11] spawned function call {call.object_id}; client "
          f"exiting. Monitor: modal app logs / volume DONE marker.")
