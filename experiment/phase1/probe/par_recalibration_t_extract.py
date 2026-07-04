#!/usr/bin/env python3
"""PAR recalibration PASS 2 — full T-surface pre-gen re-extraction (GPU).

Team-lead task #64, branch par-mining-recalibration. The original amendment-T
extractor only persisted pre-gen states for ANSWERED rows (1,488 / 8,548); the
7,060 refused rows (the over-refusal quadrant the PAR reward targets) have no
saved states. This re-extracts the pre-generation anchor for ALL 8,548 T rows on
the deployed checkpoint, forward-only (no generation), so refused rows are
captured too.

Checkpoint (LOCAL, canonical checkout — the manifest's /workspace/repo/scratch
prefix is the cloud alias for the same scratch/ tree):
  base    = scratch/.../sft_schema_clean_seed1_full/.../Qwen3-4B-bnb-4bit/merged-16bit
  adapter = scratch/.../schema_clean_sft_grpo_v2_seed1_full/.../final_model
Load mirrors amendment_t (PeftModel.from_pretrained on the merged base, adapter
ACTIVE) so we read the DEPLOYED model. Same forced-best-guess system prompt and
render recipe (enable_thinking=False), same anchor position (prompt_len-1),
float32 persisted, single-row (batch-1) — the AG-exact path.

Pool: the existing T rows.jsonl (question + row_key per row) so the surface is
byte-identical. label/correctness carried through from the original grading.

CHECKPOINT-IDENTITY GUARD (team-lead directive): before trusting the run, a
handful of re-extracted answered-row states are compared to the ORIGINAL stored
pre-states (cos >= COS_MIN). If they do not match, the script STOPS with a
non-zero exit and does NOT overwrite — wrong checkpoint.

Outputs (canonical, gitignored) under analysis/par_recalibration/t_full_pregen/:
  <safe_key>__pre.safetensors   {L0..L36} pre-gen vectors (fp32), all 8,548
  rows.jsonl                    row_key/question/label/correct/answered/prompt_len
  manifest.json                 config sha + identity-check result + counts
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import _config_sha  # noqa: E402
from amendment_t_correctness_readout_deployment_extract import (  # noqa: E402
    SYSTEM_PROMPT, MODEL_TAG, ADAPTER_NAME,
)

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
T_STAGE2 = PROBE_ROOT / "qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2"
DEFAULT_BASE = (CANONICAL / "scratch/schema_response_confidence/runs/"
                "sft_schema_clean_seed1_full/20260623_123624/"
                "Qwen3-4B-bnb-4bit/merged-16bit")
DEFAULT_ADAPTER = (CANONICAL / "scratch/schema_response_confidence/runs/"
                   "schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model")
DEFAULT_OUT = PROBE_ROOT / "analysis/par_recalibration/t_full_pregen"

EXPECTED_ROWS = 8548
COS_MIN = 0.999          # identity guard threshold on answered-row pre-states
IDENTITY_CHECK_N = 8     # answered rows to verify against stored states


def safe_key_for(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_")


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def run(args) -> int:
    import torch
    import numpy as np
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    from safetensors.torch import save_file
    from safetensors import safe_open

    base_path = Path(args.base_model).resolve()
    adapter_path = Path(args.adapter).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(T_STAGE2 / "rows.jsonl")
    if args.limit:
        rows = rows[: args.limit]
    if not args.skip_count_check and len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"T rows = {len(rows)}, expected {EXPECTED_ROWS}")

    config_payload = {
        "stage": "par_recalibration_t_full_pregen",
        "base_model_path": str(base_path), "adapter_path": str(adapter_path),
        "adapter_name": ADAPTER_NAME, "model_tag": MODEL_TAG,
        "system_prompt": SYSTEM_PROMPT, "enable_thinking": False,
        "anchor_position": "prompt_len-1", "persist_dtype": "float32",
        "generation": "NONE-forward-only", "decode": "n/a",
    }
    config_sha = _config_sha(config_payload)

    print(f"[par/t-extract] loading base {base_path} + adapter {adapter_path} ...",
          flush=True)
    tokenizer = AutoTokenizer.from_pretrained(str(base_path))
    base = AutoModelForCausalLM.from_pretrained(
        str(base_path), torch_dtype=torch.bfloat16, device_map="cuda")
    model = PeftModel.from_pretrained(base, str(adapter_path),
                                      adapter_name=ADAPTER_NAME)
    model.eval()
    model.set_adapter(ADAPTER_NAME)  # deployed model = adapter ACTIVE
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    print(f"[par/t-extract] rows={len(rows)} n_layers={n_layers}", flush=True)

    def single_anchor(question: str):
        rendered, _mode = render_probe_prompt(
            tokenizer, SYSTEM_PROMPT, question, enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states
        vecs = {f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                for li in range(len(hs))}
        return vecs, prompt_len

    # --- CHECKPOINT-IDENTITY GUARD (before writing anything) ---
    answered = [r for r in rows if r.get("answered")]
    check = {"performed": False, "n": 0, "min_cos": None, "passed": None,
             "threshold": COS_MIN}
    if answered:
        sample = answered[:IDENTITY_CHECK_N]
        print(f"[par/t-extract] identity guard on {len(sample)} answered rows "
              f"(cos >= {COS_MIN}) ...", flush=True)
        min_cos = 1.0
        for r in sample:
            sk = safe_key_for(r["row_key"])
            stored_f = T_STAGE2 / f"{sk}__pre.safetensors"
            if not stored_f.exists():
                continue
            vecs, _ = single_anchor(r["question"])
            with safe_open(str(stored_f), "pt") as st:
                stored = st.get_tensor("L24").float()
            new = vecs["L24"].float()
            cos = float(torch.nn.functional.cosine_similarity(
                new.unsqueeze(0), stored.unsqueeze(0))[0])
            min_cos = min(min_cos, cos)
        check.update(performed=True, n=len(sample), min_cos=round(min_cos, 6),
                     passed=bool(min_cos >= COS_MIN))
        print(f"[par/t-extract] identity guard min_cos={min_cos:.6f} "
              f"passed={check['passed']}", flush=True)
        if not check["passed"]:
            print("[par/t-extract] IDENTITY GUARD FAILED — wrong checkpoint. "
                  "STOPPING, nothing overwritten.", flush=True)
            (out_dir / "IDENTITY_CHECK_FAILED.json").write_text(
                json.dumps(check, indent=2), encoding="utf-8")
            return 3

    # --- full extraction (all rows, forward-only) ---
    rows_path = out_dir / "rows.jsonl"
    t0 = time.time()
    written = 0
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for r in rows:
            vecs, prompt_len = single_anchor(r["question"])
            sk = safe_key_for(r["row_key"])
            save_file(vecs, str(out_dir / f"{sk}__pre.safetensors"))
            rows_fh.write(json.dumps({
                "row_key": r["row_key"], "dataset": r.get("dataset"),
                "question": r["question"], "answered": r.get("answered"),
                "refused": r.get("refused"), "label": r.get("label"),
                "correct": r.get("correct"), "prompt_len": prompt_len,
                "safe_key": sk, "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 500 == 0 or written == len(rows):
                el = time.time() - t0
                print(f"[par/t-extract] {written}/{len(rows)} {el:.0f}s "
                      f"({written/el:.1f}/s)", flush=True)

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size, "n_rows": len(rows),
        "n_written": written, "identity_check": check,
        "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir),
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                          encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[par/t-extract] DONE {written} rows -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-model", default=str(DEFAULT_BASE))
    ap.add_argument("--adapter", default=str(DEFAULT_ADAPTER))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--skip-count-check", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
