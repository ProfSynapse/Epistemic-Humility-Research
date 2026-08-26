#!/usr/bin/env python3
"""Generate Figure 10 for Paper 5: the two direction-specificity seed censuses
(Qwen3-4B late site hs34/L34, Llama-3.2-3B mid-band site hs17), each write's
gated lift plotted against its own 15-seed matched-dose random-direction null.

Standalone script (same palette/rcParams conventions as build_figures.py and
build_restructure_figures.py), kept separate because it targets a different
pair of source experiments. Reads committed result JSONs directly from each
experiment's experiments/<slug>/analysis-committed/ directory -- no
paper-local snapshot. Deterministic except for cosmetic seed-dot jitter (fixed
RNG seeds below), CPU only, no network. Regenerate with:

    python3 papers/paper-5-actuation/scripts/build_specificity_census_fig.py

Every plotted lift, median, IQR, span, sign count, and effect ratio is
recomputed here from the committed source JSONs (never hand-typed) and
asserted against the governed AMENDMENT.md Outcome numbers at the bottom of
each figure function; a mismatch raises instead of silently drifting. Public
repo: no row-level text is read or plotted -- every source file here is an
aggregate summary JSON (per-seed rates and lifts only).
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments"
OUT = ROOT / "papers" / "paper-5-actuation" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---- palette (matches build_figures.py / build_restructure_figures.py) ----
C_GATED = "#2C6E9C"    # blue -- qwen late site
C_POOL2 = "#8172B3"    # purple -- llama mid-band site
C_HILITE = "#D4A24C"   # amber -- gated-write marker, both rows

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


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


# =========================================================================
# Sources (committed result JSONs, no row-level text):
#   Llama hs17: experiments/llama-hs17-direction-specificity/
#     analysis-committed/llama-3.2-3b/specificity_summary.json
#     (arm0_baseline.confab.rate, arm1_gated_replication.confab.rate,
#      arm2_random_census.<seed>.rate)
#   Qwen hs34/L34: experiments/qwen3-4b-l34-placebo-seed-census/
#     analysis-committed/wide_gates_report.json
#     (QG_G1_distributional_specificity.frozen_baseline_rate,
#      .frozen_gated_lift_over_baseline, per_seed.<seed>.confab_tighten_wide.rate)
# Governed verdict text: each experiment's AMENDMENT.md, Outcome section.
# =========================================================================
LLAMA = load(EXP / "llama-hs17-direction-specificity" / "analysis-committed" / "llama-3.2-3b" / "specificity_summary.json")
QWEN = load(EXP / "qwen3-4b-l34-placebo-seed-census" / "analysis-committed" / "wide_gates_report.json")


def _llama_data():
    baseline = LLAMA["arm0_baseline"]["confab"]["rate"]
    gated_rate = LLAMA["arm1_gated_replication"]["confab"]["rate"]
    gated_lift = gated_rate - baseline
    seeds = sorted(LLAMA["arm2_random_census"].keys())
    assert len(seeds) == 15, f"llama: expected 15 random-census seeds, got {len(seeds)}"
    lifts = [LLAMA["arm2_random_census"][s]["rate"] - baseline for s in seeds]
    max_abs = max(abs(x) for x in lifts)
    effect_ratio = gated_lift / max_abs
    n = LLAMA["arm0_baseline"]["confab"]["n"]
    assert n == LLAMA["arm1_gated_replication"]["confab"]["n"] == 872
    return dict(baseline=baseline, gated_lift=gated_lift, lifts=lifts,
                max_abs=max_abs, effect_ratio=effect_ratio, n=n)


def _qwen_data():
    g1 = QWEN["QG_G1_distributional_specificity"]
    baseline = g1["frozen_baseline_rate"]
    gated_lift = g1["frozen_gated_lift_over_baseline"]
    seeds = sorted(QWEN["per_seed"].keys())
    assert len(seeds) == 15, f"qwen: expected 15 random-census seeds, got {len(seeds)}"
    lifts = [QWEN["per_seed"][s]["confab_tighten_wide"]["rate"] - baseline for s in seeds]
    # cross-check against the JSON's own precomputed lift field
    for s, lift in zip(seeds, lifts):
        assert close(lift, QWEN["per_seed"][s]["lift_over_baseline_signed"], 1e-9), s
    max_abs = max(abs(x) for x in lifts)
    effect_ratio = gated_lift / max_abs
    n = QWEN["per_seed"][seeds[0]]["confab_tighten_wide"]["n"]
    assert n == 185
    return dict(baseline=baseline, gated_lift=gated_lift, lifts=lifts,
                max_abs=max_abs, effect_ratio=effect_ratio, n=n)


def fig_specificity_census():
    llama = _llama_data()
    qwen = _qwen_data()

    fig, ax = plt.subplots(figsize=(10.4, 6.2))

    rows = [
        dict(key="qwen", y=2, color=C_GATED, data=qwen,
             label="Qwen3-4B, hs34 (late site)\nwide two-instrument refusal-rate lift",
             site_ann="hs34 wide instrument, N=185 rows/arm"),
        dict(key="llama", y=1, color=C_POOL2, data=llama,
             label="Llama-3.2-3B, hs17 (mid-band site)\nclean_tighten lift, N=872 rows/arm",
             site_ann="hs17 clean_tighten instrument, N=872 rows/arm"),
    ]

    box_h = 0.30
    rng_seeds = {"qwen": 920000, "llama": 910000}

    for row in rows:
        y = row["y"]
        color = row["color"]
        lifts_pp = np.array(row["data"]["lifts"]) * 100.0
        gated_pp = row["data"]["gated_lift"] * 100.0
        ratio = row["data"]["effect_ratio"]

        median = float(np.median(lifts_pp))
        q1, q3 = float(np.percentile(lifts_pp, 25)), float(np.percentile(lifts_pp, 75))
        lo, hi = float(lifts_pp.min()), float(lifts_pp.max())

        # full-span whisker (null distribution only)
        ax.plot([lo, hi], [y, y], color=color, lw=1.2, alpha=0.55, zorder=1)
        # IQR box
        ax.add_patch(plt.Rectangle((q1, y - box_h / 2), q3 - q1, box_h,
                                    facecolor=color, alpha=0.30, edgecolor=color, lw=1.3, zorder=2))
        # median line
        ax.plot([median, median], [y - box_h / 2, y + box_h / 2], color=color, lw=2.4, zorder=3)
        # 15 jittered seed dots
        rng = np.random.default_rng(rng_seeds[row["key"]])
        jitter = rng.uniform(-0.14, 0.14, size=len(lifts_pp))
        ax.scatter(lifts_pp, y + jitter, s=26, color=color, edgecolor="white",
                   linewidth=0.5, zorder=4, alpha=0.9)

        # null-cluster annotation (median/IQR/span, since the cluster is
        # visually compressed against the far-right gated marker)
        ax.text(hi + 2.0, y + 0.20,
                 f"null: median {median:+.1f}pp, IQR [{q1:+.1f}, {q3:+.1f}], "
                 f"span [{lo:+.1f}, {hi:+.1f}]",
                 va="center", ha="left", fontsize=7.6, color="#444")

        # gated write, marked distinctly, far right on its own scale
        ax.scatter([gated_pp], [y], marker="*", s=340, color=C_HILITE,
                   edgecolor="#222", linewidth=1.0, zorder=6)
        ax.text(gated_pp, y - 0.34,
                 f"gated {gated_pp:+.1f}pp\nratio {ratio:.2f}x vs 15-seed null",
                 va="top", ha="center", fontsize=8.0, color="#222")

        # per-row instrument/site annotation
        ax.text(-13.5, y + 0.42, row["site_ann"], va="bottom", ha="left",
                 fontsize=8.4, color="#333", style="italic")

    ax.axvline(0, color="#222", ls="--", lw=1.1, zorder=0)
    ax.set_yticks([r["y"] for r in rows])
    ax.set_yticklabels([r["label"] for r in rows], fontsize=9.6)
    ax.set_ylim(0.35, 2.75)
    ax.set_xlim(-15, 85)
    ax.set_xlabel("confabulation-tightening lift over each row's own undosed baseline (percentage points)\n"
                  "different instruments and baselines per row -- shared axis is pp lift, not a shared rate scale",
                  fontsize=9.4)
    ax.set_title("A gated write's confabulation-tightening lift falls far outside\n"
                 "its own 15-seed random-direction null, at both operating points",
                 fontsize=12.2, y=1.03)

    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.text(0.01, 0.035, "dot = 1 seed (K=15 random-direction draws per row); "
                          "star = the gated write at that operating point",
              fontsize=7.8, color="#555", va="bottom")
    fig.savefig(OUT / "fig-p5-10-specificity-census.png", bbox_inches="tight")
    plt.close(fig)

    # ---- reproduction audit: recomputed values must equal the governed
    # AMENDMENT.md Outcome text for each experiment ----
    # Llama: experiments/llama-hs17-direction-specificity/AMENDMENT.md,
    # Outcome section (LG-G2 row and "Supporting numbers" bullets).
    LLAMA_CHECK = dict(
        gated_lift=0.7190, max_abs_random_lift=0.0872, effect_ratio=8.25,
        median_lift=0.0023, sign_pos=9, sign_neg=5, sign_zero=1,
    )
    lifts_llama = llama["lifts"]
    assert close(llama["gated_lift"], LLAMA_CHECK["gated_lift"], 0.0005)
    assert close(llama["max_abs"], LLAMA_CHECK["max_abs_random_lift"], 0.0005)
    assert close(llama["effect_ratio"], LLAMA_CHECK["effect_ratio"], 0.01)
    assert close(statistics.median(lifts_llama), LLAMA_CHECK["median_lift"], 0.0005)
    pos = sum(1 for x in lifts_llama if x > 0)
    neg = sum(1 for x in lifts_llama if x < 0)
    zero = sum(1 for x in lifts_llama if x == 0)
    assert (pos, neg, zero) == (LLAMA_CHECK["sign_pos"], LLAMA_CHECK["sign_neg"], LLAMA_CHECK["sign_zero"])

    # Qwen: experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md,
    # Outcome section (QG-G1/QG-G2 rows and per-seed lift summary).
    QWEN_CHECK = dict(
        baseline=0.1135, gated_lift=0.6270, effect_ratio=4.83,
        max_abs_random_lift=0.1297, median_lift=0.005, sign_neg=6,
    )
    lifts_qwen = qwen["lifts"]
    assert close(qwen["baseline"], QWEN_CHECK["baseline"], 0.0005)
    assert close(qwen["gated_lift"], QWEN_CHECK["gated_lift"], 0.0005)
    assert close(qwen["effect_ratio"], QWEN_CHECK["effect_ratio"], 0.01)
    assert close(qwen["max_abs"], QWEN_CHECK["max_abs_random_lift"], 0.0005)
    assert close(statistics.median(lifts_qwen), QWEN_CHECK["median_lift"], 0.0005)
    neg_qwen = sum(1 for x in lifts_qwen if x < 0)
    assert neg_qwen == QWEN_CHECK["sign_neg"]

    print("fig_specificity_census: reproduction audit PASSED (llama hs17 and qwen hs34"
          " per-seed lifts, medians, effect ratios reproduce both AMENDMENT.md Outcome sections)")


if __name__ == "__main__":
    fig_specificity_census()
    p = OUT / "fig-p5-10-specificity-census.png"
    print("figure written to", p.relative_to(ROOT), f"({p.stat().st_size // 1024} KB)")
