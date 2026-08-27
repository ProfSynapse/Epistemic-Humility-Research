#!/usr/bin/env python3
"""Generate the figures for the actuation paper (Paper 5).

Reads committed result JSONs DIRECTLY from each experiment's
experiments/<slug>/analysis-committed/ directory under the repo's
experiments-first tree -- no paper-local snapshot is made, so there is a
single committed copy of every number this script plots. (Paper 4 copied its
source artifacts into a paper-local analysis/source-artifacts/ directory for
historical reasons -- those files predated the experiments-first layout and
had to be migrated out of a shared locked-matrix probe tree. Paper 5's cells
were built directly under experiments/<slug>/ from the start, so no such
migration is needed; see papers/paper-5-actuation/analysis/README.md.)

Deterministic: no randomness, no network, CPU only. Regenerate with:

    python3 papers/paper-5-actuation/scripts/build_figures.py

Every number in every figure traces to a specific source artifact named in
papers/paper-5-actuation/figures/MANIFEST.md. Public repo: no row-level text
is read or plotted -- every source file here is an aggregate summary JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments"
OUT = ROOT / "papers" / "paper-5-actuation" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---- palette (colorblind-safe, consistent across figures) ----------------
C_GATED = "#2C6E9C"    # the real uncertainty-gated instrument (blue)
C_MID = "#4A9D7F"      # mid-band write site (green)
C_LATE = "#2C6E9C"     # late-band / L34 write site (blue, matches C_GATED)
C_UNGATED = "#C25B3F"  # ungated / damage condition (terracotta)
C_PLACEBO = "#9AA0A6"  # random-direction / permuted-gate placebo (grey)
C_PERMUTE = "#D4A24C"  # permuted-gate placebo, distinguished from random-dir (amber)
C_POOL2 = "#8172B3"    # rep1 ceiling-saturated pool (purple, distinct from mid/late)
C_POOL3 = "#4A9D7F"    # rep2 multi-source pool reuses mid-band green (paired site colors instead)

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


# ---- source artifacts ------------------------------------------------------
HEADLINE = load(EXP / "doubt-gated-caution-tighten" / "analysis-committed" / "full_summary.json")
H4 = load(EXP / "ungated-vs-gated-dose-matched" / "analysis-committed" / "ungated_vs_gated_summary.json")
H3 = load(EXP / "snap-seed-sampled-decode-replication" / "analysis-committed" / "h3_summary.json")
POOL1 = load(EXP / "j-space-calibrated-layer-contrast-qwen3-4b" / "analysis-committed" / "full_summary.json")
REP1 = load(EXP / "j-space-layer-contrast-replication-qwen3-4b" / "analysis-committed" / "full_summary.json")
REP2 = load(EXP / "j-space-layer-contrast-rep2-multisource" / "analysis-committed" / "full_summary.json")
DOSE_CAL = load(EXP / "j-space-midband-dose-calibration-qwen3-4b" / "analysis-committed" / "dose_calibration_summary.json")
JLENS = load(EXP / "j-space-localization-qwen3-4b" / "analysis-committed" / "results" / "jspace-jlens-r1" / "profile_full.json")


# =========================================================================
# FIG 1 -- headline conversion vs known-correct cost at the resolved
# operating point (Qwen3-4B / L34=hs34), with the rep2 multi-source
# replication at the same write site alongside.
# =========================================================================
def fig1_headline_conversion():
    gated = HEADLINE["gated"]
    rand = HEADLINE["random_direction"]
    perm = HEADLINE["permuted_gate"]
    rep2_hs34 = REP2["layers"]["hs34"]

    groups = ["Uncertainty gate\noriginal pool", "Uncertainty gate\nrep2 multi-source",
              "Random-dir.\nplacebo", "Permuted-gate\nplacebo"]
    conv = [gated["confab_tighten"]["rate"], rep2_hs34["confab_tighten"]["rate"],
            rand["confab_tighten"]["rate"], perm["confab_tighten"]["rate"]]
    conv_ci = [gated["confab_tighten"]["wilson_ci_95"], rep2_hs34["confab_tighten"]["wilson_ci_95"],
               rand["confab_tighten"]["wilson_ci_95"], perm["confab_tighten"]["wilson_ci_95"]]
    cost = [gated["known_correct_cost_control"]["rate"], rep2_hs34["known_correct_cost_control"]["rate"],
            rand["known_correct_cost_control"]["rate"], perm["known_correct_cost_control"]["rate"]]
    cost_ci = [gated["known_correct_cost_control"]["wilson_ci_95"], rep2_hs34["known_correct_cost_control"]["wilson_ci_95"],
               rand["known_correct_cost_control"]["wilson_ci_95"], perm["known_correct_cost_control"]["wilson_ci_95"]]
    colors = [C_GATED, C_GATED, C_PLACEBO, C_PERMUTE]
    hatches = [None, "//", None, None]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.6, 4.8))
    x = np.arange(len(groups))

    for ax, vals, cis, ylabel, title, ylim in [
        (axL, conv, conv_ci, "confabulation clean-tighten rate", "Confabulations converted to clean refusals\n(higher = more boundary-push write does its job)", (0, 1.02)),
        (axR, cost, cost_ci, "known-correct false-refusal rate", "Known-correct rows wrongly refused\n(lower = write stays selective)", (0, 0.30)),
    ]:
        bars = ax.bar(x, vals, color=colors, width=0.62)
        for b, h in zip(bars, hatches):
            if h:
                b.set_hatch(h)
                b.set_edgecolor("white")
        yerr = np.array([ci_err(v, c) for v, c in zip(vals, cis)]).squeeze(-1).T
        ax.errorbar(x, vals, yerr=yerr, fmt="none", ecolor="#222", elinewidth=1.1, capsize=3)
        for xi, v in zip(x, vals):
            ax.text(xi, v + 0.015, f"{v*100:.1f}%", ha="center", va="bottom", fontsize=9)
        ax.set_xticks(x)
        ax.set_xticklabels(groups, fontsize=8.3)
        ax.set_ylabel(ylabel, fontsize=9.5)
        ax.set_ylim(*ylim)
        ax.set_title(title, fontsize=10)

    fig.suptitle("The uncertainty-gated boundary-push write: headline conversion replicates on an\n"
                 "independent multi-source pool at the same write site (Qwen3-4B, L34)",
                 fontsize=12, y=1.05)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-01-headline-conversion.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 2 -- H4: dose-matched ungated vs gated damage to held-out
# known-correct rows. The gate supplies the selectivity.
# =========================================================================
def fig2_gate_supplies_selectivity():
    g1 = H4["gates"]["h4_g1_gate_certifies_selectivity"]
    g2 = H4["gates"]["h4_g2_conversion_preserved"]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.6, 4.8))

    # Left: the selectivity story (known-correct damage)
    labels = ["Ungated\n(dosed every row)", "Gated\n(uncertainty gate fires only)"]
    vals = [g1["ungated_known_correct_damage"]["rate"], g1["gated_known_correct_damage"]["rate"]]
    cis = [g1["ungated_known_correct_damage"]["wilson_ci_95"], g1["gated_known_correct_damage"]["wilson_ci_95"]]
    x = np.arange(2)
    bars = axL.bar(x, vals, color=[C_UNGATED, C_GATED], width=0.55)
    yerr = np.array([ci_err(v, c) for v, c in zip(vals, cis)]).squeeze(-1).T
    axL.errorbar(x, vals, yerr=yerr, fmt="none", ecolor="#222", elinewidth=1.1, capsize=3)
    for xi, v in zip(x, vals):
        axL.text(xi, v + 0.02, f"{v*100:.1f}%", ha="center", va="bottom", fontsize=10.5, fontweight="bold")
    axL.set_xticks(x)
    axL.set_xticklabels(labels, fontsize=9.5)
    axL.set_ylabel("known-correct rows damaged\n(not-well-formed-correct)", fontsize=9.5)
    axL.set_ylim(0, 0.75)
    mc = H4["gates"]["h4_g1_gate_certifies_selectivity"]["mcnemar"]
    axL.set_title(f"Dosing every row damages knowns;\ngating the write nearly eliminates it\n"
                 f"(McNemar p = {mc['p_value']:.1e})", fontsize=10)

    # Right: parity check -- conversion is barely reduced by gating
    labels2 = ["Ungated", "Gated"]
    vals2 = [g2["ungated_confab_clean_tighten"]["rate"], g2["gated_confab_clean_tighten"]["rate"]]
    cis2 = [g2["ungated_confab_clean_tighten"]["wilson_ci_95"], g2["gated_confab_clean_tighten"]["wilson_ci_95"]]
    bars2 = axR.bar(x, vals2, color=[C_UNGATED, C_GATED], width=0.55)
    yerr2 = np.array([ci_err(v, c) for v, c in zip(vals2, cis2)]).squeeze(-1).T
    axR.errorbar(x, vals2, yerr=yerr2, fmt="none", ecolor="#222", elinewidth=1.1, capsize=3)
    for xi, v in zip(x, vals2):
        axR.text(xi, v + 0.02, f"{v*100:.1f}%", ha="center", va="bottom", fontsize=10.5, fontweight="bold")
    axR.set_xticks(x)
    axR.set_xticklabels(labels2, fontsize=9.5)
    axR.set_ylabel("confabulation clean-tighten rate", fontsize=9.5)
    axR.set_ylim(0, 1.02)
    diff_pp = -g2["difference_gated_minus_ungated"] * 100
    axR.set_title(f"...while conversion barely drops\n(gate gives up {diff_pp:.1f}pp of conversion)", fontsize=10)

    fig.suptitle("H4 dose-matched arm: the uncertainty gate supplies the write's selectivity,\n"
                 "not the write itself (Qwen3-4B, L34, dose 200, held-out rows)",
                 fontsize=12, y=1.06)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-02-ungated-vs-gated-h4.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 3 -- H3: per-seed conversion under sampled decoding (5 seeds) against
# the registered floor, showing the greedy headline survives.
# =========================================================================
def fig3_sampled_decode_replication():
    g1 = H3["gates"]["h3_g1"]
    g2 = H3["gates"]["h3_g2"]
    seeds = H3["seeds"]
    n_seed = len(seeds)

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.8, 4.8), sharex=False)

    # Left: per-seed majority-vote conversion vs floor, greedy reference
    conv = [g1["per_seed"][str(s)]["majority_vote"]["rate"] for s in seeds]
    conv_ci = [g1["per_seed"][str(s)]["majority_vote"]["wilson_ci_95"] for s in seeds]
    x = np.arange(1, n_seed + 1)
    yerr = np.array([ci_err(v, c) for v, c in zip(conv, conv_ci)]).squeeze(-1).T
    axL.errorbar(x, conv, yerr=yerr, fmt="o", color=C_GATED, ecolor=C_GATED,
                 elinewidth=1.2, capsize=3, ms=7, label="per-seed sampled majority vote")
    pooled = g1["pooled"]["majority_vote"]["rate"]
    axL.axhline(pooled, color=C_GATED, ls="-", lw=1.6, alpha=0.5, label=f"pooled {pooled*100:.1f}%")
    greedy = H3["resolved_reference"]["gated_confab_clean_tighten"]
    axL.axhline(greedy, color="#333", ls="-.", lw=1.3, label=f"greedy headline {greedy*100:.1f}%")
    axL.axhline(0.635, color=C_UNGATED, ls="--", lw=1.3, label="registered floor 63.5%")
    axL.set_xticks(x)
    axL.set_xlabel("seed")
    axL.set_ylabel("confab clean-tighten rate\n(majority vote of 8 samples/row)")
    axL.set_ylim(0.55, 0.85)
    axL.set_title("Conversion survives sampled decoding\nin all 5 seeds", fontsize=10.5)
    axL.legend(frameon=False, fontsize=7.6, loc="upper center",
               bbox_to_anchor=(0.5, -0.16), ncol=2)

    # Right: per-seed known-correct cost vs ceiling
    cost = [g2["per_seed"][str(s)]["majority_vote"]["rate"] for s in seeds]
    cost_ci = [g2["per_seed"][str(s)]["majority_vote"]["wilson_ci_95"] for s in seeds]
    yerr2 = np.array([ci_err(v, c) for v, c in zip(cost, cost_ci)]).squeeze(-1).T
    axR.errorbar(x, cost, yerr=yerr2, fmt="s", color=C_UNGATED, ecolor=C_UNGATED,
                 elinewidth=1.2, capsize=3, ms=7, label="per-seed sampled majority vote")
    pooled_c = g2["pooled"]["majority_vote"]["rate"]
    axR.axhline(pooled_c, color=C_UNGATED, ls="-", lw=1.6, alpha=0.5, label=f"pooled {pooled_c*100:.2f}%")
    axR.axhline(0.08, color="#333", ls="--", lw=1.3, label="registered ceiling 8%")
    axR.set_xticks(x)
    axR.set_xlabel("seed")
    axR.set_ylabel("known-correct false-refusal rate\n(majority vote of 8 samples/row)")
    axR.set_ylim(0, 0.13)
    axR.set_title("Known-correct cost stays low\nunder sampled decoding", fontsize=10.5)
    axR.legend(frameon=False, fontsize=7.6, loc="upper center",
               bbox_to_anchor=(0.5, -0.16), ncol=1)

    fig.suptitle("H3: multi-seed, sampled-decode (temperature 0.7) replication of the\n"
                 "uncertainty-gated boundary-push snap -- the greedy headline is not a decoding artifact",
                 fontsize=12, y=1.05)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-03-h3-sampled-decode.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 4 -- dose ladder / dose-response at the primary (late, L34=hs34) write
# site, from the FIT-only calibration sweep (pilot scale, n=8 confab / n=8
# known-correct rows per dose point -- disclosed, not held-out evaluation).
# =========================================================================
def fig4_dose_response():
    hs34 = DOSE_CAL["layers"]["hs34"]
    doses = DOSE_CAL["doses"]
    n_confab = hs34["n_confab_fit_rows"]
    n_known = hs34["n_known_fit_rows"]

    tighten = [d["confab_tighten"]["rate"] for d in hs34["doses"]]
    tighten_ci = [d["confab_tighten"]["wilson_ci_95"] for d in hs34["doses"]]
    cost = [d["known_correct_cost_control"]["rate"] for d in hs34["doses"]]
    cost_ci = [d["known_correct_cost_control"]["wilson_ci_95"] for d in hs34["doses"]]
    collapse = [d["collapse_rate_on_dosed"] for d in hs34["doses"]]
    selected = DOSE_CAL["selected_doses"]["hs34"]

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    x = np.array(doses)

    yerr_t = np.array([ci_err(v, c) for v, c in zip(tighten, tighten_ci)]).squeeze(-1).T
    ax.errorbar(x, tighten, yerr=yerr_t, fmt="-o", color=C_LATE, ecolor=C_LATE,
                elinewidth=1.1, capsize=3, ms=6, label="confab clean-tighten rate")
    yerr_c = np.array([ci_err(v, c) for v, c in zip(cost, cost_ci)]).squeeze(-1).T
    ax.errorbar(x, cost, yerr=yerr_c, fmt="-s", color=C_UNGATED, ecolor=C_UNGATED,
                elinewidth=1.1, capsize=3, ms=6, label="known-correct cost rate")

    # collapse rate on a twin axis (readback-invalid fraction of dosed rows)
    axT = ax.twinx()
    axT.plot(x, collapse, ":", color="#888", lw=1.3, marker="x", ms=5, label="collapse rate on dosed rows")
    axT.set_ylabel("collapse rate on dosed rows", color="#888", fontsize=9)
    axT.tick_params(axis="y", colors="#888")
    axT.set_ylim(-0.06, 1.30)

    ax.axvline(selected, color="#333", ls="--", lw=1.2, alpha=0.7)
    ax.text(selected + 3, 0.95, f"selected dose = {selected:g}", fontsize=8.5, color="#333")
    ax.set_xlabel("write dose (magnitude along the boundary-push direction)")
    ax.set_ylabel("rate")
    ax.set_ylim(-0.02, 1.08)
    ax.set_xticks(doses)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = axT.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=8.3, loc="upper left")
    ax.set_title(f"Dose response at the primary write site (L34 / hs34, Qwen3-4B)\n"
                 f"FIT calibration sweep, pilot scale: n={n_confab} confab / n={n_known} known-correct rows per dose point",
                 fontsize=11, pad=12)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-04-dose-response.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 5 -- localization: (A) the read-only J-lens workspace-dimensionality
# band, (B) the write-site behavioral effect across layers on three disjoint
# pools, showing the effect direction holds but magnitude/ordering is
# pool-dependent.
# =========================================================================
def fig5_localization():
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.4, 4.9))

    # A: J-lens effective-dimension profile (read-only diagnostic)
    layers = sorted(int(k) for k in JLENS["per_layer"])
    eff_dim = [JLENS["per_layer"][str(l)]["effective_dim_frac_mean"] for l in layers]
    axA.plot(layers, eff_dim, "-o", color="#555", ms=5, lw=1.6)
    axA.axvspan(23, 29, color=C_MID, alpha=0.15, label="workspace-like band (hs 23-29)")
    peak_l = layers[int(np.argmax(eff_dim))]
    axA.plot([peak_l], [max(eff_dim)], "o", color=C_MID, ms=9, zorder=5)
    # headroom scaled to the data span so the peak annotation and legend fit
    # inside the axes instead of spilling into the title
    span = max(eff_dim) - min(eff_dim)
    axA.set_ylim(top=max(eff_dim) + span * 0.30)
    axA.text(peak_l, max(eff_dim) + span * 0.07, f"peak hs={peak_l}", ha="center", fontsize=8.5, color=C_MID)
    axA.axvline(34, color=C_LATE, ls="--", lw=1.3, alpha=0.8)
    axA.text(34.3, max(eff_dim) * 0.55, "L34 write\nsite", fontsize=8, color=C_LATE)
    axA.set_xlabel("layer (hs index)")
    axA.set_ylabel("effective dimension (fraction of hidden dim)")
    axA.set_title("Read-only diagnostic: a workspace-like\nlow-dimensional band, read-only, no gates", fontsize=10, pad=10)
    axA.legend(frameon=False, fontsize=8, loc="upper right")

    # B: write-site behavioral localization across 3 disjoint pools
    hs_sites = [23, 26, 29, 34]
    xlab = [f"hs{h}" for h in hs_sites]
    pools = [
        ("original pool (n=185 confab)", POOL1, C_GATED, "-o"),
        ("rep1, ceiling-saturated pool (n=306)", REP1, C_POOL2, "-^"),
        ("rep2, multi-source pool (n=221)", REP2, C_MID, "-s"),
    ]
    xi = np.arange(len(hs_sites))
    for label, data, color, style in pools:
        rates = [data["layers"][f"hs{h}"]["confab_tighten"]["rate"] for h in hs_sites]
        axB.plot(xi, rates, style, color=color, lw=1.8, ms=6, label=label)
    axB.set_xticks(xi)
    axB.set_xticklabels(xlab)
    axB.set_xlabel("write site")
    axB.set_ylabel("confab clean-tighten rate")
    axB.set_ylim(0.55, 1.02)
    axB.set_title("Write-site effect: direction holds on all three pools;\n"
                 "magnitude and within-band ordering are pool-dependent", fontsize=10)
    axB.legend(frameon=False, fontsize=7.6, loc="lower left")

    fig.suptitle("Localization: the workspace-like band (A, read-only) versus where the\n"
                 "boundary-push write actually acts (B, behavioral, three disjoint pools)",
                 fontsize=12, y=1.05)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-05-localization.png", bbox_inches="tight")
    plt.close(fig)


# =========================================================================
# FIG 6 -- the propensity-push null (Section 4.2, amendment AL). No
# analysis-committed/ result JSON exists for this experiment: the only
# committed artifacts are AMENDMENT.md itself and the pre-registration
# ceiling-simulation script (radial_ceiling_sim.py, which sets the gate
# thresholds, not the observed outcome). Every number below is hand-
# transcribed from the signed amendment's frontmatter `outcome:` field and
# Section 3.3 / Section 4 (verified directly against that doc, not against
# the rewrite's coordination note). The permuted-control raw kill count is
# not separately stated in the doc; it is derived by exact arithmetic from
# two numbers that ARE stated (primary kills = 0 of 116; primary-minus-
# control kill difference = 0, CI [0.00, 0.00]) -- both arms share the same
# n=116 baseline-confab denominator per the outcome text, so a precise-zero
# difference against a zero primary forces the control count to zero too.
# =========================================================================
AL_PRIMARY_KILLS = 0          # of 116 baseline confabs (outcome: "AL-G2 MISS (0 of 116...")
AL_N_CONFAB = 116
AL_CONTROL_KILLS = 0          # derived: primary(0) - diff(0) = control(0); see docstring note above
AL_DOSE_LADDER_LABELS = ["0.5x", "1.0x (primary)", "2.0x"]
AL_DOSE_LADDER_KILLS = [0, 0, 1]   # of 30 pushed confabs each (outcome: "dose ladder 0.5x/1.0x/2.0x kills 0/0/1")
AL_DOSE_LADDER_N = 30
AL_COLLATERAL_FLIPS = 0       # of 90 baseline-correct rows (AL-G1: "collateral 0 of allowed 3")
AL_COLLATERAL_N = 90
AL_COLLATERAL_CEILING = 3
AL_COMMANDED_PUSH = -2.7110   # Section: "read-back check... moved -2.7133 against a commanded -2.7110"
AL_REALIZED_PUSH = -2.7133
AL_UNPUSHED_SHIFT = 0.0000
AL_UNPUSHED_PARITY_N = 1564   # of 1564 unpushed rows (1662 total - 98 pushed)
AL_UNPUSHED_PARITY_TOTAL = 1564

C_NULL = "#6B6B6B"  # distinct neutral tone for the AL null: different checkpoint (AI-TRUE,
                    # GRPO-trained) and different direction (confab-propensity, not c_hat)
                    # than every other figure in this paper -- deliberately NOT C_GATED/C_MID/C_LATE


def fig6_propensity_null():
    fig, (axL, axM, axR) = plt.subplots(1, 3, figsize=(12.6, 4.8))

    # Left: primary vs permuted-control kill rate (the reach/specificity gates)
    labels = ["Primary\n(propensity push)", "Permuted-assignment\ncontrol"]
    kills = [AL_PRIMARY_KILLS, AL_CONTROL_KILLS]
    rates = [k / AL_N_CONFAB for k in kills]
    x = np.arange(2)
    axL.bar(x, rates, color=[C_NULL, C_PLACEBO], width=0.55)
    for xi, k in zip(x, kills):
        axL.text(xi, 0.02, f"{k}/{AL_N_CONFAB}", ha="center", va="bottom", fontsize=10.5, fontweight="bold")
    axL.set_xticks(x)
    axL.set_xticklabels(labels, fontsize=9.5)
    axL.set_ylabel("confab kill rate (of 116 baseline confabs)")
    axL.set_ylim(0, 0.20)
    axL.set_title("Reach and specificity both miss:\nprimary minus control kill diff = 0,\n"
                  "bootstrap 95% CI [0.00, 0.00]", fontsize=10)

    # Middle: dose ladder on the 30 pushed confabs
    xi2 = np.arange(3)
    dose_rates = [k / AL_DOSE_LADDER_N for k in AL_DOSE_LADDER_KILLS]
    axM.bar(xi2, dose_rates, color=C_NULL, width=0.5)
    for xi_, k in zip(xi2, AL_DOSE_LADDER_KILLS):
        axM.text(xi_, dose_rates[xi_] + 0.01, f"{k}/{AL_DOSE_LADDER_N}", ha="center", va="bottom", fontsize=9.5)
    axM.set_xticks(xi2)
    axM.set_xticklabels(AL_DOSE_LADDER_LABELS, fontsize=8.8)
    axM.set_ylabel("confab kill rate (of 30 pushed confabs)")
    axM.set_ylim(0, 0.15)
    axM.set_title(f"Dose ladder on pushed confabs:\nno reach even at 2x the\ncalibrated magnitude", fontsize=10)
    axM.text(1.0, 0.13, f"collateral: {AL_COLLATERAL_FLIPS}/{AL_COLLATERAL_N} known-correct\nflipped (ceiling {AL_COLLATERAL_CEILING})",
              ha="center", fontsize=8, color="#555")

    # Right: read-back verification -- commanded vs realized push, pushed vs unpushed shift
    xi3 = np.arange(2)
    commanded_vs_realized = [abs(AL_COMMANDED_PUSH), abs(AL_REALIZED_PUSH)]
    axR.bar(xi3, commanded_vs_realized, color=[C_PLACEBO, C_NULL], width=0.45)
    for xi_, v in zip(xi3, commanded_vs_realized):
        axR.text(xi_, v + 0.03, f"{v:.4f}", ha="center", va="bottom", fontsize=9.5)
    axR.set_xticks(xi3)
    axR.set_xticklabels(["commanded", "realized\n(pushed rows)"], fontsize=9)
    axR.set_ylabel("propensity-direction push magnitude")
    axR.set_ylim(0, 3.3)
    ratio = AL_REALIZED_PUSH / AL_COMMANDED_PUSH
    axR.set_title(f"The push landed on target\n(ratio {ratio:.4f}); unpushed rows shift\n"
                  f"{AL_UNPUSHED_SHIFT:.4f}, {AL_UNPUSHED_PARITY_N}/{AL_UNPUSHED_PARITY_TOTAL} parity", fontsize=10)

    fig.suptitle("The confabulation-propensity direction reads and moves as commanded, but does\n"
                 "not actuate the fabricate-vs-refuse choice (AI-TRUE checkpoint, use-the-signal null)",
                 fontsize=12, y=1.06)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p5-06-propensity-null.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1_headline_conversion()
    fig2_gate_supplies_selectivity()
    fig3_sampled_decode_replication()
    fig4_dose_response()
    fig5_localization()
    fig6_propensity_null()
    print("figures written to", OUT)
    for p in sorted(OUT.glob("*.png")):
        print(" -", p.relative_to(ROOT), f"({p.stat().st_size // 1024} KB)")
