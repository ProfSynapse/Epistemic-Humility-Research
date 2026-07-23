#!/usr/bin/env python3
"""Amendment AK Stage 1 - shared CPU analysis library.

Pure, deterministic helpers shared by the pilot-floor lock
(amendment_ak_stage1_pilot_floor.py) and the full gate analysis
(amendment_ak_stage1_analyze.py). Keeping the data loading, the frozen
doubt-trunk projection, the per-row answer-window slope, and the
confab-vs-refuse slope-contrast statistic in one place guarantees the pilot
and the full run compute the SAME statistic (a pre-registration requirement:
the G2 floor formula in AMENDMENT-AK-commitment-point.md §4 is
`floor = 3 x SE of the slope contrast measured on the ~50-row pilot`, and the
floor is only meaningful if the pilot statistic is identical to the full-run
statistic).

Nothing here fits an axis on the AK pool. The doubt trunk is the FROZEN AH
answerability probe (analysis/ah_stage0/probes/probe_L{layer}.joblib, class 1
== known), loaded as-is; the projection used is the standardized decision
score negated so higher == more doubt (unknown-leaning). This matches the
doc's "frozen doubt trunk" readout (§3.1) and the §7 caveat that the trunk is
measured with a probe fit at the anchor, not refit per position.

The AK-G1 veto crystallization curve DOES refit per position (item 31 showed
frozen correctness axes do not transport across positions); that fitting lives
in amendment_ak_stage1_analyze.py using PCA-128 + saga per the project probe
convention, with the AJ equal-rank random-direction control as the guard. This
library only carries the frozen-trunk G2 machinery plus the shared loaders.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------

def load_rows(arm_dir: Path) -> list[dict]:
    """Load rows.jsonl for one arm (arm_dir contains data/rows.jsonl or rows.jsonl)."""
    p = arm_dir / "data" / "rows.jsonl"
    if not p.exists():
        p = arm_dir / "rows.jsonl"
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _tensor_dir(arm_dir: Path) -> Path:
    d = arm_dir / "data"
    return d if d.exists() else arm_dir


def load_vec(arm_dir: Path, safe_key: str, layer: str, pos: str) -> np.ndarray | None:
    """Load one activation vector "<layer>@<pos>" for a row; None if absent."""
    from safetensors.numpy import load_file
    t = load_file(str(_tensor_dir(arm_dir) / f"{safe_key}.safetensors"))
    key = f"{layer}@{pos}"
    if key not in t:
        return None
    return np.asarray(t[key], dtype=np.float64)


def answer_window_positions(row: dict) -> list[str]:
    """Ordered answer-window position names for a row: answer_k0..answer_kN, answer_end.

    first_visible shares the index of answer_k0 (both == prompt_len); we use the
    answer_k* / answer_end series as the window so positions are non-duplicated
    and monotonically ordered. AK-G1 defines the window endpoints as
    "first visible token" (== answer_k0) and "answer end" (== answer_end).
    """
    pm = row["position_index_map"]
    ks = sorted((k for k in pm if k.startswith("answer_k")),
                key=lambda k: int(k[len("answer_k"):]))
    out = list(ks)
    if "answer_end" in pm and (not out or pm["answer_end"] != pm.get(out[-1])):
        out.append("answer_end")
    elif "answer_end" in pm and out and pm["answer_end"] == pm.get(out[-1]):
        # last stride hit already IS answer_end (renamed by the extractor)
        out[-1] = "answer_end"
    return out


# ----------------------------------------------------------------------------
# Frozen doubt trunk
# ----------------------------------------------------------------------------

@dataclass
class DoubtTrunk:
    """Frozen AH answerability probe as a doubt-projection function.

    projection = -(clf decision on scaled x); higher == more doubt (unknown),
    because AH class 1 == known.
    """
    layer: str
    _w: np.ndarray
    _b: float
    _mean: np.ndarray
    _scale: np.ndarray

    @classmethod
    def load(cls, probes_dir: Path, layer: str) -> "DoubtTrunk":
        import joblib
        o = joblib.load(str(probes_dir / f"probe_{layer}.joblib"))
        scaler, clf = o["scaler"], o["clf"]
        w = np.asarray(clf.coef_, dtype=np.float64).ravel()
        b = float(np.asarray(clf.intercept_, dtype=np.float64).ravel()[0])
        return cls(layer=layer, _w=w, _b=b,
                   _mean=np.asarray(scaler.mean_, dtype=np.float64),
                   _scale=np.asarray(scaler.scale_, dtype=np.float64))

    def project(self, x: np.ndarray) -> float:
        """Doubt projection of a raw activation vector (higher == more doubt)."""
        xs = (x - self._mean) / self._scale
        return -float(xs @ self._w + self._b)


# ----------------------------------------------------------------------------
# Per-row answer-window slope + confab-vs-refuse slope contrast (G2 statistic)
# ----------------------------------------------------------------------------

def row_doubt_slope(arm_dir: Path, row: dict, trunk: DoubtTrunk,
                    min_positions: int = 3) -> float | None:
    """Least-squares slope of doubt projection vs normalized window position.

    Window position is normalized to [0, 1] across the row's own answer window
    (0 == answer_k0/first visible, 1 == answer_end), so the slope is
    "doubt change from window start to window end" in projection units,
    comparable across rows of different generation lengths. Returns None for
    rows with fewer than min_positions answer positions (too short to fit).
    """
    poss = answer_window_positions(row)
    if len(poss) < min_positions:
        return None
    ys, xs = [], []
    n = len(poss)
    for i, pos in enumerate(poss):
        v = load_vec(arm_dir, row["safe_key"], trunk.layer, pos)
        if v is None:
            continue
        ys.append(trunk.project(v))
        xs.append(i / (n - 1))
    if len(ys) < min_positions:
        return None
    xs = np.asarray(xs)
    ys = np.asarray(ys)
    # slope via covariance / variance (deterministic, no solver)
    xm, ym = xs.mean(), ys.mean()
    denom = float(((xs - xm) ** 2).sum())
    if denom <= 0:
        return None
    return float(((xs - xm) * (ys - ym)).sum() / denom)


@dataclass
class SlopeContrast:
    contrast: float                      # mean(slope|confab) - mean(slope|refuse)
    se: float                            # SE of the contrast (two-sample)
    n_confab: int
    n_refuse: int
    mean_confab: float
    mean_refuse: float
    confab_slopes: list[float] = field(default_factory=list)
    refuse_slopes: list[float] = field(default_factory=list)


def slope_contrast(arm_dir: Path, rows: list[dict], trunk: DoubtTrunk,
                   min_positions: int = 3) -> SlopeContrast:
    """confab-vs-refuse slope contrast on the doubt-trunk trajectory, with SE.

    The G2 statistic (AMENDMENT-AK §4). SE is the two-sample SE of a difference
    of means: sqrt(var_c/n_c + var_r/n_r). This is the SE the pilot floor
    formula multiplies by 3.
    """
    cs, rs = [], []
    for r in rows:
        s = row_doubt_slope(arm_dir, r, trunk, min_positions=min_positions)
        if s is None:
            continue
        (cs if r["confab_on_unanswerable"] else rs).append(s)
    cs = np.asarray(cs, dtype=np.float64)
    rs = np.asarray(rs, dtype=np.float64)
    mc = float(cs.mean()) if cs.size else float("nan")
    mr = float(rs.mean()) if rs.size else float("nan")
    # unbiased variance; guard tiny samples
    vc = float(cs.var(ddof=1)) if cs.size > 1 else 0.0
    vr = float(rs.var(ddof=1)) if rs.size > 1 else 0.0
    se = float(np.sqrt(vc / max(cs.size, 1) + vr / max(rs.size, 1)))
    return SlopeContrast(contrast=mc - mr, se=se,
                         n_confab=int(cs.size), n_refuse=int(rs.size),
                         mean_confab=mc, mean_refuse=mr,
                         confab_slopes=cs.tolist(), refuse_slopes=rs.tolist())


def permutation_p(confab_slopes: list[float], refuse_slopes: list[float],
                  n_perm: int = 10000, seed: int = 20260705) -> float:
    """Two-sided permutation p for the slope contrast (label shuffle).

    p = (1 + #{|perm contrast| >= |observed|}) / (n_perm + 1).
    """
    rng = np.random.default_rng(seed)
    allv = np.asarray(list(confab_slopes) + list(refuse_slopes), dtype=np.float64)
    nc = len(confab_slopes)
    obs = abs(np.mean(confab_slopes) - np.mean(refuse_slopes))
    hits = 0
    for _ in range(n_perm):
        perm = rng.permutation(allv)
        c = perm[:nc].mean() - perm[nc:].mean()
        if abs(c) >= obs - 1e-12:
            hits += 1
    return (1 + hits) / (n_perm + 1)
