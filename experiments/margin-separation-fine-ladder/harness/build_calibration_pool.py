#!/usr/bin/env python3
"""Blinded calibration-slice pool builder for margin-separation-fine-ladder
(M1b), qwen35_4b ONLY.

cell.yaml `readout.calibration_slice` / gates.yaml `SC2_grading_integrity`:
100 rows sampled from the 212 new generations, stratified 25 per new rung
(seed 48260720), clear-positive and clear-negative decoys per the M1/
factorial recipe, CG1 floors unchanged, hash-commit-before-unblind.

NOT RUN in this phase (self-evident: this reads the 4 new-rung runlogs,
which do not exist until `generate_refined.py` has completed). `main()`
refuses immediately if they are missing, mirroring `analysis.py`'s guard.

Adapted (logic ported) from `margin-mapping/build_calibration_pool.py`
(read in full before writing this): M1 stratified ~700 core rows across 11
ladder points (10 rungs + baseline) x 2 roles via largest-remainder
allocation; M1b strata are the 4 NEW rungs x 53 refined rows only (all
confab role -- there is no known-row generation in M1b), with a plain 25
rows exact per rung (4 x 25 = 100, cell.yaml line 131) rather than
largest-remainder allocation, since 25/53 divides the population evenly
without a remainder-distribution question.

clear_positive decoys: pooled across the 4 new rungs' refused_v2==True
observations (M1's own recipe, "pooled across every non-baseline rung"),
excluding rows already drawn into the core sample.

clear_negative decoys: M1b has no held-back subset of its own tiny 53-row
population (all 53 rows are the core scored population). This reuses the
SAME external held-back source M1 itself used for qwen35_4b -- M1's own
convention, ported unchanged (see M1's build_calibration_pool.py docstring
for the qwen35-4b-midband-doubt-snap FIT-split rationale).
"""

from __future__ import annotations

import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import gen_lib  # noqa: E402
import dose_ladder  # noqa: E402

ANALYSIS = EXPERIMENT_DIR / "analysis"
RUNLOG_DIR = ANALYSIS / "runlog"
CAL_DIR = ANALYSIS / "calibration"
COMMITTED = EXPERIMENT_DIR / "analysis-committed"
STAGED = ANALYSIS / "staged_inputs"

FAMILY = "qwen35_4b"
SEED = config.CALIBRATION_SLICE_SEED          # 48260720
TARGET_CORE = config.CALIBRATION_SLICE_ROWS_TOTAL   # 100
PER_RUNG = config.CALIBRATION_SLICE_PER_RUNG        # 25

DECOY_FRACTION = 0.15  # ported literally from M1/gate-contribution-factorial's build_pool.py
CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR = config.CALIBRATION_CG1_MIN_CLEAR_POSITIVE_DECOYS  # 25

# Ported unchanged from M1's own build_calibration_pool.py -- the SAME
# external held-back known-correct source M1 used for qwen35_4b clear-
# negative decoys (disjoint from M1's/M1b's own scored population by
# construction; text already exists on disk, no fresh GPU generation).
DOUBT_SNAP_FIT_PATH = Path(
    "/home/profsynapse/code/ehr-worktrees/qwen35-midband/experiments/"
    "qwen35-4b-midband-doubt-snap/analysis/fit_rows_for_anchor.jsonl"
)


def _new_rung_runlog_path(multiplier: float) -> Path:
    tag = dose_ladder.rung_tag(multiplier)
    return RUNLOG_DIR / f"{FAMILY}__refined_rung_{tag}.jsonl"


def _require_new_generations_exist() -> None:
    missing = [p for m in config.NEW_RUNGS if not (p := _new_rung_runlog_path(m)).is_file()]
    if missing:
        raise SystemExit(
            f"[build-calibration-pool] REFUSING: {len(missing)} new-rung runlog(s) "
            f"missing: {missing}. Not run in the harness-build phase."
        )


def _sha256_of_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def refined_row_keys() -> list[str]:
    payload = common.load_json(COMMITTED / "refined_subset_ids_qwen35_4b.json")
    return sorted(payload["row_keys"])


