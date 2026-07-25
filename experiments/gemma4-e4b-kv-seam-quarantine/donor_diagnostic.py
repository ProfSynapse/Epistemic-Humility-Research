#!/usr/bin/env python3
"""Driver for `kv_seam_patch.donor_projection_diagnostic` -- how much can the
sharing-OFF condition possibly differ from ON?

Registered as AMENDMENT.md "Open questions at sign" #4. The lead authorized
this to run BEFORE any GPU spend on the main run (cell.yaml
`execution.gpu_carve_outs.donor_projection_diagnostic`), because it can only
de-risk the design if it lands before signing.

WHAT IT ANSWERS. Under sharing ON, blocks 24..41 attend over block 22's or 23's
K/V. Under OFF they recompute from their own residual stream using their own
retained `k_proj`/`v_proj`. If those retained projections nearly reproduce what
the donor would have produced, OFF is a WEAK manipulation and a negative A2
would be uninformative -- not evidence about the KV pathway. Better to know that
now than after a full dosed run.

WHAT IT DOES NOT ANSWER. High cosine does NOT prove OFF is inert: attention is
nonlinear in K and small projection differences can amplify downstream. A high
cosine licenses "treat a null as uninformative", nothing stronger. Low cosine is
the cleanly interpretable direction. That caveat rides along in the output JSON
as `interpretation_note`, so it cannot be separated from the numbers later.

SCOPE, per the carve-out: forward passes only. No dosing, no generation, no arm
executes. Output goes to the gitignored-private `analysis/<family>/`, never to
`analysis-committed/`.

Run:
    python3 donor_diagnostic.py --family gemma4-e4b [--n-rows 4]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import kv_seam_patch as kv  # noqa: E402
import model_lib as ml  # noqa: E402
from family_config import FAMILY_SLUGS, load_family  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    ap.add_argument("--n-rows", type=int, default=4,
                    help="rows to average the diagnostic over. The comparison is "
                         "per-block over one prompt's projection outputs; several "
                         "rows guard against a single prompt being unrepresentative.")
    ap.add_argument("--rows", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    import torch

    family = args.family
    cfg = load_family(family)
    rows_path = Path(args.rows or (HERE / "analysis" / family / "eval_rows.jsonl"))
    out_path = Path(args.out or (HERE / "analysis" / family
                                 / "donor_projection_diagnostic.json"))
    kv.refuse_to_write_through_symlink(out_path)

    rows = load_jsonl(rows_path)
    if not rows:
        print(f"[donor-diag:{family}] ERROR: no rows in {rows_path}", file=sys.stderr)
        return 1
    rows = rows[:args.n_rows]

    print(f"[donor-diag:{family}] loading {cfg['checkpoint']['repo']} bf16", flush=True)
    t0 = time.time()
    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    device = next(model.parameters()).device
    # Fails loudly here rather than producing a diagnostic about the wrong
    # geometry: donor identity is the entire content of this measurement.
    geom = kv.verify_architecture(model)
    print(f"[donor-diag:{family}] loaded in {time.time() - t0:.1f}s on {device}; "
          f"donors={geom['donors']} shared=[{geom['kv_shared_blocks'][0]}.."
          f"{geom['kv_shared_blocks'][-1]}]", flush=True)

    per_row = []
    for idx, row in enumerate(rows, start=1):
        rendered = ml.render(family, tokenizer, row)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        result = kv.donor_projection_diagnostic(model, enc)
        result["row_key"] = row.get("row_key")
        result["n_tokens"] = int(enc["input_ids"].shape[1])
        per_row.append(result)
        s = result["summary"]
        print(f"[donor-diag:{family}] row {idx}/{len(rows)} "
              f"({result['n_blocks_compared']} blocks): "
              f"k_proj cos median={s['k_proj_cosine']['median']:.4f} "
              f"max={s['k_proj_cosine']['max']:.4f} | "
              f"v_proj cos median={s['v_proj_cosine']['median']:.4f} "
              f"max={s['v_proj_cosine']['max']:.4f}", flush=True)

    def across_rows(key: str, stat: str) -> dict:
        vals = [r["summary"][key][stat] for r in per_row if r["summary"].get(key)]
        t = torch.tensor(vals)
        return {"min": float(t.min()), "median": float(t.median()),
                "max": float(t.max()), "mean": float(t.mean()), "n_rows": len(vals)}

    report = {
        "diagnostic": "donor_vs_own_kv_projection",
        "registered_as": "AMENDMENT.md 'Open questions at sign' #4",
        "authorized_by": "lead, explicitly, 2026-07-25 "
                         "(cell.yaml execution.gpu_carve_outs)",
        "family": family,
        "base_model": cfg["checkpoint"]["repo"],
        "rows_file": str(rows_path),
        "n_rows": len(per_row),
        "donors": geom["donors"],
        "shared_blocks": geom["kv_shared_blocks"],
        # Per-row medians aggregated across rows -- a median of medians, reported
        # as such. Not a pooled statistic; it answers "is this stable across
        # prompts", which is the only cross-row question here.
        "across_rows_of_per_row_median": {
            k: across_rows(k, "median") for k in
            ("k_proj_cosine", "k_proj_rel_l2_err",
             "v_proj_cosine", "v_proj_rel_l2_err")
        },
        "across_rows_of_per_row_max_cosine": {
            "k_proj": across_rows("k_proj_cosine", "max"),
            "v_proj": across_rows("v_proj_cosine", "max"),
        },
        "interpretation_note": per_row[0]["interpretation_note"],
        "measurement_caveat": per_row[0]["measurement_caveat"],
        "per_row": per_row,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    a = report["across_rows_of_per_row_median"]
    print()
    print(f"[donor-diag:{family}] across {len(per_row)} rows, median per-block cosine:")
    print(f"    k_proj: {a['k_proj_cosine']['median']:.4f} "
          f"(range {a['k_proj_cosine']['min']:.4f}..{a['k_proj_cosine']['max']:.4f})")
    print(f"    v_proj: {a['v_proj_cosine']['median']:.4f} "
          f"(range {a['v_proj_cosine']['min']:.4f}..{a['v_proj_cosine']['max']:.4f})")
    print(f"    k_proj rel L2 err: {a['k_proj_rel_l2_err']['median']:.4f} "
          "(scale-inflated, see measurement_caveat)")
    print(f"    v_proj rel L2 err: {a['v_proj_rel_l2_err']['median']:.4f} "
          "(scale-inflated, see measurement_caveat)")
    print()
    print(report["interpretation_note"])
    print()
    print(report["measurement_caveat"])
    print(f"\n[donor-diag:{family}] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
