#!/usr/bin/env python3
"""Create a small balanced GRPO JSONL subset from a projected dataset."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def build_subset(
    input_path: Path,
    output_path: Path,
    per_label: int,
    labels: list[str] | None = None,
) -> dict[str, int]:
    wanted_labels = [str(label).lower() for label in (labels or ["known", "unknown"])]
    buckets: dict[str, list[dict]] = defaultdict(list)
    with input_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            label = str(row.get("label", "")).lower()
            if label in wanted_labels and len(buckets[label]) < per_label:
                buckets[label].append(row)
            if all(len(buckets[label]) >= per_label for label in wanted_labels):
                break

    missing = [label for label in wanted_labels if len(buckets[label]) < per_label]
    if missing:
        raise ValueError(f"not enough rows for labels: {missing}")

    rows = []
    for idx in range(per_label):
        for label in wanted_labels:
            rows.append(buckets[label][idx])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {**{label: per_label for label in wanted_labels}, "total": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--per-label", type=int, default=16)
    parser.add_argument(
        "--labels",
        default="known,unknown",
        help="Comma-separated labels to interleave into the smoke subset.",
    )
    args = parser.parse_args(argv)

    labels = [label.strip() for label in args.labels.split(",") if label.strip()]
    counts = build_subset(args.input, args.output, args.per_label, labels)
    label_summary = " / ".join(f"{counts[label]} {label}" for label in labels)
    print(f"Wrote {counts['total']} rows to {args.output} ({label_summary})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
