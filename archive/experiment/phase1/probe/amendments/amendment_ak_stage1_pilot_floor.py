#!/usr/bin/env python3
"""Amendment AK Stage 1 - AK-G2 pilot-floor lock (CPU, deterministic).

Pre-registered by AMENDMENT-AK-commitment-point.md:
  - §3.1: "the first ~50 rows of the sweep are the AK-G2 pilot; they lock the
    G2 floor via the §4 formula and are then excluded from the G2 test set."
  - §4 (AK-G2 floor formula, pre-stated): "floor = 3 x SE of the slope contrast
    measured on the ~50-row pilot, computed and committed to the run record
    before the full-run G2 readout."

STRICT ORDER: this script must run and its output must be committed to git
BEFORE amendment_ak_stage1_analyze.py touches the non-pilot rows. Locking the
floor is a computation, not a judgment call (doc §Status), so this script takes
no thresholds as input; it only measures the pilot slope-contrast SE and writes
floor = 3 x SE.

Pilot arm: the doc gates AK-G2 on the doubt-trajectory discriminability. The
pilot floor is a property of the STATISTIC's noise on the pilot rows; per §3.1
the sweep pilot is "the first ~50 rows of the sweep" and the sweep runs both
checkpoints. We lock the floor on the grpo-v2 arm (the AK-G1 gate surface and
the deployed checkpoint) and record the raw-base pilot SE alongside as
provenance. The committed number that gates AK-G2 is the grpo-v2 floor.

Output: experiments/commitment-point/artifacts/stage1/ak_stage1_pilot_floor.json
(tracked), carrying the pilot row_keys, the trunk layer, the pilot slope
contrast + SE, floor = 3*SE, and a UTC timestamp.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import amendment_ak_stage1_lib as ak

from path_compat import repo_root  # noqa: E402

WORKTREE = repo_root()
# Frozen AH answerability probes live in the canonical checkout's untracked
# analysis tree (gitignored, shared across amendments); fall back to the
# worktree copy if a run ever materializes them locally.
_CANON = Path("/home/profsynapse/code/Epistemic-Humility-Research")
_PROBES_REL = "experiment/phase1/probe/analysis/ah_stage0/probes"
PROBES_DIR = (_CANON / _PROBES_REL if (_CANON / _PROBES_REL).is_dir()
              else WORKTREE / _PROBES_REL)
DEFAULT_TRUNK_LAYER = "L24"   # arm-B doubt/commitment peak; frozen AH probe exists
PILOT_N = 50                  # "first ~50 rows of the sweep" (§3.1)
COMMIT_PATH = (WORKTREE / "experiments/commitment-point/artifacts/stage1/"
               "ak_stage1_pilot_floor.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grpo-dir", required=True,
                    help="downloaded grpo-v2 arm dir (contains data/rows.jsonl)")
    ap.add_argument("--raw-dir", required=True,
                    help="downloaded raw-base arm dir (provenance SE only)")
    ap.add_argument("--trunk-layer", default=DEFAULT_TRUNK_LAYER)
    ap.add_argument("--pilot-n", type=int, default=PILOT_N)
    ap.add_argument("--out", default=str(COMMIT_PATH))
    args = ap.parse_args(argv)

    grpo_dir = Path(args.grpo_dir).resolve()
    raw_dir = Path(args.raw_dir).resolve()
    trunk = ak.DoubtTrunk.load(PROBES_DIR, args.trunk_layer)

    grpo_rows = ak.load_rows(grpo_dir)
    raw_rows = ak.load_rows(raw_dir)
    # rows.jsonl preserves pool order (verified); pilot == first N.
    pilot = grpo_rows[: args.pilot_n]
    pilot_keys = [r["row_key"] for r in pilot]

    sc = ak.slope_contrast(grpo_dir, pilot, trunk)
    # provenance: same pilot rows on the raw-base arm
    raw_pilot = [r for r in raw_rows if r["row_key"] in set(pilot_keys)]
    sc_raw = ak.slope_contrast(raw_dir, raw_pilot, trunk)

    floor = 3.0 * sc.se

    payload = {
        "amendment": "AK",
        "stage": "stage1_ak_g2_pilot_floor_lock",
        "formula": "floor = 3 * SE(slope_contrast) on the ~50-row pilot (doc §4)",
        "statistic": ("confab-vs-refuse contrast of per-row least-squares slope "
                      "of frozen-doubt-trunk projection vs normalized "
                      "answer-window position [0,1]"),
        "trunk": {
            "kind": "frozen AH answerability probe (class1=known); "
                    "projection = -(scaled decision), higher==more doubt",
            "layer": args.trunk_layer,
            "probe_file": f"analysis/ah_stage0/probes/probe_{args.trunk_layer}.joblib",
        },
        "pilot_n_requested": args.pilot_n,
        "pilot_row_keys": pilot_keys,
        "grpo_v2_pilot": {
            "config_sha": pilot[0]["config_sha"],
            "n_confab": sc.n_confab, "n_refuse": sc.n_refuse,
            "mean_slope_confab": sc.mean_confab,
            "mean_slope_refuse": sc.mean_refuse,
            "slope_contrast": sc.contrast,
            "slope_contrast_se": sc.se,
        },
        "raw_base_pilot_provenance": {
            "config_sha": raw_pilot[0]["config_sha"] if raw_pilot else None,
            "n_confab": sc_raw.n_confab, "n_refuse": sc_raw.n_refuse,
            "slope_contrast": sc_raw.contrast,
            "slope_contrast_se": sc_raw.se,
        },
        "COMMITTED_FLOOR": floor,
        "floor_arm": "grpo-v2",
        "note": ("Pilot rows are EXCLUDED from the AK-G2 full-run test set. "
                 "AK-G2 PASS requires full-run |slope_contrast| >= COMMITTED_FLOOR "
                 "AND permutation p < 0.01 (doc §4)."),
        "locked_utc": dt.datetime.now(dt.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items()
                      if k != "pilot_row_keys"}, indent=2))
    print(f"[ak/pilot] LOCKED floor={floor:.6g} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
