#!/usr/bin/env python3
"""Build the NORM-MATCHED random-head control artifact for the Step A.4 sweep.

The plain random-head control (`..._randomctl`) steers 11 random heads at their
own per-head sigma. Because random heads have a weaker failure axis, their sigma
(and thus the ITI delta magnitude ``alpha*sigma``) is naturally smaller than the
localized heads' -- so a null result there is confounded by a smaller push.

This script removes that confound: it keeps the random heads' POSITIONS and their
own mass-mean ``theta`` directions, but grafts the localized heads' sigma
MAGNITUDES onto them (multiset-identical, paired by rank: largest localized sigma
-> largest-sigma random head). The resulting total perturbation energy matches the
localized run exactly, so any behavioral difference isolates head
position/direction, not magnitude.

GPU-free. Reads two existing steering-direction artifacts, writes a third.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_norm_matched(localized: dict, random_ctl: dict) -> dict:
    loc_sigmas = sorted((d["sigma"] for d in localized["directions"]), reverse=True)
    rnd_dirs = random_ctl["directions"]
    if len(loc_sigmas) != len(rnd_dirs):
        raise ValueError(
            f"direction count mismatch: localized {len(loc_sigmas)} != random {len(rnd_dirs)}"
        )
    # Rank random heads by their own sigma desc, pair largest-with-largest so the
    # grafted multiset is deterministic and the magnitude profile matches exactly.
    order = sorted(range(len(rnd_dirs)), key=lambda i: -rnd_dirs[i]["sigma"])
    for rank, idx in enumerate(order):
        d = rnd_dirs[idx]
        d["sigma_original_random"] = d["sigma"]
        d["sigma"] = loc_sigmas[rank]
        d["sigma_source"] = "norm_matched_to_localized_multiset"
    out = dict(random_ctl)
    out["directions"] = rnd_dirs
    out["notice"] = "HEAD_STEERING_DIRECTIONS_RANDOM_HEAD_NORM_MATCHED_CONTROL"
    out["norm_match"] = {
        "localized_sigma_multiset_desc": loc_sigmas,
        "pairing": "rank (largest localized sigma -> largest-sigma random head)",
    }
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--localized", required=True, type=Path)
    parser.add_argument("--random", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    localized = json.loads(args.localized.read_text(encoding="utf-8"))
    random_ctl = json.loads(args.random.read_text(encoding="utf-8"))
    out = build_norm_matched(localized, random_ctl)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    sigmas = sorted(d["sigma"] for d in out["directions"])
    loc = sorted(d["sigma"] for d in localized["directions"])
    matched = [round(a, 6) for a in sigmas] == [round(b, 6) for b in loc]
    print(json.dumps({"ok": True, "out": str(args.out), "sigma_multiset_matches_localized": matched}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
