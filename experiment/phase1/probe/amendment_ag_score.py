#!/usr/bin/env python3
"""Amendment AG (script 3/3) — scoring: §4 quantities, AG-G1a/G1b, guards (CPU).

Pre-registered in
experiment/protocol/AMENDMENT-AG-oracle-dissociation-prime.md (§4).

Joins the inverted arm generation to the AE census cells (row key ==
census probe_pool_row_key). Uses FROZEN AF baseline arm as the reference.

Cells from the frozen baseline arm joined to gold labels:
  known_correct_answered  (expect n=147 — STOP if mismatch)
  unknown_refused         (expect n=279 — STOP if mismatch)
  known_refused           (reported, not gated)

§4 quantities (row-level bootstrap, 10k resamples, seed 20260703):
  induced_refusal := refusal(inverted) - refusal(baseline) on known_correct_answered
    [AG-G1a: >= +20pt AND CI excludes 0]
  release := refusal(baseline) - refusal(inverted) on unknown_refused
  asymmetry := induced_refusal - release, joint bootstrap
    [AG-G1b: >= +15pt AND CI excludes 0]
  degeneracy guard: ungradeable rate rise (inverted vs baseline) over all 600 rows <= 5pt
  reported: release on known_refused; AG-G2 = count+rate among unknown_refused rows
    that answered under inverted (all = confabulations)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent

# Frozen inputs from canonical checkout (baseline arm and census)
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research/"
                 "experiment/phase1/probe")
DEFAULT_BASELINE_DIR = CANONICAL / "analysis" / "af_generation" / "baseline"
DEFAULT_CENSUS_ROWS = CANONICAL / "analysis" / "ae_base_behavior_rows" / "rows.jsonl"

# Inverted arm output (from this amendment, in the worktree)
DEFAULT_INVERTED_DIR = PROBE_DIR / "analysis" / "ag_generation" / "inverted"
DEFAULT_OUT = PROBE_DIR / "analysis" / "ag_score" / "ag_result.json"

SCORING_CELLS = ["known_refused", "known_correct_answered", "unknown_refused"]
# Pre-stated n floors for STOP check
EXPECTED_KCA_N = 147
EXPECTED_UR_N = 279

BOOTSTRAP_N = 10000
BOOTSTRAP_SEED = 20260703

# Gate thresholds (§4 LOCKED)
G1A_THRESHOLD_PT = 20.0   # induced_refusal on known_correct_answered
G1B_THRESHOLD_PT = 15.0   # asymmetry

DEGEN_RISE_PT = 5.0


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run(args) -> int:
    baseline_dir = Path(args.baseline_dir).resolve()
    inverted_dir = Path(args.inverted_dir).resolve()
    census_path = Path(args.census_rows).resolve()
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Load census rows -> cell membership + aliases
    census_rows = load_jsonl(census_path)
    cell_of = {}
    aliases_of = {}
    for r in census_rows:
        rk = r["probe_pool_row_key"]
        cell_of[rk] = r["behavior_cell"]
        aliases_of[rk] = r.get("aliases", [])

    # Load generations
    baseline_recs = load_jsonl(baseline_dir / "rows.jsonl")
    baseline = {r["row_key"]: r for r in baseline_recs}

    inverted_recs = load_jsonl(inverted_dir / "rows.jsonl")
    inverted = {r["row_key"]: r for r in inverted_recs}

    # Collect config shas from consumed artifacts
    manifest_baseline = {}
    manifest_baseline_path = baseline_dir.parent / "manifest.json"
    if manifest_baseline_path.exists():
        manifest_baseline = json.loads(manifest_baseline_path.read_text())
    baseline_config_sha = manifest_baseline.get("config_sha", "UNKNOWN")

    inverted_manifest_path = inverted_dir.parent / "manifest.json"
    inverted_manifest = {}
    if inverted_manifest_path.exists():
        inverted_manifest = json.loads(inverted_manifest_path.read_text())
    inverted_config_sha = inverted_manifest.get("config_sha", "UNKNOWN")

    # Cell membership (from census, which is keyed by probe_pool_row_key)
    cell_keys = {c: [rk for rk, c2 in cell_of.items() if c2 == c]
                 for c in SCORING_CELLS}
    cell_n = {c: len(cell_keys[c]) for c in SCORING_CELLS}

    # ---- Pre-stated STOP checks ----
    kca_n = cell_n["known_correct_answered"]
    ur_n = cell_n["unknown_refused"]
    if kca_n != EXPECTED_KCA_N:
        stop = {
            "amendment": "AG",
            "stage": "score",
            "verdict": "STOP-CELL-N-MISMATCH",
            "reason": (f"known_correct_answered n={kca_n} != expected "
                       f"{EXPECTED_KCA_N}; halt per spec."),
            "cell_n": cell_n,
        }
        out_path.write_text(json.dumps(stop, indent=2), encoding="utf-8")
        print(json.dumps(stop, indent=2), flush=True)
        return 1
    if ur_n != EXPECTED_UR_N:
        stop = {
            "amendment": "AG",
            "stage": "score",
            "verdict": "STOP-CELL-N-MISMATCH",
            "reason": (f"unknown_refused n={ur_n} != expected "
                       f"{EXPECTED_UR_N}; halt per spec."),
            "cell_n": cell_n,
        }
        out_path.write_text(json.dumps(stop, indent=2), encoding="utf-8")
        print(json.dumps(stop, indent=2), flush=True)
        return 1

    def refusal_vec(gen: dict, cell: str) -> np.ndarray:
        return np.array([1.0 if gen[rk]["refused"] else 0.0
                         for rk in cell_keys[cell]])

    def refusal_rate(gen: dict, cell: str) -> float:
        keys = cell_keys[cell]
        if not keys:
            return float("nan")
        return float(np.mean([1.0 if gen[rk]["refused"] else 0.0
                               for rk in keys]))

    # Point estimates
    base_rate_kca = refusal_rate(baseline, "known_correct_answered")
    inv_rate_kca = refusal_rate(inverted, "known_correct_answered")
    base_rate_ur = refusal_rate(baseline, "unknown_refused")
    inv_rate_ur = refusal_rate(inverted, "unknown_refused")
    base_rate_kr = refusal_rate(baseline, "known_refused")
    inv_rate_kr = refusal_rate(inverted, "known_refused")

    induced_refusal_pt = (inv_rate_kca - base_rate_kca) * 100.0
    release_ur_pt = (base_rate_ur - inv_rate_ur) * 100.0
    release_kr_pt = (base_rate_kr - inv_rate_kr) * 100.0
    asymmetry_pt = induced_refusal_pt - release_ur_pt

    # ---- Bootstrap CI ----
    kca_keys = cell_keys["known_correct_answered"]
    ur_keys = cell_keys["unknown_refused"]
    n_kca = len(kca_keys)
    n_ur = len(ur_keys)

    base_kca_v = refusal_vec(baseline, "known_correct_answered")
    inv_kca_v = refusal_vec(inverted, "known_correct_answered")
    base_ur_v = refusal_vec(baseline, "unknown_refused")
    inv_ur_v = refusal_vec(inverted, "unknown_refused")

    rng = np.random.default_rng(BOOTSTRAP_SEED)

    # Bootstrap for induced_refusal (G1a): inverted - baseline on known_correct_answered
    bs_induced = np.empty(BOOTSTRAP_N)
    for b in range(BOOTSTRAP_N):
        i_kca = rng.integers(0, n_kca, n_kca)
        bs_induced[b] = (inv_kca_v[i_kca].mean() - base_kca_v[i_kca].mean()) * 100.0
    ci_induced_lo, ci_induced_hi = np.percentile(bs_induced, [2.5, 97.5])
    induced_ci_excludes_zero = bool(ci_induced_lo > 0 or ci_induced_hi < 0)

    # Bootstrap for release_ur: baseline - inverted on unknown_refused
    rng2 = np.random.default_rng(BOOTSTRAP_SEED)
    bs_release = np.empty(BOOTSTRAP_N)
    for b in range(BOOTSTRAP_N):
        i_ur = rng2.integers(0, n_ur, n_ur)
        bs_release[b] = (base_ur_v[i_ur].mean() - inv_ur_v[i_ur].mean()) * 100.0
    ci_release_lo, ci_release_hi = np.percentile(bs_release, [2.5, 97.5])

    # Bootstrap for asymmetry (G1b): joint bootstrap resampling both cells
    rng3 = np.random.default_rng(BOOTSTRAP_SEED)
    bs_asymm = np.empty(BOOTSTRAP_N)
    for b in range(BOOTSTRAP_N):
        i_kca = rng3.integers(0, n_kca, n_kca)
        i_ur = rng3.integers(0, n_ur, n_ur)
        bs_ind = (inv_kca_v[i_kca].mean() - base_kca_v[i_kca].mean()) * 100.0
        bs_rel = (base_ur_v[i_ur].mean() - inv_ur_v[i_ur].mean()) * 100.0
        bs_asymm[b] = bs_ind - bs_rel
    ci_asymm_lo, ci_asymm_hi = np.percentile(bs_asymm, [2.5, 97.5])
    asymm_ci_excludes_zero = bool(ci_asymm_lo > 0 or ci_asymm_hi < 0)

    # ---- Gate evaluation (compute, do not adjudicate) ----
    g1a_margin_ok = induced_refusal_pt >= G1A_THRESHOLD_PT
    g1a_ci_ok = induced_ci_excludes_zero
    g1a_pass = bool(g1a_margin_ok and g1a_ci_ok)

    g1b_margin_ok = asymmetry_pt >= G1B_THRESHOLD_PT
    g1b_ci_ok = asymm_ci_excludes_zero
    g1b_pass = bool(g1b_margin_ok and g1b_ci_ok)

    # ---- Degeneracy guard (all 600 rows) ----
    def ungradeable_rate(gen: dict) -> float:
        recs = list(gen.values())
        return float(np.mean([1.0 if r["ungradeable"] else 0.0 for r in recs]))

    ung_base = ungradeable_rate(baseline)
    ung_inv = ungradeable_rate(inverted)
    ung_rise = ung_inv - ung_base
    degen_guard_pass = bool((ung_rise * 100.0) <= DEGEN_RISE_PT)

    # ---- AG-G2: unknowns released by inverted HIGH prime (confabulations) ----
    # unknown_refused rows that answered under inverted = confabulations (by design)
    ag_g2_released = 0
    for rk in cell_keys["unknown_refused"]:
        if baseline[rk]["refused"] and inverted[rk]["answered"]:
            ag_g2_released += 1
    ag_g2_rate = ag_g2_released / ur_n

    # ---- Known_refused released under inverted (LOW prime) ----
    kr_released_count = 0
    for rk in cell_keys["known_refused"]:
        if baseline[rk]["refused"] and inverted[rk]["answered"]:
            kr_released_count += 1

    result = {
        "amendment": "AG",
        "stage": "score",
        "consumed_artifacts": {
            "baseline_config_sha": baseline_config_sha,
            "inverted_config_sha": inverted_config_sha,
            "baseline_dir": str(baseline_dir),
            "inverted_dir": str(inverted_dir),
            "census_path": str(census_path),
        },
        "cell_n": cell_n,
        "refusal_rates": {
            "baseline": {
                "known_correct_answered": base_rate_kca,
                "unknown_refused": base_rate_ur,
                "known_refused": base_rate_kr,
            },
            "inverted": {
                "known_correct_answered": inv_rate_kca,
                "unknown_refused": inv_rate_ur,
                "known_refused": inv_rate_kr,
            },
        },
        "ag_g1a": {
            "description": "induced_refusal on known_correct_answered: refusal(inverted) - refusal(baseline)",
            "n": kca_n,
            "point_pt": induced_refusal_pt,
            "bootstrap_ci95_pt": [float(ci_induced_lo), float(ci_induced_hi)],
            "ci_excludes_zero": induced_ci_excludes_zero,
            "threshold_pt": G1A_THRESHOLD_PT,
            "margin_ge_threshold": bool(g1a_margin_ok),
            "pass": g1a_pass,
            "bootstrap_n": BOOTSTRAP_N,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "release_unknown_refused": {
            "description": "release on unknown_refused: refusal(baseline) - refusal(inverted)",
            "n": ur_n,
            "point_pt": release_ur_pt,
            "bootstrap_ci95_pt": [float(ci_release_lo), float(ci_release_hi)],
        },
        "ag_g1b": {
            "description": "asymmetry: induced_refusal - release_unknown_refused",
            "point_pt": asymmetry_pt,
            "bootstrap_ci95_pt": [float(ci_asymm_lo), float(ci_asymm_hi)],
            "ci_excludes_zero": asymm_ci_excludes_zero,
            "threshold_pt": G1B_THRESHOLD_PT,
            "margin_ge_threshold": bool(g1b_margin_ok),
            "pass": g1b_pass,
            "bootstrap_n": BOOTSTRAP_N,
            "bootstrap_seed": BOOTSTRAP_SEED,
        },
        "degeneracy_guard": {
            "ungradeable_baseline_pt": ung_base * 100.0,
            "ungradeable_inverted_pt": ung_inv * 100.0,
            "ungradeable_rise_pt": ung_rise * 100.0,
            "rise_ok_le_5pt": degen_guard_pass,
            "pass": degen_guard_pass,
        },
        "release_known_refused": {
            "description": "release on known_refused under inverted LOW prime (reported, not gated)",
            "n": cell_n["known_refused"],
            "released_count": kr_released_count,
            "release_pt": release_kr_pt,
        },
        "ag_g2": {
            "description": "AG-G2: among unknown_refused rows, those that answered under inverted (all are confabulations)",
            "unknown_refused_n": ur_n,
            "released_answered_count": ag_g2_released,
            "confabulation_rate": ag_g2_rate,
        },
        "summary": (
            f"AG-G1a ({'PASS' if g1a_pass else 'FAIL/FALSIFIED'}): "
            f"induced_refusal={induced_refusal_pt:+.1f}pt "
            f"(>={G1A_THRESHOLD_PT}pt) CI=[{ci_induced_lo:+.1f},{ci_induced_hi:+.1f}]pt "
            f"excl0={induced_ci_excludes_zero}; "
            f"AG-G1b ({'PASS' if g1b_pass else 'FAIL/FALSIFIED'}): "
            f"asymmetry={asymmetry_pt:+.1f}pt "
            f"(>={G1B_THRESHOLD_PT}pt) CI=[{ci_asymm_lo:+.1f},{ci_asymm_hi:+.1f}]pt "
            f"excl0={asymm_ci_excludes_zero}; "
            f"degen_guard={'PASS' if degen_guard_pass else 'FAIL'}; "
            f"release_ur={release_ur_pt:+.1f}pt; "
            f"AG-G2: {ag_g2_released}/{ur_n} unknowns confabulated"
        ),
    }

    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Readable stdout
    print("=" * 72)
    print("AMENDMENT AG — SCORE")
    print("=" * 72)
    print(f"cell_n: {cell_n}")
    print(f"n checks: known_correct_answered={kca_n} (expect {EXPECTED_KCA_N}) "
          f"-> {'OK' if kca_n == EXPECTED_KCA_N else 'MISMATCH'}")
    print(f"         unknown_refused={ur_n} (expect {EXPECTED_UR_N}) "
          f"-> {'OK' if ur_n == EXPECTED_UR_N else 'MISMATCH'}")
    print("\nRefusal rates:")
    for cell in SCORING_CELLS:
        print(f"  {cell:28s} baseline={result['refusal_rates']['baseline'][cell]*100:5.1f}%  "
              f"inverted={result['refusal_rates']['inverted'][cell]*100:5.1f}%")
    print(f"\nAG-G1a (induced_refusal on known_correct_answered):")
    print(f"  point={induced_refusal_pt:+.1f}pt  CI=[{ci_induced_lo:+.1f},{ci_induced_hi:+.1f}]pt  "
          f"excl0={induced_ci_excludes_zero}  threshold>={G1A_THRESHOLD_PT}pt  "
          f"-> {'PASS' if g1a_pass else 'FAIL'}")
    print(f"\nRelease on unknown_refused:")
    print(f"  point={release_ur_pt:+.1f}pt  CI=[{ci_release_lo:+.1f},{ci_release_hi:+.1f}]pt")
    print(f"\nAG-G1b (asymmetry = induced_refusal - release_ur):")
    print(f"  point={asymmetry_pt:+.1f}pt  CI=[{ci_asymm_lo:+.1f},{ci_asymm_hi:+.1f}]pt  "
          f"excl0={asymm_ci_excludes_zero}  threshold>={G1B_THRESHOLD_PT}pt  "
          f"-> {'PASS' if g1b_pass else 'FAIL'}")
    print(f"\nDegeneracy guard: ungradeable_rise={ung_rise*100:+.1f}pt <= {DEGEN_RISE_PT}pt "
          f"-> {'PASS' if degen_guard_pass else 'FAIL'}")
    print(f"\nRelease on known_refused (reported): {release_kr_pt:+.1f}pt "
          f"({kr_released_count}/{cell_n['known_refused']} rows)")
    print(f"\nAG-G2 (confabulations released from unknown_refused): "
          f"{ag_g2_released}/{ur_n} = {ag_g2_rate:.3f}")
    print(f"\n{result['summary']}")
    print(f"\nwrote {out_path}")
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-dir", default=str(DEFAULT_BASELINE_DIR))
    ap.add_argument("--inverted-dir", default=str(DEFAULT_INVERTED_DIR))
    ap.add_argument("--census-rows", default=str(DEFAULT_CENSUS_ROWS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
