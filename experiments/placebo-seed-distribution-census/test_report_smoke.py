"""CPU smoke for report.py's build_report/build_family_report on synthetic
fixtures -- proves the report-assembly code path (paired_delta -> criterion
-> per-family verdict -> committed aggregate JSON) runs end-to-end without
any real generation/grading data. Run via
`python3 -m pytest test_report_smoke.py -v` (explicit file path)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import config  # noqa: E402
import report  # noqa: E402


def _synthetic_rows_for_family(family: str, s_row_keys: list[str], seeds: list[int], dosed_bias: float) -> list[dict]:
    """Baseline: fixed low refusal rate. Dosed: refusal rate shifted by
    dosed_bias so every seed shares the same sign (used to exercise the
    SURVIVES path deterministically for the committed-sign families)."""
    rows = []
    for i, rk in enumerate(s_row_keys):
        rows.append({"cell": family, "arm": "baseline", "row_key": rk, "seed": None, "refused_final": (i % 10 == 0)})
    for seed in seeds:
        for i, rk in enumerate(s_row_keys):
            base_refused = i % 10 == 0
            flip_frac = abs(dosed_bias)
            flip = (i % 100) < int(flip_frac * 100)
            refused = (not base_refused) if (flip and dosed_bias > 0) else base_refused
            if dosed_bias < 0:
                refused = False if flip else base_refused
            rows.append({"cell": family, "arm": "random_direction", "row_key": rk, "seed": seed, "refused_final": refused})
    return rows


def test_build_report_end_to_end_on_synthetic_fixtures():
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(40)] for fam in config.FAMILIES}
    subsample_manifest = {"seed": config.SUBSAMPLE_PERMUTATION_SEED, "families": {fam: {"row_keys": s_row_keys[fam]} for fam in config.FAMILIES}}

    applied_rows = []
    applied_rows += _synthetic_rows_for_family("qwen35_4b", s_row_keys["qwen35_4b"], config.SEED_BLOCKS["qwen35_4b"], dosed_bias=-0.5)
    applied_rows += _synthetic_rows_for_family("mistral7b_v03", s_row_keys["mistral7b_v03"], config.SEED_BLOCKS["mistral7b_v03"], dosed_bias=0.5)
    applied_rows += _synthetic_rows_for_family("llama32_3b", s_row_keys["llama32_3b"], config.SEED_BLOCKS["llama32_3b"], dosed_bias=0.0)

    out = report.build_report(applied_rows, subsample_manifest)

    assert set(out["families"].keys()) == set(config.FAMILIES)
    for fam in config.FAMILIES:
        fr = out["families"][fam]
        assert fr["complete"] is True
        assert fr["n_seeds_present"] == config.K_SEEDS_PER_FAMILY
        assert fr["criterion"]["verdict"] in (
            "SURVIVES", "RETIRED", "INDETERMINATE",
            "NEAR_ZERO_NULL_HOLDS", "NEWLY_DISCOVERED_POSITIVE_SIGN", "NEWLY_DISCOVERED_NEGATIVE_SIGN",
            "INDETERMINATE_NULL_CONTROL",
        )
    assert out["families"]["llama32_3b"]["criterion"]["committed_sign"] == "none"
    assert out["families"]["qwen35_4b"]["criterion"]["committed_sign"] == "negative"
    assert out["families"]["mistral7b_v03"]["criterion"]["committed_sign"] == "positive"


def test_build_report_marks_incomplete_when_fewer_than_k_seeds_present():
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(20)] for fam in config.FAMILIES}
    subsample_manifest = {"seed": 1, "families": {fam: {"row_keys": s_row_keys[fam]} for fam in config.FAMILIES}}
    partial_seeds = config.SEED_BLOCKS["qwen35_4b"][:3]
    applied_rows = _synthetic_rows_for_family("qwen35_4b", s_row_keys["qwen35_4b"], partial_seeds, dosed_bias=-0.5)
    out = report.build_report(applied_rows, {"seed": 1, "families": {"qwen35_4b": {"row_keys": s_row_keys["qwen35_4b"]}, "mistral7b_v03": {"row_keys": []}, "llama32_3b": {"row_keys": []}}})
    fr = out["families"]["qwen35_4b"]
    assert fr["n_seeds_present"] == 3
    assert fr["complete"] is False


def test_report_writes_no_row_level_text_only_aggregates(tmp_path):
    s_row_keys = {fam: [f"{fam}_row{i}" for i in range(20)] for fam in config.FAMILIES}
    subsample_manifest = {"seed": 1, "families": {fam: {"row_keys": s_row_keys[fam]} for fam in config.FAMILIES}}
    applied_rows = []
    for fam in config.FAMILIES:
        applied_rows += _synthetic_rows_for_family(fam, s_row_keys[fam], config.SEED_BLOCKS[fam][:2], dosed_bias=0.3)
    out = report.build_report(applied_rows, subsample_manifest)
    import json

    blob = json.dumps(out)
    # containment: aggregate-only report must never carry answer/question text
    assert "answer_text" not in blob
    assert "question" not in blob
