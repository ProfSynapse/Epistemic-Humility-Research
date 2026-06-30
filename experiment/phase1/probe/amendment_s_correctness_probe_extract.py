#!/usr/bin/env python3
"""Amendment S — free-answer generation + dual-position hidden-state extraction (GPU).

Pre-registered in experiment/protocol/AMENDMENT-S-correctness-confidence-probe.md
(SIGNED 2026-06-30). Exploratory, single-model, single-seed; reported separately
from the locked PROTOCOL v0.3 matrix.

WHAT THIS DOES (Amendment S §3 procedure, steps 1-2):
  1. Free-answer generation. Greedy-decode ONE answer per question on the Qwen3-4B
     Instruct base (pre-abstention; answers freely) over a hard open-domain QA pool
     (PopQA long-tail + TriviaQA-gold). Grade each attempt correct/wrong vs gold
     aliases with the VERBATIM Cheng scorer (scorers.is_correct).
  2. Dual-position hidden-state extraction. Re-forward [prompt + generated answer]
     ONCE with output_hidden_states and capture the residual stream at BOTH read
     positions across all layers:
       pre-gen  = last prompt token = the add_generation_prompt anchor
                  (the cos-0.9998 faithful generation position from the Amendment R
                  / session 0029 render fix). Under causal attention this token's
                  state is identical whether or not the answer is appended, so one
                  forward of the full sequence yields a faithful pre-gen read.
       post-gen = last CONTENT token of the generated answer (trailing EOS / im_end
                  / pad trimmed) — the model has now SEEN its own answer.

The probe fit + gate scoring (§3 steps 3-4, §4 gates) is a SEPARATE CPU script
(amendment_s_correctness_probe_score.py) that reads this script's outputs.

OUTPUTS (under a gitignored model_tag subtree):
  <out_dir>/rows.jsonl                          one record per generated attempt
  <out_dir>/<safe_key>__pre.safetensors         {L0..L<N>} pre-gen vectors (fp32)
  <out_dir>/<safe_key>__post.safetensors        {L0..L<N>} post-gen vectors (fp32)
  <out_dir>/manifest.json                        run provenance + config

This is a NEW eval/extraction surface (no cached extraction is powered for
single-attempt correctness; abstention-trained arms answer only when ~94% right).
It loads the RAW instruct base (no adapter) on purpose. No training run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

# scorers + the shared render helper live alongside this script's siblings.
PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402  (from experiment/phase1/eval)
from backends import render_probe_prompt  # noqa: E402  (from experiment/phase1/probe)

# Answer-encouraging neutral system prompt. DELIBERATELY does NOT solicit
# abstention (unlike the eval DEFAULT_SYSTEM_PROMPT): Amendment S needs a surface
# where the model answers a lot AND errs a lot, so a wrong class exists. Recorded
# in the manifest so the generation surface is provenance-traceable.
SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question as concisely as "
    "possible with a direct factual answer."
)
MODEL_NAME = "unsloth/Qwen3-4B-bnb-4bit"
MODEL_TAG = "qwen3-4b-instruct"


def _config_sha(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]


# ---------------------------------------------------------------------------
# QA pool loading. Each item -> {row_key, dataset, question, aliases_norm}.
# aliases_norm are ALREADY normalized (scorers.normalize) so is_correct can be
# called directly. PopQA difficulty is ordered by s_pop ASC (long-tail first) to
# guarantee a wrong class; TriviaQA-gold supplies normalized_aliases verbatim.
# ---------------------------------------------------------------------------


def _as_list(value) -> list:
    """PopQA stores possible_answers / *_aliases as a JSON-ENCODED STRING, not a
    JSON list. Decode the string; pass real lists through; never iterate the raw
    string (that would yield per-character 'aliases' and false-positive matches).
    """
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return [value]
    return []


def load_popqa(path: Path, limit: int | None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            aliases = [scorers.normalize(str(a)) for a in _as_list(r.get("possible_answers"))]
            aliases = [a for a in aliases if a]
            if not aliases or not r.get("question"):
                continue
            rows.append({
                "row_key": f"popqa::{r['id']}",
                "dataset": "popqa",
                "question": r["question"],
                "aliases_norm": aliases,
                "s_pop": r.get("s_pop"),
            })
    # long-tail first (smaller s_pop = rarer entity = more likely wrong)
    rows.sort(key=lambda d: (d["s_pop"] if d["s_pop"] is not None else 1 << 30))
    return rows[:limit] if limit else rows


def load_triviaqa(path: Path, limit: int | None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            aliases = [a for a in r.get("normalized_aliases", []) if a]
            q = r.get("question_norm")
            if not aliases or not q:
                continue
            rows.append({
                "row_key": f"triviaqa::{r['tqa_question_id']}",
                "dataset": "triviaqa",
                "question": q,
                "aliases_norm": aliases,
                "s_pop": None,
            })
    return rows[:limit] if limit else rows


def build_pool(datasets_root: Path, which: list[str], per_dataset: int | None,
               seed: int) -> list[dict]:
    pool: list[dict] = []
    if "popqa" in which:
        pool += load_popqa(datasets_root / "popqa" / "test.jsonl", per_dataset)
    if "triviaqa" in which:
        pool += load_triviaqa(
            datasets_root / "triviaqa-rc-nocontext" / "cheng_test_gold.jsonl",
            per_dataset,
        )
    # Deterministic interleave so we do not exhaust one dataset before the other
    # when we stop early on reaching class targets.
    rng = random.Random(seed)
    rng.shuffle(pool)
    return pool


# ---------------------------------------------------------------------------
# Model + extraction.
# ---------------------------------------------------------------------------


def _content_end_index(seq_ids, prompt_len: int, special_ids: set[int]) -> int | None:
    """Index (into the full sequence) of the last generated CONTENT token.

    Trims trailing special tokens (eos / im_end / pad) from the generated tail.
    Returns None if the model generated no content token (empty answer).
    """
    end = len(seq_ids) - 1
    while end >= prompt_len and int(seq_ids[end]) in special_ids:
        end -= 1
    return end if end >= prompt_len else None


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    datasets_root = Path(args.datasets_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config_payload = {
        "amendment": "S",
        "model_name": MODEL_NAME,
        "model_tag": MODEL_TAG,
        "system_prompt": SYSTEM_PROMPT,
        "enable_thinking": False,
        "datasets": sorted(args.datasets),
        "max_new_tokens": args.max_new_tokens,
        "target_correct": args.target_correct,
        "target_wrong": args.target_wrong,
        "max_attempts": args.max_attempts,
        "seed": args.seed,
        "persist_dtype": "float32",
        "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-s] loading {MODEL_NAME} ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers  # hidden_states has n_layers+1 entries

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    # Qwen3 stops generation on <|im_end|>; treat it as a trailing special too.
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    eos_for_gen = tokenizer.eos_token_id
    if isinstance(im_end, int) and im_end >= 0:
        eos_for_gen = [tokenizer.eos_token_id, im_end] if tokenizer.eos_token_id is not None else im_end

    pool = build_pool(datasets_root, args.datasets, args.per_dataset, args.seed)
    print(f"[amendment-s] pool size={len(pool)}; "
          f"targets correct>={args.target_correct} wrong>={args.target_wrong}",
          flush=True)

    rows_path = out_dir / "rows.jsonl"
    n_correct = n_wrong = n_answered = n_refused = n_empty = 0
    written = 0

    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for item in pool:
            if (n_correct >= args.target_correct and n_wrong >= args.target_wrong):
                break
            if written >= args.max_attempts:
                break

            rendered, _mode = render_probe_prompt(
                tokenizer, SYSTEM_PROMPT, item["question"], enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])

            with torch.no_grad():
                gen = model.generate(
                    **enc,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    num_beams=1,
                    eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True,
                )
            full = gen.sequences[0]
            full_list = full.tolist()
            new_ids = full_list[prompt_len:]
            answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()

            refused = scorers.is_stated_confidence_refusal(answer_text)
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = (content_end is not None) and bool(answer_text) and not refused

            correct = (
                scorers.is_correct(answer_text, item["aliases_norm"])
                if answered else False
            )

            # Hidden-state extraction: ONE forward over [prompt + answer content].
            # Truncate trailing specials so post-gen reads the last semantic token.
            # If the answer is empty we still record the row (excluded from the fit)
            # but skip tensor extraction (no meaningful post-gen position).
            label = None
            if answered:
                seq_end = content_end  # last content token index in full sequence
                fwd_ids = full[: seq_end + 1].unsqueeze(0).to(device)
                attn = torch.ones_like(fwd_ids)
                with torch.no_grad():
                    out = model(input_ids=fwd_ids, attention_mask=attn,
                                output_hidden_states=True, use_cache=False)
                hs = out.hidden_states  # tuple len n_layers+1, each [1, seq, hidden]
                pre_pos = prompt_len - 1
                post_pos = seq_end
                pre_tensors = {
                    f"L{li}": hs[li][0, pre_pos, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                post_tensors = {
                    f"L{li}": hs[li][0, post_pos, :].float().cpu().contiguous()
                    for li in range(len(hs))
                }
                safe_key = item["row_key"].replace("::", "__").replace("|", "_")
                save_file(pre_tensors, str(out_dir / f"{safe_key}__pre.safetensors"))
                save_file(post_tensors, str(out_dir / f"{safe_key}__post.safetensors"))
                label = "correct" if correct else "wrong"
                if correct:
                    n_correct += 1
                else:
                    n_wrong += 1
                n_answered += 1
            else:
                if refused:
                    n_refused += 1
                else:
                    n_empty += 1

            rows_fh.write(json.dumps({
                "row_key": item["row_key"],
                "dataset": item["dataset"],
                "question": item["question"],
                "answer_text": answer_text,
                "aliases_norm": item["aliases_norm"],
                "answered": answered,
                "refused": refused,
                "correct": bool(correct) if answered else None,
                "label": label,  # 'correct'|'wrong'|None — None rows excluded from fit
                "prompt_len": prompt_len,
                "answer_tok_len": (content_end - prompt_len + 1) if content_end is not None else 0,
                "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 25 == 0:
                print(f"[amendment-s] attempts={written} answered={n_answered} "
                      f"correct={n_correct} wrong={n_wrong} refused={n_refused} "
                      f"empty={n_empty}", flush=True)

    manifest = {
        **config_payload,
        "config_sha": config_sha,
        "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size,
        "n_attempts": written,
        "n_answered": n_answered,
        "n_correct": n_correct,
        "n_wrong": n_wrong,
        "n_refused": n_refused,
        "n_empty": n_empty,
        "out_dir": str(out_dir),
        "positions": ["pre", "post"],
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[amendment-s] DONE answered={n_answered} "
          f"correct={n_correct} wrong={n_wrong} -> {out_dir}", flush=True)

    # Data-adequacy precondition (Amendment S §4): hard floor >=150/>=150.
    floor = args.adequacy_floor
    if n_correct < floor or n_wrong < floor:
        print(f"[amendment-s] WARNING: below data-adequacy floor "
              f"({floor}/{floor}); correct={n_correct} wrong={n_wrong}. "
              "This is a DATA-STAGE stop (pool more questions), NOT a probe verdict.",
              flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True,
                    help="output dir (gitignored model_tag subtree)")
    ap.add_argument("--datasets-root",
                    default=str(PROBE_DIR.parents[2] / "datasets"),
                    help="repo datasets/ root")
    ap.add_argument("--datasets", nargs="+", default=["popqa", "triviaqa"],
                    choices=["popqa", "triviaqa"])
    ap.add_argument("--per-dataset", type=int, default=None,
                    help="cap rows loaded per dataset before shuffle (None=all)")
    ap.add_argument("--target-correct", type=int, default=500)
    ap.add_argument("--target-wrong", type=int, default=500)
    ap.add_argument("--max-attempts", type=int, default=4000,
                    help="hard cap on generations regardless of class targets")
    ap.add_argument("--max-new-tokens", type=int, default=48)
    ap.add_argument("--adequacy-floor", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260630)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
