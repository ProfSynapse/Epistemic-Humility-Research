"""Modal harness -- BB PHASE 1 base fit-surface generation+extraction plus
read-surface extraction on untrained base Qwen3-4B (AMENDMENT.md sections 5, 7).

DRAFT SKELETON, authored at phase-1 gate-open (phase 0 passed all three floors
2026-07-11: schema_valid_frac 0.976, confab 32, honest_unanswerable_refusal
558; see analysis-committed/phase0/density_report.json). Cloned from
`cloud/modal_bb_phase0.py` (itself cloned from H9's `modal_h9_holdout.py`) with
the phase-1 diff:

WHAT PHASE 1 DOES (GPU stages only; AMENDMENT.md section 5 -- direction fitting
and gate scoring happen locally on CPU afterward, in freeze_scorer_base.py and
score_bb_holdout.py, NOT in this script):
  1. FIT surface (1,662 rows, AL's exact A0 surface, staged privately at
     professorsynapse/eh-bb-fit-pool/fit_pool.jsonl): GENERATE + GRADE on base
     (behavior labels come from BASE, not AL's AI-TRUE grades -- AMENDMENT.md
     section 2.3), AND EXTRACT pre-generation-anchor hidden states, all 37
     layers, so the base-fit direction can be fit on L24/L35 downstream.
  2. READ surface (750 rows, H9's vendored enlarged draw, reused verbatim from
     phase 0's already-staged pool professorsynapse/eh-h9-holdout-pool):
     EXTRACT ONLY. Phase 0 already generated+graded this pool on base
     (analysis/phase0/bb-phase0-r1/rows_graded.jsonl, pulled back locally);
     phase 1 does NOT regenerate it, only adds the L24/L35 extraction that
     phase 0 deliberately skipped (AMENDMENT.md section 4: "NO extraction ...
     in phase 0").

WHAT IS UNCHANGED FROM PHASE 0 / H9 (deliberately, so the same archived entry
script + grader + import-environment block apply): the legacy-wrapper-tree
install, the AC config shim, the PYTHONPATH setup, the fail-fast preflight, the
qhash pool verification against the committed ID-manifests, the launch guards,
the in-run tree checkpoint/resume, and the DONE marker.

WHAT THE CONTAINER PRODUCES (written to the Modal Volume; pulled back with
`modal volume get eh-bb-phase1-logs ckpt/<RUN_TAG> <dest>`; no external upload):
  - fit/extract/  (pre-generation-anchor .safetensors, all 37 layers, rows.jsonl, manifest.json)
  - fit/gen/      (rows.jsonl -- base behavior labels, manifest.json)
  - fit/rows_graded.jsonl  (gold_class-joined fit-surface behavior grades)
  - read/extract/ (pre-generation-anchor .safetensors, all 37 layers, rows.jsonl, manifest.json)
All gitignored locally once pulled; only the aggregate fit/read gate report and
the fitted-direction JSON (produced by the local CPU scripts, not here) are
ever committed.

LAUNCH SAFETY GATE (same pattern as phase 0 / H9):
    export EHR_LAUNCH_OK=bb-base-propensity-fit-read
    export MODAL_COST_CAP_USD=<cap; see cost estimate below, NOT pre-registered
        in AMENDMENT.md section 7 which only estimated phase 0>
    export EHR_REPO_COMMIT=<signed commit sha>
    export HF_TOKEN=<token with read on both private pool repos>
    modal run --detach cloud/modal_bb_phase1.py
THE AGENT THAT WROTE THIS DID NOT RUN modal run: launch is reserved for the
lead. This is prep only.

COST ESTIMATE (built at gate-open; NOT a pre-registered AMENDMENT number --
AMENDMENT.md section 7.1 only estimated phase 0's generate-only 750-row job).
Scaling from the same measured 3090 rates AMENDMENT.md section 7.1 and H9's
section 6.3 use (extraction 0.099 s/row, generation 1.685 s/row):
  - fit surface (1,662 rows): generation ~2800s (~47 min) + extraction ~165s
    (~3 min)
  - read surface (750 rows): extraction only, ~74s (~1.2 min)
  - active GPU compute ~51 min at 3090 rates; A10G is typically somewhat slower
    for this shape (same caveat AMENDMENT.md 7.1 and H9 6.3 note), so budget
    ~65-90 min active compute, plus ~5-10 min to pull/load the base weights
    (same ~3-5 GB 4-bit download as phase 0). Wall time estimate ~75-100 min.
  - cost at ~$1.10-1.50/hr A10G: roughly $1.40-$2.50. This is well within the
    $15 cap phase 0 used, but the lead should set an explicit
    MODAL_COST_CAP_USD for phase 1 rather than assuming the phase-0 number
    applies unchanged (this script does not hardcode one).
"""
from __future__ import annotations

