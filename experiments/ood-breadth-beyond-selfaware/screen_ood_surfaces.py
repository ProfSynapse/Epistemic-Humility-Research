#!/usr/bin/env python3
r"""G0 disjointness screen for ood-breadth-beyond-selfaware (cell.yaml `screens`,
gates.yaml `g0_disjointness_screen`).

LOCKED SPEC: this script implements cell.yaml's `screens` block and gates.yaml's
G0 exactly as worded. Do not tune thresholds, add screens, or change the
normalization method to make a count match; a materially different drop count
means the training files or the datasets changed since registration, and the
correct response is to STOP and re-derive, not to patch the count
(gates.yaml g0_disjointness_screen.on_count_mismatch).

Method (cell.yaml `screens.method`, identical to the pinned SelfAware
derivation in papers/paper-3-knows-but-doesnt-say/analysis/
clean_subset_sensitivity_p3.py:186 and experiments/grpo-three-seed-confirmatory/
analysis/clean_subset_sensitivity.py):

    normq(text) = re.sub(r"\s+", " ", text.strip().lower())

matched against the verbatim user-turn content of every training file.

Ordered screen (cell.yaml `screens.order`): [duplicate, training_pool,
selfaware_overlap, already_in_validation_split]. Each step removes rows from
the population that SURVIVED the prior steps; a row's drop reason is the first
step that would remove it. `already_in_validation_split` applies only to the
AmbigQA internal-panel train-split top-up (cell.yaml `internal_panel.
topup_selection_rule`), not to the three primary behavior surfaces.

PUBLIC REPO / CONTAINMENT (cell.yaml `screens.outputs`, decisions 13-14 in
AMENDMENT.md "Design decisions at registration"):
  - Full per-surface screened manifests (row-level, WITH question text, in each
    surface's original schema so run_eval.py's ood.py loaders can read them
    unmodified) are written under this experiment's gitignored `analysis/`
    directory. They are NEVER committed.
  - The internal-panel row pool (row_key/question/label only, still row-level
    text) is written under the same gitignored `analysis/` directory for the
    same reason.
  - A COMMITTED summary -- counts by drop reason, input shas, and the sha256 of
    each retained id list -- is written to `screen_summary.json` at the
    experiment root (NOT under analysis/, so it is not gitignored). It carries
    no question text and no row-level data.

Run from the canonical checkout (/home/profsynapse/code/Epistemic-Humility-Research):
    python3 experiments/ood-breadth-beyond-selfaware/screen_ood_surfaces.py

CPU-only. Deterministic: pure counting/filtering, no sampling, no randomness
(the internal-panel top-up selection is an explicit sort-and-take-first-N rule,
not a random draw, per cell.yaml internal_panel.topup_selection_rule).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = EXP_DIR / "analysis" / "screen"
SUMMARY_PATH = EXP_DIR / "screen_summary.json"

sys.path.insert(0, str(REPO_ROOT / "archive" / "experiment" / "phase1" / "eval"))

# ---------------------------------------------------------------------------
# cell.yaml pins (frozen_inputs.datasets + screens.selfaware_reference +
# screens.training_pool_union.files). Every path/sha here must match cell.yaml
# byte-for-byte; this script does not read cell.yaml at runtime (cell.yaml is
# not machine-parsed elsewhere in the pipeline either) so the pins are
# duplicated here deliberately, with the source line cited, so a diff against
# cell.yaml is a straightforward manual check.
# ---------------------------------------------------------------------------

DATASET_PINS = {
    # path -> sha256, from cell.yaml frozen_inputs.datasets
    "datasets/kuq/knowns_unknowns.jsonl": "798d1677f962d11d069f77d1e3db91ad2ddb483a94b697e46bc8ca62ad0aedf6",
    "datasets/ambigqa/validation.jsonl": "e0dcbfcd1a27a239cc286b992d799c2119b991f5116e23d044370caa01b146ed",
    "datasets/ambigqa/train.jsonl": "6f9f5bd4933c0935ab3cb4d54fa10cd2c13b6d78c44cd24f94edb837dea37f4d",
    "datasets/bigbench-known-unknowns/train.jsonl": "4076b8a8ef71381fca4b1310bf6dbaa84c4f0684dab7fd2283f7d74f8025d61c",
    "datasets/bigbench-known-unknowns/validation.jsonl": "25e9170ae27f3a50d6e42c000ce1c052951f0de723d412858c3926daa97f9836",
    "datasets/selfaware/SelfAware.json": "b34a468549dc4c38d080af3a6871ba58ded7fbfc319b1ee606702f0354cee513",
}

# cell.yaml screens.training_pool_union.files: (key, path, field)
TRAINING_POOL_FILES = [
    ("sft_clean_train", "scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_clean.jsonl", "messages"),
    ("dpo_train", "scratch/schema_response_confidence/qwen3-4b-instruct/dpo_response_confidence_train.jsonl", "prompt"),
    ("kto_train", "scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl", "conversations"),
    ("grpo_train", "scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_train.jsonl", "prompt"),
    ("grpo_dev", "scratch/schema_response_confidence/qwen3-4b-instruct-grpo/grpo_dev.jsonl", "prompt"),
    ("contrastive_train", "scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive.jsonl", "messages"),
    ("contrastive_masked_train", "scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive_masked.jsonl", "messages"),
    ("probe_factual_train", "scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_probe_factual.jsonl", "messages"),
]

# gates.yaml g0_disjointness_screen.expected_drop_counts (registered counts to
# check the live run against; NOT used to compute anything).
EXPECTED_DROP_COUNTS = {
    "kuq_known": {"duplicate": 10, "training_hit": 169, "selfaware_overlap": 197, "retained": 3071},
    "kuq_unknown": {"duplicate": 955, "training_hit": 0, "selfaware_overlap": 13, "retained": 2469},
    "ambigqa_known": {"duplicate": 0, "training_hit": 0, "selfaware_overlap": 0, "retained": 830},
    "ambigqa_unknown": {"duplicate": 0, "training_hit": 0, "selfaware_overlap": 0, "retained": 1002},
    "bigbench_known": {"duplicate": 0, "training_hit": 0, "selfaware_overlap": 0, "retained": 23},
    "bigbench_unknown": {"duplicate": 0, "training_hit": 0, "selfaware_overlap": 0, "retained": 23},
    "ambigqa_internal_topup": {"unknown": 501, "known": 415, "total": 916},
}


class ScreenError(RuntimeError):
    """A screen invariant failed. Fail closed -- do not proceed to generation."""


def normq(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_id_list(ids: list[str]) -> str:
    """sha256 of the sorted, newline-joined id list (deterministic, order-independent)."""
    payload = "\n".join(sorted(ids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def iter_jsonl(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def user_contents(record: dict, field_name: str) -> list[str]:
    out = []
    for msg in record.get(field_name, []) or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str):
                out.append(content)
    return out


# ---------------------------------------------------------------------------
# Step 0: sha256 verification (cell.yaml frozen_inputs.untracked_dataset_rule /
# gates.yaml g0 thresholds.dataset_sha256_must_match_cell_yaml). Runs before
# anything else -- G0 is fail-closed and this is the cheapest fail-closed check.
# ---------------------------------------------------------------------------


def verify_dataset_shas() -> dict:
    results = {}
    all_ok = True
    for rel_path, expected in DATASET_PINS.items():
        path = REPO_ROOT / rel_path
        if not path.is_file():
            results[rel_path] = {"expected": expected, "actual": None, "match": False, "error": "missing"}
            all_ok = False
            continue
        actual = sha256_file(path)
        match = actual == expected
        results[rel_path] = {"expected": expected, "actual": actual, "match": match}
        if not match:
            all_ok = False
    return {"all_match": all_ok, "files": results}


# ---------------------------------------------------------------------------
# Step 1: training-pool union (cell.yaml screens.training_pool_union).
# ---------------------------------------------------------------------------


def build_training_pool_union() -> tuple[set[str], dict[str, int]]:
    union: set[str] = set()
    per_file_counts: dict[str, int] = {}
    for key, rel_path, field_name in TRAINING_POOL_FILES:
        path = REPO_ROOT / rel_path
        if not path.is_file():
            raise ScreenError(f"training-pool file missing: {rel_path} (key={key})")
        file_norms: set[str] = set()
        for rec in iter_jsonl(path):
            for content in user_contents(rec, field_name):
                file_norms.add(normq(content))
        per_file_counts[key] = len(file_norms)
        union |= file_norms
    return union, per_file_counts


# ---------------------------------------------------------------------------
# Step 2: SelfAware reference question set (cell.yaml screens.
# selfaware_reference), via the existing ood.load_selfaware loader.
# ---------------------------------------------------------------------------


def build_selfaware_qset() -> set[str]:
    import ood  # existing loader, archive/experiment/phase1/eval/ood.py:119

    path = REPO_ROOT / "datasets" / "selfaware" / "SelfAware.json"
    rows = ood.load_selfaware(path)
    return {normq(r["question"]) for r in rows}


# ---------------------------------------------------------------------------
# Ordered screen over one known/unknown side of one surface.
# ---------------------------------------------------------------------------


@dataclass
class SideScreenResult:
    raw: int
    drop_duplicate: int
    drop_training_hit: int
    drop_selfaware_overlap: int
    retained: int
    retained_rows: list[dict] = field(repr=False)
    retained_ids: list[str] = field(repr=False)

    def counts(self) -> dict:
        return {
            "raw": self.raw,
            "duplicate": self.drop_duplicate,
            "training_hit": self.drop_training_hit,
            "selfaware_overlap": self.drop_selfaware_overlap,
            "retained": self.retained,
        }


def screen_side(
    rows: list[dict],
    *,
    question_fn,
    id_fn,
    training_union: set[str],
    selfaware_qset: set[str],
) -> SideScreenResult:
    """Ordered screen: duplicate (within-side, first-occurrence-wins) ->
    training_pool -> selfaware_overlap. Each row's fate is decided by the FIRST
    step that would remove it; already-removed rows are not double-counted.
    """
    raw = len(rows)
    seen_norms: set[str] = set()
    survivors_after_dup: list[dict] = []
    drop_duplicate = 0
    for r in rows:
        qn = normq(question_fn(r))
        if qn in seen_norms:
            drop_duplicate += 1
            continue
        seen_norms.add(qn)
        survivors_after_dup.append(r)

    survivors_after_train: list[dict] = []
    drop_training_hit = 0
    for r in survivors_after_dup:
        qn = normq(question_fn(r))
        if qn in training_union:
            drop_training_hit += 1
            continue
        survivors_after_train.append(r)

    retained_rows: list[dict] = []
    drop_selfaware = 0
    for r in survivors_after_train:
        qn = normq(question_fn(r))
        if qn in selfaware_qset:
            drop_selfaware += 1
            continue
        retained_rows.append(r)

    retained_ids = [id_fn(r) for r in retained_rows]
    return SideScreenResult(
        raw=raw,
        drop_duplicate=drop_duplicate,
        drop_training_hit=drop_training_hit,
        drop_selfaware_overlap=drop_selfaware,
        retained=len(retained_rows),
        retained_rows=retained_rows,
        retained_ids=retained_ids,
    )


# ---------------------------------------------------------------------------
# KUQ
# ---------------------------------------------------------------------------


def screen_kuq(training_union: set[str], selfaware_qset: set[str]) -> dict:
    path = REPO_ROOT / "datasets" / "kuq" / "knowns_unknowns.jsonl"
    raw_rows = list(iter_jsonl(path))
    # id scheme matches ood.load_kuq exactly: f"kuq-{i}" over the ORIGINAL file
    # index, both sides interleaved -- so retained ids are stable join keys back
    # to the loader's own record ids.
    known_rows, unknown_rows = [], []
    for i, r in enumerate(raw_rows):
        tagged = dict(r, _orig_index=i)
        (unknown_rows if r.get("unknown") else known_rows).append(tagged)

    def qfn(r):
        return r["question"]

    def idfn(r):
        return f"kuq-{r['_orig_index']}"

    known = screen_side(known_rows, question_fn=qfn, id_fn=idfn,
                         training_union=training_union, selfaware_qset=selfaware_qset)
    unknown = screen_side(unknown_rows, question_fn=qfn, id_fn=idfn,
                           training_union=training_union, selfaware_qset=selfaware_qset)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_DIR / "kuq_screened.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for r in sorted(known.retained_rows + unknown.retained_rows, key=lambda x: x["_orig_index"]):
            rec = {k: v for k, v in r.items() if k != "_orig_index"}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return {
        "surface": "S_KUQ",
        "known": known,
        "unknown": unknown,
        "screened_file": out_path,
        "screened_file_row_count": known.retained + unknown.retained,
    }


# ---------------------------------------------------------------------------
# AmbigQA (validation split -- primary behavior surface).
# ---------------------------------------------------------------------------


def classify_ambigqa_row(r: dict) -> str | None:
    """'known' | 'unknown' | None (mixed/no-consensus, excluded on both sides)."""
    types = set(r.get("annotations", {}).get("type", []))
    if types == {"multipleQAs"}:
        return "unknown"
    if types == {"singleAnswer"}:
        return "known"
    return None


def screen_ambigqa_validation(training_union: set[str], selfaware_qset: set[str]) -> dict:
    path = REPO_ROOT / "datasets" / "ambigqa" / "validation.jsonl"
    raw_rows = list(iter_jsonl(path))
    known_rows, unknown_rows = [], []
    excluded_mixed = 0
    for r in raw_rows:
        cls = classify_ambigqa_row(r)
        if cls == "known":
            known_rows.append(r)
        elif cls == "unknown":
            unknown_rows.append(r)
        else:
            excluded_mixed += 1

    def qfn(r):
        return r["question"]

    def idfn(r):
        return f"ambigqa-{r['id']}"

    known = screen_side(known_rows, question_fn=qfn, id_fn=idfn,
                         training_union=training_union, selfaware_qset=selfaware_qset)
    unknown = screen_side(unknown_rows, question_fn=qfn, id_fn=idfn,
                           training_union=training_union, selfaware_qset=selfaware_qset)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_DIR / "ambigqa_validation_screened.jsonl"
    retained_ids_set = set(known.retained_ids) | set(unknown.retained_ids)
    with out_path.open("w", encoding="utf-8") as fh:
        for r in raw_rows:
            if f"ambigqa-{r['id']}" in retained_ids_set:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    return {
        "surface": "S_AMBIGQA",
        "known": known,
        "unknown": unknown,
        "excluded_mixed_annotation_rows": excluded_mixed,
        "screened_file": out_path,
        "screened_file_row_count": known.retained + unknown.retained,
    }


# ---------------------------------------------------------------------------
# BIG-bench known_unknowns (train + validation merged into one surface).
# ---------------------------------------------------------------------------


def _bigbench_question(r: dict) -> str:
    first_line = r["inputs"].split("\n", 1)[0]
    return first_line[2:].strip() if first_line.startswith("Q:") else first_line.strip()


def screen_bigbench(training_union: set[str], selfaware_qset: set[str]) -> dict:
    train_path = REPO_ROOT / "datasets" / "bigbench-known-unknowns" / "train.jsonl"
    val_path = REPO_ROOT / "datasets" / "bigbench-known-unknowns" / "validation.jsonl"
    raw_rows = []
    for split, path in (("train", train_path), ("validation", val_path)):
        for r in iter_jsonl(path):
            raw_rows.append(dict(r, _split=split))

    known_rows, unknown_rows = [], []
    for r in raw_rows:
        (unknown_rows if r.get("targets") == ["Unknown"] else known_rows).append(r)

    def qfn(r):
        return _bigbench_question(r)

    def idfn(r):
        return f"bigbench-known-unknowns-{r['_split']}-{r['idx']}"

    known = screen_side(known_rows, question_fn=qfn, id_fn=idfn,
                         training_union=training_union, selfaware_qset=selfaware_qset)
    unknown = screen_side(unknown_rows, question_fn=qfn, id_fn=idfn,
                           training_union=training_union, selfaware_qset=selfaware_qset)

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_DIR / "bigbench_known_unknowns_screened.jsonl"
    retained_ids_set = set(known.retained_ids) | set(unknown.retained_ids)
    with out_path.open("w", encoding="utf-8") as fh:
        for r in raw_rows:
            rid = f"bigbench-known-unknowns-{r['_split']}-{r['idx']}"
            if rid in retained_ids_set:
                rec = {k: v for k, v in r.items() if k != "_split"}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return {
        "surface": "S_BIGBENCH",
        "known": known,
        "unknown": unknown,
        "screened_file": out_path,
        "screened_file_row_count": known.retained + unknown.retained,
    }


# ---------------------------------------------------------------------------
# AmbigQA train-split top-up for the internal panel (4th screen:
# already_in_validation_split; cell.yaml internal_panel.topup_selection_rule).
# ---------------------------------------------------------------------------


def screen_ambigqa_topup(
    *,
    training_union: set[str],
    selfaware_qset: set[str],
    validation_qnorms: set[str],
    unknown_needed: int,
    known_needed: int,
) -> dict:
    path = REPO_ROOT / "datasets" / "ambigqa" / "train.jsonl"
    raw_rows = list(iter_jsonl(path))
    known_rows, unknown_rows = [], []
    excluded_mixed = 0
    for r in raw_rows:
        cls = classify_ambigqa_row(r)
        if cls == "known":
            known_rows.append(r)
        elif cls == "unknown":
            unknown_rows.append(r)
        else:
            excluded_mixed += 1

    def qfn(r):
        return r["question"]

    def idfn(r):
        return f"ambigqa-{r['id']}"

    known = screen_side(known_rows, question_fn=qfn, id_fn=idfn,
                         training_union=training_union, selfaware_qset=selfaware_qset)
    unknown = screen_side(unknown_rows, question_fn=qfn, id_fn=idfn,
                           training_union=training_union, selfaware_qset=selfaware_qset)

    # 4th screen: already_in_validation_split, applied to the 3-screen survivors.
    def drop_in_validation(result: SideScreenResult) -> tuple[list[dict], int]:
        kept, dropped = [], 0
        for r in result.retained_rows:
            if normq(r["question"]) in validation_qnorms:
                dropped += 1
                continue
            kept.append(r)
        return kept, dropped

    known_avail_rows, known_drop_val = drop_in_validation(known)
    unknown_avail_rows, unknown_drop_val = drop_in_validation(unknown)

    # Deterministic selection (cell.yaml internal_panel.topup_selection_rule):
    # sort survivors by AmbigQA id AS A STRING, take the first N per class. No
    # randomness, no seed.
    known_avail_sorted = sorted(known_avail_rows, key=lambda r: str(r["id"]))
    unknown_avail_sorted = sorted(unknown_avail_rows, key=lambda r: str(r["id"]))

    known_selected = known_avail_sorted[:known_needed]
    unknown_selected = unknown_avail_sorted[:unknown_needed]

    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_DIR / "ambigqa_train_topup_selected.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for r in known_selected + unknown_selected:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    return {
        "known": known,
        "unknown": unknown,
        "known_drop_already_in_validation": known_drop_val,
        "unknown_drop_already_in_validation": unknown_drop_val,
        "known_available": len(known_avail_rows),
        "unknown_available": len(unknown_avail_rows),
        "known_needed": known_needed,
        "unknown_needed": unknown_needed,
        "known_selected_rows": known_selected,
        "unknown_selected_rows": unknown_selected,
        "known_selected_ids": [idfn(r) for r in known_selected],
        "unknown_selected_ids": [idfn(r) for r in unknown_selected],
        "excluded_mixed_annotation_rows": excluded_mixed,
        "topup_file": out_path,
    }


# ---------------------------------------------------------------------------
# Internal-panel row pool (behavior surface + top-up, uniform schema for the
# mechinterp extract rows_path: row_key/question/label).
# ---------------------------------------------------------------------------


def build_internal_panel_pool(ambigqa_val: dict, topup: dict) -> Path:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS_DIR / "internal_panel_pool.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for r in ambigqa_val["known"].retained_rows:
            fh.write(json.dumps({
                "row_key": f"ambigqa-{r['id']}", "question": r["question"], "label": "known",
                "panel_component": "validation_behavior_surface",
            }, ensure_ascii=False) + "\n")
        for r in ambigqa_val["unknown"].retained_rows:
            fh.write(json.dumps({
                "row_key": f"ambigqa-{r['id']}", "question": r["question"], "label": "unknown",
                "panel_component": "validation_behavior_surface",
            }, ensure_ascii=False) + "\n")
        for r in topup["known_selected_rows"]:
            fh.write(json.dumps({
                "row_key": f"ambigqa-{r['id']}", "question": r["question"], "label": "known",
                "panel_component": "train_topup",
            }, ensure_ascii=False) + "\n")
        for r in topup["unknown_selected_rows"]:
            fh.write(json.dumps({
                "row_key": f"ambigqa-{r['id']}", "question": r["question"], "label": "unknown",
                "panel_component": "train_topup",
            }, ensure_ascii=False) + "\n")
    return out_path


# ---------------------------------------------------------------------------
# Committed summary (counts/shas only -- no row-level data).
# ---------------------------------------------------------------------------


def _side_summary(result: SideScreenResult) -> dict:
    d = result.counts()
    d["retained_ids_sha256"] = sha256_id_list(result.retained_ids)
    return d


def build_committed_summary(*, sha_check, training_union, training_per_file,
                             selfaware_qset, kuq, ambigqa_val, bigbench, topup) -> dict:
    return {
        "experiment": "ood-breadth-beyond-selfaware",
        "gate": "G0",
        "method": "normq(text) = re.sub(r'\\s+', ' ', text.strip().lower())",
        "order": ["duplicate", "training_pool", "selfaware_overlap", "already_in_validation_split"],
        "dataset_sha256_verification": sha_check,
        "training_pool_union_size": len(training_union),
        "training_pool_per_file_distinct_user_prompts": training_per_file,
        "selfaware_reference_question_count": len(selfaware_qset),
        "surfaces": {
            "S_KUQ": {
                "known": _side_summary(kuq["known"]),
                "unknown": _side_summary(kuq["unknown"]),
                "retained_total": kuq["known"].retained + kuq["unknown"].retained,
                "screened_file_row_count": kuq["screened_file_row_count"],
            },
            "S_AMBIGQA": {
                "known": _side_summary(ambigqa_val["known"]),
                "unknown": _side_summary(ambigqa_val["unknown"]),
                "excluded_mixed_annotation_rows": ambigqa_val["excluded_mixed_annotation_rows"],
                "retained_total": ambigqa_val["known"].retained + ambigqa_val["unknown"].retained,
                "screened_file_row_count": ambigqa_val["screened_file_row_count"],
            },
            "S_BIGBENCH": {
                "known": _side_summary(bigbench["known"]),
                "unknown": _side_summary(bigbench["unknown"]),
                "retained_total": bigbench["known"].retained + bigbench["unknown"].retained,
                "screened_file_row_count": bigbench["screened_file_row_count"],
            },
        },
        "ambigqa_internal_panel_topup": {
            "known_drop_already_in_validation": topup["known_drop_already_in_validation"],
            "unknown_drop_already_in_validation": topup["unknown_drop_already_in_validation"],
            "known_available_after_all_4_screens": topup["known_available"],
            "unknown_available_after_all_4_screens": topup["unknown_available"],
            "known_needed": topup["known_needed"],
            "unknown_needed": topup["unknown_needed"],
            "known_selected": len(topup["known_selected_ids"]),
            "unknown_selected": len(topup["unknown_selected_ids"]),
            "selected_ids_sha256": sha256_id_list(
                topup["known_selected_ids"] + topup["unknown_selected_ids"]
            ),
            "excluded_mixed_annotation_rows": topup["excluded_mixed_annotation_rows"],
        },
        "internal_panel_total": (
            ambigqa_val["known"].retained + ambigqa_val["unknown"].retained
            + len(topup["known_selected_ids"]) + len(topup["unknown_selected_ids"])
        ),
    }


def check_against_registered(summary: dict) -> list[str]:
    """Compare live counts against gates.yaml g0_disjointness_screen.
    expected_drop_counts. Returns a list of mismatch descriptions (empty = all
    match). NEVER auto-corrects; a mismatch is reported for the operator to act
    on per gates.yaml g0_disjointness_screen.on_count_mismatch.
    """
    mismatches = []

    def cmp(label, live, expected):
        for k, v in expected.items():
            if live.get(k) != v:
                mismatches.append(f"{label}.{k}: live={live.get(k)} expected={v}")

    s = summary["surfaces"]
    cmp("kuq_known", s["S_KUQ"]["known"], EXPECTED_DROP_COUNTS["kuq_known"])
    cmp("kuq_unknown", s["S_KUQ"]["unknown"], EXPECTED_DROP_COUNTS["kuq_unknown"])
    cmp("ambigqa_known", s["S_AMBIGQA"]["known"], EXPECTED_DROP_COUNTS["ambigqa_known"])
    cmp("ambigqa_unknown", s["S_AMBIGQA"]["unknown"], EXPECTED_DROP_COUNTS["ambigqa_unknown"])
    cmp("bigbench_known", s["S_BIGBENCH"]["known"], EXPECTED_DROP_COUNTS["bigbench_known"])
    cmp("bigbench_unknown", s["S_BIGBENCH"]["unknown"], EXPECTED_DROP_COUNTS["bigbench_unknown"])

    topup = summary["ambigqa_internal_panel_topup"]
    exp_topup = EXPECTED_DROP_COUNTS["ambigqa_internal_topup"]
    if topup["unknown_selected"] != exp_topup["unknown"]:
        mismatches.append(f"ambigqa_internal_topup.unknown: live={topup['unknown_selected']} expected={exp_topup['unknown']}")
    if topup["known_selected"] != exp_topup["known"]:
        mismatches.append(f"ambigqa_internal_topup.known: live={topup['known_selected']} expected={exp_topup['known']}")
    total = topup["unknown_selected"] + topup["known_selected"]
    if total != exp_topup["total"]:
        mismatches.append(f"ambigqa_internal_topup.total: live={total} expected={exp_topup['total']}")

    return mismatches


def main() -> int:
    print("=" * 78)
    print("G0 DISJOINTNESS SCREEN -- ood-breadth-beyond-selfaware")
    print("=" * 78)

    sha_check = verify_dataset_shas()
    print("\nStep 0: dataset sha256 verification")
    for path, r in sha_check["files"].items():
        status = "OK" if r["match"] else "MISMATCH/MISSING"
        print(f"  {status:18s} {path}")
    if not sha_check["all_match"]:
        raise ScreenError(
            "G0 FAIL: dataset sha256 mismatch (gates.yaml g0_disjointness_screen."
            "thresholds.dataset_sha256_must_match_cell_yaml). See sha_check above."
        )

    print("\nStep 1: training-pool union")
    training_union, training_per_file = build_training_pool_union()
    print(f"  union distinct user prompts: {len(training_union)} (cell.yaml states 15465)")
    for k, v in training_per_file.items():
        print(f"    {k:26s} {v}")

    print("\nStep 2: SelfAware reference question set")
    selfaware_qset = build_selfaware_qset()
    print(f"  distinct normalized questions: {len(selfaware_qset)}")

    print("\nStep 3: screen S_KUQ")
    kuq = screen_kuq(training_union, selfaware_qset)
    print(f"  known:   {kuq['known'].counts()}")
    print(f"  unknown: {kuq['unknown'].counts()}")

    print("\nStep 4: screen S_AMBIGQA (validation split, behavior surface)")
    ambigqa_val = screen_ambigqa_validation(training_union, selfaware_qset)
    print(f"  known:   {ambigqa_val['known'].counts()}")
    print(f"  unknown: {ambigqa_val['unknown'].counts()}")
    print(f"  excluded_mixed_annotation_rows: {ambigqa_val['excluded_mixed_annotation_rows']}")

    print("\nStep 5: screen S_BIGBENCH (train+validation merged)")
    bigbench = screen_bigbench(training_union, selfaware_qset)
    print(f"  known:   {bigbench['known'].counts()}")
    print(f"  unknown: {bigbench['unknown'].counts()}")

    print("\nStep 6: AmbigQA train-split top-up for the internal panel")
    validation_qnorms = {
        normq(r["question"])
        for r in (ambigqa_val["known"].retained_rows + ambigqa_val["unknown"].retained_rows)
    }
    topup = screen_ambigqa_topup(
        training_union=training_union,
        selfaware_qset=selfaware_qset,
        validation_qnorms=validation_qnorms,
        unknown_needed=501,
        known_needed=415,
    )
    print(f"  available after all 4 screens: unknown={topup['unknown_available']} known={topup['known_available']}")
    print(f"  selected: unknown={len(topup['unknown_selected_ids'])} known={len(topup['known_selected_ids'])}")

    panel_path = build_internal_panel_pool(ambigqa_val, topup)
    print(f"\nInternal-panel pool written: {panel_path.relative_to(REPO_ROOT)}")

    summary = build_committed_summary(
        sha_check=sha_check, training_union=training_union, training_per_file=training_per_file,
        selfaware_qset=selfaware_qset, kuq=kuq, ambigqa_val=ambigqa_val, bigbench=bigbench, topup=topup,
    )

    print("\n" + "=" * 78)
    print("CHECK AGAINST gates.yaml g0_disjointness_screen.expected_drop_counts")
    print("=" * 78)
    mismatches = check_against_registered(summary)
    if mismatches:
        print("MISMATCH -- STOP, do not proceed to generation (this IS a G0 fail condition):")
        for m in mismatches:
            print(f"  {m}")
    else:
        print("MATCH: every registered count reproduced exactly.")
    summary["registered_count_check"] = {
        "all_match": not mismatches,
        "mismatches": mismatches,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\nCommitted summary written: {SUMMARY_PATH.relative_to(REPO_ROOT)}")
    print(f"Gitignored screened manifests under: {ANALYSIS_DIR.relative_to(REPO_ROOT)}/")

    if mismatches:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
