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


def test_multi_layer_activation_hooks_apply_each_component_once():
    torch = pytest.importorskip("torch")

    class IdentityLayer(torch.nn.Module):
        def forward(self, hidden):
            return hidden

    model = torch.nn.Module()
    model.layers = torch.nn.ModuleList([IdentityLayer(), IdentityLayer(), IdentityLayer()])
    hidden = torch.zeros((1, 2, 3))
    components = [
        {"layer": 1, "direction": torch.tensor([1.0, 0.0, 0.0]), "coefficient": 2.0},
        {"layer": 3, "direction": torch.tensor([0.0, 1.0, 0.0]), "coefficient": -3.0},
    ]

    with runner.activation_addition_hooks(model, components) as state:
        out = hidden
        for layer in model.layers:
            out = layer(out)

    assert torch.equal(out[0, 0, :], torch.zeros(3))
    assert torch.equal(out[0, 1, :], torch.tensor([2.0, -3.0, 0.0]))
    assert state["applied_count"] == 2
    assert state["delta_abs_sum"] == 5.0
    assert [component["layer"] for component in state["component_states"]] == [1, 3]


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


def test_select_exact_row_keys_preserves_order_and_adds_aliases(tmp_path):
    extraction_rows = tmp_path / "rows.jsonl"
    rows = [
        {"probe_pool_row_key": "k1", "question": "Known?", "label": "known"},
        {"probe_pool_row_key": "u1", "question": "Unknown?", "label": "unknown"},
        {"probe_pool_row_key": "k2", "question": "Known 2?", "label": "known"},
    ]
    extraction_rows.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    probe_results = tmp_path / "probe_results.jsonl"
    probe_results.write_text(
        "\n".join([
            json.dumps({
                "probe_pool_row_key": "k2",
                "normalized_aliases": ["rome"],
                "answer_value": "Rome",
            }),
            json.dumps({
                "probe_pool_row_key": "u1",
                "normalized_aliases": [],
                "answer_value": "Unknown",
            }),
        ])
        + "\n",
        encoding="utf-8",
    )

    selected = runner.select_balanced_rows(
        extraction_rows,
        max_rows=1,
        probe_results=probe_results,
        row_keys=["k2", "u1"],
    )

    assert [row["probe_pool_row_key"] for row in selected] == ["k2", "u1"]
    assert [row["label"] for row in selected] == ["known", "unknown"]
    assert selected[0]["aliases"] == ["rome"]
    assert selected[0]["answer_value"] == "Rome"
    assert selected[1]["aliases"] == []


