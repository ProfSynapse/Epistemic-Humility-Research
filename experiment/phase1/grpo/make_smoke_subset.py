#!/usr/bin/env python3
"""Create a small balanced GRPO JSONL subset from a projected dataset."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def build_subset(input_path: Path, output_path: Path, per_label: int) -> dict[str, int]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    with input_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            label = str(row.get("label", "")).lower()
            if label in {"known", "unknown"} and len(buckets[label]) < per_label:
                buckets[label].append(row)
            if all(len(buckets[label]) >= per_label for label in ("known", "unknown")):
                break

    missing = [label for label in ("known", "unknown") if len(buckets[label]) < per_label]
    if missing:
        raise ValueError(f"not enough rows for labels: {missing}")

    rows = []
    for idx in range(per_label):
        rows.append(buckets["known"][idx])
        rows.append(buckets["unknown"][idx])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {"known": per_label, "unknown": per_label, "total": len(rows)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--per-label", type=int, default=16)
    args = parser.parse_args(argv)

    counts = build_subset(args.input, args.output, args.per_label)
    print(
        f"Wrote {counts['total']} rows to {args.output} "
        f"({counts['known']} known / {counts['unknown']} unknown)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
