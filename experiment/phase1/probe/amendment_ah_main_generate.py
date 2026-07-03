#!/usr/bin/env python3
"""Amendment AH MAIN RUN (script 1/3) — three-arm divergent-pool generation (GPU).

Locked spec: experiment/protocol/AMENDMENT-AH-divergent-pool-own-readout.md §3.2-3.3.
SIGNED (PR #174), launch approved 2026-07-03. Runner owns build+run+score;
adjudication is the orchestrator's.

Byte-frozen AF harness (amendment_af_generate.py lineage):
  raw base unsloth/Qwen3-4B-bnb-4bit, no adapter, bfloat16, cuda
  batch=1 sequential, greedy (do_sample=False, num_beams=1), max_new_tokens 96
  enable_thinking=False, system = prime + " " + baseline_system
  refusal = scorers.is_stated_confidence_refusal; content-end = _content_end_index
  PRIME_HIGH / PRIME_LOW imported verbatim from amendment_af_generate.

Arms (per-row renderings, §3.3):
  A0 (no prime, baseline_system only) : ALL 1,662 pool rows.
  A-certain (PRIME_HIGH)              : release-contrast rows (669+669 = 1,338).
  A-doubt   (PRIME_LOW)               : muzzle rows (87+87) + positive-control (150) = 324.
  Total 3,324 generations.

Correctness grading (Cheng lineage, scorers.is_correct) is applied to
gold-answerable rows that carry aliases (needed for G1 descriptives + induced-
confabulation counts on unanswerables, §8 caveat 2). Aliases are re-joined by
row_key from the two candidate files (the pool file does not carry them).

Degeneracy flag: a generation is degenerate if the decoded answer is empty, or
a single token repeats >= DEGEN_RUN times consecutively (AG lineage cheap check).

Outputs (canonical, gitignored) under analysis/ah_main/:
  gen_A0/rows.jsonl, gen_Acertain/rows.jsonl, gen_Adoubt/rows.jsonl
  manifest.json (per-arm config SHA + counts)
  main_run.log is the process log (redirected by the launcher).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

PROBE_DIR = Path(__file__).resolve().parent
EVAL_DIR = PROBE_DIR.parent / "eval"
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402
from backends import render_probe_prompt  # noqa: E402
from amendment_s_correctness_probe_extract import (  # noqa: E402
    MODEL_NAME, MODEL_TAG, _config_sha, _content_end_index,
)
from amendment_af_generate import PRIME_HIGH, PRIME_LOW  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
AC_CONFIG = PROBE_DIR / "config" / "phase3_ac_doubt_coupled_intervention.yaml"
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
DEFAULT_POOL = STAGE0 / "expansion" / "pool_v21.jsonl"
CAND_FILES = [
    STAGE0 / "candidates.jsonl",
    STAGE0 / "expansion" / "expansion_candidates.jsonl",
]
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_main"

EXPECTED_POOL = 1662
DEGEN_RUN = 12


def load_baseline_system_prompt() -> str:
    with AC_CONFIG.open("r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg["prompt"]["system"]


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def load_candidate_lookup():
    """row_key -> {question, aliases} joined from both candidate files."""
    lut = {}
    for f in CAND_FILES:
        for r in load_jsonl(f):
            lut[r["row_key"]] = {"question": r["question"],
                                 "aliases": r.get("aliases", [])}
    return lut


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


def run(args) -> int:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = args.base_model or MODEL_NAME
    pool_path = Path(args.pool).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_system = load_baseline_system_prompt()
    pool = load_jsonl(pool_path)
    if not args.skip_count_check and len(pool) != EXPECTED_POOL:
        raise RuntimeError(f"pool has {len(pool)} rows, expected {EXPECTED_POOL}")
    cand = load_candidate_lookup()
    missing = [r["row_key"] for r in pool if r["row_key"] not in cand]
    if missing:
        raise RuntimeError(f"{len(missing)} pool rows missing question/aliases; "
                           f"first: {missing[:3]}")

    # Build the per-arm work lists (§3.3).
    #   A0        : every pool row.
    #   A-certain : release-contrast rows.
    #   A-doubt   : muzzle rows + positive-control rows.
    a0 = list(pool)
    a_certain = [r for r in pool if r["contrast"] == "release"]
    a_doubt = [r for r in pool if r["contrast"] in ("muzzle", "positive_control")]
    print(f"[ah/main] pool={len(pool)} | A0={len(a0)} "
          f"A-certain(release)={len(a_certain)} "
          f"A-doubt(muzzle+control)={len(a_doubt)} "
          f"total_gens={len(a0)+len(a_certain)+len(a_doubt)}", flush=True)

    print(f"[ah/main] loading RAW base {model_name} (no adapter) ...", flush=True)
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
        if arm == "A-certain":
            return PRIME_HIGH + " " + baseline_system
        if arm == "A-doubt":
            return PRIME_LOW + " " + baseline_system
        raise ValueError(arm)

    def config_for(arm: str):
        payload = {
            "amendment": "AH", "stage": "main_generate", "arm": arm,
            "base_model": model_name, "adapter": "NONE-raw-instruct-base",
            "model_tag": MODEL_TAG, "baseline_system_prompt": baseline_system,
            "prime": {"A0": None, "A-certain": PRIME_HIGH,
                      "A-doubt": PRIME_LOW}[arm],
            "pool_source": str(pool_path), "enable_thinking": False,
            "max_new_tokens": args.max_new_tokens, "decode": "greedy",
        }
        return payload, _config_sha(payload)

    arms = [("A0", a0, "gen_A0"),
            ("A-certain", a_certain, "gen_Acertain"),
            ("A-doubt", a_doubt, "gen_Adoubt")]

    manifest = {"amendment": "AH", "stage": "main_generate",
                "pool_source": str(pool_path), "n_pool": len(pool),
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
        t0 = time.time()
        written = 0
        with rows_path.open("w", encoding="utf-8") as rows_fh:
            for item in work:
                c = cand[item["row_key"]]
                question = c["question"]
                rendered, _mode = render_probe_prompt(
                    tokenizer, system_prompt, question,
                    enable_thinking=False)
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
                # induced confabulation: answered a gold-unanswerable question
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
                    "gold_class": item["gold_class"], "source": item["source"],
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
                if written % 100 == 0 or written == len(work):
                    el = time.time() - t0
                    print(f"[ah/main] arm={arm} {written}/{len(work)} "
                          f"{el:.0f}s ({written/el:.2f}/s) {counts}", flush=True)
        manifest["arms"][arm] = {
            **payload, "config_sha": config_sha, "n": len(work),
            "counts": counts, "rows": str(rows_path),
            "runtime_sec": round(time.time() - t0, 1),
        }
        print(f"[ah/main] arm={arm} DONE {counts} -> {rows_path}", flush=True)

    manifest["total_runtime_sec"] = round(time.time() - t_all, 1)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                          encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[ah/main] ALL DONE -> {out_dir}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--pool", default=str(DEFAULT_POOL))
    ap.add_argument("--base-model", default=None)
    ap.add_argument("--max-new-tokens", type=int, default=96)
    ap.add_argument("--skip-count-check", action="store_true",
                    help="smoke only: bypass the 1,662-row pool guard")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
