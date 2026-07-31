"""Modal harness -- Phase B of gemma4-e4b-kv-seam-quarantine.

Pre-registered: experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md,
"Revision 2026-07-30 (lane change for Phase B, PI-approved)" (Design section).
Derived stage plan: cloud/PHASE_B_MODAL_PLAN.md -- read that file before
touching this one; it cites the exact doc lines every stage below implements.

BUILD AND DRY-RUN ONLY as of this writing. No GPU function in this file has
been launched. `EHR_LAUNCH_OK=gemma4-e4b-kv-seam-quarantine` (this repo's
launch-guard hook, .claude/hooks/launch_guard.sh) plus the lead's explicit go
are both required before any stage below actually spawns.

WHY A DOCKERFILE-BUILT IMAGE, not modal.Image.from_registry like the AK/AP/AM
lineage: those experiments run generic HF models with no exotic modeling-code
dependency. This one hooks Gemma-4's KV-sharing internals
(`kv_shared_layer_index`, `DynamicCache` truncation), which are
version-fragile -- NOTEBOOK.md's 2026-07-29 entry recorded a live crash
(`AttributeError: 'Gemma4TextAttention' object has no attribute
'kv_shared_layer_index'`) under transformers==5.12.1, resolved only by
pinning transformers==5.5.0, the version kv_seam_patch.py / kv_seam_preflight.py
were actually validated against. The LOCAL lane's answer to this was a
purpose-built Docker image (synaptic-tuner/docker/mechinterp-runner, tf550
tag). Revision 2026-07-30 condition (1) requires the Modal image reproduce
those exact pins. `modal.Image.from_dockerfile` on that same Dockerfile with
the same build args is the only way to satisfy "exactly" rather than
"approximately" -- reimplementing the pip list by hand here would be a second,
driftable copy of the same pin set.

Stage inputs: the pinned .py modules, families/gemma4-e4b.yaml, cell.yaml,
gates.yaml, and the committed common/experiment artifacts all live in git and
are cloned at a pinned commit (REPO_COMMIT below), exactly like the AK/AP
precedent. The two PRIVATE, gitignored inputs (eval_rows.jsonl question/alias
text, anchor_extract.safetensors) are NOT in git and are staged via
cloud/stage_private_inputs.py directly onto this app's own Modal Volume
(`modal volume put`, under `private-inputs/`) before any GPU stage can run --
see that file's docstring; this script's GPU stages copy them out of the
mounted volume, never from a local path or a third-party host.

Launch with BOTH --detach and --wait (one stage per invocation; see
cloud/PHASE_B_MODAL_PLAN.md for the dependency order -- B16/B17 must not be
launched before B-C1 resolves, and B-C1 itself has NO PRODUCER SCRIPT YET,
see the plan's "Gap 1"). --detach keeps the spawned `run_stage` call alive on
Modal's side even if this local client disconnects; --wait makes `main()`
block on the call's result and exit nonzero on failure, which is what makes
a SEQUENTIAL dispatch (cloud/run_tranche1.sh) actually enforce ordering.
Neither flag alone is enough: --wait without --detach still blocks correctly
under normal conditions but risks the call dying if the local network drops;
--detach without --wait returns immediately after `.spawn()` and, without a
long-lived client, tears the ephemeral App down before the call runs at all
-- confirmed directly, see `main()`'s `if not wait:` branch for the incident
this fixed (2026-07-30, all 18 tranche-1 stages "completed" in 26 seconds
having done nothing):

    EHR_LAUNCH_OK=gemma4-e4b-kv-seam-quarantine \\
    modal run --detach cloud/modal_phase_b.py --stage b1_extract_off_midband --wait

Dry-run, no GPU, no launch gate required (this is what this build pass
actually ran):

    modal run cloud/modal_phase_b.py::version_check
    python3 cloud/stage_private_inputs.py --dry-run
"""

from __future__ import annotations

import os
from pathlib import Path

import modal

# --- provenance pins ---------------------------------------------------------
REPO_URL = "https://github.com/ProfSynapse/Epistemic-Humility-Research.git"
# exp/kv-seam-phase-b branch HEAD at tranche-1 launch time (2026-07-30) --
# the commit carrying the lead's LAUNCH RECORD in AMENDMENT.md, pushed and
# confirmed as origin/exp/kv-seam-phase-b's tip. Its immediate parent
# (4c49f9b2, "EHR main HEAD at plan time" -- this pin's prior value) already
# carried everything Phase A produced and synaptic-tuner pinned at
# TUNER_COMMIT below (git submodule status, verified directly); this bump is
# ONLY to pick up the launch record itself, so the in-container checkout is
# never running ahead of what the governing doc says is authorized.
REPO_COMMIT = "86fc6e424f98e6587d0d8907b9fa90f08997e2e3"
TUNER_COMMIT = "34c89fc4f9d693a6b997422288d820e9c30b4696"
TRANSFORMERS_VERSION = "5.5.0"
EXPERIMENT_SLUG = "gemma4-e4b-kv-seam-quarantine"
EXP_DIR = f"experiments/{EXPERIMENT_SLUG}"

