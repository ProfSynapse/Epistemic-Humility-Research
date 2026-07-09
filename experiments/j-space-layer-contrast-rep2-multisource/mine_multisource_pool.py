#!/usr/bin/env python3
"""Mine a fresh MULTI-SOURCE confab pool for the J-space layer-contrast rep2.

`j-space-layer-contrast-replication-qwen3-4b` (rep1) registered a G1 fail on
a ceiling-saturated fresh pool whose 306 confabs came entirely from one
source (`kuq_ku_unknown_x`), because its candidate universe -- the AH
stage-0 EXPANSION file `ah_stage0/expansion/expansion_candidates.jsonl` --
structurally contains only that one unknown source (see rep1's Outcome,
"Consequences carried forward" (b)). This script does not read that
expansion file. It reads the three predecessor confab sources' ORIGINAL
dataset loaders directly:

  - kuq_ku_unknown:   datasets/kuq/knowns_unknowns.jsonl, rows with
                      `unknown: true` (same filter as
                      `amendment_ah_stage0_candidates.py:load_kuq_knowns`'s
                      unknown branch).
  - kuq_ku_unknown_x: datasets/kuq/unknowns_all.jsonl, all rows, deduped
                      against kuq_ku_unknown by normalized question (same
                      priority as
                      `amendment_ah_stage0_expand_candidates.py:iter_new_kuq_unknowns`:
                      knowns_unknowns.jsonl first, unknowns_all.jsonl fills
                      gaps).
  - selfaware_unanswerable: datasets/selfaware/SelfAware.json, rows with
                      `answerable: false` (same filter as
                      `amendment_ah_stage0_candidates.py:load_selfaware`'s
                      unanswerable branch).

Dual exclusion: a candidate is dropped if its NORMALIZED question text
matches any row already used by (a) the predecessor fit/held-out split
(`experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`)
or (b) rep1's own fresh pool
(`experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json`).
Both manifests are ID-only (row_key, role, source -- no question text), so
exclusion is resolved by looking each excluded row_key up in the private,
gitignored candidate file its `ah::`/`ahx::` prefix names
(`ah_stage0/candidates.jsonl` for `ah::`, `ah_stage0/expansion/expansion_candidates.jsonl`
for `ahx::`) to recover its question text, then normalizing. This is a
stronger disjointness guarantee than literal row_key matching would be here,
since this script's own row_keys use a new `msrc::` scheme that would never
collide with `ah::`/`ahx::` keys regardless of content overlap.

The KNOWN-CORRECT side is not mined here at all: the design reuses rep1's
1,957 `known_correct_answered` rows and their anchors verbatim (see
`materialize_known_side_reuse.py`).

Question text, aliases, and generations are written only under this
experiment's gitignored `analysis/` directory. The committed manifest is
ID/source/role metadata only.
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
REPO_ROOT = HERE.parents[1]
EVAL_DIR = Path("/home/profsynapse/code/Epistemic-Humility-Research/experiment/phase1/eval")

for p in (str(SOURCE), str(RENDER_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import grader  # noqa: E402
import scorers  # noqa: E402
from ah_a0_raw_base_render import render  # noqa: E402

MODEL_NAME = "unsloth/Qwen3-4B"
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")

# Raw dataset files (git-tracked; present in every worktree).
DATASETS = REPO_ROOT / "datasets"
KUQ_KNOWNS_UNKNOWNS = DATASETS / "kuq" / "knowns_unknowns.jsonl"
KUQ_UNKNOWNS_ALL = DATASETS / "kuq" / "unknowns_all.jsonl"
SELFAWARE_JSON = DATASETS / "selfaware" / "SelfAware.json"

# Private, gitignored candidate caches used ONLY to resolve prior row_keys
# back to question text for exclusion. Not read for candidate generation.
AH_CANDIDATES = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0/candidates.jsonl"
AHX_CANDIDATES = (
    CANONICAL / "experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)

PREDECESSOR_SPLIT = (
    HERE.parent / "common/doubt-gated-caution-tighten-heldout-split/split_manifest.json"
)
REP1_POOL_MANIFEST = (
    HERE.parent
    / "j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json"
)

DEFAULT_GENERATIONS = ANALYSIS / "multisource_pool_generations.jsonl"
DEFAULT_ROWS = ANALYSIS / "multisource_confab_rows.jsonl"
DEFAULT_PRIVATE_MANIFEST = ANALYSIS / "multisource_pool_private_manifest.json"
DEFAULT_PUBLIC_MANIFEST = COMMITTED / "multisource_pool_manifest.json"

SOURCES = ("kuq_ku_unknown", "kuq_ku_unknown_x", "selfaware_unanswerable")
HARDER_SOURCES = ("kuq_ku_unknown", "selfaware_unanswerable")


def norm_q(text: str) -> str:
    return scorers.norm_question(text)


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


# ---------------------------------------------------------------------------
# Dual-exclusion resolution: prior row_key -> normalized question text.
# ---------------------------------------------------------------------------

def _row_key_lookup(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for row in load_jsonl(path):
        rk = row.get("row_key")
        q = row.get("question")
        if rk and q:
            out[rk] = q
    return out


def resolve_excluded_questions() -> tuple[set[str], dict[str, int]]:
    """Return (excluded normalized-question set, per-manifest resolved counts)."""
    predecessor_keys: set[str] = set()
    if PREDECESSOR_SPLIT.exists():
        data = json.loads(PREDECESSOR_SPLIT.read_text(encoding="utf-8"))
        predecessor_keys = {row["row_key"] for row in data["rows"]}

    rep1_keys: set[str] = set()
    if REP1_POOL_MANIFEST.exists():
        data = json.loads(REP1_POOL_MANIFEST.read_text(encoding="utf-8"))
        rep1_keys = {row["row_key"] for row in data["rows"]}

    all_keys = predecessor_keys | rep1_keys
    ah_keys = {k for k in all_keys if k.startswith("ah::")}
    ahx_keys = {k for k in all_keys if k.startswith("ahx::")}
    other_keys = all_keys - ah_keys - ahx_keys

    ah_lut = _row_key_lookup(AH_CANDIDATES) if ah_keys else {}
    ahx_lut = _row_key_lookup(AHX_CANDIDATES) if ahx_keys else {}

    excluded_q: set[str] = set()
    unresolved = 0
    for k in ah_keys:
        q = ah_lut.get(k)
        if q:
            excluded_q.add(norm_q(q))
        else:
            unresolved += 1
    for k in ahx_keys:
        q = ahx_lut.get(k)
        if q:
            excluded_q.add(norm_q(q))
        else:
            unresolved += 1
    unresolved += len(other_keys)  # unknown prefix; cannot resolve, counted only

    counts = {
        "predecessor_split_keys": len(predecessor_keys),
        "rep1_pool_keys": len(rep1_keys),
        "union_keys": len(all_keys),
        "resolved_to_question": len(excluded_q),
        "unresolved_keys": unresolved,
    }
    return excluded_q, counts


# ---------------------------------------------------------------------------
# Original-loader candidate readers.
# ---------------------------------------------------------------------------

def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def load_kuq_ku_unknown(excluded_q: set[str]) -> list[dict]:
    """`datasets/kuq/knowns_unknowns.jsonl`, `unknown: true` rows. Matches
    `amendment_ah_stage0_candidates.py:load_kuq_knowns`'s unknown branch."""
    out = []
    idx = 0
    with KUQ_KNOWNS_UNKNOWNS.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if not r.get("unknown"):
                continue
            q = r.get("question")
            if not q:
                continue
            nq = norm_q(q)
            if nq in excluded_q:
                continue
            out.append({
                "row_key": f"msrc::kuq_ku_unknown::{idx:06d}",
                "label": "unknown",
                "question": q,
                "aliases": [],
                "source": "kuq_ku_unknown",
                "category_canon": r.get("category") or "kuq_ku_unknown",
                "_nq": nq,
            })
            idx += 1
    return out


