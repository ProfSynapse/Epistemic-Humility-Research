#!/usr/bin/env python3
"""Generate the figures for the two-signal-readout paper (Paper 4).

Reads the committed amendment result JSONs under the paper-local
analysis/source-artifacts/ snapshot and emits publication figures to
papers/paper-4-two-signal-readout/figures/. Deterministic: no randomness, no
network, CPU only. Regenerate with:

    python3 papers/paper-4-two-signal-readout/scripts/build_figures.py

Every number in every figure traces to a specific source artifact.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "papers" / "paper-4-two-signal-readout"
PROBE = PAPER / "analysis" / "source-artifacts" / "probe"
OUT = PAPER / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---- palette -------------------------------------------------------------
C_GATE = "#2C6E9C"   # answerability gate  (blue)
C_DIAL = "#4A9D7F"   # correctness dial    (green)
C_VETO = "#C25B3F"   # hallucination veto  (terracotta)
C_MUTE = "#9AA0A6"
THRESH = 0.65
CHANCE = 0.50
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "figure.dpi": 150,
})


def load(name: str) -> dict:
    return json.loads((PROBE / name).read_text())


def ci_err(point: float, ci: list[float]) -> list[list[float]]:
    """asymmetric yerr (2x1) from a [lo, hi] CI around point."""
    return [[point - ci[0]], [ci[1] - point]]


# ---- data ----------------------------------------------------------------
Z = {
    "Llama-3.2-3B": load("amendment_z_llama-3.2-3b_result.json"),
    "Ministral-3-3B": load("amendment_z_ministral-3-3b_result.json"),
    "Qwen3.5-4B": load("amendment_z_qwen3.5-4b_result.json"),
    "Gemma-4-E4B": load("amendment_z_gemma-4-e4b_result.json"),
}
W = load("amendment_w_base_model_result.json")
U = load("amendment_u_two_signal_result.json")
# 2026-07-18 hallucination-label re-grade for the deployed-checkpoint veto cell.
# Set A (instrument-corrected, n=12) and Set B (census-corrected, n=8) supersede the
# pre-correction hallucination group; both sit below that cell's >=50 adequacy floor,
# so the panel that uses them is annotated descriptive/unpowered.
UC = load("ug3_corrected_rescore.json")
S = load("amendment_s_stage2_result.json")
T = load("amendment_t_stage2_result.json")
X = {
    "1.7B": load("amendment_x_qwen3-1.7b-bnb-4bit_result.json"),
    "8B": load("amendment_x_qwen3-8b-bnb-4bit_result.json"),
    "14B": load("amendment_x_qwen3-14b-bnb-4bit_result.json"),
}


def z_triplet(d: dict):
    g = d["X_G1_gate"]["answerability_auroc"]
    di = d["X_G2_dial"]["auroc_correct_vs_wrong"]
    v = d["X_G3_veto_PRIMARY"]
    return g, di, v["answerability_auroc"] if False else v["auroc_correct_vs_hallucination"], v["ci_95"]


# =========================================================================
# FIG 5 — cross-family two-signal readout (the confirmatory hero)
# =========================================================================
def fig1_cross_family():
    # order families by veto ascending -> makes the variation legible
    fams = sorted(Z.items(), key=lambda kv: kv[1]["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"])
    labels = [k for k, _ in fams]
    gate = [d["X_G1_gate"]["answerability_auroc"] for _, d in fams]
    dial = [d["X_G2_dial"]["auroc_correct_vs_wrong"] for _, d in fams]
    veto = [d["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"] for _, d in fams]
    veto_ci = [d["X_G3_veto_PRIMARY"]["ci_95"] for _, d in fams]

    import numpy as np
    x = np.arange(len(labels))
    w = 0.26
    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    ax.bar(x - w, gate, w, label="Answerability gate", color=C_GATE)
    ax.bar(x, dial, w, label="Correctness dial", color=C_DIAL)
    bars = ax.bar(x + w, veto, w, label="Hallucination veto (primary)", color=C_VETO)
    ax.errorbar(x + w, veto, yerr=np.array([ci_err(v, c) for v, c in zip(veto, veto_ci)]).squeeze(-1).T,
                fmt="none", ecolor="#222", elinewidth=1.1, capsize=3)

    for xi, v, c in zip(x + w, veto, veto_ci):
        ok = v >= THRESH and c[0] > CHANCE
        ax.text(xi, c[1] + 0.015, "PASS" if ok else "FAIL",
                ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                color=(C_DIAL if ok else C_VETO))

    ax.axhline(THRESH, ls="--", lw=1.1, color="#444", zorder=0)
    ax.text(len(labels) - 0.5, THRESH + 0.006, "pass bar 0.65", ha="right", va="bottom", fontsize=8.5, color="#444")
    ax.axhline(CHANCE, ls=":", lw=1.0, color=C_MUTE, zorder=0)
    ax.text(len(labels) - 0.5, CHANCE + 0.006, "chance 0.50", ha="right", va="bottom", fontsize=8.5, color=C_MUTE)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("AUROC")
    ax.set_ylim(0.45, 1.02)
    ax.set_title("Two-signal trust readout replicates across four model families\n"
                 "gate + dial saturate everywhere; the veto is the variable axis (3/4 pass)",
                 fontsize=11.5)
    ax.legend(loc="lower center", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.22))
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-05-cross-family-readout.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 2 — the veto mechanism: dial-mean by outcome class, per family
# =========================================================================
def fig2_dial_distribution():
    import numpy as np
    fams = sorted(Z.items(), key=lambda kv: kv[1]["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"])
    labels = [k for k, _ in fams]
    correct = [d["descriptive"]["dial_mean_correct"] for _, d in fams]
    wrong = [d["descriptive"]["dial_mean_wrong"] for _, d in fams]
    halluc = [d["descriptive"]["dial_mean_hallucination"] for _, d in fams]

    x = np.arange(len(labels))
    w = 0.26
    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    ax.bar(x - w, correct, w, label="correct answers", color=C_DIAL)
    ax.bar(x, wrong, w, label="wrong answers", color=C_MUTE)
    ax.bar(x + w, halluc, w, label="confident hallucinations", color=C_VETO)

    # annotate the correct-vs-hallucination gap that the veto measures
    for xi, cc, hh in zip(x, correct, halluc):
        gap = cc - hh
        ax.annotate("", xy=(xi - w, cc), xytext=(xi + w, hh),
                    arrowprops=dict(arrowstyle="<->", color="#333", lw=0.9, alpha=0.7))
        ax.text(xi, max(cc, hh) + 0.02, f"gap {gap:.2f}", ha="center", va="bottom", fontsize=8, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("correctness-dial score (mean)")
    ax.set_ylim(0, 0.85)
    ax.set_title("Why the veto is fragile: how far confident hallucinations sit below correct answers\n"
                 "wide gap (Gemma) → veto works; collapsed gap (Llama) → veto fails",
                 fontsize=11.5)
    ax.legend(loc="upper right", frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-02-dial-distribution.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 4 — the veto is the fragile axis across BOTH size and family
# =========================================================================
def fig3_fragile_axis():
    import numpy as np
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    # left: cross-size (X) — 1.7B, 4B(=W), 8B, 14B
    sizes = ["1.7B", "4B", "8B", "14B"]
    xg = [X["1.7B"]["X_G1_gate"]["answerability_auroc"], W["W_G2_gate_on_base_anchor"]["answerability_auroc"],
          X["8B"]["X_G1_gate"]["answerability_auroc"], X["14B"]["X_G1_gate"]["answerability_auroc"]]
    xd = [X["1.7B"]["X_G2_dial"]["auroc_correct_vs_wrong"], S["headline"]["auroc_post"],
          X["8B"]["X_G2_dial"]["auroc_correct_vs_wrong"], X["14B"]["X_G2_dial"]["auroc_correct_vs_wrong"]]
    xv = [X["1.7B"]["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"],
          W["W_G1_dial_on_hallucination_PRIMARY"]["auroc_scorrect_vs_hallucination"],
          X["8B"]["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"],
          X["14B"]["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"]]
    xi = np.arange(len(sizes))
    axL.plot(xi, xg, "-o", color=C_GATE, label="gate")
    axL.plot(xi, xd, "-s", color=C_DIAL, label="dial")
    axL.plot(xi, xv, "-^", color=C_VETO, label="veto", lw=2.2, ms=8)
    axL.axhline(THRESH, ls="--", lw=1.0, color="#444")
    axL.set_xticks(xi); axL.set_xticklabels(sizes)
    axL.set_ylim(0.45, 1.02); axL.set_ylabel("AUROC")
    axL.set_xlabel("Qwen3 model size")
    axL.set_title("across SIZE (one family)", fontsize=10.5)
    axL.legend(frameon=False, fontsize=9, loc="lower left")

    # right: cross-family (Z), veto ascending
    fams = sorted(Z.items(), key=lambda kv: kv[1]["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"])
    labels = [k.split("-")[0] for k, _ in fams]
    zg = [d["X_G1_gate"]["answerability_auroc"] for _, d in fams]
    zd = [d["X_G2_dial"]["auroc_correct_vs_wrong"] for _, d in fams]
    zv = [d["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"] for _, d in fams]
    zi = np.arange(len(labels))
    axR.plot(zi, zg, "-o", color=C_GATE, label="gate")
    axR.plot(zi, zd, "-s", color=C_DIAL, label="dial")
    axR.plot(zi, zv, "-^", color=C_VETO, label="veto", lw=2.2, ms=8)
    axR.axhline(THRESH, ls="--", lw=1.0, color="#444")
    axR.text(len(labels) - 1, THRESH + 0.008, "pass bar 0.65", ha="right", va="bottom", fontsize=8, color="#444")
    axR.set_xticks(zi); axR.set_xticklabels(labels)
    axR.set_ylim(0.45, 1.02)
    axR.set_xlabel("model family")
    axR.set_title("across FAMILY (fixed ~3–4B)", fontsize=10.5)
    axR.legend(frameon=False, fontsize=9, loc="lower left")

    fig.suptitle("The gate and dial are stable; the veto is the fragile axis — in both directions",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-04-fragile-axis.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 1 — reading AFTER the answer beats reading before (S, T)
# =========================================================================
def fig4_post_beats_pre():
    import numpy as np
    fig, (axS, axT) = plt.subplots(1, 2, figsize=(11.0, 4.6), sharey=True)
    for ax, d, name, ckpt in [(axS, S, "S", "raw instruction-tuned base"), (axT, T, "T", "after abstention training")]:
        pre = d["auroc_surface"]["pre"]
        post = d["auroc_surface"]["post"]
        layers = sorted(int(k) for k in post)
        yv_pre = [pre[str(l)] for l in layers]
        yv_post = [post[str(l)] for l in layers]
        ax.plot(layers, yv_pre, "-", color=C_MUTE, label="read BEFORE answer (pre)")
        ax.plot(layers, yv_post, "-", color=C_DIAL, lw=2.0, label="read AFTER answer (post)")
        bl = d["headline"]["best_post_layer"]
        ax.plot([bl], [d["headline"]["auroc_post"]], "o", color=C_DIAL, ms=8)
        ax.axvline(bl, ls=":", lw=0.9, color=C_DIAL, alpha=0.6)
        ax.set_xlabel("layer")
        ax.set_title(ckpt, fontsize=10.5)
        ax.legend(frameon=False, fontsize=9, loc="lower right")
    axS.set_ylabel("correctness AUROC")
    axS.set_ylim(0.48, 0.87)
    fig.suptitle("Per-answer correctness reads best AFTER the answer, peaking mid-network",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-01-post-beats-pre.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 3 — training does not CREATE the veto; sharpening is unpowered (W -> corrected U)
# =========================================================================
def fig5_training_sharpens():
    import numpy as np
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(10.2, 4.5))

    # A: veto AUROC on the untrained raw base vs the pass bar and chance
    base_v = W["W_G1_dial_on_hallucination_PRIMARY"]["auroc_scorrect_vs_hallucination"]
    axA.bar([0], [base_v], color=[C_VETO], width=0.45)
    axA.axhline(THRESH, ls="--", lw=1.0, color="#444")
    axA.axhline(CHANCE, ls=":", lw=1.0, color="#888")
    axA.text(0.42, THRESH + 0.008, "pass bar 0.65", ha="right", va="bottom", fontsize=8, color="#444")
    axA.text(0.42, CHANCE + 0.008, "chance 0.50", ha="right", va="bottom", fontsize=8, color="#888")
    axA.text(0, base_v + 0.01, f"{base_v:.3f}", ha="center", va="bottom", fontsize=10)
    axA.set_xticks([0]); axA.set_xticklabels(["raw base, no abstention training"])
    axA.set_xlim(-0.55, 0.55)
    axA.set_ylabel("hallucination-veto AUROC"); axA.set_ylim(0, 1.05)
    axA.set_title("the veto EXISTS untrained", fontsize=10.5)

    # B: hallucination dial-mean, raw base vs deployed checkpoint under the corrected
    # 2026-07-18 hallucination labels (Set A n=12, Set B n=8). Both trained-side bars are
    # descriptive: they sit below the veto cell's own >=50 adequacy floor.
    base_h = W["descriptive"]["dial_mean_hallucination"]
    set_a = UC["set_A_instrument_corrected"]
    set_b = UC["set_B_census_corrected"]
    bars_h = [base_h, set_a["dial_mean_hallucination"], set_b["dial_mean_hallucination"]]
    labels_h = [
        "raw base",
        f"trained,\nSet A (n={set_a['n_hallucination']})",
        f"trained,\nSet B (n={set_b['n_hallucination']})",
    ]
    axB.bar([0, 1, 2], bars_h, color=[C_MUTE, C_VETO, C_VETO], width=0.6)
    for xi, v in zip([0, 1, 2], bars_h):
        axB.text(xi, v + 0.008, f"{v:.3f}", ha="center", va="bottom", fontsize=10)
    axB.set_xticks([0, 1, 2]); axB.set_xticklabels(labels_h, fontsize=8.5)
    axB.set_ylabel("dial score on confident hallucinations"); axB.set_ylim(0, 0.42)
    axB.set_title("training's effect on confabulation trust:\ndescriptive, below the adequacy floor",
                  fontsize=10.5)
    axB.text(1.5, 0.395, f"trained bars descriptive: n={set_a['n_hallucination']}/"
                         f"{set_b['n_hallucination']} vs a registered floor of "
                         f"{UC['adequacy_floor_hallucinations']}",
             ha="center", va="top", fontsize=8, color="#444")

    fig.suptitle("Training does not create the trust signal; whether it sharpens the veto is unpowered (Qwen3-4B)",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-03-training-sharpens.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 7 — the two-stage pipeline schematic
# =========================================================================
def fig6_pipeline():
    fig, ax = plt.subplots(figsize=(10.5, 3.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")

    def box(x, y, w, h, text, fc, tc="white"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=fc, ec="none"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=9.5, wrap=True)

    def arrow(x1, y1, x2, y2, text="", tc="#333"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, color="#555", lw=1.4))
        if text:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.18, text, ha="center", fontsize=8.5, color=tc)

    box(0.1, 1.6, 1.5, 0.9, "prompt", "#3a3a3a")
    arrow(1.6, 2.05, 2.3, 2.05)
    box(2.3, 1.4, 1.9, 1.3, "GATE\nanswerability\n(read @ anchor)", C_GATE)
    arrow(4.2, 2.6, 5.0, 3.1, "≥ τ: answer")
    arrow(4.2, 1.5, 5.0, 0.8, "< τ: abstain")
    box(5.0, 0.35, 1.9, 0.9, '"I don\'t know"', C_MUTE)
    box(5.0, 2.7, 1.9, 1.0, "model generates\nan answer", "#3a3a3a")
    arrow(6.9, 3.2, 7.6, 2.7)
    box(7.6, 1.4, 2.2, 1.3, "DIAL + VETO\ncorrectness\n(read @ answer)", C_DIAL)
    arrow(8.7, 1.4, 8.7, 0.7)
    box(7.6, -0.15, 2.2, 0.8, "surface trust # /\nveto confabulation", C_VETO)

    ax.set_title("The deployable two-stage pipeline: gate abstains, dial surfaces trust and vetoes hallucination",
                 fontsize=11.5, y=1.04)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-07-pipeline.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 6 — cross-family depth profile: gate plateau vs localized dial band
# =========================================================================
# family palette (consistent across both panels)
C_FAM = {
    "Llama-3.2-3B": "#4C72B0",
    "Ministral-3-3B": "#DD8452",
    "Qwen3.5-4B": "#55A868",
    "Gemma-4-E4B": "#8172B3",
}
GATE_TOL = 0.005   # gate plateau = layers within 0.005 of that family's max
DIAL_TOL = 0.02    # dial band    = layers within 0.02  of that family's max


def _surface(d: dict, block: str):
    """(fractional depths, aurocs, n_layers) for one family's auroc_surface."""
    surf = {int(k): v for k, v in d[block]["auroc_surface"].items()}
    n = max(surf)  # layer indices run 0..n; fractional depth = layer / n
    layers = sorted(surf)
    return [l / n for l in layers], [surf[l] for l in layers], n


