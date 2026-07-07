"""Modal harness - Amendment AP length-balanced confirmatory veto (A0-surface,
192-token extract).

Pre-registered: experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md.
Confirmatory follow-up to Amendment AM
(experiment/protocol/AMENDMENT-AM-residual-catch-veto-coverage.md). Ported
(structure, not import) from
experiment/phase1/probe/cloud/modal_am_residual_catch.py (read-only reference
on the unmerged amendment-am branch; that script's own docstring records it
was itself cloned from the crash-proof modal_al_true_a0.py v2 skeleton).

AP-specific shape (identical to AM's, two deltas):
  * ap_extract.py (this experiment's own script, new-layout under
    experiments/ap-veto-length-balanced-confirmatory/, NOT the old
    experiment/phase1/probe/ tree) does the numerics smoke THEN the full
    A0-surface regeneration at max_new_tokens=192 (up from AM's 96) + dual-
    position (pre/post) hidden-state extraction, all in one container pass.
  * The self-contained AP pool (question + aliases + gold_class +
    category_canon -- NO score_L24; AP has no residual-rule scalar) is built
    on the HOST by ap_build_pool.py and uploaded to the staging repo under
    POOL_IN_REPO before launch; the container fetches it.

Everything else (raw base only, no adapter; upload discipline uploading only
rows.jsonl + manifest.json + an L18..L24+L35 activation slice, never the full
L0..L36 tensors; the Volume checkpoint daemon; the DONE marker) matches AM.

LAUNCH SAFETY GATE (new for AP, not present in AM's script): this entrypoint
refuses to spawn unless the environment carries BOTH an explicit launch
confirmation and the pre-registered cost cap, so no numeric cap or "go" value
is baked into this file (the task's "do NOT hardcode a launch" instruction).
Set both before running:
    export EHR_LAUNCH_OK=ap-veto-length-balanced-confirmatory
    export MODAL_COST_CAP_USD=10
    modal run --detach cloud/modal_ap_veto_length_balanced.py
(HF_TOKEN must also be exported; forwarded as a scoped Secret.) The cap value
is recorded into the job manifest for provenance and used to derive a
conservative container timeout (min of the AM-proven 3-hour ceiling and a
safety-margined estimate from the cap at a conservative A10G hourly rate); it
is NOT a live Modal-billing kill switch (Modal exposes no such API to a
running container) -- treat it as a soft cap the lead still monitors via the
Modal dashboard, exactly as AM's $5 cap was.

Launch DETACHED so the app survives client death (wait for any in-flight
Modal app to finish first before launching; do not co-run with a live GPU job):
    modal run --detach cloud/modal_ap_veto_length_balanced.py

Monitor: `modal app logs` + the Volume checkpoint DONE marker. Completion = DONE.
"""

import os

import modal

# --- provenance pins (REPLACE_WITH guard, same pattern AM/AK used: filled in
# a second commit after the harness itself lands, so the pin always points at
# a commit that actually contains this file) ---------------------------------
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
REPO_COMMIT = "3462d4c9f3eab9acaf959392d2a354d02c46ada0"
STAGING_REPO = "professorsynapse/eh-al-prep-staging"  # reuse the AL prep repo
POOL_IN_REPO = "ap-veto-lb-confirm-r1/ap_pool.jsonl"   # host-built, uploaded pre-launch
RESULT_PREFIX = "ap-veto-lb-confirm-r1"                # staging path prefix for outputs
RAWBASE_MODEL = "unsloth/Qwen3-4B-bnb-4bit"
RUN_TAG = "ap-veto-lb-confirm-r1"
# Experiment slug (experiments/<slug>/), the human-facing identifier the lead
# relays after `bin/exp sign` -- this is the value EHR_LAUNCH_OK must equal,
# NOT the short RUN_TAG above. Also the name the repo's PreToolUse launch
# guard (.claude/hooks/launch_guard.sh) speed-bumps on (that hook only checks
# the literal substring "EHR_LAUNCH_OK=" is present in the command, with no
# value check; THIS script's own check below is the stricter one).
EXPERIMENT_SLUG = "ap-veto-length-balanced-confirmatory"
# The pre-registered analysis seed (AMENDMENT.md); generation itself is
# greedy/deterministic (no stochastic seed), same convention AM used.
SEED = 20260706

