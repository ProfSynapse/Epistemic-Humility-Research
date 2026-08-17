#!/usr/bin/env python3
"""Generate the three redo-list figures for the two-signal-readout paper
(Paper 4), per `docs/preparation/paper-4-restructure-outline.md` redo item 4.

Standalone companion to `build_figures.py`, same conventions (palette, rc
params, CI error bars, PASS/FAIL annotation), reading only committed /
on-disk-pinned artifacts:

  Figure A (fig-p4-08): per-family veto AUROC, three sampled seeds plus
    greedy as an open marker, against the 0.65 bar; companion panel
    contrasts the dial's across-seed spread with the veto's.
    Source: experiments/sampled-decode-seed-robustness/artifacts/*.json
    (12 files) and papers/paper-4-two-signal-readout/analysis/
    source-artifacts/probe/amendment_z_*.json (4 greedy cells).

  Figure B (fig-p4-09): gate/dial/veto across the era ladder ordered by the
    ladder's own year labels, with the 0.65 bar and the surface-text bound
    drawn on the gate series.
    Source: papers/paper-4-two-signal-readout/analysis/source-artifacts/
    probe/amendment_y_results/y-b-*.json (era ladder) and y-a-*.json
    (pretrain-only bases, Arm A "2026" rung) plus
    experiments/pretrain-only-base-readout/artifacts/
    amendment_y_text_baseline_result.json (TF-IDF surface bound).

  Figure C (fig-p4-10): veto decomposition waterfall (uncontrolled,
    length-only, carried-answerability, content-core-with-CI, plain dial as
    reference). Length-only, carried-answerability, and content-core are
    NOT recorded in any committed JSON (Amendments AM/AP report them only
    in AMENDMENT.md prose); this script pins them as literal constants with
    an exact file:line citation each, and a companion numbers table is
    written next to the figure so the pin is inspectable and diffable.

Deterministic: no randomness, no network, CPU only, no row-level text read
or emitted anywhere (all inputs here are already-aggregated AUROC/CI/mean
scalars). Regenerate with:

    python3 papers/paper-4-two-signal-readout/scripts/build_redo_figures.py

Every plotted number is asserted against its source value before saving
(reproduction audit) — the script raises rather than silently drifts.
"""
from __future__ import annotations

import csv
import glob
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "papers" / "paper-4-two-signal-readout"
PROBE = PAPER / "analysis" / "source-artifacts" / "probe"
Y_RESULTS = PROBE / "amendment_y_results"
SR_ARTIFACTS = ROOT / "experiments" / "sampled-decode-seed-robustness" / "artifacts"
Y_TEXT_BASELINE = (
    ROOT / "experiments" / "pretrain-only-base-readout" / "artifacts"
    / "amendment_y_text_baseline_result.json"
)
OUT = PAPER / "figures"
ANALYSIS = PAPER / "analysis"
OUT.mkdir(parents=True, exist_ok=True)

# ---- palette (matches build_figures.py) -----------------------------------
C_GATE = "#2C6E9C"
C_DIAL = "#4A9D7F"
C_VETO = "#C25B3F"
C_MUTE = "#9AA0A6"
C_TEXT_BOUND = "#8172B3"
THRESH = 0.65
CHANCE = 0.50
C_FAM = {
    "Llama-3.2-3B": "#4C72B0",
    "Ministral-3-3B": "#DD8452",
    "Qwen3.5-4B": "#55A868",
    "Gemma-4-E4B": "#8172B3",
}
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
    return [[point - ci[0]], [ci[1] - point]]


# =============================================================================
# FIGURE A (fig-p4-08) — per-family veto AUROC, sampled seeds + greedy
# =============================================================================

SEED_FILE_TAG = {
    "Llama-3.2-3B": "llama-3.2-3b",
    "Ministral-3-3B": "ministral-3-3b",
    "Qwen3.5-4B": "qwen3.5-4b",
    "Gemma-4-E4B": "gemma-4-e4b",
}
GREEDY_FILE_TAG = {
    "Llama-3.2-3B": "amendment_z_llama-3.2-3b_result.json",
    "Ministral-3-3B": "amendment_z_ministral-3-3b_result.json",
    "Qwen3.5-4B": "amendment_z_qwen3.5-4b_result.json",
    "Gemma-4-E4B": "amendment_z_gemma-4-e4b_result.json",
}

