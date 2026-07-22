#!/usr/bin/env python3
"""Mistral hs16 direction reconstruction provenance (Decision record item 14,
TO-DERIVE at build; SC0 `frozen_operating_point.mistral`).

AMENDMENT.md: "reconstruct the hs16 c_hat and random_direction byte-identical
from RR's committed hs16_fit_build_manifest via RR2 fit_reuse.py (RG0),
exactly as RR2/RR3 did." This module does NOT re-run the fit from raw
anchors/FIT rows (RR2's own `analysis/anchors_at_candidate_layers.json` is a
250MB private artifact; re-deriving would require importing RR2's
`direction_fit.py`/`materialize_rows.py` and re-running an sklearn fit for a
value that is already a deterministic pure function of fixed inputs RR2
already computed once). Instead, mirroring
`placebo-seed-distribution-census/llama_setpoint_provenance.py`'s
established pattern exactly: it reuses RR2's OWN already-reconstructed
hs16_{u_d,c_hat,random_direction,build_manifest}.json (staged at SC0,
`staging.py` `mistral_hs16_*` entries) and performs an INDEPENDENT
field-for-field crosscheck of RR2's reconstructed build_manifest.json against
RR's own originally-committed `hs16_fit_build_manifest.json`
(experiments/rr-cross-family-raw-refusal/analysis-committed/mistral/, present
in THIS worktree's own git history, no staging needed), on top of trusting
RR2's own `fit_reuse_report.json` self-report (also staged, checked for
pass=true).

Writes: analysis-committed/mistral_direction_provenance.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

STAGED = HERE / "analysis" / "staged_inputs"
COMMITTED = HERE / "analysis-committed"

_FLOAT_FIELDS = ("mu_d", "sigma_d", "mu_c", "sigma_c", "tau_frozen", "auc_neg_z_d_on_fit")
_FLOAT_TOLERANCE = 1e-9


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    rr_committed_path = config.RR_LOCAL_DIR / "analysis-committed" / "mistral" / "hs16_fit_build_manifest.json"
    rr2_reconstructed_path = STAGED / "mistral7b_v03" / "directions" / "hs16_build_manifest.json"
    rr2_fit_reuse_report_path = STAGED / "mistral7b_v03" / "fit_reuse_report_rr2.json"

    for p in (rr_committed_path, rr2_reconstructed_path, rr2_fit_reuse_report_path):
        if not p.is_file():
            raise SystemExit(f"mistral_direction_provenance FAILED: missing {p}; run staging.py first.")

    rr_committed = common.load_json(rr_committed_path)
    rr2_reconstructed = common.load_json(rr2_reconstructed_path)
    rr2_fit_reuse_report = common.load_json(rr2_fit_reuse_report_path)

    mismatches: dict[str, dict] = {}
    for field in _FLOAT_FIELDS:
        a = rr_committed[field]
        b = rr2_reconstructed[field]
        if abs(a - b) > _FLOAT_TOLERANCE:
            mismatches[field] = {"rr_committed": a, "rr2_reconstructed": b}

    sha_rr = common.sha256_of_file(rr_committed_path)
    sha_rr2 = common.sha256_of_file(rr2_reconstructed_path)
    whole_file_byte_identical = sha_rr == sha_rr2

    setpoint_dose_abs = config.DOSE_MULTIPLIER_SIGMA_C["mistral7b_v03"] * rr_committed["sigma_c"]
    setpoint_matches_config = abs(setpoint_dose_abs - config.SETPOINT_DOSE_ABS["mistral7b_v03"]) < 1e-9

    rr2_report_pass = rr2_fit_reuse_report["fit_reconstruction_matches_rr_committed_stats"]["pass"]

    report = {
        "layer_hs_index": config.LAYER_HS_INDEX["mistral7b_v03"],
        "dose_multiplier_sigma_c": config.DOSE_MULTIPLIER_SIGMA_C["mistral7b_v03"],
        "sigma_c_hs16_mistral": rr_committed["sigma_c"],
        "setpoint_dose_abs": setpoint_dose_abs,
        "setpoint_dose_abs_matches_config_py_constant": setpoint_matches_config,
        "crosscheck": {
            "method": "field-for-field comparison of RR's own originally-committed "
                      "hs16_fit_build_manifest.json against RR2's own from-scratch "
                      "RG0 reconstruction of the same fit (same FIT rows, same anchors, "
                      "RR's own fit seed 20260713, run via direction_fit.py/fit_reuse.py, "
                      "asserted byte-identical across two internal runs before this "
                      "comparison ever sees it -- RR2's own fit_reuse.py rule)",
            "rr_committed_manifest_path": str(rr_committed_path),
            "rr2_reconstructed_manifest_path": str(rr2_reconstructed_path),
            "rr_committed_sha256": sha_rr,
            "rr2_reconstructed_sha256": sha_rr2,
            "whole_file_byte_identical": whole_file_byte_identical,
            "fields_compared": list(_FLOAT_FIELDS),
            "mismatches": mismatches,
            "pass": whole_file_byte_identical and not mismatches,
            "rr2_own_fit_reuse_report_pass": rr2_report_pass,
        },
        "directions_dir_staged": str(STAGED / "mistral7b_v03" / "directions"),
        "reused_not_rerun_note": (
            "This experiment does NOT re-run RR2's fit_reuse.py against RR2's own "
            "250MB anchors_at_candidate_layers.json (no GPU/model load needed for "
            "that either, but it is a large private artifact this build did not "
            "stage). Instead it reuses RR2's own reconstructed hs16 direction JSONs "
            "and independently cross-checks them against RR's committed manifest, "
            "exactly mirroring the census's llama_setpoint_provenance.py precedent."
        ),
    }

    overall_pass = report["crosscheck"]["pass"] and rr2_report_pass and setpoint_matches_config
    common.write_json(COMMITTED / "mistral_direction_provenance.json", report)
    if not overall_pass:
        raise SystemExit(f"mistral_direction_provenance FAILED: {mismatches}, rr2_own_pass={rr2_report_pass}, setpoint_matches={setpoint_matches_config}")

    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
