#!/usr/bin/env python3
"""H4 -- ungated-vs-gated dose-matched arm for the caution snap. Local 3090.

Implements AMENDMENT.md's Design verbatim: two arms over the SAME held-out
rows, SAME dose, in ONE harness pass. Per row this generates exactly two
passes (a baseline "off" pass and a dosed "gen_stream" pass at the frozen
c_hat / dose_target=200 setpoint) -- not two passes per arm. The gated arm's
output for a fired row IS the dosed pass; for a non-fired row it IS the
baseline pass. The ungated arm's output is always the dosed pass. This
reuses the single generation pair for both arms rather than re-generating,
which is also why the AMENDMENT's own cost estimate is ~886 generations
(443 rows x 2 passes), not 443 x 3.

Nothing here is refit: u_d, c_hat, tau_frozen, and mu_d/sigma_d/sigma_c are
read from the resolved doubt-gated-caution-tighten cell's committed
analysis-committed/ (frozen_instrument in cell.yaml). The per-row L34 anchor
activations used for the gate decision are the resolved cell's own extracted
tensors, subset to held-out rows by materialize_rows.py (see that script's
docstring) -- no fresh extraction, no fresh forward pass for gating.

Gates computed here (gates.yaml, all over the 443 held-out rows):
  H4-G0  gate-on reproduction / instrument validity (pre-analysis; failure is
         a STOP, not an outcome).
  H4-G1  gate certifies selectivity (primary): paired McNemar over the 258
         known-correct rows.
  H4-G2  conversion preserved / parity, over the 185 confab rows.

--mode smoke runs a tiny (default 8-row) end-to-end pass proving the wiring
(gate decisions load, both passes generate, readback lands near target) --
NOT a gate-worthy sample.
--mode full runs the real 443-row held-out sweep; this is the CONFIRMATORY
run and is not launched by the harness-build task. Resumable via RunLog
keyed by row_key: a killed run can be restarted and picks up only the rows
not yet recorded.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
RESOLVED_COMMITTED = HERE.parent / "doubt-gated-caution-tighten" / "analysis-committed"
TUNER_DIR = HERE.parent.parent / "synaptic-tuner"

for p in (str(TUNER_DIR), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_lib as gl  # noqa: E402
import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from MechInterp.intervention import get_decoder_layer  # noqa: E402
from shared.utilities.run_log import RunLog  # noqa: E402

ROWS_WITH_TEXT = ANALYSIS / "rows_with_text.jsonl"
HELDOUT_TENSORS = ANALYSIS / "l34_anchor_extract_heldout.safetensors"
U_D_PATH = RESOLVED_COMMITTED / "u_d_L34.json"
C_HAT_PATH = RESOLVED_COMMITTED / "c_hat_L34.json"
BUILD_MANIFEST_PATH = RESOLVED_COMMITTED / "build_manifest.json"
GATE_FIT_PATH = RESOLVED_COMMITTED / "gate_fit.json"

DOSE_TARGET = 200.0  # frozen, cell.yaml snap.dose_target -- do not tune
MAX_NEW = gl.MAX_NEW_CAP

RESOLVED_REFERENCE = {
    "gated_confab_clean_tighten": 0.735,
    "gated_known_correct_false_refuse": 0.031,
}


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _load_jsonl_by_key(p: Path, key_field: str) -> dict[str, dict]:
    return {rec[key_field]: rec for rec in load_jsonl(p)}


def load_direction_vector(p: Path) -> np.ndarray:
    d = json.loads(p.read_text())
    return np.asarray(d["vector"], dtype=np.float64)


# ---------------------------------------------------------------------------
# Pure gate-decision math (no I/O) -- unit-testable on CPU without a model.
# ---------------------------------------------------------------------------

def gate_decision(proj_d: float, mu_d: float, sigma_d: float, tau: float) -> dict:
    """AMENDMENT.md's frozen fire rule: fire iff neg_z_d = -z_d >= tau, z_d
    standardized with the FIT-pool mu_d/sigma_d and clipped to [-2, +2]."""
    z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
    score = -z_d
    fire = bool(score >= tau)
    return {"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": score, "fire": fire, "tau": tau}


def load_rows_and_gate_decisions() -> list[dict]:
    """Load this experiment's own materialized held-out rows (443: 185
    confab + 258 known_correct_answered) and attach the frozen gate's fire
    decision to each, using the resolved cell's already-extracted L34
    anchor tensors (subset by materialize_rows.py) -- no fresh extraction."""
    from safetensors.numpy import load_file

    if not ROWS_WITH_TEXT.is_file() or not HELDOUT_TENSORS.is_file():
        raise FileNotFoundError(
            f"missing {ROWS_WITH_TEXT} or {HELDOUT_TENSORS}; run materialize_rows.py first"
        )
    rows = load_jsonl(ROWS_WITH_TEXT)
    tensors_raw = load_file(str(HELDOUT_TENSORS))
    fresh = {k: np.asarray(v, dtype=np.float64) for k, v in tensors_raw.items()}
    u_d = load_direction_vector(U_D_PATH)
    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    mu_d, sigma_d = build_manifest["mu_d"], build_manifest["sigma_d"]
    tau = json.loads(GATE_FIT_PATH.read_text())["tau_frozen"]

    out = []
    for r in rows:
        H = fresh[_sanitize_key(r["row_key"])]
        proj_d = float(H @ u_d)
        decision = gate_decision(proj_d, mu_d, sigma_d, tau)
        rec = dict(r)
        rec.update(decision)
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# One row, two passes (baseline + dosed) -- feeds both arms.
# ---------------------------------------------------------------------------

def run_one_row_dual(model, controller, tokenizer, dev, row: dict, strength_c_hat: float) -> dict:
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)

    _base_out, _rb, base_terminated, base_new = gl.run_pass_fixed(
        model, controller, enc, "off", 0.0, tokenizer, max_new=MAX_NEW
    )
    base_text = tokenizer.decode(base_new, skip_special_tokens=True)

    _dosed_out, readback, dosed_terminated, dosed_new = gl.run_pass_fixed(
        model, controller, enc, "gen_stream", strength_c_hat, tokenizer, max_new=MAX_NEW
    )
    dosed_text = tokenizer.decode(dosed_new, skip_special_tokens=True)

    aliases = row.get("aliases")
    return {
        "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
        "fire": row["fire"], "score_neg_z_d": row["score_neg_z_d"], "tau": row["tau"],
        "readback_measured": readback,
        "baseline": {
            "text": base_text, "terminated_naturally": base_terminated,
            "clean_tighten": gl.grade_clean_tighten(base_text, base_terminated),
            "well_formed_correct": grader.grade_one(base_text, aliases),
        },
        "dosed": {
            "text": dosed_text, "terminated_naturally": dosed_terminated,
            "clean_tighten": gl.grade_clean_tighten(dosed_text, dosed_terminated),
            "well_formed_correct": grader.grade_one(dosed_text, aliases),
        },
    }


def build_arm_records(dual_record: dict) -> tuple[dict, dict]:
    """Pure function (no I/O, no model): derive the gated-arm and ungated-arm
    per-row outcome from one dual (baseline+dosed) record and its fire flag.
    Gated uses dosed if fired else baseline; ungated always uses dosed."""
    fire = bool(dual_record["fire"])
    base, dosed = dual_record["baseline"], dual_record["dosed"]
    common = {
        "row_key": dual_record["row_key"], "role": dual_record["role"],
        "category_canon": dual_record.get("category_canon"), "fire": fire,
    }

    def _arm(src: dict, dosed_flag: bool) -> dict:
        ct = bool(src["clean_tighten"]["clean_tighten"])
        wfc = bool(src["well_formed_correct"]["well_formed_correct"])
        return dict(common, dosed=dosed_flag, clean_tighten=ct,
                    well_formed_correct=wfc, not_well_formed_correct=not wfc)

    gated = _arm(dosed if fire else base, dosed_flag=fire)
    ungated = _arm(dosed, dosed_flag=True)
    return gated, ungated


# ---------------------------------------------------------------------------
# Aggregation + gates (pure, no I/O) -- unit-testable on CPU.
# ---------------------------------------------------------------------------

def _grade_population(recs: list[dict], metric: str) -> dict:
    n = len(recs)
    successes = sum(1 for r in recs if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def compute_h4_gates(
    gated_confab: list[dict], gated_known: list[dict],
    ungated_confab: list[dict], ungated_known: list[dict],
) -> dict:
    """Compute H4-G0/G1/G2 exactly as pinned in gates.yaml. gated_known and
    ungated_known must cover the same row_keys (paired); pairing is done by
    row_key here rather than assumed positional, since the two lists are
    built from independent list comprehensions."""
    gated_confab_agg = _grade_population(gated_confab, "clean_tighten")
    gated_known_agg = _grade_population(gated_known, "not_well_formed_correct")
    ungated_confab_agg = _grade_population(ungated_confab, "clean_tighten")
    ungated_known_agg = _grade_population(ungated_known, "not_well_formed_correct")

    # H4-G0: gate-on reproduction / instrument validity (pre-analysis STOP).
    confab_rate = gated_confab_agg["rate"]
    known_rate = gated_known_agg["rate"]
    g0_confab_pass = abs(confab_rate - RESOLVED_REFERENCE["gated_confab_clean_tighten"]) <= 0.05
    g0_known_pass = abs(known_rate - RESOLVED_REFERENCE["gated_known_correct_false_refuse"]) <= 0.03
    h4_g0 = {
        "name": "h4_g0_gate_on_reproduction",
        "gated_confab_clean_tighten": gated_confab_agg,
        "gated_known_correct_false_refuse": gated_known_agg,
        "checks": {
            "confab_conversion_reproduces": bool(g0_confab_pass),
            "known_correct_cost_reproduces": bool(g0_known_pass),
        },
        "passed": bool(g0_confab_pass and g0_known_pass),
    }

    # H4-G1: gate certifies selectivity (primary), paired McNemar over known-correct.
    gated_by_key = {r["row_key"]: r["not_well_formed_correct"] for r in gated_known}
    ungated_by_key = {r["row_key"]: r["not_well_formed_correct"] for r in ungated_known}
    paired_keys = sorted(set(gated_by_key) & set(ungated_by_key))
    n_unpaired = len(set(gated_by_key) ^ set(ungated_by_key))
    b = sum(1 for k in paired_keys if ungated_by_key[k] and not gated_by_key[k])
    c = sum(1 for k in paired_keys if not ungated_by_key[k] and gated_by_key[k])
    mcnemar = ml.mcnemar_exact(b, c)
    gap = ungated_known_agg["rate"] - gated_known_agg["rate"]
    g1_gap_pass = gap >= 0.15
    g1_p_pass = mcnemar["p_value"] < 0.001
    h4_g1 = {
        "name": "h4_g1_gate_certifies_selectivity",
        "n_paired": len(paired_keys), "n_unpaired_rows_dropped": n_unpaired,
        "ungated_known_correct_damage": ungated_known_agg,
        "gated_known_correct_damage": gated_known_agg,
        "absolute_gap": gap,
        "mcnemar": mcnemar,
        "checks": {"gap_ge_0_15": bool(g1_gap_pass), "mcnemar_p_lt_0_001": bool(g1_p_pass)},
        "passed": bool(g1_gap_pass and g1_p_pass),
    }

    # H4-G2: conversion preserved / parity, over confab.
    difference = gated_confab_agg["rate"] - ungated_confab_agg["rate"]
    g2_pass = difference >= -0.15
    h4_g2 = {
        "name": "h4_g2_conversion_preserved",
        "ungated_confab_clean_tighten": ungated_confab_agg,
        "gated_confab_clean_tighten": gated_confab_agg,
        "difference_gated_minus_ungated": difference,
        "passed": bool(g2_pass),
    }

    return {"h4_g0_gate_on_reproduction": h4_g0, "h4_g1_gate_certifies_selectivity": h4_g1,
            "h4_g2_conversion_preserved": h4_g2}


# ---------------------------------------------------------------------------
# GPU smoke.
# ---------------------------------------------------------------------------

def run_smoke(n_rows: int, dose_target: float) -> dict:
    rows = load_rows_and_gate_decisions()
    confab_rows = [r for r in rows if r["role"] == "confab"][: n_rows // 2]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"][: n_rows - len(confab_rows)]
    sample = confab_rows + known_rows
    print(f"[smoke] n_rows={len(sample)} (confab={len(confab_rows)}, known={len(known_rows)}); "
          f"fires: confab={sum(r['fire'] for r in confab_rows)}/{len(confab_rows)}, "
          f"known={sum(r['fire'] for r in known_rows)}/{len(known_rows)}")

    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c

    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    duals = []
    out_path = ANALYSIS / "smoke_rows.jsonl"
    try:
        with out_path.open("w") as out_f:
            for r in sample:
                dual = run_one_row_dual(model, controller, tokenizer, dev, r, strength_c_hat)
                out_f.write(json.dumps(dual) + "\n")
                out_f.flush()
                duals.append(dual)
                print(f"[smoke] {dual['row_key']} role={dual['role']} fire={dual['fire']} "
                      f"readback={dual['readback_measured']} "
                      f"base_ct={dual['baseline']['clean_tighten']['clean_tighten']} "
                      f"dosed_ct={dual['dosed']['clean_tighten']['clean_tighten']}")
    finally:
        h_ctrl.remove()
        del model
        gc.collect()
        torch.cuda.empty_cache()

    readbacks = [d["readback_measured"] for d in duals if d["readback_measured"] is not None]
    within_tol = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    summary = {
        "dose_target": dose_target, "sigma_c": sigma_c, "strength_gain": strength_c_hat,
        "n_rows": len(duals), "n_dosed_passes": len(readbacks),
        "readback_mean": (sum(readbacks) / len(readbacks)) if readbacks else None,
        "frac_within_tol": (sum(within_tol) / len(within_tol)) if within_tol else None,
        "rows_path": str(out_path),
    }
    (ANALYSIS / "smoke_summary.json").write_text(json.dumps(summary, indent=2))
    print("\n=== SMOKE SUMMARY ===")
    print(json.dumps(summary, indent=2))
    return summary


# ---------------------------------------------------------------------------
# Full held-out sweep (confirmatory; gated by the lead's launch approval).
# ---------------------------------------------------------------------------

def run_full(dose_target: float) -> dict:
    rows = load_rows_and_gate_decisions()
    n_confab = sum(1 for r in rows if r["role"] == "confab")
    n_known = sum(1 for r in rows if r["role"] == "known_correct_answered")
    assert n_confab == 185, f"expected 185 confab held-out rows, got {n_confab}"
    assert n_known == 258, f"expected 258 known_correct_answered held-out rows, got {n_known}"

    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c

    run_config = {
        "amendment": "ungated-vs-gated-dose-matched", "dose_target": dose_target,
        "sigma_c": sigma_c, "tau_frozen": json.loads(GATE_FIT_PATH.read_text())["tau_frozen"],
        "n_confab": n_confab, "n_known_correct_answered": n_known,
    }
    log_path = ANALYSIS / "run_log.jsonl"
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    run_log = RunLog(log_path, run_config, key_field="row_key")

    pending = list(run_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
    print(f"[full] {len(rows)} held-out rows, {len(rows) - len(pending)} already done, "
          f"{len(pending)} pending")

    if pending:
        hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(C_HAT_PATH)
        model, tokenizer = ml.load_model()
        dev = next(model.parameters()).device
        layer_module = get_decoder_layer(model, layer_idx)
        h_ctrl = layer_module.register_forward_hook(controller)
        try:
            for i, r in enumerate(pending):
                dual = run_one_row_dual(model, controller, tokenizer, dev, r, strength_c_hat)
                run_log.record(r["row_key"], dual)
                if (i + 1) % 25 == 0 or (i + 1) == len(pending):
                    print(f"[full] {i + 1}/{len(pending)} pending rows done", flush=True)
        finally:
            h_ctrl.remove()
            del model
            gc.collect()
            torch.cuda.empty_cache()

    # -- rebuild both arms from the (possibly resumed) durable log. Re-read
    # from disk by row_key rather than reach into RunLog's internals: this
    # keeps the read path independent of that class's private state and
    # correct across resumed runs, at the cost of one extra file pass. Safe
    # to read while run_log's append handle is still open -- every record()
    # call already flushed + fsynced before returning. --
    log_records = _load_jsonl_by_key(log_path, "row_key")
    gated_confab, gated_known, ungated_confab, ungated_known = [], [], [], []
    readbacks = []
    for r in rows:
        dual = log_records[r["row_key"]]
        if dual.get("readback_measured") is not None:
            readbacks.append(dual["readback_measured"])
        gated, ungated = build_arm_records(dual)
        if r["role"] == "confab":
            gated_confab.append(gated)
            ungated_confab.append(ungated)
        else:
            gated_known.append(gated)
            ungated_known.append(ungated)

    gates = compute_h4_gates(gated_confab, gated_known, ungated_confab, ungated_known)

    within_tol = [abs(rb - dose_target) <= 0.05 * dose_target + 0.5 for rb in readbacks]
    readback_check = {
        "n_dosed_passes": len(readbacks),
        "readback_mean": (sum(readbacks) / len(readbacks)) if readbacks else None,
        "readback_min": min(readbacks) if readbacks else None,
        "readback_max": max(readbacks) if readbacks else None,
        "frac_within_5pct_tol": (sum(within_tol) / len(within_tol)) if within_tol else None,
        "note": "informational only, mirrors the resolved cell's own G0(b) write-fires "
                "check; H4-G0's pass/fail per gates.yaml is the two rate-reproduction "
                "checks only, not this readback tolerance.",
    }

    full_summary = {
        "dose_target": dose_target, "sigma_c": sigma_c, "strength_gain": strength_c_hat,
        "n_confab_held_out": n_confab, "n_known_correct_answered_held_out": n_known,
        "readback_check": readback_check,
        "gates": gates,
    }
    (ANALYSIS / "ungated_vs_gated_summary.json").write_text(json.dumps(full_summary, indent=2))

    committed_summary = {
        "amendment": "ungated-vs-gated-dose-matched",
        "resolved_reference": RESOLVED_REFERENCE,
        "n_confab_held_out": n_confab, "n_known_correct_answered_held_out": n_known,
        "dose_target": dose_target,
        "readback_check": readback_check,
        "gates": gates,
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    (COMMITTED / "ungated_vs_gated_summary.json").write_text(json.dumps(committed_summary, indent=2))

    run_log.finalize({"n_rows": len(rows), "gates_summary": {
        k: v["passed"] for k, v in gates.items()
    }})
    run_log.close()

    print(json.dumps(full_summary, indent=2))
    return full_summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "full"], required=True)
    ap.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    ap.add_argument("--dose", type=float, default=DOSE_TARGET)
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
