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

# Private HF staging repos (user uploads once before launch; see AMENDMENT.md
# section 6.2 for the checkpoint, section 6.1 for the pool). Weights are staged
# in a model repo; the held-out question pool is staged in a dataset repo keyed
# by the committed row_keys (question text never lives in the public repo).
STAGING_MODEL_REPO = "professorsynapse/eh-h9-aitrue-staging"   # base + adapter
STAGING_POOL_REPO = "professorsynapse/eh-h9-holdout-pool"      # held-out pool jsonl (text)
BASE_SUBDIR = "base/merged-16bit"        # merged-16bit clean-SFT base
ADAPTER_SUBDIR = "adapter/final_model"   # amendment_ai_grpo_true_seed1 LoRA
POOL_IN_REPO = "holdout_pool_enlarged.jsonl"  # 750-row enlarged pool (G0 remedy)      # question text keyed by committed row_keys

# Full 37-layer stack (AL-prep surface), so score_holdout's loader reads L24/L35
# from the same safetensors layout AL produced.
LAYERS_FULL = ",".join(f"L{i}" for i in range(37))

# The proven extract/generate harness (version-controlled; present in the clone).
EXTRACT_GEN = "archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py"
# The committed held-out ID-manifest (row_key + source + gold label; no text).
HOLDOUT_IDS = ("experiments/h9-propensity-reading-gate/"
               "analysis-committed/holdout_draw_enlarged/holdout_ids.jsonl")

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
        "transformers==4.57.1",
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
    import json
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

    def _mirror_tree(src_dir, dst_dir):
        # Only-new .safetensors (immutable per row); always refresh small
        # metadata files (rows.jsonl / manifest.json), atomically.
        os.makedirs(dst_dir, exist_ok=True)
        for root, _dirs, files in os.walk(src_dir):
            rel = os.path.relpath(root, src_dir)
            tgt = os.path.join(dst_dir, rel) if rel != "." else dst_dir
            os.makedirs(tgt, exist_ok=True)
            for fn in files:
                src = os.path.join(root, fn)
                dst = os.path.join(tgt, fn)
                if fn.endswith(".safetensors") and os.path.isfile(dst):
                    continue
                tmp = dst + ".tmp"
                shutil.copyfile(src, tmp)
                os.replace(tmp, dst)

    def checkpoint_once(tag=""):
        try:
            for fn in os.listdir(out):
                src = os.path.join(out, fn)
                if os.path.isfile(src):
                    tmp = os.path.join(CKPT, fn) + ".tmp"
                    shutil.copyfile(src, tmp)
                    os.replace(tmp, os.path.join(CKPT, fn))
                elif os.path.isdir(src):
                    # mirror the extract/gen trees DURING the run, so a crash
                    # after an expensive stage never loses it and a Modal retry
                    # can resume (the entry script skips rows already in its
                    # out-dir rows.jsonl, config_sha-guarded).
                    _mirror_tree(src, os.path.join(CKPT, fn))
            vol.commit()
            print(f"[modal-h9] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-h9] checkpoint FAILED (non-fatal) {tag}: {e}", flush=True)

    # Resume: restore any prior checkpointed stage trees into this container's
    # /tmp before the stages run. The entry script's own resume logic then skips
    # completed rows (and hard-fails on config_sha mismatch, so a stale or
    # foreign checkpoint can never silently mix into a fresh run).
    for sub in ("extract", "gen"):
        ck = os.path.join(CKPT, sub)
        if os.path.isdir(ck):
            _mirror_tree(ck, os.path.join(out, sub))
            print(f"[modal-h9] restored {sub}/ from volume checkpoint for resume",
                  flush=True)

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

    # 1b. import environment for the archived extract/generate entry script.
    #     A fresh clone lacks the untracked legacy tree the local checkout has:
    #     (a) the flat module names (amendment_s_*, amendment_ah_*) resolve via
    #         the compat wrappers in archive/.../legacy-wrapper-tree, which are
    #         DESIGNED to be installed at experiment/phase1/probe/ (their repo
    #         root is computed as parents[3] of their own path);
    #     (b) the wrappers redirect into the experiments.common.readouts
    #         package, which needs the workspace root on sys.path;
    #     (c) load_baseline_system_prompt() resolves the AC config at its
    #         pre-rename path under the archive root; the tracked file moved to
    #         experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml
    #         at rename d55b7d26 with prompt.system byte-identical, so shimming
    #         the old path with the tracked file preserves the governed prompt.
    legacy_probe = os.path.join(workspace, "experiment", "phase1", "probe")
    if not os.path.isdir(legacy_probe):
        os.makedirs(os.path.dirname(legacy_probe), exist_ok=True)
        shutil.copytree(
            os.path.join(workspace, "archive", "experiment", "phase1", "probe",
                         "legacy-wrapper-tree"),
            legacy_probe)
    ac_shim = os.path.join(
        workspace, "archive", "experiments", "doubt-regulated-caution",
        "phase3_ac_doubt_coupled_intervention.yaml")
    if not os.path.isfile(ac_shim):
        os.makedirs(os.path.dirname(ac_shim), exist_ok=True)
        shutil.copyfile(
            os.path.join(workspace, "experiments", "doubt-regulated-caution",
                         "ac_doubt_coupled_intervention.yaml"),
            ac_shim)
    os.environ["PYTHONPATH"] = f"{workspace}:{legacy_probe}"

    # 1c. fail-fast preflight: prove the entry script's import chain and the
    #     system-prompt resolver work BEFORE any model download, so an import
    #     gap costs seconds instead of GPU minutes.
    #     Import order mirrors the entry script: path_compat from the script's
    #     own dir FIRST, so the flat name caches the amendments copy before the
    #     readouts package can shadow it.
    sh([sys.executable, "-c",
        "import sys; sys.path.insert(0, "
        f"{os.path.dirname(os.path.join(workspace, EXTRACT_GEN))!r}); "
        "import path_compat; "
        "from amendment_s_correctness_probe_extract import MODEL_TAG; "
        "from amendment_ah_stage0_extract import load_baseline_system_prompt; "
        "sp = load_baseline_system_prompt(); "
        "assert sp.startswith('Answer the user'), 'unexpected system prompt'; "
        "print('[modal-h9] preflight imports OK, model_tag=' + MODEL_TAG)"])

    from huggingface_hub import hf_hub_download, snapshot_download

    t0 = time.time()

    # 2. fetch the AI-TRUE base + adapter from the private staging model repo,
    #    and the held-out question pool from the private staging dataset repo.
    #    Question text lives ONLY in the container-local pool (never a repo path).
    base_local = snapshot_download(STAGING_MODEL_REPO, allow_patterns=f"{BASE_SUBDIR}/*")
    base_local = os.path.join(base_local, BASE_SUBDIR)
    adapter_local = snapshot_download(STAGING_MODEL_REPO,
                                      allow_patterns=f"{ADAPTER_SUBDIR}/*")
    adapter_local = os.path.join(adapter_local, ADAPTER_SUBDIR)
    pool_path = hf_hub_download(STAGING_POOL_REPO, POOL_IN_REPO,
                                repo_type="dataset")

    # 2b. verify the staged pool matches the committed ID-manifest exactly
    #     (same row_keys, no extra/missing rows), so the scored population is the
    #     pre-registered one and nothing leaked in through the pool.
    ids_path = os.path.join(workspace, HOLDOUT_IDS)
    import hashlib
    committed = {json.loads(l)["row_key"]: json.loads(l)["qhash"]
                 for l in open(ids_path) if l.strip()}
    pool_rows = [json.loads(l) for l in open(pool_path) if l.strip()]
    pooled = {r["row_key"] for r in pool_rows}
    if committed.keys() != pooled:
        raise RuntimeError(
            f"staged pool row_keys != committed ID-manifest "
            f"(committed {len(committed)}, pooled {len(pooled)}, "
            f"symdiff {len(set(committed) ^ pooled)}); refusing to score an "
            f"off-manifest population.")
    # C3: per-row text<->key binding. Recompute qhash from the staged question
    # text and require it to equal the committed hash, so a pool that maps the
    # right row_keys to the WRONG question text (a manual build/shuffle bug) is
    # caught, not just a wrong population.
    for r in pool_rows:
        qh = hashlib.sha256(
            (r["row_key"] + "\x00" + r["question"]).encode("utf-8")).hexdigest()
        if qh != committed[r["row_key"]]:
            raise RuntimeError(
                f"staged pool qhash mismatch for {r['row_key']}: the staged "
                f"question text does not match the committed manifest hash; "
                f"refusing to feed unverified prompts into extraction.")

    extract_gen = os.path.join(workspace, EXTRACT_GEN)
    extract_out = f"{out}/extract"
    gen_out = f"{out}/gen"

    # 3. extraction: pre-generation anchor (prompt_len-1), full 37-layer stack,
    #    batch-1 forward-only, on the AI-TRUE checkpoint (proven AL/AI harness).
    sh([sys.executable, extract_gen, "--stage", "extract", "--surface", "holdout",
        "--pool", pool_path, "--base-model", base_local,
        "--adapter-repo", adapter_local, "--layers", LAYERS_FULL,
        "--out-dir", extract_out])
    checkpoint_once(tag="(post-extract)")

    # 4. generation + behavior grading (greedy; refused/answered/schema_valid),
    #    same harness, same checkpoint.
    sh([sys.executable, extract_gen, "--stage", "generate",
        "--pool", pool_path, "--base-model", base_local,
        "--adapter-repo", adapter_local, "--out-dir", gen_out])
    checkpoint_once(tag="(post-generate)")

    # 4b. join gold_class (from the pool label: known->answerable,
    #     unknown->unanswerable) into the graded rows so score_holdout can read
    #     gold_class alongside answered/refused. The propensity contrast
    #     (confab vs unanswerable-refused) and the caution control (refused vs
    #     not) need only gold_class + answered + refused, all present after this.
    l2g = {"known": "answerable", "unknown": "unanswerable"}
    gold = {}
    for r in pool_rows:
        # C4: the staged pool label MUST be the source domain {known, unknown},
        # NOT the committed manifest's mapped gold_label. Crash on any other value
        # rather than silently defaulting gold_class to None (which would collapse
        # every confab label to False and force G0 to inconclusive).
        lab = r.get("label")
        if lab not in l2g:
            raise RuntimeError(
                f"staged pool row {r['row_key']} has label {lab!r}; expected one "
                f"of {sorted(l2g)} (source domain). Did the pool copy the mapped "
                f"gold_label instead of the source label?")
        gold[r["row_key"]] = l2g[lab]
    # The generate stage writes its graded rows as rows.jsonl (fields:
    # row_key/refused/answered/schema_valid/degenerate/prompt_len/config_sha
    # plus answer_text); rows_graded.jsonl was a wrong guess at that name and
    # crashed the first complete run at this line.
    graded_in = os.path.join(gen_out, "rows.jsonl")
    graded_out = f"{out}/rows_graded.jsonl"
    with open(graded_in) as fin, open(graded_out, "w") as fout:
        for l in fin:
            if not l.strip():
                continue
            r = json.loads(l)
            r.setdefault("gold_class", gold.get(r["row_key"]))
            fout.write(json.dumps(r) + "\n")

    t_total = time.time() - t0

    # 5. mirror results to the Volume: the extraction tree (per-row .safetensors +
    #    rows.jsonl + manifest) and the gold-joined rows_graded.jsonl. These are
    #    pulled back locally (gitignored) for score_holdout.py; no external upload.
    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    for sub in ("extract", "gen"):
        src = f"{out}/{sub}"
        if os.path.isdir(src):
            dst = f"{CKPT}/{sub}"
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    checkpoint_once(tag="(final; includes rows_graded.jsonl)")
    with open(f"{CKPT}/DONE", "w") as fh:
        fh.write(f"run_tag={RUN_TAG} total_sec={t_total:.1f}\n")
    vol.commit()
    print(f"[modal-h9] DONE total={t_total:.0f}s -- pull with "
          f"`modal volume get eh-h9-holdout-logs ckpt/{RUN_TAG} <dest>`", flush=True)
    return {"status": "completed", "total_sec": round(t_total, 1)}


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
    print(f"[modal-h9] repo@{repo_commit[:12]} "
          f"model_staging={STAGING_MODEL_REPO} pool_staging={STAGING_POOL_REPO}")
    call = run_h9_holdout.spawn(repo_commit)
    print(f"[modal-h9] spawned {call.object_id}; client exiting. Monitor: "
          f"modal app logs, or `modal volume get eh-h9-holdout-logs "
          f"ckpt/{RUN_TAG} <dest>` for progress/results.")
