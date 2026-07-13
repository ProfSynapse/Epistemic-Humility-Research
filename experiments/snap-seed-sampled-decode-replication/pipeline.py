#!/usr/bin/env python3
"""H3 -- multi-seed / sampled-decode replication of the doubt-gated caution
snap. Local 3090.

Implements AMENDMENT.md's Design verbatim:

  Arm R (greedy reproduction, instrument-validity anchor): ONE deterministic
  pass per held-out row (dosed along c_hat if the row's frozen gate fires,
  else baseline), batch-1 -- parity-locked vs the resolved cell
  (.skills/experiment-runner/reference/batched-generation.md's "Parity-locked
  surface: batch-1, no exceptions"). This is the H3-G0 anchor.

  Arm S (sampled decode, primary): for each of K seeds, N=8 samples per row
  in ONE batched model.generate() call (N identical copies of that row's
  prompt -- no cross-row batch composition, see gen_lib.py's batched-decode
  section docstring), do_sample=True/temperature=0.7/top_p=0.9. Per-row
  conversion/damage scored three pre-stated ways (majority-vote primary,
  any-vote envelope, mean fraction), reported per seed and pooled.

  Placebo seed-robustness (H3-G3): per seed, a FRESH random write direction
  (random_direction_reroll) and a FRESH permuted-gate assignment
  (permuted_gate_reroll), both under GREEDY decode batch-1 (same
  parity-locked reasoning as Arm R -- these vary the direction/assignment,
  not the decode policy, so decode stays fixed to isolate that one axis).

Nothing here is refit: u_d, c_hat, tau_frozen, mu_d/sigma_d/sigma_c are read
from the resolved doubt-gated-caution-tighten cell's committed
analysis-committed/. The per-row L34 anchor activations used for the gate
decision are that cell's own extracted tensors, subset to held-out rows by
materialize_rows.py -- no fresh extraction, no fresh forward pass for gating.

--mode smoke runs a tiny end-to-end GPU pass (a handful of rows, one seed)
proving the wiring -- NOT a gate-worthy sample.
--mode full runs the real held-out sweep across all requested seeds; this is
the CONFIRMATORY run and is not launched by the harness-build task.
--seeds K slices the registered 5-seed list down to the first K (the
AMENDMENT's own pre-stated fallback if the sampled budget overruns one
evening); gates apply per-seed and pooled regardless of K and never move.

Every generation phase is RunLog-resumable, keyed appropriately for that
phase's natural atomic unit of work (see each run_* function).
"""

from __future__ import annotations

import argparse
import gc
import hashlib
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

REGISTERED_SEEDS = [20260710, 20260711, 20260712, 20260713, 20260714]  # K=5, cell.yaml
N_SAMPLES = 8  # cell.yaml decode_arms.sampled_decode.samples_per_row
MAJORITY_VOTE_THRESHOLD = 5  # of 8; 4-4 tie -> not converted / not damaged
ANY_VOTE_THRESHOLD = 1
SAMPLED_GENERATION_KWARGS = {"do_sample": True, "temperature": 0.7, "top_p": 0.9}

RESOLVED_REFERENCE = {
    "gated_confab_clean_tighten": 0.735,
    "gated_confab_wilson_ci": [0.667, 0.793],
    "gated_known_correct_false_refuse": 0.031,
}
H3_G3_RANDOM_DIRECTION_CEILING = 0.25   # every seed; resolved single-seed value 0.070
H3_G3_PERMUTED_GATE_FLOOR = 0.15        # every seed; resolved single-seed value 0.229


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _load_jsonl_by_key(p: Path, key_field: str) -> dict[str, dict]:
    return {rec[key_field]: rec for rec in load_jsonl(p)}


def load_direction_vector(p: Path) -> np.ndarray:
    d = json.loads(p.read_text())
    return np.asarray(d["vector"], dtype=np.float64)


