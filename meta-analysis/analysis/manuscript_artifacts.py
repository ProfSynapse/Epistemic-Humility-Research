#!/usr/bin/env python3
"""Generate first-pass manuscript-level figures and compact tables.

Inputs are restricted to the existing meta-analysis evidence table. The
mapping assumptions used for the schematic figures are deliberately explicit
below and are also written to tables/figure_manifest.*.

Run from repo root:
    python meta-analysis/analysis/manuscript_artifacts.py
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap

import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / "evidence" / "effects.csv"
FIGDIR = HERE / "figures"
TABLEDIR = HERE / "tables"


FIGURE_BASES = {
    "claim_family_direction": FIGDIR / "claim_family_direction",
    "depths_coverage": FIGDIR / "depths_coverage",
    "coherence_triangle": FIGDIR / "coherence_triangle",
}

CLAIM_TABLE = TABLEDIR / "claim_family_summary.csv"
REANALYSIS_TABLE = TABLEDIR / "reanalysis_contributions.csv"
GAPS_TABLE = TABLEDIR / "verified_gaps.csv"
MANIFEST_TABLE = TABLEDIR / "figure_manifest.csv"


FIGURE_STYLE = {
    "font_family": "DejaVu Sans",
    "ink": "#222222",
    "muted": "#555555",
    "axis": "#444444",
    "support": "#2b8cbe",
    "support_light": "#c7dcef",
    "contrary": "#d95f0e",
    "triangle_edge": "#333333",
    "annotation": "#777777",
}
CANONICAL_FORMATS = ("svg", "pdf")
PREVIEW_FORMATS = ("png",)

plt.rcParams.update(
    {
        "font.family": FIGURE_STYLE["font_family"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.edgecolor": FIGURE_STYLE["axis"],
        "axes.labelcolor": FIGURE_STYLE["ink"],
        "xtick.color": FIGURE_STYLE["muted"],
        "ytick.color": FIGURE_STYLE["muted"],
        "text.color": FIGURE_STYLE["ink"],
    }
)


def figure_paths(base_name: str) -> dict[str, list[Path]]:
    base = FIGURE_BASES[base_name]
    return {
        "canonical": [base.with_suffix(f".{fmt}") for fmt in CANONICAL_FORMATS],
        "preview": [base.with_suffix(f".{fmt}") for fmt in PREVIEW_FORMATS],
    }


def save_static_figure(fig: plt.Figure, base_name: str) -> None:
    paths = figure_paths(base_name)
    for path in paths["canonical"]:
        fig.savefig(path)
    for path in paths["preview"]:
        fig.savefig(path, dpi=220)


def effect_sign(row: pd.Series) -> float | None:
    """Signed effect: positive means treatment moved the metric upward."""
    if pd.notna(row.rel_change_pct):
        return float(row.rel_change_pct)
    if pd.notna(row.delta):
        return float(row.delta)
    return None


def supports_degradation(row: pd.Series) -> bool | None:
    """Support means the intervention worsened a humility-relevant metric."""
    e = effect_sign(row)
    if e is None or e == 0:
        return None
    return (row.direction == "lower" and e > 0) or (row.direction == "higher" and e < 0)


def supports_improvement(row: pd.Series) -> bool | None:
    """Support means the intervention improved a humility-relevant metric."""
    e = effect_sign(row)
    if e is None or e == 0:
        return None
    return (row.direction == "lower" and e < 0) or (row.direction == "higher" and e > 0)


@dataclass(frozen=True)
class ClaimFamily:
    code: str
    label: str
    short_label: str
    selector_note: str
    support_note: str
    selector_name: str
    judge_name: str


# Mapping assumption: these selectors mirror analysis/synthesize.py so the
# manuscript tables stay aligned with the existing quantitative synthesis.
CLAIM_FAMILIES = [
    ClaimFamily(
        "C1",
        "Instruction-tuning/RLHF degrades token-probability calibration",
        "Alignment can degrade calibration",
        "area=calibration; comparison in {pretrain_vs_rlhf, base_vs_instruct}; metric contains ECE",
        "support = lower-is-better calibration error increases",
        "select_c1",
        "supports_degradation",
    ),
    ClaimFamily(
        "C2",
        "Preference-based methods beat SFT on abstention/truthfulness quality",
        "Preference methods beat SFT",
        "comparison in {sft_vs_pref, sft_vs_dpo, sft_vs_kto, sft_vs_ipo}; metric contains truthful, reasoning, or TruthfulQA",
        "support = higher-is-better metric increases or lower-is-better metric decreases",
        "select_c2",
        "supports_improvement",
    ),
    ClaimFamily(
        "C3",
        "Preference optimization reduces SFT abstention over-refusal",
        "Preference methods reduce over-refusal",
        "comparison=sft_vs_pref; metric contains over-refusal",
        "support = over-refusal-sensitive metric improves",
        "select_c3",
        "supports_improvement",
    ),
    ClaimFamily(
        "C4",
        "Scale alone does not produce epistemic humility",
        "Scale is not sufficient",
        "comparison in {scale, scale_inverse, scale_and_rlhf, scale_and_tuning}; area in {sycophancy, hallucination, knowledge-boundary}",
        "support = humility-relevant metric worsens with scale or remains deficient",
        "select_c4",
        "supports_degradation",
    ),
    ClaimFamily(
        "C5",
        "Targeted training interventions improve humility metrics",
        "Targeted interventions help",
        "comparison in training-intervention set; area excludes capability",
        "support = humility-relevant metric improves",
        "select_c5",
        "supports_improvement",
    ),
]


def select_c1(d: pd.DataFrame) -> pd.DataFrame:
    return d[
        (d.area == "calibration")
        & d.comparison.isin(["pretrain_vs_rlhf", "base_vs_instruct"])
        & d.metric.str.contains("ECE", case=False, na=False)
    ]


def select_c2(d: pd.DataFrame) -> pd.DataFrame:
    return d[
        d.comparison.isin(["sft_vs_pref", "sft_vs_dpo", "sft_vs_kto", "sft_vs_ipo"])
        & d.metric.str.contains("truthful|reasoning|TruthfulQA", case=False, na=False)
    ]


def select_c3(d: pd.DataFrame) -> pd.DataFrame:
    return d[
        (d.comparison == "sft_vs_pref")
        & d.metric.str.contains("over-refusal", case=False, na=False)
    ]


def select_c4(d: pd.DataFrame) -> pd.DataFrame:
    return d[
        d.comparison.isin(["scale", "scale_inverse", "scale_and_rlhf", "scale_and_tuning"])
        & d.area.isin(["sycophancy", "hallucination", "knowledge-boundary"])
    ]


def select_c5(d: pd.DataFrame) -> pd.DataFrame:
    return d[
        d.comparison.isin(
            [
                "refusal_aware_sft",
                "honesty_sft",
                "dpo_calibration",
                "dpo_factuality",
                "factuality_aware_alignment",
                "synthetic_data_intervention",
                "sft_intervention",
                "rlhf_variant",
                "posthoc_fix",
                "confidence_sft_rl",
            ]
        )
        & (d.area != "capability")
    ]


SELECTORS = {
    "select_c1": select_c1,
    "select_c2": select_c2,
    "select_c3": select_c3,
    "select_c4": select_c4,
    "select_c5": select_c5,
}
JUDGES = {
    "supports_degradation": supports_degradation,
    "supports_improvement": supports_improvement,
}


# Mapping assumption: "Depths of Ignorance" is a manuscript synthesis lens, not
# a native CSV field. Each corpus area is assigned to its primary epistemic
# function so coverage can be visualized without changing effects.csv.
DEPTH_MAP = {
    "calibration": ("D1", "Confidence calibration", "knowing how likely an answer is to be right"),
    "knowledge-boundary": ("D2", "Known-unknown recognition", "knowing when the answer is not known"),
    "abstention": ("D3", "Action under uncertainty", "deciding whether to answer or abstain"),
    "hallucination": ("D4", "Factual grounding", "avoiding unsupported factual claims"),
    "sycophancy": ("D5", "Social epistemic independence", "resisting user pressure and false consensus"),
    "methods": ("D6", "Measurement integrity", "auditing datasets, judges, and reward signals"),
    "capability": ("D7", "Capability companion", "accuracy rows carried only as context"),
}


# Mapping assumption: the coherence triangle is a conceptual schematic. Areas
# are placed near the vertex that best describes the failure mode they test.
TRIANGLE_MAP = {
    "calibration": ("confidence", (0.18, 0.18)),
    "knowledge-boundary": ("confidence/abstention", (0.34, 0.24)),
    "abstention": ("abstention", (0.76, 0.18)),
    "hallucination": ("truth/abstention", (0.58, 0.52)),
    "sycophancy": ("truth", (0.50, 0.80)),
    "methods": ("measurement center", (0.50, 0.42)),
    "capability": ("context only", (0.50, 0.28)),
}


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        vals = []
        for col in columns:
            val = str(row.get(col, ""))
            vals.append(val.replace("\n", " ").replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def p1(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.1f}"


def load_evidence() -> pd.DataFrame:
    d = pd.read_csv(EVIDENCE)
    d["verified"] = d["verified"].astype(bool)
    return d


def claim_rows(d: pd.DataFrame) -> tuple[list[dict], set[int]]:
    rows = []
    matched: set[int] = set()
    for fam in CLAIM_FAMILIES:
        sub = SELECTORS[fam.selector_name](d).copy()
        matched.update(int(i) for i in sub.index)
        judge = JUDGES[fam.judge_name]
        support_studies = set()
        contrary_studies = set()
        informative_rows = 0
        for _, row in sub.iterrows():
            vote = judge(row)
            if vote is None or not bool(row.verified):
                continue
            informative_rows += 1
            if vote:
                support_studies.add(row.study)
            else:
                contrary_studies.add(row.study)
        rel = sub.rel_change_pct.dropna().abs()
        rows.append(
            {
                "claim": fam.code,
                "claim_family": fam.label,
                "short_label": fam.short_label,
                "rows": len(sub),
                "verified_rows": int(sub.verified.sum()),
                "studies": sub.study.nunique(),
                "informative_verified_rows": informative_rows,
                "supporting_studies": len(support_studies),
                "contrary_studies": len(contrary_studies),
                "median_abs_rel_change_pct": p1(rel.median() if len(rel) else None),
                "range_abs_rel_change_pct": (
                    f"{p1(rel.min())} to {p1(rel.max())}" if len(rel) else "n/a"
                ),
                "selector_assumption": fam.selector_note,
                "direction_assumption": fam.support_note,
                "studies_list": "; ".join(sorted(set(sub.study))),
            }
        )
    return rows, matched


def write_claim_family_direction(rows: list[dict]) -> None:
    labels = [r["claim"] for r in rows]
    support = [r["supporting_studies"] for r in rows]
    contrary = [-r["contrary_studies"] for r in rows]
    y = list(range(len(rows)))

    fig, ax = plt.subplots(figsize=(9.8, 4.8))
    ax.barh(y, support, color=FIGURE_STYLE["support"], label="supporting verified studies")
    ax.barh(y, contrary, color=FIGURE_STYLE["contrary"], label="contrary verified studies")
    ax.axvline(0, color=FIGURE_STYLE["axis"], lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [f"{r['claim']}: {r['short_label']}" for r in rows],
        fontsize=8.5,
    )
    ax.set_xlabel("study count (left = contrary, right = supporting)")
    ax.set_title("Claim-family evidence direction")
    max_count = max(max(support, default=0), abs(min(contrary, default=0)), 1)
    ax.set_xlim(-(max_count + 1), max_count + 5.3)
    ax.legend(loc="lower right", fontsize=8)
    for i, row in enumerate(rows):
        ax.text(
            max_count + 0.4,
            i,
            f"rows {row['verified_rows']}/{row['rows']} verified",
            va="center",
            ha="left",
            fontsize=7.5,
            color=FIGURE_STYLE["muted"],
        )
    fig.tight_layout()
    save_static_figure(fig, "claim_family_direction")
    plt.close(fig)


def write_depths_coverage(d: pd.DataFrame) -> list[dict]:
    depth_rows = []
    for area, (code, label, assumption) in DEPTH_MAP.items():
        sub = d[d.area == area]
        depth_rows.append(
            {
                "depth": code,
                "depth_label": label,
                "area": area,
                "rows": len(sub),
                "verified_rows": int(sub.verified.sum()),
                "studies": sub.study.nunique(),
                "mapping_assumption": assumption,
            }
        )

    labels = [f"{r['depth']} {r['depth_label']}" for r in depth_rows]
    rows = [r["rows"] for r in depth_rows]
    verified = [r["verified_rows"] for r in depth_rows]
    y = list(range(len(depth_rows)))

    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.barh(y, rows, color=FIGURE_STYLE["support_light"], label="all rows")
    ax.barh(y, verified, color=FIGURE_STYLE["support"], label="verified rows")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.3)
    ax.set_xlabel("evidence rows")
    ax.set_title("Depths of Ignorance coverage map")
    ax.legend(loc="lower right", fontsize=8)
    for i, row in enumerate(depth_rows):
        ax.text(
            row["rows"] + 0.35,
            i,
            f"{row['studies']} studies",
            va="center",
            fontsize=7.5,
            color=FIGURE_STYLE["muted"],
        )
    ax.set_xlim(0, max(rows) + 5)
    fig.tight_layout()
    save_static_figure(fig, "depths_coverage")
    plt.close(fig)
    return depth_rows


def write_coherence_triangle(d: pd.DataFrame) -> list[dict]:
    triangle_rows = []
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    vertices = {
        "Calibrated confidence": (0.08, 0.08),
        "Appropriate abstention": (0.92, 0.08),
        "Truthful independence": (0.50, 0.92),
    }
    poly = Polygon(
        list(vertices.values()),
        closed=True,
        fill=False,
        edgecolor=FIGURE_STYLE["triangle_edge"],
        lw=1.4,
    )
    ax.add_patch(poly)
    for label, (x, y) in vertices.items():
        ax.scatter([x], [y], s=70, color=FIGURE_STYLE["triangle_edge"], zorder=3)
        wrapped = "\n".join(wrap(label, 18))
        va = "bottom" if y > 0.5 else "top"
        ax.text(x, y + (0.045 if y > 0.5 else -0.045), wrapped, ha="center", va=va, fontsize=9)

    max_rows = max(int(v) for v in d.area.value_counts().values)
    colors = {
        "calibration": "#1b9e77",
        "knowledge-boundary": "#66a61e",
        "abstention": "#377eb8",
        "hallucination": "#984ea3",
        "sycophancy": "#e41a1c",
        "methods": "#7570b3",
        "capability": "#777777",
    }
    for area, (placement, (x, y)) in TRIANGLE_MAP.items():
        sub = d[d.area == area]
        size = 120 + 420 * (len(sub) / max_rows)
        ax.scatter([x], [y], s=size, color=colors.get(area, "#999999"), alpha=0.72, edgecolor="white")
        label_x = x + (0.055 if x <= 0.5 else -0.055)
        label_y = y + (0.035 if y < 0.75 else -0.055)
        ha = "left" if x <= 0.5 else "right"
        ax.annotate(
            f"{area}\n{len(sub)} rows",
            xy=(x, y),
            xytext=(label_x, label_y),
            ha=ha,
            va="center",
            fontsize=7.4,
            color=FIGURE_STYLE["triangle_edge"],
            arrowprops={"arrowstyle": "-", "lw": 0.6, "color": FIGURE_STYLE["annotation"]},
        )
        triangle_rows.append(
            {
                "area": area,
                "triangle_placement": placement,
                "rows": len(sub),
                "verified_rows": int(sub.verified.sum()),
                "studies": sub.study.nunique(),
                "x": x,
                "y": y,
                "mapping_assumption": "conceptual placement by primary failure mode; not a measured coordinate",
            }
        )
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.03, 1.03)
    ax.axis("off")
    ax.set_title("Coherence-axis schematic for epistemic humility", pad=12)
    fig.tight_layout()
    save_static_figure(fig, "coherence_triangle")
    plt.close(fig)
    return triangle_rows


def write_reanalysis_table(d: pd.DataFrame) -> list[dict]:
    rows = []
    re = d[d.study.astype(str).str.startswith("reanalysis-")].copy()
    for study, sub in re.groupby("study", sort=True):
        rows.append(
            {
                "reanalysis_id": study,
                "rows": len(sub),
                "areas": "; ".join(sorted(set(sub.area))),
                "comparisons": "; ".join(sorted(set(sub.comparison))),
                "metrics": "; ".join(sorted(set(sub.metric))),
                "verified_rows": int(sub.verified.sum()),
                "contribution": "new paired extraction from released outputs/results, carried as study-prefixed reanalysis row",
            }
        )
    return rows


def write_gap_table(d: pd.DataFrame, matched: set[int]) -> list[dict]:
    unmatched = d.loc[~d.index.isin(matched)]
    gap_rows = [
        {
            "gap": "unverified_effect_rows",
            "count": int((~d.verified).sum()),
            "unit": "rows",
            "why_it_matters": "not counted as verified directional evidence until primary-source access is resolved",
            "affected_items": "; ".join(d.loc[~d.verified, "study"].astype(str).tolist()) or "none",
        },
        {
            "gap": "variance_reporting_sparse",
            "count": int(d.variance_reported.fillna(False).astype(bool).sum()),
            "unit": "rows with variance information",
            "why_it_matters": "formal random-effects pooling remains underpowered for most claim families",
            "affected_items": "variance-aware rows only; see synthesis-summary.md",
        },
        {
            "gap": "outside_claim_family_boundaries",
            "count": len(unmatched),
            "unit": "rows",
            "why_it_matters": "family unanimity is conditional on selector boundaries",
            "affected_items": "; ".join(sorted(set(unmatched.study.astype(str)))),
        },
        {
            "gap": "capability_companion_rows",
            "count": int((d.area == "capability").sum()),
            "unit": "rows",
            "why_it_matters": "accuracy companion rows contextualize humility metrics but are excluded from humility-family support counts",
            "affected_items": "; ".join(d.loc[d.area == "capability", "study"].astype(str).tolist()) or "none",
        },
    ]
    return gap_rows


def manifest_figure_rows(
    base_name: str,
    source: str,
    mapping_assumptions: str,
) -> list[dict]:
    paths = figure_paths(base_name)
    canonical = "; ".join(str(path.relative_to(HERE)).replace("\\", "/") for path in paths["canonical"])
    preview = "; ".join(str(path.relative_to(HERE)).replace("\\", "/") for path in paths["preview"])
    rows = []
    for role, role_paths in paths.items():
        for path in role_paths:
            rows.append(
                {
                    "artifact": str(path.relative_to(HERE)).replace("\\", "/"),
                    "kind": "figure",
                    "source": source,
                    "mapping_assumptions": mapping_assumptions,
                    "artifact_role": role,
                    "artifact_format": path.suffix.lstrip("."),
                    "canonical_artifacts": canonical,
                    "preview_artifacts": preview,
                }
            )
    return rows


def manifest_table_row(artifact: str, source: str, mapping_assumptions: str) -> dict:
    return {
        "artifact": artifact,
        "kind": "table",
        "source": source,
        "mapping_assumptions": mapping_assumptions,
        "artifact_role": "data",
        "artifact_format": Path(artifact).suffix.lstrip("."),
        "canonical_artifacts": artifact,
        "preview_artifacts": "",
    }


def write_manifest(depth_rows: list[dict], triangle_rows: list[dict]) -> list[dict]:
    manifest = []
    manifest.extend(
        manifest_figure_rows(
            "claim_family_direction",
            "evidence/effects.csv",
            "claim-family selectors and support tests mirror analysis/synthesize.py; verified rows only determine support/contrary counts",
        )
    )
    manifest.extend(
        manifest_figure_rows(
            "depths_coverage",
            "evidence/effects.csv",
            "; ".join(f"{r['area']}->{r['depth']} {r['depth_label']}" for r in depth_rows),
        )
    )
    manifest.extend(
        manifest_figure_rows(
            "coherence_triangle",
            "evidence/effects.csv",
            "; ".join(f"{r['area']}->{r['triangle_placement']}" for r in triangle_rows),
        )
    )
    operating_canonical = ["figures/abstention_operating_points.svg"]
    if (FIGDIR / "abstention_operating_points.pdf").exists():
        operating_canonical.append("figures/abstention_operating_points.pdf")
    for artifact in operating_canonical:
        manifest.append(
            {
                "artifact": artifact,
                "kind": "figure",
                "source": "evidence/idk-method-reanalysis.csv; datasets/abstentionbench-results/abstention_performance.csv",
                "mapping_assumptions": "faceted descriptive artifact only; Cheng IDK and AbstentionBench use different datasets and metric definitions and must not be pooled as one frontier",
                "artifact_role": "canonical",
                "artifact_format": Path(artifact).suffix.lstrip("."),
                "canonical_artifacts": "; ".join(operating_canonical),
                "preview_artifacts": "",
            }
        )
    manifest.extend(
        [
            manifest_table_row(
                "tables/claim_family_summary.csv",
                "evidence/effects.csv",
                "same selectors as claim_family_direction; effect size summary uses absolute relative change when available",
            ),
            manifest_table_row(
                "tables/reanalysis_contributions.csv",
                "evidence/effects.csv",
                "reanalysis contribution defined by study id prefix 'reanalysis-'",
            ),
            manifest_table_row(
                "tables/verified_gaps.csv",
                "evidence/effects.csv",
                "gaps summarize verification, variance reporting, family-boundary exclusions, and capability companion rows",
            ),
            manifest_table_row(
                "tables/abstention_operating_points.csv",
                "evidence/idk-method-reanalysis.csv; datasets/abstentionbench-results/abstention_performance.csv",
                "operating points are source-faceted and descriptive only; over_refusal_sensitive_pct is exact Cheng over-refusal but 100 - median precision for AbstentionBench",
            ),
        ]
    )
    return manifest


def write_table_pair(path: Path, rows: list[dict], columns: list[str]) -> None:
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
    md_path = path.with_suffix(".md")
    md_path.write_text(markdown_table(rows, columns), encoding="utf-8")


def main() -> None:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    TABLEDIR.mkdir(parents=True, exist_ok=True)
    d = load_evidence()

    claims, matched = claim_rows(d)
    write_claim_family_direction(claims)
    depth_rows = write_depths_coverage(d)
    triangle_rows = write_coherence_triangle(d)
    reanalysis_rows = write_reanalysis_table(d)
    gap_rows = write_gap_table(d, matched)
    manifest_rows = write_manifest(depth_rows, triangle_rows)

    write_table_pair(
        CLAIM_TABLE,
        claims,
        [
            "claim",
            "claim_family",
            "rows",
            "verified_rows",
            "studies",
            "informative_verified_rows",
            "supporting_studies",
            "contrary_studies",
            "median_abs_rel_change_pct",
            "range_abs_rel_change_pct",
            "selector_assumption",
            "direction_assumption",
            "studies_list",
        ],
    )
    write_table_pair(
        REANALYSIS_TABLE,
        reanalysis_rows,
        ["reanalysis_id", "rows", "areas", "comparisons", "metrics", "verified_rows", "contribution"],
    )
    write_table_pair(
        GAPS_TABLE,
        gap_rows,
        ["gap", "count", "unit", "why_it_matters", "affected_items"],
    )
    write_table_pair(
        MANIFEST_TABLE,
        manifest_rows,
        [
            "artifact",
            "kind",
            "source",
            "mapping_assumptions",
            "artifact_role",
            "artifact_format",
            "canonical_artifacts",
            "preview_artifacts",
        ],
    )
    for base_name in FIGURE_BASES:
        for role, paths in figure_paths(base_name).items():
            print(f"wrote {role} " + ", ".join(str(path) for path in paths))
    print(f"wrote {CLAIM_TABLE} and markdown companions")
    print(f"wrote {REANALYSIS_TABLE} and markdown companions")
    print(f"wrote {GAPS_TABLE} and markdown companions")
    print(f"wrote {MANIFEST_TABLE} and markdown companions")


if __name__ == "__main__":
    main()
