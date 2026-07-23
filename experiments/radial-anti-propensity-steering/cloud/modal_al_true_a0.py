"""Modal port of the RunPod TRUE A0 cloud-parity cell (Amendment AL prep) -- v2.

v2 = crash-proof relaunch of v1. The v1 run was cancelled at 1350/1662 rows
because plain `modal run` creates an EPHEMERAL app (dies with its launching
client) and all outputs lived on container-local /tmp so nothing survived.

v2 changes (ALL v1 parity constants / image pins / xet mitigation / RUN_TAG /
entrypoint([]) fix are preserved verbatim):
  1. @app.function gets retries so a container death respawns the function.
  2. Reuse the existing Volume eh-al-true-a0-logs; CKPT = {VOL_MOUNT}/ckpt/{RUN_TAG}.
  3. On (re)start, restore CKPT's gen/data + extract/data into the local out dirs
     so the job script's NATIVE resume (config_sha match + present safetensors)
     skips completed work.
  4. A daemon thread mirrors the local gen_dir + ext_dir into CKPT every 120s
     (full rows.jsonl/manifest.json copies + only-new safetensors) then
     vol.commit(); every exception is caught so a bad checkpoint never kills the
     run. A synchronous checkpoint also runs right after each stage.
  5. After the final HF uploads succeed, a DONE marker is written into CKPT.

Launch DETACHED so the app survives client death:
    modal run --detach experiments/radial-anti-propensity-steering/cloud/modal_al_true_a0.py
(HF_TOKEN must be exported in the launching env; forwarded as a scoped Secret.)
"""

import os

import modal

# --- parity constants (from runpod_al_true_a0.sh + launch_hf_job.py) ---
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
REPO_COMMIT = "c26996034256a90ff7bf6bea9f36d4fc6bb45759"
STAGING_REPO = "professorsynapse/eh-al-prep-staging"
BASE_MODEL = "professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit"
ADAPTER_REPO = "professorsynapse/eh-qwen3-4b-clean-sft-grpo-par-true-seed1-lora"
ADAPTER_REV = "7e31d3cf62395275d4ba3d1d9ec8f95287188805"
POOL_IN_REPO = "pools/a0_pool_v21_questions.jsonl"
RUN_TAG = "al-prep-true-a0-modal"  # -modal: never collide with the RunPod run
NUM_LAYERS = 36

# The AI-verdict cell's pinned Unsloth image (sensor-v2 serving lineage) +
# the small CPU-side deps it imports. huggingface_hub kept <1.0 per the pin.
AI_VERDICT_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
AI_VERDICT_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml"]

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120

