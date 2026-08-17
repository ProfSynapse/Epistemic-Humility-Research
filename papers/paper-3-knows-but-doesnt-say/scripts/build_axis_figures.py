#!/usr/bin/env python3
"""Paper 3, Result 2 (Section 5) figures — two-axis geometry + axis stability.

Standalone, reproducible build script. Reads ONLY committed / on-disk-present
analysis artifacts (paths below); writes PNGs to this scratchpad directory.
No question text or generation text is read into anything that gets printed,
plotted, or written out -- only `behavior_cell` (a taxonomy label) and the
L35 h_lora hidden-state tensors are used from the per-row source.

FIGURE A — fig-p3-08-two-axis-geometry.png
  Per-question projection onto the known-unknown axis (x) vs the refusal
  axis (y), colored by outcome group, on the clean_sft_grpo_v2 (seed 1)
  checkpoint -- the same checkpoint and the same mass-mean recipe that
  produces manuscript.md Section 5's headline numbers (raw cos -0.83,
  residual/perp fraction 0.557).

  Source data:
    archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows/
      clean_sft_grpo_v2/rows.jsonl
      (1233 rows; only `row_key`, `behavior_cell`,
       source_arms.clean_sft_grpo_v2.correct are read)
    archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/
      hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f/
      *__h_lora.safetensors  (L35, 2560-d, final-prompt-token residual)

  This is the exact input pair named by the paper's own provenance
  reconstruction script, papers/paper-3-knows-but-doesnt-say/analysis/
  provenance/p3_section5_provenance_20260704/reconstruct_section5_geometry.py
  (which cites the legacy archive/experiment/phase1/probe/
  paper3_section5_geometry.py as the paper's originating script). Both rows.jsonl
  and the extraction dir are covered by .gitignore (archive/experiment/
  phase1-data/) but are PRESENT ON DISK in the canonical checkout and are the
  artifacts the paper's own reconstruction cites by content -- the
  reconstruction script's hardcoded path prefix (`.../phase1/probe/...`)
  is stale relative to the post-reorg location (`.../phase1-data/probe/...`)
  used here, confirmed by identical cell counts (168/373/676/15/1) and a
  reproduced-geometry audit below.

  Direction recipe (mass-mean, matching reconstruct_section5_geometry.py
  geometry_full(), full sample, no subsampling):
    doubt (known-unknown axis)   = unit(mean(known_correct_answered)
                                         - mean(unknown_refused))
    caution (refusal axis)       = unit(mean(known_refused)
                                         - mean(known_correct_answered))
  Both fit once on the full 1233-row sample; every row (including the 16
  wrong-answered rows outside the 3-cell caution contrast) is then projected
  onto both unit directions for the scatter.

  Outcome-group color mapping (from behavior_cell):
    correct  = known_correct_answered           (n=373)
    refused  = known_refused  (over-refusal)     (n=168)
    unknown  = unknown_refused (appropriate refusal) (n=676)
    wrong    = known_answered_wrong + unknown_answered_wrong (n=15+1=16)

FIGURE B — fig-p3-09-axis-stability.png
  Refusal-axis cross-checkpoint cosine similarity (to the GRPO-v2 reference
  fit), i.e. manuscript.md Section 5 "The refusal axis is shared across
  training regimens" (mean cross-regimen |cos| 0.701 vs random floor 0.014).

  Source data (committed, git-tracked):
    experiments/selfaware-latent-knowledge-controls/artifacts/
      latent_knowledge_controls/caution_axis_transfer.json
      (cosine_matrix, random_floor_matrix, mean_cross_cosine,
       mean_random_floor, verdict)

Run:
    python3 build_p3_axis_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from safetensors.numpy import load_file

REPO = Path("/home/profsynapse/code/Epistemic-Humility-Research")
OUT_DIR = Path(__file__).resolve().parent

ROWS = (
    REPO
    / "archive/experiment/phase1-data/probe/analysis/current_selfaware_behavior_rows"
    / "clean_sft_grpo_v2/rows.jsonl"
)
EXTRACTION = (
    REPO
    / "archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware"
    / "hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f"
)
LAYER = "L35"

TRANSFER_JSON = (
    REPO
    / "experiments/selfaware-latent-knowledge-controls/artifacts"
    / "latent_knowledge_controls/caution_axis_transfer.json"
)

# Published Section 5 headline numbers (manuscript.md Section 5), for the
# reproduction audit only -- never overwritten, only compared against.
PUBLISHED_RAW_COS = -0.83
PUBLISHED_RESIDUAL_FRACTION = 0.557

# --- house style (papers/paper-3-knows-but-doesnt-say/scripts/build_figures.py) ---
C = {
    "green":  "#2f6f4e",
    "blue":   "#4f78a8",
    "orange": "#b85c38",
    "purple": "#6f5f9f",
    "gray":   "#5c6370",
    "grid":   "#d9d6cd",
    "text":   "#1f2933",
    "gate":   "#c0392b",
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.edgecolor": C["text"],
    "axes.linewidth": 0.9,
    "text.color": C["text"],
    "axes.labelcolor": C["text"],
    "xtick.color": C["text"],
    "ytick.color": C["text"],
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def _style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=C["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


def _save(fig, name: str, suptitle: str | None = None, top: float = 0.90):
    if suptitle:
        fig.suptitle(suptitle, fontsize=13, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, top))
    else:
        fig.tight_layout()
    fig.savefig(OUT_DIR / f"{name}.png", dpi=200)
    plt.close(fig)
    print(f"wrote {name}.png")


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def load_rows_and_states():
    """Load behavior_cell + L35 h_lora vector for every row with a tensor on disk.

    Only `row_key`/`probe_pool_row_key` (identifiers) and `behavior_cell`
    (taxonomy label) are retained; `question`/`answer_text`/generation text
    in rows.jsonl is read by json.loads but never stored or printed.
    """
    keys, cells, X = [], [], []
    n_missing = 0
    with open(ROWS) as f:
        for line in f:
            r = json.loads(line)
            key = (r.get("probe_pool_row_key") or r["row_key"]).replace("::", "__")
            p = EXTRACTION / f"{key}__h_lora.safetensors"
            if not p.exists():
                n_missing += 1
                continue
            X.append(load_file(str(p))[LAYER].astype(np.float64).reshape(-1))
            cells.append(r["behavior_cell"])
            keys.append(key)
    return np.stack(X), np.asarray(cells), keys, n_missing


def fig_a_two_axis_geometry():
    X, cells, keys, n_missing = load_rows_and_states()
    n = len(X)
    print(f"[Fig A] loaded {n} rows ({n_missing} missing tensors)")

    kr = X[cells == "known_refused"]
    ka = X[cells == "known_correct_answered"]
    ur = X[cells == "unknown_refused"]
    print(f"[Fig A] cell counts: known_refused={len(kr)} "
          f"known_correct_answered={len(ka)} unknown_refused={len(ur)}")

    doubt = unit(ka.mean(0) - ur.mean(0))          # known-unknown axis
    caution_raw = kr.mean(0) - ka.mean(0)           # refusal axis (raw)
    caution = unit(caution_raw)

    # Reproduction audit against manuscript.md Section 5.
    raw_cos = float(unit(caution_raw) @ doubt)
    perp = caution_raw - (caution_raw @ doubt) * doubt
    residual_fraction = float(np.linalg.norm(perp) / np.linalg.norm(caution_raw))
    print(f"[Fig A] audit: raw_cos={raw_cos:.4f} (published {PUBLISHED_RAW_COS}), "
          f"residual_fraction={residual_fraction:.4f} "
          f"(published {PUBLISHED_RESIDUAL_FRACTION})")
    assert abs(raw_cos - PUBLISHED_RAW_COS) < 0.01, "raw cosine does not reproduce"
    assert abs(residual_fraction - PUBLISHED_RESIDUAL_FRACTION) < 0.01, \
        "residual fraction does not reproduce"

    x = X @ doubt
    y = X @ caution

    group_map = {
        "known_correct_answered": "correct",
        "known_refused": "refused",
        "unknown_refused": "unknown",
        "known_answered_wrong": "wrong",
        "unknown_answered_wrong": "wrong",
    }
    groups = np.array([group_map[c] for c in cells])

    order = ["correct", "unknown", "refused", "wrong"]
    colors = {"correct": C["green"], "unknown": C["blue"],
              "refused": C["orange"], "wrong": C["gray"]}
    labels = {
        "correct": "known, correctly answered",
        "unknown": "unknown, refused (appropriate)",
        "refused": "known, refused (over-refusal)",
        "wrong": "answered, wrong",
    }
    sizes = {"correct": 14, "unknown": 14, "refused": 16, "wrong": 30}
    alphas = {"correct": 0.55, "unknown": 0.45, "refused": 0.65, "wrong": 0.9}

    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    for g in order:
        m = groups == g
        ax.scatter(x[m], y[m], s=sizes[g], color=colors[g], alpha=alphas[g],
                   linewidth=0, zorder=3, label=f"{labels[g]}  (n={m.sum()})")

    ax.axhline(0, color=C["grid"], lw=0.9, zorder=1)
    ax.axvline(0, color=C["grid"], lw=0.9, zorder=1)
    ax.set_xlabel("known-unknown axis projection  (higher = more known)")
    ax.set_ylabel("refusal axis projection  (higher = more refuse-like)")
    ax.set_title("A graded knowledge axis, a separable refusal decision", fontsize=12.5)
    _style(ax)
    ax.grid(axis="x", color=C["grid"], linewidth=0.8, zorder=0)
    ax.legend(frameon=False, fontsize=8.8, loc="upper left", markerscale=1.6)

    ax.text(0.02, 0.02,
            f"clean SFT → GRPO-v2 (seed 1), L35 h_lora, n={n}\n"
            f"raw cos(refusal, known-unknown) = {raw_cos:.2f}  "
            f"|  refusal-axis residual fraction = {residual_fraction:.3f}",
            transform=ax.transAxes, fontsize=8, color=C["gray"], va="bottom")

    _save(fig, "fig-p3-08-two-axis-geometry",
          suptitle="Result 2 — the internal signal is two axes, not one")

    return {
        "n_rows": n,
        "n_missing": n_missing,
        "cell_counts": {"known_refused": int(len(kr)), "known_correct_answered": int(len(ka)),
                        "unknown_refused": int(len(ur))},
        "raw_cos": raw_cos,
        "residual_fraction": residual_fraction,
    }


def fig_b_axis_stability():
    with open(TRANSFER_JSON) as f:
        d = json.load(f)
    print(f"[Fig B] source verdict: {d['verdict']} "
          f"mean_cross_cosine={d['mean_cross_cosine']} "
          f"mean_random_floor={d['mean_random_floor']}")

    # All three checkpoint pairs, matching the manuscript's Figure 4 caption
    # (mean cross-regimen |cos| 0.701 vs mean random floor 0.014).
    pairs = [("sft", "grpo_dpo"), ("sft", "grpo_v2"), ("grpo_dpo", "grpo_v2")]
    name = {"sft": "SFT", "grpo_dpo": "GRPO-DPO", "grpo_v2": "GRPO-v2"}
    pair_labels = [f"{name[a]} ↔ {name[b]}" for a, b in pairs]
    cosines = [abs(d["cosine_matrix"][f"{a}|{b}"]) for a, b in pairs]
    mean_cos = d["mean_cross_cosine"]
    mean_floor = d["mean_random_floor"]

    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    x = np.arange(len(pairs))
    bars = ax.bar(x, cosines, width=0.55,
                   color=[C["blue"], C["purple"], C["green"]], zorder=3)
    for b, v in zip(bars, cosines):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", va="bottom", fontsize=9.5, color=C["text"])

    label_box = dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5)
    ax.axhline(mean_cos, ls=":", lw=1.2, color=C["gray"], zorder=2)
    ax.text(1.0, mean_cos + 0.02,
            f"mean cross-regimen |cos| = {mean_cos:.3f}",
            fontsize=8.5, color=C["gray"], ha="center", va="bottom",
            bbox=label_box, zorder=4)

    ax.axhline(mean_floor, ls="--", lw=1.2, color=C["gate"], zorder=2)
    ax.text(1.0, mean_floor + 0.025,
            f"random-direction floor = {mean_floor:.3f}",
            fontsize=8.5, color=C["gate"], ha="center", va="bottom",
            bbox=label_box, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(pair_labels)
    ax.set_ylabel("|cosine| between refusal directions")
    ax.set_ylim(0, 1.0)
    ax.set_title("The refusal axis is shared across training regimens", fontsize=12.5)
    _style(ax)

    ax.text(0.02, 0.98,
            f"L{d['layer']} {d['source']}; refusal direction fit independently "
            f"per checkpoint",
            transform=ax.transAxes, fontsize=8, color=C["gray"], va="top")

    _save(fig, "fig-p3-09-axis-stability",
          suptitle="Result 2 — one refusal mechanism, not one per training run")

    return {
        "pairwise_cosines": dict(zip(pair_labels, cosines)),
        "mean_cross_cosine": mean_cos,
        "mean_random_floor": mean_floor,
        "verdict": d["verdict"],
    }


def main():
    a = fig_a_two_axis_geometry()
    b = fig_b_axis_stability()
    print("\n=== SUMMARY ===")
    print(json.dumps({"figure_a": a, "figure_b": b}, indent=2))


if __name__ == "__main__":
    main()
