"""Shared pure-CPU utilities for placebo-signflip-question-type-analysis.

No model loading, no GPU, no new grading. Reused by staging.py, frame_port.py,
behavioral_leg.py, mechanism_leg.py, report.py. Every numeric routine here is
either a verbatim port of an already-reviewed formula from an upstream
experiment (Wilson CI, gate arithmetic) or a small pure statistic
(bootstrap SMD) exercised by test_signflip_smoke.py on synthetic fixtures.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import numpy as np

# Wilson CI z (alpha 0.05), ported verbatim from this repo's shared
# convention (doubt-snap-cross-family-confirmatory/prep_tuner_cell.py:wilson,
# byte-identical across qwen35-4b-midband-heldout/gate_lib.py,
# rr2-mistral-adjudicated-refusal-confirm/gates_lib.py,
# rr-cross-family-raw-refusal/gates_lib.py).
_Z95 = 1.959963984540054


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson(successes: int, n: int, z: float = _Z95) -> dict[str, Any]:
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {
        "n": n,
        "successes": successes,
        "rate": phat,
        "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)],
    }


def rate_wilson(records: Iterable[dict[str, Any]], field: str) -> dict[str, Any]:
    records = list(records)
    return wilson(sum(1 for r in records if bool(r.get(field))), len(records))


def delta_pts(rate_a: dict[str, Any], rate_b: dict[str, Any]) -> float:
    """Percentage-point delta (a - b), matching AMENDMENT.md's
    "random minus baseline" convention."""
    return (rate_a["rate"] - rate_b["rate"]) * 100.0


# ---------------------------------------------------------------------------
# Question-type stratification axis (AMENDMENT.md "Stratification axis:
# question type from the source field, not role")
# ---------------------------------------------------------------------------

_ANSWERABLE_PREFIXES = ("popqa", "triviaqa")


def question_type_of(row_key: str) -> str:
    """Source is read from the row_key prefix (text before the first ':'),
    NEVER from role or category_canon: kuq_unknowns_all:* -> unanswerable;
    popqa:*/triviaqa:* -> answerable. Raises on an unrecognized prefix rather
    than silently misclassifying a row."""
    prefix = row_key.split(":", 1)[0]
    if prefix.startswith("kuq"):
        return "unanswerable"
    if prefix in _ANSWERABLE_PREFIXES:
        return "answerable"
    raise ValueError(f"unrecognized row_key source prefix {prefix!r} in row_key {row_key!r}")


# Verified 2026-07-14 against the ACTUAL on-disk category_canon strings in
# qwen35-4b-midband-heldout/analysis/heldout_rows_for_steer.jsonl,
# rr2-mistral-adjudicated-refusal-confirm/analysis/joined_rows_private.jsonl,
# and rr-cross-family-raw-refusal/analysis/llama/joined_rows_private.jsonl --
# NOT cell.yaml's stylized spellings, which do not match the data (e.g. the
# data's own typo "mistery" for "mystery", space instead of hyphen). For
# popqa/triviaqa rows category_canon holds the source name, not a kuq
# subtype; those rows are excluded from the within-kuq subtype breakdown by
# construction (KUQ_SUBTYPES only names the six unanswerable subtypes).
KUQ_SUBTYPES: tuple[str, ...] = (
    "controversial/debatable question",
    "counterfactual questions",
    "question with false assumption",
    "unsolved problem/mistery",
    "future unknown",
    "underspecified question",
)


# ---------------------------------------------------------------------------
# Paired-population joins (BG2 "paired-population rule")
# ---------------------------------------------------------------------------

def index_by_row_key(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        out[r["row_key"]] = r
    return out


def paired_rows(
    active_by_key: dict[str, dict[str, Any]],
    baseline_by_key: dict[str, dict[str, Any]],
    role: str | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Rows present in BOTH active and baseline, keyed by row_key (the
    paired-population rule: only rows with a grade in both arms enter a
    delta). If `role` is given, restricts to that role as recorded on the
    ACTIVE row (matches AMENDMENT.md Cell A's convention: "paired wide
    abstention delta ... over rows present in both arms")."""
    out = []
    for rk, arow in active_by_key.items():
        if role is not None and arow.get("role") != role:
            continue
        brow = baseline_by_key.get(rk)
        if brow is None:
            continue
        out.append((arow, brow))
    return out


def combine_active_and_baseline(
    row_keys: Iterable[str],
    active_by_key: dict[str, dict[str, Any]],
    baseline_by_key: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Full-population combine: active row if present (fired), else the
    row's baseline (unfired rows reuse baseline text -- no write applied).
    Mirrors qwen35-4b-midband-heldout/pipeline.py:combine_active_and_baseline
    and rr2's own heldout_scorer.py/apply_adjudication.py versions
    byte-for-byte in behavior."""
    out = []
    for rk in row_keys:
        row = active_by_key.get(rk)
        if row is None:
            row = baseline_by_key[rk]
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Bootstrap effect size (M1/M3 mechanism contrasts)
# ---------------------------------------------------------------------------

def _smd(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    va, vb = a.var(ddof=1), b.var(ddof=1)
    pooled = (((na - 1) * va + (nb - 1) * vb) / (na + nb - 2)) ** 0.5
    if pooled == 0:
        return 0.0 if a.mean() == b.mean() else float("inf")
    return float((a.mean() - b.mean()) / pooled)


def bootstrap_smd(
    a: np.ndarray, b: np.ndarray, n_boot: int = 2000, seed: int = 20260714,
) -> dict[str, Any]:
    """Standardized mean difference (mean(a) - mean(b)) / pooled_sd, with a
    percentile bootstrap 95% CI (a and b resampled independently, WITH
    replacement, fixed seed recorded in the output so the CI is
    reproducible). Deterministic for a fixed seed and fixed inputs
    (test_signflip_smoke.py exercises this)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    smd = _smd(a, b)
    rng = np.random.default_rng(seed)
    na, nb = len(a), len(b)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        ai = a[rng.integers(0, na, na)]
        bi = b[rng.integers(0, nb, nb)]
        boots[i] = _smd(ai, bi)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "smd": smd, "n_a": int(na), "n_b": int(nb),
        "n_boot": int(n_boot), "seed": int(seed),
        "bootstrap_ci_95": [float(lo), float(hi)],
    }


def mann_whitney_u(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    """Two-sided Mann-Whitney U (scipy), used alongside bootstrap_smd for
    M1's answerable-vs-unanswerable projection contrast."""
    from scipy.stats import mannwhitneyu

    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) < 1 or len(b) < 1:
        return {"u_statistic": None, "p_value": None, "n_a": len(a), "n_b": len(b)}
    result = mannwhitneyu(a, b, alternative="two-sided")
    return {"u_statistic": float(result.statistic), "p_value": float(result.pvalue), "n_a": int(len(a)), "n_b": int(len(b))}
