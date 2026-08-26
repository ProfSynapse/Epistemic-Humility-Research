#!/usr/bin/env python3
"""Dial token-logprob T-deployed confirmatory -- fresh self-consistent
generation (GPU + CPU), gated confirmation at adequate power.

Registered in experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md.
Verbatim reuse of the experiments/dial-logprob-baseline-v3/lp_v3_harness.py
machinery (AMENDMENT.md "Design"): v3's T arm (t_deployed_descriptive)
recorded a data-stage stop at the LP3-G0 power floor (710 answered < 1,000)
under its verbatim-inherited 4,000-attempt cap. This cell reruns the SAME
single-pass self-consistent capture on the SAME deployed checkpoint at a
registered attempt cap (12,000, sized so the power floor is reachable) and
promotes the T-side comparison from descriptive-only to the gated primary
(LT-G1). No v3 file is modified; this module is a parameterized copy, single
arm.

CAPABILITY-CHECK FINDING (v3 NOTEBOOK.md 2026-08-13, carried unchanged): the
pinned vllm==0.27.1 returns generated token IDs (`CompletionOutput.token_ids`)
and per-token logprobs (`SamplingParams(logprobs=0)` -> `CompletionOutput.
logprobs`) directly from a normal generate() call -- certain, standard. It
does NOT expose per-token hidden states at an arbitrary intermediate layer
from that same call: the only hidden-state mechanism in this version
(`extract_hidden_states`) is a speculative-decoding/EAGLE-draft-model-training
method requiring a speculative_config + draft model config + KV-transfer
connector + file-based retrieval, architecturally unrelated to a simple
per-request readout, and nowhere near the batched-generation reference doc's
required bridge validation. The AMENDMENT's REGISTERED FALLBACK therefore
applies: a teacher-forced HF transformers forward pass over each row's
captured token IDs (prompt + generated, verbatim, never re-tokenized), at the
arm's pinned dial layer, executed in the SAME pinned stack/venv as the vLLM
generation (see cell.yaml `engine` block).

SINGLE ARM (t_deployed_confirmatory), THREE PHASES:

  1. GENERATE (GPU, vLLM). Build the arm's prompt pool via `build_pool`
     (imported UNCHANGED from amendment_s_correctness_probe_extract.py -- the
     SAME import the T-side extractor family always uses, keeping this cell
     on the identical pool convention as v3's T arm). Render each prompt with
     the arm's system prompt via the SHARED `render_probe_prompt` helper
     (thinking-off pinned and self-checked). ONE batched (chunked, resumable)
     vLLM generate() call per chunk captures token IDs and per-token logprobs
     together (`capture_row`). Score correctness fresh with the source cells'
     own scorer (`scorers.is_correct` / `is_stated_confidence_refusal`,
     imported unchanged). `select_attempted` then replays the T extractor's
     own sequential early-stop selection rule (stop once
     n_correct>=target_correct AND n_wrong>=target_wrong, or max_attempts)
     POST HOC over the fully-generated batch, reproducing IDENTICAL selection
     semantics to the original per-item loop without needing sequential GPU
     calls.

  2. EXTRACT (GPU, HF teacher-forced fallback). For each attempted, answered
     row: forward EXACTLY `prompt_token_ids + completion_token_ids[:span_len]`
     (the phase-1 capture's own arrays, nothing regenerated, nothing
     re-tokenized) through the SAME checkpoint loaded via HF+PEFT, and save
     the dial layer's final-position hidden state as a safetensors shard in
     the `{safe_key}__post.safetensors` layout `load_position_layers` (reused
     unchanged from amendment_s_correctness_probe_score.py) expects.

  3. SCORE (CPU-only, no model). `score_arm_t` implements LT-G0 (a) capture
     integrity -- the teacher-forced pass's input ids are asserted, per row,
     to equal the phase-1 capture's own prompt+span ids; (b) coverage --
     every attempted item has a recorded disposition; (c) power floor
     (>=1000 answered rows, unchanged from v3's LP3-G0(c) -- the cap moved,
     not the floor); (d) instrument sanity (fresh T dial OOF AUROC >= 0.75, a
     sanity bound, NOT a reproduction target -- there is nothing to
     reproduce here, same as v3). Only if all four hold does it compute the
     dial-vs-logprob paired-bootstrap margin (`paired_bootstrap_delta`,
     reused unchanged) and evaluate LT-G1 (this cell's arm is gated, not
     descriptive-only like v3's T arm).

Real GPU phases are NOT invoked by the harness build task. `--dry-run`
resolves every real input (pool source files, checkpoint/adapter paths, the
scorer/dial-refit modules) with no model and no GPU. The generation and
extraction phases are resumable (append+flush, chunked) under gitignored
analysis/; only aggregate JSON is ever eligible for commit
(analysis-committed/) -- see cell.yaml `containment`.

CLI (`main`):
  --dry-run                        CPU-only input resolution; exit 0/2.
  --arm ID --phase generate        vLLM generation only (GPU).
  --arm ID --phase extract         HF teacher-forced extraction only (GPU);
                                    requires phase generate's runlog on disk.
  --arm ID --phase score           CPU-only scoring; requires both runlogs.
  --arm ID --phase all (default)   all three phases in one process. NOTE:
                                    this holds the vLLM engine and (later) the
                                    HF extraction model in the SAME process;
                                    best-effort GPU memory release runs
                                    between phases (del + gc.collect +
                                    torch.cuda.empty_cache), but a real launch
                                    should prefer separate `--phase generate`
                                    then `--phase extract` process invocations
                                    for guaranteed release -- v3's NOTEBOOK.md
                                    flagged tighter headroom on this exact
                                    checkpoint (T arm), not resolved by this
                                    build (no arm was run).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
READOUTS_DIR = REPO_ROOT / "experiments" / "common" / "readouts"
if str(READOUTS_DIR) not in sys.path:
    sys.path.insert(0, str(READOUTS_DIR))

from path_compat import knowledge_probe_dir, locked_eval_dir  # noqa: E402
from amendment_s_correctness_probe_score import (  # noqa: E402
    oof_probe,
    load_position_layers,
    paired_bootstrap_delta,
)
# Reused BY IMPORT, never retyped: same pool and same content-end trimming as
# v3's T arm (AMENDMENT.md "Design" -- "Verbatim reuse of the v3 instrument").
# S_SYSTEM_PROMPT is not imported: this cell has no S arm.
from amendment_s_correctness_probe_extract import (  # noqa: E402
    _content_end_index,
    build_pool,
)
from amendment_t_correctness_readout_deployment_extract import (  # noqa: E402
    SYSTEM_PROMPT as T_SYSTEM_PROMPT,
)

PROBE_DIR = knowledge_probe_dir()
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
from backends import render_probe_prompt  # noqa: E402

EVAL_DIR = locked_eval_dir()
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))
import scorers  # noqa: E402  (from archive/experiment/phase1/eval; scores FRESH answers)

CELL_YAML = HERE / "cell.yaml"
GATES_YAML = HERE / "gates.yaml"

# Single arm (AMENDMENT.md "Design"): the deployed checkpoint, now gated.
ARM_SYSTEM_PROMPTS = {
    "t_deployed_confirmatory": T_SYSTEM_PROMPT,
}


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


@dataclass
class ArmConfig:
    id: str
    model_name: str
    adapter: str | None
    quantization: str | None
    lora: bool
    dial_layer: int
    gate: str
    system_prompt: str
    max_new_tokens: int
    do_sample: bool
    temperature: float
    enable_thinking: bool


def load_cell_config(cell_yaml_path: Path) -> dict:
    return yaml.safe_load(cell_yaml_path.read_text(encoding="utf-8"))


def load_gates_config(gates_yaml_path: Path) -> dict:
    return yaml.safe_load(gates_yaml_path.read_text(encoding="utf-8"))


def _gate(gates_cfg: dict, gate_id: str) -> dict:
    for g in gates_cfg["gates"]:
        if g["id"] == gate_id:
            return g
    raise KeyError(f"gate {gate_id!r} not found in gates.yaml")


def _resolve_ref(raw: str | None, repo_root: Path) -> str | None:
    """A cell.yaml model/adapter field is either an HF hub id or a
    repo-relative local path. Resolve to an absolute local path if it exists
    on disk; otherwise pass the raw string through as a hub id."""
    if raw is None:
        return None
    local = repo_root / raw
    return str(local) if local.exists() else raw


def arm_configs_from_cell(cell: dict, repo_root: Path) -> dict[str, ArmConfig]:
    gen = cell["generation"]
    out: dict[str, ArmConfig] = {}
    for arm in cell["arms"]:
        arm_id = arm["id"]
        out[arm_id] = ArmConfig(
            id=arm_id,
            model_name=arm["model"]["name"],
            adapter=arm["model"].get("adapter"),
            quantization=arm["model"].get("quantization"),
            lora=bool(arm["model"].get("lora", False)),
            dial_layer=int(arm["dial_layer"]),
            gate=arm["gate"],
            system_prompt=ARM_SYSTEM_PROMPTS[arm_id],
            max_new_tokens=int(gen["max_new_tokens"]),
            do_sample=bool(gen["do_sample"]),
            temperature=float(gen["temperature"]),
            enable_thinking=bool(gen["enable_thinking"]),
        )
    return out


# ---------------------------------------------------------------------------
# Pool (imported unchanged) + target-count replay
# ---------------------------------------------------------------------------


def build_arm_pool(cell: dict, repo_root: Path) -> list[dict]:
    """The arm's prompt inventory, capped at max_attempts. S and T call this
    with the SAME args (datasets/per_dataset/seed), so both draw from the
    identical pool -- matching build_pool's own dataset-agnostic contract."""
    pi = cell["prompt_inventory"]
    datasets_root = repo_root / "datasets"
    pool = build_pool(datasets_root, pi["datasets"], pi["per_dataset"], pi["pool_seed"])
    return pool[: pi["max_attempts"]]


