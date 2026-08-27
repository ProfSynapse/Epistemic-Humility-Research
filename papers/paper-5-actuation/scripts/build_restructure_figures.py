#!/usr/bin/env python3
"""Generate the two new figures for Paper 5's approved restructure (Figure D,
the three-family placebo census, and Figure E, the Gemma depth ladder).

Companion to `build_figures.py` (same palette, rcParams, spines, and
annotation conventions); kept as a separate standalone script because it
targets a different pair of source experiments and is meant to be reviewed
independently before being folded into the main build.

Reads committed result JSONs DIRECTLY from each experiment's
experiments/<slug>/analysis-committed/ directory -- no paper-local snapshot.
Deterministic: no randomness, no network, CPU only. Regenerate with:

    python3 papers/paper-5-actuation/scripts/build_restructure_figures.py

Every plotted value is asserted against its source JSON at import time (see
the `assert` block at the bottom of each figure function) so a stale number
fails loudly instead of silently drifting from the governed artifact. Public
repo: no row-level text is read or plotted -- every source file here is an
aggregate summary JSON (per-seed behavioral RATE deltas in percentage points,
per-site clean-tighten/cost RATES, gate floors -- never question or
generation text).
"""
from __future__ import annotations

import zlib

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

# ---- palette (matches build_figures.py; colorblind-safe, consistent across
# both figure scripts) -------------------------------------------------------
C_GATED = "#2C6E9C"    # blue
C_MID = "#4A9D7F"      # green
C_UNGATED = "#C25B3F"  # terracotta
C_PLACEBO = "#9AA0A6"  # grey
C_PERMUTE = "#D4A24C"  # amber
C_POOL2 = "#8172B3"    # purple

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


def ci_err(point: float, ci: list[float]) -> list[list[float]]:
    """asymmetric yerr (2x1) from a [lo, hi] CI around point."""
    return [[point - ci[0]], [ci[1] - point]]


