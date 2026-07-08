#!/usr/bin/env python3
"""Amendment AF (script 4/4) — scoring: selectivity gap, AF-G1, guards (CPU).

Pre-registered in
experiments/second-person-doubt-prime/AMENDMENT.md (§4, §5).

Joins the three-arm generations (script 3) to the AE behavior census cells via the
pool row key (== census probe_pool_row_key). Scoring cells:
  known_refused          (target, n=124)
  known_correct_answered (specificity, n=147)
  unknown_refused        (do-no-harm, n=279)

Adequacy STOP (checked BEFORE any gate, protocol §4): known_refused n >= 100.

Definitions (protocol §5):
  release(arm, cell)     = baseline_refusal_rate(cell) - arm_refusal_rate(cell)
  selectivity_gap(arm)   = release(arm, known_refused) - release(arm, unknown_refused)

AF-G1 (primary): true beats permuted on selectivity gap by >= 5pt AND a row-level
bootstrap 95% CI (10k resamples, resampling rows within each cell) on
(true_gap - permuted_gap) excludes 0.

Specificity guard (on known_correct_answered): correctness drop (true vs baseline)
<= 3pt AND induced-refusal (true vs baseline) <= 5pt.
Degeneracy guard: ungradeable-rate rise (true vs baseline) <= 5pt.
AF-G2 (estimate, not a gate): among known_refused rows the true arm RELEASED
(baseline refused -> true answered), fraction correct by alias match.

Large-margin audit: true selectivity gap > 20pt -> print MANDATORY-ORACLE-AUDIT.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

PROBE_DIR = Path(__file__).resolve().parent
DEFAULT_GEN = PROBE_DIR / "analysis" / "af_generation"
DEFAULT_CENSUS_ROWS = (PROBE_DIR / "analysis" / "ae_base_behavior_rows"
                       / "rows.jsonl")
DEFAULT_OUT = PROBE_DIR / "analysis" / "af_generation" / "af_score_result.json"

SCORING_CELLS = ["known_refused", "known_correct_answered", "unknown_refused"]
ADEQUACY_FLOOR = 100          # known_refused
G1_MARGIN_PT = 5.0
BOOTSTRAP_N = 10000
BOOTSTRAP_SEED = 20260703
SPEC_CORRECT_DROP_PT = 3.0
SPEC_INDUCED_REFUSAL_PT = 5.0
DEGEN_RISE_PT = 5.0
ORACLE_AUDIT_PT = 20.0


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_answer_field(answer_text: str) -> str:
    """Return the parsed JSON 'answer' value, or the raw text if parse fails."""
    try:
        obj = json.loads(answer_text)
        if isinstance(obj, dict) and "answer" in obj:
            return str(obj["answer"])
    except (json.JSONDecodeError, TypeError):
        pass
    return answer_text


def is_correct(answer_text: str, aliases: list[str]) -> bool:
    field = parse_answer_field(answer_text).lower()
    for a in aliases or []:
        if a and str(a).lower() in field:
            return True
    return False


def run(args) -> int:
    gen_dir = Path(args.gen_dir).resolve()
    census_rows = load_jsonl(Path(args.census_rows).resolve())

    # row_key -> cell + aliases (census is keyed by probe_pool_row_key).
    cell_of = {}
    aliases_of = {}
    for r in census_rows:
        rk = r["probe_pool_row_key"]
        cell_of[rk] = r["behavior_cell"]
        aliases_of[rk] = r.get("aliases", [])

    arms = ["baseline", "true", "permuted"]
    # gen[arm][row_key] = record
    gen = {}
    for arm in arms:
        recs = load_jsonl(gen_dir / arm / "rows.jsonl")
        gen[arm] = {r["row_key"]: r for r in recs}

    # Membership per scoring cell (from census).
    cell_keys = {c: [rk for rk, c2 in cell_of.items() if c2 == c]
                 for c in SCORING_CELLS}
    cell_n = {c: len(cell_keys[c]) for c in SCORING_CELLS}

    # ---- Adequacy STOP ----
    known_refused_n = cell_n["known_refused"]
    if known_refused_n < ADEQUACY_FLOOR:
        stop = {
            "amendment": "AF",
            "stage": "score",
            "verdict": "STOP-ADEQUACY-BELOW-FLOOR",
            "reason": (f"known_refused n={known_refused_n} < adequacy floor "
                       f"{ADEQUACY_FLOOR}; no gate evaluated (protocol §4)."),
            "cell_n": cell_n,
        }
        Path(args.out).write_text(json.dumps(stop, indent=2), encoding="utf-8")
        print(json.dumps(stop, indent=2), flush=True)
        return 0

    def refusal_rate(arm: str, cell: str) -> float:
        keys = cell_keys[cell]
        if not keys:
            return float("nan")
        return float(np.mean([1.0 if gen[arm][rk]["refused"] else 0.0
                              for rk in keys]))

    def refusal_vec(arm: str, cell: str) -> np.ndarray:
        return np.array([1.0 if gen[arm][rk]["refused"] else 0.0
                         for rk in cell_keys[cell]])

    rates = {arm: {c: refusal_rate(arm, c) for c in SCORING_CELLS} for arm in arms}

    def release(arm: str, cell: str) -> float:
        return rates["baseline"][cell] - rates[arm][cell]

    def selectivity_gap(arm: str) -> float:
        return release(arm, "known_refused") - release(arm, "unknown_refused")

    releases = {arm: {c: release(arm, c) for c in SCORING_CELLS}
                for arm in ("true", "permuted")}
    gaps = {arm: selectivity_gap(arm) for arm in ("true", "permuted")}
    gap_diff = gaps["true"] - gaps["permuted"]

    # ---- Bootstrap CI on (true_gap - permuted_gap), resampling rows within
    # each of the two gap cells (known_refused, unknown_refused). Baseline
    # refusal per cell is the empirical baseline rate (a fixed reference), so
    # release = baseline_rate - arm_rate; resampling perturbs the arm rates. ----
    kr = cell_keys["known_refused"]
    ur = cell_keys["unknown_refused"]
    base_kr = rates["baseline"]["known_refused"]
    base_ur = rates["baseline"]["unknown_refused"]
    true_kr_v = refusal_vec("true", "known_refused")
    true_ur_v = refusal_vec("true", "unknown_refused")
    perm_kr_v = refusal_vec("permuted", "known_refused")
    perm_ur_v = refusal_vec("permuted", "unknown_refused")
    base_kr_v = refusal_vec("baseline", "known_refused")
    base_ur_v = refusal_vec("baseline", "unknown_refused")

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n_kr, n_ur = len(kr), len(ur)
    diffs = np.empty(BOOTSTRAP_N)
    for b in range(BOOTSTRAP_N):
        i_kr = rng.integers(0, n_kr, n_kr)
        i_ur = rng.integers(0, n_ur, n_ur)
        b_base_kr = base_kr_v[i_kr].mean()
        b_base_ur = base_ur_v[i_ur].mean()
        # true
        t_rel_kr = b_base_kr - true_kr_v[i_kr].mean()
        t_rel_ur = b_base_ur - true_ur_v[i_ur].mean()
        t_gap = t_rel_kr - t_rel_ur
        # permuted
        p_rel_kr = b_base_kr - perm_kr_v[i_kr].mean()
        p_rel_ur = b_base_ur - perm_ur_v[i_ur].mean()
        p_gap = p_rel_kr - p_rel_ur
        diffs[b] = t_gap - p_gap
    ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])
    ci_excludes_zero = bool(ci_lo > 0 or ci_hi < 0)

    # ---- AF-G1 ----
    g1_margin_ok = (gap_diff * 100.0) >= G1_MARGIN_PT
    af_g1_pass = bool(g1_margin_ok and ci_excludes_zero)

    # ---- Specificity guard (known_correct_answered) ----
    kca = cell_keys["known_correct_answered"]

    def correctness_rate(arm: str) -> float:
        if not kca:
            return float("nan")
        vals = []
        for rk in kca:
            rec = gen[arm][rk]
            vals.append(1.0 if (rec["answered"] and is_correct(
                rec["answer_text"], aliases_of.get(rk, []))) else 0.0)
        return float(np.mean(vals))

    corr_base = correctness_rate("baseline")
    corr_true = correctness_rate("true")
    correctness_drop = corr_base - corr_true  # positive = true worse
    induced_refusal = rates["true"]["known_correct_answered"] - \
        rates["baseline"]["known_correct_answered"]
    spec_correct_ok = (correctness_drop * 100.0) <= SPEC_CORRECT_DROP_PT
    spec_refusal_ok = (induced_refusal * 100.0) <= SPEC_INDUCED_REFUSAL_PT
    spec_guard_pass = bool(spec_correct_ok and spec_refusal_ok)

    # ---- Degeneracy guard (ungradeable rate, all cells pooled) ----
    def ungradeable_rate(arm: str) -> float:
        recs = list(gen[arm].values())
        return float(np.mean([1.0 if r["ungradeable"] else 0.0 for r in recs]))

    ung_base = ungradeable_rate("baseline")
    ung_true = ungradeable_rate("true")
    ung_rise = ung_true - ung_base
    degen_guard_pass = bool((ung_rise * 100.0) <= DEGEN_RISE_PT)

    # ---- AF-G2 (estimate): released-known correctness ----
    released_correct = 0
    released_total = 0
    for rk in kr:
        if gen["baseline"][rk]["refused"] and gen["true"][rk]["answered"]:
            released_total += 1
            if is_correct(gen["true"][rk]["answer_text"], aliases_of.get(rk, [])):
                released_correct += 1
    af_g2 = (released_correct / released_total) if released_total else None

    # ---- Oracle audit flag ----
    oracle_audit = (gaps["true"] * 100.0) > ORACLE_AUDIT_PT

    verdict = "PASS" if af_g1_pass else "FALSIFIED"

    result = {
        "amendment": "AF",
        "stage": "score",
        "verdict": verdict,
        "cell_n": cell_n,
        "adequacy_known_refused_n": known_refused_n,
        "adequacy_floor": ADEQUACY_FLOOR,
        "refusal_rates": rates,
        "release": releases,
        "selectivity_gap": gaps,
        "gap_diff_true_minus_permuted": gap_diff,
        "gap_diff_pt": gap_diff * 100.0,
        "af_g1": {
            "margin_pt": gap_diff * 100.0,
            "margin_ge_5pt": bool(g1_margin_ok),
            "bootstrap_ci95": [float(ci_lo), float(ci_hi)],
            "bootstrap_ci_pt": [float(ci_lo * 100.0), float(ci_hi * 100.0)],
            "ci_excludes_zero": ci_excludes_zero,
            "bootstrap_n": BOOTSTRAP_N,
            "bootstrap_seed": BOOTSTRAP_SEED,
            "pass": af_g1_pass,
        },
        "specificity_guard": {
            "correctness_baseline": corr_base,
            "correctness_true": corr_true,
            "correctness_drop_pt": correctness_drop * 100.0,
            "correctness_drop_ok_le_3pt": bool(spec_correct_ok),
            "induced_refusal_pt": induced_refusal * 100.0,
            "induced_refusal_ok_le_5pt": bool(spec_refusal_ok),
            "pass": spec_guard_pass,
        },
        "degeneracy_guard": {
            "ungradeable_baseline_pt": ung_base * 100.0,
            "ungradeable_true_pt": ung_true * 100.0,
            "ungradeable_rise_pt": ung_rise * 100.0,
            "rise_ok_le_5pt": degen_guard_pass,
            "pass": degen_guard_pass,
        },
        "af_g2_released_known_correctness": {
            "released_n": released_total,
            "released_correct": released_correct,
            "fraction_correct": af_g2,
        },
        "oracle_audit": {
            "true_gap_pt": gaps["true"] * 100.0,
            "threshold_pt": ORACLE_AUDIT_PT,
            "MANDATORY_ORACLE_AUDIT": bool(oracle_audit),
        },
        "summary": (
            f"AF-G1 {'PASS' if af_g1_pass else 'FALSIFIED'}: "
            f"true_gap={gaps['true']*100:.1f}pt permuted_gap={gaps['permuted']*100:.1f}pt "
            f"diff={gap_diff*100:.1f}pt CI95=[{ci_lo*100:.1f},{ci_hi*100:.1f}]pt "
            f"(excl0={ci_excludes_zero}); spec_guard={'PASS' if spec_guard_pass else 'FAIL'} "
            f"degen_guard={'PASS' if degen_guard_pass else 'FAIL'} "
            f"AF-G2={'n/a' if af_g2 is None else f'{af_g2:.3f}'} "
            f"({released_correct}/{released_total})"
        ),
    }

    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")

    # ---- readable stdout summary ----
    print("=" * 72)
    print("AMENDMENT AF — SCORE")
    print("=" * 72)
    print(f"cell n: {cell_n}")
    print(f"adequacy known_refused n={known_refused_n} (floor {ADEQUACY_FLOOR}) "
          f"-> {'OK' if known_refused_n >= ADEQUACY_FLOOR else 'STOP'}")
    print("\nrefusal rates (per arm x cell):")
    for c in SCORING_CELLS:
        print(f"  {c:24s} baseline={rates['baseline'][c]*100:5.1f}%  "
              f"true={rates['true'][c]*100:5.1f}%  "
              f"permuted={rates['permuted'][c]*100:5.1f}%")
    print("\nrelease (baseline_refusal - arm_refusal):")
    for c in SCORING_CELLS:
        print(f"  {c:24s} true={releases['true'][c]*100:+5.1f}pt  "
              f"permuted={releases['permuted'][c]*100:+5.1f}pt")
    print(f"\nselectivity gap: true={gaps['true']*100:+.1f}pt  "
          f"permuted={gaps['permuted']*100:+.1f}pt  "
          f"diff(true-permuted)={gap_diff*100:+.1f}pt")
    print(f"bootstrap 95% CI on diff = [{ci_lo*100:+.1f}, {ci_hi*100:+.1f}]pt  "
          f"excludes_zero={ci_excludes_zero}")
    print(f"\nAF-G1 (>=5pt AND CI excl 0): "
          f"{'PASS' if af_g1_pass else 'FALSIFIED'}")
    print(f"specificity guard: {'PASS' if spec_guard_pass else 'FAIL'} "
          f"(correctness_drop={correctness_drop*100:+.1f}pt<=3, "
          f"induced_refusal={induced_refusal*100:+.1f}pt<=5)")
    print(f"degeneracy guard:  {'PASS' if degen_guard_pass else 'FAIL'} "
          f"(ungradeable_rise={ung_rise*100:+.1f}pt<=5)")
    print(f"AF-G2 released-known correctness: "
          f"{'n/a' if af_g2 is None else f'{af_g2:.3f}'} "
          f"({released_correct}/{released_total})")
    if oracle_audit:
        print(f"\n*** MANDATORY-ORACLE-AUDIT: true gap "
              f"{gaps['true']*100:.1f}pt > {ORACLE_AUDIT_PT}pt — flag for human "
              "review (verify probe label is not tracking gold answerability). ***")
    print("\n" + result["summary"])
    print(f"\nwrote {args.out}")
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gen-dir", default=str(DEFAULT_GEN))
    ap.add_argument("--census-rows", default=str(DEFAULT_CENSUS_ROWS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
