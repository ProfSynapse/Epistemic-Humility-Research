#!/usr/bin/env python3
"""Paper 3 figures — "Knows but Doesn't Say".

Generates publication figures into papers/paper-3-knows-but-doesnt-say/figures/ as both .svg
(vector) and .png (raster, for ![[...]] embeds), styled to match the Paper 1/2
muted-academic palette (build_paper1_figures.py COLORS).

Every constant below is a summary value with its provenance in a comment, in the
style of papers/paper-1-taxonomy-framework/analysis/prisma_figure.py. Regenerate with:

    python3 papers/paper-3-knows-but-doesnt-say/scripts/build_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

FIG_DIR = Path(__file__).resolve().parents[1] / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
REPO_ROOT = Path(__file__).resolve().parents[3]

# --- palette (from build_paper1_figures.py COLORS + PNG_COLORS) --------------
C = {
    "green":  "#2f6f4e",   # K / internal / calibration / appropriate
    "blue":   "#4f78a8",   # L / known
    "orange": "#b85c38",   # stated / behavior / unknown / inappropriate
    "purple": "#6f5f9f",   # GRPO-on-K (Amendment N)
    "gray":   "#5c6370",   # base / muted
    "grid":   "#d9d6cd",
    "text":   "#1f2933",
    "gate":   "#c0392b",   # gate / falsifier reference lines
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


def _save(fig, name: str, suptitle: str | None = None, top: float = 0.93):
    if suptitle:
        fig.suptitle(suptitle, fontsize=13, fontweight="bold")
        fig.tight_layout(rect=(0, 0, 1, top))
    else:
        fig.tight_layout()
    fig.savefig(FIG_DIR / f"{name}.svg")
    fig.savefig(FIG_DIR / f"{name}.png", dpi=200)
    plt.close(fig)
    print(f"wrote {name}.svg + .png")


def _bar_labels(ax, bars, fmt="{:.2f}", dy=0.0):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h),
                ha="center", va="bottom", fontsize=9.5, color=C["text"])


# ============================================================ Figure 1 — the gap
def fig1_internal_vs_stated():
    # Provenance: paper §4 / Abstract. Internal probe L35 known/unknown
    # AUROC 0.997 [experiments/selfaware-latent-knowledge-controls/artifacts/latent_knowledge_controls/c2_sft.json];
    # stated->appropriateness AUROC ~0.52. Left panel unchanged by the
    # wrong-answer-cell-power-fix re-estimate (manuscript.md: "headline 0.997
    # known/unknown readout untouched").
    #
    # Right panel: powered re-estimate on 420 correct / 360 wrong deployment-
    # rendered rows, raw accounting (gate E3 raw sub-check; the reweighted-to-
    # base-rate accounting flips sign and is reported in prose only, not this
    # panel) [experiments/wrong-answer-cell-power-fix/analysis-committed/real_run_results.md,
    # grpov2 primary/gated: A5 internal ECE raw 0.0474, A6 emitted ECE raw
    # 0.2847]. Supersedes the original n=16 estimate (ECE 0.004 / 0.142); see
    # manuscript.md:346-397 (Figure 1 caption and its regeneration note).
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(8.4, 4.2))

    labels = ["Internal\n(probe, L35)", "Stated\n(emitted number)"]
    cols = [C["green"], C["orange"]]

    bars = axL.bar(labels, [0.997, 0.52], color=cols, width=0.6, zorder=3)
    axL.axhline(0.5, ls="--", lw=1.1, color=C["gray"], zorder=2)
    axL.text(1.42, 0.505, "chance", fontsize=8.5, color=C["gray"], ha="right", va="bottom")
    axL.set_ylim(0, 1.05)
    axL.set_ylabel("AUROC (separates known / unknown)")
    axL.set_title("Discrimination")
    _style(axL); _bar_labels(axL, bars)

    bars2 = axR.bar(labels, [0.0474, 0.2847], color=cols, width=0.6, zorder=3)
    axR.set_ylim(0, 0.32)
    axR.set_ylabel("Expected calibration error (lower = better)")
    axR.set_title("Calibration error (powered re-estimate, raw)")
    _style(axR); _bar_labels(axR, bars2, fmt="{:.3f}")

    _save(fig, "fig-p2-01-internal-vs-stated-gap",
          suptitle="The internal–stated confidence gap: the model knows, but does not say")


# ===================================================== Figure 2 — K/L dissociation
def fig2_kl_dissociation():
    # Provenance: paper §7 Table 1 [calibration_gap_contrastive_sft_seed1.json;
    # calibration_gap_contrastive_masked_sft_seed1.json; AMENDMENT-L gates].
    # cal AUROC->appropriateness: base 0.52, K 0.684, L 0.552 (gate 0.62)
    # truthful_pct: base 40.58, K 30.93, L 41.59 (gate 35.6)
    arm_cols = [C["gray"], C["green"], C["blue"]]
    cal = [0.52, 0.684, 0.552]
    truthful = [40.58, 30.93, 41.59]

    fig, (axS, axB) = plt.subplots(1, 2, figsize=(9.2, 4.4))

    # Panel A — the trade-off scatter (the punchline)
    label_off = {"base": (-12, -20), "answer-\nsupervised": (-26, 30),
                 "answer-\nmasked": (10, 6)}
    label_ha = {"base": "left", "answer-\nsupervised": "center", "answer-\nmasked": "left"}
    for x, y, c, name in zip(cal, truthful, arm_cols,
                             ["base", "answer-\nsupervised", "answer-\nmasked"]):
        axS.scatter(x, y, s=190, color=c, zorder=4, edgecolor="white", linewidth=1.3)
        axS.annotate(name, (x, y), textcoords="offset points", xytext=label_off[name],
                     ha=label_ha[name], fontsize=11, fontweight="bold", color=c)
    axS.axvline(0.62, ls="--", lw=1.1, color=C["gate"], zorder=2)
    axS.axhline(35.6, ls="--", lw=1.1, color=C["gate"], zorder=2)
    axS.text(0.621, 31.2, "calibration gate 0.62", rotation=90, fontsize=8,
             color=C["gate"], va="bottom")
    axS.text(0.515, 35.9, "behavior gate 35.6", fontsize=8, color=C["gate"], va="bottom")
    axS.set_xlabel("Stated calibration  (emitted AUROC → appropriateness)")
    axS.set_ylabel("Behavior  (truthful %)")
    axS.set_title("You can buy one, not both")
    axS.set_xlim(0.49, 0.72); axS.set_ylim(28, 45)
    _style(axS); axS.grid(axis="both", color=C["grid"], linewidth=0.8)

    # Panel B — behavior detail
    metrics = ["truthful", "correct_on\n_known", "over_refusal\n(↓ better)", "refusal\n_recall"]
    base = [40.58, 47.23, 57.51, 87.02]
    K = [30.93, 36.63, 79.2, 83.72]
    L = [41.59, 50.06, 62.73, 93.51]
    import numpy as np
    x = np.arange(len(metrics)); w = 0.26
    axB.bar(x - w, base, w, label="base", color=C["gray"], zorder=3)
    axB.bar(x,     K,    w, label="answer-supervised", color=C["green"], zorder=3)
    axB.bar(x + w, L,    w, label="answer-masked",     color=C["blue"], zorder=3)
    axB.set_xticks(x); axB.set_xticklabels(metrics, fontsize=9)
    axB.set_ylabel("percent")
    axB.set_title("Behavior metrics by arm")
    axB.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0))
    axB.set_ylim(0, 105)
    _style(axB)

    _save(fig, "fig-p2-02-answer-supervision-dissociation",
          suptitle="Result 4 — the answer-supervision dissociation")


# ================================== Figure 3 — answer-supervised base cell confidence
def fig3_cell_confidence():
    # Provenance: action_conditioning_report.py / calibration_gap_report.py on
    # results_amendment_n_..._grpo_on_contrastive_sft_seed1 (greedy).
    cells = [
        ("known\ncorrect", 0.724, C["green"]),
        ("unknown\nrefused", 0.542, C["green"]),
        ("known\nwrong", 0.424, C["orange"]),
        ("known\nrefused", 0.412, C["orange"]),
        ("unknown\nwrong", 0.138, C["orange"]),
    ]
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    names = [c[0] for c in cells]
    vals = [c[1] for c in cells]
    cols = [c[2] for c in cells]
    bars = ax.bar(names, vals, color=cols, width=0.66, zorder=3)
    _bar_labels(ax, bars)
    ax.set_ylim(0, 0.85)
    ax.set_ylabel("mean stated confidence")
    _style(ax)

    # highlight the ordering the answer-masked variant inverted
    ax.annotate("",
                xy=(1, 0.542), xytext=(4, 0.138),
                arrowprops=dict(arrowstyle="<->", color=C["gate"], lw=1.3))
    ax.text(2.5, 0.60, "unknown-refused > unknown-wrong\n(the ordering answer-masking inverted — here correct)",
            ha="center", fontsize=9, color=C["gate"])

    legend = [Line2D([0], [0], marker="s", color="w", markerfacecolor=C["green"],
                     markersize=11, label="appropriate response"),
              Line2D([0], [0], marker="s", color="w", markerfacecolor=C["orange"],
                     markersize=11, label="inappropriate response")]
    ax.legend(handles=legend, frameon=False, fontsize=9, loc="upper right")
    ax.set_title("RL on the answer-supervised base retains stated calibration",
                 fontsize=12.5)
    _save(fig, "fig-p2-03-answer-supervised-cell-confidence")


# ====================================== Figure 4 — calibrated conf, uncalibrated action
def fig4_confidence_vs_action():
    # Provenance: action_conditioning_report.py on N greedy + temp1.35.
    # confidence AUROC: refusal-appropriateness 0.620, answer-correctness 0.837.
    # action answer-rate: greedy known 0.0924 / unknown 0.0640 (+2.85pt);
    # temp1.35 known 0.9375 / unknown 0.8721 (+6.5pt).
    import numpy as np
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.2, 4.3))

    # Panel A — confidence channel discriminates
    labs = ["refusal\nappropriateness", "answer\ncorrectness"]
    bars = axA.bar(labs, [0.620, 0.837], color=C["green"], width=0.55, zorder=3)
    axA.axhline(0.5, ls="--", lw=1.1, color=C["gray"], zorder=2)
    axA.text(1.45, 0.505, "chance", fontsize=8.5, color=C["gray"], ha="right", va="bottom")
    _bar_labels(axA, bars)
    axA.set_ylim(0, 1.0)
    axA.set_ylabel("AUROC")
    axA.set_title("Confidence channel: discriminates ✓")
    _style(axA)

    # Panel B — action channel barely conditions on knowledge
    x = np.arange(2); w = 0.34
    known = [9.24, 93.75]; unknown = [6.40, 87.21]
    b1 = axB.bar(x - w/2, known, w, label="known", color=C["blue"], zorder=3)
    b2 = axB.bar(x + w/2, unknown, w, label="unknown", color=C["orange"], zorder=3)
    axB.set_xticks(x); axB.set_xticklabels(["greedy\n(temp 0)", "temp 1.35\n(train temp)"])
    axB.set_ylabel("answer rate (%)")
    axB.set_ylim(0, 108)
    axB.set_title("Action channel: barely conditions ✗")
    _bar_labels(axB, b1, fmt="{:.1f}"); _bar_labels(axB, b2, fmt="{:.1f}")
    # margin annotations
    axB.text(0, 22, "margin\n+2.85 pts", ha="center", fontsize=8.5, color=C["gate"])
    axB.text(1, 102, "margin\n+6.5 pts", ha="center", fontsize=8.5, color=C["gate"])
    axB.legend(frameon=False, fontsize=9, loc="center left")
    _style(axB)

    _save(fig, "fig-p2-04-confidence-vs-action",
          suptitle="Calibrated confidence, uncalibrated action — 'says but doesn't act'")


# ============================================ Figure 5 — action margin trajectory
def fig5_margin_trajectory():
    # Provenance: action_conditioning_report.py --reward-debug
    # grpo_on_k_full_debug.jsonl (beta 0.1 run, 1861 steps, 6 bins).
    import numpy as np
    mids = [155, 465, 775, 1085, 1395, 1705]
    known = [0.769, 0.759, 0.758, 0.752, 0.741, 0.735]
    unknown = [0.743, 0.707, 0.684, 0.683, 0.662, 0.667]

    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    ax.plot(mids, known, "-o", color=C["blue"], lw=2, label="answer rate | known", zorder=4)
    ax.plot(mids, unknown, "-o", color=C["orange"], lw=2, label="answer rate | unknown", zorder=4)
    ax.fill_between(mids, unknown, known, color=C["purple"], alpha=0.15, zorder=2,
                    label="knowledge margin (≈ +5–8 pts, never opens)")
    ax.set_xlabel("training step (binned)")
    ax.set_ylabel("answer rate (rollouts, temp 1.35)")
    ax.set_ylim(0.0, 1.0)
    ax.set_xlim(0, 1861)

    # reference: margin needed to pass the behavior gate
    ax.annotate("a passing policy needs the\nmargin to open to ≈ +14.5 pts\n(and the bands to separate)",
                xy=(1705, (known[-1] + unknown[-1]) / 2),
                xytext=(900, 0.30), fontsize=9, color=C["gate"],
                arrowprops=dict(arrowstyle="->", color=C["gate"], lw=1.2))
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    _style(ax)
    ax.set_title("The action margin never opens across 1861 training steps",
                 fontsize=12.5)
    _save(fig, "fig-p2-05-action-margin-trajectory")


# ============================================ Figure 6 — refusal-axis ablation
def fig6_refusal_axis_ablation():
    # Provenance: primary arm data read programmatically from the committed
    # artifact experiments/caution-ablation-rederivation/analysis-committed/
    # config2_caution_perp_residual_intervention_summary.json — the
    # KU-orthogonalized ("caution_perp") residual intervention at L35 on
    # clean_sft_grpo_v2_seed1 (4 arms x known_refused/known_correct_answered,
    # n=168/373 rows). This is the freshly re-derived source for paper 3's
    # "0.994 to 0.524" figure (manuscript.md Section 6); AMENDMENT.md
    # "Outcome" table row "caution_perp ablate" reports the same rate
    # (0.5238, rounds to 0.524).
    summary_path = (
        REPO_ROOT
        / "experiments/caution-ablation-rederivation/analysis-committed"
        / "config2_caution_perp_residual_intervention_summary.json"
    )
    data = json.loads(summary_path.read_text())
    arms = ["baseline", "ablate", "shift_minus2", "shift_plus2"]
    arm_labels = ["baseline", "ablate", "shift\n−2σ", "shift\n+2σ"]
    kr_refusal = [data["by_arm"][a]["known_refused"]["refusal_rate"] for a in arms]
    ka_refusal = [data["by_arm"][a]["known_correct_answered"]["refusal_rate"] for a in arms]
    kr_correct = [data["by_arm"][a]["known_refused"]["correct_rate"] for a in arms]

    # In-frame replication (registered doubt-regulated-caution cell, same
    # recipe, fresh row set): ablate arm known_refused refusal 0.994 -> 0.536.
    # No analysis-committed JSON exists for experiments/doubt-regulated-caution/
    # (untracked-outputs convention, see its AMENDMENT.md "Analysis outputs
    # stay untracked"); hand-entered from AMENDMENT.md Section 8 Result table,
    # "ablate" row (kr refusal 0.536, kr correct 0.327).
    replication_kr_refusal_ablate = 0.536

    import numpy as np
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(10.2, 4.6),
                                    gridspec_kw={"wspace": 0.4})

    x = np.arange(len(arms)); w = 0.34
    b1 = axA.bar(x - w / 2, kr_refusal, w, label="known-item refusal (over-refusal)",
                 color=C["orange"], zorder=3)
    b2 = axA.bar(x + w / 2, ka_refusal, w, label="known-correct-answered refusal (specificity)",
                 color=C["green"], zorder=3)
    axA.set_xticks(x); axA.set_xticklabels(arm_labels)
    axA.set_ylabel("refusal rate")
    axA.set_ylim(0, 1.62)
    _bar_labels(axA, b1); _bar_labels(axA, b2)
    axA.scatter([1 + w / 2], [replication_kr_refusal_ablate], marker="D", s=50,
                color=C["gate"], zorder=5)
    axA.annotate(f"in-frame replication {replication_kr_refusal_ablate:.3f}",
                 xy=(1 + w / 2, replication_kr_refusal_ablate),
                 textcoords="offset points", xytext=(18, -32),
                 fontsize=8, color=C["gate"], ha="left",
                 arrowprops=dict(arrowstyle="->", color=C["gate"], lw=1.0))
    axA.legend(frameon=False, fontsize=8.2, loc="upper center", ncol=1)
    axA.set_title("Refusal-axis ablation relaxes over-refusal;\nspecificity stays intact", fontsize=11.5)
    _style(axA)

    b3 = axB.bar(arm_labels, kr_correct, color=C["blue"], width=0.6, zorder=3)
    _bar_labels(axB, b3, fmt="{:.3f}")
    axB.set_ylim(0, 0.5)
    axB.set_ylabel("correct rate\n(known_refused cell, n=168)")
    axB.set_title("Answers produced after ablation\nare correct, not just present", fontsize=11.5)
    _style(axB)

    # Manual layout: this figure's annotate() arrow makes matplotlib's
    # tight_layout report itself unreliable, so margins are set explicitly
    # rather than trusting tight_layout's automatic suptitle spacing.
    fig.suptitle("Result 3 — the refusal axis is causally real, ablation is one-way",
                 fontsize=13, fontweight="bold", y=0.99)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.76, bottom=0.11, wspace=0.4)
    fig.savefig(FIG_DIR / "fig-p2-06-refusal-axis-ablation.svg")
    fig.savefig(FIG_DIR / "fig-p2-06-refusal-axis-ablation.png", dpi=200)
    plt.close(fig)
    print("wrote fig-p2-06-refusal-axis-ablation.svg + .png")


# ================================================ Figure 7 — bounded site sweep
def fig7_bounded_site_sweep():
    # Provenance: read programmatically from the committed artifact
    # experiments/caution-install-bounded-site-sweep/analysis-committed/
    # gate_report.json. Panel A: gates.g1_actuation.trained[site:anchor_onward]
    # .rate / .wilson_lower_95 (held-out confab clean_tighten, n=154 per site).
    # Panel B: gates.g3_direction_specificity.trained[site:anchor_onward]
    # .ratio / .pass (gated lift over max permuted/positional-control draw
    # lift; hs19 and hs34 have max_draw_lift == 0, serialized as ratio "inf"
    # and failing the pre-registered positivity guard, not a finite ratio).
    # Relative depth (hs / 36) per site is the AMENDMENT.md "Pre-registered
    # search space" table (Section: Design > Pre-registered search space):
    # hs19=0.528, hs23=0.639, hs29=0.806, hs34=0.944, hs35=0.972. Only these
    # five of the seven registered sites cleared dose viability (hs13, hs16
    # recorded NOT_RUN_no_usable_rung), and only at the anchor_onward write
    # position.
    gate_path = (
        REPO_ROOT
        / "experiments/caution-install-bounded-site-sweep/analysis-committed"
        / "gate_report.json"
    )
    gates = json.loads(gate_path.read_text())["gates"]
    sites = ["hs19", "hs23", "hs29", "hs34", "hs35"]
    depth = {"hs19": 0.528, "hs23": 0.639, "hs29": 0.806, "hs34": 0.944, "hs35": 0.972}
    g1 = gates["g1_actuation"]["trained"]
    g3 = gates["g3_direction_specificity"]["trained"]

    rate = [g1[f"{s}:anchor_onward"]["rate"] for s in sites]
    wlo = [g1[f"{s}:anchor_onward"]["wilson_lower_95"] for s in sites]
    x_labels = [f"{s}\n(depth {depth[s]:.2f})" for s in sites]

    import numpy as np
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.6, 4.5))

    x = np.arange(len(sites))
    yerr = np.vstack([np.array(rate) - np.array(wlo), np.zeros(len(sites))])
    bars = axA.bar(x, rate, color=C["blue"], width=0.58, zorder=3,
                    yerr=yerr, capsize=4, ecolor=C["text"])
    axA.axhline(0.50, ls="--", lw=1.1, color=C["gate"], zorder=2)
    axA.axhline(0.40, ls=":", lw=1.0, color=C["gray"], zorder=2)
    axA.text(4.35, 0.515, "rate threshold 0.50", fontsize=7.8, color=C["gate"], ha="right")
    axA.text(4.35, 0.375, "Wilson-lower threshold 0.40", fontsize=7.8, color=C["gray"], ha="right")
    axA.set_xticks(x); axA.set_xticklabels(x_labels, fontsize=9)
    axA.set_ylabel("held-out confab → refusal rate\n(error bar: Wilson lower 95%)")
    axA.set_ylim(0, 1.08)
    _bar_labels(axA, bars)
    axA.set_title("Every dose-viable site actuates\n(write position: anchor onward)")
    _style(axA)

    ratio_vals = []
    is_finite = []
    for s in sites:
        r = g3[f"{s}:anchor_onward"]["ratio"]
        if isinstance(r, (int, float)):
            ratio_vals.append(r); is_finite.append(True)
        else:
            ratio_vals.append(0.0); is_finite.append(False)
    passed = [g3[f"{s}:anchor_onward"]["pass"] for s in sites]
    bar_cols = [C["green"] if p else C["gray"] for p in passed]
    bars2 = axB.bar(x, ratio_vals, color=bar_cols, width=0.58, zorder=3)
    for xi, (v, fin, p) in enumerate(zip(ratio_vals, is_finite, passed)):
        if not fin:
            axB.text(xi, 0.35, "undefined\n(fails\npositivity\nguard)", ha="center",
                     va="bottom", fontsize=7.2, color=C["gate"])
        else:
            axB.text(xi, v + 0.3, f"{v:.2f}×", ha="center", va="bottom", fontsize=9)
    axB.axhline(3.0, ls="--", lw=1.1, color=C["gate"], zorder=2)
    axB.text(4.35, 3.15, "G3 pass threshold (3×)", fontsize=7.8, color=C["gate"], ha="right")
    axB.set_xticks(x); axB.set_xticklabels([s for s in sites], fontsize=9)
    axB.set_ylabel("gated lift / max control-draw lift")
    axB.set_ylim(0, 14)
    legend = [Line2D([0], [0], marker="s", color="w", markerfacecolor=C["green"],
                     markersize=11, label="G3 pass (specific)"),
              Line2D([0], [0], marker="s", color="w", markerfacecolor=C["gray"],
                     markersize=11, label="G3 fail (not specific)")]
    axB.legend(handles=legend, frameon=False, fontsize=8.2, loc="upper left")
    axB.set_title("Only hs35 writes specifically\nalong the refusal direction")
    _style(axB)

    _save(fig, "fig-p2-07-bounded-site-sweep",
          suptitle="Result 3 follow-on — the bounded search to install abstention")


if __name__ == "__main__":
    fig1_internal_vs_stated()
    fig2_kl_dissociation()
    fig3_cell_confidence()
    fig4_confidence_vs_action()
    fig5_margin_trajectory()
    fig6_refusal_axis_ablation()
    fig7_bounded_site_sweep()
    print(f"\nAll figures written to {FIG_DIR}")