def test_select_exact_row_keys_fails_closed(tmp_path):
    extraction_rows = tmp_path / "rows.jsonl"
    extraction_rows.write_text(
        json.dumps({"probe_pool_row_key": "k1", "question": "Known?", "label": "known"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(runner.PilotRunnerError, match="missing from extraction rows"):
        runner.select_balanced_rows(extraction_rows, max_rows=16, row_keys=["missing"])

    with pytest.raises(runner.PilotRunnerError, match="duplicates"):
        runner.select_balanced_rows(extraction_rows, max_rows=16, row_keys=["k1", "k1"])


def test_select_rows_rejects_duplicate_extraction_keys(tmp_path):
    extraction_rows = tmp_path / "rows.jsonl"
    extraction_rows.write_text(
        "\n".join([
            json.dumps({"probe_pool_row_key": "k1", "question": "Known?", "label": "known"}),
            json.dumps({"probe_pool_row_key": "k1", "question": "Known again?", "label": "known"}),
        ])
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(runner.PilotRunnerError, match="Duplicate probe_pool_row_key 'k1'"):
        runner.select_balanced_rows(extraction_rows, max_rows=16)


def test_select_rows_rejects_duplicate_probe_result_keys(tmp_path):
    extraction_rows = tmp_path / "rows.jsonl"
    extraction_rows.write_text(
        json.dumps({"probe_pool_row_key": "k1", "question": "Known?", "label": "known"}) + "\n",
        encoding="utf-8",
    )
    probe_results = tmp_path / "probe_results.jsonl"
    probe_results.write_text(
        "\n".join([
            json.dumps({"probe_pool_row_key": "k1", "normalized_aliases": ["paris"]}),
            json.dumps({"probe_pool_row_key": "k1", "normalized_aliases": ["city of paris"]}),
        ])
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(runner.PilotRunnerError, match="Duplicate probe_pool_row_key 'k1'"):
        runner.select_balanced_rows(
            extraction_rows,
            max_rows=16,
            probe_results=probe_results,
        )


def test_runtime_adapter_path_defaults_to_extraction_manifest():
    model_cfg = {"adapter_path": None}
    extraction_manifest = {"adapter_path": "/workspace/repo/runs/adapter"}

    assert runner.runtime_adapter_path(model_cfg, extraction_manifest).endswith("runs\\adapter") or (
        runner.runtime_adapter_path(model_cfg, extraction_manifest).endswith("runs/adapter")
    )


def test_runtime_adapter_path_allows_explicit_adapterless_runtime():
    model_cfg = {
        "adapter_path": None,
        "use_extraction_adapter": False,
        "allow_adapterless": True,
    }
    extraction_manifest = {"adapter_path": "/workspace/repo/runs/adapter"}

    assert runner.runtime_adapter_path(model_cfg, extraction_manifest) is None


def test_runtime_adapter_path_fails_closed_without_adapter():
    with pytest.raises(runner.PilotRunnerError, match="allow_adapterless"):
        runner.runtime_adapter_path(
            {"adapter_path": None, "use_extraction_adapter": False},
            {"adapter_path": "/workspace/repo/runs/adapter"},
        )

    with pytest.raises(runner.PilotRunnerError, match="boolean"):
        runner.runtime_adapter_path(
            {"use_extraction_adapter": "no"},
            {"adapter_path": "/workspace/repo/runs/adapter"},
        )


def test_selection_row_keys_for_candidate_prefers_candidate_specific_keys():
    config = {
        "selection": {
            "row_keys": ["global"],
            "row_keys_by_candidate": {
                "cand_a": ["a1", "a2"],
            },
        }
    }

    assert runner.selection_row_keys_for_candidate(config, "cand_a") == ["a1", "a2"]
    assert runner.selection_row_keys_for_candidate(config, "cand_b") == ["global"]


def test_selection_row_keys_for_candidate_reads_row_keys_file(tmp_path):
    row_keys_file = tmp_path / "row_keys.txt"
    row_keys_file.write_text(
        "\n".join(
            [
                "# fixed behavior cells",
                "row-a",
                "",
                "row-b",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = {"selection": {"row_keys_file": str(row_keys_file)}}

    assert runner.selection_row_keys_for_candidate(config, "cand") == ["row-a", "row-b"]


def test_selection_row_keys_for_candidate_rejects_duplicate_row_keys_file(tmp_path):
    row_keys_file = tmp_path / "row_keys.txt"
    row_keys_file.write_text("row-a\nrow-a\n", encoding="utf-8")
    config = {"selection": {"row_keys_file": str(row_keys_file)}}

    with pytest.raises(runner.PilotRunnerError, match="must not contain duplicates"):
        runner.selection_row_keys_for_candidate(config, "cand")


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


def test_build_smoke_arms_adds_wrong_layer_and_random_provenance():
    candidate = {
        "label": "candidate",
        "direction_id": "direction__x",
        "layer": 10,
        "role": "h_lora",
    }

    arms = runner.build_smoke_arms(
        candidate=candidate,
        coefficients=[50.0],
        controls=["wrong_layer", "random_matched_norm"],
        control_settings={
            "wrong_layer": {"layer_offset": -2},
            "random_matched_norm": {"seed": 1234},
        },
    )

    wrong_layer = arms[0]
    assert wrong_layer["control"] == "wrong_layer"
    assert wrong_layer["source_layer"] == 10
    assert wrong_layer["layer"] == 8
    assert wrong_layer["coefficient"] == 50.0
    assert wrong_layer["direction_id"] == "direction__x"
    assert wrong_layer["control_provenance"] == {
        "control_type": "wrong_layer",
        "source_direction_id": "direction__x",
        "source_layer": 10,
        "source_layers": [10],
        "wrong_layer_offset": -2,
        "applied_layer": 8,
        "applied_layers": [8],
        "uses_source_direction": True,
    }

    random_control = arms[1]
    assert random_control["control"] == "random_matched_norm"
    assert random_control["layer"] == 10
    assert random_control["random_seed"] == 1234
    assert random_control["direction_id"] == "random_matched_norm_seed_1234"
    assert random_control["control_provenance"] == {
        "control_type": "random_matched_norm",
        "source_direction_id": "direction__x",
        "source_layer": 10,
        "source_layers": [10],
        "random_seed": 1234,
        "matched_norm_source_direction_id": "direction__x",
        "matched_norm_source_layer": 10,
        "matched_norm_source_layers": [10],
    }


def test_build_smoke_arms_tracks_multi_layer_source_and_wrong_layers():
    candidate = {
        "label": "multi",
        "direction_id": "multi__x",
        "role": "h_lora",
        "multi_layer_components": [
            {"layer": 27, "direction_id": "a", "direction_file": "a.safetensors"},
            {"layer": 36, "direction_id": "b", "direction_file": "b.safetensors"},
        ],
    }

    arms = runner.build_smoke_arms(
        candidate=candidate,
        coefficients=[50.0],
        controls=["wrong_layer"],
        control_settings={"wrong_layer": {"layer_offset": -2}},
    )

    assert len(arms) == 1
    arm = arms[0]
    assert arm["source_layers"] == [27, 36]
    assert arm["wrong_layer_offset"] == -2
    assert arm["control_provenance"]["applied_layers"] == [25, 34]
    assert arm["layer"] == 25


def test_build_smoke_arms_expands_random_matched_norm_seed_panel():
    candidate = {
        "label": "candidate",
        "direction_id": "direction__x",
        "layer": 10,
        "role": "h_lora",
    }

    arms = runner.build_smoke_arms(
        candidate=candidate,
        coefficients=[50.0],
        controls=["random_matched_norm"],
        control_settings={"random_matched_norm": {"seeds": [11, 22, 33]}},
    )

    assert [arm["arm_id"] for arm in arms] == [
        "candidate__coef_50p0__control_random_matched_norm__seed_11",
        "candidate__coef_50p0__control_random_matched_norm__seed_22",
        "candidate__coef_50p0__control_random_matched_norm__seed_33",
    ]
    assert [arm["random_seed"] for arm in arms] == [11, 22, 33]
    assert [arm["direction_id"] for arm in arms] == [
        "random_matched_norm_seed_11",
        "random_matched_norm_seed_22",
        "random_matched_norm_seed_33",
    ]


def test_random_matched_norm_seed_panel_fails_closed():
    with pytest.raises(runner.PilotRunnerError, match="non-empty list"):
        runner.random_matched_norm_seeds({"random_matched_norm": {"seeds": []}})

    with pytest.raises(runner.PilotRunnerError, match="non-negative integers"):
        runner.random_matched_norm_seeds({"random_matched_norm": {"seeds": [1, -1]}})

    with pytest.raises(runner.PilotRunnerError, match="duplicates"):
        runner.random_matched_norm_seeds({"random_matched_norm": {"seeds": [1, 1]}})


def test_build_smoke_arms_adds_wrong_layer_subtraction_provenance():
    candidate = {
        "label": "candidate",
        "direction_id": "direction__x",
        "layer": 10,
        "role": "h_lora",
    }

    arms = runner.build_smoke_arms(
        candidate=candidate,
        coefficients=[50.0, -50.0],
        controls=["wrong_layer_subtraction"],
        control_settings={"wrong_layer": {"layer_offset": 1}},
    )

    assert [arm["coefficient"] for arm in arms] == [-50.0, -50.0]
    for arm in arms:
        assert arm["control"] == "wrong_layer_subtraction"
        assert arm["source_layer"] == 10
        assert arm["layer"] == 11
        assert arm["direction_id"] == "direction__x"
        assert arm["control_provenance"] == {
            "control_type": "wrong_layer_subtraction",
            "source_direction_id": "direction__x",
            "source_layer": 10,
            "source_layers": [10],
            "wrong_layer_offset": 1,
            "applied_layer": 11,
            "applied_layers": [11],
            "uses_source_direction": True,
        }


def test_build_smoke_arms_expands_wrong_layer_offset_panel():
    candidate = {
        "label": "candidate",
        "direction_id": "direction__x",
        "layer": 10,
        "role": "h_lora",
    }

    arms = runner.build_smoke_arms(
        candidate=candidate,
        coefficients=[50.0],
        controls=["wrong_layer"],
        control_settings={"wrong_layer": {"layer_offsets": [-2, -1, 1, 2]}},
    )

    assert [arm["layer"] for arm in arms] == [8, 9, 11, 12]
    assert [arm["control_provenance"]["wrong_layer_offset"] for arm in arms] == [
        -2,
        -1,
        1,
        2,
    ]
    assert [arm["arm_id"] for arm in arms] == [
        "candidate__coef_50p0__control_wrong_layer__offset_neg_2",
        "candidate__coef_50p0__control_wrong_layer__offset_neg_1",
        "candidate__coef_50p0__control_wrong_layer__offset_1",
        "candidate__coef_50p0__control_wrong_layer__offset_2",
    ]


def test_wrong_layer_and_random_settings_fail_closed():
    with pytest.raises(runner.PilotRunnerError, match="nonzero integer"):
        runner.wrong_layer_offset({"wrong_layer": {"layer_offset": 0}})
    with pytest.raises(runner.PilotRunnerError, match="layer_offsets"):
        runner.wrong_layer_offsets({"wrong_layer": {"layer_offsets": []}})
    with pytest.raises(runner.PilotRunnerError, match="layer_offsets"):
        runner.wrong_layer_offsets({"wrong_layer": {"layer_offsets": [-1, -1]}})
    with pytest.raises(runner.PilotRunnerError, match="layer_offsets"):
        runner.wrong_layer_offsets({"wrong_layer": {"layer_offsets": [-1, 0]}})
    with pytest.raises(runner.PilotRunnerError, match="seed is required"):
        runner.random_matched_norm_seed({"random_matched_norm": {}})
    with pytest.raises(runner.PilotRunnerError, match="non-negative integer"):
        runner.random_matched_norm_seed({"random_matched_norm": {"seed": -1}})


def test_random_matched_norm_direction_is_deterministic_and_norm_matched():
    torch = pytest.importorskip("torch")
    direction = torch.tensor([3.0, 4.0, 0.0], dtype=torch.float32)

    first = runner.random_matched_norm_direction(direction, seed=99)
    second = runner.random_matched_norm_direction(direction, seed=99)
    other = runner.random_matched_norm_direction(direction, seed=100)

    assert torch.equal(first, second)
    assert not torch.equal(first, other)
    assert torch.linalg.vector_norm(first).item() == pytest.approx(
        torch.linalg.vector_norm(direction).item()
    )
    assert first.shape == direction.shape
    assert first.dtype == direction.dtype


def test_unsupported_live_control_fails_closed():
    with pytest.raises(runner.PilotRunnerError, match="Unsupported live control"):
        runner.effective_coefficient_for_control("random_direction", 1.0)


def test_unsupported_logit_diagnostic_control_fails_closed():
    with pytest.raises(runner.PilotRunnerError, match="Unsupported logit diagnostic control"):
        runner.effective_coefficient_for_logit_diagnostic_control("sign_flip", 1.0)
    with pytest.raises(runner.PilotRunnerError, match="Unsupported logit diagnostic control"):
        runner.effective_coefficient_for_logit_diagnostic_control("shuffled_label", 1.0)


def test_generation_controls_reject_logit_only_controls():
    runner.validate_generation_controls([
        "no_vector_baseline",
        "activation_addition",
        "activation_subtraction",
    ])

    with pytest.raises(runner.PilotRunnerError, match="logit-diagnostic-only"):
        runner.validate_generation_controls(["wrong_layer"])

    with pytest.raises(runner.PilotRunnerError, match="logit-diagnostic-only"):
        runner.validate_generation_controls(["wrong_layer_subtraction"])

    with pytest.raises(runner.PilotRunnerError, match="logit-diagnostic-only"):
        runner.validate_generation_controls(["random_matched_norm"])


def test_new_logit_diagnostic_controls_are_supported():
    assert runner.effective_coefficient_for_logit_diagnostic_control("wrong_layer", 5.0) == 5.0
    assert runner.effective_coefficient_for_logit_diagnostic_control("wrong_layer_subtraction", 5.0) == -5.0
    assert runner.effective_coefficient_for_logit_diagnostic_control("wrong_layer_subtraction", -5.0) == -5.0
    assert runner.effective_coefficient_for_logit_diagnostic_control("random_matched_norm", 5.0) == 5.0


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
        top_k=2,
    )

    assert metrics["max_abs_logit_delta"] == 3.0
    assert metrics["l2_logit_delta"] == pytest.approx(3.741657, rel=1e-6)
    assert metrics["baseline_top1_token_id"] == 0
    assert metrics["baseline_top1_text"] == " A"
    assert metrics["intervention_top1_token_id"] == 1
    assert metrics["intervention_top1_text"] == " B"
    assert metrics["top1_changed"] is True
    assert metrics["top_k"] == 2
    assert metrics["baseline_top_k"] == [
        {
            "rank": 1,
            "token_id": 0,
            "token_text": " A",
            "logit": 3.0,
            "probability": pytest.approx(0.8437947),
        },
        {
            "rank": 2,
            "token_id": 1,
            "token_text": " B",
            "logit": 1.0,
            "probability": pytest.approx(0.1141952),
        },
    ]
    assert metrics["intervention_top_k"][0]["token_id"] == 1
    assert metrics["intervention_top_k"][0]["token_text"] == " B"
    assert metrics["intervention_top_k"][0]["probability"] == pytest.approx(0.9464991)


def test_next_token_logit_metrics_include_configured_target_slices():
    torch = pytest.importorskip("torch")

    class Tokenizer:
        def decode(self, token_ids, skip_special_tokens=False):
            return {0: " I", 1: " Paris", 2: " Sorry"}[token_ids[0]]

    logit_targets = [{
        "name": "refusal_openers",
        "source": "static_strings",
        "token_ids": [0, 2],
        "token_texts": [" I", " Sorry"],
        "resolved_targets": [
            {"source_string": "I", "resolved_string": " I", "first_token_id": 0},
            {"source_string": "Sorry", "resolved_string": " Sorry", "first_token_id": 2},
        ],
    }]

    metrics = runner.compute_next_token_logit_metrics(
        baseline_logits=torch.tensor([2.0, 1.0, 0.0]),
        intervention_logits=torch.tensor([3.0, 1.0, 2.0]),
        tokenizer=Tokenizer(),
        logit_targets=logit_targets,
    )

    target_metrics = metrics["logit_target_metrics"]["refusal_openers"]
    baseline_probs = torch.softmax(torch.tensor([2.0, 1.0, 0.0]), dim=0)
    intervention_probs = torch.softmax(torch.tensor([3.0, 1.0, 2.0]), dim=0)
    assert target_metrics["baseline_probability_sum"] == pytest.approx(
        float(baseline_probs[[0, 2]].sum().item())
    )
    assert target_metrics["intervention_probability_sum"] == pytest.approx(
        float(intervention_probs[[0, 2]].sum().item())
    )
    assert target_metrics["probability_sum_delta"] == pytest.approx(
        float(intervention_probs[[0, 2]].sum().item() - baseline_probs[[0, 2]].sum().item())
    )
    assert target_metrics["baseline_logit_sum"] == 2.0
    assert target_metrics["intervention_logit_sum"] == 5.0
    assert target_metrics["logit_sum_delta"] == 3.0
    assert target_metrics["resolved_token_ids"] == [0, 2]
    assert target_metrics["resolved_token_texts"] == [" I", " Sorry"]


def test_next_token_logit_metrics_omit_target_slices_when_unconfigured():
    torch = pytest.importorskip("torch")

    metrics = runner.compute_next_token_logit_metrics(
        baseline_logits=torch.tensor([1.0, 2.0]),
        intervention_logits=torch.tensor([1.5, 1.0]),
        tokenizer=SimpleNamespace(decode=lambda token_ids, **_kwargs: str(token_ids[0])),
    )

    assert "logit_target_metrics" not in metrics


def test_next_token_logit_metrics_require_matching_shapes():
    torch = pytest.importorskip("torch")

    with pytest.raises(runner.PilotRunnerError, match="Logit shape mismatch"):
        runner.compute_next_token_logit_metrics(
            baseline_logits=torch.tensor([1.0, 2.0]),
            intervention_logits=torch.tensor([1.0, 2.0, 3.0]),
            tokenizer=SimpleNamespace(decode=lambda *_args, **_kwargs: ""),
        )


def test_logit_diagnostic_top_k_config_validation():
    assert runner.logit_diagnostic_top_k({}) == 5
    assert runner.logit_diagnostic_top_k({"logit_diagnostic": {"top_k": 10}}) == 10
    with pytest.raises(runner.PilotRunnerError, match="top_k"):
        runner.logit_diagnostic_top_k({"logit_diagnostic": {"top_k": 0}})
    with pytest.raises(runner.PilotRunnerError, match="top_k"):
        runner.logit_diagnostic_top_k({"logit_diagnostic": {"top_k": True}})


def test_resolve_logit_targets_accepts_conservative_schema_and_first_token_ids():
    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return {
                "I": [10],
                " I": [11],
                "Sorry": [12],
                " Sorry": [13],
                "I don't": [10, 14],
                " I don't": [11, 14],
            }[text]

        def decode(self, token_ids, skip_special_tokens=False):
            return {
                10: "I",
                11: " I",
                12: "Sorry",
                13: " Sorry",
                14: " don't",
            }[token_ids[0]]

    resolved = runner.resolve_logit_targets(
        {
            "logit_targets": {
                "groups": [{
                    "name": "refusal_openers",
                    "strings": ["I", "Sorry", "I don't"],
                    "include_leading_space_variants": True,
                }]
            }
        },
        Tokenizer(),
    )

    assert resolved[0]["name"] == "refusal_openers"
    assert resolved[0]["token_ids"] == [10, 11, 12, 13]
    assert resolved[0]["token_texts"] == ["I", " I", "Sorry", " Sorry"]
    multi_token = [
        item for item in resolved[0]["resolved_targets"]
        if item["resolved_string"] == "I don't"
    ][0]
    assert multi_token["token_ids"] == [10, 14]
    assert multi_token["first_token_id"] == 10
    assert multi_token["used_first_token_only"] is True


def test_resolve_logit_targets_accepts_row_alias_source():
    resolved = runner.resolve_logit_targets(
        {
            "logit_targets": {
                "groups": [{
                    "name": "answer_aliases",
                    "source": "row_aliases",
                    "include_leading_space_variants": True,
                }]
            }
        },
        SimpleNamespace(),
    )

    assert resolved == [{
        "name": "answer_aliases",
        "source": "row_aliases",
        "strings": [],
        "include_leading_space_variants": True,
        "include_multi_token_first_token": False,
        "token_ids": [],
        "token_texts": [],
        "resolved_targets": [],
        "skipped_targets": [],
    }]


def test_resolve_logit_targets_accepts_row_field_source():
    resolved = runner.resolve_logit_targets(
        {
            "logit_targets": {
                "groups": [{
                    "name": "wrong_hint_answer",
                    "source": "row_field",
                    "field_path": "sycophancy.incorrect_answer",
                    "include_leading_space_variants": True,
                    "include_multi_token_first_token": True,
                }]
            }
        },
        SimpleNamespace(),
    )

    assert resolved == [{
        "name": "wrong_hint_answer",
        "source": "row_field",
        "field_path": "sycophancy.incorrect_answer",
        "strings": [],
        "include_leading_space_variants": True,
        "include_multi_token_first_token": True,
        "token_ids": [],
        "token_texts": [],
        "resolved_targets": [],
        "skipped_targets": [],
    }]


def test_resolve_row_logit_targets_expands_answer_aliases_for_known_rows():
    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return {
                "Paris": [1],
                " Paris": [2],
                "City of Paris": [3, 4, 5],
                " City of Paris": [6, 4, 5],
            }[text]

        def decode(self, token_ids, skip_special_tokens=False):
            return {
                1: "Paris",
                2: " Paris",
                3: "City",
                4: " of",
                5: " Paris",
                6: " City",
            }[token_ids[0]]

    targets = [{
        "name": "answer_aliases",
        "source": "row_aliases",
        "strings": [],
        "include_leading_space_variants": True,
        "token_ids": [],
        "token_texts": [],
        "resolved_targets": [],
    }]

    resolved = runner.resolve_row_logit_targets(
        row={
            "label": "known",
            "aliases": ["Paris", "City of Paris"],
            "answer_value": "Paris",
        },
        logit_targets=targets,
        tokenizer=Tokenizer(),
    )

    assert resolved[0]["name"] == "answer_aliases"
    assert resolved[0]["source"] == "row_aliases"
    assert resolved[0]["token_ids"] == [1, 2]
    skipped_multi_token = [
        item for item in resolved[0]["skipped_targets"]
        if item["resolved_string"] == "City of Paris"
    ][0]
    assert skipped_multi_token["skip_reason"] == "multi_token_target"


def test_resolve_row_logit_targets_expands_row_field_value():
    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return {
                "Roald Dahl": [1, 2],
                " Roald Dahl": [3, 2],
            }[text]

        def decode(self, token_ids, skip_special_tokens=False):
            return {1: "Roald", 2: " Dahl", 3: " Roald"}[token_ids[0]]

    targets = [{
        "name": "wrong_hint_answer",
        "source": "row_field",
        "field_path": "sycophancy.incorrect_answer",
        "strings": [],
        "include_leading_space_variants": True,
        "include_multi_token_first_token": True,
        "token_ids": [],
        "token_texts": [],
        "resolved_targets": [],
        "skipped_targets": [],
    }]

    resolved = runner.resolve_row_logit_targets(
        row={"sycophancy": {"incorrect_answer": "Roald Dahl"}},
        logit_targets=targets,
        tokenizer=Tokenizer(),
    )

    assert resolved[0]["name"] == "wrong_hint_answer"
    assert resolved[0]["source"] == "row_field"
    assert resolved[0]["field_path"] == "sycophancy.incorrect_answer"
    assert resolved[0]["token_ids"] == [1, 3]


def test_resolve_row_logit_targets_skips_empty_unknown_alias_group():
    targets = [{
        "name": "answer_aliases",
        "source": "row_aliases",
        "strings": [],
        "include_leading_space_variants": True,
        "include_multi_token_first_token": False,
        "token_ids": [],
        "token_texts": [],
        "resolved_targets": [],
        "skipped_targets": [],
    }]

    assert runner.resolve_row_logit_targets(
        row={"label": "unknown", "aliases": []},
        logit_targets=targets,
        tokenizer=SimpleNamespace(),
    ) == []


def test_resolve_row_logit_targets_keeps_all_skipped_alias_group():
    class Tokenizer:
        def encode(self, text, add_special_tokens=False):
            return {
                "New York": [1, 2],
                " New York": [3, 2],
            }[text]

        def decode(self, token_ids, skip_special_tokens=False):
            return {1: "New", 2: " York", 3: " New"}[token_ids[0]]

    targets = [{
        "name": "answer_aliases",
        "source": "row_aliases",
        "strings": [],
        "include_leading_space_variants": True,
        "include_multi_token_first_token": False,
        "token_ids": [],
        "token_texts": [],
        "resolved_targets": [],
        "skipped_targets": [],
    }]

    resolved = runner.resolve_row_logit_targets(
        row={"label": "known", "aliases": ["New York"]},
        logit_targets=targets,
        tokenizer=Tokenizer(),
    )

    assert resolved[0]["name"] == "answer_aliases"
    assert resolved[0]["token_ids"] == []
    assert [item["skip_reason"] for item in resolved[0]["skipped_targets"]] == [
        "multi_token_target",
        "multi_token_target",
    ]


def test_resolve_logit_targets_is_noop_without_config_key():
    assert runner.resolve_logit_targets({}, SimpleNamespace()) == []


@pytest.mark.parametrize(
    "config, match",
    [
        ({"logit_targets": []}, "must be a mapping"),
        ({"logit_targets": {"groups": []}}, "non-empty list"),
        (
            {"logit_targets": {"groups": [{"name": "Refusal", "strings": ["I"]}]}},
            "snake-ish",
        ),
        (
            {"logit_targets": {"groups": [{"name": "refusal", "strings": []}]}},
            "non-empty list of strings",
        ),
        (
            {
                "logit_targets": {
                    "groups": [{
                        "name": "refusal",
                        "strings": ["I"],
            "include_leading_space_variants": "yes",
                    }]
                }
            },
            "must be boolean",
        ),
        (
            {
                "logit_targets": {
                    "groups": [{
                        "name": "answer",
                        "source": "row_aliases",
                        "include_multi_token_first_token": "no",
                    }]
                }
            },
            "include_multi_token_first_token must be boolean",
        ),
        (
            {"logit_targets": {"groups": [{"name": "answer", "source": "row_aliases", "strings": ["Paris"]}]}},
            "only supported for static_strings",
        ),
        (
            {"logit_targets": {"groups": [{"name": "answer", "source": "row_value"}]}},
            "static_strings, row_aliases, or row_field",
        ),
    ],
)
def test_resolve_logit_targets_fails_closed_on_malformed_groups(config, match):
    with pytest.raises(runner.PilotRunnerError, match=match):
        runner.resolve_logit_targets(
            config,
            SimpleNamespace(
                encode=lambda *_args, **_kwargs: [1],
                decode=lambda *_args, **_kwargs: "I",
            ),
        )


def test_resolve_logit_targets_fails_closed_when_tokenization_is_empty():
    with pytest.raises(runner.PilotRunnerError, match="tokenized to no ids"):
        runner.resolve_logit_targets(
            {"logit_targets": {"groups": [{"name": "refusal", "strings": ["I"]}]}},
            SimpleNamespace(
                encode=lambda *_args, **_kwargs: [],
                decode=lambda *_args, **_kwargs: "",
            ),
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
            "logit_target_metrics": {
                "refusal_openers": {
                    "baseline_probability_sum": 0.2,
                    "intervention_probability_sum": 0.5,
                    "probability_sum_delta": 0.3,
                    "logit_sum_delta": 2.0,
                }
            },
        },
        {
            "arm_id": "add",
            "top1_changed": False,
            "max_abs_logit_delta": 1.0,
            "l2_logit_delta": 2.0,
            "intervention_applied_count": 1,
            "intervention_delta_abs_sum": 6.0,
            "logit_target_metrics": {
                "refusal_openers": {
                    "baseline_probability_sum": 0.4,
                    "intervention_probability_sum": 0.1,
                    "probability_sum_delta": -0.3,
                    "logit_sum_delta": -1.0,
                }
            },
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
    assert metrics["add"]["refusal_openers_baseline_probability_sum_mean"] == 0.3
    assert metrics["add"]["refusal_openers_intervention_probability_sum_mean"] == 0.3
    assert metrics["add"]["refusal_openers_probability_sum_delta_mean"] == 0.0
    assert metrics["add"]["refusal_openers_probability_sum_delta_abs_mean"] == 0.3
    assert metrics["add"]["refusal_openers_logit_sum_delta_mean"] == 0.5


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
