#!/usr/bin/env python3
"""Deterministic CPU rebuild of the AH stage-0 candidate chain, to recover
question text for the 341 `known_correct_answered` row_keys
(`ahx::triviaqa::NNNNNN`) that `materialize_rows.py` could not resolve from
any staged/cached source (see NOTEBOOK.md 2026-07-21 entry).

WHY THIS IS RECOVERABLE (lead's scoping, verified independently below): the
341 row_keys were never lost -- they are frozen IDs in the already-committed
`split_manifest.json`. What went missing is the question TEXT, which lived
in `experiment/phase1/probe/analysis/ah_stage0/expansion/expansion_candidates.jsonl`
(gitignored GPU/CPU-pipeline output, absent everywhere local and on HF). That
file's own generator, `amendment_ah_stage0_expand_candidates.py` (read in
full, archived at
`archive/experiment/phase1/probe/amendments/amendment_ah_stage0_expand_candidates.py`),
is a DETERMINISTIC, CPU-only, seeded (20260703) function of:
  1. The AF-600 exclusion set (600 normalized questions from the frozen
     AE/AF pool) -- ONE unknown remained: this pool's row-selection was never
     committed either. Rebuilt below (Step 1).
  2. `candidates.jsonl` (the mined 5,000, itself deterministic given (1) and
     the local datasets) -- rebuilt below (Step 2), verbatim from
     `archive/experiment/phase1/probe/amendments/amendment_ah_stage0_candidates.py`.
  3. Local, already-present dataset files (SelfAware.json, kuq/*.jsonl,
     triviaqa-rc-nocontext/validation.jsonl, popqa/test.jsonl) -- Step 3,
     verbatim from `amendment_ah_stage0_expand_candidates.py`.

STEP 1 PROVENANCE (the AF-600 pool): the historical builder script
(`build_ae_base_pool_rows.py`) and its own row-selection dependency
(`load_selfaware_pool`, POOL_SEED 20260701) were never merged to main --
recovered from the abandoned local branch
`amendment-ae-base-doubt-coupled-caution` (commit 07c2a0c9, NOT an ancestor
of HEAD; read via `git show 07c2a0c9:<path>`), cross-checked against
`experiments/common/readouts/amendment_u_unified_extract.py`'s live,
currently-committed copy of `load_selfaware_pool` (identical body -- the
historical script's own docstring calls this function "vendored" from that
exact module). Both are ported VERBATIM below, with only the `gate_rows`
INPUT substituted: the original GPU extraction file
(`archive/experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/.../rows.jsonl`)
is gone, but the project's own committed, order-preserving distillation of
that exact file (`experiments/common/artifacts/selfaware_gate_pool/selfaware_gate_rows_frozen.jsonl`,
PROVENANCE.json: same source path + source_extraction_config_sha) is used in
its place -- this is the SAME substitution the project already relies on
elsewhere (see e.g.
`papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/amendment_y_results/y-b-olmo-2-7b-local_extraction_manifest.json`'s
own `gate_rows_source` pointing at this file for a live amendment run).

VERIFICATION (hard gates, not vibes): every stage's output composition is
compared EXACTLY against the two manifests independently fetched from
`professorsynapse/eh-doubt-on-command` (`metadata/stage0_candidates_manifest.json`,
`metadata/expansion_candidates_manifest.json` -- committed at Amendment AH's
own original run, long before this recovery). ANY mismatch aborts before
Step 3 runs (or before the join, if Step 3 mismatches) -- no partial credit,
no threshold loosening. A further, stronger cross-check independent of count
matching: for every `ahx::` row_key this rebuild produces that the ALREADY
VERIFIED `a0_pool_v21_questions.jsonl` staging pool also covers (i.e. was
never missing), this script asserts the question text is IDENTICAL --
positive proof against real, previously-verified text, not just internal
self-consistency.

Outputs (all gitignored under `analysis/`; verify `git check-ignore` covers
each path before trusting this docstring):
  analysis/rebuilt_af600_pool.jsonl          600 rows (row_key/label/question)
  analysis/rebuilt_candidates.jsonl          5000 rows
  analysis/rebuilt_expansion_candidates.jsonl 13496 rows
  analysis/rebuild_verification.json          all gate results, pass/fail
"""

