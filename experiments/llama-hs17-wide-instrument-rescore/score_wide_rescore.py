#!/usr/bin/env python3
"""Stage 0/1 scoring for llama-hs17-wide-instrument-rescore
(AMENDMENT.md "Instruments"; gates.yaml WR-G0/WR-G1).

Reads the per-arm run logs `run_wide_rescore.py` wrote (gitignored, under
`analysis/<family>/runlog/...`, each record already carrying the full narrow
sub-grade dict AND `out_text` -- the whole point of this cell) and computes:

1. **Narrow bridge (WR-G1).** `clean_tighten` is already computed per row by
   the generation driver (reusing the parent's `pipeline.grade_clean_tighten`
   via `run_one_row_with_text`); this script only AGGREGATES it per arm via
   `narrow.grade_population` / `narrow.pl.grade_population` (Wilson CI),
   never re-derives the metric.
2. **Wide stage-1 (detector screen only).** `detector_v2.is_refused_v2` from
   `abstention-wide-instrument-calibration` (imported directly, sys.path,
   never copied) applied to `out_text`. This is the SCREEN rate reported
   alongside the narrow bridge for every arm; it is NOT the final wide rate
   the amendment's WR-G2/WR-G3/WR-G4 gate on -- the final rate is
   detector-OR-adjudicated, computed by `gates_wide_rescore.py` after the
   blinded adjudication lane (`build_adjudication_pool.py` + the lead's
   grading + `gates_wide_rescore.py apply`) runs. Reporting the detector-only
   number here lets WR-G0/WR-G1 be checked before any adjudication pool is
   even built.

WR-G0 (wide-pin half): also verifies `detector_v2.py` / `detector_v2_patterns.yaml`
/ `grader.py` under `abstention-wide-instrument-calibration/` are byte-identical
to that experiment's OWN committed `experiment.yaml` `instrument.pins` --
loaded from ITS OWN experiment.yaml, never hardcoded here, so a future repin
there is picked up automatically rather than silently drifting out of sync.

CONTAINMENT: per-row scored files (carry `out_text`) are written ONLY under
the gitignored `analysis/` tree. The committed summary
(`analysis-committed/<family>/wide_rescore_scored_summary.json`) holds counts,
rates, and Wilson CIs ONLY -- no text, no row_key, no answer_value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
NARROW_DIR = REPO_ROOT / "experiments" / "llama-hs17-direction-specificity"
WIDE_CAL_DIR = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"

sys.path.insert(0, str(NARROW_DIR))
import run_specificity as narrow  # noqa: E402

FAMILY = narrow.FAMILY
SEEDS = narrow.SEEDS

ANALYSIS = HERE / "analysis" / FAMILY
ANALYSIS_COMMITTED = HERE / "analysis-committed" / FAMILY
RUNLOG_DIR = ANALYSIS / "runlog" / "wide_rescore"
SCORED_DIR = ANALYSIS / "scored"

ARM_IDS = ["arm0_baseline", "arm1_gated_replication"] + [f"arm2_random_{s}" for s in SEEDS]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.open(encoding="utf-8") if ln.strip()]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")


# --------------------------------------------------------------------------
# WR-G0, wide-pin half: verify against abstention-wide-instrument-calibration's
# OWN committed pins (never hardcoded here).
# --------------------------------------------------------------------------

def verify_wide_pins() -> dict:
    wide_cal_exp = yaml.safe_load((WIDE_CAL_DIR / "experiment.yaml").read_text(encoding="utf-8"))
    pins = wide_cal_exp["instrument"]["pins"]
    check_files = ["detector_v2.py", "detector_v2_patterns.yaml", "grader.py"]
    results = {}
    problems = []
    for name in check_files:
        pinned = pins.get(name)
        path = WIDE_CAL_DIR / name
        actual = sha256_file(path) if path.is_file() else None
        ok = pinned is not None and actual == pinned
        results[name] = {"pinned": pinned, "actual": actual, "ok": ok}
        if not ok:
            problems.append(name)
    if problems:
        raise SystemExit(
            f"[verify_wide_pins] WIDE-PIN VERIFICATION FAILED for {problems}: "
            f"abstention-wide-instrument-calibration's own committed pins "
            f"(experiment.yaml instrument.pins) do not match its own files on disk. {results}"
        )
    print(f"[verify_wide_pins] detector_v2.py / detector_v2_patterns.yaml / grader.py "
          f"verified byte-identical to abstention-wide-instrument-calibration's committed pins")
    return results


def _bare_top_level_import_names(source_path: Path) -> set[str]:
    """AST-scans `source_path`'s own MODULE-BODY-level bare `import X`
    statements. Ported verbatim from `qwen3-4b-l34-placebo-seed-census/
    pipeline_census_l34.py`'s function of the same name -- see its docstring
    for why this collision class is real, not hypothetical, in this repo:
    every experiment directory owns its own same-named files (`grader.py`,
    `gates_lib.py`, `detector_v2.py`, ...), and this cell's own scripts
    import from THREE such directories (narrow cell, abstention-wide-
    instrument-calibration, placebo-seed-distribution-census) in one
    process, so a bare `import grader`/`import gates_lib` inside one of
    those directories' files can silently resolve to a DIFFERENT
    directory's same-named module already cached in `sys.modules` by an
    earlier import in this same process."""
    import ast
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def import_from_dir(module_name: str, module_dir: Path, file_name: str):
    """Ported verbatim (eviction-and-restore behavior included) from
    `qwen3-4b-l34-placebo-seed-census/pipeline_census_l34.py`'s
    `_import_from_dir`. Loads `file_name` from `module_dir` as `module_name`,
    with `module_dir` prepended to sys.path for the duration of THIS file's
    own module-body exec (so its internal bare imports resolve against its
    own directory's siblings), and evicts (then restores) any of its own
    bare-imported names that are currently cached in sys.modules pointing at
    a DIFFERENT experiments/ directory -- the real collision this repo's
    convention creates when combining same-named-file directories in one
    interpreter."""
    added = str(module_dir) not in sys.path
    if added:
        sys.path.insert(0, str(module_dir))

    bare_names = _bare_top_level_import_names(module_dir / file_name)
    saved_modules: dict[str, Any] = {}
    experiments_root = str((REPO_ROOT / "experiments").resolve())
    module_dir_resolved = str(module_dir.resolve())
    for name in bare_names:
        cached = sys.modules.get(name)
        cached_file = getattr(cached, "__file__", None)
        if (
            cached is not None and cached_file is not None
            and str(Path(cached_file).resolve()).startswith(experiments_root)
            and not str(Path(cached_file).resolve()).startswith(module_dir_resolved)
        ):
            saved_modules[name] = sys.modules.pop(name)

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_dir / file_name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        for name, cached in saved_modules.items():
            sys.modules[name] = cached
        if added:
            sys.path.remove(str(module_dir))


_MODULE_CACHE: dict[str, Any] = {}


def _cached_import(cache_key: str, module_dir: Path, file_name: str):
    if cache_key not in _MODULE_CACHE:
        _MODULE_CACHE[cache_key] = import_from_dir(cache_key, module_dir, file_name)
    return _MODULE_CACHE[cache_key]


def _detector_v2():
    return _cached_import("wr_detector_v2", WIDE_CAL_DIR, "detector_v2.py")


# --------------------------------------------------------------------------
# Load per-arm run logs (real or smoke), tag detector_v2, aggregate.
# --------------------------------------------------------------------------

def load_arm_rows(arm_id: str, runlog_dir: Path = RUNLOG_DIR) -> list[dict]:
    path = runlog_dir / f"{arm_id}.jsonl"
    if not path.is_file():
        raise SystemExit(f"[score_wide_rescore] missing run log for {arm_id}: {path}")
    rows = load_jsonl(path)
    missing_text = [r["key"] for r in rows if not r.get("out_text")]
    if missing_text:
        raise SystemExit(
            f"[score_wide_rescore] arm {arm_id} has {len(missing_text)} row(s) with empty "
            f"out_text (RunLog's required_fields contract should have made this impossible "
            f"at write time): {missing_text[:5]}"
        )
    return rows


def tag_detector_v2(rows: list[dict], detector_v2_mod, cfg) -> list[dict]:
    out = []
    for r in rows:
        r = dict(r)
        r["refused_v2"] = detector_v2_mod.is_refused_v2(r["out_text"], cfg)
        out.append(r)
    return out


def score_arm(arm_id: str, runlog_dir: Path, detector_v2_mod, cfg) -> dict:
    raw = load_arm_rows(arm_id, runlog_dir)
    tagged = tag_detector_v2(raw, detector_v2_mod, cfg)
    write_jsonl(SCORED_DIR / f"{arm_id}.jsonl", tagged)

    confab = [r for r in tagged if r["role"] == "confab"]
    known = [r for r in tagged if r["role"] == "known_correct_answered"]

    result = {
        "n_rows": len(tagged),
        "narrow_confab": narrow.grade_population(confab, "clean_tighten") if confab else None,
        "wide_detector_only_confab": {
            "n": len(confab), "successes": sum(1 for r in confab if r["refused_v2"]),
            "rate": (sum(1 for r in confab if r["refused_v2"]) / len(confab)) if confab else None,
        },
    }
    if known:
        result["narrow_known"] = narrow.grade_population(known, "clean_tighten")
        result["wide_detector_only_known"] = {
            "n": len(known), "successes": sum(1 for r in known if r["refused_v2"]),
            "rate": (sum(1 for r in known if r["refused_v2"]) / len(known)),
        }
        fired_known = [r for r in known if r["fire"]]
        result["known_fired_n"] = len(fired_known)
        if fired_known:
            result["wide_detector_only_known_fired"] = {
                "n": len(fired_known), "successes": sum(1 for r in fired_known if r["refused_v2"]),
                "rate": sum(1 for r in fired_known if r["refused_v2"]) / len(fired_known),
            }
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runlog-dir", type=Path, default=RUNLOG_DIR,
                     help="defaults to the real-run path; point at the smoke path for a smoke score.")
    ap.add_argument("--out", type=Path, default=ANALYSIS_COMMITTED / "wide_rescore_scored_summary.json")
    args = ap.parse_args(argv)

    verify_wide_pins()
    detector_v2_mod = _detector_v2()
    cfg = detector_v2_mod.load_patterns()

    per_arm = {}
    for arm_id in ARM_IDS:
        per_arm[arm_id] = score_arm(arm_id, args.runlog_dir, detector_v2_mod, cfg)
        print(f"[score_wide_rescore] {arm_id}: narrow_confab={per_arm[arm_id]['narrow_confab']} "
              f"wide_detector_only_confab={per_arm[arm_id]['wide_detector_only_confab']}")

    wr_g1 = {
        "id": "WR-G1", "threshold": 0.50,
        "metric": per_arm["arm1_gated_replication"]["narrow_confab"],
        "pass": bool(per_arm["arm1_gated_replication"]["narrow_confab"]["rate"] >= 0.50),
    }

    summary = {"family": FAMILY, "per_arm": per_arm, "WR_G1_regeneration_bridge": wr_g1}
    write_json(args.out, summary)
    print(json.dumps({"WR_G1_regeneration_bridge": wr_g1}, indent=2))
    print(f"\n[score_wide_rescore] wrote {args.out}")
    if not wr_g1["pass"]:
        print(
            "[score_wide_rescore] WR-G1 FAIL: per AMENDMENT.md this cell resolves as a "
            "regeneration mismatch; wide gates are reported descriptively only, and the "
            "resolved narrow cell is NOT thereby impugned. Do not proceed to build the "
            "adjudication pool expecting a wide claim of either sign.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