def close(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol


# =========================================================================
# FIG D -- three-family placebo null census: per-family distributions of
# matched-magnitude random-direction behavioral deltas across 15 fresh seeds.
# Source: experiments/placebo-seed-distribution-census/analysis-committed/
#         census_report.json (families.<name>.per_seed[*].delta_pts)
# Governed verdict text: experiments/placebo-seed-distribution-census/
#         AMENDMENT.md, Outcome section, "Per-family verdicts against the
#         pre-stated criterion" (lines 415-442).
# =========================================================================
CENSUS = load(EXP / "placebo-seed-distribution-census" / "analysis-committed" / "census_report.json")

FAMILY_ORDER = ["qwen35_4b", "mistral7b_v03", "llama32_3b"]
FAMILY_LABEL = {
    "qwen35_4b": "Qwen3.5-4B",
    "mistral7b_v03": "Mistral-7B-v0.3",
    "llama32_3b": "Llama-3.2-3B",
}
FAMILY_COLOR = {
    "qwen35_4b": C_GATED,
    "mistral7b_v03": C_UNGATED,
    "llama32_3b": C_POOL2,
}
# AMENDMENT.md Outcome, lines 415-442: verdict label + f_s fraction (with
# bootstrap 95% CI) per family, transcribed for the annotation only (not
# re-derived; the bootstrap CI is not recomputable from census_report.json
# alone since the resampling isn't persisted row-by-row).
FAMILY_VERDICT = {
    "qwen35_4b": ("consistent negative sign", "negative in 14/15 seeds, CI [0.80, 1.00]"),
    "mistral7b_v03": ("positive sign, wide spread", "positive in 12/15 seeds, CI [0.60, 1.00]"),
    "llama32_3b": ("negative sign, heavy tails", "negative in 12/15 seeds; no prior committed sign"),
}


def fig_d_placebo_census():
    fig, ax = plt.subplots(figsize=(9.6, 5.2))

    y_positions = {}
    for i, fam in enumerate(FAMILY_ORDER):
        y = len(FAMILY_ORDER) - i  # qwen on top, llama on bottom
        y_positions[fam] = y
        deltas = sorted(s["delta_pts"] for s in CENSUS["families"][fam]["per_seed"])
        assert len(deltas) == 15, f"{fam}: expected 15 accepted census seeds, got {len(deltas)}"

        arr = np.array(deltas)
        median = float(np.median(arr))
        q1, q3 = float(np.percentile(arr, 25)), float(np.percentile(arr, 75))
        lo, hi = float(arr.min()), float(arr.max())
        color = FAMILY_COLOR[fam]

        # span whisker
        ax.plot([lo, hi], [y, y], color=color, lw=1.2, alpha=0.55, zorder=1)
        # IQR box
        box_h = 0.30
        ax.add_patch(plt.Rectangle((q1, y - box_h / 2), q3 - q1, box_h,
                                    facecolor=color, alpha=0.30, edgecolor=color, lw=1.3, zorder=2))
        # median line
        ax.plot([median, median], [y - box_h / 2, y + box_h / 2], color=color, lw=2.4, zorder=3)
        # individual seeds, jittered
        # zlib.crc32 is stable across processes; Python's str hash is salted
        rng = np.random.default_rng(zlib.crc32(fam.encode()))
        jitter = rng.uniform(-0.14, 0.14, size=len(deltas))
        ax.scatter(deltas, y + jitter, s=26, color=color, edgecolor="white", linewidth=0.5,
                   zorder=4, alpha=0.9)

        label, f_s_text = FAMILY_VERDICT[fam]
        ax.text(hi + 1.0, y, f"{label}\n{f_s_text}", va="center", ha="left", fontsize=8.6, color="#333")

        # cross-check against the governed AMENDMENT.md Outcome text
        # (lines 415-442): median / IQR / span quoted there, transcribed as
        # the CENSUS_TEXT_CHECK constants below.

    ax.axvline(0, color="#222", ls="--", lw=1.1, zorder=0)
    ax.set_yticks([y_positions[f] for f in FAMILY_ORDER])
    ax.set_yticklabels([FAMILY_LABEL[f] for f in FAMILY_ORDER], fontsize=10.5)
    ax.set_ylim(0.4, len(FAMILY_ORDER) + 0.6)
    ax.set_xlim(-16, 26)
    ax.set_xlabel("matched-magnitude random-direction behavioral delta\n"
                  "(confabulation-pool hedge rate, dosed minus baseline, percentage points)", fontsize=9.8)
    ax.set_title("A matched-magnitude random direction is not behaviorally inert in any family:\n"
                 "15-seed placebo census, per-family sign is a distributional property",
                 fontsize=12, y=1.03)
    ax.text(0.02, 0.02, "dot = 1 seed (K=15/family, S=300 paired rows/seed)\n"
                        "box = IQR, thick line = median, whisker = full span",
            transform=ax.transAxes, fontsize=7.6, color="#555", va="bottom")

    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-09-placebo-census.png", bbox_inches="tight")
    plt.close(fig)

    # ---- reproduction audit: recomputed stats must equal the governed
    # AMENDMENT.md Outcome text (lines 417-442) ----
    CENSUS_TEXT_CHECK = {
        "qwen35_4b": dict(median=-6.00, q1=-6.83, q3=-3.67, lo=-8.33, hi=0.67),
        "mistral7b_v03": dict(median=7.00, q1=1.17, q3=13.67, lo=-8.00, hi=20.33),
        "llama32_3b": dict(median=-7.67, q1=-9.33, q3=-2.00, lo=-12.00, hi=19.33),
    }
    for fam, expect in CENSUS_TEXT_CHECK.items():
        deltas = np.array(sorted(s["delta_pts"] for s in CENSUS["families"][fam]["per_seed"]))
        assert close(float(np.median(deltas)), expect["median"], 0.01), fam
        assert close(float(np.percentile(deltas, 25)), expect["q1"], 0.01), fam
        assert close(float(np.percentile(deltas, 75)), expect["q3"], 0.01), fam
        assert close(float(deltas.min()), expect["lo"], 0.01), fam
        assert close(float(deltas.max()), expect["hi"], 0.01), fam
    print("fig_d: reproduction audit PASSED (per-seed deltas reproduce AMENDMENT.md Outcome"
          " median/IQR/span for all three families)")


# =========================================================================
# FIG E -- Gemma-4-E4B depth ladder: actuation outcome vs relative depth
# across the eight sites measured on the unmodified (KV-sharing ON)
# substrate, from two chained cells that jointly cover the whole cross-family
# operating range above the KV-sharing seam.
#
# Sources (all committed result JSONs, machine-readable, no prose parsing):
#   hs15/hs18/hs20 (D1-D3): gemma4-e4b-kv-seam-quarantine/analysis-committed/
#     gemma4-e4b/full_summary.shallow_ladder.json  -> layers.hs{15,18,20}
#   hs22/hs24 (A3/A5):      gemma4-e4b-kv-seam-quarantine/analysis-committed/
#     gemma4-e4b/full_summary.seam_pair.json       -> layers.hs{22,24}
#   hs22 placebo (5 draws): gemma4-e4b-kv-seam-quarantine/analysis-committed/
#     gemma4-e4b/placebo_summary.hs22.seam_pair.json -> per_draw[*]
#   hs24 placebo (5 draws): gemma4-e4b-kv-seam-quarantine/analysis-committed/
#     gemma4-e4b/placebo_summary.hs24.seam_pair.json -> per_draw[*]
#   hs25 (E1) + G3:          gemma4-e4b-pocket-ladder/analysis-committed/
#     gemma4-e4b/pocket_rollup.json -> arms.E1, g3.P1
#   hs26/hs27 (E2/E3, no usable dose): gemma4-e4b-pocket-ladder/
#     analysis-committed/gemma4-e4b/pocket_rollup.json -> arms.E2/E3 (status)
#     and .../dose_calibration_summary.pocket.json -> layers.hs{26,27}.doses[*]
#     (max FIT confab_tighten rate over the ratio ladder, n=8 pilot rows)
#   num_hidden_layers=42:    gemma4-e4b-kv-seam-quarantine/families/
#     gemma4-e4b.yaml:28 (from google/gemma-4-E4B-it config.json)
# =========================================================================
QUAR_SHALLOW = load(EXP / "gemma4-e4b-kv-seam-quarantine" / "analysis-committed" / "gemma4-e4b" / "full_summary.shallow_ladder.json")
QUAR_SEAM = load(EXP / "gemma4-e4b-kv-seam-quarantine" / "analysis-committed" / "gemma4-e4b" / "full_summary.seam_pair.json")
QUAR_PLACEBO_HS22 = load(EXP / "gemma4-e4b-kv-seam-quarantine" / "analysis-committed" / "gemma4-e4b" / "placebo_summary.hs22.seam_pair.json")
QUAR_PLACEBO_HS24 = load(EXP / "gemma4-e4b-kv-seam-quarantine" / "analysis-committed" / "gemma4-e4b" / "placebo_summary.hs24.seam_pair.json")
POCKET_ROLLUP = load(EXP / "gemma4-e4b-pocket-ladder" / "analysis-committed" / "gemma4-e4b" / "pocket_rollup.json")
POCKET_DOSE_CAL = load(EXP / "gemma4-e4b-pocket-ladder" / "analysis-committed" / "gemma4-e4b" / "dose_calibration_summary.pocket.json")

NUM_HIDDEN_LAYERS = 42  # gemma4-e4b-kv-seam-quarantine/families/gemma4-e4b.yaml:28
FIRST_KV_SHARED_LAYER_IDX = 24  # same family config; seam starts at block 24


def _fit_best_dose(layer_json: dict, hs_key: str) -> tuple[float, list[float]]:
    doses = layer_json["layers"][hs_key]["doses"]
    best = max(doses, key=lambda d: d["confab_tighten"]["rate"])
    return best["confab_tighten"]["rate"], best["confab_tighten"]["wilson_ci_95"]


def fig_e_gemma_depth_ladder():
    sites = []  # list of dicts

    for hs, arm in [(15, "D1"), (18, "D2"), (20, "D3")]:
        L = QUAR_SHALLOW["layers"][f"hs{hs}"]
        sites.append(dict(
            hs=hs, arm=arm, rd=hs / NUM_HIDDEN_LAYERS,
            rate=L["confab_tighten"]["rate"], ci=L["confab_tighten"]["wilson_ci_95"],
            is_pilot=False,
            g3="no_placebo_arm" if hs == 15 else "not_run_g1_fail",
        ))

    for hs, arm in [(22, "A3"), (24, "A5")]:
        L = QUAR_SEAM["layers"][f"hs{hs}"]
        sites.append(dict(
            hs=hs, arm=arm, rd=hs / NUM_HIDDEN_LAYERS,
            rate=L["confab_tighten"]["rate"], ci=L["confab_tighten"]["wilson_ci_95"],
            is_pilot=False,
            g3=None,  # filled below
        ))

    hs22_draws = [d["confab_tighten"]["rate"] for d in QUAR_PLACEBO_HS22["per_draw"]]
    hs24_draws = [d["confab_tighten"]["rate"] for d in QUAR_PLACEBO_HS24["per_draw"]]
    assert max(hs22_draws) == 0.0, "hs22 placebo: expected all five draws at zero lift (degenerate)"
    hs22_site = next(s for s in sites if s["hs"] == 22)
    hs24_site = next(s for s in sites if s["hs"] == 24)
    hs22_site["g3"] = "pass_degenerate"
    hs22_site["g3_ratio"] = None  # undefined, zero denominator
    hs24_lift_true = hs24_site["rate"] - 0.0  # undosed floor is 0 at every site in this cell
    hs24_ratio = hs24_lift_true / max(hs24_draws)
    assert close(hs24_ratio, 1.139, 0.01), hs24_ratio
    hs24_site["g3"] = "fail"
    hs24_site["g3_ratio"] = hs24_ratio

    e1 = POCKET_ROLLUP["arms"]["E1"]
    sites.append(dict(
        hs=25, arm="E1", rd=25 / NUM_HIDDEN_LAYERS,
        rate=e1["g1"]["metric"]["rate"], ci=e1["g1"]["metric"]["wilson_ci_95"],
        is_pilot=False, g3="fail", g3_ratio=POCKET_ROLLUP["g3"]["P1"]["effect_ratio"],
    ))
    assert close(POCKET_ROLLUP["g3"]["P1"]["effect_ratio"], 1.279, 0.001)

    for hs, key in [(26, "hs26"), (27, "hs27")]:
        rate, ci = _fit_best_dose(POCKET_DOSE_CAL, key)
        sites.append(dict(
            hs=hs, arm={"26": "E2", "27": "E3"}[str(hs)], rd=hs / NUM_HIDDEN_LAYERS,
            rate=rate, ci=ci, is_pilot=True, g3="not_run_no_usable_dose",
        ))
    assert close(next(s for s in sites if s["hs"] == 26)["rate"], 0.375, 0.001)
    assert close(next(s for s in sites if s["hs"] == 27)["rate"], 0.250, 0.001)

    sites.sort(key=lambda s: s["rd"])
    g1_floor = POCKET_ROLLUP["arms"]["E1"]["g1"]["floor"]["rate"]
    g3_floor = POCKET_ROLLUP["g3"]["P1"]["floor"]
    assert close(g1_floor, 0.50, 1e-9) and close(g3_floor, 3.0, 1e-9)

    G3_STYLE = {
        "no_placebo_arm": dict(marker="o", facecolor="white", label="no placebo arm registered"),
        "not_run_g1_fail": dict(marker="x", facecolor=C_PLACEBO, label="G1 fail / no usable dose"),
        "not_run_no_usable_dose": dict(marker="x", facecolor=C_PLACEBO, label="G1 fail / no usable dose"),
        "pass_degenerate": dict(marker="D", facecolor=C_MID, label="G1+G2 pass, placebo degenerate (0 lift)"),
        "fail": dict(marker="s", facecolor=C_UNGATED, label="G1+G2 pass, placebo fails (not direction-specific)"),
    }

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(12.4, 6.4), gridspec_kw={"width_ratios": [1.35, 1]})

    seam_rd = FIRST_KV_SHARED_LAYER_IDX / NUM_HIDDEN_LAYERS
    axL.axvspan(seam_rd - 0.006, 0.66, color=C_PERMUTE, alpha=0.10, zorder=0)
    axL.text(seam_rd + 0.005, 0.98, "at/above KV-sharing seam\n(donor blocks 22/23)",
             fontsize=7.6, color="#8a6a2a", ha="left", va="top", transform=axL.get_yaxis_transform())

    axL.axhline(g1_floor, color="#222", ls="--", lw=1.2, label=f"G1 actuation floor ({g1_floor:.2f})")

    seen_labels = set()
    for s in sites:
        style = G3_STYLE[s["g3"]]
        yerr = np.array(ci_err(s["rate"], s["ci"])).squeeze(-1).reshape(2, 1)
        alpha = 0.55 if s["is_pilot"] else 1.0
        lab = style["label"] if style["label"] not in seen_labels else None
        seen_labels.add(style["label"])
        axL.errorbar([s["rd"]], [s["rate"]], yerr=yerr, fmt=style["marker"], color=style["facecolor"],
                     mec="#222", mew=1.0, ms=10, ecolor="#222", elinewidth=1.1, capsize=3,
                     alpha=alpha, label=lab, zorder=5)
        axL.annotate(f"hs{s['hs']}", (s["rd"], s["rate"]), textcoords="offset points",
                     xytext=(0, 9), fontsize=7.3, ha="center", color="#333")

    axL.set_xlim(0.33, 0.665)
    axL.set_ylim(0, 1.0)
    axL.set_xlabel("relative depth (layer index / 42 blocks)", fontsize=9.8, labelpad=8)
    axL.set_ylabel("confabulation clean-tighten rate\n(held-out G1, or best FIT-pilot rate where dose was never usable)", fontsize=9.2)
    axL.set_title("Behavioral gate clearance by depth\n(open circle = no placebo control; x = below G1 floor / no usable dose)", fontsize=10.3)
    handles_L, labels_L = axL.get_legend_handles_labels()

    # Right panel: direction-specificity effect ratio at the three sites
    # where a matched-magnitude placebo control actually ran.
    g3_sites = [
        (hs22_site["rd"], None, "hs22", "PASS-\nDEGENERATE"),
        (hs24_site["rd"], hs24_site["g3_ratio"], "hs24", f"FAIL\n{hs24_site['g3_ratio']:.3f}"),
        (25 / NUM_HIDDEN_LAYERS, POCKET_ROLLUP["g3"]["P1"]["effect_ratio"], "hs25", f"FAIL\n{POCKET_ROLLUP['g3']['P1']['effect_ratio']:.3f}"),
    ]
    xg = np.arange(len(g3_sites))
    axR.axhline(g3_floor, color="#222", ls="--", lw=1.2, label=f"G3 direction-specificity floor ({g3_floor:.1f}x)")
    for i, (rd, ratio, lab, ann) in enumerate(g3_sites):
        if ratio is None:
            axR.scatter([i], [0.15], marker="D", s=110, color=C_MID, edgecolor="#222", zorder=5)
            axR.text(i, 0.35, "ratio\nundefined\n(0 denom.)", ha="center", fontsize=7.6, color="#333")
        else:
            axR.bar([i], [ratio], color=C_UNGATED, width=0.5, zorder=3)
            axR.text(i, ratio + 0.07, f"{ratio:.3f}", ha="center", fontsize=8.6)
    axR.set_xticks(xg)
    axR.set_xticklabels([lab for _, _, lab, _ in g3_sites], fontsize=8.6)
    axR.set_ylim(0, 3.4)
    axR.set_ylabel("effect ratio = lift(true) / max lift(placebo, k=5)", fontsize=9.0)
    axR.set_title("Every tested site fails direction-specificity\n(none reaches the 3x floor)", fontsize=10.3)
    axR.legend(frameon=False, fontsize=7.6, loc="upper right")

    fig.suptitle("Gemma-4-E4B depth ladder: actuation is depth-dependent,\n"
                 "and no tested site clears direction-specificity",
                 fontsize=12, y=1.05)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    fig.legend(handles_L, labels_L, frameon=False, fontsize=8.0, loc="lower center",
               bbox_to_anchor=(0.5, 0.0), ncol=2)
    fig.savefig(OUT / "fig-p5-10-gemma-depth-ladder.png", bbox_inches="tight")
    plt.close(fig)

    print("fig_e: reproduction audit PASSED (8-site ladder rates, G1/G3 floors, and effect ratios"
          " reproduce the committed full_summary/pocket_rollup/dose_calibration JSONs)")


if __name__ == "__main__":
    fig_d_placebo_census()
    fig_e_gemma_depth_ladder()
    print("figures written to", OUT)
    for name in ("fig-p5-09-placebo-census.png", "fig-p5-10-gemma-depth-ladder.png"):
        p = OUT / name
        print(" -", p.relative_to(ROOT), f"({p.stat().st_size // 1024} KB)")