from __future__ import annotations

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DATASETS = REPO_ROOT / "datasets"
ANALYSIS = HERE / "analysis"

GATE_ROWS = (
    REPO_ROOT
    / "experiments/common/artifacts/selfaware_gate_pool/selfaware_gate_rows_frozen.jsonl"
)
STAGING_REPO = "professorsynapse/eh-al-prep-staging"
A0_POOL_IN_REPO = "pools/a0_pool_v21_questions.jsonl"

SPLIT_MANIFEST_PATH = (
    REPO_ROOT
    / "experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json"
)

# ---------------------------------------------------------------------------
# Ported verbatim: archive/experiment/phase1/eval/scorers.py
# ---------------------------------------------------------------------------

HIR_PREFIX = re.compile(
    r"^your current knowledge expression confidence level is [0-9.]+,\s*"
    r"please answer the user's question:\s*"
)


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def norm_question(text: str) -> str:
    q = re.sub(r"\s+", " ", text.strip().lower())
    return HIR_PREFIX.sub("", q)


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


# ---------------------------------------------------------------------------
# STEP 1 -- ported verbatim: experiments/common/readouts/amendment_u_unified_extract.py
# :load_selfaware_pool, and the abandoned-branch build_ae_base_pool_rows.py /
# steering_common.build_eval_pool selection logic (POOL_SEED 20260701).
# ---------------------------------------------------------------------------

POOL_SEED = 20260701
N_KNOWN_AF = 300
N_UNKNOWN_AF = 300


def load_selfaware_pool(gate_rows: Path, seed: int) -> list[dict]:
    rows = [json.loads(l) for l in gate_rows.open(encoding="utf-8") if l.strip()]
    pool = []
    for r in rows:
        label = r.get("label")
        if label not in ("known", "unknown"):
            continue
        q = r.get("question")
        if not q:
            continue
        pool.append({
            "row_key": str(r["row_key"]),
            "dataset": "selfaware",
            "question": q,
            "label": label,
            "aliases_norm": [],
        })
    random.Random(seed).shuffle(pool)
    return pool


def _take_by_source(items: list[dict], source: str, n: int) -> list[dict]:
    picked = [it for it in items if it["source"] == source][:n]
    if len(picked) < n:
        raise ValueError(f"pool has only {len(picked)} items with source={source!r}, need {n}")
    return picked


def build_af600_pool() -> list[dict]:
    sa = load_selfaware_pool(GATE_ROWS, POOL_SEED)
    base = [{
        "row_key": it["row_key"],
        "question": it["question"],
        "source": ("selfaware_known" if it["label"] == "known" else "selfaware_unknown"),
    } for it in sa]
    pool = (_take_by_source(base, "selfaware_unknown", N_UNKNOWN_AF)
            + _take_by_source(base, "selfaware_known", N_KNOWN_AF))
    random.Random(POOL_SEED).shuffle(pool)
    return pool


# ---------------------------------------------------------------------------
# STEP 2 -- ported verbatim: archive/experiment/phase1/probe/amendments/
# amendment_ah_stage0_candidates.py
# ---------------------------------------------------------------------------

TARGET_UNANS = 2500
TARGET_ANS = 2500
SEED_AH = 20260703


def load_selfaware(exclude: set[str]):
    data = json.loads((DATASETS / "selfaware" / "SelfAware.json").read_text())
    items = data["example"]
    out = []
    for it in items:
        q = it["question"]
        nq = norm_question(q)
        if nq in exclude:
            continue
        answerable = bool(it.get("answerable"))
        if answerable:
            aliases = [normalize(str(a)) for a in _as_list(it.get("answer"))]
            aliases = [a for a in aliases if a]
            out.append(("known", q, aliases, "selfaware_answerable"))
        else:
            out.append(("unknown", q, [], "selfaware_unanswerable"))
    return out