def derive_seed(base_seed: int, row_key: str) -> int:
    """Stable per-(row, base_seed) integer for torch.manual_seed, recorded
    per row in the manifest (this is the "seed derivation per row x sample x
    arm" the task calls for -- derivation is per row x base_seed, since a
    single torch.manual_seed call ahead of one batched generate() call seeds
    all N=8 samples of that row together; the 8 samples are not individually
    re-seedable within one batched call, see gen_lib.py's batched-decode
    docstring, and re-running the same (row, base_seed) reproduces the same
    N=8 draws given no other RNG consumption occurs in between."""
    digest = hashlib.sha256(f"{base_seed}:{row_key}".encode("utf-8")).hexdigest()
    return int(digest, 16) % (2 ** 31)


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
# Arm R: greedy reproduction, batch-1, one pass per row (H3-G0 anchor).
# ---------------------------------------------------------------------------

def run_one_row_greedy(model, controller, tokenizer, dev, row: dict, strength_c_hat: float) -> dict:
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)
    fire = bool(row["fire"])
    mode = "gen_stream" if fire else "off"
    strength = strength_c_hat if fire else 0.0

    _out, readback, terminated, new_tokens = gl.run_pass_fixed(
        model, controller, enc, mode, strength, tokenizer, max_new=MAX_NEW
    )
    text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    ct = gl.grade_clean_tighten(text, terminated)
    wfc = grader.grade_one(text, row.get("aliases"))
    return {
        "row_key": row["row_key"], "role": row["role"], "fire": fire,
        "readback_measured": readback, "terminated_naturally": terminated,
        "clean_tighten": bool(ct["clean_tighten"]),
        "well_formed_correct": bool(wfc["well_formed_correct"]),
        "not_well_formed_correct": not bool(wfc["well_formed_correct"]),
    }


# ---------------------------------------------------------------------------
# Arm S: sampled decode, batched N=8 identical-prompt copies per (row, seed).
# ---------------------------------------------------------------------------

def score_row_samples(samples: list[dict], key: str) -> dict:
    """majority_vote (>=5/8, primary), any_vote (>=1/8, envelope), and
    mean_fraction (supplement) for one row-seed unit's 8 samples on one
    boolean field. A 4-4 tie has count=4 < 5, so majority_vote is False --
    AMENDMENT.md's "4-4 tie counts as instrument did not act" for both the
    conversion (converted=False) and damage (damaged=False) directions,
    since both are scored as ">= 5 of 8", never as a symmetric >=4."""
    n = len(samples)
    count = sum(1 for s in samples if s[key])
    return {
        "n_samples": n, "count": count,
        "majority_vote": count >= MAJORITY_VOTE_THRESHOLD,
        "any_vote": count >= ANY_VOTE_THRESHOLD,
        "mean_fraction": (count / n) if n else 0.0,
    }


def run_batch_sampled_for_row(
    model, controller, tokenizer, dev, row: dict, seed: int, strength_c_hat: float,
    n_samples: int = N_SAMPLES,
) -> dict:
    fire = bool(row["fire"])
    prompt = ml.render(row)
    enc1 = tokenizer(prompt, return_tensors="pt")
    input_ids = enc1["input_ids"].repeat(n_samples, 1).to(dev)
    attention_mask = enc1["attention_mask"].repeat(n_samples, 1).to(dev)
    enc_batch = {"input_ids": input_ids, "attention_mask": attention_mask}

    mode = "gen_stream" if fire else "off"
    strength = strength_c_hat if fire else 0.0
    derived_seed = derive_seed(seed, row["row_key"])
    torch.manual_seed(derived_seed)

    texts, terminated_flags, readback = gl.run_batched_sampled_pass(
        model, controller, enc_batch, mode, strength, tokenizer,
        generation_kwargs=SAMPLED_GENERATION_KWARGS, max_new=MAX_NEW,
    )
    aliases = row.get("aliases")
    samples = []
    for text, terminated in zip(texts, terminated_flags):
        ct = gl.grade_clean_tighten(text, terminated)
        wfc = grader.grade_one(text, aliases)
        wfc_bool = bool(wfc["well_formed_correct"])
        samples.append({
            "clean_tighten": bool(ct["clean_tighten"]),
            "well_formed_correct": wfc_bool,
            "not_well_formed_correct": not wfc_bool,
        })
    readback_mean = None
    if readback and readback.get("measured"):
        readback_mean = sum(readback["measured"]) / len(readback["measured"])

    return {
        "row_key": row["row_key"], "role": row["role"], "fire": fire,
        "seed": seed, "derived_seed": derived_seed, "readback_mean": readback_mean,
        "samples": samples,
    }