# Reproduction-audit targets: manuscript Table 2 (§4.10) mean [min-max] per
# family, and Table 1 (§4.8) greedy veto, rounded to 3dp as printed there.
EXPECTED_SEED_MEAN_RANGE = {
    "Llama-3.2-3B": (0.739, 0.684, 0.801),
    "Ministral-3-3B": (0.681, 0.606, 0.742),
    "Qwen3.5-4B": (0.753, 0.659, 0.807),
    "Gemma-4-E4B": (0.742, 0.718, 0.762),
}
EXPECTED_GREEDY = {
    "Llama-3.2-3B": 0.633,
    "Ministral-3-3B": 0.733,
    "Qwen3.5-4B": 0.666,
    "Gemma-4-E4B": 0.871,
}


def _load_seed_robustness() -> dict:
    """family -> list of (seed, veto_auroc, dial_auroc, source_path)."""
    out: dict[str, list] = {fam: [] for fam in SEED_FILE_TAG}
    for path in sorted(SR_ARTIFACTS.glob("amendment_sr_*_result.json")):
        d = load(path)
        m = re.search(r"amendment_sr_(.+)_seed(\d+)_result\.json", path.name)
        tag, seed = m.group(1), m.group(2)
        fam = next(f for f, t in SEED_FILE_TAG.items() if t == tag)
        veto = d["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"]
        dial = d["X_G2_dial"]["auroc_correct_vs_wrong"]
        out[fam].append((seed, veto, dial, path))
    for fam in out:
        out[fam].sort()
        assert len(out[fam]) == 3, f"expected 3 seeds for {fam}, got {len(out[fam])}"
    return out


