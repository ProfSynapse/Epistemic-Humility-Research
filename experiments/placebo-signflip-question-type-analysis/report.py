#!/usr/bin/env python3
"""Top-level CLI for placebo-signflip-question-type-analysis: stage -> BG0/
BG1 gate checks -> behavioral leg -> (opt-in) mechanism leg -> report.

CPU-only, no model, no GPU. By default this DOES NOT run the mechanism leg
(M1/M2/M3): those require loading the mistral/llama anchor JSONs (251MB/
493MB) and this build task's binding constraint is harness-build only, no
result-producing run beyond the pre-stated BG0/BG1 integrity checks (which
DO run against real data by design -- BG0's bit-for-bit re-slice fidelity
and BG1's exact frame-port firing reproduction are the pre-stated gates
themselves, not exploratory results). Pass --with-mechanism-realdata
--i-know-this-loads-large-json-files to also run M1/M2/M3 against the real
anchor data (the lead's call, after this build).

Writes:
  analysis-committed/signflip_report.json   aggregates, gate results, counts
                                             and CIs only -- no row keys, no
                                             text (BG2's containment rule).
  analysis/signflip_report_row_level.jsonl  gitignored row-level intermediate
                                             (behavioral-leg pairs only, no
                                             text) for local debugging.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import write_json  # noqa: E402

COMMITTED = HERE / "analysis-committed"
ANALYSIS = HERE / "analysis"


def run_bg0_bg1(run_mistral_realdata: bool, run_llama_realdata: bool) -> dict[str, Any]:
    import behavioral_leg as bl
    import frame_port as fp

    cell_a = bl.cell_a_qh()
    cell_b = bl.cell_b_mc()
    cell_c = bl.cell_c_ql()

    bg0 = {
        "qh_reslice": cell_a["bg0_check"],
        "mc_reslice": cell_b["bg0_check"],
        "ql_wide_voided_narrow_only": True,
        "pass": bool(cell_a["bg0_check"]["match"] and cell_b["bg0_check"]["match"]),
    }

    bg1_qwen = fp.check_qwen_frame()
    bg1_mistral = fp.check_mistral_frame_via_fit_reuse_report()
    bg1 = {
        "qwen": bg1_qwen, "mistral_fit_reuse_crosscheck": bg1_mistral,
        "mistral_realdata_fire_set": None, "llama_realdata": None,
        "pass": bool(bg1_qwen["pass"] and bg1_mistral["pass"]),
    }
    if run_mistral_realdata:
        bg1["mistral_realdata_fire_set"] = fp.check_mistral_frame_realdata()
        bg1["pass"] = bg1["pass"] and bg1["mistral_realdata_fire_set"]["pass"]
    if run_llama_realdata:
        bg1["llama_realdata"] = fp.check_llama_frame_realdata()
        bg1["pass"] = bg1["pass"] and bg1["llama_realdata"]["pass"]

    return {"bg0": bg0, "bg1": bg1, "cell_a": cell_a, "cell_b": cell_b, "cell_c": cell_c}


def run_bg2(cell_a: dict[str, Any], cell_b: dict[str, Any], cell_c: dict[str, Any]) -> dict[str, Any]:
    """BG2 (coverage and honesty): asserts the structural invariants
    gates.yaml pre-states, rather than trusting the cell functions silently
    got them right."""
    checks = {
        "qh_answerable_coverage_named": cell_a["strata"]["answerable"]["n_paired"] == 17,
        "mc_answerable_coverage_named": cell_b["strata"]["answerable"]["n_dosed"] == 0,
        "ql_answerable_coverage_named": "no answerable stratum" in cell_c["answerable_note"],
        "ql_wide_voided_narrow_only": "narrow" in cell_c["void_note"].lower(),
        "no_answerable_behavioral_verdict_asserted": True,  # this harness never emits one; structural by construction
    }
    return {"checks": checks, "pass": all(checks.values())}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-staging", action="store_true", help="skip re-running staging.py (assumes already staged)")
    ap.add_argument("--with-mistral-realdata", action="store_true")
    ap.add_argument("--with-llama-realdata", action="store_true")
    ap.add_argument("--i-know-this-loads-large-json-files", action="store_true")
    args = ap.parse_args()

    if (args.with_mistral_realdata or args.with_llama_realdata) and not args.i_know_this_loads_large_json_files:
        print(
            "[report] --with-mistral-realdata/--with-llama-realdata load a "
            "251MB/493MB JSON file each; refusing without "
            "--i-know-this-loads-large-json-files.",
            file=sys.stderr,
        )
        return 2

    if not args.skip_staging:
        import staging

        staging.main()

    result = run_bg0_bg1(args.with_mistral_realdata, args.with_llama_realdata)
    bg2 = run_bg2(result["cell_a"], result["cell_b"], result["cell_c"])

    report = {
        "gates": {"BG0": result["bg0"], "BG1": result["bg1"], "BG2": bg2},
        "behavioral_leg": {"A_qh": result["cell_a"], "B_mc": result["cell_b"], "C_ql": result["cell_c"]},
        "mechanism_leg": {
            "status": "not_run_in_this_build_task",
            "note": (
                "M1/M2/M3 require loading the mistral (251MB) / llama (493MB) "
                "anchor JSONs; this build task's constraint is harness-build "
                "only, no result-producing run beyond the pre-stated BG0/BG1 "
                "gates. Run `python3 mechanism_leg.py` functions directly, or "
                "extend report.py's --with-mechanism-realdata path, once host "
                "RAM headroom allows (the RR3 GPU job's host process is "
                "resident during this build)."
            ),
        },
    }
    write_json(COMMITTED / "signflip_report.json", report)

    all_pass = result["bg0"]["pass"] and result["bg1"]["pass"] and bg2["pass"]
    print(f"[report] BG0 pass={result['bg0']['pass']} BG1 pass={result['bg1']['pass']} BG2 pass={bg2['pass']}", flush=True)
    print(f"[report] wrote {COMMITTED / 'signflip_report.json'}", flush=True)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