# ---------------------------------------------------------------------------
# Placebo seed-robustness (H3-G3): fresh direction / fresh permutation per
# seed, GREEDY decode batch-1 (parity-locked; only the direction/assignment
# varies across seeds, not the decode policy).
# ---------------------------------------------------------------------------

def run_one_row_greedy_with_direction(
    model, controller, tokenizer, dev, row: dict, fire: bool, strength: float,
) -> dict:
    """Same shape as run_one_row_greedy, but the caller has already set
    controller.hook.direction/sigma to whatever placebo direction is live for
    this phase, and fire/strength are passed explicitly (random_direction_reroll
    reuses the row's REAL fire flag; permuted_gate_reroll uses a reassigned
    fire flag from the fresh permutation, not row['fire'])."""
    prompt = ml.render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(dev)
    mode = "gen_stream" if fire else "off"
    eff_strength = strength if fire else 0.0

    _out, readback, terminated, new_tokens = gl.run_pass_fixed(
        model, controller, enc, mode, eff_strength, tokenizer, max_new=MAX_NEW
    )
    text = tokenizer.decode(new_tokens, skip_special_tokens=True)
    ct = gl.grade_clean_tighten(text, terminated)
    wfc = grader.grade_one(text, row.get("aliases"))
    return {
        "row_key": row["row_key"], "role": row["role"], "fire": fire,
        "readback_measured": readback, "terminated_naturally": terminated,
        "clean_tighten": bool(ct["clean_tighten"]),
        "well_formed_correct": bool(wfc["well_formed_correct"]),
        "not_well_formed_correct": not bool(wfc["well_formed_correct"]),
    }


# ---------------------------------------------------------------------------
# Aggregation + gates (pure, no I/O) -- unit-testable on CPU.
# ---------------------------------------------------------------------------

def _grade_population(recs: list[dict], metric: str) -> dict:
    n = len(recs)
    successes = sum(1 for r in recs if r[metric])
    rate, lo, hi = ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


def compute_h3_g0(greedy_confab: list[dict], greedy_known: list[dict]) -> dict:
    confab_agg = _grade_population(greedy_confab, "clean_tighten")
    known_agg = _grade_population(greedy_known, "not_well_formed_correct")
    confab_ci = tuple(confab_agg["wilson_ci_95"])
    confab_pass = (
        abs(confab_agg["rate"] - RESOLVED_REFERENCE["gated_confab_clean_tighten"]) <= 0.05
        and ml.wilson_ci_overlap(confab_ci, tuple(RESOLVED_REFERENCE["gated_confab_wilson_ci"]))
    )
    known_pass = abs(known_agg["rate"] - RESOLVED_REFERENCE["gated_known_correct_false_refuse"]) <= 0.03
    return {
        "name": "h3_g0_greedy_reproduction",
        "gated_confab_clean_tighten": confab_agg,
        "gated_known_correct_false_refuse": known_agg,
        "checks": {
            "confab_conversion_reproduces": bool(confab_pass),
            "known_correct_cost_reproduces": bool(known_pass),
        },
        "passed": bool(confab_pass and known_pass),
    }


def _score_seed_units(row_seed_units: list[dict], role: str, sample_key: str) -> list[dict]:
    """row_seed_units: run_batch_sampled_for_row() outputs. Returns one
    score_row_samples() dict per matching-role unit."""
    return [score_row_samples(u["samples"], sample_key) for u in row_seed_units if u["role"] == role]


def _pooled_and_per_seed(units_by_seed: dict[int, list[dict]], role: str, sample_key: str) -> dict:
    per_seed = {}
    pooled_scores: list[dict] = []
    for seed, units in units_by_seed.items():
        scores = _score_seed_units(units, role, sample_key)
        pooled_scores.extend(scores)
        majority_agg = _grade_population(
            [{"v": s["majority_vote"]} for s in scores], "v",
        )
        any_agg_rate = (sum(1 for s in scores if s["any_vote"]) / len(scores)) if scores else 0.0
        mean_fraction = (sum(s["mean_fraction"] for s in scores) / len(scores)) if scores else 0.0
        per_seed[seed] = {
            "majority_vote": majority_agg, "any_vote_rate": any_agg_rate,
            "mean_per_row_fraction": mean_fraction,
        }
    pooled_majority = _grade_population([{"v": s["majority_vote"]} for s in pooled_scores], "v")
    pooled_any_rate = (sum(1 for s in pooled_scores if s["any_vote"]) / len(pooled_scores)) if pooled_scores else 0.0
    pooled_mean_fraction = (
        sum(s["mean_fraction"] for s in pooled_scores) / len(pooled_scores)
    ) if pooled_scores else 0.0
    return {
        "per_seed": per_seed,
        "pooled": {
            "majority_vote": pooled_majority, "any_vote_rate": pooled_any_rate,
            "mean_per_row_fraction": pooled_mean_fraction,
        },
    }


