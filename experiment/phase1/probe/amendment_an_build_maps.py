#!/usr/bin/env python3
"""Amendment AN: build the selection manifest + per-arm gain maps (CPU).

SPEC: experiment/protocol/AMENDMENT-AN-selected-setpoint-regulator.md sections
3.3 and 4. Selection side of the propensity-selected, caution-actuated
regulator. Reads the FROZEN AL A0 per-row exhaust (prop_z, caution_z, baseline
grades) and emits one manifest that the AN couple-steer harness consumes.

Arms (section 3.3):
  primary        rows with prop_z >= 1.00 flagged, each written g = +2 (clipped)
  control        a count-matched uniform random draw (same COUNT as primary,
                 seeded) from all 1,662 rows, each written g = +2
  primary_gain_p1  flagged CONFABS only, g = +1 (descriptive dose ladder)
  primary_gain_p3  flagged CONFABS only, g = +3 (descriptive dose ladder)
  bidirectional  the 114 answerable-refused rows, each written g = -2 (setpoint
                 DOWN toward answering; secondary exploratory arm, section 5)

The couple mechanism (Amendment AC) is h' = h - (h.c_hat)c_hat + g*sigma*c_hat.
A gain map is a dict row_key -> gain; rows ABSENT from a map are UNTOUCHED
(the AN harness treats an absent row as no-op, matching AL's pushed/unpushed
split rather than AC's hard-error-on-missing runner). Every arm also records
its explicit flagged row_key list so the grader's kill/collateral universe is
unambiguous.

Provenance keys carried on the manifest: source exhaust path + sha256,
direction file + sha256, sigma, layer/block, threshold, permutation seed, and
the full flag census per arm.

Pure read (CPU): never touches the extraction or the GPU. Deterministic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
AN_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_an_prep"
DEFAULT_EXHAUST = AL_PREP / "amendment_al_run/per_row_exhaust.jsonl"
DEFAULT_DIRECTION = AN_PREP / "caution_perp_direction_L35_ai_true.json"
DEFAULT_OUT = AN_PREP / "amendment_an_run"

PRIMARY_THRESHOLD = 1.00
PRIMARY_GAIN = 2.0
LADDER_GAINS = {"primary_gain_p1": 1.0, "primary_gain_p3": 3.0}
BIDIRECTIONAL_GAIN = -2.0
GAIN_CLIP = 3.0  # ladder reaches +3; primary +2 stays within
PERMUTATION_SEED = 20260705  # doc names none; seeded here and recorded


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(p: Path):
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def grade_of(rec: dict) -> str:
    """Reconstruct the frozen baseline grade from an exhaust row's baseline
    block (mirrors amendment_al_grade_and_gates baseline populations)."""
    b = rec["baseline"]
    gc = rec["gold_class"]
    if b["confab"]:
        return "confab"
    if gc == "answerable" and b["answered"] and b["correct"] is True:
        return "correct"
    if gc == "answerable" and b["answered"] and b["correct"] is False:
        return "wrong"
    if gc == "answerable" and b["refused"]:
        return "answerable_refused"
    if b["refused"]:
        return "unanswerable_refused"
    return "other"


def census(keys, grade_by_key) -> dict:
    c = Counter(grade_by_key[k] for k in keys)
    return {"n": len(keys), **{g: c.get(g, 0) for g in
            ("confab", "correct", "wrong", "answerable_refused",
             "unanswerable_refused", "other") if c.get(g, 0)}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exhaust", type=Path, default=DEFAULT_EXHAUST)
    ap.add_argument("--direction", type=Path, default=DEFAULT_DIRECTION)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--threshold", type=float, default=PRIMARY_THRESHOLD)
    ap.add_argument("--permutation-seed", type=int, default=PERMUTATION_SEED)
    args = ap.parse_args(argv)

    rows = load_jsonl(args.exhaust)
    row_order = [r["row_key"] for r in rows]
    if len(set(row_order)) != len(row_order):
        raise ValueError("duplicate row keys in exhaust")
    grade_by_key = {r["row_key"]: grade_of(r) for r in rows}
    prop_z_by_key = {r["row_key"]: float(r["prop_z"]) for r in rows}

    direction = json.loads(args.direction.read_text())
    theta = np.array(direction["theta"], dtype=np.float64)
    sigma = float(direction["sigma"])
    layer = int(direction["layer"])
    block = int(direction["block"])
    if sigma <= 0:
        raise ValueError(f"non-positive sigma {sigma}")

    # ---- primary flag ----
    primary_keys = [k for k in row_order if prop_z_by_key[k] >= args.threshold]
    primary_confab_keys = [k for k in primary_keys
                           if grade_by_key[k] == "confab"]

    # ---- control: count-matched uniform draw, seeded, one draw ----
    rng = np.random.default_rng(args.permutation_seed)
    control_idx = rng.choice(len(row_order), size=len(primary_keys),
                             replace=False)
    control_keys = [row_order[i] for i in sorted(control_idx.tolist())]

    # ---- bidirectional: the answerable-refused cell ----
    bidirectional_keys = [k for k in row_order
                          if grade_by_key[k] == "answerable_refused"]

    arms = {
        "primary": {
            "law": f"prop_z >= {args.threshold} -> g = +{PRIMARY_GAIN}",
            "gain": PRIMARY_GAIN,
            "flagged_keys": primary_keys,
            "gains": {k: PRIMARY_GAIN for k in primary_keys},
            "census": census(primary_keys, grade_by_key),
        },
        "control": {
            "law": (f"uniform draw of {len(primary_keys)} rows (seed "
                    f"{args.permutation_seed}) -> g = +{PRIMARY_GAIN}"),
            "gain": PRIMARY_GAIN,
            "flagged_keys": control_keys,
            "gains": {k: PRIMARY_GAIN for k in control_keys},
            "census": census(control_keys, grade_by_key),
        },
        "bidirectional": {
            "law": (f"answerable_refused cell -> g = {BIDIRECTIONAL_GAIN} "
                    "(setpoint DOWN; secondary exploratory, gate-free)"),
            "gain": BIDIRECTIONAL_GAIN,
            "flagged_keys": bidirectional_keys,
            "gains": {k: BIDIRECTIONAL_GAIN for k in bidirectional_keys},
            "census": census(bidirectional_keys, grade_by_key),
        },
    }
    for tag, g in LADDER_GAINS.items():
        arms[tag] = {
            "law": f"flagged confabs only (prop_z >= {args.threshold}) -> g = {g:+g}",
            "gain": g,
            "flagged_keys": list(primary_confab_keys),
            "gains": {k: g for k in primary_confab_keys},
            "census": census(primary_confab_keys, grade_by_key),
        }

    manifest = {
        "schema_version": "amendment-an-selection-manifest/v1",
        "threshold": args.threshold,
        "primary_gain": PRIMARY_GAIN,
        "ladder_gains": LADDER_GAINS,
        "bidirectional_gain": BIDIRECTIONAL_GAIN,
        "gain_clip": GAIN_CLIP,
        "permutation_seed": args.permutation_seed,
        "layer": layer,
        "block": block,
        "sigma": sigma,
        "provenance": {
            "source_exhaust": str(args.exhaust),
            "source_exhaust_sha256": sha256_of(args.exhaust),
            "direction_file": str(args.direction),
            "direction_sha256": sha256_of(args.direction),
            "direction_theta_norm": float(np.linalg.norm(theta)),
            "direction_cos_to_grpo_v2": direction.get("cos_to_grpo_v2_caution_perp"),
            "direction_perp_fraction": direction.get("perp_fraction_of_caution"),
        },
        "baseline_totals": census(row_order, grade_by_key),
        "arms": arms,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / "an_selection_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"[an-maps] threshold prop_z >= {args.threshold}", file=sys.stderr)
    for tag, a in arms.items():
        print(f"[an-maps] {tag}: {a['census']}", file=sys.stderr)
    print(f"[an-maps] control seed {args.permutation_seed} "
          f"({len(control_keys)} rows)", file=sys.stderr)
    print(f"[an-maps] direction L{layer} block{block} sigma={sigma:.4f} "
          f"cos_to_grpo_v2={manifest['provenance']['direction_cos_to_grpo_v2']:.4f}",
          file=sys.stderr)
    print(f"[an-maps] wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