# Private-inputs paths within the mounted Volume (VOL_MOUNT below). Must
# match cloud/stage_private_inputs.py's DEST_IN_VOLUME exactly -- that script
# and this one address the SAME volume.
POOL_IN_VOLUME = "private-inputs/eval_rows.jsonl"
ANCHOR_ON_IN_VOLUME = "private-inputs/anchor_extract.safetensors"
ANCHOR_ON_MANIFEST_IN_VOLUME = "private-inputs/anchor_extract_manifest.json"
POOL_GENERATIONS_IN_VOLUME = "private-inputs/pool_generations.jsonl"
RESULT_PREFIX = "phase-b-r1"

HOURS = 60 * 60
CKPT_INTERVAL_SEC = 120

# --- the pinned Dockerfile, built with the SAME build args the local tf550
# image used (NOTEBOOK.md:1026-1034). Path is relative to this repo's root;
# Modal uploads the Dockerfile's own directory as build context (entrypoint.sh
# + print_provenance.py live alongside it and are COPYed in by the Dockerfile
# itself). -----------------------------------------------------------------
#
# This whole module gets re-imported a SECOND time inside the container to
# resolve function references (Modal copies just this script to a shallow
# path, e.g. /root/modal_phase_b.py -- confirmed directly from a crash-loop
# traceback, 2026-07-30). `Path(__file__).resolve().parents[3]` is only
# meaningful for the FIRST (local, `modal run`) import, where this file sits
# 3 levels under the repo root; inside the container `.parents` has only 1-2
# entries and a bare `[3]` raises IndexError before any function body ever
# runs -- version_check crash-loops with no chance to print anything. The
# resolved value is never used once the image is already built (the
# in-container import doesn't rebuild it), so this only needs to not crash
# there, not be correct there.
_here_parents = Path(__file__).resolve().parents
_DOCKERFILE_DIR = (
    _here_parents[3] / "synaptic-tuner" / "docker" / "mechinterp-runner"
    if len(_here_parents) > 3 else Path("/nonexistent-not-needed-in-container")
)
DOCKERFILE_PATH = _DOCKERFILE_DIR / "Dockerfile"

image = modal.Image.from_dockerfile(
    DOCKERFILE_PATH,
    # Both Dockerfile COPY sources (entrypoint.sh, print_provenance.py) are
    # relative to the Dockerfile's OWN directory, not the caller's cwd --
    # from_dockerfile's default context_dir is the process cwd (matching
    # `docker build -f path/to/Dockerfile .`), which is
    # experiments/gemma4-e4b-kv-seam-quarantine when this script is invoked
    # per its own docstring's example, not synaptic-tuner/docker/
    # mechinterp-runner/. Without this the build fails at the COPY step
    # with "source path does not exist" (hit and confirmed on the first
    # real version_check run, 2026-07-30).
    context_dir=_DOCKERFILE_DIR,
    build_args={
        "TRANSFORMERS_VERSION": TRANSFORMERS_VERSION,
        "MECHINTERP_RUNNER_GIT_REVISION": TUNER_COMMIT,
    },
)
# NOTE: do NOT append a `.pip_install("huggingface_hub...")` layer here. The
# Dockerfile already pins huggingface_hub==1.23.0, chosen (with the rest of
# the pin set) to match transformers==5.5.0's expectations. An earlier draft
# of this file added `.pip_install("huggingface_hub>=0.34,<1.0")` on top --
# a leftover from the original hf_hub_download-based private-input-staging
# design (superseded by the Modal-Volume staging above) -- which SILENTLY
# DOWNGRADED huggingface_hub below 1.0 after the Dockerfile's own pin.
# Confirmed broken directly: version_check's first real run (2026-07-30)
# came back with `"transformers_error": "cannot import name 'is_offline_mode'
# from 'huggingface_hub'"` -- transformers 5.5.0 does not import cleanly
# against the downgraded huggingface_hub. Removed; huggingface_hub stays at
# the Dockerfile's pinned 1.23.0 exactly.

app = modal.App(f"eh-{EXPERIMENT_SLUG}-phase-b", image=image)

vol = modal.Volume.from_name(f"eh-{EXPERIMENT_SLUG}-phase-b-logs", create_if_missing=True)
VOL_MOUNT = "/vol/phasebtlogs"


