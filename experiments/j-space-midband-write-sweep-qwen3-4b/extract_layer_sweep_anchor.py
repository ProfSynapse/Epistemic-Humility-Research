#!/usr/bin/env python3
"""J-space mid-band write sweep -- GPU extraction of anchor activations.

Offline prep step 1/3 (GPU). Model: unsloth/Qwen3-4B (full bf16, no 4-bit
quantization), no adapter (raw-base, checkpoint_tag "raw-base").

This experiment's LOCKED population (see AMENDMENT.md "Design" -> Population)
is confab + known_correct_answered (the gate fit/eval population) plus
unknown_refused (used only to anchor the doubt axis's "unknown" pole and the
AK Stage-1 propensity/caution-direction fit population). The release tail
(answerable_refused) is NOT extracted here: this instrument is tighten-only.

Method: same render/anchor convention and substrate as the resolved
doubt-gated-caution-tighten predecessor, extended to multiple hidden-state
indices:
  - model: unsloth FastLanguageModel.from_pretrained(unsloth/Qwen3-4B,
    max_seq_length=2048, dtype=torch.bfloat16, load_in_4bit=False), NO
    adapter (raw-base), FastLanguageModel.for_inference(model).
  - prompt: backends.render_probe_prompt(tokenizer, baseline_system_prompt,
    question, enable_thinking=False) -- same baseline system prompt string as
    the AH A0 arm.
  - anchor position: prompt_len - 1 (the last prompt token, pre-generation).
    A forward pass over the PROMPT ALONE suffices (no need to reproduce
    generation): anchor is a function of the prompt only, matching AK
    Stage-1's own "anchor_position": "prompt_len-1" definition.
  - layers: hs[23], hs[26], hs[29], hs[34].

Output (gitignored analysis/, NOT committed -- raw per-row activations are
intermediate scratch; only the FITTED direction artifacts this feeds are
promoted to analysis-committed/ by build_directions.py):
  analysis/layer_sweep_anchor_extract.safetensors   one tensor per
                                                    (layer,row_key)
  analysis/layer_sweep_anchor_extract_manifest.json provenance
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

PROBE_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe")
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

MODEL_NAME = "unsloth/Qwen3-4B"
AH_A0_ROWS = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/"
    "analysis/ah_main/gen_A0/rows.jsonl"
)
AK_STAGE1_POOL = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/"
    "analysis/ak_stage1/ak_stage1_pool.jsonl"
)

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "analysis" / "layer_sweep_anchor_extract.safetensors"
DEFAULT_MANIFEST = HERE / "analysis" / "layer_sweep_anchor_extract_manifest.json"
MINED_A0_KNOWN_CORRECT = HERE / "analysis" / "mined_a0_known_correct_rows.jsonl"
SIBLING_MINED_A0_KNOWN_CORRECT = (
    HERE.parent / "doubt-gated-caution-tighten" / "analysis" / "mined_a0_known_correct_rows.jsonl"
)

from layers import HS_INDICES  # noqa: E402


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_key(row_key: str) -> str:
    """safetensors tensor names must not contain ':'; row_key uses '::'."""
    return row_key.replace(":", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def select_rows(ah_a0_pool: list[dict], ak_stage1_pool: list[dict]) -> dict[str, list[dict]]:
    known_correct_answered = [
        r for r in ah_a0_pool
        if r.get("gold_class") == "answerable"
        and r.get("answered") is True
        and r.get("correct") is True
    ]
    mined_path = (
        MINED_A0_KNOWN_CORRECT
        if MINED_A0_KNOWN_CORRECT.exists()
        else SIBLING_MINED_A0_KNOWN_CORRECT
    )
    if mined_path.exists():
        seen = {r["row_key"] for r in known_correct_answered}
        for r in load_jsonl(mined_path):
            if r["row_key"] in seen:
                continue
            if r.get("answered") is True and r.get("correct") is True:
                known_correct_answered.append(r)
                seen.add(r["row_key"])
    unknown_refused = [r for r in ak_stage1_pool if not r["confab_on_unanswerable"]]
    confab = [r for r in ak_stage1_pool if r["confab_on_unanswerable"]]
    return {
        "known_correct_answered": known_correct_answered,
        "unknown_refused": unknown_refused,
        "confab": confab,
    }


def build_model():
    import torch
    from unsloth import FastLanguageModel  # import first (patches transformers)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME, max_seq_length=2048, dtype=torch.bfloat16,
        load_in_4bit=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def run(args: argparse.Namespace) -> int:
    import torch
    from safetensors.torch import save_file
    from backends import render_probe_prompt
    from amendment_ah_stage0_extract import load_baseline_system_prompt

    out_path = Path(args.out).resolve()
    manifest_path = Path(args.manifest).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    ah_a0_pool = load_jsonl(AH_A0_ROWS)
    ak_stage1_pool = load_jsonl(AK_STAGE1_POOL)
    selections = select_rows(ah_a0_pool, ak_stage1_pool)
    for role, rows in selections.items():
        print(f"[extract] {role}={len(rows)}", flush=True)

    work: list[tuple[str, str, dict]] = []
    for role, rows in selections.items():
        for r in rows:
            work.append((role, r["row_key"], r))

    print(f"[extract] loading raw-base model {MODEL_NAME} (unsloth, bf16, no "
          f"4-bit quant, no adapter) ...", flush=True)
    model, tokenizer = build_model()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    assert max(HS_INDICES) <= n_layers, (
        f"requested hs={HS_INDICES} requires >= {max(HS_INDICES)} hidden layers, got {n_layers}"
    )
    param_dtype = next(model.parameters()).dtype
    print(f"[extract] model dtype={param_dtype}", flush=True)

    tensors: dict[str, "torch.Tensor"] = {}
    row_meta: list[dict] = []
    t0 = time.time()
    for i, (role, row_key, row) in enumerate(work):
        question = row["question"]
        rendered, _mode = render_probe_prompt(
            tokenizer, baseline_system, question, enable_thinking=False
        )
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(
                **enc, output_hidden_states=True, use_cache=False
            )
        hs = out.hidden_states  # tuple len n_layers+1, each (1, seq, hidden)
        skey = _sanitize_key(row_key)
        for hs_index in HS_INDICES:
            vec = hs[hs_index][0, prompt_len - 1, :].float().cpu().contiguous()
            tensors[f"hs{hs_index}__{skey}"] = vec
        row_meta.append({
            "row_key": row_key, "safetensors_key": skey, "role": role,
            "prompt_len": prompt_len,
            "hs_tensor_keys": {str(h): f"hs{h}__{skey}" for h in HS_INDICES},
        })
        if (i + 1) % 100 == 0 or (i + 1) == len(work):
            el = time.time() - t0
            print(f"[extract] {i + 1}/{len(work)} ({el:.0f}s)", flush=True)

    save_file(tensors, str(out_path))

    manifest = {
        "stage": "j_space_midband_write_sweep_anchor_extract",
        "amendment": "j-space-midband-write-sweep-qwen3-4b",
        "base_model": MODEL_NAME, "substrate": "bf16", "load_in_4bit": False,
        "torch_dtype": str(param_dtype), "adapter": None,
        "loader": "unsloth.FastLanguageModel",
        "layer_labels": [f"hs{h}" for h in HS_INDICES],
        "hidden_states_indices": HS_INDICES,
        "anchor_position": "prompt_len-1",
        "source_pools": {
            "ah_a0_rows": str(AH_A0_ROWS),
            "ah_a0_rows_sha256": _sha256_file(AH_A0_ROWS),
            "mined_a0_known_correct": str(MINED_A0_KNOWN_CORRECT),
            "mined_a0_known_correct_sha256": (
                _sha256_file(MINED_A0_KNOWN_CORRECT)
                if MINED_A0_KNOWN_CORRECT.exists() else None
            ),
            "sibling_mined_a0_known_correct": str(SIBLING_MINED_A0_KNOWN_CORRECT),
            "sibling_mined_a0_known_correct_sha256": (
                _sha256_file(SIBLING_MINED_A0_KNOWN_CORRECT)
                if SIBLING_MINED_A0_KNOWN_CORRECT.exists() else None
            ),
            "ak_stage1_pool": str(AK_STAGE1_POOL),
            "ak_stage1_pool_sha256": _sha256_file(AK_STAGE1_POOL),
        },
        "n_rows_extracted": len(work),
        "counts": {role: len(rows) for role, rows in selections.items()},
        "out_path": str(out_path),
        "runtime_sec": round(time.time() - t0, 1),
        "rows": row_meta,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[extract] WROTE {out_path} ({len(tensors)} vectors) and {manifest_path}",
          flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    return ap.parse_args(argv)


def main(argv=None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
