"""Shared pure-CPU utilities for gate-contribution-factorial.

No model loading, no GPU. Wilson CI and JSON/JSONL I/O are ported
byte-for-byte (except this docstring) from
`placebo-seed-distribution-census/common.py`. The bootstrap machinery is NEW
to this experiment: census only needed a bootstrap CI on a SIGN FRACTION
(`bootstrap_fraction_ci`, kept here unchanged for the S1 random-arm sanity
use), whereas this experiment's primary gates (P2 `Gap_Sel`, P3
`cost_protection`) are bootstrap 95% CIs on RATE DIFFERENCES computed from
row-level boolean outcomes over PAIRED populations (gates.yaml
`sc3_paired_population_and_coverage`: "the gate-selectivity gap and
cost-protection gap are computed over paired populations"). `bootstrap_ci`
below is a generic percentile bootstrap over an arbitrary statistic function
of one or more same-length boolean arrays, resampling row INDICES (not each
array independently), which is what makes the resample respect the pairing
(the same resampled row_key contributes to every array in the same draw).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np

_Z95 = 1.959963984540054


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not Path(path).is_file():
        return []
    rows: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_to_list), encoding="utf-8")
    tmp.replace(path)


def _to_list(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"not JSON serializable: {type(obj)!r}")


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def bootstrap_fraction_ci(
    signs: list[int], target_sign: int, n_boot: int = 10000, seed: int = 40260714,
) -> dict[str, Any]:
    """Percentile bootstrap 95% CI on the fraction of `signs` equal to
    `target_sign`, resampling the K seed-level sign values with replacement.
    Ported verbatim from census's common.py (same unit of resolution: one
    point per seed). Used here for the random-arm K=5 sanity check against
    the census null sign, not for a criterion gate."""
    arr = np.asarray(signs, dtype=np.int64)
    k = len(arr)
    point = float(np.mean(arr == target_sign)) if k else 0.0
    if k == 0:
        return {"k": 0, "fraction": 0.0, "bootstrap_ci_95": [0.0, 0.0], "n_boot": n_boot, "seed": seed}
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        sample = arr[rng.integers(0, k, k)]
        boots[i] = np.mean(sample == target_sign)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "k": k, "fraction": point,
        "bootstrap_ci_95": [float(lo), float(hi)],
        "n_boot": n_boot, "seed": seed,
    }


def median_iqr_span(values: list[float]) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64)
    if len(arr) == 0:
        return {"median": None, "q25": None, "q75": None, "iqr_spans_zero": None, "min": None, "max": None}
    q25, median, q75 = np.percentile(arr, [25, 50, 75])
    return {
        "median": float(median), "q25": float(q25), "q75": float(q75),
        "iqr_spans_zero": bool(q25 <= 0.0 <= q75),
        "min": float(arr.min()), "max": float(arr.max()),
    }


def percentile_of_value(values: list[float], value: float) -> float:
    arr = np.asarray(values, dtype=np.float64)
    if len(arr) == 0:
        return float("nan")
    lt = float(np.mean(arr < value))
    le = float(np.mean(arr <= value))
    return 100.0 * (lt + le) / 2.0


def bootstrap_ci(
    stat_fn: Callable[..., float],
    arrays: dict[str, np.ndarray],
    *,
    pair_groups: list[list[str]],
    n_boot: int = 10000,
    seed: int = 47260714,
) -> dict[str, Any]:
    """Generic percentile bootstrap 95% CI for a scalar statistic computed
    from one or more same-length boolean/float arrays.

    `arrays`: name -> 1-D array. `pair_groups`: a list of groups of array
    NAMES that must be resampled with the SAME drawn row indices (because
    they are paired at the row level -- e.g. confab_true_gate/
    confab_permuted_gate/confab_baseline all range over the SAME confab pool
    row order, per gates.yaml sc3 "paired populations"). Arrays in different
    groups are resampled independently (their own length, their own draw).
    `stat_fn` is called once per bootstrap draw as `stat_fn(**resampled)`,
    and once on the unresampled arrays for the point estimate.
    """
    rng = np.random.default_rng(seed)
    for group in pair_groups:
        lengths = {len(arrays[name]) for name in group}
        if len(lengths) != 1:
            raise ValueError(f"paired group {group} has mismatched lengths: {[(n, len(arrays[n])) for n in group]}")

    point = float(stat_fn(**arrays))
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        resampled = dict(arrays)
        for group in pair_groups:
            n = len(arrays[group[0]])
            idx = rng.integers(0, n, n)
            for name in group:
                resampled[name] = np.asarray(arrays[name])[idx]
        boots[i] = float(stat_fn(**resampled))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "point": point, "bootstrap_ci_95": [float(lo), float(hi)],
        "excludes_zero": (lo > 0.0) or (hi < 0.0),
        "n_boot": n_boot, "seed": seed,
    }


def bootstrap_median_ci(values: list[float], n_boot: int = 10000, seed: int = 47260715) -> dict[str, Any]:
    """Percentile bootstrap 95% CI on the MEDIAN of a small set of per-seed
    point estimates (e.g. the K=5 per-seed `Gap_Sel(random)` values),
    resampling at the seed unit of resolution -- the same convention
    `bootstrap_fraction_ci` uses for K-indexed statistics."""
    arr = np.asarray(values, dtype=np.float64)
    k = len(arr)
    if k == 0:
        return {"k": 0, "median": None, "bootstrap_ci_95": [None, None], "n_boot": n_boot, "seed": seed}
    point = float(np.median(arr))
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        sample = arr[rng.integers(0, k, k)]
        boots[i] = np.median(sample)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "k": k, "median": point, "bootstrap_ci_95": [float(lo), float(hi)],
        "n_boot": n_boot, "seed": seed,
    }
