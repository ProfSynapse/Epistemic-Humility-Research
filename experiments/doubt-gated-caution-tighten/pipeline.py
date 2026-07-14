#!/usr/bin/env python3
"""Doubt-gated caution snap -- END-TO-END gated pipeline (local 3090).

Implements AMENDMENT.md's Instrument verbatim:
  (1) GATE: fire iff neg_z_d = -z_d clears the FROZEN tau (gate_fit.py,
      chosen on FIT, never touching HELD-OUT).
  (2) SNAP: on a fired row, erase-and-write along c_hat to a FIXED realized
      projection s* = DOSE_TARGET (default 200), scope anchor_onward,
      persistent through decode. Non-fired rows are left unperturbed.
  (3) GENERATION: gen_lib.run_pass_fixed -- EOS-enabled, enable_thinking=False
      (baked into the render function), greedy, max_new capped at 200.

Every reported gate number is computed on the HELD-OUT split via THIS
end-to-end pipeline (the gate decides who gets dosed row-by-row) -- never a
post-hoc multiplication of two separately-measured rates.

Populations (HELD-OUT only, per split_manifest.json):
  confab_tighten          -- G1 numerator population.
  known_correct_cost_control -- G2 numerator population.

Arms:
  gated            -- the real instrument (doubt gate -> c_hat snap).
  random_direction -- G3(i) placebo: SAME fired rows, write along a random
                      unit direction (matched realized-projection magnitude)
                      instead of c_hat.
  permuted_gate    -- G3(ii) placebo: dose the SAME TOTAL COUNT of rows
                      (across the combined confab_held + known_held pool),
                      chosen uniformly at random rather than doubt-flagged,
                      with the SAME c_hat snap.

--mode smoke runs a tiny (default 8-row) end-to-end pass proving the wiring
and G0 (write fires, realized projection lands near the dose target, no
off-target movement, generation terminates) -- NOT a gate-worthy sample.
--mode full runs the real held-out sweep and computes G1/G2 Wilson CIs plus
both G3 placebo arms; this is the CONFIRMATORY run and is not launched by
this build task.
"""

from __future__ import annotations

import argparse
import gc
import json
import random as pyrandom
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

sys.path.insert(0, str(HERE))
import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402

EXTRACT_TENSORS = ANALYSIS / "l34_anchor_extract.safetensors"
EXTRACT_MANIFEST = ANALYSIS / "l34_anchor_extract_manifest.json"
ROWS_WITH_TEXT = ANALYSIS / "rows_with_text.jsonl"
U_D_PATH = COMMITTED / "u_d_L34.json"
C_HAT_PATH = COMMITTED / "c_hat_L34.json"
RANDOM_DIR_PATH = COMMITTED / "random_direction_L34.json"
BUILD_MANIFEST_PATH = COMMITTED / "build_manifest.json"
GATE_FIT_PATH = COMMITTED / "gate_fit.json"

DOSE_TARGET_DEFAULT = 200.0
MAX_NEW = gl.MAX_NEW_CAP
PERMUTED_GATE_SEED = 20260707


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def load_direction_vector(p: Path) -> np.ndarray:
    d = json.loads(p.read_text())
    return np.asarray(d["vector"], dtype=np.float64)


# ---------------------------------------------------------------------------
# Gate: compute z_d / score / fire for every row in a role+split subset.
# ---------------------------------------------------------------------------

