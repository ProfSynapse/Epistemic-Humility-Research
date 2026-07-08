#!/usr/bin/env python3
"""Audit token-bundle choices against the tokenizer and committed H1 readout."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml
from transformers import AutoTokenizer


HERE = Path(__file__).resolve().parent
DEFAULT_BUNDLE = HERE / "token_bundle.yaml"
DEFAULT_H1 = (
    HERE.parent
    / "j-space-localization-qwen3-4b"
    / "analysis-committed"
    / "results"
    / "jspace-jlens-r1"
    / "h1_full.json"
)


def iter_tokens(bundle: dict):
    primary = bundle["primary_bundle"]
    for polarity in ("positive_tokens", "negative_tokens"):
        for rec in primary.get(polarity, []):
            yield {
                "bundle": primary["name"],
                "polarity": polarity.removesuffix("_tokens"),
                **rec,
            }
    for probe in bundle.get("probe_bundles", []):
        for polarity in ("positive_tokens", "negative_tokens"):
            for rec in probe.get(polarity, []):
                yield {
                    "bundle": probe["name"],
                    "polarity": polarity.removesuffix("_tokens"),
                    **rec,
                }


def h1_lookup(h1: dict) -> dict[tuple[str, str, int], dict]:
    out: dict[tuple[str, str, int], dict] = {}
    for direction, direction_rec in h1["directions"].items():
        for layer, layer_rec in direction_rec["per_layer"].items():
            for rank, tok in enumerate(layer_rec["top_tokens"], start=1):
                out[(direction, layer, int(tok["token_id"]))] = {
                    "rank": rank,
                    "token": tok["token"],
                    "score": tok["score"],
                }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--h1", type=Path, default=DEFAULT_H1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    bundle = yaml.safe_load(args.bundle.read_text(encoding="utf-8"))
    h1 = json.loads(args.h1.read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(bundle["tokenizer_source"])
    lookup = h1_lookup(h1)

    audited = []
    for rec in iter_tokens(bundle):
        ids = tokenizer.encode(rec["text"], add_special_tokens=False)
        observed = []
        for direction in h1["directions"]:
            for layer in h1["directions"][direction]["per_layer"]:
                hit = lookup.get((direction, layer, int(rec["token_id"])))
                if hit:
                    observed.append({"direction": direction, "layer": layer, **hit})
        audited.append(
            {
                **rec,
                "tokenizer_ids": ids,
                "single_token": len(ids) == 1,
                "id_matches_tokenizer": ids == [int(rec["token_id"])],
                "observed_in_h1_top15": observed,
            }
        )

    summary = {
        "schema": "jspace-token-bundle-audit/v1",
        "bundle": str(args.bundle),
        "h1": str(args.h1),
        "model": bundle["model"],
        "n_tokens": len(audited),
        "all_single_token": all(x["single_token"] for x in audited),
        "all_ids_match_tokenizer": all(x["id_matches_tokenizer"] for x in audited),
        "tokens": audited,
    }

    text = json.dumps(summary, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if summary["all_single_token"] and summary["all_ids_match_tokenizer"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
