#!/usr/bin/env python3
"""Diagnostics bundle cell 3 (TODO item 20 / AK Stage 1 read) — generation-time
position-sweep hidden-state extraction. Lab-notebook diagnostic (tier L): no
gates. Feeds the CPU-side doubt/caution-plane re-decomposition and the AK Stage 1
crystallization / doubt-trajectory curves.

WHY
---
The session-0035 off-axis finding (92-99% of the prime's write misses the
doubt/caution plane) was measured at the PRE-GEN ANCHOR only. Item 20 asks
whether that holds once the model is mid-generation. This cell extracts
GENERATION-TIME positions so analyze_displacement-style decomposition can be
re-run onto the doubt/caution axes at first-visible-token / mid-answer /
answer-end, not just the anchor. Same rows feed AK Stage 1's veto-crystallization
and doubt-trajectory readouts (AK §3.1).

METHOD (the Amendment S / R re-forward pattern, validated cos-0.9998 faithful)
-----------------------------------------------------------------------------
Per pool row:
  1. Greedy batch-1 generation (schema contract, enable_thinking=False,
     max_new_tokens=96) through the chosen checkpoint -> answer_text.
  2. Grade the emission: refused (scorers.is_stated_confidence_refusal) vs
     answered; for unanswerable rows an answered emission is a confabulation.
  3. Re-forward [prompt + generated content] ONCE with output_hidden_states and
     capture the residual stream at a SMALL set of positions:
       anchor      = prompt_len - 1        (the pre-gen baseline, for continuity)
       first_vis   = prompt_len            (first generated token)
       mid25/mid50/mid75 = answer-token quartile points
       answer_end  = last content token (trailing eos/im_end/pad trimmed)
  4. Persist one safetensors per (row, position): {L0..L<N>} fp32. rows.jsonl
     carries row_key/label/refused/answered/confab/answer_tok_len/positions
     (NO question text -> NO-LICENSE safe; answer_text kept for audit only when
     the pool is licensed — a flag controls it, default OFF).

POSITIONS are recorded as absolute sequence indices in rows.jsonl so the CPU
analysis knows exactly which token each tensor came from.

CHECKPOINT: designed for one checkpoint per pass (AK §3.1 runs both raw base and
grpo-v2; this bundle scopes to the AF/AG prime surface = the deployed
clean-SFT->GRPO-v2, refit axes per checkpoint per Amendment T). Pass the base +
adapter like amendment_ai_verdict_extract_gen.py.

SCOPE: ~300-600 rows, positions = 6 per row. Forward-only re-forward + one
greedy generation per row.

Usage (cloud wrapper fetches the pool from the private staging repo):
  python amendment_ak_gentime_positions_extract.py \
      --pool pool.jsonl --base-model <clean-sft-merged> \
      --adapter-repo <grpo-v2-lora> --adapter-revision <sha> \
      --out-dir <out>/data [--limit 600] [--keep-answer-text]
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

from amendment_s_correctness_probe_extract import (  # noqa: E402
    _config_sha, _content_end_index,
)
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, safe_key_for,
)

MAX_NEW_TOKENS = 96
DEGEN_RUN = 12


def load_jsonl(p: Path):
    return [json.loads(ln) for ln in Path(p).open(encoding="utf-8") if ln.strip()]


def is_degenerate(text: str) -> bool:
    if not text.strip():
        return True
    toks = text.split()
    run = 1
    for i in range(1, len(toks)):
        if toks[i] == toks[i - 1]:
            run += 1
            if run >= DEGEN_RUN:
                return True
        else:
            run = 1
    return False


def load_pool(pool_path: Path) -> list[dict]:
    rows = load_jsonl(pool_path)
    items = []
    for r in rows:
        label = r.get("label")
        if label is None:
            gold = r.get("gold_label")
            label = "unknown" if gold == "unknown" else "known"
        items.append({"row_key": r["row_key"], "question": r["question"],
                      "label": label, "source": r.get("source", "")})
    return items


def build_model(base_path, adapter_repo, adapter_revision):
    """Clean-SFT 4-bit serving config with the checkpoint's adapter applied
    (byte-identical load path to amendment_ai_verdict_extract_gen.build_model)."""
    from unsloth import FastLanguageModel
    from peft import PeftModel
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_path, max_seq_length=2048, dtype=None, load_in_4bit=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if adapter_repo:
        model = PeftModel.from_pretrained(model, adapter_repo,
                                          revision=adapter_revision)
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def answer_positions(prompt_len: int, content_end: int) -> dict[str, int]:
    """Absolute sequence indices for the position sweep. content_end is the last
    content token index in the full sequence (>= prompt_len for a non-empty
    answer). Quartile points are clamped into [first_vis, answer_end]."""
    first_vis = prompt_len
    ans_end = content_end
    span = max(ans_end - first_vis, 0)
    return {
        "anchor": prompt_len - 1,
        "first_vis": first_vis,
        "mid25": first_vis + span // 4,
        "mid50": first_vis + span // 2,
        "mid75": first_vis + (3 * span) // 4,
        "answer_end": ans_end,
    }


def run(args) -> int:
    import torch
    from safetensors.torch import save_file
    import scorers
    from backends import render_probe_prompt

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_system = load_baseline_system_prompt()
    pool = load_pool(Path(args.pool))
    if args.limit:
        pool = pool[: args.limit]

    config_payload = {
        "stage": "ak_gentime_positions", "base_model": args.base_model,
        "load_in_4bit": True, "adapter_repo": args.adapter_repo,
        "adapter_revision": args.adapter_revision,
        "baseline_system_prompt": baseline_system, "prime": "NONE-baseline-only",
        "enable_thinking": False, "decode": "greedy", "do_sample": False,
        "num_beams": 1, "max_new_tokens": MAX_NEW_TOKENS, "batch_size": 1,
        "positions": ["anchor", "first_vis", "mid25", "mid50", "mid75", "answer_end"],
        "reforward": "prompt+content, use_cache=False (Amendment S/R faithful)",
    }
    config_sha = _config_sha(config_payload)
    print(f"[ak-gentime] n={len(pool)} adapter={args.adapter_repo}@"
          f"{args.adapter_revision} config_sha={config_sha}", flush=True)

    model, tokenizer = build_model(args.base_model, args.adapter_repo,
                                   args.adapter_revision)
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers

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

    rows_path = out_dir / "rows.jsonl"
    counts = {"answered": 0, "refused": 0, "confab": 0, "empty": 0, "degenerate": 0}
    t0 = time.time()
    written = 0
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for item in pool:
            rendered, _mode = render_probe_prompt(
                tokenizer, baseline_system, item["question"], enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])
            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                    num_beams=1, eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
            full = gen.sequences[0]
            full_list = full.tolist()
            answer_text = tokenizer.decode(
                full_list[prompt_len:], skip_special_tokens=True).strip()
            refused = bool(scorers.is_stated_confidence_refusal(answer_text))
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = bool((content_end is not None) and bool(answer_text)
                            and not refused)
            degenerate = is_degenerate(answer_text)
            confab = bool(answered and item["label"] == "unknown")

            positions = None
            if answered:
                pos = answer_positions(prompt_len, content_end)
                fwd_ids = full[: content_end + 1].unsqueeze(0).to(device)
                attn = torch.ones_like(fwd_ids)
                with torch.no_grad():
                    out = model(input_ids=fwd_ids, attention_mask=attn,
                                output_hidden_states=True, use_cache=False)
                hs = out.hidden_states  # len n_layers+1, each [1, seq, hidden]
                sk = safe_key_for(item["row_key"])
                for pname, pidx in pos.items():
                    tensors = {f"L{li}": hs[li][0, pidx, :].float().cpu().contiguous()
                               for li in range(len(hs))}
                    save_file(tensors, str(out_dir / f"{sk}__{pname}.safetensors"))
                positions = pos
                counts["answered"] += 1
                counts["confab"] += int(confab)
            elif refused:
                counts["refused"] += 1
            else:
                counts["empty"] += 1
            counts["degenerate"] += int(degenerate)

            rec = {
                "row_key": item["row_key"], "safe_key": safe_key_for(item["row_key"]),
                "label": item["label"], "source": item["source"],
                "refused": refused, "answered": answered, "confab": confab,
                "degenerate": degenerate, "prompt_len": prompt_len,
                "answer_tok_len": (content_end - prompt_len + 1)
                                  if content_end is not None else 0,
                "positions": positions, "config_sha": config_sha,
            }
            if args.keep_answer_text:
                rec["answer_text"] = answer_text  # only on licensed pools
            rows_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 50 == 0 or written == len(pool):
                el = time.time() - t0
                print(f"[ak-gentime] {written}/{len(pool)} {el:.0f}s "
                      f"({written/el:.2f}/s) {counts}", flush=True)

    manifest = {**config_payload, "config_sha": config_sha, "n_layers": n_layers,
                "hidden_dim": model.config.hidden_size, "n_pool": len(pool),
                "n_written": written, "counts": counts,
                "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir)}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[ak-gentime] DONE {written} rows ({counts}) -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", required=True)
    ap.add_argument("--base-model", required=True)
    ap.add_argument("--adapter-repo", default=None)
    ap.add_argument("--adapter-revision", default=None)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--keep-answer-text", action="store_true",
                    help="record answer_text in rows.jsonl (ONLY for licensed "
                         "pools; NO-LICENSE FalseQA pools must omit it)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
