"""Build the Paper 2 prompt x training crossing figures (fig-p1-11, fig-p1-12).

Both figures read every number from the committed metrics JSONs at build
time; nothing is hardcoded except an EXPECTED cross-check table transcribed
from the two governing amendments' Outcome sections, which the script
verifies against on every run rather than trusting silently.

Reads:
  experiments/prompt-vs-training-panel/analysis-committed/metrics_*.json
  experiments/pstruct-internalization-seed-robustness/analysis-committed/metrics_*.json
  experiments/grpo-cold-start-induction/analysis-committed/metrics_cold_base_grpo_v2_seed1__selfaware.json

Ground truth (read-before-cite): experiments/prompt-vs-training-panel/AMENDMENT.md
Outcome section and experiments/pstruct-internalization-seed-robustness/AMENDMENT.md
Outcome section.

Writes PNG+SVG to papers/paper-2-training-regimen/figures/.

Reuses the shared PIL/SVG drawing primitives from build_figures.py (same
directory) so these two figures match the paper's established visual
language rather than reinventing it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from build_figures import (  # noqa: E402
    PNG_COLORS,
    _draw_axes,
    _draw_card,
    _draw_dashed_hline,
    _draw_text,
    _draw_title,
    _font,
    _new_chart,
    _paste_y_axis_label,
    _save_png,
    _svg_dashed_hline,
    _svg_escape,
    _svg_text,
    _text_size,
    _write_svg,
)
from ideal_zone import IDEAL_GREEN_RGB  # noqa: E402  (unused visual language here; see note below)

REPO = Path(__file__).resolve().parents[3]
PANEL_DIR = REPO / "experiments" / "prompt-vs-training-panel" / "analysis-committed"
SEEDROB_DIR = REPO / "experiments" / "pstruct-internalization-seed-robustness" / "analysis-committed"
GRPO_DIR = REPO / "experiments" / "grpo-cold-start-induction" / "analysis-committed"
FIGURES = REPO / "papers" / "paper-2-training-regimen" / "figures"

# Note: IDEAL_GREEN_RGB (the shared "conceptual ideal, not a literal
# threshold" wash used by the recall-vs-over-refusal scatter panels) is
# deliberately NOT reused for fig-12's two reference lines below: those are
# registered NUMERIC thresholds (SR-G1's 30% floor, the panel's R3 10%
# ceiling), which is exactly the case ideal_zone.py's docstring says that
# convention must not be used for. fig-12 instead follows build_extended_figures.py's
# axhline+text pattern for its "collapse gate (0.10)" / "chance" lines.

# ---------------------------------------------------------------- data model

PROMPT_COLORS = {
    "p_rc": (201, 151, 58),      # amber - response-confidence contract
    "p_plain": PNG_COLORS["muted"],  # slate grey - plain-answer harness default
    "p_struct": PNG_COLORS["sft"],   # sft green - structure-only, the internalization test
}
PROMPT_LABELS = {"p_rc": "response-confidence", "p_plain": "plain-answer", "p_struct": "structure-only"}
PROMPT_ORDER = ["p_rc", "p_plain", "p_struct"]

GRPO_RED = (178, 58, 72)  # matches build_extended_figures.py COLORS["grpo"] (#b23a48), reused
                          # here for cross-figure consistency: any GRPO-touching arm reads red
                          # in every Paper 2 figure, not just this one.

FAMILY_COLORS = {
    "base": PNG_COLORS["muted"],
    "sft": PNG_COLORS["sft"],
    "dpo": PNG_COLORS["dpo"],
    "kto": PNG_COLORS["kto"],
    "grpo": GRPO_RED,
}


def _load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing committed metrics artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _rr(path: Path) -> tuple[float, float, str]:
    """(refusal_recall_pct, over_refusal_pct, config_sha) from a metrics.json."""
    d = _load(path)
    m = d["metrics"]
    return float(m["refusal_recall_pct"]), float(m["over_refusal_pct"]), d["provenance"]["config_sha"]


# fig-p1-11: checkpoint -> {condition: path}, in the lead-specified checkpoint order.
FIG11_CHECKPOINTS = [
    ("raw base", {
        "p_rc": PANEL_DIR / "metrics_base_prc__selfaware.json",
        "p_plain": PANEL_DIR / "metrics_base_pplain__selfaware.json",
        "p_struct": PANEL_DIR / "metrics_base_pstruct__selfaware.json",
    }),
    ("cold DPO s1", {
        "p_rc": PANEL_DIR / "metrics_cold_dpo_seed1_prc__selfaware.json",
        "p_struct": PANEL_DIR / "metrics_cold_dpo_seed1_pstruct__selfaware.json",
    }),
    ("cold KTO s1", {
        "p_rc": PANEL_DIR / "metrics_cold_kto_seed1_prc__selfaware.json",
        "p_struct": PANEL_DIR / "metrics_cold_kto_seed1_pstruct__selfaware.json",
    }),
    ("cold GRPO s1", {
        # own cell: measured in experiments/grpo-cold-start-induction, not re-run
        # in the panel. See AMENDMENT.md:177 "(85.66 / 60.89, its own cell)".
        "p_rc": GRPO_DIR / "metrics_cold_base_grpo_v2_seed1__selfaware.json",
        "p_struct": PANEL_DIR / "metrics_cold_grpo_seed1_pstruct__selfaware.json",
    }),
    ("cold SFT s1", {
        "p_struct": PANEL_DIR / "metrics_cold_sft_seed1_pstruct__selfaware.json",
    }),
    ("clean-SFT merged", {
        "p_struct": PANEL_DIR / "metrics_clean_sft_merged_pstruct__selfaware.json",
    }),
    ("SFT→GRPO s1", {
        "p_struct": PANEL_DIR / "metrics_clean_sft_grpo_v2_seed1_pstruct__selfaware.json",
    }),
]

# fig-p1-12: (label, path, family) in the lead-specified bar order.
FIG12_BARS = [
    ("base", PANEL_DIR / "metrics_base_pstruct__selfaware.json", "base"),
    ("cold SFT\nseed 1", PANEL_DIR / "metrics_cold_sft_seed1_pstruct__selfaware.json", "sft"),
    ("cold SFT\nseed 2", SEEDROB_DIR / "metrics_cold_sft_seed2_pstruct__selfaware.json", "sft"),
    ("cold SFT\nseed 3", SEEDROB_DIR / "metrics_cold_sft_seed3_pstruct__selfaware.json", "sft"),
    ("cold DPO\nseed 1", PANEL_DIR / "metrics_cold_dpo_seed1_pstruct__selfaware.json", "dpo"),
    ("cold DPO\nseed 2", SEEDROB_DIR / "metrics_cold_dpo_seed2_pstruct__selfaware.json", "dpo"),
    ("cold DPO\nseed 3", SEEDROB_DIR / "metrics_cold_dpo_seed3_pstruct__selfaware.json", "dpo"),
    ("cold KTO\nseed 1", PANEL_DIR / "metrics_cold_kto_seed1_pstruct__selfaware.json", "kto"),
    ("cold KTO\nseed 2", SEEDROB_DIR / "metrics_cold_kto_seed2_pstruct__selfaware.json", "kto"),
    ("cold KTO\nseed 3", SEEDROB_DIR / "metrics_cold_kto_seed3_pstruct__selfaware.json", "kto"),
    ("cold GRPO\nseed 1", PANEL_DIR / "metrics_cold_grpo_seed1_pstruct__selfaware.json", "grpo"),
    ("clean-SFT\nmerged", PANEL_DIR / "metrics_clean_sft_merged_pstruct__selfaware.json", "sft"),
    ("SFT→GRPO\nseed 1", PANEL_DIR / "metrics_clean_sft_grpo_v2_seed1_pstruct__selfaware.json", "grpo"),
]

SR_G1_FLOOR = 30.0   # pstruct-internalization-seed-robustness AMENDMENT.md SR-G1
R3_CEILING = 10.0    # prompt-vs-training-panel AMENDMENT.md R3

# Transcribed straight from the two amendments' Outcome tables (recall, over_refusal),
# verified against the loaded metrics.json values below before any figure is drawn.
EXPECTED = {
    ("raw base", "p_rc"): (90.89, 65.38),
    ("raw base", "p_plain"): (0.00, 0.04),
    ("raw base", "p_struct"): (0.00, 0.09),
    ("cold DPO s1", "p_rc"): (94.48, 73.34),
    ("cold DPO s1", "p_struct"): (0.00, 0.09),
    ("cold KTO s1", "p_rc"): (93.99, 60.89),
    ("cold KTO s1", "p_struct"): (0.00, 0.04),
    ("cold GRPO s1", "p_rc"): (85.66, 60.89),
    ("cold GRPO s1", "p_struct"): (0.00, 0.09),
    ("cold SFT s1", "p_struct"): (69.57, 47.63),
    ("clean-SFT merged", "p_struct"): (69.48, 49.25),
    ("SFT→GRPO s1", "p_struct"): (77.42, 58.71),
    "cold SFT seed 2": (76.94, 55.97),
    "cold SFT seed 3": (79.36, 54.81),
    "cold DPO seed 2": (0.00, 0.09),
    "cold DPO seed 3": (0.00, 0.09),
    "cold KTO seed 2": (0.00, 0.00),
    "cold KTO seed 3": (0.00, 0.00),
}


def load_fig11() -> dict[str, dict[str, dict]]:
    """checkpoint -> condition -> {recall, over_refusal, config_sha, path}"""
    mismatches: list[str] = []
    out: dict[str, dict[str, dict]] = {}
    for checkpoint, conditions in FIG11_CHECKPOINTS:
        out[checkpoint] = {}
        for cond, path in conditions.items():
            recall, over_ref, sha = _rr(path)
            out[checkpoint][cond] = {"recall": recall, "over_refusal": over_ref, "config_sha": sha, "path": path}
            expected = EXPECTED.get((checkpoint, cond))
            if expected is not None and (abs(expected[0] - recall) > 0.005 or abs(expected[1] - over_ref) > 0.005):
                mismatches.append(
                    f"{checkpoint}/{cond}: amendment table says {expected}, "
                    f"metrics.json ({path.relative_to(REPO)}) says ({recall}, {over_ref})"
                )
    if mismatches:
        raise ValueError("fig-11 cross-check against AMENDMENT.md Outcome table FAILED:\n" + "\n".join(mismatches))
    return out


def load_fig12() -> list[dict]:
    mismatches: list[str] = []
    rows: list[dict] = []
    seed_expected_keys = {
        "cold SFT\nseed 2": "cold SFT seed 2",
        "cold SFT\nseed 3": "cold SFT seed 3",
        "cold DPO\nseed 2": "cold DPO seed 2",
        "cold DPO\nseed 3": "cold DPO seed 3",
        "cold KTO\nseed 2": "cold KTO seed 2",
        "cold KTO\nseed 3": "cold KTO seed 3",
    }
    for label, path, family in FIG12_BARS:
        recall, over_ref, sha = _rr(path)
        rows.append({"label": label, "recall": recall, "over_refusal": over_ref, "family": family, "path": path})
        expected = seed_expected_keys.get(label)
        expected_vals = EXPECTED.get(expected) if expected else None
        if expected_vals is not None and (abs(expected_vals[0] - recall) > 0.005 or abs(expected_vals[1] - over_ref) > 0.005):
            mismatches.append(
                f"{label.replace(chr(10), ' ')}: amendment table says {expected_vals}, "
                f"metrics.json ({path.relative_to(REPO)}) says ({recall}, {over_ref})"
            )
    if mismatches:
        raise ValueError("fig-12 cross-check against AMENDMENT.md Outcome table FAILED:\n" + "\n".join(mismatches))
    return rows


# --------------------------------------------------------------- fig-p1-11 PNG

def write_fig11_png(path: Path, data: dict[str, dict[str, dict]]) -> None:
    img, draw = _new_chart(1650, 980)
    _draw_title(
        draw,
        "Prompt condition crosses training regimen",
        "Refusal recall on unknown-labeled rows (%); unmeasured checkpoint x condition cells are simply absent",
    )
    left, top, plot_w, plot_h = 130, 170, 1180, 560
    y_label = _draw_axes(
        draw, left, top, plot_w, plot_h,
        x_label="", y_label="Unknown-question refusal recall (%)",
        show_x_ticks=False, bottom_pad=118,
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)

    checkpoints = [c for c, _ in FIG11_CHECKPOINTS]
    group_w = plot_w / len(checkpoints)
    bar_w = 40
    slot_gap = 8
    base_rc_bar = None
    grpo_rc_bar = None
    for g, checkpoint in enumerate(checkpoints):
        center = left + group_w * (g + 0.5)
        _draw_wrapped_label(draw, center, top + plot_h + 26, checkpoint, _font(16, bold=True), max_width=int(group_w) - 6)
        conds_here = [c for c in PROMPT_ORDER if c in data[checkpoint]]
        n = len(conds_here)
        # Fixed left-to-right slot order (RC, plain, struct); missing slots
        # are simply skipped rather than re-centering the remaining bars, so
        # a reader learns one horizontal position -> condition mapping across
        # every group in the figure.
        slot_x = {
            "p_rc": center - (bar_w + slot_gap),
            "p_plain": center,
            "p_struct": center + (bar_w + slot_gap),
        }
        for cond in PROMPT_ORDER:
            if cond not in data[checkpoint]:
                continue
            val = data[checkpoint][cond]["recall"]
            x0 = int(slot_x[cond] - bar_w / 2)
            x1 = x0 + bar_w
            y0 = top + plot_h - int(val / 100 * plot_h)
            y1 = top + plot_h
            draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=PROMPT_COLORS[cond])
            _draw_text(draw, ((x0 + x1) / 2, y0 - 10), f"{val:.1f}", _font(14, bold=True), fill=PROMPT_COLORS[cond], anchor="mm")
            if checkpoint == "raw base" and cond == "p_rc":
                base_rc_bar = (x0, x1, y0)
            if checkpoint == "cold GRPO s1" and cond == "p_rc":
                grpo_rc_bar = (x0, x1, y0)

    # Counterfactual marker on the base response-confidence bar: the only
    # measured cell where an untrained checkpoint reads near-ceiling recall.
    # A small in-plot glyph (not a filled card) so it never paints over the
    # bar itself or its value label near the top of a 0-100 axis; the
    # explanation lives in the "Markers" side card instead.
    if base_rc_bar is not None:
        x0, x1, y0 = base_rc_bar
        cx = (x0 + x1) / 2
        _draw_text(draw, (cx, y0 - 30), "‡", _font(17, bold=True), fill=PROMPT_COLORS["p_rc"], anchor="mm")

    # Provenance marker on the cold-GRPO response-confidence bar: this cell
    # is not re-run here, it is the arm's own cell in
    # experiments/grpo-cold-start-induction (AMENDMENT.md:177, "its own cell").
    if grpo_rc_bar is not None:
        x0, x1, y0 = grpo_rc_bar
        cx = (x0 + x1) / 2
        _draw_text(draw, (cx, y0 - 30), "†", _font(17, bold=True), fill=PROMPT_COLORS["p_rc"], anchor="mm")

    legend_x, legend_y = 1360, 180
    _draw_card(draw, (1335, 150, 1620, 320))
    _draw_text(draw, (1360, 178), "Prompt condition", _font(19, bold=True), anchor="la")
    for i, cond in enumerate(PROMPT_ORDER):
        y = legend_y + 42 + i * 40
        draw.rounded_rectangle((1360, y - 12, 1388, y + 14), radius=5, fill=PROMPT_COLORS[cond])
        _draw_text(draw, (1402, y + 3), PROMPT_LABELS[cond], _font(17), anchor="la")

    _draw_card(draw, (1335, 335, 1620, 470))
    _draw_text(draw, (1360, 358), "The 0-to-94 exhibit", _font(18, bold=True), anchor="la")
    for i, line in enumerate([
        "Cold DPO/KTO/GRPO track the",
        "untrained base under struct/plain",
        "(0≈0) and under RC (94≈91):",
        "same checkpoint, opposite reading.",
    ]):
        _draw_text(draw, (1360, 388 + i * 22), line, _font(14), fill=PNG_COLORS["muted"], anchor="la")

    _draw_card(draw, (1335, 485, 1620, 640))
    _draw_text(draw, (1360, 508), "Markers", _font(18, bold=True), anchor="la")
    for i, line in enumerate([
        "‡ counterfactual: the only",
        "near-ceiling read from an",
        "untrained checkpoint (raw",
        "base, RC prompt).",
        "† provenance: read from its",
        "its own experiment's",
        "evaluation, not re-run here.",
    ]):
        _draw_text(draw, (1360, 538 + i * 22), line, _font(14), fill=PNG_COLORS["muted"], anchor="la")

    _save_png(img, path)


def _draw_wrapped_label(draw, cx: float, top_y: float, text: str, font, max_width: int) -> None:
    words = text.replace("→", "→ ").split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        w, _ = _text_size(draw, candidate, font)
        if w > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    for i, line in enumerate(lines):
        _draw_text(draw, (cx, top_y + i * 20), line.replace("→ ", "→"), font, anchor="mm")


# --------------------------------------------------------------- fig-p1-11 SVG

def write_fig11_svg(path: Path, data: dict[str, dict[str, dict]]) -> None:
    width, height = 1180, 700
    left, top, plot_w, plot_h = 120, 70, 760, 400
    checkpoints = [c for c, _ in FIG11_CHECKPOINTS]
    elements = [
        _svg_text(width / 2, 26, "Prompt condition crosses training regimen", 18),
        _svg_text(width / 2, 46, "Refusal recall on unknown-labeled rows (%); unmeasured cells are absent", 12, "middle"),
        f'<text x="24" y="{top + plot_h / 2:.1f}" transform="rotate(-90 24 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="13" text-anchor="middle" fill="#202020">Unknown-question refusal recall (%)</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020"/>',
    ]
    for tick in range(0, 101, 20):
        y = top + plot_h - tick / 100 * plot_h
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(left - 16, y + 4, str(tick), 10, "end"))
    group_w = plot_w / len(checkpoints)
    bar_w = 24
    slot_gap = 5
    base_rc_x = None
    grpo_rc_x = None
    for g, checkpoint in enumerate(checkpoints):
        center = left + group_w * (g + 0.5)
        for line_i, line in enumerate(checkpoint.replace("→", "→ ").split(" ")):
            elements.append(_svg_text(center, top + plot_h + 20 + line_i * 13, _svg_escape(line.replace("→ ", "→")), 9))
        slot_x = {
            "p_rc": center - (bar_w + slot_gap),
            "p_plain": center,
            "p_struct": center + (bar_w + slot_gap),
        }
        for cond in PROMPT_ORDER:
            if cond not in data[checkpoint]:
                continue
            val = data[checkpoint][cond]["recall"]
            color = f"rgb{PROMPT_COLORS[cond]}"
            x = slot_x[cond] - bar_w / 2
            y = top + plot_h - val / 100 * plot_h
            h = val / 100 * plot_h
            elements.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}"/>')
            elements.append(_svg_text(x + bar_w / 2, y - 5, f"{val:.1f}", 9))
            if checkpoint == "raw base" and cond == "p_rc":
                base_rc_x = (x + bar_w / 2, y)
            if checkpoint == "cold GRPO s1" and cond == "p_rc":
                grpo_rc_x = (x + bar_w / 2, y)
    if base_rc_x is not None:
        cx, cy = base_rc_x
        elements.append(_svg_text(cx, cy - 18, "‡", 13))
    if grpo_rc_x is not None:
        cx, cy = grpo_rc_x
        elements.append(_svg_text(cx, cy - 18, "†", 13))
    legend_x, legend_y = 900, 110
    for i, cond in enumerate(PROMPT_ORDER):
        y = legend_y + i * 26
        elements.append(f'<rect x="{legend_x}" y="{y - 9}" width="16" height="16" fill="rgb{PROMPT_COLORS[cond]}"/>')
        elements.append(_svg_text(legend_x + 24, y + 4, PROMPT_LABELS[cond], 11, "start"))
    elements.append(
        _svg_text(
            width / 2, height - 26,
            "‡ counterfactual: only near-ceiling read from an untrained checkpoint (raw base, RC prompt)",
            9, "middle",
        )
    )
    elements.append(
        _svg_text(
            width / 2, height - 14,
            "† provenance: cold GRPO RC value is its own experiment's evaluation, not re-run here",
            9, "middle",
        )
    )
    _write_svg(path, width, height, elements)


# --------------------------------------------------------------- fig-p1-12 PNG

def write_fig12_png(path: Path, rows: list[dict]) -> None:
    img, draw = _new_chart(1750, 950)
    _draw_title(
        draw,
        "Instruction-free internalization by seed",
        "Structure-only prompt, refusal recall on unknown-labeled rows (%); dashed lines are pre-registered thresholds",
    )
    left, top, plot_w, plot_h = 120, 170, 1300, 540
    y_label = _draw_axes(
        draw, left, top, plot_w, plot_h,
        x_label="", y_label="Refusal recall, structure-only prompt (%)",
        show_x_ticks=False, bottom_pad=112,
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)

    group_w = plot_w / len(rows)
    bar_w = 52
    for i, row in enumerate(rows):
        center = left + group_w * (i + 0.5)
        color = FAMILY_COLORS[row["family"]]
        val = row["recall"]
        x0 = int(center - bar_w / 2)
        x1 = x0 + bar_w
        y0 = top + plot_h - int(val / 100 * plot_h)
        y1 = top + plot_h
        draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=color)
        _draw_text(draw, ((x0 + x1) / 2, y0 - 10), f"{val:.1f}", _font(13, bold=True), fill=color, anchor="mm")
        for line_i, line in enumerate(row["label"].split("\n")):
            _draw_text(draw, (center, top + plot_h + 24 + line_i * 20), line, _font(14, bold=True), anchor="mm")

    # Two registered numeric thresholds. Deliberately styled like
    # build_extended_figures.py's axhline+text "collapse gate (0.10)" /
    # "chance" reference lines, NOT like the shared ideal_zone.py wash: these
    # are literal frozen numbers (SR-G1's 30% floor, the panel's R3 10%
    # ceiling), the exact case that convention's docstring says never to use
    # it for.
    # Label x-position is pinned to the empty DPO/KTO/cold-GRPO band (all
    # 0.00 bars, indices 4-10 of 13) so the label text never sits over a
    # tall bar; the dashed line itself still spans the full plot width.
    label_x = left + group_w * 7.5
    floor_y = top + plot_h - int(SR_G1_FLOOR / 100 * plot_h)
    _draw_dashed_hline(draw, left, left + plot_w, floor_y, (201, 151, 58), width=2, dash=9, gap=6)
    _draw_text(draw, (label_x, floor_y - 14), "internalization floor (30%, preregistered)", _font(14, bold=True), fill=(201, 151, 58), anchor="mm")

    ceil_y = top + plot_h - int(R3_CEILING / 100 * plot_h)
    _draw_dashed_hline(draw, left, left + plot_w, ceil_y, PNG_COLORS["muted"], width=2, dash=9, gap=6)
    _draw_text(draw, (label_x, ceil_y - 14), "base ceiling (10%, preregistered)", _font(14, bold=True), fill=PNG_COLORS["muted"], anchor="mm")

    legend_x, legend_y = 1500, 180
    _draw_card(draw, (1475, 150, 1720, 400))
    _draw_text(draw, (1500, 178), "Family", _font(19, bold=True), anchor="la")
    family_legend = [("base", "base"), ("sft", "SFT-lineage"), ("dpo", "DPO"), ("kto", "KTO"), ("grpo", "GRPO-touching")]
    for i, (key, label) in enumerate(family_legend):
        y = legend_y + 42 + i * 36
        draw.rounded_rectangle((1500, y - 12, 1528, y + 14), radius=5, fill=FAMILY_COLORS[key])
        _draw_text(draw, (1542, y + 3), label, _font(16), anchor="la")

    _draw_text(
        draw, (left, top + plot_h + 88),
        "All non-SFT-lineage bars score 0.00 under the pinned scorer; a row-level audit",
        _font(13), fill=PNG_COLORS["muted"], anchor="lm",
    )
    _draw_text(
        draw, (left, top + plot_h + 106),
        "puts their honest band at ~4-6% recall, still under the 10% ceiling.",
        _font(13), fill=PNG_COLORS["muted"], anchor="lm",
    )
    _save_png(img, path)


# --------------------------------------------------------------- fig-p1-12 SVG

def write_fig12_svg(path: Path, rows: list[dict]) -> None:
    width, height = 1300, 640
    left, top, plot_w, plot_h = 110, 60, 900, 400
    elements = [
        _svg_text(width / 2, 24, "Instruction-free internalization by seed", 17),
        _svg_text(width / 2, 42, "Structure-only prompt, refusal recall on unknown-labeled rows (%)", 11, "middle"),
        f'<text x="22" y="{top + plot_h / 2:.1f}" transform="rotate(-90 22 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="#202020">Refusal recall (%)</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020"/>',
    ]
    for tick in range(0, 101, 20):
        y = top + plot_h - tick / 100 * plot_h
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(left - 14, y + 4, str(tick), 9, "end"))
    group_w = plot_w / len(rows)
    bar_w = 32
    for i, row in enumerate(rows):
        center = left + group_w * (i + 0.5)
        color = f"rgb{FAMILY_COLORS[row['family']]}"
        val = row["recall"]
        x = center - bar_w / 2
        y = top + plot_h - val / 100 * plot_h
        h = val / 100 * plot_h
        elements.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}"/>')
        elements.append(_svg_text(center, y - 5, f"{val:.1f}", 8))
        for line_i, line in enumerate(row["label"].split("\n")):
            elements.append(_svg_text(center, top + plot_h + 16 + line_i * 11, _svg_escape(line), 8))
    # Label x is pinned to the empty DPO/KTO/cold-GRPO band (indices 4-10 of
    # 13, all 0.00 bars) so it never sits over a tall bar.
    label_x = left + group_w * 7.5
    floor_y = top + plot_h - SR_G1_FLOOR / 100 * plot_h
    elements.append(_svg_dashed_hline(left, left + plot_w, floor_y, "rgb(201,151,58)", 2.0, "8,5"))
    elements.append(_svg_text(label_x, floor_y - 8, "internalization floor 30% (preregistered)", 9))
    ceil_y = top + plot_h - R3_CEILING / 100 * plot_h
    elements.append(_svg_dashed_hline(left, left + plot_w, ceil_y, f"rgb{PNG_COLORS['muted']}", 2.0, "8,5"))
    elements.append(_svg_text(label_x, ceil_y - 8, "base ceiling 10% (preregistered)", 9))
    legend_x, legend_y = 1030, 100
    family_legend = [("base", "base"), ("sft", "SFT-lineage"), ("dpo", "DPO"), ("kto", "KTO"), ("grpo", "GRPO-touching")]
    for i, (key, label) in enumerate(family_legend):
        y = legend_y + i * 26
        elements.append(f'<rect x="{legend_x}" y="{y - 9}" width="16" height="16" fill="rgb{FAMILY_COLORS[key]}"/>')
        elements.append(_svg_text(legend_x + 24, y + 4, label, 11, "start"))
    elements.append(
        _svg_text(
            width / 2, height - 12,
            "0.00 non-SFT bars: descriptive scorer-scope audit puts honest recall at ~4-6%, still below the 10% ceiling",
            9, "middle",
        )
    )
    _write_svg(path, width, height, elements)


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig11_data = load_fig11()
    fig12_rows = load_fig12()

    write_fig11_png(FIGURES / "fig-p1-11-prompt-crossing.png", fig11_data)
    write_fig11_svg(FIGURES / "fig-p1-11-prompt-crossing.svg", fig11_data)
    write_fig12_png(FIGURES / "fig-p1-12-internalization-seeds.png", fig12_rows)
    write_fig12_svg(FIGURES / "fig-p1-12-internalization-seeds.svg", fig12_rows)

    print("Cross-check against AMENDMENT.md Outcome tables: PASS")
    print(f"Wrote {FIGURES / 'fig-p1-11-prompt-crossing.png'}")
    print(f"Wrote {FIGURES / 'fig-p1-11-prompt-crossing.svg'}")
    print(f"Wrote {FIGURES / 'fig-p1-12-internalization-seeds.png'}")
    print(f"Wrote {FIGURES / 'fig-p1-12-internalization-seeds.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