import os

import modal

REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
EXPERIMENT_SLUG = "bb-base-propensity-fit-read"
RUN_TAG = "bb-phase1-r1"
MODAL_GPU = os.environ.get("BB_MODAL_GPU", "A10G")

# Untrained base pulled straight from the hub (no adapter, no staging model
# repo) -- identical pin to phase 0.
BASE_MODEL_HUB = "Qwen/Qwen3-4B"
BASE_MODEL_REVISION = "1cfa9a7208912126459214e8b04321603b3df60c"  # pinned at signing (no env override)

# FIT surface: newly staged private pool (this build's upload; AMENDMENT.md 5.1).
FIT_POOL_REPO = "professorsynapse/eh-bb-fit-pool"
FIT_POOL_IN_REPO = "fit_pool.jsonl"       # 1,662-row pool, uploaded by this build
FIT_IDS = ("experiments/bb-base-propensity-fit-read/"
           "analysis-committed/fit_surface/fit_ids.jsonl")

# READ surface: H9's pool, reused verbatim (already staged, already used by phase 0).
READ_POOL_REPO = "professorsynapse/eh-h9-holdout-pool"
READ_POOL_IN_REPO = "holdout_pool_enlarged.jsonl"   # 750-row enlarged pool
READ_IDS = ("experiments/bb-base-propensity-fit-read/"
            "analysis-committed/read_surface_h9_vendored/holdout_ids.jsonl")

# Full 37-layer stack (AL-prep surface), so the local fit/score scripts can
# read L24/L35 from the same safetensors layout AL produced.
LAYERS_FULL = ",".join(f"L{i}" for i in range(37))

# The proven extract/generate harness (version-controlled; present in the clone).
EXTRACT_GEN = "archive/experiment/phase1/probe/amendments/amendment_ai_verdict_extract_gen.py"

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120
# Generous: phase 1's fit-surface generation (1,662 rows) is more than double
# phase 0's 750-row generation job; 3 hours leaves headroom for a slower A10G
# generation rate plus the base download/load.
DEFAULT_TIMEOUT_HOURS = 3
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

app = modal.App("eh-bb-base-propensity-phase1", image=image)
vol = modal.Volume.from_name("eh-bb-phase1-logs", create_if_missing=True)
VOL_MOUNT = "/vol/bblogs1"
CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"