def fig_a_seed_robustness():
    seed_data = _load_seed_robustness()
    fams = list(SEED_FILE_TAG)  # manuscript Table 2 order

    veto_seeds = {f: [v for _, v, _, _ in seed_data[f]] for f in fams}
    dial_seeds = {f: [dv for _, _, dv, _ in seed_data[f]] for f in fams}
    greedy = {}
    for f, fname in GREEDY_FILE_TAG.items():
        d = load(PROBE / fname)
        greedy[f] = d["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"]

    # ---- reproduction audit ----
    for f in fams:
        vs = veto_seeds[f]
        mean, lo, hi = sum(vs) / 3, min(vs), max(vs)
        exp_mean, exp_lo, exp_hi = EXPECTED_SEED_MEAN_RANGE[f]
        assert abs(mean - exp_mean) < 5e-4, f"{f} seed-veto mean drift: {mean} vs {exp_mean}"
        assert abs(lo - exp_lo) < 5e-4 and abs(hi - exp_hi) < 5e-4, (
            f"{f} seed-veto range drift: [{lo},{hi}] vs [{exp_lo},{exp_hi}]"
        )
        assert abs(round(greedy[f], 3) - EXPECTED_GREEDY[f]) < 5e-4, (
            f"{f} greedy veto drift: {greedy[f]} vs {EXPECTED_GREEDY[f]}"
        )

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11.6, 4.9), gridspec_kw={"width_ratios": [1.5, 1]})

    x = np.arange(len(fams))
    for i, f in enumerate(fams):
        c = C_FAM[f]
        vs = veto_seeds[f]
        axL.scatter([i] * 3, vs, marker="o", s=46, color=c, zorder=4,
                    label=None, edgecolors="white", linewidths=0.6)
        axL.scatter([i], [greedy[f]], marker="o", s=95, facecolors="none",
                    edgecolors=c, linewidths=1.8, zorder=5)
        axL.plot([i, i], [min(vs), max(vs)], "-", color=c, lw=1.2, alpha=0.5, zorder=2)

    # legend proxies
    axL.scatter([], [], marker="o", s=46, color="#444", label="sampled seed (3/family)")
    axL.scatter([], [], marker="o", s=95, facecolors="none", edgecolors="#444",
                linewidths=1.8, label="greedy decode (single decode)")
    axL.axhline(THRESH, ls="--", lw=1.1, color="#444", zorder=0)
    axL.text(len(fams) - 0.5, THRESH + 0.008, "pass bar 0.65", ha="right", va="bottom",
              fontsize=8.5, color="#444")
    axL.axhline(CHANCE, ls=":", lw=1.0, color=C_MUTE, zorder=0)
    axL.set_xticks(x)
    axL.set_xticklabels(fams, fontsize=9.5)
    axL.set_ylabel("hallucination-veto AUROC")
    axL.set_ylim(0.45, 0.95)
    axL.set_title("Per-family veto AUROC: sampled seeds vs. single greedy decode",
                  fontsize=10.8)
    axL.legend(frameon=False, fontsize=8.5, loc="lower right")

    # right panel: dial spread vs veto spread per family
    dial_ranges = [max(dial_seeds[f]) - min(dial_seeds[f]) for f in fams]
    veto_ranges = [max(veto_seeds[f]) - min(veto_seeds[f]) for f in fams]
    w = 0.35
    axR.bar(x - w / 2, dial_ranges, w, color=C_DIAL, label="dial range")
    axR.bar(x + w / 2, veto_ranges, w, color=C_VETO, label="veto range")
    for xi, v in zip(x - w / 2, dial_ranges):
        axR.text(xi, v + 0.003, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5)
    for xi, v in zip(x + w / 2, veto_ranges):
        axR.text(xi, v + 0.003, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5)
    axR.set_xticks(x)
    axR.set_xticklabels([f.split("-")[0] for f in fams], fontsize=9)
    axR.set_ylabel("across-seed AUROC range (max − min)")
    axR.set_ylim(0, 0.18)
    axR.set_title("Across-seed spread: dial 0.01–0.04 vs. veto 0.04–0.15\n"
                  "(Gemma's veto spread is the outlier, not in the 0.12–0.15 band)",
                  fontsize=9.6)
    axR.legend(frameon=False, fontsize=8.5, loc="upper left")

    fig.suptitle("Sampled-decode seed robustness: the two greedy veto misses (Llama, Qwen3.5)\n"
                 "flip to passes under sampling; the veto is decode-sensitive, the dial is not",
                 fontsize=11.6, y=1.05)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-08-seed-robustness-veto.png", bbox_inches="tight")
    plt.close(fig)
    print("  fig-p4-08: audit OK,", {f: (round(min(veto_seeds[f]), 3), round(max(veto_seeds[f]), 3)) for f in fams})


# =============================================================================
# FIGURE B (fig-p4-09) — era ladder: gate / dial / veto vs. release year label
# =============================================================================

# (label, year-label as printed in the governed table, source json or None if
# the row is an aggregate range not used for a single point)
ERA_LADDER_ROWS = [
    ("GPT-2-XL", "2019", Y_RESULTS / "y-b-gpt2-xl_result.json"),
    ("Pythia-2.8B", "2023", Y_RESULTS / "y-b-pythia-2.8b_result.json"),
    ("Llama-2-7B", "2023", Y_RESULTS / "y-b-llama-2-7b_result.json"),
    ("OLMo-2-7B", "2025", Y_RESULTS / "y-b-olmo-2-7b-local_result.json"),
]
# Arm A bases = the ladder's own "top rungs (2026)" grouping (AMENDMENT.md
# L292); k-shot / base rows only (chat-render control and the Olmo-3-Instruct
# sibling are controls, not ladder rungs).
ARM_A_RUNGS = [
    ("Qwen3.5-4B-Base", "2026", Y_RESULTS / "y-a-qwen3.5-4b-base-r3_result.json"),
    ("Gemma-4-E4B (pt)", "2026", Y_RESULTS / "y-a-gemma-4-e4b-pt-r2_result.json"),
    ("Llama-3.2-3B (base)", "2026", Y_RESULTS / "y-a-llama-3.2-3b-base_result.json"),
    ("Olmo-3-7B (base)", "2026", Y_RESULTS / "y-a-olmo-3-7b-base_result.json"),
]

