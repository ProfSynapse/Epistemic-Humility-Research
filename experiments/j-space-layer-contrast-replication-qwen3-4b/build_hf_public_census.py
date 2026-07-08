#!/usr/bin/env python3
"""Build a public-safe HF dataset directory from the J-space census manifest.

Input is the text-free public manifest produced by `mine_fresh_eval_pool.py
--manifest-only`. Output contains no question text, aliases, prompt text, or
generation text. It is intended for a public Hugging Face dataset release after
the exhaustive census completes.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MANIFEST = HERE / "analysis-committed" / "fresh_eval_pool_manifest.json"
DEFAULT_OUT = HERE / "analysis" / "hf_public_census"
DEFAULT_REPO_ID = "professorsynapse/eh-jspace-fresh-pool-census-qwen3-4b"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "generated_rows" not in data:
        raise SystemExit(
            "manifest is missing generated_rows; rebuild it with "
            "`mine_fresh_eval_pool.py --scan-all-candidates --manifest-only`"
        )
    return data


def readme_text(manifest: dict, repo_id: str) -> str:
    counts = manifest.get("counts", {})
    policy = manifest.get("public_manifest_policy", "")
    return f"""---
license: other
task_categories:
- text-classification
language:
- en
pretty_name: J-space Fresh-Pool Census Qwen3-4B
size_categories:
- 10K<n<100K
tags:
- epistemic-humility
- mechanistic-interpretability
- abstention
- qwen3
---

# J-space Fresh-Pool Census Qwen3-4B

This dataset is a public-safe row index and behavior-flag census for the
Epistemic Humility Research J-space layer-site replication.

It intentionally contains no question text, gold aliases, prompt text, model
generation text, hidden states, or row-level intervention outputs. It contains
only row identifiers, source/provenance fields, gold labels, selected behavioral
roles, and text-free baseline generation flags.

HF repo: `{repo_id}`

## Provenance

- Experiment: `experiments/j-space-layer-contrast-replication-qwen3-4b`
- Stage: `{manifest.get("stage")}`
- Model: `{manifest.get("model_name")}`
- Substrate: `{manifest.get("substrate")}`
- Candidate source: `{manifest.get("candidate_source")}`
- Predecessor split excluded: `{manifest.get("predecessor_split_excluded")}`
- Scan all candidates: `{manifest.get("scan_all_candidates")}`

## Counts

- Generated total: {counts.get("generated_total")}
- Generated unknown: {counts.get("generated_unknown")}
- Generated known: {counts.get("generated_known")}
- Selected confab: {counts.get("selected_confab")}
- Selected known_correct_answered: {counts.get("selected_known_correct_answered")}

## Files

- `generated_rows.jsonl`: one text-free row per generated candidate.
- `selected_rows.jsonl`: row IDs selected for the replication evaluation pool.
- `manifest.json`: full public manifest copied from the repo-side build.

## Schema

`generated_rows.jsonl` fields:

- `row_key`: project-stable row identifier.
- `gold_label`: `unknown` or `known`.
- `role`: `confab`, `known_correct_answered`, or null.
- `source`: source dataset family.
- `category_canon`: source/category metadata.
- `answered`, `refused`, `degenerate`, `correct`, `well_formed_correct`:
  text-free baseline generation flags from the local grader.
- `prompt_len`, `n_new_tokens`, `terminated_naturally`: text-free generation
  metadata.

`selected_rows.jsonl` fields:

- `row_key`
- `role`
- `source`
- `category_canon`

## Release Boundary

{policy}

Raw question text and aliases are deliberately excluded because source-level
redistribution is audited separately. Rebuild from upstream sources inside the
Epistemic Humility Research repo if text is needed for a licensed local run.
"""


def run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    out_dir = Path(args.out_dir).resolve()
    manifest = read_manifest(manifest_path)

    if out_dir.exists() and args.clean:
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_rows = manifest["generated_rows"]
    selected_rows = manifest.get("rows", [])
    write_jsonl(out_dir / "generated_rows.jsonl", generated_rows)
    write_jsonl(out_dir / "selected_rows.jsonl", selected_rows)
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(
        readme_text(manifest, args.repo_id),
        encoding="utf-8",
    )
    print(f"[hf-census] wrote {out_dir}")
    print(f"[hf-census] generated_rows={len(generated_rows)} selected_rows={len(selected_rows)}")
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID)
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