@app.function(
    gpu=MODAL_GPU,
    timeout=DEFAULT_TIMEOUT_HOURS * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_bb_phase1(repo_commit: str) -> dict:
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
        print(f"[modal-bb1] $ {printable}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode})")
        return r.returncode

    def _mirror_tree(src_dir, dst_dir):
        # Only-new .safetensors (immutable per row); always refresh small
        # metadata files (rows.jsonl / manifest.json), atomically. Identical
        # to the proven H9 / phase-0 mirror.
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
                    # mirror the fit/read stage subtrees DURING the run, so a
                    # crash after an expensive stage never loses it and a
                    # Modal retry can resume (the entry script skips rows
                    # already in its out-dir rows.jsonl, config_sha-guarded).
                    _mirror_tree(src, os.path.join(CKPT, fn))
            vol.commit()
            print(f"[modal-bb1] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-bb1] checkpoint FAILED (non-fatal) {tag}: {e}", flush=True)

    # Resume: restore any prior checkpointed stage trees into this container's
    # /tmp before the stages run. The entry script's own resume logic then
    # skips completed rows (config_sha-guarded).
    for sub in ("fit/extract", "fit/gen", "read/extract"):
        ck = os.path.join(CKPT, sub)
        if os.path.isdir(ck):
            _mirror_tree(ck, os.path.join(out, sub))
            print(f"[modal-bb1] restored {sub}/ from volume checkpoint for resume",
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
    #     Byte-identical to phase 0 / H9 (see those files for the full
    #     rationale of each shim).
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

    # 1c. fail-fast preflight (byte-identical check to phase 0 / H9).
    sh([sys.executable, "-c",
        "import sys; sys.path.insert(0, "
        f"{os.path.dirname(os.path.join(workspace, EXTRACT_GEN))!r}); "
        "import path_compat; "
        "from amendment_s_correctness_probe_extract import MODEL_TAG; "
        "from amendment_ah_stage0_extract import load_baseline_system_prompt; "
        "sp = load_baseline_system_prompt(); "
        "assert sp.startswith('Answer the user'), 'unexpected system prompt'; "
        "print('[modal-bb1] preflight imports OK, model_tag=' + MODEL_TAG)"])

    from huggingface_hub import hf_hub_download, snapshot_download

    t0 = time.time()

    # 2. fetch the UNTRAINED base from the public hub (pinned revision; no
    #    adapter, no private model repo) -- identical to phase 0.
    base_local = snapshot_download(BASE_MODEL_HUB, revision=BASE_MODEL_REVISION)

    def _verify_pool(pool_path, ids_path, tag):
        import hashlib
        committed = {json.loads(l)["row_key"]: json.loads(l)["qhash"]
                     for l in open(ids_path) if l.strip()}
        pool_rows = [json.loads(l) for l in open(pool_path) if l.strip()]
        pooled = {r["row_key"] for r in pool_rows}
        if committed.keys() != pooled:
            raise RuntimeError(
                f"[{tag}] staged pool row_keys != committed ID-manifest "
                f"(committed {len(committed)}, pooled {len(pooled)}, "
                f"symdiff {len(set(committed) ^ pooled)}); refusing to feed an "
                f"off-manifest population into GPU work.")
        for r in pool_rows:
            qh = hashlib.sha256(
                (r["row_key"] + "\x00" + r["question"]).encode("utf-8")).hexdigest()
            if qh != committed[r["row_key"]]:
                raise RuntimeError(
                    f"[{tag}] staged pool qhash mismatch for {r['row_key']}: the "
                    f"staged question text does not match the committed manifest "
                    f"hash; refusing to feed unverified prompts into GPU work.")
        return pool_rows

    # 3. fetch the fit pool (private, newly staged) and the read pool (private,
    #    reused from phase 0/H9), verifying each against its committed
    #    ID-manifest (C3/C4, unchanged discipline from H9/phase 0).
    fit_pool_path = hf_hub_download(FIT_POOL_REPO, FIT_POOL_IN_REPO, repo_type="dataset")
    fit_ids_path = os.path.join(workspace, FIT_IDS)
    fit_pool_rows = _verify_pool(fit_pool_path, fit_ids_path, "fit")

    read_pool_path = hf_hub_download(READ_POOL_REPO, READ_POOL_IN_REPO, repo_type="dataset")
    read_ids_path = os.path.join(workspace, READ_IDS)
    _verify_pool(read_pool_path, read_ids_path, "read")

    extract_gen = os.path.join(workspace, EXTRACT_GEN)
    fit_extract_out = f"{out}/fit/extract"
    fit_gen_out = f"{out}/fit/gen"
    read_extract_out = f"{out}/read/extract"

    # 4. FIT surface: extraction (pre-generation anchor, full 37-layer stack,
    #    batch-1 forward-only) on the UNTRAINED base (no --adapter-repo).
    #    --surface union: the extract script only branches on --surface inside
    #    load_pool's dead surface arg (both union and holdout pool schemas
    #    already carry `label` directly, so this is a labeling choice, not a
    #    behavior change); "union" matches the AL-prep naming for a full fit
    #    surface (as opposed to "holdout" for the read surface below).
    sh([sys.executable, extract_gen, "--stage", "extract", "--surface", "union",
        "--pool", fit_pool_path, "--base-model", base_local,
        "--layers", LAYERS_FULL, "--out-dir", fit_extract_out])
    checkpoint_once(tag="(post-fit-extract)")

    # 5. FIT surface: generation + behavior grading on BASE (greedy;
    #    refused/answered/schema_valid/degenerate) -- base's OWN behavior
    #    labels, not AL's AI-TRUE grades (AMENDMENT.md section 2.3).
    sh([sys.executable, extract_gen, "--stage", "generate",
        "--pool", fit_pool_path, "--base-model", base_local,
        "--out-dir", fit_gen_out])
    checkpoint_once(tag="(post-fit-generate)")

    # 5b. join gold_class (from the pool label: known->answerable,
    #     unknown->unanswerable) into the fit-surface graded rows, identical
    #     join logic to phase 0.
    l2g = {"known": "answerable", "unknown": "unanswerable"}
    gold = {}
    for r in fit_pool_rows:
        lab = r.get("label")
        if lab not in l2g:
            raise RuntimeError(
                f"staged fit-pool row {r['row_key']} has label {lab!r}; expected "
                f"one of {sorted(l2g)} (source domain).")
        gold[r["row_key"]] = l2g[lab]
    graded_in = os.path.join(fit_gen_out, "rows.jsonl")
    graded_out = f"{out}/fit/rows_graded.jsonl"
    with open(graded_in) as fin, open(graded_out, "w") as fout:
        for l in fin:
            if not l.strip():
                continue
            r = json.loads(l)
            r.setdefault("gold_class", gold.get(r["row_key"]))
            fout.write(json.dumps(r) + "\n")

    # 6. READ surface: extraction ONLY (phase 0 already generated+graded this
    #    pool on base; that rows_graded.jsonl lives locally already, pulled
    #    back from the phase-0 volume -- it is NOT reproduced here).
    sh([sys.executable, extract_gen, "--stage", "extract", "--surface", "holdout",
        "--pool", read_pool_path, "--base-model", base_local,
        "--layers", LAYERS_FULL, "--out-dir", read_extract_out])
    checkpoint_once(tag="(post-read-extract)")

    t_total = time.time() - t0

    # 7. mirror results to the Volume: fit/extract, fit/gen, fit/rows_graded.jsonl,
    #    read/extract. Pulled back locally (gitignored); no external upload.
    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    for sub in ("fit/extract", "fit/gen", "read/extract"):
        src = f"{out}/{sub}"
        if os.path.isdir(src):
            dst = f"{CKPT}/{sub}"
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
    fit_graded_src = f"{out}/fit/rows_graded.jsonl"
    if os.path.isfile(fit_graded_src):
        shutil.copyfile(fit_graded_src, f"{CKPT}/fit/rows_graded.jsonl")
    checkpoint_once(tag="(final; includes fit/rows_graded.jsonl)")
    with open(f"{CKPT}/DONE", "w") as fh:
        fh.write(f"run_tag={RUN_TAG} total_sec={t_total:.1f}\n")
    vol.commit()
    print(f"[modal-bb1] DONE total={t_total:.0f}s -- pull with "
          f"`modal volume get eh-bb-phase1-logs ckpt/{RUN_TAG} <dest>`", flush=True)
    return {"status": "completed", "total_sec": round(t_total, 1)}


@app.local_entrypoint()
def main():
    launch_ok = os.environ.get("EHR_LAUNCH_OK")
    if launch_ok != EXPERIMENT_SLUG:
        raise SystemExit(
            f"[modal-bb1] refusing to launch: set EHR_LAUNCH_OK={EXPERIMENT_SLUG!r} "
            f"(lead approval, relayed after user sign-off), got {launch_ok!r}.")
    cap_raw = os.environ.get("MODAL_COST_CAP_USD")
    if not cap_raw:
        raise SystemExit(
            "[modal-bb1] refusing to launch: set MODAL_COST_CAP_USD (see the "
            "module docstring's phase-1 cost estimate); this script does not "
            "hardcode a cap.")
    try:
        cap_usd = float(cap_raw)
    except ValueError:
        raise SystemExit(f"[modal-bb1] MODAL_COST_CAP_USD={cap_raw!r} is not a number")
    repo_commit = os.environ.get("EHR_REPO_COMMIT")
    if not repo_commit:
        raise SystemExit("[modal-bb1] set EHR_REPO_COMMIT to the signed commit sha")

    print(f"[modal-bb1] cost cap ${cap_usd:.2f}; launching phase-1 fit "
          f"generation+extraction + read extraction on {MODAL_GPU}, "
          f"run_tag={RUN_TAG}")
    print(f"[modal-bb1] repo@{repo_commit[:12]} base={BASE_MODEL_HUB}@"
          f"{BASE_MODEL_REVISION} fit_pool={FIT_POOL_REPO} read_pool={READ_POOL_REPO}")
    call = run_bb_phase1.spawn(repo_commit)
    print(f"[modal-bb1] spawned {call.object_id}; client exiting. Monitor: "
          f"modal app logs, or `modal volume get eh-bb-phase1-logs "
          f"ckpt/{RUN_TAG} <dest>` for progress/results.")
