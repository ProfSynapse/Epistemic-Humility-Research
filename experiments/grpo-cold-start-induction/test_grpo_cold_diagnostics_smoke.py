#!/usr/bin/env python3
"""CPU-only smoke for grpo_cold_diagnostics.py and the materialized trainer
config. Every reward/label/completion value here is fabricated -- no real
question, answer, or model text (public-repo containment rule, AMENDMENT.md).

This calls the SAME functions main() calls (per the pre-sign verification
rule, .skills/experiments/SKILL.md "Before signing ANY cell..."), plus a
direct config-materialization check against the pinned SFT-warmed sibling
config this cell's trainer config was cloned from.

Run: python3 -m pytest experiments/grpo-cold-start-induction/test_grpo_cold_diagnostics_smoke.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import grpo_cold_diagnostics as diag  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture debug-JSONL construction (fabricated rewards/labels only)
# ---------------------------------------------------------------------------


def _row(idx: int, reward: float, *, valid_json: bool, refused: bool) -> dict:
    return {
        "idx": idx,
        "label": "unknown",
        "label_kind": "unknown",
        "aliases": [],
        "reward": reward,
        "behavior_reward": reward,
        "confidence_target": 0.5,
        "valid_json": valid_json,
        "refused": refused,
        "correct": False,
        "answer_text": "fx0 fx1",
        "response_confidence": 0.5,
        "completion": "fx0 fx1",
    }


def _write_events(path: Path, events: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event) + "\n")


# ---------------------------------------------------------------------------
# Diagnostic (i): per-group advantage stats
# ---------------------------------------------------------------------------


def test_per_group_advantage_stats_detects_zero_and_nonzero_groups():
    # Event 1: two groups of 4. Group A all-identical reward (zero advantage).
    # Group B has spread (nonzero advantage).
    group_a = [_row(i, reward=1.0, valid_json=True, refused=False) for i in range(4)]
    group_b = [_row(i, reward=float(i), valid_json=True, refused=False) for i in range(4)]
    event1 = {"at": "t0", "num_completions": 8, "rows": group_a + group_b}

    stats = diag.per_group_advantage_stats([event1], num_generations=4)
    assert stats["n_groups"] == 2
    assert stats["n_zero_advantage_groups"] == 1
    assert stats["zero_advantage_fraction"] == pytest.approx(0.5)
    assert stats["malformed_events"] == []


def test_per_group_advantage_stats_flags_malformed_event_without_dropping_silently():
    # 5 rows with num_generations=4 -- not an exact multiple.
    rows = [_row(i, reward=1.0, valid_json=True, refused=False) for i in range(5)]
    event = {"at": "t0", "num_completions": 5, "rows": rows}

    stats = diag.per_group_advantage_stats([event], num_generations=4)
    assert stats["n_groups"] == 0
    assert stats["zero_advantage_fraction"] is None
    assert len(stats["malformed_events"]) == 1
    assert stats["malformed_events"][0]["num_rows"] == 5


def test_per_group_advantage_stats_all_zero_across_run_is_null_b_shape():
    # Every group in every event zero-advantage -> fraction 1.0 (Null-B shape:
    # the registrants' modal expectation, AMENDMENT.md "Null-B").
    events = []
    for e in range(3):
        rows = [_row(i, reward=-1.2, valid_json=False, refused=False) for i in range(4)]
        events.append({"at": f"t{e}", "num_completions": 4, "rows": rows})
    stats = diag.per_group_advantage_stats(events, num_generations=4)
    assert stats["n_groups"] == 3
    assert stats["zero_advantage_fraction"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Diagnostics (ii) and (iii)
# ---------------------------------------------------------------------------


def test_contract_parse_and_abstention_fractions():
    rows = [
        _row(0, reward=1.0, valid_json=True, refused=True),
        _row(1, reward=1.0, valid_json=True, refused=False),
        _row(2, reward=1.0, valid_json=False, refused=False),
        _row(3, reward=1.0, valid_json=False, refused=False),
    ]
    events = [{"at": "t0", "num_completions": 4, "rows": rows}]

    parse = diag.valid_contract_parse_fraction(events)
    assert parse["n_rollouts"] == 4
    assert parse["n_valid_json"] == 2
    assert parse["valid_contract_parse_fraction"] == pytest.approx(0.5)

    abst = diag.abstention_rate(events)
    assert abst["n_rollouts"] == 4
    assert abst["n_refused"] == 1
    assert abst["abstention_rate"] == pytest.approx(0.25)


def test_diagnostics_empty_events_reports_none_not_crash():
    diagnostics = diag.compute_diagnostics([], num_generations=4)
    assert diagnostics["per_group_advantage"]["zero_advantage_fraction"] is None
    assert diagnostics["contract_parse"]["valid_contract_parse_fraction"] is None
    assert diagnostics["abstention"]["abstention_rate"] is None


# ---------------------------------------------------------------------------
# CG-G0
# ---------------------------------------------------------------------------


def test_cg_g0_passes_on_clean_training_full_eval_and_present_diagnostics():
    diagnostics = diag.compute_diagnostics(
        [{"at": "t0", "num_completions": 4,
          "rows": [_row(i, reward=float(i), valid_json=True, refused=False) for i in range(4)]}],
        num_generations=4,
    )
    result = diag.cg_g0_checklist(
        training_completed_clean=True, degenerate_reward_stop=False,
        eval_rows_scored=3369, eval_rows_total=3369, diagnostics=diagnostics,
    )
    assert result["pass"] is True
    assert result["checks"]["training_completed_or_degenerate_stop"] is True
    assert result["checks"]["eval_full_row_set_scored"] is True
    assert result["checks"]["diagnostics_present"] is True


def test_cg_g0_fails_when_training_status_is_ambiguous_both_or_neither():
    diagnostics = diag.compute_diagnostics(
        [{"at": "t0", "num_completions": 4,
          "rows": [_row(i, reward=float(i), valid_json=True, refused=False) for i in range(4)]}],
        num_generations=4,
    )
    both = diag.cg_g0_checklist(
        training_completed_clean=True, degenerate_reward_stop=True,
        eval_rows_scored=3369, eval_rows_total=3369, diagnostics=diagnostics,
    )
    assert both["checks"]["training_completed_or_degenerate_stop"] is False
    assert both["pass"] is False

    neither = diag.cg_g0_checklist(
        training_completed_clean=False, degenerate_reward_stop=False,
        eval_rows_scored=3369, eval_rows_total=3369, diagnostics=diagnostics,
    )
    assert neither["checks"]["training_completed_or_degenerate_stop"] is False
    assert neither["pass"] is False


def test_cg_g0_fails_on_partial_eval_row_coverage():
    diagnostics = diag.compute_diagnostics(
        [{"at": "t0", "num_completions": 4,
          "rows": [_row(i, reward=float(i), valid_json=True, refused=False) for i in range(4)]}],
        num_generations=4,
    )
    result = diag.cg_g0_checklist(
        training_completed_clean=True, degenerate_reward_stop=False,
        eval_rows_scored=3000, eval_rows_total=3369, diagnostics=diagnostics,
    )
    assert result["checks"]["eval_full_row_set_scored"] is False
    assert result["pass"] is False


def test_cg_g0_fails_when_a_diagnostic_is_missing_not_footnoted():
    # Empty events -> all three diagnostics compute to None (missing).
    diagnostics = diag.compute_diagnostics([], num_generations=4)
    result = diag.cg_g0_checklist(
        training_completed_clean=True, degenerate_reward_stop=False,
        eval_rows_scored=3369, eval_rows_total=3369, diagnostics=diagnostics,
    )
    assert result["checks"]["diagnostics_present"] is False
    assert result["pass"] is False


def test_cg_g0_fails_on_malformed_group_capture():
    rows = [_row(i, reward=1.0, valid_json=True, refused=False) for i in range(5)]
    diagnostics = diag.compute_diagnostics(
        [{"at": "t0", "num_completions": 5, "rows": rows}], num_generations=4,
    )
    result = diag.cg_g0_checklist(
        training_completed_clean=True, degenerate_reward_stop=False,
        eval_rows_scored=3369, eval_rows_total=3369, diagnostics=diagnostics,
    )
    assert result["checks"]["diagnostics_capture_well_formed"] is False
    assert result["pass"] is False


# ---------------------------------------------------------------------------
# CG-G1 -- all four pre-registered bands
# ---------------------------------------------------------------------------


def test_cg_g1_null_b_when_zero_advantage_at_or_above_floor():
    result = diag.cg_g1_call(zero_advantage_fraction=0.90, eval_refusal_recall_pct=1.0)
    assert result["mechanism"] == "Null-B"
    assert result["is_null_b"] is True

    result_high = diag.cg_g1_call(zero_advantage_fraction=0.97, eval_refusal_recall_pct=50.0)
    # Null-B takes precedence over eval recall once the floor is met, even if
    # (hypothetically) eval recall were high -- the mechanism call is fixed by
    # the training-time signal first, per AMENDMENT.md "Gates".
    assert result_high["mechanism"] == "Null-B"


def test_cg_g1_null_a_below_zero_advantage_floor_and_low_eval_recall():
    result = diag.cg_g1_call(zero_advantage_fraction=0.50, eval_refusal_recall_pct=5.0)
    assert result["mechanism"] == "Null-A"
    assert result["is_null_b"] is False


def test_cg_g1_falsifier_zone_at_or_above_20pp_recall():
    result = diag.cg_g1_call(zero_advantage_fraction=0.10, eval_refusal_recall_pct=20.0)
    assert result["mechanism"] == "falsifier-zone"

    result_high = diag.cg_g1_call(zero_advantage_fraction=0.0, eval_refusal_recall_pct=80.0)
    assert result_high["mechanism"] == "falsifier-zone"


def test_cg_g1_ambiguous_band_between_10_and_20pp_recall():
    result = diag.cg_g1_call(zero_advantage_fraction=0.30, eval_refusal_recall_pct=15.0)
    assert result["mechanism"] == "ambiguous-band"


def test_cg_g1_band_boundaries_are_exact():
    # 10.0 belongs to Null-A's ceiling being EXCLUSIVE (< 10.0 is Null-A), so
    # exactly 10.0 falls into the ambiguous band, not Null-A.
    at_ten = diag.cg_g1_call(zero_advantage_fraction=0.0, eval_refusal_recall_pct=10.0)
    assert at_ten["mechanism"] == "ambiguous-band"
    just_under_ten = diag.cg_g1_call(zero_advantage_fraction=0.0, eval_refusal_recall_pct=9.999)
    assert just_under_ten["mechanism"] == "Null-A"


# ---------------------------------------------------------------------------
# End-to-end CLI (main()) over a fixture debug JSONL on disk
# ---------------------------------------------------------------------------


def test_main_end_to_end_over_fixture_debug_jsonl(tmp_path, capsys):
    debug_path = tmp_path / "reward_debug.jsonl"
    events = [
        {"at": "t0", "num_completions": 4,
         "rows": [_row(i, reward=1.0, valid_json=True, refused=True) for i in range(4)]},
        {"at": "t1", "num_completions": 4,
         "rows": [_row(i, reward=float(i), valid_json=False, refused=False) for i in range(4)]},
    ]
    _write_events(debug_path, events)

    out_path = tmp_path / "result.json"
    code = diag.main([
        "--debug-path", str(debug_path),
        "--num-generations", "4",
        "--eval-refusal-recall-pct", "3.5",
        "--training-completed-clean",
        "--eval-rows-scored", "3369",
        "--eval-rows-total", "3369",
        "--out", str(out_path),
    ])
    assert code == 0
    assert out_path.is_file()
    result = json.loads(out_path.read_text(encoding="utf-8"))

    assert result["diagnostics"]["per_group_advantage"]["n_groups"] == 2
    assert result["diagnostics"]["per_group_advantage"]["n_zero_advantage_groups"] == 1
    assert result["cg_g0"]["pass"] is True
    assert result["cg_g1"]["mechanism"] == "Null-A"  # 50% zero-adv < 90% floor, recall 3.5% < 10%


def test_main_returns_2_on_missing_debug_path(tmp_path):
    code = diag.main(["--debug-path", str(tmp_path / "does-not-exist.jsonl")])
    assert code == 2


# ---------------------------------------------------------------------------
# Trainer config materialization correctness: diff against the pinned
# SFT-warmed sibling this cell's config was cloned from. Per AMENDMENT.md
# "Design": "Single difference: source is the raw base... and seed 1" --
# this test asserts EXACTLY that shape, nothing else silently diverged.
# ---------------------------------------------------------------------------


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_cold_trainer_config_differs_from_warmed_sibling_only_in_source_and_seed():
    cold = _load_yaml(HERE / "configs" / "grpo_cold_base_seed1_full.yaml")
    warmed = _load_yaml(
        REPO_ROOT / "experiments" / "grpo-three-seed-confirmatory" / "configs"
        / "grpo_schema_clean_sft_merged_seed2_v2_full.yaml"
    )

    # Cold start: no SFT source to merge.
    assert cold["model"]["lora_path"] is None
    assert warmed["model"]["lora_path"] is None  # both null in this schema (merge already
    # baked into model.model_name for the warmed arm); the REAL distinguishing
    # field is model_name itself, checked next.
    assert "cold_base" not in warmed["model"]["model_name"]
    assert cold["model"]["model_name"] == "unsloth/Qwen3-4B-bnb-4bit"
    assert warmed["model"]["model_name"] != cold["model"]["model_name"]

    # Seed threading: cold arm registered at seed 1 (AMENDMENT.md "Design").
    assert cold["seed"] == 1
    assert cold["lora"]["random_state"] == 1

    # Every OTHER top-level training/lora/dataset/reward field must be
    # byte-identical to the warmed sibling (dataset, reward v2, batch 32,
    # num_generations 4, LR 5.0e-6, beta 0.1, 1 epoch) -- AMENDMENT.md
    # "identical in every field except source... and seed 1".
    ignore_paths = {
        ("model", "model_name"), ("model", "lora_path"),
        ("lora", "random_state"),
        ("training", "output_dir"),
        ("seed",),
    }

    def _walk(prefix: tuple, a, b, diffs: list):
        if prefix in ignore_paths:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for key in sorted(set(a) | set(b)):
                _walk(prefix + (key,), a.get(key), b.get(key), diffs)
        elif a != b:
            diffs.append((prefix, a, b))

    diffs: list = []
    _walk((), cold, warmed, diffs)
    assert diffs == [], f"unexpected divergence from the warmed sibling: {diffs}"


def test_cold_trainer_config_reward_file_is_the_unchanged_v2_reward():
    cold = _load_yaml(HERE / "configs" / "grpo_cold_base_seed1_full.yaml")
    assert cold["rewards"]["custom"]["file"].endswith("humility_reward_v2.py")
    assert cold["rewards"]["custom"]["functions"][0]["name"] == "epistemic_humility_reward"


def test_cold_eval_config_loads_and_flags_its_own_placeholder():
    eval_cfg = _load_yaml(
        HERE / "configs" / "eval_grpo_cold_start_selfaware_full_local_4b.yaml"
    )
    assert eval_cfg["model_name"] == "unsloth/Qwen3-4B-bnb-4bit"
    # The adapter is a documented placeholder until training completes; this
    # assertion exists so the placeholder can never silently start looking
    # like a real path without this test being touched.
    assert eval_cfg["arms"][0]["adapter"].startswith("<FILLED_AFTER_TRAINING>")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
