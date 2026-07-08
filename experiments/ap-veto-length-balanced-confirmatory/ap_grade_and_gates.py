#!/usr/bin/env python3
"""Amendment AP - CPU analysis + gates verdict (length-balanced veto confirmatory).

Pre-registered: experiments/ap-veto-length-balanced-confirmatory/AMENDMENT.md.
CPU-only; runs on the host from the canonical checkout after the Modal extract
lands. Never touches the GPU. Confirmatory follow-up to Amendment AM
(experiment/protocol/AMENDMENT-AM-residual-catch-veto-coverage.md); reported
separately and never pooled with AM, PROTOCOL v0.3, or the PR #205 published
veto operating characteristics.

INPUTS (the Modal extract output dir, local or downloaded from staging):
  <in-dir>/rows.jsonl                    graded per-row provenance (ap_extract.py)
  <in-dir>/<safe_key>__post.safetensors  post-gen content-token states {L0..L36}

WHAT IT COMPUTES (AMENDMENT.md Design + Gates):
  * Population: class 1 (hallucination) = confab-on-unanswerable OR
    wrong-on-answerable; class 0 (good) = correct-on-answerable. Identical
    is_halluc / is_good split AM used, on the FRESH AP generation's own graded
    rows (no label or scalar carried from AM).
  * Caliper match: 1:1 nearest-neighbour match on `answer_tok_len` between the
    hallucination and good populations, caliper +/-3 tokens, unmatched rows
    dropped. Global greedy matching (see `caliper_match` docstring):
    deterministic, order-independent of input list order.
  * Veto fit: PCA (<=128 components, randomized svd, seed 20260706) + saga LR,
    class_weight balanced, fit OUT-OF-FOLD (5-fold StratifiedKFold) on the
    MATCHED set's post-L20 hidden states ONLY -- no pool scalar, no
    answer_tok_len, ever enters the feature matrix. Identical recipe to
    experiment/phase1/probe/amendment_am_grade_and_gates.py's `_fit_probe` /
    `oof_scores` (read-only reference on the unmerged amendment-am branch).
  * Length-only baseline: `roc_auc_score(y_halluc, answer_tok_len)` on the
    IDENTICAL matched-set rows (same y labels, same row set as the veto).
  * Margin: veto AUROC minus length-only AUROC, with a PAIRED bootstrap (each
    resample draws one set of row indices and scores BOTH the veto and the
    length-only baseline on it, so the shared-sample correlation is preserved
    in the margin's CI, not just in two independently-resampled CIs).
  * AP-G0 (precondition): length-only AUROC <= 0.60, else VOID (no G1/G2 read).
  * AP-G1 (floor): OOF veto AUROC >= 0.68 AND bootstrap 95% CI lower bound > 0.60.
  * AP-G2 (crux): paired margin bootstrap 95% CI excludes 0 AND point >= +0.10.
  * Residual truncation rate (`hit_token_cap`) in the matched set, reported as
    a caveat per the AMENDMENT (flagged above 10%).
"""

from __future__ import annotations

import argparse
import bisect
import json
import sys
from pathlib import Path

import numpy as np

SEED = 20260706  # AP's own seed, distinct from AM's 20260705 (AMENDMENT.md).
N_BOOT = 1000
POST_L20 = 20  # post-generation content_end readout, same layer AM used.
CALIPER = 3    # answer-token-length caliper, +/- tokens (AMENDMENT.md).
# Gate thresholds (LOCKED at signing; AMENDMENT.md "Gates").
G0_LENGTH_ONLY_MAX = 0.60
G1_AUROC_FLOOR = 0.68
G1_CI_LB_FLOOR = 0.60
G2_MARGIN_FLOOR = 0.10


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def load_post_layer(in_dir: Path, safe_keys, layer):
    """Stack post-gen states for `layer` across safe_keys. Returns (X, mask)."""
    from safetensors.torch import load_file
    X, mask = [], []
    key = f"L{layer}"
    for sk in safe_keys:
        f = in_dir / f"{sk}__post.safetensors"
        if not f.is_file():
            mask.append(False)
            continue
        t = load_file(str(f))
        if key not in t:
            mask.append(False)
            continue
        X.append(t[key].float().numpy())
        mask.append(True)
    return (np.vstack(X) if X else np.zeros((0, 0))), np.array(mask)


