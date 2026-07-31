#!/usr/bin/env python3
"""Build Figure C3 (recall/over-refusal trade) and Figure C4 (scale vs
training) for paper 1 (taxonomy/synthesis paper).

Data sources (verified against these files before plotting; see the
build report for exact source line numbers):
  - meta-analysis/evidence/idk-method-reanalysis.csv
  - meta-analysis/evidence/abstentionbench-reanalysis.md

Deterministic: no randomness, fixed rcParams, matplotlib only (no seaborn).
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

REPO_ROOT = Path("/home/profsynapse/code/Epistemic-Humility-Research")
EVIDENCE_DIR = REPO_ROOT / "meta-analysis" / "evidence"
HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parent / "figures"

# Colorblind-safe categorical palette (dataviz skill reference palette,
# fixed hue order; validated via scripts/validate_palette.js).
PALETTE = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
}

RC = {
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.8,
    "axes.edgecolor": "#333333",
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.5,
    "grid.alpha": 0.7,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "svg.fonttype": "none",
}


def save(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{stem}.pdf")
    fig.savefig(FIG_DIR / f"{stem}.png")
    plt.close(fig)


def make_fig_c3() -> None:
    """Scatter: refusal recall (unknown) vs over-refusal (known), 5 Cheng
    IDK methods on Llama-2-7b-chat. Source: idk-method-reanalysis.csv."""
    csv_path = EVIDENCE_DIR / "idk-method-reanalysis.csv"
    rows = {}
    with open(csv_path, newline="") as f:
        for r in csv.DictReader(f):
            rows[r["method"]] = r

    order = ["idk-sft", "idk-dpo", "idk-ppo", "idk-bon", "idk-hir"]
    labels = {
        "idk-sft": "Idk-SFT",
        "idk-dpo": "Idk-DPO",
        "idk-ppo": "Idk-PPO",
        "idk-bon": "Idk-BoN",
        "idk-hir": "Idk-HIR",
    }
    colors = [PALETTE["blue"], PALETTE["orange"], PALETTE["aqua"],
              PALETTE["yellow"], PALETTE["magenta"]]
    markers = ["o", "s", "^", "D", "v"]

    fig, ax = plt.subplots(figsize=(3.5, 3.0))

    label_offsets = {
        "idk-sft": (5, 4),
        "idk-dpo": (5, -10),
        "idk-ppo": (5, 4),
        "idk-bon": (5, -12),
        "idk-hir": (-38, 4),
    }

    for method, color, marker in zip(order, colors, markers):
        r = rows[method]
        x = float(r["over_refusal_pct"])
        y = float(r["refusal_recall_pct"])
        ax.scatter(x, y, s=42, color=color, marker=marker,
                   edgecolor="white", linewidth=0.6, zorder=3,
                   label=labels[method])
        dx, dy = label_offsets[method]
        ax.annotate(labels[method], (x, y), xytext=(dx, dy),
                    textcoords="offset points", fontsize=7,
                    color="#222222")

    ax.set_xlabel("Over-refusal on known questions (%)")
    ax.set_ylabel("Refusal recall on unknown questions (%)")
    ax.set_xlim(5, 55)
    ax.set_ylim(60, 95)

    # Ideal-direction annotation: top-left is the desired corner.
    ax.annotate(
        "ideal",
        xy=(8, 92), xytext=(8, 92),
        fontsize=7, color="#666666", style="italic",
        ha="left", va="top",
    )
    ax.annotate(
        "", xy=(9, 90), xytext=(16, 83),
        arrowprops=dict(arrowstyle="->", color="#999999", lw=0.9,
                         shrinkA=0, shrinkB=0),
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    save(fig, "fig-c3-tradeoff")


def parse_scale_and_dpo_deltas() -> tuple[float, float]:
    """Parse the B2 scale-sweep table and B1 8B-ladder DPO-vs-SFT row from
    abstentionbench-reanalysis.md and recompute the two deltas rather than
    hardcoding them."""
    md_path = EVIDENCE_DIR / "abstentionbench-reanalysis.md"
    text = md_path.read_text().splitlines()

    scale_medians = {}
    in_scale_table = False
    for line in text:
        if line.startswith("### Llama 3.1 Instruct"):
            in_scale_table = True
            continue
        if in_scale_table:
            if line.startswith("| Llama 3.1"):
                parts = [p.strip() for p in line.strip("|").split("|")]
                name, recall, _ = parts
                scale_medians[name] = float(recall)
            elif line.startswith("- Recall monotonically"):
                break

    scale_delta = (scale_medians["Llama 3.1 405B Instruct"]
                    - scale_medians["Llama 3.1 8B Instruct"])

    dpo_delta = None
    in_8b_ladder = False
    for line in text:
        if line.startswith("### 8B ladder"):
            in_8b_ladder = True
            continue
        if in_8b_ladder:
            if line.startswith("| DPO vs SFT | recall |"):
                parts = [p.strip() for p in line.strip("|").split("|")]
                dpo_delta = float(parts[2])
                break
            if line.startswith("### 70B ladder"):
                break

    assert dpo_delta is not None, "DPO vs SFT 8B recall row not found"
    return scale_delta, dpo_delta


def make_fig_c4() -> None:
    """Two-bar comparison: 50x scale (Llama 3.1 Instruct 8B->405B) vs one
    DPO stage (Tulu-3 8B) median abstention recall delta. Source:
    abstentionbench-reanalysis.md, parsed at build time (not hardcoded)."""
    scale_delta, dpo_delta = parse_scale_and_dpo_deltas()

    labels = ["50x parameters\n(Llama 3.1 Instruct\n8B to 405B)",
              "One DPO stage\n(Tulu-3 8B)"]
    values = [scale_delta, dpo_delta]
    colors = [PALETTE["blue"], PALETTE["orange"]]

    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    x = range(len(values))
    bars = ax.bar(x, values, color=colors, width=0.55, zorder=3,
                   edgecolor="white", linewidth=0.6)

    for xi, v in zip(x, values):
        ax.annotate(f"+{v:.2f}", (xi, v), xytext=(0, 4),
                    textcoords="offset points", ha="center",
                    fontsize=8, color="#222222")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Median abstention recall delta\n(AbstentionBench)")
    ax.set_ylim(0, max(values) * 1.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x")
    fig.tight_layout()
    save(fig, "fig-c4-scale-vs-training")


def main() -> None:
    plt.rcParams.update(RC)
    make_fig_c3()
    scale_delta, dpo_delta = parse_scale_and_dpo_deltas()
    make_fig_c4()
    print(f"scale_delta(8B->405B Instruct) = {scale_delta:.4f}")
    print(f"dpo_delta(8B DPO vs SFT)       = {dpo_delta:.4f}")
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()