# --- stage registry -----------------------------------------------------------
# One entry per row of cloud/PHASE_B_MODAL_PLAN.md's derived stage table.
# `gpu`: False = CPU-only (still runs inside the pinned image for identical
# library versions, per Revision condition (2) -- "same-environment
# internally"). `needs`: stage ids that must have a committed output present
# before this one is meaningful; checked (not enforced) at dispatch so a
# resume-safe re-run of an already-done stage is cheap, not so an
# out-of-order launch is silently allowed.
STAGES: dict[str, dict] = {
    "b0_g0kv_preflight": {
        "gpu": False,
        "cmd": ["python3", "kv_seam_preflight.py"],
        "needs": [],
        "produces": None,  # stdout-only PASS/FAIL, not a committed artifact
    },
    "b1_extract_off_midband": {
        "gpu": True,
        "cmd": ["python3", "extract_anchor.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off"],
        "needs": ["b0_g0kv_preflight"],
        "produces": "analysis/gemma4-e4b/anchor_extract.kv_off.safetensors",
    },
    "b2_extract_off_seampair": {
        "gpu": True,
        "cmd": ["python3", "extract_anchor.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off"],
        "needs": ["b0_g0kv_preflight"],
        "produces": "analysis/gemma4-e4b/anchor_extract.kv_off.safetensors",
    },
    "b3_alin_part2": {
        "gpu": False,
        "cmd": ["python3", "alin_sweep.py", "--site", "38",
                "--both-conditions", "--emit-selection"],
        "needs": ["b1_extract_off_midband"],
        "produces": "analysis-committed/gemma4-e4b/alin_part2_discrimination.json",
    },
    # b-c1 (G0-C1 precondition control) intentionally NOT registered here --
    # no producer script exists yet (PHASE_B_MODAL_PLAN.md "Gap 1"). Adding a
    # stub would misrepresent the instrument as complete.
    "b4_directions_a1": {
        "gpu": False,
        "cmd": ["python3", "build_directions.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "on"],
        "needs": [],
        "produces": "analysis-committed/gemma4-e4b/layers/hs38/u_d_hs38.json",
    },
    "b5_directions_a2": {
        "gpu": False,
        "cmd": ["python3", "build_directions.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off"],
        "needs": ["b1_extract_off_midband"],
        "produces": "analysis-committed/gemma4-e4b/layers/hs38/u_d_hs38.kv_off.json",
    },
    "b6_directions_a4": {
        "gpu": False,
        "cmd": ["python3", "build_directions.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off"],
        "needs": ["b2_extract_off_seampair"],
        "produces": "analysis-committed/gemma4-e4b/layers/hs22/u_d_hs22.kv_off.json",
    },
    "b7_gatefit_a1": {
        "gpu": False,
        "cmd": ["python3", "gate_fit.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "on"],
        "needs": ["b4_directions_a1"],
        "produces": "analysis-committed/gemma4-e4b/gate_fit_layers.json",
    },
    "b7_gatefit_a2": {
        "gpu": False,
        "cmd": ["python3", "gate_fit.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off"],
        "needs": ["b5_directions_a2"],
        "produces": "analysis-committed/gemma4-e4b/gate_fit_layers.kv_off.json",
    },
    "b7_gatefit_a4": {
        "gpu": False,
        "cmd": ["python3", "gate_fit.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off"],
        "needs": ["b6_directions_a4"],
        "produces": "analysis-committed/gemma4-e4b/gate_fit_layers.seam_pair.kv_off.json",
    },
    "b8_dose_a1": {
        "gpu": True,
        "cmd": ["python3", "calibrate_dose.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "on"],
        "needs": ["b7_gatefit_a1"],
        "produces": "analysis-committed/gemma4-e4b/dose_calibration_summary.json",
        "verdict_exit_ok": True,
    },
    "b9_dose_a2": {
        "gpu": True,
        "cmd": ["python3", "calibrate_dose.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off"],
        "needs": ["b7_gatefit_a2"],
        "produces": "analysis-committed/gemma4-e4b/dose_calibration_summary.kv_off.json",
        "verdict_exit_ok": True,
    },
    "b10_dose_a4": {
        "gpu": True,
        "cmd": ["python3", "calibrate_dose.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off"],
        "needs": ["b7_gatefit_a4"],
        "produces": "analysis-committed/gemma4-e4b/dose_calibration_summary.seam_pair.kv_off.json",
        "verdict_exit_ok": True,
    },
    "b11_smoke_a1": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "on", "--mode", "smoke",
                "--n-rows", "8", "--i-know-this-is-the-cross-family-run"],
        "needs": ["b8_dose_a1"],
        "produces": "analysis/gemma4-e4b/smoke_summary.json",
    },
    "b12_smoke_a2": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off", "--mode", "smoke",
                "--n-rows", "8", "--i-know-this-is-the-cross-family-run"],
        "needs": ["b9_dose_a2"],
        "produces": "analysis/gemma4-e4b/smoke_summary.kv_off.json",
    },
    "b13_smoke_a4": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off", "--mode", "smoke",
                "--n-rows", "8", "--i-know-this-is-the-cross-family-run"],
        "needs": ["b10_dose_a4"],
        "produces": "analysis/gemma4-e4b/smoke_summary.seam_pair.kv_off.json",
    },
    "b14_full_a1": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "on", "--mode", "full",
                "--i-know-this-is-the-cross-family-run"],
        "needs": ["b11_smoke_a1"],
        "produces": "analysis-committed/gemma4-e4b/full_summary.json",
        "gate_note": "g1_actuation_floor / g2_selectivity_cap. NOT gated by C1 "
                     "(C1 governs OFF arms only).",
    },
    "b15_undosed_a1": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "on", "--mode", "full",
                "--arm-kind", "undosed", "--i-know-this-is-the-cross-family-run"],
        "needs": ["b14_full_a1"],
        "produces": "analysis-committed/gemma4-e4b/undosed_summary.hs38.json",
    },
    "b16_full_a2": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off", "--mode", "full",
                "--i-know-this-is-the-cross-family-run"],
        "needs": ["b12_smoke_a2"],
        "produces": "analysis-committed/gemma4-e4b/full_summary.kv_off.json",
        "gate_note": "PRIMARY. gates.yaml g0_c1_precondition_control: if C1 "
                     "fails, A2 is recorded NOT-RUN instead. DO NOT LAUNCH "
                     "before b-c1 (no producer script yet) resolves PASS.",
        "blocked_on_c1": True,
    },
    "b17_full_a4": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off", "--mode", "full",
                "--i-know-this-is-the-cross-family-run"],
        "needs": ["b13_smoke_a4"],
        "produces": "analysis-committed/gemma4-e4b/full_summary.seam_pair.kv_off.json",
        "gate_note": "Same C1 gating as b16 (A4 named explicitly in gates.yaml).",
        "blocked_on_c1": True,
    },
    "b18a_undosed_a2": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "midband", "--kv-sharing", "off", "--mode", "full",
                "--arm-kind", "undosed", "--i-know-this-is-the-cross-family-run"],
        "needs": ["b16_full_a2"],
        "produces": "analysis-committed/gemma4-e4b/undosed_summary.hs38.kv_off.json",
        "blocked_on_c1": True,
    },
    "b18b_undosed_a4": {
        "gpu": True,
        "cmd": ["python3", "run_contrast.py", "--family", "gemma4-e4b",
                "--site-set", "seam_pair", "--kv-sharing", "off", "--mode", "full",
                "--arm-kind", "undosed", "--i-know-this-is-the-cross-family-run"],
        "needs": ["b17_full_a4"],
        "produces": "analysis-committed/gemma4-e4b/undosed_summary.hs22.seam_pair.kv_off.json",
        "blocked_on_c1": True,
    },
    # b19 (fired-only G2 companion) does NOT exist as a separate stage:
    # g2_companion.py has no CLI (`python3 g2_companion.py --help` prints
    # nothing -- confirmed directly, not assumed from its docstring). It is a
    # pure library module imported by pipeline.py / run_contrast.py, so the
    # companion metric is already embedded in every full_summary.*.json B14/
    # B16/B17/B18a/B18b produce (visible in Phase A's Stage 2 output as the
    # "fired_only" / "undosed_floor" blocks). No dispatchable stage here.
    "b_c1_precondition": {
        # Producer for gates.yaml g0_c1_precondition_control, filling the
        # instrument gap the plan doc calls "Gap 1". Registered by the lead
        # after review (NOTEBOOK.md 2026-07-30 C1 entry): reference
        # completion = the row's C0 greedy completion teacher-forced under
        # BOTH conditions, paired per row; rollup.c1_verdict arithmetic
        # imported unchanged. Needs no Phase B stage output (FIT split,
        # undosed, both KV conditions in one process), only the staged
        # private inputs. Gates tranche 2: b16/b17/b18a/b18b/b20 stay
        # blocked until this stage's committed summary exists AND passes.
        "gpu": True,
        "cmd": ["python3", "c1_precondition.py", "--family", "gemma4-e4b"],
        "needs": [],
        "produces": "analysis-committed/gemma4-e4b/c1_precondition_summary.json",
    },
    "b20_rollup": {
        "gpu": False,
        "cmd": ["python3", "rollup.py"],
        "needs": ["b3_alin_part2", "b14_full_a1", "b15_undosed_a1",
                  "b16_full_a2", "b17_full_a4", "b18a_undosed_a2",
                  "b18b_undosed_a4"],
        "produces": "analysis-committed/gemma4-e4b/rollup_summary.json",
        "gate_note": "BLOCKED until c1_precondition_summary.json exists "
                     "(rollup.py:401-408 raises RollupInputMissing before "
                     "producing anything). Do not dispatch until Gap 1 lands.",
        "blocked_on_c1": True,
    },
}

