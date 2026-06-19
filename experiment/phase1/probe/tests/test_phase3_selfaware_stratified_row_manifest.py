from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_selfaware_stratified_row_manifest as manifest  # noqa: E402


def _row(row_index: int, label: str, *, arm: str, refused: bool, correct: bool, truthful: bool) -> dict:
    return {
        "arm": arm,
        "eval_set": "selfaware",
        "row_index": row_index,
        "id": f"selfaware-{row_index + 1}",
        "question": f"Question {row_index}?",
        "label": label,
        "generated_answer": "answer",
        "answer_text": "answer",
        "refused": refused,
        "correct": correct,
        "truthful": truthful,
        "config_sha": "abc123",
        "method": arm.split("_")[1],
        "model": "qwen3-4b",
        "source": "selfaware",
    }


def _write_sources(root: Path, rows_by_arm: dict[str, list[dict]]) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    for arm, rows in rows_by_arm.items():
        path = root / arm / "scored_rows.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )
        sources[arm] = path
    return sources


def _all_required_rows(row_defs: dict[int, tuple[str, dict[str, tuple[bool, bool, bool]]]]) -> dict[str, list[dict]]:
    rows_by_arm = {arm: [] for arm in manifest.REQUIRED_ARMS}
    for row_index, (label, arm_states) in row_defs.items():
        for arm in manifest.REQUIRED_ARMS:
            refused, correct, truthful = arm_states[arm]
            rows_by_arm[arm].append(
                _row(row_index, label, arm=arm, refused=refused, correct=correct, truthful=truthful)
            )
    return rows_by_arm


def _state(refused: bool, correct: bool, truthful: bool) -> tuple[bool, bool, bool]:
    return refused, correct, truthful


def test_build_manifest_uses_frozen_selfaware_identity_and_strata(tmp_path):
    all_refuse = {arm: _state(True, False, True) for arm in manifest.REQUIRED_ARMS}
    all_known_correct = {arm: _state(False, True, True) for arm in manifest.REQUIRED_ARMS}
    dpo_loss = {
        **{arm: _state(True, False, True) for arm in manifest.SFT_MERGED_ARMS},
        **{arm: _state(False, False, False) for arm in manifest.DPO_ARMS},
        **{arm: _state(True, False, True) for arm in manifest.KTO_ARMS},
    }
    kto_loss = {
        **{arm: _state(True, False, True) for arm in manifest.SFT_MERGED_ARMS},
        **{arm: _state(True, False, True) for arm in manifest.DPO_ARMS},
        **{arm: _state(False, False, False) for arm in manifest.KTO_ARMS},
    }
    known_recovery = {
        **{arm: _state(True, False, False) for arm in manifest.SFT_MERGED_ARMS},
        **{arm: _state(False, True, True) for arm in manifest.DPO_ARMS},
        **{arm: _state(True, False, False) for arm in manifest.KTO_ARMS},
    }
    known_corruption = {
        **{arm: _state(False, True, True) for arm in manifest.SFT_MERGED_ARMS},
        **{arm: _state(False, False, False) for arm in manifest.DPO_ARMS},
        **{arm: _state(False, True, True) for arm in manifest.KTO_ARMS},
    }
    sources = _write_sources(
        tmp_path,
        _all_required_rows({
            0: ("unknown", all_refuse),
            1: ("known", all_known_correct),
            2: ("unknown", dpo_loss),
            3: ("unknown", kto_loss),
            4: ("known", known_recovery),
            5: ("known", known_corruption),
        }),
    )

    built = manifest.build_manifest(sources)

    assert built["schema_version"] == "phase3-selfaware-frozen-row-manifest/v1"
    assert built["scope"]["not_probe_pool_runner_ready"] is True
    assert built["row_count"] == 6
    assert built["strata"]["stable_unknown_refusal"]["row_keys"] == [
        "selfaware::selfaware::000000::selfaware-1"
    ]
    assert built["strata"]["stable_known_correct"]["row_keys"] == [
        "selfaware::selfaware::000001::selfaware-2"
    ]
    assert built["strata"]["dpo_unknown_refusal_loss_transition"]["row_keys"] == [
        "selfaware::selfaware::000002::selfaware-3"
    ]
    assert built["strata"]["kto_unknown_refusal_loss_transition"]["row_keys"] == [
        "selfaware::selfaware::000003::selfaware-4"
    ]
    assert built["strata"]["known_recovery_transition"]["row_keys"] == [
        "selfaware::selfaware::000004::selfaware-5"
    ]
    assert built["strata"]["known_corruption_transition"]["row_keys"] == [
        "selfaware::selfaware::000005::selfaware-6"
    ]
    first = built["rows"][0]
    assert first["stable_identity"] == {
        "eval_set": "selfaware",
        "row_index": 0,
        "id": "selfaware-1",
        "source": "selfaware",
    }
    assert first["prompt"] == "Question 0?"
    assert set(first["source_arms"]) == set(manifest.REQUIRED_ARMS)


def test_build_manifest_fails_closed_on_duplicate_identity(tmp_path):
    row = _row(0, "known", arm="sft_merged_seed1", refused=False, correct=True, truthful=True)
    path = tmp_path / "sft_merged_seed1" / "scored_rows.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n", encoding="utf-8")
    sources = {"sft_merged_seed1": path}

    with pytest.raises(manifest.SelfAwareManifestError, match="duplicate SelfAware row identity"):
        manifest.load_source_rows(sources)


def test_build_manifest_fails_closed_on_incomplete_coverage(tmp_path):
    rows_by_arm = {arm: [_row(0, "known", arm=arm, refused=False, correct=True, truthful=True)] for arm in manifest.REQUIRED_ARMS}
    rows_by_arm["sft_kto_seed3"] = []
    sources = _write_sources(tmp_path, rows_by_arm)

    with pytest.raises(manifest.SelfAwareManifestError, match="incomplete arm coverage"):
        manifest.build_manifest(sources)


def test_validate_row_requires_selfaware_fields(tmp_path):
    bad = _row(0, "known", arm="sft_merged_seed1", refused=False, correct=True, truthful=True)
    del bad["question"]

    with pytest.raises(manifest.SelfAwareManifestError, match="missing required fields"):
        manifest.validate_row(
            bad,
            path=tmp_path / "rows.jsonl",
            line_number=1,
            source_arm="sft_merged_seed1",
        )
