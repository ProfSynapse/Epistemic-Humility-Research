#!/usr/bin/env python3
"""Tests for the Amendment M Revision 3 probe-FACTUAL SFT target.

R3 retargets the cell (after the R1/R2 quantile preflight showed appropriateness_p
is near-degenerate on clean-SFT data) onto the calibrated factual/doubt axis
DIRECTLY: response_confidence = factual_p (Laplace 32-sample P-correct), with NO
balancing and NO abstention inversion. The load-bearing properties (Amendment M
§3.1a / §4):

  1. identity:        target == clamp(factual_p)  (calibrated by construction;
                      Spearman vs factual_p = 1.0)
  2. polarity:        abstentions / wrong answers get LOW targets, knowns-correct
                      get HIGH targets (the opposite of R1/R2 appropriateness for
                      abstentions; the polarity the threshold bridge needs)
  3. bimodal NOT balanced: both modes populated with a middle tail; the uniform-
                      balance gate is explicitly retired
  4. behavior-ident.: answer text + prompt are byte-identical to clean SFT; only the
                      response_confidence number differs.
"""

from pathlib import Path
import json
import sys

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import build_schema_response_confidence_datasets as builder  # noqa: E402


def _payload(content: str) -> dict:
    return json.loads(content)


def _conf(row: dict) -> float:
    return _payload(row["messages"][-1]["content"])["response_confidence"]


def _row(question: str, answer: str) -> dict:
    return {
        "conversations": [
            {"role": "system", "content": "old"},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


def _probe(key: str, k_correct: int, n: int = 32, label: str = "known") -> dict:
    return {
        "probe_pool_row_key": key,
        "label": label,
        "p_correct": k_correct / n,
        "n_samples": n,
        "sampled_correct": [True] * k_correct + [False] * (n - k_correct),
    }


def _laplace(k: int, n: int = 32) -> float:
    return (k + 1.0) / (n + 2.0)


# --- 1. identity: target == clamp(factual_p) ------------------------------------

def test_target_equals_factual_p():
    rows, probes = [], []
    for i, k in enumerate([0, 4, 8, 12, 16, 20, 24, 28, 32]):
        rows.append(_row(f"Q{i}?", f"A{i}."))
        probes.append(_probe(f"k{i}", k))
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    lo, hi = builder.PROBE_FACTUAL_CLAMP
    for r, k in zip(out, [0, 4, 8, 12, 16, 20, 24, 28, 32]):
        expected = round(min(hi, max(lo, _laplace(k))), 4)
        assert _conf(r) == expected, (k, _conf(r), expected)
        assert r["factual_p"] is not None


def test_target_is_monotone_in_factual_p():
    rows, probes = [], []
    for i, k in enumerate([0, 4, 8, 12, 16, 20, 24, 28, 32]):
        rows.append(_row(f"Q{i}?", f"A{i}."))
        probes.append(_probe(f"k{i}", k))
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    confs = [_conf(r) for r in out]
    assert confs == sorted(confs), confs


# --- 2. polarity: NO abstention inversion ---------------------------------------

def test_abstention_gets_low_target_no_inversion():
    # An abstention on a clear unknown (low factual_p) must get a LOW target.
    # R1/R2 inverted this (1 - factual_p -> HIGH); R3 must NOT.
    rows = [_row("Unknown?", "I don't know the answer."), _row("Known?", "Paris.")]
    probes = [_probe("u", 0, label="unknown"), _probe("k", 30)]
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    by_key = {r["probe_pool_row_key"]: r for r in out}
    assert _conf(by_key["u"]) < 0.1, _conf(by_key["u"])   # abstention -> LOW
    assert _conf(by_key["k"]) > 0.8, _conf(by_key["k"])   # confident known -> HIGH


def test_known_wrong_gets_low_target():
    # A gold-answer row the probe says is usually WRONG must get a LOW target
    # (this is what the threshold bridge converts to an abstention at inference).
    rows = [_row("HardKnown?", "SomeAnswer.")]
    probes = [_probe("h", 1)]  # factual_p ~ 0.06
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    assert _conf(out[0]) < 0.1, _conf(out[0])


# --- 3. bimodal-with-tail, NOT balanced -----------------------------------------

def test_distribution_is_bimodal_not_balanced():
    # 40 confident knowns (32/32) + 40 clear unknowns (0/32) + a few middle.
    rows, probes = [], []
    for i in range(40):
        rows.append(_row(f"K{i}?", f"A{i}.")); probes.append(_probe(f"k{i}", 32))
    for i in range(40):
        rows.append(_row(f"U{i}?", "I don't know the answer.")); probes.append(_probe(f"u{i}", 0, label="unknown"))
    for i in range(10):
        rows.append(_row(f"M{i}?", f"M{i}.")); probes.append(_probe(f"m{i}", 16))
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    confs = [_conf(r) for r in out]
    low = sum(1 for c in confs if c <= 0.2)
    mid = sum(1 for c in confs if 0.2 < c < 0.8)
    high = sum(1 for c in confs if c >= 0.8)
    # both modes populated AND a middle tail present (the §004 collapse cannot occur)
    assert low >= 30 and high >= 30 and mid >= 5, (low, mid, high)


# --- 4. behavior-identity to clean SFT ------------------------------------------

def test_behavior_identical_to_clean_sft_only_confidence_differs():
    rows = [_row("Q1?", "Paris."), _row("Q2?", "I don't know the answer."), _row("Q3?", "Rome.")]
    probes = [_probe("a", 30), _probe("b", 1, label="unknown"), _probe("c", 18)]
    clean = builder.build_clean_sft_rows(rows, probe_records=probes)
    factual = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    assert len(clean) == len(factual)
    for c, d in zip(clean, factual):
        assert c["messages"][:-1] == d["messages"][:-1]  # prompt byte-identical
        cp, dp = _payload(c["messages"][-1]["content"]), _payload(d["messages"][-1]["content"])
        assert cp["answer"] == dp["answer"]              # answer text byte-identical
        assert set(cp) == set(dp) == {"answer", "response_confidence"}


# --- determinism + provenance + fallback ----------------------------------------

def test_deterministic_across_runs():
    rows = [_row(f"Q{i}?", f"A{i}.") for i in range(30)]
    probes = [_probe(f"k{i}", (i * 7) % 33) for i in range(30)]
    a = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    b = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    assert [_conf(r) for r in a] == [_conf(r) for r in b]


def test_missing_probe_gets_global_mean_fallback():
    # one row has no probe -> falls back to the mean factual_p of the rows that do.
    rows = [_row("Q?", "A."), _row("Q2?", "B."), _row("Q3?", "C.")]
    probes = [None, _probe("k", 32), _probe("j", 0)]
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    assert out[0]["response_confidence_source"] == "constant_fallback"
    assert out[0]["factual_p"] is None
    mean = (_laplace(32) + _laplace(0)) / 2
    lo, hi = builder.PROBE_FACTUAL_CLAMP
    assert _conf(out[0]) == round(min(hi, max(lo, round(mean, 6))), 4)


def test_formula_label_recorded():
    rows = [_row("Q?", "A.")]
    probes = [_probe("k", 20)]
    out = builder.build_probe_factual_sft_rows(rows, probe_records=probes)
    assert out[0]["response_confidence_formula"] == builder.PROBE_FACTUAL_FORMULA
    assert out[0]["response_confidence_role"] == "factual"
    assert out[0]["schema_target"] == "response_confidence_json"
