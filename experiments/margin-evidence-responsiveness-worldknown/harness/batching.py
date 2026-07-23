"""Single, deterministic batch-composition rule for margin-evidence-
responsiveness-worldknown (M4-WK) (gates.yaml SC0 "single pinned batching
regime", MAJOR M2: extended to both paired-contrast sites, not only the
census).

One canonical sort key (numeric PopQA id, parsed from the `popqa:{id}`
row_key) and one canonical batching function are used EVERYWHERE a batch is
formed in this harness -- the census, the three channel-1 capture arms, each
ladder rebuild rung, and the three channel-2 survival arms -- so "one pinned,
recorded batch composition" is a single point of truth rather than a
convention repeated by hand at each call site. Applying the SAME
sort-then-sequential-batch rule to a different (smaller) row set is what
"identical per-row batch grouping" means across differently sized
populations: the row ORDER within a shared row set is always identical, and
the batch boundaries are always sequential slices of that order at the
site's own batch_size.
"""

from __future__ import annotations


def _popqa_numeric_id(row_key: str) -> int:
    if not row_key.startswith("popqa:"):
        raise ValueError(f"batching FAIL: row_key {row_key!r} is not a popqa: row_key")
    return int(row_key.split(":", 1)[1])


def canonical_order(row_keys: list[str]) -> list[str]:
    """Deterministic ascending order by numeric PopQA id."""
    return sorted(row_keys, key=_popqa_numeric_id)


def make_batches(rows_sorted: list[dict], batch_size: int) -> list[list[dict]]:
    """Sequential, non-shuffled slices of an ALREADY-canonically-ordered row
    list. Callers must pass rows already sorted via `canonical_order` (on
    their row_key) to keep composition auditable from this one function."""
    return [rows_sorted[i:i + batch_size] for i in range(0, len(rows_sorted), batch_size)]


def batch_composition_record(rows_sorted: list[dict], batch_size: int) -> dict:
    """A recordable summary of the composition: n_rows, batch_size, n_batches,
    and a hash of the exact row_key order (so a later run's SAME row set in
    the SAME order can be verified byte-identical without storing the full
    order in a committed path)."""
    import hashlib
    import json

    order = [r["row_key"] for r in rows_sorted]
    order_sha256 = hashlib.sha256(json.dumps(order, sort_keys=False).encode("utf-8")).hexdigest()
    n_batches = (len(order) + batch_size - 1) // batch_size if batch_size else 0
    return {"n_rows": len(order), "batch_size": batch_size, "n_batches": n_batches, "row_order_sha256": order_sha256}
