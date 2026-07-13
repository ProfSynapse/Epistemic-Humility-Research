#!/usr/bin/env python3
"""Materialize thinking-on Amendment B eval configs.

The thinking comparison configs are derived from the existing non-thinking
stated-confidence SelfAware configs. This keeps the comparison surface tight:
same prompt contract, same arms, same bootstrap, same eval set, separate
results directories, and only `generation.enable_thinking` flipped.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


EVAL_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = EVAL_DIR / "config"

SOURCE_CONFIGS = (
    "eval_amendment_b_stated_confidence_neutral_selfaware_seed1_base_smoke_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seed1_all_arms_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seed2_all_arms_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seed3_all_arms_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed1_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed2_sft_merged_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed2_sft_dpo_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed2_sft_kto_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed3_sft_merged_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed3_sft_dpo_local_4b.yaml",
    "eval_amendment_b_stated_confidence_selfaware_seq_seed3_sft_kto_local_4b.yaml",
)


def thinking_config_name(source_name: str) -> str:
    suffix = "_local_4b.yaml"
    if not source_name.endswith(suffix):
        raise ValueError(f"source config does not end with {suffix!r}: {source_name}")
    return f"{source_name.removesuffix(suffix)}_thinking_local_4b.yaml"


def materialize_one(source_path: Path, *, overwrite: bool = False) -> Path:
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    generation = payload.setdefault("generation", {})
    if generation.get("enable_thinking") is not False:
        raise ValueError(f"source must have generation.enable_thinking=false: {source_path}")

    original_results_dir = payload["results_dir"]
    payload["results_dir"] = f"{original_results_dir}_thinking_on"
    generation["enable_thinking"] = True

    provenance = payload.setdefault("derived_from", {})
    provenance["config"] = source_path.name
    provenance["comparison_condition"] = "thinking_on"

    output_path = source_path.with_name(thinking_config_name(source_path.name))
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing config: {output_path}")
    output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return output_path


def materialize_all(*, overwrite: bool = False) -> list[Path]:
    return [
        materialize_one(CONFIG_DIR / source_name, overwrite=overwrite)
        for source_name in SOURCE_CONFIGS
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize thinking-on variants of Amendment B eval configs."
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    written = materialize_all(overwrite=args.overwrite)
    for path in written:
        print(path.relative_to(EVAL_DIR.parents[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