def select_attempted(
    pool_items: list[dict], dispositions: list[dict],
    target_correct: int, target_wrong: int, max_attempts: int,
) -> list[tuple[dict, dict]]:
    """Replay the S/T extractors' own sequential early-stop selection rule
    POST HOC over a fully-generated batch: walk pool order, include items
    until (n_correct>=target_correct and n_wrong>=target_wrong) first holds,
    or max_attempts items have been included, whichever comes first.
    `dispositions[i]` must expose `label` in {'correct','wrong',None} for
    `pool_items[i]`. Reproduces IDENTICAL selection semantics to the source
    extractors' loop (`amendment_s_correctness_probe_extract.run`), computed
    after batched vLLM generation rather than during a sequential one --
    legitimate because the break condition only depends on the running class
    counts in pool order, which are unaffected by how generation was batched.
    """
    n_correct = n_wrong = 0
    attempted: list[tuple[dict, dict]] = []
    for item, disp in zip(pool_items, dispositions):
        if len(attempted) >= max_attempts:
            break
        attempted.append((item, disp))
        if disp.get("label") == "correct":
            n_correct += 1
        elif disp.get("label") == "wrong":
            n_wrong += 1
        if n_correct >= target_correct and n_wrong >= target_wrong:
            break
    return attempted


# ---------------------------------------------------------------------------
# Phase 1: generation + capture (vLLM real; engine-agnostic so a stub can
# stand in for tests -- see test_lp_v3_smoke.py's _StubVLLMEngine)
# ---------------------------------------------------------------------------


