#!/usr/bin/env python3
"""Amendment AH Addendum A1 (script 2/3) — A0 + A-doubt on the recalibration
stratum (GPU).

Locked spec §10.1: re-run ONLY the positive control (A0 + A-doubt / PRIME_LOW
verbatim) on the 150-row caution-representative concordant-known stratum, on the
byte-frozen AF harness — batch-1 greedy, max_new_tokens 96, enable_thinking
False, system = prime + " " + baseline_system. ~300 generations.

Harness machinery (render, tokenizer special-id handling, generate call,
refusal/answered/degeneracy grading, per-arm config SHA, skip-resume) is IMPORTED
from amendment_ah_main_generate so this run is byte-identical to the main run.
Only the arm set and the work pool differ:
  A0      : all 150 stratum rows (baseline_system only)
  A-doubt : all 150 stratum rows (PRIME_LOW + baseline_system)

Outputs (canonical, gitignored) under analysis/ah_addendum_a1/:
  gen_A0/rows.jsonl, gen_Adoubt/rows.jsonl, manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ARCHIVE_AMENDMENTS_DIR = Path(__file__).resolve().parent
from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR), str(ARCHIVE_AMENDMENTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)
from amendment_af_generate import PRIME_LOW  # noqa: E402
from amendment_ah_main_generate import (  # noqa: E402
    load_baseline_system_prompt, load_jsonl, load_candidate_lookup,
    is_degenerate,
)

CANONICAL = repo_root()
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_addendum_a1"
DEFAULT_STRATUM = DEFAULT_OUT / "stratum.jsonl"
EXPECTED_STRATUM = 150


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = args.base_model or MODEL_NAME
    stratum_path = Path(args.stratum).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    stratum = load_jsonl(stratum_path)
    if not args.skip_count_check and len(stratum) != EXPECTED_STRATUM:
        raise RuntimeError(f"stratum has {len(stratum)} rows, "
                           f"expected {EXPECTED_STRATUM}")
    cand = load_candidate_lookup()
    missing = [r["row_key"] for r in stratum if r["row_key"] not in cand]
    if missing:
        raise RuntimeError(f"{len(missing)} stratum rows missing question/aliases; "
                           f"first: {missing[:3]}")

    print(f"[a1/gen] stratum={len(stratum)} | A0={len(stratum)} "
          f"A-doubt={len(stratum)} total_gens={2*len(stratum)}", flush=True)

    print(f"[a1/gen] loading RAW base {model_name} (no adapter) ...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    device = next(model.parameters()).device

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

    def system_for(arm: str) -> str:
        if arm == "A0":
            return baseline_system
        if arm == "A-doubt":
            return PRIME_LOW + " " + baseline_system
        raise ValueError(arm)

    def config_for(arm: str):
        # Byte-identical payload shape to amendment_ah_main_generate.config_for
        # so the config SHA is comparable across the main run and the addendum.
        payload = {
            "amendment": "AH", "stage": "main_generate", "arm": arm,
            "base_model": model_name, "adapter": "NONE-raw-instruct-base",
            "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
            "prime": {"A0": None, "A-doubt": PRIME_LOW}[arm],
            "pool_source": str(stratum_path), "enable_thinking": False,
            "max_new_tokens": args.max_new_tokens, "decode": "greedy",
        }
        return payload, _config_sha(payload)

    arms = [("A0", stratum, "gen_A0"),
            ("A-doubt", stratum, "gen_Adoubt")]

    manifest = {"amendment": "AH", "stage": "addendum_a1_generate",
                "stratum_source": str(stratum_path), "n_stratum": len(stratum),
                "arms": {}}
    t_all = time.time()

    for arm, work, subdir in arms:
        system_prompt = system_for(arm)
        payload, config_sha = config_for(arm)
        arm_dir = out_dir / subdir
        arm_dir.mkdir(parents=True, exist_ok=True)
        rows_path = arm_dir / "rows.jsonl"
        counts = {"answered": 0, "refused": 0, "ungradeable": 0,
                  "degenerate": 0, "correct": 0, "graded_answerable": 0,
                  "confab_on_unanswerable": 0}

        # --- RESUME (identical semantics to the main run) ---
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
                if pr.get("arm") != arm:
                    continue
                if pr.get("config_sha") != config_sha:
                    raise RuntimeError(
                        f"resume config_sha mismatch in {rows_path}: "
                        f"row {pr.get('row_key')} has {pr.get('config_sha')} "
                        f"!= current {config_sha}")
                if pr["row_key"] in done_keys:
                    continue
                done_keys.add(pr["row_key"])
                prior_rows.append(pr)
                if pr.get("answered"):
                    counts["answered"] += 1
                elif pr.get("refused"):
                    counts["refused"] += 1
                else:
                    counts["ungradeable"] += 1
                if pr.get("degenerate"):
                    counts["degenerate"] += 1
                if pr.get("confab_on_unanswerable"):
                    counts["confab_on_unanswerable"] += 1
                if pr.get("gold_class") == "answerable" and pr.get("correct") is not None:
                    counts["graded_answerable"] += 1
                    if pr.get("correct"):
                        counts["correct"] += 1
        remaining = [it for it in work if it["row_key"] not in done_keys]
        if done_keys:
            print(f"[a1/gen] arm={arm} RESUME: {len(done_keys)} present, "
                  f"{len(remaining)} remaining (of {len(work)})", flush=True)

        t0 = time.time()
        written = len(done_keys)
        with rows_path.open("w", encoding="utf-8") as rows_fh:
            for pr in prior_rows:
                rows_fh.write(json.dumps(pr, ensure_ascii=False) + "\n")
            rows_fh.flush()
            for item in remaining:
                c = cand[item["row_key"]]
                question = c["question"]
                rendered, _mode = render_probe_prompt(
                    tokenizer, system_prompt, question, enable_thinking=False)
                enc = tokenizer(rendered, return_tensors="pt").to(device)
                prompt_len = int(enc["input_ids"].shape[1])
                with torch.no_grad():
                    gen = model.generate(
                        **enc, max_new_tokens=args.max_new_tokens,
                        do_sample=False, num_beams=1, eos_token_id=eos_for_gen,
                        pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                        return_dict_in_generate=True)
                full_list = gen.sequences[0].tolist()
                new_ids = full_list[prompt_len:]
                answer_text = tokenizer.decode(new_ids, skip_special_tokens=True).strip()

                refused = scorers.is_stated_confidence_refusal(answer_text)
                content_end = _content_end_index(full_list, prompt_len, special_ids)
                answered = ((content_end is not None) and bool(answer_text)
                            and not refused)
                ungradeable = (not refused) and (not answered)
                degenerate = is_degenerate(answer_text)

                aliases = c["aliases"]
                is_answerable = (item["gold_class"] == "answerable")
                correct = None
                if is_answerable and aliases:
                    correct = bool(scorers.is_correct(answer_text, aliases))
                    counts["graded_answerable"] += 1
                    if correct:
                        counts["correct"] += 1
                confab = bool(answered and (not is_answerable))

                if answered:
                    counts["answered"] += 1
                elif refused:
                    counts["refused"] += 1
                else:
                    counts["ungradeable"] += 1
                if degenerate:
                    counts["degenerate"] += 1
                if confab:
                    counts["confab_on_unanswerable"] += 1

                rows_fh.write(json.dumps({
                    "row_key": item["row_key"], "safe_key": item["safe_key"],
                    "question": question, "aliases": aliases,
                    "arm": arm, "contrast": item["contrast"],
                    "congruent": item["congruent"], "stratum": item["stratum"],
                    "quintile": item.get("quintile"),
                    "gold_class": item["gold_class"], "source": item["source"],
                    "source_group": item.get("source_group", ""),
                    "category_canon": item.get("category_canon", ""),
                    "category_raw": item.get("category_raw", ""),
                    "caution_dist": item["caution_dist"],
                    "caution_dist_z": item["caution_dist_z"],
                    "score_L24": item["score_L24"],
                    "answer_text": answer_text, "refused": refused,
                    "answered": answered, "ungradeable": ungradeable,
                    "degenerate": degenerate, "correct": correct,
                    "confab_on_unanswerable": confab,
                    "prompt_len": prompt_len, "config_sha": config_sha,
                }, ensure_ascii=False) + "\n")
                rows_fh.flush()
                written += 1
                new_written = written - len(done_keys)
                if new_written % 50 == 0 or written == len(work):
                    el = time.time() - t0
                    rate = new_written / el if el else 0
                    print(f"[a1/gen] arm={arm} {written}/{len(work)} "
                          f"(+{new_written} this run) {el:.0f}s ({rate:.2f}/s) "
                          f"{counts}", flush=True)
        manifest["arms"][arm] = {
            **payload, "config_sha": config_sha, "n": len(work),
            "counts": counts, "rows": str(rows_path),
            "runtime_sec": round(time.time() - t0, 1),
        }
        print(f"[a1/gen] arm={arm} DONE {counts} -> {rows_path}", flush=True)

    manifest["total_runtime_sec"] = round(time.time() - t_all, 1)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                          encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[a1/gen] ALL DONE -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--stratum", default=str(DEFAULT_STRATUM))
    ap.add_argument("--base-model", default=None)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--skip-count-check", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
