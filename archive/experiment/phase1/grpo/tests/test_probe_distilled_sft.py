#!/usr/bin/env python3
"""Tests for the Amendment M probe-distilled (quantile-balanced) SFT target.

The cell installs stated-confidence DISCRIMINATION by distilling the internal
appropriateness_p into the response_confidence scalar through a monotone, marginal-
balanced quantile transform — while keeping the behavior completions byte-identical
to clean SFT. The three load-bearing properties (Amendment M §3.1/§4):

  1. monotone:        appropriateness_p_i < _j  =>  confidence_i <= confidence_j
  2. balanced:        no quantized target exceeds 15% of rows (defeats §004 collapse,
                      which was 81.79% on the naive 0.1+0.8*p target)
  3. behavior-ident.: answer text + prompt are identical to clean SFT; only the
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


# --- 1. monotone in appropriateness_p -------------------------------------------

def test_target_is_monotone_in_appropriateness_p():
    # graded knowns: more correct samples -> higher factual_p -> higher appropriateness
    rows, probes = [], []
    for i, k in enumerate([0, 4, 8, 12, 16, 20, 24, 28, 32]):
        rows.append(_row(f"Q{i}?", f"A{i}."))
        probes.append(_probe(f"k{i}", k))
    out = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    ap = [r["appropriateness_p"] for r in out]
    conf = [_conf(r) for r in out]
    paired = sorted(zip(ap, conf), key=lambda t: t[0])
    confs_in_ap_order = [c for _, c in paired]
    assert confs_in_ap_order == sorted(confs_in_ap_order), confs_in_ap_order


def test_refusal_inverts_appropriateness():
    # an abstention on a clear unknown is APPROPRIATE -> high appropriateness_p
    rows = [_row("Unknown?", "I don't know the answer."), _row("Known?", "Paris.")]
    probes = [_probe("u", 0, label="unknown"), _probe("k", 30)]
    out = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    by_key = {r["probe_pool_row_key"]: r for r in out}
    # unknown-abstention: appropriateness = 1 - factual_p (factual_p low) -> high
    assert by_key["u"]["appropriateness_p"] > 0.9
    # known-answer: appropriateness = factual_p -> high too, but both are "appropriate"
    assert by_key["k"]["appropriateness_p"] > 0.8


# --- 2. balanced marginal (defeats the §004 point-mass collapse) ----------------

def test_balance_holds_against_a_heavy_point_mass():
    # 100 easy knowns all at the SAME factual_p (32/32) -> one appropriateness value.
    # Average-rank would map them all to ONE target (relocating the §004 mode);
    # deterministic tie-breaking must spread them across the band instead.
    rows, probes = [], []
    for i in range(100):
        rows.append(_row(f"Q{i}?", f"A{i}."))
        probes.append(_probe(f"k{i}", 32))
    out = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    confs = [_conf(r) for r in out]
    counts: dict[float, int] = {}
    for c in confs:
        counts[c] = counts.get(c, 0) + 1
    max_share = max(counts.values()) / len(confs)
    assert max_share <= builder.PROBE_DISTILLED_BALANCE_CAP, (max_share, counts)
    # and the spread genuinely uses the band, not a single mode
    assert min(confs) < 0.2 and max(confs) > 0.8


def test_targets_stay_inside_band_endpoints_avoided():
    rows = [_row(f"Q{i}?", f"A{i}.") for i in range(20)]
    probes = [_probe(f"k{i}", i + 1) for i in range(20)]
    out = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    lo, hi = builder.PROBE_DISTILLED_BAND
    for r in out:
        assert lo <= _conf(r) <= hi


# --- 3. behavior-identity to clean SFT ------------------------------------------

def test_behavior_identical_to_clean_sft_only_confidence_differs():
    rows = [_row("Q1?", "Paris."), _row("Q2?", "I don't know the answer."), _row("Q3?", "Rome.")]
    probes = [_probe("a", 30), _probe("b", 1, label="unknown"), _probe("c", 18)]
    clean = builder.build_clean_sft_rows(rows, probe_records=probes)
    distilled = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    assert len(clean) == len(distilled)
    for c, d in zip(clean, distilled):
        # prompt (everything but the assistant turn) is byte-identical
        assert c["messages"][:-1] == d["messages"][:-1]
        # the answer text is byte-identical; only response_confidence differs
        cp, dp = _payload(c["messages"][-1]["content"]), _payload(d["messages"][-1]["content"])
        assert cp["answer"] == dp["answer"]
        assert set(cp) == set(dp) == {"answer", "response_confidence"}


# --- determinism + provenance ---------------------------------------------------

def test_deterministic_across_runs():
    rows = [_row(f"Q{i}?", f"A{i}.") for i in range(30)]
    probes = [_probe(f"k{i}", (i * 7) % 33) for i in range(30)]
    a = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    b = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    assert [_conf(r) for r in a] == [_conf(r) for r in b]


def test_missing_probe_gets_constant_fallback_midpoint():
    rows = [_row("Q?", "A."), _row("Q2?", "B.")]
    probes = [None, _probe("k", 16)]
    out = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    lo, hi = builder.PROBE_DISTILLED_BAND
    assert out[0]["response_confidence_source"] == "constant_fallback"
    assert out[0]["appropriateness_p"] is None
    assert _conf(out[0]) == round(lo + (hi - lo) * 0.5, 4)


def test_formula_label_recorded():
    rows = [_row("Q?", "A.")]
    probes = [_probe("k", 20)]
    out = builder.build_probe_distilled_sft_rows(rows, probe_records=probes)
    assert out[0]["response_confidence_formula"] == builder.PROBE_DISTILLED_QUANTILE_FORMULA
    assert out[0]["schema_target"] == "response_confidence_json"