def load_kuq_knowns(exclude: set[str]):
    knowns, unknowns = [], []
    with (DATASETS / "kuq" / "knowns_unknowns.jsonl").open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            q = r["question"]
            nq = norm_question(q)
            if nq in exclude:
                continue
            if r.get("unknown"):
                unknowns.append(("unknown", q, [], "kuq_ku_unknown"))
            else:
                aliases = [normalize(str(a)) for a in _as_list(r.get("answer"))]
                aliases = [a for a in aliases if a]
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
            nq = norm_question(q)
            if nq in exclude:
                continue
            out.append(("unknown", q, [], "kuq_unknowns_all"))
    return out


def make_row_key_ah(source: str, idx: int) -> str:
    return f"ah::{source}::{idx:06d}"


def build_candidates(af600_questions: set[str]) -> list[dict]:
    rng = random.Random(SEED_AH)
    seen = set(af600_questions)

    def dedupe(items):
        kept = []
        for label, q, aliases, source in items:
            nq = norm_question(q)
            if nq in seen:
                continue
            seen.add(nq)
            kept.append((label, q, aliases, source))
        return kept

    sa = dedupe(load_selfaware(af600_questions))
    sa_ans = [x for x in sa if x[0] == "known"]
    sa_unans = [x for x in sa if x[0] == "unknown"]

    kuq_kn, kuq_ku_unk = load_kuq_knowns(seen)
    kuq_kn = dedupe(kuq_kn)
    kuq_ku_unk = dedupe(kuq_ku_unk)
    kuq_ua = dedupe(load_kuq_unknowns_all(seen))

    rng.shuffle(kuq_kn)
    rng.shuffle(kuq_ku_unk)
    rng.shuffle(kuq_ua)

    answerable = list(sa_ans)
    need_ans = max(0, TARGET_ANS - len(answerable))
    answerable += kuq_kn[:need_ans]

    unanswerable = list(sa_unans)
    need_unans = max(0, TARGET_UNANS - len(unanswerable))
    take_ku = kuq_ku_unk[:need_unans]
    unanswerable += take_ku
    need_unans2 = max(0, TARGET_UNANS - len(unanswerable))
    unanswerable += kuq_ua[:need_unans2]

    pool = answerable + unanswerable
    rng.shuffle(pool)

    rows = []
    for idx, (label, q, aliases, source) in enumerate(pool):
        rows.append({
            "row_key": make_row_key_ah(source, idx),
            "label": label,
            "question": q,
            "aliases": aliases,
            "source": source,
        })
    return rows


# ---------------------------------------------------------------------------
# STEP 3 -- ported verbatim: archive/experiment/phase1/probe/amendments/
# amendment_ah_stage0_expand_candidates.py
# ---------------------------------------------------------------------------

TARGET_ANSWERABLE = 10000
TRIVIA_LIMIT = 6000


def iter_new_kuq_unknowns(exclude: set[str]):
    seen = set(exclude)
    out = []
    for fname, qkey in (("knowns_unknowns.jsonl", "question"), ("unknowns_all.jsonl", "question")):
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
                nq = norm_question(q)
                if nq in seen:
                    continue
                seen.add(nq)
                out.append((q, r.get("category") or ""))
    return out


def iter_triviaqa(exclude: set[str], limit: int):
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
            nq = norm_question(q)
            if nq in seen:
                continue
            ans = r.get("answer") or {}
            aliases = [normalize(str(a)) for a in _as_list(ans.get("normalized_aliases") or ans.get("aliases"))]
            aliases = [a for a in aliases if a]
            if not aliases:
                continue
            seen.add(nq)
            out.append((q, aliases))
            if limit and len(out) >= limit:
                break
    return out


def iter_popqa(exclude: set[str], limit: int):
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
            nq = norm_question(q)
            if nq in seen:
                continue
            raw = r.get("possible_answers")
            try:
                cand = json.loads(raw) if isinstance(raw, str) else _as_list(raw)
            except (json.JSONDecodeError, TypeError):
                cand = []
            aliases = [normalize(str(a)) for a in cand]
            aliases = [a for a in aliases if a]
            if not aliases:
                continue
            seen.add(nq)
            out.append((q, aliases))
            if limit and len(out) >= limit:
                break
    return out


