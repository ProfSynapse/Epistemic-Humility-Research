#!/usr/bin/env python3
"""Pre-sign check (lab-notebook tier): hidden-state index convention, Stage 0 vs Stage 1.

Runs INSIDE the Stage 1 image (unsloth digest, the analyze_confidence runtime),
with the synaptic-tuner submodule on sys.path. Loads the pointer decision
checkpoint exactly as analyze_confidence does (DecisionModel.load), DISABLES the
LoRA adapter (the decision model's torso == the base labeler), and runs the same
prompt token ids a smoke `mechinterp extract` captured, through the same module
call capture() uses: model._decoder()(input_ids, output_hidden_states=True).

For each smoke row it compares the extraction's anchor tensors (last prompt
token, every hidden-state index, from <extract_dir>/<row>__anchor.safetensors)
with the decoder states at the same token, reporting for every index i the
relative L2 error vs index i and vs indices i-1 / i+1. The convention holds iff
the count matches and every index's diagonal error is far below its
off-diagonal neighbours. A second pass with the adapter ENABLED records how far
the LoRA moves each layer (descriptive).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
TUNER = REPO / "synaptic-tuner"
for p in (TUNER / "Trainers/decision", TUNER):
    sys.path.insert(0, str(p))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--extract-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import numpy as np
    import torch
    import transformers
    from safetensors.numpy import load_file

    from decision_core.modeling import DecisionModel

    mfs = sorted(Path(args.extract_dir).glob("manifest_shard_*.json")) or [Path(args.extract_dir) / "manifest.json"]
    manifest = {"rows": [r for mf in mfs for r in json.loads(mf.read_text())["rows"] if r.get("answered")]}
    model = DecisionModel.load(args.checkpoint, device="cuda")
    tok = model.tokenizer
    sys.path.insert(0, str(REPO / "experiments/common/knowledge_probe"))
    sys.path.insert(0, str(HERE))
    from backends import render_probe_prompt
    from smoke_questions import QUESTIONS
    import yaml

    pc = yaml.safe_load((CELL / "probe.yaml").read_text(encoding="utf-8"))

    def rel(a, b):
        return float(np.linalg.norm(a - b) / max(np.linalg.norm(b), 1e-12))

    rows_out = []
    for rec in manifest["rows"]:
        i = int(rec["row_key"].split("-")[1])
        text, _ = render_probe_prompt(tok, pc["prompt"]["system"], QUESTIONS[i], enable_thinking=False)
        ids = tok(text, return_tensors="pt")["input_ids"]
        if ids.shape[1] != rec["prompt_len"]:
            raise SystemExit(f"row {i}: prompt_len {ids.shape[1]} != extraction {rec['prompt_len']}")
        ext = load_file(str(Path(args.extract_dir) / f"{rec['row_key']}__anchor.safetensors"))
        n_ext = len(ext)
        out = {}
        for adapter in ("disabled", "enabled"):
            with torch.no_grad():
                if adapter == "disabled":
                    with model.lm.disable_adapter():
                        hs = model._decoder()(input_ids=ids.cuda(), attention_mask=torch.ones_like(ids).cuda(),
                                              use_cache=False, output_hidden_states=True).hidden_states
                else:
                    hs = model._decoder()(input_ids=ids.cuda(), attention_mask=torch.ones_like(ids).cuda(),
                                          use_cache=False, output_hidden_states=True).hidden_states
            dec = [h[0, -1, :].float().cpu().numpy() for h in hs]
            per = []
            for li in range(len(dec)):
                e = ext.get(f"L{li}")
                if e is None:
                    continue
                e = e[0]
                per.append({"i": li, "diag": rel(dec[li], e),
                            "prev": rel(dec[li - 1], e) if li > 0 else None,
                            "next": rel(dec[li + 1], e) if li + 1 < len(dec) else None})
            out[adapter] = {"n_decoder_states": len(dec), "per_index": per}
        rows_out.append({"row_key": rec["row_key"], "n_extraction_states": n_ext, **out})

    dis = [r["disabled"] for r in rows_out]
    worst_diag = max(p["diag"] for d in dis for p in d["per_index"])
    best_off = min(min(x for x in (p["prev"], p["next"]) if x is not None) for d in dis for p in d["per_index"])
    count_ok = all(r["n_extraction_states"] == r["disabled"]["n_decoder_states"] for r in rows_out)
    res = {"check": "layer_index_convention", "transformers": transformers.__version__,
           "torch": torch.__version__, "checkpoint": args.checkpoint,
           "num_hidden_layers": int(model._inner().config.num_hidden_layers),
           "count_match": count_ok, "worst_diag_rel_err_adapter_disabled": worst_diag,
           "best_offdiag_rel_err_adapter_disabled": best_off,
           "convention_holds": bool(count_ok and worst_diag < 0.5 * best_off),
           "rows": rows_out}
    Path(args.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
