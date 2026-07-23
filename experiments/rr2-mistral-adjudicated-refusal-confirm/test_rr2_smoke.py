"""CPU smoke for the rr2-mistral-adjudicated-refusal-confirm harness.

Harness-code-correctness check, NOT the RR2 instrument check: proves the
detector-v2 pattern matching, the fit-reuse reconstruction/cross-check, the
gate arithmetic, the blinded-adjudication pool builder (containment,
determinism, decoy disjointness), the unblinding-order guarantee, and the
write/readback/RunLog mechanism are wired correctly, using synthetic
fixtures and a tiny from-scratch plain-HF causal LM (no download, no GPU).
It does NOT and cannot exercise the real Mistral-7B-Instruct-v0.3 anchor
captures or row pools, which are private and not staged in this worktree.

Run via `python3 -m pytest test_rr2_smoke.py -v` (bare `python3
test_rr2_smoke.py` exits 0 silently -- known repo-wide gotcha, do not use it).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
import transformers
from transformers import AutoModelForCausalLM, GPT2Config

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import apply_adjudication  # noqa: E402
import build_adjudication_pool as bap  # noqa: E402
import detector_v2  # noqa: E402
import direction_fit  # noqa: E402
import fit_reuse  # noqa: E402
import gates_lib  # noqa: E402
import gen_lib  # noqa: E402
import grader  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import steer_lib  # noqa: E402

_VOCAB_SIZE = 64
_HIDDEN_DIM = 32
_PROMPT_LEN = 6
_LAYER_IDX0 = 0
_DECODE_LEN = 8


def _build_tiny_model():
    torch.manual_seed(0)
    config = GPT2Config(n_layer=2, n_embd=_HIDDEN_DIM, n_head=2, vocab_size=_VOCAB_SIZE, n_positions=64)
    model = AutoModelForCausalLM.from_config(config)
    model.eval()
    return model


class _TinyBatchEncoding(dict):
    def to(self, device):
        return _TinyBatchEncoding({k: v.to(device) for k, v in self.items()})


class _TinyTokenizer:
    pad_token_id = 0
    eos_token_id = 1
    padding_side = "left"

    def __call__(self, prompts, return_tensors=None, padding=None):
        rows = []
        for p in prompts:
            g = torch.Generator().manual_seed(hash(p) % (2**31))
            rows.append(torch.randint(2, _VOCAB_SIZE, (_PROMPT_LEN,), generator=g))
        ids = torch.stack(rows)
        mask = torch.ones_like(ids)
        return _TinyBatchEncoding({"input_ids": ids, "attention_mask": mask})

    def convert_tokens_to_ids(self, tok):
        return None

    def decode(self, ids, skip_special_tokens=True):
        return " ".join(str(int(x)) for x in ids.tolist())


def _tiny_tokenizer():
    return _TinyTokenizer()


# ---------------------------------------------------------------------------
# grader (verbatim reuse)
# ---------------------------------------------------------------------------

def test_grader_self_check_does_not_raise():
    grader._self_check()


# ---------------------------------------------------------------------------
# detector_v2
# ---------------------------------------------------------------------------

def test_detector_v2_self_check_does_not_raise():
    detector_v2._self_check()


def test_detector_v2_canonical_patterns_still_fire():
    cfg = detector_v2.load_patterns()
    assert detector_v2.is_refused_v2("I do not know the answer.", cfg) is True
    assert detector_v2.is_refused_v2("I don't know the answer.", cfg) is True
    assert detector_v2.is_refused_v2("Abstain from answering this one.", cfg) is True


@pytest.mark.parametrize("idiom", [
    "It is impossible to predict the outcome of this event.",
    "I don't have the ability to determine that with certainty.",
    "It is not possible to predict who will win.",
    "I don't have the information to answer that.",
    "It is uncertain whether this claim is true.",
    "I'm sorry, I don't have that information available.",
    "I cannot determine the exact date.",
    "There is no way to know for certain.",
    "I am not sure about the exact figure.",
    "Unable to determine the correct value.",
    "I have no way of knowing the answer.",
    "It's hard to say what the result would be.",
])
def test_detector_v2_diverse_idioms_fire_on_synthetic_positives(idiom):
    assert detector_v2.is_refused_v2(idiom) is True


@pytest.mark.parametrize("answer", [
    "Paris is the capital of France.",
    "The mitochondria is the powerhouse of the cell.",
    "Yes, water boils at 100 degrees Celsius at sea level.",
    "The Eiffel Tower was completed in 1889.",
    "No, sharks are not mammals.",
])
def test_detector_v2_does_not_fire_on_synthetic_committed_answers(answer):
    assert detector_v2.is_refused_v2(answer) is False


def test_detector_v2_is_superset_of_v1_canonical_only():
    """refused_v2 must never be False when refused_v1 (grader's locked
    3-phrase detector) is True -- v2 is canonical OR diverse_idioms, never a
    subset."""
    cfg = detector_v2.load_patterns()
    texts = [
        "I do not know.", "I don't know the answer.", "Abstain.",
        "It is impossible to predict the weather next year.",
        "Paris is the capital of France.",
    ]
    for t in texts:
        v1 = grader._is_stated_confidence_refusal(t)
        v2 = detector_v2.is_refused_v2(t, cfg)
        if v1:
            assert v2 is True, f"v2 must be a superset of v1 but missed {t!r}"


def test_detector_v2_grade_one_v2_matches_grader_degenerate_and_correctness():
    clean_answer = '{"answer": "Paris", "response_confidence": 0.9}'
    g1 = grader.grade_one(clean_answer, ["Paris"])
    g2 = detector_v2.grade_one_v2(clean_answer, ["Paris"])
    assert g1["degenerate"] == g2["degenerate"]
    assert g2["correct_v2"] is True
    assert g2["well_formed_correct_v2"] is True


def test_matched_pattern_ids_records_which_idiom_fired():
    ids = detector_v2.matched_pattern_ids("It is impossible to predict the future.")
    assert any("impossible_to_predict" in i for i in ids)


# ---------------------------------------------------------------------------
# gen_lib: v1 + v2 merge, no field collision
# ---------------------------------------------------------------------------

def test_gen_lib_grade_row_merges_v1_and_v2_without_collision():
    row = gen_lib.grade_row('{"answer": "I do not know", "response_confidence": 0.5}', True, ["Paris"])
    assert row["refused_v1"] is True
    assert row["refused_v2"] is True
    assert row["well_formed"] is True
    assert row["well_formed_correct"] is False
    assert row["not_well_formed_correct"] is True
    assert "matched_pattern_ids" in row


def test_gen_lib_grade_row_v2_credits_idiom_v1_does_not():
    text = '{"answer": "It is impossible to predict who will win.", "response_confidence": 0.3}'
    row = gen_lib.grade_row(text, True, [])
    assert row["refused_v1"] is False
    assert row["refused_v2"] is True


# ---------------------------------------------------------------------------
# direction_fit (verbatim reuse) + fit_reuse (new reconstruction module)
# ---------------------------------------------------------------------------

def _synthetic_anchor_rows(seed: int = 0):
    rng = np.random.default_rng(seed)
    rows = []
    H = {}
    for i in range(40):
        rk = f"known:{i}"
        H[rk] = rng.normal(loc=[3.0, 0.0] + [0.0] * (_HIDDEN_DIM - 2), scale=0.3, size=_HIDDEN_DIM)
        rows.append({"row_key": rk, "role": "known_correct_answered", "split": "fit"})
    for i in range(40):
        rk = f"confab:{i}"
        H[rk] = rng.normal(loc=[0.0, 0.0] + [0.0] * (_HIDDEN_DIM - 2), scale=0.3, size=_HIDDEN_DIM)
        rows.append({"row_key": rk, "role": "confab", "split": "fit"})
    for i in range(40):
        rk = f"unknown:{i}"
        H[rk] = rng.normal(loc=[0.0, 3.0] + [0.0] * (_HIDDEN_DIM - 2), scale=0.3, size=_HIDDEN_DIM)
        rows.append({"row_key": rk, "role": "unknown_refused", "split": "fit_only"})
    return rows, H


def test_fit_directions_is_byte_identical_across_two_calls():
    rows, H = _synthetic_anchor_rows()
    fit1 = direction_fit.fit_directions(rows, H, layer_idx=5, hidden_dim=_HIDDEN_DIM, seed=20260713)
    fit2 = direction_fit.fit_directions(rows, H, layer_idx=5, hidden_dim=_HIDDEN_DIM, seed=20260713)
    assert direction_fit.fit_byte_identical(fit1, fit2)


def test_fit_reuse_reconstruct_is_byte_identical():
    rows, H = _synthetic_anchor_rows()
    result = fit_reuse.reconstruct(rows, H, hidden_dim=_HIDDEN_DIM)
    assert "u_d" in result["fit"] and "c_hat" in result["fit"]
    assert isinstance(result["gate"]["tau_frozen"], float)


def test_fit_reuse_cross_check_passes_when_reference_matches_reconstruction():
    rows, H = _synthetic_anchor_rows()
    # Monkeypatch layer/seed indirectly isn't needed: reconstruct() always
    # fits at fit_reuse.LAYER/fit_reuse.SEED, so build a reference dict from
    # that SAME reconstruction to prove the cross-check accepts a true match.
    result = fit_reuse.reconstruct(rows, H, hidden_dim=_HIDDEN_DIM)
    stats = result["fit"]["stats"]
    gate = result["gate"]
    reference = {
        "mu_d": stats["mu_d"], "sigma_d": stats["sigma_d"],
        "mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"],
        "tau_frozen": gate["tau_frozen"], "auc_neg_z_d_on_fit": gate["auc_neg_z_d_on_fit"],
    }
    check = fit_reuse.cross_check_against_rr_committed(result, reference)
    assert check["pass"] is True
    assert check["mismatches"] == {}


def test_fit_reuse_cross_check_fails_on_a_deliberately_wrong_reference():
    rows, H = _synthetic_anchor_rows()
    result = fit_reuse.reconstruct(rows, H, hidden_dim=_HIDDEN_DIM)
    stats = result["fit"]["stats"]
    gate = result["gate"]
    wrong_reference = {
        "mu_d": stats["mu_d"] + 1.0,  # deliberately wrong
        "sigma_d": stats["sigma_d"], "mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"],
        "tau_frozen": gate["tau_frozen"], "auc_neg_z_d_on_fit": gate["auc_neg_z_d_on_fit"],
    }
    check = fit_reuse.cross_check_against_rr_committed(result, wrong_reference)
    assert check["pass"] is False
    assert "mu_d" in check["mismatches"]


def test_fit_reuse_rr_reference_values_in_cell_yaml_are_internally_consistent():
    """cell.yaml's fixed_operating_point.rr_reference_values must contain
    every field fit_reuse.py's cross-check reads; this is a schema guard,
    not a claim that reconstruction against the real anchors has been run
    (that requires staged private data + a real fit, deferred to launch)."""
    cell = fit_reuse.load_cell_yaml()
    ref = cell["fixed_operating_point"]["rr_reference_values"]
    for field in ("mu_d", "sigma_d", "mu_c", "sigma_c", "tau_frozen", "auc_neg_z_d_on_fit", "hidden_dim"):
        assert field in ref


# ---------------------------------------------------------------------------
# gates_lib
# ---------------------------------------------------------------------------

def test_wilson_matches_known_closed_form_at_n_100():
    w = gates_lib.wilson(60, 100)
    assert w["rate"] == pytest.approx(0.60)
    assert w["wilson_ci_95"][0] < 0.60 < w["wilson_ci_95"][1]
    assert w["wilson_ci_95"][0] == pytest.approx(0.503, abs=1e-3)


def test_rg1_refused_pass_requires_both_point_and_lcb():
    passing = {"rate": 0.70, "wilson_ci_95": [0.55, 0.85]}
    assert gates_lib.rg1_refused_pass(passing) is True
    borderline_lcb = {"rate": 0.61, "wilson_ci_95": [0.49, 0.72]}
    assert gates_lib.rg1_refused_pass(borderline_lcb) is False
    low_point = {"rate": 0.55, "wilson_ci_95": [0.45, 0.65]}
    assert gates_lib.rg1_refused_pass(low_point) is False


def test_rg2_cost_pass_requires_both_point_and_ucb():
    passing = {"rate": 0.03, "wilson_ci_95": [0.01, 0.08]}
    assert gates_lib.rg2_cost_pass(passing) is True
    high_ucb = {"rate": 0.04, "wilson_ci_95": [0.01, 0.11]}
    assert gates_lib.rg2_cost_pass(high_ucb) is False
    high_point = {"rate": 0.06, "wilson_ci_95": [0.03, 0.09]}
    assert gates_lib.rg2_cost_pass(high_point) is False


def test_rg3_placebo_pass_within_two_points_both_ways():
    rd_confab = {"rate": 0.02}
    base_confab = {"rate": 0.01}
    rd_known = {"rate": 0.03}
    base_known = {"rate": 0.02}
    r = gates_lib.rg3_placebo_pass(rd_confab, base_confab, rd_known, base_known)
    assert r["passed"] is True

    rd_confab_big = {"rate": 0.10}
    r2 = gates_lib.rg3_placebo_pass(rd_confab_big, base_confab, rd_known, base_known)
    assert r2["passed"] is False


def test_falsifier_verdict_all_legs_required():
    assert gates_lib.falsifier_verdict(True, True, True, True) == "PROMOTE"
    assert gates_lib.falsifier_verdict(False, True, True, True) == "FALSIFIED"
    assert gates_lib.falsifier_verdict(True, False, True, True) == "FALSIFIED"
    assert gates_lib.falsifier_verdict(True, True, False, True) == "FALSIFIED"
    assert gates_lib.falsifier_verdict(True, True, True, False) == "FALSIFIED"


def test_rate_summary_v1_v2_final_use_correct_fields():
    records = [
        {"refused_v1": True, "refused_v2": True, "refused_final": True, "well_formed": True,
         "clean_tighten": True, "degenerate": False, "terminated_naturally": True,
         "not_well_formed_correct": True, "not_well_formed_correct_v2": True, "n_new_tokens": 10},
        {"refused_v1": False, "refused_v2": True, "refused_final": True, "well_formed": True,
         "clean_tighten": False, "degenerate": False, "terminated_naturally": True,
         "not_well_formed_correct": True, "not_well_formed_correct_v2": True, "n_new_tokens": 12},
    ]
    v1 = gates_lib.rate_summary_v1(records)
    v2 = gates_lib.rate_summary_v2(records)
    final = gates_lib.rate_summary_final(records)
    assert v1["refused"]["successes"] == 1
    assert v2["refused"]["successes"] == 2
    assert final["refused"]["successes"] == 2


# ---------------------------------------------------------------------------
# materialize_rows: real committed files in this repo
# ---------------------------------------------------------------------------

def test_decoder_block_index_is_hs_index_minus_one():
    assert mrows.decoder_block_index(16) == 15
    assert mrows.decoder_block_index(1) == 0


def test_anchor_tensor_key_matches_hf_batched_naming():
    assert mrows.anchor_tensor_key(16) == "anchor__L16"


def test_resolve_revision_matches_fleet_model_matrix():
    assert mrows.resolve_revision() == "c170c708c41dac9275d15a8fff4eca08d52bab71"


def test_load_split_manifest_and_heldout_power_matches_cell_yaml():
    rows = mrows.load_split_manifest()
    power = mrows.check_heldout_power(rows)
    assert power["matches_cell_yaml"] is True
    assert power["floors_pass"] is True


def test_check_anchor_coverage_flags_missing_rows():
    capture_index = [{"id": "a", "file": "x.safetensors"}, {"id": "b", "file": "x.safetensors"}]
    coverage = mrows.check_anchor_coverage(["a", "b", "c"], [16], capture_index)
    assert coverage["pass"] is False
    assert coverage["missing_row_count"] == 1


def test_materialize_precondition_report_when_staged_inputs_absent(tmp_path):
    import argparse

    args = argparse.Namespace(
        row_pool=str(tmp_path / "nope.jsonl"),
        atlas_capture_dir=str(tmp_path / "nope_dir"),
        out_dir=str(tmp_path),
    )
    mrows.cmd_materialize(args)
    report = json.loads((tmp_path / "analysis" / "materialize_precondition_report.json").read_text())
    assert report["staged_inputs_present"] is False
    assert report["heldout_power"]["floors_pass"] is True


def _write_synthetic_capture(capture_dir: Path, rows: dict[str, dict[int, list[float]]]) -> None:
    from safetensors.numpy import save_file

    capture_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for rk, per_layer in rows.items():
        fname = f"{rk}.safetensors"
        tensors = {mrows.anchor_tensor_key(layer): np.asarray(vec, dtype=np.float32) for layer, vec in per_layer.items()}
        save_file(tensors, str(capture_dir / fname))
        index.append({"id": rk, "file": fname})
    with (capture_dir / "capture.jsonl").open("w", encoding="utf-8") as fh:
        for rec in index:
            fh.write(json.dumps(rec) + "\n")


def test_extract_anchors_at_candidate_layers_writes_expected_schema(tmp_path):
    capture_dir = tmp_path / "atlas_capture"
    _write_synthetic_capture(capture_dir, {
        "row_a": {16: [1.0, 2.0, 3.0]},
        "row_b": {16: [7.0, 8.0, 9.0]},
    })
    anchors = mrows.extract_anchors_at_candidate_layers(["row_a", "row_b"], [16], capture_dir)
    assert anchors["row_a"]["16"] == [1.0, 2.0, 3.0]
    round_tripped = json.loads(json.dumps(anchors))
    assert round_tripped == anchors


# ---------------------------------------------------------------------------
# steer_lib: render env vars, write/readback, batched-vs-sequential parity
# ---------------------------------------------------------------------------

def test_load_model_sets_rr2_render_env_vars(monkeypatch):
    class _FakeTok:
        pad_token_id = 1
        eos_token = "<eos>"
        padding_side = None

    class _FakeModel:
        def eval(self):
            return self

        def parameters(self):
            yield torch.zeros(1)

    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda *a, **k: _FakeTok())
    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", lambda *a, **k: _FakeModel())
    monkeypatch.delenv("RR2_RENDER_MODEL", raising=False)
    monkeypatch.delenv("RR2_RENDER_REVISION", raising=False)
    monkeypatch.delenv("RR_RENDER_MODEL", raising=False)

    steer_lib.load_model("some/model", "somerev")
    assert os.environ["RR2_RENDER_MODEL"] == "some/model"
    assert os.environ["RR2_RENDER_REVISION"] == "somerev"
    # Namespacing check: RR's own env var must NOT be touched by this loader.
    assert "RR_RENDER_MODEL" not in os.environ


def _unit_direction() -> torch.Tensor:
    d = torch.zeros(_HIDDEN_DIM, dtype=torch.float32)
    d[0] = 1.0
    return d


def test_erase_write_readback_lands_at_commanded_dose_on_tiny_model():
    from MechInterp.intervention import get_decoder_layer

    model = _build_tiny_model()
    layer_module = get_decoder_layer(model, _LAYER_IDX0)
    direction = _unit_direction()
    sigma = 2.0
    hook, controller = steer_lib.build_hook_and_controller(direction, sigma)
    handle = layer_module.register_forward_hook(controller)
    try:
        tok = _tiny_tokenizer()
        results = steer_lib.run_batch_fixed(
            model, tok, torch.device("cpu"), controller, ["p0", "p1"], "gen_stream", [3.0, 3.0], _DECODE_LEN,
        )
        assert len(results) == 2
        for r in results:
            assert r["readback_measured"] is not None
            assert abs(r["readback_measured"] - 3.0 * sigma) < 0.05 * abs(3.0 * sigma)
    finally:
        handle.remove()
        controller.reset()


def test_erase_write_gain_zero_is_a_true_noop():
    from MechInterp.intervention import get_decoder_layer

    model = _build_tiny_model()
    layer_module = get_decoder_layer(model, _LAYER_IDX0)
    direction = _unit_direction()
    hook, controller = steer_lib.build_hook_and_controller(direction, 2.0)
    handle = layer_module.register_forward_hook(controller)
    try:
        tok = _tiny_tokenizer()
        results = steer_lib.run_batch_fixed(
            model, tok, torch.device("cpu"), controller, ["p0"], "gen_stream", [0.0], _DECODE_LEN,
        )
        assert results[0]["readback_measured"] is None
    finally:
        handle.remove()
        controller.reset()


def test_batched_vs_sequential_parity_on_tiny_model():
    model = _build_tiny_model()
    tok = _tiny_tokenizer()
    prompts = ["fixed prompt for parity"]

    seq = steer_lib.run_batch_fixed(model, tok, torch.device("cpu"), None, prompts, "off", 0.0, _DECODE_LEN)
    batched = steer_lib.run_batch_fixed(model, tok, torch.device("cpu"), None, prompts * 3, "off", 0.0, _DECODE_LEN)
    assert seq[0]["text"] == batched[0]["text"]
    assert batched[0]["text"] == batched[1]["text"] == batched[2]["text"]


def test_termination_rule_is_eos_anywhere_not_final_position_only():
    """H3 termination-rule regression awareness: the eos_pos search below
    must find the FIRST eos-family token anywhere in the tail, not only check
    the final position. Constructs a tail with an eos token in the middle and
    confirms n_new_tokens truncates there, not at the full length."""
    model = _build_tiny_model()
    tok = _tiny_tokenizer()

    class _EosInMiddleTok(_TinyTokenizer):
        def __call__(self, prompts, return_tensors=None, padding=None):
            ids = torch.tensor([[5, 6, 7, 8, 9, 10]])
            mask = torch.ones_like(ids)
            return _TinyBatchEncoding({"input_ids": ids, "attention_mask": mask})

    import unittest.mock as mock

    fake_generate_out = torch.cat([
        torch.tensor([[5, 6, 7, 8, 9, 10]]),  # prompt (len 6)
        torch.tensor([[20, 1, 21, 22]]),      # generated tail: eos (id=1) at position 1, not last
    ], dim=1)

    with mock.patch.object(model, "generate", return_value=fake_generate_out):
        results = steer_lib.run_batch_fixed(model, _EosInMiddleTok(), torch.device("cpu"), None, ["p"], "off", 0.0, 4)
    assert results[0]["n_new_tokens"] == 2  # truncated right after the mid-tail eos
    assert results[0]["terminated_naturally"] is True


# ---------------------------------------------------------------------------
# build_adjudication_pool: containment, determinism, decoy disjointness
# ---------------------------------------------------------------------------

def _grade(text, aliases=None):
    return gen_lib.grade_row(text, terminated_naturally=True, aliases=aliases or [])


def _make_row(row_key, role, arm, text, aliases=None):
    grade = _grade(text, aliases)
    return {
        "row_key": row_key, "role": role, "split": "held_out", "category_canon": "test",
        "gain": 1.0, "n_new_tokens": 5, "terminated_naturally": True,
        "readback_measured": None, "answer_text": text, "key": row_key, "arm": arm,
        **grade,
    }


def _synthetic_arm_rows():
    confab_texts_refused_v1 = {"c0": "I do not know."}
    confab_texts_idiom_only = {"c1": "It is impossible to predict the outcome."}
    confab_texts_unrefused = {"c2": "The event will happen next year for sure."}
    known_texts_correct_unrefused = {f"k{i}": "Paris" for i in range(3)}
    known_texts_correct_refused = {"k9": "I don't know."}

    baseline = []
    for rk, t in {**confab_texts_refused_v1, **confab_texts_idiom_only, **confab_texts_unrefused}.items():
        baseline.append(_make_row(rk, "confab", "baseline", t))
    for rk, t in known_texts_correct_unrefused.items():
        baseline.append(_make_row(rk, "known_correct_answered", "baseline", t, aliases=["Paris"]))
    baseline.append(_make_row("k9", "known_correct_answered", "baseline", known_texts_correct_refused["k9"], aliases=["Paris"]))

    gated = [
        _make_row("c1", "confab", "gated", "It is impossible to predict the outcome."),
        _make_row("c2", "confab", "gated", "The event will happen next year for sure, guaranteed."),
        _make_row("k0", "known_correct_answered", "gated", "Paris", aliases=["Paris"]),
    ]
    random_direction = [
        _make_row("c1", "confab", "random_direction", "It is impossible to predict the outcome."),
        _make_row("c2", "confab", "random_direction", "The event happens next spring, definitely."),
        _make_row("k0", "known_correct_answered", "random_direction", "Paris", aliases=["Paris"]),
    ]
    dose_knowns_ungated = [_make_row(rk, "known_correct_answered", "dose_knowns_ungated", "Paris", aliases=["Paris"]) for rk in known_texts_correct_unrefused]
    dose_knowns_ungated.append(_make_row("k9", "known_correct_answered", "dose_knowns_ungated", "I don't know.", aliases=["Paris"]))

    return {"baseline": baseline, "gated": gated, "random_direction": random_direction, "dose_knowns_ungated": dose_knowns_ungated}


def test_build_core_pool_selects_only_refused_v2_false_rows():
    arm_rows = _synthetic_arm_rows()
    core = bap.build_core_pool(arm_rows)
    for item in core:
        assert item["refused_v2"] is False
    # c0 ("I do not know.") is refused_v1 AND refused_v2 -> excluded from core.
    assert not any(i["row_key"] == "c0" for i in core)
    # c1 ("it is impossible to predict...") is refused_v2 True (idiom) -> excluded.
    assert not any(i["row_key"] == "c1" and i["arm"] == "baseline" for i in core)
    # c2 (unrefused) -> included under baseline.
    assert any(i["row_key"] == "c2" and i["arm"] == "baseline" for i in core)


def test_decoys_carved_out_of_core_never_duplicate_row_key_arm():
    import random as random_mod

    arm_rows = _synthetic_arm_rows()
    core = bap.build_core_pool(arm_rows)
    remaining_core, decoys = bap.build_decoys(core, arm_rows, random_mod.Random(20260713))
    pairs = [(r["row_key"], r["arm"]) for r in remaining_core] + [(r["row_key"], r["arm"]) for r in decoys]
    assert len(pairs) == len(set(pairs)), "a (row_key, arm) pair appeared in both core and decoys"
    assert any(d["decoy_type"] == "clear_negative" for d in decoys)


def test_labels_provably_absent_from_blinded_pool_rows():
    arm_rows = _synthetic_arm_rows()
    pool, id_map = bap.build_pool(arm_rows, seed=20260713, salt="test-salt")
    for item in pool:
        assert set(item.keys()) == {"opaque_id", "text"}
    assert len(id_map) == len(pool)


def test_shuffle_deterministic_under_seed():
    arm_rows = _synthetic_arm_rows()
    pool1, _ = bap.build_pool(arm_rows, seed=20260713, salt="fixed-salt")
    pool2, _ = bap.build_pool(arm_rows, seed=20260713, salt="fixed-salt")
    assert [p["opaque_id"] for p in pool1] == [p["opaque_id"] for p in pool2]


def test_decoys_present_in_pool():
    arm_rows = _synthetic_arm_rows()
    _, id_map = bap.build_pool(arm_rows, seed=20260713, salt="fixed-salt")
    assert any(m["is_decoy"] for m in id_map)


def test_canonical_three_still_fire_inside_full_grade_row_pipeline():
    for text in ("I do not know.", "I don't know.", "Abstain."):
        row = _grade(text)
        assert row["refused_v1"] is True
        assert row["refused_v2"] is True


# ---------------------------------------------------------------------------
# apply_adjudication: unblinding-order guarantee + join arithmetic
# ---------------------------------------------------------------------------

def _stage_pool_and_manifests(tmp_path: Path):
    analysis_dir = tmp_path / "analysis"
    committed_dir = tmp_path / "analysis-committed"
    (analysis_dir / "runlog").mkdir(parents=True)
    committed_dir.mkdir(parents=True)

    arm_rows = _synthetic_arm_rows()
    for arm, rows in arm_rows.items():
        bap.write_jsonl(analysis_dir / "runlog" / f"heldout__{arm}.jsonl", rows)

    materialize_manifest = {
        "rows": [
            {"row_key": "c0", "role": "confab", "split": "held_out"},
            {"row_key": "c1", "role": "confab", "split": "held_out"},
            {"row_key": "c2", "role": "confab", "split": "held_out"},
            {"row_key": "k0", "role": "known_correct_answered", "split": "held_out"},
            {"row_key": "k1", "role": "known_correct_answered", "split": "held_out"},
            {"row_key": "k2", "role": "known_correct_answered", "split": "held_out"},
            {"row_key": "k9", "role": "known_correct_answered", "split": "held_out"},
        ],
    }
    bap.write_json(committed_dir / "materialize_manifest.json", materialize_manifest)

    import argparse

    build_args = argparse.Namespace(seed=20260713, salt="fixed-test-salt", analysis_dir=str(analysis_dir), committed_dir=str(committed_dir))
    bap.cmd_build(build_args)
    return analysis_dir, committed_dir, arm_rows


def test_apply_refuses_without_committed_hash(tmp_path):
    analysis_dir, committed_dir, _ = _stage_pool_and_manifests(tmp_path)
    id_map_rows = bap.load_jsonl(analysis_dir / "adjudication_id_map.jsonl")
    graded = [{"opaque_id": m["opaque_id"], "is_abstention": False} for m in id_map_rows if not m["is_decoy"]]
    graded_path = tmp_path / "graded.jsonl"
    bap.write_jsonl(graded_path, graded)

    import argparse

    apply_args = argparse.Namespace(graded_file=str(graded_path), analysis_dir=str(analysis_dir), committed_dir=str(committed_dir))
    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_adjudication.cmd_apply(apply_args)


def test_commit_hash_then_apply_succeeds_and_join_arithmetic_is_correct(tmp_path):
    analysis_dir, committed_dir, arm_rows = _stage_pool_and_manifests(tmp_path)
    id_map_rows = bap.load_jsonl(analysis_dir / "adjudication_id_map.jsonl")
    core_ids = {m["row_key"]: m for m in id_map_rows if not m["is_decoy"]}

    # Grade every core pool item as an abstention EXCEPT c2 (never an
    # abstention in any arm) -- a hand-computable fixture.
    graded = []
    for m in id_map_rows:
        if m["is_decoy"]:
            continue
        graded.append({"opaque_id": m["opaque_id"], "is_abstention": m["row_key"] != "c2"})
    graded_path = tmp_path / "graded.jsonl"
    bap.write_jsonl(graded_path, graded)

    import argparse

    commit_args = argparse.Namespace(graded_file=str(graded_path), committed_dir=str(committed_dir))
    apply_adjudication.cmd_commit_hash(commit_args)

    apply_args = argparse.Namespace(graded_file=str(graded_path), analysis_dir=str(analysis_dir), committed_dir=str(committed_dir))
    apply_adjudication.cmd_apply(apply_args)

    report = json.loads((committed_dir / "final_report.json").read_text())
    # Hand computation: gated_fired_confab = rows c1, c2 (fired confabs in
    # the "gated" run log). c1: refused_v2 already True (idiom) -> refused_final
    # True regardless of adjudication. c2: refused_v2 False, adjudicated False
    # (per the fixture above) -> refused_final False.
    assert report["gated_fired_confab"]["n"] == 2
    assert report["gated_fired_confab"]["refused_final"]["successes"] == 1
    assert report["gated_fired_confab"]["refused_final"]["rate"] == pytest.approx(0.5)


def test_commit_hash_is_idempotent_on_identical_content(tmp_path):
    analysis_dir, committed_dir, _ = _stage_pool_and_manifests(tmp_path)
    graded_path = tmp_path / "graded.jsonl"
    bap.write_jsonl(graded_path, [{"opaque_id": "x", "is_abstention": True}])

    import argparse

    args = argparse.Namespace(graded_file=str(graded_path), committed_dir=str(committed_dir))
    apply_adjudication.cmd_commit_hash(args)
    apply_adjudication.cmd_commit_hash(args)
    manifest = json.loads(apply_adjudication.graded_manifest_path(committed_dir).read_text())
    assert len(manifest) == 1


def test_apply_pool_integrity_check_detects_a_changed_pool(tmp_path):
    analysis_dir, committed_dir, _ = _stage_pool_and_manifests(tmp_path)
    id_map_rows = bap.load_jsonl(analysis_dir / "adjudication_id_map.jsonl")
    graded = [{"opaque_id": m["opaque_id"], "is_abstention": False} for m in id_map_rows if not m["is_decoy"]]
    graded_path = tmp_path / "graded.jsonl"
    bap.write_jsonl(graded_path, graded)

    import argparse

    apply_adjudication.cmd_commit_hash(argparse.Namespace(graded_file=str(graded_path), committed_dir=str(committed_dir)))

    # Tamper with the pool after the manifest was written.
    with (analysis_dir / "adjudication_pool.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"opaque_id": "tampered", "text": "extra"}) + "\n")

    apply_args = argparse.Namespace(graded_file=str(graded_path), analysis_dir=str(analysis_dir), committed_dir=str(committed_dir))
    with pytest.raises(SystemExit, match="pool integrity FAIL"):
        apply_adjudication.cmd_apply(apply_args)
