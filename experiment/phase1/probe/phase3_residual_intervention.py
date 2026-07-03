#!/usr/bin/env python3
"""Causal residual-stream intervention on the CAUTION axis (B1, Tier-2).

B2 (read-trajectory) established that the L35 caution direction separates
over-refusals from answered knowns BEFORE the refusal is verbalized
(pre-commitment), but a read cannot tell whether that state is *load-bearing* for
the abstention. B1 closes that with a causal handle that survives the
anti-steerability F/K hit: instead of additive ITI, **ablate** (project out) the
caution direction from the residual stream during generation and ask whether the
model stops over-refusing. Directional shift arms (+/- alpha*sigma) characterize
the steerability sign as a secondary check.

Two halves, mirroring the read-trajectory split:

1. A torch forward POST-hook on the target decoder block that REWRITES the block
   output: ``ablate`` removes the theta component at every position; ``shift``
   adds ``alpha*sigma*theta``. The GPU wiring lives in the runner; the hook math
   has a pure-numpy reference (``apply_intervention``) that is unit-tested offline.

2. Pure-numpy refusal-rate aggregation + a load-bearing verdict over the arms
   (baseline vs ablate on known_refused, with known_correct_answered as the
   specificity control).
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

KNOWN_REFUSED = "known_refused"
KNOWN_ANSWERED = "known_correct_answered"
BASELINE_ARM = "baseline"

MODE_ABLATE = "ablate"
MODE_SHIFT = "shift"
MODE_BASELINE = "baseline"
# Amendment AC: erase the theta component and write a per-row doubt-scaled
# setpoint (alpha resolved per row from a gain map). couple with alpha=0 is
# exactly ablate, so the constant comparison nests inside the coupling family.
MODE_COUPLE = "couple"

UNKNOWN_REFUSED = "unknown_refused"
DEFAULT_GROUPS = (KNOWN_REFUSED, KNOWN_ANSWERED)


class ResidualInterventionError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# pure-numpy intervention reference (offline-testable)
# ---------------------------------------------------------------------------

def _unit(theta: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(theta))
    if n == 0.0:
        raise ResidualInterventionError("theta has zero norm")
    return theta / n


def apply_intervention(hidden: np.ndarray, theta: np.ndarray, *, mode: str,
                       alpha: float = 0.0, sigma: float = 1.0) -> np.ndarray:
    """Reference for the write hook. ``hidden`` is [..., hidden_dim].

    - ``ablate``: subtract the projection onto unit(theta) at every position
      (removes the caution component).
    - ``shift``: add ``alpha*sigma*unit(theta)`` at every position.
    - ``couple``: erase the theta component AND add ``alpha*sigma*unit(theta)``
      (set the theta coordinate to a doubt-scaled setpoint; Amendment AC).
      ``couple`` with alpha=0 is identical to ``ablate``.

    ``alpha`` may be a scalar or a 1-D vector of length hidden.shape[0]
    (one value per leading batch element, broadcast over positions) so a
    batch of rows with DIFFERENT per-row gains runs in one forward.
    """
    th = _unit(np.asarray(theta, dtype=np.float64))
    h = np.asarray(hidden, dtype=np.float64)
    a = np.asarray(alpha, dtype=np.float64)
    if a.ndim not in (0, 1):
        raise ResidualInterventionError(
            f"alpha must be a scalar or a 1-D per-batch vector, got ndim={a.ndim}")
    if a.ndim == 1:
        if h.ndim < 2 or a.shape[0] != h.shape[0]:
            raise ResidualInterventionError(
                f"alpha vector length {a.shape[0]} does not match batch size "
                f"{h.shape[0] if h.ndim >= 2 else '<no batch dim>'}")
        a = a.reshape((h.shape[0],) + (1,) * (h.ndim - 1))
    if mode == MODE_ABLATE:
        proj = h @ th  # [...]
        return h - proj[..., None] * th
    if mode == MODE_COUPLE:
        proj = h @ th
        return h - proj[..., None] * th + (a * sigma) * th
    if mode == MODE_SHIFT:
        return h + (a * sigma) * th
    if mode == MODE_BASELINE:
        return h
    raise ResidualInterventionError(f"unknown mode {mode!r}")


# ---------------------------------------------------------------------------
# arm parsing + write-hook mechanism
# ---------------------------------------------------------------------------

def build_intervention_spec(direction: dict[str, Any]) -> dict[str, Any]:
    """Validate a fitted direction dict -> ``{layer, block, theta(unit), sigma}``."""
    layer = int(direction["layer"])
    if layer <= 0:
        raise ResidualInterventionError("layer 0 is embeddings; pick a decoder-block layer")
    theta = np.asarray([float(t) for t in direction["theta"]], dtype=np.float64)
    theta = _unit(theta)
    sigma = float(direction["sigma"])
    if sigma <= 0:
        raise ResidualInterventionError(f"sigma must be positive, got {sigma}")
    return {"layer": layer, "block": layer - 1, "theta": [float(v) for v in theta], "sigma": sigma}


def parse_arms(arms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize arm dicts: each is ``{arm_id, mode, alpha}``.

    ``baseline`` registers no hook; ``ablate`` ignores alpha; ``shift`` uses alpha
    (in sigma units, may be negative). ``couple`` (Amendment AC) carries
    ``gain_map`` (path to a doubt-gain-map JSON) + ``gain_key`` ("gains" or
    "gains_permuted"); its per-row alpha is resolved by the runner and the
    arm-level alpha stays 0.0.
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for arm in arms:
        arm_id = str(arm["arm_id"])
        mode = str(arm.get("mode", MODE_BASELINE))
        if mode not in (MODE_BASELINE, MODE_ABLATE, MODE_SHIFT, MODE_COUPLE):
            raise ResidualInterventionError(f"arm {arm_id!r}: unknown mode {mode!r}")
        if arm_id in seen:
            raise ResidualInterventionError(f"duplicate arm_id {arm_id!r}")
        seen.add(arm_id)
        rec = {"arm_id": arm_id, "mode": mode, "alpha": float(arm.get("alpha", 0.0))}
        if mode == MODE_COUPLE:
            if not arm.get("gain_map"):
                raise ResidualInterventionError(f"arm {arm_id!r}: couple mode requires gain_map")
            gain_key = str(arm.get("gain_key", "gains"))
            if gain_key not in ("gains", "gains_permuted"):
                raise ResidualInterventionError(
                    f"arm {arm_id!r}: gain_key must be 'gains' or 'gains_permuted', got {gain_key!r}")
            rec["gain_map"] = str(arm["gain_map"])
            rec["gain_key"] = gain_key
        out.append(rec)
    if not any(a["mode"] == MODE_BASELINE for a in out):
        raise ResidualInterventionError("arms must include a baseline (mode=baseline) arm")
    return out


def resolve_couple_alpha(gain_map: dict[str, Any], gain_key: str, row_key: str) -> float:
    """Per-row alpha for a couple arm. A row missing from the map is a HARD
    error (never a silent 0-gain: that would quietly turn coupled into ablate)."""
    gains = gain_map.get(gain_key)
    if not isinstance(gains, dict):
        raise ResidualInterventionError(f"gain map has no {gain_key!r} table")
    entry = gains.get(row_key)
    if entry is None:
        raise ResidualInterventionError(f"row {row_key!r} missing from gain map {gain_key!r}")
    return float(entry["gain"])


def make_residual_write_hook(spec: dict[str, Any], arm: dict[str, Any]):
    """Forward POST-hook that rewrites the block output per the arm's intervention.

    Applies at EVERY position in the forward (prefill: all prompt positions;
    decode: the new position) so the intervention shapes the whole trajectory.

    ``arm["alpha"]`` may be a scalar or a list/tuple with one alpha per batch
    element (batched couple arms: rows with different per-row gains in one
    forward). A vector alpha must match the batch size seen by the hook.
    """
    mode = arm["mode"]
    raw_alpha = arm["alpha"]
    alpha_vec: Optional[list[float]] = (
        [float(v) for v in raw_alpha]
        if isinstance(raw_alpha, (list, tuple)) else None)
    alpha_scalar = 0.0 if alpha_vec is not None else float(raw_alpha)
    sigma = float(spec["sigma"])
    theta_list = spec["theta"]

    def _alpha_sigma(hs: Any):
        """Scalar alpha*sigma, or a [batch, 1, ..., 1] tensor of per-row
        alpha*sigma broadcasting over positions."""
        if alpha_vec is None:
            return alpha_scalar * sigma
        if hs.shape[0] != len(alpha_vec):
            raise ResidualInterventionError(
                f"alpha vector length {len(alpha_vec)} does not match "
                f"batch size {hs.shape[0]}")
        a = hs.new_tensor(alpha_vec)
        return a.reshape([hs.shape[0]] + [1] * (hs.dim() - 1)) * sigma

    def _hook(_module: Any, _args: tuple[Any, ...], output: Any):
        is_tuple = isinstance(output, tuple)
        hs = output[0] if is_tuple else output
        th = hs.new_tensor(theta_list)
        if mode == MODE_ABLATE:
            proj = hs @ th  # [batch, seq]
            hs2 = hs - proj.unsqueeze(-1) * th
        elif mode == MODE_COUPLE:
            proj = hs @ th  # [batch, seq]
            hs2 = hs - proj.unsqueeze(-1) * th + _alpha_sigma(hs) * th
        elif mode == MODE_SHIFT:
            hs2 = hs + _alpha_sigma(hs) * th
        else:  # baseline should not register a hook, but be safe
            return None
        return (hs2, *output[1:]) if is_tuple else hs2

    return _hook


@contextmanager
def residual_intervention(model: Any, spec: dict[str, Any], arm: dict[str, Any]):
    """Register the write hook on the target decoder block; remove on exit.

    A baseline arm yields without registering any hook (true no-op forward).
    """
    if arm["mode"] == MODE_BASELINE:
        yield
        return
    from phase3_causal_pilot_runner import find_decoder_layers  # noqa: PLC0415

    layers = find_decoder_layers(model)
    block = spec["block"]
    if not (0 <= block < len(layers)):
        raise ResidualInterventionError(
            f"target block {block} out of range for {len(layers)} decoder layers")
    handle = layers[block].register_forward_hook(make_residual_write_hook(spec, arm))
    try:
        yield
    finally:
        handle.remove()


# ---------------------------------------------------------------------------
# refusal-rate aggregation + load-bearing verdict (offline)
# ---------------------------------------------------------------------------

def _rate(rows: list[dict[str, Any]], field: str) -> float:
    vals = [bool(r.get(field)) for r in rows if r.get(field) is not None]
    return float(np.mean(vals)) if vals else float("nan")


def analyze_arms(rows: list[dict[str, Any]], *, drop_tol: float = 0.15,
                 groups: tuple[str, ...] = DEFAULT_GROUPS) -> dict[str, Any]:
    """Refusal rate per (arm, baseline behavior group) + a load-bearing verdict.

    ``rows`` carry ``arm_id``, ``behavior_cell`` (the row's BASELINE group), and
    ``refused``/``correct`` from re-scored generation under that arm. ``groups``
    defaults to the B1 pair; Amendment AC passes the three-cell tuple including
    ``unknown_refused`` (the verdict logic still keys on the B1 pair only).
    """
    arm_ids = sorted({r["arm_id"] for r in rows})
    groups = list(groups)
    table: dict[str, dict[str, Any]] = {}
    for arm_id in arm_ids:
        arm_rows = [r for r in rows if r["arm_id"] == arm_id]
        cell: dict[str, Any] = {}
        for g in groups:
            grp = [r for r in arm_rows if r.get("behavior_cell") == g]
            cell[g] = {
                "n": len(grp),
                "refusal_rate": round(_rate(grp, "refused"), 4),
                "correct_rate": round(_rate(grp, "correct"), 4),
            }
        table[arm_id] = cell

    base = table.get(BASELINE_ARM)
    verdict = _verdict(table, drop_tol=drop_tol) if base else \
        "INCONCLUSIVE: no baseline arm present."
    return {
        "ok": True,
        "analysis_type": "phase3_residual_intervention",
        "n_rows": len(rows),
        "arms": arm_ids,
        "by_arm": table,
        "verdict": verdict,
    }


def _verdict(table: dict[str, dict[str, Any]], *, drop_tol: float) -> str:
    base = table[BASELINE_ARM]
    base_ref = base[KNOWN_REFUSED]["refusal_rate"]
    ablate = table.get("ablate")
    if ablate is None:
        return (f"NO-ABLATE-ARM: baseline known_refused refusal={base_ref:.2f}; "
                f"add an 'ablate' arm to test load-bearingness.")
    abl_ref = ablate[KNOWN_REFUSED]["refusal_rate"]
    abl_ctrl = ablate[KNOWN_ANSWERED]["refusal_rate"]
    base_ctrl = base[KNOWN_ANSWERED]["refusal_rate"]
    if not (np.isfinite(base_ref) and np.isfinite(abl_ref)):
        return "INCONCLUSIVE: known_refused group empty in baseline or ablate arm."
    drop = base_ref - abl_ref
    ctrl_rise = (abl_ctrl - base_ctrl) if (np.isfinite(abl_ctrl) and np.isfinite(base_ctrl)) else float("nan")
    if drop >= drop_tol:
        spec_msg = ""
        if np.isfinite(ctrl_rise):
            spec_msg = (f" Specificity: ablating raised known_answered refusal by "
                        f"{ctrl_rise:+.2f} (want ~0).")
        return (
            f"LOAD-BEARING: ablating the caution axis at the target layer drops "
            f"known_refused refusal by {drop:.2f} ({base_ref:.2f} -> {abl_ref:.2f}); "
            f"the encoded caution state is causally load-bearing for the over-refusal.{spec_msg}"
        )
    if drop <= -drop_tol:
        return (
            f"INVERTED: ablating the caution axis INCREASED known_refused refusal "
            f"({base_ref:.2f} -> {abl_ref:.2f}); an anti-steerable-style sign, report and inspect."
        )
    return (
        f"NOT-LOAD-BEARING (single-site): ablating at the target layer barely moves "
        f"known_refused refusal ({base_ref:.2f} -> {abl_ref:.2f}, drop {drop:+.2f} < tol "
        f"{drop_tol:.2f}). The L35 caution read may be a correlate or re-derived downstream; "
        f"next try a multi-layer ablation band."
    )


def run_analysis(rows_path: Path, out_path: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    summary = analyze_arms(rows)
    summary["rows"] = str(rows_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    summary["_written"] = str(out_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    summary = run_analysis(args.rows, args.out)
    print(f"VERDICT: {summary['verdict']}", file=sys.stderr)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
