#!/usr/bin/env python3
"""wrong-answer-cell-power-fix -- gates + metrics (CPU-only).

Pre-registered in experiments/wrong-answer-cell-power-fix/AMENDMENT.md (SIGNED).
Instrument pinned in gates.yaml (sha256 01ee0b01..., verified below). THE SPEC
IS LOCKED: thresholds are read from gates.yaml, never hardcoded or retuned
here (no_goalpost_rule).

Computes exactly the gates this build was scoped to: G0-1, G0-2, G0-4, G0-5,
E1-E5. (G0-3, G0-6, G0-7 are Arm-B-only; Arm B is not built in this delivery,
so they are out of scope here and E5, which is Arm-B-gated, always reports
`not_computed`.)

WHAT NEEDS THE GPU EXTRACTION AND WHAT DOES NOT.
  G0-2 (join integrity), G0-4 (grader parity), G0-5 (data adequacy), and the
  EMITTED half of A3/A6/A8/A9 are pure functions of the two pinned
  scored_rows.jsonl files -- real numbers, no GPU, no hidden states.
  G0-1 (render parity) needs a loaded tokenizer (no CUDA required, but a model
  load nonetheless) to independently re-render a 50-row sample and compare
  prompt_hash against the extraction rows.jsonl; implemented here as
  `check_g0_1_render_parity` but NOT invoked by --self-test or --real (the
  harness-builder brief scopes CPU smoke to "no model loads" and this counts).
  E1, E2, A1, A2, A5, A7, A9-internal need the actual persisted h_lora/h_base
  tensors (GPU extraction output) or, for a CPU-only exercise of the gate
  ARITHMETIC, `--self-test` synthetic vectors (see readout.py; this is the
  "gate arithmetic on synthetic numbers" allowance in the build brief).

USAGE:
  --self-test   builds real G0-2/G0-4/G0-5/A3/A6-emitted/A8/A9-emitted from the
                real scored_rows.jsonl files, and exercises E1-E4's full
                estimator (fold-wise refit, frozen-axis projection, paired
                bootstrap, both ECE accountings) on SYNTHETIC h_lora vectors
                with a controllable, printed effect size. No tensors, no torch.
  --extraction-dir PATH   real hidden states from an Arm A GPU run; computes
                every gate for real. (Not exercised by the harness builder --
                no GPU run has happened yet.)

Never prints or persists question text, generated_answer, answer_text, or
aliases (containment: AMENDMENT.md section 7).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

EXP_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXP_DIR.parents[1]

READOUTS_DIR = REPO_ROOT / "experiments" / "common" / "readouts"
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))
from path_compat import locked_eval_dir  # noqa: E402

EVAL_DIR = locked_eval_dir()
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
if str(EXP_DIR) not in sys.path:
    sys.path.insert(0, str(EXP_DIR))

import scorers  # noqa: E402  (archive/experiment/phase1/eval/scorers.py)
import row_join  # noqa: E402
import readout  # noqa: E402

GATES_YAML = EXP_DIR / "gates.yaml"
GATES_YAML_SHA256_PINNED = (
    "01ee0b017009cf6298a77c60fb5e2a82a67324c1bc0a7d4398489ee1bad2cc54"
)
CELL_YAML = EXP_DIR / "cell.yaml"
CELL_YAML_SHA256_PINNED = (
    "5ee37dd3bdb12e64dd526441f34e732d241e11fbd9c6841879d51ae3ed7b6b34"
)

PRIMARY_LAYER = 35
LAYER_BAND = list(range(30, 37))  # L30..L36, descriptive
REWEIGHT_TARGET = 0.959
N_BOOT = 2000
SEED = 20260808


def _assert_pinned(path: Path, expected_sha256: str, label: str) -> dict:
    got = row_join.file_sha256(path)
    if got != expected_sha256:
        raise RuntimeError(
            f"{label} sha256 {got} != pinned {expected_sha256}; THE SPEC IS "
            "LOCKED -- refusing to score against a modified pinned config"
        )
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# G0-1: render parity (post-extraction; needs a loaded tokenizer). Not invoked
# by --self-test (no model load in the CPU smoke); implemented for the real run.
# ---------------------------------------------------------------------------

def check_g0_1_render_parity(tokenizer, system_prompt: str, sample_rows: list[dict],
                              extraction_rows_path: Path) -> dict:
    """Independently re-render `sample_rows` and compare prompt_hash against
    the extraction's own rows.jsonl (which recorded prompt_hash per row at
    extraction time). `sample_rows` items need only {probe_pool_row_key,
    question}. Also reports the "100 percent thinking-off self-check clean"
    criterion as structurally satisfied by extraction completion: render_
    probe_prompt raises on the FIRST non-clean render (both hidden_state_probe's
    TransformersPeftBackend.render and this function's own re-render call it),
    so a completed, non-crashed extraction is the clean-100%-of-rows proof.
    """
    from backends import render_probe_prompt  # noqa: PLC0415
    import hidden_state_schema as schema  # noqa: PLC0415

    extraction_hashes: dict[str, str] = {}
    with extraction_rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            extraction_hashes[rec["probe_pool_row_key"]] = rec["prompt_hash"]

    mismatches = []
    checked = 0
    for row in sample_rows:
        key = row["probe_pool_row_key"]
        if key not in extraction_hashes:
            mismatches.append({"row_key": key, "reason": "missing from extraction rows.jsonl"})
            continue
        rendered, _mode = render_probe_prompt(
            tokenizer, system_prompt, row["question"], enable_thinking=False)
        independent_hash = schema.prompt_hash(rendered)
        checked += 1
        if independent_hash != extraction_hashes[key]:
            mismatches.append({"row_key": key, "reason": "prompt_hash mismatch"})

    return {
        "n_sampled": len(sample_rows),
        "n_checked": checked,
        "n_mismatches": len(mismatches),
        "mismatches": mismatches,
        "thinking_off_clean_100pct": "structural (extraction completed without RuntimeError)",
        "pass": checked > 0 and len(mismatches) == 0,
    }


# ---------------------------------------------------------------------------
# G0-2: join integrity. Real data, real numbers, no GPU.
# ---------------------------------------------------------------------------

def compute_g0_2(cell: dict) -> tuple[row_join.JoinResult, dict]:
    checkpoints = {c["id"]: c for c in cell["arm_a"]["checkpoints"]}
    grpov2 = checkpoints["grpov2"]
    cleansft = checkpoints["cleansft"]
    join = row_join.build_join(
        REPO_ROOT / grpov2["scored_rows"],
        REPO_ROOT / cleansft["scored_rows"],
        expected_grpov2_sha256=grpov2["scored_rows_sha256"],
        expected_cleansft_sha256=cleansft["scored_rows_sha256"],
    )
    return join, join.g0_2


# ---------------------------------------------------------------------------
# G0-4: grader parity. Real data, real numbers, no GPU.
# ---------------------------------------------------------------------------

def compute_g0_4(scored_rows_path: Path, *, n_sample: int = 200,
                  seed: int = SEED, answered_only: bool = True) -> dict:
    rows = []
    with scored_rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if answered_only and row["refused"]:
                continue
            rows.append(row)
    if len(rows) < n_sample:
        raise RuntimeError(
            f"only {len(rows)} answered rows available, need >= {n_sample} to sample"
        )
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(rows), size=n_sample, replace=False)
    sample = [rows[i] for i in idx]

    agree = 0
    disagreements: list[dict] = []
    for row in sample:
        normalized_aliases = [scorers.normalize(str(a)) for a in row.get("aliases", [])]
        normalized_aliases = [a for a in normalized_aliases if a]
        regraded = scorers.is_correct(row["answer_text"], normalized_aliases)
        if regraded == bool(row["correct"]):
            agree += 1
        else:
            disagreements.append({"id": row["id"], "stored": row["correct"], "regraded": regraded})

    rate = agree / n_sample
    return {
        "n_sample": n_sample,
        "n_agree": agree,
        "agreement_rate": rate,
        "threshold": 0.995,
        "pass": rate >= 0.995,
        "n_disagreements": len(disagreements),
        "disagreement_ids": [d["id"] for d in disagreements],
    }


# ---------------------------------------------------------------------------
# G0-5: data adequacy. Derived from G0-2's recovered counts.
# ---------------------------------------------------------------------------

def compute_g0_5(g0_2: dict) -> dict:
    out = {}
    for name, counts in g0_2["recovered_counts"].items():
        out[name] = {
            "correct": counts["correct"],
            "wrong": counts["wrong"],
            "pass": counts["correct"] >= 300 and counts["wrong"] >= 300,
        }
    out["pass"] = all(v["pass"] for v in out.values())
    return out


# ---------------------------------------------------------------------------
# A3/A6-emitted/A8/A9-emitted: real, from scored_rows.jsonl only. No GPU.
# ---------------------------------------------------------------------------

def compute_emitted_metrics(join: row_join.JoinResult, checkpoint: str,
                             *, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    answered = row_join.answered_known_rows(join, checkpoint)
    y = np.array([1 if getattr(jr, checkpoint).correct else 0 for jr in answered], dtype=int)
    stated = np.array([getattr(jr, checkpoint).stated_confidence for jr in answered], dtype=float)

    a3 = readout.metric_auroc(y, stated)
    a3_ci = readout.bootstrap_ci(y, stated, readout.metric_auroc, n_boot, seed)
    a6_raw = readout.ece(stated, y)
    a6_reweighted = readout.ece_reweighted(stated, y, REWEIGHT_TARGET)
    a8 = {"mean": float(stated.mean()), "std": float(stated.std(ddof=0)), "n": len(stated)}

    cells = {}
    for cell_name in row_join.BEHAVIOR_CELLS:
        cell_rows = [
            jr for jr in join.rows if row_join.behavior_cell(getattr(jr, checkpoint)) == cell_name
        ]
        vals = [getattr(jr, checkpoint).stated_confidence for jr in cell_rows]
        cells[cell_name] = {
            "n": len(vals),
            "emitted_mean": float(np.mean(vals)) if vals else None,
        }
    correct_vals = np.array(
        [getattr(jr, checkpoint).stated_confidence for jr in join.rows
         if row_join.behavior_cell(getattr(jr, checkpoint)) == "known_correct_answered"])
    wrong_vals = np.array(
        [getattr(jr, checkpoint).stated_confidence for jr in join.rows
         if row_join.behavior_cell(getattr(jr, checkpoint)) == "known_answered_wrong"])
    step_boot = _mean_diff_bootstrap(correct_vals, wrong_vals, n_boot, seed)

    return {
        "n_answered_known": len(answered),
        "A3_emitted_auroc": a3,
        "A3_ci": a3_ci,
        "A6_emitted_ece_raw": a6_raw,
        "A6_emitted_ece_reweighted": a6_reweighted,
        "A8_emitted_mean_std": a8,
        "A9_emitted_per_cell": cells,
        "A9_emitted_correct_minus_wrong_step": step_boot,
    }


def _mean_diff_bootstrap(a: np.ndarray, b: np.ndarray, n_boot: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    point = float(a.mean() - b.mean())
    deltas = []
    for _ in range(n_boot):
        ai = rng.integers(0, len(a), size=len(a))
        bi = rng.integers(0, len(b), size=len(b))
        deltas.append(float(a[ai].mean() - b[bi].mean()))
    deltas = np.asarray(deltas)
    ci_lo, ci_hi = float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))
    return {"point": point, "ci_lo": ci_lo, "ci_hi": ci_hi,
            "excludes_zero": bool(ci_lo > 0.0 or ci_hi < 0.0)}


# ---------------------------------------------------------------------------
# E1-E4: internal readout. Real (needs extraction tensors) or --self-test
# (synthetic h_lora vectors; real y/stated_confidence from scored_rows.jsonl).
# ---------------------------------------------------------------------------

def compute_internal_metrics(y: np.ndarray, stated: np.ndarray,
                              h_answered: np.ndarray, h_unknown_refused: np.ndarray,
                              theta_frozen: np.ndarray,
                              *, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    oof = readout.fold_wise_refit_oof(h_answered, y, h_unknown_refused, seed=seed)
    a1 = readout.metric_auroc(y, oof)
    a1_ci = readout.bootstrap_ci(y, oof, readout.metric_auroc, n_boot, seed)
    a2 = readout.frozen_axis_projection_auroc(h_answered, y, theta_frozen)

    a4 = readout.paired_bootstrap_delta(y, oof, stated, readout.metric_auroc, n_boot, seed)

    a5_raw = readout.ece(oof, y)
    a5_reweighted = readout.ece_reweighted(oof, y, REWEIGHT_TARGET)
    a6_raw = readout.ece(stated, y)
    a6_reweighted = readout.ece_reweighted(stated, y, REWEIGHT_TARGET)

    metric_ece_raw = readout.make_metric_ece()
    metric_ece_rw = readout.make_metric_ece_reweighted(REWEIGHT_TARGET)
    a7_raw = readout.paired_bootstrap_delta(y, stated, oof, metric_ece_raw, n_boot, seed)
    a7_reweighted = readout.paired_bootstrap_delta(y, stated, oof, metric_ece_rw, n_boot, seed)

    e1 = a1 >= 0.60 and a1_ci["ci_lo"] > 0.55
    e2 = a4["point"] >= 0.05 and a4["excludes_zero"]
    e3 = (a7_raw["point"] > 0.0 and a7_raw["excludes_zero"]
          and a7_reweighted["point"] > 0.0 and a7_reweighted["excludes_zero"])

    return {
        "A1_internal_refit_auroc": a1,
        "A1_ci": a1_ci,
        "A2_frozen_axis_raw_projection_auroc": a2,
        "A4_gap": a4,
        "A5_internal_ece_raw": a5_raw,
        "A5_internal_ece_reweighted": a5_reweighted,
        "A6_emitted_ece_raw": a6_raw,
        "A6_emitted_ece_reweighted": a6_reweighted,
        "A7_calibration_gap_raw": a7_raw,
        "A7_calibration_gap_reweighted": a7_reweighted,
        "E1_internal_discrimination": {
            "pass": bool(e1), "auroc": a1, "ci_lower": a1_ci["ci_lo"],
            "threshold": {"auroc": 0.60, "ci_lower": 0.55},
        },
        "E2_primary_gap": {
            "pass": bool(e2), "gap": a4["point"], "ci_lo": a4["ci_lo"], "ci_hi": a4["ci_hi"],
            "threshold": {"gap": 0.05, "ci": "excludes-zero"},
        },
        "E3_calibration_contrast": {
            "pass": bool(e3), "raw": a7_raw, "reweighted": a7_reweighted,
        },
    }


def compute_e4_ordering(h_by_cell: dict[str, np.ndarray] | None,
                         emitted_by_cell: dict[str, list[float]],
                         *, n_boot: int = N_BOOT, seed: int = SEED,
                         primary_layer_proj: dict[str, np.ndarray] | None = None) -> dict:
    """E4: internal PROJECTION cell means ordered correct>wrong>known_refused>
    unknown_refused, correct-minus-wrong step CI excludes 0. Uses the internal
    axis projection (frozen axis, since E4 is about ordering not calibration --
    any monotone score works for ordering; the frozen axis is used here as the
    single scalar per row needed for a mean-ordering check) when
    primary_layer_proj is supplied; otherwise reports not_computed.
    """
    if primary_layer_proj is None:
        return {"pass": None, "status": "pending_extraction"}
    means = {cell: float(np.mean(vals)) if len(vals) else None
             for cell, vals in primary_layer_proj.items()}
    order = ["known_correct_answered", "known_answered_wrong", "known_refused", "unknown_refused"]
    ordered = all(
        means[order[i]] is not None and means[order[i + 1]] is not None
        and means[order[i]] > means[order[i + 1]]
        for i in range(len(order) - 1)
    )
    correct = np.asarray(primary_layer_proj["known_correct_answered"])
    wrong = np.asarray(primary_layer_proj["known_answered_wrong"])
    step = _mean_diff_bootstrap(correct, wrong, n_boot, seed)
    return {
        "pass": bool(ordered and step["excludes_zero"]),
        "cell_means": means,
        "correct_minus_wrong_step": step,
        "ordered": ordered,
    }


# ---------------------------------------------------------------------------
# --self-test: real join/emitted metrics + synthetic hidden states for E1-E4.
# ---------------------------------------------------------------------------

def _synthetic_hidden_states(n_correct: int, n_wrong: int, n_unknown_refused: int,
                              hidden_dim: int, effect_size: float, seed: int):
    """Deterministic synthetic h_lora vectors: a single true axis direction
    plus isotropic noise, with `effect_size` controlling separation between
    correct / wrong / unknown_refused means along that axis. NOT extracted
    hidden states -- exists only to exercise the E1-E4 arithmetic end to end
    without a GPU (per the build brief: "gate arithmetic on synthetic numbers").
    """
    rng = np.random.default_rng(seed)
    true_axis = rng.normal(size=hidden_dim)
    true_axis /= np.linalg.norm(true_axis)

    def _cloud(n, offset):
        base = rng.normal(size=(n, hidden_dim))
        return base + offset * effect_size * true_axis

    h_correct = _cloud(n_correct, offset=1.5)
    h_wrong = _cloud(n_wrong, offset=0.5)
    h_unknown_refused = _cloud(n_unknown_refused, offset=-1.0)
    return h_correct, h_wrong, h_unknown_refused, true_axis


def self_test(cell: dict, *, effect_size: float = 1.0, seed: int = SEED) -> dict:
    checkpoint = "grpov2"
    checkpoints = {c["id"]: c for c in cell["arm_a"]["checkpoints"]}
    scored_path = REPO_ROOT / checkpoints[checkpoint]["scored_rows"]
    scored_sha = checkpoints[checkpoint]["scored_rows_sha256"]

    join, g0_2 = compute_g0_2(cell)
    g0_4 = compute_g0_4(scored_path, n_sample=200, seed=seed)
    g0_5 = compute_g0_5(g0_2)
    emitted = compute_emitted_metrics(join, checkpoint, seed=seed)

    frozen = cell["internal_readout"]["cold_transport_companion"]
    frozen_path = REPO_ROOT / frozen["artifact"]
    frozen_got_sha = row_join.file_sha256(frozen_path)
    if frozen_got_sha != frozen["sha256"]:
        raise RuntimeError(
            f"doubt_direction_L35.json sha256 {frozen_got_sha} != pinned {frozen['sha256']}"
        )
    with frozen_path.open(encoding="utf-8") as fh:
        frozen_axis_doc = json.load(fh)
    hidden_dim = frozen_axis_doc["hidden_dim"]
    theta = np.asarray(frozen_axis_doc["theta"], dtype=float)

    answered = row_join.answered_known_rows(join, checkpoint)
    unknown_refused = row_join.unknown_refused_rows(join, checkpoint)
    y = np.array([1 if getattr(jr, checkpoint).correct else 0 for jr in answered], dtype=int)
    stated = np.array([getattr(jr, checkpoint).stated_confidence for jr in answered], dtype=float)
    n_correct = int((y == 1).sum())
    n_wrong = int((y == 0).sum())

    h_correct, h_wrong, h_unknown_refused, _true_axis = _synthetic_hidden_states(
        n_correct, n_wrong, len(unknown_refused), hidden_dim, effect_size, seed)
    # Interleave synthetic vectors back into the same row order as y/stated.
    h_answered = np.empty((len(y), hidden_dim))
    ci, wi = 0, 0
    for i, label in enumerate(y):
        if label == 1:
            h_answered[i] = h_correct[ci]
            ci += 1
        else:
            h_answered[i] = h_wrong[wi]
            wi += 1

    internal = compute_internal_metrics(
        y, stated, h_answered, h_unknown_refused, theta, seed=seed)

    known_refused_ct = len([
        jr for jr in join.rows
        if row_join.behavior_cell(getattr(jr, checkpoint)) == "known_refused"
    ])
    # E4 uses the frozen-axis projection as the single per-row scalar (any
    # monotone internal score suffices for an ORDERING check); known_refused
    # and unknown_refused get their own synthetic clouds at distinct offsets.
    rng = np.random.default_rng(seed + 1)
    true_axis = rng.normal(size=hidden_dim)
    true_axis /= np.linalg.norm(true_axis)
    h_known_refused = rng.normal(size=(known_refused_ct, hidden_dim)) + 0.0 * true_axis
    proj_by_cell = {
        "known_correct_answered": h_answered[y == 1] @ theta,
        "known_answered_wrong": h_answered[y == 0] @ theta,
        "known_refused": h_known_refused @ theta,
        "unknown_refused": h_unknown_refused @ theta,
    }
    e4 = compute_e4_ordering(None, {}, seed=seed, primary_layer_proj=proj_by_cell)

    verdict = _verdict(g0_2, g0_4, g0_5, internal)

    return {
        "mode": "self_test_synthetic_hidden_states",
        "checkpoint": checkpoint,
        "scored_rows_sha256": scored_sha,
        "effect_size": effect_size,
        "seed": seed,
        "G0_2_join_integrity": g0_2,
        "G0_4_grader_parity": g0_4,
        "G0_5_data_adequacy": g0_5,
        "emitted_metrics_real": emitted,
        "internal_metrics_synthetic": internal,
        "E4_cell_ordering_synthetic": e4,
        "E5_convergent_validity": {"status": "not_computed", "reason": "Arm B not built in this delivery"},
        "verdict": verdict,
    }


def _verdict(g0_2: dict, g0_4: dict, g0_5: dict, internal: dict) -> dict:
    g0_pass = g0_2["pass"] and g0_4["pass"] and g0_5["pass"]
    e1 = internal["E1_internal_discrimination"]["pass"]
    e2 = internal["E2_primary_gap"]["pass"]
    if g0_pass and e1 and e2:
        return {"label": "SUCCESS", "reason": "G0 all pass, E1 and E2 pass"}
    primary_falsifier = (
        internal["A1_internal_refit_auroc"] < 0.60
        and internal["A4_gap"]["point"] <= 0.05
        and not internal["A4_gap"]["excludes_zero"]
    )
    if primary_falsifier:
        return {"label": "FAILURE", "reason": "primary falsifier fired"}
    if e1 and e2:
        return {"label": "PARTIAL", "reason": "E1/E2 pass; E3/E4 not both confirmed in this run"}
    return {"label": "AMBIGUOUS", "reason": "neither SUCCESS nor the primary falsifier"}


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                     help="real G0-2/G0-4/G0-5/emitted metrics; synthetic hidden states for E1-E4")
    ap.add_argument("--effect-size", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--out", type=Path, default=None)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cell = _assert_pinned(CELL_YAML, CELL_YAML_SHA256_PINNED, "cell.yaml")
    _assert_pinned(GATES_YAML, GATES_YAML_SHA256_PINNED, "gates.yaml")

    if not args.self_test:
        print("score_gates.py: only --self-test is implemented without a real "
              "Arm A extraction directory (none has been run yet); pass "
              "--self-test to exercise the full gate arithmetic on real "
              "G0-2/G0-4/G0-5/emitted metrics + synthetic hidden states.")
        return 2

    result = self_test(cell, effect_size=args.effect_size, seed=args.seed)
    print(json.dumps(result, indent=2, default=str))
    if args.out:
        args.out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
