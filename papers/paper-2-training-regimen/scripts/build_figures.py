"""Build reproducible Paper 2 result tables from local locked training-regimen eval artifacts.

This script intentionally reads the persisted eval outputs rather than the
manuscript scaffold. It summarizes the available SelfAware seed-complete local
4B runs, SFT-warmed preference runs, and stated-confidence artifacts for paper drafting.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev

from PIL import Image, ImageDraw, ImageFont


REPO = Path(__file__).resolve().parents[3]
EVAL_ROOT = REPO / "archive" / "experiment" / "phase1" / "eval"
PAPER_ROOT = REPO / "papers" / "paper-2-training-regimen"
DEFAULT_OUT = PAPER_ROOT / "analysis"
DEFAULT_FIGURES = PAPER_ROOT / "figures"
AMENDMENT_B_REPORT = (
    REPO / "archive" / "experiment" / "phase1" / "eval" / "analysis" / "amendment_b_sequential_results_report.md"
)
AMENDMENT_B_SEQ_PREFIX = "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq"
T_975_DF2 = 4.302652729911275
COLORS = {
    "sft": "#2f6f4e",
    "dpo": "#4f78a8",
    "kto": "#b85c38",
    "sft_merged": "#6f5f9f",
}
PNG_COLORS = {
    "sft": (47, 111, 78),
    "dpo": (68, 105, 151),
    "kto": (174, 83, 56),
    "sft_merged": (111, 95, 159),
    "grid": (217, 214, 205),
    "axis": (43, 48, 54),
    "text": (31, 41, 51),
    "muted": (92, 99, 112),
    "paper": (255, 255, 255),
    "panel": (255, 255, 255),
}

SELF_AWARE_SEED_DIRS = {
    1: EVAL_ROOT / "results_selfaware_full_seed1_all_arms_4b_20260615_2148",
    2: EVAL_ROOT / "results_selfaware_full_seed2_all_arms_4b_20260615_2148",
    3: EVAL_ROOT / "results_selfaware_full_seed3_all_arms_4b_20260616_0615",
}

AMENDMENT_A_SUMMARY_TABLES = [
    (
        "seed1_all",
        EVAL_ROOT / "results_amendment_a_selfaware_full_local_4b" / "comparisons" / "summary_table.csv",
    ),
    (
        "seed2_dpo_clean",
        EVAL_ROOT
        / "results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b"
        / "comparisons"
        / "summary_table.csv",
    ),
    (
        "seed2_kto_clean",
        EVAL_ROOT
        / "results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b"
        / "comparisons"
        / "summary_table.csv",
    ),
    (
        "seed3_dpo",
        EVAL_ROOT
        / "results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b"
        / "comparisons"
        / "summary_table.csv",
    ),
]

METRICS = [
    "truthful_pct",
    "refusal_recall_pct",
    "over_refusal_pct",
    "correct_on_known_pct",
    "answer_on_unknown_pct",
]


@dataclass(frozen=True)
class SeedMetricRow:
    seed: int
    arm: str
    n: int
    n_unknown: int
    n_known: int
    truthful_pct: float
    refusal_recall_pct: float
    over_refusal_pct: float
    correct_on_known_pct: float
    answer_on_unknown_pct: float
    config_sha: str
    source_csv: str


def _read_summary_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_selfaware_seed_metrics() -> list[SeedMetricRow]:
    rows: list[SeedMetricRow] = []
    for seed, result_dir in SELF_AWARE_SEED_DIRS.items():
        csv_path = result_dir / "comparisons" / "summary_table.csv"
        for row in _read_summary_csv(csv_path):
            arm = row["arm"].split("_seed", 1)[0]
            rows.append(
                SeedMetricRow(
                    seed=seed,
                    arm=arm,
                    n=int(row["n"]),
                    n_unknown=int(row["n_unknown_labeled"]),
                    n_known=int(row["n_known_labeled"]),
                    truthful_pct=float(row["truthful_pct"]),
                    refusal_recall_pct=float(row["refusal_recall_pct"]),
                    over_refusal_pct=float(row["over_refusal_pct"]),
                    correct_on_known_pct=float(row["correct_on_known_pct"]),
                    answer_on_unknown_pct=float(row["answer_on_unknown_pct"]),
                    config_sha=row["config_sha"],
                    source_csv=str(csv_path.relative_to(REPO)),
                )
            )
    return rows


def seed_summary(rows: list[SeedMetricRow]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for arm in sorted({row.arm for row in rows}):
        arm_rows = [row for row in rows if row.arm == arm]
        for metric in METRICS:
            vals = [float(getattr(row, metric)) for row in arm_rows]
            mu = mean(vals)
            sd = stdev(vals)
            ci_half = T_975_DF2 * sd / math.sqrt(len(vals))
            out.append(
                {
                    "arm": arm,
                    "metric": metric,
                    "mean": mu,
                    "sd": sd,
                    "ci95_low": mu - ci_half,
                    "ci95_high": mu + ci_half,
                    "ci95_low_bounded": max(0.0, mu - ci_half),
                    "ci95_high_bounded": min(100.0, mu + ci_half),
                    "n_seeds": len(vals),
                }
            )
    return out


def _read_scored_rows(seed: int, arm: str) -> dict[tuple[str, int], dict[str, object]]:
    result_dir = SELF_AWARE_SEED_DIRS[seed]
    candidates = list(result_dir.glob(f"{arm}_seed{seed}__selfaware/scored_rows.jsonl"))
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected one scored_rows.jsonl for seed={seed} arm={arm}")
    rows: dict[tuple[str, int], dict[str, object]] = {}
    with candidates[0].open(encoding="utf-8") as fh:
        for line in fh:
            payload = json.loads(line)
            rows[(str(payload["eval_set"]), int(payload["row_index"]))] = payload
    return rows


def _logaddexp(a: float, b: float) -> float:
    if a == -math.inf:
        return b
    if b == -math.inf:
        return a
    hi = max(a, b)
    return hi + math.log(math.exp(a - hi) + math.exp(b - hi))


def _binom_logpmf(k: int, n: int) -> float:
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        - n * math.log(2.0)
    )


def exact_mcnemar_p(discordant_a_not_b: int, discordant_b_not_a: int) -> float:
    """Two-sided exact McNemar/binomial p-value under p=0.5."""

    n = discordant_a_not_b + discordant_b_not_a
    if n == 0:
        return 1.0
    tail = min(discordant_a_not_b, discordant_b_not_a)
    log_prob = -math.inf
    for k in range(tail + 1):
        log_prob = _logaddexp(log_prob, _binom_logpmf(k, n))
    return min(1.0, 2.0 * math.exp(log_prob))


def paired_transitions() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for seed in sorted(SELF_AWARE_SEED_DIRS):
        scored = {arm: _read_scored_rows(seed, arm) for arm in ("sft", "dpo", "kto")}
        for arm_a, arm_b in (("sft", "dpo"), ("sft", "kto"), ("dpo", "kto")):
            rows_a = scored[arm_a]
            rows_b = scored[arm_b]
            keys = sorted(set(rows_a) & set(rows_b))
            if len(keys) != len(rows_a) or len(keys) != len(rows_b):
                raise ValueError(f"Row mismatch for seed={seed} {arm_a}->{arm_b}")
            values = {
                "seed": seed,
                "pair": f"{arm_a}->{arm_b}",
                "n_rows": len(keys),
                "truthful_a_not_b": 0,
                "truthful_b_not_a": 0,
                "unknown_a_refused_b_answered": 0,
                "unknown_b_refused_a_answered": 0,
                "known_a_refused_b_answered": 0,
                "known_b_refused_a_answered": 0,
                "known_a_refused_b_correct": 0,
                "known_a_correct_b_bad": 0,
                "known_b_correct_a_bad": 0,
            }
            for key in keys:
                row_a = rows_a[key]
                row_b = rows_b[key]
                if bool(row_a["truthful"]) and not bool(row_b["truthful"]):
                    values["truthful_a_not_b"] += 1
                if bool(row_b["truthful"]) and not bool(row_a["truthful"]):
                    values["truthful_b_not_a"] += 1
                if (
                    row_a["label"] == "unknown"
                    and bool(row_a["refused"])
                    and not bool(row_b["refused"])
                ):
                    values["unknown_a_refused_b_answered"] += 1
                if (
                    row_a["label"] == "unknown"
                    and bool(row_b["refused"])
                    and not bool(row_a["refused"])
                ):
                    values["unknown_b_refused_a_answered"] += 1
                if row_a["label"] == "known" and bool(row_a["refused"]) and not bool(row_b["refused"]):
                    values["known_a_refused_b_answered"] += 1
                    if bool(row_b["correct"]):
                        values["known_a_refused_b_correct"] += 1
                if row_a["label"] == "known" and bool(row_b["refused"]) and not bool(row_a["refused"]):
                    values["known_b_refused_a_answered"] += 1
                if row_a["label"] == "known" and bool(row_a["correct"]) and not bool(row_b["correct"]):
                    values["known_a_correct_b_bad"] += 1
                if row_a["label"] == "known" and bool(row_b["correct"]) and not bool(row_a["correct"]):
                    values["known_b_correct_a_bad"] += 1
            values["truthful_mcnemar_p"] = exact_mcnemar_p(
                int(values["truthful_a_not_b"]),
                int(values["truthful_b_not_a"]),
            )
            values["unknown_refusal_mcnemar_p"] = exact_mcnemar_p(
                int(values["unknown_a_refused_b_answered"]),
                int(values["unknown_b_refused_a_answered"]),
            )
            values["known_refusal_mcnemar_p"] = exact_mcnemar_p(
                int(values["known_a_refused_b_answered"]),
                int(values["known_b_refused_a_answered"]),
            )
            values["known_correct_mcnemar_p"] = exact_mcnemar_p(
                int(values["known_a_correct_b_bad"]),
                int(values["known_b_correct_a_bad"]),
            )
            out.append(values)
    return out


def amendment_a_summary() -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for source_label, csv_path in AMENDMENT_A_SUMMARY_TABLES:
        for row in _read_summary_csv(csv_path):
            out.append(
                {
                    "source": source_label,
                    "arm": row["arm"],
                    "n": int(row["n"]),
                    "n_unknown": int(row["n_unknown_labeled"]),
                    "n_known": int(row["n_known_labeled"]),
                    "truthful_pct": float(row["truthful_pct"]),
                    "refusal_recall_pct": float(row["refusal_recall_pct"]),
                    "over_refusal_pct": float(row["over_refusal_pct"]),
                    "correct_on_known_pct": float(row["correct_on_known_pct"]),
                    "config_sha": row["config_sha"],
                    "source_csv": str(csv_path.relative_to(REPO)),
                }
            )
    return out


def amendment_b_stated_confidence_summary() -> list[dict[str, object]]:
    metrics_paths = sorted(
        path
        for result_dir in EVAL_ROOT.glob(f"{AMENDMENT_B_SEQ_PREFIX}*")
        for path in result_dir.glob("*__selfaware/metrics.json")
    )
    if not metrics_paths:
        raise FileNotFoundError(f"No Amendment B sequential metrics found under {EVAL_ROOT}")

    by_family: dict[str, list[dict[str, float]]] = {"merged SFT": [], "SFT -> DPO": [], "SFT -> KTO": []}
    for path in metrics_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        arm = str(payload["arm"])
        if arm.startswith("sft_dpo"):
            family = "SFT -> DPO"
        elif arm.startswith("sft_kto"):
            family = "SFT -> KTO"
        elif arm.startswith("sft_merged"):
            family = "merged SFT"
        else:
            continue
        stated = payload["stated_confidence"]
        by_family[family].append(
            {
                "confidence_coverage_pct": float(stated["coverage_pct"]),
                "mean_stated_confidence": float(stated["mean_stated_confidence"]),
                "mae_vs_known_label": float(stated["mae_vs_known_label"]),
                "brier_vs_known_label": float(stated["brier_vs_known_label"]),
                "mae_vs_answer_correctness": float(stated["mae_vs_answer_correctness"]),
                "brier_vs_answer_correctness": float(stated["brier_vs_answer_correctness"]),
            }
        )

    report_rows_by_arm = {}
    if AMENDMENT_B_REPORT.exists():
        in_table = False
        for line in AMENDMENT_B_REPORT.read_text(encoding="utf-8").splitlines():
            if line.startswith("| Arm | Refusal recall |"):
                in_table = True
                continue
            if not in_table:
                continue
            if report_rows_by_arm and not line.startswith("|"):
                break
            if line.startswith("| ---") or not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 7 or cells[0] == "Transition":
                break
            report_rows_by_arm[cells[0]] = {
                "refusal_recall_pct": float(cells[1]),
                "over_refusal_pct": float(cells[2]),
                "correct_on_known_pct": float(cells[3]),
                "truthful_pct": float(cells[4]),
            }

    rows: list[dict[str, object]] = []
    for family in ("merged SFT", "SFT -> DPO", "SFT -> KTO"):
        metrics = by_family[family]
        if not metrics:
            raise ValueError(f"No Amendment B metrics for {family}")
        report_metrics = report_rows_by_arm.get(family, {})
        rows.append(
            {
                "arm": family,
                "n_seeds": len(metrics),
                "refusal_recall_pct": report_metrics.get("refusal_recall_pct", ""),
                "over_refusal_pct": report_metrics.get("over_refusal_pct", ""),
                "correct_on_known_pct": report_metrics.get("correct_on_known_pct", ""),
                "truthful_pct": report_metrics.get("truthful_pct", ""),
                "confidence_coverage_pct": mean([row["confidence_coverage_pct"] for row in metrics]),
                "mean_stated_confidence": mean([row["mean_stated_confidence"] for row in metrics]),
                "mae_vs_known_label": mean([row["mae_vs_known_label"] for row in metrics]),
                "brier_vs_known_label": mean([row["brier_vs_known_label"] for row in metrics]),
                "mae_vs_answer_correctness": mean([row["mae_vs_answer_correctness"] for row in metrics]),
                "brier_vs_answer_correctness": mean([row["brier_vs_answer_correctness"] for row in metrics]),
                "source_metrics": "local locked training-regimen stated-confidence metrics.json files",
            }
        )
    return rows


def _amendment_b_scored_paths() -> list[Path]:
    return sorted(
        path
        for result_dir in EVAL_ROOT.glob(f"{AMENDMENT_B_SEQ_PREFIX}*")
        for path in result_dir.glob("*__selfaware/scored_rows.jsonl")
    )


def _amendment_b_family(arm: str) -> str:
    if arm.startswith("sft_dpo"):
        return "SFT -> DPO"
    if arm.startswith("sft_kto"):
        return "SFT -> KTO"
    if arm.startswith("sft_merged"):
        return "merged SFT"
    raise ValueError(f"Unexpected Amendment B arm: {arm}")


def _confidence_bucket(row: dict[str, object]) -> tuple[str, str, float, float]:
    label = str(row["label"]).lower()
    refused = bool(row["refused"])
    correct = bool(row["correct"])
    if label == "known" and refused:
        return "known_over_refusal", "Known refusal", 0.0, 1.0
    if label == "known" and correct:
        return "known_correct_answer", "Known correct answer", 1.0, 1.0
    if label == "known":
        return "known_wrong_answer", "Known wrong answer", 0.0, 1.0
    if refused:
        return "unknown_refusal", "Unknown refusal", 0.0, 0.0
    return "unknown_answer", "Unknown answer", 0.0, 0.0


def amendment_b_confidence_alignment() -> list[dict[str, object]]:
    buckets: dict[tuple[str, str], dict[str, object]] = {}
    for path in _amendment_b_scored_paths():
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                confidence = row.get("stated_confidence")
                if confidence is None:
                    continue
                arm = _amendment_b_family(str(row["arm"]))
                bucket, bucket_label, answer_target, known_target = _confidence_bucket(row)
                key = (arm, bucket)
                if key not in buckets:
                    buckets[key] = {
                        "arm": arm,
                        "bucket": bucket,
                        "bucket_label": bucket_label,
                        "n": 0,
                        "conf_sum": 0.0,
                        "answer_sq_error": 0.0,
                        "known_sq_error": 0.0,
                        "high_conf": 0,
                        "source_rows": "local locked training-regimen stated-confidence scored_rows.jsonl files",
                    }
                acc = buckets[key]
                conf = float(confidence)
                acc["n"] = int(acc["n"]) + 1
                acc["conf_sum"] = float(acc["conf_sum"]) + conf
                acc["answer_sq_error"] = float(acc["answer_sq_error"]) + (conf - answer_target) ** 2
                acc["known_sq_error"] = float(acc["known_sq_error"]) + (conf - known_target) ** 2
                if conf >= 0.7:
                    acc["high_conf"] = int(acc["high_conf"]) + 1
    rows: list[dict[str, object]] = []
    order = {
        "known_correct_answer": 1,
        "known_wrong_answer": 2,
        "known_over_refusal": 3,
        "unknown_refusal": 4,
        "unknown_answer": 5,
    }
    for acc in buckets.values():
        n = int(acc["n"])
        rows.append(
            {
                "arm": acc["arm"],
                "bucket": acc["bucket"],
                "bucket_label": acc["bucket_label"],
                "n": n,
                "mean_stated_confidence": float(acc["conf_sum"]) / n if n else 0.0,
                "brier_vs_answer_reality": float(acc["answer_sq_error"]) / n if n else 0.0,
                "brier_vs_known_label": float(acc["known_sq_error"]) / n if n else 0.0,
                "high_conf_pct": _pct(int(acc["high_conf"]), n),
                "source_rows": acc["source_rows"],
            }
        )
    return sorted(rows, key=lambda row: (str(row["arm"]), order[str(row["bucket"])]))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _pct(numerator: int, denominator: int) -> float:
    return round(100.0 * numerator / denominator, 6) if denominator else 0.0


def _markdown_table(rows: list[dict[str, object]], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(_fmt(row[col]) for col in columns) + " |")
    return lines


def _svg_text(x: float, y: float, text: str, size: int = 13, anchor: str = "middle") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" text-anchor="{anchor}" fill="#202020">{text}</text>'
    )


def _svg_escape(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _write_svg(path: Path, width: int, height: int, elements: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(elements)
    path.write_text(
        "\n".join(
            [
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                '<rect width="100%" height="100%" fill="#ffffff"/>',
                body,
                "</svg>",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] = PNG_COLORS["text"],
    anchor: str = "la",
) -> None:
    draw.text((int(xy[0]), int(xy[1])), text, font=font, fill=fill, anchor=anchor)


def _new_chart(width: int = 1400, height: int = 900) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), PNG_COLORS["paper"])
    draw = ImageDraw.Draw(img)
    return img, draw


def _save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)


def _draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle(box, radius=18, fill=PNG_COLORS["panel"], outline=(232, 229, 220), width=2)


def _draw_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str | None = None) -> None:
    _draw_text(draw, (70, 46), title, _font(34, bold=True), anchor="la")
    if subtitle:
        _draw_text(draw, (70, 92), subtitle, _font(20), fill=PNG_COLORS["muted"], anchor="la")


def _draw_axes(
    draw: ImageDraw.ImageDraw,
    left: int,
    top: int,
    width: int,
    height: int,
    *,
    x_label: str,
    y_label: str,
    y_max: float = 100.0,
    x_max: float = 100.0,
    y_tick_step: int = 20,
    x_tick_step: int = 20,
    show_x_ticks: bool = True,
    bottom_pad: int | None = None,
) -> None:
    if bottom_pad is None:
        bottom_pad = 82 if x_label else 68
    _draw_card(draw, (left - 24, top - 24, left + width + 24, top + height + bottom_pad))
    for tick in range(0, int(y_max) + 1, y_tick_step):
        y = top + height - int((tick / y_max) * height)
        draw.line((left, y, left + width, y), fill=PNG_COLORS["grid"], width=1)
        _draw_text(draw, (left - 18, y), str(tick), _font(16), fill=PNG_COLORS["muted"], anchor="rm")
    if show_x_ticks:
        for tick in range(0, int(x_max) + 1, x_tick_step):
            x = left + int((tick / x_max) * width)
            draw.line((x, top, x, top + height), fill=(238, 235, 228), width=1)
            _draw_text(draw, (x, top + height + 24), str(tick), _font(16), fill=PNG_COLORS["muted"], anchor="mm")
    draw.line((left, top + height, left + width, top + height), fill=PNG_COLORS["axis"], width=3)
    draw.line((left, top, left, top + height), fill=PNG_COLORS["axis"], width=3)
    if x_label:
        _draw_text(draw, (left + width / 2, top + height + 58), x_label, _font(20, bold=True), anchor="mm")
    y_img = Image.new("RGBA", (height + 80, 40), (0, 0, 0, 0))
    y_draw = ImageDraw.Draw(y_img)
    y_draw.text((int((height + 80) / 2), 18), y_label, font=_font(20, bold=True), fill=PNG_COLORS["text"], anchor="mm")
    y_img = y_img.rotate(270, expand=True)
    return y_img


def _paste_y_axis_label(
    img: Image.Image,
    y_label: Image.Image,
    left: int,
    top: int,
    plot_h: int,
) -> None:
    x = max(16, left - 108)
    y = int(top + plot_h / 2 - y_label.height / 2)
    img.paste(y_label, (x, y), y_label)


def _plot_point(x: float, y: float, left: int, top: int, width: int, height: int, x_max: float = 100.0, y_max: float = 100.0) -> tuple[int, int]:
    return left + int((x / x_max) * width), top + height - int((y / y_max) * height)


def write_tradeoff_png(path: Path, seed_rows: list[SeedMetricRow]) -> None:
    img, draw = _new_chart()
    _draw_title(draw, "Cold-start SelfAware abstention tradeoff", "SFT learns refusal; cold-start preference arms mostly answer everything")
    left, top, plot_w, plot_h = 130, 160, 820, 560
    y_label = _draw_axes(
        draw,
        left,
        top,
        plot_w,
        plot_h,
        x_label="Known-question over-refusal (%)",
        y_label="Unknown-question refusal recall (%)",
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)
    for arm, label in (("sft", "SFT"), ("dpo", "DPO"), ("kto", "KTO")):
        arm_rows = [row for row in seed_rows if row.arm == arm]
        color = PNG_COLORS[arm]
        for row in arm_rows:
            x, y = _plot_point(row.over_refusal_pct, row.refusal_recall_pct, left, top, plot_w, plot_h)
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color + (120,) if len(color) == 4 else color, outline=(255, 255, 255), width=2)
        mx = mean([row.over_refusal_pct for row in arm_rows])
        my = mean([row.refusal_recall_pct for row in arm_rows])
        x, y = _plot_point(mx, my, left, top, plot_w, plot_h)
        draw.ellipse((x - 16, y - 16, x + 16, y + 16), fill=color, outline=PNG_COLORS["axis"], width=3)
        if arm == "sft":
            _draw_text(draw, (x + 24, y - 36), f"{label} mean", _font(19, bold=True), fill=color, anchor="la")
    _draw_text(draw, (175, 606), "DPO/KTO means cluster at the origin", _font(18, bold=True), fill=PNG_COLORS["muted"], anchor="la")
    _draw_text(draw, (175, 634), "See the zoom panel for separation.", _font(17), fill=PNG_COLORS["muted"], anchor="la")
    draw.line((164, 625, left + 12, top + plot_h - 10), fill=PNG_COLORS["muted"], width=2)
    legend_x, legend_y = 1010, 180
    _draw_card(draw, (990, 146, 1325, 374))
    _draw_text(draw, (1025, 185), "Reading the plot", _font(22, bold=True), anchor="la")
    notes = [
        "Small points are seeds.",
        "Large points are seed means.",
        "Upper-left is better:",
        "high unknown refusal,",
        "low known over-refusal.",
    ]
    for i, note in enumerate(notes):
        _draw_text(draw, (1025, 225 + i * 28), note, _font(18), fill=PNG_COLORS["muted"], anchor="la")
    inset_w, inset_h = 250, 160
    _draw_card(draw, (990, 398, 1325, 760))
    _draw_text(draw, (1025, 432), "Origin zoom", _font(22, bold=True), anchor="la")
    _draw_text(draw, (1025, 462), "DPO and KTO are both", _font(17), fill=PNG_COLORS["muted"], anchor="la")
    _draw_text(draw, (1025, 487), "near zero refusal.", _font(17), fill=PNG_COLORS["muted"], anchor="la")
    axis_top = 540
    axis_left = 1040
    draw.rectangle((axis_left, axis_top, axis_left + inset_w, axis_top + inset_h), fill=(252, 252, 249), outline=PNG_COLORS["axis"], width=2)
    for tick, label in ((0.0, "0.0"), (0.1, "0.1"), (0.2, "0.2"), (0.3, "0.3")):
        x = axis_left + int((tick / 0.35) * inset_w)
        draw.line((x, axis_top, x, axis_top + inset_h), fill=(232, 229, 220), width=1)
        _draw_text(draw, (x, axis_top + inset_h + 22), label, _font(13), fill=PNG_COLORS["muted"], anchor="mm")
    for tick, label in ((0.0, "0.0"), (0.1, "0.1"), (0.2, "0.2")):
        y = axis_top + inset_h - int((tick / 0.2) * inset_h)
        draw.line((axis_left, y, axis_left + inset_w, y), fill=(232, 229, 220), width=1)
        _draw_text(draw, (axis_left - 8, y), label, _font(13), fill=PNG_COLORS["muted"], anchor="rm")
    for arm, label, dy in (("dpo", "DPO", -18), ("kto", "KTO", 18)):
        arm_rows = [row for row in seed_rows if row.arm == arm]
        mx = mean([row.over_refusal_pct for row in arm_rows])
        my = mean([row.refusal_recall_pct for row in arm_rows])
        x = axis_left + int((mx / 0.35) * inset_w)
        y = axis_top + inset_h - int((my / 0.2) * inset_h)
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=PNG_COLORS[arm], outline=PNG_COLORS["axis"], width=2)
        label_x = min(x + 14, axis_left + inset_w - 50)
        label_y = max(axis_top + 18, min(y + dy, axis_top + inset_h - 26))
        _draw_text(draw, (label_x, label_y), label, _font(16, bold=True), fill=PNG_COLORS[arm], anchor="la")
    _save_png(img, path)


def write_metric_bar_png(path: Path, summary_rows: list[dict[str, object]]) -> None:
    img, draw = _new_chart(1500, 900)
    _draw_title(draw, "Mean SelfAware metrics across three seeds", "Error bars are bounded t-based 95% intervals over seed-level point estimates")
    left, top, plot_w, plot_h = 115, 160, 1060, 560
    y_label = _draw_axes(
        draw,
        left,
        top,
        plot_w,
        plot_h,
        x_label="",
        y_label="Rate (%)",
        show_x_ticks=False,
        bottom_pad=104,
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)
    metrics = [
        ("truthful_pct", "Truthful"),
        ("refusal_recall_pct", "Refusal\nrecall"),
        ("over_refusal_pct", "Over-\nrefusal"),
        ("correct_on_known_pct", "Correct\nknown"),
    ]
    arms = [("sft", "SFT"), ("dpo", "DPO"), ("kto", "KTO")]
    summary = {(str(row["arm"]), str(row["metric"])): row for row in summary_rows}
    group_w = plot_w / len(metrics)
    bar_w = 46
    for g, (metric, label) in enumerate(metrics):
        center = left + group_w * (g + 0.5)
        for line_i, line in enumerate(label.split("\n")):
            _draw_text(draw, (center, top + plot_h + 28 + line_i * 22), line, _font(18, bold=True), anchor="mm")
        for i, (arm, _arm_label) in enumerate(arms):
            row = summary[(arm, metric)]
            val = float(row["mean"])
            ci_low = float(row["ci95_low_bounded"])
            ci_high = float(row["ci95_high_bounded"])
            x0 = int(center + (i - 1) * (bar_w + 14) - bar_w / 2)
            y0 = top + plot_h - int(val / 100 * plot_h)
            x1 = x0 + bar_w
            y1 = top + plot_h
            draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill=PNG_COLORS[arm])
            err_x = int((x0 + x1) / 2)
            err_y1 = top + plot_h - int(ci_high / 100 * plot_h)
            err_y2 = top + plot_h - int(ci_low / 100 * plot_h)
            draw.line((err_x, err_y1, err_x, err_y2), fill=PNG_COLORS["axis"], width=3)
            draw.line((err_x - 9, err_y1, err_x + 9, err_y1), fill=PNG_COLORS["axis"], width=3)
            draw.line((err_x - 9, err_y2, err_x + 9, err_y2), fill=PNG_COLORS["axis"], width=3)
    legend_x, legend_y = 1220, 175
    _draw_card(draw, (1195, 145, 1430, 280))
    for i, (arm, label) in enumerate(arms):
        y = legend_y + i * 38
        draw.rounded_rectangle((1225, y - 12, 1251, y + 14), radius=5, fill=PNG_COLORS[arm])
        _draw_text(draw, (1266, y + 3), label, _font(20), anchor="la")
    _save_png(img, path)


def write_transition_png(path: Path, transition_rows: list[dict[str, object]]) -> None:
    img, draw = _new_chart(1500, 900)
    _draw_title(draw, "SFT refusal transitions under cold-start preference arms", "Most converted refusals do not become correct known answers")
    left, top, plot_w, plot_h = 125, 160, 980, 560
    pairs = ["sft->dpo", "sft->kto"]
    series = [
        ("unknown_a_refused_b_answered", "Unknown refusals lost", (174, 83, 56)),
        ("known_a_refused_b_answered", "Known refusals converted", (68, 105, 151)),
        ("known_a_refused_b_correct", "Converted and correct", (47, 111, 78)),
    ]
    max_val = max(float(row[key]) for row in transition_rows if row["pair"] in pairs for key, _, _ in series)
    y_max = math.ceil(max_val / 250) * 250
    y_label = _draw_axes(
        draw,
        left,
        top,
        plot_w,
        plot_h,
        x_label="",
        y_label="Rows per seed",
        y_max=y_max,
        x_max=100,
        y_tick_step=250,
        show_x_ticks=False,
        bottom_pad=92,
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)
    rows_by_pair = {pair: [row for row in transition_rows if row["pair"] == pair] for pair in pairs}
    group_w = plot_w / len(pairs)
    bar_w = 62
    for p_i, pair in enumerate(pairs):
        center = left + group_w * (p_i + 0.5)
        _draw_text(draw, (center, top + plot_h + 32), pair.upper(), _font(20, bold=True), anchor="mm")
        pair_rows = rows_by_pair[pair]
        for s_i, (key, _label, color) in enumerate(series):
            val = mean([float(row[key]) for row in pair_rows])
            x0 = int(center + (s_i - 1) * (bar_w + 26) - bar_w / 2)
            y0 = top + plot_h - int(val / y_max * plot_h)
            draw.rounded_rectangle((x0, y0, x0 + bar_w, top + plot_h), radius=7, fill=color)
            _draw_text(draw, (x0 + bar_w / 2, y0 - 10), f"{val:.0f}", _font(17, bold=True), fill=color, anchor="mm")
    legend_x, legend_y = 1160, 170
    _draw_card(draw, (1135, 140, 1445, 315))
    for i, (_key, label, color) in enumerate(series):
        y = legend_y + i * 45
        draw.rounded_rectangle((1165, y - 13, 1194, y + 16), radius=5, fill=color)
        _draw_text(draw, (1210, y + 5), label, _font(18), anchor="la")
    _save_png(img, path)


def write_amendment_tradeoff_png(path: Path, amendment_rows: list[dict[str, object]]) -> None:
    img, draw = _new_chart()
    _draw_title(draw, "SFT-warmed SelfAware operating points", "DPO moves farther against refusal; KTO preserves more abstention")
    left, top, plot_w, plot_h = 130, 160, 820, 560
    y_label = _draw_axes(
        draw,
        left,
        top,
        plot_w,
        plot_h,
        x_label="Known-question over-refusal (%)",
        y_label="Unknown-question refusal recall (%)",
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)

    def family(arm: str) -> str:
        if arm.startswith("sft_dpo"):
            return "dpo"
        if arm.startswith("sft_kto"):
            return "kto"
        return "sft_merged"

    for row in amendment_rows:
        fam = family(str(row["arm"]))
        x, y = _plot_point(float(row["over_refusal_pct"]), float(row["refusal_recall_pct"]), left, top, plot_w, plot_h)
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=PNG_COLORS[fam], outline=PNG_COLORS["axis"], width=2)
    callouts = [
        ("Merged SFT", "high refusal,\nhigh over-refusal", "sft_merged", 1000, 185),
        ("SFT -> DPO", "lower over-refusal,\nmore unknown losses", "dpo", 1000, 310),
        ("SFT -> KTO", "more abstention,\nless correction", "kto", 1000, 435),
    ]
    _draw_card(draw, (980, 145, 1330, 565))
    for title, body, color_key, x, y in callouts:
        draw.ellipse((x, y - 10, x + 24, y + 14), fill=PNG_COLORS[color_key], outline=PNG_COLORS["axis"], width=2)
        _draw_text(draw, (x + 42, y + 3), title, _font(20, bold=True), anchor="la")
        for i, line in enumerate(body.split("\n")):
            _draw_text(draw, (x + 42, y + 34 + i * 24), line, _font(18), fill=PNG_COLORS["muted"], anchor="la")
    _save_png(img, path)


def write_stated_confidence_png(path: Path, confidence_rows: list[dict[str, object]]) -> None:
    img, draw = _new_chart(1500, 900)
    _draw_title(draw, "Stated-confidence profile", "Mean confidence is scaled to 0-100; MAE/Brier are shown as error rates x100")
    left, top, plot_w, plot_h = 115, 160, 1040, 560
    y_label = _draw_axes(
        draw,
        left,
        top,
        plot_w,
        plot_h,
        x_label="",
        y_label="Score (0-100)",
        show_x_ticks=False,
        bottom_pad=104,
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)
    arms = [("merged SFT", "Merged SFT", "sft_merged"), ("SFT -> DPO", "SFT -> DPO", "dpo"), ("SFT -> KTO", "SFT -> KTO", "kto")]
    metrics = [
        ("mean_stated_confidence", "Mean\nconfidence", 100),
        ("mae_vs_known_label", "MAE vs\nknown label", 100),
        ("mae_vs_answer_correctness", "MAE vs\ncorrectness", 100),
        ("brier_vs_answer_correctness", "Brier vs\ncorrectness", 100),
    ]
    by_arm = {str(row["arm"]): row for row in confidence_rows}
    group_w = plot_w / len(metrics)
    bar_w = 44
    for g, (metric, label, scale) in enumerate(metrics):
        center = left + group_w * (g + 0.5)
        for line_i, line in enumerate(label.split("\n")):
            _draw_text(draw, (center, top + plot_h + 28 + line_i * 22), line, _font(18, bold=True), anchor="mm")
        for i, (arm, _label, color_key) in enumerate(arms):
            raw = float(by_arm[arm][metric])
            val = raw * scale
            x0 = int(center + (i - 1) * (bar_w + 14) - bar_w / 2)
            y0 = top + plot_h - int(val / 100 * plot_h)
            draw.rounded_rectangle((x0, y0, x0 + bar_w, top + plot_h), radius=6, fill=PNG_COLORS[color_key])
            _draw_text(draw, (x0 + bar_w / 2, y0 - 9), f"{val:.0f}", _font(15, bold=True), fill=PNG_COLORS[color_key], anchor="mm")
    legend_x, legend_y = 1205, 170
    _draw_card(draw, (1185, 140, 1445, 305))
    for i, (_arm, label, color_key) in enumerate(arms):
        y = legend_y + i * 43
        draw.rounded_rectangle((1215, y - 13, 1243, y + 15), radius=5, fill=PNG_COLORS[color_key])
        _draw_text(draw, (1258, y + 5), label, _font(18), anchor="la")
    _draw_card(draw, (1185, 350, 1445, 510))
    _draw_text(draw, (1208, 385), "Coverage", _font(20, bold=True), anchor="la")
    for i, (arm, label, _color_key) in enumerate(arms):
        cov = float(by_arm[arm]["confidence_coverage_pct"])
        _draw_text(draw, (1208, 422 + i * 30), f"{label}: {cov:.2f}%", _font(17), fill=PNG_COLORS["muted"], anchor="la")
    _save_png(img, path)


def write_confidence_alignment_png(path: Path, alignment_rows: list[dict[str, object]]) -> None:
    img, draw = _new_chart(1700, 950)
    _draw_title(draw, "Confidence alignment by actual outcome", "Good calibration is high only for correct factual answers and low for wrong answers or refusals")
    left, top, plot_w, plot_h = 120, 170, 1220, 590
    y_label = _draw_axes(
        draw,
        left,
        top,
        plot_w,
        plot_h,
        x_label="",
        y_label="Mean stated confidence (0-100)",
        show_x_ticks=False,
        bottom_pad=128,
    )
    _paste_y_axis_label(img, y_label, left, top, plot_h)
    arms = [("merged SFT", "Merged SFT", "sft_merged"), ("SFT -> DPO", "SFT -> DPO", "dpo"), ("SFT -> KTO", "SFT -> KTO", "kto")]
    buckets = [
        ("known_correct_answer", "Known\ncorrect\nanswer"),
        ("known_wrong_answer", "Known\nwrong\nanswer"),
        ("known_over_refusal", "Known\nrefusal"),
        ("unknown_refusal", "Unknown\nrefusal"),
        ("unknown_answer", "Unknown\nanswer"),
    ]
    by_key = {(str(row["arm"]), str(row["bucket"])): row for row in alignment_rows}
    group_w = plot_w / len(buckets)
    bar_w = 42
    for g, (bucket, label) in enumerate(buckets):
        center = left + group_w * (g + 0.5)
        for line_i, line in enumerate(label.split("\n")):
            _draw_text(draw, (center, top + plot_h + 28 + line_i * 20), line, _font(16, bold=True), anchor="mm")
        for i, (arm, _label, color_key) in enumerate(arms):
            row = by_key.get((arm, bucket))
            if not row:
                continue
            raw = float(row["mean_stated_confidence"])
            val = raw * 100
            x0 = int(center + (i - 1) * (bar_w + 12) - bar_w / 2)
            y0 = top + plot_h - int(val / 100 * plot_h)
            draw.rounded_rectangle((x0, y0, x0 + bar_w, top + plot_h), radius=6, fill=PNG_COLORS[color_key])
            if val >= 7:
                _draw_text(draw, (x0 + bar_w / 2, y0 - 8), f"{val:.0f}", _font(14, bold=True), fill=PNG_COLORS[color_key], anchor="mm")
    legend_x, legend_y = 1385, 170
    _draw_card(draw, (1360, 140, 1640, 315))
    for i, (_arm, label, color_key) in enumerate(arms):
        y = legend_y + i * 43
        draw.rounded_rectangle((1390, y - 13, 1418, y + 15), radius=5, fill=PNG_COLORS[color_key])
        _draw_text(draw, (1433, y + 5), label, _font(18), anchor="la")
    _draw_card(draw, (1360, 365, 1640, 650))
    _draw_text(draw, (1390, 405), "Interpretation", _font(22, bold=True), anchor="la")
    notes = [
        "Known correct answers",
        "should be high.",
        "Wrong answers and",
        "refusals should be low",
        "for answer-content",
        "confidence.",
        "Known refusals are still",
        "bad boundary behavior."
    ]
    for i, note in enumerate(notes):
        _draw_text(draw, (1390, 442 + i * 24), note, _font(17), fill=PNG_COLORS["muted"], anchor="la")
    _save_png(img, path)


def _plot_xy(
    x: float,
    y: float,
    left: float,
    top: float,
    plot_w: float,
    plot_h: float,
    x_max: float = 100.0,
    y_max: float = 100.0,
) -> tuple[float, float]:
    return left + (x / x_max) * plot_w, top + plot_h - (y / y_max) * plot_h


def write_tradeoff_figure(path: Path, seed_rows: list[SeedMetricRow]) -> None:
    width, height = 760, 520
    left, top, plot_w, plot_h = 95, 70, 520, 350
    elements: list[str] = [
        _svg_text(width / 2, 34, "Cold-start SelfAware abstention tradeoff", 20),
        _svg_text(width / 2, 492, "Known-question over-refusal (%)", 14),
        f'<text x="24" y="{top + plot_h / 2:.1f}" transform="rotate(-90 24 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="14" text-anchor="middle" fill="#202020">Unknown-question refusal recall (%)</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020" stroke-width="1"/>',
    ]
    for tick in range(0, 101, 20):
        x = left + tick / 100 * plot_w
        y = top + plot_h - tick / 100 * plot_h
        elements.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" stroke="#dddddd"/>')
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(x, top + plot_h + 22, str(tick), 11))
        elements.append(_svg_text(left - 20, y + 4, str(tick), 11, "end"))
    for arm in ("sft", "dpo", "kto"):
        arm_rows = [row for row in seed_rows if row.arm == arm]
        color = COLORS[arm]
        for row in arm_rows:
            x, y = _plot_xy(row.over_refusal_pct, row.refusal_recall_pct, left, top, plot_w, plot_h)
            elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{color}" opacity="0.55"/>')
        mx = mean([row.over_refusal_pct for row in arm_rows])
        my = mean([row.refusal_recall_pct for row in arm_rows])
        x, y = _plot_xy(mx, my, left, top, plot_w, plot_h)
        elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{color}" stroke="#202020" stroke-width="1.5"/>')
        elements.append(_svg_text(x + 14, y - 10, arm.upper(), 12, "start"))
    legend_x, legend_y = 640, 110
    elements.append(_svg_text(legend_x, legend_y - 24, "Points = seeds", 12, "start"))
    elements.append(_svg_text(legend_x, legend_y - 8, "Outlined = mean", 12, "start"))
    for i, arm in enumerate(("sft", "dpo", "kto")):
        y = legend_y + i * 28
        elements.append(f'<circle cx="{legend_x + 8}" cy="{y}" r="7" fill="{COLORS[arm]}" stroke="#202020"/>')
        elements.append(_svg_text(legend_x + 24, y + 4, arm.upper(), 12, "start"))
    _write_svg(path, width, height, elements)


def write_metric_bar_figure(path: Path, summary_rows: list[dict[str, object]]) -> None:
    width, height = 860, 520
    left, top, plot_w, plot_h = 90, 70, 610, 340
    metrics = [
        ("truthful_pct", "Truthful"),
        ("refusal_recall_pct", "Refusal recall"),
        ("over_refusal_pct", "Over-refusal"),
        ("correct_on_known_pct", "Correct known"),
    ]
    arms = ["sft", "dpo", "kto"]
    summary = {(str(row["arm"]), str(row["metric"])): row for row in summary_rows}
    elements = [
        _svg_text(width / 2, 34, "Mean SelfAware metrics across three seeds", 20),
        _svg_text(width / 2, 492, "Metric", 14),
        f'<text x="24" y="{top + plot_h / 2:.1f}" transform="rotate(-90 24 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="14" text-anchor="middle" fill="#202020">Rate (%)</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020"/>',
    ]
    for tick in range(0, 101, 20):
        y = top + plot_h - tick / 100 * plot_h
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(left - 18, y + 4, str(tick), 11, "end"))
    group_w = plot_w / len(metrics)
    bar_w = 28
    for g, (metric, label) in enumerate(metrics):
        center = left + group_w * (g + 0.5)
        elements.append(_svg_text(center, top + plot_h + 26, label, 11))
        for i, arm in enumerate(arms):
            row = summary[(arm, metric)]
            val = float(row["mean"])
            ci_low = float(row["ci95_low_bounded"])
            ci_high = float(row["ci95_high_bounded"])
            x = center + (i - 1) * (bar_w + 8) - bar_w / 2
            y = top + plot_h - val / 100 * plot_h
            h = val / 100 * plot_h
            err_y1 = top + plot_h - ci_high / 100 * plot_h
            err_y2 = top + plot_h - ci_low / 100 * plot_h
            elements.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{COLORS[arm]}"/>')
            elements.append(f'<line x1="{x + bar_w/2:.1f}" y1="{err_y1:.1f}" x2="{x + bar_w/2:.1f}" y2="{err_y2:.1f}" stroke="#202020" stroke-width="1.2"/>')
            elements.append(f'<line x1="{x + bar_w/2 - 5:.1f}" y1="{err_y1:.1f}" x2="{x + bar_w/2 + 5:.1f}" y2="{err_y1:.1f}" stroke="#202020"/>')
            elements.append(f'<line x1="{x + bar_w/2 - 5:.1f}" y1="{err_y2:.1f}" x2="{x + bar_w/2 + 5:.1f}" y2="{err_y2:.1f}" stroke="#202020"/>')
    legend_x, legend_y = 725, 110
    for i, arm in enumerate(arms):
        y = legend_y + i * 28
        elements.append(f'<rect x="{legend_x}" y="{y - 10}" width="18" height="18" fill="{COLORS[arm]}"/>')
        elements.append(_svg_text(legend_x + 28, y + 4, arm.upper(), 12, "start"))
    _write_svg(path, width, height, elements)


def write_transition_figure(path: Path, transition_rows: list[dict[str, object]]) -> None:
    width, height = 860, 520
    left, top, plot_w, plot_h = 95, 70, 570, 340
    pairs = ["sft->dpo", "sft->kto"]
    series = [
        ("unknown_a_refused_b_answered", "Unknown refusals lost", "#b85c38"),
        ("known_a_refused_b_answered", "Known refusals converted", "#4f78a8"),
        ("known_a_refused_b_correct", "Converted and correct", "#2f6f4e"),
    ]
    max_val = max(float(row[key]) for row in transition_rows if row["pair"] in pairs for key, _, _ in series)
    y_max = math.ceil(max_val / 250) * 250
    elements = [
        _svg_text(width / 2, 34, "What SFT refusals become under cold-start preference arms", 20),
        f'<text x="24" y="{top + plot_h / 2:.1f}" transform="rotate(-90 24 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="14" text-anchor="middle" fill="#202020">Rows per seed</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020"/>',
    ]
    for tick in range(0, int(y_max) + 1, 250):
        y = top + plot_h - tick / y_max * plot_h
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(left - 18, y + 4, str(tick), 11, "end"))
    rows_by_pair = {pair: [row for row in transition_rows if row["pair"] == pair] for pair in pairs}
    group_w = plot_w / len(pairs)
    bar_w = 24
    for p_i, pair in enumerate(pairs):
        pair_center = left + group_w * (p_i + 0.5)
        elements.append(_svg_text(pair_center, top + plot_h + 28, pair.upper(), 12))
        pair_rows = rows_by_pair[pair]
        for s_i, (key, _label, color) in enumerate(series):
            vals = [float(row[key]) for row in pair_rows]
            val = mean(vals)
            x = pair_center + (s_i - 1) * (bar_w + 12) - bar_w / 2
            y = top + plot_h - val / y_max * plot_h
            h = val / y_max * plot_h
            elements.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{color}"/>')
            elements.append(_svg_text(x + bar_w / 2, y - 6, f"{val:.0f}", 10))
    legend_x, legend_y = 690, 110
    for i, (_key, label, color) in enumerate(series):
        y = legend_y + i * 34
        elements.append(f'<rect x="{legend_x}" y="{y - 10}" width="18" height="18" fill="{color}"/>')
        elements.append(_svg_text(legend_x + 28, y + 4, label, 12, "start"))
    _write_svg(path, width, height, elements)


def write_amendment_tradeoff_figure(path: Path, amendment_rows: list[dict[str, object]]) -> None:
    width, height = 760, 520
    left, top, plot_w, plot_h = 95, 70, 520, 350
    elements = [
        _svg_text(width / 2, 34, "SFT-warmed SelfAware operating points", 20),
        _svg_text(width / 2, 492, "Known-question over-refusal (%)", 14),
        f'<text x="24" y="{top + plot_h / 2:.1f}" transform="rotate(-90 24 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="14" text-anchor="middle" fill="#202020">Unknown-question refusal recall (%)</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020"/>',
    ]
    for tick in range(0, 101, 20):
        x = left + tick / 100 * plot_w
        y = top + plot_h - tick / 100 * plot_h
        elements.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" stroke="#dddddd"/>')
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(x, top + plot_h + 22, str(tick), 11))
        elements.append(_svg_text(left - 20, y + 4, str(tick), 11, "end"))
    def family(arm: str) -> str:
        if arm.startswith("sft_dpo"):
            return "dpo"
        if arm.startswith("sft_kto"):
            return "kto"
        return "sft_merged"
    for row in amendment_rows:
        fam = family(str(row["arm"]))
        x, y = _plot_xy(float(row["over_refusal_pct"]), float(row["refusal_recall_pct"]), left, top, plot_w, plot_h)
        elements.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{COLORS[fam]}" stroke="#202020" opacity="0.85"/>')
        elements.append(_svg_text(x + 12, y - 8, _svg_escape(row["source"]), 10, "start"))
    legend_x, legend_y = 640, 110
    labels = [("sft_merged", "Merged SFT"), ("dpo", "SFT -> DPO"), ("kto", "SFT -> KTO")]
    for i, (key, label) in enumerate(labels):
        y = legend_y + i * 28
        elements.append(f'<circle cx="{legend_x + 8}" cy="{y}" r="7" fill="{COLORS[key]}" stroke="#202020"/>')
        elements.append(_svg_text(legend_x + 24, y + 4, label, 12, "start"))
    _write_svg(path, width, height, elements)


def write_stated_confidence_figure(path: Path, confidence_rows: list[dict[str, object]]) -> None:
    width, height = 860, 520
    left, top, plot_w, plot_h = 95, 70, 570, 340
    arms = ["merged SFT", "SFT -> DPO", "SFT -> KTO"]
    colors = {
        "merged SFT": COLORS["sft_merged"],
        "SFT -> DPO": COLORS["dpo"],
        "SFT -> KTO": COLORS["kto"],
    }
    metrics = [
        ("refusal_recall_pct", "Refusal recall"),
        ("over_refusal_pct", "Over-refusal"),
        ("correct_on_known_pct", "Correct known"),
        ("mean_stated_confidence", "Mean confidence"),
    ]
    by_arm = {str(row["arm"]): row for row in confidence_rows}
    elements = [
        _svg_text(width / 2, 34, "Stated-confidence profile", 20),
        _svg_text(width / 2, 492, "Metric", 14),
        f'<text x="24" y="{top + plot_h / 2:.1f}" transform="rotate(-90 24 {top + plot_h / 2:.1f})" '
        'font-family="Arial, sans-serif" font-size="14" text-anchor="middle" fill="#202020">Rate (%) or confidence x100</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#fafafa" stroke="#202020"/>',
    ]
    for tick in range(0, 101, 20):
        y = top + plot_h - tick / 100 * plot_h
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#dddddd"/>')
        elements.append(_svg_text(left - 18, y + 4, str(tick), 11, "end"))
    group_w = plot_w / len(metrics)
    bar_w = 26
    for g, (metric, label) in enumerate(metrics):
        center = left + group_w * (g + 0.5)
        elements.append(_svg_text(center, top + plot_h + 28, label, 11))
        for i, arm in enumerate(arms):
            raw = float(by_arm[arm][metric])
            val = raw * 100 if metric == "mean_stated_confidence" else raw
            x = center + (i - 1) * (bar_w + 8) - bar_w / 2
            y = top + plot_h - val / 100 * plot_h
            h = val / 100 * plot_h
            elements.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" fill="{colors[arm]}"/>')
            label_text = f"{raw:.2f}" if metric == "mean_stated_confidence" else f"{raw:.0f}"
            elements.append(_svg_text(x + bar_w / 2, y - 6, label_text, 10))
    legend_x, legend_y = 690, 110
    for i, arm in enumerate(arms):
        y = legend_y + i * 30
        elements.append(f'<rect x="{legend_x}" y="{y - 10}" width="18" height="18" fill="{colors[arm]}"/>')
        elements.append(_svg_text(legend_x + 28, y + 4, arm, 12, "start"))
    elements.append(_svg_text(legend_x, legend_y + 116, "Coverage is ~100% for all arms", 12, "start"))
    _write_svg(path, width, height, elements)


def write_figures(
    figures_dir: Path,
    seed_rows: list[SeedMetricRow],
    summary_rows: list[dict[str, object]],
    transition_rows: list[dict[str, object]],
    amendment_rows: list[dict[str, object]],
    confidence_rows: list[dict[str, object]],
    alignment_rows: list[dict[str, object]],
) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    write_tradeoff_figure(figures_dir / "fig-p1-01-cold-start-tradeoff.svg", seed_rows)
    write_metric_bar_figure(figures_dir / "fig-p1-02-selfaware-metrics.svg", summary_rows)
    write_transition_figure(figures_dir / "fig-p1-03-paired-transitions.svg", transition_rows)
    write_amendment_tradeoff_figure(figures_dir / "fig-p1-04-sft-warmed-tradeoff.svg", amendment_rows)
    write_stated_confidence_figure(figures_dir / "fig-p1-05-stated-confidence.svg", confidence_rows)
    write_tradeoff_png(figures_dir / "fig-p1-01-cold-start-tradeoff.png", seed_rows)
    write_metric_bar_png(figures_dir / "fig-p1-02-selfaware-metrics.png", summary_rows)
    write_transition_png(figures_dir / "fig-p1-03-paired-transitions.png", transition_rows)
    write_amendment_tradeoff_png(figures_dir / "fig-p1-04-sft-warmed-tradeoff.png", amendment_rows)
    write_stated_confidence_png(figures_dir / "fig-p1-05-stated-confidence.png", confidence_rows)
    write_confidence_alignment_png(figures_dir / "fig-p1-06-confidence-alignment.png", alignment_rows)


def write_report(
    out_path: Path,
    seed_rows: list[SeedMetricRow],
    summary_rows: list[dict[str, object]],
    transition_rows: list[dict[str, object]],
    amendment_rows: list[dict[str, object]],
    confidence_rows: list[dict[str, object]],
    alignment_rows: list[dict[str, object]],
) -> None:
    seed_dicts = [row.__dict__ for row in seed_rows]
    sft_over = mean([row.over_refusal_pct for row in seed_rows if row.arm == "sft"])
    dpo_over = mean([row.over_refusal_pct for row in seed_rows if row.arm == "dpo"])
    kto_over = mean([row.over_refusal_pct for row in seed_rows if row.arm == "kto"])
    lines = [
        "# Paper 2 Reproducible Results Analysis",
        "",
        "Generated by `papers/paper-2-training-regimen/scripts/build_figures.py` from local locked training-regimen eval artifacts.",
        "",
        "## SelfAware Three-Seed Local 4B Metrics",
        "",
        *_markdown_table(
            seed_dicts,
            [
                "arm",
                "seed",
                "truthful_pct",
                "refusal_recall_pct",
                "over_refusal_pct",
                "correct_on_known_pct",
                "answer_on_unknown_pct",
                "config_sha",
            ],
        ),
        "",
        "## Across-Seed Summary",
        "",
        "Intervals are t-based 95% intervals over three seed-level point estimates (df=2).",
        "",
        *_markdown_table(
            summary_rows,
            ["arm", "metric", "mean", "sd", "ci95_low", "ci95_high", "n_seeds"],
        ),
        "",
        "For rate metrics, manuscript tables should use the bounded interval columns in",
        "`selfaware_seed_summary.csv`; the unbounded values above are retained to make",
        "the t-interval calculation transparent.",
        "",
        "## Cold-Start Over-Refusal Reduction Relative to SFT",
        "",
        f"- DPO mean over-refusal: {dpo_over:.2f}% vs SFT {sft_over:.2f}% "
        f"({(sft_over - dpo_over) / sft_over * 100:.1f}% lower).",
        f"- KTO mean over-refusal: {kto_over:.2f}% vs SFT {sft_over:.2f}% "
        f"({(sft_over - kto_over) / sft_over * 100:.1f}% lower).",
        "- This is not a success claim by itself because both cold-start preference arms also have near-zero refusal recall on unknown rows.",
        "",
        "## Paired Row Transitions",
        "",
        "Rows are aligned by `(eval_set, row_index)` in each seed's `scored_rows.jsonl`.",
        "",
        *_markdown_table(
            transition_rows,
            [
                "seed",
                "pair",
                "n_rows",
                "truthful_a_not_b",
                "truthful_b_not_a",
                "unknown_a_refused_b_answered",
                "unknown_b_refused_a_answered",
                "known_a_refused_b_answered",
                "known_b_refused_a_answered",
                "known_a_refused_b_correct",
                "known_a_correct_b_bad",
                "known_b_correct_a_bad",
                "truthful_mcnemar_p",
                "unknown_refusal_mcnemar_p",
                "known_refusal_mcnemar_p",
                "known_correct_mcnemar_p",
            ],
        ),
        "",
        "## SFT-Warmed SelfAware Metrics",
        "",
        *_markdown_table(
            amendment_rows,
            [
                "source",
                "arm",
                "truthful_pct",
                "refusal_recall_pct",
                "over_refusal_pct",
                "correct_on_known_pct",
                "config_sha",
            ],
        ),
        "",
        "## Stated-Confidence SelfAware Metrics",
        "",
        *_markdown_table(
            confidence_rows,
            [
                "arm",
                "n_seeds",
                "refusal_recall_pct",
                "over_refusal_pct",
                "correct_on_known_pct",
                "truthful_pct",
                "confidence_coverage_pct",
                "mean_stated_confidence",
                "mae_vs_known_label",
                "brier_vs_known_label",
                "mae_vs_answer_correctness",
                "brier_vs_answer_correctness",
                "source_metrics",
            ],
        ),
        "",
        "## Confidence Alignment By Outcome",
        "",
        *_markdown_table(
            alignment_rows,
            [
                "arm",
                "bucket_label",
                "n",
                "mean_stated_confidence",
                "brier_vs_answer_reality",
                "brier_vs_known_label",
                "high_conf_pct",
            ],
        ),
        "",
        "## Provenance Caveats",
        "",
        "- These outputs summarize local SelfAware artifacts available in this workspace.",
        "- v0.3 headline claims still need the protocol-defined scope decision for domains, 8B confirm, bridge, and robustness panels.",
        "- SFT-warmed rows are reported as secondary operating-point evidence rather than substituted for the cold-start comparison.",
        "- Stated-confidence summaries are parsed from answer/confidence contract metrics files.",
        "",
        "## Generated Figures",
        "",
        "- `papers/paper-2-training-regimen/figures/fig-p1-01-cold-start-tradeoff.svg`",
        "- `papers/paper-2-training-regimen/figures/fig-p1-02-selfaware-metrics.svg`",
        "- `papers/paper-2-training-regimen/figures/fig-p1-03-paired-transitions.svg`",
        "- `papers/paper-2-training-regimen/figures/fig-p1-04-sft-warmed-tradeoff.svg`",
        "- `papers/paper-2-training-regimen/figures/fig-p1-05-stated-confidence.svg`",
        "- `papers/paper-2-training-regimen/figures/fig-p1-06-confidence-alignment.png`",
        "",
    ]
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES)
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_rows = load_selfaware_seed_metrics()
    summary_rows = seed_summary(seed_rows)
    transition_rows = paired_transitions()
    amendment_rows = amendment_a_summary()
    confidence_rows = amendment_b_stated_confidence_summary()
    alignment_rows = amendment_b_confidence_alignment()

    _write_csv(out_dir / "selfaware_seed_metrics.csv", [row.__dict__ for row in seed_rows])
    _write_csv(out_dir / "selfaware_seed_summary.csv", summary_rows)
    _write_csv(out_dir / "selfaware_paired_transitions.csv", transition_rows)
    _write_csv(out_dir / "amendment_a_selfaware_summary.csv", amendment_rows)
    _write_csv(out_dir / "amendment_b_stated_confidence_summary.csv", confidence_rows)
    _write_csv(out_dir / "amendment_b_confidence_alignment_by_outcome.csv", alignment_rows)
    write_figures(args.figures_dir, seed_rows, summary_rows, transition_rows, amendment_rows, confidence_rows, alignment_rows)
    write_report(
        out_dir / "paper1_results_analysis.md",
        seed_rows,
        summary_rows,
        transition_rows,
        amendment_rows,
        confidence_rows,
        alignment_rows,
    )
    print(f"Wrote Paper 2 analysis outputs to {out_dir}")
    print(f"Wrote Paper 2 figures to {args.figures_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
