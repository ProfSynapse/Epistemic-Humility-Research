#!/usr/bin/env python3
"""Stage C: per-layer dose ladder for qwen35-4b-midband-doubt-snap.

DRAFT INSTRUMENT. Per AMENDMENT.md, this amendment does NOT execute Stage C
as evidence; `full` mode below is the harness that WOULD produce the g1
numbers once this experiment is signed, and it refuses to run without an
explicit flag naming that fact. `smoke` mode is instrument validation only
(model load, hook write, generation, grading, RunLog write+resume) on a
handful of rows -- never treat its output as a result.

Design (see AMENDMENT.md "Registered readouts", cell.yaml, gates.yaml;
those files are the source of truth -- this docstring summarizes, it does
not redefine):

  Rows: FIT split only, reused verbatim from doubt-snap-cross-family-
  confirmatory's qwen35_4b cell -- 887 confab + 240 known_correct_answered
  (unknown_refused is fit_only, used for Stage B direction fitting, and is
  NOT part of the Stage C dose-response population). Held-out rows are never
  touched by this script.

  Layers: hs20, hs23, hs26 (the three mid-band candidates from Stage A) plus
  hs30 (the late-site comparator, refit under this experiment's own
  extraction in Stage B). cell.yaml's `snap.dose_grid_proposal` registers a
  dose grid for all four, so this runner treats hs30 as an in-run arm too --
  read as a within-run consistency check against the ORIGINAL cross-family
  hs30 dose-response (which stays cited, not reproduced row-for-row, since
  it ran on a different harness against the same rows).

  Doses: 7 multipliers {2,4,6,8,12,16,20} of each layer's own fitted sigma_c
  (analysis-committed/build_manifest.json), i.e. absolute realized-projection
  targets that differ per layer. Cross-checked at startup against cell.yaml's
  own precomputed per_layer_dose_grid so the two representations in that file
  cannot silently drift apart.

  Arms:
    gated            -- real instrument: c_hat write at the frozen dose,
                         applied ONLY to rows the doubt gate fires on.
    random_direction -- same fired rows, this layer's random_direction
                         placebo vector, gain scaled so the realized
                         projection target matches the gated arm's absolute
                         dose exactly (random_direction.json stores sigma=1.0,
                         so gain_random = dose_abs; c_hat's gain = dose_abs /
                         sigma_c). "Matched realized projection", not matched
                         gain.
    permuted_gate    -- same COUNT as the real fire (n_fired for that layer),
                         but drawn as a uniform random subset of the combined
                         FIT confab + known_correct_answered pool (seed
                         SEED + 2000 + hs_index, fixed per layer, reused
                         across every dose at that layer -- fire count does
                         not depend on dose), written with c_hat at the same
                         dose as `gated`.

  Write law: erase_write (synaptic-tuner MechInterp/intervention/hooks.py,
  reused unmodified), position anchor_onward, generation_mode gen_stream --
  the hook is inactive during prefill and edits every decode step, per
  GenerationInterventionController's documented "gen_stream" semantics.
  (This is the project's neg_z_d GATE sign convention showing up in the doubt
  sensor score, not the WRITE direction's sign: the write dose is a positive
  gain along c_hat/random_direction in every arm, matching cell.yaml's
  registered dose grid and the late-site/mid-band precedent scripts this
  amendment mirrors -- see this module's own harness-builder task report for
  how that ambiguity in the task brief was resolved.)

  Baseline: ONE shared no-write pass per row (mode "off", no hook registered
  at all), computed once for the full 1,127-row FIT population and reused
  across every layer/arm/dose -- correct, not an approximation, because
  erase_write treats a row outside an arm's active set as an untouched
  no-op (see hooks.py `_resolve_active`), identical to never registering a
  hook for that row.

  Readouts per arm/dose/layer, computed via grader.grade_one +
  gen_lib.grade_clean_tighten (both byte-for-byte ports of
  doubt-snap-cross-family-confirmatory's own modules -- see grader.py/
  gen_lib.py docstrings for the diff-verified provenance): clean_tighten,
  refused (format-agnostic stated-confidence refusal), well_formed,
  degenerate, terminated_naturally, mean new tokens -- over (a) this arm's
  active-and-confab rows ("fired FIT confabs" for gated/random_direction,
  the permuted-selected confab subset for permuted_gate) and (b) the FULL
  240-row known_correct_answered population (active rows get the fresh
  write; inactive rows reuse the shared baseline).

Environment (hard requirements, see AMENDMENT.md loader/architecture notes
and cell.yaml surface.loader_note / hybrid_attention_note):
  - /home/profsynapse/miniconda3/bin/python3 (base conda, transformers 5.5.0).
    NOT the project's unsloth_env (transformers 4.57.1 does not recognize
    model_type qwen3_5 at all).
  - CUDA_LAUNCH_BLOCKING=1. Stage B's plain-forward anchor extraction did NOT
    need this (NOTEBOOK.md 2026-07-10), but this script drives `model.
    generate()` through many decode steps under an active forward hook on
    Qwen3.5's custom chunk_gated_delta_rule op, and the team-lead's task
    brief named this a hard requirement for this script specifically; this
    module does not re-litigate that empirically, it enforces it (see
    check_env()).
  - HF_TOKEN from .env (never printed), HF_HUB_DISABLE_XET=1,
    HF_HUB_ENABLE_HF_TRANSFER=0.

Row-level outputs (generations, per-row grades) live under this experiment's
gitignored analysis/ directory (RunLog jsonl + sidecars, one file per
arm/layer, or per smoke tag). Nothing under analysis-committed/ is touched by
this script; promoting an aggregate summary there is a deliberate, separate
step for whoever runs and resolves Stage C, not automatic.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
import yaml

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shared.utilities.run_log import RunLog  # noqa: E402
from MechInterp.intervention import (  # noqa: E402
    InterventionHook,
    GenerationInterventionController,
    get_decoder_layer,
)

import gen_lib  # noqa: E402  (local mirror, see gen_lib.py docstring)
import grader  # noqa: E402  (local mirror, see grader.py docstring)
# Same-directory reuse (not a cross-branch mirror): Stage B's own render/
# constants, single source of truth for the prompt surface and model pin.
from fit_midband_directions import (  # noqa: E402
    MODEL_NAME,
    MODEL_REVISION,
    HIDDEN_DIM,
    SEED,
    ANCHOR_TENSORS_PATH,
    render,
)

MAX_NEW = gen_lib.MAX_NEW_CAP  # 200
FIT_ROWS_PATH = ANALYSIS / "fit_rows_for_anchor.jsonl"
BUILD_MANIFEST_PATH = COMMITTED / "build_manifest.json"
CELL_YAML_PATH = HERE / "cell.yaml"

CANDIDATE_LAYERS_HS = (20, 23, 26, 30)
DOSE_MULTIPLIERS = (2, 4, 6, 8, 12, 16, 20)


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def runlog_path(name: str) -> Path:
    return ANALYSIS / "runlog" / f"{name}.jsonl"


def check_env() -> None:
    if os.environ.get("CUDA_LAUNCH_BLOCKING") != "1":
        raise SystemExit(
            "CUDA_LAUNCH_BLOCKING=1 is a hard requirement for this script "
            "(Qwen3.5's hybrid linear-attention custom op under a forward "
            "hook active across many decode steps; see AMENDMENT.md "
            "architecture note and cell.yaml hybrid_attention_note). Set it "
            "before invoking, e.g. `export CUDA_LAUNCH_BLOCKING=1`."
        )


def load_fit_rows() -> list[dict[str, Any]]:
    """FIT confab + known_correct_answered rows only (Stage C population).

    unknown_refused rows (role fit_only) are excluded: gates.yaml registers
    only "fired FIT confabs" and "FIT known_correct_answered" as Stage C
    populations.
    """
    all_rows = load_jsonl(FIT_ROWS_PATH)
    rows = [
        r for r in all_rows
        if r["role"] in ("confab", "known_correct_answered") and r.get("split") == "fit"
    ]
    n_confab = sum(1 for r in rows if r["role"] == "confab")
    n_known = sum(1 for r in rows if r["role"] == "known_correct_answered")
    if n_confab != 887 or n_known != 240:
        raise SystemExit(
            "Stage C row population does not match reused_rows_manifest.json "
            f"exactly (expected 887 confab_fit + 240 known_correct_answered_fit; "
            f"got confab={n_confab} known={n_known})"
        )
    rows.sort(key=lambda r: r["row_key"])
    return rows


def load_anchor_tensors() -> dict[str, np.ndarray]:
    from safetensors.numpy import load_file

    return load_file(str(ANCHOR_TENSORS_PATH))


def dose_grid_for_layer(cfg: dict[str, Any], hs_index: int) -> list[float]:
    per_layer = cfg["snap"]["dose_grid_proposal"]["per_layer_dose_grid"]
    key = "hs30_late_comparator_refit" if hs_index == 30 else f"hs{hs_index}"
    return [float(x) for x in per_layer[key]]


def assert_dose_grid_consistent(cfg: dict[str, Any], hs_index: int, sigma_c: float) -> None:
    """cell.yaml registers the dose grid TWICE: as a grid-shape formula
    (`{2,4,6,8,12,16,20} x sigma_c`) and as precomputed absolute values
    (`per_layer_dose_grid`, hand-rounded to 1 decimal for the LAUNCH-PLAN.md
    table -- confirmed by cross-checking every entry: max relative error
    ~1.5%, consistent with 1-decimal rounding of the live sigma_c, not a
    second independently-derived number). Comparing at 1-decimal precision
    catches a REAL drift (e.g. a stale sigma_c after a Stage B refit) without
    flagging the table's own intentional rounding as one."""
    grid = dose_grid_for_layer(cfg, hs_index)
    for mult in DOSE_MULTIPLIERS:
        expected = round(mult * sigma_c, 1)
        if not any(abs(expected - g) < 1e-9 for g in grid):
            raise SystemExit(
                f"hs{hs_index}: {mult} x sigma_c ({sigma_c}) = {mult * sigma_c:.4f} "
                f"(rounds to {expected}) not found in cell.yaml's registered "
                f"per_layer_dose_grid {grid} at 1-decimal precision. This is a real "
                "drift between cell.yaml's grid_shape formula and its own "
                "precomputed table -- refusing to proceed on an ambiguous grid."
            )


