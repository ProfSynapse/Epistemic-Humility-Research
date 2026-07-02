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

AMENDMENT Y ADDITION (backward-compatible, default OFF via --base-mode): a
pretrain-only base-model prompting surface. Pretrain-only bases (gpt2-xl,
pythia-2.8b, Llama-2-7B, OLMo-2-7B, and the Arm A bases) mostly ship no chat
template, so the chat/system-prompt render path cannot run them. With --base-mode
the script renders a FIXED handcrafted 5-shot trivia QA completion block (see
_BASE_MODE_FEWSHOT; those exemplars are hand-written and deliberately NOT drawn
from PopQA/TriviaQA/SelfAware, per the leakage rule) and parses the answer as the
first line of the plain completion. When --base-mode is OFF the render, parse, and
config_sha are byte-identical to the X/Z/SR chat-surface cells.
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


# ---------------------------------------------------------------------------
# Amendment Y base-mode prompting surface (default OFF; §6 of AMENDMENT-Y).
#
# Pretrain-only base models (gpt2-xl, pythia-2.8b, Llama-2-7B, OLMo-2-7B, and the
# modern Arm A bases) mostly ship NO chat template, so the instruct render path
# (render_probe_prompt -> apply_chat_template) cannot run them. Base-mode replaces
# that surface with a FIXED few-shot QA completion block: a handcrafted 5-shot
# trivia prefix followed by the target question and a bare "A:" answer cue, then
# plain completion parsed at the first line.
#
# LEAKAGE RULE: these five demonstration QA pairs are hand-written here and are
# deliberately NOT drawn from the PopQA, TriviaQA, or SelfAware evaluation pools,
# so no evaluation item can appear as an in-context exemplar. They are generic
# world-knowledge facts chosen to be unambiguous and short.
_BASE_MODE_FEWSHOT: tuple[tuple[str, str], ...] = (
    ("What is the largest planet in our solar system?", "Jupiter"),
    ("How many sides does a hexagon have?", "Six"),
    ("What is the chemical symbol for gold?", "Au"),
    ("In what year did the Second World War end?", "1945"),
    ("What is the tallest mountain on Earth?", "Mount Everest"),
)


def build_base_mode_prompt(question: str) -> str:
    """Render the fixed k-shot QA completion block for one target question.

    Format is a plain completion surface (no chat template, no system prompt):
    each exemplar is "Q: <question>\\nA: <answer>\\n\\n", repeated for the five
    frozen exemplars, then the target as "Q: <question>\\nA:" with a trailing
    space so the model completes the answer inline. The continuation is parsed as
    the FIRST LINE after this cue (see _first_line_content_end).
    """
    block = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in _BASE_MODE_FEWSHOT)
    return f"{block}Q: {question}\nA:"


def base_mode_kshot_sha() -> str:
    """Stable sha of the exact rendered k-shot exemplar block (answer-cue prefix
    only, target-independent) so config_sha changes when base-mode is on and a
    run record can prove which prompting surface a cell used."""
    import hashlib
    block = "".join(f"Q: {q}\nA: {a}\n\n" for q, a in _BASE_MODE_FEWSHOT)
    return hashlib.sha256(block.encode("utf-8")).hexdigest()[:16]


