"""Exact generated-token parity for zero patch, batches, and export round trip."""

from __future__ import annotations


from . import jobs as J
from .config import Cell, Layout
from .util import read_jsonl, write_json, write_jsonl

BASIS = "generated_token_ids"


def compare(records_a: list[dict], records_b: list[dict]) -> dict:
    for record in [*records_a, *records_b]:
        ids = record.get("generated_token_ids")
        if not isinstance(ids, list) or len(ids) != record["n_new_tokens"] or any(type(i) is not int or i < 0 for i in ids):
            return {"passed": False, "n": 0, "reason": "missing or invalid token IDs; fresh outputs required", "basis": BASIS}
    a = {r["row_key"]: (r["generated_token_ids"], r["answer_text"], r["n_new_tokens"], r["terminated_naturally"]) for r in records_a}
    b = {r["row_key"]: (r["generated_token_ids"], r["answer_text"], r["n_new_tokens"], r["terminated_naturally"]) for r in records_b}
    if set(a) != set(b) or len(a) != len(records_a) or len(b) != len(records_b):
        return {"passed": False, "n": len(a), "mismatches": None, "reason": "row sets differ", "basis": BASIS}
    bad = sorted(k for k in a if a[k] != b[k])
    return {"passed": not bad, "n": len(a), "n_mismatches": len(bad), "mismatching_row_keys": bad[:20], "basis": BASIS}


def slice_rows(rows: list[dict], n: int) -> list[dict]:
    """Registered preflight slice: the first n/2 rows of each of the first two roles, in file order."""
    by_role: dict[str, list[dict]] = {}
    for r in rows:
        by_role.setdefault(r["role"], []).append(r)
    roles = sorted(by_role)[:2]
    per = max(1, n // len(roles))
    return [r for role in roles for r in by_role[role][:per]]


def make_slice(layout: Layout, n: int) -> list[dict]:
    rows = read_jsonl(layout.local("materialize/fit_screen.jsonl", shared=True))
    picked = slice_rows(rows, n)
    write_jsonl(layout.local("materialize/parity_slice.jsonl", shared=True), picked)
    return picked


def parity_jobs(cell: Cell, layout: Layout, *, n_rows: int, zero_spec_rel: str, selected_spec_rel: str | None,
                exported_model_path: str | None) -> list[J.Job]:
    rel = "materialize/parity_slice.jsonl"
    out = [
        J.make_job(cell, layout, "parity_untouched_b4", rows_rel=rel, n_rows=n_rows, batch_size=4, meta={"parity": True}),
        J.make_job(cell, layout, "parity_untouched_b1", rows_rel=rel, n_rows=n_rows, batch_size=1, meta={"parity": True}),
        J.make_job(cell, layout, "parity_zero_b4", rows_rel=rel, n_rows=n_rows, batch_size=4, patch_rel=zero_spec_rel,
                   meta={"parity": True}),
    ]
    if selected_spec_rel and exported_model_path:
        out += [J.make_job(cell, layout, "parity_selected_b4", rows_rel=rel, n_rows=n_rows, batch_size=4,
                           patch_rel=selected_spec_rel, meta={"parity": True}),
                J.make_job(cell, layout, "parity_exported_b4", rows_rel=rel, n_rows=n_rows, batch_size=4,
                           meta={"parity": True, "model_path": exported_model_path})]
    return out


def write_evidence(layout: Layout, name: str, doc: dict) -> None:
    write_json(layout.local(f"results/evidence/{name}.json", shared=True), doc)


def zero_patch_evidence(untouched: list[dict], zero: list[dict], noop: bool) -> dict:
    cmp_ = compare(untouched, zero)
    return {**cmp_, "passed": bool(cmp_["passed"] and noop), "engine_receipt_noop": bool(noop)}


def export_evidence(selected: list[dict], exported: list[dict], in_memory_tensors: list[dict] | None,
                    export_tensors: list[dict] | None) -> dict:
    """In-memory patched generation vs generation from the exported checkpoint, plus per-tensor byte identity.

    The engine's ``patch_digest`` covers the spec bytes (the export spec carries an extra block), so tensor-level
    ``after_sha256`` values are compared instead.
    """
    cmp_ = compare(selected, exported)
    mem = {t["name"]: t["after_sha256"] for t in (in_memory_tensors or [])}
    exp = {t["name"]: t["after_sha256"] for t in (export_tensors or [])}
    same = bool(mem) and mem == exp
    return {**cmp_, "passed": bool(cmp_["passed"] and same), "tensor_after_sha256_in_memory": mem,
            "tensor_after_sha256_export": exp, "tensor_bytes_equal": same}
