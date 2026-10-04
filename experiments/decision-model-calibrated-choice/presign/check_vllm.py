#!/usr/bin/env python3
"""Pre-sign check (lab-notebook tier): vLLM label-path smoke for the labeler.

Runs in the label runtime (WSL venv, vllm==0.27.1) with VLLM_BATCH_INVARIANT=1.
Uses EH's own render path (experiments/common/knowledge_probe/backends.py
render_probe_prompt) and probe.yaml's system prompt, on the 20 fixed non-PopQA
smoke questions. No scoring, no labels.

Records:
  render      sha256 of every rendered prompt + vLLM's prompt_token_ids
  greedy      completion token ids: batched order A, batched reversed, one-by-one
  sampled     n=8, T=1.0, top_p=0.9, fixed per-question seed, run twice
  invariance  greedy identical across the three regimes; sampled identical across runs

GPU use is capped (gpu_memory_utilization from --gpu-mem, default 0.30) because
the card is shared with a running training container; this is a check-only
override of probe.yaml's 0.90 and is recorded in the output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
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
    ap.add_argument("--gpu-mem", type=float, default=0.30)
    args = ap.parse_args()

    pc = yaml.safe_load((CELL / "probe.yaml").read_text(encoding="utf-8"))
    s = pc["sampling"]
    import vllm
    from vllm import LLM, SamplingParams

    t0 = time.time()
    llm = LLM(model=args.snapshot, dtype=pc["runtime"]["vllm"]["dtype"],
              gpu_memory_utilization=args.gpu_mem, max_model_len=pc["runtime"]["vllm"]["max_model_len"])
    load_s = time.time() - t0
    tok = llm.get_tokenizer()
    rendered, modes = [], set()
    for q in QUESTIONS:
        text, mode = render_probe_prompt(tok, pc["prompt"]["system"], q,
                                         enable_thinking=bool(pc["model"]["enable_thinking"]))
        rendered.append(text)
        modes.add(mode)

    greedy = SamplingParams(n=1, temperature=0.0, top_p=1.0, max_tokens=s["max_new_tokens"], seed=0)

    def run(prompts, params):
        outs = llm.generate(prompts, params, use_tqdm=False)
        return [(list(o.prompt_token_ids), [list(c.token_ids) for c in o.outputs]) for o in outs]

    idx = list(range(len(rendered)))
    a = run([rendered[i] for i in idx], greedy)
    b_rev = run([rendered[i] for i in reversed(idx)], greedy)[::-1]
    c_one = [run([rendered[i]], greedy)[0] for i in idx]
    greedy_ok = all(a[i][1] == b_rev[i][1] == c_one[i][1] for i in idx)
    greedy_diff = [i for i in idx if not (a[i][1] == b_rev[i][1] == c_one[i][1])]

    def sampled_run():
        return [run([rendered[i]], SamplingParams(n=8, temperature=s["temperature"], top_p=s["top_p"],
                                                  max_tokens=s["max_new_tokens"], seed=1000 + i))[0][1]
                for i in idx]

    s1, s2 = sampled_run(), sampled_run()
    sampled_ok = s1 == s2

    res = {
        "check": "vllm_label_path_smoke",
        "vllm_version": vllm.__version__,
        "env": {k: os.environ.get(k) for k in ("VLLM_BATCH_INVARIANT", "VLLM_WSL2_ENABLE_PIN_MEMORY")},
        "snapshot": args.snapshot,
        "gpu_memory_utilization_override": args.gpu_mem,
        "engine_load_seconds": round(load_s, 1),
        "render_modes": sorted(m for m in modes if m),
        "rows": [{"i": i, "prompt_sha256": hashlib.sha256(rendered[i].encode("utf-8")).hexdigest(),
                  "prompt_token_ids": a[i][0], "greedy_completion_ids": a[i][1][0]} for i in idx],
        "greedy_invariant_across_batch_orders": greedy_ok,
        "greedy_mismatch_rows": greedy_diff,
        "sampled_repeat_identical": sampled_ok,
        "prompt_ids_consistent_across_regimes": all(a[i][0] == b_rev[i][0] == c_one[i][0] for i in idx),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
