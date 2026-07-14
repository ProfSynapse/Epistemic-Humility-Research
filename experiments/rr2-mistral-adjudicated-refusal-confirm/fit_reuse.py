#!/usr/bin/env python3
"""Fit-REUSE module (G0) for rr2-mistral-adjudicated-refusal-confirm.

This experiment runs NO fresh FIT stage, no dose ladder, no selection logic
(cell.yaml, AMENDMENT.md "Design"): the operating point (hs16, dose 12
sigma_c) is fixed in advance, the exact rung RR's mistral FIT dose sweep
already swept and committed
(`experiments/rr-cross-family-raw-refusal/analysis-committed/mistral/
hs16_fit_build_manifest.json`). RR's own harness, however, never persisted
the RAW direction vectors (u_d, c_hat, random_direction) to that committed
manifest -- `dose_ladder.py` writes only `{**gate, **fit["stats"]}` (scalars:
mu_d, sigma_d, mu_c, sigma_c, tau_frozen, auc), never the vectors themselves,
and RR's `heldout_scorer.py` (which DOES expect `hs{layer}_c_hat.json` etc.
under `analysis-committed/`) was never exercised for real because RR's
mistral leg resolved shape F before held-out scoring ever ran. This is a
genuine gap in RR's own harness, surfaced only now that a held-out leg is
actually being run at this operating point; NOTEBOOK.md records it.

This module closes that gap WITHOUT re-opening a FIT decision: it
RECONSTRUCTS u_d/c_hat/random_direction/stats at hs16 by calling RR's own
`direction_fit.fit_directions` (ported verbatim into this experiment as
`direction_fit.py`) on the SAME FIT rows and the SAME anchors RR used, at
the SAME seed (20260713) and the SAME layer (16). Because `fit_directions`
is a pure deterministic function of (rows, H, layer_idx, hidden_dim, seed),
reconstructing it here reproduces RR's original fit byte-for-byte -- this is
verified two ways, not asserted on faith:

  1. RR's own `fit_byte_identical` rule: fit twice here, assert identical
     (mirrors G0 `directions_byte_identical`).
  2. A NEW cross-check this experiment adds: the reconstruction's
     mu_d/sigma_d/mu_c/sigma_c/tau_frozen/auc are compared FIELD-FOR-FIELD
     against cell.yaml's `fixed_operating_point.rr_reference_values`
     (themselves transcribed from RR's committed hs16_fit_build_manifest.json).
     Any mismatch is a G0 hard stop: `fit_reconstruction_matches_rr_committed_stats`.
     Passing this check is what makes "no new FIT stage" true in practice,
     not just in the prose -- a mismatch would mean this reconstruction is
     NOT actually reproducing RR's frozen point, which this experiment is not
     authorized to select around.

Reconstructed vectors are written to `directions/hs16_{u_d,c_hat,
random_direction}.json` (gitignored, matching this repo's convention that raw
direction vectors are large local data, never committed -- see .gitignore and
NOTEBOOK.md), NOT to `analysis-committed/`, which per this experiment's own
containment rule holds ID-only manifests and aggregates only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_fit  # noqa: E402
import materialize_rows as mrows  # noqa: E402

DIRECTIONS = HERE / "directions"
ANALYSIS = HERE / "analysis"
SEED = 20260713
LAYER = 16

_FLOAT_FIELDS = ("mu_d", "sigma_d", "mu_c", "sigma_c", "tau_frozen", "auc_neg_z_d_on_fit")
_FLOAT_TOLERANCE = 1e-9


def load_cell_yaml() -> dict[str, Any]:
    with (HERE / "cell.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_to_list), encoding="utf-8")


def _to_list(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"not JSON serializable: {type(obj)!r}")


def reconstruct(fit_rows: list[dict[str, Any]], H: dict[str, np.ndarray], hidden_dim: int) -> dict[str, Any]:
    """Runs `direction_fit.fit_directions` TWICE at hs16 and asserts
    byte-identical (RR's own rule), then computes the frozen gate
    (`fit_gate`) exactly as RR's `dose_ladder.py:fit_all_layers` does."""
    fit1 = direction_fit.fit_directions(fit_rows, H, LAYER, hidden_dim, SEED)
    fit2 = direction_fit.fit_directions(fit_rows, H, LAYER, hidden_dim, SEED)
    if not direction_fit.fit_byte_identical(fit1, fit2):
        raise SystemExit("fit_reuse G0 FAIL: reconstruction is not byte-identical across two calls")
    gate = direction_fit.fit_gate(fit1)
    return {"fit": fit1, "gate": gate}


def cross_check_against_rr_committed(reconstructed: dict[str, Any], rr_reference_values: dict[str, Any]) -> dict[str, Any]:
    """Field-for-field comparison of the reconstruction's stats against
    cell.yaml's `fixed_operating_point.rr_reference_values` (transcribed from
    RR's own committed hs16_fit_build_manifest.json). This is the check that
    makes "reconstruction, not a new fit" verifiable rather than asserted."""
    stats = reconstructed["fit"]["stats"]
    gate = reconstructed["gate"]
    observed = {
        "mu_d": stats["mu_d"], "sigma_d": stats["sigma_d"],
        "mu_c": stats["mu_c"], "sigma_c": stats["sigma_c"],
        "tau_frozen": gate["tau_frozen"], "auc_neg_z_d_on_fit": gate["auc_neg_z_d_on_fit"],
    }
    mismatches = {}
    for field in _FLOAT_FIELDS:
        expected = rr_reference_values[field]
        got = observed[field]
        if abs(expected - got) > _FLOAT_TOLERANCE:
            mismatches[field] = {"expected_rr_committed": expected, "reconstructed": got}
    return {
        "pass": not mismatches,
        "observed": observed,
        "expected": {f: rr_reference_values[f] for f in _FLOAT_FIELDS},
        "mismatches": mismatches,
    }


def cmd_reconstruct(args: argparse.Namespace) -> int:
    cell = load_cell_yaml()
    rr_reference_values = cell["fixed_operating_point"]["rr_reference_values"]

    joined_path = ANALYSIS / "joined_rows_private.jsonl"
    if not joined_path.is_file():
        raise SystemExit(f"missing {joined_path}; run materialize_rows.py first (requires staged private inputs).")
    rows = mrows.load_jsonl(joined_path)
    fit_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "fit"]
    fit_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "fit"]
    unknown = [r for r in rows if r["role"] == "unknown_refused"]
    fit_rows = fit_confab + fit_known + unknown

    anchor_path = ANALYSIS / "anchors_at_candidate_layers.json"
    if not anchor_path.is_file():
        raise SystemExit(f"missing {anchor_path}; run materialize_rows.py first.")
    raw_anchors = json.loads(anchor_path.read_text())
    H = {rk: np.asarray(per[str(LAYER)], dtype=np.float64) for rk, per in raw_anchors.items() if str(LAYER) in per}

    hidden_dim = rr_reference_values["hidden_dim"]
    reconstructed = reconstruct(fit_rows, H, hidden_dim)
    check = cross_check_against_rr_committed(reconstructed, rr_reference_values)

    report = {
        "layer": LAYER, "seed": SEED,
        "n_fit_confab": len(fit_confab), "n_fit_known": len(fit_known), "n_unknown": len(unknown),
        "fit_reconstruction_matches_rr_committed_stats": check,
    }
    _write_json(ANALYSIS / "fit_reuse_report.json", report)
    if not check["pass"]:
        raise SystemExit(
            f"fit_reuse G0 FAIL: reconstruction does not match RR's committed "
            f"hs16_fit_build_manifest.json: {check['mismatches']}"
        )

    fit = reconstructed["fit"]
    _write_json(DIRECTIONS / "hs16_u_d.json", {"vector": fit["u_d"], "layer": LAYER})
    _write_json(DIRECTIONS / "hs16_c_hat.json", {"vector": fit["c_hat"], "layer": LAYER})
    _write_json(DIRECTIONS / "hs16_random_direction.json", {"vector": fit["random_direction"], "layer": LAYER, "sigma": 1.0})
    _write_json(DIRECTIONS / "hs16_build_manifest.json", {**reconstructed["gate"], **fit["stats"]})

    print(json.dumps(report, indent=2, default=_to_list), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("reconstruct", help="reconstruct u_d/c_hat/random_direction at hs16, cross-check against RR's committed stats")
    p.set_defaults(func=cmd_reconstruct)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
