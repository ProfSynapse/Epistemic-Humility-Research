#!/usr/bin/env python3
"""Full-depth anchor capture for one family-atlas cell.

READ-ONLY mapping instrument: no steering, no interventions, no writes to
activations, no re-mining, no re-generation. Generalized from
`experiments/jspace-family-atlas/capture_atlas_cell.py` (the resolved
llama32_3b/mistral7b atlas) so any new model/family/size can run the same
capture without touching this script.

Per cell, this script only:

1. Reads an already-mined, already-graded row pool (`--row-pool`, one JSON
   object per line, each with at least `row_key`, `role`, `split`, and
   whatever fields the project's own render module needs). This script never
   mines rows and never re-generates answers; the row pool is read-only
   input, typically the fleet/source experiment's own committed
   `split_rows_private.jsonl`.
2. Renders each row's prompt via a project-supplied, dynamically loaded
   render module (`--render-module`, a path to a `.py` file exposing a
   callable named `--render-function`, default `render`). The render module
   is deliberately NOT bundled here: reproducing a source experiment's exact
   anchor position requires reusing that experiment's own prompt/template
   logic (system prompt, chat-template thinking-off handling, tokenization),
   which is specific to whichever fleet/source experiment this atlas cell is
   mapping. Point `--render-module` at a copy of that experiment's own
   render.py (ported, not imported, so this read-only instrument never
   depends on another experiment's directory). Before calling the render
   function this script sets `FAMILY_ATLAS_RENDER_MODEL` /
   `FAMILY_ATLAS_RENDER_REVISION` in the environment (the model repo and
   revision from `cell.yaml`); a render module that needs its own tokenizer
   identity should read these two variables (see
   `templates/render_example.py` for the pattern ported from
   jspace-family-atlas).
3. Tokenizes each rendered prompt and computes the anchor position as
   `len(token_ids) - 1` (manual tokenize, `add_special_tokens=True`) --
   mirrors `doubt-snap-cross-family-confirmatory/prep_tuner_cell.py`'s
   `capture_anchor()`, NOT the batch-capture engine's `"last"` string
   position spec, so a new atlas cell's anchor matches whichever source
   experiment it is auditing against, exactly.
4. Runs Synaptic-Tuner's `batch-capture` with the engine registered in
   `cell.yaml` and `--layers all`. The HF reference resolves this to
   `range(n_hidden_states)` in `hf_batched.py`; a vLLM engine must pass the
   skill's bridge proving the same indices `0..num_hidden_layers` inclusive.
   Capture is at the single anchor position in float32.
5. Writes two committed, text-free aggregate files: `split_manifest.json`
   (row_key/role/split/source/category_canon only) and
   `capture_manifest.json` (coverage and shape summary for gate AG0). No
   question text, aliases, generation text, or token IDs are ever written
   under `analysis-committed/`.

Private, gitignored outputs (safetensors + raw capture index + rendered
token-id rows) go under `analysis/<cell_id>/`. This script never touches
`mechinterp steer`, never opens a write law, and never mutates any other
experiment's own volume namespace; any source row pool it reads is read-only
input.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parent
# Assumes this script is copied into `experiments/<slug>/` (two levels below
# the repo root); see SKILL.md's numbered procedure.
REPO_ROOT = ROOT.parents[1]
TUNER = REPO_ROOT / "synaptic-tuner" / "tuner.py"


def load_cell_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def cell_by_id(cfg: dict[str, Any], cell_id: str) -> dict[str, Any]:
    for cell in cfg.get("cells", []):
        if cell.get("cell_id") == cell_id:
            return cell
    raise SystemExit(f"unknown cell_id: {cell_id}")


def load_render_fn(module_path: Path, function_name: str) -> Callable[[dict[str, Any]], str]:
    spec = importlib.util.spec_from_file_location("family_atlas_render_module", module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"could not load render module at {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = getattr(module, function_name, None)
    if fn is None or not callable(fn):
        raise SystemExit(f"{module_path} has no callable {function_name!r}")
    return fn


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
    print(f"[capture-family-atlas] $ {' '.join(cmd)}", flush=True)
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
    cell_yaml_path = Path(args.cell_yaml) if args.cell_yaml else (ROOT / "cell.yaml")
    cfg = load_cell_yaml(cell_yaml_path)
    cell = cell_by_id(cfg, args.cell_id)
    capture_cfg = cfg.get("capture") or {}
    engine = str(capture_cfg.get("engine", "hf-batched"))
    if engine == "vllm" and os.environ.get("VLLM_BATCH_INVARIANT") != "1":
        raise SystemExit(
            "capture.engine=vllm requires VLLM_BATCH_INVARIANT=1 before engine construction"
        )
    row_pool_path = Path(args.row_pool)
    if not row_pool_path.is_file():
        raise SystemExit(
            f"row pool not found at {row_pool_path}. This is expected to be "
            f"the source experiment's own row pool, mounted or downloaded "
            f"read-only; see cell.yaml's `source:` block for where it comes "
            f"from for cell_id={args.cell_id!r}."
        )
    rows = load_jsonl(row_pool_path)
    if not rows:
        raise SystemExit(f"row pool at {row_pool_path} is empty")

    render_fn = load_render_fn(Path(args.render_module), args.render_function)

    pdir = private_dir(args.cell_id)
    cdir = committed_dir(args.cell_id)
    pdir.mkdir(parents=True, exist_ok=True)
    cdir.mkdir(parents=True, exist_ok=True)

    os.environ["FAMILY_ATLAS_RENDER_MODEL"] = cell["repo"]
    os.environ["FAMILY_ATLAS_RENDER_REVISION"] = cell["revision"]

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
        prompt = render_fn(row)
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
            engine,
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
        "engine": engine,
        "position_name": "anchor",
        "position_rule": "len(token_ids) - 1 (manual tokenize, add_special_tokens=True)",
        "persist_dtype": "float32",
        "batch_size": args.batch_size,
        "n_rows_in_pool": len(pool_ids),
        "n_rows_captured": len(captured_ids),
        "coverage_frac": coverage_frac,
        "coverage_pass_ag0": coverage_frac >= args.min_coverage,
        "missing_row_count": len(missing),
        "missing_row_keys_sample": sorted(missing)[:20],
        "row_pool_source": cell.get("source"),
        "capture_index_sha256": sha256_file(cap_dir / "capture.jsonl"),
    }
    write_json(cdir / "capture_manifest.json", capture_manifest)
    print(json.dumps(capture_manifest, indent=2), flush=True)
    if coverage_frac < args.min_coverage:
        raise SystemExit(
            f"AG0 capture_coverage failed: {coverage_frac:.4f} < {args.min_coverage} "
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
        help="Path to the source experiment's row pool (read-only JSONL, one row per line).",
    )
    p_capture.add_argument(
        "--cell-yaml",
        default=None,
        help="Path to this cell's cell.yaml (default: cell.yaml next to this script).",
    )
    p_capture.add_argument(
        "--render-module",
        required=True,
        help=(
            "Path to a .py file exposing the render callable (default name "
            "'render', see --render-function). Must reproduce the source "
            "experiment's own prompt/anchor convention exactly."
        ),
    )
    p_capture.add_argument("--render-function", default="render")
    p_capture.add_argument("--batch-size", type=int, default=8)
    p_capture.add_argument(
        "--min-coverage",
        type=float,
        default=0.95,
        help="AG0 capture-coverage floor (default matches the family-atlas gates.yaml template).",
    )
    p_capture.set_defaults(func=cmd_capture)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
