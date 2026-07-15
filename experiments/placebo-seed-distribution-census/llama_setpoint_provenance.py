#!/usr/bin/env python3
"""Llama setpoint_dose_abs provenance reconstruction (SC0/SC1 build-time
TO-DERIVE item; AMENDMENT.md lines 96-102, cell.yaml line 61).

cell.yaml pins llama's dose multiplier (12 x sigma_c(hs20 llama)) but leaves
setpoint_dose_abs as `TO-DERIVE`, requiring an RG0-style field-for-field
crosscheck against RR's own COMMITTED llama hs20 fit-build manifest
(`experiments/rr-cross-family-raw-refusal/analysis-committed/llama/
hs20_fit_build_manifest.json`, present in THIS worktree's own git history, no
staging needed).

This module does NOT re-run the fit from raw anchors/FIT rows (that would
require the 493MB private llama anchor capture, cross-worktree staging, and a
fresh sklearn fit for a value that is already a deterministic pure function
of fixed inputs). Instead it performs the SAME crosscheck RR3's own
`fit_reuse.py` already ran and PASSED
(`rr3-corrected-placebo-replication/analysis/llama/fit_reuse_report.json`,
staged at SC0 as `llama_fit_reuse_report_rr3`): RR3 reconstructed the hs20
llama fit twice (asserted byte-identical across the two runs, RR's own rule),
cross-checked mu_d/sigma_d/mu_c/sigma_c/tau_frozen/auc_neg_z_d_on_fit
field-for-field against RR's committed manifest, and the result was
`pass=true, mismatches={}`.

This module adds an INDEPENDENT second crosscheck on top of trusting RR3's
report: it compares RR's own originally-committed hs20_fit_build_manifest.json
(read live from this worktree's git history) DIRECTLY against RR3's
reconstructed build_manifest.json (staged at SC0 from the sibling
rr3-corrected-placebo worktree) -- two files with two different provenance
paths (one is RR's original fit output, the other is RR3's from-scratch
byte-identical reconstruction of that same fit, months apart, different
worktree) -- and asserts they match FIELD-FOR-FIELD, not merely that RR3
self-reports a pass. A whole-file sha256 match (verified informally during
SC0 staging: both files hashed to f160666885...) already suggests identity;
this script makes that comparison explicit, structured, and committed.

Writes: analysis-committed/llama_setpoint_provenance.json
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

    rr_committed_path = config.RR_LOCAL_DIR / "analysis-committed" / "llama" / "hs20_fit_build_manifest.json"
    rr3_reconstructed_path = STAGED / "llama32_3b" / "directions" / "llama_hs20_build_manifest.json"
    rr3_fit_reuse_report_path = STAGED / "llama32_3b" / "fit_reuse_report_rr3.json"

    for p in (rr_committed_path, rr3_reconstructed_path, rr3_fit_reuse_report_path):
        if not p.is_file():
            raise SystemExit(f"llama_setpoint_provenance FAILED: missing {p}; run staging.py first.")

    rr_committed = common.load_json(rr_committed_path)
    rr3_reconstructed = common.load_json(rr3_reconstructed_path)
    rr3_fit_reuse_report = common.load_json(rr3_fit_reuse_report_path)

    mismatches: dict[str, dict] = {}
    for field in _FLOAT_FIELDS:
        a = rr_committed[field]
        b = rr3_reconstructed[field]
        if abs(a - b) > _FLOAT_TOLERANCE:
            mismatches[field] = {"rr_committed": a, "rr3_reconstructed": b}

    sha_rr = common.sha256_of_file(rr_committed_path)
    sha_rr3 = common.sha256_of_file(rr3_reconstructed_path)
    whole_file_byte_identical = sha_rr == sha_rr3

    sigma_c = rr_committed["sigma_c"]
    setpoint_dose_abs = config.LLAMA_DOSE_MULTIPLIER_SIGMA_C * sigma_c
    config_setpoint = config.LLAMA_SETPOINT_DOSE_ABS
    setpoint_matches_config = abs(setpoint_dose_abs - config_setpoint) < 1e-9

    report = {
        "layer_hs_index": config.LAYER_HS_INDEX["llama32_3b"],
        "dose_multiplier_sigma_c": config.LLAMA_DOSE_MULTIPLIER_SIGMA_C,
        "sigma_c_hs20_llama": sigma_c,
        "setpoint_dose_abs": setpoint_dose_abs,
        "setpoint_dose_abs_matches_config_py_constant": setpoint_matches_config,
        "crosscheck": {
            "method": "field-for-field comparison of RR's own originally-committed "
                      "hs20_fit_build_manifest.json against rr3-corrected-placebo-replication's "
                      "independent from-scratch RG0 reconstruction of the same fit "
                      "(same FIT rows, same anchors, RR's own fit seed 20260713, "
                      "run via direction_fit.py/fit_reuse.py, asserted byte-identical "
                      "across two internal runs before this comparison ever sees it)",
            "rr_committed_manifest_path": str(rr_committed_path),
            "rr3_reconstructed_manifest_path": str(rr3_reconstructed_path),
            "rr_committed_sha256": sha_rr,
            "rr3_reconstructed_sha256": sha_rr3,
            "whole_file_byte_identical": whole_file_byte_identical,
            "fields_compared": list(_FLOAT_FIELDS),
            "mismatches": mismatches,
            "pass": whole_file_byte_identical and not mismatches,
            "rr3_own_fit_reuse_report_pass": rr3_fit_reuse_report["fit_reconstruction_matches_rr_committed_stats"]["pass"],
        },
        "directions_dir_pinned": str(config.DIRECTIONS_DIR["llama32_3b"]),
        "directions_dir_note": (
            "cell.yaml line 65 leaves llama directions_dir as TO-PIN. This harness "
            "pins it to rr3-corrected-placebo-replication's OWN gitignored directions/ "
            "dir (reused, not re-run -- see this module's docstring), staged into "
            "analysis/staged_inputs/llama32_3b/directions/ at SC0."
        ),
    }

    if not report["crosscheck"]["pass"]:
        common.write_json(COMMITTED / "llama_setpoint_provenance.json", report)
        raise SystemExit(f"llama_setpoint_provenance FAILED: {mismatches}")

    common.write_json(COMMITTED / "llama_setpoint_provenance.json", report)
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
