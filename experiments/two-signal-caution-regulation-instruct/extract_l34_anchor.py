#!/usr/bin/env python3
"""Two-signal caution regulation -- GPU extraction of L34 anchor activations.

Offline prep step 1/2 (GPU). See AMENDMENT.md "Design" and the u_d doubt-sensor
decision (2026-07-06): u_d is a fresh known-vs-unknown mean-diff refit at L34 on
the AH A0 / AK Stage-1 pool. The AK Stage-1 raw-base tensor cache
($HOME/ak_census_data/ak-stage1-raw-base-r1/tensors/extracted/*.safetensors)
already carries L34@anchor for all 1,338 UNANSWERABLE pool rows (309 confab +
1,029 refuse), because AK Stage 1 captured the unanswerable-only surface. It
does NOT carry activations for any ANSWERABLE row, because that pool was never
run through the AK Stage-1 extraction. This script fills that gap for exactly
the two answerable-side row sets this experiment needs:

  known_correct_answered  (gold_class == "answerable", answered, correct)
                           -- the "known" class for the u_d mean-diff fit.
  answerable_refused      (gold_class == "answerable", refused)
                           -- the release-tail eval-pool rows (need z_d/z_p to
                           write the two-signal gain).

Method (byte-identical to the AK Stage-1 capture's own loading + anchor
convention, read in full from
experiment/phase1/probe/amendment_ak_stage1_extract.py -- the script that
produced the cached tensors this run must be comparable to):
  - model: unsloth FastLanguageModel.from_pretrained(unsloth/Qwen3-4B-bnb-4bit,
    max_seq_length=2048, dtype=None, load_in_4bit=True), NO adapter (raw-base),
    FastLanguageModel.for_inference(model). This is NOT the plain
    AutoModelForCausalLM path amendment_ah_main_generate.py used for its own
    GENERATION -- it is the unsloth path the AK Stage-1 tensor cache was built
    with, so the two hidden-state sources are numerically comparable.
  - prompt: backends.render_probe_prompt(tokenizer, baseline_system_prompt,
    question, enable_thinking=False) -- same baseline system prompt string as
    the AH A0 arm (verified byte-identical to the AH main manifest's own
    string; see NOTEBOOK.md).
  - anchor position: prompt_len - 1 (the last prompt token, pre-generation).
    A forward pass over the PROMPT ALONE suffices (no need to reproduce
    generation): anchor is a function of the prompt only, not the emitted
    answer, matching AK Stage-1's own "anchor_position": "prompt_len-1"
    definition.
  - layer: L34 == hs[34] (hidden_states index 34, matching AK Stage-1's
    "L34" -> hs[int("34")] convention exactly; this is the SAME "L34" label
    build_directions.py maps to tuner 0-indexed decoder block 33).

Output (gitignored analysis/, NOT committed -- raw per-row activations are
intermediate scratch; only the FITTED direction/gain artifacts this feeds are
promoted to analysis-committed/ by build_directions.py):
  analysis/l34_anchor_extract.safetensors   one row per extracted row_key
                                            (sanitized key -> float32 [2560])
  analysis/l34_anchor_extract_manifest.json provenance: n extracted per role,
                                            model/config, source pool sha256
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

MODEL_NAME = "unsloth/Qwen3-4B-bnb-4bit"
AH_A0_ROWS = Path(
    "/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/probe/"
    "analysis/ah_main/gen_A0/rows.jsonl"
)

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "analysis" / "l34_anchor_extract.safetensors"
DEFAULT_MANIFEST = HERE / "analysis" / "l34_anchor_extract_manifest.json"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sanitize_key(row_key: str) -> str:
    """safetensors tensor names must not contain ':'; row_key uses '::'."""
    return row_key.replace(":", "_")


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def select_rows(pool: list[dict]) -> dict[str, list[dict]]:
    known_correct_answered = [
        r for r in pool
        if r.get("gold_class") == "answerable"
        and r.get("answered") is True
        and r.get("correct") is True
    ]
    answerable_refused = [
        r for r in pool
        if r.get("gold_class") == "answerable"
        and r.get("refused") is True
    ]
    return {
        "known_correct_answered": known_correct_answered,
        "answerable_refused": answerable_refused,
    }


def build_model():
    from unsloth import FastLanguageModel  # import first (patches transformers)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME, max_seq_length=2048, dtype=None, load_in_4bit=True
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
    pool = load_jsonl(AH_A0_ROWS)
    selections = select_rows(pool)
    n_known = len(selections["known_correct_answered"])
    n_release = len(selections["answerable_refused"])
    print(f"[extract] AH A0 pool n={len(pool)} | known_correct_answered={n_known} "
          f"answerable_refused={n_release}", flush=True)

    work: list[tuple[str, str, dict]] = []
    for role, rows in selections.items():
        for r in rows:
            work.append((role, r["row_key"], r))

    print(f"[extract] loading raw-base model {MODEL_NAME} (unsloth, 4-bit, no "
          f"adapter) ...", flush=True)
    model, tokenizer = build_model()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    assert 34 <= n_layers, f"L34 requires >= 34 hidden layers, got {n_layers}"

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
        vec = hs[34][0, prompt_len - 1, :].float().cpu().contiguous()
        skey = _sanitize_key(row_key)
        tensors[skey] = vec
        row_meta.append({
            "row_key": row_key, "safetensors_key": skey, "role": role,
            "prompt_len": prompt_len,
        })
        if (i + 1) % 40 == 0 or (i + 1) == len(work):
            el = time.time() - t0
            print(f"[extract] {i + 1}/{len(work)} ({el:.0f}s)", flush=True)

    save_file(tensors, str(out_path))

    manifest = {
        "stage": "two_signal_l34_anchor_extract",
        "amendment": "two-signal-caution-regulation-instruct",
        "base_model": MODEL_NAME, "load_in_4bit": True, "adapter": None,
        "loader": "unsloth.FastLanguageModel (matches amendment_ak_stage1_extract.py)",
        "layer_label": "L34", "hidden_states_index": 34,
        "anchor_position": "prompt_len-1",
        "source_pool": str(AH_A0_ROWS),
        "source_pool_sha256": _sha256_file(AH_A0_ROWS),
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
