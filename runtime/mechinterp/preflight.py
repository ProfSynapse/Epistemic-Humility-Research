"""Synthetic installed-engine capture smoke; no research rows or acceptance claim.

Run inside the pinned desktop image, with this project and its T7 paths bound
at their original absolute paths. The model load belongs to the engine CLI.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml

from engine_host.cli_boundary import EngineCLI
from engine_host.storage import configure_storage, load_host, local_model


def render_row(row):
    return row["prompt"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--host-config", type=Path, required=True)
    parser.add_argument("--output", default="runtime-preflight")
    parser.add_argument("--layers", type=int, nargs="+", required=True)
    parser.add_argument("--site-blocks", type=int, nargs="+", required=True)
    parser.add_argument("--i-know-this-runs-on-gpu", action="store_true", required=True)
    args = parser.parse_args()
    root = args.project_root.resolve()
    if not args.output or Path(args.output).is_absolute() or ".." in Path(args.output).parts:
        parser.error("output must be a project artifact-relative namespace")
    os.environ.update(configure_storage(root, args.host_config))
    host = load_host(args.host_config)
    model = host["base_model"]
    source = local_model(args.host_config, model["repo"], model["revision"])
    output = root / ".synaptic" / "artifacts" / args.output
    output.mkdir(parents=True, exist_ok=True)
    rows = [{"row_key": "synthetic_" + str(i), "prompt": text} for i, text in enumerate(
        ("Hello.", "The sum of two and two is", "Return an empty JSON object."))]
    rows_path = output / "rows.jsonl"
    rows_bytes = "".join(json.dumps(row) + "\n" for row in rows)
    if rows_path.exists() and rows_path.read_text() != rows_bytes:
        raise ValueError("synthetic preflight input changed; use a new namespace")
    rows_path.write_text(rows_bytes)
    config = {"rows_path": f"artifact://{args.output}/rows.jsonl",
              "output_dir": f"artifact://{args.output}/capture", "families": ["anchor"],
              "layers": args.layers, "render_fn": "preflight:render_row",
              "forward_only": True, "use_cache": True, "resume": True,
              "capture_sites": [{"layer": block, "module": "mlp.down_proj", "tensor": "input"}
                                for block in args.site_blocks]}
    config_path = output / "extract.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    EngineCLI(root, plugin_roots=(Path(__file__).resolve().parent,)).run(
        "mechinterp", ["extract", "--mi-config", f"artifact://{args.output}/extract.yaml",
                       "--model", source, "--model-revision", model["revision"],
                       "--i-know-this-runs-on-gpu"])
    manifest = json.loads((output / "capture" / "manifest.json").read_text())
    if manifest.get("n_rows") != 3 or not manifest.get("complete"):
        raise ValueError("synthetic capture is incomplete")
    print(json.dumps({"status": "synthetic-capture-complete", "rows": 3,
                      "layers": args.layers, "site_blocks": args.site_blocks,
                      "scientific_result": False}, sort_keys=True))


if __name__ == "__main__":
    main()
