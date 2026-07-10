from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import probe_smoke_stratified_row_manifest as manifest  # noqa: E402


def _write_candidate_rows(root: Path, candidate: str, rows: list[dict]) -> None:
    run_dir = root / candidate / "generation" / "run_test"
    run_dir.mkdir(parents=True)
    path = run_dir / "scored_rows.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps({
                "candidate_label": candidate,
                "control": "no_vector_baseline",
                **row,
            }) + "\n")


def _row(key: str, label: str, *, refused: bool, correct: bool, truthful: bool) -> dict:
    return {
        "probe_pool_row_key": key,
        "label": label,
        "refused": refused,
        "correct": correct,
        "truthful": truthful,
    }


def test_build_manifest_derives_runner_ready_smoke_strata(tmp_path):
    rows_by_candidate = {
        "sft_h_lora_l36": [
            _row("u_stable", "unknown", refused=True, correct=False, truthful=True),
            _row("k_stable", "known", refused=False, correct=True, truthful=True),
            _row("u_loss", "unknown", refused=True, correct=False, truthful=True),
            _row("k_recovery", "known", refused=True, correct=False, truthful=False),
            _row("k_bad", "known", refused=False, correct=True, truthful=True),
        ],
        "sft_delta_l35": [
            _row("u_stable", "unknown", refused=True, correct=False, truthful=True),
            _row("k_stable", "known", refused=False, correct=True, truthful=True),
            _row("u_loss", "unknown", refused=True, correct=False, truthful=True),
            _row("k_recovery", "known", refused=True, correct=False, truthful=False),
            _row("k_bad", "known", refused=False, correct=True, truthful=True),
        ],
        "sft_dpo_h_lora_l34": [
            _row("u_stable", "unknown", refused=True, correct=False, truthful=True),
            _row("k_stable", "known", refused=False, correct=True, truthful=True),
            _row("u_loss", "unknown", refused=False, correct=False, truthful=False),
            _row("k_recovery", "known", refused=False, correct=True, truthful=True),
            _row("k_bad", "known", refused=False, correct=False, truthful=False),
        ],
        "sft_dpo_delta_l35": [
            _row("u_stable", "unknown", refused=True, correct=False, truthful=True),
            _row("k_stable", "known", refused=False, correct=True, truthful=True),
            _row("u_loss", "unknown", refused=True, correct=False, truthful=True),
            _row("k_recovery", "known", refused=True, correct=False, truthful=False),
            _row("k_bad", "known", refused=False, correct=True, truthful=True),
        ],
        "sft_kto_h_lora_l35": [
            _row("u_stable", "unknown", refused=True, correct=False, truthful=True),
            _row("k_stable", "known", refused=False, correct=True, truthful=True),
            _row("u_loss", "unknown", refused=True, correct=False, truthful=True),
            _row("k_recovery", "known", refused=True, correct=False, truthful=False),
            _row("k_bad", "known", refused=False, correct=True, truthful=True),
        ],
        "sft_kto_delta_l36": [
            _row("u_stable", "unknown", refused=True, correct=False, truthful=True),
            _row("k_stable", "known", refused=False, correct=True, truthful=True),
            _row("u_loss", "unknown", refused=True, correct=False, truthful=True),
            _row("k_recovery", "known", refused=True, correct=False, truthful=False),
            _row("k_bad", "known", refused=False, correct=True, truthful=True),
        ],
    }
    for candidate, rows in rows_by_candidate.items():
        _write_candidate_rows(tmp_path, candidate, rows)

    built = manifest.build_manifest(tmp_path)

    assert built["scope"]["no_gpu"] is True
    assert built["scope"]["no_docker"] is True
    assert built["bridge_rationale"]["status"] == "not_runner_ready"
    assert built["strata"]["stable_unknown_refusal_sequential_family"]["row_keys"] == ["u_stable"]
    assert built["strata"]["stable_known_correct_all_executable"]["row_keys"] == ["k_stable"]
    assert built["strata"]["unknown_sft_refusal_to_sequential_answer"]["row_keys"] == ["u_loss"]
    assert built["strata"]["known_sft_refusal_to_sequential_correct"]["row_keys"] == ["k_recovery"]
    assert built["strata"]["known_sft_correct_to_sequential_bad"]["row_keys"] == ["k_bad"]
    assert built["first_smoke"]["row_keys"] == [
        "k_bad",
        "k_recovery",
        "k_stable",
        "u_loss",
        "u_stable",
    ]
    assert set(built["first_smoke"]["row_keys_by_candidate"]) == set(manifest.FIRST_SMOKE_CANDIDATES)


def test_build_manifest_fails_closed_on_inconsistent_duplicate_baseline(tmp_path):
    run_dir = tmp_path / "sft_h_lora_l36" / "generation" / "run_test"
    run_dir.mkdir(parents=True)
    row = {
        "candidate_label": "sft_h_lora_l36",
        "control": "no_vector_baseline",
        "probe_pool_row_key": "dup",
        "label": "known",
    }
    inconsistent = {**row, "label": "unknown"}
    (run_dir / "scored_rows.jsonl").write_text(
        json.dumps(row) + "\n" + json.dumps(inconsistent) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(manifest.RowManifestError, match="inconsistent duplicate baseline row"):
        manifest.build_manifest(tmp_path)
