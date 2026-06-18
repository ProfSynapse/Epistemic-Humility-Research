from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_causal_pilot_runner as runner  # noqa: E402


def test_generation_requires_explicit_allow_flag():
    config = {
        "spec": {"status": "generation_smoke"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "output": {"intervention_results_allowed_by_this_spec": True},
    }

    with pytest.raises(runner.PilotRunnerError, match="--allow-generation"):
        runner.require_generation_enabled(config, allow_generation=False)


def test_logit_diagnostic_requires_explicit_allow_flag():
    config = {
        "spec": {"status": "generation_smoke"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": True}},
        "output": {"intervention_results_allowed_by_this_spec": True},
    }

    with pytest.raises(runner.PilotRunnerError, match="--allow-logit-diagnostic"):
        runner.require_logit_diagnostic_enabled(config, allow_logit_diagnostic=False)


def test_readiness_config_is_not_live_generation_config():
    config = {
        "spec": {"status": "readiness_spec_only"},
        "model": {"enable_thinking": False},
        "first_smoke": {"initial_scope": {"generation_allowed_by_this_spec": False}},
        "output": {"intervention_results_allowed_by_this_spec": False},
    }

    with pytest.raises(runner.PilotRunnerError, match="generation_smoke"):
        runner.require_generation_enabled(config, allow_generation=True)


def test_hidden_state_layer_maps_to_decoder_block():
    assert runner.block_index_for_hidden_state_layer(36) == 35
    assert runner.block_index_for_hidden_state_layer(1) == 0
    with pytest.raises(runner.PilotRunnerError, match="layer 0"):
        runner.block_index_for_hidden_state_layer(0)


def test_final_prompt_hook_adds_once_to_last_prompt_token():
    torch = pytest.importorskip("torch")
    direction = torch.tensor([1.0, 2.0, 3.0])
    hook = runner.make_final_prompt_token_addition_hook(direction, 0.5)
    hidden = torch.zeros((1, 4, 3))

    out = hook(None, (), hidden)

    assert torch.equal(out[0, 0, :], torch.zeros(3))
    assert torch.equal(out[0, 3, :], torch.tensor([0.5, 1.0, 1.5]))
    assert hook._phase3_state["applied_count"] == 1
    assert hook._phase3_state["delta_abs_sum"] == 3.0

    out2 = hook(None, (), out)
    assert torch.equal(out2, out)
    assert hook._phase3_state["applied_count"] == 1


def test_select_balanced_rows_adds_aliases(tmp_path):
    extraction_rows = tmp_path / "rows.jsonl"
    rows = [
        {"probe_pool_row_key": "k1", "question": "Known?", "label": "known"},
        {"probe_pool_row_key": "u1", "question": "Unknown?", "label": "unknown"},
        {"probe_pool_row_key": "k2", "question": "Known 2?", "label": "known"},
        {"probe_pool_row_key": "u2", "question": "Unknown 2?", "label": "unknown"},
    ]
    extraction_rows.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    probe_results = tmp_path / "probe_results.jsonl"
    probe_results.write_text(
        "\n".join([
            json.dumps({"probe_pool_row_key": "k1", "normalized_aliases": ["paris"]}),
            json.dumps({"probe_pool_row_key": "u1", "normalized_aliases": []}),
        ])
        + "\n",
        encoding="utf-8",
    )

    selected = runner.select_balanced_rows(
        extraction_rows,
        max_rows=2,
        probe_results=probe_results,
    )

    assert [row["label"] for row in selected] == ["known", "unknown"]
    assert selected[0]["aliases"] == ["paris"]
    assert selected[1]["aliases"] == []


def test_score_generation_and_metrics():
    known = {"label": "known", "aliases": ["paris"]}
    unknown = {"label": "unknown", "aliases": []}
    rows = [
        {
            "arm_id": "baseline",
            "label": "known",
            **runner.score_generation(known, "Paris"),
        },
        {
            "arm_id": "baseline",
            "label": "unknown",
            **runner.score_generation(unknown, "I do not know"),
        },
    ]

    metrics = runner.summarize_metrics(rows)

    assert metrics["baseline"]["truthful_rate"] == 100.0
    assert metrics["baseline"]["known_answer_correctness"] == 100.0
    assert metrics["baseline"]["unknown_refusal_rate"] == 100.0
    assert metrics["baseline"]["thinking_tag_contamination_count"] == 0
    assert metrics["baseline"]["per_row_delta_vs_no_vector"]["truthful_changed"] == 0


def test_metrics_report_row_deltas_against_baseline():
    rows = [
        {
            "arm_id": "baseline",
            "control": "no_vector_baseline",
            "probe_pool_row_key": "u1",
            "label": "unknown",
            "generated_answer": "I do not know",
            "refused": True,
            "correct": False,
            "truthful": True,
        },
        {
            "arm_id": "intervention",
            "control": "activation_addition",
            "probe_pool_row_key": "u1",
            "label": "unknown",
            "generated_answer": "Paris",
            "refused": False,
            "correct": False,
            "truthful": False,
        },
    ]

    metrics = runner.summarize_metrics(rows)

    delta = metrics["intervention"]["per_row_delta_vs_no_vector"]
    assert delta["n_joined"] == 1
    assert delta["refusal_changed"] == 1
    assert delta["truthful_changed"] == 1


def test_build_smoke_arms_sets_zero_baseline_direction_to_none():
    candidate = {
        "label": "candidate",
        "direction_id": "direction__x",
        "layer": 3,
        "role": "h_lora",
    }

    arms = runner.build_smoke_arms(
        candidate=candidate,
        coefficients=[0.0, 1.0],
        controls=["no_vector_baseline", "activation_addition", "activation_subtraction"],
    )

    baseline = [arm for arm in arms if arm["control"] == "no_vector_baseline"]
    assert all(arm["coefficient"] == 0.0 for arm in baseline)
    assert all(arm["direction_id"] is None for arm in baseline)
    additions = [arm for arm in arms if arm["control"] == "activation_addition"]
    subtractions = [arm for arm in arms if arm["control"] == "activation_subtraction"]
    assert all(arm["coefficient"] >= 0.0 for arm in additions)
    assert all(arm["coefficient"] <= 0.0 for arm in subtractions)


def test_unsupported_live_control_fails_closed():
    with pytest.raises(runner.PilotRunnerError, match="Unsupported live control"):
        runner.effective_coefficient_for_control("random_direction", 1.0)


def test_unsupported_logit_diagnostic_control_fails_closed():
    with pytest.raises(runner.PilotRunnerError, match="Unsupported logit diagnostic control"):
        runner.effective_coefficient_for_logit_diagnostic_control("sign_flip", 1.0)


def test_logit_diagnostic_controls_require_baseline_first():
    runner.validate_logit_diagnostic_controls([
        "no_vector_baseline",
        "activation_addition",
        "activation_subtraction",
    ])

    with pytest.raises(runner.PilotRunnerError, match="must include no_vector_baseline"):
        runner.validate_logit_diagnostic_controls(["activation_addition"])

    with pytest.raises(runner.PilotRunnerError, match="first control"):
        runner.validate_logit_diagnostic_controls([
            "activation_addition",
            "no_vector_baseline",
        ])


def test_run_grid_requires_non_empty_coefficients_and_controls():
    runner.validate_non_empty_run_grid([1.0], ["no_vector_baseline"])

    with pytest.raises(runner.PilotRunnerError, match="At least one coefficient"):
        runner.validate_non_empty_run_grid([], ["no_vector_baseline"])

    with pytest.raises(runner.PilotRunnerError, match="At least one control"):
        runner.validate_non_empty_run_grid([1.0], [])


def test_logit_diagnostic_row_overrides_generation_metadata():
    row = {"probe_pool_row_key": "k1", "question": "Known?", "label": "known"}
    arm = {
        "arm_id": "candidate__coef_1p0__control_activation_addition",
        "control": "activation_addition",
        "generation_executed": True,
    }
    metrics = {
        "max_abs_logit_delta": 1.0,
        "l2_logit_delta": 2.0,
        "top1_changed": True,
    }

    diagnostic_row = runner.build_logit_diagnostic_row(
        row=row,
        arm=arm,
        metrics=metrics,
        hook_state={"applied_count": 1, "delta_abs_sum": 3.5},
    )

    assert diagnostic_row["generation_executed"] is False
    assert diagnostic_row["logit_diagnostic_executed"] is True
    assert diagnostic_row["intervention_applied_count"] == 1
    assert diagnostic_row["intervention_delta_abs_sum"] == 3.5
    assert diagnostic_row["control"] == "activation_addition"
    assert diagnostic_row["top1_changed"] is True


def test_next_token_logit_metrics_report_movement_and_top1_change():
    torch = pytest.importorskip("torch")

    class Tokenizer:
        def decode(self, token_ids, skip_special_tokens=False):
            return {0: " A", 1: " B", 2: " C"}[token_ids[0]]

    metrics = runner.compute_next_token_logit_metrics(
        baseline_logits=torch.tensor([3.0, 1.0, 0.0]),
        intervention_logits=torch.tensor([1.0, 4.0, -1.0]),
        tokenizer=Tokenizer(),
    )

    assert metrics["max_abs_logit_delta"] == 3.0
    assert metrics["l2_logit_delta"] == pytest.approx(3.741657, rel=1e-6)
    assert metrics["baseline_top1_token_id"] == 0
    assert metrics["baseline_top1_text"] == " A"
    assert metrics["intervention_top1_token_id"] == 1
    assert metrics["intervention_top1_text"] == " B"
    assert metrics["top1_changed"] is True


def test_next_token_logit_metrics_require_matching_shapes():
    torch = pytest.importorskip("torch")

    with pytest.raises(runner.PilotRunnerError, match="Logit shape mismatch"):
        runner.compute_next_token_logit_metrics(
            baseline_logits=torch.tensor([1.0, 2.0]),
            intervention_logits=torch.tensor([1.0, 2.0, 3.0]),
            tokenizer=SimpleNamespace(decode=lambda *_args, **_kwargs: ""),
        )


def test_summarize_logit_metrics_groups_by_arm():
    rows = [
        {
            "arm_id": "baseline",
            "top1_changed": False,
            "max_abs_logit_delta": 0.0,
            "l2_logit_delta": 0.0,
            "intervention_applied_count": 1,
            "intervention_delta_abs_sum": 0.0,
        },
        {
            "arm_id": "add",
            "top1_changed": True,
            "max_abs_logit_delta": 3.0,
            "l2_logit_delta": 4.0,
            "intervention_applied_count": 1,
            "intervention_delta_abs_sum": 10.0,
        },
        {
            "arm_id": "add",
            "top1_changed": False,
            "max_abs_logit_delta": 1.0,
            "l2_logit_delta": 2.0,
            "intervention_applied_count": 1,
            "intervention_delta_abs_sum": 6.0,
        },
    ]

    metrics = runner.summarize_logit_metrics(rows)

    assert metrics["baseline"]["top1_changed_rate"] == 0.0
    assert metrics["add"]["top1_changed_count"] == 1
    assert metrics["add"]["top1_changed_rate"] == 50.0
    assert metrics["add"]["max_abs_logit_delta_max"] == 3.0
    assert metrics["add"]["max_abs_logit_delta_mean"] == 2.0
    assert metrics["add"]["l2_logit_delta_mean"] == 3.0
    assert metrics["add"]["intervention_applied_count_total"] == 2
    assert metrics["add"]["intervention_delta_abs_sum_mean"] == 8.0


def test_validated_candidate_merge_preserves_raw_paths():
    raw = {
        "label": "candidate",
        "extraction_dir": "raw/extraction",
        "direction_file": "raw/direction.safetensors",
    }
    validated = {
        "label": "candidate",
        "row_count": 2,
        "direction_file": "/abs/direction.safetensors",
    }

    merged = {**raw, **validated}

    assert merged["extraction_dir"] == "raw/extraction"
    assert merged["direction_file"] == "/abs/direction.safetensors"