image = (
    # The Unsloth image ships an ENTRYPOINT that launches supervisord
    # (Jupyter/SSH/Ollama) for interactive use; on Modal that hijacks the
    # container so our function never runs. entrypoint([]) clears it.
    modal.Image.from_registry(AI_VERDICT_IMAGE, add_python=None)
    .entrypoint([])
    .pip_install(*AI_VERDICT_PIP)
    .apt_install("git")
    # Force plain-HTTP downloads. The real hang is hf_xet (the CAS backend that
    # SUPERSEDES hf_transfer): its Rust client stalls without timeout in xet_get
    # on multi-GB pulls of this repo (froze at ~5GB here and killed the parallel
    # RunPod run). HF_HUB_DISABLE_XET=1 routes through the classic resolve
    # endpoint (healthy single-stream). Keep HF_HUB_ENABLE_HF_TRANSFER=0 too
    # (unsloth force-enables it; it is a no-op once xet is off but harmless).
    # Baked into the image env so both are live before unsloth imports.
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-al-true-a0", image=image)

# Modal-native scratch store for logs + manifests (demonstrates the Volume path)
vol = modal.Volume.from_name("eh-al-true-a0-logs", create_if_missing=True)
VOL_MOUNT = "/vol/allogs"
CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"


@app.function(
    gpu="A10G",
    timeout=3 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    # v2: respawn the function if the container dies mid-run. Native job resume
    # + volume checkpoint means a respawn continues from the last committed rows.
    retries=modal.Retries(max_retries=3, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_true_a0():
    import shutil
    import subprocess
    import sys
    import threading
    import time

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    # Hard-off the xet CAS backend + hf_transfer (see image comment): force both
    # even if the image env layer is bypassed, so subprocesses inherit them
    # before unsloth imports. HF_HUB_DISABLE_XET is the load-bearing one.
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"

    def sh(cmd, cwd=None, check=True):
        print(f"[modal-a0] $ {' '.join(cmd)}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}")
        return r.returncode

    out = f"/tmp/{RUN_TAG}"
    os.makedirs(out, exist_ok=True)
    gen_dir = f"{out}/gen/data"
    ext_dir = f"{out}/extract/data"
    os.makedirs(gen_dir, exist_ok=True)
    os.makedirs(ext_dir, exist_ok=True)

    # CKPT subtrees mirror the local out subtrees exactly.
    ckpt_gen = f"{CKPT}/gen/data"
    ckpt_ext = f"{CKPT}/extract/data"

    # --- v2 restore: pull any prior checkpoint into the local out dirs so the
    # job script's native resume kicks in. -------------------------------------
    def _copy_tree_into(src, dst):
        """Copy every file under src into dst (creating dst), overwriting."""
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
        print(f"[modal-a0] vol.reload() at restore failed (non-fatal): {e}",
              flush=True)
    restored = 0
    if os.path.isdir(CKPT):
        restored += _copy_tree_into(ckpt_gen, gen_dir)
        restored += _copy_tree_into(ckpt_ext, ext_dir)
    print(f"[modal-a0] restore: {restored} files restored from checkpoint "
          f"(CKPT={CKPT})", flush=True)

    # --- v2 checkpoint primitive: mirror a local out subtree into its CKPT
    # subtree cheaply (full copy of rows.jsonl/manifest.json; only-new
    # safetensors), via temp-name + atomic rename, no long-lived handles. ------
    def _mirror_subtree(local_dir, ckpt_dir):
        if not os.path.isdir(local_dir):
            return
        os.makedirs(ckpt_dir, exist_ok=True)
        for fn in os.listdir(local_dir):
            src = os.path.join(local_dir, fn)
            if not os.path.isfile(src):
                continue
            dst = os.path.join(ckpt_dir, fn)
            # only-new safetensors: skip if already present in CKPT (they are
            # immutable per safe_key). Always refresh rows.jsonl/manifest.json.
            if fn.endswith(".safetensors") and os.path.isfile(dst):
                continue
            tmp = dst + ".tmp"
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)  # atomic

    def checkpoint_once(tag=""):
        try:
            _mirror_subtree(gen_dir, ckpt_gen)
            _mirror_subtree(ext_dir, ckpt_ext)
            vol.commit()
            print(f"[modal-a0] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-a0] checkpoint FAILED (non-fatal) {tag}: {e}",
                  flush=True)

    stop_ckpt = threading.Event()

    def _ckpt_loop():
        while not stop_ckpt.wait(CKPT_INTERVAL_SEC):
            checkpoint_once(tag="(periodic)")

    ckpt_thread = threading.Thread(target=_ckpt_loop, daemon=True)
    ckpt_thread.start()

    # 1. clone repo at the pinned commit
    sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)

    probe = os.path.join(workspace, "archive/experiment/phase1/probe")
    script = os.path.join(probe, "amendment_ai_verdict_extract_gen.py")
    upload = os.path.join(probe, "cloud/upload_result.py")

    boot_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    job_log = f"{out}/job_log_{boot_id}.txt"

    # nvidia-smi banner (parity with the RunPod wrapper)
    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    # fetch the pool from the private staging dataset
    pool_local = f"{out}/pool.jsonl"
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO,
                        repo_type="dataset")
    shutil.copyfile(p, pool_local)
    print(f"[modal-a0] fetched pool {STAGING_REPO}:{POOL_IN_REPO} -> {pool_local}",
          flush=True)

    layer_list = ",".join(f"L{i}" for i in range(NUM_LAYERS + 1))

    t0 = time.time()
    # stage 1: generation (raw rows incl. answer_text; graded locally later)
    sh([sys.executable, script, "--stage", "generate", "--pool", pool_local,
        "--base-model", BASE_MODEL,
        "--adapter-repo", ADAPTER_REPO, "--adapter-revision", ADAPTER_REV,
        "--out-dir", gen_dir])
    if not os.path.isfile(f"{gen_dir}/rows.jsonl"):
        raise RuntimeError("no gen rows")
    t_gen = time.time() - t0
    checkpoint_once(tag="(post-generate)")

    # stage 2: full-stack pre-gen extraction (L0..L36)
    t1 = time.time()
    sh([sys.executable, script, "--stage", "extract", "--surface", "union",
        "--pool", pool_local, "--base-model", BASE_MODEL,
        "--adapter-repo", ADAPTER_REPO, "--adapter-revision", ADAPTER_REV,
        "--layers", layer_list, "--out-dir", ext_dir])
    if not os.path.isfile(f"{ext_dir}/manifest.json"):
        raise RuntimeError("no extract manifest")
    t_ext = time.time() - t1
    checkpoint_once(tag="(post-extract)")

    # upload: gen dir as files, extract dir as one tarball
    for f in (f"{gen_dir}/rows.jsonl", f"{gen_dir}/manifest.json"):
        sh([sys.executable, upload, "--repo", STAGING_REPO,
            "--path-prefix", f"{RUN_TAG}/gen", "--file", f])
    tarball = f"{out}/extract_data.tar.gz"
    sh(["tar", "-C", f"{out}/extract", "-czf", tarball, "data"])
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{RUN_TAG}/extract", "--file", tarball])

    # write log + manifest copies to the Modal Volume (native storage demo)
    with open(job_log, "w") as fh:
        fh.write(f"run_tag={RUN_TAG} boot={boot_id}\n"
                 f"gen_sec={t_gen:.1f} extract_sec={t_ext:.1f}\n"
                 f"pool={STAGING_REPO}:{POOL_IN_REPO}\n"
                 f"base={BASE_MODEL} adapter={ADAPTER_REPO}@{ADAPTER_REV}\n")
    for src, name in ((job_log, os.path.basename(job_log)),
                      (f"{gen_dir}/manifest.json", "gen_manifest.json"),
                      (f"{ext_dir}/manifest.json", "extract_manifest.json")):
        if os.path.isfile(src):
            shutil.copyfile(src, f"{VOL_MOUNT}/{name}")
    vol.commit()

    # also push the job log to the staging repo (parity with the wrapper)
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{RUN_TAG}/logs", "--file", job_log], check=False)

    # v2: stop the periodic thread, final checkpoint, DONE marker.
    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    checkpoint_once(tag="(final)")
    try:
        os.makedirs(CKPT, exist_ok=True)
        with open(f"{CKPT}/DONE", "w") as fh:
            fh.write(f"run_tag={RUN_TAG} boot={boot_id} "
                     f"gen_sec={t_gen:.1f} extract_sec={t_ext:.1f}\n")
        vol.commit()
        print("[modal-a0] DONE marker written to CKPT", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-a0] DONE marker write failed (non-fatal): {e}", flush=True)

    print(f"[modal-a0] DONE gen={t_gen:.0f}s extract={t_ext:.0f}s "
          f"total={time.time()-t0:.0f}s", flush=True)
    return {"status": "completed", "gen_sec": round(t_gen, 1),
            "extract_sec": round(t_ext, 1)}


@app.local_entrypoint()
def main():
    print(f"[modal-a0] launching TRUE A0 parity cell on A10G, run_tag={RUN_TAG}")
    print(f"[modal-a0] repo@{REPO_COMMIT[:12]} pool={POOL_IN_REPO}")
    result = run_true_a0.remote()
    print(f"[modal-a0] result: {result}")
