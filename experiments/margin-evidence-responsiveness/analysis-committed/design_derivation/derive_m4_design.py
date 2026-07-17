#!/usr/bin/env python3
"""
M4 (evidence-responsiveness) pre-sign design derivation.

Reads ONLY already-committed/pinned M1 and M2 artifacts (row_key, role,
score/dose fields -- never question/answer text) and computes:
  - a sanity reproduction of one M2 headline number (readout AUROC)
  - a sanity reproduction of one M1 headline number (confab median tipping dose)
  - baseline readout-projection distributions (confab vs known) in the
    registered orientation (negative z, confab-positive)
  - baseline margin (tipping-dose) distributions (confab vs known)
  - derived collapse-floor and margin-lengthening-criterion candidates
  - the arm x population x measurement count matrix for M4 Option A vs B

No paired-shift or post-intervention quantity is computed anywhere in this
script, per the M2-style self-blinding convention: M4 has not been signed,
so no intervention data exists yet. Everything here is a description of
ALREADY-COMMITTED baseline (M1/M2) data, used to derive pre-registration
knobs -- exactly the M1b-style design-derivation posture.
"""
import json
import hashlib
import math
import statistics
from pathlib import Path

REPO = Path("/home/profsynapse/code/Epistemic-Humility-Research")

READOUT_SCORES = REPO / "experiments/susceptibility-as-probe/analysis/capture/readout_scores.jsonl"
MARGIN_ROWS = REPO / "experiments/margin-mapping/analysis/margin_dataset/qwen35_4b_margin_rows.jsonl"
SUBSAMPLE_IDS = REPO / "experiments/margin-mapping/analysis-committed/subsample_ids_qwen35_4b.json"
M2_RESULTS = REPO / "experiments/susceptibility-as-probe/analysis/results/m2_results.json"

