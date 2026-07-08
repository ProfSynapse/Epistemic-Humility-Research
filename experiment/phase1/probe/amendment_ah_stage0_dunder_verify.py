#!/usr/bin/env python3
"""Amendment AH Stage-0 (script 5) — D-under behavioral verification (GPU).

Pre-registered in
experiments/divergent-pool-own-readout/AMENDMENT.md (§4 step 5).

For every D-under candidate under the LOOSEST rule (L24 alone, band 0; from
score/dunder_candidates.jsonl), run greedy forced-best-guess generation and
grade correctness. verified-known = greedy answer is correct.

Forced-best-guess system prompt is VERBATIM from Amendment T
(amendment_t_correctness_readout_deployment_extract.SYSTEM_PROMPT, the locked
abstention-suppression method / AG census lineage). Rendering, decode, and
content-end logic mirror the AF/AG generation harness (raw base, no adapter,
greedy, max_new_tokens 96, enable_thinking False). Grading = scorers.is_correct
(Cheng port); candidate aliases are already scorers.normalize'd.

Only the loosest-rule set is generated; attrition to stricter rules/bands is
computed post-hoc from the per-candidate probe scores (already in the input),
so a single greedy pass covers every rule/band cell.

Writes:
  ah_stage0/verify/dunder_verified.jsonl   (per-candidate: answer, correct, scores)
  ah_stage0/verify/attrition.json          (candidates -> verified per rule/band)
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

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)
from amendment_t_correctness_readout_deployment_extract import (  # noqa: E402
    SYSTEM_PROMPT as FORCED_BEST_GUESS_PROMPT,
)

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_ROOT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"

LAYERS = ["L20", "L24", "L28"]
BANDS = [0.0, 0.5, 1.0, 2.0]


def load_cands(path: Path):
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    root = Path(args.root).resolve()
    cands = load_cands(root / "score" / "dunder_candidates.jsonl")
    out_dir = root / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    grid = json.loads((root / "score" / "divergence_grid.json").read_text())
    z = grid["score_sd"]

    model_name = args.base_model or MODEL_NAME
    config_payload = {
        "amendment": "AH", "stage": "stage0_dunder_verify",
        "base_model": model_name, "adapter": "NONE-raw-instruct-base",
        "model_tag": MODEL_TAG, "system_prompt": FORCED_BEST_GUESS_PROMPT,
        "abstention_suppression": "forced-best-guess-prompt (T lineage)",
        "enable_thinking": False, "max_new_tokens": args.max_new_tokens,
        "decode": "greedy", "grading": "scorers.is_correct (Cheng)",
        "n_candidates": len(cands),
    }
    config_sha = _config_sha(config_payload)

    print(f"[ah/verify] loading RAW base {model_name} ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    eos_for_gen = tokenizer.eos_token_id
    if isinstance(im_end, int) and im_end >= 0:
        eos_for_gen = ([tokenizer.eos_token_id, im_end]
                       if tokenizer.eos_token_id is not None else im_end)

    print(f"[ah/verify] D-under candidates to verify: {len(cands)}", flush=True)
    t0 = time.time()
    verified = []
    with (out_dir / "dunder_verified.jsonl").open("w", encoding="utf-8") as fh:
        for i, r in enumerate(cands):
            rendered, _mode = render_probe_prompt(
                tokenizer, FORCED_BEST_GUESS_PROMPT, r["question"],
                enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=args.max_new_tokens, do_sample=False,
                    num_beams=1, eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
            full_list = gen.sequences[0].tolist()
            new_ids = full_list[prompt_len:]
            answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
            refused = scorers.is_stated_confidence_refusal(answer_text)
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = (content_end is not None) and bool(answer_text) and not refused
            aliases = r.get("aliases", [])  # already normalized
            correct = bool(aliases) and scorers.is_correct(answer_text, aliases)
            rec = {
                "row_key": r["row_key"], "question": r["question"],
                "aliases": aliases, "source": r["source"],
                "answer_text": answer_text, "refused": refused,
                "answered": answered, "correct": correct,
                "score_L20": r["score_L20"], "score_L24": r["score_L24"],
                "score_L28": r["score_L28"], "fold_scores": r["fold_scores"],
                "config_sha": config_sha,
            }
            verified.append(rec)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if (i + 1) % 25 == 0 or (i + 1) == len(cands):
                el = time.time() - t0
                nc = sum(1 for v in verified if v["correct"])
                print(f"[ah/verify] {i+1}/{len(cands)} verified-known={nc} "
                      f"{el:.0f}s", flush=True)

    # Attrition: candidates -> verified (correct) per rule/band.
    # A candidate counts in a rule/band cell if its probe scores clear the band
    # on the D-under side (score < -band*z) under that rule's readout set.
    import numpy as np

    def qualifies(v, rule, b):
        if rule == "L24_alone":
            return v["score_L24"] < -b * z["L24"]
        if rule == "consensus_L20_L24_L28":
            return (v["score_L20"] < -b * z["L20"] and
                    v["score_L24"] < -b * z["L24"] and
                    v["score_L28"] < -b * z["L28"])
        if rule == "ensemble_unanimity_L24":
            return all(fs < -b * z["fold"] for fs in v["fold_scores"])
        raise ValueError(rule)

    attrition = {"n_candidates_generated": len(verified),
                 "n_answered": int(sum(v["answered"] for v in verified)),
                 "n_verified_known_total": int(sum(v["correct"] for v in verified)),
                 "rules": {}}
    for rule in ["L24_alone", "consensus_L20_L24_L28", "ensemble_unanimity_L24"]:
        cells = {}
        for b in BANDS:
            in_cell = [v for v in verified if qualifies(v, rule, b)]
            n_cand = len(in_cell)
            n_verified = sum(1 for v in in_cell if v["correct"])
            cells[f"{b}z"] = {"candidates": n_cand, "verified_known": n_verified}
        attrition["rules"][rule] = cells

    (out_dir / "attrition.json").write_text(json.dumps(attrition, indent=2),
                                            encoding="utf-8")
    print(json.dumps(attrition, indent=2), flush=True)
    runtime = time.time() - t0
    print(f"[ah/verify] DONE {len(verified)} in {runtime:.0f}s -> {out_dir}",
          flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--base-model", default=None)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
