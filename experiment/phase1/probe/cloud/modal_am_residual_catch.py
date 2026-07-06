"""Modal harness - Amendment AM residual-catch veto coverage (A0-surface extract).

Pre-registered: experiment/protocol/AMENDMENT-AM-residual-catch-veto-coverage.md
(SIGNED 2026-07-06; §3 design, §5 preconditions, $5 cap). Cloned from the
crash-proof modal_al_true_a0.py v2 skeleton (detached app, Volume checkpoint
daemon @120s, retries with restore-before-start native resume, DONE marker,
staging-repo upload) and the modal_ak_stage1.py .spawn() entrypoint.

AM-specific shape:
  * ONE stage: amendment_am_extract.py does the §5.3 numerics smoke (batch-1 vs
    batch-12 token agreement, bisect on divergence) THEN the full A0-surface
    regeneration + dual-position (pre/post) hidden-state extraction, all in one
    container pass. No separate generate/extract split.
  * Raw base only: unsloth/Qwen3-4B-bnb-4bit, NO adapter (the A0 arm surface).
  * The self-contained AM pool (question + aliases + gold_class + category_canon
    + score_L24) is built on the HOST by amendment_am_build_pool.py and uploaded
    to the staging repo under POOL_IN_REPO BEFORE launch; the container fetches
    it (the pool + its aliases are gitignored, so the repo clone lacks them).
  * Upload discipline: to keep the upload sane and never publish FalseQA text
    beyond the frozen A0 questions, the container uploads (a) rows.jsonl (graded
    per-row provenance) and manifest.json as files, and (b) ONLY the activation
    slice the analysis needs -- the L18..L24 window plus L35 for the post-L20
    layer sweep, pre and post positions -- as one tarball. The full L0..L36
    tensors stay on the Volume checkpoint (not uploaded).

Launch DETACHED so the app survives client death (see §5.2 -- wait for any
in-flight Modal app to finish first; local GPU is off limits, live AN run):
    modal run --detach modal_am_residual_catch.py
(HF_TOKEN must be exported in the launching env; forwarded as a scoped Secret.)

Monitor: `modal app logs` + the Volume checkpoint DONE marker. Completion = DONE.
"""

import os

import modal

# --- provenance pins (REPO_COMMIT filled in a second commit after the first
# AM commit lands, same REPLACE_WITH guard the AK/item-11 wrappers use) ---------
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
REPO_COMMIT = "091ab78dd789a533d319a4631312203a496bfc80"  # AM harness commit; re-pin if the branch moves
STAGING_REPO = "professorsynapse/eh-al-prep-staging"  # reuse the AL prep repo
POOL_IN_REPO = "am-residual-catch-r1/am_pool.jsonl"  # host-built, uploaded pre-launch
RESULT_PREFIX = "am-residual-catch-r1"               # staging path prefix for outputs
RAWBASE_MODEL = "unsloth/Qwen3-4B-bnb-4bit"
RUN_TAG = "am-residual-catch-r1"

# Activation layers uploaded (slice only; full L0..L36 stay on the Volume ckpt).
# L18..L24 window (the post-L20 peak neighborhood) + L35, for the layer sweep.
UPLOAD_LAYERS = [18, 19, 20, 21, 22, 23, 24, 35]

# Pinned Unsloth image (AL/AK lineage) + the small CPU deps the extract imports.
AI_VERDICT_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
AI_VERDICT_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml",
                  "safetensors"]

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120

