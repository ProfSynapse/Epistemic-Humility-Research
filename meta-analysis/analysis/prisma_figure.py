#!/usr/bin/env python3
"""PRISMA-style flow figure for the epistemic-humility meta-analysis.

Counts are the reconstructed funnel documented in evidence/prisma-flow.md;
each constant cites its recomputation source. Regenerate with:
    python3 meta-analysis/analysis/prisma_figure.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).parent / "figures" / "prisma.png"

# evidence/prisma-flow.md — recomputable from raw reports, manifest, effects.csv
QUERIES = 110          # sum of agent_queries frontmatter, reports 01-06
ENTRIES = 93           # ^PAPER: entries across reports
UNIQUE_ARXIV = 114     # deduplicated arXiv IDs in reports
NON_ARXIV = 5          # gray literature + essay
ADMITTED = 97          # library/manifest.yaml (search phases)
BACKCITE_STUDIES = 4   # backward-citation pass admissions (prisma-flow.md)
BACKCITE_CONTEXT = 20  # 19 arXiv context + 1 non-arXiv (Farquhar 2024)
NOT_ADMITTED = 21      # 13 peripheral + 4 post-freeze + 4 ID artifacts
STUDIES, ROWS = 38, 75  # effects.csv (post 2026-06-11 review: mis-attributed
#                          row removed; IPO arm of 2404.14723 extracted)
CONTEXT_CITED = 38 + BACKCITE_CONTEXT  # cited in draft without extracted rows
VERIFIED = 73          # effects.csv verified column
CORRECTED, EXCLUDED = 6, 1

MAIN = [
    ("Identification",
     f"6 structured searches, {QUERIES} documented queries (June 2026)\n"
     "funnel starts at structured assessment (see \u00a77)"),
    ("Structured assessment",
     f"{ENTRIES} per-paper entries in 6 raw reports\n"
     f"{UNIQUE_ARXIV} unique arXiv IDs + {NON_ARXIV} non-arXiv records"),
    ("Library admission",
     f"{ADMITTED} papers admitted after dedup + eligibility screening\n"
     "(93 search-surfaced + 4 verification/follow-up additions)\n"
     f"+ backward-citation pass: {BACKCITE_STUDIES} effect studies, "
     f"{BACKCITE_CONTEXT} context refs (June 2026)"),
    ("Quantitative extraction",
     f"{STUDIES} studies → {ROWS} effect rows in unified schema\n"
     f"+ {CONTEXT_CITED} papers cited as context/framework only"),
    ("PDF verification",
     f"{VERIFIED}/{ROWS} rows verified · {CORRECTED} corrected · "
     f"{EXCLUDED} excluded + removed (mis-attribution)\n"
     "+ review pass: IPO arm extracted (2404.14723)"),
]

SIDE = {
    2: ("Not admitted: 21 IDs\n13 peripheral mentions\n4 post-extraction-freeze\n"
        "4 ID-disambiguation artifacts"),
    4: ("Unverifiable: 2 rows\nblog replication · no-PDF journal\n(mis-attributed row removed)"),
}

fig, ax = plt.subplots(figsize=(8.2, 9.2))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10.6)
ax.axis("off")

ys = [9.4, 7.5, 5.6, 3.7, 1.8]
for i, ((title, body), y) in enumerate(zip(MAIN, ys)):
    box = FancyBboxPatch((0.6, y - 0.62), 5.9, 1.32,
                         boxstyle="round,pad=0.12",
                         fc="#eef3fb", ec="#2b5797", lw=1.3)
    ax.add_patch(box)
    ax.text(3.55, y + 0.42, title, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="#1a3a6b")
    ax.text(3.55, y - 0.18, body, ha="center", va="center", fontsize=8.3)
    if i < len(MAIN) - 1:
        ax.add_patch(FancyArrowPatch((3.55, y - 0.78), (3.55, ys[i + 1] + 0.74),
                                     arrowstyle="-|>", mutation_scale=16,
                                     color="#2b5797", lw=1.3))

for i, note in SIDE.items():
    y = ys[i]
    box = FancyBboxPatch((7.0, y - 0.58), 2.6, 1.24,
                         boxstyle="round,pad=0.1",
                         fc="#fbf2ee", ec="#a33b1f", lw=1.1)
    ax.add_patch(box)
    ax.text(8.3, y + 0.04, note, ha="center", va="center", fontsize=7.4,
            color="#6b2413")
    ax.add_patch(FancyArrowPatch((6.62, y), (6.96, y),
                                 arrowstyle="-|>", mutation_scale=12,
                                 color="#a33b1f", lw=1.1))

ax.text(5.0, 10.35, "Evidence flow (retrospective reconstruction)",
        ha="center", fontsize=12, fontweight="bold")
ax.text(5.0, 0.45,
        "Counts recomputable from raw-reports/01–06, library/manifest.yaml, "
        "effects.csv — see evidence/prisma-flow.md",
        ha="center", fontsize=7.2, style="italic", color="#555555")

OUT.parent.mkdir(exist_ok=True)
fig.savefig(OUT, dpi=200, bbox_inches="tight")
print(f"wrote {OUT}")
