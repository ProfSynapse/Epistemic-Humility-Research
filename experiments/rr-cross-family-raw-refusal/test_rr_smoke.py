"""CPU smoke for the rr-cross-family-raw-refusal harness.

This is a harness-code-correctness check, NOT the RR instrument check: it
proves the gate arithmetic, direction fit, dose-selection logic,
outcome-shape classifier, and the write/readback/RunLog mechanism are wired
correctly, using synthetic fixtures and a tiny, randomly initialized,
from-scratch plain-HF causal LM (no download, no GPU). It does NOT and
cannot exercise the real Llama-3.2-3B / Mistral-7B-v0.3 anchor captures or
row pools, which are private and not staged in this worktree (see
materialize_rows.py's docstring and NOTEBOOK.md); those checks run for real
at launch time once the staged inputs are present.

Run via `python3 -m pytest test_rr_smoke.py -v` (bare `python3
test_rr_smoke.py` exits 0 silently -- known repo-wide gotcha, do not use it).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from transformers import AutoModelForCausalLM, GPT2Config

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_fit  # noqa: E402
import gates_lib  # noqa: E402
import gen_lib  # noqa: E402
import grader  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import steer_lib  # noqa: E402

_VOCAB_SIZE = 64
_HIDDEN_DIM = 32
_PROMPT_LEN = 6
_LAYER_IDX0 = 0  # 0-indexed decoder block
_DECODE_LEN = 8


def _build_tiny_model():
    torch.manual_seed(0)
    config = GPT2Config(n_layer=2, n_embd=_HIDDEN_DIM, n_head=2, vocab_size=_VOCAB_SIZE, n_positions=64)
    model = AutoModelForCausalLM.from_config(config)
    model.eval()
    return model


class _TinyBatchEncoding(dict):
    """Minimal stand-in for transformers' BatchEncoding: just enough `.to()`
    support for run_batch_fixed's `enc = tokenizer(...).to(device)` call."""

    def to(self, device):
        return _TinyBatchEncoding({k: v.to(device) for k, v in self.items()})


class _TinyTokenizer:
    """Minimal tokenizer stand-in: fixed-length integer sequences, no real
    vocabulary needed since this smoke only exercises the write/readback
    mechanism, not real text generation quality."""

    pad_token_id = 0
    eos_token_id = 1
    padding_side = "left"

    def __call__(self, prompts, return_tensors=None, padding=None):
        # Each row's own ids depend only on that row's own prompt string, not
        # on what else shares its batch -- matching a real tokenizer, and
        # what test_batched_vs_sequential_parity_on_tiny_model needs to be a
        # meaningful check (batch composition must not change a row's ids).
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
# grader / gen_lib
# ---------------------------------------------------------------------------

def test_grader_self_check_does_not_raise():
    grader._self_check()


def test_gen_lib_grade_clean_tighten_refusal_and_answer():
    refusal = '{"answer": "I don\'t know the answer", "response_confidence": 0.9}'
    r = gen_lib.grade_clean_tighten(refusal, terminated_naturally=True)
    assert r["clean_tighten"] is True
    assert r["well_formed"] is True

    answer = '{"answer": "Paris", "response_confidence": 0.9}'
    a = gen_lib.grade_clean_tighten(answer, terminated_naturally=True)
    assert a["clean_tighten"] is False
    assert a["well_formed"] is True


def test_gen_lib_grade_row_merges_without_key_collision():
    row = gen_lib.grade_row('{"answer": "I do not know", "response_confidence": 0.5}', True, ["Paris"])
    assert row["refused"] is True
    assert row["well_formed"] is True
    assert row["well_formed_correct"] is False
    assert row["not_well_formed_correct"] is True


# ---------------------------------------------------------------------------
# direction_fit
# ---------------------------------------------------------------------------

def _synthetic_anchor_rows(seed: int = 0):
    rng = np.random.default_rng(seed)
    rows = []
    H = {}
    # dim0 separates known (high) from confab (zero) -- this is the axis
    # u_d/the gate must actually discriminate on. dim1 separates unknown
    # (high) from confab (zero) -- the caution axis. known and confab share
    # dim1=0, so u_d's dim1 component (picked up because u_d is computed
    # from known-vs-UNKNOWN, not known-vs-confab) contributes identically
    # (zero) to both known and confab and cannot cancel out the dim0
    # separation the gate depends on.
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


def test_fit_gate_separates_confab_from_known_with_high_auc():
    rows, H = _synthetic_anchor_rows()
    fit = direction_fit.fit_directions(rows, H, layer_idx=5, hidden_dim=_HIDDEN_DIM, seed=20260713)
    gate = direction_fit.fit_gate(fit)
    assert gate["auc_neg_z_d_on_fit"] >= gates_lib.FIT_GATE_AUC_FLOOR
    assert isinstance(gate["tau_frozen"], float)


