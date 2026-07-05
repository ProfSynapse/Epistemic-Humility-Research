"""Modal port of the Amendment AK Stage 1 commitment-point extraction (v1).

Cloned from modal_al_true_a0.py (the crash-proof v2 skeleton): detached app,
Volume checkpoint daemon @120s, retries with restore-before-start native resume,
DONE marker, staging-repo upload. All the AL image pins / xet mitigation /
entrypoint([]) fix are preserved verbatim.

AK-specific differences from the AL skeleton:
  * ONE stage per run: amendment_ak_stage1_extract.py does generate + per-token
    capture in a single pass (not the AL two-stage generate/extract split).
  * Parameterized by CHECKPOINT ARM. `raw-base` runs the public raw instruct
    base with no adapter (arm-B's native surface, AK-G1 descriptive). `grpo-v2`
    runs the clean-SFT merged base with the trained grpo-v2 LoRA (the AK-G1 gate
    surface). Pick with the local_entrypoint --checkpoint arg.
  * A NUMERICS SMOKE pre-stage runs the runner at --limit 20 first and asserts
    the determinism spot-check passed before the full pool; the frozen
    generation batch size (1, greedy, decode-identical to arm-B) is recorded in
    the run's manifest. (AK Stage 1 batches only the capture forward pass, never
    generation; the smoke guards that the captured anchor/first-visible states
    are stable - the batch-1-vs-batch-N agreement contract is unit-tested in
    tests/test_ak_stage1_extract.py and re-asserted here on real GPU states.)

Launch DETACHED so the app survives client death:
    modal run --detach modal_ak_stage1.py --checkpoint raw-base
    modal run --detach modal_ak_stage1.py --checkpoint grpo-v2
(HF_TOKEN must be exported in the launching env; forwarded as a scoped Secret.)

grpo-v2 CHECKPOINT PROVENANCE IS AN OPEN ITEM: the deployed clean-SFT->GRPO-v2
base+adapter+revision are NOT yet fixed in this file. Fill GRPOV2_BASE_MODEL /
GRPOV2_ADAPTER_REPO / GRPOV2_ADAPTER_REV from the public-artifacts manifest (or
a private staging adapter) before launching the grpo-v2 arm. The raw-base arm is
fully specified and launch-ready.
"""

import os

import modal

# --- parity constants (from modal_al_true_a0.py) ---
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
# Pin to the AK branch commit at launch time (filled by the launch plan; the
# raw-base arm needs only the AK Stage 1 runner + pool builder, both on-branch).
REPO_COMMIT = "REPLACE_WITH_AK_BRANCH_COMMIT"
STAGING_REPO = "professorsynapse/eh-al-prep-staging"  # reuse the AL prep repo
# The Stage 1 pool the CPU builder emits, uploaded to the private staging repo.
POOL_IN_REPO = "pools/ak_stage1_pool.jsonl"

# raw-base arm (arm-B native surface) -- public, launch-ready.
RAWBASE_MODEL = "unsloth/Qwen3-4B-bnb-4bit"

# grpo-v2 arm (AK-G1 gate surface) -- provenance OPEN, fill before launch.
GRPOV2_BASE_MODEL = "professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit"
GRPOV2_ADAPTER_REPO = "REPLACE_WITH_GRPO_V2_LORA_REPO"
GRPOV2_ADAPTER_REV = "REPLACE_WITH_GRPO_V2_LORA_REVISION"

LAYERS = "L16,L20,L24,L28,L34"
ANSWER_STRIDE = 4
SMOKE_LIMIT = 20

AI_VERDICT_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
AI_VERDICT_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml"]

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120

