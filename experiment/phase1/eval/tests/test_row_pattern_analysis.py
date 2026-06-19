import csv
import json
import sys
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parent.parent / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import row_pattern_analysis as rpa


def _counts(rows):
    return rpa.count_rows(rows)


def _write_arm(base, arm_dir, rows):
    arm_path = base / arm_dir
    arm_path.mkdir(parents=True)
    with (arm_path / "scored_rows.jsonl").open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    metrics = {"counts": _counts(rows), "metrics": {"n": len(rows)}}
    (arm_path / "metrics.json").write_text(json.dumps(metrics), encoding="utf-8")


def _row(arm, row_index, label, refused, correct, question, answer):
    return {
        "arm": arm,
        "eval_set": "selfaware",
        "row_index": row_index,
        "id": f"selfaware-{row_index}",
        "question": question,
        "label": label,
        "generated_answer": answer,
        "refused": refused,
        "correct": correct,
        "truthful": (label == "unknown" and refused) or (label == "known" and correct),
        "config_sha": f"sha-{arm}",
        "method": "sft" if "merged" in arm else arm.split("_")[1],
        "model": f"model-{arm}",
        "source": "selfaware",
    }


def _b_row(arm, row_index, label, refused, correct, question, answer, confidence, retry_exhausted=False):
    row = _row(arm, row_index, label, refused, correct, question, json.dumps({"answer": answer, "confidence": confidence}))
    row.update(
        {
            "answer_text": answer,
            "stated_confidence": confidence,
            "generation_attempts": 1,
            "stated_confidence_retry_count": 1 if retry_exhausted else 0,
            "stated_confidence_retry_exhausted": retry_exhausted,
        }
    )
    return row


def _entry(family, contract, result_dir, arm_dir, arm_role, status="include", reason=""):
    return {
        "analysis_family": family,
        "prompt_contract": contract,
        "evidence_scope": "local_bounded_exploratory" if status == "include" else "inventory_only",
        "include_status": status,
        "exclude_reason": reason,
        "result_dir": str(result_dir),
        "arm_dir": arm_dir,
        "arm_role": arm_role,
        "objective_path": {"sft_merged": "sft", "sft_dpo": "dpo", "sft_kto": "kto"}.get(arm_role, "dpo"),
        "seed": 1,
        "eval_set": "selfaware",
    }


