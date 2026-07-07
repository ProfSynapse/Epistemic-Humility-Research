"""Modal harness -- J-lens (Jacobian lens) full characterization on Qwen3-4B
bf16, for the READ-ONLY j-space-localization-qwen3-4b lab-diagnostic.

Pre-registered: experiments/j-space-localization-qwen3-4b/AMENDMENT.md
(lab-diagnostic; characterization, no hard gates/falsifier -- see
experiment.yaml). Structure (detached app, Volume checkpoint daemon, DONE
marker) ported from
experiments/ap-veto-length-balanced-confirmatory/cloud/modal_ap_veto_length_balanced.py
(read that file's own docstring for the lineage back through AM/AL/AK).

WHAT'S DIFFERENT FROM THE AP/AK/AM LINEAGE THIS BORROWS STRUCTURE FROM: this
run pushes NO results to any external staging repo (unlike AP/AK/AM). It
DOES need one HF pool-fetch step, same as AK: the 1000-question corpus is
never committed to this public repo (question text is forbidden in this
repo, see analysis-committed/corpus/PROVENANCE.md); the container fetches
the source pool from the private HF staging repo
(professorsynapse/eh-al-prep-staging:pools/ak_stage1_pool.jsonl, via
jlens.py's own `build-corpus` subcommand, which calls hf_hub_download
exactly like experiment/phase1/probe/cloud/modal_ak_stage1.py's pool fetch)
and deterministically re-samples the SAME 1000-row corpus (seed 20260707)
this experiment's local runs use -- see analysis-committed/corpus/
jlens_corpus_manifest.json for the exact row-id manifest that verifies the
sample without storing any question text. The four fitted directions
(u_d, pos_ctrl, neg_ctrl, c_hat) remain committed directly into this
experiment's own analysis-committed/source_directions/ (those are our own
fitted artifacts, not dataset/question text), so the container's
`git clone` at the pinned commit already has them. Results are written to
the Modal Volume this function mounts (the SAME mechanism AP/AM/AK use for
their own checkpoint/logs/manifest side-channel) and pulled back from
there --
    modal volume get eh-jspace-jlens-logs ckpt/<RUN_TAG> <local-dest>
No huggingface_hub UPLOAD of outputs happens anywhere in this script (only
the one pool download); results either go to the Modal Volume.

READ-ONLY, no training, no injection: this container runs
`jlens.py smoke`, `jlens.py profile`, and `jlens.py h1` (all three CLI
subcommands already validated locally on the 3090, see NOTEBOOK.md) against
the bf16 sibling of the raw-base model (unsloth/Qwen3-4B, NOT the bnb-4bit
quantized raw-base -- autograd/JVPs do not work cleanly through bnb-4bit;
see jlens.py's module docstring). The H1 direction inputs are the sibling
two-signal-caution-regulation-instruct bf16 refit, so the full-corpus H1 read
is same-substrate bf16.

COST ESTIMATE (derived from an ACTUAL local-3090 benchmark, not a guess --
see NOTEBOOK.md "Modal cost estimate" entry for the raw numbers):
  * Per-(layer, direction, prompt) JVP unit costs ~45ms (near the final
    layer, where the double-backward only traverses norm+lm_head) up to
    ~175ms (near the first sampled layer, where it traverses ~34 blocks of
    eager-attention double backward). Measured directly: hs_index=8 ->
    152.9ms/prompt, hs_index=20 -> 106.6ms/prompt, hs_index=34 -> 59.1ms/
    prompt, hs_index=36 -> 51.2ms/prompt (n_prompts=100, single direction).
  * profile stage: LAYERS (13 points spanning depth) x N_RANDOM_DIRS (5) x
    N_PROMPTS (1000) JVP units. Summing the measured/interpolated per-layer
    cost across LAYERS gives ~1.39s per (prompt, direction) full-depth
    sweep; x 1000 prompts x 5 directions ~= 6950s ~= 1.93h.
  * h1 stage: 4 directions x 4 layer-offsets x 1000 prompts, all within
    ~4 blocks of the final layer (cheap end) ~= 4*4*1000*0.07s ~= 1120s
    ~= 0.31h.
  * smoke (full-corpus verbalize sweep) at the final layer only, a handful
    of directions ~= a few minutes.
  * Total GPU-busy estimate: ~2.3-2.5h. On an A10G (the AP/AK/AM lineage's
    proven choice, ~$1.10-1.50/hr) that is roughly $3-4, well under the
    $25 cap the lead set -- see the cap-derived timeout helper below for
    the (soft, monitored-not-enforced) safety margin.

LAUNCH SAFETY GATE (same pattern as AP): refuses to spawn unless both an
explicit launch confirmation and the pre-registered cost cap are set:
    export EHR_LAUNCH_OK=j-space-localization-qwen3-4b
    export MODAL_COST_CAP_USD=25
    modal run --detach cloud/modal_jlens.py
(HF_TOKEN must also be exported; forwarded as a scoped Secret -- needed both
to pull the ungated unsloth/Qwen3-4B weights AND to fetch the private
source-pool dataset professorsynapse/eh-al-prep-staging.) THE AGENT
THAT WROTE THIS SCRIPT DID NOT RUN modal run: the harness-builder agent is
explicitly barred from firing cloud/paid launches (launch_guard blocks
modal run/deploy unless EHR_LAUNCH_OK is present, and this repo's binding
invariant reserves that gate for the lead). This is prep only.

Launch DETACHED so the app survives client death:
    modal run --detach cloud/modal_jlens.py
Monitor: `modal app logs` + the Volume checkpoint DONE marker, or pull the
progress-visible partial JSONs this script mirrors to the Volume after each
stage (profile flushes after every layer, h1 after every direction -- see
jlens.py's on_layer_done / per-direction flush) with
    modal volume get eh-jspace-jlens-logs ckpt/<RUN_TAG> <local-dest>
"""

