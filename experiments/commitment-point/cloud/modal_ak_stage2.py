"""Modal port of the Amendment AK Stage 2 commitment-window steering (v1).

Built on modal_ak_stage1.py (which itself descends from the modal_al_true_a0
crash-proof skeleton): detached app, Volume checkpoint daemon @120s, retries with
restore-before-start, DONE marker, staging-repo upload, entrypoint([]) fix, xet
mitigation, clone-at-pinned-commit. All those parity constants are preserved.

AK Stage 2 differences from Stage 1:
  * INTERVENTION, not extraction. amendment_ak_stage2_steer.py registers the
    item-11-certified SteeringHook + GenerationHookController on the raw instruct
    base and generates the {+/- dir} x {anchor, gen_stream} x dose arms on the
    matched unanswerable rows, grading confab vs refuse per row.
  * Needs THREE staging inputs, not one: (1) the Stage 1 pool (confab labels +
    caution_dist_z), (2) the Stage 1 RAW-BASE tensors (the arm-B commitment
    direction is computed from <layer>@anchor), (3) the frozen AH answerability
    probes (the caution axis to orthogonalize against, B1 convention). All three
    already live in the AL/AK private staging repo; paths below.
  * Raw base only (doc §3.2: "raw instruct base primary"; grpo-v2 refit-and-steer
    is an authorized follow-on knob, not a gate surface, and is NOT wired here).
  * SMOKE pre-stage runs --smoke --limit 10 --alphas 1 first and asserts the
    readback check passed (commanded projection moves ~alpha*sigma at the steered
    position and ~0 elsewhere) before the full arm sweep.

Launch DETACHED so the app survives client death:
    modal run --detach experiments/commitment-point/cloud/modal_ak_stage2.py

(HF_TOKEN must be exported in the launching env; forwarded as a scoped Secret.)

LAUNCH GATES (unchanged standing rules): pool + Stage 1 raw-base tensors + AH
probes present in the private staging repo, Modal proven end-to-end, explicit
user GPU approval, and REPO_COMMIT pinned to the pushed AK branch commit (the
runtime guard below refuses a placeholder).
"""

import os

import modal

# --- parity constants (from modal_ak_stage1.py) ---
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
# Pin to the AK branch commit carrying amendment_ak_stage2_steer.py at launch
# time. Filled in a SECOND commit once the branch is pushed and the SHA exists;
# the runtime guard below refuses to run while this is a placeholder.
REPO_COMMIT = "3075518e10f3ea005d430f431dda4f61d4d5e837"  # carries the Stage 2 runner
STAGING_REPO = "professorsynapse/eh-al-prep-staging"  # reuse the AL/AK prep repo

# Stage 2 staging inputs (all already uploaded by the Stage 1 pipeline / prep).
POOL_IN_REPO = "pools/ak_stage1_pool.jsonl"
# Stage 1 raw-base tensors: the runner needs rows.jsonl + <safe_key>.safetensors
# under one dir. The Stage 1 Modal wrapper uploaded these as ak-stage1-raw-base-r1
# (rows.jsonl + a tensors tarball). We download the tarball + rows.jsonl and
# unpack them into one dir the runner reads via --stage1-dir.
STAGE1_RAWBASE_ROWS = "ak-stage1-raw-base-r1/data/rows.jsonl"
STAGE1_RAWBASE_TENSORS_TARBALL = "ak-stage1-raw-base-r1/tensors/ak_stage1_tensors.tar.gz"
# Frozen AH answerability probes (caution axis). Uploaded under this prefix by
# the AH prep; the runner reads probe_L<layer>.joblib from --probes-dir.
AH_PROBES_PREFIX = "ah_stage0/probes"
AH_PROBE_FILES = ("probe_L24.joblib",)  # steer layer default L24 (see runner)

# raw instruct base (arm-B native surface) -- public, launch-ready.
RAWBASE_MODEL = "unsloth/Qwen3-4B-bnb-4bit"

STEER_LAYER = "L24"
ALPHAS = "-2,-1,-0.5,0,0.5,1,2"
SMOKE_LIMIT = 10
SMOKE_ALPHAS = "1"

AI_VERDICT_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
AI_VERDICT_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml",
                  "safetensors"]

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120

