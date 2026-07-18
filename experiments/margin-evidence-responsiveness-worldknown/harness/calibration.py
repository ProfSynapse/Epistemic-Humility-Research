#!/usr/bin/env python3
"""Blinded calibration slices for margin-evidence-responsiveness-worldknown
(M4-WK) (gates.yaml `SC2_grading_integrity`).

CPU-only pool construction, seed 48260726 (config.CALIBRATION_SLICE_SEED).
Two DISTINCT slices (do not conflate):

  1. CORRECTNESS calibration slice (gates.yaml SC2 bullet 1 / MINOR m3):
     bounds the alias-grader FALSE-WRONG rate (a correctly-phrased answer
     scored wrong and mislabeled confab) -- the one new construct risk this
     rebase introduces (correctness is now on the critical path defining the
     confab class, unlike KUQ). Target n >= 150 (config.
     CORRECTNESS_CALIBRATION_MIN_N), stratified across roles (confab /
     correct / refused) by largest-remainder allocation (ported convention
     from `margin-mapping/harness/build_calibration_pool.py`, read in full
     before writing this), AND additionally stratified across prop
     categories WITHIN the confab stratum (cell.yaml/gates.yaml text: "and
     across prop categories within the confab class"). BUILD-TIME
     INTERPRETATION (documented per this repo's convention for such gaps,
     mirroring build_calibration_pool.py's own documented interpretations):
     the false-wrong RATE itself is scored only over the CONFAB-labeled
     subset of the graded slice (a false-wrong event is only coherent for a
     row the census actually labeled confab); the correct/refused strata are
     included in the drawn slice as a broader sanity check on the alias
     grader but do not enter the false-wrong-rate denominator.
  2. CHANNEL-2 ABSTENTION calibration slice (gates.yaml SC2 bullet 2 + CG1):
     validates detector_v2's refused_v2 bit against a blinded adjudicator on
     rows drawn from the channel-2 survival true_answer/false_answer arms
     (stratified across those two arms). CG1 floors (clear-negative
     agreement >= 0.95, clear-positive agreement >= 0.60, >= 25
     clear-positive decoys) and the detector-vs-adjudication disagreement
     ceiling (<= 0.05) are config.py constants ported from M1's CG1
     convention.

Both slices follow the SAME commit-before-grade / commit-before-unblind
ceremony (SC2): pool sha256 + opaque-id list committed BEFORE grading;
graded-file sha256 committed BEFORE unblind (enforced in code below).

NOT implemented here: the actual blinded-grading PASS (a human or a
carefully isolated adjudicator that must never see the census's own
detector_v2 verdict or row_key -- a leaking context would break the SC2
gate's validity). This script only builds the blinded shard and, given an
already-graded shard (`--graded-shard`), scores it. Running the grading
itself is a distinct action reserved for lead decision (see harness-builder
final report): who/what adjudicates, and how blinding is enforced for that
specific mechanism, is not this build-time script's call to make.
"""

from __future__ import annotations

import argparse
import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import popqa_pool  # noqa: E402
import stats  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
CAL_DIR = ANALYSIS / "calibration"
SELECTION_DIR = COMMITTED / "selection"
CENSUS_PATH = COMMITTED / "census" / "qwen35_4b_worldknown_census.jsonl"
CENSUS_GEN_TEXT_PATH = ANALYSIS / "census" / "qwen35_4b_worldknown_gen_text.jsonl"
SURVIVAL_DIR = ANALYSIS / "channel2_survival"

SEED = config.CALIBRATION_SLICE_SEED


def largest_remainder_allocation(strata_sizes: dict[Any, int], target_total: int) -> dict[Any, int]:
    """Ported verbatim (logic) from margin-mapping/harness/
    build_calibration_pool.py::largest_remainder_allocation."""
    universe = sum(strata_sizes.values())
    ideal = {k: target_total * n / universe for k, n in strata_sizes.items()}
    floors = {k: int(v) for k, v in ideal.items()}
    remainder = target_total - sum(floors.values())
    order = sorted(ideal.keys(), key=lambda k: (-(ideal[k] - floors[k]), str(k)))
    for k in order[:remainder]:
        floors[k] += 1
    assert sum(floors.values()) == target_total
    for k, v in floors.items():
        assert v <= strata_sizes[k], f"stratum {k} allocation {v} exceeds size {strata_sizes[k]}"
    return floors


