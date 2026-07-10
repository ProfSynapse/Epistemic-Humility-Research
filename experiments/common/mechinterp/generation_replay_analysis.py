#!/usr/bin/env python3
"""Summarize Phase 3 generated-answer replay deltas.

The analysis compares intervention rows against matching no-vector baselines
within completed `generations.jsonl` files. It is intentionally conservative:
string matching is only a triage aid, and changed rows should still be manually
inspected before making behavior claims.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


REFUSAL_MARKERS = (
    "i don't know",
    "i do not know",
    "i'm not sure",
    "i am not sure",
    "not confident",
    "sorry",
    "beyond the scope",
    "can't answer",
    "cannot answer",
    "unknown",
    "no answer",
    "do not have",
    "don't have",
    "not able to",
    "unable to",
)


def normalize(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def is_refusal(text: str | None) -> bool:
    normalized = (text or "").strip().lower()
    return any(marker in normalized for marker in REFUSAL_MARKERS)


def is_correct(text: str | None, aliases: list[str]) -> bool:
    if is_refusal(text):
        return False
    normalized_text = normalize(text)
    if not normalized_text:
        return False
    for alias in aliases:
        normalized_alias = normalize(alias)
        if normalized_alias and (
            normalized_alias == normalized_text
            or normalized_alias in normalized_text
            or normalized_text in normalized_alias
        ):
            return True
    return False


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} is not valid JSON") from exc
    return rows


def load_run_candidate(path: Path) -> dict[str, Any]:
    manifest_path = path.with_name("run_manifest.json")
    if not manifest_path.exists():
        return {}
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    candidate = manifest.get("candidate", {})
    return candidate if isinstance(candidate, dict) else {}


def _run_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return sorted(root.glob("*/generation/run_*/generations.jsonl"))


def summarize_file(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = load_jsonl(path)
    run_candidate = load_run_candidate(path)
    source_direction_layer = run_candidate.get("source_direction_layer")
    multi_layer_components = run_candidate.get("multi_layer_components") or []
    source_layers = [
        component.get("layer")
        for component in multi_layer_components
        if isinstance(component, dict) and component.get("layer") is not None
    ]
    by_key: dict[tuple[str, float | None, str], dict[str, Any]] = {}
    for row in rows:
        by_key[(row["row_key"], row.get("grid_coefficient"), row["control"])] = row

    summaries: dict[tuple[str, str, float | None, int | None], dict[str, Any]] = {}
    changed_rows: list[dict[str, Any]] = []
    for (row_key, grid_coefficient, control), intervention in by_key.items():
        if control == "no_vector_baseline":
            continue
        baseline = by_key.get((row_key, grid_coefficient, "no_vector_baseline"))
        if baseline is None:
            continue
        candidate = intervention.get("candidate_label", "")
        layer = intervention.get("layer")
        key = (candidate, control, grid_coefficient, layer)
        summary = summaries.setdefault(
            key,
            {
                "candidate": candidate,
                "control": control,
                "grid_coefficient": grid_coefficient,
                "layer": layer,
                "applied_layer": layer,
                "source_direction_layer": source_direction_layer,
                "source_layers": source_layers or intervention.get("source_layers", []),
                "pair_count": 0,
                "known_rows": 0,
                "unknown_rows": 0,
                "changed_rows": 0,
                "known_repairs_truthful": 0,
                "known_truthful_worsened": 0,
                "known_wrong_new_answers": 0,
                "unknown_new_nonrefusal": 0,
                "baseline_known_answer_correct": 0,
                "baseline_known_answered": 0,
                "baseline_known_refused": 0,
                "baseline_unknown_refused": 0,
                "baseline_unknown_answered": 0,
                "known_answer_correct": 0,
                "known_answered": 0,
                "known_refused": 0,
                "unknown_refused": 0,
                "unknown_answered": 0,
            },
        )
        summary["pair_count"] += 1
        aliases = list(intervention.get("aliases") or [])
        baseline_answer = baseline.get("generated_answer") or ""
        intervention_answer = intervention.get("generated_answer") or ""
        baseline_refused = is_refusal(baseline_answer)
        intervention_refused = is_refusal(intervention_answer)
        baseline_correct = is_correct(baseline_answer, aliases)
        intervention_correct = is_correct(intervention_answer, aliases)
        text_changed = normalize(baseline_answer) != normalize(intervention_answer)
        label = intervention.get("label")

        if text_changed:
            summary["changed_rows"] += 1
        if label == "known":
            summary["known_rows"] += 1
            if baseline_refused:
                summary["baseline_known_refused"] += 1
            else:
                summary["baseline_known_answered"] += 1
            if baseline_correct:
                summary["baseline_known_answer_correct"] += 1
            if intervention_refused:
                summary["known_refused"] += 1
            else:
                summary["known_answered"] += 1
            if intervention_correct:
                summary["known_answer_correct"] += 1
            if baseline_refused and intervention_correct:
                summary["known_repairs_truthful"] += 1
            if baseline_correct and not intervention_correct:
                summary["known_truthful_worsened"] += 1
            if baseline_refused and not intervention_refused and not intervention_correct:
                summary["known_wrong_new_answers"] += 1
        elif label == "unknown":
            summary["unknown_rows"] += 1
            if baseline_refused:
                summary["baseline_unknown_refused"] += 1
            else:
                summary["baseline_unknown_answered"] += 1
            if intervention_refused:
                summary["unknown_refused"] += 1
            else:
                summary["unknown_answered"] += 1
            if baseline_refused and not intervention_refused:
                summary["unknown_new_nonrefusal"] += 1

        if text_changed or baseline_refused != intervention_refused or baseline_correct != intervention_correct:
            changed_rows.append(
                {
                    "candidate": candidate,
                    "control": control,
                    "grid_coefficient": grid_coefficient,
                    "layer": layer,
                    "row_key": row_key,
                    "label": label,
                    "baseline_refused": baseline_refused,
                    "intervention_refused": intervention_refused,
                    "baseline_correct": baseline_correct,
                    "intervention_correct": intervention_correct,
                    "baseline_answer": baseline_answer,
                    "intervention_answer": intervention_answer,
                    "aliases": "|".join(aliases),
                }
            )

    summary_rows = []
    for row in summaries.values():
        known_rows = row["known_rows"] or 1
        unknown_rows = row["unknown_rows"] or 1
        row["known_answer_correctness"] = round(100 * row["known_answer_correct"] / known_rows, 2)
        row["known_answer_rate"] = round(100 * row["known_answered"] / known_rows, 2)
        row["over_refusal_on_known"] = round(100 * row["known_refused"] / known_rows, 2)
        row["unknown_refusal_rate"] = round(100 * row["unknown_refused"] / unknown_rows, 2)
        row["answer_on_unknown_rate"] = round(100 * row["unknown_answered"] / unknown_rows, 2)
        row["baseline_known_answer_correctness"] = round(
            100 * row["baseline_known_answer_correct"] / known_rows, 2
        )
        row["baseline_known_answer_rate"] = round(100 * row["baseline_known_answered"] / known_rows, 2)
        row["baseline_over_refusal_on_known"] = round(100 * row["baseline_known_refused"] / known_rows, 2)
        row["baseline_unknown_refusal_rate"] = round(
            100 * row["baseline_unknown_refused"] / unknown_rows, 2
        )
        row["baseline_answer_on_unknown_rate"] = round(
            100 * row["baseline_unknown_answered"] / unknown_rows, 2
        )
        row["known_answer_correct_delta"] = row["known_answer_correct"] - row["baseline_known_answer_correct"]
        row["known_refusal_delta"] = row["known_refused"] - row["baseline_known_refused"]
        row["unknown_refusal_delta"] = row["unknown_refused"] - row["baseline_unknown_refused"]
        summary_rows.append(row)
    return summary_rows, changed_rows


def write_outputs(summary_rows: list[dict[str, Any]], changed_rows: list[dict[str, Any]], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    summary_rows = sorted(
        summary_rows,
        key=lambda row: (
            str(row.get("candidate", "")),
            str(row.get("control", "")),
            row.get("grid_coefficient") or 0,
            row.get("layer") or -1,
        ),
    )
    (out / "summary.json").write_text(
        json.dumps({"generation_replay_summary": summary_rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if summary_rows:
        with (out / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)
    if changed_rows:
        with (out / "changed_rows.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(changed_rows[0].keys()))
            writer.writeheader()
            writer.writerows(changed_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Sweep root or one generations.jsonl file")
    parser.add_argument("--out", required=True, type=Path, help="Output directory for summary artifacts")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary_rows: list[dict[str, Any]] = []
    changed_rows: list[dict[str, Any]] = []
    for path in _run_files(args.root):
        file_summary, file_changed = summarize_file(path)
        summary_rows.extend(file_summary)
        changed_rows.extend(file_changed)
    write_outputs(summary_rows, changed_rows, args.out)
    print(
        json.dumps(
            {
                "run_files": len(_run_files(args.root)),
                "summary_rows": len(summary_rows),
                "changed_rows": len(changed_rows),
                "out": str(args.out),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