def load_model():
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, revision=MODEL_REVISION, trust_remote_code=True
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Left padding is required for batched generate(): it keeps every
    # prompt's real last token in the same trailing column so decode steps
    # stay synchronized across the batch (see run_batch_fixed).
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, revision=MODEL_REVISION, dtype=torch.bfloat16,
        device_map="cuda", trust_remote_code=True,
    )
    model.eval()
    device = next(model.parameters()).device
    return model, tokenizer, device


def compute_fire_decisions(
    hs_index: int, rows: list[dict[str, Any]], tensors: dict[str, np.ndarray],
    mu_d: float, sigma_d: float, tau: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Doubt-gate fire decision, mirroring fit_midband_directions.py's
    z_d/score computation exactly (same clip-to-[-2,2] standardization, same
    tau_frozen convention). Uses the Stage B cached anchor extraction --
    no fresh forward pass needed just to decide which rows fire."""
    u_d = np.asarray(
        load_json(COMMITTED / "directions" / f"hs{hs_index}" / "u_d.json")["vector"],
        dtype=np.float64,
    )
    scored = []
    for row in rows:
        key = f"hs{hs_index}__{row['row_key'].replace(':', '_')}"
        h = np.asarray(tensors[key], dtype=np.float64)
        proj_d = float(h @ u_d)
        z_d = float(np.clip((proj_d - mu_d) / sigma_d, -2.0, 2.0))
        score = -z_d
        rec = dict(row)
        rec.update({"proj_d": proj_d, "z_d": z_d, "score_neg_z_d": score, "fire": bool(score >= tau)})
        scored.append(rec)
    fired = [r for r in scored if r["fire"]]
    return fired, scored


def grade_row(text: str, terminated_naturally: bool, aliases: list[str] | None) -> dict[str, Any]:
    clean = gen_lib.grade_clean_tighten(text, terminated_naturally)
    semantic = grader.grade_one(text, aliases)
    return {**clean, **semantic, "not_well_formed_correct": not bool(semantic["well_formed_correct"])}


def _rate_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(records)

    def rate(field: str):
        return (sum(1 for r in records if r.get(field)) / n) if n else None

    return {
        "n": n,
        "clean_tighten": rate("clean_tighten"),
        "refused": rate("refused"),
        "well_formed": rate("well_formed"),
        "degenerate": rate("degenerate"),
        "terminated_naturally": rate("terminated_naturally"),
        "mean_new_tokens": (sum(r.get("n_new_tokens", 0) for r in records) / n) if n else None,
    }


# --------------------------------------------------------------------------
# batched generation
# --------------------------------------------------------------------------

def run_batch_fixed(
    model, tokenizer, device, controller, prompts: list[str], mode: str, strength, max_new: int,
) -> list[dict[str, Any]]:
    """Batched analog of gen_lib.run_pass_fixed. `controller=None` is a true
    no-write pass (no hook registered at all -- used for baseline); a
    non-None controller is armed via begin_pass exactly as the single-row
    ported function does.

    Left-padding (see load_model) keeps every row's own prompt end at the
    same trailing column, so `out.shape[1] - prompt_len` is the number of
    shared decode steps run, common to the whole batch. Per-row natural-stop
    detection cannot rely on that shared length, though (HF pads shorter
    rows with pad_token_id after their own EOS while longer rows keep
    decoding): each row's own EOS position within its tail is located
    explicitly, matching the single-row convention (new_tokens includes the
    EOS token itself; terminated_naturally is True iff that row produced its
    own EOS before the batch's shared step cap).
    """
    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    eos_ids = gen_lib.resolve_eos_ids(tokenizer)
    if controller is not None:
        controller.hook.last_readback = None
        controller.begin_pass(mode, strength, attention_mask=enc["attention_mask"])
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new, min_new_tokens=1, do_sample=False,
            num_beams=1, eos_token_id=eos_ids, pad_token_id=tokenizer.pad_token_id,
        )
    readback = None
    if controller is not None:
        rb = controller.hook.last_readback
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
    return results


# --------------------------------------------------------------------------
# baseline (shared across all layers/arms/doses)
# --------------------------------------------------------------------------

def run_baseline(model, tokenizer, device, rows: list[dict[str, Any]], batch_size: int, tag: str) -> dict[str, dict]:
    log_name = f"{tag}__baseline" if tag == "smoke" else "baseline"
    run_config = {
        "stage": "baseline", "tag": tag, "model": MODEL_NAME, "revision": MODEL_REVISION,
        "seed": SEED, "max_new_tokens": MAX_NEW,
    }
    log = RunLog(runlog_path(log_name), run_config=run_config)
    done = log.done_keys()
    pending = [r for r in rows if r["row_key"] not in done]
    print(f"[{log_name}] {len(rows) - len(pending)}/{len(rows)} already done, {len(pending)} pending", flush=True)
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [render(tokenizer, r["question"]) for r in batch]
        gen = run_batch_fixed(model, tokenizer, device, None, prompts, "off", 0.0, MAX_NEW)
        for row, res in zip(batch, gen):
            grade = grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            log.record(row["row_key"], {
                "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "answer_text": res["text"], **grade,
            })
        print(f"[{log_name}] {min(i + batch_size, len(pending))}/{len(pending)} ({time.time() - t0:.0f}s)", flush=True)
    log.finalize({"n_rows": len(rows)})
    log.close()
    return {r["row_key"]: r for r in load_jsonl(runlog_path(log_name))}


# --------------------------------------------------------------------------
# one arm at one dose for one layer
# --------------------------------------------------------------------------

def run_arm_dose(
    model, tokenizer, device, controller, arm: str, hs_index: int,
    dose_mult: float, dose_abs: float, gain: float,
    rows: list[dict[str, Any]], batch_size: int,
    known_rows_all: list[dict[str, Any]], baseline_by_key: dict[str, dict],
    tag: str,
) -> dict[str, Any]:
    log_name = f"{tag}__hs{hs_index}__{arm}" if tag == "smoke" else f"hs{hs_index}__{arm}"
    run_config = {
        "stage": "dose_ladder", "tag": tag, "model": MODEL_NAME, "revision": MODEL_REVISION,
        "hs_index": hs_index, "arm": arm, "seed": SEED, "max_new_tokens": MAX_NEW,
    }
    log = RunLog(runlog_path(log_name), run_config=run_config)
    keys = {r["row_key"]: f"{dose_mult}|{r['row_key']}" for r in rows}
    done = log.done_keys()
    pending = [r for r in rows if keys[r["row_key"]] not in done]
    print(
        f"[{log_name}/dose_{dose_mult}] {len(rows) - len(pending)}/{len(rows)} already done, "
        f"{len(pending)} pending", flush=True,
    )
    t0 = time.time()
    for i in range(0, len(pending), batch_size):
        batch = pending[i:i + batch_size]
        prompts = [render(tokenizer, r["question"]) for r in batch]
        gen = run_batch_fixed(model, tokenizer, device, controller, prompts, "gen_stream", gain, MAX_NEW)
        for row, res in zip(batch, gen):
            grade = grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
            log.record(keys[row["row_key"]], {
                "row_key": row["row_key"], "role": row["role"], "category_canon": row.get("category_canon"),
                "arm": arm, "hs_index": hs_index, "dose_multiplier": dose_mult, "dose_abs": dose_abs, "gain": gain,
                "n_new_tokens": res["n_new_tokens"], "terminated_naturally": res["terminated_naturally"],
                "readback_measured": res["readback_measured"], "answer_text": res["text"], **grade,
            })
        print(
            f"[{log_name}/dose_{dose_mult}] {min(i + batch_size, len(pending))}/{len(pending)} "
            f"({time.time() - t0:.0f}s)", flush=True,
        )
    log.finalize({"n_rows_this_dose": len(rows), "dose_abs": dose_abs, "gain": gain})
    log.close()

    all_records = load_jsonl(runlog_path(log_name))
    written_this_dose = {r["row_key"]: r for r in all_records if r.get("dose_multiplier") == dose_mult}
    active_keys = {r["row_key"] for r in rows}

    confab_active = [
        written_this_dose[k] for k in active_keys
        if k in written_this_dose and written_this_dose[k]["role"] == "confab"
    ]
    known_all = []
    for r in known_rows_all:
        rk = r["row_key"]
        rec = written_this_dose.get(rk) if rk in active_keys else baseline_by_key.get(rk)
        if rec is not None:
            known_all.append(rec)

    return {
        "dose_mult": dose_mult, "dose_abs": dose_abs, "gain": gain, "n_active": len(rows),
        "confab_active": _rate_summary(confab_active),
        "known_all_covered": len(known_all), "known_all": _rate_summary(known_all),
    }


# --------------------------------------------------------------------------
# smoke
# --------------------------------------------------------------------------

def cmd_smoke(args: argparse.Namespace) -> int:
    check_env()
    cfg = load_yaml(CELL_YAML_PATH)
    rows = load_fit_rows()

    model, tokenizer, device = load_model()
    tensors = load_anchor_tensors()
    build_manifest = load_json(BUILD_MANIFEST_PATH)

    hs_index = args.smoke_layer
    layer_key = f"hs{hs_index}"
    build = build_manifest["layers"][layer_key]
    sigma_c = build["sigma_c"]
    assert_dose_grid_consistent(cfg, hs_index, sigma_c)

    fired_rows, _ = compute_fire_decisions(
        hs_index, rows, tensors, build["mu_d"], build["sigma_d"], build["tau_frozen"]
    )
    fired_sorted = sorted(fired_rows, key=lambda r: r["row_key"])
    smoke_rows = fired_sorted[: args.n_rows]
    print(f"[smoke] hs{hs_index}: n_fired={len(fired_rows)}/{len(rows)}, "
          f"smoke rows={[r['row_key'] for r in smoke_rows]}", flush=True)

    dose_mult = args.smoke_dose_mult
    dose_abs = dose_mult * sigma_c

    # Smoke-only reduced permutation size: production run_arm_dose draws
    # exactly n_fired (see cmd_full); at smoke scale that would mean running
    # ~n_fired rows through permuted_gate, defeating the point of a bounded
    # smoke. This exercises the SAME selection/write/grade/RunLog code path
    # at args.n_rows scale instead, documented here as a smoke-only override.
    rng = np.random.default_rng(SEED + 2000 + hs_index)
    permuted_idx = sorted(rng.choice(len(rows), size=args.n_rows, replace=False).tolist())
    permuted_rows = [rows[i] for i in permuted_idx]
    print(f"[smoke] permuted_gate smoke subset (reduced size, NOT n_fired): "
          f"{[r['row_key'] for r in permuted_rows]}", flush=True)

    baseline_rows = smoke_rows
    baseline_by_key = run_baseline(model, tokenizer, device, baseline_rows, args.batch_size, tag="smoke")

    layer_dir = COMMITTED / "directions" / layer_key
    c_hat_vec = torch.tensor(load_json(layer_dir / "c_hat.json")["vector"], dtype=torch.float32)
    rand_vec = torch.tensor(load_json(layer_dir / "random_direction.json")["vector"], dtype=torch.float32)

    hook_c = InterventionHook(law="erase_write", direction=c_hat_vec, sigma=sigma_c,
                               position="anchor_onward", measure_readback=True)
    ctrl_c = GenerationInterventionController(hook_c)
    hook_r = InterventionHook(law="erase_write", direction=rand_vec, sigma=1.0,
                               position="anchor_onward", measure_readback=True)
    ctrl_r = GenerationInterventionController(hook_r)

    layer_module = get_decoder_layer(model, hs_index - 1)

    results: dict[str, Any] = {}
    handle_c = layer_module.register_forward_hook(ctrl_c)
    try:
        results["gated"] = run_arm_dose(
            model, tokenizer, device, ctrl_c, "gated", hs_index, dose_mult, dose_abs, dose_mult,
            smoke_rows, args.batch_size, [], baseline_by_key, tag="smoke",
        )
        results["permuted_gate"] = run_arm_dose(
            model, tokenizer, device, ctrl_c, "permuted_gate", hs_index, dose_mult, dose_abs, dose_mult,
            permuted_rows, args.batch_size, [], baseline_by_key, tag="smoke",
        )
    finally:
        handle_c.remove()
        ctrl_c.reset()

    handle_r = layer_module.register_forward_hook(ctrl_r)
    try:
        gain_random = dose_abs / 1.0
        results["random_direction"] = run_arm_dose(
            model, tokenizer, device, ctrl_r, "random_direction", hs_index, dose_mult, dose_abs, gain_random,
            smoke_rows, args.batch_size, [], baseline_by_key, tag="smoke",
        )
    finally:
        handle_r.remove()
        ctrl_r.reset()

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS / "smoke_dose_ladder_summary.json"
    summary = {
        "hs_index": hs_index, "sigma_c": sigma_c, "dose_mult": dose_mult, "dose_abs": dose_abs,
        "n_fired_full_layer": len(fired_rows), "n_rows_full_layer": len(rows),
        "smoke_rows": [r["row_key"] for r in smoke_rows],
        "permuted_smoke_rows": [r["row_key"] for r in permuted_rows],
        "arms": results,
    }
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))
    return 0


# --------------------------------------------------------------------------
# full (NOT executed by this amendment -- see AMENDMENT.md)
# --------------------------------------------------------------------------

def cmd_full(args: argparse.Namespace) -> int:
    if not args.i_know_this_launches_the_full_stage_c_ladder:
        print(
            "[full] Stage C is NOT executed as evidence by this amendment until "
            "sign (AMENDMENT.md); refusing without "
            "--i-know-this-launches-the-full-stage-c-ladder",
            file=sys.stderr,
        )
        return 2

    check_env()
    cfg = load_yaml(CELL_YAML_PATH)
    rows = load_fit_rows()
    known_rows_all = [r for r in rows if r["role"] == "known_correct_answered"]

    model, tokenizer, device = load_model()
    tensors = load_anchor_tensors()
    build_manifest = load_json(BUILD_MANIFEST_PATH)

    baseline_by_key = run_baseline(model, tokenizer, device, rows, args.batch_size, tag="full")

    layers = [int(x) for x in args.layers.split(",")]
    summary: dict[str, Any] = {"layers": {}}
    for hs_index in layers:
        layer_key = f"hs{hs_index}"
        build = build_manifest["layers"][layer_key]
        sigma_c = build["sigma_c"]
        assert_dose_grid_consistent(cfg, hs_index, sigma_c)

        fired_rows, _ = compute_fire_decisions(
            hs_index, rows, tensors, build["mu_d"], build["sigma_d"], build["tau_frozen"]
        )
        n_fired = len(fired_rows)
        rng = np.random.default_rng(SEED + 2000 + hs_index)
        permuted_idx = sorted(rng.choice(len(rows), size=n_fired, replace=False).tolist())
        permuted_rows = [rows[i] for i in permuted_idx]

        layer_dir = COMMITTED / "directions" / layer_key
        c_hat_vec = torch.tensor(load_json(layer_dir / "c_hat.json")["vector"], dtype=torch.float32)
        rand_vec = torch.tensor(load_json(layer_dir / "random_direction.json")["vector"], dtype=torch.float32)
        hook_c = InterventionHook(law="erase_write", direction=c_hat_vec, sigma=sigma_c,
                                   position="anchor_onward", measure_readback=True)
        ctrl_c = GenerationInterventionController(hook_c)
        hook_r = InterventionHook(law="erase_write", direction=rand_vec, sigma=1.0,
                                   position="anchor_onward", measure_readback=True)
        ctrl_r = GenerationInterventionController(hook_r)
        layer_module = get_decoder_layer(model, hs_index - 1)

        dose_results: dict[Any, Any] = {}
        handle_c = layer_module.register_forward_hook(ctrl_c)
        try:
            for mult in DOSE_MULTIPLIERS:
                dose_abs = mult * sigma_c
                dose_results.setdefault(mult, {})["gated"] = run_arm_dose(
                    model, tokenizer, device, ctrl_c, "gated", hs_index, mult, dose_abs, mult,
                    fired_rows, args.batch_size, known_rows_all, baseline_by_key, tag="full",
                )
                dose_results.setdefault(mult, {})["permuted_gate"] = run_arm_dose(
                    model, tokenizer, device, ctrl_c, "permuted_gate", hs_index, mult, dose_abs, mult,
                    permuted_rows, args.batch_size, known_rows_all, baseline_by_key, tag="full",
                )
        finally:
            handle_c.remove()
            ctrl_c.reset()

        handle_r = layer_module.register_forward_hook(ctrl_r)
        try:
            for mult in DOSE_MULTIPLIERS:
                dose_abs = mult * sigma_c
                gain_random = dose_abs / 1.0
                dose_results.setdefault(mult, {})["random_direction"] = run_arm_dose(
                    model, tokenizer, device, ctrl_r, "random_direction", hs_index, mult, dose_abs, gain_random,
                    fired_rows, args.batch_size, known_rows_all, baseline_by_key, tag="full",
                )
        finally:
            handle_r.remove()
            ctrl_r.reset()

        summary["layers"][layer_key] = {"sigma_c": sigma_c, "n_fired": n_fired, "doses": dose_results}

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    out_path = ANALYSIS / "dose_ladder_full_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"[full] wrote {out_path}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_smoke = sub.add_parser("smoke", help="instrument validation only, tiny row count")
    p_smoke.add_argument("--layer", type=int, default=23, dest="smoke_layer")
    p_smoke.add_argument("--dose-mult", type=float, default=8.0, dest="smoke_dose_mult")
    p_smoke.add_argument("--n-rows", type=int, default=2)
    p_smoke.add_argument("--batch-size", type=int, default=8)
    p_smoke.set_defaults(func=cmd_smoke)

    p_full = sub.add_parser("full", help="the signed evidence run -- not executed by this amendment")
    p_full.add_argument("--layers", default=",".join(str(x) for x in CANDIDATE_LAYERS_HS))
    p_full.add_argument("--batch-size", type=int, default=8)
    p_full.add_argument("--i-know-this-launches-the-full-stage-c-ladder", action="store_true")
    p_full.set_defaults(func=cmd_full)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
