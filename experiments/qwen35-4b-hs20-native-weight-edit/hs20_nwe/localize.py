"""Per-row resumable localization statistics and column ranking.

Each captured FIT-L row is reduced to a small per-row file (``float32`` anchor
activations for the configured sites) that is hash-journalled with the host
``RunLog``.  A resumed run skips rows whose journal record and file hash both
verify; everything else is recomputed.  The final reduction reads only
verified per-row files.  Persistence is per row; there is no mid-row state.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .capture import check_rows_covered, load_manifest, read_row, site_key
from .config import Cell
from .util import HarnessError, sha256_file

SITE_MODULE = "mlp.down_proj"
SITE_TENSOR = "input"


def rank_columns(mean_confab: np.ndarray, mean_known: np.ndarray, dots: np.ndarray, k: int) -> dict:
    """Top-k strictly positive scores of (mean_confab - mean_known) * dots; ties by column index."""
    mean_confab, mean_known, dots = (np.asarray(x, dtype=np.float64) for x in (mean_confab, mean_known, dots))
    if not (mean_confab.shape == mean_known.shape == dots.shape and mean_confab.ndim == 1):
        raise HarnessError("RANK_SHAPE", "means and dots must be matching 1-D arrays")
    scores = (mean_confab - mean_known) * dots
    positive = np.flatnonzero(scores > 0.0)
    # Stable: descending score, ascending column index on ties.
    order = sorted(positive.tolist(), key=lambda j: (-float(scores[j]), j))
    chosen = order[:k]
    return {"n_positive": int(positive.size), "eligible": positive.size >= k,
            "columns": chosen if positive.size >= k else [],
            "scores": [float(scores[j]) for j in chosen] if positive.size >= k else []}


def _journal_hashes(path: Path) -> dict[str, str]:
    import json

    out: dict[str, str] = {}
    if Path(path).is_file():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                out[str(rec["key"])] = rec.get("sha256")
    return out


def _row_path(root: Path, key: str) -> Path:
    from .util import sha256_bytes

    return root / "rows" / f"{sha256_bytes(key.encode('utf-8'))}.npz"


def reduce_rows(cell: Cell, capture_dir: Path, rows: list[dict], work_dir: Path, *, blocks: list[int]) -> dict:
    """Resumable per-row reduction; returns the per-role sums/means per block."""
    from engine_host.runlog import RunLog

    manifest = load_manifest(capture_dir)
    check_rows_covered(manifest, [r["row_key"] for r in rows])
    capture_by_key = {r["row_key"]: r for r in manifest["rows"]}
    sites = [(b, SITE_MODULE, SITE_TENSOR) for b in blocks]
    work_dir = Path(work_dir)
    run_config = {"schema_version": "hs20-nwe-localization-journal/v1", "blocks": blocks,
                  "rows": [(r["row_key"], r["role"]) for r in rows],
                  "capture_manifest_sha256": sha256_file(Path(capture_dir) / "manifest.json")}
    recomputed = 0
    with RunLog(work_dir / "localization.runlog.jsonl", run_config) as log:
        done = log.done_keys()
        journal_hashes = _journal_hashes(work_dir / "localization.runlog.jsonl")
        for row in rows:
            key, path = row["row_key"], _row_path(work_dir, row["row_key"])
            if key in done and path.is_file():
                if sha256_file(path) == journal_hashes.get(key):
                    continue
            data = read_row(capture_dir, capture_by_key[key], hidden_state=int(cell.cell["sensor"]["hidden_state"]),
                            sites=sites)
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp.npz")
            np.savez(tmp, **{str(b): data["sites"][site_key(b, SITE_MODULE, SITE_TENSOR)].astype(np.float32)
                             for b in blocks})
            tmp.replace(path)
            log.record(key, {"role": row["role"], "sha256": sha256_file(path)})
            recomputed += 1
        log.finalize({"n_rows": len(rows), "recomputed_this_pass": recomputed})
    sums, counts = {}, {}
    for row in rows:
        path = _row_path(work_dir, row["row_key"])
        with np.load(path) as arrays:
            for b in blocks:
                a = arrays[str(b)].astype(np.float64)
                sums.setdefault((row["role"], b), np.zeros_like(a))
                sums[(row["role"], b)] += a
        counts[row["role"]] = counts.get(row["role"], 0) + 1
    means = {(role, b): sums[(role, b)] / counts[role] for (role, b) in sums}
    return {"means": means, "counts": counts, "recomputed_this_pass": recomputed}
