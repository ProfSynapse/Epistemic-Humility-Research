#!/usr/bin/env python3
"""Generate Figure 10 for Paper 5: the instruction-amplification picture the
Section 5 scope note states in prose. One bar per family: the gated write's
two-stage held-out abstention lift with NO abstention instruction in the
prompt (95% CI); amber diamonds mark the with-instruction lift at the parent
operating point for the two families whose parents measured the same
construction (Qwen3-4B and Llama-3.2-3B).

Standalone script (same palette/rcParams conventions as build_figures.py and
build_specificity_census_fig.py). Reads the committed aggregate summary from
experiments/no-abstention-prompt-gated-replication/analysis-committed/ (no
row-level text anywhere in the pipeline). Every plotted lift and CI is
recomputed here from the committed counts and asserted against the governed
AMENDMENT.md Outcome numbers; a mismatch raises instead of silently
drifting. The two with-instruction reference lifts are the gates.yaml
derivation values (with-prompt gated lift 0.891892 for Qwen3-4B from its
parent Outcome; 0.719037 for Llama hs17), asserted below. Deterministic,
CPU only, no network. Regenerate with:

    python3 papers/paper-5-actuation/scripts/build_instruction_amplification_fig.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
SRC = (
    ROOT
    / "experiments"
    / "no-abstention-prompt-gated-replication"
    / "analysis-committed"
    / "two_stage_family_summary.json"
)
OUT = ROOT / "papers" / "paper-5-actuation" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ---- palette (matches build_figures.py / build_specificity_census_fig.py) --
C_GATED = "#2C6E9C"   # blue -- instruction-free gated lift bars
C_HILITE = "#D4A24C"  # amber -- with-instruction reference diamonds

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

# Display order (descending instruction-free lift) and labels.
ORDER = [
    ("gemma-4-e4b", "Gemma-4-E4B"),
    ("qwen3.5-4b", "Qwen3.5-4B"),
    ("mistral-7b-v0.3", "Mistral-7B-v0.3"),
    ("qwen3-4b", "Qwen3-4B"),
    ("llama-3.2-3b", "Llama-3.2-3B"),
]

# With-instruction gated lifts at the parent operating points, exactly as
# derived in the cell's gates.yaml (G1: 165/185 = 0.891892 parent held-out
# abstention over a structurally-zero no_op baseline; G1b: 635/872 minus
# 8/872 = 0.719037). Only these two families' parents measured the same
# gated construction under the instruction.
WITH_INSTRUCTION = {"qwen3-4b": 0.891892, "llama-3.2-3b": 0.719037}

# Governed AMENDMENT.md Outcome lifts and 95% CIs (percentage points),
# assertion targets only.
AMENDMENT = {
    "gemma-4-e4b": (47.0, 37.1, 55.5),
    "qwen3.5-4b": (45.6, 42.4, 48.6),
    "mistral-7b-v0.3": (18.8, 15.8, 21.8),
    "qwen3-4b": (11.4, 7.0, 16.7),
    "llama-3.2-3b": (9.3, 6.7, 12.0),
}


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - half, center + half


def newcombe(k1: int, n1: int, k0: int, n0: int) -> tuple[float, float, float]:
    """Newcombe-Wilson CI for p1 - p0 (the cell's registered CI method)."""
    d = k1 / n1 - k0 / n0
    l1, u1 = wilson(k1, n1)
    l0, u0 = wilson(k0, n0)
    lo = d - math.sqrt((k1 / n1 - l1) ** 2 + (u0 - k0 / n0) ** 2)
    hi = d + math.sqrt((u1 - k1 / n1) ** 2 + (k0 / n0 - l0) ** 2)
    return d, lo, hi


def main() -> None:
    fams = json.loads(SRC.read_text())["families"]
    labels, lifts, lo_err, hi_err = [], [], [], []
    for slug, label in ORDER:
        arms = fams[slug]["arms"]
        g, b = arms["gated"], arms["no_op"]
        d, lo, hi = newcombe(
            g["two_stage_refused"], g["heldout_confab_n"],
            b["two_stage_refused"], b["heldout_confab_n"],
        )
        want, want_lo, want_hi = AMENDMENT[slug]
        for got, exp in ((d, want), (lo, want_lo), (hi, want_hi)):
            assert abs(got * 100 - exp) < 0.15, (slug, got * 100, exp)
        labels.append(label)
        lifts.append(d * 100)
        lo_err.append((d - lo) * 100)
        hi_err.append((hi - d) * 100)

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    x = range(len(labels))
    ax.bar(
        x, lifts, width=0.58, color=C_GATED,
        yerr=[lo_err, hi_err], capsize=4,
        error_kw={"elinewidth": 1.2, "ecolor": "#333333"},
        label="gated write, no abstention instruction (95% CI)",
        zorder=3,
    )
    ref_x = [i for i, (slug, _) in enumerate(ORDER) if slug in WITH_INSTRUCTION]
    ref_y = [WITH_INSTRUCTION[ORDER[i][0]] * 100 for i in ref_x]
    ax.scatter(
        ref_x, ref_y, marker="D", s=70, color=C_HILITE,
        edgecolor="#333333", linewidth=0.8,
        label="same construction with the instruction (parent operating point)",
        zorder=4,
    )
    for i, y in zip(ref_x, ref_y):
        ax.plot([i, i], [lifts[i] + hi_err[i], y], color=C_HILITE,
                linewidth=1.1, linestyle=(0, (3, 2)), zorder=2)
        ax.annotate(f"{y:.1f}", (i, y), textcoords="offset points",
                    xytext=(-9, -4), ha="right", fontsize=9, color="#7a5c1e")
    for i, v in enumerate(lifts):
        ax.annotate(f"{v:.1f}", (i, v + hi_err[i] + 2.5), ha="center",
                    fontsize=9, color="#1d4d6e")
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("two-stage abstention lift, held-out confabulations (pp)")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), frameon=False,
              fontsize=9)
    fig.tight_layout()
    out = OUT / "fig-p5-10-instruction-amplification.png"
    fig.savefig(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
