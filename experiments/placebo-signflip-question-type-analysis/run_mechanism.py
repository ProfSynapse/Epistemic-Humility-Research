#!/usr/bin/env python3
"""Mechanism-leg runner (M1/M2/M3 + the lead's pre-stated kuq-subtype-resolved
readout) for placebo-signflip-question-type-analysis.

CPU-only, no model, no GPU. This is a THIN orchestration layer: every
statistic (Mann-Whitney, bootstrap SMD, the two-stage standardized projection,
the analytic M3 displacement) is computed exclusively by the PINNED
mechanism_leg.py / frame_port.py / common.py functions, imported and called
here, never reimplemented. This module owns only:

  1. sequencing -- load qwen (small, safetensors), then mistral (251MB JSON),
     then llama (493MB JSON), one family at a time, freeing each family's
     anchor dict before the next is loaded (host-RAM discipline carried over
     from mechanism_leg.py's own loader docstrings);
  2. the category_canon (kuq subtype) lookup join, read from each family's
     already-staged joined/rows-for-steer file, and the median-based grouping
     of mechanism_leg.py's own per-row outputs by that subtype -- this is the
     lead's PRE-STATED (NOTEBOOK.md 2026-07-14 entry, before this leg ran)
     subtype-resolved descriptive readout, not a new registered analysis;
  3. merging the M1/M2/M3 + subtype-resolved results into the existing
     signflip_report.json's "mechanism" key (report.py's other sections --
     BG0/BG1/BG2/behavioral_leg -- are left exactly as report.py produced
     them; this script does not touch that logic).

No verdict, no falsifier adjudication, no scoreboard call: numbers only.
"""

from __future__ import annotations

import gc
import json
import sys
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import KUQ_SUBTYPES, load_jsonl, write_json  # noqa: E402
import mechanism_leg as ml  # noqa: E402
from staging import STAGED  # noqa: E402

COMMITTED = HERE / "analysis-committed"


def _category_lookup(path: Path) -> dict[str, str | None]:
    return {r["row_key"]: r.get("category_canon") for r in load_jsonl(path)}


def _subtype_resolved(
    projected: list[dict[str, Any]],
    category_lookup: dict[str, str | None],
    displacement_by_key: dict[str, float] | None,
) -> dict[str, Any]:
    """Per-kuq-subtype (unanswerable stratum only, by construction of
    KUQ_SUBTYPES): n, median raw/standardized doubt+caution projection, and
    (if displacement_by_key given) median M3 realized caution-axis
    displacement. Descriptive grouping only -- no new statistic beyond what
    project_population/m3_row_displacement already computed per row."""
    out: dict[str, Any] = {}
    unanswerable = [r for r in projected if r["question_type"] == "unanswerable"]
    for subtype in KUQ_SUBTYPES:
        rows = [r for r in unanswerable if category_lookup.get(r["row_key"]) == subtype]
        entry: dict[str, Any] = {
            "n": len(rows),
            "median_proj_d": median(r["proj_d"] for r in rows) if rows else None,
            "median_z_d": median(r["z_d"] for r in rows) if rows else None,
            "median_proj_c": median(r["proj_c"] for r in rows) if rows else None,
            "median_z_c": median(r["z_c"] for r in rows) if rows else None,
        }
        if displacement_by_key is not None:
            disp = [displacement_by_key[r["row_key"]] for r in rows if r["row_key"] in displacement_by_key]
            entry["n_displacement"] = len(disp)
            entry["median_m3_displacement"] = median(disp) if disp else None
        out[subtype] = entry
    covered = sum(v["n"] for v in out.values())
    out["_coverage_note"] = f"{covered}/{len(unanswerable)} unanswerable anchors matched a named kuq subtype"
    return out