EXPECTED_ERA = {
    "GPT-2-XL": (0.9911, 0.7940, 0.7936),
    "Pythia-2.8B": (0.9927, 0.8206, 0.7511),
    "Llama-2-7B": (0.9977, 0.8267, 0.8666),
    "OLMo-2-7B": (0.9982, 0.8580, 0.7752),
    "Qwen3.5-4B-Base": (0.9984, 0.8725, 0.6657),
    "Gemma-4-E4B (pt)": (0.9975, 0.8633, 0.8743),
    "Llama-3.2-3B (base)": (0.9972, 0.8235, 0.8354),
    "Olmo-3-7B (base)": (0.9975, 0.8442, 0.8029),
}


def fig_b_era_ladder():
    rows = ERA_LADDER_ROWS + ARM_A_RUNGS
    labels, years, gate, dial, veto, gate_ci, veto_ci = [], [], [], [], [], [], []
    for name, year, path in rows:
        d = load(path)
        g = d["X_G1_gate"]["answerability_auroc"]
        di = d["X_G2_dial"]["auroc_correct_vs_wrong"]
        v = d["X_G3_veto_PRIMARY"]["auroc_correct_vs_hallucination"]
        assert abs(g - EXPECTED_ERA[name][0]) < 5e-4, f"{name} gate drift"
        assert abs(di - EXPECTED_ERA[name][1]) < 5e-4, f"{name} dial drift"
        assert abs(v - EXPECTED_ERA[name][2]) < 5e-4, f"{name} veto drift"
        labels.append(name)
        years.append(year)
        gate.append(g)
        dial.append(di)
        veto.append(v)
        gate_ci.append(d["X_G1_gate"]["ci_95"])
        veto_ci.append(d["X_G3_veto_PRIMARY"]["ci_95"])

    tfidf = load(Y_TEXT_BASELINE)
    surf_mean = tfidf["gate_baseline_frozen_pool"]["tfidf_word_1_2"]["auroc_mean"]
    surf_std = tfidf["gate_baseline_frozen_pool"]["tfidf_word_1_2"]["auroc_std"]
    assert abs(surf_mean - 0.9639) < 1e-4 and abs(surf_std - 0.0159) < 1e-4, "TF-IDF bound drift"

    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(12.0, 5.2))

    ax.plot(x, gate, "-o", color=C_GATE, label="gate (answerability)", ms=7, zorder=4)
    ax.errorbar(x, gate, yerr=np.array([ci_err(v, c) for v, c in zip(gate, gate_ci)]).squeeze(-1).T,
                fmt="none", ecolor=C_GATE, elinewidth=0.9, capsize=2, alpha=0.6)
    ax.plot(x, dial, "-s", color=C_DIAL, label="dial (correctness)", ms=6, zorder=3)
    ax.plot(x, veto, "-^", color=C_VETO, label="veto (hallucination)", ms=7, zorder=3)
    ax.errorbar(x, veto, yerr=np.array([ci_err(v, c) for v, c in zip(veto, veto_ci)]).squeeze(-1).T,
                fmt="none", ecolor=C_VETO, elinewidth=0.9, capsize=2, alpha=0.6)

    # surface-text bound band on the gate series only
    ax.axhspan(surf_mean - surf_std, surf_mean + surf_std, color=C_TEXT_BOUND, alpha=0.14, zorder=0)
    ax.axhline(surf_mean, color=C_TEXT_BOUND, ls="-.", lw=1.1, zorder=1)
    ax.text(0.05, surf_mean - surf_std - 0.008,
            f"question-surface TF-IDF bound on the gate: {surf_mean:.3f} ± {surf_std:.3f}",
            ha="left", va="top", fontsize=8.5, color=C_TEXT_BOUND)

    ax.axhline(THRESH, ls="--", lw=1.1, color="#444", zorder=0)
    ax.text(len(labels) - 0.4, THRESH - 0.02, "pass bar 0.65", ha="right", va="top",
            fontsize=8.5, color="#444")

    ax.axvline(3.5, ls=":", lw=1.0, color=C_MUTE)
    ax.text(3.5, 0.47, " Arm A bases\n (paired instruct siblings)", fontsize=8, color=C_MUTE,
            ha="left", va="bottom")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}\n({y})" for n, y in zip(labels, years)], fontsize=8, rotation=20, ha="right")
    ax.set_ylabel("AUROC")
    ax.set_ylim(0.45, 1.03)
    ax.set_title("The readout predates post-training: gate/dial/veto across an era ladder\n"
                 "(descriptive, no era claim; ordered by the ladder's own release-year labels)",
                 fontsize=11.2)
    ax.legend(frameon=False, fontsize=9, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.32))
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-09-era-ladder.png", bbox_inches="tight")
    plt.close(fig)
    print("  fig-p4-09: audit OK, TF-IDF bound", surf_mean, "+/-", surf_std)


