#!/usr/bin/env python3
"""Amendment AH Stage-0 EXPANSION (script 1/2) — candidate diversification (CPU).

Team-lead task 2026-07-03 (GPU-approved expansion pass). Extends the mined 5,000
with dataset diversification, so the divergent-pool identification is not
KUQ/SelfAware-bound:

  (a) NEW KUQ unknowns NOT in the mined 5,000 (dedupe by scorers.norm_question vs
      candidates.jsonl AND the AF-600). CARRY the `category` field per row.
  (b) ~10,000 answerable factoid items from:
        datasets/triviaqa-rc-nocontext/validation.jsonl  (answer.normalized_aliases)
        datasets/popqa/test.jsonl                        (possible_answers JSON list)
      carry gold aliases (normalized via scorers.normalize); dedupe as above;
      record per-source counts.

Also backfills `category` onto the ORIGINAL 1,768 mined kuq_ku_unknown rows by
normalized-question join -> a SIDECAR file (does NOT touch candidates.jsonl).

Emits rows in the frozen af_base_pregen row schema so the frozen extractor and
probe scorer consume them unchanged, plus a carried `category` (KUQ) field:
  row_key, label ("known"|"unknown"), question, aliases (normalized), source,
  category (KUQ unknowns only; "" otherwise).

Gold semantics (matches the probe recipe: label "known" == answerable == y=1):
  gold-answerable   -> label "known"    (muzzle-rescue / D-under candidate space)
  gold-unanswerable -> label "unknown"  (D-over candidate space)

No GPU. Outputs under analysis/ah_stage0/expansion/ (gitignored).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402

CANONICAL = repo_root()
DATASETS = CANONICAL / "datasets"
STAGE0 = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
AF_ROWS = CANONICAL / "experiment/phase1/probe/analysis/af_base_pregen/rows.jsonl"
MINED_CANDIDATES = STAGE0 / "candidates.jsonl"
DEFAULT_OUT = STAGE0 / "expansion"

TARGET_ANSWERABLE = 10000  # triviaqa + popqa combined
SEED = 20260703


def norm_q(text: str) -> str:
    return scorers.norm_question(text)


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def load_norm_questions(path: Path, key="question") -> set[str]:
    seen = set()
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                seen.add(norm_q(json.loads(line)[key]))
    return seen


def load_kuq_unknown_lookup() -> dict[str, str]:
    """norm_question -> category, over both KUQ unknown files (knowns_unknowns
    unknowns + unknowns_all). Used for backfill AND for the new-unknown source."""
    lut = {}
    with (DATASETS / "kuq" / "knowns_unknowns.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("unknown"):
                lut[norm_q(r["question"])] = r.get("category") or ""
    # unknowns_all fills any gaps (both files carry category)
    with (DATASETS / "kuq" / "unknowns_all.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            q = r.get("question")
            if q and norm_q(q) not in lut:
                lut[norm_q(q)] = r.get("category") or ""
    return lut


def iter_new_kuq_unknowns(exclude: set[str]):
    """Yield (question, category) for KUQ unknowns not in exclude, self-deduped.
    Preference: knowns_unknowns.jsonl first (the source the original mining used),
    then unknowns_all.jsonl for breadth."""
    seen = set(exclude)
    out = []
    for fname, qkey in (("knowns_unknowns.jsonl", "question"),
                        ("unknowns_all.jsonl", "question")):
        with (DATASETS / "kuq" / fname).open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                if fname == "knowns_unknowns.jsonl" and not r.get("unknown"):
                    continue
                q = r.get(qkey)
                if not q:
                    continue
                nq = norm_q(q)
                if nq in seen:
                    continue
                seen.add(nq)
                out.append((q, r.get("category") or ""))
    return out


def iter_triviaqa(exclude: set[str], limit: int):
    """Yield (question, aliases_norm) from triviaqa validation, deduped."""
    seen = set(exclude)
    out = []
    with (DATASETS / "triviaqa-rc-nocontext" / "validation.jsonl").open() as fh:
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
            ans = r.get("answer") or {}
            aliases = [scorers.normalize(str(a))
                       for a in _as_list(ans.get("normalized_aliases")
                                         or ans.get("aliases"))]
            aliases = [a for a in aliases if a]
            if not aliases:
                continue
            seen.add(nq)
            out.append((q, aliases))
            if limit and len(out) >= limit:
                break
    return out


def iter_popqa(exclude: set[str], limit: int):
    """Yield (question, aliases_norm) from popqa test, deduped.
    possible_answers is a JSON-encoded list string."""
    seen = set(exclude)
    out = []
    with (DATASETS / "popqa" / "test.jsonl").open() as fh:
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
            raw = r.get("possible_answers")
            try:
                cand = json.loads(raw) if isinstance(raw, str) else _as_list(raw)
            except (json.JSONDecodeError, TypeError):
                cand = []
            aliases = [scorers.normalize(str(a)) for a in cand]
            aliases = [a for a in aliases if a]
            if not aliases:
                continue
            seen.add(nq)
            out.append((q, aliases))
            if limit and len(out) >= limit:
                break
    return out


def make_row_key(source: str, idx: int) -> str:
    return f"ahx::{source}::{idx:06d}"


def run(args) -> int:
    import random
    rng = random.Random(SEED)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    af600 = load_norm_questions(AF_ROWS)
    mined = load_norm_questions(MINED_CANDIDATES)
    exclude = af600 | mined
    print(f"[ahx/cand] exclusion set: AF600={len(af600)} mined={len(mined)} "
          f"union={len(exclude)}", flush=True)

    # ---- (a) new KUQ unknowns w/ category ----
    new_ku = iter_new_kuq_unknowns(exclude)
    ku_cat = Counter(c or "(none)" for _, c in new_ku)
    print(f"[ahx/cand] NEW kuq unknowns: {len(new_ku)}  "
          f"categories={dict(ku_cat)}", flush=True)

    # ---- (b) answerable factoids: triviaqa + popqa ----
    # Build a growing exclude across both answerable sources too.
    excl_ans = set(exclude)
    tqa = iter_triviaqa(excl_ans, args.trivia_limit)
    for q, _ in tqa:
        excl_ans.add(norm_q(q))
    # remaining budget goes to popqa
    remaining = max(0, TARGET_ANSWERABLE - len(tqa)) if args.balance else args.popqa_limit
    pqa = iter_popqa(excl_ans, remaining)
    print(f"[ahx/cand] answerable: triviaqa={len(tqa)} popqa={len(pqa)} "
          f"total={len(tqa)+len(pqa)} (target ~{TARGET_ANSWERABLE})", flush=True)

    # ---- assemble expansion pool ----
    pool = []
    idx = 0
    for q, cat in new_ku:
        pool.append({"row_key": make_row_key("kuq_ku_unknown_x", idx),
                     "label": "unknown", "question": q, "aliases": [],
                     "source": "kuq_ku_unknown_x", "category": cat})
        idx += 1
    for q, aliases in tqa:
        pool.append({"row_key": make_row_key("triviaqa", idx),
                     "label": "known", "question": q, "aliases": aliases,
                     "source": "triviaqa", "category": ""})
        idx += 1
    for q, aliases in pqa:
        pool.append({"row_key": make_row_key("popqa", idx),
                     "label": "known", "question": q, "aliases": aliases,
                     "source": "popqa", "category": ""})
        idx += 1
    rng.shuffle(pool)

    rows_path = out_dir / "expansion_candidates.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for r in pool:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- category backfill sidecar for the ORIGINAL 1,768 mined kuq rows ----
    ku_lut = load_kuq_unknown_lookup()
    backfill = []
    bf_hit = bf_miss = 0
    with MINED_CANDIDATES.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r["source"] != "kuq_ku_unknown":
                continue
            cat = ku_lut.get(norm_q(r["question"]), "")
            if cat:
                bf_hit += 1
            else:
                bf_miss += 1
            backfill.append({"row_key": r["row_key"], "question": r["question"],
                             "category": cat})
    sidecar_path = out_dir / "mined_kuq_category_backfill.jsonl"
    with sidecar_path.open("w", encoding="utf-8") as fh:
        for r in backfill:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"[ahx/cand] category backfill sidecar: {len(backfill)} rows "
          f"(hit={bf_hit} miss={bf_miss})", flush=True)

    comp = Counter(r["source"] for r in pool)
    manifest = {
        "amendment": "AH", "stage": "stage0_expansion_candidates", "seed": SEED,
        "exclude_af600": len(af600), "exclude_mined": len(mined),
        "n_total_expansion": len(pool),
        "n_new_kuq_unknown": len(new_ku),
        "n_triviaqa": len(tqa), "n_popqa": len(pqa),
        "composition_by_source": dict(comp),
        "new_kuq_category_split": dict(ku_cat),
        "backfill_rows": len(backfill), "backfill_hit": bf_hit,
        "backfill_miss": bf_miss,
        "dedupe_key": "scorers.norm_question",
        "expansion_candidates": str(rows_path),
        "category_backfill_sidecar": str(sidecar_path),
        "target_answerable": TARGET_ANSWERABLE,
        "note": ("kuq_ku_unknown_x source carries category; triviaqa/popqa carry "
                 "normalized gold aliases. Original candidates.jsonl untouched; "
                 "category backfilled via sidecar (norm-question join)."),
    }
    (out_dir / "expansion_candidates_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[ahx/cand] DONE -> {rows_path}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--trivia-limit", type=int, default=6000,
                    help="max triviaqa answerable items")
    ap.add_argument("--popqa-limit", type=int, default=4000,
                    help="max popqa items (used only when --balance is off)")
    ap.add_argument("--balance", action="store_true", default=True,
                    help="fill popqa up to TARGET_ANSWERABLE - n_triviaqa")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
