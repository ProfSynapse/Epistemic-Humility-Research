#!/usr/bin/env python3
"""Mine additional bf16 raw-base A0 known-correct rows for G2 power.

This is a pre-sign prerequisite helper for `doubt-gated-caution-tighten`.
It reads the existing AH expansion answerable candidates, runs the SAME
AH-A0 raw-base render surface as the steer cell (`unsloth/Qwen3-4B`, bf16,
no adapter, no prime), and writes text-bearing generation rows only under
gitignored `analysis/`.

Committed downstream artifacts must remain ID-only: this file's output is
scratch input to extraction/materialization, not a public artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
RENDER_DIR = HERE.parent / "common" / "renders"
EVAL_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/eval")

for p in (str(HERE), str(RENDER_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import grader  # noqa: E402
from ah_a0_raw_base_render import render  # noqa: E402

MODEL_NAME = "unsloth/Qwen3-4B"
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
EXPANSION_CANDIDATES = (
    CANONICAL
    / "experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)
AH_A0_ROWS = (
    CANONICAL / "experiment/phase1/probe/analysis/ah_main/gen_A0/rows.jsonl"
)
DEFAULT_OUT = ANALYSIS / "mined_a0_known_correct_rows.jsonl"
DEFAULT_ALL_OUT = ANALYSIS / "mined_a0_answerable_generations.jsonl"
DEFAULT_MANIFEST = ANALYSIS / "mined_a0_known_correct_manifest.json"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def existing_known_correct_count() -> tuple[int, set[str]]:
    rows = load_jsonl(AH_A0_ROWS)
    keys = {
        r["row_key"]
        for r in rows
        if r.get("gold_class") == "answerable"
        and r.get("answered") is True
        and r.get("correct") is True
    }
    return len(keys), keys


def load_candidates(existing_keys: set[str], limit: int | None, source_order: list[str]) -> list[dict]:
    rows = []
    for r in load_jsonl(EXPANSION_CANDIDATES):
        if r.get("label") != "known":
            continue
        if r["row_key"] in existing_keys:
            continue
        aliases = r.get("aliases") or []
        if not aliases:
            continue
        rows.append(
            {
                "row_key": r["row_key"],
                "question": r["question"],
                "aliases": aliases,
                "source": r.get("source") or "unknown",
                "category_canon": r.get("category") or r.get("source") or "answerable",
            }
        )
    rank = {source: i for i, source in enumerate(source_order)}
    rows.sort(key=lambda r: (rank.get(r["source"], len(rank)), r["row_key"]))
    return rows[:limit] if limit else rows


def resolve_eos_ids(tokenizer) -> list[int]:
    ids = set()
    if tokenizer.eos_token_id is not None:
        ids.add(int(tokenizer.eos_token_id))
    im_end = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if im_end is not None and im_end != getattr(tokenizer, "unk_token_id", None):
        ids.add(int(im_end))
    return sorted(ids)


def load_model():
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME, device_map="auto", dtype=torch.bfloat16
    )
    model.eval()
    return model, tokenizer


def read_existing_generation_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        out.setdefault(row["row_key"], row)
    return out


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(args: argparse.Namespace) -> int:
    existing_count, existing_keys = existing_known_correct_count()
    target_total = args.target_total_known_correct
    need = max(0, target_total - existing_count)
    print(
        f"[mine] existing known_correct_answered={existing_count}; "
        f"target_total={target_total}; need_new={need}",
        flush=True,
    )
    if need == 0:
        return 0

    source_order = [s.strip() for s in args.source_order.split(",") if s.strip()]
    candidates = load_candidates(existing_keys, args.max_candidates, source_order)
    print(f"[mine] candidate answerable rows available={len(candidates)}", flush=True)
    print(f"[mine] source_order={source_order}", flush=True)
    prior = read_existing_generation_rows(Path(args.all_out))
    if prior:
        print(f"[mine] resume rows already generated={len(prior)}", flush=True)

    model, tokenizer = load_model()
    device = next(model.parameters()).device
    eos_ids = resolve_eos_ids(tokenizer)

    all_rows: list[dict] = []
    mined: list[dict] = []
    t0 = time.time()

    try:
        for i, row in enumerate(candidates, start=1):
            rec = prior.get(row["row_key"])
            if rec is None:
                prompt = render(row)
                enc = tokenizer(prompt, return_tensors="pt").to(device)
                prompt_len = int(enc["input_ids"].shape[1])
                with torch.no_grad():
                    out = model.generate(
                        **enc,
                        max_new_tokens=args.max_new_tokens,
                        min_new_tokens=1,
                        do_sample=False,
                        num_beams=1,
                        eos_token_id=eos_ids,
                        pad_token_id=tokenizer.pad_token_id,
                    )
                new_tokens = out[0, prompt_len:]
                answer_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
                grade = grader.grade_one(answer_text, row["aliases"])
                rec = {
                    **row,
                    "role": "known_correct_answered",
                    "gold_class": "answerable",
                    "answer_text": answer_text,
                    "answered": grade["answered"],
                    "refused": grade["refused"],
                    "degenerate": grade["degenerate"],
                    "correct": grade["correct"],
                    "well_formed_correct": grade["well_formed_correct"],
                    "prompt_len": prompt_len,
                    "n_new_tokens": int(new_tokens.shape[0]),
                    "terminated_naturally": int(new_tokens.shape[0]) < args.max_new_tokens,
                    "mined_by": "doubt-gated-caution-tighten/mine_known_correct.py",
                    "model_name": MODEL_NAME,
                    "substrate": "bf16",
                }
            all_rows.append(rec)
            if rec.get("answered") is True and rec.get("correct") is True:
                mined.append(rec)

            if i % args.flush_every == 0:
                write_jsonl(Path(args.all_out), all_rows)
                write_jsonl(Path(args.out), mined)

            total = existing_count + len(mined)
            if i % 25 == 0 or total >= target_total:
                elapsed = time.time() - t0
                print(
                    f"[mine] scanned={i}/{len(candidates)} new_correct={len(mined)} "
                    f"total_correct={total} elapsed={elapsed:.0f}s",
                    flush=True,
                )
            if total >= target_total:
                break
    finally:
        del model
        torch.cuda.empty_cache()

    write_jsonl(Path(args.all_out), all_rows)
    write_jsonl(Path(args.out), mined)
    manifest = {
        "stage": "doubt_gated_caution_tighten_g2_known_correct_mining",
        "model_name": MODEL_NAME,
        "substrate": "bf16",
        "existing_known_correct_answered": existing_count,
        "target_total_known_correct": target_total,
        "new_known_correct_answered": len(mined),
        "total_known_correct_answered": existing_count + len(mined),
        "scanned_candidates": len(all_rows),
        "candidate_source": str(EXPANSION_CANDIDATES),
        "all_generations_path": str(Path(args.all_out).resolve()),
        "known_correct_rows_path": str(Path(args.out).resolve()),
        "runtime_sec": round(time.time() - t0, 1),
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-total-known-correct", type=int, default=430)
    ap.add_argument("--max-candidates", type=int, default=2000)
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--source-order", default="triviaqa,popqa")
    ap.add_argument("--flush-every", type=int, default=25)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--all-out", default=str(DEFAULT_ALL_OUT))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    return ap.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