# =============================================================================
# FIGURE C (fig-p4-10) — veto decomposition waterfall
# =============================================================================
# Pinned constants. Length-only, carried-answerability, and content-core are
# NOT in any committed JSON (Amendments AM/AP report them only in
# AMENDMENT.md prose; scripts that produced AM's/AP's numbers are not
# committed artifacts under analysis-committed/, only the prose result). Each
# constant below cites its exact source file:line; the two "controlling
# cells" are AM (residual-catch-veto-coverage) and AP
# (ap-veto-length-balanced-confirmatory). Uncontrolled and plain-dial values
# ARE in committed JSONs and are loaded, not pinned.

W = load(PROBE / "amendment_w_base_model_result.json")
S = load(PROBE / "amendment_s_stage2_result.json")

UNCONTROLLED = W["W_G1_dial_on_hallucination_PRIMARY"]["auroc_scorrect_vs_hallucination"]
UNCONTROLLED_CI = W["W_G1_dial_on_hallucination_PRIMARY"]["ci_95"]
PLAIN_DIAL = S["headline"]["auroc_post"]

DECOMPOSITION = [
    {
        "component": "Uncontrolled (headline veto, raw base)",
        "auroc": UNCONTROLLED,
        "ci": UNCONTROLLED_CI,
        "source": "papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/amendment_w_base_model_result.json (W_G1_dial_on_hallucination_PRIMARY)",
        "source_line": None,
        "note": "correct-answerable vs confabulation-on-unanswerable, raw Qwen3-4B base",
    },
    {
        "component": "Length-only (answer length alone)",
        "auroc": 0.943,
        "ci": None,
        "source": "experiments/residual-catch-veto-coverage/AMENDMENT.md",
        "source_line": 429,
        "note": "residual-vs-good population (AM); answer-token median 94 vs 24, length alone separates at 0.943",
    },
    {
        "component": "Carried answerability (question-property carry-through)",
        "auroc": 0.99,
        "ci": None,
        "source": "experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md",
        "source_line": 142,
        "note": "confabs on unanswerable questions vs good answers, ~0.99, approximate as reported (no CI in source)",
    },
    {
        "component": "Content core (length- and answerability-controlled)",
        "auroc": 0.737,
        "ci": [0.650, 0.815],
        "source": "experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md",
        "source_line": 147,
        "note": "wrong-on-answerable vs correct-on-answerable, 65 matched pairs, out-of-fold",
    },
    {
        "component": "Plain dial (reference, correct vs wrong, no confabulation)",
        "auroc": PLAIN_DIAL,
        "ci": None,
        "source": "papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/amendment_s_stage2_result.json (headline.auroc_post)",
        "source_line": None,
        "note": "raw base, §4.2 headline; reference line, not part of the veto decomposition",
    },
]


