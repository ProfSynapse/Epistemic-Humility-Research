#!/usr/bin/env python3
"""Mine a fresh private eval pool for the J-space layer-site replication.

This script reads the AH expansion candidate pool, excludes every row key used
by the predecessor J-space split, runs the same raw-base Qwen3-4B AH-A0 render,
and selects two fresh evaluation roles:

- confab: gold-unanswerable row where the raw base answers rather than refuses.
- known_correct_answered: gold-answerable row where the raw base answers
  correctly.

Question text, aliases, and baseline generations are written only under the
experiment's gitignored analysis/ directory. The public manifest contains row
keys, roles, source/category metadata, and counts only.

By default the script stops once the registered fresh-pool targets are met.
Use --scan-all-candidates for a resumable census over the full configured
candidate universe; that mode is intended for future reusable pool construction,
not as a license-cleared public text release.
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
COMMITTED = HERE / "analysis-committed"
SOURCE = HERE.parent / "j-space-midband-write-sweep-qwen3-4b"
RENDER_DIR = HERE.parent / "common" / "renders"
EVAL_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/archive/experiment/phase1/eval")

for p in (str(SOURCE), str(RENDER_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import grader  # noqa: E402
from ah_a0_raw_base_render import render  # noqa: E402

MODEL_NAME = "unsloth/Qwen3-4B"
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
EXPANSION_CANDIDATES = (
    CANONICAL
    / "archive/experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)
PREDECESSOR_SPLIT = (
    HERE.parent
    / "common/doubt-gated-caution-tighten-heldout-split/split_manifest.json"
)

DEFAULT_GENERATIONS = ANALYSIS / "fresh_pool_generations.jsonl"
DEFAULT_ROWS = ANALYSIS / "fresh_eval_rows.jsonl"
DEFAULT_PRIVATE_MANIFEST = ANALYSIS / "fresh_eval_pool_private_manifest.json"
DEFAULT_PUBLIC_MANIFEST = COMMITTED / "fresh_eval_pool_manifest.json"
REPO_ROOT = HERE.parents[1]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_existing_rows(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out: dict[str, dict] = {}
    for row in load_jsonl(path):
        out.setdefault(row["row_key"], row)
    return out


def predecessor_keys() -> set[str]:
    data = json.loads(PREDECESSOR_SPLIT.read_text(encoding="utf-8"))
    return {row["row_key"] for row in data["rows"]}


def candidate_rows(label: str, excluded: set[str], source_order: list[str]) -> list[dict]:
    rows = []
    for row in load_jsonl(EXPANSION_CANDIDATES):
        if row.get("label") != label:
            continue
        if row["row_key"] in excluded:
            continue
        if label == "known" and not row.get("aliases"):
            continue
        rows.append({
            "row_key": row["row_key"],
            "label": row["label"],
            "question": row["question"],
            "aliases": row.get("aliases", []),
            "source": row.get("source") or "unknown",
            "category_canon": (
                row.get("category_canon")
                or row.get("category")
                or row.get("source")
                or "unknown"
            ),
        })
    rank = {source: i for i, source in enumerate(source_order)}
    rows.sort(key=lambda r: (rank.get(r["source"], len(rank)), r["row_key"]))
    return rows


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


def generate_one(model, tokenizer, row: dict, max_new_tokens: int) -> dict:
    device = next(model.parameters()).device
    prompt = render(row)
    enc = tokenizer(prompt, return_tensors="pt").to(device)
    prompt_len = int(enc["input_ids"].shape[1])
    eos_ids = resolve_eos_ids(tokenizer)
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            min_new_tokens=1,
            do_sample=False,
            num_beams=1,
            eos_token_id=eos_ids,
            pad_token_id=tokenizer.pad_token_id,
        )
    new_tokens = out[0, prompt_len:]
    answer_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    grade = grader.grade_one(answer_text, row.get("aliases"))
    return {
        **row,
        "answer_text": answer_text,
        "answered": grade["answered"],
        "refused": grade["refused"],
        "degenerate": grade["degenerate"],
        "correct": grade["correct"],
        "well_formed_correct": grade["well_formed_correct"],
        "prompt_len": prompt_len,
        "n_new_tokens": int(new_tokens.shape[0]),
        "terminated_naturally": int(new_tokens.shape[0]) < max_new_tokens,
        "model_name": MODEL_NAME,
        "substrate": "bf16",
    }


def select_eval_rows(generated: list[dict]) -> list[dict]:
    selected = []
    for row in generated:
        if row["label"] == "unknown" and row.get("answered") is True:
            selected.append({
                "row_key": row["row_key"],
                "role": "confab",
                "question": row["question"],
                "aliases": [],
                "source": row.get("source"),
                "category_canon": row.get("category_canon"),
            })
        elif (
            row["label"] == "known"
            and row.get("answered") is True
            and row.get("correct") is True
        ):
            selected.append({
                "row_key": row["row_key"],
                "role": "known_correct_answered",
                "question": row["question"],
                "aliases": row.get("aliases", []),
                "source": row.get("source"),
                "category_canon": row.get("category_canon"),
            })
    return selected


def public_row(row: dict) -> dict:
    return {
        "row_key": row["row_key"],
        "role": row["role"],
        "source": row.get("source"),
        "category_canon": row.get("category_canon"),
    }


def public_generated_row(row: dict, role_by_key: dict[str, str]) -> dict:
    return {
        "row_key": row["row_key"],
        "gold_label": row.get("label"),
        "role": role_by_key.get(row["row_key"]),
        "source": row.get("source"),
        "category_canon": row.get("category_canon"),
        "answered": row.get("answered"),
        "refused": row.get("refused"),
        "degenerate": row.get("degenerate"),
        "correct": row.get("correct"),
        "well_formed_correct": row.get("well_formed_correct"),
        "prompt_len": row.get("prompt_len"),
        "n_new_tokens": row.get("n_new_tokens"),
        "terminated_naturally": row.get("terminated_naturally"),
    }


def display_path(path: Path) -> str:
    resolved = path.resolve()
    for root in (REPO_ROOT.resolve(), CANONICAL.resolve()):
        try:
            return str(resolved.relative_to(root))
        except ValueError:
            continue
    return str(path)


def write_manifests(args: argparse.Namespace, generated: list[dict], selected: list[dict], runtime: float) -> None:
    role_by_key = {row["row_key"]: row["role"] for row in selected}
    counts = {
        "generated_total": len(generated),
        "generated_unknown": sum(1 for r in generated if r.get("label") == "unknown"),
        "generated_known": sum(1 for r in generated if r.get("label") == "known"),
        "selected_confab": sum(1 for r in selected if r["role"] == "confab"),
        "selected_known_correct_answered": sum(
            1 for r in selected if r["role"] == "known_correct_answered"
        ),
        "public_generated_rows_included": True,
    }
    public = {
        "stage": "j_space_layer_contrast_replication_fresh_eval_pool",
        "model_name": MODEL_NAME,
        "substrate": "bf16",
        "predecessor_split_excluded": display_path(PREDECESSOR_SPLIT),
        "candidate_source": display_path(EXPANSION_CANDIDATES),
        "target_confab": args.target_confab,
        "target_known_correct": args.target_known_correct,
        "max_unknown_candidates": args.max_unknown_candidates,
        "max_known_candidates": args.max_known_candidates,
        "scan_all_candidates": args.scan_all_candidates,
        "public_manifest_policy": (
            "ID/provenance/role metadata only. Question text, aliases, and "
            "model generations remain private until per-source redistribution "
            "rights are audited."
        ),
        "counts": counts,
        "generated_rows": [
            public_generated_row(row, role_by_key) for row in generated
        ],
        "rows": [public_row(row) for row in selected],
        "runtime_sec": round(runtime, 1),
    }
    private = {
        **public,
        "private_generations_path": str(Path(args.generations_out).resolve()),
        "private_eval_rows_path": str(Path(args.rows_out).resolve()),
        "contains_question_text": True,
        "contains_aliases": True,
        "contains_generations": True,
    }
    Path(args.private_manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.private_manifest).write_text(json.dumps(private, indent=2), encoding="utf-8")
    Path(args.public_manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.public_manifest).write_text(json.dumps(public, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    excluded = predecessor_keys()
    source_order = [s.strip() for s in args.source_order.split(",") if s.strip()]
    unknown = candidate_rows("unknown", excluded, source_order)[: args.max_unknown_candidates]
    known = candidate_rows("known", excluded, source_order)[: args.max_known_candidates]
    print(
        f"[mine-fresh] candidates after predecessor exclusion: "
        f"unknown={len(unknown)} known={len(known)}",
        flush=True,
    )

    prior = read_existing_rows(Path(args.generations_out))
    if args.manifest_only:
        generated = list(prior.values())
        selected = select_eval_rows(generated)
        write_jsonl(Path(args.rows_out), selected)
        write_manifests(args, generated, selected, 0.0)
        print(
            f"[mine-fresh] manifest-only rebuild: generated={len(generated)} "
            f"selected={len(selected)}",
            flush=True,
        )
        return 0

    generated: list[dict] = []
    selected: list[dict] = []
    t0 = time.time()

    model, tokenizer = load_model()
    try:
        for label, rows, target_role, target_n in (
            ("unknown", unknown, "confab", args.target_confab),
            ("known", known, "known_correct_answered", args.target_known_correct),
        ):
            for idx, row in enumerate(rows, start=1):
                rec = prior.get(row["row_key"])
                if rec is None:
                    rec = generate_one(model, tokenizer, row, args.max_new_tokens)
                generated.append(rec)
                selected = select_eval_rows(generated)
                have = sum(1 for r in selected if r["role"] == target_role)
                if idx % args.flush_every == 0:
                    write_jsonl(Path(args.generations_out), generated)
                    write_jsonl(Path(args.rows_out), selected)
                target_met = have >= target_n
                if idx % 50 == 0 or (target_met and not args.scan_all_candidates):
                    print(
                        f"[mine-fresh] {label} scanned={idx}/{len(rows)} "
                        f"{target_role}={have}/{target_n}",
                        flush=True,
                    )
                if target_met and not args.scan_all_candidates:
                    break
    finally:
        del model
        torch.cuda.empty_cache()

    selected = select_eval_rows(generated)
    write_jsonl(Path(args.generations_out), generated)
    write_jsonl(Path(args.rows_out), selected)
    write_manifests(args, generated, selected, time.time() - t0)

    n_confab = sum(1 for r in selected if r["role"] == "confab")
    n_known = sum(1 for r in selected if r["role"] == "known_correct_answered")
    print(
        f"[mine-fresh] wrote selected rows: confab={n_confab} known={n_known} "
        f"-> {args.rows_out}",
        flush=True,
    )
    if n_confab < args.target_confab or n_known < args.target_known_correct:
        print("[mine-fresh] ERROR: target counts not met", file=sys.stderr)
        return 1
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-confab", type=int, default=200)
    parser.add_argument("--target-known-correct", type=int, default=300)
    parser.add_argument("--max-unknown-candidates", type=int, default=3496)
    parser.add_argument("--max-known-candidates", type=int, default=10000)
    parser.add_argument("--max-new-tokens", type=int, default=200)
    parser.add_argument("--source-order", default="kuq_ku_unknown_x,popqa,triviaqa")
    parser.add_argument(
        "--scan-all-candidates",
        action="store_true",
        help=(
            "Scan every configured unknown and known candidate instead of "
            "stopping at target counts. Resumable via --generations-out."
        ),
    )
    parser.add_argument("--flush-every", type=int, default=25)
    parser.add_argument("--generations-out", default=str(DEFAULT_GENERATIONS))
    parser.add_argument("--rows-out", default=str(DEFAULT_ROWS))
    parser.add_argument("--private-manifest", default=str(DEFAULT_PRIVATE_MANIFEST))
    parser.add_argument("--public-manifest", default=str(DEFAULT_PUBLIC_MANIFEST))
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help=(
            "Rebuild private/public manifests from --generations-out without "
            "loading the model or generating new rows."
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