# ---------------------------------------------------------------------------
# Population split (identical to AM's is_halluc / is_good, on AP's own rows).
# ---------------------------------------------------------------------------
def is_halluc(r):
    if r.get("confab_on_unanswerable"):
        return True
    if r.get("gold_class") == "answerable" and r.get("correct") is False:
        return True
    return False


def is_good(r):
    return r.get("gold_class") == "answerable" and r.get("correct") is True


# ---------------------------------------------------------------------------
# Caliper matching. Pure function of row dicts; unit-testable without any
# GPU artifact (see tests/test_ap_grade_and_gates.py).
# ---------------------------------------------------------------------------
def caliper_match(halluc_rows, good_rows, caliper=CALIPER,
                  len_field="answer_tok_len", key_field="safe_key"):
    """Global greedy 1:1 nearest-neighbour caliper match on `len_field`.

    Every (h, g) candidate pair whose |length difference| <= caliper is a
    candidate. Candidates are sorted by (|diff|, h[key_field], g[key_field])
    ascending and accepted greedily: a pair is taken if and only if BOTH rows
    are still unmatched. This is deterministic and independent of input list
    order (the sort key never references list position), and it prefers the
    closest available pairs globally rather than a one-sided nearest-neighbour
    walk, so it does not systematically favor whichever side is iterated
    first. Unmatched rows on either side are dropped.

    Returns (matched_halluc, matched_good): matched_halluc[i] is paired with
    matched_good[i], both lists the same length.
    """
    # Bucket good rows by length, sorted, for an efficient windowed candidate
    # search instead of full O(H*G) pair generation.
    good_by_len = sorted(good_rows, key=lambda r: r[len_field])
    good_lens = [r[len_field] for r in good_by_len]

    candidates = []  # (abs_diff, h_key, g_key, h_idx, g_idx)
    for hi, h in enumerate(halluc_rows):
        lo = bisect.bisect_left(good_lens, h[len_field] - caliper)
        hi_bound = bisect.bisect_right(good_lens, h[len_field] + caliper)
        for gi in range(lo, hi_bound):
            g = good_by_len[gi]
            diff = abs(h[len_field] - g[len_field])
            candidates.append((diff, h[key_field], g[key_field], hi, gi))

    candidates.sort(key=lambda c: (c[0], c[1], c[2]))

    h_used = set()
    g_used = set()
    matched_h, matched_g = [], []
    for diff, hk, gk, hi, gi in candidates:
        if hi in h_used or gi in g_used:
            continue
        h_used.add(hi)
        g_used.add(gi)
        matched_h.append(halluc_rows[hi])
        matched_g.append(good_by_len[gi])
    return matched_h, matched_g


# ---- PCA + saga probe (identical recipe to AM's amendment_am_grade_and_gates
# _fit_probe / oof_scores; see that file's docstring for the vt_lib lineage) --
def _fit_probe(Xtr, ytr, seed):
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression
    mu = Xtr.mean(0)
    k = min(128, Xtr.shape[0] - 1, Xtr.shape[1])
    pca = PCA(n_components=k, svd_solver="randomized", random_state=seed)
    Ztr = pca.fit_transform(Xtr - mu)
    lr = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000, C=1.0,
                            class_weight="balanced")
    lr.fit(Ztr, ytr)
    return mu, pca, lr


def oof_scores(X, y, seed=SEED, n_splits=5):
    """OOF decision scores for the CORRECTNESS dial (higher = trust/good).
    y here is y_trust: 1 = good (correct-answerable), 0 = hallucination."""
    from sklearn.model_selection import StratifiedKFold
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        mu, pca, lr = _fit_probe(X[tr], y[tr], seed)
        Zte = pca.transform(X[te] - mu)
        oof[te] = lr.decision_function(Zte)
    return oof


