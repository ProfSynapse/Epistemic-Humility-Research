#!/usr/bin/env python3
"""Fit-REUSE module (RG0) for rr3-corrected-placebo-replication.

Two-family generalization of
`experiments/rr2-mistral-adjudicated-refusal-confirm/fit_reuse.py` (read in
full before writing this): reconstructs u_d/c_hat/random_direction/stats at
the ONE fixed operating layer per family (mistral hs16, llama hs20; both
locked in cell.yaml, no sweep, no selection freedom) by calling
`direction_fit.fit_directions` (ported verbatim as `direction_fit.py`) on
the SAME FIT rows and anchors RR's own `rr-cross-family-raw-refusal` cell
used, at the SAME seed RR used for each family's fit
(`rr-cross-family-raw-refusal` seed 20260713 for both families -- this
experiment's OWN seed, 20260714, governs only THIS experiment's fresh
random_direction placebo draws and pool/subsample seeding, never the
reconstructed fit itself; see cell.yaml `core_cell.fixed_operating_point.
fit_reuse_note` and `rider_cells.rider_llama_placebo_ladder.fit_reuse_note`).

Unlike RR2 (which transcribed RR's committed hs16 stats into cell.yaml's own
`rr_reference_values` block and cross-checked against that transcription),
this module reads RR's committed fit-build manifests DIRECTLY off disk at
reconstruct time --
`rr-cross-family-raw-refusal/analysis-committed/mistral/
hs16_fit_build_manifest.json` and `.../llama/hs20_fit_build_manifest.json`
(cell.yaml's `core_cell.fixed_operating_point.rr_reference_manifest` names
the mistral path explicitly; the llama path is the analogous file the
rider's `fit_reuse_note` references) -- rather than trusting a second,
hand-transcribed copy. This removes one transcription-error surface RR2 had
(cell.yaml's rr_reference_values were themselves "transcribed... not trusted
blind" and re-verified anyway) without adding any new fit DECISION: the
values being cross-checked against are still exactly RR's own already-
committed, already-locked numbers, just read once instead of copied twice.

Verification, per family, mirrors RR2 exactly:
  1. RR's own `fit_byte_identical` rule: fit twice here, assert identical.
  2. Field-for-field cross-check of mu_d/sigma_d/mu_c/sigma_c/tau_frozen/
     auc_neg_z_d_on_fit against RR's committed manifest. Any mismatch is an
     RG0 hard stop (`fit_reconstruction_matches_rr_committed_stats`).

Reconstructed vectors are written to
`directions/{family}_hs{layer}_{u_d,c_hat,random_direction}.json`
(gitignored, large local data, never committed), NOT to
`analysis-committed/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
RR_DIR = REPO_ROOT / "rr-cross-family-raw-refusal"
if not RR_DIR.is_dir():
    RR_DIR = REPO_ROOT / "experiments" / "rr-cross-family-raw-refusal"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import direction_fit  # noqa: E402
import materialize_rows as mrows  # noqa: E402

DIRECTIONS = HERE / "directions"
ANALYSIS = HERE / "analysis"

# This experiment's OWN base seed (cell.yaml `seed: 20260714`) governs fresh
# draws (random_direction placebo seeds, pool/subsample seeding) only. The
# FIT reconstruction seed below is RR's OWN fit seed, unchanged, because
# fit_directions is a pure function of (rows, H, layer, hidden_dim, seed) and
# reconstructing RR's frozen fit byte-identical requires RR's original seed,
# not this experiment's.
RR_FIT_SEED = 20260713

FAMILY_TO_LAYER = {"mistral": 16, "llama": 20}
FAMILY_TO_RR_MANIFEST = {
    "mistral": RR_DIR / "analysis-committed" / "mistral" / "hs16_fit_build_manifest.json",
    "llama": RR_DIR / "analysis-committed" / "llama" / "hs20_fit_build_manifest.json",
}

_FLOAT_FIELDS = ("mu_d", "sigma_d", "mu_c", "sigma_c", "tau_frozen", "auc_neg_z_d_on_fit")
_FLOAT_TOLERANCE = 1e-9


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_to_list), encoding="utf-8")


def _to_list(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"not JSON serializable: {type(obj)!r}")


def load_rr_reference_values(family: str) -> dict[str, Any]:
    path = FAMILY_TO_RR_MANIFEST[family]
    if not path.is_file():
        raise SystemExit(
            f"missing RR's committed fit-build manifest for family={family!r}: {path}. "
            f"This module cross-checks against RR's own already-committed numbers; "
            f"it does not reconstruct a fresh reference."
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for field in _FLOAT_FIELDS + ("hidden_dim",):
        if field not in manifest:
            raise SystemExit(f"RR committed manifest {path} is missing required field {field!r}")
    return manifest


def reconstruct(fit_rows: list[dict[str, Any]], H: dict[str, np.ndarray], layer: int, hidden_dim: int) -> dict[str, Any]:
    """Runs `direction_fit.fit_directions` TWICE at `layer` and asserts
    byte-identical (RR's own rule), then computes the frozen gate
    (`fit_gate`) exactly as RR's `dose_ladder.py:fit_all_layers` does."""
    fit1 = direction_fit.fit_directions(fit_rows, H, layer, hidden_dim, RR_FIT_SEED)
    fit2 = direction_fit.fit_directions(fit_rows, H, layer, hidden_dim, RR_FIT_SEED)
    if not direction_fit.fit_byte_identical(fit1, fit2):
        raise SystemExit(f"fit_reuse RG0 FAIL (layer {layer}): reconstruction is not byte-identical across two calls")
    gate = direction_fit.fit_gate(fit1)
    return {"fit": fit1, "gate": gate}


def cross_check_against_rr_committed(reconstructed: dict[str, Any], rr_reference_values: dict[str, Any]) -> dict[str, Any]:
    """Field-for-field comparison of the reconstruction's stats against RR's
    OWN committed hs{layer}_fit_build_manifest.json, read live off disk (see
    module docstring). This is the check that makes "reconstruction, not a
    new fit" verifiable rather than asserted."""
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
    family = args.family
    layer = FAMILY_TO_LAYER[family]
    rr_reference_values = load_rr_reference_values(family)

    joined_path = ANALYSIS / family / "joined_rows_private.jsonl"
    if not joined_path.is_file():
        raise SystemExit(f"missing {joined_path}; run `materialize_rows.py --family {family}` first (requires staged private inputs).")
    rows = mrows.load_jsonl(joined_path)
    fit_confab = [r for r in rows if r["role"] == "confab" and r.get("split") == "fit"]
    fit_known = [r for r in rows if r["role"] == "known_correct_answered" and r.get("split") == "fit"]
    unknown = [r for r in rows if r["role"] == "unknown_refused"]
    fit_rows = fit_confab + fit_known + unknown

    anchor_path = ANALYSIS / family / "anchors_at_candidate_layer.json"
    if not anchor_path.is_file():
        raise SystemExit(f"missing {anchor_path}; run `materialize_rows.py --family {family}` first.")
    raw_anchors = json.loads(anchor_path.read_text())
    H = {rk: np.asarray(per[str(layer)], dtype=np.float64) for rk, per in raw_anchors.items() if str(layer) in per}

    hidden_dim = rr_reference_values["hidden_dim"]
    reconstructed = reconstruct(fit_rows, H, layer, hidden_dim)
    check = cross_check_against_rr_committed(reconstructed, rr_reference_values)

    report = {
        "family": family, "layer": layer, "rr_fit_seed": RR_FIT_SEED,
        "n_fit_confab": len(fit_confab), "n_fit_known": len(fit_known), "n_unknown": len(unknown),
        "fit_reconstruction_matches_rr_committed_stats": check,
    }
    _write_json(ANALYSIS / family / "fit_reuse_report.json", report)
    if not check["pass"]:
        raise SystemExit(
            f"fit_reuse RG0 FAIL (family={family}): reconstruction does not match RR's "
            f"committed hs{layer}_fit_build_manifest.json: {check['mismatches']}"
        )

    fit = reconstructed["fit"]
    prefix = f"{family}_hs{layer}"
    _write_json(DIRECTIONS / f"{prefix}_u_d.json", {"vector": fit["u_d"], "layer": layer, "family": family})
    _write_json(DIRECTIONS / f"{prefix}_c_hat.json", {"vector": fit["c_hat"], "layer": layer, "family": family})
    _write_json(DIRECTIONS / f"{prefix}_random_direction.json", {"vector": fit["random_direction"], "layer": layer, "family": family, "sigma": 1.0})
    _write_json(DIRECTIONS / f"{prefix}_build_manifest.json", {**reconstructed["gate"], **fit["stats"]})

    print(json.dumps(report, indent=2, default=_to_list), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("reconstruct", help="reconstruct u_d/c_hat/random_direction at this family's fixed layer, cross-check against RR's committed stats")
    p.add_argument("--family", required=True, choices=sorted(FAMILY_TO_LAYER))
    p.set_defaults(func=cmd_reconstruct)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