def make_row_key_ahx(source: str, idx: int) -> str:
    return f"ahx::{source}::{idx:06d}"


def build_expansion(af600_questions: set[str], candidates_rows: list[dict]) -> list[dict]:
    mined = {norm_question(r["question"]) for r in candidates_rows}
    exclude = set(af600_questions) | mined

    new_ku = iter_new_kuq_unknowns(exclude)

    excl_ans = set(exclude)
    tqa = iter_triviaqa(excl_ans, TRIVIA_LIMIT)
    for q, _ in tqa:
        excl_ans.add(norm_question(q))
    remaining = max(0, TARGET_ANSWERABLE - len(tqa))
    pqa = iter_popqa(excl_ans, remaining)

    pool = []
    idx = 0
    for q, cat in new_ku:
        pool.append({"row_key": make_row_key_ahx("kuq_ku_unknown_x", idx), "label": "unknown",
                      "question": q, "aliases": [], "source": "kuq_ku_unknown_x", "category": cat})
        idx += 1
    for q, aliases in tqa:
        pool.append({"row_key": make_row_key_ahx("triviaqa", idx), "label": "known",
                      "question": q, "aliases": aliases, "source": "triviaqa", "category": ""})
        idx += 1
    for q, aliases in pqa:
        pool.append({"row_key": make_row_key_ahx("popqa", idx), "label": "known",
                      "question": q, "aliases": aliases, "source": "popqa", "category": ""})
        idx += 1
    # Note: the original script's final rng.shuffle(pool) only reorders the
    # WRITE order to expansion_candidates.jsonl; row_key<->question is fixed
    # by idx assignment above, before the shuffle. Preserved here for fidelity
    # (does not affect the row_key join this script exists to serve).
    random.Random(SEED_AH).shuffle(pool)
    return pool, new_ku, tqa, pqa


# ---------------------------------------------------------------------------
# Verification targets, fetched independently from
# professorsynapse/eh-doubt-on-command (metadata/*_manifest.json), the
# original Amendment AH run's own committed provenance. See NOTEBOOK.md.
# ---------------------------------------------------------------------------

STAGE0_MANIFEST_TARGET = {
    "af600_excluded": 600,
    "n_total": 5000,
    "n_known_answerable": 2500,
    "n_unknown_unanswerable": 2500,
    "composition_by_source": {
        "kuq_ku_unknown": 1768,
        "selfaware_answerable": 2034,
        "selfaware_unanswerable": 732,
        "kuq_ku_known": 466,
    },
}

EXPANSION_MANIFEST_TARGET = {
    "exclude_af600": 600,
    "exclude_mined": 5000,
    "n_total_expansion": 13496,
    "n_new_kuq_unknown": 3496,
    "n_triviaqa": 6000,
    "n_popqa": 4000,
    "composition_by_source": {
        "triviaqa": 6000,
        "popqa": 4000,
        "kuq_ku_unknown_x": 3496,
    },
    "new_kuq_category_split": {
        "controversial": 150,
        "unsolved problem": 90,
        "future unknown": 672,
        "false assumption": 98,
        "counterfactual": 104,
        "ambiguous": 111,
        "controversial/debatable question": 545,
        "underspecified question": 424,
        "unsolved problem/mistery": 427,
        "question with false assumption": 390,
        "counterfactual questions": 485,
    },
}