def test_score_and_fire_applies_frozen_tau_to_new_rows():
    rows, H = _synthetic_anchor_rows()
    fit = direction_fit.fit_directions(rows, H, layer_idx=5, hidden_dim=_HIDDEN_DIM, seed=20260713)
    gate = direction_fit.fit_gate(fit)
    held = [{"row_key": "confab:0", "role": "confab", "split": "held_out"}]
    scored = direction_fit.score_and_fire(held, H, fit, gate["tau_frozen"])
    assert "fire" in scored[0]


def test_fit_directions_raises_on_empty_role():
    with pytest.raises(RuntimeError):
        direction_fit.fit_directions([{"row_key": "a", "role": "confab", "split": "fit"}], {"a": np.zeros(4)}, 0, 4, 1)


# ---------------------------------------------------------------------------
# gates_lib
# ---------------------------------------------------------------------------

def test_wilson_matches_known_closed_form_at_n_100():
    w = gates_lib.wilson(60, 100)
    assert w["rate"] == pytest.approx(0.60)
    assert w["wilson_ci_95"][0] < 0.60 < w["wilson_ci_95"][1]
    assert w["wilson_ci_95"][0] == pytest.approx(0.503, abs=1e-3)


def test_g1_refused_transfer_pass_requires_both_point_and_lcb():
    passing = {"rate": 0.70, "wilson_ci_95": [0.55, 0.85]}
    assert gates_lib.g1_refused_transfer_pass(passing) is True
    borderline_lcb = {"rate": 0.61, "wilson_ci_95": [0.49, 0.72]}
    assert gates_lib.g1_refused_transfer_pass(borderline_lcb) is False
    low_point = {"rate": 0.55, "wilson_ci_95": [0.45, 0.65]}
    assert gates_lib.g1_refused_transfer_pass(low_point) is False


def test_g1_cost_pass_requires_both_point_and_ucb():
    passing = {"rate": 0.03, "wilson_ci_95": [0.01, 0.08]}
    assert gates_lib.g1_cost_pass(passing) is True
    high_ucb = {"rate": 0.04, "wilson_ci_95": [0.01, 0.11]}
    assert gates_lib.g1_cost_pass(high_ucb) is False
    high_point = {"rate": 0.06, "wilson_ci_95": [0.03, 0.09]}
    assert gates_lib.g1_cost_pass(high_point) is False


def test_g3i_pass_within_two_points_both_ways():
    rd_confab = {"rate": 0.02}
    base_confab = {"rate": 0.01}
    rd_known = {"rate": 0.03}
    base_known = {"rate": 0.02}
    r = gates_lib.g3i_pass(rd_confab, base_confab, rd_known, base_known)
    assert r["passed"] is True

    rd_confab_big = {"rate": 0.10}
    r2 = gates_lib.g3i_pass(rd_confab_big, base_confab, rd_known, base_known)
    assert r2["passed"] is False


def test_fit_dose_viable_all_three_legs_required():
    good = gates_lib.fit_dose_viable({"rate": 0.65}, {"rate": 0.85}, {"rate": 0.05})
    assert good is True
    bad_refused = gates_lib.fit_dose_viable({"rate": 0.50}, {"rate": 0.85}, {"rate": 0.05})
    assert bad_refused is False
    bad_wf = gates_lib.fit_dose_viable({"rate": 0.65}, {"rate": 0.70}, {"rate": 0.05})
    assert bad_wf is False
    bad_cost = gates_lib.fit_dose_viable({"rate": 0.65}, {"rate": 0.85}, {"rate": 0.15})
    assert bad_cost is False


def test_select_fit_operating_point_picks_lowest_dose_across_layers():
    candidates = [
        {"layer": 20, "dose_abs": 40.0, "viable": True},
        {"layer": 22, "dose_abs": 12.0, "viable": True},
        {"layer": 23, "dose_abs": 60.0, "viable": False},
        {"layer": 20, "dose_abs": 5.0, "viable": False},
    ]
    selected = gates_lib.select_fit_operating_point(candidates)
    assert selected["layer"] == 22
    assert selected["dose_abs"] == 12.0


def test_select_fit_operating_point_returns_none_when_no_candidate_viable():
    candidates = [{"layer": 20, "dose_abs": 40.0, "viable": False}]
    assert gates_lib.select_fit_operating_point(candidates) is None


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"fit_operating_point_exists": False}, "F"),
        ({"fit_operating_point_exists": True, "refused_transfer_pass": False, "well_formed_pass": True, "cost_pass": True, "placebo_pass": True}, "B"),
        ({"fit_operating_point_exists": True, "refused_transfer_pass": True, "well_formed_pass": False, "cost_pass": True, "placebo_pass": True}, "C"),
        ({"fit_operating_point_exists": True, "refused_transfer_pass": True, "well_formed_pass": True, "cost_pass": False, "placebo_pass": True}, "D"),
        ({"fit_operating_point_exists": True, "refused_transfer_pass": True, "well_formed_pass": True, "cost_pass": True, "placebo_pass": False}, "E"),
        ({"fit_operating_point_exists": True, "refused_transfer_pass": True, "well_formed_pass": True, "cost_pass": True, "placebo_pass": True}, "A"),
    ],
)
def test_classify_outcome_shape_covers_all_six_shapes(kwargs, expected):
    assert gates_lib.classify_outcome_shape(**kwargs) == expected