def _special_ids(tokenizer) -> set[int]:
    """Mirrors the S/T extractors' inline eos/special-id discovery (that
    logic is not factored into an importable function upstream)."""
    special_ids = set(tokenizer.all_special_ids or [])
    if tokenizer.eos_token_id is not None:
        special_ids.add(tokenizer.eos_token_id)
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end, int) and im_end >= 0:
        special_ids.add(im_end)
    return special_ids


def render_arm_prompts(tokenizer, arm: ArmConfig, pool_items: list[dict]) -> list[str]:
    rendered = []
    for item in pool_items:
        text, _mode = render_probe_prompt(
            tokenizer, arm.system_prompt, item["question"],
            enable_thinking=arm.enable_thinking,
        )
        rendered.append(text)
    return rendered


def _extract_step_logprobs(logprobs_list, span_ids: list[int], span_len: int) -> list[float]:
    """logprobs_list is one dict-per-generated-step (vLLM's SampleLogprobs
    shape, keyed by token id -> an object with a `.logprob` attribute, OR a
    plain float in the test stub). Only the sampled token's own logprob is
    used (SamplingParams(logprobs=0) guarantees it is always present)."""
    if not logprobs_list:
        return []
    out: list[float] = []
    for step in range(span_len):
        entry = logprobs_list[step].get(span_ids[step])
        if entry is None:
            continue
        lp = entry.logprob if hasattr(entry, "logprob") else float(entry)
        out.append(float(lp))
    return out