PINS = {
    str(READOUT_SCORES): "6861ea24ba03368b49d4b76503df5f78a08f8bd230155dd5cb6dec39551da5d9",
    str(MARGIN_ROWS): "84f4d3b8674a18eb944a4b921383e1cfb1147db892dee2c19348f671b7f41565",
    str(SUBSAMPLE_IDS): "60d5a3e13de5f85d35776dcee3c15dddea2e301951ded42849516865fe32723d",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pins():
    out = {}
    for path_str, expected in PINS.items():
        actual = sha256_of(Path(path_str))
        out[path_str] = {"expected": expected, "actual": actual, "match": actual == expected}
    return out


def load_jsonl(path: Path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    idx = q * (n - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_vals[lo]
    frac = idx - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


def describe(vals):
    if not vals:
        return None
    s = sorted(vals)
    return {
        "n": len(vals),
        "mean": statistics.fmean(vals),
        "median": quantile(s, 0.5),
        "sd": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "q25": quantile(s, 0.25),
        "q75": quantile(s, 0.75),
        "min": s[0],
        "max": s[-1],
    }


def auroc_mannwhitney(pos_scores, neg_scores):
    """AUROC = P(pos > neg), with 0.5 credit for ties. pos = confab (label 1)."""
    combined = sorted(pos_scores + neg_scores)
    ranks = {}
    # average-rank tie handling via rank-sum (Mann-Whitney U)
    n1, n2 = len(pos_scores), len(neg_scores)
    all_vals = pos_scores + neg_scores
    order = sorted(range(len(all_vals)), key=lambda i: all_vals[i])
    rank = [0.0] * len(all_vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and all_vals[order[j + 1]] == all_vals[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            rank[order[k]] = avg_rank
        i = j + 1
    r_pos_sum = sum(rank[k] for k in range(n1))
    u1 = r_pos_sum - n1 * (n1 + 1) / 2.0
    auc = u1 / (n1 * n2)
    return auc


def bootstrap_ci_median_diff(a_vals, b_vals, n_boot=10000, seed=48260721):
    import random
    rng = random.Random(seed)
    diffs = []
    na, nb = len(a_vals), len(b_vals)
    for _ in range(n_boot):
        a_s = [a_vals[rng.randrange(na)] for _ in range(na)]
        b_s = [b_vals[rng.randrange(nb)] for _ in range(nb)]
        diffs.append(statistics.median(a_s) - statistics.median(b_s))
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot) - 1]
    return {"point": statistics.median(a_vals) - statistics.median(b_vals), "ci95": [lo, hi], "n_boot": n_boot, "seed": seed}


def main():
    report = {}
    report["pin_verification"] = verify_pins()
    if not all(v["match"] for v in report["pin_verification"].values()):
        report["HALT"] = "sha256 mismatch on a pinned input; stop before deriving anything else"
        print(json.dumps(report, indent=2))
        return

    readout_rows = load_jsonl(READOUT_SCORES)
    margin_rows = load_jsonl(MARGIN_ROWS)
    with open(M2_RESULTS) as f:
        m2_results = json.load(f)

    report["row_counts"] = {
        "readout_scores_rows": len(readout_rows),
        "margin_rows": len(margin_rows),
    }

    # ---- Sanity reproduction 1: M2 readout AUROC (confab-positive orientation) ----
    # NOTE: the raw `readout_z` field on disk is the RAW (pre-negation) projection.
    # cell.yaml registers the score as its NEGATIVE (confab-positive orientation).
    # First attempt without negating reproduces the *raw-polarity diagnostic*
    # (0.0179375, the value that halted M2's S1 gate) rather than the registered
    # 0.9820625 -- caught by this sanity check, exactly the pitfall M2 itself hit.
    raw_confab_z = [r["readout_z"] for r in readout_rows if r["role"] == "confab"]
    raw_known_z = [r["readout_z"] for r in readout_rows if r["role"] == "known_correct_answered"]
    other_roles = sorted(set(r["role"] for r in readout_rows) - {"confab", "known_correct_answered"})
    raw_polarity_auroc = auroc_mannwhitney(raw_confab_z, raw_known_z)

    confab_z = [-v for v in raw_confab_z]  # registered orientation: negative z, confab-positive
    known_z = [-v for v in raw_known_z]
    reproduced_auroc = auroc_mannwhitney(confab_z, known_z)
    committed_auroc = m2_results["channel_aurocs"]["readout"]["point"]
    committed_raw_polarity_auroc = m2_results["S1_readout_sanity"]["auroc_raw_polarity_diagnostic"]["point"]
    report["sanity_reproduction_M2_readout_auroc"] = {
        "n_confab": len(confab_z),
        "n_known": len(known_z),
        "other_roles_present": other_roles,
        "raw_field_polarity_check": {
            "reproduced_raw_polarity_auroc": raw_polarity_auroc,
            "committed_raw_polarity_auroc": committed_raw_polarity_auroc,
            "match": abs(raw_polarity_auroc - committed_raw_polarity_auroc) < 1e-6,
            "interpretation": "confirms the on-disk readout_z field is RAW (pre-negation); registered score = -readout_z",
        },
        "reproduced_auroc_negated_registered_orientation": reproduced_auroc,
        "committed_auroc_m2_results_json": committed_auroc,
        "match_within_1e-6": abs(reproduced_auroc - committed_auroc) < 1e-6,
        "amendment_text_cited_value": 0.9821,
        "rounds_to_amendment_value": round(reproduced_auroc, 4) == 0.9821,
    }

    # ---- Sanity reproduction 2: M1 confab median tipping dose ----
    confab_tip = [r["tipping_dose_abs"] for r in margin_rows if r["role"] == "confab"]
    known_tip = [r["tipping_dose_abs"] for r in margin_rows if r["role"] == "known_correct_answered"]
    confab_tip_censored = [r for r in margin_rows if r["role"] == "confab" and r.get("tipping_censored")]
    known_tip_censored = [r for r in margin_rows if r["role"] == "known_correct_answered" and r.get("tipping_censored")]
    reproduced_confab_median = statistics.median(confab_tip)
    report["sanity_reproduction_M1_confab_median_tipping"] = {
        "n_confab": len(confab_tip),
        "n_known": len(known_tip),
        "reproduced_confab_median_tipping_dose_abs": reproduced_confab_median,
        "amendment_text_cited_value": 9.456,
        "match_within_0.001": abs(reproduced_confab_median - 9.456) < 0.001,
        "confab_tipping_censored_n": len(confab_tip_censored),
        "confab_tipping_censored_frac": len(confab_tip_censored) / len(confab_tip),
        "known_tipping_censored_n": len(known_tip_censored),
        "known_tipping_censored_frac": len(known_tip_censored) / len(known_tip),
    }

    # ---- Baseline projection distributions (readout_z, confab-positive orientation) ----
    confab_desc = describe(confab_z)
    known_desc = describe(known_z)
    gap_median = confab_desc["median"] - known_desc["median"]
    gap_mean = confab_desc["mean"] - known_desc["mean"]
    pooled_sd = math.sqrt(((confab_desc["n"] - 1) * confab_desc["sd"] ** 2 + (known_desc["n"] - 1) * known_desc["sd"] ** 2) / (confab_desc["n"] + known_desc["n"] - 2))
    cohens_d = gap_mean / pooled_sd if pooled_sd > 0 else None
    report["baseline_projection_distribution"] = {
        "orientation": "readout_z field as stored in readout_scores.jsonl; cell.yaml registers this as the negative-z, confab-positive score (higher = more confab-like)",
        "confab": confab_desc,
        "known_correct_answered": known_desc,
        "gap_median_confab_minus_known": gap_median,
        "gap_mean_confab_minus_known": gap_mean,
        "pooled_sd": pooled_sd,
        "cohens_d": cohens_d,
        "auroc_separation": reproduced_auroc,
    }

    # ---- Baseline margin (tipping dose) distributions ----
    confab_tip_desc = describe(confab_tip)
    known_tip_desc = describe(known_tip)
    report["baseline_margin_distribution"] = {
        "confab_tipping_dose_abs": confab_tip_desc,
        "known_tipping_dose_abs_censoring_dominated": known_tip_desc,
        "note": "known median is a right-censoring artifact (top ladder rung recorded value per M1 Decision record item 7), not a real tipping measurement; see M1 Outcome",
    }

    # ---- Derived collapse-floor candidates (descriptive only; NOT a paired-shift computation) ----
    # Candidate framing: require a paired post-true-answer shift (baseline_z - true_answer_z)
    # on confab rows to reach some fraction of the *already-measured* baseline gap.
    candidate_fractions = [0.25, 0.5, 0.75, 1.0]
    collapse_candidates = []
    for frac in candidate_fractions:
        collapse_candidates.append({
            "fraction_of_median_gap": frac,
            "implied_absolute_shift_floor_z": frac * gap_median,
            "resulting_target_z_if_hit": confab_desc["median"] - frac * gap_median,
            "known_median_z_for_reference": known_desc["median"],
        })
    gap_ci = bootstrap_ci_median_diff(confab_z, known_z, seed=48260721)
    report["collapse_floor_candidates"] = {
        "gap_median": gap_median,
        "gap_median_bootstrap_ci95_row_level_10k_seed_48260721": gap_ci,
        "candidates": collapse_candidates,
        "method": "each candidate states: paired median (baseline_z - true_answer_z) on confab rows must be >= fraction * gap_median. No actual shift is computed -- M4 has no true-answer data yet.",
        "recommendation": "0.5 (halfway into the gap) as a moderate floor consistent with criterion (d)'s qualitative language ('move toward the known regime'); the gap itself is estimated with very tight precision (AUROC 0.982, Cohen's d 3.34, bootstrap CI on the median gap given above), so noise in the BASELINE gap is not the binding constraint -- the real risk is a shift driven by mere prompt-length/format change (appending ANY in-context text) rather than by the true answer specifically. Recommend the floor be a CONJUNCTION, not a single number: (1) paired median shift on confab rows >= 0.5 * gap_median (position-into-gap), AND (2) specificity: the true-answer shift exceeds the false-answer/placebo shift by a paired bootstrap 95% CI that excludes zero (same convention as M2 Decision record item 4). Exact fraction for (1) is a PI judgment call; (2)'s existence as a required leg is the derivation-time recommendation.",
    }

    # ---- Margin-lengthening option costs ----
    n_confab_total = len(confab_tip)
    n_confab_uncensored = n_confab_total - len(confab_tip_censored)
    n_known_total = len(known_tip)
    ladder_rungs = 10  # from M1 cell.yaml / AMENDMENT design section

    option_a = {
        "description": "single-dose survival at each row's OWN M1 tipping dose",
        "population": "confab rows with a genuine (non-right-censored) tipping dose",
        "n_eligible_confab_rows": n_confab_uncensored,
        "arms_requiring_new_generation": ["true_answer", "false_answer_placebo"],
        "arms_reused_from_M1_zero_new_generations": ["no_answer_baseline (tautological: M1's own generation at the tipping rung already establishes abstention there)"],
        "generations_per_row_per_new_arm": 1,
        "total_new_generations": n_confab_uncensored * 2,
    }
    option_b = {
        "description": "full ladder re-run under the true-answer condition (and placebo)",
        "population": "same confab rows (or full 400 including censored, since a full ladder could resolve some censored rows)",
        "ladder_rungs": ladder_rungs,
        "arms_requiring_new_generation": ["true_answer", "false_answer_placebo"],
        "generations_per_row_per_new_arm": ladder_rungs,
        "total_new_generations_uncensored_only": n_confab_uncensored * 2 * ladder_rungs,
        "total_new_generations_full_400": 400 * 2 * ladder_rungs,
    }
    # Analogous SE-based floor derivation for the margin-lengthening rate difference,
    # mirroring M2 Decision record item 3's Wilson/Hanley-McNeil style anchoring.
    # Uses only n (a design constant, not a measured M4 quantity) -- Wilson half-width
    # at worst-case p=0.5 for the paired rate-difference SE.
    n_margin = n_confab_uncensored
    wilson_se_p05 = math.sqrt(0.25 / n_margin)
    wilson_halfwidth_95 = 1.96 * wilson_se_p05
    report["margin_lengthening_options"] = {
        "option_a_single_dose_survival": option_a,
        "option_b_full_ladder_rerun": option_b,
        "cost_ratio_b_over_a": (option_b["total_new_generations_uncensored_only"] / option_a["total_new_generations"]),
        "recommendation": "Option A: ~10x cheaper, and the M1b batch-composition lesson (see mechanism qwen-midband-margin-separation-is-instrument-resolution-limited) argues for fewer generations per row batched consistently rather than a full re-ladder that reintroduces the same resolution-limited noise at every rung.",
        "criterion_design": "lengthened = survives (non-abstaining, well-formed) at the row's own tipping dose under the true-answer arm. no_answer_baseline survival is tautologically 0% by definition of tipping dose (0 new generations needed). Primary test: paired rate difference (true_answer survival rate minus false_answer/placebo survival rate) on the n_eligible_confab_rows population, row-level bootstrap 95% CI (10000 resamples, repo statistical convention), floor = CI excludes zero AND point estimate clears a pre-registered absolute margin.",
        "floor_derivation_analogous_to_M2_item3": {
            "n_margin_population": n_margin,
            "wilson_se_at_worst_case_p0.5": wilson_se_p05,
            "wilson_95_halfwidth": wilson_halfwidth_95,
            "candidate_floor_absolute_rate_difference": round(wilson_halfwidth_95, 3),
            "note": "one conservative unpaired half-width at n=308, same style as M2's 0.02 AUROC floor; the PAIRED design (same rows, two arms) has strictly smaller variance than this unpaired anchor, so a floor set at this half-width is comfortably resolvable if a real effect exists -- exact floor value is still a PI call, this is the derivation anchor only.",
        },
    }

    # ---- Full arm x population x measurement count matrix ----
    n_confab_projection = n_confab_total  # all confab rows have a projection regardless of censoring
    n_known_projection = n_known_total
    projection_arms = ["no_answer_baseline", "true_answer", "false_answer_placebo"]
    matrix = {
        "channel_1_projection_capture_forward_pass_only": {
            "confab_population_n": n_confab_projection,
            "known_population_n": n_known_projection,
            "arms": projection_arms,
            "captures_per_row_per_arm": 1,
            "total_captures_confab": n_confab_projection * len(projection_arms),
            "total_captures_known": n_known_projection * len(projection_arms),
            "total_captures_all": (n_confab_projection + n_known_projection) * len(projection_arms),
            "note": "no_answer_baseline arm is IDENTICAL prompt text to the already-committed M2 readout_scores.jsonl capture, but M1b's single-batching-regime lesson argues for recapturing it fresh within the same M4 batch composition rather than reusing the separately-batched M2 artifact for a paired comparison -- capture is cheap (forward pass only), so the cost of doing so is negligible.",
        },
        "channel_2_margin_generation_option_a": {
            "confab_population_n": n_confab_uncensored,
            "known_population_n": "not applicable in the primary design (known rows are ~89% right-censored, no finite own-tipping-dose to test lengthening at); proposed as a TO-DECIDE control using a fixed reference dose instead, see ambiguity notes",
            "arms_with_new_generation": ["true_answer", "false_answer_placebo"],
            "generations_per_row_per_arm": 1,
            "total_generations_confab": n_confab_uncensored * 2,
        },
        "grand_total_new_model_passes_option_a": (n_confab_projection + n_known_projection) * len(projection_arms) + n_confab_uncensored * 2,
    }
    report["full_arm_population_matrix"] = matrix

    # ---- Injection template (structural placeholders only, never real text) ----
    report["injection_template_structural"] = {
        "no_answer_baseline": "{system_prompt}\n{user_question}",
        "true_answer": "{system_prompt}\n{user_question}\n\n[Context: the answer is {true_answer}.]",
        "false_answer_placebo": "{system_prompt}\n{user_question}\n\n[Context: the answer is {false_answer}.]",
        "false_answer_source": "TO-DECIDE: a plausible-but-wrong answer, structurally distinct from 'true_answer' only in content, never read/inspected by the design derivation step; the placebo's construction (e.g. a distractor from the same dataset family, or an irrelevant fact) is a harness-build-time decision, not a design-derivation-time one.",
    }

    # ---- Knob table ----
    report["knob_table"] = [
        {"knob": "collapse floor (fraction of baseline gap)", "label": "TO-DECIDE (candidates DERIVED from baseline gap)", "candidates": candidate_fractions, "derivation": "gap_median computed from committed M2 readout_scores.jsonl; fraction itself not derivable without real shift data, PI must pick"},
        {"knob": "margin-lengthening criterion", "label": "DERIVED (population) + JUDGMENT (option choice)", "value": "Option A recommended; population = uncensored confab subset (n given above)"},
        {"knob": "population counts", "label": "DERIVED from M1 registered subsample", "value": {"confab_projection": n_confab_projection, "confab_margin_eligible": n_confab_uncensored, "known_projection_control": n_known_projection}},
        {"knob": "arm set", "label": "JUDGMENT", "value": projection_arms},
        {"knob": "capture convention", "label": "CONVENTION (byte-identical reuse of M2 pins)", "value": {"direction_sha256": "937d1bffe1924e73bca40a88c8096d7e01bb67c5b64286362196aa968e2c2e1f", "layer_index": 19, "hs_index": 20, "orientation": "negative z, confab-positive"}},
        {"knob": "bootstrap seeds", "label": "CONVENTION (lineage continuation)", "value": "M4 starts 48260721 (M1 48260714-16, M2 48260717-18, M1b 48260719-20)"},
        {"knob": "self-blinding rule", "label": "CONVENTION (carried from M2)", "value": "no paired-shift AUROC/median computed pre-sign; only distributions/hashes/counts of already-committed baseline data, as executed in this script"},
        {"knob": "preflight", "label": "CONVENTION (standing directive)", "value": "GPU smoke (8-row capture + 8-row generation) before any full capture/generation pass, code-enforced pass marker"},
        {"knob": "known-row margin control", "label": "AMBIGUOUS / TO-DECIDE", "value": "no finite own-tipping-dose exists for ~89% of known rows (right-censored); PI call needed on whether to (a) skip margin-lengthening for knowns entirely, using only the projection-specificity check, or (b) test at a fixed reference dose (e.g. setpoint dose_abs 12.608) despite the ceiling effect"},
        {"knob": "false-answer placebo construction", "label": "TO-DECIDE", "value": "structural template fixed; actual distractor-selection rule is a harness-build-time decision"},
    ]

    out_path = Path("/tmp/claude-1000/-mnt-f-Code-Epistemic-Humility-Research/292064d8-cb30-460a-ad90-29559ab5cf7f/scratchpad/m4/m4_design_report.json")
    out_path.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
