"""Frozen-detector grading of generation outputs (private; text stays in artifacts)."""

from __future__ import annotations

from pathlib import Path

from .gen_lib import grade_row
from .jobs import Job
from .util import HarnessError, read_jsonl, write_jsonl


def load_job_records(job: Job, output: Path, expected_rows: list[dict], *, patch_digest: str | None = None) -> list[dict]:
    """All records of a finished job; refuses missing/extra/duplicate rows or foreign patch lineage."""
    records = read_jsonl(output) if output.exists() else []
    want = [r["row_key"] for r in expected_rows]
    got = [r["row_key"] for r in records]
    if len(set(got)) != len(got):
        raise HarnessError("JOB_DUPLICATES", f"{job.job_id}: duplicate row keys in output")
    if sorted(got) != sorted(want):
        raise HarnessError("JOB_INCOMPLETE", f"{job.job_id}: output rows ({len(got)}) differ from the registered rows ({len(want)})")
    digests = {r.get("weight_patch_digest") for r in records}
    if patch_digest is None and digests != {None}:
        raise HarnessError("JOB_LINEAGE", f"{job.job_id}: unexpected weight-patch digests {digests}")
    if patch_digest is not None and digests != {patch_digest}:
        raise HarnessError("JOB_LINEAGE", f"{job.job_id}: rows were not generated under the registered patch")
    return records


def grade_records(records: list[dict], job_id: str) -> list[dict]:
    """One graded row per record. Text is NOT copied; join back through row_key."""
    out = []
    for rec in records:
        g = grade_row(rec.get("answer_text", ""), bool(rec.get("terminated_naturally")), rec.get("aliases"))
        out.append({
            "job": job_id, "row_key": rec["row_key"], "role": rec.get("role"), "fire": rec.get("fire"),
            "refused_v2": bool(g["refused_v2"]), "well_formed": bool(g["well_formed"]),
            "degenerate": bool(g["degenerate"]), "correct": bool(g["well_formed_correct_v2"]),
            "answered_v2": bool(g["answered_v2"]), "n_new_tokens": rec.get("n_new_tokens"),
            "matched_pattern_ids": g["matched_pattern_ids"],
        })
    return out


def write_grades(path: Path, graded: list[dict]) -> str:
    return write_jsonl(path, graded)


def rates_by_role(graded: list[dict]) -> dict:
    from .util import rate

    out = {}
    for role in sorted({r["role"] for r in graded}):
        sub = [r for r in graded if r["role"] == role]
        out[role] = {"n": len(sub), "refused_v2": rate(sub, "refused_v2"), "well_formed": rate(sub, "well_formed"),
                     "degenerate": rate(sub, "degenerate"), "correct": rate(sub, "correct")}
    return out