def capture_row(item: dict, output, tokenizer, special_ids: set[int]) -> dict:
    """Build the per-row capture record from ONE generate() request output --
    the single source every downstream quantity derives from (LT-G0a). The
    answer text is decoded ONCE here and that same string is what scoring
    sees; the logprob variants are computed from the SAME span_ids; the
    teacher-forced extraction pass (phase 2) will consume
    prompt_token_ids + this exact span, nothing re-tokenized."""
    completion = output.outputs[0]
    prompt_token_ids = list(output.prompt_token_ids)
    completion_token_ids = list(completion.token_ids)
    full_ids = prompt_token_ids + completion_token_ids
    prompt_len = len(prompt_token_ids)

    content_end = _content_end_index(full_ids, prompt_len, special_ids)
    span_len = (content_end - prompt_len + 1) if content_end is not None else 0
    span_ids = completion_token_ids[:span_len]

    answer_text = tokenizer.decode(span_ids, skip_special_tokens=True).strip()
    refused = scorers.is_stated_confidence_refusal(answer_text)
    answered = (content_end is not None) and bool(answer_text) and not refused
    correct = scorers.is_correct(answer_text, item["aliases_norm"]) if answered else False
    label = ("correct" if correct else "wrong") if answered else None

    step_logprobs = _extract_step_logprobs(completion.logprobs, span_ids, span_len)
    variants = {
        "mean_answer_span": float(np.mean(step_logprobs)) if step_logprobs else float("nan"),
        "sum_answer_span": float(np.sum(step_logprobs)) if step_logprobs else float("nan"),
        "min_answer_span": float(np.min(step_logprobs)) if step_logprobs else float("nan"),
    }

    return {
        "row_key": item["row_key"],
        "dataset": item["dataset"],
        "prompt_token_ids": prompt_token_ids,
        "completion_token_ids": completion_token_ids,
        "span_len": span_len,
        "answer_text": answer_text,
        "answered": answered,
        "refused": refused,
        "correct": bool(correct) if answered else None,
        "label": label,
        "variants": variants,
    }


def _read_done_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    keys: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                keys.add(json.loads(line)["row_key"])
    return keys


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def run_arm_generation(
    engine, tokenizer, arm: ArmConfig, pool_items: list[dict],
    runlog_path: Path, params, lora_request=None, chunk_size: int = 200,
) -> list[dict]:
    """Chunked, resumable generation over one arm's capped pool. Each chunk
    is ONE batched engine.generate() call (vLLM's throughput; a stub in tests
    stands in for `engine`). Progress-visible: appends+flushes after every
    chunk, so a kill mid-arm loses at most the in-flight chunk and resumes by
    row_key on restart. `params` is caller-supplied (built by
    `build_sampling_params` on the real path) so this function never imports
    vllm itself -- keeps it exercisable with any engine-shaped stub."""
    runlog_path.parent.mkdir(parents=True, exist_ok=True)
    done_keys = _read_done_keys(runlog_path)
    special_ids = _special_ids(tokenizer)
    pending = [item for item in pool_items if item["row_key"] not in done_keys]

    with runlog_path.open("a", encoding="utf-8") as out_fh:
        for start in range(0, len(pending), chunk_size):
            chunk = pending[start : start + chunk_size]
            prompts = render_arm_prompts(tokenizer, arm, chunk)
            gen_kwargs = {"lora_request": lora_request} if lora_request is not None else {}
            outputs = engine.generate(prompts, params, **gen_kwargs)
            for item, output in zip(chunk, outputs):
                row = capture_row(item, output, tokenizer, special_ids)
                out_fh.write(json.dumps(row) + "\n")
                out_fh.flush()

    return _read_jsonl(runlog_path)


def build_sampling_params(arm: ArmConfig):
    """Real vLLM SamplingParams. Lazy-imported so this module (and
    run_arm_generation) loads and runs without vLLM installed; NOT called by
    the smoke test, which builds its own stub params object directly."""
    from vllm import SamplingParams  # noqa: PLC0415

    return SamplingParams(temperature=arm.temperature, max_tokens=arm.max_new_tokens, logprobs=0)


def _lora_rank(arm: ArmConfig, repo_root: Path) -> int:
    adapter_ref = _resolve_ref(arm.adapter, repo_root)
    cfg_path = Path(adapter_ref) / "adapter_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    return int(cfg["r"])


def build_vllm_engine(arm: ArmConfig, cell: dict):
    """Real GPU vLLM engine. Lazy-imported (mirrors hs_backends.py /
    backends.py's established lazy-heavy-import convention in this repo) so
    this module loads on a host without vLLM."""
    from vllm import LLM  # noqa: PLC0415

    sched = cell["engine"]["scheduler"]
    kwargs: dict[str, Any] = dict(
        model=_resolve_ref(arm.model_name, REPO_ROOT),
        dtype="auto",
        max_model_len=sched["max_model_len"],
        max_num_seqs=sched["max_num_seqs"],
        max_num_batched_tokens=sched["max_num_batched_tokens"],
        gpu_memory_utilization=cell["engine"].get("gpu_memory_utilization", 0.85),
    )
    if arm.quantization:
        kwargs["quantization"] = arm.quantization
        kwargs["load_format"] = "bitsandbytes"
    if arm.lora:
        kwargs["enable_lora"] = True
        kwargs["max_lora_rank"] = _lora_rank(arm, REPO_ROOT)
    return LLM(**kwargs)