def build_core_sample() -> list[dict[str, Any]]:
    row_keys = refined_row_keys()
    if len(row_keys) != config.REFINED_SUBSET_N:
        raise SystemExit(f"[build-calibration-pool] FAIL: refined subset has {len(row_keys)} rows, expected {config.REFINED_SUBSET_N}.")

    core: list[dict[str, Any]] = []
    for m in config.NEW_RUNGS:
        tag = dose_ladder.rung_tag(m)
        dose_abs = dose_ladder.rung_dose_abs(FAMILY, m)
        table = {r["row_key"]: r for r in common.load_jsonl(_new_rung_runlog_path(m))}
        missing = [rk for rk in row_keys if rk not in table]
        if missing:
            raise SystemExit(f"[build-calibration-pool] FAIL: rung {m}x missing {len(missing)} refined rows: {missing[:5]}")
        rng = random.Random(f"{SEED}:core:{tag}")
        shuffled = row_keys[:]
        rng.shuffle(shuffled)
        for rk in shuffled[:PER_RUNG]:
            rec = table[rk]
            core.append({
                "row_key": rk, "role": "confab", "rung_tag": tag, "dose_abs": dose_abs,
                "text": rec["answer_text"], "refused_v2": bool(rec["refused_v2"]),
                "well_formed": bool(rec["well_formed"]),
            })
    if len(core) != TARGET_CORE:
        raise SystemExit(f"[build-calibration-pool] FAIL: core sample size {len(core)} != target {TARGET_CORE}.")
    return core


def build_clear_positive_decoys(core: list[dict[str, Any]], n_each: int) -> list[dict[str, Any]]:
    row_keys = refined_row_keys()
    core_keys = {(c["row_key"], c["rung_tag"]) for c in core}
    candidates: list[dict[str, Any]] = []
    for m in config.NEW_RUNGS:
        tag = dose_ladder.rung_tag(m)
        dose_abs = dose_ladder.rung_dose_abs(FAMILY, m)
        table = {r["row_key"]: r for r in common.load_jsonl(_new_rung_runlog_path(m))}
        for rk in row_keys:
            rec = table.get(rk)
            if rec is None or (rk, tag) in core_keys:
                continue
            if not bool(rec["refused_v2"]):
                continue
            candidates.append({
                "row_key": rk, "role": "confab", "rung_tag": tag, "dose_abs": dose_abs,
                "text": rec["answer_text"], "refused_v2": True, "well_formed": bool(rec["well_formed"]),
            })
    rng = random.Random(f"{SEED}:decoy_positive")
    rng.shuffle(candidates)
    chosen = candidates[:n_each]
    for c in chosen:
        c["decoy_type"] = "clear_positive"
        c["decoy_true_label"] = "abstained"
    return chosen


def build_clear_negative_decoys(n_each: int) -> tuple[list[dict[str, Any]], int]:
    if not DOUBT_SNAP_FIT_PATH.exists():
        raise SystemExit(f"[build-calibration-pool] FAIL: missing decoy source {DOUBT_SNAP_FIT_PATH}")
    fit_rows = [
        r for r in common.load_jsonl(DOUBT_SNAP_FIT_PATH)
        if r.get("role") == "known_correct_answered" and r.get("split") == "fit"
    ]
    if len(fit_rows) != 240:
        print(f"WARNING: expected 240 doubt-snap FIT known rows, found {len(fit_rows)}", file=sys.stderr)

    m1b_population = set(refined_row_keys())
    overlap = {r["row_key"] for r in fit_rows} & m1b_population
    if overlap:
        raise SystemExit(
            f"[build-calibration-pool] FAIL: {len(overlap)} decoy source row_keys "
            f"overlap M1b's own refined population (disjointness violated): {sorted(overlap)[:5]}"
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
    _require_new_generations_exist()

    CAL_DIR.mkdir(parents=True, exist_ok=True)
    core = build_core_sample()

    n_each = max(1, round(len(core) * DECOY_FRACTION / 2))
    decoys_pos = build_clear_positive_decoys(core, n_each)
    decoys_neg, n_qualifying_neg = build_clear_negative_decoys(n_each)

    if len(decoys_pos) < CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR:
        raise SystemExit(
            f"[build-calibration-pool] FAIL: only {len(decoys_pos)} clear_positive "
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
        "per_rung": PER_RUNG,
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
