"""Batched generation + activation-write driver for
idk-switch-naming-confirmatory.

Adapted from `write-direction-naming-battery/steer_lib.py` (source sha256
edc25a1721e43c0d8644fa6178439a057fd1da2ba2929d4bc9ab8d782e572890, matching
that file's own pin; read in full before writing this), itself adapted from
`qwen35-4b-midband-heldout/steer_lib.py`: same InterventionHook/
GenerationInterventionController/RunLog driving, same left-padding rationale,
same render-env-setting-at-load-site discipline. Differs from the naming
battery's own module where this cell's design requires it:

  - `load_model` sets `ISNC_RENDER_MODEL`/`ISNC_RENDER_REVISION` (this
    cell's own render env namespace, see render.py), not
    `WDNB_RENDER_MODEL`/`WDNB_RENDER_REVISION`.
  - `run_rows` does NOT redact any field before persisting (cell.yaml
    `execution.redact_fields: []`). DEVIATION FROM THE NAMING BATTERY,
    documented (see cell.yaml "execution" comment and the harness-build
    report): this cell's judge lane needs the actual generation text, and
    keeping it in the gitignored `analysis/runlog/*.jsonl` (never committed)
    avoids the naming battery's own post-hoc "form_sidecar" rebuild.
  - `run_rows` optionally seeds the generation RNG per row-batch call when
    `decode_mode == "sampled"` (cell.yaml `surface.generation`), via
    `apply_generation_seed`. This is a no-op under `decode_mode == "greedy"`
    (do_sample=False; torch.manual_seed has no effect on a deterministic
    argmax decode) -- see cell.yaml's "AMBIGUITY FLAGGED FOR SIGN" comment
    for why decode_mode itself is a REGISTERED_AT_SIGN placeholder, not
    assumed here.
  - Only ONE readout family is dosed per arm at multiplier 0.0, 0.5, or 1.0
    (the reduced 4-arm ladder); this module does not special-case negative
    multipliers (the naming battery's Arm B design) since this cell never
    doses negative.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_lib  # noqa: E402
import render as render_mod  # noqa: E402

MODEL_NAME = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
HIDDEN_DIM = 2560

# cell.yaml execution.redact_fields: [] -- nothing is redacted from the
# persisted runlog record (deviation from the naming battery, documented
# above). Kept as a named constant so a future repin that wants to restore
# redaction has one place to change.
REDACT_FIELDS: tuple[str, ...] = ()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def load_model(model_name: str = MODEL_NAME, revision: str = MODEL_REVISION):
    """Loads the generation model/tokenizer. Per the local-runtime invariant
    (.skills/mechinterp-cells/reference/modal-launch.md "Local GPU runs
    execute in a pinned container"), this cell does NOT hard-code a bare
    conda python path the way the naming battery's own steer_lib.py did --
    the launching harness (pipeline.py) is invoked with whatever `python3`
    the pinned mechinterp-runner container provides on PATH. Sets
    render.py's ISNC_RENDER_MODEL/ISNC_RENDER_REVISION to the SAME
    model/revision in the same place, so the two can never drift apart. Left
    padding keeps every row's real last prompt token in the same trailing
    column so decode steps stay synchronized across the batch."""
    import os

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["ISNC_RENDER_MODEL"] = model_name
    os.environ["ISNC_RENDER_REVISION"] = revision or ""

    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        model_name, revision=revision, dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True,
    )
    model.eval()
    device = next(model.parameters()).device
    return model, tokenizer, device


def build_hook_and_controller(direction_vec, sigma: float):
    """direction_vec: torch.Tensor, unit-norm. Returns (hook, controller)
    driving InterventionHook(law="erase_write", position="anchor_onward")
    under GenerationInterventionController's "gen_stream" mode. `sigma` is
    per-call (sigma_c for c_hat, 1.0 for random_direction, matching every
    prior cell in this lineage's convention) so one function serves both
    readouts across every arm."""
    from MechInterp.intervention import GenerationInterventionController, InterventionHook

    hook = InterventionHook(
        law="erase_write", direction=direction_vec, sigma=sigma,
        position="anchor_onward", measure_readback=True,
    )
    return hook, GenerationInterventionController(hook)


def render_prompt(row: dict[str, Any]) -> str:
    return render_mod.render(row)


def apply_generation_seed(seed: Optional[int]) -> None:
    """Seeds the generation RNG for a sampled-decode call. A no-op call site
    under decode_mode == "greedy" (do_sample=False never consults the RNG);
    pipeline.py is responsible for deciding whether to call this at all, per
    cell.yaml `surface.generation.decode_mode`."""
    if seed is None:
        return
    # Match the program's registered sampled-decode seeding convention
    # (sampled-decode-seed-robustness/AMENDMENT.md "Seeds and decode
    # (LOCKED)": torch.manual_seed(seed) + transformers.set_seed(seed)).
    import torch

    torch.manual_seed(int(seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))
    import transformers

    transformers.set_seed(int(seed))


def run_batch_fixed(
    model, tokenizer, device, controller, prompts: list[str],
    mode: str, strength, max_new: int,
    *, do_sample: bool = False, temperature: Optional[float] = None, top_p: Optional[float] = None,
) -> tuple[list[dict[str, Any]], Optional[dict[str, Any]]]:
    """Batched pass. `controller=None` is a true no-write pass (no hook
    registered at all -- used for every arm's baseline, per this lineage's
    universal convention that multiplier==0.0 means NO hook, not a
    zero-gain hook call). `strength` is a SCALAR gain in sigma units.
    `do_sample`/`temperature`/`top_p` are read from cell.yaml
    `surface.generation` (REGISTERED_AT_SIGN until sign; pipeline.py is
    responsible for refusing to run while they are unresolved)."""
    import torch

    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    eos_ids = gen_lib.resolve_eos_ids(tokenizer)
    if controller is not None:
        controller.hook.last_readback = None
        controller.begin_pass(mode, strength, attention_mask=enc["attention_mask"])
    gen_kwargs: dict[str, Any] = dict(
        max_new_tokens=max_new, min_new_tokens=1, do_sample=do_sample,
        num_beams=1, eos_token_id=eos_ids, pad_token_id=tokenizer.pad_token_id,
    )
    if do_sample:
        gen_kwargs["temperature"] = temperature
        gen_kwargs["top_p"] = top_p
    with torch.no_grad():
        out = model.generate(**enc, **gen_kwargs)
    readback = None
    raw_readback = None
    if controller is not None:
        rb = controller.hook.last_readback
        raw_readback = rb
        if rb is not None and rb.get("measured"):
            readback = list(rb["measured"])
        controller.reset()

    prompt_len = int(enc["input_ids"].shape[1])
    results = []
    for b in range(out.shape[0]):
        tail = out[b, prompt_len:]
        tail_ids = tail.tolist()
        eos_pos = next((i for i, t in enumerate(tail_ids) if int(t) in eos_ids), None)
        if eos_pos is not None:
            n_new = eos_pos + 1
            terminated_naturally = True
        else:
            n_new = len(tail_ids)
            terminated_naturally = n_new < max_new
        text = tokenizer.decode(tail[:n_new], skip_special_tokens=True)
        results.append({
            "text": text,
            "n_new_tokens": n_new,
            "terminated_naturally": terminated_naturally,
            "readback_measured": (readback[b] if readback is not None and b < len(readback) else None),
        })
    return results, raw_readback


def redact(record: dict[str, Any], redact_fields=REDACT_FIELDS) -> dict[str, Any]:
    if not redact_fields:
        return record
    return {k: v for k, v in record.items() if k not in redact_fields}


def run_rows(
    model, tokenizer, device, controller, mode: str,
    rows: list[dict[str, Any]], strength, max_new: int, batch_size: int,
    run_log,
    *,
    arm: str,
    multiplier: float,
    dose_abs: float,
    readout: str,
    do_sample: bool = False,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    generation_sampling_seed: Optional[int] = None,
    readback_collector: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Generic batched runner for ONE arm's rows: renders, generates, grades
    (full gen_lib.grade_row dict, data-exhaust principle), then persists
    (no redaction, cell.yaml `execution.redact_fields: []`). Resumable:
    already-recorded row_keys are skipped. If `do_sample`, reseeds the
    generation RNG once per batch from `generation_sampling_seed` combined
    with the batch offset, so the run is deterministic-given-seed and
    resumable (a resumed run reseeds identically for the remaining batches,
    it does not replay already-written batches)."""
    done = run_log.done_keys()
    pending = [r for r in rows if r["row_key"] not in done]
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        if do_sample and generation_sampling_seed is not None:
            apply_generation_seed(int(generation_sampling_seed) + i)
        batch = pending[i:i + batch_size]
        prompts = [render_prompt(r) for r in batch]
        gen, raw_rb = run_batch_fixed(
            model, tokenizer, device, controller, prompts, mode, strength, max_new,
            do_sample=do_sample, temperature=temperature, top_p=top_p,
        )
        if readback_collector is not None and raw_rb is not None:
            readback_collector.append(raw_rb)
        for row, res in zip(batch, gen):
            grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            record = {
                "row_key": row["row_key"], "role": row["role"], "population": row.get("population"),
                "arm": arm, "readout": readout, "multiplier": multiplier, "dose_abs": dose_abs,
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            }
            run_log.record(row["row_key"], redact(record))
        print(f"[steer_lib] {arm}: {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
