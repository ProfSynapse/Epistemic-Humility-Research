"""
Amendment AG Stage-0: Conditional Compliance in AF's Permuted Arm

Splits AF's permuted arm by per-row alignment (certainty_permuted == certainty_true)
to estimate baseline compliance with aligned vs anti-aligned primes.

Outputs structured JSON and prints a compact summary.
"""

import argparse
import json
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_labels(labels_path: str) -> dict:
    """Return {row_key: {certainty_true, certainty_permuted}} for all pool rows."""
    with open(labels_path) as f:
        raw = json.load(f)
    inner = raw.get("labels", {})
    # Validate expected structure
    for k, v in inner.items():
        if not isinstance(v, dict) or "certainty_true" not in v or "certainty_permuted" not in v:
            raise ValueError(f"Unexpected label entry for row_key {k!r}: {v}")
    return inner


def load_arm_rows(arm_path: str) -> dict:
    """Return {row_key: row} for a generation arm rows.jsonl."""
    rows = {}
    with open(arm_path) as f:
        for line in f:
            row = json.loads(line.strip())
            rk = row["row_key"]
            if rk in rows:
                raise ValueError(f"Duplicate row_key in {arm_path}: {rk!r}")
            rows[rk] = row
    return rows


def load_ae_cells(ae_path: str) -> dict:
    """Return {probe_pool_row_key: behavior_cell}."""
    cells = {}
    with open(ae_path) as f:
        for line in f:
            row = json.loads(line.strip())
            rk = row["probe_pool_row_key"]
            if rk in cells:
                raise ValueError(f"Duplicate probe_pool_row_key in {ae_path}: {rk!r}")
            cells[rk] = row["behavior_cell"]
    return cells


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_rate_diff(x_a, x_b, n_resamp: int = 10_000, seed: int = 20260703):
    """
    Bootstrap 95% CI for (mean(x_a) - mean(x_b)) via percentile method.
    x_a and x_b are 0/1 arrays of equal or different length.
    Returns (diff, ci_lo, ci_hi).
    """
    rng = np.random.default_rng(seed)
    na, nb = len(x_a), len(x_b)
    diffs = np.empty(n_resamp)
    for i in range(n_resamp):
        ra = rng.choice(x_a, size=na, replace=True)
        rb = rng.choice(x_b, size=nb, replace=True)
        diffs[i] = ra.mean() - rb.mean()
    diff = float(x_a.mean() - x_b.mean())
    ci_lo, ci_hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    return diff, ci_lo, ci_hi


def bootstrap_rate(x, n_resamp: int = 10_000, seed: int = 20260703):
    """Bootstrap 95% CI for mean(x). Returns (mean, ci_lo, ci_hi)."""
    rng = np.random.default_rng(seed)
    n = len(x)
    resampled = np.empty(n_resamp)
    for i in range(n_resamp):
        resampled[i] = rng.choice(x, size=n, replace=True).mean()
    mean_ = float(x.mean())
    ci_lo, ci_hi = float(np.percentile(resampled, 2.5)), float(np.percentile(resampled, 97.5))
    return mean_, ci_lo, ci_hi


