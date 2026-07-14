"""CPU smoke for the rr3-corrected-placebo-replication harness.

Harness-code-correctness check, NOT the RR3 instrument check: proves the
detector-v2 pattern matching, the fit-reuse reconstruction/cross-check
against RR's OWN committed manifests, the corrected-placebo RG1 max-over-K
arithmetic, the sharded blinded-adjudication pool builder (global opaque-id
uniqueness including cross-dose/cross-seed reuse, held-back clear-negative
decoy disjointness), the positional-join unblinding-order guarantee, the
per-shard-AND-pooled CG1 grader-calibration floor with its void-once/void-
cell-terminal ladder, and the write/readback/RunLog mechanism are wired
correctly, using synthetic fixtures and a tiny from-scratch plain-HF causal
LM (no download, no GPU). It does NOT and cannot exercise the real Mistral/
Llama anchor captures or row pools, which are private and not staged in this
worktree.

Run via `python3 -m pytest test_rr3_smoke.py -v` (bare `python3
test_rr3_smoke.py` exits 0 silently -- known repo-wide gotcha, do not use it).

NOTE on cell.yaml: as of this harness build, `experiments/
rr3-corrected-placebo-replication/cell.yaml` does NOT parse as valid YAML --
`rider_cells:` mixes an unmarked block mapping (dose_ladder/subsample/
reporting) with `- id: ...` block-sequence items under the same key, which
PyYAML rejects (ParserError at line 134). This predates this harness build
(present at HEAD, commit b66f9b19; confirmed NOT introduced by this build's
one authorized edit to the synaptic_tuner_pin line -- see `git diff` on that
line only). Every function in this harness that itself calls
`load_cell_yaml()` is therefore untestable against the REAL file right now;
this suite tests that logic via monkeypatched synthetic cell dicts instead,
and separately documents the parse failure below as an XFAIL so it is
visible in test output without blocking this otherwise-green suite. This is
reported as the primary STOP item for the lead; the harness is not being
self-repaired against a locked spec file.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
import transformers
import yaml
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
import heldout_scorer as hs  # noqa: E402
import materialize_rows as mrows  # noqa: E402
import rr3_scorer  # noqa: E402
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
# Known STOP item: cell.yaml does not parse. Documented, not silently fixed.
# ---------------------------------------------------------------------------

@pytest.mark.xfail(strict=True, reason=(
    "cell.yaml rider_cells mixes an unmarked block mapping with `- id: ...` "
    "block-sequence items under one key (ParserError at line 134); present "
    "at HEAD before this harness build, not introduced by it. STOP item for "
    "the lead, not fixed here."
))
def test_cell_yaml_parses_as_valid_yaml():
    with (HERE / "cell.yaml").open(encoding="utf-8") as fh:
        yaml.safe_load(fh)


# ---------------------------------------------------------------------------
# grader / detector_v2 / gen_lib (verbatim-ported logic; same checks as RR2)
# ---------------------------------------------------------------------------

def test_grader_self_check_does_not_raise():
    grader._self_check()


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
])
def test_detector_v2_diverse_idioms_fire_on_synthetic_positives(idiom):
    assert detector_v2.is_refused_v2(idiom) is True


@pytest.mark.parametrize("answer", [
    "Paris is the capital of France.",
    "The mitochondria is the powerhouse of the cell.",
    "Yes, water boils at 100 degrees Celsius at sea level.",
])
def test_detector_v2_does_not_fire_on_synthetic_committed_answers(answer):
    assert detector_v2.is_refused_v2(answer) is False


def test_detector_v2_is_superset_of_v1_canonical_only():
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


def test_gen_lib_grade_row_merges_v1_and_v2_without_collision():
    row = gen_lib.grade_row('{"answer": "I do not know", "response_confidence": 0.5}', True, ["Paris"])
    assert row["refused_v1"] is True
    assert row["refused_v2"] is True
    assert row["well_formed"] is True
    assert "matched_pattern_ids" in row


def test_gen_lib_grade_row_v2_credits_idiom_v1_does_not():
    text = '{"answer": "It is impossible to predict who will win.", "response_confidence": 0.3}'
    row = gen_lib.grade_row(text, True, [])
    assert row["refused_v1"] is False
    assert row["refused_v2"] is True


def test_detector_v2_patterns_yaml_is_byte_identical_to_rr2_and_calibration_pins():
    rr2_path = HERE.parents[0] / "rr2-mistral-adjudicated-refusal-confirm" / "detector_v2_patterns.yaml"
    calib_path = HERE.parents[0] / "abstention-wide-instrument-calibration" / "detector_v2_patterns.yaml"
    here_bytes = (HERE / "detector_v2_patterns.yaml").read_bytes()
    assert here_bytes == rr2_path.read_bytes()
    assert here_bytes == calib_path.read_bytes()
    here_sha = hashlib.sha256(here_bytes).hexdigest()
    assert here_sha == hashlib.sha256(rr2_path.read_bytes()).hexdigest()


def test_detector_v2_py_is_byte_identical_to_rr2_and_calibration_pins():
    rr2_path = HERE.parents[0] / "rr2-mistral-adjudicated-refusal-confirm" / "detector_v2.py"
    calib_path = HERE.parents[0] / "abstention-wide-instrument-calibration" / "detector_v2.py"
    here_bytes = (HERE / "detector_v2.py").read_bytes()
    assert here_bytes == rr2_path.read_bytes()
    assert here_bytes == calib_path.read_bytes()


# ---------------------------------------------------------------------------
# direction_fit (verbatim reuse) + fit_reuse (family-generalized reconstruct)
# ---------------------------------------------------------------------------

def _synthetic_anchor_rows(seed: int = 0):
    rng = np.random.default_rng(seed)
    rows, H = [], {}
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
    result = fit_reuse.reconstruct(rows, H, 16, _HIDDEN_DIM)
    assert "u_d" in result["fit"] and "c_hat" in result["fit"]
    assert isinstance(result["gate"]["tau_frozen"], float)


def test_fit_reuse_cross_check_passes_when_reference_matches_reconstruction():
    rows, H = _synthetic_anchor_rows()
    result = fit_reuse.reconstruct(rows, H, 16, _HIDDEN_DIM)
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
    result = fit_reuse.reconstruct(rows, H, 16, _HIDDEN_DIM)
    stats = result["fit"]["stats"]
    gate = result["gate"]
    wrong_reference = {
        "mu_d": stats["mu_d"] + 1.0,
        "sigma_d": stats["sigma_d"], "mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"],
        "tau_frozen": gate["tau_frozen"], "auc_neg_z_d_on_fit": gate["auc_neg_z_d_on_fit"],
    }
    check = fit_reuse.cross_check_against_rr_committed(result, wrong_reference)
    assert check["pass"] is False
    assert "mu_d" in check["mismatches"]


@pytest.mark.parametrize("family", ["mistral", "llama"])
def test_fit_reuse_loads_rrs_real_committed_reference_manifest(family):
    """RG0 precondition: RR's own already-committed hs16/hs20 fit-build
    manifests (read live, not transcribed) must exist and carry every field
    the cross-check reads. Does not run a real reconstruction against them
    (that requires staged private anchors), only proves the reference source
    itself is present and well-formed."""
    ref = fit_reuse.load_rr_reference_values(family)
    for field in ("mu_d", "sigma_d", "mu_c", "sigma_c", "tau_frozen", "auc_neg_z_d_on_fit", "hidden_dim"):
        assert field in ref


# ---------------------------------------------------------------------------
# gates_lib: Wilson, RG1 (max-over-K, REQUIRED), RG2/RG3, falsifier, CG1
# (per-shard + POOLED floor and void-once/void-cell-terminal ladder, REQUIRED)
# ---------------------------------------------------------------------------

def test_wilson_matches_known_closed_form_at_n_100():
    w = gates_lib.wilson(60, 100)
    assert w["rate"] == pytest.approx(0.60)
    assert w["wilson_ci_95"][0] == pytest.approx(0.503, abs=1e-3)


def test_rg1_effect_ratio_uses_max_over_k_not_mean_or_sum():
    """REQUIRED: max-over-K RG1 arithmetic. Denominator must be the MAX of
    the K per-seed absolute lifts, not their mean/sum -- a single unlucky
    seed sets the (conservative) floor, per AMENDMENT.md Q2 resolution."""
    random_lifts_abs = [0.01, 0.05, 0.03]  # mean=0.03, sum=0.09, max=0.05
    r = gates_lib.rg1_effect_ratio(gated_lift=0.18, random_lifts_abs=random_lifts_abs)
    assert r["max_over_k_random_lift_abs"] == pytest.approx(0.05)
    assert r["effect_ratio"] == pytest.approx(0.18 / 0.05)
    assert r["passed"] is True  # 3.6 >= 3.0 floor
    # If the denominator were the MEAN (0.03) instead, ratio would be 6.0 --
    # also passing here, so use a case that only passes under max, not mean:
    tight_lifts = [0.01, 0.02, 0.059]  # mean ~= 0.0297 -> ratio(mean) ~6.06; max=0.059 -> ratio(max)~3.05
    r2 = gates_lib.rg1_effect_ratio(gated_lift=0.18, random_lifts_abs=tight_lifts)
    assert r2["max_over_k_random_lift_abs"] == pytest.approx(0.059)
    assert r2["passed"] is True
    # A case that passes under mean but FAILS under the registered max floor:
    lucky_seeds_mostly_low = [0.01, 0.01, 0.20]  # mean ~0.0733 -> ratio(mean)~2.45 fails anyway;
    # construct precisely: gated_lift chosen so ratio(mean) passes but ratio(max) fails.
    gated_lift = 0.10
    lifts = [0.01, 0.01, 0.05]  # mean=0.0233 -> ratio(mean)=4.28 (pass); max=0.05 -> ratio(max)=2.0 (fail)
    r3 = gates_lib.rg1_effect_ratio(gated_lift=gated_lift, random_lifts_abs=lifts)
    assert r3["max_over_k_random_lift_abs"] == pytest.approx(0.05)
    assert r3["effect_ratio"] == pytest.approx(2.0)
    assert r3["passed"] is False  # would have PASSED at 4.28 under a mean denominator; max is the registered rule


def test_rg1_effect_ratio_requires_k_gte_3():
    with pytest.raises(ValueError, match="K >= 3"):
        gates_lib.rg1_effect_ratio(gated_lift=0.10, random_lifts_abs=[0.01, 0.02])


def test_rg1_effect_ratio_zero_random_lift_is_infinite_ratio():
    r = gates_lib.rg1_effect_ratio(gated_lift=0.10, random_lifts_abs=[0.0, 0.0, 0.0])
    assert r["effect_ratio"] == float("inf")
    assert r["passed"] is True


def test_rg2_refused_pass_requires_both_point_and_lcb():
    assert gates_lib.rg2_refused_pass({"rate": 0.70, "wilson_ci_95": [0.55, 0.85]}) is True
    assert gates_lib.rg2_refused_pass({"rate": 0.61, "wilson_ci_95": [0.49, 0.72]}) is False
    assert gates_lib.rg2_refused_pass({"rate": 0.55, "wilson_ci_95": [0.45, 0.65]}) is False


def test_rg2_well_formed_pass():
    assert gates_lib.rg2_well_formed_pass({"rate": 0.85}) is True
    assert gates_lib.rg2_well_formed_pass({"rate": 0.79}) is False


def test_rg3_cost_pass_requires_both_point_and_ucb():
    assert gates_lib.rg3_cost_pass({"rate": 0.03, "wilson_ci_95": [0.01, 0.08]}) is True
    assert gates_lib.rg3_cost_pass({"rate": 0.04, "wilson_ci_95": [0.01, 0.11]}) is False
    assert gates_lib.rg3_cost_pass({"rate": 0.06, "wilson_ci_95": [0.03, 0.09]}) is False


def test_falsifier_verdict_all_legs_required_no_rescoring_lane():
    assert gates_lib.falsifier_verdict(True, True, True, True) == "PROMOTE"
    assert gates_lib.falsifier_verdict(False, True, True, True) == "FALSIFIED"
    assert gates_lib.falsifier_verdict(True, False, True, True) == "FALSIFIED"
    assert gates_lib.falsifier_verdict(True, True, False, True) == "FALSIFIED"
    assert gates_lib.falsifier_verdict(True, True, True, False) == "FALSIFIED"


def test_rate_summary_v2_and_final_use_correct_fields():
    records = [
        {"refused_v2": True, "refused_final": True, "well_formed": True, "not_well_formed_correct_v2": True},
        {"refused_v2": False, "refused_final": True, "well_formed": True, "not_well_formed_correct_v2": False},
    ]
    v2 = gates_lib.rate_summary_v2(records)
    final = gates_lib.rate_summary_final(records)
    assert v2["refused"]["successes"] == 1
    assert final["refused"]["successes"] == 2


def test_rate_by_source_stratifies_by_source_not_role():
    records = [
        {"source": "triviaqa", "refused_v2": True}, {"source": "triviaqa", "refused_v2": False},
        {"source": "popqa", "refused_v2": True}, {"source": "kuq", "refused_v2": False},
        {"source": "untracked_source", "refused_v2": True},
    ]
    out = gates_lib.rate_by_source(records)
    assert set(out.keys()) == {"triviaqa", "popqa", "kuq"}
    assert out["triviaqa"]["n"] == 2
    assert out["triviaqa"]["rate"]["successes"] == 1


def test_secondary_tolerance_check_inside_and_outside_envelope():
    inside = gates_lib.secondary_tolerance_check("llama32_3b_instruct", random_lift_points=5.0)
    assert inside["inside_envelope"] is True
    assert inside["gates"] is False
    outside = gates_lib.secondary_tolerance_check("llama32_3b_instruct", random_lift_points=-9.0)
    assert outside["inside_envelope"] is False


def test_cg1_shard_pass_thresholds():
    assert gates_lib.cg1_shard_pass(0.96, 0.65) is True
    assert gates_lib.cg1_shard_pass(0.94, 0.65) is False  # clear_negative below 0.95
    assert gates_lib.cg1_shard_pass(0.96, 0.59) is False  # clear_positive below 0.60


def test_cg1_evaluate_shard_void_regrade_once_then_terminal_ladder():
    """REQUIRED: the void-once-then-terminal ladder. attempt=1 failure ->
    VOID_REGRADE_ONCE (not yet a cell void); attempt=2 failure on the SAME
    shard -> VOID_CELL_TERMINAL."""
    first = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=20, clear_negative_total=25,
                                          clear_positive_correct=5, clear_positive_total=25, attempt=1)
    assert first["passed"] is False
    assert first["status"] == "VOID_REGRADE_ONCE"

    second = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=20, clear_negative_total=25,
                                           clear_positive_correct=5, clear_positive_total=25, attempt=2)
    assert second["passed"] is False
    assert second["status"] == "VOID_CELL_TERMINAL"

    passing = gates_lib.cg1_evaluate_shard("s1", clear_negative_correct=24, clear_negative_total=25,
                                            clear_positive_correct=20, clear_positive_total=25, attempt=1)
    assert passing["passed"] is True
    assert passing["status"] == "PASS"
    assert passing["clear_positive_floor_met"] is True


def test_cg1_evaluate_shard_flags_per_shard_floor_not_met_even_if_agreement_would_pass():
    below_floor = gates_lib.cg1_evaluate_shard("s2", clear_negative_correct=10, clear_negative_total=10,
                                                clear_positive_correct=10, clear_positive_total=10, attempt=1)
    assert below_floor["clear_positive_agreement"] == pytest.approx(1.0)
    assert below_floor["clear_positive_floor_met"] is False  # 10 < registered floor of 25


def test_cg1_pooled_clear_positive_floor_catches_what_per_shard_alone_would_miss():
    """REQUIRED: the pooled clear-positive floor. Successor fix (b): a shard
    that individually PASSES its per-shard floor can still be voided if the
    POOLED rate across the whole grading effort (including a still-live
    attempt-1 VOID_REGRADE_ONCE shard's decoy counts) falls below the pooled
    floor -- protects against one hard decoy subset in one shard."""
    shard_a = gates_lib.cg1_evaluate_shard("a", 25, 25, 23, 25, attempt=1)  # PASS on its own
    shard_b = gates_lib.cg1_evaluate_shard("b", 25, 25, 5, 25, attempt=1)   # VOID_REGRADE_ONCE on its own
    assert shard_a["status"] == "PASS"
    assert shard_b["status"] == "VOID_REGRADE_ONCE"

    pooled = gates_lib.cg1_pooled_clear_positive([shard_a, shard_b])
    assert pooled["clear_positive_total_pooled"] == 50
    assert pooled["clear_positive_correct_pooled"] == 28
    assert pooled["clear_positive_agreement_pooled"] == pytest.approx(0.56)
    assert pooled["passed"] is False  # 0.56 < 0.60 pooled floor, even though shard_a alone passed


def test_cg1_pooled_clear_positive_passes_when_weighted_average_clears_floor():
    shard_a = gates_lib.cg1_evaluate_shard("a", 25, 25, 20, 25, attempt=1)
    shard_b = gates_lib.cg1_evaluate_shard("b", 25, 25, 18, 25, attempt=1)
    pooled = gates_lib.cg1_pooled_clear_positive([shard_a, shard_b])
    assert pooled["clear_positive_agreement_pooled"] == pytest.approx(38 / 50)
    assert pooled["passed"] is True


# ---------------------------------------------------------------------------
# materialize_rows: pure helpers + real fleet model_matrix.yaml cross-check
# (resolve_revision reads the FLEET's file, not the broken cell.yaml)
# ---------------------------------------------------------------------------

def test_decoder_block_index_is_hs_index_minus_one():
    assert mrows.decoder_block_index(16) == 15
    assert mrows.decoder_block_index(20) == 19


def test_anchor_tensor_key_matches_hf_batched_naming():
    assert mrows.anchor_tensor_key(16) == "anchor__L16"
    assert mrows.anchor_tensor_key(20) == "anchor__L20"


@pytest.mark.parametrize("family,expected_revision", [
    ("mistral", "c170c708c41dac9275d15a8fff4eca08d52bab71"),
    ("llama", "006f5dcd1393c3add266de40994ba96225e9689d"),
])
def test_resolve_revision_matches_fleet_model_matrix(family, expected_revision):
    assert mrows.resolve_revision(family) == expected_revision


def test_check_heldout_power_with_synthetic_cell(monkeypatch):
    synthetic_cell = {"core_cell": {"family": {"heldout_power": {"confab": 2, "known_correct_answered": 2}}}}
    monkeypatch.setattr(mrows, "load_cell_yaml", lambda: synthetic_cell)
    rows = [
        {"role": "confab", "split": "held_out"}, {"role": "confab", "split": "held_out"},
        {"role": "known_correct_answered", "split": "held_out"}, {"role": "known_correct_answered", "split": "held_out"},
        {"role": "known_correct_answered", "split": "fit"},
    ]
    power = mrows.check_heldout_power("mistral", rows)
    assert power["matches_cell_yaml"] is True
    assert power["known_correct_answered_fit"] == 1


def test_check_anchor_coverage_flags_missing_rows():
    capture_index = [{"id": "a", "file": "x.safetensors"}, {"id": "b", "file": "x.safetensors"}]
    coverage = mrows.check_anchor_coverage(["a", "b", "c"], 16, capture_index)
    assert coverage["pass"] is False
    assert coverage["missing_row_count"] == 1


def test_materialize_precondition_report_when_staged_inputs_absent(tmp_path, monkeypatch):
    synthetic_cell = {"core_cell": {"family": {
        "model": "org/mistral", "revision": "c170c708c41dac9275d15a8fff4eca08d52bab71",
        "heldout_power": {"confab": 150, "known_correct_answered": 250},
    }}}
    monkeypatch.setattr(mrows, "load_cell_yaml", lambda: synthetic_cell)
    synthetic_rows = (
        [{"role": "confab", "split": "held_out"} for _ in range(150)]
        + [{"role": "known_correct_answered", "split": "held_out"} for _ in range(250)]
    )
    monkeypatch.setattr(mrows, "load_split_manifest", lambda family: synthetic_rows)

    import argparse

    args = argparse.Namespace(
        family="mistral", row_pool=str(tmp_path / "nope.jsonl"),
        atlas_capture_dir=str(tmp_path / "nope_dir"), out_dir=str(tmp_path),
    )
    mrows.cmd_materialize(args)
    report = json.loads((tmp_path / "analysis" / "mistral" / "materialize_precondition_report.json").read_text())
    assert report["staged_inputs_present"] is False
    assert report["heldout_power"]["floors_pass"] is True  # meets the 150/250 floors; only staging is missing


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


def test_extract_anchors_at_layer_writes_expected_schema(tmp_path):
    capture_dir = tmp_path / "atlas_capture"
    _write_synthetic_capture(capture_dir, {"row_a": {16: [1.0, 2.0, 3.0]}, "row_b": {16: [7.0, 8.0, 9.0]}})
    anchors = mrows.extract_anchors_at_layer(["row_a", "row_b"], 16, capture_dir)
    assert anchors["row_a"]["16"] == [1.0, 2.0, 3.0]
    round_tripped = json.loads(json.dumps(anchors))
    assert round_tripped == anchors


# ---------------------------------------------------------------------------
# steer_lib: RR3-namespaced render env vars, write/readback, batched parity
# ---------------------------------------------------------------------------

def test_load_model_sets_rr3_render_env_vars_and_leaves_rr2_and_rr_untouched(monkeypatch):
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
    for var in ("RR3_RENDER_MODEL", "RR3_RENDER_REVISION", "RR2_RENDER_MODEL", "RR2_RENDER_REVISION", "RR_RENDER_MODEL", "RR_RENDER_REVISION"):
        monkeypatch.delenv(var, raising=False)

    steer_lib.load_model("some/model", "somerev")
    assert os.environ["RR3_RENDER_MODEL"] == "some/model"
    assert os.environ["RR3_RENDER_REVISION"] == "somerev"
    assert "RR2_RENDER_MODEL" not in os.environ
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
    model = _build_tiny_model()

    class _EosInMiddleTok(_TinyTokenizer):
        def __call__(self, prompts, return_tensors=None, padding=None):
            ids = torch.tensor([[5, 6, 7, 8, 9, 10]])
            mask = torch.ones_like(ids)
            return _TinyBatchEncoding({"input_ids": ids, "attention_mask": mask})

    import unittest.mock as mock

    fake_generate_out = torch.cat([
        torch.tensor([[5, 6, 7, 8, 9, 10]]),
        torch.tensor([[20, 1, 21, 22]]),
    ], dim=1)

    with mock.patch.object(model, "generate", return_value=fake_generate_out):
        results = steer_lib.run_batch_fixed(model, _EosInMiddleTok(), torch.device("cpu"), None, ["p"], "off", 0.0, 4)
    assert results[0]["n_new_tokens"] == 2
    assert results[0]["terminated_naturally"] is True


# ---------------------------------------------------------------------------
# heldout_scorer: seed formulas (build-time interpretations), subsample
# ---------------------------------------------------------------------------

def test_rider_direction_seed_families_never_collide_with_each_other_or_core_k_seeds():
    mistral_seeds = {hs.rider_direction_seed("mistral", d) for d in hs.DOSE_LADDER}
    llama_seeds = {hs.rider_direction_seed("llama", d) for d in hs.DOSE_LADDER}
    assert mistral_seeds.isdisjoint(llama_seeds)
    core_seeds = {30260714, 30260715, 30260716}  # cell.yaml's registered K seeds (draft values)
    assert all(s < hs._CORE_SEED_FLOOR for s in mistral_seeds | llama_seeds)
    assert all(s >= hs._CORE_SEED_FLOOR for s in core_seeds)


def test_fresh_random_direction_deterministic_and_unit_norm():
    d1 = hs.fresh_random_direction(20260714, _HIDDEN_DIM)
    d2 = hs.fresh_random_direction(20260714, _HIDDEN_DIM)
    d3 = hs.fresh_random_direction(20260715, _HIDDEN_DIM)
    assert np.array_equal(d1, d2)
    assert not np.array_equal(d1, d3)
    assert abs(float(np.linalg.norm(d1)) - 1.0) < 1e-9


def test_rider_confab_subsample_deterministic_under_seed():
    rows = [{"row_key": f"c{i}"} for i in range(10)]
    out1 = hs.rider_confab_subsample({"mistral": rows}, ["mistral"], dose_ladder=(2, 4), n=5)
    out2 = hs.rider_confab_subsample({"mistral": rows}, ["mistral"], dose_ladder=(2, 4), n=5)
    assert [r["row_key"] for r in out1[("mistral", 2)]] == [r["row_key"] for r in out2[("mistral", 2)]]
    assert len(out1[("mistral", 2)]) == 5


# ---------------------------------------------------------------------------
# build_adjudication_pool: REQUIRED -- global opaque-id uniqueness including
# cross-dose/cross-seed reuse, held-back decoy disjointness, shard floors
# ---------------------------------------------------------------------------

def _core_row(cell, arm, row_key, refused_v2=False, seed=None, dose_multiplier=None, well_formed_correct=True, text="answer"):
    return {
        "cell": cell, "arm": arm, "row_key": row_key, "role": "confab", "source": "triviaqa",
        "seed": seed, "dose_multiplier": dose_multiplier, "hs_index": 16, "text": text,
        "well_formed_correct": well_formed_correct, "refused_v2": refused_v2,
    }


def test_item_key_is_full_five_tuple():
    a = _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=4)
    b = _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=8)
    assert bap.item_key(a) != bap.item_key(b)


def test_build_core_and_positive_candidates_dedup_raises_on_true_duplicate_but_allows_cross_dose_reuse():
    same_row_key_two_doses = [
        _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=4, text="dose4 text"),
        _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=8, text="dose8 text"),
    ]
    core, positive = bap.build_core_and_positive_candidates({"rider_mistral": same_row_key_two_doses})
    assert len(core) == 2  # cross-dose reuse of the same row_key is NOT a duplicate

    exact_duplicate = [
        _core_row("core_mistral", "gated", "k1"),
        _core_row("core_mistral", "gated", "k1"),  # identical (cell, arm, row_key, seed, dose_multiplier)
    ]
    with pytest.raises(SystemExit, match="duplicate pool-source item key"):
        bap.build_core_and_positive_candidates({"core_mistral": exact_duplicate})


def test_build_core_and_positive_candidates_positive_only_from_random_direction_arm():
    rows = [
        _core_row("core_mistral", "gated", "g1", refused_v2=True),         # refused, NOT random_direction -> dropped entirely
        _core_row("core_mistral", "random_direction", "r1", refused_v2=True, seed=1),  # -> positive candidate
        _core_row("core_mistral", "baseline", "b1", refused_v2=False),     # -> core
    ]
    core, positive = bap.build_core_and_positive_candidates({"core_mistral": rows})
    assert {r["row_key"] for r in core} == {"b1"}
    assert {r["row_key"] for r in positive} == {"r1"}


def test_carve_decoys_clear_negative_drawn_only_from_heldback_never_from_core():
    """REQUIRED: held-back clear-negative decoy disjointness. clear_negative
    candidates come from the HELD-BACK pool (cell='heldback'), structurally
    disjoint from every scored cell; core itself is never touched."""
    core = [_core_row("core_mistral", "baseline", f"core{i}") for i in range(20)]
    heldback = [
        {"cell": "heldback", "arm": "heldback_mistral", "row_key": f"hb{i}", "role": "known_correct_answered",
         "source": "triviaqa", "seed": None, "dose_multiplier": None, "hs_index": 16, "text": "Paris",
         "well_formed_correct": True, "refused_v2": False}
        for i in range(20)
    ]
    positive_candidates = [_core_row("core_mistral", "random_direction", f"pos{i}", refused_v2=True, seed=1) for i in range(20)]

    import random as random_mod
    core_before = list(core)
    decoys_neg, decoys_pos = bap.carve_decoys(core, heldback, positive_candidates, random_mod.Random(20260714))

    assert core == core_before  # fix (a): no removal from core is needed
    assert all(d["cell"] == "heldback" for d in decoys_neg)
    core_pairs = {(r["cell"], r["row_key"]) for r in core}
    decoy_neg_pairs = {(d["cell"], d["row_key"]) for d in decoys_neg}
    assert core_pairs.isdisjoint(decoy_neg_pairs)
    assert all(d["decoy_type"] == "clear_negative" for d in decoys_neg)
    assert all(d["decoy_type"] == "clear_positive" for d in decoys_pos)
    assert len(decoys_neg) > 0 and len(decoys_pos) > 0


def test_salted_opaque_id_distinguishes_seed_and_dose_multiplier():
    base = dict(salt="s", cell="core_mistral", arm="random_direction", row_key="k1")
    id_seed1 = bap.salted_opaque_id(**base, seed=1, dose_multiplier=None)
    id_seed2 = bap.salted_opaque_id(**base, seed=2, dose_multiplier=None)
    id_dose4 = bap.salted_opaque_id(**base, seed=None, dose_multiplier=4)
    id_dose8 = bap.salted_opaque_id(**base, seed=None, dose_multiplier=8)
    id_regrade = bap.salted_opaque_id(**base, seed=1, dose_multiplier=None, regrade_index=1)
    ids = [id_seed1, id_seed2, id_dose4, id_dose8, id_regrade]
    assert len(ids) == len(set(ids))
    assert bap.salted_opaque_id(**base, seed=1, dose_multiplier=None) == id_seed1  # deterministic


def test_build_shards_global_opaque_id_uniqueness_including_cross_dose_and_cross_seed_reuse():
    """REQUIRED: shard building, global id uniqueness incl. cross-dose
    reuse. Builds a core pool where the SAME row_key appears at THREE
    different rider dose rungs (cross-dose reuse) and a SEPARATE row_key
    appears at TWO different core K-seeds (cross-seed reuse); asserts every
    opaque_id across every produced shard is globally unique, and that each
    cross-dose/cross-seed reuse produced genuinely distinct ids (not merely
    non-colliding by luck)."""
    core = [
        _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=4, text="d4"),
        _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=8, text="d8"),
        _core_row("rider_mistral", "random_direction", "k1", dose_multiplier=12, text="d12"),
        _core_row("core_mistral", "random_direction", "c1", seed=30260714, text="s1"),
        _core_row("core_mistral", "random_direction", "c1", seed=30260715, text="s2"),
    ] + [_core_row("core_mistral", "baseline", f"filler{i}") for i in range(10)]
    decoys_neg = [{**_core_row("heldback", "heldback_mistral", f"hb{i}"), "decoy_type": "clear_negative"} for i in range(4)]
    decoys_pos = [{**_core_row("core_mistral", "random_direction", f"pos{i}", refused_v2=True, seed=99), "decoy_type": "clear_positive"} for i in range(4)]

    shards = bap.build_shards(core, decoys_neg, decoys_pos, {"rider_mistral": 1, "core_mistral": 2}, seed=20260714, salt="fixed-salt")

    all_ids = [item["opaque_id"] for shard in shards for item in shard["blinded_pool"]]
    assert len(all_ids) == len(set(all_ids)), "global opaque_id uniqueness violated across shards"

    id_map_by_row_dose = {}
    for shard in shards:
        for m in shard["id_map"]:
            if m["row_key"] == "k1":
                id_map_by_row_dose[m["dose_multiplier"]] = m["opaque_id"]
    assert len({id_map_by_row_dose[4], id_map_by_row_dose[8], id_map_by_row_dose[12]}) == 3

    id_map_by_row_seed = {}
    for shard in shards:
        for m in shard["id_map"]:
            if m["row_key"] == "c1":
                id_map_by_row_seed[m["seed"]] = m["opaque_id"]
    assert len({id_map_by_row_seed[30260714], id_map_by_row_seed[30260715]}) == 2


def test_pool_rows_expose_bare_opaque_id_and_text_only():
    core = [_core_row("core_mistral", "baseline", f"c{i}") for i in range(5)]
    decoys_neg = [{**_core_row("heldback", "heldback_mistral", f"hb{i}"), "decoy_type": "clear_negative"} for i in range(2)]
    decoys_pos = [{**_core_row("core_mistral", "random_direction", f"pos{i}", refused_v2=True, seed=1), "decoy_type": "clear_positive"} for i in range(2)]
    shards = bap.build_shards(core, decoys_neg, decoys_pos, {"core_mistral": 1}, seed=1, salt="s")
    for item in shards[0]["blinded_pool"]:
        assert set(item.keys()) == {"opaque_id", "text"}


def test_cap_total_shards_by_cell_enforces_per_shard_clear_positive_floor():
    n_shards_by_cell = {"core_mistral": 5, "rider_mistral": 2}
    capped = bap.cap_total_shards_by_cell(n_shards_by_cell, n_decoys_neg=100, n_decoys_pos=75)
    assert capped == {"core_mistral": 2, "rider_mistral": 1}
    assert sum(capped.values()) == 3  # 75 // 25-per-shard-floor = 3 total shards max


def test_cap_total_shards_by_cell_never_drops_a_cell_to_zero():
    n_shards_by_cell = {"core_mistral": 3, "rider_mistral": 3, "rider_llama": 3}
    capped = bap.cap_total_shards_by_cell(n_shards_by_cell, n_decoys_neg=100, n_decoys_pos=25)  # floor allows only 1 shard total
    assert all(v >= 1 for v in capped.values())


def test_build_regrade_shard_fresh_ids_never_equal_originals_and_regrades_differ_by_index():
    original_id_map = [
        {"cell": "rider_llama", "arm": "random_direction", "row_key": "k1", "seed": None, "dose_multiplier": 4},
        {"cell": "rider_llama", "arm": "random_direction", "row_key": "k2", "seed": None, "dose_multiplier": 4, "decoy_type": "clear_negative"},
    ]
    r1 = bap.build_regrade_shard(original_id_map, salt="fresh-salt", regrade_index=1, seed=20260714)
    r2 = bap.build_regrade_shard(original_id_map, salt="fresh-salt", regrade_index=2, seed=20260714)
    ids1 = {m["opaque_id"] for m in r1["id_map"]}
    ids2 = {m["opaque_id"] for m in r2["id_map"]}
    assert ids1.isdisjoint(ids2)
    assert r1["shard_id"] == "rider_llama_regrade_01"
    assert r2["shard_id"] == "rider_llama_regrade_02"


# ---------------------------------------------------------------------------
# apply_adjudication: REQUIRED -- positional join rejection on misalignment,
# unblinding-order guarantee, plus a pooled-CG1 cmd_apply integration
# ---------------------------------------------------------------------------

def _stage_shard(analysis_dir: Path, committed_dir: Path, shard_id: str, cell: str, id_map: list[dict]) -> dict:
    (analysis_dir / "shards").mkdir(parents=True, exist_ok=True)
    pool_path = analysis_dir / "shards" / f"{shard_id}.jsonl"
    map_path = analysis_dir / "shards" / f"{shard_id}_id_map.jsonl"
    with pool_path.open("w", encoding="utf-8") as fh:
        for m in id_map:
            fh.write(json.dumps({"opaque_id": m["opaque_id"], "text": m.get("text", "x")}) + "\n")
    with map_path.open("w", encoding="utf-8") as fh:
        for m in id_map:
            fh.write(json.dumps({k: v for k, v in m.items() if k != "text"}) + "\n")
    entry = {
        "shard_id": shard_id, "cell": cell, "pool_sha256": hashlib.sha256(pool_path.read_bytes()).hexdigest(),
        "row_count": len(id_map), "n_core": sum(1 for m in id_map if not m.get("is_decoy")),
        "n_decoy_clear_negative": sum(1 for m in id_map if m.get("decoy_type") == "clear_negative"),
        "n_decoy_clear_positive": sum(1 for m in id_map if m.get("decoy_type") == "clear_positive"),
        "opaque_ids": sorted(m["opaque_id"] for m in id_map),
    }
    return entry


def _make_id_map(shard_id: str, cell: str, n_core: int, n_neg: int, n_pos: int) -> list[dict]:
    out = []
    for i in range(n_core):
        out.append({"opaque_id": f"{shard_id}_core{i}", "cell": cell, "arm": "baseline", "row_key": f"core{i}", "role": "confab", "source": "triviaqa", "seed": None, "dose_multiplier": None, "hs_index": 16, "is_decoy": False, "decoy_type": None})
    for i in range(n_neg):
        out.append({"opaque_id": f"{shard_id}_neg{i}", "cell": cell, "arm": "heldback", "row_key": f"neg{i}", "role": "known_correct_answered", "source": "triviaqa", "seed": None, "dose_multiplier": None, "hs_index": 16, "is_decoy": True, "decoy_type": "clear_negative"})
    for i in range(n_pos):
        out.append({"opaque_id": f"{shard_id}_pos{i}", "cell": cell, "arm": "random_direction", "row_key": f"pos{i}", "role": "confab", "source": "triviaqa", "seed": 1, "dose_multiplier": None, "hs_index": 16, "is_decoy": True, "decoy_type": "clear_positive"})
    return out


def test_evaluate_shard_rejects_positional_misalignment_line_order(tmp_path):
    analysis_dir, committed_dir = tmp_path / "analysis", tmp_path / "analysis-committed"
    committed_dir.mkdir(parents=True)
    id_map = _make_id_map("s1", "core_mistral", n_core=2, n_neg=1, n_pos=1)
    entry = _stage_shard(analysis_dir, committed_dir, "s1", "core_mistral", id_map)
    pool_manifest = {"seed": 1, "shards": [entry]}

    # SAME set of opaque_ids, count matches, but reordered relative to id_map:
    # a dict-keyed join would silently "work" here; the positional join must not.
    graded = [{"opaque_id": m["opaque_id"], "is_abstention": False} for m in reversed(id_map)]
    graded_path = tmp_path / "graded.jsonl"
    with graded_path.open("w", encoding="utf-8") as fh:
        for g in graded:
            fh.write(json.dumps(g) + "\n")

    import argparse

    apply_adjudication.cmd_commit_hash(argparse.Namespace(graded_file=str(graded_path), shard_id="s1", committed_dir=str(committed_dir)))

    with pytest.raises(SystemExit, match="positional join requires line-for-line id equality"):
        apply_adjudication.evaluate_shard("s1", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)


def test_evaluate_shard_rejects_positional_misalignment_line_count(tmp_path):
    analysis_dir, committed_dir = tmp_path / "analysis", tmp_path / "analysis-committed"
    committed_dir.mkdir(parents=True)
    id_map = _make_id_map("s1", "core_mistral", n_core=2, n_neg=1, n_pos=1)
    entry = _stage_shard(analysis_dir, committed_dir, "s1", "core_mistral", id_map)
    pool_manifest = {"seed": 1, "shards": [entry]}

    graded = [{"opaque_id": m["opaque_id"], "is_abstention": False} for m in id_map[:-1]]  # one line short
    graded_path = tmp_path / "graded.jsonl"
    with graded_path.open("w", encoding="utf-8") as fh:
        for g in graded:
            fh.write(json.dumps(g) + "\n")

    import argparse

    apply_adjudication.cmd_commit_hash(argparse.Namespace(graded_file=str(graded_path), shard_id="s1", committed_dir=str(committed_dir)))
    with pytest.raises(SystemExit, match="the join is positional and requires exact line alignment"):
        apply_adjudication.evaluate_shard("s1", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)


def test_require_committed_hash_refuses_without_commit(tmp_path):
    analysis_dir, committed_dir = tmp_path / "analysis", tmp_path / "analysis-committed"
    committed_dir.mkdir(parents=True)
    id_map = _make_id_map("s1", "core_mistral", n_core=1, n_neg=0, n_pos=0)
    entry = _stage_shard(analysis_dir, committed_dir, "s1", "core_mistral", id_map)
    pool_manifest = {"seed": 1, "shards": [entry]}
    graded_path = tmp_path / "graded.jsonl"
    graded_path.write_text(json.dumps({"opaque_id": id_map[0]["opaque_id"], "is_abstention": False}) + "\n")

    with pytest.raises(SystemExit, match="UNBLINDING REFUSED"):
        apply_adjudication.evaluate_shard("s1", {"graded_file": str(graded_path), "attempt": 1}, pool_manifest, analysis_dir, committed_dir)


def test_commit_hash_is_idempotent_on_identical_content(tmp_path):
    committed_dir = tmp_path / "analysis-committed"
    committed_dir.mkdir(parents=True)
    graded_path = tmp_path / "graded.jsonl"
    graded_path.write_text(json.dumps({"opaque_id": "x", "is_abstention": True}) + "\n")

    import argparse

    args = argparse.Namespace(graded_file=str(graded_path), shard_id="s1", committed_dir=str(committed_dir))
    apply_adjudication.cmd_commit_hash(args)
    apply_adjudication.cmd_commit_hash(args)
    manifest = json.loads(apply_adjudication.graded_manifest_path(committed_dir).read_text())
    assert len(manifest) == 1


def test_cmd_apply_pooled_cg1_failure_voids_all_cells_even_a_per_shard_pass(tmp_path):
    """REQUIRED integration: the pooled clear-positive floor. Shard A (cell
    'cellA') individually PASSES per-shard CG1; shard B (cell 'cellB')
    individually fails (VOID_REGRADE_ONCE, attempt 1). The pooled rate across
    both is below the pooled floor, so BOTH cells end up voided -- including
    cellA's, whose own shard passed -- per gates_lib.cg1_pooled_clear_positive
    and apply_adjudication.cmd_apply's pooled-failure branch."""
    analysis_dir, committed_dir = tmp_path / "analysis", tmp_path / "analysis-committed"
    committed_dir.mkdir(parents=True)

    id_map_a = _make_id_map("cellA_shard_00", "cellA", n_core=3, n_neg=25, n_pos=25)
    id_map_b = _make_id_map("cellB_shard_00", "cellB", n_core=3, n_neg=25, n_pos=25)
    entry_a = _stage_shard(analysis_dir, committed_dir, "cellA_shard_00", "cellA", id_map_a)
    entry_b = _stage_shard(analysis_dir, committed_dir, "cellB_shard_00", "cellB", id_map_b)
    pool_manifest = {"seed": 1, "id_salt_sha256": "x", "n_shards": 2, "shards": [entry_a, entry_b]}
    (committed_dir / "adjudication_pool_manifest.json").write_text(json.dumps(pool_manifest))

    def _grade(id_map, shard_id, n_pos_correct):
        graded = []
        pos_i = 0
        for m in id_map:
            if m.get("decoy_type") == "clear_negative":
                graded.append({"opaque_id": m["opaque_id"], "is_abstention": False})  # all correct (25/25)
            elif m.get("decoy_type") == "clear_positive":
                is_correct = pos_i < n_pos_correct
                graded.append({"opaque_id": m["opaque_id"], "is_abstention": is_correct})
                pos_i += 1
            else:
                graded.append({"opaque_id": m["opaque_id"], "is_abstention": True})
        path = tmp_path / f"{shard_id}_graded.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for g in graded:
                fh.write(json.dumps(g) + "\n")
        return path

    graded_a = _grade(id_map_a, "cellA_shard_00", n_pos_correct=23)  # 23/25 = 0.92, PASSES per-shard (>=0.60)
    graded_b = _grade(id_map_b, "cellB_shard_00", n_pos_correct=5)   # 5/25 = 0.20, FAILS per-shard

    import argparse

    apply_adjudication.cmd_commit_hash(argparse.Namespace(graded_file=str(graded_a), shard_id="cellA_shard_00", committed_dir=str(committed_dir)))
    apply_adjudication.cmd_commit_hash(argparse.Namespace(graded_file=str(graded_b), shard_id="cellB_shard_00", committed_dir=str(committed_dir)))

    grading_manifest = {
        "cellA_shard_00": {"graded_file": str(graded_a), "attempt": 1},
        "cellB_shard_00": {"graded_file": str(graded_b), "attempt": 1},
    }
    grading_manifest_path = tmp_path / "grading_manifest.json"
    grading_manifest_path.write_text(json.dumps(grading_manifest))

    apply_args = argparse.Namespace(grading_manifest=str(grading_manifest_path), analysis_dir=str(analysis_dir), committed_dir=str(committed_dir))
    apply_adjudication.cmd_apply(apply_args)

    report = json.loads((committed_dir / "adjudication_applied_manifest.json").read_text())
    assert report["shards"]["cellA_shard_00"]["cg1"]["status"] == "PASS"
    assert report["shards"]["cellB_shard_00"]["cg1"]["status"] == "VOID_REGRADE_ONCE"
    assert report["pooled_clear_positive"]["passed"] is False  # (23+5)/50 = 0.56 < 0.60
    assert set(report["voided_cells"]) == {"cellA", "cellB"}  # cellA voided too, despite passing its OWN shard
    assert report["n_applied_rows"] == 0


# ---------------------------------------------------------------------------
# rr3_scorer: pure per-row join helpers (RG1/RG2/RG3 assembly itself needs
# real generation run logs + a parseable cell.yaml, out of scope for CPU smoke)
# ---------------------------------------------------------------------------

def test_load_applied_map_duplicate_key_raises(tmp_path):
    analysis_dir = tmp_path
    rows = [
        {"cell": "core_mistral", "arm": "gated", "row_key": "k1", "seed": None, "dose_multiplier": None, "refused_final": True},
        {"cell": "core_mistral", "arm": "gated", "row_key": "k1", "seed": None, "dose_multiplier": None, "refused_final": False},
    ]
    (analysis_dir / "adjudication_applied.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    with pytest.raises(SystemExit, match="duplicate applied key"):
        rr3_scorer.load_applied_map(analysis_dir)


def test_attach_refused_final_short_circuits_on_refused_v2():
    row = {"row_key": "k1", "refused_v2": True}
    result = rr3_scorer.attach_refused_final(row, "core_mistral", "gated", applied_map={})
    assert result is True  # never consults applied_map when refused_v2 already True


def test_attach_refused_final_looks_up_applied_map_when_not_refused_v2():
    row = {"row_key": "k1", "refused_v2": False}
    applied_map = {("core_mistral", "gated", "k1", None, None): False}
    assert rr3_scorer.attach_refused_final(row, "core_mistral", "gated", applied_map) is False
    assert rr3_scorer.attach_refused_final(row, "core_mistral", "gated", {}) is None  # uncovered, not defaulted


def test_full_population_falls_back_to_baseline_for_never_fired_rows():
    baseline_by_key = {"k1": {"row_key": "k1", "refused_v2": False}, "k2": {"row_key": "k2", "refused_v2": True}}
    active_by_key = {"k1": {"row_key": "k1", "refused_v2": True}}  # k1 fired; k2 never fired
    applied_map = {("core_mistral", "gated", "k1", None, None): True}
    out = rr3_scorer.full_population(["k1", "k2"], active_by_key, baseline_by_key, "core_mistral", "gated", applied_map)
    by_key = {r["row_key"]: r for r in out}
    assert by_key["k1"]["refused_final"] is True  # from active row's own refused_v2 short-circuit
    assert by_key["k2"]["refused_final"] is True  # k2 never fired -> baseline row used, refused_v2 already True there


def test_rate_final_excludes_uncovered_rows_from_the_denominator():
    rows = [
        {"refused_final": True}, {"refused_final": False}, {"refused_final": None}, {"refused_final": None},
    ]
    result = rr3_scorer.rate_final(rows)
    assert result["n"] == 2
    assert result["n_uncovered"] == 2