# Activation layers uploaded (slice only; full L0..L36 stay on the Volume
# ckpt). L18..L24 window (the post-L20 readout AP's gates use) + L35, kept for
# parity with AM's own slice even though AP's gates only need L20.
UPLOAD_LAYERS = [18, 19, 20, 21, 22, 23, 24, 35]

# Pinned Unsloth image (AL/AK/AM lineage) + the small CPU deps the extract
# script imports.
AP_IMAGE = "unsloth/unsloth:2026.1.2-pt2.9.0-cu12.8-update"
AP_PIP = ["scikit-learn", "huggingface_hub>=0.34,<1.0", "pyyaml", "safetensors"]

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120
# AP's 192-token budget runs longer than AM's 96-token pass (AM found 47% of
# confabs hit the old cap), so the estimate is 3-4h vs AM's ~2-2.5h. The timeout
# is the real cost control here (timeout x assumed A10G rate approximates spend),
# so it is sized to the pre-registered $10 cap, not AM's 3h: 6h x $1.50/hr = $9,
# under the cap, with headroom above the 4h estimate so a healthy run completes.
# A hang still auto-dies at 6h (~$9) and checkpoint-resume keeps a retry cheap.
DEFAULT_TIMEOUT_HOURS = 6
# Conservative (rounded up) A10G $/hr used only to size the timeout from a
# launch-time cost cap; not a Modal billing API.
ASSUMED_A10G_USD_PER_HOUR = 1.50