def compute_gate_decisions(rows: list[dict]) -> list[dict]:
    """rows: list of {"row_key", "role", "split", "category_canon",
    "question", "aliases"} from rows_with_text.jsonl. Returns the same rows
    augmented with z_d, score (neg_z_d), fire (bool)."""
    tensors_raw = __import__("safetensors.numpy", fromlist=["load_file"]).load_file(str(EXTRACT_TENSORS))
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors_raw.items()}
    u_d = load_direction_vector(U_D_PATH)
    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    mu_d, sigma_d = build_manifest["mu_d"], build_manifest["sigma_d"]
    tau = json.loads(GATE_FIT_PATH.read_text())["tau_frozen"]

    out = []
    for r in rows:
        H = fresh[_sanitize_key(r["row_key"])]
        proj_d = float(H @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        score = -z_d
        fire = bool(score >= tau)
        rec = dict(r)
        rec.update({"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": score, "fire": fire, "tau": tau})
        out.append(rec)
    return out


def load_rows(role: str, split: str) -> list[dict]:
    rows = load_jsonl(ROWS_WITH_TEXT)
    return [r for r in rows if r["role"] == role and r["split"] == split]


def stratified_subset(rows: list[dict], n: int) -> list[dict]:
    """Deterministic stratified-by-category_canon subset (same convention as
    the sibling two-signal diagnostic's own loaders)."""
    by_cat: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in sorted(rows, key=lambda r: r["row_key"]):
        cat = r.get("category_canon")
        if cat not in by_cat:
            by_cat[cat] = []
            order.append(cat)
        by_cat[cat].append(r)
    out: list[dict] = []
    idx = 0
    while len(out) < n:
        added = False
        for cat in order:
            if idx < len(by_cat[cat]):
                out.append(by_cat[cat][idx])
                added = True
                if len(out) >= n:
                    break
        if not added:
            break
        idx += 1
    return out[:n]


# ---------------------------------------------------------------------------
# Generation for one row under a given arm decision.
# ---------------------------------------------------------------------------

def run_one_row(
    model, controller, tokenizer, dev, row: dict, dose_row: bool,
    strength_if_dosed: float, role: str,
) -> dict:
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, max_new=MAX_NEW
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    if dose_row:
        dosed_out, readback, terminated_naturally, dosed_new = gl.run_pass_fixed(
            model, controller, enc, "gen_stream", strength_if_dosed, tokenizer, max_new=MAX_NEW
        )
        out_text = tokenizer.decode(dosed_new, skip_special_tokens=True)
        n_new = int(dosed_new.shape[0])
    else:
        out_text = base_text
        readback = None
        terminated_naturally = base_terminated
        n_new = int(base_new.shape[0])

    ct = gl.grade_clean_tighten(out_text, terminated_naturally)
    old_grade = grader.grade_one(out_text, row.get("aliases"))

    return {
        "row_key": row["row_key"], "role": role, "category_canon": row.get("category_canon"),
        "dosed": dose_row, "readback_measured": readback, "n_new_tokens": n_new,
        "terminated_naturally": terminated_naturally,
        "baseline_text": base_text, "out_text": out_text,
        "clean_tighten": ct["clean_tighten"], "semantic_refuse": ct["semantic_refuse"],
        "well_formed_correct": old_grade["well_formed_correct"],
        "not_well_formed_correct": not old_grade["well_formed_correct"],
        "grade": ct, "old_grade": old_grade,
    }


# ---------------------------------------------------------------------------
# G0 smoke.
# ---------------------------------------------------------------------------

def run_smoke(n_rows: int, dose_target: float) -> dict:
    confab_held = compute_gate_decisions(load_rows("confab", "held_out"))
    known_held = compute_gate_decisions(load_rows("known_correct_answered", "held_out"))

    n_confab = n_rows // 2
    n_known = n_rows - n_confab
    confab_sub = stratified_subset(confab_held, n_confab)
    known_sub = stratified_subset(known_held, n_known)
    rows = confab_sub + known_sub
    print(f"[smoke] n_rows={len(rows)} (confab={len(confab_sub)}, known_correct_answered={len(known_sub)}); "
          f"fires: confab={sum(r['fire'] for r in confab_sub)}/{len(confab_sub)}, "
          f"known={sum(r['fire'] for r in known_sub)}/{len(known_sub)}")

    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c

    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    recs = []
    out_path = ANALYSIS / "smoke_rows.jsonl"
    try:
        with out_path.open("w") as out_f:
            for r in rows:
                rec = run_one_row(model, controller, tokenizer, dev, r, r["fire"],
                                  strength_c_hat, r["role"])
                rec["fire"] = r["fire"]
                rec["score_neg_z_d"] = r["score_neg_z_d"]
                rec["tau"] = r["tau"]
                out_f.write(json.dumps(rec) + "\n")
                out_f.flush()
                recs.append(rec)
                print(f"[smoke] {rec['row_key']} role={rec['role']} fire={rec['fire']} "
                      f"readback={rec['readback_measured']} terminated={rec['terminated_naturally']} "
                      f"clean_tighten={rec['clean_tighten']} well_formed_correct={rec['well_formed_correct']}")
    finally:
        h_ctrl.remove()
        del model
        gc.collect()
        torch.cuda.empty_cache()

    dosed = [r for r in recs if r["dosed"]]
    readbacks = [r["readback_measured"] for r in dosed if r["readback_measured"] is not None]
    within_tol = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    n_collapse = sum(1 for r in dosed if r["grade"]["degenerate"])

    g0 = {
        "n_rows": len(recs), "n_dosed": len(dosed),
        "write_fires": len(dosed) > 0,
        "readback_mean": (sum(readbacks) / len(readbacks)) if readbacks else None,
        "readback_min": min(readbacks) if readbacks else None,
        "readback_max": max(readbacks) if readbacks else None,
        "n_within_5pct_tol_of_dose_target": sum(within_tol),
        "n_dosed_total": len(dosed),
        "frac_within_tol": (sum(within_tol) / len(within_tol)) if within_tol else None,
        "collapse_rate_on_dosed": (n_collapse / len(dosed)) if dosed else None,
        "gen_stream_fired": len(dosed) > 0 and all(rb is not None for rb in readbacks),
        "baseline_well_formed_rate_on_undosed": (
            sum(1 for r in recs if not r["dosed"] and not r["grade"]["degenerate"])
            / max(1, sum(1 for r in recs if not r["dosed"]))
        ),
    }
    summary = {"dose_target": dose_target, "sigma_c": sigma_c, "strength_gain": strength_c_hat,
              "g0": g0, "rows_path": str(out_path)}
    (ANALYSIS / "smoke_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SMOKE / G0 SUMMARY ===")
    print(json.dumps(summary, indent=2))
    return summary


# ---------------------------------------------------------------------------
# Full held-out sweep (NOT run by this build task -- confirmatory, gated by
# the lead's launch approval). Included so the harness is complete and the
# lead can launch it later without further engineering.
# ---------------------------------------------------------------------------

def _grade_population(recs: list[dict], metric: str) -> dict:
    n = len(recs)
    successes = sum(1 for r in recs if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def run_full(dose_target: float, placebo_seed: int = PERMUTED_GATE_SEED) -> dict:
    confab_held = compute_gate_decisions(load_rows("confab", "held_out"))
    known_held = compute_gate_decisions(load_rows("known_correct_answered", "held_out"))

    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c
    # random-direction placebo: sigma=1.0 in random_direction_L34.json, so
    # strength == realized setpoint exactly -- matched norm to dose_target.
    strength_random_dir = dose_target

    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    results: dict = {}
    try:
        # -- gated arm (the real instrument) --------------------------------
        confab_recs = [run_one_row(model, controller, tokenizer, dev, r, r["fire"],
                                   strength_c_hat, "confab") for r in confab_held]
        known_recs = [run_one_row(model, controller, tokenizer, dev, r, r["fire"],
                                  strength_c_hat, "known_correct_answered") for r in known_held]
        results["gated"] = {
            "confab_tighten": _grade_population(confab_recs, "clean_tighten"),
            "known_correct_cost_control": _grade_population(known_recs, "not_well_formed_correct"),
        }

        n_fired = sum(1 for r in confab_held if r["fire"]) + sum(1 for r in known_held if r["fire"])

        # -- G3(i) random-direction placebo: SAME fired rows, garbage direction --
        h_ctrl.remove()
        hook_rd, controller_rd, layer_idx_rd, _sigma_rd, _rec_rd = ml.setup_hook_from_path(RANDOM_DIR_PATH)
        layer_module_rd = get_decoder_layer(model, layer_idx_rd)
        h_ctrl = layer_module_rd.register_forward_hook(controller_rd)
        confab_rd = [run_one_row(model, controller_rd, tokenizer, dev, r, r["fire"],
                                 strength_random_dir, "confab") for r in confab_held]
        known_rd = [run_one_row(model, controller_rd, tokenizer, dev, r, r["fire"],
                                strength_random_dir, "known_correct_answered") for r in known_held]
        results["random_direction"] = {
            "confab_tighten": _grade_population(confab_rd, "clean_tighten"),
            "known_correct_cost_control": _grade_population(known_rd, "not_well_formed_correct"),
        }
        h_ctrl.remove()

        # -- G3(ii) permuted-gate placebo: same TOTAL fire count, random rows --
        hook_pg, controller_pg, layer_idx_pg, _s, _r = ml.setup_hook_from_path(C_HAT_PATH)
        layer_module_pg = get_decoder_layer(model, layer_idx_pg)
        h_ctrl = layer_module_pg.register_forward_hook(controller_pg)
        pool = [dict(r, _pool="confab") for r in confab_held] + \
               [dict(r, _pool="known") for r in known_held]
        rng = pyrandom.Random(placebo_seed)
        idx = list(range(len(pool)))
        rng.shuffle(idx)
        fire_idx = set(idx[:n_fired])
        confab_pg_recs, known_pg_recs = [], []
        for i, r in enumerate(pool):
            fire = i in fire_idx
            rec = run_one_row(model, controller_pg, tokenizer, dev, r, fire,
                              strength_c_hat, "confab" if r["_pool"] == "confab" else "known_correct_answered")
            if r["_pool"] == "confab":
                confab_pg_recs.append(rec)
            else:
                known_pg_recs.append(rec)
        results["permuted_gate"] = {
            "n_fired_total": n_fired,
            "confab_tighten": _grade_population(confab_pg_recs, "clean_tighten"),
            "known_correct_cost_control": _grade_population(known_pg_recs, "not_well_formed_correct"),
        }
        h_ctrl.remove()
    finally:
        try:
            h_ctrl.remove()
        except Exception:
            pass
        del model
        gc.collect()
        torch.cuda.empty_cache()

    out_path = ANALYSIS / "full_summary.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "full"], required=True)
    ap.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    ap.add_argument("--dose", type=float, default=DOSE_TARGET_DEFAULT)
    ap.add_argument("--i-know-this-is-the-confirmatory-run", action="store_true")
    args = ap.parse_args()

    if args.mode == "smoke":
        run_smoke(args.n_rows, args.dose)
    else:
        print(
            "[pipeline] --mode full is the CONFIRMATORY end-to-end held-out "
            "run. This build task does not launch it; it is included so the "
            "lead can run it after sign-off. Refusing to run without "
            "--i-know-this-is-the-confirmatory-run.",
            file=sys.stderr,
        )
        if not args.i_know_this_is_the_confirmatory_run:
            return 2
        run_full(args.dose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
