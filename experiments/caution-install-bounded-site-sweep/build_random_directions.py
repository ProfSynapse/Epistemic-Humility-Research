#!/usr/bin/env python3
"""Stage 3 support (CPU): K >= 3 fresh random-direction draws per site under
SC1 draw hygiene (cell.yaml `placebo.draw_hygiene_sc1`, gates.yaml G3
`draw_hygiene_sc1`), for the `random_direction` arm's G3 placebo and the
mandatory read control.

Draw hygiene (both max_abs_cos checks against the site's own c_hat and u_d,
magnitude match by exact readback, sigma != gain assertion, void-and-redraw
ledger) is implemented literally as pre-registered -- this script is math and
bookkeeping only, no threshold is loosened to make a draw pass.

A candidate draw is a uniform-random unit vector in R^hidden_dim (fixed seed
sequence `random_state:site:draw_index`, redrawing under the same sequence
position on a void so the ledger is deterministic and replayable). It is
accepted iff |cos(draw, c_hat)| <= 0.015 AND |cos(draw, u_d)| <= 0.015; a
rejected draw is appended to the void ledger and a fresh draw is taken at the
next index in the same seeded stream.

Output: `directions/<substrate>/<site>/random_direction_draw_<k>_<site>.json`
(mechinterp-direction/v1, sigma copied from that site's c_hat.sigma per
draw_hygiene_sc1's magnitude-match rule -- the ACTUAL commanded magnitude
match happens at write time via readback, per gates.yaml; this sigma is the
scaling convention the writer applies before readback verification) and
`analysis-committed/<substrate>/random_direction_ledger.json` (accepted +
voided draws, cosines, no vectors).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sweep_lib import (  # noqa: E402
    COMMITTED,
    DIRECTIONS_DIR,
    direction_record,
    load_cell,
    load_gates,
    sites_for,
    write_json,
)

def unit(v: np.ndarray) -> np.ndarray:
    return v / float(np.linalg.norm(v))


def load_vector(path: Path) -> np.ndarray:
    return np.asarray(json.loads(path.read_text())["vector"], dtype=np.float64)


def draw_one(rng: np.random.Generator, hidden_dim: int) -> np.ndarray:
    return unit(rng.standard_normal(hidden_dim))


def run(args: argparse.Namespace) -> int:
    cell = load_cell()
    gates = load_gates()
    k_min = int(cell["placebo"]["k_draws_min"])
    random_state = int(cell["directions"]["random_state"])
    substrate = args.substrate
    sites = sites_for(substrate, cell)

    # F21 fix: previously a hardcoded MAX_ABS_COS = 0.015 constant, ignoring
    # `gates` (loaded but unused). gates.yaml g3_direction_specificity's
    # draw_hygiene_sc1 registers two separate thresholds
    # (max_abs_cos_vs_c_hat, max_abs_cos_vs_u_d); both are read here rather
    # than collapsed into one shared constant, in case they are ever set to
    # different values.
    g3_gate = next(g for g in gates["gates"] if g["name"] == "g3_direction_specificity")
    hygiene = g3_gate["draw_hygiene_sc1"]
    max_abs_cos_c_hat = float(hygiene["max_abs_cos_vs_c_hat"])
    max_abs_cos_u_d = float(hygiene["max_abs_cos_vs_u_d"])

    ledger = {"substrate": substrate, "random_state": random_state,
              "k_draws_min": k_min,
              "max_abs_cos_vs_c_hat": max_abs_cos_c_hat, "max_abs_cos_vs_u_d": max_abs_cos_u_d,
              "sites": {}}

    for site in sites:
        site_dir = DIRECTIONS_DIR / substrate / site.name
        c_hat_path = site_dir / f"c_hat_{site.name}.json"
        u_d_path = site_dir / f"u_d_{site.name}.json"
        if not (c_hat_path.exists() and u_d_path.exists()):
            print(f"[random-dir:{substrate}] {site.name}: missing c_hat/u_d "
                  f"(run build_directions.py first); skipping.", file=sys.stderr)
            continue
        c_hat_rec = json.loads(c_hat_path.read_text())
        c_hat = np.asarray(c_hat_rec["vector"], dtype=np.float64)
        u_d = load_vector(u_d_path)
        sigma = float(c_hat_rec.get("sigma", 1.0))
        hidden_dim = int(c_hat_rec["hidden_dim"])

        seed_seq = np.random.SeedSequence([random_state, site.hs_index])
        rng = np.random.default_rng(seed_seq)

        accepted, voided = [], []
        draw_idx = 0
        while len(accepted) < k_min:
            v = draw_one(rng, hidden_dim)
            cos_c = float(np.dot(v, c_hat))
            cos_d = float(np.dot(v, u_d))
            ok = abs(cos_c) <= max_abs_cos_c_hat and abs(cos_d) <= max_abs_cos_u_d
            entry = {"draw_index": draw_idx, "cos_vs_c_hat": cos_c, "cos_vs_u_d": cos_d, "accepted": ok}
            if ok:
                accepted.append((draw_idx, v))
                (site_dir / f"random_direction_draw_{len(accepted)}_{site.name}.json").write_text(
                    json.dumps(direction_record(
                        v, site.decoder_block, hidden_dim, sigma, "random_direction_draw",
                        {"substrate": substrate, "hs_index": site.hs_index, "draw_index": draw_idx,
                         "cos_vs_c_hat": cos_c, "cos_vs_u_d": cos_d,
                         "sigma_gain_assertion": "sigma copied from c_hat; NOT the write gain "
                                                  "(see gates.yaml G3 sigma_gain_assertion) -- "
                                                  "the write-time strength/gain is computed by "
                                                  "the writer against the arm's readback tolerance, "
                                                  "never by reusing this sigma as a gain value"}),
                        indent=2))
            else:
                voided.append(entry)
            draw_idx += 1

        ledger["sites"][site.name] = {
            "hidden_dim": hidden_dim, "n_accepted": len(accepted), "n_voided": len(voided),
            "accepted_draw_indices": [i for i, _ in accepted], "void_ledger": voided,
        }
        print(f"[random-dir:{substrate}] {site.name}: {len(accepted)} accepted, "
              f"{len(voided)} voided (max_abs_cos_vs_c_hat={max_abs_cos_c_hat}, "
              f"max_abs_cos_vs_u_d={max_abs_cos_u_d})", flush=True)

    out_path = COMMITTED / substrate / "random_direction_ledger.json"
    write_json(out_path, ledger)
    print(f"[random-dir:{substrate}] wrote {out_path}", flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--substrate", required=True, choices=["trained", "raw_base"])
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