def fig_c_veto_decomposition():
    assert abs(UNCONTROLLED - 0.7545) < 1e-4, "uncontrolled veto drift"
    assert abs(PLAIN_DIAL - 0.8342) < 1e-4, "plain dial drift"

    order = ["Uncontrolled (headline veto, raw base)", "Length-only (answer length alone)",
             "Carried answerability (question-property carry-through)",
             "Content core (length- and answerability-controlled)"]
    by_name = {r["component"]: r for r in DECOMPOSITION}
    rows = [by_name[n] for n in order]

    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    x = np.arange(len(rows))
    colors = [C_VETO, C_MUTE, C_MUTE, C_VETO]
    vals = [r["auroc"] for r in rows]
    bars = ax.bar(x, vals, 0.55, color=colors)
    for xi, r in zip(x, rows):
        if r["ci"] is not None:
            lo, hi = r["ci"]
            ax.errorbar([xi], [r["auroc"]], yerr=ci_err(r["auroc"], r["ci"]),
                        fmt="none", ecolor="#222", elinewidth=1.2, capsize=4)
            label = f"{r['auroc']:.3f}\nCI [{lo:.3f}, {hi:.3f}]"
            label_y = hi + 0.025
        else:
            label = f"{r['auroc']:.3f}\n(as reported)" if r["component"].startswith("Carried") else f"{r['auroc']:.3f}"
            label_y = r["auroc"] + 0.02
        ax.text(xi, label_y, label, ha="center", va="bottom", fontsize=8.5)

    # plain dial reference line (label placed in the gap between the two
    # nuisance bars, clear of every value/CI annotation above)
    dial_row = by_name["Plain dial (reference, correct vs wrong, no confabulation)"]
    ax.axhline(dial_row["auroc"], ls="--", lw=1.3, color=C_DIAL, zorder=0)
    ax.text(1.5, dial_row["auroc"] + 0.012,
            f"plain correctness dial (reference): {dial_row['auroc']:.3f}",
            ha="center", va="bottom", fontsize=8.5, color=C_DIAL)

    ax.axhline(THRESH, ls=":", lw=1.0, color="#444", zorder=0)
    ax.text(-0.45, THRESH + 0.01, "0.65", ha="left", va="bottom", fontsize=7.5, color="#444")

    ax.set_xticks(x)
    ax.set_xticklabels(["Uncontrolled\n(headline)", "Length-only\n(nuisance)",
                        "Carried\nanswerability\n(nuisance)", "Content core\n(both controlled)"],
                        fontsize=9)
    ax.set_ylabel("AUROC")
    ax.set_ylim(0, 1.08)
    ax.set_title("What the veto is made of: two nuisances and a content core\n"
                 "the surviving content signal (0.737) sits BELOW the plain correctness dial",
                 fontsize=11.4)
    fig.tight_layout()
    fig.savefig(OUT / "fig-p4-10-veto-decomposition.png", bbox_inches="tight")
    plt.close(fig)
    print("  fig-p4-10: audit OK,", {r["component"]: r["auroc"] for r in rows})

    # companion numbers table (required by the outline)
    table_path = ANALYSIS / "veto_decomposition_numbers.csv"
    with table_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["component", "auroc", "ci_lo", "ci_hi", "source_file", "source_line", "note"])
        for r in DECOMPOSITION:
            ci_lo, ci_hi = (r["ci"] if r["ci"] else ("", ""))
            w.writerow([r["component"], r["auroc"], ci_lo, ci_hi, r["source"], r["source_line"] or "", r["note"]])
    print("  wrote", table_path.relative_to(ROOT))


if __name__ == "__main__":
    print("Figure A (seed-robustness veto)...")
    fig_a_seed_robustness()
    print("Figure B (era ladder)...")
    fig_b_era_ladder()
    print("Figure C (veto decomposition)...")
    fig_c_veto_decomposition()
    print("\nfigures written to", OUT)
    for p in sorted(OUT.glob("fig-p4-0[89]*.png")) + sorted(OUT.glob("fig-p4-10*.png")):
        print(" -", p.relative_to(ROOT), f"({p.stat().st_size // 1024} KB)")
