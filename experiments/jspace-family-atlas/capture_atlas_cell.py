#!/usr/bin/env python3
"""Full-depth anchor capture for one jspace-family-atlas cell.

READ-ONLY mapping instrument: no steering, no interventions, no writes to
activations, no re-mining, no re-generation. This script only:

1. Reads the fleet's already-mined, already-graded row pool
   (`split_rows_private.jsonl`, produced by
   `doubt-snap-cross-family-confirmatory/prep_tuner_cell.py stratified_split`
   / `assign_roles`) for one cell, from wherever the fleet's Modal volume
   (`eh-doubt-snap-cross-family`) is mounted for this run.
2. Renders the fleet's own baseline prompt for each row (`render_jspace_atlas
   .render`, a verbatim port of the fleet's `render.py`).
3. Tokenizes and computes the anchor position exactly the way the fleet's
   `capture_anchor()` does (`prep_tuner_cell.py:402-419`): manual tokenize
   with `add_special_tokens=True`, position = `len(token_ids) - 1`. This is
   deliberately NOT the batch-capture engine's `"last"` position-spec string,
   so the atlas's anchor position matches the fleet's own anchor exactly for
   audit-parity.
4. Runs Synaptic-Tuner's `batch-capture` with `--layers all`, which resolves
   to `range(n_hidden_states)` -- every hidden-state index 0..num_hidden_layers
   inclusive (`synaptic-tuner/tuner/batch/engines/hf_batched.py
   _resolve_layers`) -- at the single anchor position, in float32.
5. Writes two committed, text-free aggregate files: a `split_manifest.json`
   (row_key/role/split/source/category_canon only, same shape as the fleet's
   own committed split manifest) and a `capture_manifest.json` (coverage and
   shape summary for AG0). No question text, aliases, generation text, or
   token IDs are ever written under `analysis-committed/`.

Private, gitignored outputs (safetensors + raw capture index + rendered
token-id rows) go under `analysis/<cell_id>/`. This script never touches
`mechinterp steer`, never opens a write law, and never mutates the fleet's
own volume namespace; the fleet's row pool is read-only input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"

sys.path.insert(0, str(ROOT))
import render_jspace_atlas as render_mod  # noqa: E402


def load_cell_yaml() -> dict[str, Any]:
    with (ROOT / "cell.yaml").open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def cell_by_id(cfg: dict[str, Any], cell_id: str) -> dict[str, Any]:
    for cell in cfg.get("cells", []):
        if cell.get("cell_id") == cell_id:
            return cell
    raise SystemExit(f"unknown cell_id: {cell_id}")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    tmp.replace(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def sh(cmd: list[str], *, cwd: Path = REPO_ROOT, env: dict[str, str] | None = None) -> None:
    print(f"[capture-atlas] $ {' '.join(cmd)}", flush=True)
    merged = {**os.environ, **(env or {})}
    result = subprocess.run(cmd, cwd=str(cwd), env=merged)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def private_dir(cell_id: str) -> Path:
    return ROOT / "analysis" / cell_id


def committed_dir(cell_id: str) -> Path:
    return ROOT / "analysis-committed" / cell_id


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_capture(args: argparse.Namespace) -> None:
    cfg = load_cell_yaml()
    cell = cell_by_id(cfg, args.cell_id)
    row_pool_path = Path(args.row_pool)
    if not row_pool_path.is_file():
        raise SystemExit(
            f"row pool not found at {row_pool_path}. In production this is "
            f"the fleet's split_rows_private.jsonl mounted read-only from "
            f"Modal volume {cell['source']['modal_volume']!r} at "
            f"{cell['source']['row_pool_path']!r} (RUN_TAG="
            f"{cell['source']['modal_run_tag']!r})."
        )
    rows = load_jsonl(row_pool_path)
    if not rows:
        raise SystemExit(f"row pool at {row_pool_path} is empty")

    pdir = private_dir(args.cell_id)
    cdir = committed_dir(args.cell_id)
    pdir.mkdir(parents=True, exist_ok=True)
    cdir.mkdir(parents=True, exist_ok=True)

    os.environ["JSPACE_ATLAS_RENDER_MODEL"] = cell["repo"]
    os.environ["JSPACE_ATLAS_RENDER_REVISION"] = cell["revision"]

    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        cell["repo"],
        revision=cell["revision"],
        token=os.environ.get("HF_TOKEN") or None,
        trust_remote_code=True,
    )

    cap_rows: list[dict[str, Any]] = []
    rowmeta: list[dict[str, Any]] = []
    for row in rows:
        prompt = render_mod.render(row)
        token_ids = tok(prompt, add_special_tokens=True)["input_ids"]
        cap_rows.append(
            {
                "id": row["row_key"],
                "token_ids": token_ids,
                "positions": {"anchor": len(token_ids) - 1},
            }
        )
        rowmeta.append(
            {
                "row_key": row["row_key"],
                "role": row["role"],
                "split": row["split"],
                "source": row.get("source"),
                "category_canon": row.get("category_canon"),
            }
        )

    cap_in = pdir / "atlas_capture_rows.jsonl"
    cap_dir = pdir / "atlas_capture"
    write_jsonl(cap_in, cap_rows)

    sh(
        [
            sys.executable,
            str(TUNER),
            "batch-capture",
            "--rows",
            str(cap_in),
            "--model",
            cell["repo"],
            "--model-revision",
            cell["revision"],
            "--out-dir",
            str(cap_dir),
            "--engine",
            "hf-batched",
            "--layers",
            "all",
            "--persist-dtype",
            "float32",
            "--batch-size",
            str(args.batch_size),
            "--resume",
        ]
    )

    index = load_jsonl(cap_dir / "capture.jsonl")
    captured_ids = {rec["id"] for rec in index}
    pool_ids = {r["row_key"] for r in rows}
    missing = pool_ids - captured_ids
    coverage_frac = len(captured_ids) / max(1, len(pool_ids))

    write_json(
        cdir / "split_manifest.json",
        {"cell_id": args.cell_id, "rows": rowmeta},
    )

    capture_manifest = {
        "cell_id": args.cell_id,
        "model": cell["repo"],
        "revision": cell["revision"],
        "num_hidden_layers": cell["num_hidden_layers"],
        "hidden_size": cell["hidden_size"],
        "n_hidden_states": cell["n_hidden_states"],
        "layers_requested": "all",
        "position_name": "anchor",
        "position_rule": "len(token_ids) - 1 (manual tokenize, add_special_tokens=True)",
        "persist_dtype": "float32",
        "batch_size": args.batch_size,
        "n_rows_in_pool": len(pool_ids),
        "n_rows_captured": len(captured_ids),
        "coverage_frac": coverage_frac,
        "coverage_pass_ag0": coverage_frac >= 0.95,
        "missing_row_count": len(missing),
        "missing_row_keys_sample": sorted(missing)[:20],
        "row_pool_source": cell["source"],
        "capture_index_sha256": sha256_file(cap_dir / "capture.jsonl"),
    }
    write_json(cdir / "capture_manifest.json", capture_manifest)
    print(json.dumps(capture_manifest, indent=2), flush=True)
    if coverage_frac < 0.95:
        raise SystemExit(
            f"AG0 capture_coverage failed: {coverage_frac:.4f} < 0.95 "
            f"({len(missing)} rows missing)"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_capture = sub.add_parser("capture", help="full-depth anchor capture for one cell")
    p_capture.add_argument("--cell-id", required=True)
    p_capture.add_argument(
        "--row-pool",
        required=True,
        help=(
            "Path to the fleet's split_rows_private.jsonl for this cell "
            "(read-only; e.g. the fleet's Modal volume mounted at "
            "/vol/doubt_snap_cross_family/doubt-snap-cross-family-r1/_live/"
            "<cell_id>/analysis/split_rows_private.jsonl)."
        ),
    )
    p_capture.add_argument("--batch-size", type=int, default=8)
    p_capture.set_defaults(func=cmd_capture)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
