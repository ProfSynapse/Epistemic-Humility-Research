#!/usr/bin/env python3
"""AL prep: L35 doubt-axis check + full-stack drift profile on the A0 surface.

The AL-prep A0 cells extracted the FULL layer stack (L0..L36, pre-generation
anchor) for the AI-TRUE and AI-PERMUTED checkpoints over the same 1,662-row
question pool. This closes the gap the earlier L24-only extracts left: the
doubt/caution axes live at L35 and could not be read until now.

Three questions, CPU-only:
  1. Do the grpo_v2-lineage reference axes (doubt, caution, caution_perp; all
     L35 h_lora) still read behavior on these GRPO-v3 PAR checkpoints?
     (AUROCs of axis projections vs gold class / refusal / confab.)
  2. How far have the axes themselves drifted? (arm-local re-fits vs the
     reference directions, and TRUE-local vs PERMUTED-local.)
  3. Where in the stack does TRUE diverge from PERMUTED, and is the L35
     divergence aligned with the doubt/caution axes? (row-aligned TRUE-PERM
     drift: per-layer norms + axis alignment + variance fractions at L35.)

Reference doubt axis is recomputed exactly as build_caution_perp_direction.py
defines it: unit(mean(known_correct_answered) - mean(unknown_refused)) on the
grpo_v2 selfaware extraction. Caution / caution_perp thetas load from their
direction JSONs. Arm-local cells come from the graded A0 rows:
  ka = answerable & answered & correct     (known_correct_answered analogue)
  ur = unanswerable & refused              (unknown_refused analogue)
  ar = answerable & refused                (caution positive-cell proxy; the
       true known_refused cell needs knowledge labels refusals don't carry)

Usage:
  python amendment_al_prep_doubt_axis_check.py [--al-prep-dir <dir>]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
if str(ARCHIVE_AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))

from path_compat import phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from phase3_latent_knowledge_probe import load_layers  # noqa: E402

CANONICAL = repo_root()
CPROBE = CANONICAL / "experiment/phase1/probe"
REF_EXTRACT = (CPROBE / "qwen3-4b-clean-sft-grpo-v2-seed1-selfaware"
               / "hidden_states_selfaware_clean_sft_grpo_v2_full"
               / "extraction__55254a04aa1f")
REF_OVERLAY = (CPROBE / "analysis/current_selfaware_behavior_rows"
               / "clean_sft_grpo_v2/rows.jsonl")
REF_DIR_DIR = CPROBE / "analysis/current_clean_grpo_v2_caution_residual_direction"
DEFAULT_AL_PREP = CPROBE / "analysis/amendment_al_prep"
L35 = 35
N_LAYERS = 37
EXPECTED_ROWS = 1662


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def auroc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Rank-based AUROC, ties handled; no sklearn dependency."""
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    scores = np.concatenate([pos, neg])
    order = scores.argsort(kind="mergesort")
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    # average ranks over ties
    sorted_scores = scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def load_a0_stack(extract_data: Path, row_keys: list[str]) -> np.ndarray:
    """[n_rows, 37, 2560] float32; one safetensors open per row."""
    from safetensors import safe_open

    safe = {r["row_key"]: r["safe_key"]
            for r in load_jsonl(extract_data / "rows.jsonl")}
    keys = [f"L{i}" for i in range(N_LAYERS)]
    out = None
    for i, rk in enumerate(row_keys):
        path = extract_data / f"{safe[rk]}__pre.safetensors"
        with safe_open(str(path), "np") as h:
            if out is None:
                dim = h.get_tensor("L0").shape[0]
                out = np.empty((len(row_keys), N_LAYERS, dim), dtype=np.float32)
            for li, key in enumerate(keys):
                out[i, li] = h.get_tensor(key)
    return out


def ref_axes() -> dict[str, np.ndarray]:
    overlay = load_jsonl(REF_OVERLAY)
    cell = lambda c: [r["probe_pool_row_key"] for r in overlay  # noqa: E731
                      if r["behavior_cell"] == c]
    Xka = load_layers(REF_EXTRACT, cell("known_correct_answered"), [L35])[L35]
    Xur = load_layers(REF_EXTRACT, cell("unknown_refused"), [L35])[L35]
    doubt = unit(Xka.mean(0) - Xur.mean(0))
    caution = unit(np.asarray(json.loads(
        (REF_DIR_DIR / "caution_direction_L35.json").read_text())["theta"]))
    caution_perp = unit(np.asarray(json.loads(
        (REF_DIR_DIR / "caution_perp_direction_L35.json").read_text())["theta"]))
    return {"doubt": doubt, "caution": caution, "caution_perp": caution_perp}


def arm_local_axes(X35: np.ndarray, graded: list[dict]) -> dict:
    idx = lambda pred: np.array([i for i, r in enumerate(graded) if pred(r)])  # noqa: E731
    ka = idx(lambda r: r["gold_class"] == "answerable" and r["answered"] and r["correct"] is True)
    ur = idx(lambda r: r["gold_class"] == "unanswerable" and r["refused"])
    ar = idx(lambda r: r["gold_class"] == "answerable" and r["refused"])
    doubt = unit(X35[ka].mean(0) - X35[ur].mean(0))
    caution = X35[ar].mean(0) - X35[ka].mean(0)
    caution_perp = unit(caution - (caution @ doubt) * doubt)
    return {"doubt": doubt, "caution": unit(caution), "caution_perp": caution_perp,
            "n_cells": {"ka": int(len(ka)), "ur": int(len(ur)), "ar": int(len(ar))}}


