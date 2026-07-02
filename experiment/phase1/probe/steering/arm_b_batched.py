#!/usr/bin/env python3
"""Amendment AA — Arm B tuner-batched engine (throughput plan §4, steering follow-up).

DESIGN REFERENCE: docs/plans/generation-throughput-plan.md §4 ("Arm B needs the
probe score before injection → batched capture pass, then batched injected
generation") and the Amendment X extractor's established `--engine tuner-batched`
glue pattern (amendment_x_cross_model_extract.py): subprocess to the PUBLIC
Synaptic-Tuner CLI only (`tuner.py batch-generate` / `tuner.py batch-capture`,
pinned at db4f9a3cf7e8342bc1ddce337a36b82931dd3f39), token_ids-based capture
rows with per-row named positions, tensor paths read from capture.jsonl,
`--scratch-dir` for the local 9P lane, `--tuner-dir` override. Never imports
tuner internals; nothing Epistemic-specific is written into synaptic-tuner/.

Staged batch-pass design (mirrors run_arm_b.run_arm_b_cell phase-for-phase):

  position=early (4 generations/item):
    1. batch-capture  — pre-answer anchor read on every item's plain initial
                        prompt (token_ids + position = prompt_len-1, direction
                        layer only) -> real probe scores
    2. permute_scores — the SAME within-batch placebo permutation as the
                        sequential engine (same item set, same --seed)
    3. batch-generate — injected INITIAL passes, real + placebo (2N prompts,
                        note seeded into the think block exactly as sequential)
    4. batch-generate — plain REVISION passes for both variants (2N prompts)

  position=late (3 generations/item):
    1. batch-generate — ONE shared plain initial pass per item (N prompts)
    2. batch-capture  — post-answer read on [rendered initial prompt +
                        initial answer] (content-end scan, direction layer)
    3. permute_scores — same placebo permutation as sequential
    4. batch-generate — injected REVISION passes, real + placebo (2N prompts)

Render / note construction / grading / coherence checks / placebo semantics /
result-JSON schema are the sequential engine's own functions (imported, not
reimplemented); the ONLY thing this module swaps is the GPU inner loop.

SAMPLED-DECODE HONESTY (checked against tuner/cli/parser.py and
tuner/batch/engines/hf_batched.py at the db4f9a3 pin): `batch-generate` accepts
ONE GLOBAL `--seed` — the hf-batched engine applies `torch.manual_seed(seed)`
once per micro-batch chunk. There are NO per-row seeds, so batched sampling
does NOT reproduce the sequential per-item RNG streams: batched != sequential
per-row under sampled decode, BY DESIGN (we do not hack around it). Equivalence
is instead checked at the AGGREGATE level with spot_check_arm_b.py on a small
(~40-item) slice run under both engines: (a) rendered injected notes
byte-identical, (b) prompt token ids byte-identical on deterministic surfaces,
(c) metric-level agreement within binomial noise. See spot_check_arm_b.py's
docstring for the exact recipe. Any GPU spot-check run requires explicit user
launch approval.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from itertools import count
from pathlib import Path
from typing import Callable, Optional

STEERING_DIR = Path(__file__).resolve().parent
if str(STEERING_DIR) not in sys.path:
    sys.path.insert(0, str(STEERING_DIR))

from steering_common import (  # noqa: E402
    SYSTEM_PROMPT,
    _content_end_index,
    base_cell_payload,
    build_initial_messages,
    build_revision_messages,
    make_flat_record,
    probe_score_from_hidden,
    write_cell_json,
)
# The sequential engine's own note/permutation functions (identical semantics
# by construction — imported, never reimplemented). run_arm_b imports THIS
# module only lazily inside main(), so there is no import cycle.
from run_arm_b import make_note, permute_scores, summarize_arm_b  # noqa: E402


# ---------------------------------------------------------------------------
# Shared prompt rendering (single source of truth for the batched engine and
# the --emit-prompts recorder; mirrors run_arm_b.main's sequential generate_fn
# construction line-for-line — parity is covered by unit tests)
# ---------------------------------------------------------------------------

def make_pass_id(row_key: str, pass_name: str, variant: str) -> str:
    """Stable id for one generation request: '<row_key>::<pass>::<variant>'."""
    return f"{row_key}::{pass_name}::{variant}"


def render_pass_prompt(
    render: Callable[..., str],
    item: dict,
    initial_answer: Optional[str],
    pass_name: str,
    note: Optional[str],
) -> str:
    """Render one generation request's prompt EXACTLY as the sequential engine.

    `render(messages, enable_thinking=...)` is the runner's tokenizer-backed
    chat-template closure. A plain pass renders with enable_thinking=False; an
    injected pass renders with enable_thinking=True and opens the think block
    seeded with the note ("<think>\\n" + note + "\\n\\n"), matching
    cot_inject.build_think_prompt's layout — identical to run_arm_b.main's
    generate_fn.
    """
    if pass_name == "initial":
        messages = build_initial_messages(item["question"], SYSTEM_PROMPT)
    else:
        messages = build_revision_messages(
            item["question"], initial_answer or "", SYSTEM_PROMPT)
    if note is None:
        return render(messages, enable_thinking=False)
    return render(messages, enable_thinking=True) + "<think>\n" + note + "\n\n"


# ---------------------------------------------------------------------------
# Batched cell loop (pure orchestration — injected BATCH callables, fully
# unit-testable on CPU; mirrors run_arm_b.run_arm_b_cell's phases, ordering,
# placebo permutation, and per-record extras exactly)
# ---------------------------------------------------------------------------

def run_arm_b_cell_batched(
    items: list[dict],
    signal: str,
    position: str,
    probe_scores_batch_fn: Callable[[list[dict], Optional[list[str]]], list[float]],
    generate_batch_fn: Callable[[list[dict], str], list[str]],
    seed: int,
) -> dict[str, list[dict]]:
    """Batched mirror of run_arm_b.run_arm_b_cell (identical result structure).

    Parameters
    ----------
    items                 : eval pool (row_key, question, source, aliases_norm)
    signal, position      : as in run_arm_b_cell (validated identically)
    probe_scores_batch_fn : (items, initial_answers_or_None) -> list of probe
                            P(positive) scores aligned to items. Called with
                            None for 'early' (pre-answer anchor read) and with
                            the shared initial answers for 'late'.
    generate_batch_fn     : (requests, pass_name) -> list of generated texts
                            aligned to requests. Each request is a dict with
                            pass_id / item / initial_answer / pass_name /
                            variant / note (same fields the sequential
                            generate_fn receives, plus the pass_id).
    seed                  : placebo permutation seed — fed to the SAME
                            permute_scores(real_scores, seed) as sequential, so
                            the within-batch score permutation is identical
                            over the same item set.

    Returns {'real': [...], 'placebo': [...]} — flat records aligned
    item-for-item, byte-identical in structure to run_arm_b_cell's output given
    the same texts and scores.
    """
    if signal not in ("gate", "dial"):
        raise ValueError(f"signal must be 'gate' or 'dial', got {signal!r}")
    if position not in ("early", "late"):
        raise ValueError(f"position must be 'early' or 'late', got {position!r}")

    results: dict[str, list[dict]] = {"real": [], "placebo": []}

    if position == "early":
        # Phase 1 — real scores at the pre-answer anchor (batched capture).
        real_scores = [float(s) for s in probe_scores_batch_fn(items, None)]
        # Phase 2 — placebo: the SAME within-batch permutation as sequential.
        placebo_scores = permute_scores(real_scores, seed)
        # Phase 3a — injected INITIAL passes for both variants (one batch).
        init_reqs: list[dict] = []
        for i, item in enumerate(items):
            for variant, score in (("real", real_scores[i]),
                                   ("placebo", placebo_scores[i])):
                note = make_note(signal, score, position)
                init_reqs.append({
                    "pass_id": make_pass_id(item["row_key"], "initial", variant),
                    "item": item, "initial_answer": None,
                    "pass_name": "initial", "variant": variant, "note": note,
                })
        init_texts = generate_batch_fn(init_reqs, "initial")
        # Phase 3b — plain REVISION passes for both variants (one batch).
        rev_reqs = [{
            "pass_id": make_pass_id(r["item"]["row_key"], "revision", r["variant"]),
            "item": r["item"], "initial_answer": init_texts[j],
            "pass_name": "revision", "variant": r["variant"], "note": None,
        } for j, r in enumerate(init_reqs)]
        rev_texts = generate_batch_fn(rev_reqs, "revision")
        # Assemble in the sequential engine's record order.
        k = 0
        for i, item in enumerate(items):
            for variant, score in (("real", real_scores[i]),
                                   ("placebo", placebo_scores[i])):
                results[variant].append(make_flat_record(
                    item, init_texts[k], rev_texts[k],
                    extra={
                        "variant": variant,
                        "injected_score": float(score),
                        "real_score": float(real_scores[i]),
                        "placebo_score": float(placebo_scores[i]),
                        "injection_note": init_reqs[k]["note"],
                        "shared_initial": False,
                    },
                ))
                k += 1
        return results

    # position == "late"
    # Phase 1a — ONE shared plain initial pass per item (one batch).
    shared_reqs = [{
        "pass_id": make_pass_id(item["row_key"], "initial", "shared"),
        "item": item, "initial_answer": None,
        "pass_name": "initial", "variant": "shared", "note": None,
    } for item in items]
    shared_texts = generate_batch_fn(shared_reqs, "initial")
    # Phase 1b — real scores at the post-answer read (batched capture).
    real_scores = [float(s) for s in probe_scores_batch_fn(items, shared_texts)]
    # Phase 2 — placebo permutation (same as sequential).
    placebo_scores = permute_scores(real_scores, seed)
    # Phase 3 — injected REVISION passes for both variants (one batch).
    rev_reqs = []
    for i, item in enumerate(items):
        for variant, score in (("real", real_scores[i]),
                               ("placebo", placebo_scores[i])):
            note = make_note(signal, score, position)
            rev_reqs.append({
                "pass_id": make_pass_id(item["row_key"], "revision", variant),
                "item": item, "initial_answer": shared_texts[i] or "",
                "pass_name": "revision", "variant": variant, "note": note,
            })
    rev_texts = generate_batch_fn(rev_reqs, "revision")
    k = 0
    for i, item in enumerate(items):
        initial_text = shared_texts[i] or ""
        for variant, score in (("real", real_scores[i]),
                               ("placebo", placebo_scores[i])):
            results[variant].append(make_flat_record(
                item, initial_text, rev_texts[k],
                extra={
                    "variant": variant,
                    "injected_score": float(score),
                    "real_score": float(real_scores[i]),
                    "placebo_score": float(placebo_scores[i]),
                    "injection_note": rev_reqs[k]["note"],
                    "shared_initial": True,
                },
            ))
            k += 1
    return results


# ---------------------------------------------------------------------------
# --emit-prompts recording (both engines): one JSONL row per generation
# request with the rendered prompt + its token ids — the spot-check surface
# for checks (a) notes and (b) prompt token ids.
# ---------------------------------------------------------------------------

def make_emit_row(tokenizer, req: dict, prompt: str) -> dict:
    ids = None
    if tokenizer is not None:
        ids = [int(t) for t in tokenizer(prompt)["input_ids"]]
    return {
        "pass_id": req["pass_id"],
        "row_key": req["item"]["row_key"],
        "pass_name": req["pass_name"],
        "variant": req["variant"],
        "note": req["note"],
        "prompt_sha": hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16],
        "prompt_token_ids": ids,
    }


def write_emit_prompts(path: Path, rows: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def wrap_generate_for_emit(inner, render, tokenizer, emit_rows: list[dict]):
    """Wrap the SEQUENTIAL engine's generate_fn for --emit-prompts.

    Re-renders the request's prompt via render_pass_prompt (the same
    construction generate_fn performs internally — parity unit-tested), records
    the emit row, then delegates to the unmodified inner callable. Only active
    when --emit-prompts is set, so the default path is untouched.
    """
    def wrapped(item, initial_answer, pass_name, variant, note):
        prompt = render_pass_prompt(render, item, initial_answer, pass_name, note)
        emit_rows.append(make_emit_row(tokenizer, {
            "pass_id": make_pass_id(item["row_key"], pass_name, variant),
            "item": item, "pass_name": pass_name,
            "variant": variant, "note": note,
        }, prompt))
        return inner(item, initial_answer, pass_name, variant, note)
    return wrapped


# ---------------------------------------------------------------------------
# Tuner CLI glue (public CLI subprocess only — mirrors the Amendment X
# extractor's _tuner_repo_dir/_run_tuner/_read_jsonl pattern verbatim)
# ---------------------------------------------------------------------------

def _tuner_repo_dir() -> Path:
    """Locate the synaptic-tuner checkout that owns the batch CLI verbs.

    steering/ lives at experiment/phase1/probe/steering under the research
    repo; the submodule is at <repo-root>/synaptic-tuner. Overridable via
    --tuner-dir (cloud lane / uninitialized worktree submodule).
    """
    return STEERING_DIR.parents[3] / "synaptic-tuner"


def resolve_tuner_dir(args) -> Path:
    tuner_dir = (Path(args.tuner_dir).resolve() if args.tuner_dir
                 else _tuner_repo_dir())
    if not (tuner_dir / "tuner.py").exists():
        raise RuntimeError(
            f"tuner.py not found under {tuner_dir}; pass --tuner-dir to point "
            "at the synaptic-tuner checkout that exposes batch-generate/"
            "batch-capture (pinned db4f9a3, branch feature/batch-inference-engine).")
    return tuner_dir


def _run_tuner(tuner_dir: Path, verb: str, cli_args: list[str]) -> None:
    """Invoke `python tuner.py <verb> ...` as a subprocess (public CLI only).

    Streams the tuner's output; raises RuntimeError on non-zero exit so a
    failed batch verb stops the cell rather than persisting a partial result.
    """
    cmd = [sys.executable, "tuner.py", verb, *cli_args]
    print(f"[run_arm_b] $ (cwd={tuner_dir}) {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=str(tuner_dir))
    if proc.returncode != 0:
        raise RuntimeError(
            f"tuner {verb} exited {proc.returncode}; aborting before writing "
            "a partial cell JSON (see the tuner output above).")


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_generate_cli(args, prompts_path: Path, out_dir: Path,
                       max_new: int) -> list[str]:
    """CLI args for `tuner.py batch-generate` (flags per tuner/cli/parser.py
    at the db4f9a3 pin; the stop flag there is --stop-string, unused here —
    the chat surface terminates at EOS exactly as the sequential engine)."""
    cli = [
        "--prompts", str(prompts_path),
        "--model", args.model,
        "--out-dir", str(out_dir),
        "--engine", "hf-batched",
        "--batch-size", str(args.batch_size),
        "--max-new-tokens", str(max_new),
        "--seed", str(args.seed),
    ]
    if not args.greedy:
        # ONE global seed for the whole batched run (no per-row seeds — see the
        # module docstring's sampled-decode honesty note).
        cli += ["--do-sample", "--temperature", str(args.temperature),
                "--top-p", str(args.top_p)]
    return cli


def tuner_generate_requests(
    requests: list[dict],
    *,
    args,
    render,
    work_dir: Path,
    stage_tag: str,
    max_new: int,
    tuner_dir: Path,
    emit_rows: Optional[list[dict]] = None,
    tokenizer=None,
) -> list[str]:
    """One batched generation stage: render -> batch-generate -> texts.

    Returns completion texts aligned to `requests`, stripped exactly as the
    sequential engine strips its decoded generations.
    """
    prompts_path = work_dir / f"prompts_{stage_tag}.jsonl"
    with prompts_path.open("w", encoding="utf-8") as fh:
        for r in requests:
            prompt = render_pass_prompt(
                render, r["item"], r["initial_answer"], r["pass_name"], r["note"])
            fh.write(json.dumps({"id": r["pass_id"], "prompt": prompt},
                                ensure_ascii=False) + "\n")
            if emit_rows is not None:
                emit_rows.append(make_emit_row(tokenizer, r, prompt))

    gen_dir = work_dir / f"gen_{stage_tag}"
    _run_tuner(tuner_dir, "batch-generate",
               build_generate_cli(args, prompts_path, gen_dir, max_new))

    comp_by_id = {c["id"]: c for c in _read_jsonl(gen_dir / "completions.jsonl")}
    texts = []
    for r in requests:
        comp = comp_by_id.get(r["pass_id"])
        if comp is None:
            raise RuntimeError(
                f"batch-generate produced no completion for pass "
                f"{r['pass_id']!r}; refusing to assemble an incomplete cell.")
        # The sequential engine returns decode(...).strip(); mirror that.
        texts.append((comp.get("completion_text") or "").strip())
    return texts


def build_capture_rows(
    items: list[dict],
    initials: Optional[list[str]],
    *,
    render,
    tokenizer,
    special_ids: set[int],
) -> list[dict]:
    """token_ids + read position per item, EXACTLY as the sequential
    probe_score_fn computes them: pre-answer anchor = last prompt token
    (initials is None); post-answer = last content token of
    [rendered initial prompt + initial answer] via _content_end_index."""
    rows = []
    for i, item in enumerate(items):
        messages = build_initial_messages(item["question"], SYSTEM_PROMPT)
        if initials is None:
            rendered = render(messages, enable_thinking=False)
            ids = [int(t) for t in tokenizer(rendered)["input_ids"]]
            read_idx = len(ids) - 1
        else:
            rendered = render(messages, enable_thinking=False) + initials[i]
            ids = [int(t) for t in tokenizer(rendered)["input_ids"]]
            end = _content_end_index(ids, 0, special_ids)
            read_idx = end if end is not None else len(ids) - 1
        rows.append({
            "id": item["row_key"],
            "token_ids": ids,
            "positions": {"score": int(read_idx)},
        })
    return rows


def tuner_probe_scores(
    items: list[dict],
    initials: Optional[list[str]],
    *,
    args,
    render,
    tokenizer,
    special_ids: set[int],
    layer_idx: int,
    d_np,
    work_dir: Path,
    stage_tag: str,
    tuner_dir: Path,
) -> list[float]:
    """One batched capture stage: capture rows -> batch-capture -> probe scores.

    Captures ONLY the direction layer (hidden_states index = meta['best_layer'],
    the same index the sequential forward reads), float32 on disk, then maps
    each vector through probe_score_from_hidden — identical scoring math."""
    import numpy as np
    from safetensors.torch import load_file

    rows = build_capture_rows(items, initials, render=render,
                              tokenizer=tokenizer, special_ids=special_ids)
    rows_path = work_dir / f"capture_rows_{stage_tag}.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    cap_dir = work_dir / f"cap_{stage_tag}"
    cap_cli = [
        "--rows", str(rows_path),
        "--model", args.model,
        "--out-dir", str(cap_dir),
        "--engine", "hf-batched",
        "--layers", str(layer_idx),
        "--persist-dtype", "float32",
        "--batch-size", str(args.batch_size),
    ]
    _run_tuner(tuner_dir, "batch-capture", cap_cli)

    cap_by_id = {rec["id"]: rec for rec in _read_jsonl(cap_dir / "capture.jsonl")}
    scores = []
    d = np.asarray(d_np)
    for item in items:
        rec = cap_by_id.get(item["row_key"])
        if rec is None:
            raise RuntimeError(
                f"batch-capture produced no tensors for id "
                f"{item['row_key']!r}; refusing to assemble a torn cell.")
        loaded = load_file(str(cap_dir / rec["file"]))
        h = loaded[f"score__L{layer_idx}"].float().cpu().numpy()
        scores.append(probe_score_from_hidden(h, d))
    return scores


# ---------------------------------------------------------------------------
# Batched main (called from run_arm_b.main behind --engine tuner-batched).
# This process stays model-free: it renders prompts, drives the tuner
# subprocess (which owns the model), and assembles the identical cell JSON.
# ---------------------------------------------------------------------------

def main_tuner_batched(a, d_np, meta, items: list[dict], plan: dict) -> int:
    from transformers import AutoTokenizer

    tuner_dir = resolve_tuner_dir(a)
    tokenizer = AutoTokenizer.from_pretrained(a.model)
    layer_idx = meta["best_layer"]

    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)

    def _render(messages: list[dict], enable_thinking: bool) -> str:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=enable_thinking)

    emit_rows: Optional[list[dict]] = [] if a.emit_prompts else None

    work_root = Path(a.scratch_dir).resolve() if a.scratch_dir else None
    work_dir = Path(tempfile.mkdtemp(
        prefix="arm_b_tuner_work__",
        dir=(str(work_root) if work_root else None)))
    stage_counter = count()
    try:
        def generate_batch_fn(requests: list[dict], pass_name: str) -> list[str]:
            tag = f"{next(stage_counter):02d}_{pass_name}"
            max_new = (a.max_new_tokens_initial if pass_name == "initial"
                       else a.max_new_tokens_revision)
            return tuner_generate_requests(
                requests, args=a, render=_render, work_dir=work_dir,
                stage_tag=tag, max_new=max_new, tuner_dir=tuner_dir,
                emit_rows=emit_rows, tokenizer=tokenizer)

        def probe_scores_batch_fn(items_: list[dict],
                                  initials: Optional[list[str]]) -> list[float]:
            tag = f"{next(stage_counter):02d}_probe"
            return tuner_probe_scores(
                items_, initials, args=a, render=_render, tokenizer=tokenizer,
                special_ids=special_ids, layer_idx=layer_idx, d_np=d_np,
                work_dir=work_dir, stage_tag=tag, tuner_dir=tuner_dir)

        results = run_arm_b_cell_batched(
            items=items, signal=a.signal, position=a.position,
            probe_scores_batch_fn=probe_scores_batch_fn,
            generate_batch_fn=generate_batch_fn, seed=a.seed)
    finally:
        if getattr(a, "keep_batch_artifacts", False):
            print(f"[run_arm_b] batch artifacts kept at {work_dir}", flush=True)
        else:
            shutil.rmtree(work_dir, ignore_errors=True)

    if emit_rows is not None:
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