def _unanswerable_stats(projected: list[dict[str, Any]]) -> dict[str, float]:
    unanswerable_zd = np.array([r["z_d"] for r in projected if r["question_type"] == "unanswerable"])
    unanswerable_zc = np.array([r["z_c"] for r in projected if r["question_type"] == "unanswerable"])
    return {
        "mean_z_d": float(unanswerable_zd.mean()), "std_z_d": float(unanswerable_zd.std(ddof=1)),
        "mean_z_c": float(unanswerable_zc.mean()), "std_z_c": float(unanswerable_zc.std(ddof=1)),
    }


# ---------------------------------------------------------------------------
# Per-family runs
# ---------------------------------------------------------------------------

def run_qwen() -> dict[str, Any]:
    fam = ml.load_qwen_family()
    projected = ml.project_population(
        fam["anchors"], fam["u_d"], fam["c_hat"], fam["mu_d"], fam["sigma_d"], fam["mu_c"], fam["sigma_c"],
    )
    m1_doubt = ml.m1_contrast(projected, "z_d")
    m1_caution = ml.m1_contrast(projected, "z_c")
    m3 = ml.m3_contrast(fam["anchors"], fam["r_hat"], fam["c_hat"], fam["dose_abs"])
    displacement_by_key = {
        rk: ml.m3_row_displacement(np.asarray(h, dtype=np.float64), fam["r_hat"], fam["c_hat"], fam["dose_abs"])
        for rk, h in fam["anchors"].items()
    }
    category_lookup = _category_lookup(STAGED / "qh" / "heldout_rows_for_steer.jsonl")
    subtype = _subtype_resolved(projected, category_lookup, displacement_by_key)
    stats = _unanswerable_stats(projected)
    result = {
        "family": "qwen35-4b", "layer": "hs20",
        "m1_doubt": m1_doubt, "m1_caution": m1_caution, "m3": m3,
        "subtype_resolved": subtype, "unanswerable_stats": stats,
    }
    del fam, projected, displacement_by_key, category_lookup
    gc.collect()
    return result


def run_mistral() -> dict[str, Any]:
    fam = ml.load_mistral_family_realdata()
    projected = ml.project_population(
        fam["anchors"], fam["u_d"], fam["c_hat"], fam["mu_d"], fam["sigma_d"], fam["mu_c"], fam["sigma_c"],
    )
    m1_doubt = ml.m1_contrast(projected, "z_d")
    m1_caution = ml.m1_contrast(projected, "z_c")
    m3 = ml.m3_contrast(fam["anchors"], fam["r_hat"], fam["c_hat"], fam["dose_abs"])
    displacement_by_key = {
        rk: ml.m3_row_displacement(np.asarray(h, dtype=np.float64), fam["r_hat"], fam["c_hat"], fam["dose_abs"])
        for rk, h in fam["anchors"].items()
    }
    category_lookup = _category_lookup(STAGED / "mc" / "joined_rows_private.jsonl")
    subtype = _subtype_resolved(projected, category_lookup, displacement_by_key)
    stats = _unanswerable_stats(projected)
    result = {
        "family": "mistral7b-v03", "layer": "hs16",
        "m1_doubt": m1_doubt, "m1_caution": m1_caution, "m3": m3,
        "subtype_resolved": subtype, "unanswerable_stats": stats,
    }
    del fam, projected, displacement_by_key, category_lookup
    gc.collect()
    return result