def compute_h3_g1(units_by_seed: dict[int, list[dict]]) -> dict:
    """units_by_seed holds ALL rows (both roles) per seed; role filtering to
    confab happens inside _pooled_and_per_seed."""
    agg = _pooled_and_per_seed(units_by_seed, "confab", "clean_tighten")
    pooled_rate = agg["pooled"]["majority_vote"]["rate"]
    pooled_pass = pooled_rate >= 0.635
    per_seed_pass = {seed: (v["majority_vote"]["rate"] >= 0.635) for seed, v in agg["per_seed"].items()}
    return {
        "name": "h3_g1_sampled_conversion_band",
        **agg,
        "checks": {"pooled_ge_0_635": bool(pooled_pass), "per_seed_ge_0_635": per_seed_pass},
        "passed": bool(pooled_pass and all(per_seed_pass.values())),
    }


def compute_h3_g2(units_by_seed: dict[int, list[dict]]) -> dict:
    """units_by_seed holds ALL rows (both roles) per seed; role filtering to
    known_correct_answered happens inside _pooled_and_per_seed."""
    agg = _pooled_and_per_seed(units_by_seed, "known_correct_answered", "not_well_formed_correct")
    pooled = agg["pooled"]["majority_vote"]
    pooled_pass = pooled["rate"] <= 0.08 and pooled["wilson_ci_95"][1] < 0.12
    per_seed_pass = {}
    for seed, v in agg["per_seed"].items():
        m = v["majority_vote"]
        per_seed_pass[seed] = bool(m["rate"] <= 0.08 and m["wilson_ci_95"][1] < 0.12)
    return {
        "name": "h3_g2_sampled_cost_ceiling",
        **agg,
        "checks": {"pooled_pass": bool(pooled_pass), "per_seed_pass": per_seed_pass},
        "passed": bool(pooled_pass and all(per_seed_pass.values())),
    }


def compute_h3_g3(
    random_direction_by_seed: dict[int, list[dict]],
    permuted_gate_by_seed: dict[int, list[dict]],
) -> dict:
    random_checks, permuted_checks = {}, {}
    random_rates, permuted_rates = {}, {}
    for seed, recs in random_direction_by_seed.items():
        confab_recs = [r for r in recs if r["role"] == "confab"]
        agg = _grade_population(confab_recs, "clean_tighten")
        random_rates[seed] = agg
        random_checks[seed] = bool(agg["rate"] < H3_G3_RANDOM_DIRECTION_CEILING)
    for seed, recs in permuted_gate_by_seed.items():
        known_recs = [r for r in recs if r["role"] == "known_correct_answered"]
        agg = _grade_population(known_recs, "not_well_formed_correct")
        permuted_rates[seed] = agg
        permuted_checks[seed] = bool(agg["rate"] > H3_G3_PERMUTED_GATE_FLOOR)
    return {
        "name": "h3_g3_placebo_seed_robustness",
        "random_direction_confab_clean_tighten_by_seed": random_rates,
        "permuted_gate_known_correct_false_refuse_by_seed": permuted_rates,
        "checks": {
            "random_direction_stays_inert_every_seed": random_checks,
            "permuted_gate_stays_worse_every_seed": permuted_checks,
        },
        "passed": bool(all(random_checks.values()) and all(permuted_checks.values())),
    }


# ---------------------------------------------------------------------------
# GPU smoke.
# ---------------------------------------------------------------------------