# GPU is an OPERATOR ARGUMENT, not a hardcoded constant (PI directive,
# 2026-07-30, .skills/mechinterp-cells/reference/modal-launch.md "GPU sizing
# rule"): set PHASEB_GPU at dispatch, e.g.
#   PHASEB_GPU=L40S modal run --detach cloud/modal_phase_b.py --stage ... --wait
# The default stays A100-80GB for THIS experiment only, for arm-parity: the
# A1 arm already ran on A100-80GB, and paired arms of one registered contrast
# stay on identical hardware (rule 4). Future lanes size the default to the
# model's actual footprint at harness review; an E4B-class model like this
# one fits an L40S. The resolved value is recorded per stage in provenance
# (gpu_type) so the executed hardware is auditable.
GPU_TYPE = os.environ.get("PHASEB_GPU", "A100-80GB")


def _run_tag(stage: str) -> str:
    return f"phase-b-{stage}-r1"


@app.function(image=image)
def version_check():
    """CPU-only. No GPU, no repo clone, no secret needed. Confirms the image
    itself carries the pinned versions before anything else is attempted."""
    import json
    import subprocess
    import sys

    out: dict = {"event": "phase_b_version_check"}
    try:
        import torch
        out["torch"] = torch.__version__
        out["cuda_available"] = bool(torch.cuda.is_available())
    except Exception as e:  # noqa: BLE001
        out["torch_error"] = str(e)
    try:
        import transformers
        out["transformers"] = transformers.__version__
        assert transformers.__version__ == TRANSFORMERS_VERSION, (
            f"pinned transformers=={TRANSFORMERS_VERSION}, image has "
            f"{transformers.__version__}"
        )
    except Exception as e:  # noqa: BLE001
        out["transformers_error"] = str(e)
    try:
        import accelerate
        out["accelerate"] = accelerate.__version__
    except Exception as e:  # noqa: BLE001
        out["accelerate_error"] = str(e)
    try:
        import inspect
        from transformers.models.gemma4 import modeling_gemma4
        src = inspect.getsource(modeling_gemma4)
        out["kv_shared_layer_index_present"] = "kv_shared_layer_index" in src
    except Exception as e:  # noqa: BLE001
        out["gemma4_import_error"] = str(e)
    out["python"] = sys.version.split()[0]
    out["image_git_revision"] = os.environ.get(
        "MECHINTERP_RUNNER_GIT_REVISION", "unknown")
    print(json.dumps(out, sort_keys=True), flush=True)
    return out