def axis_readouts(X35: np.ndarray, graded: list[dict], axes: dict) -> dict:
    answerable = np.array([r["gold_class"] == "answerable" for r in graded])
    refused = np.array([bool(r["refused"]) for r in graded])
    answered = np.array([bool(r["answered"]) for r in graded])
    una = ~answerable
    out = {}
    for name, u in axes.items():
        p = X35 @ u
        entry = {
            "auroc_answerable_vs_unanswerable": auroc(p[answerable], p[una]),
            "auroc_refused_vs_answered": auroc(p[refused], p[answered]),
        }
        # within unanswerable: do confabs sit high on this axis (reads-as-known)?
        entry["auroc_confab_vs_refused_within_unanswerable"] = auroc(
            p[una & answered], p[una & refused])
        out[name] = {k: round(v, 4) for k, v in entry.items()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    args = ap.parse_args()
    al_prep = Path(args.al_prep_dir)

    graded = {arm: load_jsonl(al_prep / arm / "gen/data/rows_graded.jsonl")
              for arm in ("true_a0", "permuted_a0")}
    row_keys = [r["row_key"] for r in graded["true_a0"]]
    assert len(row_keys) == EXPECTED_ROWS
    assert [r["row_key"] for r in graded["permuted_a0"]] == row_keys, \
        "arms are not row-aligned"

    print("[axes] recomputing reference doubt axis from grpo_v2 extraction ...")
    ref = ref_axes()

    stacks = {}
    for arm in graded:
        print(f"[load] {arm} full stack ...")
        stacks[arm] = load_a0_stack(al_prep / arm / "extract/data", row_keys)

    report = {"n_rows": EXPECTED_ROWS, "layers": N_LAYERS, "arms": {}}
    local = {}
    for arm in graded:
        X35 = stacks[arm][:, L35, :].astype(np.float64)
        local[arm] = arm_local_axes(X35, graded[arm])
        report["arms"][arm] = {
            "n_cells": local[arm]["n_cells"],
            "reference_axis_readouts": axis_readouts(X35, graded[arm], ref),
            "local_axis_readouts": axis_readouts(
                X35, graded[arm],
                {k: local[arm][k] for k in ("doubt", "caution", "caution_perp")}),
            "local_vs_reference_cos": {
                k: round(float(local[arm][k] @ ref[k]), 4)
                for k in ("doubt", "caution", "caution_perp")},
        }

    report["cross_arm_local_axis_cos"] = {
        k: round(float(local["true_a0"][k] @ local["permuted_a0"][k]), 4)
        for k in ("doubt", "caution", "caution_perp")}

    # row-aligned TRUE - PERMUTED drift, full stack
    drift = stacks["true_a0"].astype(np.float64) - stacks["permuted_a0"].astype(np.float64)
    true_norm = np.linalg.norm(stacks["true_a0"].astype(np.float64), axis=2).mean(0)
    per_layer = []
    for li in range(N_LAYERS):
        D = drift[:, li, :]
        per_layer.append({
            "layer": li,
            "mean_drift_norm": round(float(np.linalg.norm(D.mean(0))), 3),
            "mean_row_drift_norm": round(float(np.linalg.norm(D, axis=1).mean()), 3),
            "rel_row_drift": round(float(np.linalg.norm(D, axis=1).mean()
                                         / true_norm[li]), 4),
        })
    report["drift_per_layer"] = per_layer

    D35 = drift[:, L35, :]
    mean_d = D35.mean(0)
    total_var = float(D35.var(0).sum())
    align = {}
    for name, u in {**ref, **{f"local_true_{k}": v for k, v in local["true_a0"].items()
                              if k != "n_cells"}}.items():
        proj = D35 @ u
        align[name] = {
            "cos_mean_drift": round(float(unit(mean_d) @ u), 4),
            "drift_variance_fraction": round(float(proj.var() / total_var), 5),
            "mean_projection": round(float(proj.mean()), 3),
        }
    report["l35_drift_axis_alignment"] = align

    out = al_prep / "doubt_axis_check_report.json"
    out.write_text(json.dumps(report, indent=2))

    print(f"\n== reference-axis readouts (L35) ==")
    for arm in report["arms"]:
        print(f"[{arm}] ref: {json.dumps(report['arms'][arm]['reference_axis_readouts'])}")
        print(f"[{arm}] local-vs-ref cos: {report['arms'][arm]['local_vs_reference_cos']}")
    print(f"cross-arm local axis cos: {report['cross_arm_local_axis_cos']}")
    top = sorted(per_layer, key=lambda r: -r["rel_row_drift"])[:5]
    print(f"top drift layers (rel): {[(r['layer'], r['rel_row_drift']) for r in top]}")
    print(f"L35 drift alignment: {json.dumps(align, indent=1)}")
    print(f"[doubt-axis-check] report -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
