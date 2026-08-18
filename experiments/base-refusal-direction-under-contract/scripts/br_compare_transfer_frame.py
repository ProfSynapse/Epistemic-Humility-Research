#!/usr/bin/env python3
"""Registered-frame Stage 5 for base-refusal-direction-under-contract.

Reruns the base-vs-trained refusal-direction comparison in the frame gates.yaml
actually pins: "permutation_floor: recomputed with the Section 5 procedure".
That procedure is the one implemented by
experiments/selfaware-latent-knowledge-controls/caution_axis_transfer.py -- an
L2 logistic refusal direction (C=0.5) fit per checkpoint in a frame
standardized on the POOLED known-row activations of every checkpoint being
compared, absolute cosines in that shared frame, and a label-permutation floor
computed with the identical fit on shuffled refuse/answer labels within each
checkpoint (ONE shuffle per checkpoint, not averaged reps -- that is what the
pinned script itself does; this script does not add reps beyond it).

This does NOT reimplement that logic from scratch: it imports
caution_axis_transfer.load_known and caution_axis_transfer._unit_direction
directly and drives them over 4 arms (the 3 trained checkpoints
caution_axis_transfer.py itself compares, plus base_under_contract) instead of
3, because cat.caution_axis_transfer() takes one `source` for every arm and
the base arm has no LoRA adapter (h_base, not h_lora) -- everything else
(StandardScaler pooled fit, LogisticRegression C=0.5, single-shuffle floor,
pairwise |cos|) is the pinned script's own code, called, not rewritten.

The first-pass br_compare_result.json (fit_and_compare.py) used a DIFFERENT,
mass-mean estimator in raw (unstandardized) space with a narrower known-only
(known_refused vs known_correct_answered) negative class for every arm -- kept
as a descriptive companion per that script's own methodology-anomaly note.
This script is the registered-frame comparison gates.yaml actually calibrates
BR-G1 against.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CAT_DIR = ROOT / "experiments/selfaware-latent-knowledge-controls"
sys.path.insert(0, str(CAT_DIR))

import caution_axis_transfer as cat  # noqa: E402
import latent_knowledge_probe as lkp  # noqa: E402

CELL_DIR = ROOT / "experiments/base-refusal-direction-under-contract"
LAYER = 35
FIT_C = 0.5
SEED = 0  # matches caution_axis_transfer.py's own default --seed / rng default

ARMS = [
    {
        "name": "base_under_contract",
        "extraction_dir": CELL_DIR / "analysis/hidden_states/base_prc_L35",
        "behavior_rows": CELL_DIR / "analysis/labels/known_rows.jsonl",
        "source": "h_base",  # raw base, no adapter
    },
    {
        "name": "clean_sft",
        "extraction_dir": ROOT / "archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-seed1-selfaware/"
                                 "hidden_states_selfaware_clean_sft_full/extraction__8dbd3f623393",
        "behavior_rows": ROOT / "archive/experiment/phase1-data/probe/analysis/"
                                 "current_selfaware_behavior_rows/clean_sft_merged/rows.jsonl",
        "source": "h_lora",
    },
    {
        "name": "sft_grpo_dpo",
        "extraction_dir": ROOT / "archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-dpo-seed1-selfaware/"
                                 "hidden_states_selfaware_clean_sft_grpo_dpo_full/extraction__00af99a2efe7",
        "behavior_rows": ROOT / "archive/experiment/phase1-data/probe/analysis/"
                                 "current_selfaware_behavior_rows/clean_sft_grpo_dpo/rows.jsonl",
        "source": "h_lora",
    },
    {
        "name": "sft_grpo_v2",
        "extraction_dir": ROOT / "archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/"
                                 "hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f",
        "behavior_rows": ROOT / "archive/experiment/phase1-data/probe/analysis/"
                                 "current_selfaware_behavior_rows/clean_sft_grpo_v2/rows.jsonl",
        "source": "h_lora",
    },
]

# Published 3-arm-only result: experiments/selfaware-latent-knowledge-controls/
# artifacts/latent_knowledge_controls/caution_axis_transfer.json
# (arms named sft/grpo_dpo/grpo_v2 there == clean_sft/sft_grpo_dpo/sft_grpo_v2 here).
PUBLISHED_TRAINED_PAIR_COS = {
    ("clean_sft", "sft_grpo_dpo"): 0.6713,
    ("clean_sft", "sft_grpo_v2"): 0.5762,
    ("sft_grpo_dpo", "sft_grpo_v2"): 0.8566,
}
PUBLISHED_PERMUTATION_FLOOR_OVERALL_MEAN = 0.0144  # mean of the 3-arm off-diag rand_cos


def known_class_breakdown(behavior_rows: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in behavior_rows.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("label") != "known":
            continue
        cell = r.get("behavior_cell")
        counts[cell] = counts.get(cell, 0) + 1
    return counts


def main() -> int:
    loaded = []
    class_conventions = {}
    for a in ARMS:
        X, y, keys = cat.load_known(a["extraction_dir"], a["behavior_rows"], layer=LAYER, source=a["source"])
        loaded.append({"name": a["name"], "X": X, "y": y, "n": len(keys), "n_pos": int(y.sum())})
        breakdown = known_class_breakdown(a["behavior_rows"])
        neg_cells = sorted(c for c in breakdown if c != "known_refused")
        class_conventions[a["name"]] = {
            "known_behavior_cell_counts": breakdown,
            "positive_class (y=1)": "known_refused",
            "negative_class (y=0)": neg_cells,
            "note": (
                "cat.load_known labels y=1 iff behavior_cell=='known_refused', y=0 for every "
                "other behavior_cell among label=='known' rows (the Section-5/caution_axis_transfer "
                "convention -- broader than known_correct_answered alone whenever known_answered_wrong "
                "rows exist)."
                if "known_answered_wrong" in breakdown else
                "No known_answered_wrong rows exist in this extraction (confirmed: base P-rc known "
                "population is known_refused/known_correct_answered only), so y=0 reduces to "
                "known_correct_answered here -- not a convention choice, the broader class is absent "
                "from the source data."
            ),
        }

    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler().fit(np.vstack([d["X"] for d in loaded]))  # shared 4-arm frame
    rng = np.random.default_rng(SEED)
    for d in loaded:
        Xw = scaler.transform(d["X"])
        d["dir"] = cat._unit_direction(Xw, d["y"], C=FIT_C)
        yshuf = d["y"].copy()
        rng.shuffle(yshuf)
        d["dir_rand"] = cat._unit_direction(Xw, yshuf, C=FIT_C)

    names = [d["name"] for d in loaded]
    cos: dict[str, float] = {}
    rand_cos: dict[str, float] = {}
    for i, di in enumerate(loaded):
        for j, dj in enumerate(loaded):
            cos[f"{names[i]}|{names[j]}"] = round(float(abs(np.dot(di["dir"], dj["dir"]))), 4)
            rand_cos[f"{names[i]}|{names[j]}"] = round(float(abs(np.dot(di["dir_rand"], dj["dir_rand"]))), 4)

    base_name = "base_under_contract"
    trained_names = ["clean_sft", "sft_grpo_dpo", "sft_grpo_v2"]
    base_vs_trained = {t: cos[f"{base_name}|{t}"] for t in trained_names}
    mean_base_vs_trained = round(float(np.mean(list(base_vs_trained.values()))), 4)

    trained_pairs: dict[str, float] = {}
    deltas: dict[str, float] = {}
    for a, b in PUBLISHED_TRAINED_PAIR_COS:
        key = f"{a}|{b}"
        val = cos.get(key, cos.get(f"{b}|{a}"))
        trained_pairs[key] = val
        deltas[key] = round(val - PUBLISHED_TRAINED_PAIR_COS[(a, b)], 4)

    off_diag_rand = [rand_cos[f"{names[i]}|{names[j]}"]
                      for i in range(len(names)) for j in range(i + 1, len(names))]
    permutation_floor_overall_mean = round(float(np.mean(off_diag_rand)), 4)

    # BR-G0 companion: held-out refuse-vs-answer AUROC of the base logistic fit, 5-fold.
    base_arm = next(d for d in loaded if d["name"] == base_name)
    auroc_seed = 0
    base_auroc = lkp.cv_auroc(base_arm["X"], base_arm["y"], folds=5, C=FIT_C, seed=auroc_seed)

    result = {
        "procedure": (
            "caution_axis_transfer.py Section-5 transfer frame (L2 logistic C=0.5 fit per "
            "checkpoint on a StandardScaler frame fit on the POOLED known-row activations of "
            "every checkpoint being compared; single label-permutation floor per checkpoint), "
            "extended from 3 to 4 arms (base_under_contract + clean_sft + sft_grpo_dpo + "
            "sft_grpo_v2). load_known() and _unit_direction() imported and called unmodified "
            "from caution_axis_transfer.py; only the pooling loop (per-arm `source`) is new."
        ),
        "layer": LAYER,
        "fit_C": FIT_C,
        "seed": SEED,
        "arms": [
            {"name": d["name"], "n_known": d["n"], "n_positive_known_refused": d["n_pos"],
             "source": a["source"]}
            for d, a in zip(loaded, ARMS)
        ],
        "class_conventions_by_checkpoint": class_conventions,
        "cosine_matrix": cos,
        "base_vs_trained_cosines": base_vs_trained,
        "mean_base_vs_trained_cosine": mean_base_vs_trained,
        "trained_pair_cosines_4arm_frame": trained_pairs,
        "trained_pair_cosines_published_3arm_frame": {
            f"{a}|{b}": v for (a, b), v in PUBLISHED_TRAINED_PAIR_COS.items()
        },
        "trained_pair_cosine_deltas_4arm_minus_published": deltas,
        "trained_pair_source_note": (
            "Published 3-arm values are experiments/selfaware-latent-knowledge-controls/artifacts/"
            "latent_knowledge_controls/caution_axis_transfer.json (arms sft/grpo_dpo/grpo_v2 == "
            "clean_sft/sft_grpo_dpo/sft_grpo_v2 here). Deltas reflect the pooled StandardScaler "
            "frame shifting when the base arm's activations join the pool, not a methodology change."
        ),
        "random_floor_matrix": rand_cos,
        "permutation_floor": {
            "method": (
                "single label-shuffle per arm (numpy Generator.shuffle), refit logistic on the "
                "shuffled labels in the SAME shared standardized frame, pairwise |cos| of the "
                "resulting per-arm random directions -- identical to caution_axis_transfer.py's "
                "own scheme. The pinned script computes exactly ONE permutation per arm (not "
                "averaged reps); this script matches that, it does not add reps."
            ),
            "rep_count": 1,
            "seed": SEED,
            "overall_mean_off_diagonal_4arm": permutation_floor_overall_mean,
            "published_overall_mean_off_diagonal_3arm": PUBLISHED_PERMUTATION_FLOOR_OVERALL_MEAN,
        },
        "br_g0_companion_base_held_out_auroc": {
            "auroc": round(base_auroc, 4), "n_folds": 5, "C": FIT_C, "seed": auroc_seed,
            "note": "StratifiedKFold, per-fold StandardScaler.fit(train)+LogisticRegression(C=0.5), "
                    "decision_function scored held-out -- lkp.cv_auroc(), unmodified.",
        },
    }

    out_path = CELL_DIR / "analysis" / "br_compare_transfer_frame.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