image = (
    modal.Image.from_registry(AI_VERDICT_IMAGE, add_python=None)
    .entrypoint([])
    .pip_install(*AI_VERDICT_PIP)
    .apt_install("git")
    # HF_HUB_DISABLE_XET=1 is load-bearing (see AL skeleton comment): the xet CAS
    # backend stalls without timeout on multi-GB pulls; route through the classic
    # resolve endpoint. hf_transfer off too (unsloth force-enables; no-op once
    # xet is off).
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-ak-stage1", image=image)

vol = modal.Volume.from_name("eh-ak-stage1-logs", create_if_missing=True)
VOL_MOUNT = "/vol/aklogs"


def _run_tag(checkpoint: str) -> str:
    return f"ak-stage1-{checkpoint}-r1"


@app.function(
    gpu="A10G",
    timeout=6 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=3, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_stage1(checkpoint: str):
    import shutil
    import subprocess
    import sys
    import threading
    import time

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"
    run_tag = _run_tag(checkpoint)
    ckpt = f"{VOL_MOUNT}/ckpt/{run_tag}"

    if checkpoint == "raw-base":
        base_model, adapter_repo, adapter_rev = RAWBASE_MODEL, None, None
    elif checkpoint == "grpo-v2":
        base_model = GRPOV2_BASE_MODEL
        adapter_repo, adapter_rev = GRPOV2_ADAPTER_REPO, GRPOV2_ADAPTER_REV
        for name, val in (("GRPOV2_ADAPTER_REPO", adapter_repo),
                          ("GRPOV2_ADAPTER_REV", adapter_rev),
                          ("REPO_COMMIT", REPO_COMMIT)):
            if isinstance(val, str) and val.startswith("REPLACE_WITH"):
                raise RuntimeError(
                    f"{name} is a placeholder; fill the grpo-v2 provenance "
                    "before launching the grpo-v2 arm")
    else:
        raise RuntimeError(f"unknown checkpoint {checkpoint!r}")
    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT is a placeholder; pin the AK branch "
                           "commit before launch")

    def sh(cmd, cwd=None, check=True):
        print(f"[modal-ak] $ {' '.join(cmd)}", flush=True)
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
        print(f"[modal-ak] vol.reload() at restore failed (non-fatal): {e}",
              flush=True)
    restored = _copy_tree_into(ckpt_data, data_dir) if os.path.isdir(ckpt) else 0
    print(f"[modal-ak] restore: {restored} files from checkpoint (ckpt={ckpt})",
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
            # safetensors are immutable per safe_key; skip if present. Always
            # refresh rows.jsonl / manifest.json.
            if fn.endswith(".safetensors") and os.path.isfile(dst):
                continue
            tmp = dst + ".tmp"
            shutil.copyfile(src, tmp)
            os.replace(tmp, dst)

    def checkpoint_once(tag=""):
        try:
            _mirror_subtree(data_dir, ckpt_data)
            vol.commit()
            print(f"[modal-ak] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[modal-ak] checkpoint FAILED (non-fatal) {tag}: {e}",
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

    probe = os.path.join(workspace, "experiment/phase1/probe")
    script = os.path.join(probe, "amendment_ak_stage1_extract.py")
    upload = os.path.join(probe, "cloud/upload_result.py")

    boot_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    job_log = f"{out}/job_log_{boot_id}.txt"

    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    # fetch the pool from the private staging dataset
    pool_local = f"{out}/pool.jsonl"
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO,
                        repo_type="dataset")
    shutil.copyfile(p, pool_local)
    print(f"[modal-ak] fetched pool {STAGING_REPO}:{POOL_IN_REPO} -> {pool_local}",
          flush=True)

    common = [sys.executable, script, "--pool", pool_local,
              "--base-model", base_model, "--checkpoint-tag", checkpoint,
              "--layers", LAYERS, "--answer-stride", str(ANSWER_STRIDE)]
    if adapter_repo:
        common += ["--adapter-repo", adapter_repo]
        if adapter_rev:
            common += ["--adapter-revision", adapter_rev]

    # --- NUMERICS SMOKE pre-stage: run the runner at --limit SMOKE_LIMIT into a
    # throwaway dir, then assert the determinism spot-check passed on real GPU
    # states before committing to the full pool. Records the frozen generation
    # batch size (1) into the smoke manifest. ---
    import json
    smoke_dir = f"{out}/smoke"
    sh(common + ["--limit", str(SMOKE_LIMIT), "--out-dir", smoke_dir,
                 "--overwrite"])
    smoke_manifest = json.load(open(f"{smoke_dir}/manifest.json"))
    spot = smoke_manifest.get("determinism_spot_check", {})
    if not spot.get("passed"):
        raise RuntimeError(f"AK numerics smoke FAILED: spot-check {spot}")
    frozen_batch = smoke_manifest.get("generation_batch_size", 1)
    print(f"[modal-ak] numerics smoke PASSED spot={spot} "
          f"frozen_generation_batch={frozen_batch}", flush=True)

    # --- FULL pool extraction (native resume + volume checkpoint) ---
    t0 = time.time()
    sh(common + ["--out-dir", data_dir])
    if not os.path.isfile(f"{data_dir}/manifest.json"):
        raise RuntimeError("no extract manifest")
    t_ext = time.time() - t0
    checkpoint_once(tag="(post-extract)")

    # upload: rows.jsonl + manifest as files, tensors as one tarball
    for f in (f"{data_dir}/rows.jsonl", f"{data_dir}/manifest.json"):
        sh([sys.executable, upload, "--repo", STAGING_REPO,
            "--path-prefix", f"{run_tag}/data", "--file", f])
    tarball = f"{out}/ak_stage1_tensors.tar.gz"
    sh(["bash", "-c",
        f"cd {data_dir} && tar -czf {tarball} *.safetensors"])
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{run_tag}/tensors", "--file", tarball])
    # also upload the smoke manifest for provenance
    sh([sys.executable, upload, "--repo", STAGING_REPO,
        "--path-prefix", f"{run_tag}/smoke", "--file",
        f"{smoke_dir}/manifest.json"], check=False)

    with open(job_log, "w") as fh:
        fh.write(f"run_tag={run_tag} boot={boot_id} checkpoint={checkpoint}\n"
                 f"extract_sec={t_ext:.1f}\n"
                 f"pool={STAGING_REPO}:{POOL_IN_REPO}\n"
                 f"base={base_model} adapter={adapter_repo}@{adapter_rev}\n"
                 f"frozen_generation_batch={frozen_batch}\n")
    for src, name in ((job_log, os.path.basename(job_log)),
                      (f"{data_dir}/manifest.json", "extract_manifest.json")):
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
            fh.write(f"run_tag={run_tag} boot={boot_id} "
                     f"extract_sec={t_ext:.1f}\n")
        vol.commit()
        print("[modal-ak] DONE marker written to ckpt", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-ak] DONE marker write failed (non-fatal): {e}", flush=True)

    print(f"[modal-ak] DONE checkpoint={checkpoint} extract={t_ext:.0f}s "
          f"total={time.time()-t0:.0f}s", flush=True)
    return {"status": "completed", "checkpoint": checkpoint,
            "extract_sec": round(t_ext, 1), "frozen_generation_batch": frozen_batch}


@app.local_entrypoint()
def main(checkpoint: str = "raw-base"):
    if checkpoint not in ("raw-base", "grpo-v2"):
        raise SystemExit(f"--checkpoint must be raw-base|grpo-v2, got {checkpoint}")
    print(f"[modal-ak] launching AK Stage 1 on A10G, checkpoint={checkpoint}, "
          f"run_tag={_run_tag(checkpoint)}")
    print(f"[modal-ak] repo@{REPO_COMMIT[:12]} pool={POOL_IN_REPO}")
    result = run_stage1.remote(checkpoint)
    print(f"[modal-ak] result: {result}")
