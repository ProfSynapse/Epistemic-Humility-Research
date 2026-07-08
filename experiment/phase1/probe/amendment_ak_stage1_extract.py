#!/usr/bin/env python3
"""Amendment AK Stage 1 - commitment-point position-sweep extraction (GPU).

Pre-registered in experiments/commitment-point/AMENDMENT.md §3.1.
This is the GPU half: it produces the per-token hidden states the CPU scorer
projects onto the four AK axes (doubt trunk, caution, arm-B commitment, veto/
correctness) to build the crystallization curve (AK-G1), the doubt-trajectory
slope contrast (AK-G2), and the descriptive commitment-carry curve. All axis
fitting, projection, AUROC, slope-contrast and gate logic is CPU-side and post
hoc - this script writes states only, so it is checkpoint-agnostic (raw base or
grpo-v2 via the same code path).

POSITION SET captured per row (§3.1: "the anchor, each thinking-segment
boundary, first visible token, and every k-th answer token through answer end"):
  - anchor            : prompt_len-1 (the frozen pre-gen read the probes were
                        fit on; identical index to AH/AI single_anchor)
  - think_boundaries  : the token index of each </think> close tag, if the
                        generation contains a thinking segment. With the frozen
                        serving surface (enable_thinking=False, the AF/AG/AH/AI
                        surface all four axes were fit on) there is normally no
                        thinking segment, so this list is usually empty; it is
                        captured only when tags are actually emitted so the
                        script is robust to either render mode.
  - first_visible     : prompt_len (the first generated token)
  - answer_kth        : every --answer-stride-th generated content token
  - answer_end        : the last generated CONTENT token (_content_end_index)

Extraction mechanism (deterministic, resume-safe): greedy batch-1 generation
(do_sample=False, num_beams=1) records the emitted sequence; a SINGLE forward
pass over prompt+completion with output_hidden_states=True then slices the
target positions at the AK layers. This is byte-identical on re-run (parity with
amendment_ai_verdict_extract_gen.py's resume guarantee), avoids fragile
per-decode-step hook bookkeeping, and captures every layer/position in one pass.

Batching: generation stays batch-1 greedy so the emitted sequence (and
therefore the captured positions) is decode-identical to the arm-B / AH
generations. The Modal wrapper runs a numerics-smoke pre-stage (--limit 20) and
asserts this run's determinism spot-check passed before the full pool; the
frozen generation batch size (1) is recorded in the manifest. The
batch-1-vs-batch-N capture agreement contract is unit-tested in
tests/test_ak_stage1_extract.py.

Outputs (canonical checkout, gitignored; uploaded only to the PRIVATE staging
repo by the Modal wrapper):
  <out-dir>/rows.jsonl        per-row position map + labels + config_sha
                              (NO question text - safe_key only)
  <out-dir>/<safe_key>.safetensors
                              tensor keys "<L>@<pos_name>" (e.g. "L24@anchor",
                              "L24@answer_k0"), float32 cpu
  <out-dir>/manifest.json     config + counts + smoke result + frozen batch size
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
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)
from amendment_ah_stage0_extract import (  # noqa: E402
    load_baseline_system_prompt, safe_key_for,
)

# AK layer band: the arm-B sweep layers (commitment direction peaks L24-28) plus
# the veto/correctness read layers (Amendment S/T L20-22). The CPU scorer selects
# per-axis layers from this band; capturing the union keeps the GPU pass single.
DEFAULT_LAYERS = ("L16", "L20", "L24", "L28", "L34")
DEFAULT_ANSWER_STRIDE = 4
MAX_NEW_TOKENS = 96          # AH main-generate value (parity with AI verdict)
DEGEN_RUN = 12
SPOT_CHECK_N = 3


def load_jsonl(p: Path) -> list[dict]:
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


def build_model(base_path: str, adapter_repo: str | None,
                adapter_revision: str | None, load_in_4bit: bool):
    """Load the extraction model.

    Two surfaces, one code path:
      * raw base (arm-B native surface): base_path = unsloth/Qwen3-4B-bnb-4bit,
        adapter_repo None. Loaded via unsloth for parity with the AI/AL serving
        image (4-bit); the arm-B axes were fit on this base.
      * grpo-v2 (deployed, AK-G1 gate surface): base_path = clean-SFT merged
        base, adapter_repo = the trained grpo-v2 LoRA. Adapter applied on top.
    """
    from unsloth import FastLanguageModel  # import first (patches transformers)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_path, max_seq_length=2048, dtype=None,
        load_in_4bit=load_in_4bit)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    if adapter_repo:
        from peft import PeftModel
        model = PeftModel.from_pretrained(
            model, adapter_repo, revision=adapter_revision)
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def _think_close_indices(seq_ids: list[int], prompt_len: int,
                         close_ids: set[int]) -> list[int]:
    """Full-sequence indices of </think> close tokens in the generated span."""
    out = []
    for i in range(prompt_len, len(seq_ids)):
        if int(seq_ids[i]) in close_ids:
            out.append(i)
    return out


def _answer_positions(prompt_len: int, content_end: int | None,
                      stride: int) -> list[tuple[str, int]]:
    """(name, full-seq index) for first-visible + every stride-th + answer-end.

    Indices are clamped to [prompt_len, content_end]. Names are stable across
    runs: answer_k0 (first visible), answer_k1, ... and answer_end.
    """
    if content_end is None or content_end < prompt_len:
        # empty / all-special generation: only the first-visible slot exists
        return [("answer_k0", prompt_len)]
    positions: list[tuple[str, int]] = []
    k = 0
    idx = prompt_len
    while idx <= content_end:
        positions.append((f"answer_k{k}", idx))
        k += 1
        idx += stride
    if positions[-1][1] != content_end:
        positions.append(("answer_end", content_end))
    else:
        # rename the last stride hit to answer_end for a stable end key
        positions[-1] = ("answer_end", content_end)
    return positions


def _capture_positions(model, tokenizer, seq_ids: list[int], prompt_len: int,
                       layers: tuple[str, ...], answer_stride: int,
                       close_ids: set[int], special_ids: set[int], device):
    """One forward pass over the full sequence; slice AK positions at AK layers.

    Returns (vecs, pos_map) where vecs maps "<L>@<pos_name>" -> cpu float32
    tensor and pos_map maps pos_name -> full-sequence index (for provenance).
    """
    import torch

    ids = torch.tensor([seq_ids], device=device)
    attn = torch.ones_like(ids)
    with torch.no_grad():
        out = model(input_ids=ids, attention_mask=attn,
                    output_hidden_states=True, use_cache=False)
    hs = out.hidden_states  # tuple len n_layers+1, each (1, seq, hidden)

    content_end = _content_end_index(seq_ids, prompt_len, special_ids)
    pos_map: dict[str, int] = {"anchor": prompt_len - 1,
                               "first_visible": prompt_len}
    for j, ti in enumerate(_think_close_indices(seq_ids, prompt_len, close_ids)):
        pos_map[f"think_close{j}"] = ti
    for name, ti in _answer_positions(prompt_len, content_end, answer_stride):
        pos_map[name] = ti

    seq_len = len(seq_ids)
    vecs = {}
    for lk in layers:
        li = int(lk[1:])
        layer_h = hs[li][0]  # (seq, hidden)
        for pos_name, ti in pos_map.items():
            ti_c = max(0, min(ti, seq_len - 1))
            vecs[f"{lk}@{pos_name}"] = (
                layer_h[ti_c, :].float().cpu().contiguous())
    return vecs, pos_map, content_end


def run_extract(args) -> int:
    import torch
    from safetensors.torch import save_file
    from backends import render_probe_prompt

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline_system = load_baseline_system_prompt()
    pool = load_jsonl(Path(args.pool))
    if args.limit:
        pool = pool[: args.limit]
    layers = tuple(args.layers.split(",")) if args.layers else DEFAULT_LAYERS

    config_payload = {
        "amendment": "AK", "stage": "stage1_commitment_point_extract",
        "base_model": args.base_model, "load_in_4bit": bool(args.load_in_4bit),
        "adapter_repo": args.adapter_repo,
        "adapter_revision": args.adapter_revision,
        "checkpoint_tag": args.checkpoint_tag, "model_tag": MODEL_TAG,
        "baseline_system_prompt": baseline_system, "prime": "NONE-baseline-only",
        "enable_thinking": False, "anchor_position": "prompt_len-1",
        "decode": "greedy", "do_sample": False, "num_beams": 1,
        "max_new_tokens": MAX_NEW_TOKENS, "answer_stride": args.answer_stride,
        "persist_dtype": "float32", "generation_batch_size": 1,
        "layers": list(layers),
        "positions": "anchor,think_close*,first_visible,answer_k*,answer_end",
    }
    config_sha = _config_sha(config_payload)

    print(f"[ak/stage1] checkpoint={args.checkpoint_tag} n={len(pool)} "
          f"base={args.base_model} adapter={args.adapter_repo}"
          f"@{args.adapter_revision} layers={','.join(layers)} "
          f"config_sha={config_sha}", flush=True)

    model, tokenizer = build_model(args.base_model, args.adapter_repo,
                                   args.adapter_revision, args.load_in_4bit)
    device = next(model.parameters()).device
    n_layers = model.config.num_hidden_layers
    for lk in layers:
        if int(lk[1:]) > n_layers:
            raise RuntimeError(f"layer {lk} > n_layers {n_layers}")

    # special / thinking-close ids
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
    close_ids = set()
    think_close = tokenizer.convert_tokens_to_ids("</think>")
    if isinstance(think_close, int) and think_close >= 0:
        close_ids.add(think_close)

    def generate_seq(question: str):
        rendered, _mode = render_probe_prompt(
            tokenizer, baseline_system, question, enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        prompt_len = int(enc["input_ids"].shape[1])
        with torch.no_grad():
            gen = model.generate(
                **enc, max_new_tokens=MAX_NEW_TOKENS, do_sample=False,
                num_beams=1, eos_token_id=eos_for_gen,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                return_dict_in_generate=True)
        seq_ids = gen.sequences[0].tolist()
        return seq_ids, prompt_len

    # determinism spot check: re-capture L(first) @ anchor twice, must match.
    spot = {"performed": True, "n": min(SPOT_CHECK_N, len(pool)),
            "max_abs_diff": None, "threshold": 1e-4, "passed": None}
    max_d = 0.0
    for i in range(spot["n"]):
        seq_ids, plen = generate_seq(pool[i]["question"])
        v1, _, _ = _capture_positions(model, tokenizer, seq_ids, plen, layers,
                                      args.answer_stride, close_ids, special_ids,
                                      device)
        v2, _, _ = _capture_positions(model, tokenizer, seq_ids, plen, layers,
                                      args.answer_stride, close_ids, special_ids,
                                      device)
        k0 = f"{layers[0]}@anchor"
        max_d = max(max_d, float((v1[k0] - v2[k0]).abs().max()))
    spot["max_abs_diff"] = max_d
    spot["passed"] = bool(max_d <= spot["threshold"])
    print(f"[ak/stage1] determinism max_abs_diff={max_d:.4g} "
          f"passed={spot['passed']}", flush=True)

    # --- native resume: skip rows whose tensor exists + config_sha matches ---
    rows_path = out_dir / "rows.jsonl"
    done_keys = set()
    prior_rows = []
    if rows_path.exists() and not args.overwrite:
        for ln in rows_path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                pr = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if pr.get("config_sha") != config_sha:
                raise RuntimeError(
                    f"resume config_sha mismatch: {pr.get('config_sha')} "
                    f"!= {config_sha}")
            if not (out_dir / f"{pr['safe_key']}.safetensors").exists():
                continue
            done_keys.add(pr["row_key"])
            prior_rows.append(pr)
    if done_keys:
        print(f"[ak/stage1] RESUME: {len(done_keys)} present, "
              f"{len(pool) - len(done_keys)} remaining", flush=True)

    counts = {"answered_span": 0, "empty_span": 0, "degenerate": 0,
              "with_think": 0}
    for pr in prior_rows:
        counts["degenerate"] += int(bool(pr.get("degenerate")))
        counts["with_think"] += int(bool(pr.get("n_think_close")))

    t0 = time.time()
    written = len(done_keys)
    with rows_path.open("w", encoding="utf-8") as rows_fh:
        for pr in prior_rows:
            rows_fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
        rows_fh.flush()
        for item in pool:
            if item["row_key"] in done_keys:
                continue
            seq_ids, plen = generate_seq(item["question"])
            vecs, pos_map, content_end = _capture_positions(
                model, tokenizer, seq_ids, plen, layers, args.answer_stride,
                close_ids, special_ids, device)
            answer_text = tokenizer.decode(
                seq_ids[plen:], skip_special_tokens=True).strip()
            degenerate = is_degenerate(answer_text)
            n_gen = max(0, len(seq_ids) - plen)
            n_think = sum(1 for k in pos_map if k.startswith("think_close"))
            n_answer_pos = sum(1 for k in pos_map
                               if k.startswith("answer_k") or k == "answer_end")

            sk = safe_key_for(item["row_key"])
            save_file(vecs, str(out_dir / f"{sk}.safetensors"))
            rows_fh.write(json.dumps({
                "row_key": item["row_key"], "safe_key": sk,
                "label": item["label"],
                "confab_on_unanswerable": bool(item.get("confab_on_unanswerable")),
                "caution_dist_z": item.get("caution_dist_z"),
                "category_canon": item.get("category_canon", ""),
                "source": item.get("source", ""),
                "prompt_len": plen, "n_generated": n_gen,
                "content_end": content_end, "degenerate": degenerate,
                "n_think_close": n_think, "n_answer_positions": n_answer_pos,
                "position_index_map": pos_map,   # pos_name -> full-seq index
                "config_sha": config_sha,
                # NO question text, NO answer text (safe_key only)
            }, ensure_ascii=False) + "\n")
            rows_fh.flush()

            counts["degenerate"] += int(degenerate)
            counts["with_think"] += int(bool(n_think))
            counts["answered_span" if content_end is not None
                   else "empty_span"] += 1
            written += 1
            if written % 100 == 0 or written == len(pool):
                el = time.time() - t0
                print(f"[ak/stage1] {written}/{len(pool)} {el:.0f}s "
                      f"({written/max(el,1e-6):.2f}/s) {counts}", flush=True)

    manifest = {
        **config_payload, "config_sha": config_sha, "n_layers": n_layers,
        "hidden_dim": model.config.hidden_size, "n_pool": len(pool),
        "n_written": written, "counts": counts,
        "determinism_spot_check": spot,
        "runtime_sec": round(time.time() - t0, 1), "out_dir": str(out_dir),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                           encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items()
                      if k != "baseline_system_prompt"}, indent=2), flush=True)
    print(f"[ak/stage1] DONE {written} rows -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pool", required=True,
                    help="ak_stage1_pool.jsonl (private staging)")
    ap.add_argument("--base-model", default=MODEL_NAME,
                    help="raw base (default) or clean-SFT merged base for grpo-v2")
    ap.add_argument("--adapter-repo", default=None,
                    help="grpo-v2 trained LoRA (omit for the raw-base arm)")
    ap.add_argument("--adapter-revision", default=None)
    ap.add_argument("--checkpoint-tag", required=True,
                    choices=["raw-base", "grpo-v2"],
                    help="which AK Stage 1 checkpoint arm this run is")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--layers", default=",".join(DEFAULT_LAYERS))
    ap.add_argument("--answer-stride", type=int, default=DEFAULT_ANSWER_STRIDE)
    ap.add_argument("--load-in-4bit", action="store_true", default=True,
                    help="4-bit serving config (parity with AI/AL image)")
    ap.add_argument("--no-4bit", dest="load_in_4bit", action="store_false")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    return run_extract(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
