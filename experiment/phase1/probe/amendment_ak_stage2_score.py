#!/usr/bin/env python3
"""Amendment AK Stage 2 - AK-G3 gate scoring (CPU, deterministic, seeded).

Consumes amendment_ak_stage2_steer.py's rows.jsonl and computes, per
AMENDMENT-AK-commitment-point.md §4:

  AK-G3 (steering asymmetry): answer-window steering moves confab rate by
  >= 2x the anchor-only condition at matched dose, with anchor-only bounded above
  by the carried-minority prediction (item 31 r ~ 0.34-0.37).

Statistic
---------
For each dose magnitude |alpha| > 0 and each sign, the effect of an arm is the
SIGNED confab-rate shift from the alpha=0 baseline:

    shift(arm) = confab_rate(arm) - confab_rate(baseline)

measured on the SAME matched rows (paired). The AK-G3 ratio at a matched dose is

    ratio = |shift(gen_stream)| / |shift(anchor)|

PASS requires ratio >= 2.0 with a bootstrap 95% CI whose lower bound clears 2.0
(row-paired resampling, the steering_common.paired_bootstrap convention), on at
least one dose where both effects are estimable and the window shift is non-null.
Anchor-only is additionally reported against the carried-minority ceiling
(|shift(anchor)| should sit at or below ~1/3 of |shift(gen_stream)|).

The falsifier (doc §4): a flat crystallization curve (G1 miss, already recorded)
AND no steering asymmetry (G3 miss) => the commitment/veto middle is NOT
token-localized. Stage 1's G1 already MISSED, so an AK-G3 miss here fires the
falsifier.

Guards (doc §3.2): schema validity (every arm present for every matched row),
degenerate-output fraction (<= 5% coherence floor), length drift (mean generated
length per arm vs baseline). Guards are reported and gate-blocking if the
degenerate floor is breached on a scored arm.

Outputs (UNTRACKED) under analysis/ak_stage2/:
  ak_stage2_g3_report.json   machine-readable verdict + per-dose ratios + CIs
  ak_stage2_g3_report.md     human summary
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

SEED = 20260706
N_BOOT = 2000
AK_G3_RATIO = 2.0                 # doc §4
CARRIED_MINORITY_CEILING = 1.0 / 3.0   # item 31 r ~ 0.34-0.37 -> anchor <= ~1/3
COHERENCE_FLOOR = 0.05


def load_rows(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def _rate(vals: list[int]) -> float:
    return float(np.mean(vals)) if vals else float("nan")


def _by_arm(rows: list[dict]) -> dict[tuple[str, float], dict[str, list]]:
    """(position, alpha) -> {row_key -> confab int, plus degen/len lists}."""
    out: dict[tuple[str, float], dict] = defaultdict(
        lambda: {"confab": {}, "degen": [], "len": []})
    for r in rows:
        key = (r["position"], float(r["alpha"]))
        out[key]["confab"][r["row_key"]] = int(r["confab"])
        out[key]["degen"].append(int(r["degenerate"]))
        out[key]["len"].append(int(r["n_generated"]))
    return out


def _paired_shift_ratio(anchor_confab: dict, window_confab: dict,
                        base_confab: dict) -> tuple[float, list[str]]:
    """|shift(window)| / |shift(anchor)| on the shared row set (point estimate).

    Returns (ratio, shared_row_keys). ratio is nan if the anchor shift is ~0.
    """
    keys = sorted(set(anchor_confab) & set(window_confab) & set(base_confab))
    if not keys:
        return float("nan"), []
    base = np.array([base_confab[k] for k in keys], dtype=float)
    anch = np.array([anchor_confab[k] for k in keys], dtype=float)
    wind = np.array([window_confab[k] for k in keys], dtype=float)
    shift_anchor = anch.mean() - base.mean()
    shift_window = wind.mean() - base.mean()
    if abs(shift_anchor) < 1e-9:
        return float("inf") if abs(shift_window) > 1e-9 else float("nan"), keys
    return abs(shift_window) / abs(shift_anchor), keys


def _bootstrap_ratio_ci(anchor_confab: dict, window_confab: dict,
                        base_confab: dict, keys: list[str],
                        n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Row-paired bootstrap CI for the shift ratio and for both signed shifts."""
    rng = np.random.default_rng(seed)
    base = np.array([base_confab[k] for k in keys], dtype=float)
    anch = np.array([anchor_confab[k] for k in keys], dtype=float)
    wind = np.array([window_confab[k] for k in keys], dtype=float)
    n = len(keys)
    ratios, sa, sw = [], [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        b, a, w = base[idx], anch[idx], wind[idx]
        d_a = a.mean() - b.mean()
        d_w = w.mean() - b.mean()
        sa.append(d_a)
        sw.append(d_w)
        if abs(d_a) >= 1e-9:
            ratios.append(abs(d_w) / abs(d_a))
    def ci(v):
        if not v:
            return [None, None]
        return [round(float(np.percentile(v, 2.5)), 4),
                round(float(np.percentile(v, 97.5)), 4)]
    return {
        "ratio_ci95": ci(ratios),
        "ratio_median": round(float(np.median(ratios)), 4) if ratios else None,
        "shift_anchor_ci95": ci(sa),
        "shift_window_ci95": ci(sw),
        "n_boot_ratio_defined": len(ratios),
    }


def score(rows: list[dict]) -> dict:
    arms = _by_arm(rows)
    alphas = sorted({a for (_p, a) in arms})
    positions = sorted({p for (p, _a) in arms})
    doses = sorted({abs(a) for a in alphas if abs(a) > 1e-9})

    # ---- guards ----
    n_rows_per_arm = {f"{p}@a{a:+g}": len(arms[(p, a)]["degen"])
                      for (p, a) in arms}
    degen_rate = {f"{p}@a{a:+g}": round(_rate(arms[(p, a)]["degen"]), 4)
                  for (p, a) in arms}
    mean_len = {f"{p}@a{a:+g}": round(float(np.mean(arms[(p, a)]["len"])), 2)
                for (p, a) in arms if arms[(p, a)]["len"]}
    schema_ok = len(set(n_rows_per_arm.values())) == 1
    coherence_ok = all(v <= COHERENCE_FLOOR for v in degen_rate.values())

    # ---- baseline confab per position (alpha=0). alpha=0 never steers, so both
    # positions' baselines should match; use each position's own for pairing. ----
    per_dose = []
    best = None
    for dose in doses:
        for sign in (+1.0, -1.0):
            alpha = sign * dose
            if ("anchor", alpha) not in arms or ("gen_stream", alpha) not in arms:
                continue
            base_anchor = arms[("anchor", 0.0)]["confab"] \
                if ("anchor", 0.0) in arms else {}
            base_window = arms[("gen_stream", 0.0)]["confab"] \
                if ("gen_stream", 0.0) in arms else {}
            anchor_confab = arms[("anchor", alpha)]["confab"]
            window_confab = arms[("gen_stream", alpha)]["confab"]
            # pair each condition to its own-position baseline, then take shifts
            keys = sorted(set(anchor_confab) & set(window_confab)
                          & set(base_anchor) & set(base_window))
            if not keys:
                continue
            ba = np.array([base_anchor[k] for k in keys], dtype=float)
            bw = np.array([base_window[k] for k in keys], dtype=float)
            aa = np.array([anchor_confab[k] for k in keys], dtype=float)
            ww = np.array([window_confab[k] for k in keys], dtype=float)
            shift_anchor = float(aa.mean() - ba.mean())
            shift_window = float(ww.mean() - bw.mean())
            ratio = (abs(shift_window) / abs(shift_anchor)
                     if abs(shift_anchor) > 1e-9
                     else (float("inf") if abs(shift_window) > 1e-9
                           else float("nan")))
            # bootstrap: pair window shift vs anchor shift on shared rows,
            # each against its own-position baseline
            rng = np.random.default_rng(SEED + int(dose * 1000) + int(sign))
            n = len(keys)
            ratios_b, sa_b, sw_b = [], [], []
            for _ in range(N_BOOT):
                idx = rng.integers(0, n, size=n)
                d_a = aa[idx].mean() - ba[idx].mean()
                d_w = ww[idx].mean() - bw[idx].mean()
                sa_b.append(d_a)
                sw_b.append(d_w)
                if abs(d_a) >= 1e-9:
                    ratios_b.append(abs(d_w) / abs(d_a))

            def _ci(v):
                if not v:
                    return [None, None]
                return [round(float(np.percentile(v, 2.5)), 4),
                        round(float(np.percentile(v, 97.5)), 4)]

            ratio_ci = _ci(ratios_b)
            entry = {
                "dose": dose, "sign": ("+" if sign > 0 else "-"),
                "alpha": alpha, "n_rows": n,
                "confab_rate_baseline_anchor": round(float(ba.mean()), 4),
                "confab_rate_baseline_window": round(float(bw.mean()), 4),
                "confab_rate_anchor": round(float(aa.mean()), 4),
                "confab_rate_window": round(float(ww.mean()), 4),
                "shift_anchor": round(shift_anchor, 4),
                "shift_window": round(shift_window, 4),
                "ratio_window_over_anchor": (round(ratio, 4)
                                             if np.isfinite(ratio) else ratio),
                "ratio_ci95": ratio_ci,
                "ratio_median": (round(float(np.median(ratios_b)), 4)
                                 if ratios_b else None),
                "shift_anchor_ci95": _ci(sa_b),
                "shift_window_ci95": _ci(sw_b),
                "anchor_within_carried_ceiling": bool(
                    abs(shift_anchor) <= CARRIED_MINORITY_CEILING
                    * abs(shift_window) + 1e-9) if abs(shift_window) > 1e-9
                    else None,
                "pass_point": bool(np.isfinite(ratio) and ratio >= AK_G3_RATIO
                                   and abs(shift_window) > 1e-9),
                "pass_ci": bool(ratio_ci[0] is not None
                                and ratio_ci[0] >= AK_G3_RATIO),
            }
            per_dose.append(entry)
            # best = largest window shift among CI-passing entries
            if entry["pass_ci"] and abs(shift_window) > 1e-9:
                if best is None or abs(shift_window) > abs(best["shift_window"]):
                    best = entry

    g3_pass = (best is not None) and schema_ok and coherence_ok
    return {
        "amendment": "AK", "stage": "stage2_g3", "seed": SEED,
        "n_boot": N_BOOT, "ak_g3_ratio_floor": AK_G3_RATIO,
        "carried_minority_ceiling": round(CARRIED_MINORITY_CEILING, 4),
        "alphas": alphas, "positions": positions, "doses": doses,
        "guards": {
            "schema_ok": schema_ok,
            "n_rows_per_arm": n_rows_per_arm,
            "degenerate_rate_per_arm": degen_rate,
            "coherence_floor": COHERENCE_FLOOR,
            "coherence_ok": coherence_ok,
            "mean_generated_len_per_arm": mean_len,
        },
        "per_dose": per_dose,
        "AK_G3": {
            "pass": bool(g3_pass),
            "passing_dose": (best["dose"] if best else None),
            "passing_sign": (best["sign"] if best else None),
            "passing_ratio": (best["ratio_window_over_anchor"] if best else None),
            "passing_ratio_ci95": (best["ratio_ci95"] if best else None),
            "verdict": ("PASS: window steering moves confab >= 2x anchor at a "
                        "matched dose (CI clears 2.0)" if g3_pass
                        else "MISS: no dose clears the 2x window/anchor ratio "
                             "with CI; with Stage 1 G1 MISS this fires the "
                             "falsifier (middle not token-localized)"),
        },
    }


def render_md(report: dict) -> str:
    g = report["guards"]
    lines = [
        "# Amendment AK Stage 2 - AK-G3 steering asymmetry", "",
        f"AK-G3 floor: window/anchor confab-shift ratio >= {report['ak_g3_ratio_floor']} "
        f"(CI lower bound clears it).", "",
        f"Guards: schema_ok={g['schema_ok']} coherence_ok={g['coherence_ok']} "
        f"(floor {g['coherence_floor']}).", "",
        "## Per-dose", "",
        "| dose | sign | n | rate base(a/w) | rate anchor | rate window | "
        "shift anchor | shift window | ratio | ratio CI95 | pass |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in report["per_dose"]:
        lines.append(
            f"| {e['dose']} | {e['sign']} | {e['n_rows']} | "
            f"{e['confab_rate_baseline_anchor']}/{e['confab_rate_baseline_window']} | "
            f"{e['confab_rate_anchor']} | {e['confab_rate_window']} | "
            f"{e['shift_anchor']} | {e['shift_window']} | "
            f"{e['ratio_window_over_anchor']} | {e['ratio_ci95']} | "
            f"{'YES' if e['pass_ci'] else 'no'} |")
    v = report["AK_G3"]
    lines += ["", "## Verdict", "",
              f"AK-G3: **{'PASS' if v['pass'] else 'MISS'}** - {v['verdict']}"]
    if v["passing_dose"] is not None:
        lines.append(f"Passing dose {v['passing_sign']}{v['passing_dose']} "
                     f"ratio {v['passing_ratio']} CI {v['passing_ratio_ci95']}.")
    return "\n".join(lines) + "\n"


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", required=True,
                    help="amendment_ak_stage2_steer.py rows.jsonl")
    ap.add_argument("--out-dir", required=True)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    rows = load_rows(Path(args.rows).resolve())
    report = score(rows)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ak_stage2_g3_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    (out_dir / "ak_stage2_g3_report.md").write_text(
        render_md(report), encoding="utf-8")
    print(json.dumps(report["AK_G3"], indent=2), flush=True)
    print(f"[ak/stage2-score] wrote report -> {out_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