def load_kuq_ku_unknown_x(excluded_q: set[str], dedupe_against: set[str]) -> list[dict]:
    """`datasets/kuq/unknowns_all.jsonl`, all rows, deduped against the
    kuq_ku_unknown normalized-question set. Matches
    `amendment_ah_stage0_expand_candidates.py:iter_new_kuq_unknowns`'s
    unknowns_all.jsonl gap-fill priority (knowns_unknowns.jsonl first)."""
    out = []
    idx = 0
    seen = set(dedupe_against)
    with KUQ_UNKNOWNS_ALL.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            q = r.get("question")
            if not q:
                continue
            nq = norm_q(q)
            if nq in seen:
                continue
            seen.add(nq)
            if nq in excluded_q:
                continue
            out.append({
                "row_key": f"msrc::kuq_ku_unknown_x::{idx:06d}",
                "label": "unknown",
                "question": q,
                "aliases": [],
                "source": "kuq_ku_unknown_x",
                "category_canon": r.get("category") or "kuq_ku_unknown_x",
                "_nq": nq,
            })
            idx += 1
    return out


def load_selfaware_unanswerable(excluded_q: set[str]) -> list[dict]:
    """`datasets/selfaware/SelfAware.json`, `answerable: false` rows. Matches
    `amendment_ah_stage0_candidates.py:load_selfaware`'s unanswerable
    branch."""
    data = json.loads(SELFAWARE_JSON.read_text(encoding="utf-8"))
    out = []
    idx = 0
    for it in data["example"]:
        if it.get("answerable"):
            continue
        q = it.get("question")
        if not q:
            continue
        nq = norm_q(q)
        if nq in excluded_q:
            continue
        out.append({
            "row_key": f"msrc::selfaware_unanswerable::{idx:06d}",
            "label": "unknown",
            "question": q,
            "aliases": [],
            "source": "selfaware_unanswerable",
            "category_canon": "selfaware_unanswerable",
            "_nq": nq,
        })
        idx += 1
    return out