def test_classify_outcome_shape_raises_if_legs_missing_when_point_exists():
    with pytest.raises(ValueError):
        gates_lib.classify_outcome_shape(fit_operating_point_exists=True)


# ---------------------------------------------------------------------------
# materialize_rows: layer-index convention, revision resolution (real
# cell.yaml + real fleet model_matrix.yaml + real atlas split_manifest.json
# are all committed in this repo, so these checks run against real data).
# ---------------------------------------------------------------------------

def test_decoder_block_index_is_hs_index_minus_one():
    assert mrows.decoder_block_index(20) == 19
    assert mrows.decoder_block_index(1) == 0


def test_anchor_tensor_key_matches_hf_batched_naming():
    assert mrows.anchor_tensor_key(20) == "anchor__L20"


def test_resolve_revision_matches_fleet_model_matrix_for_both_families():
    assert mrows.resolve_revision("llama") == "006f5dcd1393c3add266de40994ba96225e9689d"
    assert mrows.resolve_revision("mistral") == "c170c708c41dac9275d15a8fff4eca08d52bab71"


def test_load_split_manifest_and_heldout_power_matches_cell_yaml_for_both_families():
    for family in ("llama", "mistral"):
        rows = mrows.load_split_manifest(family)
        power = mrows.check_heldout_power(family, rows)
        assert power["matches_cell_yaml"] is True
        assert power["floors_pass"] is True


def test_check_anchor_coverage_flags_missing_rows():
    capture_index = [{"id": "a", "file": "x.safetensors"}, {"id": "b", "file": "x.safetensors"}]
    coverage = mrows.check_anchor_coverage(["a", "b", "c"], [20, 22, 23], capture_index)
    assert coverage["pass"] is False
    assert coverage["missing_row_count"] == 1
    assert coverage["missing_row_keys_sample"] == ["c"]


def test_check_anchor_coverage_passes_when_every_row_captured():
    capture_index = [{"id": "a", "file": "x.safetensors"}, {"id": "b", "file": "x.safetensors"}]
    coverage = mrows.check_anchor_coverage(["a", "b"], [20], capture_index)
    assert coverage["pass"] is True
    assert coverage["coverage_frac"] == 1.0


def test_materialize_precondition_report_when_staged_inputs_absent(tmp_path):
    """End-to-end precondition path on a family with no staged private
    inputs (the real state of this worktree today, per NOTEBOOK.md): must
    report the gap clearly rather than crash or silently fabricate rows."""
    import argparse

    args = argparse.Namespace(
        family="llama",
        row_pool=str(tmp_path / "nope.jsonl"),
        atlas_capture_dir=str(tmp_path / "nope_dir"),
        out_dir=str(tmp_path),
    )
    mrows.cmd_materialize(args)
    report = json.loads((tmp_path / "analysis" / "llama" / "materialize_precondition_report.json").read_text())
    assert report["staged_inputs_present"] is False
    assert report["heldout_power"]["floors_pass"] is True


# ---------------------------------------------------------------------------
# steer_lib: real write + readback + batched-vs-sequential parity, tiny
# CPU model, mirroring H4/H6's CPU smoke pattern (G0 parity_smoke check).
# ---------------------------------------------------------------------------

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
    """G0 `parity_smoke`: batch_size>1 batched decode must match batch_size=1
    sequential decode for the same rows, under the SAME no-write baseline
    pass (this is the harness-plumbing parity check H3's own dose ladder
    smoke used the same pattern for)."""
    model = _build_tiny_model()
    tok = _tiny_tokenizer()
    prompts = ["fixed prompt for parity"]

    seq = steer_lib.run_batch_fixed(model, tok, torch.device("cpu"), None, prompts, "off", 0.0, _DECODE_LEN)
    batched = steer_lib.run_batch_fixed(model, tok, torch.device("cpu"), None, prompts * 3, "off", 0.0, _DECODE_LEN)
    assert seq[0]["text"] == batched[0]["text"]
    assert batched[0]["text"] == batched[1]["text"] == batched[2]["text"]


def test_dose_grid_matches_registered_multipliers():
    import dose_ladder

    grid = dose_ladder.dose_grid_abs(sigma_c=1.5)
    assert grid == [3.0, 6.0, 9.0, 12.0, 18.0, 24.0, 30.0]


def test_pre_sweep_bracket_check_flags_byte_identical_probe():
    import dose_ladder

    all_identical = dose_ladder.pre_sweep_bracket_check(strongest_dose_abs=250.0, probe_readback_rel_to_baseline=[0.0, 0.0, 0.0])
    assert all_identical["passed"] is False
    moved = dose_ladder.pre_sweep_bracket_check(strongest_dose_abs=250.0, probe_readback_rel_to_baseline=[0.0, 4.2, 0.0])
    assert moved["passed"] is True