@app.function(
    gpu=GPU_TYPE,
    timeout=6 * HOURS,
    volumes={VOL_MOUNT: vol},
    secrets=[modal.Secret.from_name("hf-token")],
    retries=modal.Retries(max_retries=2, backoff_coefficient=1.0, initial_delay=10.0),
)
def run_stage(stage: str, dispatched_gpu_type: str = ""):
    """Generic per-stage runner. Clones the repo at REPO_COMMIT, checks the
    synaptic-tuner submodule out to TUNER_COMMIT explicitly (overriding
    whatever main's pointer says, in case it has moved since REPO_COMMIT was
    picked), copies the private staged inputs out of the mounted Volume, runs
    the stage's pinned CLI invocation unmodified, uploads whatever it
    produced, and writes a per-stage provenance line."""
    import json
    import shutil
    import subprocess
    import sys
    import time

    spec = STAGES.get(stage)
    if spec is None:
        raise RuntimeError(f"unknown stage {stage!r}; see STAGES in this file")

    def sh(cmd, cwd=None, check=True):
        print(f"[modal-phaseb:{stage}] $ {' '.join(cmd)}", flush=True)
        r = subprocess.run(cmd, cwd=cwd)
        if check and r.returncode != 0:
            raise RuntimeError(f"command failed ({r.returncode}): {' '.join(cmd)}")
        return r.returncode

    workspace = "/workspace/ehr"
    if not os.path.isdir(os.path.join(workspace, ".git")):
        sh(["git", "clone", REPO_URL, workspace])
    sh(["git", "fetch", "--all", "--tags"], cwd=workspace, check=False)
    sh(["git", "checkout", REPO_COMMIT], cwd=workspace)
    sh(["git", "submodule", "update", "--init", "--recursive"], cwd=workspace)
    tuner_dir = os.path.join(workspace, "synaptic-tuner")
    sh(["git", "checkout", TUNER_COMMIT], cwd=tuner_dir)
    # structural check this experiment's AMENDMENT.md requires (line 561-563):
    # the tuner commit must carry the Gemma-4 decoder-layer-path fix,
    # verified structurally not by version comparison.
    check = subprocess.run(
        ["grep", "-n", "model.language_model.layers",
         os.path.join(tuner_dir, "MechInterp/intervention/hooks.py")],
        capture_output=True, text=True,
    )
    if check.returncode != 0:
        raise RuntimeError(
            "structural check FAILED: 'model.language_model.layers' not found "
            "in synaptic-tuner MechInterp/intervention/hooks.py at "
            f"{TUNER_COMMIT} -- Gemma-4 decoder blocks unreachable, every GPU "
            "stage of this experiment would fail at first hook install."
        )
    print(f"[modal-phaseb:{stage}] structural check PASS: {check.stdout.strip()}",
          flush=True)

    exp_dir = os.path.join(workspace, EXP_DIR)

    private_dir = os.path.join(exp_dir, "analysis", "gemma4-e4b")
    os.makedirs(private_dir, exist_ok=True)
    try:
        vol.reload()  # pick up files `modal volume put` wrote from the host,
                       # outside this container's own writes
    except Exception as e:  # noqa: BLE001
        print(f"[modal-phaseb:{stage}] vol.reload() before private-input "
              f"copy failed (non-fatal): {e}", flush=True)
    pool_in_vol = os.path.join(VOL_MOUNT, POOL_IN_VOLUME)
    anchor_in_vol = os.path.join(VOL_MOUNT, ANCHOR_ON_IN_VOLUME)
    anchor_manifest_in_vol = os.path.join(VOL_MOUNT, ANCHOR_ON_MANIFEST_IN_VOLUME)
    if (not os.path.isfile(pool_in_vol) or not os.path.isfile(anchor_in_vol)
            or not os.path.isfile(anchor_manifest_in_vol)):
        raise RuntimeError(
            f"[modal-phaseb:{stage}] private inputs not found on the mounted "
            f"volume ({pool_in_vol}, {anchor_in_vol}, "
            f"{anchor_manifest_in_vol}). Run "
            "`python3 cloud/stage_private_inputs.py --execute` from the host "
            "before dispatching any GPU stage."
        )
    rows_local = os.path.join(private_dir, "eval_rows.jsonl")
    shutil.copyfile(pool_in_vol, rows_local)
    print(f"[modal-phaseb:{stage}] copied {pool_in_vol} -> {rows_local}",
          flush=True)
    # ON anchor cache is only needed by stages that touch the ON condition
    # directly (b4, b7_gatefit_a1, b8, b11, b14, b15, b0/b3 read it too via
    # alin_sweep's default parent-analysis path). Copy unconditionally --
    # it's 342MB once per container, cheap next to model weights, and reading
    # from the mounted volume (not a network fetch) is effectively free.
    anchor_local = os.path.join(private_dir, "anchor_extract.safetensors")
    shutil.copyfile(anchor_in_vol, anchor_local)
    print(f"[modal-phaseb:{stage}] copied {anchor_in_vol} -> {anchor_local}",
          flush=True)
    # The manifest is the safetensors' inseparable half: ON-condition
    # consumers (alin_sweep part 2, build_directions --kv-sharing on, ...)
    # resolve the pair together and fail closed when either is missing
    # (b3 halt, 2026-07-30 17:21Z, first live run of this path).
    anchor_manifest_local = os.path.join(private_dir, "anchor_extract_manifest.json")
    shutil.copyfile(anchor_manifest_in_vol, anchor_manifest_local)
    print(f"[modal-phaseb:{stage}] copied {anchor_manifest_in_vol} -> "
          f"{anchor_manifest_local}", flush=True)
    # Restricted parent-experiment generations: alin_sweep part 2 reads
    # `analysis/<family>/pool_generations.jsonl` to build its targets
    # (second live b3 halt, 2026-07-30 17:28Z). Copy when staged; absence is
    # fatal only for b3, so the check is stage-scoped rather than global.
    pool_gen_in_vol = os.path.join(VOL_MOUNT, POOL_GENERATIONS_IN_VOLUME)
    if os.path.isfile(pool_gen_in_vol):
        pool_gen_local = os.path.join(private_dir, "pool_generations.jsonl")
        shutil.copyfile(pool_gen_in_vol, pool_gen_local)
        print(f"[modal-phaseb:{stage}] copied {pool_gen_in_vol} -> "
              f"{pool_gen_local}", flush=True)
    elif stage == "b3_alin_part2":
        raise RuntimeError(
            f"[modal-phaseb:{stage}] {pool_gen_in_vol} not staged; alin_sweep "
            "part 2 cannot build targets without it. Run "
            "`python3 cloud/stage_private_inputs.py --execute` from the host."
        )
    # Layout shim: the ON extraction manifest records rows_path as the
    # ABSOLUTE host path of the parent experiment's eval_rows.jsonl (a
    # machine-local layout that does not exist in this container), and
    # alin_sweep part 2 fails closed on it. The staged eval_rows.jsonl is
    # byte-identical to that parent file (sha 7a2784bd, verified on the host
    # before staging), so materializing the recorded path with the staged
    # copy reconstructs the exact layout the manifest describes.
    try:
        with open(anchor_manifest_local) as fh:
            recorded_rows_path = json.load(fh).get("rows_path")
    except Exception as e:  # noqa: BLE001
        recorded_rows_path = None
        print(f"[modal-phaseb:{stage}] could not parse rows_path from the ON "
              f"manifest (non-fatal outside b3): {e}", flush=True)
    if recorded_rows_path and not os.path.exists(recorded_rows_path):
        os.makedirs(os.path.dirname(recorded_rows_path), exist_ok=True)
        shutil.copyfile(rows_local, recorded_rows_path)
        print(f"[modal-phaseb:{stage}] layout shim: staged eval_rows "
              f"materialized at manifest rows_path {recorded_rows_path}",
              flush=True)

    # Restore each needs-stage's own analysis/ + analysis-committed/ output
    # from ITS ckpt mirror into this (fresh) container's workspace. Every
    # container starts from a clean `git clone` at the FIXED REPO_COMMIT, so
    # nothing a Phase B stage produces during this tranche is visible to a
    # later stage any other way: the resume-safety block below only restores
    # THIS stage's own prior partial run, never a different stage's, and
    # `stage_private_inputs.py` only stages the two upstream pool/anchor
    # inputs, not per-stage outputs. Confirmed as a real gap by TRACING the
    # actual consumer, not assuming from `produces`: build_directions.py
    # --kv-sharing off (b5/b6) reads `analysis/gemma4-e4b/
    # anchor_extract.kv_off.safetensors` AND `anchor_extract_manifest.
    # kv_off.json` via `kv_seam_patch.condition_artifact` (build_directions.py
    # ~157-161) -- both written by b1/b2 to their PRIVATE analysis/ dir, and
    # the manifest specifically was invisible to the `produces` field
    # entirely (only the .safetensors file is tracked there). Every stage
    # with a nonempty `needs` list is affected the same way (extractions ->
    # direction fits -> gate fits -> dose calibration -> smoke -> full),
    # since ALL of those artifacts are Phase-B-fresh and none are in git at
    # REPO_COMMIT. Restoring the WHOLE subtree (not just the one `produces`
    # path) rather than enumerating every side-artifact each script writes.
    for needed in spec.get("needs", []):
        needed_ckpt = f"{VOL_MOUNT}/ckpt/{_run_tag(needed)}"
        prov_path = os.path.join(needed_ckpt, f"provenance_{needed}.json")
        try:
            vol.reload()
        except Exception as e:  # noqa: BLE001
            print(f"[modal-phaseb:{stage}] vol.reload() before needs-restore "
                  f"of {needed!r} failed (non-fatal): {e}", flush=True)
        if not os.path.isfile(prov_path):
            raise RuntimeError(
                f"[modal-phaseb:{stage}] needs-stage {needed!r} has no "
                f"provenance file at {prov_path} -- it has not completed on "
                "Modal yet (or the volume has not synced). Dispatch "
                f"{needed!r} first; refusing to run {stage!r} against "
                "missing/unverified upstream output."
            )
        for sub in ("analysis-committed", "analysis"):
            src = os.path.join(needed_ckpt, sub)
            dst = os.path.join(exp_dir, sub)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"[modal-phaseb:{stage}] restored needs-stage {needed!r} "
              f"output from {needed_ckpt}", flush=True)

    # resume-safety: if the stage's expected output already exists in this
    # container's restored volume mirror of analysis-committed/, skip.
    run_tag = _run_tag(stage)
    ckpt = f"{VOL_MOUNT}/ckpt/{run_tag}"
    committed_dir = os.path.join(exp_dir, "analysis-committed", "gemma4-e4b")
    if os.path.isdir(ckpt):
        try:
            vol.reload()
        except Exception as e:  # noqa: BLE001
            print(f"[modal-phaseb:{stage}] vol.reload() failed (non-fatal): {e}",
                  flush=True)
        for root, _dirs, files in os.walk(os.path.join(ckpt, "analysis-committed")):
            rel = os.path.relpath(root, os.path.join(ckpt, "analysis-committed"))
            tgt = committed_dir if rel == "." else os.path.join(committed_dir, rel)
            os.makedirs(tgt, exist_ok=True)
            for fn in files:
                shutil.copyfile(os.path.join(root, fn), os.path.join(tgt, fn))
    expected = spec.get("produces")
    if expected:
        expected_path = os.path.join(workspace, expected)
        if os.path.isfile(expected_path):
            print(f"[modal-phaseb:{stage}] SKIP -- expected output already "
                  f"present: {expected}", flush=True)
            return {"status": "skipped-already-done", "stage": stage,
                    "output": expected}

    if spec.get("blocked_on_c1"):
        raise RuntimeError(
            f"stage {stage!r} is gated on the G0-C1 precondition control "
            "(gates.yaml g0_c1_precondition_control). No producer script "
            "exists for c1_precondition_summary.json as of this harness's "
            "build (see cloud/PHASE_B_MODAL_PLAN.md 'Gap 1'). Refusing to "
            "run rather than silently proceeding as if C1 had passed."
        )

    sh(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
       check=False)

    # verdict_exit_ok stages (calibrate_dose.py) use their process exit code
    # to carry a REGISTERED VERDICT, not just crash/success: main() there
    # `return 0 if summary["all_midband_have_usable_dose"] else 1` -- exit 1
    # means "ran its full sweep, wrote its summary, found no usable mid-band
    # dose," which is pinned, pre-registered instrument behavior (see
    # calibrate_dose.py), not an infra failure. For those stages only, run
    # with check=False so a nonzero exit does not raise here; the artifact's
    # actual presence on disk (not the exit code) decides crash vs verdict.
    t0 = time.time()
    verdict_exit_ok = bool(spec.get("verdict_exit_ok"))
    rc = sh(spec["cmd"], cwd=exp_dir, check=not verdict_exit_ok)
    t_elapsed = time.time() - t0

    is_verdict_exit = verdict_exit_ok and rc != 0
    if is_verdict_exit:
        expected = spec.get("produces")
        # calibrate_dose.py resolves its own output dir from its own file
        # location (HERE = Path(__file__).resolve().parent, confirmed by
        # reading calibrate_dose.py directly), i.e. exp_dir -- the same cwd
        # this sh() call ran with -- not the repo-root `workspace` the
        # separate resume-SKIP check below happens to use for its own
        # (pre-existing, untouched) path.
        expected_path = os.path.join(exp_dir, expected) if expected else None
        if not expected_path or not os.path.isfile(expected_path):
            raise RuntimeError(
                f"[modal-phaseb:{stage}] command exited {rc} (a "
                "verdict_exit_ok stage) but its expected produces artifact "
                f"{expected!r} is missing at {expected_path} -- treating "
                "this as a real crash, not a registered verdict; refusing "
                "to silently swallow it."
            )
        print(f"[modal-phaseb:{stage}] verdict exit {rc}: {expected} is "
              "present on disk -- recording as a registered calibration "
              "verdict (no usable mid-band dose), not an infra failure",
              flush=True)

    provenance = {
        "event": "phase_b_stage_provenance", "stage": stage,
        "image_transformers": TRANSFORMERS_VERSION,
        "tuner_commit": TUNER_COMMIT, "repo_commit": REPO_COMMIT,
        # dispatched_gpu_type is the LOCAL dispatch-side resolution of
        # PHASEB_GPU, passed as a function argument: the container re-imports
        # this module, so reading the env here would report the container's
        # environment, not the operator's choice that actually sized the GPU.
        "gpu": spec["gpu"],
        "gpu_type": (dispatched_gpu_type or GPU_TYPE) if spec["gpu"] else None,
        "elapsed_sec": round(t_elapsed, 1),
    }
    if is_verdict_exit:
        provenance["verdict_exit"] = rc
        provenance["verdict_note"] = (
            "calibration verdict exit (no usable mid-band dose); artifact "
            "recorded, not an infra failure"
        )
    print(json.dumps(provenance, sort_keys=True), flush=True)

    # mirror analysis-committed/ and analysis/ (private, per-stage; volume is
    # already scoped to this Modal app, not shared outside it) to the
    # checkpoint volume so a resumed/repeated stage can skip cheaply and so
    # the lead can pull results without re-running.
    os.makedirs(ckpt, exist_ok=True)
    for sub in ("analysis-committed", "analysis"):
        src = os.path.join(exp_dir, sub)
        dst = os.path.join(ckpt, sub)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    with open(os.path.join(ckpt, f"provenance_{stage}.json"), "w") as fh:
        json.dump(provenance, fh, indent=2, sort_keys=True)
    vol.commit()

    if is_verdict_exit:
        return {"status": "verdict-recorded", "stage": stage,
                "returncode": rc, "elapsed_sec": round(t_elapsed, 1)}
    return {"status": "completed", "stage": stage, "elapsed_sec": round(t_elapsed, 1)}


