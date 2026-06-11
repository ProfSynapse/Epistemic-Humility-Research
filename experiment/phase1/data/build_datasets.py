#!/usr/bin/env python3
"""Component B - Phase 1 dataset builders (paper 2: SFT vs DPO vs KTO abstention).

Location: experiment/phase1/data/build_datasets.py
Reads:    a probe_results.jsonl (Component A / coder-probe contract, arch doc
          section 3.8), datasets/triviaqa-rc-nocontext/cheng_test_gold.jsonl
          (held-out test keys for the leakage guard), abstention_bank.json
          (checked-in marker-bearing phrasings), and config/build.yaml.
Writes:   four training arms (SFT / DPO / KTO-congruence / KTO-correctness-safe)
          as train+dev JSONL plus questions_frozen.json and build_manifest.json,
          under experiment/phase1/data/<model_tag>/ (arch doc section 4.8).

Single responsibility: labeling-to-training-format transform. This module owns
four load-bearing, pre-registered invariants (arch doc sections 3.2, 4.2, 4.3, 4.7):
  1. LEAKAGE GUARD - normalized(probe questions) intersect normalized(Cheng test)
     MUST be empty. Hard abort (LeakageError) on any overlap. Uses norm_question
     (the whitespace-collapse form that keys cheng_test_gold.jsonl), NOT the
     alphanumeric-token normalize used for answers (auditor watch-item).
  2. BUDGET = distinct source QUESTIONS - one frozen K/U set + one shared seed,
     all four arms derived from it; per-arm row-count expansion is documented in
     the manifest, not treated as a confound.
  3. ABSTENTION MARKER INVARIANT - every abstention phrasing must contain one of
     the four eval refusal markers; the builder re-validates the bank and aborts
     if any phrasing matches none.
  4. DEV SPLIT - one held-out dev set (fixed fraction/seed) from the frozen set,
     format-matched per arm, excluded from every arm's train file, identical dev
     questions across arms.

Determinism: all randomness is seeded; builds reproduce from probe_results +
config + abstention_bank. No live generation, no network, no hardcoded paths.

Usage:
    python build_datasets.py --config config/build.yaml --model-tag qwen3-4b-instruct
    python build_datasets.py --config config/build.yaml --model-tag <tag> \
        --probe-results <path> --output-dir <dir>   # overrides for fixtures/tests
"""

import argparse
import hashlib
import json
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Ported correctness / refusal primitives.
#
# Re-implemented here (NOT imported) from the read-only Cheng reanalysis
# meta-analysis/analysis/reanalyze_idk_outputs.py so the builder carries no
# dependency on the read-only paper-1 tree. norm_question MUST stay byte-identical
# to the reanalysis version because cheng_test_gold.jsonl is keyed by it and the
# leakage guard intersects against those keys.
# ---------------------------------------------------------------------------

REFUSAL_MARKERS = (
    "beyond the scope of my knowledge",
    "i am not sure what the answer is",
    "i don't know the answer",
    "i do not know the answer",
)

# HIR-style confidence-conditioning prefix the reanalysis strips before keying.
# Kept here verbatim so norm_question matches the gold keys exactly.
HIR_PREFIX = re.compile(
    r"^your current knowledge expression confidence level is [0-9.]+,\s*"
    r"please answer the user's question:\s*"
)


def norm_question(text: str) -> str:
    """Question-key normalization: whitespace-collapse + lowercase + HIR strip.

    This is the form that keys cheng_test_gold.jsonl. The leakage guard depends
    on this matching the reanalysis exactly; do not swap it for `normalize`.
    """
    q = re.sub(r"\s+", " ", text.strip().lower())
    return HIR_PREFIX.sub("", q)


