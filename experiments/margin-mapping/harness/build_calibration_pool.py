#!/usr/bin/env python3
"""Blinded calibration-slice pool builder for margin-mapping (M1), qwen35_4b
ONLY (mistral7b_v03 is VOID_INSTRUMENT_LOSS, out of scope).

cell.yaml `readout.calibration_slice` / gates.yaml `SC2_grading_integrity`:
"one shard-equivalent per family, ~700 rows sampled across rungs and roles
by a registered seed [48260715], clear-positive and clear-negative decoys
per the factorial recipe, CG1 floors unchanged."

CPU-only. No GPU, no model load (the clear_negative decoy source text is
REUSED, not freshly generated -- see module docstring below).

BUILD-TIME INTERPRETATIONS (not spec values; documented per this
experiment's own established convention, e.g. NOTEBOOK.md's preflight-row
interpretation):

  1. "~700 rows... stratified across rungs and roles" is read as: 700 is the
     target CORE sample size (decoys are additional, per the factorial
     recipe, not carved out of the 700). Stratification is proportional
     allocation across the 22 (rung x role) strata by the largest-remainder
     method, landing on exactly 700 core rows; sampling within each stratum
     is a seeded (48260715) shuffle-then-take, without replacement. The
     dose-0 baseline rung is included as one of the 11 ladder points (cell.
     yaml `ladder.dose_zero_rung` calls it a rung).
  2. DECOY_FRACTION = 0.15 (split evenly between clear_positive/
     clear_negative) and the salted-random opaque-id convention are ported
     LITERALLY from `gate-contribution-factorial/build_pool.py` (read in
     full before writing this) -- "per the factorial recipe" in cell.yaml.
  3. clear_positive decoys: M1's OWN refused_v2==True dosed observations,
     pooled across every NON-BASELINE rung (mirrors the factorial's "pooled
     across every non-baseline arm"), excluding any (row_key, rung) already
     drawn into the core sample.
  4. clear_negative decoys: M1 doses its ENTIRE known-correct held-out pool
     at every rung (cell.yaml has no gate/held-back subset), so -- exactly
     the "structural finding" `gate-contribution-factorial/heldback_
     decoys.py` documents for that experiment -- there is NO held-back
     subset of M1's OWN population to draw from. This module reuses the
     SAME external held-back source the factorial used for qwen35_4b:
     `qwen35-4b-midband-doubt-snap`'s FIT-split known_correct_answered rows
     (240 rows, disjoint from M1's held_out population by construction).
     UNLIKE the mistral hs16_c_hat incident, this source's GENERATION TEXT
     already exists on disk (`fit_rows_for_anchor.jsonl` carries a
     `baseline_text` field from that experiment's own unsteered baseline
     pass) -- no fresh GPU generation is needed. This is TEXT reuse for a
     decoy source, not a core experimental instrument, so byte-identical
     reuse is not required (contrast SC0's 6 named reused artifacts, which
     ARE required to be byte-identical); the text is regraded fresh here
     via M1's OWN `gen_lib.grade_row` (detector_v2) to determine
     committed-answer + non-refused qualification, same filter the
     factorial applied.

OUTPUTS:
  analysis/calibration/qwen35_4b_calibration_shard.jsonl      gitignored,
      BLINDED: [{opaque_id, text}] only, shuffled order. This is the ONLY
      file a grader ever sees.
  analysis/calibration/qwen35_4b_calibration_id_map.jsonl     gitignored,
      full unblinding map (row_key, role, rung, dose, detector verdict,
      decoy true label where applicable). NEVER sent to a grader, NEVER
      committed.
  analysis-committed/calibration_pool_manifest.json            COMMITTED:
      shard sha256, opaque-id list, counts, seed -- NO text, NO row_keys,
      NO true labels (SC2: "pool sha256 + opaque-id list committed before
      grading").
"""

from __future__ import annotations

import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import gen_lib  # noqa: E402
import derive_margins as dm  # noqa: E402

ANALYSIS = HERE.parent / "analysis"
RUNLOG_DIR = ANALYSIS / "runlog"
CAL_DIR = ANALYSIS / "calibration"
COMMITTED = HERE.parent / "analysis-committed"

