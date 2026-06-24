from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_causal_pilot_dry_run as dry_run  # noqa: E402


def _write_fixture(tmp_path: Path, *, direction_role: str = "h_lora") -> Path:
    extraction_dir = tmp_path / "extraction"
    direction_dir = extraction_dir / "directions"
    direction_dir.mkdir(parents=True)
    rows = [
        {"probe_pool_row_key": "000|known_a", "label": "known"},
        {"probe_pool_row_key": "001|unknown_a", "label": "unknown"},
    ]
    with (extraction_dir / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    (extraction_dir / "manifest.json").write_text(
        json.dumps({"status": "ok", "verified": True}),
        encoding="utf-8",
    )
    direction_id = "direction__fixture"
    (direction_dir / f"{direction_id}.safetensors").write_text("placeholder", encoding="utf-8")
    (extraction_dir / "hidden_state_candidate_directions.manifest.json").write_text(
        json.dumps({
            "n_labeled_rows": 2,
            "label_counts": {"known": 1, "unknown": 1},
            "directions": [{
                "direction_id": direction_id,
                "role": direction_role,
                "layer": 3,
                "status": "ok",
                "method": "known_unknown_diff",
                "contrast": "unknown_minus_known",
                "tensor_key": "direction",
                "vector_sha256": "abc123",
                "n_total": 2,
            }],
        }),
        encoding="utf-8",
    )

    config = {
        "spec": {
            "status": "readiness_spec_only",
            "evidence_tier_current": "tier1_correlational",
            "evidence_tier_if_intervention_runs": "tier2_exploratory_local",
        },
        "model": {"enable_thinking": False},
        "first_smoke": {
            "initial_scope": {"generation_allowed_by_this_spec": False},
        },
        "candidate_directions": [{
            "label": "fixture_direction",
            "priority": 1,
            "arm": "sft",
            "extraction_dir": str(extraction_dir),
            "extraction_manifest": str(extraction_dir / "manifest.json"),
            "direction_manifest": str(extraction_dir / "hidden_state_candidate_directions.manifest.json"),
            "direction_id": direction_id,
            "direction_file": str(direction_dir / f"{direction_id}.safetensors"),
            "tensor_key": "direction",
            "role": "h_lora",
            "layer": 3,
            "method": "known_unknown_diff",
            "contrast": "unknown_minus_known",
            "required_status": "ok",
        }],
        "readiness_checks": {
            "require_extraction_manifest": {
                "status": "ok",
                "verified": True,
                "row_count": 2,
                "label_counts": {"known": 1, "unknown": 1},
            },
        },
        "coefficient_grid": {
            "values": [-1.0, 0.0, 1.0],
            "include_zero_baseline": True,
            "include_sign_flip": True,
        },
        "controls": {
            "required": ["no_vector_baseline", "sign_flip", "random_direction"],
        },
        "metrics": {
            "primary": ["unknown_abstention_rate"],
            "contamination": ["think_tag_contamination"],
        },
        "output": {
            "root": str(tmp_path / "out"),
            "dry_run_manifest": "dry_run_manifest.json",
            "planned_arms_file": "planned_arms.json",
            "metrics_plan_file": "metrics_plan.json",
        },
        "stop_conditions": ["direction_missing_or_not_ok"],
    }
    config_path = tmp_path / "phase3_causal_pilot_smoke.yaml"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


def test_success_writes_dry_run_outputs(tmp_path):
    config_path = _write_fixture(tmp_path)

    result = dry_run.run(config_path)

    output_root = tmp_path / "out"
    assert result["ok"] is True
    assert result["generation_executed"] is False
    assert (output_root / "dry_run_manifest.json").exists()
    assert (output_root / "planned_arms.json").exists()
    assert (output_root / "metrics_plan.json").exists()

    manifest = json.loads((output_root / "dry_run_manifest.json").read_text(encoding="utf-8"))
    planned_arms = json.loads((output_root / "planned_arms.json").read_text(encoding="utf-8"))
    metrics_plan = json.loads((output_root / "metrics_plan.json").read_text(encoding="utf-8"))
    assert manifest["generation_executed"] is False
    assert manifest["row_counts"]["fixture_direction"]["label_counts"] == {"known": 1, "unknown": 1}
    assert len(planned_arms) == 9
    assert any(arm["is_zero_no_vector_baseline"] for arm in planned_arms)
    assert any(arm["is_sign_flip_control"] for arm in planned_arms)
    assert metrics_plan["generation_executed"] is False


def test_direction_mismatch_fails(tmp_path):
    config_path = _write_fixture(tmp_path, direction_role="delta")

    with pytest.raises(dry_run.DryRunValidationError, match="role mismatch"):
        dry_run.run(config_path, no_write=True)


def test_no_write_validates_without_outputs(tmp_path):
    config_path = _write_fixture(tmp_path)

    result = dry_run.run(config_path, no_write=True)

    assert result["ok"] is True
    assert result["no_write"] is True
    assert result["written"] == []
    assert not (tmp_path / "out").exists()


def test_multi_layer_candidate_validates_components(tmp_path):
    config_path = _write_fixture(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    extraction_dir = Path(config["candidate_directions"][0]["extraction_dir"])
    direction_manifest = extraction_dir / "hidden_state_candidate_directions.manifest.json"
    manifest = json.loads(direction_manifest.read_text(encoding="utf-8"))
    manifest["directions"] = [
        {
            "direction_id": "direction__component_a",
            "role": "h_lora",
            "layer": 27,
            "status": "ok",
            "method": "behavior_axis_mean_difference",
            "contrast": "known_refused_vs_correct",
            "tensor_key": "direction",
            "vector_sha256": "aaa",
        },
        {
            "direction_id": "direction__component_b",
            "role": "h_lora",
            "layer": 36,
            "status": "ok",
            "method": "behavior_axis_mean_difference",
            "contrast": "unknown_wrong_vs_refused",
            "tensor_key": "direction",
            "vector_sha256": "bbb",
        },
    ]
    direction_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    direction_dir = extraction_dir / "directions"
    (direction_dir / "direction__component_a.safetensors").write_text("placeholder", encoding="utf-8")
    (direction_dir / "direction__component_b.safetensors").write_text("placeholder", encoding="utf-8")
    config["candidate_directions"] = [
        {
            "label": "multi_layer_fixture",
            "priority": 1,
            "arm": "sft_kto",
            "direction_id": "multi_layer__fixture",
            "role": "h_lora",
            "method": "multi_layer_direction",
            "contrast": "calibrated_expression_multi_layer",
            "extraction_dir": str(extraction_dir),
            "extraction_manifest": str(extraction_dir / "manifest.json"),
            "multi_layer_components": [
                {
                    "label": "known_repair",
                    "direction_id": "direction__component_a",
                    "direction_manifest": str(direction_manifest),
                    "direction_file": str(direction_dir / "direction__component_a.safetensors"),
                    "tensor_key": "direction",
                    "role": "h_lora",
                    "layer": 27,
                    "method": "behavior_axis_mean_difference",
                    "contrast": "known_refused_vs_correct",
                    "vector_sha256": "aaa",
                    "weight": 1.0,
                },
                {
                    "label": "unknown_repair",
                    "direction_id": "direction__component_b",
                    "direction_manifest": str(direction_manifest),
                    "direction_file": str(direction_dir / "direction__component_b.safetensors"),
                    "tensor_key": "direction",
                    "role": "h_lora",
                    "layer": 36,
                    "method": "behavior_axis_mean_difference",
                    "contrast": "unknown_wrong_vs_refused",
                    "vector_sha256": "bbb",
                    "weight": -1.0,
                },
            ],
        }
    ]
    config_path.write_text(json.dumps(config), encoding="utf-8")

    candidate = dry_run.validate_candidate(
        config["candidate_directions"][0],
        config.get("readiness_checks", {}),
    )
    assert candidate["label"] == "multi_layer_fixture"
    assert len(candidate["multi_layer_components"]) == 2
    assert [component["layer"] for component in candidate["multi_layer_components"]] == [27, 36]