def run_llama(layers: tuple[int, ...] = (20, 22, 23)) -> dict[str, Any]:
    """M1 + subtype-resolved projection only (no M3: no placebo arm ran for
    llama, shape F, per AMENDMENT.md / cell.yaml mechanism_probe.llama32-3b
    contrasts = [M1, M2])."""
    category_lookup = _category_lookup(STAGED / "llama" / "joined_rows_private.jsonl")
    per_layer: dict[str, Any] = {}
    for layer in layers:
        fam = ml.load_llama_family_realdata(layers=(layer,))
        layer_data = fam["layers"][f"hs{layer}"]
        projected = ml.project_population(
            layer_data["anchors"], layer_data["u_d"], layer_data["c_hat"],
            layer_data["mu_d"], layer_data["sigma_d"], layer_data["mu_c"], layer_data["sigma_c"],
        )
        m1_doubt = ml.m1_contrast(projected, "z_d")
        m1_caution = ml.m1_contrast(projected, "z_c")
        subtype = _subtype_resolved(projected, category_lookup, displacement_by_key=None)
        stats = _unanswerable_stats(projected)
        per_layer[f"hs{layer}"] = {
            "family": "llama32-3b", "layer": f"hs{layer}",
            "frame_crosscheck_pass": layer_data["crosscheck_pass"],
            "m1_doubt": m1_doubt, "m1_caution": m1_caution,
            "subtype_resolved": subtype, "unanswerable_stats": stats,
            "m3": "dropped: no placebo arm ran for llama (shape F); AMENDMENT.md M3 scope is qwen+mistral only",
        }
        del fam, layer_data, projected
        gc.collect()
    return {"family": "llama32-3b", "layers": per_layer}


def main() -> int:
    print("[run_mechanism] qwen35-4b (small, safetensors)...", flush=True)
    qwen = run_qwen()
    print("[run_mechanism] qwen done. mistral7b-v03 (251MB JSON)...", flush=True)
    mistral = run_mistral()
    print("[run_mechanism] mistral done. llama32-3b (493MB JSON x3 layers)...", flush=True)
    llama = run_llama()
    print("[run_mechanism] llama done.", flush=True)

    m2_by_llama_layer = {
        layer_key: ml.m2_summary({
            "qwen35-4b": qwen["unanswerable_stats"],
            "mistral7b-v03": mistral["unanswerable_stats"],
            "llama32-3b": layer_result["unanswerable_stats"],
        })
        for layer_key, layer_result in llama["layers"].items()
    }

    mechanism = {
        "status": "run",
        "note": (
            "M1/M2/M3 executed against the real staged mistral (251MB) / llama "
            "(493MB) anchor JSONs and the qwen safetensors, per AMENDMENT.md's "
            "Mechanism probe design; every statistic is computed by the pinned "
            "mechanism_leg.py functions, this runner only sequences loads, "
            "joins category_canon, and groups by kuq subtype (the lead's "
            "pre-stated subtype-resolved readout)."
        ),
        "M1": {
            "qwen35-4b": {"m1_doubt": qwen["m1_doubt"], "m1_caution": qwen["m1_caution"]},
            "mistral7b-v03": {"m1_doubt": mistral["m1_doubt"], "m1_caution": mistral["m1_caution"]},
            "llama32-3b": {
                layer_key: {"m1_doubt": r["m1_doubt"], "m1_caution": r["m1_caution"], "frame_crosscheck_pass": r["frame_crosscheck_pass"]}
                for layer_key, r in llama["layers"].items()
            },
        },
        "M2_by_llama_layer": m2_by_llama_layer,
        "M3": {
            "qwen35-4b": qwen["m3"],
            "mistral7b-v03": mistral["m3"],
            "llama32-3b": "dropped: no placebo arm ran for llama (shape F); AMENDMENT.md M3 scope is qwen+mistral only",
        },
        "subtype_resolved_readout": {
            "note": (
                "Descriptive, hypothesis-generating only (NOTEBOOK.md 2026-07-14 "
                "lead pre-statement, before any mechanism-leg anchor tensor was "
                "loaded): per kuq subtype per family, n, median doubt/caution "
                "projection, and (qwen/mistral only) median M3 realized "
                "displacement. No gate, no bearing on the registered falsifier."
            ),
            "qwen35-4b": qwen["subtype_resolved"],
            "mistral7b-v03": mistral["subtype_resolved"],
            "llama32-3b": {layer_key: r["subtype_resolved"] for layer_key, r in llama["layers"].items()},
        },
    }

    report_path = COMMITTED / "signflip_report.json"
    report = json.loads(report_path.read_text())
    report["mechanism_leg"] = mechanism
    write_json(report_path, report)
    print(f"[run_mechanism] merged mechanism leg into {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