def build_candidate_pool(excluded_q: set[str]) -> dict[str, list[dict]]:
    ku = load_kuq_ku_unknown(excluded_q)
    ku_nq = {r["_nq"] for r in ku}
    kux = load_kuq_ku_unknown_x(excluded_q, ku_nq)
    sa = load_selfaware_unanswerable(excluded_q)
    for r in ku + kux + sa:
        r.pop("_nq", None)
    return {"kuq_ku_unknown": ku, "kuq_ku_unknown_x": kux, "selfaware_unanswerable": sa}


# ---------------------------------------------------------------------------
# Generation (raw-base Qwen3-4B bf16, AH-A0 render, greedy, same contract as
# rep1's mine_fresh_eval_pool.py generate_one).
# ---------------------------------------------------------------------------

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
        **{k: v for k, v in row.items() if k != "_nq"},
        "answer_text": answer_text,
        "answered": grade["answered"],
        "refused": grade["refused"],
        "degenerate": grade["degenerate"],
        "prompt_len": prompt_len,
        "n_new_tokens": int(new_tokens.shape[0]),
        "terminated_naturally": int(new_tokens.shape[0]) < max_new_tokens,
        "model_name": MODEL_NAME,
        "substrate": "bf16",
    }


def select_confab_rows(generated: list[dict]) -> list[dict]:
    """confab: gold-unanswerable row where raw-base bf16 answers (does not
    refuse) -- same rule as rep1 (and the pre-rep1 predecessor)."""
    return [
        {
            "row_key": row["row_key"],
            "role": "confab",
            "question": row["question"],
            "aliases": [],
            "source": row.get("source"),
            "category_canon": row.get("category_canon"),
        }
        for row in generated
        if row.get("answered") is True
    ]


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
        "prompt_len": row.get("prompt_len"),
        "n_new_tokens": row.get("n_new_tokens"),
        "terminated_naturally": row.get("terminated_naturally"),
    }


def per_source_counts(selected: list[dict]) -> dict[str, int]:
    counts = {s: 0 for s in SOURCES}
    for r in selected:
        counts[r["source"]] = counts.get(r["source"], 0) + 1
    return counts


