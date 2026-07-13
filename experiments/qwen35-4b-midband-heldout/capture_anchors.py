#!/usr/bin/env python3
"""qwen35-4b-midband-heldout -- forward-only hs20 anchor capture over the
1,692-row held-out pool. GPU, no generation.

AMENDMENT.md "Population"/"Lane and cost": "Anchor readout capture
(forward-only, no generation) over 1,692 rows to compute neg_z_d and the
fired set." No anchor tensors exist yet for held-out rows -- only the FIT
rows were anchor-extracted by the ladder's `fit_midband_directions.py`
Stage B (its own AMENDMENT.md scope statement 2: "the held-out pool was
never touched by design"). This script performs that first-ever forward
pass over held-out at hs20 (decoder block 19), mirroring
`fit_midband_directions.py:cmd_extract`'s anchor position convention
(hidden_states[hs_index][row, prompt_len-1, :], the last REAL prompt token,
pre-generation) exactly, but batched: per
`.skills/experiment-runner/reference/batched-generation.md`, "Pure
extraction (forward passes over existing text, no generation): Always
batchable, no smoke needed." Left-padding (steer_lib.load_model's own
convention) puts every row's own last real prompt token at the SAME
trailing column (index -1) regardless of that row's own prompt length, so
batched anchor capture needs no per-row length bookkeeping: hidden_states[
hs_index][:, -1, :] is the anchor row for every row in a left-padded batch.

Also computes and persists (row-level, gitignored) this experiment's OWN
fresh doubt-gate fire decision at hs20 using the ladder's frozen u_d/tau/mu_d/
sigma_d (byte-identical G0 check happens in pipeline.py, not here) -- this
is a pure, cheap projection once the anchor vector exists, done here so
pipeline.py's arms never need to touch the anchor tensors again.

Outputs (gitignored `analysis/`, never committed):
  analysis/anchor_extract_heldout.safetensors   1,692 hs20 anchor vectors,
                                                 keyed by sanitized row_key.
  analysis/anchor_extract_heldout_manifest.json capture provenance (counts,
                                                 runtime; no question/answer
                                                 text).
  analysis/fire_decisions_heldout.jsonl         row_key + proj_d/z_d/score/
                                                 fire per row (numbers only,
                                                 no text; kept under
                                                 gitignored analysis/ per
                                                 this repo's blanket
                                                 row-level-artifact rule).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
LADDER_COMMITTED = REPO_ROOT / "experiments" / "qwen35-4b-midband-doubt-snap" / "analysis-committed"
for _p in (str(REPO_ROOT / "synaptic-tuner"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import steer_lib  # noqa: E402

ANALYSIS = HERE / "analysis"
HS_INDEX = 20
DECODER_BLOCK_INDEX = 19
HIDDEN_DIM = steer_lib.HIDDEN_DIM

U_D_PATH = LADDER_COMMITTED / "directions" / "hs20" / "u_d.json"
BUILD_MANIFEST_PATH = LADDER_COMMITTED / "build_manifest.json"

OUT_TENSORS = ANALYSIS / "anchor_extract_heldout.safetensors"
OUT_MANIFEST = ANALYSIS / "anchor_extract_heldout_manifest.json"
OUT_FIRE = ANALYSIS / "fire_decisions_heldout.jsonl"

ROWS_PATH = ANALYSIS / "heldout_rows_for_steer.jsonl"


def _sanitize_key(row_key: str) -> str:
    return row_key.replace(":", "_")


def load_jsonl(path: Path) -> list[dict]:
    return steer_lib.load_jsonl(path)


def gate_decision(proj_d: float, mu_d: float, sigma_d: float, tau: float) -> dict:
    """AMENDMENT.md's frozen fire rule: fire iff neg_z_d = -z_d >= tau_frozen,
    z_d standardized with the ladder's own FIT-pool mu_d/sigma_d and clipped
    to [-2, 2]. Identical math to H3/H4/H6's own gate_decision (this repo's
    shared convention), not re-derived."""
    z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
    score = -z_d
    fire = bool(score >= tau)
    return {"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": score, "fire": fire, "tau": tau}


def cmd_capture(args: argparse.Namespace) -> int:
    import torch
    from safetensors.torch import save_file

    if not ROWS_PATH.is_file():
        raise SystemExit(f"missing {ROWS_PATH}; run materialize_rows.py first")
    rows = load_jsonl(ROWS_PATH)
    if args.n_rows is not None:
        rows = rows[: args.n_rows]
    print(f"[capture] {len(rows)} rows, hs_index={HS_INDEX}", flush=True)

    model, tokenizer, device = steer_lib.load_model()
    text_cfg = getattr(model.config, "text_config", model.config)
    n_layers = int(text_cfg.num_hidden_layers)
    hidden_dim = int(text_cfg.hidden_size)
    if hidden_dim != HIDDEN_DIM:
        raise SystemExit(f"expected hidden_dim={HIDDEN_DIM}, got {hidden_dim}")
    if HS_INDEX > n_layers:
        raise SystemExit(f"hs_index {HS_INDEX} exceeds n_layers={n_layers}")

    tensors: dict[str, "torch.Tensor"] = {}
    row_meta: list[dict] = []
    t0 = time.time()
    batch_size = args.batch_size
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        prompts = [steer_lib.render_prompt(r) for r in batch]
        enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        if len(hs) != n_layers + 1:
            raise RuntimeError(f"hidden_states length mismatch: got {len(hs)}, expected {n_layers + 1}")
        # Left padding (steer_lib.load_model) puts every row's true last
        # prompt token at column -1 regardless of that row's own length.
        vecs = hs[HS_INDEX][:, -1, :].float().cpu()
        for row, vec in zip(batch, vecs):
            skey = _sanitize_key(row["row_key"])
            tensors[skey] = vec.contiguous()
            row_meta.append({"row_key": row["row_key"], "safetensors_key": skey, "role": row["role"]})
        if (i + batch_size) % (batch_size * 20) < batch_size or (i + batch_size) >= len(rows):
            print(f"[capture] {min(i + batch_size, len(rows))}/{len(rows)} ({time.time() - t0:.0f}s)", flush=True)

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    save_file(tensors, str(OUT_TENSORS))
    manifest = {
        "base_model": steer_lib.MODEL_NAME, "revision": steer_lib.MODEL_REVISION, "substrate": "bf16",
        "hidden_dim": hidden_dim, "n_layers": n_layers, "hs_index": HS_INDEX,
        "anchor_position": "prompt_len-1 (last real prompt token; batched via left-padding column -1)",
        "render": "doubt-snap-cross-family-confirmatory BASELINE_SYSTEM_PROMPT + chat template, enable_thinking=False",
        "n_rows_extracted": len(rows), "runtime_sec": round(time.time() - t0, 1),
        "rows": row_meta,
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[capture] wrote {OUT_TENSORS} ({len(tensors)} vectors) and {OUT_MANIFEST}", flush=True)

    if args.skip_fire_decisions:
        return 0

    u_d = np.asarray(json.loads(U_D_PATH.read_text())["vector"], dtype=np.float64)
    build = json.loads(BUILD_MANIFEST_PATH.read_text())["layers"]["hs20"]
    mu_d, sigma_d, tau = build["mu_d"], build["sigma_d"], build["tau_frozen"]

    fire_records = []
    for row in rows:
        skey = _sanitize_key(row["row_key"])
        h = np.asarray(tensors[skey].numpy(), dtype=np.float64)
        proj_d = float(h @ u_d)
        decision = gate_decision(proj_d, mu_d, sigma_d, tau)
        fire_records.append({"row_key": row["row_key"], "role": row["role"], **decision})
    with OUT_FIRE.open("w", encoding="utf-8") as fh:
        for rec in fire_records:
            fh.write(json.dumps(rec) + "\n")
    n_fired_confab = sum(1 for r in fire_records if r["role"] == "confab" and r["fire"])
    n_fired_known = sum(1 for r in fire_records if r["role"] == "known_correct_answered" and r["fire"])
    print(
        f"[capture] wrote {OUT_FIRE}: fired confab={n_fired_confab}/"
        f"{sum(1 for r in fire_records if r['role'] == 'confab')}, "
        f"fired known={n_fired_known}/{sum(1 for r in fire_records if r['role'] == 'known_correct_answered')}",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--n-rows", type=int, default=None, help="probe subset, for wall-time bracketing only")
    ap.add_argument("--skip-fire-decisions", action="store_true")
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    args = ap.parse_args()
    if not args.i_know_this_runs_on_gpu:
        print(
            "[capture] refusing to run without --i-know-this-runs-on-gpu "
            "(this loads the model and runs a forward pass on GPU; the lead "
            "launches this, not the harness-build task).",
            file=sys.stderr,
        )
        return 2
    return cmd_capture(args)


if __name__ == "__main__":
    raise SystemExit(main())