image = (
    modal.Image.from_registry(AI_VERDICT_IMAGE, add_python=None)
    .entrypoint([])  # clear the supervisord ENTRYPOINT so our function runs
    .pip_install(*AI_VERDICT_PIP)
    .apt_install("git")
    # hf_xet hangs multi-GB pulls without timeout; force the classic resolve
    # endpoint. Baked into the image env so both are live before unsloth imports.
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-am-residual-catch", image=image)

vol = modal.Volume.from_name("eh-am-residual-catch-logs", create_if_missing=True)
VOL_MOUNT = "/vol/amlogs"
CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"


@app.function(
    gpu="A10G",  # doc allows T4/L4/A10G; A10G is the known-good (AL/AK lineage)
    timeout=3 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=3, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_am():
    import shutil
    import subprocess
    import sys
    import threading
    import time

    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT is a placeholder; pin the AM branch "
                           "commit before launch (second commit, guard pattern).")

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    # Force xet off / hf_transfer off even if the image env layer is bypassed, so
    # subprocesses inherit them before unsloth imports. (hf-xet-download-hang.)
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"

    def sh(cmd, cwd=None, check=True):
        # redact any hf_ token that could appear in an echoed command
        printable = " ".join(cmd)
        import re
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", printable)
        print(f"[modal-am] $ {printable}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode})")
        return r.returncode

    out = f"/tmp/{RUN_TAG}"
    os.makedirs(out, exist_ok=True)
    ext_dir = f"{out}/extract/data"
    os.makedirs(ext_dir, exist_ok=True)
    ckpt_ext = f"{CKPT}/extract/data"

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
        print(f"[modal-am] vol.reload() at restore failed (non-fatal): {e}",
              flush=True)
    restored = 0
    if os.path.isdir(CKPT):
        restored += _copy_tree_into(ckpt_ext, ext_dir)
    print(f"[modal-am] restore: {restored} files from checkpoint (CKPT={CKPT})",
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
            if fn.endswith(".safetensors") and os.path.isfile(dst):
                continue  # immutable per safe_key
            tmp = dst + ".tmp"
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)

    def checkpoint_once(tag=""):
        try:
            _mirror_subtree(ext_dir, ckpt_ext)
            vol.commit()
            print(f"[modal-am] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-am] checkpoint FAILED (non-fatal) {tag}: {e}", flush=True)

    stop_ckpt = threading.Event()

    def _ckpt_loop():
        while not stop_ckpt.wait(CKPT_INTERVAL_SEC):
            checkpoint_once(tag="(periodic)")

    ckpt_thread = threading.Thread(target=_ckpt_loop, daemon=True)
    ckpt_thread.start()

    # 1. clone repo at the pinned commit (idempotent: reuse an existing checkout
    #    on a retry rather than failing on a non-empty dir).
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "--all", "--tags"], cwd=workspace, check=False)
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)

    probe = os.path.join(workspace, "experiment/phase1/probe")
    script = os.path.join(probe, "amendment_am_extract.py")
    upload = os.path.join(probe, "cloud/upload_result.py")

    boot_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    job_log = f"{out}/job_log_{boot_id}.txt"

    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    # fetch the host-built self-contained pool from the private staging repo
    pool_local = f"{out}/am_pool.jsonl"
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO,
                        repo_type="dataset")
    shutil.copyfile(p, pool_local)
    print(f"[modal-am] fetched pool {STAGING_REPO}:{POOL_IN_REPO} -> {pool_local}",
          flush=True)

    # 2. smoke + full A0-surface regen + dual-position extract (one pass)
    t0 = time.time()
    sh([sys.executable, script, "--pool", pool_local,
        "--base-model", RAWBASE_MODEL, "--out-dir", ext_dir])
    if not os.path.isfile(f"{ext_dir}/manifest.json"):
        raise RuntimeError("no extract manifest")
    t_ext = time.time() - t0
    checkpoint_once(tag="(post-extract)")

    # 3. upload: rows.jsonl + manifest.json as files; a SLICE tarball of the
    #    UPLOAD_LAYERS activations (pre+post) to keep the upload sane. Full
    #    L0..L36 tensors remain on the Volume checkpoint.
    for f in (f"{ext_dir}/rows.jsonl", f"{ext_dir}/manifest.json"):
        if os.path.isfile(f):
            sh([sys.executable, upload, "--repo", STAGING_REPO,
                "--path-prefix", f"{RESULT_PREFIX}/extract", "--file", f])

    # build the layer-slice tarball with a tiny in-container safetensors reslice
    slice_dir = f"{out}/slice"
    os.makedirs(slice_dir, exist_ok=True)
    try:
        from safetensors.torch import load_file, save_file
        keep = {f"L{li}" for li in UPLOAD_LAYERS}
        n_sliced = 0
        for fn in os.listdir(ext_dir):
            if not fn.endswith(".safetensors"):
                continue
            full = load_file(os.path.join(ext_dir, fn))
            sub = {k: v for k, v in full.items() if k in keep}
            if sub:
                save_file(sub, os.path.join(slice_dir, fn))
                n_sliced += 1
        print(f"[modal-am] sliced {n_sliced} safetensors to layers {UPLOAD_LAYERS}",
              flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-am] slice step failed (non-fatal): {e}", flush=True)

    tarball = f"{out}/am_activations_slice.tar.gz"
    sh(["tar", "-C", out, "-czf", tarball, "slice"], check=False)
    if os.path.isfile(tarball):
        sh([sys.executable, upload, "--repo", STAGING_REPO,
            "--path-prefix", f"{RESULT_PREFIX}/extract", "--file", tarball],
           check=False)

    with open(job_log, "w") as fh:
        fh.write(f"run_tag={RUN_TAG} boot={boot_id}\n"
                 f"extract_sec={t_ext:.1f}\n"
                 f"pool={STAGING_REPO}:{POOL_IN_REPO}\n"
                 f"base={RAWBASE_MODEL} adapter=NONE-raw-instruct-base\n")
    shutil.copyfile(job_log, f"{VOL_MOUNT}/{os.path.basename(job_log)}")
    if os.path.isfile(f"{ext_dir}/manifest.json"):
        shutil.copyfile(f"{ext_dir}/manifest.json", f"{VOL_MOUNT}/extract_manifest.json")
    vol.commit()
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{RESULT_PREFIX}/logs", "--file", job_log], check=False)

    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    checkpoint_once(tag="(final)")
    try:
        os.makedirs(CKPT, exist_ok=True)
        with open(f"{CKPT}/DONE", "w") as fh:
            fh.write(f"run_tag={RUN_TAG} boot={boot_id} extract_sec={t_ext:.1f}\n")
        vol.commit()
        print("[modal-am] DONE marker written to CKPT", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-am] DONE marker write failed (non-fatal): {e}", flush=True)

    print(f"[modal-am] DONE extract={t_ext:.0f}s total={time.time()-t0:.0f}s",
          flush=True)
    return {"status": "completed", "extract_sec": round(t_ext, 1)}


@app.local_entrypoint()
def main():
    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise SystemExit("[modal-am] REPO_COMMIT is a placeholder; pin the AM "
                         "branch commit before launch (second commit).")
    print(f"[modal-am] launching AM residual-catch on A10G, run_tag={RUN_TAG}")
    print(f"[modal-am] repo@{REPO_COMMIT[:12]} pool={POOL_IN_REPO}")
    # .spawn(), not .remote(): the client exits right after scheduling, so a
    # dying client has no in-flight input to cancel. Requires --detach.
    call = run_am.spawn()
    print(f"[modal-am] spawned function call {call.object_id}; client exiting. "
          f"Monitor: modal app logs / volume ckpt DONE marker.")