def auroc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s))


def bootstrap_auroc_ci(y, s, n=N_BOOT, seed=SEED):
    rng = np.random.default_rng(seed)
    y = np.asarray(y); s = np.asarray(s)
    idx_pos = np.where(y == 1)[0]
    idx_neg = np.where(y == 0)[0]
    vals = []
    for _ in range(n):
        bp = rng.choice(idx_pos, size=len(idx_pos), replace=True)
        bn = rng.choice(idx_neg, size=len(idx_neg), replace=True)
        bi = np.concatenate([bp, bn])
        try:
            vals.append(auroc(y[bi], s[bi]))
        except ValueError:
            continue
    vals = np.array(vals)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), vals


def paired_bootstrap_margin_ci(y, s_veto, s_length, n=N_BOOT, seed=SEED):
    """Bootstrap CI for (AUROC(s_veto) - AUROC(s_length)) on the SAME matched
    set, resampling row indices ONCE per iteration and scoring both metrics on
    that identical resample. This propagates the shared-sample correlation
    between the two AUROCs into the margin's CI (a paired CI), rather than
    combining two independently-resampled CIs (which would overstate the
    margin's uncertainty)."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y); s_veto = np.asarray(s_veto); s_length = np.asarray(s_length)
    idx_pos = np.where(y == 1)[0]
    idx_neg = np.where(y == 0)[0]
    margins = []
    for _ in range(n):
        bp = rng.choice(idx_pos, size=len(idx_pos), replace=True)
        bn = rng.choice(idx_neg, size=len(idx_neg), replace=True)
        bi = np.concatenate([bp, bn])
        try:
            a_v = auroc(y[bi], s_veto[bi])
            a_l = auroc(y[bi], s_length[bi])
        except ValueError:
            continue
        margins.append(a_v - a_l)
    margins = np.array(margins)
    return float(np.percentile(margins, 2.5)), float(np.percentile(margins, 97.5)), margins


# ---------------------------------------------------------------------------
# Gate evaluation. Pure function of already-computed statistics; unit-testable
# directly against hand-picked numbers for every pass/fail/void branch.
# ---------------------------------------------------------------------------
def evaluate_gates(length_only_auroc, veto_auroc, veto_ci_lo,
                   margin_point, margin_ci_lo, margin_ci_hi):
    g0_pass = bool(length_only_auroc <= G0_LENGTH_ONLY_MAX)
    ap_g0 = {"length_only_auroc": round(length_only_auroc, 4),
             "max": G0_LENGTH_ONLY_MAX, "pass": g0_pass}
    if not g0_pass:
        return {
            "AP_G0": ap_g0, "AP_G1": None, "AP_G2": None,
            "void": True,
            "overall": "VOID",
            "note": "length-only AUROC exceeds the G0 precondition; the "
                     "caliper match did not neutralize length, no content "
                     "verdict is drawn.",
        }

    g1_pass = bool(veto_auroc >= G1_AUROC_FLOOR and veto_ci_lo > G1_CI_LB_FLOOR)
    ap_g1 = {"veto_auroc": round(veto_auroc, 4),
             "ci_lb": round(veto_ci_lo, 4),
             "auroc_floor": G1_AUROC_FLOOR, "ci_lb_floor": G1_CI_LB_FLOOR,
             "pass": g1_pass}

    ci_excludes_zero = bool(margin_ci_lo > 0.0 or margin_ci_hi < 0.0)
    g2_pass = bool(ci_excludes_zero and margin_point >= G2_MARGIN_FLOOR)
    ap_g2 = {"margin_point": round(margin_point, 4),
             "margin_ci95": [round(margin_ci_lo, 4), round(margin_ci_hi, 4)],
             "ci_excludes_zero": ci_excludes_zero,
             "margin_floor": G2_MARGIN_FLOOR, "pass": g2_pass}

    overall = "PASS" if (g1_pass and g2_pass) else "FAIL"
    return {"AP_G0": ap_g0, "AP_G1": ap_g1, "AP_G2": ap_g2,
            "void": False, "overall": overall}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-dir", required=True,
                    help="Modal extract output dir (rows.jsonl + post safetensors)")
    ap.add_argument("--out", required=True, help="gates verdict JSON path")
    args = ap.parse_args(argv)

    in_dir = Path(args.in_dir).resolve()
    rows = load_jsonl(in_dir / "rows.jsonl")
    answered = [r for r in rows if r.get("answered")]

    halluc_rows = [r for r in answered if is_halluc(r)]
    good_rows = [r for r in answered if is_good(r)]

    matched_h, matched_g = caliper_match(halluc_rows, good_rows, caliper=CALIPER)
    n_matched_pairs = len(matched_h)
    if n_matched_pairs == 0:
        raise SystemExit("[ap/gates] caliper match produced zero pairs; "
                         "cannot proceed (check answer_tok_len population overlap).")

    fit_rows = matched_h + matched_g
    y_halluc = np.array([1] * len(matched_h) + [0] * len(matched_g))
    fit_keys = [r["safe_key"] for r in fit_rows]
    length_all = np.array([r["answer_tok_len"] for r in fit_rows], dtype=float)

    Xpost, mask = load_post_layer(in_dir, fit_keys, POST_L20)
    if mask.sum() != len(fit_keys):
        fit_rows = [r for r, m in zip(fit_rows, mask) if m]
        y_halluc = y_halluc[mask]
        length_all = length_all[mask]

    # OOF veto (higher = trust/good); negate so higher = hallucination, the
    # convention AM's veto_oof used, matching the gate wording "veto AUROC".
    dial_oof = oof_scores(Xpost, 1 - y_halluc, seed=SEED)  # y_trust = 1-halluc
    veto_oof = -dial_oof

    length_only_auroc = auroc(y_halluc, length_all)
    veto_auroc = auroc(y_halluc, veto_oof)
    veto_ci_lo, veto_ci_hi, _ = bootstrap_auroc_ci(y_halluc, veto_oof)
    margin_point = veto_auroc - length_only_auroc
    margin_ci_lo, margin_ci_hi, _ = paired_bootstrap_margin_ci(
        y_halluc, veto_oof, length_all)

    gates = evaluate_gates(length_only_auroc, veto_auroc, veto_ci_lo,
                           margin_point, margin_ci_lo, margin_ci_hi)

    n_truncated = sum(1 for r in fit_rows if r.get("hit_token_cap"))
    n_truncated_halluc = sum(1 for r, y in zip(fit_rows, y_halluc)
                             if y == 1 and r.get("hit_token_cap"))
    truncation_rate_matched = n_truncated / len(fit_rows) if fit_rows else 0.0
    truncation_rate_halluc = (n_truncated_halluc / int(y_halluc.sum())
                              if y_halluc.sum() else 0.0)

    verdict = {
        "amendment": "AP", "seed": SEED, "post_layer": POST_L20,
        "caliper": CALIPER,
        "counts": {
            "answered": len(answered),
            "hallucination_class_full": len(halluc_rows),
            "good_class_full": len(good_rows),
            "matched_pairs": n_matched_pairs,
            "matched_set_size": len(fit_rows),
        },
        "length_only_auroc": round(length_only_auroc, 4),
        "veto_auroc": round(veto_auroc, 4),
        "veto_bootstrap_ci95": [round(veto_ci_lo, 4), round(veto_ci_hi, 4)],
        "margin_point": round(margin_point, 4),
        "margin_bootstrap_ci95": [round(margin_ci_lo, 4), round(margin_ci_hi, 4)],
        "truncation": {
            "matched_set_rate": round(truncation_rate_matched, 4),
            "hallucination_subset_rate": round(truncation_rate_halluc, 4),
            "caveat_threshold": 0.10,
            "flagged": bool(truncation_rate_matched > 0.10),
        },
        "gates": gates,
    }

    Path(args.out).write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(json.dumps(verdict, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