def build_lora_request(arm: ArmConfig):
    from vllm.lora.request import LoRARequest  # noqa: PLC0415

    adapter_ref = _resolve_ref(arm.adapter, REPO_ROOT)
    return LoRARequest(lora_name=arm.id, lora_int_id=1, lora_path=adapter_ref)


# ---------------------------------------------------------------------------
# Phase 2: teacher-forced extraction (registered fallback; HF + PEFT)
# ---------------------------------------------------------------------------


def load_hf_model_for_extraction(arm: ArmConfig):
    """Registered-fallback load: mirrors the S/T extractors' own load code
    (bfloat16, device_map=cuda, PEFT for the adapter arm). Runs in the SAME
    pinned stack/venv as the vLLM generation phase (cell.yaml `engine.stack`;
    NOTEBOOK.md capability-check finding), sequentially after phase 1."""
    import torch  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    model_ref = _resolve_ref(arm.model_name, REPO_ROOT)
    tokenizer = AutoTokenizer.from_pretrained(model_ref)
    base = AutoModelForCausalLM.from_pretrained(
        model_ref, torch_dtype=torch.bfloat16, device_map="cuda"
    )
    if arm.adapter is not None:
        from peft import PeftModel  # noqa: PLC0415

        adapter_ref = _resolve_ref(arm.adapter, REPO_ROOT)
        model = PeftModel.from_pretrained(base, adapter_ref, adapter_name="v3_extract")
        model.set_adapter("v3_extract")
    else:
        model = base
    model.eval()
    device = next(model.parameters()).device
    return model, tokenizer, device


def run_arm_extraction(
    model, tokenizer, device, arm: ArmConfig, captures: list[dict],
    tensors_dir: Path, runlog_path: Path,
) -> list[dict]:
    """Phase 2: teacher-forced forward pass over EACH answered row's captured
    (prompt + generated) token IDs, verbatim -- nothing regenerated, nothing
    re-tokenized (AMENDMENT.md registered fallback). Saves the dial layer's
    final-position hidden state as a safetensors shard in the SAME
    {safe_key}__post.safetensors layout `load_position_layers` expects.
    Resumable (append+flush per row, like v2's run_arm)."""
    import torch  # noqa: PLC0415
    from safetensors.torch import save_file  # noqa: PLC0415

    tensors_dir.mkdir(parents=True, exist_ok=True)
    runlog_path.parent.mkdir(parents=True, exist_ok=True)
    done_keys = _read_done_keys(runlog_path)

    # load_position_layers (reused unchanged from amendment_s_correctness_
    # probe_score.py) expects a rows.jsonl alongside the safetensors shards,
    # carrying row_key + label per row -- mirrors the S/T extractors' own
    # out_dir layout. Rewritten each call from `captures` (already fully
    # known upfront); NOT part of the resumable state -- the safetensors
    # shards and the extraction runlog are what resume protects.
    with (tensors_dir / "rows.jsonl").open("w", encoding="utf-8") as rows_fh:
        for row in captures:
            rows_fh.write(json.dumps({"row_key": row["row_key"], "label": row["label"]}) + "\n")

    with runlog_path.open("a", encoding="utf-8") as out_fh:
        for row in captures:
            if row["row_key"] in done_keys:
                continue
            if not row["answered"]:
                # No meaningful post-gen position; recorded but not
                # extracted, mirroring the S/T extractors' own "answered
                # rows only" tensor rule.
                rec = {"row_key": row["row_key"], "extracted": False,
                       "teacher_forced_input_ids": None}
                out_fh.write(json.dumps(rec) + "\n")
                out_fh.flush()
                continue

            span_ids = row["completion_token_ids"][: row["span_len"]]
            input_ids_list = row["prompt_token_ids"] + span_ids
            fwd_ids = torch.tensor([input_ids_list], device=device)
            attn = torch.ones_like(fwd_ids)
            with torch.no_grad():
                out = model(input_ids=fwd_ids, attention_mask=attn,
                            output_hidden_states=True, use_cache=False)
            hs = out.hidden_states
            if arm.dial_layer >= len(hs):
                raise RuntimeError(
                    f"dial_layer {arm.dial_layer} out of range for "
                    f"{len(hs)} hidden_states entries"
                )
            vec = hs[arm.dial_layer][0, -1, :].float().cpu().contiguous()
            safe_key = row["row_key"].replace("::", "__").replace("|", "_")
            save_file({f"L{arm.dial_layer}": vec},
                      str(tensors_dir / f"{safe_key}__post.safetensors"))

            rec = {"row_key": row["row_key"], "extracted": True,
                   "teacher_forced_input_ids": input_ids_list}
            out_fh.write(json.dumps(rec) + "\n")
            out_fh.flush()

    return _read_jsonl(runlog_path)