image = (
    modal.Image.from_registry(AI_VERDICT_IMAGE, add_python=None)
    .entrypoint([])
    .pip_install(*AI_VERDICT_PIP)
    .apt_install("git")
    # HF_HUB_DISABLE_XET=1 routes around the xet CAS stall on multi-GB pulls;
    # hf_transfer off too (unsloth force-enables; no-op once xet is off).
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-ak-stage2", image=image)

vol = modal.Volume.from_name("eh-ak-stage2-logs", create_if_missing=True)
VOL_MOUNT = "/vol/aklogs"

RUN_TAG = "ak-stage2-raw-base-r1"


@app.function(
    gpu="A10G",
    timeout=8 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=3, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_stage2():
    import shutil
    import subprocess
    import sys
    import threading
    import time

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"
    run_tag = RUN_TAG
    ckpt = f"{VOL_MOUNT}/ckpt/{run_tag}"

    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT is a placeholder; pin the AK Stage 2 "
                           "branch commit before launch")

    def sh(cmd, cwd=None, check=True):
        print(f"[modal-ak2] $ {' '.join(cmd)}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}")
        return r.returncode

    out = f"/tmp/{run_tag}"
    os.makedirs(out, exist_ok=True)
    data_dir = f"{out}/data"
    os.makedirs(data_dir, exist_ok=True)
    ckpt_data = f"{ckpt}/data"

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

    try:
        vol.reload()
    except Exception as e:  # noqa: BLE001
        print(f"[modal-ak2] vol.reload() at restore failed (non-fatal): {e}",
              flush=True)
    restored = _copy_tree_into(ckpt_data, data_dir) if os.path.isdir(ckpt) else 0
    print(f"[modal-ak2] restore: {restored} files from checkpoint (ckpt={ckpt})",
          flush=True)

    def _mirror_subtree(local_dir, ckpt_dir):
        if not os.path.isdir(local_dir):
            return
        os.makedirs(ckpt_dir, exist_ok=True)
        for fn in os.listdir(local_dir):
            src = os.path.join(local_dir, fn)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(ckpt_dir, fn)
            tmp = dst + ".tmp"
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)

    def checkpoint_once(tag=""):
        try:
            _mirror_subtree(data_dir, ckpt_data)
            vol.commit()
            print(f"[modal-ak2] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[modal-ak2] checkpoint FAILED (non-fatal) {tag}: {e}",
                  flush=True)

    stop_ckpt = threading.Event()

    def _ckpt_loop():
        while not stop_ckpt.wait(CKPT_INTERVAL_SEC):
            checkpoint_once(tag="(periodic)")

    ckpt_thread = threading.Thread(target=_ckpt_loop, daemon=True)
    ckpt_thread.start()

    # 1. clone repo at the pinned commit. Idempotent: a retry lands on a warm
    # container where the clone already exists (the item-11 r1 lesson).
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "origin"], cwd=workspace, check=False)
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)

    probe = os.path.join(workspace, "archive/experiment/phase1/probe")
    script = os.path.join(probe, "amendment_ak_stage2_steer.py")
    upload = os.path.join(probe, "cloud/upload_result.py")

    boot_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    job_log = f"{out}/job_log_{boot_id}.txt"

    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    from huggingface_hub import hf_hub_download

    # 2. fetch the three staging inputs
    pool_local = f"{out}/pool.jsonl"
    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO,
                        repo_type="dataset")
    shutil.copyfile(p, pool_local)
    print(f"[modal-ak2] fetched pool {POOL_IN_REPO}", flush=True)

    # Stage 1 raw-base dir: rows.jsonl + unpacked tensors in one directory
    s1_dir = f"{out}/stage1_rawbase"
    os.makedirs(s1_dir, exist_ok=True)
    s1_rows = hf_hub_download(repo_id=STAGING_REPO,
                             filename=STAGE1_RAWBASE_ROWS, repo_type="dataset")
    shutil.copyfile(s1_rows, os.path.join(s1_dir, "rows.jsonl"))
    s1_tar = hf_hub_download(repo_id=STAGING_REPO,
                            filename=STAGE1_RAWBASE_TENSORS_TARBALL,
                            repo_type="dataset")
    sh(["tar", "-xzf", s1_tar, "-C", s1_dir])
    n_tensors = len([f for f in os.listdir(s1_dir) if f.endswith(".safetensors")])
    print(f"[modal-ak2] fetched Stage 1 raw-base rows + {n_tensors} tensors",
          flush=True)

    # AH probes (caution axis)
    probes_dir = f"{out}/ah_probes"
    os.makedirs(probes_dir, exist_ok=True)
    for fn in AH_PROBE_FILES:
        pf = hf_hub_download(repo_id=STAGING_REPO,
                            filename=f"{AH_PROBES_PREFIX}/{fn}",
                            repo_type="dataset")
        shutil.copyfile(pf, os.path.join(probes_dir, fn))
    print(f"[modal-ak2] fetched AH probes {AH_PROBE_FILES}", flush=True)

    common = [sys.executable, script, "--pool", pool_local,
              "--stage1-dir", s1_dir, "--probes-dir", probes_dir,
              "--base-model", RAWBASE_MODEL, "--steer-layer", STEER_LAYER]

    # --- SMOKE pre-stage: readback check on a small run, both position conds ---
    import json
    smoke_dir = f"{out}/smoke"
    sh(common + ["--smoke", "--limit", str(SMOKE_LIMIT),
                 "--alphas", SMOKE_ALPHAS, "--out-dir", smoke_dir])
    smoke_manifest = json.load(open(f"{smoke_dir}/manifest.json"))
    rb = smoke_manifest.get("readback", {})
    if not rb.get("passed"):
        raise RuntimeError(f"AK Stage 2 readback smoke FAILED: {rb}")
    print(f"[modal-ak2] readback smoke PASSED {rb}", flush=True)

    # --- FULL arm sweep (Volume checkpoint each 120s) ---
    # --alphas=<v> equals form: argparse rejects a separate value starting
    # with "-" ("expected one argument"), which killed r1's full sweep.
    t0 = time.time()
    sh(common + [f"--alphas={ALPHAS}", "--out-dir", data_dir])
    if not os.path.isfile(f"{data_dir}/manifest.json"):
        raise RuntimeError("no stage2 manifest")
    t_run = time.time() - t0
    checkpoint_once(tag="(post-run)")

    # upload rows + manifest + direction as files
    for f in (f"{data_dir}/rows.jsonl", f"{data_dir}/manifest.json",
              f"{data_dir}/direction.json"):
        if os.path.isfile(f):
            sh([sys.executable, upload, "--repo", STAGING_REPO,
                "--path-prefix", f"{run_tag}/data", "--file", f])
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{run_tag}/smoke", "--file",
        f"{smoke_dir}/manifest.json"], check=False)

    with open(job_log, "w") as fh:
        fh.write(f"run_tag={run_tag} boot={boot_id}\n"
                 f"run_sec={t_run:.1f}\n"
                 f"steer_layer={STEER_LAYER} alphas={ALPHAS}\n"
                 f"base={RAWBASE_MODEL}\n"
                 f"n_generations={smoke_manifest.get('n_generations','?')}(smoke)\n")
    for src, name in ((job_log, os.path.basename(job_log)),
                      (f"{data_dir}/manifest.json", "stage2_manifest.json")):
        if os.path.isfile(src):
            shutil.copyfile(src, f"{VOL_MOUNT}/{name}")
    vol.commit()
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{run_tag}/logs", "--file", job_log], check=False)

    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    checkpoint_once(tag="(final)")
    try:
        os.makedirs(ckpt, exist_ok=True)
        with open(f"{ckpt}/DONE", "w") as fh:
            fh.write(f"run_tag={run_tag} boot={boot_id} run_sec={t_run:.1f}\n")
        vol.commit()
        print("[modal-ak2] DONE marker written to ckpt", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-ak2] DONE marker write failed (non-fatal): {e}", flush=True)

    print(f"[modal-ak2] DONE run={t_run:.0f}s total={time.time()-t0:.0f}s",
          flush=True)
    return {"status": "completed", "run_sec": round(t_run, 1)}


@app.local_entrypoint()
def main():
    print(f"[modal-ak2] launching AK Stage 2 on A10G, run_tag={RUN_TAG}")
    print(f"[modal-ak2] repo@{REPO_COMMIT[:12]} steer_layer={STEER_LAYER} "
          f"alphas={ALPHAS}")
    # .spawn(), not .remote(): the client exits after scheduling, so a dying
    # client has no in-flight input to cancel. Requires --detach. Monitor via
    # `modal app logs` + the Volume checkpoint DONE marker.
    call = run_stage2.spawn()
    print(f"[modal-ak2] spawned function call {call.object_id}; client exiting. "
          f"Monitor: modal app logs / volume ckpt DONE marker.")
