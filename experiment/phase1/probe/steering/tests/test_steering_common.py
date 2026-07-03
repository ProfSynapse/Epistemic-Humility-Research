"""Unit tests for steering_common.py (Amendment AA shared harness plumbing).

CPU-only, synthetic fixtures — no model downloads, no GPU. Covers:
  - degenerate-output detection (the amendment's coherence floor)
  - grading (abstention / correctness / revised flag)
  - pool-file loading + eval-pool construction
  - metric functions + condition summaries
  - paired bootstrap CI shape, determinism, and alignment guards
  - GenerationHookController pass/call gating (torch)
  - cell-JSON writing + header payload
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from steering_common import (
    COHERENCE_FLOOR,
    GenerationHookController,
    adequacy_check,
    base_cell_payload,
    build_eval_pool,
    compare_conditions,
    compute_revised,
    grade_output,
    is_degenerate,
    load_pool_file,
    make_flat_record,
    metric_abstention_unknown,
    metric_accuracy_answerable,
    metric_answer_rate_known,
    metric_degenerate_rate,
    metric_revision_discrimination,
    paired_bootstrap_diff_ci,
    parse_alpha_list,
    probe_score_from_hidden,
    summarize_condition,
    text_hash,
    write_cell_json,
)


# ---------------------------------------------------------------------------
# Degenerate-output detection
# ---------------------------------------------------------------------------

class TestIsDegenerate:
    def test_empty_is_degenerate(self):
        assert is_degenerate("")
        assert is_degenerate("   \n\t  ")

    def test_no_alphanumeric_is_degenerate(self):
        assert is_degenerate("!!! ??? --- ***")

    def test_repeated_unigram_is_degenerate(self):
        assert is_degenerate("the the the the the the")

    def test_repeated_bigram_is_degenerate(self):
        assert is_degenerate("very good very good very good")

    def test_repeated_ngram_with_partial_tail_is_degenerate(self):
        assert is_degenerate("go on go on go on go")

    def test_normal_answer_not_degenerate(self):
        assert not is_degenerate("The capital of France is Paris.")

    def test_abstention_not_degenerate(self):
        assert not is_degenerate("I don't know the answer to that question.")

    def test_two_repeats_not_degenerate(self):
        # fewer than 3 repetitions is not the repeated-n-gram pathology
        assert not is_degenerate("hello world hello world")


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------

class TestGradeOutput:
    def test_abstention_detected(self):
        g = grade_output("I don't know the answer to that.", [])
        assert g["abstained"] and not g["answered"] and not g["degenerate"]
        assert g["correct"] is None

    def test_correct_answer(self):
        g = grade_output("The capital is Paris, of course.", ["paris"])
        assert g["answered"] and g["correct"] is True

    def test_wrong_answer(self):
        g = grade_output("The capital is Lyon.", ["paris"])
        assert g["answered"] and g["correct"] is False

    def test_no_aliases_gives_none_correct(self):
        g = grade_output("Some confident answer.", [])
        assert g["answered"] and g["correct"] is None

    def test_degenerate_neither_abstains_nor_answers(self):
        g = grade_output("", ["paris"])
        assert g["degenerate"] and not g["abstained"] and not g["answered"]
        assert g["correct"] is None


class TestComputeRevised:
    """Answer-level (grade-transition) contract — the post-AB instrument.

    Text is never compared: the old normalized-full-text fallback saturated
    under sampled decode (revised was True on 100% of records)."""

    def _grades(self, initial, final, aliases=()):
        return grade_output(initial, list(aliases)), grade_output(final, list(aliases))

    def test_same_text_not_revised(self):
        gi, gf = self._grades("Paris.", "Paris.")
        assert compute_revised("Paris.", "Paris.", gi, gf) is False

    def test_case_and_punctuation_change_not_revised(self):
        gi, gf = self._grades("Paris.", "paris")
        assert compute_revised("Paris.", "paris", gi, gf) is False

    def test_sampled_decode_paraphrase_same_grade_not_revised(self):
        # THE saturation regression: temp>0 rewords everything; same graded
        # answer must NOT count as a revision.
        a, b = "The capital of France is Paris.", "Paris is France's capital."
        gi, gf = self._grades(a, b, aliases=("paris",))
        assert gi["correct"] and gf["correct"]
        assert compute_revised(a, b, gi, gf) is False

    def test_correctness_flip_is_revised(self):
        gi, gf = self._grades("Lyon.", "Paris.", aliases=("paris",))
        assert compute_revised("Lyon.", "Paris.", gi, gf) is True
        gi, gf = self._grades("Paris.", "Lyon.", aliases=("paris",))
        assert compute_revised("Paris.", "Lyon.", gi, gf) is True

    def test_final_abstention_after_answer_is_revised(self):
        gi, gf = self._grades("Lyon.", "I don't know.")
        assert compute_revised("Lyon.", "I don't know.", gi, gf) is True

    def test_answer_after_abstention_is_revised(self):
        gi, gf = self._grades("I don't know.", "Paris.")
        assert compute_revised("I don't know.", "Paris.", gi, gf) is True

    def test_wrong_to_different_wrong_undetectable(self):
        # Documented limitation: no answer extraction, so a different wrong
        # answer is invisible (both grade correct=False).
        gi, gf = self._grades("Lyon.", "Marseille.", aliases=("paris",))
        assert compute_revised("Lyon.", "Marseille.", gi, gf) is False

    def test_ungraded_text_change_not_revised(self):
        # No gold aliases (gate rows): only abstention flips are detectable.
        gi, gf = self._grades("Lyon.", "Paris.")
        assert compute_revised("Lyon.", "Paris.", gi, gf) is False


# ---------------------------------------------------------------------------
# Alpha parsing + probe scoring
# ---------------------------------------------------------------------------

class TestParseAlphaList:
    def test_parses_signed_floats(self):
        assert parse_alpha_list("-4,-2,-1,0,+1,2,4") == [-4, -2, -1, 0, 1, 2, 4]

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_alpha_list(",")


class TestProbeScoreFromHidden:
    def test_zero_dot_gives_half(self):
        h = np.zeros(8)
        d = np.ones(8) / math.sqrt(8)
        assert abs(probe_score_from_hidden(h, d) - 0.5) < 1e-9

    def test_monotonic_in_projection(self):
        d = np.zeros(4)
        d[0] = 1.0
        lo = probe_score_from_hidden(np.array([-2.0, 0, 0, 0]), d)
        hi = probe_score_from_hidden(np.array([+2.0, 0, 0, 0]), d)
        assert lo < 0.5 < hi


# ---------------------------------------------------------------------------
# Pool loading
# ---------------------------------------------------------------------------

class TestPoolLoading:
    def test_load_pool_file(self, synthetic_gate_pool_file):
        items = load_pool_file(synthetic_gate_pool_file)
        assert len(items) == 24
        assert all("aliases_norm" in it for it in items)

    def test_missing_key_raises(self, tmp_path):
        p = tmp_path / "bad.jsonl"
        p.write_text(json.dumps({"row_key": "x", "question": "q"}) + "\n")
        with pytest.raises(ValueError, match="source"):
            load_pool_file(p)

    def test_bad_source_raises(self, tmp_path):
        p = tmp_path / "bad2.jsonl"
        p.write_text(json.dumps(
            {"row_key": "x", "question": "q", "source": "mystery"}) + "\n")
        with pytest.raises(ValueError, match="bad source"):
            load_pool_file(p)

    def test_gate_pool_counts(self, synthetic_gate_pool_file):
        pool = build_eval_pool("gate", n_unknown=5, n_known=7, n_answerable=0,
                               seed=7, pool_file=synthetic_gate_pool_file)
        assert sum(1 for it in pool if it["source"] == "selfaware_unknown") == 5
        assert sum(1 for it in pool if it["source"] == "selfaware_known") == 7
        assert len(pool) == 12

    def test_dial_pool_counts(self, synthetic_dial_pool_file):
        pool = build_eval_pool("dial", n_unknown=0, n_known=0, n_answerable=9,
                               seed=7, pool_file=synthetic_dial_pool_file)
        assert len(pool) == 9
        assert all(it["source"] == "answerable" for it in pool)
        assert all(it["aliases_norm"] for it in pool)

    def test_too_few_items_raises(self, synthetic_gate_pool_file):
        with pytest.raises(ValueError, match="need"):
            build_eval_pool("gate", n_unknown=999, n_known=1, n_answerable=0,
                            seed=7, pool_file=synthetic_gate_pool_file)

    def test_shuffle_deterministic_under_seed(self, synthetic_gate_pool_file):
        p1 = build_eval_pool("gate", 6, 6, 0, seed=13,
                             pool_file=synthetic_gate_pool_file)
        p2 = build_eval_pool("gate", 6, 6, 0, seed=13,
                             pool_file=synthetic_gate_pool_file)
        assert [it["row_key"] for it in p1] == [it["row_key"] for it in p2]


# ---------------------------------------------------------------------------
# Flat records, metrics, summaries
# ---------------------------------------------------------------------------

def _rec(row_key: str, source: str, initial: str, final: str, aliases=()):
    item = {"row_key": row_key, "source": source,
            "aliases_norm": list(aliases), "question": "q?"}
    return make_flat_record(item, initial, final)


def _gate_records(n_abstain: int, n_answer: int, prefix: str = "u"):
    """Unknown-source records: n_abstain final abstentions + n_answer answers."""
    recs = []
    for i in range(n_abstain):
        recs.append(_rec(f"{prefix}{i:03d}", "selfaware_unknown",
                         "Some guess.", "I don't know the answer."))
    for i in range(n_abstain, n_abstain + n_answer):
        recs.append(_rec(f"{prefix}{i:03d}", "selfaware_unknown",
                         "Some guess.", "A confident final guess."))
    return recs


class TestMetrics:
    def test_abstention_unknown(self):
        recs = _gate_records(n_abstain=3, n_answer=1)
        assert metric_abstention_unknown(recs) == pytest.approx(0.75)

    def test_abstention_unknown_none_without_unknown_rows(self):
        recs = [_rec("k0", "selfaware_known", "A.", "A.")]
        assert metric_abstention_unknown(recs) is None

    def test_answer_rate_known(self):
        recs = [
            _rec("k0", "selfaware_known", "A.", "Answer stays."),
            _rec("k1", "selfaware_known", "A.", "I don't know."),
        ]
        assert metric_answer_rate_known(recs) == pytest.approx(0.5)

    def test_accuracy_answerable(self):
        recs = [
            _rec("a0", "answerable", "It is Paris.", "It is Paris.", ["paris"]),
            _rec("a1", "answerable", "It is Lyon.", "It is Lyon.", ["paris"]),
        ]
        assert metric_accuracy_answerable(recs) == pytest.approx(0.5)

    def test_revision_discrimination(self):
        # 2 initial-wrong: 1 revises; 2 initial-correct: 0 revise -> 0.5 - 0.0
        recs = [
            _rec("a0", "answerable", "It is Lyon.", "Actually it is Paris.", ["paris"]),
            _rec("a1", "answerable", "It is Lyon.", "It is Lyon.", ["paris"]),
            _rec("a2", "answerable", "It is Paris.", "It is Paris.", ["paris"]),
            _rec("a3", "answerable", "It is Paris.", "It is Paris.", ["paris"]),
        ]
        assert metric_revision_discrimination(recs) == pytest.approx(0.5)

    def test_revision_discrimination_undefined_without_both_classes(self):
        recs = [
            _rec("a0", "answerable", "It is Paris.", "It is Paris.", ["paris"]),
        ]
        assert metric_revision_discrimination(recs) is None

    def test_degenerate_rate_and_exclusion(self):
        recs = _gate_records(n_abstain=2, n_answer=1)
        recs.append(_rec("u999", "selfaware_unknown", "Guess.", ""))  # degenerate
        assert metric_degenerate_rate(recs) == pytest.approx(0.25)
        # degenerate-final record excluded from the abstention denominator
        assert metric_abstention_unknown(recs) == pytest.approx(2 / 3)


class TestSummarizeCondition:
    def test_summary_fields_and_floor(self):
        recs = _gate_records(n_abstain=4, n_answer=4)
        s = summarize_condition(recs)
        assert s["n_items"] == 8
        assert s["abstention_unknown"] == pytest.approx(0.5)
        assert s["degenerate_rate"] == 0.0
        assert s["coherence_floor_ok"] is True

    def test_floor_violation_flagged(self):
        recs = _gate_records(n_abstain=1, n_answer=1)
        recs.append(_rec("u9", "selfaware_unknown", "Guess.", ""))
        s = summarize_condition(recs)
        assert s["degenerate_rate"] > COHERENCE_FLOOR
        assert s["coherence_floor_ok"] is False


class TestAdequacyCheck:
    def test_counts_and_floors(self):
        recs = [
            _rec(f"a{i}", "answerable", "It is Lyon.", "It is Lyon.", ["paris"])
            for i in range(45)
        ] + [
            _rec(f"b{i}", "answerable", "It is Paris.", "It is Paris.", ["paris"])
            for i in range(41)
        ]
        ad = adequacy_check(recs)
        assert ad["n_initial_wrong"] == 45
        assert ad["n_initial_correct"] == 41
        assert ad["dial_adequate_ge_40_40"] is True
        assert ad["gate_adequate_ge_100_unknown_answered"] is False


# ---------------------------------------------------------------------------
# Paired bootstrap
# ---------------------------------------------------------------------------

class TestPairedBootstrap:
    def test_ci_shape_and_direction(self):
        a = _gate_records(n_abstain=16, n_answer=4)     # 0.80
        b = _gate_records(n_abstain=4, n_answer=16)     # 0.20
        ci = paired_bootstrap_diff_ci(metric_abstention_unknown, a, b,
                                      n_boot=500, seed=1)
        assert set(ci) == {"delta", "ci_lo", "ci_hi", "n_boot", "ci_excludes_zero"}
        assert ci["delta"] == pytest.approx(0.6)
        assert ci["ci_lo"] <= ci["delta"] <= ci["ci_hi"]
        assert ci["ci_excludes_zero"] is True
        assert ci["n_boot"] <= 500

    def test_deterministic_under_seed(self):
        a = _gate_records(10, 10)
        b = _gate_records(6, 14)
        c1 = paired_bootstrap_diff_ci(metric_abstention_unknown, a, b, 300, seed=9)
        c2 = paired_bootstrap_diff_ci(metric_abstention_unknown, a, b, 300, seed=9)
        assert c1 == c2

    def test_unequal_lengths_raise(self):
        a = _gate_records(2, 2)
        with pytest.raises(ValueError, match="equal-length"):
            paired_bootstrap_diff_ci(metric_abstention_unknown, a, a[:-1], 10, 0)

    def test_misaligned_row_keys_raise(self):
        a = _gate_records(2, 2)
        b = list(reversed(_gate_records(2, 2)))
        with pytest.raises(ValueError, match="row_key-aligned"):
            paired_bootstrap_diff_ci(metric_abstention_unknown, a, b, 10, 0)

    def test_undefined_stat_returns_none(self):
        a = [_rec("k0", "selfaware_known", "A.", "A.")]
        assert paired_bootstrap_diff_ci(metric_abstention_unknown, a, a, 10, 0) is None

    def test_compare_conditions_keys(self):
        a = _gate_records(16, 4)
        b = _gate_records(4, 16)
        out = compare_conditions(a, b, n_boot=200, seed=3)
        assert "abstention_unknown" in out
        assert "degenerate_rate" not in out  # floor is per-condition, no contrast


# ---------------------------------------------------------------------------
# GenerationHookController (torch)
# ---------------------------------------------------------------------------

torch = pytest.importorskip("torch", reason="torch required for controller tests")


def _make_controller(hidden_dim: int = 8, alpha: float = 2.0):
    from confidence_steer import SteeringHook
    d = torch.zeros(hidden_dim)
    d[0] = 1.0
    hook = SteeringHook(d=d, alpha=0.0, position="anchor")
    return GenerationHookController(hook), alpha, hidden_dim


def _call(controller, seq_len: int, hidden_dim: int):
    x = torch.zeros(1, seq_len, hidden_dim)
    out = controller(None, None, (x.clone(),))
    return x, out[0].detach()


class TestGenerationHookController:
    def test_anchor_steers_prefill_last_token_only(self):
        controller, alpha, hd = _make_controller()
        controller.begin_pass("anchor", alpha)
        x, y = _call(controller, seq_len=6, hidden_dim=hd)  # prefill
        assert y[0, -1, 0].item() == pytest.approx(alpha)
        assert y[0, :-1, :].abs().max().item() == 0.0
        # decode steps (seq_len == 1) must NOT be steered in anchor mode
        _, y2 = _call(controller, seq_len=1, hidden_dim=hd)
        assert y2.abs().max().item() == 0.0

    def test_gen_stream_skips_prefill_steers_decode_steps(self):
        controller, alpha, hd = _make_controller()
        controller.begin_pass("gen_stream", alpha)
        _, y1 = _call(controller, seq_len=6, hidden_dim=hd)  # prefill: untouched
        assert y1.abs().max().item() == 0.0
        _, y2 = _call(controller, seq_len=1, hidden_dim=hd)  # decode step
        assert y2[0, 0, 0].item() == pytest.approx(alpha)
        _, y3 = _call(controller, seq_len=1, hidden_dim=hd)
        assert y3[0, 0, 0].item() == pytest.approx(alpha)

    def test_off_mode_never_steers(self):
        controller, alpha, hd = _make_controller()
        controller.begin_pass("off", alpha)
        for seq in (6, 1, 1):
            _, y = _call(controller, seq_len=seq, hidden_dim=hd)
            assert y.abs().max().item() == 0.0

    def test_zero_alpha_never_steers_even_in_anchor_mode(self):
        controller, _, hd = _make_controller()
        controller.begin_pass("anchor", 0.0)
        _, y = _call(controller, seq_len=6, hidden_dim=hd)
        assert y.abs().max().item() == 0.0

    def test_begin_pass_resets_call_counter(self):
        controller, alpha, hd = _make_controller()
        controller.begin_pass("anchor", alpha)
        _call(controller, 6, hd)
        _call(controller, 1, hd)
        controller.begin_pass("anchor", alpha)  # new pass: prefill again
        _, y = _call(controller, seq_len=4, hidden_dim=hd)
        assert y[0, -1, 0].item() == pytest.approx(alpha)

    def test_invalid_mode_raises(self):
        controller, _, _ = _make_controller()
        with pytest.raises(ValueError, match="mode"):
            controller.begin_pass("sideways", 1.0)

    def test_pass_log_records_provenance(self):
        controller, alpha, _ = _make_controller()
        controller.begin_pass("anchor", alpha)
        controller.begin_pass("off", 0.0)
        assert controller.pass_log == [
            {"mode": "anchor", "alpha": alpha},
            {"mode": "off", "alpha": 0.0},
        ]


# ---------------------------------------------------------------------------
# Cell JSON output
# ---------------------------------------------------------------------------

class TestCellJson:
    def test_write_creates_parents_and_roundtrips(self, tmp_path):
        out = tmp_path / "results" / "nested" / "cell.json"
        payload = {"amendment": "AA", "items": [1, 2, 3]}
        path = write_cell_json(out, payload)
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8")) == payload

    def test_base_cell_payload_header(self):
        meta = {"signal": "gate", "best_layer": 3, "auroc_at_best_layer": 0.99,
                "provenance": {"model_tag": "synthetic-tiny"}}
        hdr = base_cell_payload(
            arm="A", cell="AA-1", signal="gate", position="anchor",
            model="synthetic/tiny", direction_meta=meta, eval_pool="gate",
            seed=7, n_items=12, config_extra={"alpha_values": [0, 1]})
        for key in ("amendment", "arm", "cell", "signal", "position", "model",
                    "eval_pool", "seed", "n_items", "coherence_floor",
                    "revision_instruction", "created_utc", "direction",
                    "config", "config_sha"):
            assert key in hdr, f"header missing {key}"
        assert hdr["amendment"] == "AA"
        assert hdr["direction"]["best_layer"] == 3

    def test_text_hash_stable(self):
        assert text_hash("abc") == text_hash("abc")
        assert text_hash("abc") != text_hash("abd")
        assert len(text_hash("abc")) == 16
