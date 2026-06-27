#!/usr/bin/env python3
"""Build a cross-dataset transfer panel from a known/unknown question source (GPU-free).

Step 1 of the cross-dataset-transfer protocol (see the mech-interp-runner skill).
Given a JSONL of questions carrying an intrinsic known/unknown label (e.g. KUQ,
SelfAware), emit the two frozen artifacts the rest of the pipeline consumes:

- ``gen_rows.jsonl`` — rows for the baseline generation pass
  (``phase3_head_intervention_runner`` at alpha=0): one record per question with
  ``probe_pool_row_key``, ``label``, ``question``, ``aliases``.
- ``manifest.json`` — a ``phase3-selfaware-frozen-row-manifest/v1`` manifest the
  hidden-state extractor consumes via ``selection.source: selfaware_manifest``.
  (The manifest format is dataset-agnostic despite the historical name.)

Both reference the SAME ``row_key`` per question so generation behavior and
extracted activations join downstream. Balanced subsampling is seeded and
deterministic. No GPU, no model load.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "phase3-selfaware-frozen-row-manifest/v1"


class PanelBuildError(RuntimeError):
    pass


def _coerce_aliases(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(v) for v in value if isinstance(v, (str, int, float)) and str(v).strip()]
    return []


def load_source(source: Path, *, question_field: str, unknown_field: str,
                answer_field: str) -> list[dict[str, Any]]:
    """Read the source JSONL into {question, label, aliases} records."""
    if not source.is_file():
        raise PanelBuildError(f"source not found: {source}")
    out: list[dict[str, Any]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        q = r.get(question_field)
        if not isinstance(q, str) or not q.strip():
            continue
        label = "unknown" if bool(r.get(unknown_field)) else "known"
        out.append({"question": q.strip(), "label": label,
                    "aliases": _coerce_aliases(r.get(answer_field))})
    if not out:
        raise PanelBuildError(f"no usable rows in {source} (question_field={question_field!r})")
    return out


def balanced_subsample(rows: list[dict[str, Any]], *, n_known: int, n_unknown: int,
                       seed: int) -> list[dict[str, Any]]:
    known = [r for r in rows if r["label"] == "known"]
    unknown = [r for r in rows if r["label"] == "unknown"]
    rng = random.Random(seed)
    rng.shuffle(known)
    rng.shuffle(unknown)
    if n_known > len(known):
        raise PanelBuildError(f"requested {n_known} known but only {len(known)} available")
    if n_unknown > len(unknown):
        raise PanelBuildError(f"requested {n_unknown} unknown but only {len(unknown)} available")
    picked = known[:n_known] + unknown[:n_unknown]
    rng.shuffle(picked)  # interleave so resume/order is not label-blocked
    return picked


def build_artifacts(rows: list[dict[str, Any]], *, dataset: str,
                    source_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    gen_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for i, r in enumerate(rows):
        row_key = f"{dataset}::{dataset}::{i:06d}::{dataset}-{i + 1}"
        gen_rows.append({
            "probe_pool_row_key": row_key,
            "label": r["label"],
            "question": r["question"],
            "aliases": r["aliases"],
        })
        manifest_rows.append({
            "row_key": row_key,
            "stable_identity": {"dataset": dataset, "index": i, "source": source_name},
            "strata": [f"{dataset}_{r['label']}"],
            "label": r["label"],
            "question": r["question"],
            "prompt": r["question"],
            "aliases": r["aliases"],
        })
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": None,  # stamped by caller if needed; kept null for determinism
        "dataset": dataset,
        "row_count": len(manifest_rows),
        "scope": {
            "phase": "phase3",
            "source": source_name,
            "no_gpu": True,
            "no_docker": True,
            "not_probe_pool_runner_ready": True,
            "intended_next_step": "cross-dataset hidden-state extraction using these frozen rows",
        },
        "identity": {
            "required_identity_fields": ["dataset", "index", "source"],
            "row_key_format": f"{dataset}::{dataset}::<index6>::{dataset}-<n>",
        },
        "required_arms": [],
        "strata": _strata_index(manifest_rows),
        "rows": manifest_rows,
    }
    return gen_rows, manifest


def _strata_index(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    idx: dict[str, list[str]] = {}
    for r in manifest_rows:
        for s in r["strata"]:
            idx.setdefault(s, []).append(r["row_key"])
    return {s: {"count": len(keys), "row_keys": keys} for s, keys in idx.items()}


def run(source: Path, out_dir: Path, *, dataset: str, n_known: int, n_unknown: int,
        seed: int, question_field: str = "question", unknown_field: str = "unknown",
        answer_field: str = "answer") -> dict[str, Any]:
    rows = load_source(source, question_field=question_field, unknown_field=unknown_field,
                       answer_field=answer_field)
    picked = balanced_subsample(rows, n_known=n_known, n_unknown=n_unknown, seed=seed)
    gen_rows, manifest = build_artifacts(picked, dataset=dataset, source_name=source.name)

    out_dir.mkdir(parents=True, exist_ok=True)
    gen_path = out_dir / "gen_rows.jsonl"
    manifest_path = out_dir / "manifest.json"
    gen_path.write_text("".join(json.dumps(r) + "\n" for r in gen_rows), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    meta = {
        "ok": True,
        "dataset": dataset,
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()[:16],
        "seed": seed,
        "n_known": n_known,
        "n_unknown": n_unknown,
        "row_count": len(gen_rows),
        "gen_rows": str(gen_path),
        "manifest": str(manifest_path),
    }
    (out_dir / "panel_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", required=True, type=Path, help="known/unknown JSONL")
    p.add_argument("--dataset", required=True, help="short dataset id (row_key prefix), e.g. kuq")
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--n-known", type=int, required=True)
    p.add_argument("--n-unknown", type=int, required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--question-field", default="question")
    p.add_argument("--unknown-field", default="unknown")
    p.add_argument("--answer-field", default="answer")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    meta = run(args.source, args.out_dir, dataset=args.dataset, n_known=args.n_known,
               n_unknown=args.n_unknown, seed=args.seed, question_field=args.question_field,
               unknown_field=args.unknown_field, answer_field=args.answer_field)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