import os

import modal

# --- provenance pins (REPLACE_WITH guard, same pattern AP/AM/AK used: filled
# in a second commit after the harness itself lands, so the pin always
# points at a commit that actually contains this file) ----------------------
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
# Input-bearing commit for this run (branch exp/j-space-localization-qwen3-4b):
# contains the bf16-refit direction swap, runtime-HF corpus fetch, and the
# J-lens code Modal will execute after cloning from REPO_URL.
REPO_COMMIT = "40da3ee87127d13f9bd2198c7838ae73096eb71d"
MODEL_BF16 = "unsloth/Qwen3-4B"
EXPERIMENT_SLUG = "j-space-localization-qwen3-4b"
RUN_TAG = "jspace-jlens-r1"
SEED = 20260707

# jlens.py's own defaults / this run's chosen scope (see cost estimate
# above for how these were sized against the $25 cap).
N_PROMPTS_FULL = 1000
PROFILE_LAYERS = "2,5,8,11,14,17,20,23,26,29,32,35,36"  # sample across full depth
PROFILE_N_RANDOM_DIRS = 5
H1_LAYER_OFFSETS = "-4,-2,0,2"
SMOKE_N_TEST_DIRS = 5

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120
# ~2.3-2.5h estimated GPU-busy (see docstring); 5h ceiling leaves comfortable
# headroom for container/model-load overhead and Modal scheduling variance
# without letting a hung run burn past the cap unnoticed for long.
DEFAULT_TIMEOUT_HOURS = 5
ASSUMED_A10G_USD_PER_HOUR = 1.50  # conservative; not a live Modal billing API

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.9.1",
        index_url="https://download.pytorch.org/whl/cu128",
    )
    .pip_install(
        "transformers==4.57.1", "accelerate",
        "huggingface_hub>=0.34,<1.0", "safetensors",
    )
    .apt_install("git")
    .env({"HF_HUB_DISABLE_XET": "1", "HF_HUB_ENABLE_HF_TRANSFER": "0"})
)

app = modal.App("eh-j-space-localization-qwen3-4b", image=image)

vol = modal.Volume.from_name("eh-jspace-jlens-logs", create_if_missing=True)
VOL_MOUNT = "/vol/jspacelogs"
CKPT = f"{VOL_MOUNT}/ckpt/{RUN_TAG}"


def _timeout_seconds_for_cap(cap_usd: float) -> int:
    """Derive a conservative container timeout from the launch-time cost
    cap. Never exceeds the cap-sized DEFAULT_TIMEOUT_HOURS ceiling; only
    tightens it. Reported, not enforced -- Modal exposes no live billing
    kill switch; the lead still monitors the dashboard."""
    margin = 0.9
    from_cap = (cap_usd / ASSUMED_A10G_USD_PER_HOUR) * HOURS * margin
    return int(min(DEFAULT_TIMEOUT_HOURS * HOURS, from_cap))