image = (
    modal.Image.from_registry(AP_IMAGE, add_python=None)
    .entrypoint([])  # clear the supervisord ENTRYPOINT so our function runs
    .pip_install(*AP_PIP)
    .apt_install("git")
    # hf_xet hangs multi-GB pulls without timeout; force the classic resolve
    # endpoint. Baked into the image env so both are live before unsloth imports.
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-ap-veto-length-balanced-confirmatory", image=image)

vol = modal.Volume.from_name("eh-ap-veto-lb-confirm-logs", create_if_missing=True)
VOL_MOUNT = "/vol/aplogs"
CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"


def _timeout_seconds_for_cap(cap_usd: float) -> int:
    """Derive a conservative container timeout from the launch-time cost cap.
    Never exceeds the cap-sized DEFAULT_TIMEOUT_HOURS ceiling; only tightens it."""
    margin = 0.9  # leave 10% headroom under the naive cap/rate estimate
    from_cap = (cap_usd / ASSUMED_A10G_USD_PER_HOUR) * HOURS * margin
    return int(min(DEFAULT_TIMEOUT_HOURS * HOURS, from_cap))


@app.function(
    gpu="A10G",  # AM's known-good choice (AL/AK lineage); doc allows T4/L4/A10G
    timeout=DEFAULT_TIMEOUT_HOURS * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=3, backoff_coefficient=1.0,
                          initial_delay=10.0),
)
def run_ap():
    import shutil
    import subprocess
    import sys
    import threading
    import time

    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT is a placeholder; pin the AP harness "
                           "commit before launch (second commit, guard pattern).")

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"

    def sh(cmd, cwd=None, check=True):
        printable = " ".join(cmd)
        import re
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", printable)
        print(f"[modal-ap] $ {printable}", flush=True)
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
        print(f"[modal-ap] vol.reload() at restore failed (non-fatal): {e}",
              flush=True)
    restored = 0
    if os.path.isdir(CKPT):
        restored += _copy_tree_into(ckpt_ext, ext_dir)
    print(f"[modal-ap] restore: {restored} files from checkpoint (CKPT={CKPT})",
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
            print(f"[modal-ap] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-ap] checkpoint FAILED (non-fatal) {tag}: {e}", flush=True)

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

    exp_dir = os.path.join(workspace, "experiments/ap-veto-length-balanced-confirmatory")
    script = os.path.join(exp_dir, "ap_extract.py")
    upload = os.path.join(workspace, "experiment/phase1/probe/cloud/upload_result.py")

    boot_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    job_log = f"{out}/job_log_{boot_id}.txt"

    sh(["nvidia-smi", "--query-gpu=name,memory.total",
        "--format=csv,noheader"], check=False)

    # fetch the host-built self-contained pool from the private staging repo
    pool_local = f"{out}/ap_pool.jsonl"
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(repo_id=STAGING_REPO, filename=POOL_IN_REPO,
                        repo_type="dataset")
    shutil.copyfile(p, pool_local)
    print(f"[modal-ap] fetched pool {STAGING_REPO}:{POOL_IN_REPO} -> {pool_local}",
          flush=True)

    # 2. smoke + full A0-surface regen at 192 tokens + dual-position extract
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
        print(f"[modal-ap] sliced {n_sliced} safetensors to layers {UPLOAD_LAYERS}",
              flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-ap] slice step failed (non-fatal): {e}", flush=True)

    tarball = f"{out}/ap_activations_slice.tar.gz"
    sh(["tar", "-C", out, "-czf", tarball, "slice"], check=False)
    if os.path.isfile(tarball):
        sh([sys.executable, upload, "--repo", STAGING_REPO,
            "--path-prefix", f"{RESULT_PREFIX}/extract", "--file", tarball],
           check=False)

    with open(job_log, "w") as fh:
        fh.write(f"run_tag={RUN_TAG} boot={boot_id} seed={SEED}\n"
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
        print("[modal-ap] DONE marker written to CKPT", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-ap] DONE marker write failed (non-fatal): {e}", flush=True)

    print(f"[modal-ap] DONE extract={t_ext:.0f}s total={time.time()-t0:.0f}s",
          flush=True)
    return {"status": "completed", "extract_sec": round(t_ext, 1)}


@app.local_entrypoint()
def main():
    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise SystemExit("[modal-ap] REPO_COMMIT is a placeholder; pin the AP "
                         "harness commit before launch (second commit).")

    launch_ok = os.environ.get("EHR_LAUNCH_OK")
    if launch_ok != EXPERIMENT_SLUG:
        raise SystemExit(
            "[modal-ap] refusing to launch: set "
            f"EHR_LAUNCH_OK={EXPERIMENT_SLUG!r} in the environment (relayed "
            "lead approval after `bin/exp sign`), got EHR_LAUNCH_OK="
            f"{launch_ok!r}.")

    cap_raw = os.environ.get("MODAL_COST_CAP_USD")
    if not cap_raw:
        raise SystemExit(
            "[modal-ap] refusing to launch: set MODAL_COST_CAP_USD (the "
            "pre-registered cap, e.g. 10) in the environment; this script "
            "does not hardcode a cap value.")
    try:
        cap_usd = float(cap_raw)
    except ValueError:
        raise SystemExit(f"[modal-ap] MODAL_COST_CAP_USD={cap_raw!r} is not a number")

    derived_timeout_sec = _timeout_seconds_for_cap(cap_usd)
    print(f"[modal-ap] cost cap ${cap_usd:.2f} -> derived safety timeout "
          f"{derived_timeout_sec/3600:.2f}h (function timeout stays fixed at "
          f"{DEFAULT_TIMEOUT_HOURS}h; this is a REPORTED consistency check, "
          "not a live re-decoration of the deployed function's timeout)")
    if derived_timeout_sec < DEFAULT_TIMEOUT_HOURS * HOURS:
        print(f"[modal-ap] WARNING: at the assumed ${ASSUMED_A10G_USD_PER_HOUR}/hr "
              f"A10G rate, the ${cap_usd:.2f} cap affords less than the function's "
              f"{DEFAULT_TIMEOUT_HOURS}h timeout ceiling; the job could exceed the "
              "cap before the timeout kills it. Monitor the Modal dashboard.")

    print(f"[modal-ap] launching AP length-balanced confirmatory on A10G, "
          f"run_tag={RUN_TAG}")
    print(f"[modal-ap] repo@{REPO_COMMIT[:12]} pool={POOL_IN_REPO} seed={SEED}")
    # .spawn(), not .remote(): the client exits right after scheduling, so a
    # dying client has no in-flight input to cancel. Requires --detach.
    call = run_ap.spawn()
    print(f"[modal-ap] spawned function call {call.object_id}; client exiting. "
          f"Monitor: modal app logs / volume ckpt DONE marker.")
