"""Build the Paper 1 draft-v2 figures (fig-p1-07..09): GRPO regimen operating
points, the confidence-channel seesaw, and the internal-vs-emitted gap.

Complements build_paper1_figures.py (fig-p1-01..06, unchanged for v2).
Every number is read from a persisted artifact; the two values with no JSON
artifact (the RL-on-contrastive calibration triple) are transcribed from the
governing amendment document's result table and marked with their source.

Reads:
  experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
  experiment/phase1/eval/analysis/calibration_gap_*.json
  experiment/phase1/eval/results_amendment_{j,k,l,n}_*/**/metrics.json

Writes PNG+SVG to papers/paper-2-training-regimen/figures/.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[3]
ANALYSIS = REPO / "experiment" / "phase1" / "eval" / "analysis"
EVAL_ROOT = REPO / "experiment" / "phase1" / "eval"
FIGURES = REPO / "papers" / "paper-2-training-regimen" / "figures"

COLORS = {
    "baseline": "#5c6370",
    "pref": "#4f78a8",
    "grpo": "#b23a48",
    "stack": "#6f5f9f",
    "contrastive": "#2f6f4e",
    "chance": "#9aa0a6",
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#d9d6cd",
        "grid.linewidth": 0.6,
        "figure.dpi": 150,
    }
)


def save(fig, stem: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{stem}.png", bbox_inches="tight")
    fig.savefig(FIGURES / f"{stem}.svg", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.png/.svg")


def grouped_rows() -> dict[str, dict[str, float]]:
    """Response-confidence-contract seed-1 arms from the grouped inventory."""
    out: dict[str, dict[str, float]] = {}
    with open(ANALYSIS / "selfaware_full_run_comparison_grouped.csv") as fh:
        for row in csv.DictReader(fh):
            fam, arm = row["family"], row["normalized_arm"]
            if fam.startswith(("Amendment D", "Amendment E", "Amendment F")):
                out[arm] = {
                    "truthful": float(row["mean_truthful_pct"]),
                    "recall": float(row["mean_refusal_recall_pct"]),
                    "over_refusal": float(row["mean_over_refusal_pct"]),
                }
    return out


def calib(stem: str) -> dict[str, float]:
    r = json.load(open(ANALYSIS / f"calibration_gap_{stem}.json"))
    a = r["A_full_eval"]
    return {
        "std": a["emitted_std"],
        "auroc": a["auroc_emitted_to_appropriateness"],
        "ece": a["ece_vs_appropriateness"],
    }


def behavior(results_dir: str) -> dict[str, float]:
    m = next((EVAL_ROOT / results_dir).glob("*/metrics.json"))
    r = json.load(open(m))["metrics"]
    return {
        "truthful": r["truthful_pct"],
        "recall": r["refusal_recall_pct"],
        "over_refusal": r["over_refusal_pct"],
    }


# ---------------------------------------------------------------- fig-p1-07
def fig_07_regimen_operating_points() -> None:
    g = grouped_rows()
    pts = [
        # (arm key, label, class, label offset)
        ("clean_sft_merged", "SFT (baseline)", "baseline", (6, -14)),
        ("clean_sft_dpo", "SFT→DPO", "pref", (-12, 10)),
        ("clean_sft_kto", "SFT→KTO", "pref", (6, -4)),
        ("clean_sft_grpo_v1", "SFT→GRPO (first reward)", "grpo", (-118, 6)),
        ("clean_sft_grpo_v2", "SFT→GRPO (rebalanced)", "grpo", (12, 12)),
        ("clean_sft_dpo_grpo", "DPO→GRPO", "stack", (-92, -24)),
        ("clean_sft_grpo_dpo", "GRPO→DPO", "stack", (-78, 6)),
        ("clean_sft_kto_grpo", "KTO→GRPO", "stack", (14, -14)),
        ("clean_sft_grpo_kto", "GRPO→KTO", "stack", (8, -4)),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for key, label, cls, (dx, dy) in pts:
        r = g[key]
        ax.scatter(
            r["over_refusal"],
            r["recall"],
            s=110 if cls == "baseline" else 80,
            color=COLORS[cls],
            edgecolor="white",
            linewidth=1.2,
            zorder=3,
        )
        ax.annotate(
            f"{label}\n(truthful {r['truthful']:.1f})",
            (r["over_refusal"], r["recall"]),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=7.8,
            color="#1f2933",
            zorder=4,
        )
    ax.set_xlabel("Over-refusal on known questions (%)  ← better")
    ax.set_ylabel("Refusal recall on unknown questions (%)  better →")
    ax.set_title(
        "GRPO amplifies the abstention routine; stacks stay on its frontier\n"
        "(SelfAware, response-confidence contract, seed 1, exploratory)",
        fontsize=10.5,
    )
    ax.set_xlim(48, 82)
    ax.set_ylim(78, 100)
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=COLORS[c], label=l)
        for c, l in [
            ("baseline", "clean SFT baseline"),
            ("pref", "preference stage (DPO/KTO)"),
            ("grpo", "GRPO stage"),
            ("stack", "two-stage stacks"),
        ]
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=False)
    save(fig, "fig-p1-07-regimen-operating-points")


# ---------------------------------------------------------------- fig-p1-08
def fig_08_confidence_channel() -> None:
    arms = [
        # (display label, calibration dict, behavior dict, color)
        (
            "GRPO\n(rebal.)",
            calib("clean_sft_grpo_v2_seed1"),
            grouped_rows()["clean_sft_grpo_v2"],
            COLORS["grpo"],
        ),
        (
            "GRPO\n(proper)",
            calib("clean_sft_grpo_v3_seed1"),
            behavior(
                "results_amendment_j_response_confidence_selfaware_clean_sft_grpo_v3_seed1_full_4b"
            ),
            COLORS["grpo"],
        ),
        (
            "Contrastive\nSFT ",
            calib("contrastive_sft_seed1"),
            behavior(
                "results_amendment_k_response_confidence_selfaware_contrastive_sft_seed1_merged_full_4b"
            ),
            COLORS["contrastive"],
        ),
        (
            "Contr. SFT\n(masked)",
            calib("contrastive_masked_sft_seed1"),
            behavior(
                "results_amendment_l_response_confidence_selfaware_contrastive_masked_sft_seed1_merged_full_4b"
            ),
            COLORS["contrastive"],
        ),
        (
            "GRPO on\ncontr. base",
            # No calibration-gap JSON was emitted for this cell; the triple is
            # transcribed from the governing amendment result table
            # (AMENDMENT-N-grpo-v3-on-contrastive-sft-base.md, section 7,
            # beta=0.1 column) and cross-checked against the beta=0.05 re-run.
            {"std": 0.311, "auroc": 0.646, "ece": 0.214},
            behavior(
                "results_amendment_n_response_confidence_selfaware_grpo_on_contrastive_sft_seed1_full_4b"
            ),
            COLORS["stack"],
        ),
    ]
    labels = [a[0] for a in arms]
    colors = [a[3] for a in arms]
    x = range(len(arms))

    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9))
    fig.subplots_adjust(wspace=0.28)

    ax = axes[0]
    ax.bar(x, [a[1]["std"] for a in arms], color=colors)
    ax.axhline(0.10, color=COLORS["chance"], ls="--", lw=1)
    ax.text(0.52, 0.115, "collapse gate (0.10)", fontsize=7.5, color="#5c6370")
    ax.set_title("Emitted-confidence spread (std)", fontsize=10)
    ax.set_ylabel("std of emitted confidence")

    ax = axes[1]
    ax.bar(x, [a[1]["auroc"] for a in arms], color=colors)
    ax.axhline(0.5, color=COLORS["chance"], ls="--", lw=1)
    ax.text(4.45, 0.508, "chance", fontsize=7.5, color="#5c6370", ha="right")
    ax.set_ylim(0.4, 0.75)
    ax.set_title("Calibration (AUROC → appropriateness)", fontsize=10)

    ax = axes[2]
    ax.bar(x, [a[2]["over_refusal"] for a in arms], color=colors)
    ax.set_ylim(0, 100)
    ax.set_title("Behavioral cost (over-refusal %)", fontsize=10)

    for ax in axes:
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, fontsize=7.0)

    fig.suptitle(
        "The confidence channel and behavior fail in opposite arms: RL rewards leave confidence "
        "collapsed at chance;\nsupervision calibrates it at behavioral cost; RL on the calibrated "
        "base keeps calibration but worsens behavior  (seed 1, exploratory)",
        fontsize=10,
        y=1.09,
    )
    save(fig, "fig-p1-08-confidence-channel")


# ---------------------------------------------------------------- fig-p1-09
def fig_09_knows_vs_says() -> None:
    r = json.load(open(ANALYSIS / "calibration_gap_clean_sft_grpo_v2_seed1.json"))
    b = r["B_internal_vs_emitted"]
    internal, emitted = b["auroc_internal_to_known"], b["auroc_emitted_to_known"]

    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    bars = ax.bar(
        [0, 1],
        [internal, emitted],
        width=0.55,
        color=["#2f6f4e", "#b23a48"],
    )
    ax.axhline(0.5, color=COLORS["chance"], ls="--", lw=1)
    ax.text(1.28, 0.512, "chance", fontsize=8, color="#5c6370")
    for bar, v in zip(bars, [internal, emitted]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.015,
            f"{v:.3f}",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )
    ax.set_xticks([0, 1])
    ax.set_xticklabels(
        [
            "Linear probe of hidden states\n(layer 35, held-out)",
            "Model's own emitted\nconfidence",
        ],
        fontsize=9,
    )
    ax.set_ylim(0.4, 1.05)
    ax.set_ylabel("AUROC vs known/unknown boundary")
    ax.set_title(
        "The model knows more than it says\n(same checkpoint, same evaluation rows)",
        fontsize=11,
    )
    save(fig, "fig-p1-09-knows-vs-says")


if __name__ == "__main__":
    fig_07_regimen_operating_points()
    fig_08_confidence_channel()
    fig_09_knows_vs_says()