@app.function(
    gpu="A10G",  # AP/AM/AK's proven choice for a 4B model at this budget
    timeout=DEFAULT_TIMEOUT_HOURS * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_dict({"HF_TOKEN": os.environ.get("HF_TOKEN", "")})],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_jlens():
    import re
    import shutil
    import subprocess
    import sys
    import threading
    import time

    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise RuntimeError("REPO_COMMIT is a placeholder; pin the j-lens "
                           "harness commit before launch (second commit, "
                           "guard pattern).")

    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
    workspace = "/workspace/ehr"

    def sh(cmd, cwd=None, check=True):
        printable = re.sub(r"hf_[A-Za-z0-9]+", "hf_[REDACTED]", " ".join(cmd))
        print(f"[modal-jlens] $ {printable}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode})")
        return r.returncode

    out = f"/tmp/{RUN_TAG}"
    os.makedirs(out, exist_ok=True)
    os.makedirs(CKPT, exist_ok=True)

    def checkpoint_once(tag=""):
        """Mirror every *.json result file produced so far onto the Modal
        Volume -- this IS the results retrieval path for this run (no
        external upload anywhere): `modal volume get eh-jspace-jlens-logs
        ckpt/<RUN_TAG> <local-dest>`."""
        try:
            for fn in os.listdir(out):
                src = os.path.join(out, fn)
                if os.path.isfile(src) and (fn.endswith(".json") or fn.endswith(".txt")):
                    tmp = os.path.join(CKPT, fn) + ".tmp"
                    shutil.copyfile(src, tmp)
                    os.replace(tmp, os.path.join(CKPT, fn))
            vol.commit()
            print(f"[modal-jlens] checkpoint committed {tag}".rstrip(), flush=True)
        except Exception as e:  # noqa: BLE001 -- a bad checkpoint must never kill the run
            print(f"[modal-jlens] checkpoint FAILED (non-fatal) {tag}: {e}", flush=True)

    stop_ckpt = threading.Event()

    def _ckpt_loop():
        while not stop_ckpt.wait(CKPT_INTERVAL_SEC):
            checkpoint_once(tag="(periodic)")

    ckpt_thread = threading.Thread(target=_ckpt_loop, daemon=True)
    ckpt_thread.start()

    # 1. clone repo at the pinned commit (idempotent on retry).
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "--all", "--tags"], cwd=workspace, check=False)
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)

    exp_dir = os.path.join(workspace, "experiments/j-space-localization-qwen3-4b")
    jlens_script = os.path.join(exp_dir, "jlens.py")
    directions_dir = os.path.join(exp_dir, "analysis-committed")
    # Ephemeral, container-local corpus (never a repo path): built fresh
    # each run by jlens.py build-corpus, which fetches the source pool from
    # the private HF staging repo (STAGING_REPO/POOL_IN_REPO in jlens.py)
    # and re-derives the SAME deterministic 1000-row sample (seed SEED) the
    # local runs use -- see analysis-committed/corpus/
    # jlens_corpus_manifest.json for the row-id manifest that verifies this
    # without any question text living in the repo.
    corpus_path = f"{out}/corpus_pool.jsonl"

    sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
       check=False)

    t0 = time.time()

    # 1b. build the corpus (HF fetch + deterministic re-sample); logged as
    #     its own step so the fetch and row count are visible before any
    #     GPU-heavy stage runs.
    sh([sys.executable, jlens_script, "build-corpus", "--out", corpus_path,
        "--n", str(N_PROMPTS_FULL), "--seed", str(SEED)])
    checkpoint_once(tag="(post-build-corpus)")

    # 2. correctness smoke, full corpus (repeats the local validation at
    #    scale; cheap, final layer only).
    smoke_out = f"{out}/smoke_full.json"
    sh([sys.executable, jlens_script, "smoke",
        "--corpus", corpus_path, "--n-prompts", str(N_PROMPTS_FULL),
        "--n-test-dirs", str(SMOKE_N_TEST_DIRS), "--seed", str(SEED),
        "--out", smoke_out])
    checkpoint_once(tag="(post-smoke)")

    # 3. H1: verbalize the fitted directions at L34 and nearby layers,
    #    full corpus.
    h1_out = f"{out}/h1_full.json"
    sh([sys.executable, jlens_script, "h1",
        "--corpus", corpus_path, "--n-prompts", str(N_PROMPTS_FULL),
        "--directions-dir", directions_dir,
        "--layer-offsets", H1_LAYER_OFFSETS, "--seed", str(SEED),
        "--out", h1_out])
    checkpoint_once(tag="(post-h1)")

    # 4. layer_profile: locate the workspace across depth, full corpus.
    #    This is the dominant-cost stage (see docstring estimate); flushes
    #    partial results after every layer (jlens.py on_layer_done hook),
    #    and each flush is mirrored to the Volume by the periodic
    #    checkpoint thread above, so progress is visible without waiting
    #    for the whole sweep.
    profile_out = f"{out}/profile_full.json"
    sh([sys.executable, jlens_script, "profile",
        "--corpus", corpus_path, "--n-prompts", str(N_PROMPTS_FULL),
        "--layers", PROFILE_LAYERS, "--n-random-dirs", str(PROFILE_N_RANDOM_DIRS),
        "--seed", str(SEED), "--out", profile_out])
    checkpoint_once(tag="(post-profile)")

    t_total = time.time() - t0

    job_log = f"{out}/job_log.txt"
    with open(job_log, "w") as fh:
        fh.write(f"run_tag={RUN_TAG} seed={SEED} model={MODEL_BF16}\n"
                 f"total_sec={t_total:.1f}\n"
                 f"n_prompts={N_PROMPTS_FULL} profile_layers={PROFILE_LAYERS} "
                 f"profile_n_random_dirs={PROFILE_N_RANDOM_DIRS}\n")

    stop_ckpt.set()
    ckpt_thread.join(timeout=30)
    checkpoint_once(tag="(final, includes job_log.txt)")
    try:
        with open(f"{CKPT}/DONE", "w") as fh:
            fh.write(f"run_tag={RUN_TAG} total_sec={t_total:.1f}\n")
        vol.commit()
        print("[modal-jlens] DONE marker written to CKPT", flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"[modal-jlens] DONE marker write failed (non-fatal): {e}", flush=True)

    print(f"[modal-jlens] DONE total={t_total:.0f}s -- pull results with "
          f"`modal volume get eh-jspace-jlens-logs ckpt/{RUN_TAG} <local-dest>`",
          flush=True)
    return {"status": "completed", "total_sec": round(t_total, 1)}


