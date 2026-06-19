import csv
import sys
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parent.parent / "analysis" / "unknown_question_labels"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import build_unknown_question_labels as uql


def _row(family, question, arm_role, refused, *, label="unknown", confidence="", row_index="0"):
    return {
        "analysis_family": family,
        "prompt_contract": "plain_answer" if family == "amendment_a" else "stated_confidence_answer_confidence",
        "evidence_scope": "local_bounded_exploratory",
        "include_status": "include",
        "eval_set": "selfaware",
        "row_index": row_index,
        "id": f"{family}-{row_index}",
        "question": question,
        "label": label,
        "answer_text": "That falls beyond the scope of my knowledge." if refused else "Ada Lovelace",
        "refused": str(refused).lower(),
        "behavior_state": "unknown_refused_accurate_idk" if refused else "unknown_answered_hallucination_exposure",
        "arm_role": arm_role,
        "seed": "1",
        "row_hash": f"hash-{family}-{arm_role}-{row_index}",
        "stated_confidence": confidence,
    }


def test_manifest_filters_unknown_rows_and_keeps_amendments_separate():
    question = "Who invented the made-up Florb drive?"
    rows = [
        _row("amendment_a", question, "sft_merged", True),
        _row("amendment_a", question, "sft_dpo", False),
        _row("amendment_a", "What is the capital of France?", "sft_dpo", False, label="known", row_index="1"),
        _row("amendment_b", question, "sft_merged", True, confidence="0.1"),
        _row("amendment_b", question, "sft_dpo", False, confidence="0.7"),
        _row("amendment_b", question, "sft_kto", True, confidence="0.0"),
    ]

    manifest = uql.make_manifest(rows)

    assert len(manifest) == 2
    assert {row["analysis_family_coverage"] for row in manifest} == {"amendment_a", "amendment_b"}
    assert {row["question"] for row in manifest} == {question}
    assert all(row["evidence_tier"] == "exploratory" for row in manifest)
    assert all(row["answered_by_any_arm"] == "true" for row in manifest)
    assert all(row["dpo_answered"] == "true" for row in manifest)
    assert all(row["sft_merged_refused"] == "true" for row in manifest)

    by_family = {row["analysis_family_coverage"]: row for row in manifest}
    assert by_family["amendment_a"]["max_confidence_if_b"] == ""
    assert by_family["amendment_b"]["max_confidence_if_b"] == "0.700000"
    assert by_family["amendment_b"]["kto_answered"] == "false"
    assert by_family["amendment_b"]["arms_answered"] == "sft_dpo"
    assert by_family["amendment_b"]["arms_refused"] == "sft_merged;sft_kto"


def test_run_writes_manifest_and_summary_from_synthetic_row_masters(tmp_path):
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    input_dir.mkdir()

    fieldnames = [
        "analysis_family",
        "prompt_contract",
        "evidence_scope",
        "include_status",
        "eval_set",
        "row_index",
        "id",
        "question",
        "label",
        "answer_text",
        "refused",
        "behavior_state",
        "arm_role",
        "seed",
        "row_hash",
        "stated_confidence",
    ]
    a_rows = [
        _row("amendment_a", "Would you rather lose GPS or a credit card?", "sft_merged", False),
        _row("amendment_a", "Would you rather lose GPS or a credit card?", "sft_kto", True),
    ]
    b_rows = [
        _row("amendment_b", "Is the big rip related to the big bang only?", "sft_merged", True, confidence="0.0"),
        _row("amendment_b", "Is the big rip related to the big bang only?", "sft_dpo", False, confidence="0.95"),
    ]
    for filename, rows in (
        ("row_master_amendment_a.csv", a_rows),
        ("row_master_amendment_b.csv", b_rows),
    ):
        with (input_dir / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    summary = uql.run(input_dir, output_dir)

    assert summary == {"source_unknown_rows": 4, "manifest_questions": 2, "answered_by_any_arm": 2}
    manifest_path = output_dir / "unknown_question_label_manifest.csv"
    summary_path = output_dir / "unknown_question_label_summary.md"
    assert manifest_path.exists()
    assert summary_path.exists()

    with manifest_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert {row["provisional_epistemic_type"] for row in rows} >= {"subjective_normative", "underspecified"}
    assert "Selection Rules" in summary_path.read_text(encoding="utf-8")
