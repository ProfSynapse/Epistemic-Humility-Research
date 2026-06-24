#!/usr/bin/env python3
"""Dump the current knowledge-graph atom/mechanism inventory as JSON.

Run from the repo root. The output feeds the ingestion workflow's Resolve stage
so that ingesting a new paper REUSES existing canonical atoms instead of minting
duplicates (the whole point of the incremental ingestion posture).

Usage:
    python .agents/skills/kg-ingest/scripts/kg_inventory.py > /tmp/kg_inventory.json
"""
import glob
import json
import os
import sys


def parse_frontmatter(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return {}
    body = text[3:end]
    meta = {}
    key = None
    for line in body.split("\n"):
        if not line.strip():
            continue
        if line[0] not in " \t" and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val and val not in ("[]", ""):
                # crude list parse for aliases on one line
                if val.startswith("[") and val.endswith("]"):
                    inner = val[1:-1]
                    meta[key] = [
                        x.strip().strip('"').strip("'")
                        for x in inner.split(",")
                        if x.strip()
                    ]
                else:
                    meta[key] = val.strip('"').strip("'")
            else:
                meta[key] = ""
    return meta


def collect(kind_dirs):
    out = []
    for d in kind_dirs:
        for p in sorted(glob.glob(f"library/concepts/{d}/*.md")):
            meta = parse_frontmatter(p)
            stem = os.path.basename(p)[:-3]
            aliases = meta.get("aliases", [])
            if isinstance(aliases, str):
                aliases = [aliases] if aliases else []
            out.append(
                {
                    "id": meta.get("id", stem),
                    "type": meta.get("type", d.rstrip("s")),
                    "aliases": aliases,
                }
            )
    return out


def main():
    atoms = collect(["methods", "metrics", "datasets", "models", "terms"])
    mechanisms = collect(["mechanisms"])
    papers = [os.path.basename(p)[:-3] for p in sorted(glob.glob("library/notes/*.md"))]
    json.dump(
        {"atoms": atoms, "mechanisms": mechanisms, "paper_stems": papers},
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
