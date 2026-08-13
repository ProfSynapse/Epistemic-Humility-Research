"""Build the Paper 1 draft-v2 figures (fig-p1-07..10): GRPO regimen operating
points, the confidence-channel seesaw, the internal-vs-emitted gap, and the
three-seed GRPO replication.

Complements build_paper1_figures.py (fig-p1-01..06, unchanged for v2).
Every number is read from a persisted artifact; the two values with no JSON
artifact (the RL-on-contrastive calibration triple) are transcribed from the
governing amendment document's result table and marked with their source, and
the three-seed mean/CI values (fig-p1-10) are transcribed from the manuscript's
own already-published three-seed table since no committed machine-readable
per-seed artifact survives (see fig_10_three_seed_replication docstring).

Reads:
  archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
  archive/experiment/phase1/eval/analysis/calibration_gap_*.json
  archive/experiment/phase1/eval/results_amendment_{j,k,l,n}_*/**/metrics.json

Writes PNG+SVG to papers/paper-2-training-regimen/figures/.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from ideal_zone import IDEAL_GREEN_RGB, IDEAL_QUADRANT_ALPHA

REPO = Path(__file__).resolve().parents[3]
ANALYSIS = REPO / "archive" / "experiment" / "phase1" / "eval" / "analysis"
EVAL_ROOT = REPO / "archive" / "experiment" / "phase1" / "eval"
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


def _shade_ideal_quadrant(ax) -> None:
    """Flat-fill the panel's own upper-left quadrant (low over-refusal, high
    recall) in translucent green: no fade, no marker, no boundary line drawn
    at the midline itself. The quadrant boundary is the midpoint of
    whatever range is actually plotted on each axis, so it moves with a
    zoomed panel rather than pointing at a fixed data value that may sit
    outside the view. Restores the caller's axis limits afterward so the
    shading rectangle cannot expand the view via autoscale.
    """
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    x_mid = (xlim[0] + xlim[1]) / 2
    y_mid = (ylim[0] + ylim[1]) / 2
    r, g, b = (c / 255 for c in IDEAL_GREEN_RGB)
    ax.add_patch(
        plt.Rectangle(
            (xlim[0], y_mid),
            x_mid - xlim[0],
            ylim[1] - y_mid,
            facecolor=(r, g, b, IDEAL_QUADRANT_ALPHA),
            edgecolor="none",
            zorder=0,
        )
    )
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)


# ---------------------------------------------------------------- fig-p1-07
def fig_07_regimen_operating_points() -> None:
    g = grouped_rows()
    pts = [
        # (arm key, label, class, marker, label offset). Marker encodes stage
        # order for the stacks: "^" is GRPO applied first, "s" is GRPO applied
        # second, so a reader reads the order off the shape without relying on
        # the crowded label text alone.
        ("clean_sft_merged", "SFT (baseline)", "baseline", "o", (6, -14)),
        ("clean_sft_dpo", "SFT→DPO", "pref", "o", (-16, 20)),
        ("clean_sft_kto", "SFT→KTO", "pref", "o", (8, -6)),
        ("clean_sft_grpo_v2", "SFT→GRPO", "grpo", "o", (14, 22)),
        ("clean_sft_dpo_grpo", "DPO→GRPO", "stack", "s", (-48, 26)),
        ("clean_sft_grpo_dpo", "GRPO→DPO", "stack", "^", (-64, -26)),
        ("clean_sft_kto_grpo", "KTO→GRPO", "stack", "s", (42, 14)),
        ("clean_sft_grpo_kto", "GRPO→KTO", "stack", "^", (-14, -32)),
    ]
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for key, label, cls, marker, (dx, dy) in pts:
        r = g[key]
        ax.scatter(
            r["over_refusal"],
            r["recall"],
            marker=marker,
            s=110 if cls == "baseline" else 90,
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
            arrowprops=dict(arrowstyle="-", color=COLORS[cls], lw=0.7, alpha=0.6, shrinkA=0, shrinkB=5),
        )
    ax.set_xlabel("Over-refusal on known questions (%)")
    ax.set_ylabel("Refusal recall on unknown questions (%)")
    ax.set_title(
        "GRPO amplifies the abstention routine; stacks stay on its frontier\n"
        "(SelfAware, response-confidence contract, seed 1, exploratory)",
        fontsize=10.5,
    )
    ax.set_xlim(48, 82)
    ax.set_ylim(78, 100)
    _shade_ideal_quadrant(ax)
    handles = [
        plt.Line2D([], [], marker="o", ls="", color=COLORS["baseline"], label="clean SFT baseline"),
        plt.Line2D([], [], marker="o", ls="", color=COLORS["pref"], label="preference stage (DPO/KTO)"),
        plt.Line2D([], [], marker="o", ls="", color=COLORS["grpo"], label="GRPO stage"),
        plt.Line2D([], [], marker="^", ls="", color=COLORS["stack"], label="stack, GRPO first"),
        plt.Line2D([], [], marker="s", ls="", color=COLORS["stack"], label="stack, GRPO second"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=8, frameon=False)
    save(fig, "fig-p1-07-regimen-operating-points")


# ---------------------------------------------------------------- fig-p1-10
# Three-seed mean [95% CI] for the five GRPO-touching arms, response-confidence
# contract. Transcribed from papers/paper-2-training-regimen/manuscript.md
# (Section 4.3 three-seed table, lines 565-571), which is itself the paper's
# own already-published, red-team-reviewed rendering of
# experiments/grpo-three-seed-confirmatory/NOTEBOOK.md:1780-1790 (G3
# deliverable). No committed machine-readable per-seed artifact survives this
# transcription: seed-2/3 raw metrics.json files are uncommitted local scratch
# (analysis/g3_three_seed_intervals.py header, same experiment, documents the
# gap), and the CI construction is a percentile bootstrap bounded by the three
# seed-level values (NOTEBOOK.md:1778), not an inferential interval.
THREE_SEED_GRPO_TOUCHING = {
    "clean_sft_grpo_v2": {"recall": (94.25, 93.41, 95.06), "over_refusal": (67.35, 66.62, 68.68)},
    "clean_sft_dpo_grpo": {"recall": (93.41, 92.54, 94.38), "over_refusal": (65.26, 64.66, 65.81)},
    "clean_sft_kto_grpo": {"recall": (92.99, 92.54, 93.31), "over_refusal": (65.70, 64.23, 66.50)},
    "clean_sft_grpo_dpo": {"recall": (94.25, 93.31, 94.77), "over_refusal": (65.48, 63.63, 66.84)},
    "clean_sft_grpo_kto": {"recall": (91.08, 89.63, 91.86), "over_refusal": (61.90, 60.59, 64.01)},
}


def fig_10_three_seed_replication() -> None:
    """Seed-1-only operating point vs. three-seed mean [95% CI] for the five
    GRPO-touching arms (SelfAware, response-confidence contract). Seed-1
    points come from the same tracked grouped_rows() CSV that fig-p1-07 reads;
    three-seed mean/CI values are the transcribed table above."""
    g = grouped_rows()
    arms = [
        ("clean_sft_grpo_v2", "SFT→GRPO", COLORS["grpo"], (30, 28)),
        ("clean_sft_dpo_grpo", "DPO→GRPO", COLORS["stack"], (-102, -10)),
        ("clean_sft_kto_grpo", "KTO→GRPO", COLORS["stack"], (58, -20)),
        ("clean_sft_grpo_dpo", "GRPO→DPO", COLORS["stack"], (-102, 18)),
        ("clean_sft_grpo_kto", "GRPO→KTO", COLORS["stack"], (18, -34)),
    ]
    fig, ax = plt.subplots(figsize=(8.4, 6.6))
    x_vals: list[float] = []
    y_vals: list[float] = []
    for key, label, color, (dx, dy) in arms:
        s1 = g[key]
        three = THREE_SEED_GRPO_TOUCHING[key]
        r_mean, r_lo, r_hi = three["recall"]
        o_mean, o_lo, o_hi = three["over_refusal"]
        x_vals.extend([o_lo, o_hi, s1["over_refusal"]])
        y_vals.extend([r_lo, r_hi, s1["recall"]])
        # three-seed mean +/- bootstrap-CI error bars (asymmetric, bounded by
        # the three seed-level values per NOTEBOOK.md:1778)
        ax.errorbar(
            o_mean,
            r_mean,
            xerr=[[o_mean - o_lo], [o_hi - o_mean]],
            yerr=[[r_mean - r_lo], [r_hi - r_mean]],
            fmt="D",
            color=color,
            ecolor=color,
            elinewidth=1.3,
            capsize=4,
            markersize=8,
            markeredgecolor="white",
            markeredgewidth=1.0,
            zorder=4,
        )
        # seed-1-only point (smaller, faint), connected to the 3-seed mean
        ax.plot(
            [s1["over_refusal"], o_mean],
            [s1["recall"], r_mean],
            ls=":",
            lw=1.0,
            color=color,
            alpha=0.55,
            zorder=2,
        )
        ax.scatter(
            s1["over_refusal"],
            s1["recall"],
            s=40,
            facecolor="white",
            edgecolor=color,
            linewidth=1.3,
            zorder=3,
        )
        ax.annotate(
            label,
            (o_mean, r_mean),
            textcoords="offset points",
            xytext=(dx, dy),
            fontsize=8.2,
            color="#1f2933",
            zorder=5,
            arrowprops=dict(arrowstyle="-", color=color, lw=0.7, alpha=0.6, shrinkA=0, shrinkB=5),
        )
    x_pad = (max(x_vals) - min(x_vals)) * 0.18
    y_pad = (max(y_vals) - min(y_vals)) * 0.18
    ax.set_xlim(min(x_vals) - x_pad, max(x_vals) + x_pad)
    ax.set_ylim(min(y_vals) - y_pad, max(y_vals) + y_pad)
    _shade_ideal_quadrant(ax)
    ax.set_xlabel("Over-refusal on known questions (%)")
    ax.set_ylabel("Refusal recall on unknown questions (%)")
    ax.set_title(
        "The three-seed replication holds: GRPO-touching arms stay shifted,\n"
        "not just the seed-1 point (SelfAware, response-confidence contract, exploratory)",
        fontsize=10.5,
    )
    handles = [
        plt.Line2D(
            [], [], marker="D", ls="", color=COLORS["grpo"], markeredgecolor="white",
            markersize=8, label="3-seed mean ± bootstrap CI (seeds 1-3)",
        ),
        plt.Line2D(
            [], [], marker="o", ls="", markerfacecolor="white", markeredgecolor=COLORS["grpo"],
            markersize=6, label="seed 1 only (single-seed point)",
        ),
    ]
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=False)
    fig.subplots_adjust(bottom=0.22)
    fig.text(
        0.5,
        0.02,
        "Exploratory response-confidence track; never pooled with the plain-answer headline (Section 4.1).\n"
        "n=3 seeds per arm; CI is a descriptive seed-level bootstrap bounded by the seed min/max, not an inferential interval.",
        ha="center",
        fontsize=7.5,
        color="#5c6370",
    )
    save(fig, "fig-p1-10-three-seed-replication")


# ---------------------------------------------------------------- fig-p1-08
def fig_08_confidence_channel() -> None:
    arms = [
        # (display label, calibration dict, behavior dict, color)
        (
            "GRPO",
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
    fig_10_three_seed_replication()
    fig_08_confidence_channel()
    fig_09_knows_vs_says()
