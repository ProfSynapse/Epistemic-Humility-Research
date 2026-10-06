"""Tests for the pre-registered recognition labeling rule.

Location: experiments/decision-model-idk-option/tests/test_recognition_rule.py
Run:      python -m pytest experiments/decision-model-idk-option/tests -q

Synthetic rows only; no PopQA text, no model.
"""

from __future__ import annotations

import ast
import sys
from math import comb
from pathlib import Path

import pytest

CELL = Path(__file__).resolve().parents[1]
REPO = CELL.parents[1]
sys.path.insert(0, str(CELL))

import idk_harness as H  # noqa: E402

C = H.cfg()
RC = C["recognition"]
GATES = H._yaml_load(CELL / "gates.yaml")


def _y_fewshot() -> tuple:
    """Amendment Y's frozen exemplars, read from source without importing it."""
    src = (REPO / "experiments/common/readouts/amendment_x_cross_model_extract.py").read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "_BASE_MODE_FEWSHOT":
            return ast.literal_eval(node.value)
    raise AssertionError("_BASE_MODE_FEWSHOT not found")


def test_exemplar_questions_and_answers_are_amendment_y_byte_identical():
    ours = tuple((e["question"], e["gold"]) for e in RC["prompt"]["exemplars"])
    assert ours == _y_fewshot()


def test_exemplars_have_four_distinct_options_containing_gold():
    for e in RC["prompt"]["exemplars"]:
        assert len(e["options"]) == 4 and len(set(e["options"])) == 4 and e["gold"] in e["options"]


def test_exemplar_gold_letters_are_registered_b_d_a_c_b():
    letters = RC["letters"]
    assert [letters[e["options"].index(e["gold"])] for e in RC["prompt"]["exemplars"]] == list("BDACB")


def test_prompt_shape_ends_at_answer_cue():
    p = H.build_mc_prompt("Who wrote Example?", ["w", "x", "y", "z"], RC)
    assert p.endswith("Q: Who wrote Example?\nA. w\nB. x\nC. y\nD. z\nA:")
    assert p.startswith("Q: What is the largest planet in our solar system?\nA. Saturn\nB. Jupiter\n")
    assert p.count("\nA: ") == 5 and "\nA: B\n\nQ: How many sides" in p
    assert "know" not in p  # recognition never shows the IDK option


def test_rotations_put_gold_at_every_letter_once():
    opts = ["g", "d1", "d2", "d3"]
    rots = H.rotations(opts, 0, 4)
    assert rots[0][0] == opts  # ordering 0 = canonical decision-row order
    assert sorted(g for _, g in rots) == [0, 1, 2, 3]
    for o, g in rots:
        assert o[g] == "g" and sorted(o) == sorted(opts)


@pytest.mark.parametrize("c,group", [(0, "unknown_true"), (1, "recognition_ambiguous"),
                                     (2, "recognition_ambiguous"), (3, "known_recognized"),
                                     (4, "known_recognized")])
def test_group_rule(c, group):
    assert H.recognition_group(c, 4, RC["group_rule"]) == group


def test_position_biased_responder_is_always_ambiguous():
    for gold in range(4):
        rots = H.rotations(["a", "b", "c", "d"], gold, 4)
        for fixed_letter in range(4):
            c = sum(int(fixed_letter == g) for _, g in rots)
            assert c == 1 and H.recognition_group(c, 4, RC["group_rule"]) == "recognition_ambiguous"


def test_chance_reference_matches_binomial():
    p = {k: comb(4, k) * 0.25 ** k * 0.75 ** (4 - k) for k in range(5)}
    ref = GATES["r0_chance_reference"]
    assert ref["p_c_ge_3"] == pytest.approx(p[3] + p[4])
    assert ref["p_c_eq_0"] == pytest.approx(p[0])
    assert ref["p_c_1_or_2"] == pytest.approx(p[1] + p[2])


def test_argmax_tie_goes_to_lowest_letter_and_is_flagged():
    assert H.letter_argmax([1.0, 3.0, 3.0, 0.0]) == (1, True)
    assert H.letter_argmax([1.0, 2.0, 3.0, 0.0]) == (2, False)


