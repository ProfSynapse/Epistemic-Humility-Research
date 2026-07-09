#!/usr/bin/env python3
"""Amendment AH Stage-0 EXPANSION — pool v2.1 (CPU).

Team-lead task 2026-07-03 step 4. Rebuilds the caliper-matched divergent pool
over the UNION of the original 5,000 mined rows + the expansion, using the SAME
recipe as the redesign check: greedy 1:1 nearest-neighbor match on caution
distance, caliper 0.25 * caution_base_sd (= 3.10 on the frozen AG axis).

Contrasts (prime DIRECTION held constant, READOUT state varied within gold class):
  release (gold-unanswerable):
    congruent   = ALL consensus D-over rows (probe-certain unanswerable), carry category
    incongruent = probe-uncertain gold-unanswerable, caliper-matched
  muzzle (gold-answerable):
    congruent   = ALL probe-uncertain gold-answerable consensus rows (old 75 + new)
    incongruent = concordant-known (probe-certain answerable), caliper-matched
  positive-control stratum:
    150 concordant-known from the LOW-caution end, sampled across
    SelfAware / KUQ / TriviaQA / PopQA sources.

Consensus rule = L20 AND L24 AND L28 on the divergent side at band 0, with z =
per-probe SD on the ORIGINAL mined pool (frozen mining z, comparable across
passes). Caution axis = frozen AG axis (reconstructed identically to the
redesign check). Category on the original 1,768 KUQ rows comes from the backfill
sidecar; on expansion rows from the expansion scored file.

Writes analysis/ah_stage0/expansion/:
  pool_v21.jsonl        per-row {safe_key, source, category, label(gold class),
                        scores, caution_dist, contrast, congruent, stratum}
  pool_v21_composition.json  category split of congruent-release (+ crisp flag),
                        source split of congruent-muzzle, post-match overlap/AUC
                        per contrast, total row + generation counts.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from safetensors import safe_open

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ARCHIVE_AMENDMENTS_DIR))
from path_compat import repo_root  # noqa: E402
from amendment_ah_redesign_collinearity import (  # noqa: E402
    load_af_caution, overlap_coefficient, separability_auc,
)
from amendment_ah_stage0_expand_score import canon_category, CRISP_FLAG  # noqa: E402

CANONICAL = repo_root()
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
EXP = STAGE0 / "expansion"
ORIG_PREGEN = STAGE0 / "pregen"
ORIG_SCORED = STAGE0 / "score" / "scored_rows.jsonl"
BACKFILL = EXP / "mined_kuq_category_backfill.jsonl"
EXP_SCORED = EXP / "score" / "scored_rows.jsonl"
GRID = STAGE0 / "score" / "divergence_grid.json"
OUT = EXP

CALIPER_FRAC = 0.25
N_POS_CONTROL = 150
POOL_SEED = 20260703
GEN_PER_ROW = 2  # release + muzzle arms both re-generate; positive control 1 arm


def load_jsonl(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def build_union():
    """Assemble a unified per-row record for original 5,000 + expansion.
    Returns list of dicts with doubt scores, caution_dist, gold, source, category."""
    clf_c, sign, base_sd, cv_auroc = load_af_caution()

    # --- original 5,000: recompute caution from pregen L24; category from sidecar ---
    orig_scored = {r["row_key"]: r for r in load_jsonl(ORIG_SCORED)}
    backfill = {r["row_key"]: r.get("category", "") for r in load_jsonl(BACKFILL)}
    orig_rows = load_jsonl(ORIG_PREGEN / "rows.jsonl")

    union = []
    for r in orig_rows:
        with safe_open(str(ORIG_PREGEN / f"{r['safe_key']}__pre.safetensors"), "pt") as st:
            v = st.get_tensor("L24").float().numpy().astype(np.float64)
        caution = float(sign * clf_c.decision_function(v[None, :])[0])
        sc = orig_scored[r["row_key"]]
        cat = backfill.get(r["row_key"], "")  # only KUQ unknowns have it
        union.append({
            "safe_key": r["safe_key"], "row_key": r["row_key"],
            "pregen_dir": str(ORIG_PREGEN), "pass": "mined",
            "label": r["label"], "source": r["source"], "question": r["question"],
            "category": cat, "category_raw": cat, "category_canon": canon_category(cat),
            "score_L20": sc["score_L20"], "score_L24": sc["score_L24"],
            "score_L28": sc["score_L28"], "fold_scores": sc["fold_scores"],
            "caution_dist": caution, "caution_dist_z": caution / base_sd,
        })

    # --- expansion: caution already computed in expand_score ---
    for r in load_jsonl(EXP_SCORED):
        union.append({
            "safe_key": r["safe_key"], "row_key": r["row_key"],
            "pregen_dir": str(EXP / "pregen"), "pass": "expansion",
            "label": r["label"], "source": r["source"], "question": r["question"],
            "category": r.get("category", ""),
            "category_raw": r.get("category_raw", r.get("category", "")),
            "category_canon": r.get("category_canon", canon_category(r.get("category", ""))),
            "score_L20": r["score_L20"], "score_L24": r["score_L24"],
            "score_L28": r["score_L28"], "fold_scores": r["fold_scores"],
            "caution_dist": r["caution_dist"],
            "caution_dist_z": r["caution_dist_z"],
        })
    return union, base_sd, cv_auroc, sign


def run(args) -> int:
    rng = np.random.default_rng(POOL_SEED)

    z = json.loads(GRID.read_text())["score_sd"]
    union, base_sd, cv_auroc, sign = build_union()
    n = len(union)
    print(f"[ahx/pool] union rows: {n} (mined + expansion)", flush=True)

    L20 = np.array([r["score_L20"] for r in union])
    L24 = np.array([r["score_L24"] for r in union])
    L28 = np.array([r["score_L28"] for r in union])
    caution = np.array([r["caution_dist"] for r in union])
    gold_known = np.array([1 if r["label"] == "known" else 0 for r in union])

    cons_certain = (L20 > 0) & (L24 > 0) & (L28 > 0)
    cons_uncertain = (L20 < 0) & (L24 < 0) & (L28 < 0)

    # contrast cell masks
    m_rel_cong = cons_certain & (gold_known == 0)              # D-over
    m_rel_incong = (L24 < 0) & (gold_known == 0)               # probe-uncertain unanswerable
    m_muz_cong = cons_uncertain & (gold_known == 1)            # muzzle-rescue (old 75 + new)
    m_muz_incong = (L24 > 0) & (gold_known == 1)               # concordant-known

    print(f"[ahx/pool] release congruent(D-over)={int(m_rel_cong.sum())} "
          f"incong={int(m_rel_incong.sum())} | muzzle congruent={int(m_muz_cong.sum())} "
          f"incong={int(m_muz_incong.sum())}", flush=True)

    caliper = CALIPER_FRAC * base_sd

    def caliper_match(cong_idx, incong_idx):
        cong_idx = list(cong_idx)
        rng.shuffle(cong_idx)
        inc_arr = np.array(list(incong_idx))
        inc_c = caution[inc_arr]
        used = set(); pairs = []
        for ci in cong_idx:
            d = np.abs(inc_c - caution[ci])
            order = np.argsort(d)
            for j in order:
                if d[j] > caliper:
                    break
                cand = int(inc_arr[j])
                if cand not in used:
                    used.add(cand); pairs.append((ci, cand)); break
        return pairs

    rel_pairs = caliper_match(np.where(m_rel_cong)[0], np.where(m_rel_incong)[0])
    muz_pairs = caliper_match(np.where(m_muz_cong)[0], np.where(m_muz_incong)[0])
    print(f"[ahx/pool] matched pairs: release={len(rel_pairs)} muzzle={len(muz_pairs)}",
          flush=True)

    # --- positive-control stratum: 150 concordant-known, LOW-caution end,
    #     sampled across SelfAware / KUQ / TriviaQA / PopQA sources ---
    def source_group(src):
        if src.startswith("selfaware"):
            return "selfaware"
        if src.startswith("kuq"):
            return "kuq"
        if src == "triviaqa":
            return "triviaqa"
        if src == "popqa":
            return "popqa"
        return "other"

    conc_known_idx = np.where((L24 > 0) & (gold_known == 1))[0]
    # rank by caution ascending (lowest caution = most confidently answerable)
    conc_sorted = conc_known_idx[np.argsort(caution[conc_known_idx])]
    groups = {"selfaware": [], "kuq": [], "triviaqa": [], "popqa": []}
    for idx in conc_sorted:
        g = source_group(union[idx]["source"])
        if g in groups:
            groups[g].append(int(idx))
    # round-robin across available source groups from the low-caution end
    per = N_POS_CONTROL // 4
    pos_control = []
    for g in ["selfaware", "kuq", "triviaqa", "popqa"]:
        pos_control += groups[g][:per]
    # top up to 150 from the global low-caution end if a group was short
    if len(pos_control) < N_POS_CONTROL:
        have = set(pos_control)
        for idx in conc_sorted:
            if int(idx) not in have:
                pos_control.append(int(idx)); have.add(int(idx))
                if len(pos_control) >= N_POS_CONTROL:
                    break
    pos_control = pos_control[:N_POS_CONTROL]

    # --- assemble pool rows ---
    pool_rows = []
    seen = set()

    def add(idx, contrast, congruent, stratum):
        r = union[idx]
        key = (r["safe_key"], contrast, stratum)
        if key in seen:
            return
        seen.add(key)
        pool_rows.append({
            "safe_key": r["safe_key"], "row_key": r["row_key"],
            "pass": r["pass"], "pregen_dir": r["pregen_dir"],
            "source": r["source"], "category": r["category"],
            "category_raw": r.get("category_raw", r["category"]),
            "category_canon": r["category_canon"],
            "gold_class": ("answerable" if r["label"] == "known"
                           else "unanswerable"),
            "label": r["label"],
            "score_L20": round(r["score_L20"], 3),
            "score_L24": round(r["score_L24"], 3),
            "score_L28": round(r["score_L28"], 3),
            "caution_dist": round(r["caution_dist"], 3),
            "caution_dist_z": round(r["caution_dist_z"], 3),
            "contrast": contrast, "congruent": bool(congruent),
            "stratum": stratum,
        })

    for ci, ii in rel_pairs:
        add(ci, "release", True, "release")
        add(ii, "release", False, "release")
    for ci, ii in muz_pairs:
        add(ci, "muzzle", True, "muzzle")
        add(ii, "muzzle", False, "muzzle")
    for idx in pos_control:
        add(idx, "positive_control", True, "positive_control")

    with (OUT / "pool_v21.jsonl").open("w", encoding="utf-8") as fh:
        for row in pool_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    # ---- composition summary ----
    def crisp_flag_for(r):
        cc = r["category_canon"]
        if cc in CRISP_FLAG:
            return CRISP_FLAG[cc]
        if r["source"].startswith("selfaware"):
            return "selfaware"
        return cc  # controversial / ambiguous / unsolved_problem / future_unknown / (none)

    rel_cong_rows = [r for r in pool_rows if r["contrast"] == "release" and r["congruent"]]
    muz_cong_rows = [r for r in pool_rows if r["contrast"] == "muzzle" and r["congruent"]]

    rel_cong_cat = Counter(r["category_canon"] for r in rel_cong_rows)
    rel_cong_crisp = Counter(crisp_flag_for(r) for r in rel_cong_rows)
    rel_cong_src = Counter(r["source"] for r in rel_cong_rows)
    muz_cong_src = Counter(r["source"] for r in muz_cong_rows)

    def post_overlap(contrast):
        c = np.array([r["caution_dist"] for r in pool_rows
                      if r["contrast"] == contrast and r["congruent"]])
        i = np.array([r["caution_dist"] for r in pool_rows
                      if r["contrast"] == contrast and not r["congruent"]])
        if len(c) == 0 or len(i) == 0:
            return None
        return {
            "n_congruent": int(len(c)), "n_incongruent": int(len(i)),
            "mean_congruent": round(float(c.mean()), 3),
            "mean_incongruent": round(float(i.mean()), 3),
            "sd_congruent": round(float(c.std()), 3),
            "sd_incongruent": round(float(i.std()), 3),
            "overlap_coefficient": round(overlap_coefficient(c, i), 4),
            "separability_auc": (round(separability_auc(c, i), 4)
                                 if separability_auc(c, i) is not None else None),
        }

    pos_src = Counter(source_group(union[idx]["source"]) for idx in pos_control)

    # generation counts: each unique row is generated once per arm it appears in.
    n_rows_total = len({r["safe_key"] for r in pool_rows})
    n_release = len([r for r in pool_rows if r["contrast"] == "release"])
    n_muzzle = len([r for r in pool_rows if r["contrast"] == "muzzle"])
    n_pos = len([r for r in pool_rows if r["contrast"] == "positive_control"])
    # main run generates each pool row under baseline + prime arm (release/muzzle
    # contrasts get a congruent-direction prime + baseline); estimate = rows*2.
    est_generations = (n_release + n_muzzle) * GEN_PER_ROW + n_pos

    comp = {
        "amendment": "AH", "stage": "pool_v21",
        "caution_axis": {"cv_auroc": round(cv_auroc, 4), "base_sd": round(base_sd, 3),
                         "sign": sign, "caliper": round(caliper, 3)},
        "union_n": n,
        "mined_pool_z_used": z,
        "cell_sizes_union": {
            "release_congruent_Dover": int(m_rel_cong.sum()),
            "release_incongruent": int(m_rel_incong.sum()),
            "muzzle_congruent_rescue": int(m_muz_cong.sum()),
            "muzzle_incongruent_concordant_known": int(m_muz_incong.sum()),
            "concordant_known_pool_for_pos_control": int(len(conc_known_idx)),
        },
        "matched_pairs": {"release": len(rel_pairs), "muzzle": len(muz_pairs)},
        "congruent_release_category_split": dict(rel_cong_cat.most_common()),
        "congruent_release_crisp_flag": dict(rel_cong_crisp.most_common()),
        "congruent_release_source_split": dict(rel_cong_src.most_common()),
        "congruent_muzzle_source_split": dict(muz_cong_src.most_common()),
        "positive_control_source_split": dict(pos_src.most_common()),
        "post_match_overlap": {
            "release": post_overlap("release"),
            "muzzle": post_overlap("muzzle"),
        },
        "counts": {
            "unique_rows": n_rows_total,
            "release_rows": n_release, "muzzle_rows": n_muzzle,
            "positive_control_rows": n_pos,
            "total_pool_row_entries": len(pool_rows),
            "estimated_generations_main_run": est_generations,
        },
        "recipe": {
            "match": "greedy 1:1 NN on caution distance",
            "caliper_units": f"{CALIPER_FRAC}*caution_base_sd",
            "consensus": "L20&L24&L28 same side, band0",
            "seed": POOL_SEED,
        },
        "pool_file": str(OUT / "pool_v21.jsonl"),
        "note": "PROPOSAL. Congruent-release = ALL consensus D-over (uncapped). "
                "Congruent-muzzle = ALL consensus muzzle-rescue (old 75 + new). "
                "Incongruent arms caliper-matched. Positive control = 150 "
                "low-caution concordant-known across 4 sources.",
    }
    (OUT / "pool_v21_composition.json").write_text(json.dumps(comp, indent=2),
                                                  encoding="utf-8")
    print(json.dumps(comp, indent=2), flush=True)
    print(f"[ahx/pool] DONE -> {OUT/'pool_v21.jsonl'}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