def _span(d: dict, block: str, tol: float):
    """min/max layer within tol of the max, plus argmax layer and n_layers."""
    surf = {int(k): v for k, v in d[block]["auroc_surface"].items()}
    n = max(surf)
    best = max(surf.values())
    keep = [l for l in sorted(surf) if surf[l] >= best - tol]
    return min(keep), max(keep), max(surf, key=surf.get), n


def fig7_depth_profile():
    fig, (axG, axD) = plt.subplots(1, 2, figsize=(11.0, 4.8), sharex=True)

    for panel, (ax, block, tol) in enumerate([(axG, "X_G1_gate", GATE_TOL),
                                              (axD, "X_G2_dial", DIAL_TOL)]):
        for fi, (fam, d) in enumerate(Z.items()):
            c = C_FAM[fam]
            fx, fy, n = _surface(d, block)
            lo, hi, am, _ = _span(d, block, tol)
            ax.plot(fx, fy, "-", color=c, lw=1.6,
                    label=f"{fam} ({n} blk)" if panel == 0 else None)
            surf = d[block]["auroc_surface"]
            ax.plot([am / n], [surf[str(am)]], "o", color=c, ms=7, zorder=5)
            # per-family span bar (within-tol band), stacked under the curves
            y0 = ax.get_ylim()  # placeholder; bars drawn after ylim set below
            ax._span_bars = getattr(ax, "_span_bars", [])
            ax._span_bars.append((lo / n, hi / n, c))
        ax.set_xlabel("fractional depth  (layer / n_layers)")
        ax.set_xlim(-0.02, 1.02)

    axG.set_ylabel("answerability AUROC (gate)")
    axG.set_ylim(0.96, 1.003)
    axG.set_title(f"GATE: saturated plateau (within {GATE_TOL} of max)\n"
                  "layer 0 sits at chance, below this zoomed axis", fontsize=10.5)
    axD.set_ylabel("correctness AUROC (dial)")
    axD.set_ylim(0.55, 0.90)
    axD.set_title(f"DIAL: localized mid-to-late band (within {DIAL_TOL} of max)",
                  fontsize=10.5)

    # draw the stacked within-tol span bars now that ylims are fixed
    for ax in (axG, axD):
        y_lo, y_hi = ax.get_ylim()
        h = (y_hi - y_lo) * 0.016
        for i, (x0, x1, c) in enumerate(ax._span_bars):
            y = y_lo + (i + 1.2) * h * 1.5
            ax.plot([x0, x1], [y, y], "-", color=c, lw=3.2, alpha=0.65,
                    solid_capstyle="butt", zorder=1)
        del ax._span_bars

    axG.legend(frameon=False, fontsize=8.5, loc="center right")
    fig.suptitle("Where each signal lives: the gate plateaus from ~20% depth onward in all four "
                 "families;\nthe dial concentrates in an overlapping mid-to-late band "
                 "(dots = argmax layer; bars = within-tolerance span)",
                 fontsize=11.5, y=1.06)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-06-depth-profile.png", bbox_inches="tight")
    plt.close(fig)

    # provenance printout: recomputed spans backing the paper text
    for fam, d in Z.items():
        glo, ghi, gam, gn = _span(d, "X_G1_gate", GATE_TOL)
        dlo, dhi, dam, dn = _span(d, "X_G2_dial", DIAL_TOL)
        print(f"  fig6 {fam}: gate plateau L{glo}-{ghi}/{gn} (argmax L{gam}), "
              f"dial band L{dlo}-{dhi}/{dn} (argmax L{dam})")



if __name__ == "__main__":
    fig1_cross_family()
    fig2_dial_distribution()
    fig3_fragile_axis()
    fig4_post_beats_pre()
    fig5_training_sharpens()
    fig6_pipeline()
    fig7_depth_profile()
    print("figures written to", OUT)
    for p in sorted(OUT.glob("*.png")):
        print(" -", p.relative_to(ROOT), f"({p.stat().st_size // 1024} KB)")