# ---------------------------------------------------------------------------
# Phase 3: scoring (CPU-only; no model, no GPU)
# ---------------------------------------------------------------------------


def score_arm_t(
    arm: ArmConfig, captures: list[dict], extraction_records: list[dict],
    tensors_dir: Path, n_boot: int, seed: int, gates_cfg: dict,
    power_floor_n: int, instrument_sanity_min: float,
) -> dict:
    """LT-G0 (a-d) then, only if all pass, LT-G1. No reproduction target
    anywhere -- verbatim from v3's score_arm_v3, this cell has no external
    cached artifact to reproduce against either."""
    by_key_capture = {r["row_key"]: r for r in captures}
    by_key_extract = {r["row_key"]: r for r in extraction_records}

    # LT-G0(a): capture integrity -- the teacher-forced pass consumed
    # EXACTLY the captured prompt+span ids, for every extracted row.
    integrity_fail = 0
    for row_key, ext in by_key_extract.items():
        if not ext.get("extracted"):
            continue
        cap = by_key_capture.get(row_key)
        if cap is None:
            integrity_fail += 1
            continue
        span_ids = cap["completion_token_ids"][: cap["span_len"]]
        expected = cap["prompt_token_ids"] + span_ids
        if ext.get("teacher_forced_input_ids") != expected:
            integrity_fail += 1
    capture_integrity_ok = integrity_fail == 0

    # LT-G0(b): coverage -- every attempted item has exactly one recorded
    # disposition (no dup/missing row_keys between the attempted set and the
    # capture set scoring reads).
    coverage_ok = len(captures) == len(by_key_capture) == len(
        {c["row_key"] for c in captures}
    )

    # LT-G0(c): power floor (unchanged from v3's LP3-G0(c) -- the cap moved,
    # not the floor).
    answered_rows = [r for r in captures if r["label"] in ("correct", "wrong")]
    n_answered = len(answered_rows)
    power_floor_ok = n_answered >= power_floor_n

    result: dict[str, Any] = {
        "arm": arm.id,
        "lt_g0": {
            "a_capture_integrity_ok": capture_integrity_ok,
            "a_n_integrity_fail": integrity_fail,
            "b_coverage_ok": coverage_ok,
            "c_power_floor_ok": power_floor_ok,
            "c_n_answered": n_answered,
            "c_power_floor_n": power_floor_n,
        },
    }

    abc_pass = capture_integrity_ok and coverage_ok and power_floor_ok
    if not abc_pass:
        result["lt_g0"]["pass"] = False
        result["gate_verdict"] = {"stopped_at_lt_g0": True}
        return result

    # Dial refit: fresh OOF AUROC at the pinned dial layer. No reproduction
    # target -- LT-G0(d) is a sanity floor applied to this cell's own (T) arm
    # (AMENDMENT.md LT-G0d: "the fresh T dial OOF AUROC").
    X, y, keys = load_position_layers(tensors_dir, "post")
    if arm.dial_layer not in X:
        raise RuntimeError(
            f"dial_layer {arm.dial_layer} not present in {tensors_dir} "
            f"(layers on disk: {sorted(X)})"
        )
    X_dial = X[arm.dial_layer]
    p_dial = oof_probe(X_dial, y, seed)
    dial_auroc = float(roc_auc_score(y, p_dial))

    # Single arm, always gated (LT-G1) -- unlike v3's T arm (descriptive-only,
    # sanity bypassed), this cell's LT-G0(d) sanity floor always applies.
    instrument_sanity_ok = (
        dial_auroc >= instrument_sanity_min if arm.gate == "LT-G1" else True
    )
    result["lt_g0"]["d_instrument_sanity_ok"] = instrument_sanity_ok
    result["lt_g0"]["d_dial_auroc"] = round(dial_auroc, 4)
    result["lt_g0"]["d_instrument_sanity_auroc_min"] = instrument_sanity_min
    result["lt_g0"]["pass"] = instrument_sanity_ok

    if not instrument_sanity_ok:
        result["gate_verdict"] = {"stopped_at_lt_g0": True}
        return result

    by_key_answered = {r["row_key"]: r for r in answered_rows}
    idx_common = [i for i, k in enumerate(keys) if k in by_key_answered]
    y_common = y[idx_common]
    p_dial_common = p_dial[idx_common]

    variant_scores: dict[str, dict] = {}
    for variant in ("mean_answer_span", "sum_answer_span", "min_answer_span"):
        scores = np.array([by_key_answered[keys[i]]["variants"][variant] for i in idx_common])
        variant_scores[variant] = {"auroc": float(roc_auc_score(y_common, scores)),
                                    "n": int(len(scores))}

    primary = np.array([by_key_answered[keys[i]]["variants"]["mean_answer_span"] for i in idx_common])
    dial_auroc_common = float(roc_auc_score(y_common, p_dial_common))
    primary_auroc = float(roc_auc_score(y_common, primary))
    margin = dial_auroc_common - primary_auroc
    margin_boot = paired_bootstrap_delta(y_common, p_dial_common, primary, n_boot, seed)

    if arm.gate == "LT-G1":
        floor = float(_gate(gates_cfg, "LT-G1")["floor"])
        g1_pass = (margin >= floor) and (margin_boot["ci_lo"] > 0.0)
        falsifier_fired = (margin <= 0.0) and (margin_boot["ci_hi"] < 0.0)
        ambiguous = (not g1_pass) and (not falsifier_fired)
        gate_verdict: dict[str, Any] = {
            "LT_G1_pass": g1_pass,
            "falsifier_fired": falsifier_fired,
            "ambiguous_band": ambiguous,
        }
    else:
        gate_verdict = {"descriptive_only": True}

    result["variant_aurocs"] = variant_scores
    result["dial_minus_primary_logprob_margin"] = round(margin, 4)
    result["margin_bootstrap_ci"] = margin_boot
    result["gate_verdict"] = gate_verdict
    return result


