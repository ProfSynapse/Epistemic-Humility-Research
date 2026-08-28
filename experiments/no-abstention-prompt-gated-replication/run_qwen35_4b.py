#!/usr/bin/env python3
"""qwen3.5-4b arm: no-abstention-prompt gated replication.

Reuses, unmodified, via direct import (no edits to any parent file):
  - experiments/qwen35-4b-midband-heldout/steer_lib.py (load_model,
    build_hook_and_controller, run_rows / run_batch_fixed -- the BATCHED
    driver the parent's own with-prompt measurement used; batching is an
    engine-equivalent efficiency choice, not a new generation contract:
    each row's greedy decode is independent under left-padded attention
    masking, same InterventionHook/erase_write law).
  - experiments/qwen35-4b-midband-heldout/gen_lib.py (grade_row/
    grade_clean_tighten/resolve_eos_ids/MAX_NEW_CAP).
  - experiments/qwen35-4b-midband-heldout/pipeline.py's
    `combine_active_and_baseline` (only the fired subset is run through the
    dosed pass; the rest of the arm's population reuses the shared baseline
    pass -- reused verbatim, not reimplemented).
  - experiments/j-space-cross-family-layer-contrast/gate_fit.py
    (youden_tau, roc_auc) for the FIT-split threshold refit (mu_d/sigma_d
    frozen from the pinned build_manifest; only tau is refit on fresh
    no-abstention-prompt extraction, matching capture_anchors.gate_decision's
    identical frozen-mu/sigma, refit-tau construction).
  - THIS cell's own pinned render.py (no-abstention prompt, all families).

RENDER OVERRIDE MECHANISM: `steer_lib.py` does `import render as render_mod`
at its own module-import time, resolving whatever module is registered
under the plain name "render" in `sys.modules`. This script imports THIS
cell's render.py under that exact name FIRST (before importing steer_lib),
so steer_lib's `render_prompt()` calls resolve to the no-abstention render,
not qwen35-4b-midband-heldout's own with-prompt render.py -- the identical
"swap the render, keep the engine" substitution AMENDMENT.md's Design
section requires, done via sys.modules caching rather than editing any
parent file.

Row sources (frozen, parity-locked, per cell.yaml heldout_pool):
  FIT:      experiments/qwen35-4b-midband-doubt-snap/analysis/fit_rows_for_anchor.jsonl
  HELD_OUT: experiments/qwen35-4b-midband-heldout/analysis/heldout_rows_for_steer.jsonl

Arms: no_op (baseline pass, mode "off", every row), gated (c_hat write on
fired rows only, combined with baseline on non-fired rows). No
random_direction arm for qwen3.5-4b (AMENDMENT.md "Arms": qwen3-4b and
llama only).
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
FAMILY = "qwen3.5-4b"
ANALYSIS = HERE / "analysis" / FAMILY
ANALYSIS.mkdir(parents=True, exist_ok=True)
RUNLOG_DIR = ANALYSIS / "runlog"
RUNLOG_DIR.mkdir(parents=True, exist_ok=True)

CELL = yaml.safe_load((HERE / "cell.yaml").read_text())
FAM = CELL["families"][FAMILY]

# Pinned revision: not carried in cell.yaml's family block (only "model" is),
# but identical across every pinned artifact's own provenance block for this
# family (c_hat.json/u_d.json "provenance.revision", steer_lib.MODEL_REVISION) --
# sourced from those pinned artifacts, not from memory.
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"

# Import THIS cell's render.py under the plain name "render" BEFORE steer_lib,
# so steer_lib's internal `import render as render_mod` resolves to ours
# (sys.modules caching -- see module docstring).
sys.path.insert(0, str(HERE))
os.environ["DOUBT_SNAP_RENDER_MODEL"] = FAM["model"]
os.environ["DOUBT_SNAP_RENDER_REVISION"] = MODEL_REVISION
import render as cell_render  # noqa: E402
sys.modules.setdefault("render", cell_render)

HELDOUT_DIR = REPO_ROOT / "experiments" / "qwen35-4b-midband-heldout"
DOUBT_SNAP_DIR = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap"
CROSS_DIR = REPO_ROOT / "experiments" / "j-space-cross-family-layer-contrast"
sys.path.insert(0, str(HELDOUT_DIR))
import steer_lib  # noqa: E402  (its `import render as render_mod` now resolves to ours)
import gen_lib  # noqa: E402  (qwen35-4b-midband-heldout's own; grade_row/resolve_eos_ids/MAX_NEW_CAP)
sys.path.insert(0, str(CROSS_DIR))
import gate_fit  # noqa: E402  (reuse youden_tau/roc_auc only)

TUNER_DIR = REPO_ROOT / "synaptic-tuner"
sys.path.insert(0, str(TUNER_DIR))
from shared.utilities.run_log import RunLog  # noqa: E402

assert steer_lib.render_mod is cell_render, "render override failed: steer_lib is not using this cell's render.py"

FIT_ROWS_PATH = DOUBT_SNAP_DIR / "analysis" / "fit_rows_for_anchor.jsonl"
HELDOUT_ROWS_PATH = HELDOUT_DIR / "analysis" / "heldout_rows_for_steer.jsonl"

DOSE_ABS = float(FAM["dose_abs"])
BUILD_MANIFEST = json.loads((REPO_ROOT / FAM["build_manifest"]["path"]).read_text())
BUILD_LAYER = BUILD_MANIFEST["layers"][FAM["site"]]
MU_D, SIGMA_D = BUILD_LAYER["mu_d"], BUILD_LAYER["sigma_d"]

EXTRACT_MANIFEST_PATH = ANALYSIS / "extract_manifest.json"
REFIT_PATH = ANALYSIS / "refit.json"
MAX_NEW = gen_lib.MAX_NEW_CAP
BATCH_SIZE = 8


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_direction_vector(rel_path: str) -> tuple[np.ndarray, float, int]:
    data = json.loads((REPO_ROOT / rel_path).read_text())
    return np.asarray(data["vector"], dtype=np.float64), float(data.get("sigma", 1.0)), int(data["layer"])


def fit_rows() -> list[dict]:
    rows = load_jsonl(FIT_ROWS_PATH)
    return [r for r in rows if r["role"] in ("confab", "known_correct_answered") and r["split"] == "fit"]


def held_out_rows() -> list[dict]:
    return load_jsonl(HELDOUT_ROWS_PATH)


def cmd_extract() -> int:
    rows = fit_rows() + held_out_rows()
    print(f"[extract] {len(rows)} rows")
    model, tokenizer, device = steer_lib.load_model(FAM["model"], MODEL_REVISION)
    u_d, _sig, hs_layer_idx = load_direction_vector(FAM["detector_direction"]["path"])
    hs_index = int(FAM["site"].replace("hs", ""))

    run_log = RunLog(
        RUNLOG_DIR / "extract.jsonl",
        run_config={"family": FAMILY, "stage": "extract", "model": FAM["model"], "site": FAM["site"],
                    "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT},
        key_field="row_key",
    )
    pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
    print(f"[extract] {len(pending)} pending ({len(rows) - len(pending)} done)")
    t0 = time.time()
    for i, row in enumerate(pending):
        prompt = cell_render.render(row)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        vec = out.hidden_states[hs_index][0, prompt_len - 1, :].float().cpu().numpy().tolist()
        run_log.record(row["row_key"], {"role": row["role"], "split": row.get("split", "held_out"), "vector": vec})
        if (i + 1) % 100 == 0 or (i + 1) == len(pending):
            print(f"[extract] {i + 1}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    run_log.finalize({"n_rows": len(rows)})
    run_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()

    all_records = load_jsonl(RUNLOG_DIR / "extract.jsonl")
    by_key = {r["row_key"]: r for r in all_records}
    missing = [r["row_key"] for r in rows if r["row_key"] not in by_key]
    if missing:
        print(f"[extract] FAILED: {len(missing)} missing: {missing[:5]}")
        return 1
    np.savez_compressed(ANALYSIS / "extract_vectors.npz",
                         **{_sanitize_key(k): np.asarray(v["vector"], dtype=np.float64) for k, v in by_key.items()})
    EXTRACT_MANIFEST_PATH.write_text(json.dumps({
        "n_rows": len(rows), "hs_index": hs_index, "model": FAM["model"],
        "rows": [{"row_key": k, "role": v["role"], "split": v["split"]} for k, v in by_key.items()],
    }, indent=2))
    print(f"[extract] DONE: {len(by_key)} vectors")
    return 0


def _load_vectors() -> dict[str, np.ndarray]:
    npz = np.load(ANALYSIS / "extract_vectors.npz")
    return {k: npz[k] for k in npz.files}


def cmd_refit() -> int:
    manifest = json.loads(EXTRACT_MANIFEST_PATH.read_text())
    vecs = _load_vectors()
    role_by_key = {r["row_key"]: r["role"] for r in manifest["rows"]}
    split_by_key = {r["row_key"]: r["split"] for r in manifest["rows"]}
    u_d, _sig, _layer = load_direction_vector(FAM["detector_direction"]["path"])

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
        "family": FAMILY, "n_confab_fit": len(confab_fit), "n_known_fit": len(known_fit),
        "mu_d_frozen": MU_D, "sigma_d_frozen": SIGMA_D,
        "auc_neg_z_d_on_fit_fresh_extraction": auc, "tau_frozen_refit": tau, "youden_stats": stats,
    }
    REFIT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def _fire_decisions(rows: list[dict]) -> dict[str, bool]:
    refit = json.loads(REFIT_PATH.read_text())
    tau = refit["tau_frozen_refit"]
    vecs = _load_vectors()
    u_d, _sig, _layer = load_direction_vector(FAM["detector_direction"]["path"])
    fire = {}
    for row in rows:
        h = vecs[_sanitize_key(row["row_key"])]
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - MU_D) / SIGMA_D, -2.0, 2.0))
        fire[row["row_key"]] = bool(-z_d >= tau)
    return fire


def combine_active_and_baseline(all_rows: list[dict], active_by_key: dict, baseline_by_key: dict) -> dict:
    return {r["row_key"]: (active_by_key.get(r["row_key"]) or baseline_by_key[r["row_key"]]) for r in all_rows}


def cmd_generate(arm: str) -> int:
    assert arm in ("no_op", "gated")
    rows = held_out_rows()
    print(f"[generate:{arm}] {len(rows)} held-out rows")

    fire = _fire_decisions(rows) if arm != "no_op" else {r["row_key"]: False for r in rows}
    fired_rows = [r for r in rows if fire[r["row_key"]]]
    print(f"[generate:{arm}] n_fire={len(fired_rows)}/{len(rows)}")

    model, tokenizer, device = steer_lib.load_model(FAM["model"], MODEL_REVISION)

    baseline_log = RunLog(
        RUNLOG_DIR / "baseline.jsonl",
        run_config={"family": FAMILY, "stage": "generate", "arm": "no_op", "model": FAM["model"],
                    "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT},
        key_field="row_key",
    )
    print(f"[generate:{arm}] running/reusing shared baseline pass ({len(rows)} rows)")
    steer_lib.run_rows(model, tokenizer, device, None, "off", rows, 0.0, MAX_NEW, BATCH_SIZE, baseline_log)
    baseline_log.finalize({"n_rows": len(rows)})
    baseline_log.close()

    if arm == "gated":
        from MechInterp.intervention import get_decoder_layer
        c_hat, sigma_c, layer_idx = load_direction_vector(FAM["write_direction"]["path"])
        gain = DOSE_ABS / sigma_c
        hook, controller = steer_lib.build_hook_and_controller(torch.tensor(c_hat, dtype=torch.float32), sigma_c)
        layer_module = get_decoder_layer(model, layer_idx)
        h_ctrl = layer_module.register_forward_hook(controller)
        gated_log = RunLog(
            RUNLOG_DIR / "gated.jsonl",
            run_config={"family": FAMILY, "stage": "generate", "arm": "gated", "model": FAM["model"],
                        "dose_abs": DOSE_ABS, "prompt": cell_render.NO_ABSTENTION_SYSTEM_PROMPT},
            key_field="row_key",
        )
        try:
            print(f"[generate:gated] {len(fired_rows)} fired rows through dosed pass")
            steer_lib.run_rows(model, tokenizer, device, controller, "gen_stream", fired_rows, gain, MAX_NEW, BATCH_SIZE, gated_log)
        finally:
            h_ctrl.remove()
            controller.reset()
        gated_log.finalize({"n_rows": len(fired_rows), "gain": gain})
        gated_log.close()

    del model
    gc.collect()
    torch.cuda.empty_cache()
    print(f"[generate:{arm}] DONE")
    return 0


def cmd_grade() -> int:
    """Two readouts, per the task's grading scope (strict string rule +
    detector_v2 only; the LLM judge / apply_adjudication stage is explicitly
    out of scope for this run): `gate_lib.rate_summary` (this family's own
    reusable Wilson-CI machinery over refused/well_formed/clean_tighten,
    ALREADY embedded per-row by steer_lib.run_rows -> gen_lib.grade_row) plus
    a supplementary detector_v2_refused Wilson computation. This calls only
    `gate_lib.rate_summary`/`rate_wilson` (pure Wilson-CI arithmetic, not the
    parent's own g1_*/g3*_pass threshold functions -- this cell has its own
    distinct gates.yaml and must not be scored against the parent's
    thresholds)."""
    calib_dir = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"
    sys.path.insert(0, str(calib_dir))

    # This script imported qwen35-4b-midband-heldout/gen_lib.py above, which
    # itself does an unqualified `import grader` at module-import time,
    # caching that family's grader.py in sys.modules under "grader".
    # detector_v2.py does its OWN unqualified `import grader`, expecting ITS
    # sibling (abstention-wide-instrument-calibration/grader.py, which
    # defines _is_stated_confidence_refusal) -- without this swap it would
    # silently resolve to the already-cached wrong module and crash with
    # AttributeError. Load the correct sibling explicitly, install it into
    # sys.modules only for detector_v2's own import, then restore. See
    # run_qwen3_4b.py's identical helper for the full rationale;
    # detector_v2.py itself is not edited (pinned instrument).
    import importlib.util

    calib_grader_path = calib_dir / "grader.py"
    spec = importlib.util.spec_from_file_location("_calib_grader_for_detector_v2", calib_grader_path)
    calib_grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calib_grader)
    if not hasattr(calib_grader, "_is_stated_confidence_refusal"):
        raise RuntimeError(
            f"loaded grader module at {calib_grader_path} lacks "
            "_is_stated_confidence_refusal; detector_v2 cannot run"
        )
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
    import gate_lib

    cfg = detector_v2.load_patterns()
    baseline_by_key = {r["row_key"]: r for r in load_jsonl(RUNLOG_DIR / "baseline.jsonl")}
    gated_path = RUNLOG_DIR / "gated.jsonl"
    gated_by_key = {r["row_key"]: r for r in load_jsonl(gated_path)} if gated_path.exists() else {}
    rows = held_out_rows()

    report = {"family": FAMILY, "arms": {}}
    for arm, active_by_key in (("no_op", {}), ("gated", gated_by_key)):
        combined = combine_active_and_baseline(rows, active_by_key, baseline_by_key)
        for rec in combined.values():
            rec["detector_v2_refused"] = detector_v2.is_refused_v2(rec.get("answer_text", ""), cfg)
        confab = [combined[r["row_key"]] for r in rows if r["role"] == "confab"]
        known = [combined[r["row_key"]] for r in rows if r["role"] == "known_correct_answered"]
        n_fired_confab = sum(1 for r in confab if r.get("row_key") in gated_by_key)
        n_fired_known = sum(1 for r in known if r.get("row_key") in gated_by_key)

        report["arms"][arm] = {
            "confab": {
                "n_fired": n_fired_confab,
                **gate_lib.rate_summary(confab),
                "detector_v2_refused": gate_lib.rate_wilson(confab, "detector_v2_refused"),
                "well_formed_correct": gate_lib.rate_wilson(confab, "well_formed_correct"),
            },
            "known_correct_answered": {
                "n_fired": n_fired_known,
                **gate_lib.rate_summary(known),
                "detector_v2_refused": gate_lib.rate_wilson(known, "detector_v2_refused"),
                "well_formed_correct": gate_lib.rate_wilson(known, "well_formed_correct"),
            },
        }
    (ANALYSIS / "grade_report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["extract", "refit", "generate", "grade", "all"])
    ap.add_argument("--arm", choices=["no_op", "gated"])
    args = ap.parse_args()

    if args.stage == "extract":
        return cmd_extract()
    if args.stage == "refit":
        return cmd_refit()
    if args.stage == "generate":
        if not args.arm:
            print("--arm required", file=sys.stderr)
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
        rc = cmd_generate("gated")  # runs the shared baseline pass too
        if rc:
            return rc
        return cmd_grade()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
