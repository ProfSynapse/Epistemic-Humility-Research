#!/usr/bin/env python3
"""qwen3-4b arm: no-abstention-prompt gated replication.

Reuses, unmodified, via direct import (no edits to any parent file):
  - experiments/j-space-midband-write-sweep-qwen3-4b/model_lib.py
    (load_model, setup_hook_from_path, setup_hook_from_vector, wilson_ci)
  - experiments/j-space-midband-write-sweep-qwen3-4b/gen_lib.py
    (run_pass_fixed, grade_clean_tighten, MAX_NEW_CAP)
  - experiments/j-space-midband-write-sweep-qwen3-4b/grader.py (grade_one)
  - experiments/j-space-midband-write-sweep-qwen3-4b/gate_fit.py (youden_tau,
    roc_auc) -- the SAME threshold-fitting method as the parent's gate_fit,
    fed FRESH extraction (this cell's no-abstention-prompt renders) instead
    of the parent's cached extraction tensors. mu_d/sigma_d are read frozen
    from the pinned build_manifest (cell.yaml), matching how the parent's own
    gate_fit.py treats them (an input it never recomputes) -- only tau is
    refit, per AMENDMENT.md "Detector".
  - THIS cell's own pinned render.py (no-abstention prompt, all families).

Anchor definition (unchanged from the parent's extract_layer_sweep_anchor.py):
  forward pass over the rendered PROMPT ALONE, output_hidden_states=True,
  use_cache=False, anchor = hidden_states[hs_index][0, prompt_len-1, :].
  Extraction uses the SAME plain-HF model instance loaded for generation
  (model_lib.load_model(), not a second unsloth-loaded copy) so the model is
  loaded exactly once per this rule's "load models once per script"
  invariant; hidden states from a deterministic eval-mode forward pass are
  identical regardless of loader.

Arms: no_op (mode "off" always), gated (c_hat write when fire),
random_direction (pinned random_direction_hs23.json write when fire, same
fire decisions as gated -- "matched-dose": strength = dose_target /
direction_record["sigma"], generalizing the parent's
strength = dose_target / build["sigma_c"] to each direction's own sigma
field, which is how model_lib.setup_hook_from_path already treats it).

Stages (resumable via RunLog for extraction+generation; refit is cheap CPU
and always recomputed from the current extraction file):
  extract   -- FIT + HELD_OUT rows, single forward pass each.
  refit     -- CPU-only threshold refit on FIT split.
  generate  -- one of {no_op, gated, random_direction}; requires refit output.
  grade     -- string-stage (clean_tighten / well_formed_correct) +
               detector_v2 abstention counts per arm.
  all       -- extract -> refit -> generate (all three arms) -> grade.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
FAMILY = "qwen3-4b"
ANALYSIS = HERE / "analysis" / FAMILY
ANALYSIS.mkdir(parents=True, exist_ok=True)
RUNLOG_DIR = ANALYSIS / "runlog"
RUNLOG_DIR.mkdir(parents=True, exist_ok=True)

CELL = yaml.safe_load((HERE / "cell.yaml").read_text())
FAM = CELL["families"][FAMILY]

WRITE_SWEEP_DIR = REPO_ROOT / "experiments" / "j-space-midband-write-sweep-qwen3-4b"
sys.path.insert(0, str(WRITE_SWEEP_DIR))
sys.path.insert(0, str(HERE))

import model_lib as ml  # noqa: E402  (write-sweep, reused unmodified)
import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import gate_fit  # noqa: E402  (reuse youden_tau/roc_auc only)

os.environ["DOUBT_SNAP_RENDER_MODEL"] = FAM["model"]
import render as cell_render  # noqa: E402  (THIS cell's pinned render)

TUNER_DIR = REPO_ROOT / "synaptic-tuner"
sys.path.insert(0, str(TUNER_DIR))
from shared.utilities.run_log import RunLog  # noqa: E402

ROWS_WITH_TEXT = WRITE_SWEEP_DIR / "analysis" / "rows_with_text.jsonl"
HS_INDEX = int(FAM["site"].replace("hs", ""))
SETPOINT_ABS = float(FAM["setpoint_abs"])
BUILD_MANIFEST = json.loads((REPO_ROOT / FAM["build_manifest"]["path"]).read_text())
BUILD_LAYER = BUILD_MANIFEST["layers"][FAM["site"]]
MU_D, SIGMA_D = BUILD_LAYER["mu_d"], BUILD_LAYER["sigma_d"]

EXTRACT_PATH = ANALYSIS / "extract.safetensors"
EXTRACT_MANIFEST_PATH = ANALYSIS / "extract_manifest.json"
REFIT_PATH = ANALYSIS / "refit.json"


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def load_direction_vector(rel_path: str) -> np.ndarray:
    data = json.loads((REPO_ROOT / rel_path).read_text())
    return np.asarray(data["vector"], dtype=np.float64)


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def all_rows() -> list[dict]:
    rows = load_jsonl(ROWS_WITH_TEXT)
    return [r for r in rows if r["role"] in ("confab", "known_correct_answered")]


def rows_for(split: str) -> list[dict]:
    return [r for r in all_rows() if r["split"] == split]


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------

def cmd_extract() -> int:
    rows = all_rows()
    print(f"[extract] {len(rows)} rows (fit+held_out, confab+known_correct_answered)")

    model, tokenizer = ml.load_model()
    device = next(model.parameters()).device

    run_log = RunLog(
        RUNLOG_DIR / "extract.jsonl",
        run_config={
            "family": FAMILY, "stage": "extract", "model": FAM["model"],
            "site": FAM["site"], "render_sha256": CELL["render"]["parent_render"]["sha256"],
            "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT,
        },
        key_field="row_key",
    )
    pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
    print(f"[extract] {len(pending)} pending (resuming {len(rows) - len(pending)} already done)")
    t0 = time.time()
    for i, row in enumerate(pending):
        prompt = cell_render.render(row)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        vec = out.hidden_states[HS_INDEX][0, prompt_len - 1, :].float().cpu().numpy().tolist()
        run_log.record(row["row_key"], {
            "role": row["role"], "split": row["split"], "vector": vec, "prompt_len": prompt_len,
        })
        if (i + 1) % 50 == 0 or (i + 1) == len(pending):
            print(f"[extract] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    run_log.finalize({"n_rows": len(rows)})
    run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()

    # Materialize a flat manifest + safetensors-free npz cache for downstream stages.
    all_records = [json.loads(ln) for ln in (RUNLOG_DIR / "extract.jsonl").open() if ln.strip()]
    by_key = {r["row_key"]: r for r in all_records}
    missing = [r["row_key"] for r in rows if r["row_key"] not in by_key]
    if missing:
        print(f"[extract] FAILED: {len(missing)} rows missing from extract log: {missing[:5]}...")
        return 1
    np.savez_compressed(
        ANALYSIS / "extract_vectors.npz",
        **{_sanitize_key(k): np.asarray(v["vector"], dtype=np.float64) for k, v in by_key.items()},
    )
    EXTRACT_MANIFEST_PATH.write_text(json.dumps({
        "n_rows": len(rows), "hs_index": HS_INDEX, "model": FAM["model"],
        "rows": [{"row_key": k, "role": v["role"], "split": v["split"]} for k, v in by_key.items()],
    }, indent=2))
    print(f"[extract] DONE: {len(by_key)} vectors -> {ANALYSIS / 'extract_vectors.npz'}")
    return 0


def _load_vectors() -> dict[str, np.ndarray]:
    npz = np.load(ANALYSIS / "extract_vectors.npz")
    return {k: npz[k] for k in npz.files}


# --------------------------------------------------------------------------
# refit (CPU only)
# --------------------------------------------------------------------------

def cmd_refit() -> int:
    manifest = json.loads(EXTRACT_MANIFEST_PATH.read_text())
    vecs = _load_vectors()
    role_by_key = {r["row_key"]: r["role"] for r in manifest["rows"]}
    split_by_key = {r["row_key"]: r["split"] for r in manifest["rows"]}

    u_d = load_direction_vector(FAM["detector_direction"]["path"])

    confab_fit = [rk for rk, role in role_by_key.items() if role == "confab" and split_by_key[rk] == "fit"]
    known_fit = [rk for rk, role in role_by_key.items() if role == "known_correct_answered" and split_by_key[rk] == "fit"]

    def z_d_for(keys: list[str]) -> np.ndarray:
        h = np.stack([vecs[_sanitize_key(rk)] for rk in keys])
        proj = h @ u_d
        return np.clip((proj - MU_D) / SIGMA_D, -2.0, 2.0)

    z_d = np.concatenate([z_d_for(confab_fit), z_d_for(known_fit)])
    labels = np.concatenate([np.ones(len(confab_fit)), np.zeros(len(known_fit))]).astype(int)
    score = -z_d
    tau, stats = gate_fit.youden_tau(score, labels)
    auc = gate_fit.roc_auc(score, labels)

    report = {
        "family": FAMILY, "hs_index": HS_INDEX,
        "n_confab_fit": len(confab_fit), "n_known_fit": len(known_fit),
        "mu_d_frozen": MU_D, "sigma_d_frozen": SIGMA_D,
        "auc_neg_z_d_on_fit_fresh_extraction": auc,
        "tau_frozen_refit": tau, "youden_stats": stats,
        "method": "gate_fit.youden_tau (reused byte-identical) fed fresh no-abstention-prompt extraction; mu_d/sigma_d frozen from parent build_manifest",
    }
    REFIT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def _import_detector_v2():
    """Import the pinned abstention-wide-instrument-calibration/detector_v2.py
    without letting its internal `import grader` resolve to the WRONG grader
    module. This script already imported
    j-space-midband-write-sweep-qwen3-4b/grader.py (for grade_one, above) and
    cached it in sys.modules under the bare name "grader"; detector_v2.py
    does its own unqualified `import grader` expecting its OWN sibling
    (abstention-wide-instrument-calibration/grader.py, which defines
    _is_stated_confidence_refusal) and would otherwise silently pick up the
    already-cached wrong module. Fix: load the correct sibling explicitly,
    swap it into sys.modules under "grader" only for detector_v2's own
    import, then restore this script's original binding immediately after --
    detector_v2 keeps its own module-level reference regardless of the later
    restore. detector_v2.py itself is NOT edited (pinned instrument)."""
    import importlib.util

    calib_dir = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"
    calib_grader_path = calib_dir / "grader.py"
    spec = importlib.util.spec_from_file_location("_calib_grader_for_detector_v2", calib_grader_path)
    calib_grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calib_grader)
    if not hasattr(calib_grader, "_is_stated_confidence_refusal"):
        raise RuntimeError(
            f"loaded grader module at {calib_grader_path} lacks "
            "_is_stated_confidence_refusal; detector_v2 cannot run"
        )

    sys.path.insert(0, str(calib_dir))
    prior_grader = sys.modules.get("grader")
    sys.modules["grader"] = calib_grader
    try:
        import detector_v2
    finally:
        if prior_grader is not None:
            sys.modules["grader"] = prior_grader
        else:
            sys.modules.pop("grader", None)
    print(f"[grade] detector_v2 grader module resolved to: {calib_grader_path}", flush=True)
    return detector_v2


def _fire_decisions(held_out_rows: list[dict]) -> dict[str, bool]:
    refit = json.loads(REFIT_PATH.read_text())
    tau = refit["tau_frozen_refit"]
    vecs = _load_vectors()
    u_d = load_direction_vector(FAM["detector_direction"]["path"])
    fire = {}
    for row in held_out_rows:
        h = vecs[_sanitize_key(row["row_key"])]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - MU_D) / SIGMA_D, -2.0, 2.0))
        score = -z_d
        fire[row["row_key"]] = bool(score >= tau)
    return fire


# --------------------------------------------------------------------------
# generate
# --------------------------------------------------------------------------

def _direction_and_sigma(arm: str):
    # no_op uses the write direction too, but "off" mode never applies it
    # (matches the parent's run_layer, which always sets up ONE hook per
    # layer and calls run_pass_fixed with mode "off" or "gen_stream" on the
    # SAME controller instance -- the direction choice is inert under "off").
    if arm in ("no_op", "gated"):
        path = FAM["write_direction"]["path"]
    elif arm == "random_direction":
        path = FAM["random_direction"]["path"]
    else:
        raise ValueError(arm)
    data = json.loads((REPO_ROOT / path).read_text())
    return np.asarray(data["vector"], dtype=np.float64), float(data.get("sigma", 1.0)), int(data["layer"])


def cmd_generate(arm: str) -> int:
    assert arm in ("no_op", "gated", "random_direction")
    held_out = rows_for("held_out")
    print(f"[generate:{arm}] {len(held_out)} held-out rows")

    fire = _fire_decisions(held_out) if arm != "no_op" else {r["row_key"]: False for r in held_out}
    n_fire = sum(1 for v in fire.values() if v)
    print(f"[generate:{arm}] n_fire={n_fire}/{len(held_out)}")

    model, tokenizer = ml.load_model()
    device = next(model.parameters()).device

    # A controller/hook is always registered (matches the parent's run_layer:
    # one hook per layer, reused for both the always-run "off" pass and the
    # conditional "gen_stream" pass); no_op's direction is inert since it is
    # only ever invoked in "off" mode.
    vector, sigma, layer_idx = _direction_and_sigma(arm)
    strength = SETPOINT_ABS / sigma
    from MechInterp.intervention import get_decoder_layer
    _hook, controller, layer_idx2, _sigma2 = ml.setup_hook_from_vector(vector, sigma, layer_idx)
    layer_module = get_decoder_layer(model, layer_idx2)
    h_ctrl = layer_module.register_forward_hook(controller)

    run_log = RunLog(
        RUNLOG_DIR / f"{arm}.jsonl",
        run_config={
            "family": FAMILY, "stage": "generate", "arm": arm, "model": FAM["model"],
            "site": FAM["site"], "setpoint_abs": SETPOINT_ABS,
            "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT,
        },
        key_field="row_key",
        required_fields=("out_text",),
    )
    pending = list(run_log.iter_pending(held_out, key_fn=lambda r: r["row_key"]))
    print(f"[generate:{arm}] {len(pending)} pending (resuming {len(held_out) - len(pending)} already done)")

    try:
        t0 = time.time()
        for i, row in enumerate(pending):
            prompt = cell_render.render(row)
            enc = tokenizer(prompt, return_tensors="pt").to(device)
            row_fire = fire[row["row_key"]]

            base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
                model, controller, enc, "off", 0.0, tokenizer, max_new=gl.MAX_NEW_CAP
            )
            base_text = tokenizer.decode(base_new, skip_special_tokens=True)

            if arm != "no_op" and row_fire:
                dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
                    model, controller, enc, "gen_stream", strength, tokenizer, max_new=gl.MAX_NEW_CAP
                )
                out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
                n_new = int(dosed_new.shape[0])
            else:
                out_text = base_text
                readback = None
                terminated_naturally = base_terminated
                n_new = int(base_new.shape[0])

            if not out_text:
                out_text = " "  # RunLog required_fields needs a non-empty string; empty generation recorded via well_formed=False downstream

            run_log.record(row["row_key"], {
                "role": row["role"], "fire": row_fire, "out_text": out_text,
                "readback_measured": readback, "n_new_tokens": n_new,
                "terminated_naturally": terminated_naturally,
                "aliases": row.get("aliases", []),
            })
            if (i + 1) % 25 == 0 or (i + 1) == len(pending):
                print(f"[generate:{arm}] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        if h_ctrl is not None:
            h_ctrl.remove()
        if controller is not None:
            controller.reset()
        run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()
    print(f"[generate:{arm}] DONE")
    return 0


# --------------------------------------------------------------------------
# grade (string stage + detector_v2), CPU only
# --------------------------------------------------------------------------

def cmd_grade() -> int:
    detector_v2 = _import_detector_v2()

    cfg = detector_v2.load_patterns()
    report = {"family": FAMILY, "arms": {}}
    for arm in ("no_op", "gated", "random_direction"):
        log_path = RUNLOG_DIR / f"{arm}.jsonl"
        if not log_path.exists():
            continue
        records = [json.loads(ln) for ln in log_path.open() if ln.strip()]
        confab = [r for r in records if r["role"] == "confab"]
        known = [r for r in records if r["role"] == "known_correct_answered"]

        def grade_pop(pop: list[dict], metric_key: str) -> dict:
            n = len(pop)
            gradings = []
            for r in pop:
                ct = gl.grade_clean_tighten(r["out_text"], r["terminated_naturally"])
                og = grader.grade_one(r["out_text"], r.get("aliases"))
                v2_refused = detector_v2.is_refused_v2(r["out_text"], cfg)
                gradings.append({"clean_tighten": ct["clean_tighten"], "well_formed_correct": og["well_formed_correct"], "detector_v2_refused": v2_refused, "degenerate": og["degenerate"]})
            successes_string = sum(1 for g in gradings if g[metric_key])
            successes_v2 = sum(1 for g in gradings if g["detector_v2_refused"])
            rate_s, lo_s, hi_s = ml.wilson_ci(successes_string, n) if n else (0, 0, 0)
            rate_v2, lo_v2, hi_v2 = ml.wilson_ci(successes_v2, n) if n else (0, 0, 0)
            n_fired = sum(1 for r in pop if r.get("fire"))
            return {
                "n": n, "n_fired": n_fired,
                "string_stage": {"successes": successes_string, "rate": rate_s, "wilson_ci_95": [lo_s, hi_s]},
                "detector_v2": {"successes": successes_v2, "rate": rate_v2, "wilson_ci_95": [lo_v2, hi_v2]},
            }

        report["arms"][arm] = {
            "confab_abstention": grade_pop(confab, "clean_tighten"),
            "known_correct_false_refusal": grade_pop(known, "detector_v2_refused"),
            "known_correct_well_formed_correct": grade_pop(known, "well_formed_correct"),
        }
    out_path = ANALYSIS / "grade_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["extract", "refit", "generate", "grade", "all"])
    ap.add_argument("--arm", choices=["no_op", "gated", "random_direction"])
    args = ap.parse_args()

    if args.stage == "extract":
        return cmd_extract()
    if args.stage == "refit":
        return cmd_refit()
    if args.stage == "generate":
        if not args.arm:
            print("--arm required for generate", file=sys.stderr)
            return 2
        return cmd_generate(args.arm)
    if args.stage == "grade":
        return cmd_grade()
    if args.stage == "all":
        rc = cmd_extract()
        if rc:
            return rc
        rc = cmd_refit()
        if rc:
            return rc
        for arm in ("no_op", "gated", "random_direction"):
            rc = cmd_generate(arm)
            if rc:
                return rc
        return cmd_grade()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
