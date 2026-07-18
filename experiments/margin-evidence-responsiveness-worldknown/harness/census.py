#!/usr/bin/env python3
"""World-known correctness+abstention census for margin-evidence-
responsiveness-worldknown (M4-WK) (cell.yaml `population.census`).

GPU. One greedy generation per PopQA test row (full pool, 14267) under the
frozen BASELINE_SYSTEM_PROMPT + chat template (render.py, context=None: the
no_answer_baseline arm's exact prompt shape), in ONE pinned, recorded
batching regime (batching.py). No steering, no InterventionHook -- this is a
plain unsteered generation pass, graded via gen_lib.grade_row (detector_v2 +
grader, byte-identical stack).

Outputs:
  analysis/runlog/census.jsonl                                  gitignored,
      full RunLog (resumable, checkpointed per batch): every gen_lib.grade_row
      field + generation_text + PopQA metadata.
  analysis/census/qwen35_4b_worldknown_gen_text.jsonl            gitignored
      sidecar: {row_key, generation_text, prop, source_id, s_pop,
      matched_pattern_ids, gold_aliases_present, answered_v2}. Question text,
      answer text (gold + generated), and category live ONLY here.
  analysis-committed/census/qwen35_4b_worldknown_census.jsonl     COMMITTED:
      {row_key, role, question_sha, correct_v2, refused_v2} ONLY. NO
      generation_text, NO question text, NO answer text inline (MAJOR M3).
  analysis-committed/census/census_manifest.json                 COMMITTED:
      role counts, batch composition record, runlog sha256.

Refuses to run the FULL pool without a passing preflight PASS marker
(mirrors M1/M2's own preflight-gate convention); `--rows N` runs a smoke
subset bypassing that gate for build/debug use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
TUNER_DIR = REPO_ROOT / "synaptic-tuner"
for _p in (str(TUNER_DIR), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config  # noqa: E402
import common  # noqa: E402
import batching  # noqa: E402
import gen_lib  # noqa: E402
import popqa_pool  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
RUNLOG_PATH = ANALYSIS / "runlog" / "census.jsonl"
GEN_TEXT_SIDECAR = ANALYSIS / "census" / "qwen35_4b_worldknown_gen_text.jsonl"
COMMITTED_CENSUS = COMMITTED / "census" / "qwen35_4b_worldknown_census.jsonl"
CENSUS_MANIFEST = COMMITTED / "census" / "census_manifest.json"


def load_model_for_census():
    import os

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    os.environ["M4WK_RENDER_MODEL"] = config.MODEL_REPO
    os.environ["M4WK_RENDER_REVISION"] = config.MODEL_REVISION

    tokenizer = AutoTokenizer.from_pretrained(config.MODEL_REPO, revision=config.MODEL_REVISION, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(
        config.MODEL_REPO, revision=config.MODEL_REVISION, dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True,
    )
    model.eval()
    device = next(model.parameters()).device
    return model, tokenizer, device


def generate_batch_plain(model, tokenizer, device, prompts: list[str], max_new: int) -> list[dict[str, Any]]:
    import torch

    eos_ids = gen_lib.resolve_eos_ids(tokenizer)
    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        out = model.generate(
            **enc, max_new_tokens=max_new, min_new_tokens=1, do_sample=False,
            num_beams=1, eos_token_id=eos_ids, pad_token_id=tokenizer.pad_token_id,
        )
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
        results.append({"text": text, "n_new_tokens": n_new, "terminated_naturally": terminated_naturally})
    return results


def run_census(rows: list[dict[str, Any]], batch_size: int, runlog_path: Path) -> dict[str, Any]:
    from shared.utilities.run_log import RunLog

    import render as render_mod

    # `rows` is already in canonical order (caller's responsibility); this
    # just records that composition for the single-regime attestation.
    composition = batching.batch_composition_record(rows, batch_size)

    log = RunLog(runlog_path, run_config={"stage": "census", "n_rows": len(rows), "batch_size": batch_size, "row_order_sha256": composition["row_order_sha256"]}, fresh=False)
    model, tokenizer, device = load_model_for_census()

    pending = [r for r in rows if r["row_key"] not in log.done_keys()]
    batches = batching.make_batches(pending, batch_size)
    t0 = time.time()
    n_done = len(rows) - len(pending)
    n_generated = 0
    try:
        for batch in batches:
            prompts = [render_mod.render({"row_key": r["row_key"], "question": r["question"], "context": None}) for r in batch]
            gen = generate_batch_plain(model, tokenizer, device, prompts, config.GEN_MAX_NEW_TOKENS)
            for row, res in zip(batch, gen):
                grade = gen_lib.grade_row(res["text"], res["terminated_naturally"], row.get("aliases"))
                rec = {
                    "row_key": row["row_key"], "popqa_id": row["popqa_id"], "prop": row["category"],
                    "generation_text": res["text"], "n_new_tokens": res["n_new_tokens"],
                    **grade,
                }
                log.record(row["row_key"], rec)
            n_done += len(batch)
            n_generated += len(batch)
            print(f"[census] {n_done}/{len(rows)} ({time.time() - t0:.0f}s)", flush=True)
    finally:
        try:
            import gc

            import torch
            del model
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        log.close()

    log2 = RunLog(runlog_path, run_config={"stage": "census", "n_rows": len(rows), "batch_size": batch_size, "row_order_sha256": composition["row_order_sha256"]}, fresh=False)
    if set(log2.done_keys()) == {r["row_key"] for r in rows}:
        log2.finalize({"n_rows": len(rows)})
    log2.close()
    composition["generation_only_elapsed_sec"] = round(time.time() - t0, 2)
    composition["n_generated_this_call"] = n_generated
    return composition


def _role_of(grade: dict[str, Any]) -> str:
    if grade.get("degenerate"):
        return "excluded"
    if grade.get("refused_v2"):
        return "refused_on_answerable"
    if grade.get("answered_v2") and grade.get("correct_v2") is False:
        return "confab_on_answerable"
    if grade.get("answered_v2") and grade.get("correct_v2") is True:
        return "correct_on_answerable"
    return "excluded"


def derive_outputs(pool: dict[str, dict[str, Any]]) -> dict[str, Any]:
    runlog_rows = common.load_jsonl(RUNLOG_PATH)
    by_key = {r["row_key"]: r for r in runlog_rows}
    missing = [rk for rk in pool if rk not in by_key]
    if missing:
        raise SystemExit(f"census FAIL: {len(missing)} pool rows missing from runlog, e.g. {missing[:5]}")

    gen_text_rows = []
    committed_rows = []
    role_counts: dict[str, int] = {}
    for rk, meta in pool.items():
        rec = by_key[rk]
        role = _role_of(rec)
        role_counts[role] = role_counts.get(role, 0) + 1
        question_sha = hashlib.sha256(meta["question"].encode("utf-8")).hexdigest()
        gen_text_rows.append({
            "row_key": rk, "generation_text": rec["generation_text"], "prop": meta["category"],
            "source_id": meta["popqa_id"], "matched_pattern_ids": rec.get("matched_pattern_ids", []),
            "gold_aliases_present": bool(meta.get("aliases")), "answered_v2": bool(rec.get("answered_v2")),
        })
        committed_rows.append({
            "row_key": rk, "role": role, "question_sha": question_sha,
            "correct_v2": rec.get("correct_v2"), "refused_v2": bool(rec.get("refused_v2")),
        })

    GEN_TEXT_SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    common.write_jsonl(GEN_TEXT_SIDECAR, sorted(gen_text_rows, key=lambda r: r["row_key"]))
    COMMITTED_CENSUS.parent.mkdir(parents=True, exist_ok=True)
    common.write_jsonl(COMMITTED_CENSUS, sorted(committed_rows, key=lambda r: r["row_key"]))

    return {"role_counts": role_counts, "n_rows": len(pool)}


THROUGHPUT_PROBE_PATH = HERE.parent / "analysis" / "preflight" / "census_throughput_probe.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", type=int, default=None, help="cap population to first N rows (smoke/throughput-probe; writes the mandatory census throughput probe record instead of gating on it)")
    ap.add_argument("--batch-size", type=int, default=config.CENSUS_BATCH_SIZE)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true")
    args = ap.parse_args()

    if not args.i_know_this_runs_on_gpu:
        print("[census] this loads the model and generates on GPU; refusing without --i-know-this-runs-on-gpu.", file=sys.stderr)
        return 2

    config.assert_pinned_hashes()

    # gates.yaml SC1_dose_and_preflight: "MANDATORY throughput probe (8-row
    # rate) before the full census" -- census has no dose/setpoint (plain
    # unsteered generation), so this is a throughput measurement, not the
    # dosed capture+generation PASS marker gate that channel1/channel2 use.
    if args.rows is None and not THROUGHPUT_PROBE_PATH.is_file():
        raise SystemExit(
            f"census FAIL: full census requested (--rows omitted) but no "
            f"throughput probe record at {THROUGHPUT_PROBE_PATH}; run "
            f"`census.py --rows 8 --i-know-this-runs-on-gpu` first."
        )

    pool = popqa_pool.load_pool()
    ordered_keys = batching.canonical_order(list(pool.keys()))
    rows = [pool[rk] for rk in ordered_keys]
    if args.rows is not None:
        rows = rows[: args.rows]
        runlog_path = ANALYSIS / "runlog" / f"census_smoke_{args.rows}.jsonl"
    else:
        runlog_path = RUNLOG_PATH

    composition = run_census(rows, args.batch_size, runlog_path)

    if args.rows is not None:
        gen_elapsed = composition["generation_only_elapsed_sec"]
        n_gen = max(1, composition["n_generated_this_call"])
        probe = {
            "n_rows": len(rows), "generation_only_elapsed_sec": gen_elapsed,
            "sec_per_row": round(gen_elapsed / n_gen, 3),
            "estimated_full_pool_sec": round(gen_elapsed / n_gen * config.POPQA_N_ROWS, 1),
            "note": "excludes one-time model-load time; measures the batched-generation loop only",
            "composition": composition,
        }
        THROUGHPUT_PROBE_PATH.parent.mkdir(parents=True, exist_ok=True)
        common.write_json(THROUGHPUT_PROBE_PATH, probe)
        print(json.dumps({"smoke_rows": len(rows), "throughput_probe": probe}, indent=2), flush=True)
        return 0

    summary = derive_outputs(pool)
    manifest = {
        "family": config.FAMILY, "model": config.MODEL_REPO, "revision": config.MODEL_REVISION,
        "batch_composition": composition, "role_counts": summary["role_counts"], "n_rows": summary["n_rows"],
        "runlog_sha256": common.sha256_of_file(RUNLOG_PATH), "committed_census_sha256": common.sha256_of_file(COMMITTED_CENSUS),
    }
    common.write_json(CENSUS_MANIFEST, manifest)
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
