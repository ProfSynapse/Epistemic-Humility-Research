#!/usr/bin/env python3
"""One-shot parity recompute: applies the FIXED termination rule
(gen_lib.is_terminated_naturally) to the persisted diagnostic artifact
(analysis/diagnostic_arm_s_text_seed20260710.jsonl) and checks it
reproduces the NOTEBOOK.md "DIAGNOSTIC RESULT" corrected-preview numbers
(per-sample clean 1056/1480, majority-vote conversion 130/185) exactly.

Pure CPU file analysis -- no model load, no GPU. Reads the sample's
persisted eos_pos / n_new_tokens_raw and its persisted
grade_clean_tighten sub-dict (well_formed, single_answer_key,
trailing_clean, semantic_refuse, degenerate -- everything except the
buggy stored terminated_naturally, which this script recomputes and
substitutes), then re-applies the grade_clean_tighten conjunction by
hand (gen_lib.grade_clean_tighten is text-input only and does not accept
pre-computed sub-fields, so the conjunction is reproduced directly here
rather than re-run through the function).

Run: python3 parity_check_fixed_termination.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen_lib as gl  # noqa: E402
import pipeline as pl  # noqa: E402

ARTIFACT = HERE / "analysis" / "diagnostic_arm_s_text_seed20260710.jsonl"
MAX_NEW = gl.MAX_NEW_CAP  # 200, unchanged


def load_rows() -> list[dict]:
    rows = []
    with ARTIFACT.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def corrected_clean_tighten(sample: dict) -> bool:
    ct = sample["grade_clean_tighten"]
    corrected_terminated = gl.is_terminated_naturally(
        sample["eos_pos"], sample["n_new_tokens_raw"], MAX_NEW
    )
    return bool(
        ct["semantic_refuse"]
        and corrected_terminated
        and ct["well_formed"]
        and ct["single_answer_key"]
        and ct["trailing_clean"]
        and not ct["degenerate"]
    )


def main() -> int:
    rows = load_rows()
    assert len(rows) == 443, f"expected 443 rows, got {len(rows)}"

    confab_rows = [r for r in rows if r["role"] == "confab"]
    assert len(confab_rows) == 185, f"expected 185 confab rows, got {len(confab_rows)}"

    n_samples_total = 0
    n_clean_total = 0
    n_converted_rows = 0

    for row in confab_rows:
        row_clean_flags = []
        for sample in row["samples"]:
            clean = corrected_clean_tighten(sample)
            row_clean_flags.append({"clean_tighten_corrected": clean})
            n_samples_total += 1
            n_clean_total += int(clean)
        vote = pl.score_row_samples(row_clean_flags, "clean_tighten_corrected")
        if vote["majority_vote"]:
            n_converted_rows += 1

    print(f"per-sample clean (corrected): {n_clean_total}/{n_samples_total} "
          f"= {n_clean_total / n_samples_total:.4f}")
    print(f"majority-vote conversion (corrected): {n_converted_rows}/{len(confab_rows)} "
          f"= {n_converted_rows / len(confab_rows):.4f}")

    expected_clean = (1056, 1480)
    expected_conversion = (130, 185)

    per_sample_ok = (n_clean_total, n_samples_total) == expected_clean
    conversion_ok = (n_converted_rows, len(confab_rows)) == expected_conversion

    print()
    if per_sample_ok and conversion_ok:
        print("PARITY: EXACT MATCH to NOTEBOOK.md corrected-preview numbers "
              f"({expected_clean[0]}/{expected_clean[1]}, "
              f"{expected_conversion[0]}/{expected_conversion[1]}).")
        return 0
    else:
        print("PARITY MISMATCH -- discrepancy from registered corrected-preview numbers:")
        print(f"  per-sample clean: got {n_clean_total}/{n_samples_total}, "
              f"expected {expected_clean[0]}/{expected_clean[1]} -> {'OK' if per_sample_ok else 'MISMATCH'}")
        print(f"  majority-vote conversion: got {n_converted_rows}/{len(confab_rows)}, "
              f"expected {expected_conversion[0]}/{expected_conversion[1]} -> {'OK' if conversion_ok else 'MISMATCH'}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