# ---------------------------------------------------------------------------
# --dry-run: real-input existence check, no model, no compute
# ---------------------------------------------------------------------------


def dry_run(cell: dict, repo_root: Path) -> int:
    problems: list[str] = []
    plan: dict[str, Any] = {"engine": cell["engine"], "arms": []}

    pi = cell["prompt_inventory"]
    datasets_root = repo_root / "datasets"
    popqa_path = datasets_root / "popqa" / "test.jsonl"
    triviaqa_path = datasets_root / "triviaqa-rc-nocontext" / "cheng_test_gold.jsonl"
    for name, p in (("popqa", popqa_path), ("triviaqa", triviaqa_path)):
        if name in pi["datasets"] and not p.exists():
            problems.append(f"prompt_inventory: {name} file not found: {p}")
    plan["prompt_inventory"] = {
        "popqa_path": str(popqa_path), "popqa_exists": popqa_path.exists(),
        "triviaqa_path": str(triviaqa_path), "triviaqa_exists": triviaqa_path.exists(),
    }

    for arm_raw in cell["arms"]:
        arm_id = arm_raw["id"]
        model_ref = _resolve_ref(arm_raw["model"]["name"], repo_root)
        arm_plan: dict[str, Any] = {"id": arm_id, "model_ref": model_ref,
                                     "dial_layer": arm_raw["dial_layer"]}
        looks_local = (repo_root / arm_raw["model"]["name"]) == Path(model_ref)
        if looks_local and not Path(model_ref).exists():
            problems.append(f"{arm_id}: local model path not found: {model_ref}")
        raw_adapter = arm_raw["model"].get("adapter")
        if raw_adapter:
            adapter_ref = _resolve_ref(raw_adapter, repo_root)
            arm_plan["adapter_ref"] = adapter_ref
            if not Path(adapter_ref).exists():
                problems.append(f"{arm_id}: adapter not found: {adapter_ref}")
        plan["arms"].append(arm_plan)

    dial_module = READOUTS_DIR / "amendment_s_correctness_probe_score.py"
    plan["dial_refit_module"] = str(dial_module)
    if not dial_module.exists():
        problems.append(f"dial refit module not found: {dial_module}")

    scorer_module = EVAL_DIR / "scorers.py"
    plan["scorer_module"] = str(scorer_module)
    if not scorer_module.exists():
        problems.append(f"scorer module not found: {scorer_module}")

    pool_module = READOUTS_DIR / "amendment_s_correctness_probe_extract.py"
    plan["pool_module"] = str(pool_module)
    if not pool_module.exists():
        problems.append(f"pool module not found: {pool_module}")

    if popqa_path.exists() or triviaqa_path.exists():
        pool = build_pool(datasets_root, pi["datasets"], pi["per_dataset"], pi["pool_seed"])
        plan["pool_size_uncapped"] = len(pool)
        plan["pool_size_capped"] = min(len(pool), pi["max_attempts"])

    print(json.dumps(plan, indent=2))
    if problems:
        print("\n[dry-run] UNRESOLVED real inputs:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    print("\n[dry-run] all real inputs resolved.", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _set_engine_env_vars(cell: dict) -> None:
    import os  # noqa: PLC0415

    for k, v in cell["engine"].get("env_vars", {}).items():
        os.environ.setdefault(k, str(v))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=CELL_YAML)
    ap.add_argument("--gates", type=Path, default=GATES_YAML)
    ap.add_argument("--dry-run", action="store_true",
                     help="resolve real inputs and print the plan; exit 0/2, no compute")
    ap.add_argument("--arm", choices=sorted(ARM_SYSTEM_PROMPTS), default=None,
                     help="run this arm for real (GPU) -- requires the launch "
                          "precondition in AMENDMENT.md sec.8")
    ap.add_argument("--phase", choices=["generate", "extract", "score", "all"], default="all")
    ap.add_argument("--seed", type=int, default=20260813)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--chunk-size", type=int, default=200)
    a = ap.parse_args(argv)

    cell = load_cell_config(a.config)

    if a.dry_run:
        return dry_run(cell, REPO_ROOT)

    if a.arm is None:
        print("nothing to do: pass --dry-run, or --arm <id> [--phase generate|extract|score|all]",
              file=sys.stderr)
        return 2

    arms = arm_configs_from_cell(cell, REPO_ROOT)
    arm = arms[a.arm]
    pi = cell["prompt_inventory"]

    arm_dir = HERE / "analysis" / arm.id
    gen_runlog = arm_dir / "runlog" / f"{arm.id}_generation.jsonl"
    ext_runlog = arm_dir / "runlog" / f"{arm.id}_extraction.jsonl"
    tensors_dir = arm_dir / "tensors"

    if a.phase in ("generate", "all"):
        _set_engine_env_vars(cell)
        pool = build_arm_pool(cell, REPO_ROOT)
        engine = build_vllm_engine(arm, cell)
        tokenizer = engine.get_tokenizer()
        lora_request = build_lora_request(arm) if arm.lora else None
        params = build_sampling_params(arm)
        run_arm_generation(engine, tokenizer, arm, pool, gen_runlog, params,
                            lora_request=lora_request, chunk_size=a.chunk_size)
        if a.phase == "generate":
            print(f"[lp-t] generation phase done -> {gen_runlog}", file=sys.stderr)
            return 0
        del engine
        import gc  # noqa: PLC0415
        import torch  # noqa: PLC0415
        gc.collect()
        torch.cuda.empty_cache()

    if a.phase in ("extract", "all"):
        if not gen_runlog.exists():
            print(f"[lp-t] extract phase requires generation runlog: {gen_runlog}", file=sys.stderr)
            return 2
        captures = _read_jsonl(gen_runlog)
        attempted = select_attempted(captures, captures, pi["target_correct"],
                                      pi["target_wrong"], pi["max_attempts"])
        attempted_captures = [d for _item, d in attempted]
        model, hf_tokenizer, device = load_hf_model_for_extraction(arm)
        run_arm_extraction(model, hf_tokenizer, device, arm, attempted_captures,
                            tensors_dir, ext_runlog)
        if a.phase == "extract":
            print(f"[lp-t] extraction phase done -> {ext_runlog}", file=sys.stderr)
            return 0

    if a.phase in ("score", "all"):
        if not gen_runlog.exists() or not ext_runlog.exists():
            print("[lp-t] score phase requires both generation and extraction runlogs",
                  file=sys.stderr)
            return 2
        captures = _read_jsonl(gen_runlog)
        attempted = select_attempted(captures, captures, pi["target_correct"],
                                      pi["target_wrong"], pi["max_attempts"])
        attempted_captures = [d for _item, d in attempted]
        extraction_records = _read_jsonl(ext_runlog)
        gates_cfg = load_gates_config(a.gates)
        result = score_arm_t(
            arm, attempted_captures, extraction_records, tensors_dir,
            a.n_boot, a.seed, gates_cfg,
            power_floor_n=cell["power_floor_n"],
            instrument_sanity_min=cell["dial_refit"]["instrument_sanity_auroc_min"],
        )
        out_dir = HERE / "analysis-committed"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"lp_t_{arm.id}_result.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        print(f"\nwrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