@app.local_entrypoint()
def main(stage: str = "", dry_run: bool = False, wait: bool = False):
    if dry_run or not stage:
        print("[modal-phaseb] no --stage given (or --dry-run passed); "
              "listing registered stages and exiting without spawning "
              "anything:")
        for sid, spec in STAGES.items():
            gpu = "GPU" if spec["gpu"] else "cpu"
            blocked = " [BLOCKED on C1]" if spec.get("blocked_on_c1") else ""
            print(f"  {sid:24s} {gpu:4s} needs={spec['needs']}{blocked}")
        print("[modal-phaseb] run `modal run cloud/modal_phase_b.py::version_check` "
              "for a cost-free image/version dry-run, or pass --stage <id> "
              "with EHR_LAUNCH_OK set to actually launch a stage.")
        return

    if stage not in STAGES:
        raise SystemExit(f"[modal-phaseb] unknown --stage {stage!r}; valid: "
                          f"{sorted(STAGES)}")

    launch_ok = os.environ.get("EHR_LAUNCH_OK")
    if launch_ok != EXPERIMENT_SLUG:
        raise SystemExit(
            "[modal-phaseb] refusing to launch: set "
            f"EHR_LAUNCH_OK={EXPERIMENT_SLUG!r} in the environment (relayed "
            f"lead approval), got EHR_LAUNCH_OK={launch_ok!r}.")

    spec = STAGES[stage]
    if spec.get("blocked_on_c1"):
        raise SystemExit(
            f"[modal-phaseb] refusing to launch {stage!r}: gated on the "
            "G0-C1 precondition control, which has no producer script yet "
            "(cloud/PHASE_B_MODAL_PLAN.md 'Gap 1'). This is a lead call, "
            "not a flag to override.")

    print(f"[modal-phaseb] launching stage={stage} gpu={spec['gpu']} "
          f"on {GPU_TYPE if spec['gpu'] else 'CPU (in pinned image)'}")
    print(f"[modal-phaseb] repo@{REPO_COMMIT[:12]} tuner@{TUNER_COMMIT[:12]} "
          f"transformers=={TRANSFORMERS_VERSION}")
    call = run_stage.spawn(stage, dispatched_gpu_type=GPU_TYPE)
    print(f"[modal-phaseb] spawned function call {call.object_id}")

    if not wait:
        # DANGEROUS without --detach: `run_stage.spawn()` returns immediately,
        # so a plain `modal run` (no --detach) tears down this ephemeral App
        # the moment `main()` returns below -- killing the just-spawned call
        # before it does anything. Confirmed directly: the first tranche-1
        # dispatch (2026-07-30, cloud/run_tranche1.sh without --detach or
        # --wait) "completed" all 18 stages in 26 seconds, `modal app list`
        # showed every one of those apps stopped with Tasks: 0, and the
        # volume had no stage output beyond private-inputs/ -- nothing had
        # actually run. Always pass --detach (survive a dropped client) AND
        # --wait (block here so ordering/failure is enforced) together for a
        # real dispatch; this fire-and-forget path is for interactive,
        # single-stage use only, monitored by hand afterward.
        print("[modal-phaseb] --wait not set; client exiting WITHOUT waiting "
              "for the stage to finish. Pass --detach --wait for a real "
              "dispatch (required for a sequential chain -- see "
              "cloud/run_tranche1.sh). Monitor: modal app logs / volume ckpt "
              "provenance file.")
        return

    import json

    print(f"[modal-phaseb] --wait set; blocking on {call.object_id} ...")
    try:
        result = call.get()
    except Exception as e:  # noqa: BLE001 -- deliberately broad: any remote
        # failure (gate raise, crashed stage, timeout) must halt a sequential
        # dispatch, not just ones of a particular exception type.
        print(f"[modal-phaseb] stage {stage!r} FAILED: {e}", flush=True)
        raise SystemExit(1)
    print(f"[modal-phaseb] stage {stage!r} result: "
          f"{json.dumps(result, sort_keys=True)}")
    if result.get("status") == "verdict-recorded":
        # A registered calibration verdict (calibrate_dose.py exiting 1 for
        # "no usable mid-band dose") is DATA, not an infra failure -- the
        # dispatch itself succeeded (artifact written, ckpt mirrored). Exit 0
        # (fall through without raising SystemExit) so a sequential caller
        # (run_tranche1.sh) does not halt the chain on it; the greppable
        # marker line below lets that caller detect the verdict and skip
        # downstream stages that depend on a usable dose.
        print(f"[modal-phaseb] VERDICT-RECORDED stage={stage} "
              f"exit={result.get('returncode')}", flush=True)
