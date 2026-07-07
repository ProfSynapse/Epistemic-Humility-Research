#!/usr/bin/env python3
"""Materialize the LOCAL, gitignored, full row pool
(`analysis/rows_with_text.jsonl`) that `pipeline.py` reads, by joining the
promoted committed ID-only split manifest (row_key, role, split -- NO question
text, NO aliases) against question text fetched at run time from the private HF
staging repo, mirroring the resolved predecessor's containment scheme.

This repo is PUBLIC. Dataset/pool/question-text/eval-row text is never
committed (see `.skills/pr-workflow/SKILL.md` "Datasets are never
committed").

Question text: `hf_hub_download(repo_id="professorsynapse/eh-al-prep-staging",
filename="pools/a0_pool_v21_questions.jsonl", repo_type="dataset")` --
verified (2026-07-07, this experiment's own build) to cover the FULL 1,662-row
AH A0 pool by row_key, including both roles this experiment needs
(known_correct_answered: 89/89, confab: 309/309).

Aliases (gold-answer text for known_correct_answered rows' correctness
grading after a false-positive dose): NOT re-committed and NOT re-staged to
HF by this script -- aliases already originate from this repo's own
already-committed, publicly-tracked `datasets/kuq/knowns_unknowns.jsonl` /
`datasets/selfaware/SelfAware.json` (joined upstream into the canonical-
checkout-only, gitignored AH A0 pool). This script reads that local file for
aliases only; it does not commit or re-stage it.

Usage:
  python materialize_rows.py
    (writes analysis/rows_with_text.jsonl, gitignored)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"

SPLIT_MANIFEST_PATH = (
    HERE.parent / "common" / "doubt-gated-caution-tighten-heldout-split" / "split_manifest.json"
)
EXTRACT_MANIFEST_PATH = ANALYSIS / "layer_sweep_anchor_extract_manifest.json"
OUT_PATH = ANALYSIS / "rows_with_text.jsonl"

STAGING_REPO = "professorsynapse/eh-al-prep-staging"
QUESTION_POOL_IN_REPO = "pools/a0_pool_v21_questions.jsonl"

AH_A0_ROWS = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/"
    "analysis/ah_main/gen_A0/rows.jsonl"
)
MINED_A0_KNOWN_CORRECT = ANALYSIS / "mined_a0_known_correct_rows.jsonl"
SIBLING_MINED_A0_KNOWN_CORRECT = (
    HERE.parent / "doubt-gated-caution-tighten" / "analysis" / "mined_a0_known_correct_rows.jsonl"
)


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def fetch_question_pool() -> Path:
    from huggingface_hub import hf_hub_download

    p = hf_hub_download(repo_id=STAGING_REPO, filename=QUESTION_POOL_IN_REPO,
                        repo_type="dataset")
    return Path(p)


def main() -> int:
    if not SPLIT_MANIFEST_PATH.is_file():
        print(f"[materialize] ERROR: split manifest not found at {SPLIT_MANIFEST_PATH}. "
              "Run split_fit_heldout.py first.", file=sys.stderr)
        return 1

    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text())
    extract_manifest = json.loads(EXTRACT_MANIFEST_PATH.read_text())
    cat_by_key = {rm["row_key"]: rm.get("category_canon") for rm in extract_manifest["rows"]}

    split_rows = split_manifest["rows"]
    print(f"[materialize] loaded {len(split_rows)} row assignments from {SPLIT_MANIFEST_PATH}")

    q_pool_path = fetch_question_pool()
    print(f"[materialize] fetched question pool -> {q_pool_path}")
    question_by_key: dict[str, str] = {}
    for r in load_jsonl(q_pool_path):
        rk = r.get("row_key")
        q = r.get("question")
        if rk is not None and q is not None:
            question_by_key[rk] = q

    aliases_by_key: dict[str, list[str]] = {}
    if AH_A0_ROWS.is_file():
        for r in load_jsonl(AH_A0_ROWS):
            rk = r.get("row_key")
            if rk is not None:
                aliases_by_key[rk] = r.get("aliases", [])
    else:
        print(f"[materialize] WARNING: local AH A0 pool not found at {AH_A0_ROWS}; "
              "known_correct_answered rows will have empty aliases (false-refusal "
              "correctness grading will be unreliable).", file=sys.stderr)

    mined_path = (
        MINED_A0_KNOWN_CORRECT
        if MINED_A0_KNOWN_CORRECT.is_file()
        else SIBLING_MINED_A0_KNOWN_CORRECT
    )
    if mined_path.is_file():
        for r in load_jsonl(mined_path):
            rk = r.get("row_key")
            if rk is None:
                continue
            if r.get("question"):
                question_by_key[rk] = r["question"]
            aliases_by_key[rk] = r.get("aliases", [])

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    n_missing_q = 0
    n_missing_alias_known = 0
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for rec in split_rows:
            rk = rec["row_key"]
            question = question_by_key.get(rk)
            if not question:
                n_missing_q += 1
            aliases = aliases_by_key.get(rk, [])
            if rec["role"] == "known_correct_answered" and not aliases:
                n_missing_alias_known += 1
            out_rec = dict(rec)
            out_rec["category_canon"] = cat_by_key.get(rk)
            out_rec["question"] = question
            out_rec["aliases"] = aliases
            fh.write(json.dumps(out_rec, ensure_ascii=False) + "\n")

    print(f"[materialize] WROTE {OUT_PATH} ({len(split_rows)} rows); "
          f"missing_question={n_missing_q} "
          f"missing_alias_on_known_correct_answered={n_missing_alias_known}")
    if n_missing_q:
        print(f"[materialize] ERROR: {n_missing_q} rows have no question text "
              "after the HF join.", file=sys.stderr)
        return 1
    if n_missing_alias_known:
        # HARD-FAIL, not a warning: same rationale as the sibling
        # experiment's own hard-fail fix (a missing/broken canonical AH A0
        # pool could otherwise silently produce a vacuous G2 null).
        print(
            f"[materialize] ERROR: {n_missing_alias_known} known_correct_answered "
            "rows have empty aliases after the local AH A0 join -- correctness "
            "grading (false-refusal cost) cannot proceed. Check that the canonical "
            f"checkout's {AH_A0_ROWS} is present and up to date.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
