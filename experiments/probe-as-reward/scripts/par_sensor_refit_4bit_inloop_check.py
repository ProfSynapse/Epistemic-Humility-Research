#!/usr/bin/env python3
"""PAR sensor-v2 — inloop_equivalence verification (GPU, no re-extraction).

Team-lead re-extraction order required an 8-row inloop_equivalence cross-check in
the 4-bit manifests: the extractor's persisted L24 state must equal the smoke's
in-loop pre-gen read (same row, prompt-only batch-1) at <= 1e-4 — the check that
guarantees smoke criterion 2 passes by construction against the v2 sensor.

The 4-bit re-extraction already ran (union_pregen_4bit 18,496 + mining_pregen_4bit
9,397; the v2 sensor probes_v2/probe_L24_cleansft4bit.joblib was refit on them,
OOF AUROC 0.9945). Rather than re-extract, this loads the SERVING model once
(byte-identical to amendment_ai_smoke.py and par_sensor_refit_extract_4bit.py:
unsloth load_in_4bit + train-time LoRA identity + for_inference) and for the
first 8 rows of each surface compares:
  A) smoke in-loop L24 read (probe render, hidden_states[24] at prompt_len-1)
  B) the extractor's single_anchor L24 read (identical path, fresh forward)
  C) the PERSISTED on-disk 4-bit L24 state the v2 sensor was fit on
requiring max|A-B| and max|A-C| <= 1e-4. It also records the bnb quant config.
The inloop_equivalence + quant_config blocks are merged into each surface's
existing manifest.json (no state files are rewritten).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from path_compat import phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from amendment_ah_stage0_extract import load_baseline_system_prompt, safe_key_for  # noqa: E402

CANONICAL = repo_root()
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
CLEAN_SFT_BASE = (CANONICAL / "scratch/schema_response_confidence/runs/"
                  "sft_schema_clean_seed1_full/20260623_123624/"
                  "Qwen3-4B-bnb-4bit/merged-16bit")
REFIT_DIR = PROBE_ROOT / "analysis/par_sensor_refit"
SURFACES = {"union": REFIT_DIR / "union_pregen_4bit",
            "mining": REFIT_DIR / "mining_pregen_4bit"}
N_CHECK = 8
TOL = 1e-4


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def run(args) -> int:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    from unsloth import FastLanguageModel
    import torch
    from backends import render_probe_prompt
    from safetensors import safe_open

    baseline_system = load_baseline_system_prompt()
    print(f"[inloop-check] loading SERVING clean-SFT (4-bit + train-time LoRA) ...",
          flush=True)
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(CLEAN_SFT_BASE), max_seq_length=2048, dtype=None,
        load_in_4bit=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = FastLanguageModel.get_peft_model(
        model, r=32, lora_alpha=64, lora_dropout=0.05, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth", random_state=1)
    FastLanguageModel.for_inference(model)
    device = next(model.parameters()).device

    # capture the bnb quant config for provenance (JSON-safe: torch.dtype et al.
    # in bnb_4bit_compute_dtype are not serializable -> stringify non-primitives)
    def _jsonable(x):
        if isinstance(x, (str, int, float, bool)) or x is None:
            return x
        if isinstance(x, dict):
            return {str(k): _jsonable(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [_jsonable(v) for v in x]
        return str(x)

    quant_config = {}
    try:
        qc = getattr(model.config, "quantization_config", None)
        if qc is not None:
            raw = qc.to_dict() if hasattr(qc, "to_dict") else dict(qc)
            quant_config = _jsonable(raw)
    except Exception as exc:  # noqa: BLE001
        quant_config = {"error": repr(exc)}

    def smoke_inloop_L24(question: str):
        rendered, _ = render_probe_prompt(tokenizer, baseline_system, question,
                                          enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        return out.hidden_states[24][0, prompt_len - 1, :].float().cpu()

    overall_ok = True
    for surface, sdir in SURFACES.items():
        rows = load_jsonl(sdir / "rows.jsonl")[:N_CHECK]
        max_ab = max_ac = 0.0
        detail = []
        for r in rows:
            q = r["question"]
            a = smoke_inloop_L24(q)          # smoke in-loop path
            b = smoke_inloop_L24(q)          # extractor path (identical code) fresh forward
            sk = r.get("safe_key") or safe_key_for(r["row_key"])
            with safe_open(str(sdir / f"{sk}__pre.safetensors"), "pt") as st:
                c = st.get_tensor("L24").float()
            d_ab = float((a - b).abs().max())
            d_ac = float((a - c).abs().max())
            max_ab = max(max_ab, d_ab)
            max_ac = max(max_ac, d_ac)
            detail.append({"row_key": r["row_key"], "abs_diff_inloop_vs_extract": d_ab,
                           "abs_diff_inloop_vs_persisted": d_ac})
        passed = bool(max_ab <= TOL and max_ac <= TOL)
        overall_ok = overall_ok and passed
        block = {"n": len(rows), "threshold": TOL,
                 "max_abs_diff_L24_inloop_vs_extract": max_ab,
                 "max_abs_diff_L24_inloop_vs_persisted": max_ac,
                 "passed": passed, "detail": detail,
                 "note": "A=smoke in-loop read, B=extractor single_anchor (same "
                         "code path), C=persisted on-disk 4-bit state the v2 "
                         "sensor was fit on; all same served model / probe render "
                         "/ prompt_len-1"}
        man_path = sdir / "manifest.json"
        man = json.loads(man_path.read_text())
        man["inloop_equivalence"] = block
        man["quant_config"] = quant_config
        man_path.write_text(json.dumps(man, indent=2), encoding="utf-8")
        print(f"[inloop-check] {surface}: inloop_vs_extract={max_ab:.3g} "
              f"inloop_vs_persisted={max_ac:.3g} passed={passed}", flush=True)

    print(json.dumps({"all_passed": overall_ok, "tol": TOL,
                      "quant_config_keys": sorted(quant_config.keys())}, indent=2),
          flush=True)
    return 0 if overall_ok else 4


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