@app.local_entrypoint()
def main():
    if REPO_COMMIT.startswith("REPLACE_WITH"):
        raise SystemExit("[modal-jlens] REPO_COMMIT is a placeholder; pin the "
                         "j-lens harness commit before launch (second commit).")

    launch_ok = os.environ.get("EHR_LAUNCH_OK")
    if launch_ok != EXPERIMENT_SLUG:
        raise SystemExit(
            "[modal-jlens] refusing to launch: set "
            f"EHR_LAUNCH_OK={EXPERIMENT_SLUG!r} in the environment (lead "
            f"approval, relayed after review), got EHR_LAUNCH_OK={launch_ok!r}.")

    cap_raw = os.environ.get("MODAL_COST_CAP_USD")
    if not cap_raw:
        raise SystemExit(
            "[modal-jlens] refusing to launch: set MODAL_COST_CAP_USD (the "
            "pre-registered cap, e.g. 25) in the environment; this script "
            "does not hardcode a cap value.")
    try:
        cap_usd = float(cap_raw)
    except ValueError:
        raise SystemExit(f"[modal-jlens] MODAL_COST_CAP_USD={cap_raw!r} is not a number")

    derived_timeout_sec = _timeout_seconds_for_cap(cap_usd)
    print(f"[modal-jlens] cost cap ${cap_usd:.2f} -> derived safety timeout "
          f"{derived_timeout_sec/3600:.2f}h (function timeout stays fixed at "
          f"{DEFAULT_TIMEOUT_HOURS}h; this is a REPORTED consistency check, "
          "not a live re-decoration of the deployed function's timeout)")
    if derived_timeout_sec < DEFAULT_TIMEOUT_HOURS * HOURS:
        print(f"[modal-jlens] WARNING: at the assumed ${ASSUMED_A10G_USD_PER_HOUR}/hr "
              f"A10G rate, the ${cap_usd:.2f} cap affords less than the function's "
              f"{DEFAULT_TIMEOUT_HOURS}h timeout ceiling; the job could exceed the "
              "cap before the timeout kills it. Monitor the Modal dashboard.")

    print(f"[modal-jlens] launching J-lens full characterization on A10G, "
          f"run_tag={RUN_TAG}")
    print(f"[modal-jlens] repo@{REPO_COMMIT[:12]} model={MODEL_BF16} seed={SEED}")
    call = run_jlens.spawn()
    print(f"[modal-jlens] spawned function call {call.object_id}; client exiting. "
          f"Monitor: modal app logs, or `modal volume get eh-jspace-jlens-logs "
          f"ckpt/{RUN_TAG} <local-dest>` for progress/results.")