def _new_opaque_ids(n: int) -> list[str]:
    seen: set[str] = set()
    out = []
    while len(out) < n:
        oid = secrets.token_hex(8)
        if oid not in seen:
            seen.add(oid)
            out.append(oid)
    return out


# ---------------------------------------------------------------------------
# 1. Correctness calibration slice
# ---------------------------------------------------------------------------

def build_correctness_pool(args: argparse.Namespace) -> int:
    config.assert_pinned_hashes()
    if not CENSUS_PATH.is_file():
        raise SystemExit(f"calibration FAIL: no committed census at {CENSUS_PATH}; run census.py first.")
    if not CENSUS_GEN_TEXT_PATH.is_file():
        raise SystemExit(f"calibration FAIL: no census generation-text sidecar at {CENSUS_GEN_TEXT_PATH}.")

    census_rows = common.load_jsonl(CENSUS_PATH)
    census_by_key = {r["row_key"]: r for r in census_rows}
    gen_text_by_key = {r["row_key"]: r for r in common.load_jsonl(CENSUS_GEN_TEXT_PATH)}
    pool = popqa_pool.load_pool()

    by_role: dict[str, list[str]] = {"confab_on_answerable": [], "correct_on_answerable": [], "refused_on_answerable": []}
    for r in census_rows:
        if r["role"] in by_role:
            by_role[r["role"]].append(r["row_key"])
    for role in by_role:
        by_role[role].sort()

    strata_sizes = {role: len(rks) for role, rks in by_role.items() if rks}
    target = max(args.n, config.CORRECTNESS_CALIBRATION_MIN_N)
    alloc = largest_remainder_allocation(strata_sizes, target)

    drawn: list[dict[str, Any]] = []
    for role, rks in by_role.items():
        n = alloc.get(role, 0)
        if role == "confab_on_answerable":
            # additionally stratify by prop category within confab (cell.yaml
            # "and across prop categories within the confab class").
            by_cat: dict[str, list[str]] = {}
            for rk in rks:
                by_cat.setdefault(pool[rk]["category"], []).append(rk)
            cat_sizes = {c: len(v) for c, v in by_cat.items()}
            cat_alloc = largest_remainder_allocation(cat_sizes, n)
            for cat, cat_rks in by_cat.items():
                cn = cat_alloc.get(cat, 0)
                rng = random.Random(f"{SEED}:correctness:{role}:{cat}")
                shuffled = cat_rks[:]
                rng.shuffle(shuffled)
                for rk in shuffled[:cn]:
                    drawn.append({"row_key": rk, "role": role, "category": cat})
        else:
            rng = random.Random(f"{SEED}:correctness:{role}")
            shuffled = rks[:]
            rng.shuffle(shuffled)
            for rk in shuffled[:n]:
                drawn.append({"row_key": rk, "role": role, "category": pool[rk]["category"]})

    CAL_DIR.mkdir(parents=True, exist_ok=True)
    opaque_ids = _new_opaque_ids(len(drawn))
    id_map = []
    shard = []
    for item, oid in zip(drawn, opaque_ids):
        gt = gen_text_by_key.get(item["row_key"])
        if gt is None:
            raise SystemExit(f"calibration FAIL: no generation-text sidecar entry for drawn row_key {item['row_key']!r}")
        census_rec = census_by_key.get(item["row_key"])
        if census_rec is None:
            raise SystemExit(f"calibration FAIL: no committed census entry for drawn row_key {item['row_key']!r}")
        # "answer_value" (the detector's parsed answer string) is not carried
        # into census.py's committed census or gen-text sidecar (only the raw
        # generation_text and a few grading booleans are) -- the adjudicator
        # sees the full generation_text directly and does not need it
        # pre-parsed; "correct_v2" (a boolean, not text) IS in the committed
        # census, so it is read from there rather than the sidecar.
        # decoy_type "clear_positive": every drawn correct_on_answerable row is
        # a row the alias grader already matched unambiguously (detector_
        # correct_v2=True by construction of that role) -- used as a lead-
        # directed CG1-style sanity check on the adjudicator's own accuracy
        # before trusting their false-wrong calls on the ambiguous confab
        # rows. NEVER exposed in `shard` (adjudicator-visible); lives only in
        # id_map (private, gitignored until unblind).
        decoy_type = "clear_positive" if item["role"] == "correct_on_answerable" else None
        id_map.append({
            "opaque_id": oid, "row_key": item["row_key"], "role": item["role"], "category": item["category"],
            "detector_correct_v2": census_rec.get("correct_v2"), "decoy_type": decoy_type,
        })
        shard.append({
            "opaque_id": oid, "question": pool[item["row_key"]]["question"],
            "gold_aliases": pool[item["row_key"]]["aliases"], "model_answer_text": gt.get("generation_text"),
        })

    n_clear_positive_decoys = sum(1 for r in id_map if r["decoy_type"] == "clear_positive")
    if n_clear_positive_decoys < config.CG1_CLEAR_POSITIVE_DECOYS_MIN:
        raise SystemExit(
            f"calibration FAIL: only {n_clear_positive_decoys} clear_positive decoys drawn "
            f"(correct_on_answerable stratum), below CG1 floor {config.CG1_CLEAR_POSITIVE_DECOYS_MIN}; "
            "increase --n or the correct_on_answerable allocation."
        )

    shard_path = CAL_DIR / "correctness_calibration_shard.jsonl"
    id_map_path = CAL_DIR / "correctness_calibration_id_map.jsonl"
    common.write_jsonl(shard_path, shard)
    common.write_jsonl(id_map_path, id_map)
    shard_sha256 = common.sha256_of_file(shard_path)
    id_map_sha256 = common.sha256_of_file(id_map_path)

    manifest = {
        "seed": SEED, "target_n": target, "n_drawn": len(drawn),
        "role_allocation": alloc, "shard_sha256": shard_sha256,
        "id_map_sha256": id_map_sha256,  # blind-index->row_key mapping committed as a HASH ONLY; id_map.jsonl itself stays gitignored (analysis/) until unblind
        "n_clear_positive_decoys": n_clear_positive_decoys,
        "opaque_id_list": sorted(opaque_ids), "committed_before_grading": True,
    }
    common.write_json(COMMITTED / "correctness_calibration_pool_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "opaque_id_list"}, indent=2), flush=True)
    return 0


def score_correctness(args: argparse.Namespace) -> int:
    """`--graded-shard` is a JSONL of {opaque_id, correct: bool, note: str}
    produced by whatever blinded-grading process the lead designates; this
    function only consumes it, never produces it. (Schema confirmed against
    the M4-WK grading ceremony's actual graded file, commit 1c28acde:
    `correct`, not the earlier placeholder `adjudicated_correct` this
    docstring originally guessed at build time.)"""
    config.assert_pinned_hashes()
    manifest = common.load_json(COMMITTED / "correctness_calibration_pool_manifest.json")
    shard_path = CAL_DIR / "correctness_calibration_shard.jsonl"
    live_sha256 = common.sha256_of_file(shard_path)
    if live_sha256 != manifest["shard_sha256"]:
        raise SystemExit(f"calibration FAIL: correctness shard sha256 {live_sha256} != committed pin {manifest['shard_sha256']} (pool drifted after commit).")

    graded = {r["opaque_id"]: r for r in common.load_jsonl(Path(args.graded_shard))}
    id_map = {r["opaque_id"]: r for r in common.load_jsonl(CAL_DIR / "correctness_calibration_id_map.jsonl")}
    missing = set(id_map.keys()) - set(graded.keys())
    if missing:
        raise SystemExit(f"calibration FAIL: {len(missing)} opaque_ids in the shard have no graded entry: {sorted(missing)[:10]}")

    graded_sha256 = common.sha256_of_file(Path(args.graded_shard))

    confab_ids = [oid for oid, m in id_map.items() if m["role"] == "confab_on_answerable"]
    n_confab_graded = len(confab_ids)
    n_false_wrong = sum(1 for oid in confab_ids if bool(graded[oid]["correct"]))
    wilson = stats.wilson(n_false_wrong, n_confab_graded)

    # lead-directed CG1-style sanity check on the adjudicator's own accuracy,
    # scored on the clear_positive decoys (correct_on_answerable rows, ground
    # truth "correct" by construction of that role) BEFORE trusting their
    # false-wrong calls on the ambiguous confab rows above. gates.yaml's own
    # CG1 bullet ties the clear_negative/clear_positive agreement floors to
    # the abstention slice's refusal classification specifically; there is no
    # natural clear_negative analog for a correctness judgment (the confab
    # role IS the ambiguous class under test, so it cannot supply a ground-
    # truth-wrong decoy without circularity), so only the clear_positive count
    # + agreement rate is computed here, per the lead's explicit ask.
    decoy_ids = [oid for oid, m in id_map.items() if m.get("decoy_type") == "clear_positive"]
    n_clear_positive_decoys_graded = len(decoy_ids)
    n_clear_positive_agree = sum(1 for oid in decoy_ids if bool(graded[oid]["correct"]) == True)
    clear_positive_agreement = (n_clear_positive_agree / n_clear_positive_decoys_graded) if decoy_ids else None

    result = {
        "n_confab_graded": n_confab_graded, "n_false_wrong": n_false_wrong,
        "false_wrong_rate_wilson_ci_95": wilson,
        "null_interpretable_max": config.CORRECTNESS_CALIBRATION_FALSE_WRONG_NULL_INTERPRETABLE_MAX,
        "null_would_be_interpretable": wilson["rate"] <= config.CORRECTNESS_CALIBRATION_FALSE_WRONG_NULL_INTERPRETABLE_MAX,
        "clear_positive_decoys": {
            "n": n_clear_positive_decoys_graded, "n_agree": n_clear_positive_agree,
            "agreement_rate": clear_positive_agreement,
            "agreement_floor": config.CG1_CLEAR_POSITIVE_AGREEMENT_MIN,
            "floor_min_decoys": config.CG1_CLEAR_POSITIVE_DECOYS_MIN,
        },
        "graded_shard_sha256": graded_sha256,
        "note": "a POSITIVE (d) verdict is robust regardless of this bound (the bias is conservative); this bound only gates interpretability of a NULL result (gates.yaml SC2 bullet 1).",
    }
    common.write_json(CAL_DIR / "correctness_calibration_score.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return 0


# ---------------------------------------------------------------------------
# 2. Channel-2 abstention calibration slice
# ---------------------------------------------------------------------------

def build_abstention_pool(args: argparse.Namespace) -> int:
    config.assert_pinned_hashes()
    direction = args.direction
    rows_by_arm: dict[str, list[dict[str, Any]]] = {}
    for arm in ("true_answer", "false_answer_placebo"):
        path = SURVIVAL_DIR.parent / "runlog" / f"channel2_survival_{direction}__{arm}.jsonl"
        if not path.is_file():
            raise SystemExit(f"calibration FAIL: no {path}; run survival_channel2.py generate --direction {direction} first.")
        rows_by_arm[arm] = common.load_jsonl(path)

    strata_sizes = {arm: len(rows) for arm, rows in rows_by_arm.items()}
    target = max(args.n, 1)
    alloc = largest_remainder_allocation(strata_sizes, min(target, sum(strata_sizes.values())))

    drawn: list[dict[str, Any]] = []
    for arm, rows in rows_by_arm.items():
        n = alloc.get(arm, 0)
        rng = random.Random(f"{SEED}:abstention:{direction}:{arm}")
        shuffled = rows[:]
        rng.shuffle(shuffled)
        for rec in shuffled[:n]:
            drawn.append({"row_key": rec["row_key"], "arm": arm, "refused_v2_detector": bool(rec["refused_v2"]), "well_formed": bool(rec["well_formed"]), "text": rec["answer_text"]})

    CAL_DIR.mkdir(parents=True, exist_ok=True)
    opaque_ids = _new_opaque_ids(len(drawn))
    id_map, shard = [], []
    for item, oid in zip(drawn, opaque_ids):
        id_map.append({"opaque_id": oid, "row_key": item["row_key"], "direction": direction, "arm": item["arm"], "refused_v2_detector": item["refused_v2_detector"], "well_formed": item["well_formed"]})
        shard.append({"opaque_id": oid, "model_answer_text": item["text"]})

    shard_path = CAL_DIR / f"abstention_calibration_shard_{direction}.jsonl"
    id_map_path = CAL_DIR / f"abstention_calibration_id_map_{direction}.jsonl"
    common.write_jsonl(shard_path, shard)
    common.write_jsonl(id_map_path, id_map)
    shard_sha256 = common.sha256_of_file(shard_path)

    manifest = {
        "direction": direction, "seed": SEED, "target_n": target, "n_drawn": len(drawn),
        "arm_allocation": alloc, "shard_sha256": shard_sha256,
        "opaque_id_list": sorted(opaque_ids), "committed_before_grading": True,
    }
    common.write_json(COMMITTED / f"abstention_calibration_pool_manifest_{direction}.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k != "opaque_id_list"}, indent=2), flush=True)
    return 0


def score_abstention(args: argparse.Namespace) -> int:
    config.assert_pinned_hashes()
    direction = args.direction
    manifest = common.load_json(COMMITTED / f"abstention_calibration_pool_manifest_{direction}.json")
    shard_path = CAL_DIR / f"abstention_calibration_shard_{direction}.jsonl"
    live_sha256 = common.sha256_of_file(shard_path)
    if live_sha256 != manifest["shard_sha256"]:
        raise SystemExit(f"calibration FAIL: abstention shard sha256 {live_sha256} != committed pin {manifest['shard_sha256']} (pool drifted after commit).")

    graded = {r["opaque_id"]: r for r in common.load_jsonl(Path(args.graded_shard))}
    id_map = {r["opaque_id"]: r for r in common.load_jsonl(CAL_DIR / f"abstention_calibration_id_map_{direction}.jsonl")}
    missing = set(id_map.keys()) - set(graded.keys())
    if missing:
        raise SystemExit(f"calibration FAIL: {len(missing)} opaque_ids have no graded entry: {sorted(missing)[:10]}")
    graded_sha256 = common.sha256_of_file(Path(args.graded_shard))

    agree = disagree = 0
    for oid, m in id_map.items():
        detector_says_refused = m["refused_v2_detector"]
        adjudicator_says_refused = bool(graded[oid]["adjudicated_refused"])
        if detector_says_refused == adjudicator_says_refused:
            agree += 1
        else:
            disagree += 1
    n = agree + disagree
    disagreement_rate = disagree / n if n else None

    clear_negative = [oid for oid, m in id_map.items() if graded[oid].get("decoy_type") == "clear_negative"]
    clear_positive = [oid for oid, m in id_map.items() if graded[oid].get("decoy_type") == "clear_positive"]

    def _agreement(ids: list[str]) -> Optional[float]:
        if not ids:
            return None
        a = sum(1 for oid in ids if id_map[oid]["refused_v2_detector"] == bool(graded[oid]["adjudicated_refused"]))
        return a / len(ids)

    cg1 = {
        "n_clear_negative_decoys": len(clear_negative), "clear_negative_agreement": _agreement(clear_negative),
        "n_clear_positive_decoys": len(clear_positive), "clear_positive_agreement": _agreement(clear_positive),
        "clear_positive_decoys_floor": config.CG1_CLEAR_POSITIVE_DECOYS_MIN,
        "clear_negative_agreement_floor": config.CG1_CLEAR_NEGATIVE_AGREEMENT_MIN,
        "clear_positive_agreement_floor": config.CG1_CLEAR_POSITIVE_AGREEMENT_MIN,
    }

    result = {
        "direction": direction, "n_graded": n, "n_agree": agree, "n_disagree": disagree,
        "disagreement_rate": disagreement_rate, "disagreement_ceiling": config.DETECTOR_ADJUDICATION_DISAGREEMENT_MAX,
        "disagreement_within_ceiling": (disagreement_rate is not None and disagreement_rate <= config.DETECTOR_ADJUDICATION_DISAGREEMENT_MAX),
        "cg1": cg1, "graded_shard_sha256": graded_sha256,
        "note": "gates.yaml: disagreement > ceiling voids channel 2 for criterion use (channel 1 is unaffected); this script reports the raw numbers, lead adjudicates.",
    }
    common.write_json(CAL_DIR / f"abstention_calibration_score_{direction}.json", result)
    print(json.dumps(result, indent=2), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("build-correctness-pool", help="CPU: draw + commit the blinded correctness calibration shard")
    p1.add_argument("--n", type=int, default=config.CORRECTNESS_CALIBRATION_MIN_N)
    p1.set_defaults(func=build_correctness_pool)

    p2 = sub.add_parser("score-correctness", help="CPU: score an already-graded correctness shard")
    p2.add_argument("--graded-shard", required=True)
    p2.set_defaults(func=score_correctness)

    p3 = sub.add_parser("build-abstention-pool", help="CPU: draw + commit the blinded channel-2 abstention calibration shard")
    p3.add_argument("--direction", required=True, choices=config.DIRECTIONS)
    p3.add_argument("--n", type=int, default=150)
    p3.set_defaults(func=build_abstention_pool)

    p4 = sub.add_parser("score-abstention", help="CPU: score an already-graded abstention shard")
    p4.add_argument("--direction", required=True, choices=config.DIRECTIONS)
    p4.add_argument("--graded-shard", required=True)
    p4.set_defaults(func=score_abstention)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