def _fixture_manifest(tmp_path):
    a_dir = tmp_path / "amendment_a"
    b_dir = tmp_path / "amendment_b"
    excluded_dir = tmp_path / "bad_merge"

    a_sft = [
        _row("sft_merged", 0, "unknown", True, False, "Who invented the made-up Florb drive?", "I don't know."),
        _row("sft_merged", 1, "known", True, False, "What is the capital of France?", "I don't know."),
        _row("sft_merged", 2, "known", False, True, "When was the Apollo 11 landing?", "1969"),
    ]
    a_dpo = [
        _row("sft_dpo", 0, "unknown", False, False, "Who invented the made-up Florb drive?", "Ada Lovelace."),
        _row("sft_dpo", 1, "known", False, True, "What is the capital of France?", "Paris."),
        _row("sft_dpo", 2, "known", False, False, "When was the Apollo 11 landing?", "1971."),
    ]
    a_kto = [
        _row("sft_kto", 0, "unknown", True, False, "Who invented the made-up Florb drive?", "I don't know."),
        _row("sft_kto", 1, "known", False, False, "What is the capital of France?", "Lyon."),
        _row("sft_kto", 2, "known", True, False, "When was the Apollo 11 landing?", "I don't know."),
    ]
    _write_arm(a_dir, "sft_merged__selfaware", a_sft)
    _write_arm(a_dir, "sft_dpo__selfaware", a_dpo)
    _write_arm(a_dir, "sft_kto__selfaware", a_kto)
    _write_arm(excluded_dir, "sft_dpo_seed2__selfaware", a_dpo)

    b_sft = [
        _b_row("sft_merged_seed1", 0, "unknown", True, False, "Who invented the made-up Florb drive?", "I don't know.", 0.1),
        _b_row("sft_merged_seed1", 1, "known", True, False, "What is the capital of France?", "I don't know.", 0.2),
    ]
    b_dpo = [
        _b_row("sft_dpo_seed1", 0, "unknown", False, False, "Who invented the made-up Florb drive?", "Ada Lovelace.", 0.7),
        _b_row("sft_dpo_seed1", 1, "known", False, True, "What is the capital of France?", "Paris.", 0.9),
    ]
    b_kto = [
        _b_row(
            "sft_kto_seed1",
            0,
            "unknown",
            True,
            False,
            "Who invented the made-up Florb drive?",
            "I don't know.",
            None,
            retry_exhausted=True,
        ),
        _b_row("sft_kto_seed1", 1, "known", False, False, "What is the capital of France?", "Lyon.", 0.6),
    ]
    _write_arm(b_dir, "sft_merged_seed1__selfaware", b_sft)
    _write_arm(b_dir, "sft_dpo_seed1__selfaware", b_dpo)
    _write_arm(b_dir, "sft_kto_seed1__selfaware", b_kto)

    manifest = {
        "inputs": [
            _entry("amendment_a", "plain_answer", a_dir, "sft_merged__selfaware", "sft_merged"),
            _entry("amendment_a", "plain_answer", a_dir, "sft_dpo__selfaware", "sft_dpo"),
            _entry("amendment_a", "plain_answer", a_dir, "sft_kto__selfaware", "sft_kto"),
            _entry(
                "amendment_a",
                "plain_answer",
                excluded_dir,
                "sft_dpo_seed2__selfaware",
                "sft_dpo",
                status="exclude",
                reason="bad_merge_seed2_dpo_excluded_by_assignment",
            ),
            _entry("amendment_b", "stated_confidence_answer_confidence", b_dir, "sft_merged_seed1__selfaware", "sft_merged"),
            _entry("amendment_b", "stated_confidence_answer_confidence", b_dir, "sft_dpo_seed1__selfaware", "sft_dpo"),
            _entry("amendment_b", "stated_confidence_answer_confidence", b_dir, "sft_kto_seed1__selfaware", "sft_kto"),
        ]
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_row_pattern_analysis_writes_separate_outputs_and_validates(tmp_path):
    manifest_path = _fixture_manifest(tmp_path)
    output_dir = tmp_path / "outputs"

    summary = rpa.run(manifest_path, output_dir, write=True)

    assert summary["status"] == "pass"
    assert summary["amendment_a_row_count"] == 9
    assert summary["amendment_b_row_count"] == 6
    assert summary["bad_merge_exclusion_present"] is True
    assert summary["amendment_b_schema_has_answer_text_column"] is True
    assert summary["amendment_b_schema_has_stated_confidence_column"] is True
    assert summary["amendment_b_stated_confidence_nonempty_count"] == 5
    assert summary["amendment_b_stated_confidence_blank_count"] == 1
    assert summary["amendment_b_stated_confidence_blank_retry_exhausted_count"] == 1
    assert summary["amendment_b_stated_confidence_blank_not_retry_exhausted_count"] == 0
    assert (output_dir / "row_master_amendment_a.csv").exists()
    assert (output_dir / "row_master_amendment_b.csv").exists()
    assert (output_dir.parent / "row_pattern_report.md").exists()

    rows_a = _read_csv(output_dir / "row_master_amendment_a.csv")
    rows_b = _read_csv(output_dir / "row_master_amendment_b.csv")
    assert {row["analysis_family"] for row in rows_a} == {"amendment_a"}
    assert {row["analysis_family"] for row in rows_b} == {"amendment_b"}
    assert "stated_confidence" not in rows_a[0]
    baseline_b = [row for row in rows_b if row["arm_role"] == "sft_merged" and row["row_index"] == "0"][0]
    assert baseline_b["stated_confidence"] != ""
    assert baseline_b["confidence_delta_from_sft_merged"] == "0.000000"

    inventory = _read_csv(output_dir / "input_inventory.csv")
    excluded = [row for row in inventory if row["include_status"] == "exclude"]
    assert excluded
    assert excluded[0]["row_count"] == "3"


def test_row_pattern_analysis_transitions_and_deterministic_outputs(tmp_path):
    manifest_path = _fixture_manifest(tmp_path)
    output_dir = tmp_path / "outputs"

    summary_1 = rpa.run(manifest_path, output_dir, write=True)
    first_transitions = (output_dir / "paired_transitions_amendment_b.csv").read_text(encoding="utf-8")
    summary_2 = rpa.run(manifest_path, output_dir, write=True)
    second_transitions = (output_dir / "paired_transitions_amendment_b.csv").read_text(encoding="utf-8")

    assert summary_1 == summary_2
    assert first_transitions == second_transitions

    transitions_a = _read_csv(output_dir / "paired_transitions_amendment_a.csv")
    transition_names = {row["transition"] for row in transitions_a}
    assert "unknown_refused_to_answered" in transition_names
    assert "known_refused_to_correct_answer" in transition_names
    assert "known_correct_to_failure" in transition_names

    transitions_b = _read_csv(output_dir / "paired_transitions_amendment_b.csv")
    dpo_unknown = [
        row
        for row in transitions_b
        if row["comparison"] == "sft_merged_to_sft_dpo" and row["row_index"] == "0"
    ][0]
    assert dpo_unknown["confidence_delta_from_sft_merged"] == "0.600000"
    assert "wh_who" in dpo_unknown["question_tags"]

    kto_unknown = [
        row
        for row in transitions_b
        if row["comparison"] == "sft_merged_to_sft_kto" and row["row_index"] == "0"
    ][0]
    assert kto_unknown["from_answer_bin"] == "refusal"
    assert kto_unknown["to_answer_bin"] == "refusal"
    assert kto_unknown["to_stated_confidence"] == ""
    assert kto_unknown["confidence_delta_from_sft_merged"] == ""