def write_manifests(
    args: argparse.Namespace,
    generated: list[dict],
    selected: list[dict],
    exclusion_counts: dict,
    runtime: float,
) -> None:
    role_by_key = {row["row_key"]: row["role"] for row in selected}
    src_counts = per_source_counts(selected)
    counts = {
        "generated_total": len(generated),
        "selected_confab_total": len(selected),
        "selected_confab_by_source": src_counts,
        "g0_total_floor": 200,
        "g0_total_met": len(selected) >= 200,
        "g0_harder_source_floor": 40,
        "g0_harder_sources_met": {
            s: src_counts.get(s, 0) >= 40 for s in HARDER_SOURCES
        },
    }
    public = {
        "stage": "j_space_layer_contrast_rep2_multisource_confab_pool",
        "model_name": MODEL_NAME,
        "substrate": "bf16",
        "predecessor_split_excluded": str(PREDECESSOR_SPLIT),
        "rep1_pool_excluded": str(REP1_POOL_MANIFEST),
        "exclusion_resolution_counts": exclusion_counts,
        "candidate_loaders": {
            "kuq_ku_unknown": "datasets/kuq/knowns_unknowns.jsonl (unknown=true)",
            "kuq_ku_unknown_x": "datasets/kuq/unknowns_all.jsonl (deduped vs kuq_ku_unknown)",
            "selfaware_unanswerable": "datasets/selfaware/SelfAware.json (answerable=false)",
        },
        "target_confab_by_source": {
            "kuq_ku_unknown": args.target_kuq_ku_unknown,
            "kuq_ku_unknown_x": args.target_kuq_ku_unknown_x,
            "selfaware_unanswerable": args.target_selfaware_unanswerable,
        },
        "public_manifest_policy": (
            "ID/provenance/role metadata only. Question text, aliases, and "
            "model generations remain private under analysis/."
        ),
        "counts": counts,
        "generated_rows": [public_generated_row(row, role_by_key) for row in generated],
        "rows": [public_row(row) for row in selected],
        "runtime_sec": round(runtime, 1),
    }
    private = {
        **public,
        "private_generations_path": str(Path(args.generations_out).resolve()),
        "private_rows_path": str(Path(args.rows_out).resolve()),
        "contains_question_text": True,
        "contains_generations": True,
    }
    Path(args.private_manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.private_manifest).write_text(json.dumps(private, indent=2), encoding="utf-8")
    Path(args.public_manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.public_manifest).write_text(json.dumps(public, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    excluded_q, exclusion_counts = resolve_excluded_questions()
    print(f"[mine-multisource] exclusion resolution: {exclusion_counts}", flush=True)

    pools = build_candidate_pool(excluded_q)
    for src, rows in pools.items():
        print(f"[mine-multisource] candidates after dual exclusion: {src}={len(rows)}", flush=True)

    targets = {
        "kuq_ku_unknown": args.target_kuq_ku_unknown,
        "kuq_ku_unknown_x": args.target_kuq_ku_unknown_x,
        "selfaware_unanswerable": args.target_selfaware_unanswerable,
    }
    max_scan = {
        "kuq_ku_unknown": args.max_kuq_ku_unknown_candidates,
        "kuq_ku_unknown_x": args.max_kuq_ku_unknown_x_candidates,
        "selfaware_unanswerable": args.max_selfaware_candidates,
    }

    prior = read_existing_rows(Path(args.generations_out))
    if args.manifest_only:
        generated = list(prior.values())
        selected = select_confab_rows(generated)
        write_jsonl(Path(args.rows_out), selected)
        write_manifests(args, generated, selected, exclusion_counts, 0.0)
        print(
            f"[mine-multisource] manifest-only rebuild: generated={len(generated)} "
            f"selected={len(selected)} by_source={per_source_counts(selected)}",
            flush=True,
        )
        return 0

    generated: list[dict] = list(prior.values())
    t0 = time.time()

    model, tokenizer = load_model()
    try:
        for src in SOURCES:
            rows = pools[src][: max_scan[src]]
            target_n = targets[src]
            have = sum(
                1 for r in generated if r.get("source") == src and r.get("answered") is True
            )
            for idx, row in enumerate(rows, start=1):
                if have >= target_n and not args.scan_all_candidates:
                    break
                rec = prior.get(row["row_key"])
                if rec is None:
                    rec = generate_one(model, tokenizer, row, args.max_new_tokens)
                    generated.append(rec)
                    if rec.get("answered") is True:
                        have += 1
                if idx % args.flush_every == 0:
                    write_jsonl(Path(args.generations_out), generated)
                    write_jsonl(Path(args.rows_out), select_confab_rows(generated))
                if idx % 50 == 0 or have >= target_n:
                    print(
                        f"[mine-multisource] {src} scanned={idx}/{len(rows)} "
                        f"confab={have}/{target_n}",
                        flush=True,
                    )
    finally:
        del model
        torch.cuda.empty_cache()

    selected = select_confab_rows(generated)
    write_jsonl(Path(args.generations_out), generated)
    write_jsonl(Path(args.rows_out), selected)
    write_manifests(args, generated, selected, exclusion_counts, time.time() - t0)

    by_source = per_source_counts(selected)
    print(
        f"[mine-multisource] wrote selected confabs: total={len(selected)} "
        f"by_source={by_source} -> {args.rows_out}",
        flush=True,
    )
    ok_total = len(selected) >= 200
    ok_harder = all(by_source.get(s, 0) >= 40 for s in HARDER_SOURCES)
    if not (ok_total and ok_harder):
        print(
            "[mine-multisource] ERROR: G0 floors not met "
            f"(total>=200: {ok_total}, harder-source>=40 each: {ok_harder})",
            file=sys.stderr,
        )
        return 1
    return 0


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-kuq-ku-unknown", type=int, default=70)
    parser.add_argument("--target-kuq-ku-unknown-x", type=int, default=80)
    parser.add_argument("--target-selfaware-unanswerable", type=int, default=70)
    parser.add_argument("--max-kuq-ku-unknown-candidates", type=int, default=3437)
    parser.add_argument("--max-kuq-ku-unknown-x-candidates", type=int, default=6363)
    parser.add_argument("--max-selfaware-candidates", type=int, default=1032)
    parser.add_argument("--max-new-tokens", type=int, default=200)
    parser.add_argument(
        "--scan-all-candidates",
        action="store_true",
        help="Scan every configured candidate per source instead of stopping at target.",
    )
    parser.add_argument("--flush-every", type=int, default=25)
    parser.add_argument("--generations-out", default=str(DEFAULT_GENERATIONS))
    parser.add_argument("--rows-out", default=str(DEFAULT_ROWS))
    parser.add_argument("--private-manifest", default=str(DEFAULT_PRIVATE_MANIFEST))
    parser.add_argument("--public-manifest", default=str(DEFAULT_PUBLIC_MANIFEST))
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Rebuild manifests from --generations-out without loading the model.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