def run_smoke(n_rows: int, dose_target: float) -> dict:
    rows = load_rows_and_gate_decisions()
    confab_rows = [r for r in rows if r["role"] == "confab"][: n_rows // 2]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"][: n_rows - len(confab_rows)]
    sample = confab_rows + known_rows

    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c
    smoke_seed = REGISTERED_SEEDS[0]

    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    greedy_recs, sampled_recs = [], []
    try:
        for r in sample:
            greedy_recs.append(run_one_row_greedy(model, controller, tokenizer, dev, r, strength_c_hat))
            sampled_recs.append(
                run_batch_sampled_for_row(model, controller, tokenizer, dev, r, smoke_seed, strength_c_hat, n_samples=4)
            )
        # G3 smoke: one row through a freshly-drawn random direction, proving
        # that placebo code path too.
        fresh_vec = ml.draw_random_direction(smoke_seed)
        controller.hook.direction = torch.tensor(fresh_vec, dtype=torch.float32)
        controller.hook.sigma = 1.0
        placebo_random_rec = run_one_row_greedy_with_direction(
            model, controller, tokenizer, dev, sample[0], fire=True, strength=dose_target,
        )

        # G3 smoke, other placebo arm: restore c_hat, then run one row under a
        # freshly-drawn permuted-gate fire flag (deliberately flipped from the
        # row's real gate decision, to prove the flag actually drives mode).
        controller.hook.direction = torch.tensor(load_direction_vector(C_HAT_PATH), dtype=torch.float32)
        controller.hook.sigma = sigma_c
        permuted_fire = not bool(sample[0]["fire"])
        placebo_permuted_rec = run_one_row_greedy_with_direction(
            model, controller, tokenizer, dev, sample[0], fire=permuted_fire, strength=strength_c_hat,
        )
    finally:
        h_ctrl.remove()
        del model
        gc.collect()
        torch.cuda.empty_cache()

    summary = {
        "dose_target": dose_target, "sigma_c": sigma_c, "strength_gain": strength_c_hat,
        "n_rows": len(sample),
        "greedy_fires": sum(1 for r in greedy_recs if r["fire"]),
        "sampled_fires": sum(1 for r in sampled_recs if r["fire"]),
        "sampled_sample_counts": [len(r["samples"]) for r in sampled_recs],
        "placebo_random_direction_smoke_row": placebo_random_rec["row_key"],
        "placebo_permuted_gate_smoke_row": placebo_permuted_rec["row_key"],
        "placebo_permuted_gate_smoke_fire": permuted_fire,
    }
    (ANALYSIS / "smoke_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("\n=== SMOKE SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return summary


# ---------------------------------------------------------------------------
# Full held-out sweep (confirmatory; gated by the lead's launch approval).
# ---------------------------------------------------------------------------

def run_full(dose_target: float, seeds: list[int]) -> dict:
    rows = load_rows_and_gate_decisions()
    confab_rows = [r for r in rows if r["role"] == "confab"]
    known_rows = [r for r in rows if r["role"] == "known_correct_answered"]
    assert len(confab_rows) == 185, f"expected 185 confab held-out rows, got {len(confab_rows)}"
    assert len(known_rows) == 258, f"expected 258 known_correct_answered held-out rows, got {len(known_rows)}"

    build_manifest = json.loads(BUILD_MANIFEST_PATH.read_text())
    sigma_c = build_manifest["sigma_c"]
    strength_c_hat = dose_target / sigma_c
    n_fired_real = sum(1 for r in rows if r["fire"])

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    hook, controller, layer_idx, _sigma, _rec = ml.setup_hook_from_path(C_HAT_PATH)
    model, tokenizer = ml.load_model()
    dev = next(model.parameters()).device
    layer_module = get_decoder_layer(model, layer_idx)
    h_ctrl = layer_module.register_forward_hook(controller)

    try:
        # -- Phase A: Arm R greedy reproduction, batch-1, all 443 rows --------
        greedy_log = RunLog(ANALYSIS / "run_log_greedy.jsonl",
                            {"dose_target": dose_target, "sigma_c": sigma_c}, key_field="row_key")
        pending = list(greedy_log.iter_pending(rows, key_fn=lambda r: r["row_key"]))
        print(f"[full] Arm R greedy: {len(rows)} rows, {len(rows) - len(pending)} done, {len(pending)} pending")
        for i, r in enumerate(pending):
            rec = run_one_row_greedy(model, controller, tokenizer, dev, r, strength_c_hat)
            greedy_log.record(r["row_key"], rec)
            if (i + 1) % 50 == 0 or (i + 1) == len(pending):
                print(f"[full] Arm R {i + 1}/{len(pending)}", flush=True)
        greedy_records = _load_jsonl_by_key(ANALYSIS / "run_log_greedy.jsonl", "row_key")
        greedy_confab = [greedy_records[r["row_key"]] for r in confab_rows]
        greedy_known = [greedy_records[r["row_key"]] for r in known_rows]
        h3_g0 = compute_h3_g0(greedy_confab, greedy_known)
        greedy_log.finalize({"n_rows": len(rows), "g0_passed": h3_g0["passed"]})
        greedy_log.close()

        # -- Phase B: Arm S sampled decode, batched N=8, rows x seeds --------
        sampled_log = RunLog(ANALYSIS / "run_log_sampled.jsonl",
                             {"dose_target": dose_target, "sigma_c": sigma_c,
                              "n_samples": N_SAMPLES, "gen_kwargs": SAMPLED_GENERATION_KWARGS},
                             key_field="unit_key")
        sampled_work = [(r, s) for s in seeds for r in rows]
        pending_s = [
            (r, s) for (r, s) in sampled_work
            if f"{r['row_key']}::{s}" not in sampled_log.done_keys()
        ]
        print(f"[full] Arm S sampled: {len(sampled_work)} row-seed units, "
              f"{len(sampled_work) - len(pending_s)} done, {len(pending_s)} pending")
        for i, (r, s) in enumerate(pending_s):
            rec = run_batch_sampled_for_row(model, controller, tokenizer, dev, r, s, strength_c_hat)
            sampled_log.record(f"{r['row_key']}::{s}", rec)
            if (i + 1) % 100 == 0 or (i + 1) == len(pending_s):
                print(f"[full] Arm S {i + 1}/{len(pending_s)}", flush=True)
        sampled_records = _load_jsonl_by_key(ANALYSIS / "run_log_sampled.jsonl", "unit_key")
        units_by_seed: dict[int, list[dict]] = {s: [] for s in seeds}
        for r in rows:
            for s in seeds:
                units_by_seed[s].append(sampled_records[f"{r['row_key']}::{s}"])
        h3_g1 = compute_h3_g1(units_by_seed)
        h3_g2 = compute_h3_g2(units_by_seed)
        sampled_log.finalize({"n_units": len(sampled_work), "g1_passed": h3_g1["passed"], "g2_passed": h3_g2["passed"]})
        sampled_log.close()

        # -- Phase C: placebo random_direction_reroll, greedy batch-1 --------
        random_log = RunLog(ANALYSIS / "run_log_placebo_random_direction.jsonl",
                            {"dose_target": dose_target}, key_field="unit_key")
        random_work = [(r, s) for s in seeds for r in rows]
        pending_rd = [
            (r, s) for (r, s) in random_work
            if f"{s}::{r['row_key']}" not in random_log.done_keys()
        ]
        print(f"[full] placebo random_direction_reroll: {len(random_work)} units, "
              f"{len(random_work) - len(pending_rd)} done, {len(pending_rd)} pending")
        current_seed_for_hook = None
        for i, (r, s) in enumerate(pending_rd):
            if s != current_seed_for_hook:
                fresh_vec = ml.draw_random_direction(s)
                controller.hook.direction = torch.tensor(fresh_vec, dtype=torch.float32)
                controller.hook.sigma = 1.0
                current_seed_for_hook = s
            rec = run_one_row_greedy_with_direction(
                model, controller, tokenizer, dev, r, fire=bool(r["fire"]), strength=dose_target,
            )
            random_log.record(f"{s}::{r['row_key']}", rec)
            if (i + 1) % 100 == 0 or (i + 1) == len(pending_rd):
                print(f"[full] placebo random {i + 1}/{len(pending_rd)}", flush=True)
        random_records = _load_jsonl_by_key(ANALYSIS / "run_log_placebo_random_direction.jsonl", "unit_key")
        random_by_seed = {s: [random_records[f"{s}::{r['row_key']}"] for r in rows] for s in seeds}
        random_log.finalize({"n_units": len(random_work)})
        random_log.close()

        # -- Phase D: placebo permuted_gate_reroll, greedy batch-1, c_hat -----
        controller.hook.direction = torch.tensor(load_direction_vector(C_HAT_PATH), dtype=torch.float32)
        controller.hook.sigma = sigma_c
        permuted_log = RunLog(ANALYSIS / "run_log_placebo_permuted_gate.jsonl",
                              {"dose_target": dose_target, "n_fired_real": n_fired_real},
                              key_field="unit_key")
        permuted_work = [(r, s) for s in seeds for r in rows]
        pending_pg = [
            (r, s) for (r, s) in permuted_work
            if f"{s}::{r['row_key']}" not in permuted_log.done_keys()
        ]
        print(f"[full] placebo permuted_gate_reroll: {len(permuted_work)} units, "
              f"{len(permuted_work) - len(pending_pg)} done, {len(pending_pg)} pending")
        row_key_to_idx = {row["row_key"]: idx for idx, row in enumerate(rows)}
        fire_idx_by_seed: dict[int, set] = {}
        for i, (r, s) in enumerate(pending_pg):
            if s not in fire_idx_by_seed:
                fire_idx_by_seed[s] = ml.draw_permuted_gate_indices(len(rows), n_fired_real, s)
            # row_idx is this row's position in `rows` (whatever order
            # load_rows_and_gate_decisions produced it in, not assumed to be
            # confab-then-known) -- draw_permuted_gate_indices was drawn over
            # range(len(rows)) against that same list, so the positions line up.
            row_idx = row_key_to_idx[r["row_key"]]
            fire = row_idx in fire_idx_by_seed[s]
            rec = run_one_row_greedy_with_direction(
                model, controller, tokenizer, dev, r, fire=fire, strength=strength_c_hat,
            )
            permuted_log.record(f"{s}::{r['row_key']}", rec)
            if (i + 1) % 100 == 0 or (i + 1) == len(pending_pg):
                print(f"[full] placebo permuted {i + 1}/{len(pending_pg)}", flush=True)
        permuted_records = _load_jsonl_by_key(ANALYSIS / "run_log_placebo_permuted_gate.jsonl", "unit_key")
        permuted_by_seed = {s: [permuted_records[f"{s}::{r['row_key']}"] for r in rows] for s in seeds}
        permuted_log.finalize({"n_units": len(permuted_work)})
        permuted_log.close()
    finally:
        h_ctrl.remove()
        del model
        gc.collect()
        torch.cuda.empty_cache()

    h3_g3 = compute_h3_g3(random_by_seed, permuted_by_seed)

    full_summary = {
        "dose_target": dose_target, "sigma_c": sigma_c, "seeds": seeds,
        "n_confab_held_out": len(confab_rows), "n_known_correct_answered_held_out": len(known_rows),
        "n_fired_real": n_fired_real,
        "gates": {"h3_g0": h3_g0, "h3_g1": h3_g1, "h3_g2": h3_g2, "h3_g3": h3_g3},
    }
    (ANALYSIS / "h3_full_summary.json").write_text(json.dumps(full_summary, indent=2, default=str))

    committed_summary = {
        "amendment": "snap-seed-sampled-decode-replication",
        "resolved_reference": RESOLVED_REFERENCE,
        "seeds": seeds, "dose_target": dose_target,
        "n_confab_held_out": len(confab_rows), "n_known_correct_answered_held_out": len(known_rows),
        "n_fired_real": n_fired_real,
        "gates": {"h3_g0": h3_g0, "h3_g1": h3_g1, "h3_g2": h3_g2, "h3_g3": h3_g3},
    }
    COMMITTED.mkdir(parents=True, exist_ok=True)
    (COMMITTED / "h3_summary.json").write_text(json.dumps(committed_summary, indent=2, default=str))

    print(json.dumps(full_summary, indent=2, default=str))
    return full_summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "full"], required=True)
    ap.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    ap.add_argument("--dose", type=float, default=DOSE_TARGET)
    ap.add_argument("--seeds", type=int, default=len(REGISTERED_SEEDS),
                     help="use the first K of the 5 registered seeds (AMENDMENT's own "
                          "pre-stated K=3 fallback); gates apply per-seed and pooled "
                          "regardless of K and never move")
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
        seeds = REGISTERED_SEEDS[: args.seeds]
        run_full(args.dose, seeds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
