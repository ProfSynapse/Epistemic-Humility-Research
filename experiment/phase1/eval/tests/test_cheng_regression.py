#!/usr/bin/env python3
"""experiment/phase1/eval/tests/test_cheng_regression.py

KEYSTONE regression test (WS-4). Asserts the ported scorers reproduce Cheng's
published over-refusal numbers (Idk-SFT 42.71%, Idk-DPO 23.27%, n=11,313) and
the full per-method reanalysis row set, computed against the ON-DISK Cheng
outputs with the bridge-arm labeling (known/unknown inferred from the IDK
training target via is_refusal).

If this fails, a scoring PIPELINE bug is indicted, not the metric: the source
reanalysis already produced these numbers from the same inputs, so the only new
variable is the port. Ground truth = meta-analysis/evidence/idk-method-reanalysis.csv
(read-only), produced by meta-analysis/analysis/reanalyze_idk_outputs.py.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scorers import (  # noqa: E402  (sys.path set in conftest.py)
    load_gold,
    metrics_from_quadrants,
    score_quadrants,
)

# Real on-disk locations (NOT the stale docs/epistemic-humility/ paths the
# read-only source hardcodes; those predate the repo split).
REPO = Path(__file__).resolve().parents[4]
CHENG_OUTPUTS = REPO / "datasets" / "say-i-dont-know-outputs"
GOLD = REPO / "datasets" / "triviaqa-rc-nocontext" / "cheng_test_gold.jsonl"
EVIDENCE_CSV = REPO / "meta-analysis" / "evidence" / "idk-method-reanalysis.csv"

METHODS = ["sft", "dpo", "ppo", "bon", "hir"]

# The columns the port computes that the evidence CSV also carries.
COMPARED_COLUMNS = [
    "n",
    "n_unknown_labeled",
    "n_known_labeled",
    "refusal_recall_pct",
    "answer_on_unknown_pct",
    "over_refusal_pct",
    "refusal_rate_pct",
    "correct_on_known_pct",
    "correct_on_unknown_pct",
    "truthful_pct",
]


def _load_expected() -> dict[str, dict[str, float]]:
    """method -> {column: expected value} from the read-only evidence CSV."""
    expected: dict[str, dict[str, float]] = {}
    with EVIDENCE_CSV.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            method = row["method"].replace("idk-", "")
            expected[method] = {
                col: float(row[col]) for col in COMPARED_COLUMNS
            }
    return expected


@pytest.fixture(scope="module")
def gold() -> dict[str, list[str]]:
    if not GOLD.exists():
        pytest.skip(f"Cheng gold not on disk: {GOLD}")
    return load_gold(GOLD)


@pytest.fixture(scope="module")
def expected() -> dict[str, dict[str, float]]:
    if not EVIDENCE_CSV.exists():
        pytest.skip(f"evidence CSV not on disk: {EVIDENCE_CSV}")
    return _load_expected()


def _score_method(method: str, gold: dict[str, list[str]]) -> dict[str, float]:
    path = CHENG_OUTPUTS / f"triviaqa_test_llama2_7b_chat_idk_{method}.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    counts = score_quadrants(
        records,
        gold,
        label_from_target=True,  # bridge-arm: label from IDK target
        target_key="answer",
        generation_key="generated_answer",
        question_key="question",
    )
    return metrics_from_quadrants(counts)


@pytest.mark.parametrize("method", METHODS)
def test_port_reproduces_all_columns(method, gold, expected):
    """Every reanalysis column reproduces exactly for every method."""
    path = CHENG_OUTPUTS / f"triviaqa_test_llama2_7b_chat_idk_{method}.json"
    if not path.exists():
        pytest.skip(f"Cheng output not on disk: {path}")
    got = _score_method(method, gold)
    for col in COMPARED_COLUMNS:
        assert got[col] == pytest.approx(expected[method][col], abs=1e-9), (
            f"{method}.{col}: port={got[col]} expected={expected[method][col]}"
        )


def test_headline_over_refusal_numbers(gold, expected):
    """The two numbers in the paper abstract, asserted explicitly."""
    sft_path = CHENG_OUTPUTS / "triviaqa_test_llama2_7b_chat_idk_sft.json"
    dpo_path = CHENG_OUTPUTS / "triviaqa_test_llama2_7b_chat_idk_dpo.json"
    if not (sft_path.exists() and dpo_path.exists()):
        pytest.skip("Cheng SFT/DPO outputs not on disk")
    sft = _score_method("sft", gold)
    dpo = _score_method("dpo", gold)
    assert sft["over_refusal_pct"] == 42.71
    assert dpo["over_refusal_pct"] == 23.27
    assert sft["n"] == 11313
    assert dpo["n"] == 11313
