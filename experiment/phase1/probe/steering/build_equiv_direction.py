#!/usr/bin/env python3
"""Convert a residual-caution-direction JSON into the cell-native direction the
GPU equivalence cell (gpu_equivalence_cell.py) consumes.

The residual-direction JSON emitted by build_caution_perp_direction.py stores an
UN-normalized ``theta`` (the consuming intervention runner unit-normalizes it)
and uses the ``layer`` / ``block`` schema (``block = layer - 1`` is the decoder
block whose OUTPUT equals hidden_states[layer], Transformers convention). The
steering cell's confidence_steer.load_direction instead expects:
  * a ``best_layer`` key equal to the decoder-block index to hook
    (model.model.layers[best_layer]), and
  * a unit-norm vector in a sibling ``.npy`` (bare array) or ``.safetensors``.

This converter is deterministic: it unit-normalizes ``theta``, sets
``best_layer = block`` (so the hook edits the layer whose output the direction
was fit on), records the source path + sha256 for provenance, and writes the
JSON + sibling ``.npy``. It is CPU-only and reads a small JSON (no GPU tensors).

Usage:
  python build_equiv_direction.py \
      --source .../caution_perp_direction_L35.json \
      --out directions/qwen3-4b-grpo-v2/direction_caution.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def convert(source: Path, out: Path) -> dict:
    raw_bytes = source.read_bytes()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    src = json.loads(raw_bytes)

    theta = np.asarray(src["theta"], dtype=np.float64)
    norm = float(np.linalg.norm(theta))
    if norm == 0.0:
        raise ValueError("source theta has zero norm")
    d = (theta / norm).astype(np.float32)
    # sanity: the residual schema stores block = layer - 1 (hidden_states[layer]
    # is decoder block (layer-1)'s output). We hook that decoder block.
    block = int(src["block"])
    if int(src["layer"]) - 1 != block:
        raise ValueError(
            f"unexpected schema: layer={src['layer']} block={block} "
            "(expected block == layer - 1)")

    meta = {
        "schema_version": "steering-cell-direction/v1",
        "best_layer": block,
        "hidden_dim": int(d.shape[0]),
        "d": [float(v) for v in d],
        "provenance": {
            "source_direction": str(source),
            "source_sha256": sha,
            "source_schema_version": src.get("schema_version"),
            "source_layer": int(src["layer"]),
            "source_block": block,
            "source_theta_norm": norm,
            "source_notice": src.get("notice"),
            "source_pos_cell": src.get("pos_cell"),
            "source_neg_cell": src.get("neg_cell"),
            "converter": "experiment/phase1/probe/steering/build_equiv_direction.py",
            "note": ("Unit-normalized preimage of caution_perp theta. best_layer "
                     "= source block (decoder layer whose output is "
                     "hidden_states[source_layer]). For the GPU batching-parity "
                     "self-check only; NOT a scientific readout."),
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(meta, indent=2))
    np.save(out.with_suffix(".npy"), d)
    return meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    meta = convert(args.source, args.out)
    print(f"wrote {args.out} (+ .npy) best_layer={meta['best_layer']} "
          f"hidden_dim={meta['hidden_dim']} "
          f"source_sha256={meta['provenance']['source_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
