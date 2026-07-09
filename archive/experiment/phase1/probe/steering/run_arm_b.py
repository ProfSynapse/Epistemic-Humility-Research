#!/usr/bin/env python3
"""Amendment AA — Arm B orchestration: CoT-injection cells AA-5..AA-8.

SPEC: experiments/causal-confidence-steering/AMENDMENT.md (Tier-2,
DRAFT — NOT signed). NO GPU cell may launch until the amendment is signed AND
the user gives explicit launch approval naming the exact cells and lane.

IMPORT-TIME IS GPU-FREE. Model loading happens only inside main()'s guarded
path (never under --dry-run). The cell loop (run_arm_b_cell) takes injected
callables so it is fully unit-testable on CPU with synthetic fixtures.

Protocol per item (unified two-pass; injection via cot_inject.py notes):
  position=early -> the probe score is read at the pre-answer anchor and the
                    note is injected into the INITIAL pass's think block; the
                    revision pass is plain. Real and placebo variants each run
                    their own initial + revision passes.
  position=late  -> ONE shared plain initial pass per item; the probe score is
                    read post-answer; the note is injected into the REVISION
                    pass's think block for the real and placebo variants.
  position=final -> Amendment AB Revision 1 (think-end): ONE shared plain
                    initial pass per item (score read post-answer, as late)
                    PLUS one shared thinking-enabled plain revision-reasoning
                    pass; per variant the note is appended AFTER the shared
                    think draft as the final thought and the think block is
                    CLOSED, forcing the immediate answer. The reasoning
                    trajectory is byte-identical across variants; only the
                    final-thought score differs.

Placebo control (handled INTERNALLY, paired over the same items): identical
note structure with the real per-item scores PERMUTED across items
(within-batch permutation, seeded by --seed — the same control as
cot_inject.build_placebo_batch). "vs control" for every Arm B gate means
real vs placebo, never a no-injection baseline.

Output: one JSON per cell (per-item paired records + real/placebo summaries +
paired bootstrap 95% CIs, 2000 resamples).

Engines (docs/plans/generation-throughput-plan.md §4, steering follow-up):
the default --engine sequential is the original bs=1 loop, byte-identical to
the pre-batching harness. --engine tuner-batched replaces ONLY the GPU inner
loop with the synaptic-tuner PUBLIC CLI verbs (batch-generate/batch-capture;
see arm_b_batched.py for the staged design and the tuner pin). SAMPLED-DECODE
HONESTY: the tuner batch verbs take one GLOBAL --seed (no per-row seeds), so
batched sampling does NOT reproduce the sequential per-item RNG streams —
batched != sequential per-row under sampled decode. Equivalence is checked at
the AGGREGATE level with spot_check_arm_b.py on a ~40-item slice run under
both engines (rendered notes byte-identical, prompt token ids byte-identical
on deterministic surfaces, metrics within binomial noise); see its docstring
for the exact recipe. --emit-prompts records the spot-check surface from
either engine.

Example (Stage 1, AA-5 — DO NOT run without signed amendment + launch approval):
  python run_arm_b.py \
      --model unsloth/Qwen3.5-4B \
      --direction experiments/common/artifacts/two_signal_probe_directions/qwen3.5-4b/direction_gate.json \
      --signal gate --position early \
      --eval-pool gate --n-unknown 300 --n-known 300 \
      --gate-rows <selfaware rows.jsonl> \
      --seed 20260701 --device cuda --out results/aa5_gate_early.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Callable, Optional

from ab_templates import render_note as render_note_variant
from path_compat import datasets_dir as _default_datasets_dir
from cot_inject import InjectionConfig, extract_think_content
from steering_common import (
    N_BOOT_DEFAULT,
    SYSTEM_PROMPT,
    adequacy_check,
    base_cell_payload,
    build_eval_pool,
    build_initial_messages,
    build_revision_messages,
    compare_conditions,
    load_direction,
    make_flat_record,
    summarize_condition,
    write_cell_json,
)


# ---------------------------------------------------------------------------
# Placebo permutation (within-batch score permutation, seeded — the same
# control as cot_inject.build_placebo_batch, applied to paired two-pass runs)
# ---------------------------------------------------------------------------

def permute_scores(real_scores: list[float], seed: int) -> list[float]:
    placebo = list(real_scores)
    random.Random(seed).shuffle(placebo)
    return placebo


def make_note(signal: str, score: float, position: str,
              variant: str = "v0") -> str:
    """Render the injection note.

    variant='v0' is the registered AA telemetry template, rendered via
    cot_inject.InjectionConfig (byte-identical to the AA cells). Amendment AB
    variants v1-v3 render banded first-person prose via ab_templates.
    The runner's cell position maps directly onto the position of the pass
    the note lands in."""
    if variant == "v0":
        cfg = InjectionConfig(signal=signal, score=float(score), position=position)
        return cfg.render_note()
    return render_note_variant(variant, signal, float(score), position)


# ---------------------------------------------------------------------------
# Cell loop (pure orchestration — injected callables, unit-testable on CPU)
# ---------------------------------------------------------------------------

def run_arm_b_cell(
    items: list[dict],
    signal: str,
    position: str,
    probe_score_fn: Callable[[dict, Optional[str]], float],
    generate_fn: Callable[[dict, Optional[str], str, str, Optional[str]], str],
    seed: int,
    note_variant: str = "v0",
) -> dict[str, list[dict]]:
    """Run paired real + placebo two-pass generation over the same items.

    Parameters
    ----------
    items          : eval pool (row_key, question, source, aliases_norm)
    signal         : 'gate' | 'dial' (note wording + which score is rendered)
    position       : 'early' (note in initial pass) | 'late' (note in revision)
                     | 'final' (note as the closing thought of the revision
                     think block, after a SHARED thinking-enabled plain
                     reasoning pass — Amendment AB Revision 1)
    probe_score_fn : (item, initial_answer_or_None) -> probe P(positive).
                     Called with None for 'early' (pre-answer anchor read) and
                     with the shared initial answer for 'late'/'final'
                     (post-answer read).
    generate_fn    : (item, initial_answer_or_None, pass_name, variant, note)
                     -> generated text. pass_name in {'initial','revision',
                     'revision_think','revision_final'}, variant in
                     {'real','placebo','shared'}, note is the injection note
                     string or None (plain pass). For 'revision_final' the
                     shared think draft is passed as the keyword argument
                     `think_draft`. The callable owns prompt rendering +
                     think-block injection + decoding.
    seed           : placebo permutation seed (determinism contract).

    Returns
    -------
    {'real': [flat_record, ...], 'placebo': [flat_record, ...]}
    — both aligned item-for-item (paired).
    """
    if signal not in ("gate", "dial"):
        raise ValueError(f"signal must be 'gate' or 'dial', got {signal!r}")
    if position not in ("early", "late", "final"):
        raise ValueError(
            f"position must be 'early', 'late', or 'final', got {position!r}")

    # Phase 1 — real scores (and, for 'late'/'final', the shared plain initial
    # pass; for 'final', additionally the shared thinking-enabled plain
    # revision-reasoning pass whose think content is the frozen draft).
    shared_initials: list[Optional[str]] = [None] * len(items)
    shared_think_drafts: list[Optional[str]] = [None] * len(items)
    real_scores: list[float] = []
    if position == "early":
        for item in items:
            real_scores.append(float(probe_score_fn(item, None)))
    else:
        for i, item in enumerate(items):
            initial = generate_fn(item, None, "initial", "shared", None)
            shared_initials[i] = initial
            real_scores.append(float(probe_score_fn(item, initial)))
            if position == "final":
                think_full = generate_fn(item, initial, "revision_think",
                                         "shared", None)
                shared_think_drafts[i] = extract_think_content(think_full)

    # Phase 2 — placebo scores: within-batch permutation of the real scores.
    placebo_scores = permute_scores(real_scores, seed)

    # Phase 3 — paired generation.
    results: dict[str, list[dict]] = {"real": [], "placebo": []}
    for i, item in enumerate(items):
        for variant, score in (("real", real_scores[i]),
                               ("placebo", placebo_scores[i])):
            note = make_note(signal, score, position, note_variant)
            if position == "early":
                initial_text = generate_fn(item, None, "initial", variant, note)
                final_text = generate_fn(item, initial_text, "revision", variant, None)
            elif position == "late":
                initial_text = shared_initials[i] or ""
                final_text = generate_fn(item, initial_text, "revision", variant, note)
            else:  # final
                initial_text = shared_initials[i] or ""
                final_text = generate_fn(
                    item, initial_text, "revision_final", variant, note,
                    think_draft=shared_think_drafts[i] or "")
            results[variant].append(make_flat_record(
                item, initial_text, final_text,
                extra={
                    "variant": variant,
                    "note_variant": note_variant,
                    "injected_score": float(score),
                    "real_score": float(real_scores[i]),
                    "placebo_score": float(placebo_scores[i]),
                    "injection_note": note,
                    "shared_initial": position in ("late", "final"),
                    "shared_think_draft": position == "final",
                },
            ))
    return results


def summarize_arm_b(
    results: dict[str, list[dict]],
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = 20260701,
) -> dict:
    """Real vs placebo metric summaries + paired bootstrap contrasts.

    The placebo variant is the control (Amendment AA: never a no-injection
    baseline); adequacy floors are evaluated on the placebo condition."""
    for key in ("real", "placebo"):
        if key not in results:
            raise ValueError(f"summarize_arm_b requires the {key!r} condition")
    return {
        "real": summarize_condition(results["real"]),
        "placebo": summarize_condition(results["placebo"]),
        "real_vs_placebo": compare_conditions(
            results["real"], results["placebo"], n_boot=n_boot, seed=seed),
        "adequacy": adequacy_check(results["placebo"]),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True,
                    help="Model name/path (HF hub or local; thinking-enabled "
                         "family required for the think-block injection)")
    ap.add_argument("--direction", required=True, type=Path,
                    help="direction_<signal>.json (probe scoring source)")
    ap.add_argument("--signal", choices=["gate", "dial"], required=True)
    ap.add_argument("--position", choices=["early", "late", "final"], required=True,
                    help="early = note in initial pass; late = note at the top "
                         "of the revision think block; final = note as the "
                         "closing thought after a shared reasoning draft "
                         "(Amendment AB Revision 1)")
    ap.add_argument("--note-variant", choices=["v0", "v1", "v2", "v3"],
                    default="v0",
                    help="injection note template: v0 = registered AA telemetry "
                         "note; v1-v3 = Amendment AB banded first-person prose")
    ap.add_argument("--eval-pool", choices=["gate", "dial"], required=True)
    ap.add_argument("--n-unknown", type=int, default=300)
    ap.add_argument("--n-known", type=int, default=300)
    ap.add_argument("--n-answerable", type=int, default=500)
    ap.add_argument("--pool-file", type=Path, default=None,
                    help="JSONL pool override (CPU dry-run / tests)")
    ap.add_argument("--gate-rows", type=Path, default=None,
                    help="SelfAware frozen rows.jsonl (gate pool source)")
    ap.add_argument("--datasets-root", type=Path,
                    default=_default_datasets_dir(),
                    help="root for the PopQA/TriviaQA dial pool")
    ap.add_argument("--cell", default=None, help="cell tag, e.g. AA-5 (provenance)")
    ap.add_argument("--seed", type=int, default=20260701,
                    help="decode seed AND placebo permutation seed")
    ap.add_argument("--n-boot", type=int, default=N_BOOT_DEFAULT)
    ap.add_argument("--max-new-tokens-initial", type=int, default=128)
    ap.add_argument("--max-new-tokens-revision", type=int, default=96)
    ap.add_argument("--greedy", action="store_true",
                    help="greedy decode (default: sampled, per Amendment SR)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--device", default="cuda")
    # Throughput plan §4 (steering follow-up): batched engine. The default
    # 'sequential' is the original byte-identical bs=1 loop; 'tuner-batched'
    # swaps ONLY the GPU inner loop for the synaptic-tuner batch verbs
    # (public CLI subprocess; see arm_b_batched.py).
    ap.add_argument("--engine", choices=["sequential", "tuner-batched"],
                    default="sequential",
                    help="GPU inner-loop engine: sequential (default, byte-"
                         "identical bs=1) or tuner-batched (tuner batch verbs)")
    ap.add_argument("--batch-size", type=int, default=32,
                    help="micro-batch size for the tuner-batched engine "
                         "(auto-halves on CUDA OOM in the tuner); ignored by "
                         "the sequential engine")
    ap.add_argument("--tuner-dir", type=Path, default=None,
                    help="path to the synaptic-tuner checkout exposing batch-"
                         "generate/batch-capture (tuner-batched engine only); "
                         "default = <repo-root>/synaptic-tuner")
    ap.add_argument("--scratch-dir", type=Path, default=None,
                    help="fast local dir for the tuner-batched work dir "
                         "(9P write-stall fix); default = system temp")
    ap.add_argument("--keep-batch-artifacts", action="store_true",
                    help="keep the tuner-batched work dir (prompts/"
                         "completions/capture) instead of deleting it — the "
                         "spot-check inspection surface")
    ap.add_argument("--emit-prompts", type=Path, default=None,
                    help="write a JSONL of every generation request's rendered "
                         "prompt + prompt token ids (spot-check surface; works "
                         "with BOTH engines; default off = unchanged behavior)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="CPU-only: load direction, build pool, print the cell "
                         "plan; no model load, no generation")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    d_np, meta = load_direction(a.direction)

    items = build_eval_pool(
        eval_pool=a.eval_pool,
        n_unknown=a.n_unknown,
        n_known=a.n_known,
        n_answerable=a.n_answerable,
        seed=a.seed,
        pool_file=a.pool_file,
        datasets_root=a.datasets_root,
        gate_rows=a.gate_rows,
    )

    # Per item: early = 2 variants x 2 passes; late = 1 shared + 2 revisions;
    # final = 1 shared initial + 1 shared revision-think + 2 forced answers.
    per_item_gens = 3 if a.position == "late" else 4
    plan = {
        "arm": "B",
        "cell": a.cell,
        "signal": a.signal,
        "position": a.position,
        "note_variant": a.note_variant,
        "model": a.model,
        "direction": str(a.direction),
        "direction_layer": meta.get("best_layer"),
        "direction_signal": meta.get("signal"),
        "eval_pool": a.eval_pool,
        "n_items": len(items),
        "placebo": "internal paired within-batch score permutation",
        "seed": a.seed,
        "decode": ("greedy" if a.greedy
                   else f"sampled(temp={a.temperature},top_p={a.top_p})"),
        "max_new_tokens": {"initial": a.max_new_tokens_initial,
                           "revision": a.max_new_tokens_revision},
        "n_generations": len(items) * per_item_gens,
        "out": str(a.out),
    }
    if a.engine != "sequential":
        # Engine provenance ONLY when non-sequential (mirrors the Amendment X
        # extractor's manifest): the sequential plan — and therefore its
        # config_sha — is byte-identical to the pre-batching harness.
        plan["engine"] = a.engine
        plan["batch_size"] = a.batch_size
    print("[run_arm_b] cell plan:\n" + json.dumps(plan, indent=2), flush=True)
    if a.dry_run:
        print("[run_arm_b] dry-run: direction + pool OK; no model loaded.",
              flush=True)
        return 0

    if a.engine == "tuner-batched":
        # Batched engine: prompts/artifacts are handled in this process, the
        # MODEL lives inside the tuner subprocess (public CLI only). Same
        # signed-amendment + explicit-launch-approval requirement as below.
        from arm_b_batched import main_tuner_batched
        return main_tuner_batched(a, d_np, meta, items, plan)

    # ------------------------------------------------------------------
    # GPU path (signed amendment + explicit user launch approval required)
    # ------------------------------------------------------------------
    import numpy as np
    import torch
    import transformers as _tf

    from steering_common import _content_end_index, probe_score_from_hidden
    from confidence_steer import load_model_and_tokenizer

    _tf.set_seed(a.seed)
    torch.manual_seed(a.seed)

    print(f"[run_arm_b] loading model {a.model} ...", flush=True)
    model, tokenizer = load_model_and_tokenizer(a.model, device=a.device)
    device = next(model.parameters()).device
    layer_idx = meta["best_layer"]

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)

    def _render(messages: list[dict], enable_thinking: bool) -> str:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=enable_thinking)

    def _generate(prompt: str, max_new: int) -> str:
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        gen_kw = dict(max_new_tokens=max_new, num_beams=1,
                      pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
        if a.greedy:
            gen_kw.update(do_sample=False)
        else:
            gen_kw.update(do_sample=True, temperature=a.temperature, top_p=a.top_p)
        with torch.no_grad():
            out = model.generate(**enc, **gen_kw)
        return tokenizer.decode(out[0][enc["input_ids"].shape[1]:],
                                skip_special_tokens=True).strip()

    def generate_fn(item: dict, initial_answer: Optional[str], pass_name: str,
                    variant: str, note: Optional[str],
                    think_draft: Optional[str] = None) -> str:
        if pass_name == "initial":
            messages = build_initial_messages(item["question"], SYSTEM_PROMPT)
            max_new = a.max_new_tokens_initial
        else:
            messages = build_revision_messages(
                item["question"], initial_answer or "", SYSTEM_PROMPT)
            max_new = a.max_new_tokens_revision
        if pass_name == "revision_think":
            # Shared thinking-enabled PLAIN reasoning pass (position=final):
            # the model re-reasons with no note; the think content becomes the
            # frozen draft shared verbatim by the real and placebo variants.
            return _generate(_render(messages, enable_thinking=True), max_new)
        if pass_name == "revision_final":
            # Think-end injection (Amendment AB Revision 1): shared draft +
            # note as the final thought, block CLOSED, matching
            # cot_inject.build_think_prompt(position='final'); the model must
            # answer immediately.
            base = _render(messages, enable_thinking=True)
            prompt = (base + "<think>\n" + (think_draft or "") + "\n\n"
                      + (note or "") + "\n</think>\n")
            return _generate(prompt, max_new)
        if note is None:
            return _generate(_render(messages, enable_thinking=False), max_new)
        # Injected pass: open the think block and seed it with the rendered
        # note (make_note = cot_inject.InjectionConfig.render_note), matching
        # cot_inject.build_think_prompt's layout ("<think>\n" + note + "\n\n");
        # the model continues reasoning from the injection point.
        base = _render(messages, enable_thinking=True)
        prompt = base + "<think>\n" + note + "\n\n"
        return _generate(prompt, max_new)

    def probe_score_fn(item: dict, initial_answer: Optional[str]) -> float:
        """Direction-layer read: pre-answer anchor (early) or last content
        token of [prompt + initial answer] (late)."""
        if initial_answer is None:
            messages = build_initial_messages(item["question"], SYSTEM_PROMPT)
            rendered = _render(messages, enable_thinking=False)
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            read_idx = enc["input_ids"].shape[1] - 1
            ids = enc["input_ids"]
        else:
            messages = build_initial_messages(item["question"], SYSTEM_PROMPT)
            rendered = _render(messages, enable_thinking=False) + initial_answer
            enc = tokenizer(rendered, return_tensors="pt").to(device)
            ids = enc["input_ids"]
            seq = ids[0].tolist()
            end = _content_end_index(seq, 0, special_ids)
            read_idx = end if end is not None else len(seq) - 1
        attn = torch.ones_like(ids)
        with torch.no_grad():
            out = model(input_ids=ids, attention_mask=attn,
                        output_hidden_states=True, use_cache=False)
        h = out.hidden_states[layer_idx][0, read_idx, :].float().cpu().numpy()
        return probe_score_from_hidden(h, np.asarray(d_np))

    emit_rows: Optional[list] = [] if a.emit_prompts else None
    if emit_rows is not None:
        # Opt-in spot-check surface: record every generation request's rendered
        # prompt + token ids around the UNMODIFIED generate_fn (default off).
        from arm_b_batched import wrap_generate_for_emit
        generate_fn = wrap_generate_for_emit(generate_fn, _render, tokenizer,
                                             emit_rows)

    results = run_arm_b_cell(
        items=items,
        signal=a.signal,
        position=a.position,
        probe_score_fn=probe_score_fn,
        generate_fn=generate_fn,
        seed=a.seed,
        note_variant=a.note_variant,
    )

    if emit_rows is not None:
        from arm_b_batched import write_emit_prompts
        write_emit_prompts(Path(a.emit_prompts), emit_rows)
        print(f"[run_arm_b] emitted {len(emit_rows)} prompt records -> "
              f"{a.emit_prompts}", flush=True)

    summary = summarize_arm_b(results, n_boot=a.n_boot, seed=a.seed)
    payload = base_cell_payload(
        arm="B", cell=a.cell, signal=a.signal, position=a.position,
        model=a.model, direction_meta=meta, eval_pool=a.eval_pool,
        seed=a.seed, n_items=len(items), config_extra=plan,
    )
    payload["items"] = results
    payload["summary"] = summary
    out = write_cell_json(a.out, payload)
    print(f"[run_arm_b] wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
