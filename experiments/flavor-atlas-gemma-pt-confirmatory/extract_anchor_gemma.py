#!/usr/bin/env python3
"""Seam-safe forward-only anchor extraction for flavor-atlas-gemma-pt-confirmatory.

Adapted from `experiments/gemma4-e4b-kv-seam-quarantine/extract_anchor.py`'s
`use_cache=True` pattern (AMENDMENT.md "Instrument hazard that governs the
whole design"). `google/gemma-4-E4B` shares K/V across depth: blocks 24
through 41 read donor K/V from blocks 22/23 THROUGH the cache object built
during the SAME forward call. `synaptic-tuner/MechInterp/extraction/
capture.py:161` passes `use_cache=False` unconditionally, which starves
those blocks (hs00-hs24 stay bit-identical, hs25-hs42 decay from cosine
0.732 to 0.075). THE `mechinterp extract` VERB IS PROHIBITED FOR THIS CELL
(gates.yaml gg1_kv_seam_admissibility); this script is the sole admissible
extraction path.

Unlike the vendored source (which supports toggling K/V sharing OFF via
`kv_seam_patch` for a different experiment's ablation), this cell never
runs the OFF condition -- it always extracts with `use_cache=True`, which
is transformers' own default cache-construction behavior for a plain
`model(**enc, use_cache=True, ...)` call with no `past_key_values` passed
in. A fresh `DynamicCache` is implicitly built by the model call each row
(no cache object is reused across rows), which satisfies the "fresh
full-length cache per row" requirement without needing to port
`kv_seam_patch.py` / `model_lib.py`'s explicit cache-factory plumbing (that
plumbing exists upstream to make the ON/OFF conditions differ ONLY in the
sharing flag, not in cache construction -- a distinction that does not
apply here since this cell has no OFF condition).

Output layout matches what `flavor_probe_sweep.py` / `latent_knowledge_
probe.py::load_layers` already read (byte-identical schema, so the probe
protocol imports unchanged): one safetensors file per row at
`<extraction_dir>/<row_key with "::" -> "__">__anchor.safetensors` with
tensor keys `L0` .. `L{n_hidden_states-1}`, plus a `manifest.json` at
`<extraction_dir>/manifest.json` recording `layers: "all"`,
`n_hidden_states`, `forward_use_cache: true` (the GG1 provenance marker),
`complete`, and per-row metadata. This differs from the kv-seam-quarantine
source's own manifest (which writes ONE combined safetensors file keyed
`hs{layer}__{row}`) -- AMENDMENT.md registers this cell's own layout choice
explicitly ("write per-row safetensors plus a manifest in the layout
flavor_probe_sweep.py already reads").
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

FLUSH_EVERY = 50  # rows between durable manifest flushes (kill-resume safety)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def tensor_path(extraction_dir: Path, row_key: str, source: str = "anchor") -> Path:
    """Byte-identical convention to latent_knowledge_probe.row_key_to_tensor_file."""
    stem = row_key.replace("::", "__")
    return extraction_dir / f"{stem}__{source}.safetensors"


def run(args: argparse.Namespace) -> int:
    import torch
    from safetensors.torch import save_file

    if args.render == "primary":
        from render_gemma import render_primary_kshot as render_fn
    elif args.render == "control":
        from render_gemma import render_control_chat as render_fn
    else:
        raise SystemExit(f"unknown --render {args.render!r}, expected primary|control")

    panel_path = Path(args.panel)
    out_dir = Path(args.out_dir)
    manifest_path = out_dir / "manifest.json"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(panel_path)
    if not rows:
        print(f"[extract-anchor-gemma] ERROR: no rows in {panel_path}", file=sys.stderr)
        return 1
    panel_sha = sha256_file(panel_path)

    # Kill-resume: a row is "done" iff its own safetensors file already
    # exists (each row is independently durable -- unlike the combined-file
    # upstream source, there is no partial-row state to distinguish).
    done_meta: dict[str, dict] = {}
    if manifest_path.is_file() and not args.fresh:
        prev = json.loads(manifest_path.read_text())
        if (prev.get("panel_sha256") == panel_sha
                and prev.get("n_hidden_states") == 43
                and prev.get("forward_use_cache") is True
                and prev.get("render") == args.render):
            for rm in prev.get("rows", []):
                if tensor_path(out_dir, rm["row_key"]).is_file():
                    done_meta[rm["row_key"]] = rm
            print(f"[extract-anchor-gemma] resume: {len(done_meta)} rows already "
                  f"extracted, {len(rows) - len(done_meta)} remaining", flush=True)
        else:
            print("[extract-anchor-gemma] existing manifest has a different "
                  "fingerprint (panel/render changed); starting fresh", flush=True)

    print(f"[extract-anchor-gemma] loading {args.model_repo}@{args.revision} bf16, "
          f"render={args.render}", flush=True)
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model_repo, revision=args.revision)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_repo, revision=args.revision, torch_dtype=torch.bfloat16
    )
    model.eval()
    device = next(model.parameters()).device

    text_cfg = getattr(model.config, "text_config", model.config)
    n_layers = int(text_cfg.num_hidden_layers)
    hidden_size = int(text_cfg.hidden_size)
    n_hidden_states = n_layers + 1
    if n_hidden_states != 43:
        raise SystemExit(
            f"GG0 STOP: expected 43 hidden states (42 blocks), got {n_hidden_states} "
            f"({n_layers} blocks) -- substrate architecture drifted from what was "
            "confirmed at signing."
        )

    row_meta: list[dict] = list(done_meta.values())
    t0 = time.time()

    def write_manifest(complete: bool) -> None:
        manifest = {
            "stage": "flavor_atlas_gemma_pt_confirmatory_anchor_extract",
            "model_repo": args.model_repo,
            "revision": args.revision,
            "base_form": "pretrain-only base, no adapter, bf16",
            "render": args.render,
            "hidden_size": hidden_size,
            "n_hidden_layers": n_layers,
            "layers": "all",
            "n_hidden_states": n_hidden_states,
            "anchor_position": "prompt_len-1",
            # Provenance marker: any manifest WITHOUT this field True is
            # inadmissible on this KV-sharing substrate (gates.yaml gg1).
            "forward_use_cache": True,
            "panel_path": str(panel_path),
            "panel_sha256": panel_sha,
            "out_dir": str(out_dir),
            "n_rows_extracted": len(row_meta),
            "n_rows_total": len(rows),
            "complete": complete,
            "runtime_sec": round(time.time() - t0, 1),
            "rows": row_meta,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    since_flush = 0
    for idx, row in enumerate(rows, start=1):
        row_key = row["row_key"]
        if row_key in done_meta:
            continue
        prompt = render_fn(row)
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            # use_cache MUST be True on this substrate -- see module
            # docstring. No past_key_values is passed, so transformers
            # builds a fresh DynamicCache for this call only; nothing is
            # reused across rows.
            out = model(**enc, output_hidden_states=True, use_cache=True)
        hs = out.hidden_states
        if len(hs) != n_hidden_states:
            raise SystemExit(
                f"GG2 STOP: row {row_key} produced {len(hs)} hidden states, "
                f"expected {n_hidden_states}"
            )
        tensors = {
            f"L{layer}": hs[layer][0, prompt_len - 1, :].float().cpu().contiguous()
            for layer in range(n_hidden_states)
        }
        save_file(tensors, str(tensor_path(out_dir, row_key)))
        row_meta.append({
            "row_key": row_key,
            "label": row.get("label"),
            "flavor": row.get("flavor"),
            "prompt_len": prompt_len,
        })
        since_flush += 1
        if since_flush >= FLUSH_EVERY:
            write_manifest(complete=False)
            since_flush = 0
        if idx % 50 == 0 or idx == len(rows):
            print(f"[extract-anchor-gemma] {idx}/{len(rows)} "
                  f"(extracted {len(row_meta)})", flush=True)

    write_manifest(complete=True)
    print(json.dumps({
        "stage": "flavor_atlas_gemma_pt_confirmatory_anchor_extract",
        "n_rows_extracted": len(row_meta), "n_rows_total": len(rows),
        "runtime_sec": round(time.time() - t0, 1),
    }, indent=2))
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--panel", required=True, help="panel jsonl (row_key/question/label/flavor)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--render", choices=["primary", "control"], default="primary",
                     help="primary=base-mode k-shot (gates.yaml g_bands.primary_render); "
                          "control=chat-template (descriptive G6 only)")
    ap.add_argument("--model-repo", default="google/gemma-4-E4B")
    ap.add_argument("--revision", default="411aa17b749aa952df1359d2dcea73917a544d9a")
    ap.add_argument("--fresh", action="store_true",
                     help="ignore any existing partial extraction and restart from row 0")
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
