#!/usr/bin/env python3
"""Launch-prep materialization (item 27, PR #430 launch prep item 2).

Reconstructs `analysis/rows_with_text_raw_base.jsonl`: question text for the
221 row_keys named in rep2's committed, ID/role-only raw_base anchor pool
(`experiments/j-space-layer-contrast-rep2-multisource/analysis-committed/
multisource_pool_manifest.json`, cited by AMENDMENT.md's G4 block for the
hs23/hs29 reference rates 194/221, 205/221).

rep2's own containment policy keeps question text out of that committed
manifest ("ID/provenance/role metadata only ... Question text ... remain
private under analysis/"), and rep2's private analysis/ does not exist in
this worktree. This script does NOT read rep2's private files (there are
none to read); it deterministically REPRODUCES rep2's own row_key -> question
derivation, verbatim-ported from
`experiments/j-space-layer-contrast-rep2-multisource/mine_multisource_pool.py`
(`resolve_excluded_questions`, `load_kuq_ku_unknown`,
`load_kuq_ku_unknown_x`, `load_selfaware_unanswerable`), reading the same
git-tracked raw dataset files under `datasets/` that script reads, plus the
same two private candidate caches it uses ONLY to resolve prior row_keys
back to question text for exclusion (their migrated locations in this
checkout, verified present and gitignored):

  - AH_CANDIDATES  -> experiments/divergent-pool-own-readout/analysis/
                      phase1-migrated/probe/analysis/ah_stage0/candidates.jsonl
  - AHX_CANDIDATES -> experiments/divergent-pool-own-readout/analysis/
                      phase1-migrated/probe/analysis/ah_stage0/expansion/
                      expansion_candidates.jsonl (== item 1's F16 expansion
                      corpus, mine_pool.EXPANSION_CANDIDATES)

Because idx assignment in the source loaders only increments for candidates
that SURVIVE the dual-exclusion filter, getting that exclusion set exactly
right decides correctness outright: a wrong exclusion set
would silently shift every downstream row_key's index. This script
cross-checks its own exclusion resolution against the exact counts rep2's
manifest recorded at mining time (`exclusion_resolution_counts`:
predecessor_split_keys=739, rep1_pool_keys=2263, union_keys=3002,
resolved_to_question=3002, unresolved_keys=0) and hard-fails on any
mismatch, rather than silently producing a plausible-looking but misaligned
join.

Output: `analysis/rows_with_text_raw_base.jsonl`, one row per rep2 row_key:
{row_key, role: "confab", question, aliases, source, category}, matching the
schema `mine_pool.py` writes for the trained substrate's
`rows_with_text.jsonl` (row_key/role/question/aliases/source/category) so
every downstream consumer (`extract_anchor.py`, `dose_calibrate.py`) reads
one shape regardless of substrate. No sampling: all 221 registered row_keys
are included, deterministically, every run.

CPU only. Reads only git-tracked / already-staged gitignored inputs; writes
only under this experiment's own gitignored analysis/.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ANALYSIS = HERE / "analysis"

REP2_DIR = REPO_ROOT / "experiments" / "j-space-layer-contrast-rep2-multisource"
REP2_MANIFEST_PATH = REP2_DIR / "analysis-committed" / "multisource_pool_manifest.json"

DATASETS = REPO_ROOT / "datasets"
KUQ_KNOWNS_UNKNOWNS = DATASETS / "kuq" / "knowns_unknowns.jsonl"
KUQ_UNKNOWNS_ALL = DATASETS / "kuq" / "unknowns_all.jsonl"
SELFAWARE_JSON = DATASETS / "selfaware" / "SelfAware.json"

PREDECESSOR_SPLIT = (
    REPO_ROOT
    / "experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json"
)
REP1_POOL_MANIFEST = (
    REPO_ROOT
    / "experiments/j-space-layer-contrast-replication-qwen3-4b/analysis-committed/fresh_eval_pool_manifest.json"
)

# Migrated locations of rep2's two private exclusion-resolution caches
# (verified present + gitignored in this checkout; see docstring).
AH_CANDIDATES = (
    REPO_ROOT
    / "experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_stage0/candidates.jsonl"
)
AHX_CANDIDATES = (
    REPO_ROOT
    / "experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl"
)

OUT_PATH = ANALYSIS / "rows_with_text_raw_base.jsonl"

# Verbatim from experiments/j-space-cross-family-layer-contrast/scorers.py
# norm_question (item-27's own probe_common.py carries the same verbatim
# port; reused here without importing across experiment boundaries).
_HIR_PREFIX = re.compile(
    r"^your current knowledge expression confidence level is [0-9.]+,\s*"
    r"please answer the user's question:\s*"
)


def norm_q(text: str) -> str:
    q = re.sub(r"\s+", " ", text.strip().lower())
    return _HIR_PREFIX.sub("", q)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


# ---------------------------------------------------------------------------
# Verbatim port of mine_multisource_pool.py's dual-exclusion resolution.
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
    unresolved += len(other_keys)

    counts = {
        "predecessor_split_keys": len(predecessor_keys),
        "rep1_pool_keys": len(rep1_keys),
        "union_keys": len(all_keys),
        "resolved_to_question": len(excluded_q),
        "unresolved_keys": unresolved,
    }
    return excluded_q, counts


# Expected counts, read from rep2's OWN committed manifest
# (exclusion_resolution_counts), cross-checked below rather than trusted.
EXPECTED_EXCLUSION_COUNTS = {
    "predecessor_split_keys": 739,
    "rep1_pool_keys": 2263,
    "union_keys": 3002,
    "resolved_to_question": 3002,
    "unresolved_keys": 0,
}


# ---------------------------------------------------------------------------
# Verbatim port of mine_multisource_pool.py's per-source candidate loaders.
# ---------------------------------------------------------------------------


def load_kuq_ku_unknown(excluded_q: set[str]) -> list[dict]:
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
                "question": q,
                "aliases": [],
                "source": "kuq_ku_unknown",
                "category_canon": r.get("category") or "kuq_ku_unknown",
            })
            idx += 1
    return out


def load_kuq_ku_unknown_x(excluded_q: set[str], dedupe_against: set[str]) -> list[dict]:
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
                "question": q,
                "aliases": [],
                "source": "kuq_ku_unknown_x",
                "category_canon": r.get("category") or "kuq_ku_unknown_x",
            })
            idx += 1
    return out


def load_selfaware_unanswerable(excluded_q: set[str]) -> list[dict]:
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
            "question": q,
            "aliases": [],
            "source": "selfaware_unanswerable",
            "category_canon": "selfaware_unanswerable",
        })
        idx += 1
    return out


def build_row_key_index(excluded_q: set[str]) -> dict[str, dict]:
    ku = load_kuq_ku_unknown(excluded_q)
    ku_nq = {norm_q(r["question"]) for r in ku}
    kux = load_kuq_ku_unknown_x(excluded_q, ku_nq)
    sa = load_selfaware_unanswerable(excluded_q)
    index: dict[str, dict] = {}
    for r in ku + kux + sa:
        index[r["row_key"]] = r
    return index


def main() -> int:
    for p in (
        REP2_MANIFEST_PATH, KUQ_KNOWNS_UNKNOWNS, KUQ_UNKNOWNS_ALL, SELFAWARE_JSON,
        PREDECESSOR_SPLIT, REP1_POOL_MANIFEST, AH_CANDIDATES, AHX_CANDIDATES,
    ):
        if not p.exists():
            print(f"FATAL: required input missing: {p}", file=sys.stderr)
            return 1

    manifest = json.loads(REP2_MANIFEST_PATH.read_text(encoding="utf-8"))
    target_rows = manifest["rows"]
    if len(target_rows) != 221:
        print(f"FATAL: rep2 manifest carries {len(target_rows)} rows, expected 221", file=sys.stderr)
        return 1

    excluded_q, exclusion_counts = resolve_excluded_questions()
    if exclusion_counts != EXPECTED_EXCLUSION_COUNTS:
        print(
            "FATAL: exclusion-resolution counts do not match rep2's own "
            f"recorded exclusion_resolution_counts.\n  computed: {exclusion_counts}\n"
            f"  expected: {EXPECTED_EXCLUSION_COUNTS}\n"
            "This means the reconstructed exclusion set differs from the one "
            "rep2's own mining run used, which would silently misalign the "
            "row_key -> question join. Not writing output.",
            file=sys.stderr,
        )
        return 1

    row_key_index = build_row_key_index(excluded_q)

    out_rows = []
    missing_keys = []
    source_counts: dict[str, int] = {}
    category_mismatches = []
    for target in target_rows:
        rk = target["row_key"]
        rec = row_key_index.get(rk)
        if rec is None:
            missing_keys.append(rk)
            continue
        if rec["source"] != target["source"]:
            print(f"FATAL: source mismatch for {rk}: reconstructed={rec['source']!r} manifest={target['source']!r}", file=sys.stderr)
            return 1
        if rec["category_canon"] != target["category_canon"]:
            category_mismatches.append(rk)
        out_rows.append({
            "row_key": rk,
            "role": "confab",
            "question": rec["question"],
            "aliases": rec["aliases"],
            "source": target["source"],
            "category": target["category_canon"],
        })
        source_counts[target["source"]] = source_counts.get(target["source"], 0) + 1

    if missing_keys:
        print(
            f"FATAL: {len(missing_keys)}/221 of rep2's registered row_keys "
            f"could not be resolved to question text (first 5: {missing_keys[:5]}). "
            "Not writing output.",
            file=sys.stderr,
        )
        return 1

    if category_mismatches:
        print(
            f"FATAL: {len(category_mismatches)} row(s) resolved to a "
            f"different category_canon than rep2's manifest records (first 5: "
            f"{category_mismatches[:5]}). This indicates the row_key -> "
            "candidate mapping is not exactly reproducing rep2's own mining "
            "run. Not writing output.",
            file=sys.stderr,
        )
        return 1

    expected_by_source = manifest["counts"]["selected_confab_by_source"]
    if source_counts != expected_by_source:
        print(
            f"FATAL: per-source counts mismatch. computed={source_counts} "
            f"expected={expected_by_source}. Not writing output.",
            file=sys.stderr,
        )
        return 1

    empty_q = [r["row_key"] for r in out_rows if not r["question"]]
    if empty_q:
        print(f"FATAL: {len(empty_q)} resolved rows carry empty question text (first 5: {empty_q[:5]}). Not writing output.", file=sys.stderr)
        return 1

    non_confab = [r["row_key"] for r in out_rows if r["role"] != "confab"]
    if non_confab:
        print(f"FATAL: {len(non_confab)} rows do not carry role 'confab' (first 5: {non_confab[:5]}). Not writing output.", file=sys.stderr)
        return 1

    out_rows.sort(key=lambda r: r["row_key"])

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for r in out_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    sha256 = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()

    print(json.dumps({
        "ok": True,
        "out_path": str(OUT_PATH.relative_to(REPO_ROOT)),
        "n_rows": len(out_rows),
        "n_target_rows": len(target_rows),
        "source_counts": source_counts,
        "expected_source_counts": expected_by_source,
        "exclusion_resolution_counts": exclusion_counts,
        "sha256": sha256,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
