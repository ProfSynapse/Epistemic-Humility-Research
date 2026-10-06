#!/usr/bin/env python3
"""Pre-sign check (lab-notebook tier), CPU only, in the label runtime (vLLM venv).

The label-path render without starting an engine: vLLM's own tokenizer factory
(vllm.tokenizers.get_tokenizer on the pinned snapshot, the object LLM.get_tokenizer
wraps) through EH backends.render_probe_prompt with probe.yaml's system prompt.
Token ids are the tokenizer's encode of the rendered text (the engine's text-prompt
path); engine-observed prompt_token_ids are a later exclusive-GPU smoke item.
Written because the engine smoke could not run on the shared GPU (NOTEBOOK).
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
sys.path.insert(0, str(REPO / "experiments/common/knowledge_probe"))
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from smoke_questions import QUESTIONS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import vllm
    from vllm.tokenizers import get_tokenizer

    pc = yaml.safe_load((CELL / "probe.yaml").read_text(encoding="utf-8"))
    tok = get_tokenizer(args.snapshot)
    rows, modes = [], set()
    for i, q in enumerate(QUESTIONS):
        text, mode = render_probe_prompt(tok, pc["prompt"]["system"], q, enable_thinking=False)
        modes.add(mode)
        ids_call = list(tok(text)["input_ids"])
        ids_enc = list(tok.encode(text))
        rows.append({"i": i, "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                     "prompt_token_ids": ids_call, "encode_equals_call": ids_enc == ids_call})
    res = {"check": "vllm_tokenizer_render", "vllm_version": vllm.__version__,
           "tokenizer_class": type(tok).__name__, "render_modes": sorted(m for m in modes if m), "rows": rows}
    Path(args.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}),
          "encode==call all:", all(r["encode_equals_call"] for r in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
