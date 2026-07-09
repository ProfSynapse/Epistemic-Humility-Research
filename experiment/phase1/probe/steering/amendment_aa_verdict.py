#!/usr/bin/env python3
"""Amendment AA — mechanical Stage-1 verdict roll-up (CPU-only).

Reads the eight cell JSONs produced by run_arm_a.py / run_arm_b.py and applies
the LOCKED gates of experiments/causal-confidence-steering/AMENDMENT.md
exactly as pre-registered. WRITTEN AND TESTED BEFORE ANY STAGE-1 RESULT EXISTED
(2026-07-02, while AA-1 was in flight) so the analysis cannot drift after the
data lands.

Gates (Stage 1, Qwen3.5-4B):
  AA-G1  (aa1, Arm A gate@anchor): some coherent alpha with
         abstention_unknown delta >= +0.15 vs alpha=0, CI excludes 0,
         AND answer_rate_known delta >= -0.05 at that same alpha.
  AA-G2  (aa5, Arm B gate@early): real vs placebo abstention_unknown
         delta >= +0.10, CI excludes 0, AND answer_rate_known delta >= -0.05.
  AA-G3  (aa3, Arm A dial@end): some coherent alpha with
         revision_discrimination delta >= +0.10 vs alpha=0, CI excludes 0.
  AA-G4  (aa7, Arm B dial@late): real vs placebo revision_discrimination
         delta >= +0.10, CI excludes 0.
  AA-G5  (PRIMARY): for each arm x signal combo passing its effect gate, the
         position-asymmetry contrast (same metric, predicted-position effect
         minus wrong-position effect, both vs their own controls, paired
         bootstrap over row_key-aligned items) is > 0 with CI excluding 0,
         in >= 3 of 4 combinations.

STAGE-1 SUCCESS = AA-G5 AND (G1 or G2) AND (G3 or G4).
FALSIFIER 1 = no effect gate passes at any coherent operating point.
FALSIFIER 2 = effect gates pass but the asymmetry fails in >= 2 passing combos.
FALSIFIER 3 = effects exist only at alphas violating the coherence floor.

Usage:
  python3 amendment_aa_verdict.py \
      --results-dir experiment/phase1/probe/steering/results \
      --out experiments/causal-confidence-steering/artifacts/amendment_aa_qwen3.5-4b_result.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Optional

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from steering_common import (  # noqa: E402
    metric_abstention_unknown,
    metric_answer_rate_known,
    metric_revision_discrimination,
)

N_BOOT = 2000

# Effect thresholds per the amendment (LOCKED).
TH_G1_EFFECT = 0.15
TH_G2_EFFECT = 0.10
TH_G3_EFFECT = 0.10
TH_G4_EFFECT = 0.10
TH_KNOWN_FLOOR = -0.05

CELL_FILES = {
    "AA-1": "aa1_gate_anchor.json",
    "AA-2": "aa2_gate_end.json",
    "AA-3": "aa3_dial_end.json",
    "AA-4": "aa4_dial_anchor.json",
    "AA-5": "aa5_gate_early.json",
    "AA-6": "aa6_gate_late.json",
    "AA-7": "aa7_dial_late.json",
    "AA-8": "aa8_dial_early.json",
}


def load_cells(results_dir: Path) -> dict:
    cells = {}
    for cell, fname in CELL_FILES.items():
        p = results_dir / fname
        cells[cell] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    return cells


# ---------------------------------------------------------------------------
# Effect gates from the harness summaries (the same numbers the cells printed)
# ---------------------------------------------------------------------------

def _contrasts(summary: dict) -> dict:
    """Arm B summaries expose the paired contrast as real_vs_placebo (fall back
    to vs_control if the key differs); Arm A keys vs_control by alpha string."""
    return summary.get("real_vs_placebo") or summary.get("vs_control") or {}


def _adequacy(cell: dict, kind: str) -> dict:
    """Locked adequacy preconditions: gate cells need >=100 unknown answered
    under control; dial cells need >=40 initial-wrong AND >=40 initial-correct.
    An underpowered cell cannot pass its effect gate."""
    a = cell["summary"].get("adequacy", {})
    key = ("gate_adequate_ge_100_unknown_answered" if kind == "gate"
           else "dial_adequate_ge_40_40")
    return {"ok": bool(a.get(key)), "detail": a}


def gate_arm_a(cell: dict, metric: str, th_effect: float,
               known_floor: bool) -> dict:
    """G1/G3: scan the sweep for the smallest-|alpha| coherent pass (the
    amendment's alpha* rule; ties resolve to larger effect)."""
    adequacy = _adequacy(cell, "gate" if metric == "abstention_unknown" else "dial")
    per = cell["summary"]["per_alpha"]
    vs = cell["summary"]["vs_control"]
    passing = []
    for a_str, c in vs.items():
        if float(a_str) == 0.0:
            continue
        if not per.get(a_str, {}).get("coherence_floor_ok"):
            continue
        eff = c.get(metric) or {}
        if not (eff.get("delta", 0.0) >= th_effect and eff.get("ci_excludes_zero")):
            continue
        if known_floor:
            fl = c.get("answer_rate_known") or {}
            if fl.get("delta", 0.0) < TH_KNOWN_FLOOR:
                continue
        passing.append((abs(float(a_str)), -eff["delta"], a_str, eff))
    passing.sort()
    out = {"pass": bool(passing) and adequacy["ok"],
           "adequate": adequacy["ok"], "adequacy": adequacy["detail"],
           "passing_alphas": [p[2] for p in passing]}
    if passing and not adequacy["ok"]:
        out["note"] = "UNDERPOWERED: effect present but adequacy floor not met"
    if passing:
        out["alpha_star"] = passing[0][2]
        out["effect_at_alpha_star"] = passing[0][3]
    return out


def gate_arm_b(cell: dict, metric: str, th_effect: float,
               known_floor: bool) -> dict:
    """G2/G4: real vs placebo paired contrast, both variants coherent."""
    adequacy = _adequacy(cell, "gate" if metric == "abstention_unknown" else "dial")
    per_var = {v: cell["summary"].get(v, {}) for v in ("real", "placebo")}
    coherent = all(per_var[v].get("coherence_floor_ok") for v in per_var)
    c = _contrasts(cell["summary"])
    eff = c.get(metric) or {}
    ok = (coherent and eff.get("delta", 0.0) >= th_effect
          and bool(eff.get("ci_excludes_zero")))
    if ok and known_floor:
        fl = c.get("answer_rate_known") or {}
        ok = fl.get("delta", 0.0) >= TH_KNOWN_FLOOR
    out = {"pass": bool(ok) and adequacy["ok"], "adequate": adequacy["ok"],
           "adequacy": adequacy["detail"], "effect": eff,
           "coherent_both": coherent}
    if ok and not adequacy["ok"]:
        out["note"] = "UNDERPOWERED: effect present but adequacy floor not met"
    return out


# ---------------------------------------------------------------------------
# AA-G5: cross-cell position-asymmetry contrast (paired bootstrap over the
# row_key intersection of all four record lists)
# ---------------------------------------------------------------------------

def _records(cell: dict, key: str) -> list[dict]:
    return cell["items"].get(key, [])


def asymmetry_contrast(pred_test: list[dict], pred_ctrl: list[dict],
                       wrong_test: list[dict], wrong_ctrl: list[dict],
                       stat_fn: Callable[[list[dict]], Optional[float]],
                       n_boot: int = N_BOOT, seed: int = 20260701) -> Optional[dict]:
    """(stat(pred_test)-stat(pred_ctrl)) - (stat(wrong_test)-stat(wrong_ctrl)),
    resampling row_key-aligned items in lockstep across all four lists."""
    maps = [{r["row_key"]: r for r in lst}
            for lst in (pred_test, pred_ctrl, wrong_test, wrong_ctrl)]
    common = set(maps[0])
    for m in maps[1:]:
        common &= set(m)
    if not common:
        return None
    keys = sorted(common)
    aligned = [[m[k] for k in keys] for m in maps]

    def point(lists):
        vals = [stat_fn(lst) for lst in lists]
        if any(v is None for v in vals):
            return None
        return (vals[0] - vals[1]) - (vals[2] - vals[3])

    pt = point(aligned)
    if pt is None:
        return None
    rng = np.random.default_rng(seed)
    n = len(keys)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        b = point([[lst[i] for i in idx] for lst in aligned])
        if b is not None:
            boots.append(b)
    if not boots:
        return None
    lo, hi = np.percentile(boots, 2.5), np.percentile(boots, 97.5)
    return {
        "contrast": round(float(pt), 4),
        "ci_lo": round(float(lo), 4),
        "ci_hi": round(float(hi), 4),
        "n_items_aligned": n,
        "n_boot": len(boots),
        "pass": bool(pt > 0 and lo > 0),
    }


def g5_for_combo(combo: str, cells: dict, effect_gates: dict) -> dict:
    """One arm x signal combination. Only computed when its effect gate passed;
    otherwise reported as NOT_APPLICABLE (cannot count toward G5)."""
    spec = {
        # combo: (pred_cell, wrong_cell, gate_key, metric_fn, armA?)
        "armA_gate": ("AA-1", "AA-2", "AA-G1", metric_abstention_unknown, True),
        "armA_dial": ("AA-3", "AA-4", "AA-G3", metric_revision_discrimination, True),
        "armB_gate": ("AA-5", "AA-6", "AA-G2", metric_abstention_unknown, False),
        "armB_dial": ("AA-7", "AA-8", "AA-G4", metric_revision_discrimination, False),
    }[combo]
    pred_name, wrong_name, gate_key, stat_fn, arm_a = spec
    gate = effect_gates.get(gate_key, {})
    if not gate.get("pass"):
        return {"status": "NOT_APPLICABLE", "reason": f"{gate_key} did not pass"}
    pred, wrong = cells.get(pred_name), cells.get(wrong_name)
    if pred is None or wrong is None:
        return {"status": "MISSING_CELL"}
    if arm_a:
        a_star = gate["alpha_star"]
        wrong_alphas = [a for a in wrong["items"] if float(a) != 0.0]
        if not wrong_alphas:
            return {"status": "MISSING_CELL", "reason": "wrong-position cell has no steered alpha"}
        res = asymmetry_contrast(
            _records(pred, a_star), _records(pred, "0.0"),
            _records(wrong, wrong_alphas[0]), _records(wrong, "0.0"),
            stat_fn, n_boot=N_BOOT)
        extra = {"alpha_star": a_star, "wrong_cell_alpha": wrong_alphas[0]}
    else:
        res = asymmetry_contrast(
            _records(pred, "real"), _records(pred, "placebo"),
            _records(wrong, "real"), _records(wrong, "placebo"),
            stat_fn, n_boot=N_BOOT)
        extra = {}
    if res is None:
        return {"status": "UNDEFINED", **extra}
    return {"status": "PASS" if res["pass"] else "FAIL", **extra, **res}


# ---------------------------------------------------------------------------
# Falsifier-3 signal: effects that exist only past the coherence floor
# ---------------------------------------------------------------------------

def incoherent_only_effects(cell: dict, metric: str, th: float) -> list[str]:
    per = cell["summary"]["per_alpha"]
    vs = cell["summary"]["vs_control"]
    return [a for a, c in vs.items()
            if float(a) != 0.0
            and not per.get(a, {}).get("coherence_floor_ok")
            and (c.get(metric) or {}).get("delta", 0.0) >= th
            and (c.get(metric) or {}).get("ci_excludes_zero")]


# ---------------------------------------------------------------------------
# Roll-up
# ---------------------------------------------------------------------------

def compute_verdict(cells: dict) -> dict:
    missing = [c for c, v in cells.items() if v is None]
    gates: dict = {}
    if cells["AA-1"]:
        gates["AA-G1"] = gate_arm_a(cells["AA-1"], "abstention_unknown",
                                    TH_G1_EFFECT, known_floor=True)
    if cells["AA-5"]:
        gates["AA-G2"] = gate_arm_b(cells["AA-5"], "abstention_unknown",
                                    TH_G2_EFFECT, known_floor=True)
    if cells["AA-3"]:
        gates["AA-G3"] = gate_arm_a(cells["AA-3"], "revision_discrimination",
                                    TH_G3_EFFECT, known_floor=False)
    if cells["AA-7"]:
        gates["AA-G4"] = gate_arm_b(cells["AA-7"], "revision_discrimination",
                                    TH_G4_EFFECT, known_floor=False)

    combos = {c: g5_for_combo(c, cells, gates)
              for c in ("armA_gate", "armA_dial", "armB_gate", "armB_dial")}
    n_pass = sum(1 for v in combos.values() if v.get("status") == "PASS")
    n_fail = sum(1 for v in combos.values() if v.get("status") == "FAIL")
    g5 = {"combos": combos, "n_pass": n_pass, "n_fail": n_fail,
          "pass": n_pass >= 3}

    arm_a_effect = any(gates.get(k, {}).get("pass") for k in ("AA-G1", "AA-G3"))
    arm_b_effect = any(gates.get(k, {}).get("pass") for k in ("AA-G2", "AA-G4"))
    gate_side = any(gates.get(k, {}).get("pass") for k in ("AA-G1", "AA-G2"))
    dial_side = any(gates.get(k, {}).get("pass") for k in ("AA-G3", "AA-G4"))
    any_effect = arm_a_effect or arm_b_effect

    f3_signal = {}
    for cell_name, metric, th in (("AA-1", "abstention_unknown", TH_G1_EFFECT),
                                  ("AA-3", "revision_discrimination", TH_G3_EFFECT)):
        if cells[cell_name]:
            hits = incoherent_only_effects(cells[cell_name], metric, th)
            if hits:
                f3_signal[cell_name] = hits

    if missing:
        verdict = "INCOMPLETE"
    elif g5["pass"] and gate_side and dial_side:
        verdict = "SUCCESS"
    elif not any_effect:
        verdict = ("FALSIFIER-3 (effects only past coherence floor)"
                   if f3_signal else
                   "FALSIFIER-1 (channel stays shut — no effect gate passed)")
    elif n_fail >= 2:
        verdict = "FALSIFIER-2 (position does not matter — asymmetry fails in >=2 passing combos)"
    else:
        verdict = "PARTIAL (some effect gates passed; G5 bar not met — report as ambiguous/mixed)"

    return {
        "amendment": "AA",
        "stage": 1,
        "model": "Qwen/Qwen3.5-4B",
        "verdict": verdict,
        "verdict_rule": ("SUCCESS = AA-G5 (>=3/4 combos, predicted-minus-wrong "
                         "contrast >0 with CI excl 0) AND (G1 or G2) AND (G3 or G4); "
                         "gates locked in AMENDMENT-AA before the run"),
        "missing_cells": missing,
        "effect_gates": gates,
        "AA_G5_position_asymmetry_PRIMARY": g5,
        "falsifier3_incoherent_only_effects": f3_signal,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    cells = load_cells(a.results_dir)
    result = compute_verdict(cells)
    a.out.write_text(json.dumps(result, indent=2, ensure_ascii=False),
                     encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ("verdict", "missing_cells")}, indent=2))
    for k, v in result["effect_gates"].items():
        print(f"  {k}: {'PASS' if v.get('pass') else 'fail'}")
    g5 = result["AA_G5_position_asymmetry_PRIMARY"]
    print(f"  AA-G5 PRIMARY: {g5['n_pass']} pass / {g5['n_fail']} fail -> "
          f"{'PASS' if g5['pass'] else 'fail'}")
    print(f"[amendment_aa_verdict] wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
