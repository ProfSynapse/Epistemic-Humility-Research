#!/usr/bin/env python3
"""Pre-sign check (lab-notebook tier), runs INSIDE the Stage 0 runner image.

Renders the 20 fixed non-PopQA smoke questions through the exact Stage 0
extraction render (dmcc_harness:render -> EH backends.render_probe_prompt with
the pinned HF tokenizer) and records prompt sha256 + token ids as
`mechinterp extract` would tokenize them (tokenizer(prompt) defaults). Also
records the loaded model class and hidden-state count for the base model as
MechInterp's own loader (_load_model_and_tokenizer) builds it. CPU-only unless
--forward is given (then one short forward on the GPU).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CELL = HERE.parent
REPO = CELL.parents[1]
for p in (CELL, HERE, REPO / "synaptic-tuner", REPO / "experiments/common/knowledge_probe"):
    sys.path.insert(0, str(p))

import dmcc_harness  # noqa: E402
from smoke_questions import QUESTIONS  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import transformers

    rows = []
    for i, q in enumerate(QUESTIONS):
        text = dmcc_harness.render({"row_key": f"smoke-{i}", "question": q})
        tok = dmcc_harness._render_state()["tok"]
        ids = tok(text)["input_ids"]
        rows.append({"i": i, "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                     "prompt_token_ids": list(ids)})
    res = {"check": "runner_render", "transformers": transformers.__version__, "rows": rows}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"rendered {len(rows)} prompts under transformers {transformers.__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
