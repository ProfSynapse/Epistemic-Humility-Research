#!/usr/bin/env python3
"""Mine a private per-family eval pool for the cross-family J-space layer
contrast.

FALLBACK-ONLY (sign-time revision 2026-07-23): for the four reused families
this is SUPERSEDED by `materialize_reused_rows.py`, which consumes
`doubt-snap-cross-family-confirmatory`'s already-mined pool + FIT/HELD-OUT split
verbatim. Run this only if a family's Modal row text is gone AND the lead
authorizes a fresh mine (which is NOT the reused pool and loses reuse
provenance). See AMENDMENT.md "Consumed doubt-snap artifacts".

LEGACY DESIGN (only if used as fallback): for each family, generate
on that family's OWN raw-base checkpoint over the shared AH expansion
candidate pool (the question/alias text is family-agnostic; only the
GENERATION and the resulting role labels are family-specific), and select:

  - confab: gold-unanswerable candidate where this family's raw base
    answers rather than refuses.
  - known_correct_answered: gold-answerable candidate where this family's
    raw base answers and grades correct.
  - unknown_refused: gold-unanswerable candidate where this family's raw
    base refuses (not degenerate). Scaffold role only -- never itself
    gated/graded downstream, used solely as the doubt axis's "unknown" pole
    and the propensity/caution-direction fit population, matching
    `j-space-midband-write-sweep-qwen3-4b`'s own role set.

Unlike the same-model replication
(`j-space-layer-contrast-replication-qwen3-4b/mine_fresh_eval_pool.py`),
there is no predecessor split to exclude here: each family's pool is fresh
from scratch (the four families have never been evaluated by this project
before), so this script mines the full candidate universe up to per-family
targets rather than excluding a prior split.

Question text, aliases, and per-family baseline generations are written
ONLY under this experiment's gitignored `analysis/<family>/`. The committed
manifest under `analysis-committed/<family>/` carries row keys, roles, and
source/category metadata only -- no question text, no aliases, no
generations (same containment scheme as the replication and midband-write-
sweep predecessors).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import grader  # noqa: E402
import model_lib as ml  # noqa: E402
from family_config import FAMILY_SLUGS, load_family  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
# The phase1 tree was archived after this script was pinned; the corpus now
# lives under divergent-pool-own-readout's phase1-migrated mirror (same file:
# 13496 rows, sha256 2886a602..., its sidecar manifest still names the old
# path as canonical). Repointed via governed repin 2026-07-24.
EXPANSION_CANDIDATES = (
    CANONICAL
    / "experiments/divergent-pool-own-readout/analysis/phase1-migrated"
    / "probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)
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


def candidate_rows(label: str, source_order: list[str]) -> list[dict]:
    rows = []
    for row in load_jsonl(EXPANSION_CANDIDATES):
        if row.get("label") != label:
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


def generate_one(family: str, model, tokenizer, eos_ids: list[int], row: dict,
                  max_new_tokens: int) -> dict:
    device = next(model.parameters()).device
    prompt = ml.render(family, tokenizer, row)
    enc = tokenizer(prompt, return_tensors="pt").to(device)
    prompt_len = int(enc["input_ids"].shape[1])
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
        "family": family,
        "substrate": "bf16",
    }


def select_eval_rows(generated: list[dict]) -> list[dict]:
    selected = []
    for row in generated:
        if row["label"] == "unknown" and row.get("answered") is True:
            selected.append({
                "row_key": row["row_key"], "role": "confab",
                "question": row["question"], "aliases": [],
                "source": row.get("source"), "category_canon": row.get("category_canon"),
            })
        elif (
            row["label"] == "unknown"
            and row.get("refused") is True
            and row.get("degenerate") is False
        ):
            selected.append({
                "row_key": row["row_key"], "role": "unknown_refused",
                "question": row["question"], "aliases": [],
                "source": row.get("source"), "category_canon": row.get("category_canon"),
            })
        elif (
            row["label"] == "known"
            and row.get("answered") is True
            and row.get("correct") is True
        ):
            selected.append({
                "row_key": row["row_key"], "role": "known_correct_answered",
                "question": row["question"], "aliases": row.get("aliases", []),
                "source": row.get("source"), "category_canon": row.get("category_canon"),
            })
    return selected


def public_row(row: dict) -> dict:
    return {
        "row_key": row["row_key"], "role": row["role"],
        "source": row.get("source"), "category_canon": row.get("category_canon"),
    }


def display_path(path: Path) -> str:
    resolved = path.resolve()
    for root in (REPO_ROOT.resolve(), CANONICAL.resolve()):
        try:
            return str(resolved.relative_to(root))
        except ValueError:
            continue
    return str(path)


def paths_for(family: str, args: argparse.Namespace) -> dict[str, Path]:
    analysis = HERE / "analysis" / family
    committed = HERE / "analysis-committed" / family
    return {
        "generations": Path(args.generations_out or (analysis / "pool_generations.jsonl")),
        "rows": Path(args.rows_out or (analysis / "eval_rows.jsonl")),
        "private_manifest": Path(args.private_manifest or (analysis / "eval_pool_private_manifest.json")),
        "public_manifest": Path(args.public_manifest or (committed / "eval_pool_manifest.json")),
    }


def write_manifests(family: str, args: argparse.Namespace, paths: dict[str, Path],
                     generated: list[dict], selected: list[dict], runtime: float) -> None:
    role_by_key = {row["row_key"]: row["role"] for row in selected}
    counts = {
        "generated_total": len(generated),
        "generated_unknown": sum(1 for r in generated if r.get("label") == "unknown"),
        "generated_known": sum(1 for r in generated if r.get("label") == "known"),
        "selected_confab": sum(1 for r in selected if r["role"] == "confab"),
        "selected_unknown_refused": sum(1 for r in selected if r["role"] == "unknown_refused"),
        "selected_known_correct_answered": sum(
            1 for r in selected if r["role"] == "known_correct_answered"
        ),
    }
    public = {
        "stage": "j_space_cross_family_layer_contrast_eval_pool",
        "family": family,
        "checkpoint_repo": load_family(family)["checkpoint"]["repo"],
        "substrate": "bf16",
        "candidate_source": display_path(EXPANSION_CANDIDATES),
        "target_confab": args.target_confab,
        "target_known_correct": args.target_known_correct,
        "target_unknown_refused": args.target_unknown_refused,
        "public_manifest_policy": (
            "ID/provenance/role metadata only. Question text, aliases, and "
            "model generations remain private under analysis/."
        ),
        "counts": counts,
        "rows": [public_row(row) for row in selected],
        "runtime_sec": round(runtime, 1),
    }
    private = {
        **public,
        "private_generations_path": str(paths["generations"].resolve()),
        "private_eval_rows_path": str(paths["rows"].resolve()),
        "contains_question_text": True,
        "contains_aliases": True,
        "contains_generations": True,
    }
    paths["private_manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["private_manifest"].write_text(json.dumps(private, indent=2), encoding="utf-8")
    paths["public_manifest"].parent.mkdir(parents=True, exist_ok=True)
    paths["public_manifest"].write_text(json.dumps(public, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    family = args.family
    paths = paths_for(family, args)
    source_order = [s.strip() for s in args.source_order.split(",") if s.strip()]
    unknown = candidate_rows("unknown", source_order)[: args.max_unknown_candidates]
    known = candidate_rows("known", source_order)[: args.max_known_candidates]
    print(
        f"[mine-eval-pool:{family}] candidates: unknown={len(unknown)} known={len(known)}",
        flush=True,
    )

    prior = read_existing_rows(paths["generations"])
    generated: list[dict] = list(prior.values())
    selected: list[dict] = select_eval_rows(generated)
    t0 = time.time()

    model, tokenizer, hidden_size, n_layers = ml.load_model_and_tokenizer(family)
    eos_ids = ml.resolve_eos_ids(family, tokenizer)
    print(
        f"[mine-eval-pool:{family}] loaded checkpoint hidden_size={hidden_size} "
        f"n_hidden_layers={n_layers} eos_ids={eos_ids}",
        flush=True,
    )
    try:
        for label, rows, target_role, target_n in (
            ("unknown", unknown, "confab", args.target_confab),
            ("known", known, "known_correct_answered", args.target_known_correct),
        ):
            for idx, row in enumerate(rows, start=1):
                rec = prior.get(row["row_key"])
                if rec is None:
                    rec = generate_one(family, model, tokenizer, eos_ids, row, args.max_new_tokens)
                    generated.append(rec)
                selected = select_eval_rows(generated)
                have = sum(1 for r in selected if r["role"] == target_role)
                if idx % args.flush_every == 0:
                    write_jsonl(paths["generations"], generated)
                    write_jsonl(paths["rows"], selected)
                if idx % 50 == 0 or have >= target_n:
                    print(
                        f"[mine-eval-pool:{family}] {label} scanned={idx}/{len(rows)} "
                        f"{target_role}={have}/{target_n}",
                        flush=True,
                    )
                if have >= target_n and not args.scan_all_candidates:
                    break
    finally:
        del model
        torch.cuda.empty_cache()

    selected = select_eval_rows(generated)
    write_jsonl(paths["generations"], generated)
    write_jsonl(paths["rows"], selected)
    write_manifests(family, args, paths, generated, selected, time.time() - t0)

    n_confab = sum(1 for r in selected if r["role"] == "confab")
    n_known = sum(1 for r in selected if r["role"] == "known_correct_answered")
    n_unknown_refused = sum(1 for r in selected if r["role"] == "unknown_refused")
    print(
        f"[mine-eval-pool:{family}] selected: confab={n_confab} "
        f"known_correct_answered={n_known} unknown_refused={n_unknown_refused} "
        f"-> {paths['rows']}",
        flush=True,
    )
    if n_confab < args.target_confab or n_known < args.target_known_correct:
        print(f"[mine-eval-pool:{family}] ERROR: target counts not met", file=sys.stderr)
        return 1
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    parser.add_argument("--target-confab", type=int, default=200)
    parser.add_argument("--target-known-correct", type=int, default=300)
    parser.add_argument("--target-unknown-refused", type=int, default=200,
                        help="descriptive only; unknown_refused is a byproduct of the "
                             "unknown-candidate scan, not separately targeted")
    parser.add_argument("--max-unknown-candidates", type=int, default=3496)
    parser.add_argument("--max-known-candidates", type=int, default=10000)
    parser.add_argument("--max-new-tokens", type=int, default=200)
    parser.add_argument("--source-order", default="kuq_ku_unknown_x,popqa,triviaqa")
    parser.add_argument(
        "--scan-all-candidates", action="store_true",
        help="scan every configured candidate instead of stopping at target counts",
    )
    parser.add_argument("--flush-every", type=int, default=25)
    parser.add_argument("--generations-out", default=None)
    parser.add_argument("--rows-out", default=None)
    parser.add_argument("--private-manifest", default=None)
    parser.add_argument("--public-manifest", default=None)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