def bootstrap_diff_of_diffs(
    x_perm_a, x_base_a, x_perm_b, x_base_b,
    n_resamp: int = 10_000, seed: int = 20260703
):
    """
    Bootstrap CI for (release_a - release_b), where release = base_rate - perm_rate.
    All arrays are 0/1. Resamples within each subset independently.
    Returns (point_estimate, ci_lo, ci_hi).
    """
    rng = np.random.default_rng(seed)
    na_perm, na_base = len(x_perm_a), len(x_base_a)
    nb_perm, nb_base = len(x_perm_b), len(x_base_b)
    diffs = np.empty(n_resamp)
    for i in range(n_resamp):
        ra_perm = rng.choice(x_perm_a, size=na_perm, replace=True).mean()
        ra_base = rng.choice(x_base_a, size=na_base, replace=True).mean()
        rb_perm = rng.choice(x_perm_b, size=nb_perm, replace=True).mean()
        rb_base = rng.choice(x_base_b, size=nb_base, replace=True).mean()
        release_a = ra_base - ra_perm
        release_b = rb_base - rb_perm
        diffs[i] = release_a - release_b
    release_a_pt = float(x_base_a.mean() - x_perm_a.mean())
    release_b_pt = float(x_base_b.mean() - x_perm_b.mean())
    point = release_a_pt - release_b_pt
    ci_lo, ci_hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    return point, ci_lo, ci_hi


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run(args):
    rng_seed = 20260703
    n_resamp = 10_000

    # Load inputs
    labels = load_labels(args.labels)
    baseline_rows = load_arm_rows(str(Path(args.af_gen_dir) / "baseline" / "rows.jsonl"))
    permuted_rows = load_arm_rows(str(Path(args.af_gen_dir) / "permuted" / "rows.jsonl"))
    true_rows = load_arm_rows(str(Path(args.af_gen_dir) / "true" / "rows.jsonl"))
    ae_cells = load_ae_cells(args.ae_rows)

    pool_keys = set(labels.keys())

    # ---------------------------------------------------------------------------
    # Sanity check 1: row counts
    # ---------------------------------------------------------------------------
    for arm_name, arm_dict in [("baseline", baseline_rows), ("permuted", permuted_rows), ("true", true_rows)]:
        if len(arm_dict) != len(pool_keys):
            raise ValueError(
                f"SANITY FAIL: {arm_name} has {len(arm_dict)} rows; expected {len(pool_keys)}"
            )
        missing = pool_keys - set(arm_dict.keys())
        extra = set(arm_dict.keys()) - pool_keys
        if missing or extra:
            raise ValueError(
                f"SANITY FAIL: {arm_name} row_key mismatch. missing={len(missing)}, extra={len(extra)}"
            )

    ae_keyset = set(ae_cells.keys())
    if ae_keyset != pool_keys:
        missing_ae = pool_keys - ae_keyset
        extra_ae = ae_keyset - pool_keys
        raise ValueError(
            f"SANITY FAIL: ae_cells key mismatch. missing={len(missing_ae)}, extra={len(extra_ae)}"
        )

    sanity_checks = {"row_counts": "PASS", "key_alignment": "PASS"}

    # ---------------------------------------------------------------------------
    # Build per-row alignment and cell map
    # ---------------------------------------------------------------------------
    # alignment: True if certainty_permuted == certainty_true
    alignment = {
        rk: (lbl["certainty_permuted"] == lbl["certainty_true"])
        for rk, lbl in labels.items()
    }

    aligned_count = sum(alignment.values())
    anti_aligned_count = len(alignment) - aligned_count

    # Cells of interest per spec
    cells_of_interest = {"known_refused", "known_correct_answered", "unknown_refused"}

    # Per-cell × alignment row-key sets
    subsets = {}
    for cell in cells_of_interest:
        cell_keys = [rk for rk, c in ae_cells.items() if c == cell]
        subsets[cell] = {
            "aligned": [rk for rk in cell_keys if alignment[rk]],
            "anti_aligned": [rk for rk in cell_keys if not alignment[rk]],
        }

    # ---------------------------------------------------------------------------
    # Sanity check 2: subset sizes sum to cell n
    # ---------------------------------------------------------------------------
    cell_ns = {}
    for cell in cells_of_interest:
        total = sum(1 for c in ae_cells.values() if c == cell)
        sub_total = len(subsets[cell]["aligned"]) + len(subsets[cell]["anti_aligned"])
        cell_ns[cell] = total
        if total != sub_total:
            raise ValueError(
                f"SANITY FAIL: {cell} subset sizes {sub_total} != cell n {total}"
            )
    sanity_checks["subset_sums"] = "PASS"

    # ---------------------------------------------------------------------------
    # Sanity check 3: verify permuted arm per-cell refusal rates match AF committed results
    # ---------------------------------------------------------------------------
    af_committed = {
        "known_refused": 0.9032,
        "known_correct_answered": 0.2245,
        "unknown_refused": 0.9570,
    }
    tolerance = 0.001  # allow up to 0.1pt rounding

    computed_perm_rates = {}
    for cell in cells_of_interest:
        cell_keys = [rk for rk, c in ae_cells.items() if c == cell]
        refused_flags = np.array([int(permuted_rows[rk]["refused"]) for rk in cell_keys])
        rate = float(refused_flags.mean())
        computed_perm_rates[cell] = rate

    sanity_checks["committed_rate_checks"] = {}
    all_match = True
    for cell, committed_rate in af_committed.items():
        computed = computed_perm_rates[cell]
        match = abs(computed - committed_rate) <= tolerance
        sanity_checks["committed_rate_checks"][cell] = {
            "committed": committed_rate,
            "computed": round(computed, 6),
            "diff": round(abs(computed - committed_rate), 6),
            "pass": match,
        }
        if not match:
            all_match = False

    if not all_match:
        # Report mismatch and stop
        print("SANITY FAIL: Permuted arm refusal rates do not match AF committed results.")
        print(json.dumps(sanity_checks["committed_rate_checks"], indent=2))
        return None

    sanity_checks["committed_rates"] = "PASS"

    # ---------------------------------------------------------------------------
    # Helper: get refusal array for a subset in a given arm
    # ---------------------------------------------------------------------------
    def refused_array(arm_dict, row_keys):
        return np.array([int(arm_dict[rk]["refused"]) for rk in row_keys], dtype=float)

    # ---------------------------------------------------------------------------
    # Section 1: Overall alignment counts + per-cell × alignment subset sizes
    # ---------------------------------------------------------------------------
    alignment_summary = {
        "aligned_count": aligned_count,
        "anti_aligned_count": anti_aligned_count,
        "total": len(alignment),
    }

    subset_sizes = {}
    for cell in cells_of_interest:
        subset_sizes[cell] = {
            "aligned": len(subsets[cell]["aligned"]),
            "anti_aligned": len(subsets[cell]["anti_aligned"]),
            "total": cell_ns[cell],
        }

    # ---------------------------------------------------------------------------
    # Section 2: Per cell × alignment: refusal rates + release
    # ---------------------------------------------------------------------------
    cell_alignment_rates = {}
    for cell in cells_of_interest:
        cell_alignment_rates[cell] = {}
        for align_label, row_keys in subsets[cell].items():
            if len(row_keys) == 0:
                cell_alignment_rates[cell][align_label] = {
                    "n": 0, "perm_refused_rate": None, "baseline_refused_rate": None, "release": None
                }
                continue
            perm_refused = refused_array(permuted_rows, row_keys)
            base_refused = refused_array(baseline_rows, row_keys)
            perm_rate = float(perm_refused.mean())
            base_rate = float(base_refused.mean())
            release = base_rate - perm_rate  # positive = prime released rows
            cell_alignment_rates[cell][align_label] = {
                "n": len(row_keys),
                "perm_refused_rate": round(perm_rate, 6),
                "baseline_refused_rate": round(base_rate, 6),
                "release": round(release, 6),
            }

    # ---------------------------------------------------------------------------
    # Section 3: Four calibration quantities with bootstrap 95% CIs
    # ---------------------------------------------------------------------------
    # (a) known_refused × aligned (HIGH-on-known): release = baseline_rate - permuted_rate
    kr_al_keys = subsets["known_refused"]["aligned"]
    kr_al_perm = refused_array(permuted_rows, kr_al_keys)
    kr_al_base = refused_array(baseline_rows, kr_al_keys)
    kr_al_release = float(kr_al_base.mean() - kr_al_perm.mean())
    # Bootstrap CI on the release
    rng = np.random.default_rng(rng_seed)
    kr_al_boots = np.array([
        rng.choice(kr_al_base, size=len(kr_al_base), replace=True).mean()
        - rng.choice(kr_al_perm, size=len(kr_al_perm), replace=True).mean()
        for _ in range(n_resamp)
    ])
    kr_al_ci = (float(np.percentile(kr_al_boots, 2.5)), float(np.percentile(kr_al_boots, 97.5)))

    # (b) known_refused × anti-aligned (LOW-on-known): release
    kr_aa_keys = subsets["known_refused"]["anti_aligned"]
    kr_aa_perm = refused_array(permuted_rows, kr_aa_keys)
    kr_aa_base = refused_array(baseline_rows, kr_aa_keys)
    kr_aa_release = float(kr_aa_base.mean() - kr_aa_perm.mean())
    rng = np.random.default_rng(rng_seed)
    kr_aa_boots = np.array([
        rng.choice(kr_aa_base, size=len(kr_aa_base), replace=True).mean()
        - rng.choice(kr_aa_perm, size=len(kr_aa_perm), replace=True).mean()
        for _ in range(n_resamp)
    ])
    kr_aa_ci = (float(np.percentile(kr_aa_boots, 2.5)), float(np.percentile(kr_aa_boots, 97.5)))

    # (c) unknown_refused × anti-aligned (HIGH-on-unknown): release = baseline_rate - permuted_rate
    ur_aa_keys = subsets["unknown_refused"]["anti_aligned"]
    ur_aa_perm = refused_array(permuted_rows, ur_aa_keys)
    ur_aa_base = refused_array(baseline_rows, ur_aa_keys)
    ur_aa_release = float(ur_aa_base.mean() - ur_aa_perm.mean())
    rng = np.random.default_rng(rng_seed)
    ur_aa_boots = np.array([
        rng.choice(ur_aa_base, size=len(ur_aa_base), replace=True).mean()
        - rng.choice(ur_aa_perm, size=len(ur_aa_perm), replace=True).mean()
        for _ in range(n_resamp)
    ])
    ur_aa_ci = (float(np.percentile(ur_aa_boots, 2.5)), float(np.percentile(ur_aa_boots, 97.5)))

    # (c)-companion: among unknown rows released by anti-aligned HIGH primes, count answers (confabulations)
    # Released = was refused in baseline but answered in permuted
    confab_count = 0
    for rk in ur_aa_keys:
        if baseline_rows[rk]["refused"] and not permuted_rows[rk]["refused"]:
            # answered in permuted arm = confabulation (unknown row)
            confab_count += 1

    # (d) known_correct_answered × anti-aligned (LOW-on-known-answered): induced_refusal = perm_rate - base_rate
    kca_aa_keys = subsets["known_correct_answered"]["anti_aligned"]
    kca_aa_perm = refused_array(permuted_rows, kca_aa_keys)
    kca_aa_base = refused_array(baseline_rows, kca_aa_keys)
    kca_aa_induced_refusal = float(kca_aa_perm.mean() - kca_aa_base.mean())  # sign flipped per spec
    rng = np.random.default_rng(rng_seed)
    kca_aa_boots = np.array([
        rng.choice(kca_aa_perm, size=len(kca_aa_perm), replace=True).mean()
        - rng.choice(kca_aa_base, size=len(kca_aa_base), replace=True).mean()
        for _ in range(n_resamp)
    ])
    kca_aa_ci = (float(np.percentile(kca_aa_boots, 2.5)), float(np.percentile(kca_aa_boots, 97.5)))

    calibration = {
        "a_known_refused_aligned_release": {
            "description": "known_refused x aligned (HIGH-on-known): right-label release rate",
            "n": len(kr_al_keys),
            "point_pct": round(kr_al_release * 100, 4),
            "ci_95_pct": [round(kr_al_ci[0] * 100, 4), round(kr_al_ci[1] * 100, 4)],
            "perm_refused_rate": round(float(kr_al_perm.mean()), 6),
            "base_refused_rate": round(float(kr_al_base.mean()), 6),
        },
        "b_known_refused_anti_aligned_release": {
            "description": "known_refused x anti-aligned (LOW-on-known): should be ~0",
            "n": len(kr_aa_keys),
            "point_pct": round(kr_aa_release * 100, 4),
            "ci_95_pct": [round(kr_aa_ci[0] * 100, 4), round(kr_aa_ci[1] * 100, 4)],
            "perm_refused_rate": round(float(kr_aa_perm.mean()), 6),
            "base_refused_rate": round(float(kr_aa_base.mean()), 6),
        },
        "c_unknown_refused_anti_aligned_release": {
            "description": "unknown_refused x anti-aligned (HIGH-on-unknown): wrong pro-answer prime compliance",
            "n": len(ur_aa_keys),
            "point_pct": round(ur_aa_release * 100, 4),
            "ci_95_pct": [round(ur_aa_ci[0] * 100, 4), round(ur_aa_ci[1] * 100, 4)],
            "perm_refused_rate": round(float(ur_aa_perm.mean()), 6),
            "base_refused_rate": round(float(ur_aa_base.mean()), 6),
            "confabulation_count": confab_count,
        },
        "d_known_correct_answered_anti_aligned_induced_refusal": {
            "description": "known_correct_answered x anti-aligned (LOW-on-known): wrong muzzle prime compliance",
            "n": len(kca_aa_keys),
            "point_pct": round(kca_aa_induced_refusal * 100, 4),
            "ci_95_pct": [round(kca_aa_ci[0] * 100, 4), round(kca_aa_ci[1] * 100, 4)],
            "perm_refused_rate": round(float(kca_aa_perm.mean()), 6),
            "base_refused_rate": round(float(kca_aa_base.mean()), 6),
        },
    }

    # ---------------------------------------------------------------------------
    # Section 4: Predicted inverted arm outcome G_inv
    # Using anti-aligned conditional rates as the estimator:
    #   release_pred(known_refused | LOW prime) = kr_aa_release (LOW prime on known)
    #     BUT sign: LOW-on-known = more muzzling, so the release could be NEGATIVE
    #     The anti-aligned LOW prime for known_refused is: does it INCREASE refusal?
    #     Actually by spec: release = baseline - permuted, so negative = more refusal.
    #     For the inverted arm prediction: G_inv = release_pred(known_refused | LOW) - release_pred(unknown_refused | HIGH)
    #     where release for unknown = ur_aa_release (HIGH-on-unknown anti-aligned prime)
    # ---------------------------------------------------------------------------
    #
    # Under the inverted arm design:
    #   known rows get LOW prime (anti-aligned for known => kr_aa_release is the estimator)
    #   unknown rows get HIGH prime (anti-aligned for unknown => ur_aa_release is the estimator)
    #
    # But note: for known_refused, the "release" from a LOW prime could be NEGATIVE
    # (further muzzles) or near zero. The selectivity gap G_inv for the inverted arm
    # is: how much does it DIFFERENTLY affect knowns vs unknowns?
    #
    # Per spec: G_inv = release_pred(known_refused | LOW) - release_pred(unknown_refused | HIGH)
    # This uses the anti-aligned subset as the estimator for the full inverted arm.
    # Under compliance: knowns get muzzled (kr_aa_release negative or ~0) and
    # unknowns get released (ur_aa_release positive), so G_inv would be large negative.

    g_true = 22.94  # AF's frozen true selectivity gap (pt)
    g_inv_pred = kr_aa_release - ur_aa_release  # in fraction; convert to pct
    g_inv_pred_pct = g_inv_pred * 100

    # Bootstrap CI for G_inv: propagate from subset resamples
    rng = np.random.default_rng(rng_seed)
    g_inv_boots = np.empty(n_resamp)
    for i in range(n_resamp):
        # known_refused anti-aligned release bootstrap
        kr_aa_base_boot = rng.choice(kr_aa_base, size=len(kr_aa_base), replace=True).mean()
        kr_aa_perm_boot = rng.choice(kr_aa_perm, size=len(kr_aa_perm), replace=True).mean()
        release_known_boot = kr_aa_base_boot - kr_aa_perm_boot
        # unknown_refused anti-aligned release bootstrap
        ur_aa_base_boot = rng.choice(ur_aa_base, size=len(ur_aa_base), replace=True).mean()
        ur_aa_perm_boot = rng.choice(ur_aa_perm, size=len(ur_aa_perm), replace=True).mean()
        release_unknown_boot = ur_aa_base_boot - ur_aa_perm_boot
        g_inv_boots[i] = (release_known_boot - release_unknown_boot) * 100

    g_inv_ci = (float(np.percentile(g_inv_boots, 2.5)), float(np.percentile(g_inv_boots, 97.5)))
    g_inv_abs = abs(g_inv_pred_pct)
    ratio_06 = 0.6 * g_true
    ratio_03 = 0.3 * g_true

    inverted_prediction = {
        "g_true_pt": g_true,
        "g_inv_pred_pt": round(g_inv_pred_pct, 4),
        "g_inv_pred_abs_pt": round(g_inv_abs, 4),
        "ci_95_pt": [round(g_inv_ci[0], 4), round(g_inv_ci[1], 4)],
        "ratio_g_inv_over_g_true": round(g_inv_abs / g_true, 4),
        "threshold_0_6x_g_true_pt": round(ratio_06, 4),
        "threshold_0_3x_g_true_pt": round(ratio_03, 4),
        "note": "Numbers only; no gate recommendation. Release estimator uses anti-aligned conditional rates as proxy for full inverted arm.",
    }

    # ---------------------------------------------------------------------------
    # Assemble result
    # ---------------------------------------------------------------------------
    result = {
        "amendment": "AG",
        "stage": "Stage-0 conditional compliance",
        "bootstrap_seed": rng_seed,
        "n_resamp": n_resamp,
        "inputs": {
            "labels": str(args.labels),
            "af_gen_dir": str(args.af_gen_dir),
            "ae_rows": str(args.ae_rows),
        },
        "sanity_checks": sanity_checks,
        "alignment_summary": alignment_summary,
        "subset_sizes": subset_sizes,
        "cell_alignment_rates": cell_alignment_rates,
        "calibration": calibration,
        "inverted_arm_prediction": inverted_prediction,
    }

    # Write JSON
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Result JSON written to: {out_path}")

    # ---------------------------------------------------------------------------
    # Print compact summary
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("AMENDMENT AG STAGE-0: CONDITIONAL COMPLIANCE REPORT")
    print("=" * 70)

    print("\n--- Sanity Checks ---")
    for k, v in sanity_checks.items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for cell, check in v.items():
                status = "PASS" if check["pass"] else "FAIL"
                print(f"    {cell}: committed={check['committed']:.4f}, computed={check['computed']:.4f}, diff={check['diff']:.4f} -> {status}")
        else:
            print(f"  {k}: {v}")

    print("\n--- Alignment Summary ---")
    print(f"  Aligned   (certainty_permuted == certainty_true): {aligned_count}")
    print(f"  Anti-aligned                                    : {anti_aligned_count}")
    print(f"  Total                                           : {len(alignment)}")

    print("\n--- Subset Sizes (cell × alignment) ---")
    print(f"  {'Cell':<30} {'aligned':>10} {'anti-aligned':>14} {'total':>8}")
    for cell in cells_of_interest:
        s = subset_sizes[cell]
        print(f"  {cell:<30} {s['aligned']:>10} {s['anti_aligned']:>14} {s['total']:>8}")

    print("\n--- Per-cell × Alignment: Refusal Rates & Release ---")
    for cell in cells_of_interest:
        print(f"\n  {cell}:")
        for align_label in ["aligned", "anti_aligned"]:
            d = cell_alignment_rates[cell][align_label]
            if d["n"] == 0:
                print(f"    {align_label:<15}: n=0")
                continue
            print(
                f"    {align_label:<15}: n={d['n']:>3}  "
                f"baseline={d['baseline_refused_rate']:.4f}  "
                f"perm={d['perm_refused_rate']:.4f}  "
                f"release={d['release']:+.4f}"
            )

    print("\n--- Four Calibration Quantities (bootstrap 95% CI, 10k resamples, seed 20260703) ---")

    def fmt_cal(label, d, is_induced=False):
        metric = "induced_refusal" if is_induced else "release"
        val_key = "point_pct"
        print(
            f"  ({label}) n={d['n']:>3}  {metric}={d['point_pct']:+.2f}pt  "
            f"CI=[{d['ci_95_pct'][0]:+.2f}, {d['ci_95_pct'][1]:+.2f}]pt"
        )
        if "confabulation_count" in d:
            print(f"       confabulation_count (released unknowns answered): {d['confabulation_count']}")

    fmt_cal("a", calibration["a_known_refused_aligned_release"])
    fmt_cal("b", calibration["b_known_refused_anti_aligned_release"])
    fmt_cal("c", calibration["c_unknown_refused_anti_aligned_release"])
    fmt_cal("d", calibration["d_known_correct_answered_anti_aligned_induced_refusal"], is_induced=True)

    print("\n--- Predicted Inverted-Arm |G_inv| ---")
    p = inverted_prediction
    print(f"  G_true (AF frozen)        : {p['g_true_pt']:.2f}pt")
    print(f"  G_inv_pred (signed)       : {p['g_inv_pred_pt']:+.2f}pt")
    print(f"  |G_inv_pred|              : {p['g_inv_pred_abs_pt']:.2f}pt")
    print(f"  CI 95%                    : [{p['ci_95_pt'][0]:+.2f}, {p['ci_95_pt'][1]:+.2f}]pt")
    print(f"  |G_inv| / G_true          : {p['ratio_g_inv_over_g_true']:.4f}")
    print(f"  0.6 × G_true threshold    : {p['threshold_0_6x_g_true_pt']:.2f}pt")
    print(f"  0.3 × G_true threshold    : {p['threshold_0_3x_g_true_pt']:.2f}pt")

    print("\n" + "=" * 70)
    return result


def main():
    p = argparse.ArgumentParser(description="Amendment AG Stage-0 conditional compliance analysis")
    p.add_argument(
        "--labels",
        default="/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/analysis/af_base_pregen/af_labels.json",
        help="Path to af_labels.json",
    )
    p.add_argument(
        "--af-gen-dir",
        default="/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/analysis/af_generation",
        help="Directory containing baseline/, permuted/, true/ subdirs",
    )
    p.add_argument(
        "--ae-rows",
        default="/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/analysis/ae_base_behavior_rows/rows.jsonl",
        help="Path to AE behavior rows.jsonl",
    )
    p.add_argument(
        "--output",
        default="/home/profsynapse/code/ehr-worktrees/amendment-ag/experiment/phase1/probe/analysis/ag_stage0/ag_stage0_result.json",
        help="Output JSON path",
    )
    args = p.parse_args()
    run(args)


if __name__ == "__main__":
    main()
