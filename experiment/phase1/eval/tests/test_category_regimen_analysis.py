import csv
import sys
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parent.parent / "analysis" / "unknown_question_labels"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import category_regimen_analysis as cra


def _label(family, question, domain, epistemic_type):
    q_hash = cra.question_hash(question)
    return {
        "question_key": f"{family}:{q_hash}",
        "question_hash": q_hash,
        "question": question,
        "analysis_family_coverage": family,
        "primary_domain": domain,
        "secondary_domain": "",
        "epistemic_type": epistemic_type,
        "answer_form": "yes_no",
        "label_confidence": "high",
    }


def _row(family, question, arm_role, refused, *, confidence="", row_index="0"):
    return {
        "analysis_family": family,
        "prompt_contract": "plain_answer" if family == "amendment_a" else "stated_confidence_answer_confidence",
        "evidence_scope": "local_bounded_exploratory",
        "include_status": "include",
        "eval_set": "selfaware",
        "row_index": row_index,
        "id": f"{family}-{row_index}",
        "question": question,
        "label": "unknown",
        "answer_text": "I don't know." if refused else "Yes",
        "refused": str(refused).lower(),
        "behavior_state": "unknown_refused_accurate_idk" if refused else "unknown_answered_hallucination_exposure",
        "arm_role": arm_role,
        "seed": "1",
        "row_hash": f"hash-{family}-{arm_role}-{row_index}",
        "stated_confidence": confidence,
    }


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_wilson_interval_bounds_rate_without_zero_width():
    low, high = cra.wilson_interval(5, 10)

    assert 0 < low < 0.5 < high < 1


def test_run_joins_labels_and_writes_category_outputs(tmp_path):
    row_dir = tmp_path / "rows"
    output_dir = tmp_path / "outputs"
    labels_path = tmp_path / "labels.csv"
    question_a = "Can birds extinguish forest fires independently?"
    question_b = "Will the invented Florb drive launch next year?"

    _write_csv(
        labels_path,
        [
            _label("amendment_a", question_a, "science_health", "impossible_false_premise"),
            _label("amendment_b", question_b, "business_technology", "future_or_unverifiable"),
        ],
    )
    _write_csv(
        row_dir / "row_master_amendment_a.csv",
        [
            _row("amendment_a", question_a, "sft_merged", True),
            _row("amendment_a", question_a, "sft_dpo", False),
            _row("amendment_a", question_a, "sft_kto", True),
            _row("amendment_a", "Unlabeled unknown?", "sft_dpo", False, row_index="1"),
        ],
    )
    _write_csv(
        row_dir / "row_master_amendment_b.csv",
        [
            _row("amendment_b", question_b, "sft_merged", True, confidence="0.1"),
            _row("amendment_b", question_b, "sft_dpo", False, confidence="0.9"),
            _row("amendment_b", question_b, "sft_kto", False, confidence="0.4"),
        ],
    )

    coverage = cra.run(labels_path, row_dir, output_dir)

    assert coverage["source_unknown_rows"] == 7
    assert coverage["joined_unknown_rows"] == 6
    assert coverage["missing_unknown_rows"] == 1

    by_arm = _read_csv(output_dir / "category_regimen_behavior_by_arm.csv")
    assert {row["category_axis"] for row in by_arm} == {"primary_domain", "epistemic_type"}
    dpo_science = [
        row
        for row in by_arm
        if row["analysis_family"] == "amendment_a"
        and row["category_axis"] == "primary_domain"
        and row["category_value"] == "science_health"
        and row["arm_role"] == "sft_dpo"
    ][0]
    assert dpo_science["answered_count"] == "1"
    assert dpo_science["answer_rate"] == "1.000000"

    deltas = _read_csv(output_dir / "category_regimen_deltas.csv")
    assert any(
        row["analysis_family"] == "amendment_a"
        and row["category_value"] == "science_health"
        and row["comparison"] == "dpo_minus_sft"
        and row["answer_rate_delta"] == "1.000000"
        for row in deltas
    )
    confidence = _read_csv(output_dir / "category_regimen_confidence_by_category_b.csv")
    assert any(row["category_value"] == "business_technology" and row["mean_stated_confidence"] == "0.900000" for row in confidence)
    assert (output_dir / "category_regimen_report.md").exists()