def test_normalizer_matches_eh_scorer():
    sys.path.insert(0, str(REPO / "experiments/common/knowledge_probe"))
    from scoring import normalize_answer

    for s in ["Mount Everest", "A.U.", "  Sao   Paulo ", "1945", "I don't know"]:
        assert H.normalize_answer(s) == normalize_answer(s)


def test_collision_rule_matches_alias_or_option_text_exactly():
    rows = [
        {"meta": {"qid": "q1"}, "options": [["Paris", ""], ["Lyon", ""], ["Nice", ""], ["Lille", ""]]},
        {"meta": {"qid": "q2"}, "options": [["Mars", ""], ["Saturn", ""], ["X", ""], ["Y", ""]]},   # option "Saturn"
        {"meta": {"qid": "q3"}, "options": [["Fe Records", ""], ["B", ""], ["C", ""], ["D", ""]]},  # superstring only
        {"meta": {"qid": "q4"}, "options": [["A1", ""], ["B1", ""], ["C1", ""], ["D1", ""]]},
    ]
    meta = {"q1": {"aliases": ["Paris"], "obj": "Paris"}, "q2": {"aliases": ["Mars"], "obj": "Mars"},
            "q3": {"aliases": ["Fe Records"], "obj": "Fe Records"},
            "q4": {"aliases": ["mount everest"], "obj": "A1"}}  # alias collides
    assert H.exemplar_option_collision_qids(rows, meta, RC) == ["q2", "q4"]


def test_registered_collision_count_is_zero():
    assert GATES["g0_exemplar_option_collision_exclusion"]["expected_count"] == 0


# ---- fp32 letter-logit scoring (PI decision 2026-10-06) -------------------


def test_cell_declares_fp32_letter_logits_with_tie_fallback():
    assert RC["letter_logit_precision"] == "fp32"
    assert RC["letter_logit_precision"] in H.LETTER_LOGIT_PRECISIONS
    assert RC["argmax_tie_rule"] == "lowest_letter_index"
    assert 0 < float(RC["letter_logit_fp32_vs_bf16_max_abs_diff"]) <= 1.0


def test_fp32_letter_logits_equal_an_fp32_matmul_of_bf16_inputs():
    torch = pytest.importorskip("torch")
    g = torch.Generator().manual_seed(0)
    h = torch.randn(64, generator=g).to(torch.bfloat16)
    w = torch.randn(4, 64, generator=g).to(torch.bfloat16)
    b = torch.randn(4, generator=g).to(torch.bfloat16)
    got = H.fp32_letter_logits(h, w, b)
    want = (w.double() @ h.double() + b.double()).tolist()
    assert all(abs(x - y) < 1e-4 for x, y in zip(got, want))
    assert got == H.fp32_letter_logits(h, w, b)  # deterministic
    assert H.fp32_letter_logits(h, w) == [float(x) for x in (w.float() @ h.float())]


def test_fp32_projection_breaks_a_tie_that_bf16_rounding_creates():
    torch = pytest.importorskip("torch")
    # Two letter rows whose true logits are 20.03 and 20.06: bf16 rounds both
    # to 20.0 (step 0.125 in [16, 32)), fp32 keeps them apart.
    h = torch.tensor([1.0, 1.0], dtype=torch.bfloat16)
    w = torch.tensor([[20.0, 0.03125], [20.0, 0.0625], [10.0, 0.0], [5.0, 0.0]], dtype=torch.bfloat16)
    bf16 = [float(x) for x in (w @ h).float()]
    assert H.letter_argmax(bf16) == (0, True)
    fp32 = H.fp32_letter_logits(h, w)
    assert H.letter_argmax(fp32) == (1, False)


def test_residual_exact_tie_still_uses_the_registered_rule():
    torch = pytest.importorskip("torch")
    h = torch.tensor([1.0], dtype=torch.bfloat16)
    w = torch.tensor([[2.0], [3.0], [3.0], [1.0]], dtype=torch.bfloat16)
    assert H.letter_argmax(H.fp32_letter_logits(h, w)) == (1, True)