FAMILY = "qwen35_4b"
SEED = config.CALIBRATION_SLICE_SEED  # 48260715, cell.yaml line 86
TARGET_CORE = config.CALIBRATION_SLICE_ROWS_PER_FAMILY  # 700, cell.yaml line 85

DECOY_FRACTION = 0.15  # ported literally from gate-contribution-factorial/build_pool.py
CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR = 25  # ported from gates_lib.py; gates.yaml SC2

DOUBT_SNAP_FIT_PATH = Path(
    "/home/profsynapse/code/ehr-worktrees/qwen35-midband/experiments/"
    "qwen35-4b-midband-doubt-snap/analysis/fit_rows_for_anchor.jsonl"
)


def _sha256_of_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def largest_remainder_allocation(strata_sizes: dict[Any, int], target_total: int) -> dict[Any, int]:
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


def build_core_sample() -> list[dict[str, Any]]:
    points = dm._ladder_points()
    population = dm.load_population_row_keys()
    role_row_keys: dict[str, list[str]] = {"confab": [], "known_correct_answered": []}
    for rk, role in population.items():
        role_row_keys[role].append(rk)
    for role in role_row_keys:
        role_row_keys[role].sort()

    strata_sizes: dict[tuple[str, str], int] = {}
    for _, tag, _ in points:
        for role, rks in role_row_keys.items():
            strata_sizes[(tag, role)] = len(rks)

    alloc = largest_remainder_allocation(strata_sizes, TARGET_CORE)

    core: list[dict[str, Any]] = []
    for m, tag, filename in points:
        dose_abs = m * config.REFERENCE_DOSE_ABS[FAMILY] if m > 0 else 0.0
        table = dm.load_rung_records(filename)
        for role, rks in role_row_keys.items():
            n = alloc[(tag, role)]
            rng = random.Random(f"{SEED}:core:{tag}:{role}")
            shuffled = rks[:]
            rng.shuffle(shuffled)
            for rk in shuffled[:n]:
                rec = table[rk]
                core.append({
                    "row_key": rk, "role": role, "rung_tag": tag, "dose_abs": dose_abs,
                    "text": rec["answer_text"], "refused_v2": bool(rec["refused_v2"]),
                    "well_formed": bool(rec["well_formed"]),
                })
    assert len(core) == TARGET_CORE, f"core sample size {len(core)} != target {TARGET_CORE}"
    return core


def build_clear_positive_decoys(core: list[dict[str, Any]], n_each: int) -> list[dict[str, Any]]:
    points = dm._ladder_points()
    population = dm.load_population_row_keys()
    core_keys = {(c["row_key"], c["rung_tag"]) for c in core}
    candidates: list[dict[str, Any]] = []
    for m, tag, filename in points:
        if m == 0.0:
            continue  # exclude baseline rung, mirrors factorial's arm!="baseline" filter
        dose_abs = m * config.REFERENCE_DOSE_ABS[FAMILY]
        table = dm.load_rung_records(filename)
        for rk, rec in table.items():
            if (rk, tag) in core_keys:
                continue
            if not bool(rec["refused_v2"]):
                continue
            candidates.append({
                "row_key": rk, "role": population[rk], "rung_tag": tag, "dose_abs": dose_abs,
                "text": rec["answer_text"], "refused_v2": True, "well_formed": bool(rec["well_formed"]),
            })
    rng = random.Random(f"{SEED}:decoy_positive")
    rng.shuffle(candidates)
    chosen = candidates[:n_each]
    for c in chosen:
        c["decoy_type"] = "clear_positive"
        c["decoy_true_label"] = "abstained"
    return chosen