def _first_line_content_end(tokenizer, seq_ids, prompt_len: int,
                            special_ids: set[int]) -> int | None:
    """Index (into the full sequence) of the last CONTENT token of the FIRST LINE
    of the base-mode continuation.

    Base-mode completions babble past the answer (further "Q:/A:" pairs, prose),
    so the post-gen read must stop at the first newline of the continuation rather
    than at the whole generation's content end (_content_end_index's job for the
    chat surface). A newline can live inside a multi-character token (byte-level
    tokenizers like GPT-2 encode "\\n" as its own token, but SentencePiece merges
    can bury it), so we decode the generated tail token-by-token and stop at the
    FIRST token whose incremental decode introduces a newline. The boundary token
    itself (the one carrying the newline) is excluded from the first line; then we
    trim trailing specials from what remains. Returns None if the first line has
    no content token (empty answer).
    """
    n = len(seq_ids)
    # Walk the generated continuation; the newline may be introduced mid-token, so
    # decode incrementally and detect the first token that adds a "\n" to the run.
    end = n - 1
    prev = ""
    for i in range(prompt_len, n):
        cur = tokenizer.decode(seq_ids[prompt_len:i + 1], skip_special_tokens=True)
        added = cur[len(prev):]
        if "\n" in added:
            end = i - 1  # exclude the token that carries the newline
            break
        prev = cur
    while end >= prompt_len and int(seq_ids[end]) in special_ids:
        end -= 1
    return end if end >= prompt_len else None


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
        "system_prompt": (None if args.base_mode else SYSTEM_PROMPT),
        "abstention_suppression": "NONE-base-is-pre-abstention",
        "pool_sources": ["popqa", "triviaqa", "selfaware_known", "selfaware_unknown"],
        "gate_rows_source": str(gate_rows),
        "enable_thinking": False,
        "n_answerable": args.n_answerable,
        "max_new_tokens": args.max_new_tokens,
        "max_attempts": args.max_attempts,
        "seed": args.seed,
        "persist_dtype": "float32",
        "decode": (f"sampled(temp={args.temperature},top_p={args.top_p})"
                   if args.do_sample else "greedy"),
    }
    if args.base_mode:
        # Amendment Y base-mode surface (§6): no chat template, fixed k-shot QA
        # completion block. Record base_mode + a sha of the exact exemplar block
        # so config_sha differs from the chat-surface X/Z/SR cells and a run record
        # can prove which prompting surface produced a given extraction.
        config_payload["base_mode"] = True
        config_payload["kshot_sha"] = base_mode_kshot_sha()
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
    # Pretrain-only bases (GPT-2) ship no pad token; generation needs one. Fall
    # back to EOS for padding without mutating the special-id set (EOS already in
    # special_ids). No effect on Qwen3 (pad_token_id already set), so X/Z/SR are
    # unchanged. pad_token_id is read via `tokenizer.pad_token_id or eos` below.
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    # Seed the generation RNG per run so sampled decoding (Amendment SR) is a
    # reproducible independent draw. No effect on greedy runs (do_sample=False),
    # so X/Z remain byte-for-byte reproducible from this script.
    if args.do_sample:
        import transformers as _tf_seed
        _tf_seed.set_seed(args.seed)
        torch.manual_seed(args.seed)

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
            if args.base_mode:
                rendered = build_base_mode_prompt(item["question"])
            else:
                rendered, _mode = render_probe_prompt(
                    tokenizer, SYSTEM_PROMPT, item["question"], enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            prompt_len = int(enc["input_ids"].shape[1])

            with torch.no_grad():
                gen_kw = dict(
                    max_new_tokens=args.max_new_tokens, num_beams=1,
                    eos_token_id=eos_for_gen,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                    return_dict_in_generate=True)
                if args.do_sample:
                    gen_kw.update(do_sample=True, temperature=args.temperature,
                                  top_p=args.top_p)
                else:
                    gen_kw.update(do_sample=False)
                gen = model.generate(**enc, **gen_kw)
            full = gen.sequences[0]
            full_list = full.tolist()
            if args.base_mode:
                # Base-mode: parse the answer as the FIRST LINE of the completion
                # (strip, cut at first newline); trailing babble after the newline
                # is discarded and NOT read into the post-gen position.
                cont = tokenizer.decode(
                    full_list[prompt_len:], skip_special_tokens=True)
                answer_text = cont.split("\n", 1)[0].strip()
                content_end = _first_line_content_end(
                    tokenizer, full_list, prompt_len, special_ids)
            else:
                answer_text = tokenizer.decode(
                    full_list[prompt_len:], skip_special_tokens=True).strip()
                content_end = _content_end_index(full_list, prompt_len, special_ids)

            refused = scorers.is_stated_confidence_refusal(answer_text)
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
    # Amendment Y: pretrain-only base-model surface. DEFAULT OFF; when off the
    # render/parse path is byte-identical to X/Z/SR. When on, swaps the chat
    # template for a fixed k-shot QA completion block and first-line parsing.
    ap.add_argument("--base-mode", action="store_true",
                    help="Amendment Y base-mode: fixed k-shot QA completion "
                         "surface for pretrain-only bases with no chat template; "
                         "default off = chat-template surface (X/Z/SR)")
    # Amendment SR: sampled-decode seed-robustness. Defaults preserve greedy X/Z.
    ap.add_argument("--do-sample", action="store_true",
                    help="sampled decoding (Amendment SR); default off = greedy (X/Z)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