def main() -> int:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    gates: dict[str, object] = {}
    all_pass = True

    def gate(name: str, ok: bool, detail: object) -> None:
        nonlocal all_pass
        gates[name] = {"pass": bool(ok), "detail": detail}
        all_pass = all_pass and ok
        print(f"[rebuild] GATE {name}: {'PASS' if ok else 'FAIL'} {detail}", flush=True)

    # ---- Step 1: AF-600 pool ----
    af600_pool = build_af600_pool()
    gate("af600_pool_size", len(af600_pool) == 600, {"n": len(af600_pool)})
    af600_questions = {norm_question(r["question"]) for r in af600_pool}
    gate("af600_unique_questions", len(af600_questions) == 600,
         {"n_unique": len(af600_questions)})
    (ANALYSIS / "rebuilt_af600_pool.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in af600_pool) + "\n",
        encoding="utf-8",
    )
    if not all_pass:
        (ANALYSIS / "rebuild_verification.json").write_text(json.dumps(gates, indent=2))
        print("[rebuild] STOP: Step 1 gate failed, not proceeding.", file=sys.stderr)
        return 1

    # ---- Step 2: candidates.jsonl ----
    candidates = build_candidates(af600_questions)
    comp2 = Counter(r["source"] for r in candidates)
    n_known2 = sum(1 for r in candidates if r["label"] == "known")
    n_unknown2 = len(candidates) - n_known2
    gate("stage0_n_total", len(candidates) == STAGE0_MANIFEST_TARGET["n_total"],
         {"got": len(candidates), "want": STAGE0_MANIFEST_TARGET["n_total"]})
    gate("stage0_composition", dict(comp2) == STAGE0_MANIFEST_TARGET["composition_by_source"],
         {"got": dict(comp2), "want": STAGE0_MANIFEST_TARGET["composition_by_source"]})
    gate("stage0_known_unknown_split",
         n_known2 == STAGE0_MANIFEST_TARGET["n_known_answerable"]
         and n_unknown2 == STAGE0_MANIFEST_TARGET["n_unknown_unanswerable"],
         {"n_known": n_known2, "n_unknown": n_unknown2})
    (ANALYSIS / "rebuilt_candidates.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in candidates) + "\n",
        encoding="utf-8",
    )
    if not all_pass:
        (ANALYSIS / "rebuild_verification.json").write_text(json.dumps(gates, indent=2))
        print("[rebuild] STOP: Step 2 gate failed, not proceeding to Step 3.", file=sys.stderr)
        return 1

    # ---- Step 3: expansion_candidates.jsonl ----
    expansion, new_ku, tqa, pqa = build_expansion(af600_questions, candidates)
    comp3 = Counter(r["source"] for r in expansion)
    ku_cat = Counter(c or "(none)" for _, c in new_ku)
    gate("expansion_n_total", len(expansion) == EXPANSION_MANIFEST_TARGET["n_total_expansion"],
         {"got": len(expansion), "want": EXPANSION_MANIFEST_TARGET["n_total_expansion"]})
    gate("expansion_composition", dict(comp3) == EXPANSION_MANIFEST_TARGET["composition_by_source"],
         {"got": dict(comp3), "want": EXPANSION_MANIFEST_TARGET["composition_by_source"]})
    gate("expansion_kuq_category_split", dict(ku_cat) == EXPANSION_MANIFEST_TARGET["new_kuq_category_split"],
         {"got": dict(ku_cat), "want": EXPANSION_MANIFEST_TARGET["new_kuq_category_split"]})
    (ANALYSIS / "rebuilt_expansion_candidates.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in expansion) + "\n",
        encoding="utf-8",
    )
    if not all_pass:
        (ANALYSIS / "rebuild_verification.json").write_text(json.dumps(gates, indent=2))
        print("[rebuild] STOP: Step 3 gate failed, not proceeding to the join.", file=sys.stderr)
        return 1

    # ---- Join: the 341 missing known_correct_answered row_keys ----
    split_manifest = json.loads(SPLIT_MANIFEST_PATH.read_text())
    kca_keys = {r["row_key"] for r in split_manifest["rows"] if r["role"] == "known_correct_answered"}
    # by_key covers BOTH stage0 outputs: ah:: rows live in candidates.jsonl
    # (Step 2), ahx:: rows live in expansion_candidates.jsonl (Step 3). The
    # known_correct_answered role draws from both (verified breakdown:
    # ahx::triviaqa 370, ah::kuq_ku_known 26, ah::selfaware_answerable 22,
    # ahx::popqa 12 = 430).
    by_key = {r["row_key"]: r for r in candidates}
    by_key.update({r["row_key"]: r for r in expansion})
    resolved = {k: by_key[k] for k in kca_keys if k in by_key}
    still_missing = sorted(kca_keys - set(resolved))
    gate("join_341_missing_resolved",
         len(still_missing) == 0 and len(resolved) == len(kca_keys),
         {"n_kca_keys": len(kca_keys), "n_resolved_by_rebuild": len(resolved),
          "n_still_missing": len(still_missing), "sample_still_missing": still_missing[:10]})
    empty_text = [k for k, r in resolved.items() if not r.get("question")]
    empty_alias_known = [k for k, r in resolved.items() if not r.get("aliases")]
    gate("join_no_empty_question_text", len(empty_text) == 0,
         {"n_empty": len(empty_text), "sample": empty_text[:10]})
    gate("join_no_empty_aliases", len(empty_alias_known) == 0,
         {"n_empty": len(empty_alias_known), "sample": empty_alias_known[:10]})
    # Prefix sanity vs the pre-declared breakdown (verified directly against
    # split_manifest.json before writing this script): every resolved key
    # must be one of these four (source, count) pairs, exactly.
    prefixes = Counter("::".join(k.split("::")[:2]) for k in resolved)
    expected_prefixes = {
        "ahx::triviaqa": 370, "ah::kuq_ku_known": 26,
        "ah::selfaware_answerable": 22, "ahx::popqa": 12,
    }
    gate("join_prefix_matches_expected", dict(prefixes) == expected_prefixes,
         {"got": dict(prefixes), "want": expected_prefixes})

    # ---- Zero-overlap check (lead's explicit gate): the 341 keys this rebuild
    # exists to recover must be disjoint from the 89 keys a0_pool_v21_questions
    # already resolved (trivially true by construction -- they partition the
    # 430 known_correct_answered keys -- verified explicitly rather than assumed).
    from huggingface_hub import hf_hub_download as _hf_dl_precheck
    _a0_path_precheck = Path(_hf_dl_precheck(repo_id=STAGING_REPO, filename=A0_POOL_IN_REPO, repo_type="dataset"))
    _a0_keys_precheck = set()
    with _a0_path_precheck.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                r = json.loads(line)
                if r.get("row_key"):
                    _a0_keys_precheck.add(r["row_key"])
    originally_resolved = kca_keys & _a0_keys_precheck
    originally_missing = kca_keys - _a0_keys_precheck
    overlap = originally_resolved & originally_missing
    gate("zero_overlap_originally_resolved_vs_missing",
         len(overlap) == 0 and len(originally_resolved) == 89 and len(originally_missing) == 341,
         {"n_originally_resolved": len(originally_resolved),
          "n_originally_missing": len(originally_missing), "n_overlap": len(overlap)})

    # ---- Cross-check against ALREADY-VERIFIED text (a0_pool_v21_questions.jsonl) ----
    from huggingface_hub import hf_hub_download

    a0_path = Path(hf_hub_download(repo_id=STAGING_REPO, filename=A0_POOL_IN_REPO, repo_type="dataset"))
    a0_questions: dict[str, str] = {}
    with a0_path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("row_key") and r.get("question"):
                a0_questions[r["row_key"]] = r["question"]

    cross_check_n = 0
    cross_check_mismatches: list[str] = []
    for row_key, verified_q in a0_questions.items():
        if row_key.startswith("ahx::") and row_key in by_key:
            cross_check_n += 1
            if by_key[row_key]["question"] != verified_q:
                cross_check_mismatches.append(row_key)
    gate("cross_check_vs_verified_a0_pool",
         cross_check_n > 0 and len(cross_check_mismatches) == 0,
         {"n_checked": cross_check_n, "n_mismatches": len(cross_check_mismatches),
          "sample_mismatches": cross_check_mismatches[:10]})

    (ANALYSIS / "rebuild_verification.json").write_text(json.dumps(gates, indent=2))
    print(f"\n[rebuild] ALL GATES {'PASS' if all_pass else 'FAIL'}", flush=True)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