def build_clear_negative_decoys(n_each: int) -> list[dict[str, Any]]:
    if not DOUBT_SNAP_FIT_PATH.exists():
        raise SystemExit(f"build_calibration_pool FAIL: missing decoy source {DOUBT_SNAP_FIT_PATH}")
    fit_rows = [
        r for r in common.load_jsonl(DOUBT_SNAP_FIT_PATH)
        if r.get("role") == "known_correct_answered" and r.get("split") == "fit"
    ]
    if len(fit_rows) != 240:
        print(f"WARNING: expected 240 doubt-snap FIT known rows, found {len(fit_rows)}", file=sys.stderr)

    m1_population = set(dm.load_population_row_keys().keys())
    overlap = {r["row_key"] for r in fit_rows} & m1_population
    if overlap:
        raise SystemExit(
            f"build_calibration_pool FAIL: {len(overlap)} decoy source row_keys "
            f"overlap M1's own scored population (disjointness violated): {sorted(overlap)[:5]}"
        )

    qualifying: list[dict[str, Any]] = []
    for r in fit_rows:
        grade = gen_lib.grade_row(r["baseline_text"], bool(r["baseline_terminated_naturally"]), r.get("aliases"))
        if grade["well_formed_correct_v2"] and not grade["refused_v2"]:
            qualifying.append({
                "row_key": r["row_key"], "role": "known_correct_answered_heldback",
                "rung_tag": "heldback_fit_baseline", "dose_abs": 0.0,
                "text": r["baseline_text"], "refused_v2": False, "well_formed": True,
            })

    rng = random.Random(f"{SEED}:decoy_negative")
    rng.shuffle(qualifying)
    chosen = qualifying[:n_each]
    for c in chosen:
        c["decoy_type"] = "clear_negative"
        c["decoy_true_label"] = "answered"
    return chosen, len(qualifying)


def main() -> int:
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    core = build_core_sample()

    n_each = max(1, round(len(core) * DECOY_FRACTION / 2))
    decoys_pos = build_clear_positive_decoys(core, n_each)
    decoys_neg, n_qualifying_neg = build_clear_negative_decoys(n_each)

    if len(decoys_pos) < CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR:
        raise SystemExit(
            f"build_calibration_pool FAIL: only {len(decoys_pos)} clear_positive "
            f"decoys available, below the gates.yaml SC2 floor of "
            f"{CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR}"
        )

    all_items = core + decoys_pos + decoys_neg
    order_rng = random.Random(SEED)
    order_rng.shuffle(all_items)

    seen_ids: set[str] = set()
    id_map: list[dict[str, Any]] = []
    shard: list[dict[str, str]] = []
    for item in all_items:
        while True:
            opaque_id = secrets.token_hex(8)
            if opaque_id not in seen_ids:
                seen_ids.add(opaque_id)
                break
        is_decoy = "decoy_type" in item
        id_map.append({
            "opaque_id": opaque_id,
            "is_decoy": is_decoy,
            "decoy_type": item.get("decoy_type"),
            "decoy_true_label": item.get("decoy_true_label"),
            "row_key": item["row_key"],
            "role": item["role"],
            "rung_tag": item["rung_tag"],
            "dose_abs": item["dose_abs"],
            "refused_v2_detector": item["refused_v2"],
            "well_formed": item["well_formed"],
        })
        shard.append({"opaque_id": opaque_id, "text": item["text"]})

    shard_path = CAL_DIR / "qwen35_4b_calibration_shard.jsonl"
    with shard_path.open("w", encoding="utf-8") as fh:
        for row in shard:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    id_map_path = CAL_DIR / "qwen35_4b_calibration_id_map.jsonl"
    with id_map_path.open("w", encoding="utf-8") as fh:
        for row in id_map:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    shard_sha256 = _sha256_of_file(shard_path)
    manifest = {
        "family": FAMILY,
        "seed": SEED,
        "target_core": TARGET_CORE,
        "decoy_fraction": DECOY_FRACTION,
        "n_core": len(core),
        "n_decoy_clear_positive": len(decoys_pos),
        "n_decoy_clear_negative": len(decoys_neg),
        "n_qualifying_clear_negative_candidates": n_qualifying_neg,
        "n_total_shard_rows": len(shard),
        "clear_positive_decoys_per_shard_floor": CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR,
        "clear_positive_floor_met": len(decoys_pos) >= CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR,
        "shard_sha256": shard_sha256,
        "shard_path": str(shard_path),
        "opaque_id_list": sorted(seen_ids),
        "committed_before_grading": True,
    }
    manifest_path = COMMITTED / "calibration_pool_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps({k: v for k, v in manifest.items() if k != "opaque_id_list"}, indent=2, sort_keys=True))
    print(f"opaque_id_list: {len(manifest['opaque_id_list'])} ids (committed, not printed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
