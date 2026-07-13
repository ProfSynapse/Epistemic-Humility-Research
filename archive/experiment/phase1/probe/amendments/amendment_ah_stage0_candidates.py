#!/usr/bin/env python3
"""Amendment AH Stage-0 (script 1/4) — candidate-set assembly (CPU).

Pre-registered in
experiments/divergent-pool-own-readout/AMENDMENT.md (§4 step 1).

Builds the ~5,000-item candidate pool for the divergent-row mining pass:
  - SelfAware.json items NOT in the frozen AF 600 (join by normalized question).
  - KUQ top-up (knowns_unknowns.jsonl for gold-answerable knowns with a gold
    answer; unknowns_all.jsonl + KUQ unknowns for gold-unanswerable) so the
    final set has ~2,500 gold-unanswerable and ~2,000-2,500 gold-answerable.

Emits rows in the frozen af_base_pregen / ae_base_pool row schema so the
downstream extractor and probe scorer consume them unchanged:
  row_key, label ("known"|"unknown"), question, aliases (normalized), source.

Gold semantics (matches the probe recipe: label "known" == answerable == y=1):
  - gold-answerable  -> label "known"    (D-under candidate space)
  - gold-unanswerable-> label "unknown"  (D-over  candidate space)

Dedupe by normalized question text (scorers.norm_question). No GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
for p in (str(PROBE_DIR), str(EVAL_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scorers  # noqa: E402

# Canonical checkout holds datasets + AF surface + output artifacts.
CANONICAL = repo_root()
DATASETS = CANONICAL / "datasets"
AF_ROWS = CANONICAL / "experiment/phase1/probe/analysis/af_base_pregen/rows.jsonl"
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"

TARGET_UNANS = 2500
TARGET_ANS = 2500
SEED = 20260703


def norm_q(text: str) -> str:
    return scorers.norm_question(text)


def load_af600_questions() -> set[str]:
    seen = set()
    with AF_ROWS.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                seen.add(norm_q(json.loads(line)["question"]))
    return seen


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def load_selfaware(exclude: set[str]):
    """Yield (label, question, aliases_norm, source) for SelfAware minus AF600."""
    data = json.loads((DATASETS / "selfaware" / "SelfAware.json").read_text())
    items = data["example"]
    out = []
    for it in items:
        q = it["question"]
        nq = norm_q(q)
        if nq in exclude:
            continue
        answerable = bool(it.get("answerable"))
        if answerable:
            aliases = [scorers.normalize(str(a)) for a in _as_list(it.get("answer"))]
            aliases = [a for a in aliases if a]
            out.append(("known", q, aliases, "selfaware_answerable"))
        else:
            out.append(("unknown", q, [], "selfaware_unanswerable"))
    return out


def load_kuq_knowns(exclude: set[str]):
    """KUQ knowns_unknowns.jsonl -> gold-answerable knowns WITH a gold answer,
    and gold-unanswerable unknowns (no gold answer needed)."""
    knowns, unknowns = [], []
    with (DATASETS / "kuq" / "knowns_unknowns.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            q = r["question"]
            nq = norm_q(q)
            if nq in exclude:
                continue
            if r.get("unknown"):
                unknowns.append(("unknown", q, [], "kuq_ku_unknown"))
            else:
                aliases = [scorers.normalize(str(a)) for a in _as_list(r.get("answer"))]
                aliases = [a for a in aliases if a]
                # only usable as a D-under candidate if gradeable (has a gold alias)
                if aliases:
                    knowns.append(("known", q, aliases, "kuq_ku_known"))
    return knowns, unknowns


def load_kuq_unknowns_all(exclude: set[str]):
    out = []
    with (DATASETS / "kuq" / "unknowns_all.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            q = r.get("question")
            if not q:
                continue
            nq = norm_q(q)
            if nq in exclude:
                continue
            out.append(("unknown", q, [], "kuq_unknowns_all"))
    return out


def make_row_key(source: str, idx: int) -> str:
    return f"ah::{source}::{idx:06d}"


def run(args) -> int:
    import random
    rng = random.Random(SEED)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    af600 = load_af600_questions()
    print(f"[ah/cand] AF600 exclusion set: {len(af600)} normalized questions",
          flush=True)

    # Running dedupe set: AF600 first, then across all sources by normalized q.
    seen = set(af600)

    def dedupe(items):
        kept = []
        for label, q, aliases, source in items:
            nq = norm_q(q)
            if nq in seen:
                continue
            seen.add(nq)
            kept.append((label, q, aliases, source))
        return kept

    # SelfAware first (priority source; same distribution as AF/AG).
    sa = dedupe(load_selfaware(af600))
    sa_ans = [x for x in sa if x[0] == "known"]
    sa_unans = [x for x in sa if x[0] == "unknown"]
    print(f"[ah/cand] SelfAware (minus AF600, deduped): "
          f"answerable={len(sa_ans)} unanswerable={len(sa_unans)}", flush=True)

    # KUQ knowns_unknowns top-up.
    kuq_kn, kuq_ku_unk = load_kuq_knowns(seen)
    kuq_kn = dedupe(kuq_kn)
    kuq_ku_unk = dedupe(kuq_ku_unk)
    # KUQ unknowns_all top-up.
    kuq_ua = dedupe(load_kuq_unknowns_all(seen))
    print(f"[ah/cand] KUQ: knowns={len(kuq_kn)} ku_unknowns={len(kuq_ku_unk)} "
          f"unknowns_all={len(kuq_ua)}", flush=True)

    # Assemble to targets. SelfAware is prioritized; KUQ tops up.
    rng.shuffle(kuq_kn)
    rng.shuffle(kuq_ku_unk)
    rng.shuffle(kuq_ua)

    # Answerable: SelfAware answerable first, then KUQ knowns.
    answerable = list(sa_ans)
    need_ans = max(0, TARGET_ANS - len(answerable))
    answerable += kuq_kn[:need_ans]

    # Unanswerable: SelfAware unanswerable first, then KUQ ku_unknowns, then unknowns_all.
    unanswerable = list(sa_unans)
    need_unans = max(0, TARGET_UNANS - len(unanswerable))
    take_ku = kuq_ku_unk[:need_unans]
    unanswerable += take_ku
    need_unans2 = max(0, TARGET_UNANS - len(unanswerable))
    unanswerable += kuq_ua[:need_unans2]

    pool = answerable + unanswerable
    rng.shuffle(pool)

    # Compose per-source stats.
    comp = {}
    for label, q, aliases, source in pool:
        comp[source] = comp.get(source, 0) + 1

    rows_path = out_dir / "candidates.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for idx, (label, q, aliases, source) in enumerate(pool):
            fh.write(json.dumps({
                "row_key": make_row_key(source, idx),
                "label": label,
                "question": q,
                "aliases": aliases,
                "source": source,
            }, ensure_ascii=False) + "\n")

    n_known = sum(1 for x in pool if x[0] == "known")
    n_unknown = len(pool) - n_known
    manifest = {
        "amendment": "AH",
        "stage": "stage0_candidates",
        "seed": SEED,
        "af600_excluded": len(af600),
        "target_answerable": TARGET_ANS,
        "target_unanswerable": TARGET_UNANS,
        "n_total": len(pool),
        "n_known_answerable": n_known,
        "n_unknown_unanswerable": n_unknown,
        "composition_by_source": comp,
        "dedupe_key": "scorers.norm_question",
        "out": str(rows_path),
    }
    (out_dir / "candidates_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2), flush=True)
    print(f"[ah/cand] DONE -> {rows_path}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
