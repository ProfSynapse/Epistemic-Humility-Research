#!/usr/bin/env python3
"""Amendment X — cross-SIZE RAW-base mixed-pool generation + dual-position extraction.

Pre-registered in experiment/protocol/AMENDMENT-X-cross-model-size-sweep.md.
Exploratory, multi-model (one Qwen3 family), single-seed; reported separately from
PROTOCOL v0.3.

THE QUESTION (§2 H_X): is the training-free two-signal readout validated on Qwen3-4B
(Amendments S + W) a SIZE-general property of the Qwen3 instruct family, or a 4B
artifact? This script is the per-model GPU pass; run once per size (1.7B / 8B / 14B).

ONE mixed-pool generation pass on the RAW instruct base (NO adapter, S's
answer-encouraging system prompt VERBATIM) yields all three signal classes at once:
  - PopQA/TriviaQA ANSWERABLE, graded vs gold aliases -> correct / wrong   (DIAL, X-G2)
  - SelfAware-KNOWN, answered                          -> known_answered   (gate + control)
  - SelfAware-UNKNOWN, answered                        -> hallucination    (VETO, X-G3)
The SelfAware known-vs-unknown pre-gen anchor IS the gate (X-G1), faithfully
replicating W-G2 within-SelfAware; the answerable correct/wrong post-gen surface IS
the dial, applied cold to the hallucinations for the veto. This combines the S
(answerable) and W (SelfAware) surfaces of the 4B run into a single per-model pass.

Reuses W's raw-base load + S's grading/prompt/helpers + V's mixed-pool idea; the
`<|im_end|>` handling is guarded so non-Qwen families fall back to plain EOS. The
ONLY per-model knob is --base-model. Persists (gitignored model_tag subtree) for every
ANSWERED row: rows.jsonl + <safe_key>__{pre,post}.safetensors + manifest.json.
No training run.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
# RAW-base surface + helpers VERBATIM from Amendment S (the dial source on 4B).
from amendment_s_correctness_probe_extract import (  # noqa: E402
    SYSTEM_PROMPT,
    MODEL_NAME,
    _config_sha,
    _content_end_index,
    build_pool,
)
# SelfAware pool loader VERBATIM from Amendment U.
from amendment_u_unified_extract import load_selfaware_pool  # noqa: E402


def _safe_model_tag(model_name: str) -> str:
    """unsloth/Qwen3-8B-bnb-4bit -> qwen3-8b-bnb-4bit (a filesystem-safe tag)."""
    return model_name.split("/")[-1].lower()


def build_mixed_pool(datasets_root, gate_rows, n_answerable, seed):
    """PopQA/TriviaQA answerable (graded) + SelfAware known + SelfAware unknown.

    Three sources in one pool so a single generation pass yields the dial
    (answerable correct/wrong), the gate (SelfAware known vs unknown at the prompt
    anchor), and the veto target (SelfAware-unknown hallucinations).
    """
    answerable = build_pool(datasets_root, ["popqa", "triviaqa"], None, seed)[:n_answerable]
    for it in answerable:
        it["source"] = "answerable"
    selfaware = load_selfaware_pool(gate_rows, seed)
    for it in selfaware:
        it["source"] = ("selfaware_known" if it["label"] == "known"
                        else "selfaware_unknown")
    pool = answerable + selfaware
    random.Random(seed).shuffle(pool)
    return pool


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from safetensors.torch import save_file

    model_name = args.base_model
    model_tag = _safe_model_tag(model_name)
    gate_rows = Path(args.gate_rows).resolve()
    datasets_root = Path(args.datasets_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config_payload = {
        "amendment": "X",
        "base_model": model_name,
        "adapter": "NONE-raw-instruct-base",
        "checkpoint": f"raw {model_name} (no adapter)",
        "model_tag": model_tag,
        "system_prompt": SYSTEM_PROMPT,
        "abstention_suppression": "NONE-base-is-pre-abstention",
        "pool_sources": ["popqa", "triviaqa", "selfaware_known", "selfaware_unknown"],
        "gate_rows_source": str(gate_rows),
        "enable_thinking": False,
        "n_answerable": args.n_answerable,
        "max_new_tokens": args.max_new_tokens,
        "max_attempts": args.max_attempts,
        "seed": args.seed,
        "persist_dtype": "float32",
        "decode": "greedy",
    }
    config_sha = _config_sha(config_payload)

    print(f"[amendment-x] loading RAW base {model_name} (no adapter) ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Backward-compatible loader: Qwen3 (and any text-only CausalLM) loads via the
    # first path unchanged; multimodal families (Gemma 4, Qwen 3.5) fall back to
    # the image-text-to-text / vision2seq auto-classes, from which we still read
    # the text backbone's hidden states. NO behavior change for X's Qwen3 sizes.
    import transformers as _tf
    # transformers 5.x renamed the load kwarg torch_dtype -> dtype.
    _major = int(_tf.__version__.split(".")[0])
    _dtype_kw = "dtype" if _major >= 5 else "torch_dtype"
    load_kw = {_dtype_kw: torch.bfloat16, "device_map": "cuda"}
    model = None
    last_err = None
    _classes = ["AutoModelForCausalLM"]
    for _name in ("AutoModelForImageTextToText", "AutoModelForVision2Seq"):
        if hasattr(_tf, _name):
            _classes.append(_name)
    for _cls_name in _classes:
        try:
            import transformers as _tf
            _Cls = getattr(_tf, _cls_name)
            model = _Cls.from_pretrained(model_name, **load_kw)
            print(f"[amendment-x] loaded via {_cls_name}", flush=True)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"[amendment-x] {_cls_name} load failed: {type(e).__name__}: "
                  f"{str(e)[:200]}", flush=True)
    if model is None:
        raise RuntimeError(
            f"could not load {model_name} via any of {_classes}: {last_err}")
    model.eval()
    device = next(model.parameters()).device

    def _text_cfg(m):
        # multimodal configs nest the LM hyperparams under text_config
        return getattr(m.config, "text_config", m.config)

    _tcfg = _text_cfg(model)
    n_layers = getattr(_tcfg, "num_hidden_layers", None)
    if n_layers is None:
        n_layers = getattr(model.config, "num_hidden_layers")

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

    pool = build_mixed_pool(datasets_root, gate_rows, args.n_answerable, args.seed)
    n_ans = sum(1 for p in pool if p["source"] == "answerable")
    n_known = sum(1 for p in pool if p["source"] == "selfaware_known")
    n_unknown = sum(1 for p in pool if p["source"] == "selfaware_unknown")
    print(f"[amendment-x] {model_tag} pool size={len(pool)} "
          f"(answerable={n_ans} sa_known={n_known} sa_unknown={n_unknown})", flush=True)

    rows_path = out_dir / "rows.jsonl"
    n_answered = n_refused = n_empty = 0
    n_correct = n_wrong = n_halluc = n_known_answered = 0
    written = 0

    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for item in pool:
            if written >= args.max_attempts:
                break
            rendered, _mode = render_probe_prompt(
                tokenizer, SYSTEM_PROMPT, item["question"], enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])

            with torch.no_grad():
                gen = model.generate(
                    **enc, max_new_tokens=args.max_new_tokens, do_sample=False,
                    num_beams=1, eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
            full = gen.sequences[0]
            full_list = full.tolist()
            answer_text = tokenizer.decode(
                full_list[prompt_len:], skip_special_tokens=True).strip()

            refused = scorers.is_stated_confidence_refusal(answer_text)
            content_end = _content_end_index(full_list, prompt_len, special_ids)
            answered = (content_end is not None) and bool(answer_text) and not refused

            correct = None
            outcome = None
            if answered:
                source = item["source"]
                if source == "answerable":
                    correct = bool(scorers.is_correct(answer_text, item["aliases_norm"]))
                    outcome = "correct" if correct else "wrong"
                    n_correct += correct
                    n_wrong += (not correct)
                elif source == "selfaware_known":
                    outcome = "known_answered"
                    n_known_answered += 1
                else:  # selfaware_unknown
                    outcome = "hallucination"
                    n_halluc += 1
                seq_end = content_end
                fwd_ids = full[: seq_end + 1].unsqueeze(0).to(device)
                attn = torch.ones_like(fwd_ids)
                with torch.no_grad():
                    out = model(input_ids=fwd_ids, attention_mask=attn,
                                output_hidden_states=True, use_cache=False)
                hs = out.hidden_states
                if hs is None or len(hs) != n_layers + 1:
                    raise RuntimeError(
                        f"hidden_states shape mismatch: got "
                        f"{None if hs is None else len(hs)} layers, expected "
                        f"{n_layers + 1} (n_layers+1). Wrong model wrapper for "
                        f"{model_name}? Aborting before persisting garbage.")
                pre_tensors = {f"L{li}": hs[li][0, prompt_len - 1, :].float().cpu().contiguous()
                               for li in range(len(hs))}
                post_tensors = {f"L{li}": hs[li][0, seq_end, :].float().cpu().contiguous()
                                for li in range(len(hs))}
                safe_key = item["row_key"].replace("::", "__").replace("|", "_")
                save_file(pre_tensors, str(out_dir / f"{safe_key}__pre.safetensors"))
                save_file(post_tensors, str(out_dir / f"{safe_key}__post.safetensors"))
                n_answered += 1
            else:
                if refused:
                    n_refused += 1
                else:
                    n_empty += 1

            rows_fh.write(json.dumps({
                "row_key": item["row_key"], "dataset": item["dataset"],
                "question": item["question"], "source": item["source"],
                "answer_text": answer_text, "answered": answered, "refused": refused,
                "correct": correct, "outcome": outcome, "prompt_len": prompt_len,
                "answer_tok_len": (content_end - prompt_len + 1) if content_end is not None else 0,
                "config_sha": config_sha,
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()
            written += 1
            if written % 50 == 0:
                print(f"[amendment-x] {model_tag} attempts={written} answered={n_answered} "
                      f"correct={n_correct} wrong={n_wrong} halluc={n_halluc} "
                      f"known_ans={n_known_answered} refused={n_refused}", flush=True)

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": getattr(_tcfg, "hidden_size",
                              getattr(model.config, "hidden_size", None)),
        "n_pool": len(pool),
        "n_attempts": written, "n_answered": n_answered, "n_correct": n_correct,
        "n_wrong": n_wrong, "n_hallucination": n_halluc,
        "n_known_answered": n_known_answered, "n_refused": n_refused, "n_empty": n_empty,
        "out_dir": str(out_dir), "positions": ["pre", "post"],
        "tensor_layer_keys": f"L0..L{n_layers}",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"\n[amendment-x] {model_tag} DONE answered={n_answered} correct={n_correct} "
          f"wrong={n_wrong} halluc={n_halluc} known_ans={n_known_answered} -> {out_dir}",
          flush=True)

    if n_wrong < args.wrong_floor or n_halluc < args.hallucination_floor:
        print(f"[amendment-x] WARNING: below adequacy floor "
              f"(wrong>={args.wrong_floor} AND halluc>={args.hallucination_floor}); "
              f"got wrong={n_wrong} halluc={n_halluc}. Raw bases are pre-abstention and "
              "should answer freely, so a shortfall is a DATA-STAGE stop for THIS model, "
              "NOT a probe verdict.", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True,
                    help="output dir (gitignored model_tag subtree)")
    ap.add_argument("--base-model", required=True,
                    help="raw Instruct base, e.g. unsloth/Qwen3-8B-bnb-4bit; NO adapter")
    ap.add_argument("--gate-rows", required=True,
                    help="SelfAware gate extraction rows.jsonl (frozen known/unknown source)")
    ap.add_argument("--datasets-root", default=str(PROBE_DIR.parents[2] / "datasets"))
    ap.add_argument("--n-answerable", type=int, default=2000,
                    help="answerable PopQA/TriviaQA cap in the pool")
    ap.add_argument("--max-attempts", type=int, default=3000)
    ap.add_argument("--max-new-tokens", type=int, default=48)
    ap.add_argument("--wrong-floor", type=int, default=30)
    ap.add_argument("--hallucination-floor", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260630)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
