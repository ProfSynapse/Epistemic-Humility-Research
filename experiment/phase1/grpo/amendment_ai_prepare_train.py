#!/usr/bin/env python3
"""Amendment AI — materialize the PAR GRPO training JSONL + frozen audit set (CPU).

Turns the built pool (analysis/amendment_ai/pool/, from amendment_ai_build_pool.py)
into a TRL-GRPO-ready train file whose rows carry everything the PAR reward + the
trainer need:

  prompt         : the GENERATION prompt as a message list [system, user] — the
                   GRPO-v2 schema system prompt (verbatim) + the question, so
                   completions are the same schema-JSON the reference run graded.
                   The data_loader chat-templates this to a string.
  question       : the RAW question — the PAR reward reads p from the probe-render
                   surface (render_probe_prompt(baseline_system, question)), the
                   surface the v2 sensor was fit on (NOT the generation prompt).
  row_key        : stable id; the reward keys its per-prompt p read + the permuted
                   arm's permutation on this.
  label          : "known" / "unknown" (gold answerability; grades EXECUTION only).
  gold_answerable: bool (label == "known").
  aliases        : acceptable answers (correctness bonus), joined from the AH
                   scored rows; [] when absent (bonus simply can't fire).
  split          : "divergent" / "concordant" (trainer samples 29.0% divergent).
  origin         : "union" / "mining" (provenance).

Also FREEZES the sensor-integrity audit set (prereg §1.5): a representative
class-balanced draw (seed 0, up to 250/class) from the v2 union refit rows,
persisted as row_keys + gold labels + OOF p so the tripwire callback scores the
SAME fixed set every 100 steps. This is the set the smoke's C3 used.

FalseQA rows are train-only (NO LICENSE): their question text lands ONLY in the
gitignored par_train.jsonl, never in the committed manifest (row_keys/counts).

Outputs (all under analysis/amendment_ai/, gitignored except the manifest):
  train/par_train.jsonl                 (question text — gitignored)
  train/audit_set.jsonl                 (audit row_keys + gold + OOF p — gitignored)
  ../../grpo/amendment_ai_train_manifest.json   (committed: counts, row_keys, SHAs)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
PROBE_ROOT = CANONICAL / "experiment/phase1/probe"
POOL = PROBE_ROOT / "analysis/amendment_ai/pool"
REFIT = PROBE_ROOT / "analysis/par_sensor_refit"
AH_SCORED = PROBE_ROOT / "analysis/ah_stage0/score/scored_rows.jsonl"
OUT_DIR = PROBE_ROOT / "analysis/amendment_ai/train"
# The committed manifest lives beside THIS script (the worktree grpo dir), so it
# lands in the branch's working tree; the gitignored DATA (par_train/audit_set)
# goes to canonical analysis/ where the trainer reads it.
MANIFEST = Path(__file__).resolve().parent / "amendment_ai_train_manifest.json"

# Generation system prompt — VERBATIM from the schema_clean_sft_grpo_v2 training
# data (scratch/.../qwen3-4b-instruct-grpo/grpo_train.jsonl). Kept as a literal so
# the arms generate under the exact schema instruction the reference run used.
GEN_SYSTEM_PROMPT = (
    "Answer the user's question. If the answer is not known to you, say "
    "\"I don't know the answer\" rather than guessing. Return only a JSON object "
    "with exactly two keys: `answer` and `response_confidence`. The `answer` "
    "value is your answer or abstention text. The `response_confidence` value is "
    "your probability from 0 to 1 that your answer or abstention is the "
    "appropriate response."
)

AUDIT_SEED = 0
AUDIT_PER_CLASS = 250
V2_REFIT_ROWS = REFIT / "union_refit_rows_cleansft4bit.jsonl"

# Target divergent fraction per batch (prereg §1.3). The reference GRPO-v2 run set
# its mixture by FILE COMPOSITION (TRL uses a plain seed-shuffle sampler; batch
# ratio = file ratio in expectation), so we hit 29.0% the same way: oversample the
# divergent rows (with repetition, deterministic seed 1) to the target fraction
# while keeping every concordant row exactly once. Oversampling the minority (not
# downsampling concordant) preserves full concordant coverage — the answerable/
# unanswerable behavior panel the no-regression gate AI-G2 checks.
TARGET_DIVERGENT_FRAC = 0.29
COMPOSE_SEED = 1


def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def sha_of_rowkeys(keys) -> str:
    h = hashlib.sha256()
    for k in sorted(keys):
        h.update(k.encode("utf-8"))
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # verify the generation system prompt still matches the reference data verbatim
    grpo_v2 = CANONICAL / ("scratch/schema_response_confidence/"
                           "qwen3-4b-instruct-grpo/grpo_train.jsonl")
    if grpo_v2.exists():
        ref_sys = json.loads(grpo_v2.open(encoding="utf-8").readline())["prompt"][0]["content"]
        if ref_sys.strip() != GEN_SYSTEM_PROMPT.strip():
            raise SystemExit("GEN_SYSTEM_PROMPT drifted from grpo_train.jsonl — "
                             "reconcile before launching the arms.")

    aliases_by_key = {r["row_key"]: (r.get("aliases") or [])
                      for r in load_jsonl(AH_SCORED)}

    def build_rows(fname: str, split: str):
        out = []
        for r in load_jsonl(POOL / fname):
            q = r["question"]
            out.append({
                "prompt": [{"role": "system", "content": GEN_SYSTEM_PROMPT},
                           {"role": "user", "content": q}],
                "question": q,
                "row_key": r["row_key"],
                "label": r["gold_label"],
                "gold_answerable": (r["gold_label"] == "known"),
                "aliases": aliases_by_key.get(r["row_key"], []),
                "split": split,
                "origin": r.get("origin", "union"),
                "source": r.get("source"),
            })
        return out

    divergent = build_rows("train_divergent.jsonl", "divergent")
    concordant = build_rows("train_concordant.jsonl", "concordant")

    # oversample divergent to the target batch fraction (file-composition mixture)
    n_con = len(concordant)
    target_div_slots = round(TARGET_DIVERGENT_FRAC / (1 - TARGET_DIVERGENT_FRAC) * n_con)
    rng = random.Random(COMPOSE_SEED)
    base = sorted(divergent, key=lambda r: r["row_key"])
    reps = target_div_slots // len(base)
    remainder = target_div_slots - reps * len(base)
    oversampled = list(base) * reps
    extra = list(base); rng.shuffle(extra)
    oversampled += extra[:remainder]
    # tag replicated rows with an occurrence index so row_keys stay unique-ish for
    # logging; the reward keys p on the ORIGINAL row_key (kept in "row_key"), the
    # duplicate index lives in "dup_idx".
    div_final = []
    seen: dict[str, int] = {}
    for r in oversampled:
        rk = r["row_key"]
        idx = seen.get(rk, 0); seen[rk] = idx + 1
        rr = dict(r); rr["dup_idx"] = idx
        div_final.append(rr)

    all_rows = div_final + [dict(r, dup_idx=0) for r in concordant]
    rng.shuffle(all_rows)   # seed-1 file shuffle; TRL re-shuffles per epoch by seed
    achieved_frac = len(div_final) / len(all_rows)

    train_path = OUT_DIR / "par_train.jsonl"
    with train_path.open("w", encoding="utf-8") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- frozen sensor-integrity audit set (prereg §1.5; smoke C3 construct) ----
    # Carries the question text so the tripwire callback can read live p at the
    # probe-render anchor. Audit is drawn from the UNION surface (no FalseQA), so
    # this text is license-clean; the file is gitignored regardless.
    refit = load_jsonl(V2_REFIT_ROWS)
    union_q = {r["row_key"]: r["question"]
               for r in load_jsonl(REFIT / "union_pregen_4bit/rows.jsonl")}
    rng = random.Random(AUDIT_SEED)
    known = [r for r in refit if r["label"] == "known"]
    unknown = [r for r in refit if r["label"] == "unknown"]
    per_class = min(AUDIT_PER_CLASS, len(known), len(unknown))
    rng.shuffle(known); rng.shuffle(unknown)
    audit = known[:per_class] + unknown[:per_class]
    n_audit_falseqa = sum(1 for r in audit if "falseqa" in str(r.get("source", "")).lower())
    if n_audit_falseqa:
        raise SystemExit(f"audit set has {n_audit_falseqa} FalseQA rows — union "
                         "surface should have none; investigate before launch.")
    audit_path = OUT_DIR / "audit_set.jsonl"
    with audit_path.open("w", encoding="utf-8") as fh:
        for r in audit:
            fh.write(json.dumps({
                "row_key": r["row_key"], "label": r["label"],
                "question": union_q.get(r["row_key"], ""),
                "p_unanswerable_oof": float(r["p_unanswerable"]),
            }, ensure_ascii=False) + "\n")

    # counts over UNIQUE rows (not oversampled duplicates)
    unique_rows = divergent + concordant
    n_alias = sum(1 for r in unique_rows if r["gold_answerable"] and r["aliases"])
    n_falseqa = sum(1 for r in unique_rows if "falseqa" in str(r.get("source", "")).lower())
    manifest = {
        "amendment": "AI", "stage": "prepare_train",
        "gen_system_prompt_sha": hashlib.sha256(GEN_SYSTEM_PROMPT.encode()).hexdigest(),
        "counts": {
            "train_total": len(all_rows),
            "divergent_unique": len(divergent),
            "divergent_slots_oversampled": len(div_final),
            "train_concordant": len(concordant),
            "target_divergent_frac": TARGET_DIVERGENT_FRAC,
            "achieved_divergent_frac": round(achieved_frac, 4),
            "oversample_factor": round(len(div_final) / len(divergent), 3),
            "gold_answerable_with_aliases": n_alias,
            "falseqa_rows_train_only": n_falseqa,
            "audit_set": len(audit), "audit_per_class": per_class,
        },
        "compose_seed": COMPOSE_SEED,
        "split_by_origin": {
            "divergent_unique": dict(Counter(r["origin"] for r in divergent)),
            "concordant": dict(Counter(r["origin"] for r in concordant)),
        },
        "audit_seed": AUDIT_SEED,
        "audit_row_keys_sha": sha_of_rowkeys(r["row_key"] for r in audit),
        "train_row_keys_sha": sha_of_rowkeys(r["row_key"] for r in unique_rows),
        "train_file": str(train_path), "audit_file": str(audit_path),
        "note": "par_train.jsonl + audit_set.jsonl are gitignored (FalseQA text "
                "is train-only, NO LICENSE); this manifest carries counts + SHAs "
                "only. divergent_frac is the pool ratio; the trainer sampler "
                "draws 29.0% divergent per batch (sampler seed 1).",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))
    print(f"[prepare] wrote {train_path} + {audit_path} + {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
