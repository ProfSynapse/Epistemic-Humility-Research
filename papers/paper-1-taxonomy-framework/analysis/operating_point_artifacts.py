#!/usr/bin/env python3
"""Combined abstention operating-point artifacts.

This script intentionally keeps Cheng IDK and AbstentionBench in separate
facets. The sources use different datasets and metric definitions, so the
output is a descriptive side-by-side artifact, not a pooled frontier.

Inputs:
  papers/paper-1-taxonomy-framework/evidence/idk-method-reanalysis.csv
  datasets/abstentionbench-results/abstention_performance.csv

Outputs:
  papers/paper-1-taxonomy-framework/analysis/tables/abstention_operating_points.csv
  papers/paper-1-taxonomy-framework/analysis/tables/abstention_operating_points.md
  papers/paper-1-taxonomy-framework/analysis/figures/abstention_operating_points.svg
  papers/paper-1-taxonomy-framework/analysis/figures/abstention_operating_points.pdf, if local SVG conversion support is available

Run:
  python papers/paper-1-taxonomy-framework/analysis/operating_point_artifacts.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]  # repo root
CHENG_CSV = HERE.parent / "evidence" / "idk-method-reanalysis.csv"
ABSTENTIONBENCH_CSV = ROOT / "datasets" / "abstentionbench-results" / "abstention_performance.csv"
TABLE_DIR = HERE / "tables"
FIGURE_DIR = HERE / "figures"
TABLE_CSV = TABLE_DIR / "abstention_operating_points.csv"
TABLE_MD = TABLE_DIR / "abstention_operating_points.md"
MANIFEST_CSV = TABLE_DIR / "figure_manifest.csv"
MANIFEST_MD = TABLE_DIR / "figure_manifest.md"
FIGURE_SVG = FIGURE_DIR / "abstention_operating_points.svg"
FIGURE_PDF = FIGURE_DIR / "abstention_operating_points.pdf"

STYLE = {
    "font_family": "Arial, sans-serif",
    "ink": "#222222",
    "muted": "#555555",
    "grid": "#e5e5e5",
    "grid_light": "#eeeeee",
    "axis": "#777777",
    "panel_border": "#bbbbbb",
    "cheng": "#33aa77",
    "cheng_stroke": "#1b6b4d",
    "ladder": "#555555",
    "background": "#ffffff",
}

PARTIAL_ABSTENTIONBENCH_MODELS = {
    "TinyLlamaChat",
    "o1HighReasoningAPI",
    "o1LowReasoningAPI",
}

TULU_LADDER_ORDER = ["Base", "SFT", "DPO", "PPO RLVF"]
TULU_LADDER_MODELS = {
    "8B": {
        "Base": "Llama 3.1 8B Base",
        "SFT": "Llama 3.1 8B Tulu 3 SFT",
        "DPO": "Llama 3.1 8B Tulu 3 DPO",
        "PPO RLVF": "Llama 3.1 8B Tulu 3 PPO RLVF",
    },
    "70B": {
        "Base": "Llama 3.1 70B Base",
        "SFT": "Llama 3.1 70B Tulu 3 SFT",
        "DPO": "Llama 3.1 70B Tulu 3 DPO",
        "PPO RLVF": "Llama 3.1 70B Tulu 3 PPO RLVF",
    },
}

COMPARABILITY_NOTE = (
    "Descriptive only: Cheng IDK and AbstentionBench use different datasets "
    "and metric definitions; do not pool or compare as one frontier."
)


def f1(value: float) -> str:
    return f"{value:.1f}"


def cell_table(df: pd.DataFrame, model: str) -> pd.DataFrame:
    sub = df[df.model_name_formatted == model]
    return sub.set_index(["dataset_name_formatted", "scenario_label"])[["recall", "precision"]]


def load_cheng_points() -> pd.DataFrame:
    df = pd.read_csv(CHENG_CSV)
    rows = []
    for _, row in df.sort_values("method").iterrows():
        rows.append(
            {
                "source": "Cheng IDK reanalysis",
                "source_panel": "Cheng IDK exact method-level tradeoff",
                "operating_point": row["method"],
                "stage_or_family": "IDK method",
                "n_units": int(row["n"]),
                "recall_pct": float(row["refusal_recall_pct"]),
                "precision_pct": float("nan"),
                "over_refusal_sensitive_pct": float(row["over_refusal_pct"]),
                "x_metric": "over_refusal_pct",
                "x_metric_definition": "Refusal rate on known-answer labeled items.",
                "y_metric": "refusal_recall_pct",
                "y_metric_definition": "Refusal recall on unknown-labeled items.",
                "comparability_note": COMPARABILITY_NOTE,
            }
        )
    return pd.DataFrame(rows)


def load_abstentionbench_points() -> pd.DataFrame:
    df = pd.read_csv(ABSTENTIONBENCH_CSV)
    full = df[~df.model_name_formatted.isin(PARTIAL_ABSTENTIONBENCH_MODELS)].copy()
    models = sorted(full.model_name_formatted.unique())
    shared_cells = sorted(
        set.intersection(*(set(cell_table(full, model).index) for model in models))
    )

    rows = []
    for model in models:
        model_cells = cell_table(full, model).loc[shared_cells]
        stage = full.loc[full.model_name_formatted == model, "post_training_stage"].iloc[0]
        stage = stage if isinstance(stage, str) else "none"
        recall_pct = 100.0 * float(model_cells.recall.median())
        precision_pct = 100.0 * float(model_cells.precision.median())
        rows.append(
            {
                "source": "AbstentionBench released results reanalysis",
                "source_panel": "AbstentionBench shared-subset model frontier",
                "operating_point": model,
                "stage_or_family": stage,
                "n_units": len(shared_cells),
                "recall_pct": recall_pct,
                "precision_pct": precision_pct,
                "over_refusal_sensitive_pct": 100.0 - precision_pct,
                "x_metric": "100_minus_median_precision_pct",
                "x_metric_definition": (
                    "Over-refusal-sensitive proxy: 100 - median abstention "
                    "precision over shared benchmark cells."
                ),
                "y_metric": "median_recall_pct",
                "y_metric_definition": (
                    "Median abstention recall over the shared "
                    "(dataset, scenario) cells."
                ),
                "comparability_note": COMPARABILITY_NOTE,
            }
        )
    return pd.DataFrame(rows)


def write_markdown_table(table: pd.DataFrame) -> None:
    display = table[
        [
            "source",
            "operating_point",
            "stage_or_family",
            "n_units",
            "recall_pct",
            "precision_pct",
            "over_refusal_sensitive_pct",
        ]
    ].copy()
    for column in ("recall_pct", "precision_pct", "over_refusal_sensitive_pct"):
        display[column] = display[column].map(
            lambda value: "" if pd.isna(value) else f1(float(value))
        )
    headers = list(display.columns)
    markdown_rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for _, row in display.iterrows():
        markdown_rows.append(
            "| " + " | ".join(str(row[column]) for column in headers) + " |"
        )

    lines = [
        "# Abstention operating points",
        "",
        "Auto-generated by `papers/paper-1-taxonomy-framework/analysis/operating_point_artifacts.py`.",
        "",
        COMPARABILITY_NOTE,
        "",
        "Metric note: `over_refusal_sensitive_pct` is exact Cheng over-refusal "
        "for known-answer items, but `100 - median precision` for AbstentionBench.",
        "",
        *markdown_rows,
        "",
    ]
    TABLE_MD.write_text("\n".join(lines), encoding="utf-8")


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


def upsert_manifest(pdf_available: bool) -> None:
    if not MANIFEST_CSV.exists():
        return

    columns = [
        "artifact",
        "kind",
        "source",
        "mapping_assumptions",
        "artifact_role",
        "artifact_format",
        "canonical_artifacts",
        "preview_artifacts",
        "availability_status",
        "availability_note",
    ]
    manifest = pd.read_csv(MANIFEST_CSV)
    for column in columns:
        if column not in manifest.columns:
            manifest[column] = ""

    source = (
        "evidence/idk-method-reanalysis.csv; "
        "datasets/abstentionbench-results/abstention_performance.csv"
    )
    assumptions = (
        "faceted descriptive artifact only; Cheng IDK and AbstentionBench use "
        "different datasets and metric definitions and must not be pooled as one frontier"
    )
    canonical = ["figures/abstention_operating_points.svg"]
    if pdf_available:
        canonical.append("figures/abstention_operating_points.pdf")

    rows = []
    for artifact in canonical:
        rows.append(
            {
                "artifact": artifact,
                "kind": "figure",
                "source": source,
                "mapping_assumptions": assumptions,
                "artifact_role": "canonical",
                "artifact_format": Path(artifact).suffix.lstrip("."),
                "canonical_artifacts": "; ".join(canonical),
                "preview_artifacts": "",
                "availability_status": "available",
                "availability_note": "generated by operating_point_artifacts.py",
            }
        )
    if not pdf_available:
        rows.append(
            {
                "artifact": "figures/abstention_operating_points.pdf",
                "kind": "figure",
                "source": source,
                "mapping_assumptions": assumptions,
                "artifact_role": "unavailable",
                "artifact_format": "pdf",
                "canonical_artifacts": "figures/abstention_operating_points.svg",
                "preview_artifacts": "",
                "availability_status": "unavailable",
                "availability_note": "PDF export requires cairosvg; SVG remains the canonical operating-point artifact when cairosvg is not installed.",
            }
        )
    rows.append(
        {
            "artifact": "tables/abstention_operating_points.csv",
            "kind": "table",
            "source": source,
            "mapping_assumptions": (
                "operating points are source-faceted and descriptive only; "
                "over_refusal_sensitive_pct is exact Cheng over-refusal but "
                "100 - median precision for AbstentionBench"
            ),
            "artifact_role": "data",
            "artifact_format": "csv",
            "canonical_artifacts": "tables/abstention_operating_points.csv",
            "preview_artifacts": "",
            "availability_status": "available",
            "availability_note": "generated by operating_point_artifacts.py",
        }
    )

    manifest = manifest[~manifest.artifact.isin([row["artifact"] for row in rows])]
    manifest = pd.concat([manifest, pd.DataFrame(rows, columns=columns)], ignore_index=True)
    manifest.to_csv(MANIFEST_CSV, index=False)
    MANIFEST_MD.write_text(markdown_table(manifest.to_dict("records"), columns), encoding="utf-8")


def write_pdf_if_available() -> bool:
    try:
        import cairosvg  # type: ignore
    except Exception:
        if FIGURE_PDF.exists():
            FIGURE_PDF.unlink()
        return False

    cairosvg.svg2pdf(url=str(FIGURE_SVG), write_to=str(FIGURE_PDF))
    return True


def plot_operating_points(table: pd.DataFrame) -> None:
    cheng = table[table.source == "Cheng IDK reanalysis"]
    ab = table[table.source == "AbstentionBench released results reanalysis"]

    width, height = 1200, 520
    margin = {"left": 70, "right": 35, "top": 88, "bottom": 86}
    panel_gap = 72
    panel_w = (width - margin["left"] - margin["right"] - panel_gap) / 2
    panel_h = height - margin["top"] - margin["bottom"]
    panels = {
        "cheng": (margin["left"], margin["top"], panel_w, panel_h),
        "ab": (margin["left"] + panel_w + panel_gap, margin["top"], panel_w, panel_h),
    }

    def scale_x(value: float, limit: float, panel: tuple) -> float:
        x0, _, w, _ = panel
        return x0 + (value / limit) * w

    def scale_y(value: float, panel: tuple) -> float:
        _, y0, _, h = panel
        return y0 + h - (value / 100.0) * h

    def text(x: float, y: float, body: str, size: int = 12, anchor: str = "start",
             weight: str = "normal", fill: str = STYLE["ink"]) -> str:
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{STYLE["font_family"]}" '
            f'font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
            f'fill="{fill}">{escape(body)}</text>'
        )

    def line(x1: float, y1: float, x2: float, y2: float, color: str = "#cccccc",
             width_: float = 1.0, dash: str = "") -> str:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{width_}"{dash_attr}/>'
        )

    def circle(x: float, y: float, radius: float, fill: str, stroke: str = STYLE["ink"]) -> str:
        return (
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
        )

    def draw_axes(panel: tuple, x_limit: float, title: str, x_label: str, y_label: str) -> list[str]:
        x0, y0, w, h = panel
        elements = [
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'fill="{STYLE["background"]}" stroke="{STYLE["panel_border"]}" stroke-width="1"/>',
            text(x0 + w / 2, y0 - 34, title, size=15, anchor="middle", weight="bold"),
            text(x0 + w / 2, y0 + h + 48, x_label, size=12, anchor="middle"),
            (
                f'<text x="{x0 - 48:.1f}" y="{y0 + h / 2:.1f}" '
                f'font-family="{STYLE["font_family"]}" font-size="12" text-anchor="middle" '
                f'transform="rotate(-90 {x0 - 48:.1f} {y0 + h / 2:.1f})">'
                f'{escape(y_label)}</text>'
            ),
        ]
        for tick in range(0, 101, 25):
            y = scale_y(tick, panel)
            elements.append(line(x0, y, x0 + w, y, color=STYLE["grid"]))
            elements.append(text(x0 - 8, y + 4, str(tick), size=10, anchor="end", fill=STYLE["muted"]))
        step = 10 if x_limit <= 60 else 25
        tick = 0
        while tick <= x_limit + 0.001:
            x = scale_x(tick, x_limit, panel)
            elements.append(line(x, y0, x, y0 + h, color=STYLE["grid_light"]))
            elements.append(text(x, y0 + h + 20, str(int(tick)), size=10, anchor="middle", fill=STYLE["muted"]))
            tick += step
        elements.append(line(x0, y0 + h, x0 + w, y0 + h, color=STYLE["axis"], width_=1.2))
        elements.append(line(x0, y0, x0, y0 + h, color=STYLE["axis"], width_=1.2))
        return elements

    cheng_limit = max(55.0, float(cheng.over_refusal_sensitive_pct.max()) + 6.0)
    ab_limit = max(25.0, float(ab.over_refusal_sensitive_pct.max()) + 4.0)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="100%" height="100%" fill="{STYLE["background"]}"/>',
        text(width / 2, 28, "Abstention operating points, faceted by source", size=17,
             anchor="middle", weight="bold"),
        text(width / 2, 50, "Descriptive only: different datasets and x-axis definitions; not a pooled frontier.",
             size=11, anchor="middle", fill=STYLE["muted"]),
        *draw_axes(
            panels["cheng"],
            cheng_limit,
            "Cheng IDK methods",
            "Over-refusal on known-answer items (%)",
            "Refusal recall on unknown-labeled items (%)",
        ),
        *draw_axes(
            panels["ab"],
            ab_limit,
            "AbstentionBench model frontier",
            "100 - median abstention precision (%)",
            "Median abstention recall (%)",
        ),
    ]

    for _, row in cheng.iterrows():
        x = scale_x(float(row.over_refusal_sensitive_pct), cheng_limit, panels["cheng"])
        y = scale_y(float(row.recall_pct), panels["cheng"])
        svg.append(circle(x, y, 5.8, STYLE["cheng"], STYLE["cheng_stroke"]))
        svg.append(text(x + 7, y - 7, str(row.operating_point), size=10))

    stage_style = {
        "Base": "#888888",
        "SFT": "#d89000",
        "DPO": "#33aa77",
        "PPO RLVF": "#2775b7",
        "Instruct": "#9955aa",
        "none": "#c65f5f",
    }
    for scale, stages in TULU_LADDER_MODELS.items():
        ladder = ab[ab.operating_point.isin(stages.values())].copy()
        ladder["stage_order"] = ladder.stage_or_family.map(
            {stage: index for index, stage in enumerate(TULU_LADDER_ORDER)}
        )
        ladder = ladder.sort_values("stage_order")
        points = [
            (
                scale_x(float(row.over_refusal_sensitive_pct), ab_limit, panels["ab"]),
                scale_y(float(row.recall_pct), panels["ab"]),
            )
            for _, row in ladder.iterrows()
        ]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            svg.append(line(x1, y1, x2, y2, color=STYLE["ladder"], width_=1.4))
        last = ladder.iloc[-1]
        svg.append(
            text(
                scale_x(float(last.over_refusal_sensitive_pct), ab_limit, panels["ab"]) + 6,
                scale_y(float(last.recall_pct), panels["ab"]) + 13,
                f"Tulu {scale}",
                size=9,
                fill=STYLE["axis"],
            )
        )

    for _, row in ab.iterrows():
        x = scale_x(float(row.over_refusal_sensitive_pct), ab_limit, panels["ab"])
        y = scale_y(float(row.recall_pct), panels["ab"])
        color = stage_style.get(row.stage_or_family, "#333333")
        svg.append(circle(x, y, 4.8, color, STYLE["ink"]))

    label_models = {
        "Llama 3.1 70B Tulu 3 DPO",
        "Llama 3.1 8B Base",
        "Llama 3.1 70B Base",
        "GPT-4o",
        "DeepSeek R1 Distill Llama 70B",
        "S1.1 32B",
    }
    for _, row in ab[ab.operating_point.isin(label_models)].iterrows():
        x = scale_x(float(row.over_refusal_sensitive_pct), ab_limit, panels["ab"])
        y = scale_y(float(row.recall_pct), panels["ab"])
        svg.append(text(x + 6, y - 5, str(row.operating_point), size=8))

    legend_x = panels["ab"][0] + panels["ab"][2] - 115
    legend_y = panels["ab"][1] + 18
    svg.append(text(legend_x, legend_y - 4, "stage", size=10, weight="bold"))
    for index, (stage, color) in enumerate(stage_style.items()):
        y = legend_y + 18 + index * 17
        svg.append(circle(legend_x + 5, y - 4, 4.2, color, "#333333"))
        svg.append(text(legend_x + 16, y, stage, size=9))

    svg.extend(
        [
            text(
                width / 2,
                height - 18,
                "Metric note: Cheng x-axis is exact over-refusal; AbstentionBench x-axis is 100 - median precision.",
                size=10,
                anchor="middle",
                fill=STYLE["muted"],
            ),
            "</svg>",
        ]
    )
    FIGURE_SVG.write_text("\n".join(svg), encoding="utf-8")


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    table = pd.concat([load_cheng_points(), load_abstentionbench_points()], ignore_index=True)
    table.to_csv(TABLE_CSV, index=False)
    write_markdown_table(table)
    plot_operating_points(table)
    pdf_available = write_pdf_if_available()
    upsert_manifest(pdf_available)

    print(f"wrote {TABLE_CSV.relative_to(ROOT)} ({len(table)} rows)")
    print(f"wrote {TABLE_MD.relative_to(ROOT)}")
    print(f"wrote {FIGURE_SVG.relative_to(ROOT)}")
    if pdf_available:
        print(f"wrote {FIGURE_PDF.relative_to(ROOT)}")
    else:
        print("skipped abstention operating-point PDF: cairosvg is not installed")


if __name__ == "__main__":
    main()