def normalize(text: str) -> str:
    """Answer/alias normalization: alphanumeric tokens joined by single spaces."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def is_refusal(text: str) -> bool:
    """True iff `text` contains one of the four eval refusal markers."""
    lowered = text.lower()
    return any(marker in lowered for marker in REFUSAL_MARKERS)


# ---------------------------------------------------------------------------
# Errors.
# ---------------------------------------------------------------------------


class LeakageError(RuntimeError):
    """Raised when probe/train questions overlap the Cheng held-out test set.

    This is a hard abort. A leak silently invalidates every downstream result
    and the bridge-arm comparison to published numbers, so the build must stop.
    """


class AbstentionBankError(ValueError):
    """Raised when an abstention phrasing carries no refusal marker."""


class ProbeSchemaError(ValueError):
    """Raised when a probe record is missing a required field."""


class DevSplitError(ValueError):
    """Raised when the train/dev split degenerates to an empty train or dev set."""


# ---------------------------------------------------------------------------
# Loading + validation.
# ---------------------------------------------------------------------------

REQUIRED_PROBE_FIELDS = (
    "question_id",
    "question",
    "normalized_aliases",
    "greedy_answer",
    "p_correct",
    "sampled_answers",
    "sampled_correct",
    "label",
)


def load_jsonl(path: Path) -> list:
    """Load a JSONL file into a list of dicts."""
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return records


def load_probe_records(path: Path) -> list:
    """Load probe_results.jsonl and validate the required-field contract."""
    records = load_jsonl(path)
    if not records:
        raise ProbeSchemaError(f"{path}: probe results are empty")
    for idx, rec in enumerate(records):
        missing = [f for f in REQUIRED_PROBE_FIELDS if f not in rec]
        if missing:
            raise ProbeSchemaError(
                f"{path}: record {idx} (question_id="
                f"{rec.get('question_id', '?')}) missing fields: {missing}"
            )
    return records


def load_abstention_bank(path: Path) -> list:
    """Load + validate the abstention bank; every phrasing must carry a marker."""
    data = json.loads(path.read_text(encoding="utf-8"))
    phrasings = data.get("phrasings", [])
    if not phrasings:
        raise AbstentionBankError(f"{path}: abstention bank has no phrasings")
    offenders = [p for p in phrasings if not is_refusal(p)]
    if offenders:
        raise AbstentionBankError(
            f"{path}: {len(offenders)} abstention phrasing(s) carry no refusal "
            f"marker and would break eval-time refusal detection. First: "
            f"{offenders[0]!r}. Allowed markers: {list(REFUSAL_MARKERS)}"
        )
    return phrasings


def load_cheng_test_norms(path: Path) -> set:
    """Load the Cheng test question_norm keys for the leakage guard."""
    norms = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            # cheng_test_gold.jsonl is pre-keyed by question_norm; re-derive
            # defensively from `question` if the field is absent.
            key = rec.get("question_norm") or norm_question(rec.get("question", ""))
            if key:
                norms.add(key)
    return norms


# ---------------------------------------------------------------------------
# Leakage guard (load-bearing, pre-registered).
# ---------------------------------------------------------------------------


def assert_no_leakage(probe_records: list, cheng_norms: set) -> dict:
    """Abort if any probe question appears in the Cheng held-out test set.

    Returns a small proof dict (counts + sample of any offenders) for the
    manifest. The probe side is ALWAYS re-derived here via this module's own
    norm_question rather than trusting a probe-stored `question_norm`: a stale or
    divergent stored value must never be able to weaken the guard by making it
    compare the wrong keys. The Cheng side keeps its on-disk `question_norm` key,
    which is the pinned, provenance-verified canonical join key for that gold file
    (see load_cheng_test_norms).
    """
    if not cheng_norms:
        # Fail closed: a guard that cannot load the test set must not pass
        # vacuously (teachback contingency clause).
        raise LeakageError(
            "leakage guard could not load any Cheng test question keys; "
            "refusing to build (fail-closed). Check inputs.cheng_test_gold."
        )
    probe_norms = {norm_question(rec["question"]) for rec in probe_records}
    overlap = sorted(probe_norms & cheng_norms)
    if overlap:
        sample = overlap[:5]
        raise LeakageError(
            f"LEAKAGE GUARD FAILED: {len(overlap)} probe/train question(s) "
            f"appear in the Cheng held-out test set. This invalidates the "
            f"experiment. First offenders: {sample}. "
            f"Probe and Cheng test sets MUST be disjoint (arch doc section 3.2)."
        )
    return {
        "probe_question_count": len(probe_norms),
        "cheng_test_question_count": len(cheng_norms),
        "intersection_count": 0,
        "passed": True,
    }


# ---------------------------------------------------------------------------
# Frozen question set (budget anchor).
# ---------------------------------------------------------------------------


def gold_answer(rec: dict) -> str:
    """Pick the gold short answer for a known question.

    Prefers the natural-case `answer_value` (e.g. "John Milton") when the probe
    propagated it, so the known training target matches how the base model
    naturally answers rather than the lowercased TriviaQA normalized alias
    ("john milton"). Falls back to the first non-empty normalized alias when
    `answer_value` is absent (older probe outputs), keeping the builder
    forward- and backward-compatible across the A->B contract.
    """
    value = rec.get("answer_value")
    if isinstance(value, str) and value.strip():
        return value
    for alias in rec.get("normalized_aliases", []):
        if alias and alias.strip():
            return alias
    raise ProbeSchemaError(
        f"known question {rec.get('question_id')} has no usable gold answer "
        f"(no answer_value and no non-empty normalized alias)"
    )


def hallucinated_sample(rec: dict):
    """Return the model's own wrong probe sample for an unknown question, or None.

    The wrong sample is the KTO/DPO undesirable on unknowns (arch doc section 4.5,
    4.6). Pairs sampled_answers with sampled_correct; returns the first answer
    flagged incorrect. None if the probe retained no wrong sample.
    """
    answers = rec.get("sampled_answers", [])
    flags = rec.get("sampled_correct", [])
    for answer, correct in zip(answers, flags):
        if correct is False and isinstance(answer, str) and answer.strip():
            return answer
    return None


def select_frozen_set(probe_records: list, config: dict) -> dict:
    """Draw the frozen known/unknown question set deterministically.

    Budget = distinct source questions. Applies optional per-class caps and
    label balancing with the shared seed, then freezes the result so all four
    arms derive from the identical set.
    """
    known = [r for r in probe_records if r["label"] == "known"]
    unknown = [r for r in probe_records if r["label"] == "unknown"]

    rng = random.Random(config["seed"])
    known = _cap(known, config.get("max_known_questions"), rng)
    unknown = _cap(unknown, config.get("max_unknown_questions"), rng)

    if config.get("balance_labels"):
        size = min(len(known), len(unknown))
        known = _cap(known, size, rng)
        unknown = _cap(unknown, size, rng)

    return {"known": known, "unknown": unknown}


def _cap(records: list, cap, rng: random.Random) -> list:
    """Deterministically subsample `records` to at most `cap` (None = keep all)."""
    if cap is None or cap >= len(records):
        return sorted(records, key=lambda r: r["question_id"])
    ordered = sorted(records, key=lambda r: r["question_id"])
    chosen = rng.sample(ordered, cap)
    return sorted(chosen, key=lambda r: r["question_id"])


def split_dev(records: list, fraction: float, seed: int) -> tuple:
    """Split a question list into (train, dev) deterministically by question_id.

    The dev questions are the SAME across arms (caller passes the same records
    and seed), so early stopping is comparable.

    Raises DevSplitError if the split degenerates to an empty side: dev=0 (N too
    small or fraction too low to yield a held-out set for Gekhman early stopping)
    or train=0 (fraction too high, leaving nothing to train on). Either case would
    silently produce an unusable arm, so it is a hard, explained abort.
    """
    ordered = sorted(records, key=lambda r: r["question_id"])
    rng = random.Random(seed)
    rng.shuffle(ordered)
    dev_count = int(round(len(ordered) * fraction))
    dev = ordered[:dev_count]
    train = ordered[dev_count:]
    if not dev:
        raise DevSplitError(
            f"dev split is empty: {len(ordered)} question(s) x dev_fraction="
            f"{fraction} rounds to 0 dev examples. Early stopping needs a "
            f"non-empty dev set; raise dev_fraction or supply more questions."
        )
    if not train:
        raise DevSplitError(
            f"train split is empty: dev_fraction={fraction} consumed all "
            f"{len(ordered)} question(s). Lower dev_fraction below 1.0."
        )
    return train, dev


# ---------------------------------------------------------------------------
# Abstention sampling (deterministic, per question_id).
# ---------------------------------------------------------------------------


def abstention_for(question_id: str, bank: list, seed: int) -> str:
    """Pick an abstention phrasing for a question deterministically.

    Seeds on (seed, question_id) so the same question always draws the same
    phrasing across arms and across reruns.
    """
    local = random.Random(f"{seed}:{question_id}")
    return local.choice(bank)


# ---------------------------------------------------------------------------
# Per-arm record emitters.
# ---------------------------------------------------------------------------


def _system_msg(system_prompt: str) -> dict:
    return {"role": "system", "content": system_prompt}


def build_sft_row(rec: dict, ctx: dict) -> dict:
    """One SFT positive: known -> gold answer, unknown -> abstention."""
    if rec["label"] == "known":
        target = ctx["known_answer_template"].format(answer=gold_answer(rec))
    else:
        target = abstention_for(rec["question_id"], ctx["bank"], ctx["seed"])
    return {
        "conversations": [
            _system_msg(ctx["system_prompt"]),
            {"role": "user", "content": rec["question"]},
            {"role": "assistant", "content": target},
        ]
    }


def build_dpo_row(rec: dict, ctx: dict):
    """One DPO pair. Returns None if an unknown question has no usable negative.

    known:   chosen = gold answer, rejected = abstention (the over-refusal we
             train against).
    unknown: chosen = abstention, rejected = the model's own hallucinated sample
             (fallback per config.unknown_negative_source when none exists).
    """
    abstention = abstention_for(rec["question_id"], ctx["bank"], ctx["seed"])
    if rec["label"] == "known":
        chosen = ctx["known_answer_template"].format(answer=gold_answer(rec))
        rejected = abstention
    else:
        chosen = abstention
        rejected = _unknown_negative(rec, ctx)
        if rejected is None:
            return None
    return {
        "prompt": [
            _system_msg(ctx["system_prompt"]),
            {"role": "user", "content": rec["question"]},
        ],
        "chosen": [{"role": "assistant", "content": chosen}],
        "rejected": [{"role": "assistant", "content": rejected}],
    }


def _unknown_negative(rec: dict, ctx: dict):
    """Resolve the undesirable completion for an unknown question, or None.

    Prefers the model's own hallucinated sample; falls back per config strategy.
    Records dropped/distractor-substituted question_ids on ctx for the manifest.
    """
    sample = hallucinated_sample(rec)
    if sample is not None:
        return sample
    strategy = ctx["unknown_negative_strategy"]
    if strategy == "distractor":
        ctx["distractor_substituted"].append(rec["question_id"])
        return ctx["distractor_text"]
    ctx["dropped_no_negative"].append(rec["question_id"])
    return None


def _kto_rows_for_question(rec: dict, ctx: dict) -> list:
    """Emit the KTO (completion, label) rows for one question.

    BOTH mappings (congruence and correctness_safe) emit the SAME four rows
    (arch doc section 4.6, weights-only ablation ruling):
      known+gold = true, unknown+abstention = true,
      unknown+hallucinated = false, known+abstention = false.

    The congruence vs correctness_safe difference is NOT in the row set; it lives
    entirely in the desirable_weight / undesirable_weight applied at training time
    (build.yaml correctness_safe_*_weight, surfaced into the recipe YAMLs). Emitting
    only desirable rows for correctness_safe would produce a 100%-True file that
    crashes the tuner: interleave_dataset collapses to min(n_true, 0) -> empty, and
    the undesirable-count division raises ZeroDivisionError at load time. So both
    mappings carry both labels; the row set is mapping-independent by construction.
    """
    abstention = abstention_for(rec["question_id"], ctx["bank"], ctx["seed"])
    rows = []
    if rec["label"] == "known":
        gold = ctx["known_answer_template"].format(answer=gold_answer(rec))
        rows.append(_kto_row(rec, gold, True, ctx))            # known+gold = true
        rows.append(_kto_row(rec, abstention, False, ctx))     # known+abstain = false
    else:
        rows.append(_kto_row(rec, abstention, True, ctx))      # unknown+abstain = true
        negative = _unknown_negative(rec, ctx)
        if negative is not None:
            rows.append(_kto_row(rec, negative, False, ctx))   # unknown+halluc = false
    return rows


def _kto_row(rec: dict, completion: str, label: bool, ctx: dict) -> dict:
    return {
        "conversations": [
            _system_msg(ctx["system_prompt"]),
            {"role": "user", "content": rec["question"]},
            {"role": "assistant", "content": completion},
        ],
        "label": label,
    }


def interleave_kto(rows: list, seed: int) -> list:
    """Pre-interleave KTO rows T/F/T/F (fixed seed), balancing by truncation.

    Mirrors the tuner's interleave_dataset (Trainers/kto/src/data_loader.py): the
    trainer re-interleaves as a safety net, but writing an already-interleaved,
    human-inspectable file is the architect's instruction (arch doc section 4.6).
    """
    rng = random.Random(seed)
    trues = [r for r in rows if r["label"] is True]
    falses = [r for r in rows if r["label"] is False]
    rng.shuffle(trues)
    rng.shuffle(falses)
    count = min(len(trues), len(falses))
    interleaved = []
    for i in range(count):
        interleaved.append(trues[i])
        interleaved.append(falses[i])
    return interleaved


# ---------------------------------------------------------------------------
# Output writing.
# ---------------------------------------------------------------------------


def write_jsonl(path: Path, rows: list) -> None:
    """Write rows as JSONL (one compact object per line), creating parents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    """SHA-256 of a file's bytes (provenance stamp)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------


def _make_context(config: dict, bank: list) -> dict:
    """Assemble the shared per-build context passed to every emitter."""
    neg = config.get("unknown_negative_source", {})
    templates = config["templates"]
    return {
        "system_prompt": templates["system_prompt"],
        "known_answer_template": templates["known_answer_template"],
        "bank": bank,
        "seed": config["seed"],
        "unknown_negative_strategy": neg.get("strategy", "drop"),
        "distractor_text": neg.get("distractor_text", ""),
        "dropped_no_negative": [],
        "distractor_substituted": [],
    }


def build_all(config: dict, model_tag: str, paths: dict) -> dict:
    """Run the full build for one model_tag. Returns the manifest dict."""
    probe_records = load_probe_records(paths["probe_results"])
    cheng_norms = load_cheng_test_norms(paths["cheng_test_gold"])
    bank = load_abstention_bank(paths["abstention_bank"])

    # Invariant 1: leakage guard (hard abort).
    leakage_proof = assert_no_leakage(probe_records, cheng_norms)

    # Invariant 2: frozen budget set.
    frozen = select_frozen_set(probe_records, config)
    all_questions = frozen["known"] + frozen["unknown"]

    # Invariant 4: one dev split, identical questions across arms.
    train_recs, dev_recs = split_dev(
        all_questions, config["dev_fraction"], config["seed"]
    )

    ctx = _make_context(config, bank)
    out_dir = paths["output_dir"]
    counts = {}

    _emit_sft(train_recs, dev_recs, ctx, out_dir, counts)
    _emit_dpo(train_recs, dev_recs, ctx, out_dir, counts)
    _emit_kto("congruence", train_recs, dev_recs, ctx, config, out_dir, counts)
    if config.get("kto", {}).get("emit_correctness_safe", False):
        _emit_kto(
            "correctness_safe", train_recs, dev_recs, ctx, config, out_dir, counts
        )

    frozen_path = _write_frozen(frozen, train_recs, dev_recs, config, out_dir)
    manifest = _assemble_manifest(
        config, model_tag, paths, frozen, train_recs, dev_recs,
        leakage_proof, counts, ctx, bank,
    )
    manifest["questions_frozen_sha256"] = sha256_file(frozen_path)
    _write_manifest(out_dir, manifest)
    return manifest


def _emit_sft(train, dev, ctx, out_dir, counts) -> None:
    train_rows = [build_sft_row(r, ctx) for r in train]
    dev_rows = [build_sft_row(r, ctx) for r in dev]
    write_jsonl(out_dir / "sft_train.jsonl", train_rows)
    write_jsonl(out_dir / "sft_dev.jsonl", dev_rows)
    counts["sft"] = {"train_rows": len(train_rows), "dev_rows": len(dev_rows)}


def _emit_dpo(train, dev, ctx, out_dir, counts) -> None:
    train_rows = [row for r in train if (row := build_dpo_row(r, ctx))]
    dev_rows = [row for r in dev if (row := build_dpo_row(r, ctx))]
    write_jsonl(out_dir / "dpo_train.jsonl", train_rows)
    write_jsonl(out_dir / "dpo_dev.jsonl", dev_rows)
    counts["dpo"] = {"train_rows": len(train_rows), "dev_rows": len(dev_rows)}


def _emit_kto(mapping, train, dev, ctx, config, out_dir, counts) -> None:
    # Both mappings emit the same four-row set (_kto_rows_for_question is
    # mapping-independent per the weights-only ruling); the only mapping-specific
    # output difference is the filename. Both are pre-interleaved T/F/T/F so the
    # on-disk file is training-ready and balanced (the tuner re-interleaves as a
    # safety net). A non-interleaved correctness_safe file used to reach the
    # trainer all-True and crash it; interleaving both arms closes that.
    train_rows = [row for r in train for row in _kto_rows_for_question(r, ctx)]
    dev_rows = [row for r in dev for row in _kto_rows_for_question(r, ctx)]
    train_rows = interleave_kto(train_rows, config["seed"])
    dev_rows = interleave_kto(dev_rows, config["seed"])
    write_jsonl(out_dir / f"kto_{mapping}_train.jsonl", train_rows)
    write_jsonl(out_dir / f"kto_{mapping}_dev.jsonl", dev_rows)
    counts[f"kto_{mapping}"] = {
        "train_rows": len(train_rows),
        "dev_rows": len(dev_rows),
        "train_desirable": sum(1 for r in train_rows if r["label"] is True),
        "train_undesirable": sum(1 for r in train_rows if r["label"] is False),
    }


def _write_frozen(frozen, train_recs, dev_recs, config, out_dir) -> Path:
    """Write questions_frozen.json (the budget anchor) and return its path."""
    dev_ids = {r["question_id"] for r in dev_recs}
    payload = {
        "seed": config["seed"],
        "budget_distinct_questions": len(frozen["known"]) + len(frozen["unknown"]),
        "known_question_ids": [r["question_id"] for r in frozen["known"]],
        "unknown_question_ids": [r["question_id"] for r in frozen["unknown"]],
        "train_question_ids": [r["question_id"] for r in train_recs],
        "dev_question_ids": sorted(dev_ids),
    }
    path = out_dir / "questions_frozen.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _assemble_manifest(
    config, model_tag, paths, frozen, train_recs, dev_recs,
    leakage_proof, counts, ctx, bank,
) -> dict:
    """Build the provenance manifest (arch doc section 4.8, HANDOFF section 5)."""
    return {
        "component": "WS-2 dataset builders",
        "model_tag": model_tag,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": sha256_file(paths["config"]),
        "abstention_bank_sha256": sha256_file(paths["abstention_bank"]),
        "abstention_bank_size": len(bank),
        "probe_results": str(paths["probe_results"]),
        "cheng_test_gold": str(paths["cheng_test_gold"]),
        "seed": config["seed"],
        "leakage_guard": leakage_proof,
        "budget": {
            "definition": "distinct source questions (frozen K/U set, shared seed)",
            "distinct_questions": len(frozen["known"]) + len(frozen["unknown"]),
            "known_questions": len(frozen["known"]),
            "unknown_questions": len(frozen["unknown"]),
            "train_questions": len(train_recs),
            "dev_questions": len(dev_recs),
            "dev_fraction": config["dev_fraction"],
        },
        "per_arm_row_counts": counts,
        "unknown_negative_source": {
            "strategy": ctx["unknown_negative_strategy"],
            "dropped_no_negative": sorted(set(ctx["dropped_no_negative"])),
            "distractor_substituted": sorted(set(ctx["distractor_substituted"])),
        },
        "kto_correctness_safe_weights": {
            "desirable_weight": config.get("kto", {}).get(
                "correctness_safe_desirable_weight"
            ),
            "undesirable_weight": config.get("kto", {}).get(
                "correctness_safe_undesirable_weight"
            ),
        },
    }


def _write_manifest(out_dir: Path, manifest: dict) -> None:
    path = out_dir / "build_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def _resolve_paths(config: dict, args, repo_root: Path) -> dict:
    """Resolve every input/output path, honoring CLI overrides and {model_tag}."""
    tag = args.model_tag
    inputs = config["inputs"]

    def fill(template: str) -> Path:
        return repo_root / template.format(model_tag=tag)

    probe = Path(args.probe_results) if args.probe_results else fill(
        inputs["probe_results"]
    )
    out = Path(args.output_dir) if args.output_dir else (
        repo_root / config["output_dir"].format(model_tag=tag)
    )
    cheng = Path(args.cheng_test_gold) if args.cheng_test_gold else (
        repo_root / inputs["cheng_test_gold"]
    )
    bank = Path(args.abstention_bank) if args.abstention_bank else (
        repo_root / inputs["abstention_bank"]
    )
    return {
        "probe_results": probe,
        "cheng_test_gold": cheng,
        "abstention_bank": bank,
        "output_dir": out,
        "config": Path(args.config).resolve(),
    }


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 1 dataset builders (WS-2).")
    parser.add_argument("--config", required=True, help="path to build.yaml")
    parser.add_argument("--model-tag", required=True, help="model tag, e.g. qwen3-4b-instruct")
    parser.add_argument("--probe-results", help="override probe_results.jsonl path")
    parser.add_argument("--cheng-test-gold", help="override cheng_test_gold.jsonl path")
    parser.add_argument("--abstention-bank", help="override abstention_bank.json path")
    parser.add_argument("--output-dir", help="override output directory")
    parser.add_argument(
        "--repo-root",
        help="research-repo worktree root (default: inferred from this file)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        # experiment/phase1/data/build_datasets.py -> repo root is 3 parents up.
        repo_root = Path(__file__).resolve().parents[3]
    paths = _resolve_paths(config, args, repo_root)
    try:
        manifest = build_all(config, args.model_tag, paths)
    except (LeakageError, AbstentionBankError, ProbeSchemaError, DevSplitError) as exc:
        print(f"BUILD ABORTED: {exc}", file=sys.stderr)
        return 1
    budget = manifest["budget"]
    print(
        f"Build OK: {budget['distinct_questions']} distinct questions "
        f"({budget['known_questions']} known / {budget['unknown_questions']} "
        f"unknown), leakage guard passed. Outputs in {paths['output_dir']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
