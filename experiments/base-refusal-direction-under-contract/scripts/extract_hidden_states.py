#!/usr/bin/env python3
"""Stage 2 (extraction, GPU) for base-refusal-direction-under-contract.

L35 hidden states for the raw Qwen3-4B base under the byte-identical P-rc
render, on the Stage-1 known rows (known_refused + known_correct_answered),
via the shared render+verify helper
(experiments/common/knowledge_probe/backends.py:render_probe_prompt) and the
same no-grad / output_hidden_states=True / use_cache=False / last-prompt-token
forward idiom as hs_backends.py's TransformersPeftBackend.forward_hidden_states
-- reused verbatim; the only difference is there is no PEFT/adapter wrapper
here because this cell's substrate is the raw base with no adapter.

The P-rc system prompt is read directly from the pinned panel config
(experiments/prompt-vs-training-panel/configs/eval_panel_prc_local_4b.yaml)
at run time, byte-identical, never hand-copied.

Output: one <row_key>__h_base.safetensors per row (tensor key "L{layer}"),
matching latent_knowledge_probe.row_key_to_tensor_file's naming convention
exactly, so the pinned residual_caution_direction.py fit script (--source
h_base) can load this extraction directory unmodified.

No generation anywhere in this script (engine_exception: parity-locked).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_PROBE_DIR = ROOT / "experiments" / "common" / "knowledge_probe"
for p in (str(KNOWLEDGE_PROBE_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

PANEL_PRC_CONFIG = (
    ROOT / "experiments" / "prompt-vs-training-panel" / "configs"
    / "eval_panel_prc_local_4b.yaml"
)


def load_prc_system_prompt() -> str:
    with PANEL_PRC_CONFIG.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_known_rows(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def stem(row_key: str) -> str:
    return row_key.replace("::", "__")


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from backends import render_probe_prompt  # noqa: E402  (knowledge_probe/backends.py)

    system_prompt = load_prc_system_prompt()
    rows = load_known_rows(args.rows)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[extract] model={args.model_name} rows={len(rows)} layer={args.layer} "
          f"out_dir={out_dir}", flush=True)
    print(f"[extract] P-rc system prompt (byte-identical from {PANEL_PRC_CONFIG.name}): "
          f"{system_prompt!r}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()

    done_path = out_dir / "rows.jsonl"
    done_keys: set[str] = set()
    if done_path.exists():
        for line in done_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done_keys.add(json.loads(line)["row_key"])
        print(f"[extract] resume: {len(done_keys)} rows already present", flush=True)

    t0 = time.time()
    n_new = 0
    with done_path.open("a", encoding="utf-8") as rows_fh:
        for i, row in enumerate(rows):
            key = row["row_key"]
            if key in done_keys:
                continue
            rendered, mode = render_probe_prompt(
                tokenizer, system_prompt, row["question"], enable_thinking=False)
            inputs = tokenizer(rendered, return_tensors="pt").to("cuda")
            with torch.no_grad():
                out = model(**inputs, output_hidden_states=True,
                            use_cache=False, return_dict=True)
            vec = out.hidden_states[args.layer][0, -1, :].float().cpu()
            from safetensors.torch import save_file
            save_file({f"L{args.layer}": vec.contiguous()},
                      str(out_dir / f"{stem(key)}__h_base.safetensors"))
            rows_fh.write(json.dumps({
                "row_key": key,
                "behavior_cell": row["behavior_cell"],
                "render_mode": mode,
                "prompt_len": int(inputs["input_ids"].shape[1]),
            }) + "\n")
            rows_fh.flush()
            n_new += 1
            if (i + 1) % 200 == 0:
                elapsed = time.time() - t0
                print(f"[extract] {i + 1}/{len(rows)} rows "
                      f"({n_new} new, {elapsed:.0f}s elapsed)", flush=True)

    manifest = {
        "model_name": args.model_name,
        "layer": args.layer,
        "system_prompt": system_prompt,
        "system_prompt_source": str(PANEL_PRC_CONFIG.relative_to(ROOT)),
        "enable_thinking": False,
        "token_position_rule": "final_prompt_token",
        "persist_dtype": "float32",
        "rows_file": str(args.rows),
        "n_rows_requested": len(rows),
        "n_rows_written_this_run": n_new,
        "n_rows_total_in_out_dir": len(done_keys) + n_new,
        "out_dir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[extract] DONE -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-name", default="unsloth/Qwen3-4B-bnb-4bit")
    ap.add_argument("--rows", required=True, type=Path)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--layer", type=int, default=35)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
