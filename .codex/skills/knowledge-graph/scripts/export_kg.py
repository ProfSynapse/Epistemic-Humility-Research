#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from kg_common import NoteIndex, collect_graph_notes, collect_triples, load_ontology


CSV_FIELDS = [
    "source_path",
    "source",
    "source_id",
    "source_type",
    "edge_type",
    "target",
    "target_id",
    "target_path",
    "confidence",
    "status",
    "start",
    "end",
    "evidence",
    "legacy",
]


def write_csv(rows: list[dict[str, object]], output: str) -> None:
    handle = open(output, "w", newline="", encoding="utf-8") if output else sys.stdout
    try:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            clean = dict(row)
            clean["evidence"] = "; ".join(str(item) for item in row.get("evidence") or [])
            writer.writerow(clean)
    finally:
        if output:
            handle.close()


def write_json(rows: list[dict[str, object]], output: str) -> None:
    text = json.dumps(rows, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def write_jsonl(rows: list[dict[str, object]], output: str) -> None:
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    text = "\n".join(lines) + ("\n" if lines else "")
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Obsidian knowledge graph relationships as triples.")
    parser.add_argument("paths", nargs="*", help="Markdown files or folders. Defaults to the vault root.")
    parser.add_argument("--root", default=".", help="Vault root. Defaults to current directory.")
    parser.add_argument("--ontology", default="", help="Path to edge ontology YAML.")
    parser.add_argument("--format", choices=["csv", "json", "jsonl"], default="csv")
    parser.add_argument("--output", default="", help="Output path. Defaults to stdout.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ontology = load_ontology(Path(args.ontology).resolve()) if args.ontology else load_ontology()
    index = NoteIndex.build(root)
    notes, findings = collect_graph_notes([Path(path) for path in args.paths], root=root)
    if any(finding.severity == "ERROR" for finding in findings):
        for finding in findings:
            print(f"{finding.severity} {finding.code} {finding.path}: {finding.message}", file=sys.stderr)
        return 1

    rows = [triple.as_dict() for triple in collect_triples(notes, ontology, index=index)]
    if args.format == "csv":
        write_csv(rows, args.output)
    elif args.format == "json":
        write_json(rows, args.output)
    else:
        write_jsonl(rows, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
