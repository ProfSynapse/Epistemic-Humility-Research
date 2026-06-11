#!/usr/bin/env python3
"""Audit of the Reward-Calibration (PPO-M/CRM) released training data.

Input (preferred): full auto-converted parquet shards fetched from the HF
datasets-server, stored at <repo>/scratch/rewardcal-fetch/:
  calib_pref.parquet  (25,524 rows; HINT-lab/calibration_preference_mixture_final-v0.1)
  prompts.parquet     (20,480 rows; HINT-lab/prompt-collections-final-v0.3)
Fallback: stratified samples in datasets/reward-calibration/
  (calibration_preference_mixture.sample2400.jsonl, head-200 per dataset_name;
   prompt_collections.sample.jsonl, head-170 per dataset). The output files
  record which source was used.

Schema (calibration_preference_mixture): per row, `chosen` / `rejected` are
[user, assistant] message lists; `dataset_name` names one of 12 source
mixtures; `chosen_high` / `chosen_low` / `rejected_high` / `rejected_low` are
the same conversations with (a) a confidence-elicitation system prompt
prepended and (b) a verbalized confidence statement appended to the assistant
message. This is the CRM (calibrated reward model) training set from
"Taming Overconfidence in LLMs: Reward Calibration in RLHF"
(arXiv 2410.09724); the RM is trained so reward(chosen_high) >
reward(chosen_low) and reward(rejected_low) > reward(rejected_high).

Analyses:
  R1 (KTO recipe + dataset stats -> experiment/protocol/rewardcal-kto-recipe.md):
     exact CRM -> KTO binary-label mapping ({chosen_high, rejected_low} ->
     desirable, {chosen_low, rejected_high} -> undesirable), row counts per
     source mixture, confidence-phrase template inventory (extracted from all
     rows by diffing each variant against its base response, digits
     normalized), confidence-value distributions, response length stats,
     desirable/undesirable balance under the mapping and under a
     correctness-safe alternative, KTO-format example records, interleaving
     requirement, prompt-collections structure check.
  R3 (contamination audit -> meta-analysis/evidence/rewardcal-contamination-audit.md):
     regex-only inventory of pre-existing verbalized confidence / hedging
     INSIDE the base chosen/rejected assistant responses (before
     augmentation), strong and weak tiers, per source mixture and overall,
     verbatim example hits, and the double-stacking rate (augmented variant =
     pre-existing hedging + appended confidence phrase).

Output (deterministic, recomputable; this script is the provenance):
  experiment/protocol/rewardcal-kto-recipe.md
  meta-analysis/evidence/rewardcal-contamination-audit.md
  meta-analysis/analysis/figures/rewardcal_contamination.png

Run: python3 rewardcal_audit.py
"""

import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent          # meta-analysis/analysis
EH = HERE.parent.parent                          # repo root (project root)
REPO = HERE.parents[1]                           # repo root
OUT_R1 = EH / "experiment" / "protocol" / "rewardcal-kto-recipe.md"
OUT_R3 = HERE.parent / "evidence" / "rewardcal-contamination-audit.md"
FIGDIR = HERE / "figures"

# Candidate locations for the full parquets (repo scratch is where the
# 2026-06-10 fetch landed; the epistemic-humility-local path is checked too).
PARQUET_DIRS = [
    REPO / "scratch" / "rewardcal-fetch",
    EH / "scratch" / "rewardcal-fetch",
]
SAMPLE_DIR = EH / "datasets" / "reward-calibration"

VARIANTS = ("chosen_high", "chosen_low", "rejected_high", "rejected_low")
BASE_OF = {
    "chosen_high": "chosen", "chosen_low": "chosen",
    "rejected_high": "rejected", "rejected_low": "rejected",
}
# CRM -> KTO mapping: confidence congruent with correctness = desirable.
KTO_LABEL = {
    "chosen_high": True,    # correct response + high confidence
    "rejected_low": True,   # wrong response + low confidence
    "chosen_low": False,    # correct response + low confidence
    "rejected_high": False, # wrong response + high confidence
}

# ---------------- R3 regex inventory ----------------
# Regex-only detection of verbalized confidence / hedging. All patterns are
# applied case-insensitively to the final assistant message of the BASE
# chosen/rejected conversations (pre-augmentation). Strong tier targets
# explicit self-referential confidence or knowledge disclaimers; weak tier
# targets generic hedging words that also occur in ordinary prose, so the
# weak tier is an overcount of calibration-relevant hedging by construction.
STRONG_PATTERNS = {
    "self_confidence": re.compile(
        r"\bI(?:'m| am)\s+(?:not\s+)?(?:very\s+|quite\s+|fairly\s+|pretty\s+"
        r"|absolutely\s+|completely\s+|entirely\s+|100%\s+)?"
        r"(?:sure|confident|certain)\b", re.I),
    "self_unsure": re.compile(r"\bI(?:'m| am)\s+un(?:sure|certain)\b", re.I),
    "confidence_keyword": re.compile(
        r"\bconfidence(?:\s*:|\s+level|\s+score|\s+rating)", re.I),
    "dont_know": re.compile(
        r"\bI\s+(?:don't|do\s+not|cannot|can't)\s+"
        r"(?:know|say|tell|be\s+(?:sure|certain))\b", re.I),
    "numeric_confidence": re.compile(
        r"(?:confiden\w*|certain\w*|\bsure\b)\W{0,40}\d{1,3}\s*%"
        r"|\d{1,3}\s*%\W{0,40}(?:confiden\w*|certain\w*|\bsure\b)", re.I),
}
WEAK_PATTERNS = {
    "think_believe": re.compile(r"\bI\s+(?:think|believe|guess|suppose)\b", re.I),
    "probability_adverbs": re.compile(
        r"\b(?:probably|likely|maybe|perhaps|possibly)\b", re.I),
    "seems_might": re.compile(
        r"\b(?:it\s+seems|appears\s+to|might\s+be|could\s+be)\b", re.I),
}
# Direct collision with the augmentation template ("Confidence: <N>"):
CONF_COLON = re.compile(r"\bconfidence\s*:", re.I)
# Trailing verbalized-confidence statement already ending the base response
# (UltraFeedback legacy style, e.g. "... Confidence: 95%"):
CONF_TRAILING = re.compile(r"confidence\s*:\s*\d{1,3}\s*%?\s*\.?\s*$", re.I)

CONF_SUFFIX = re.compile(r"\nConfidence:\s*(\d+(?:\.\d+)?)\.?\s*$")


def _guard_sample_fallback(missing: str) -> None:
    """The committed evidence doc's percentages come from the FULL parquets
    (scratch/rewardcal-fetch/, not committed). Falling back to the stratified
    sample silently changes every percentage, so it must be opted into."""
    import os
    if os.environ.get("REWARDCAL_ALLOW_SAMPLE") != "1":
        raise SystemExit(
            f"{missing} not found in {[str(d) for d in PARQUET_DIRS]}. "
            "Refusing to fall back to the 2,400-row sample (it changes the "
            "audit percentages). Re-fetch the parquets, or set "
            "REWARDCAL_ALLOW_SAMPLE=1 to run on the sample anyway."
        )


def load_pref():
    """Return (records, source_desc, is_full). Records: list of dicts with
    message lists as list[{'role','content'}]."""
    for d in PARQUET_DIRS:
        pq = d / "calib_pref.parquet"
        if pq.exists():
            import pandas as pd
            df = pd.read_parquet(pq)
            recs = df.to_dict("records")
            for r in recs:  # numpy arrays -> lists of plain dicts
                for k in ("chosen", "rejected") + VARIANTS:
                    r[k] = [dict(m) for m in r[k]]
            return recs, f"FULL parquet ({pq.relative_to(REPO)}, {len(recs)} rows)", True
    _guard_sample_fallback("calib_pref.parquet")
    sample = SAMPLE_DIR / "calibration_preference_mixture.sample2400.jsonl"
    recs = [json.loads(line) for line in sample.open()]
    return recs, f"stratified SAMPLE ({sample.name}, {len(recs)} rows of 25,524)", False


def load_prompts():
    for d in PARQUET_DIRS:
        pq = d / "prompts.parquet"
        if pq.exists():
            import pandas as pd
            df = pd.read_parquet(pq)
            recs = df.to_dict("records")
            for r in recs:
                for k in ("prompt", "confidence_prompt"):
                    r[k] = [dict(m) for m in r[k]]
            return recs, f"FULL parquet ({pq.relative_to(REPO)}, {len(recs)} rows)", True
    _guard_sample_fallback("prompts.parquet")
    sample = SAMPLE_DIR / "prompt_collections.sample.jsonl"
    recs = [json.loads(line) for line in sample.open()]
    return recs, f"stratified SAMPLE ({sample.name}, {len(recs)} rows of 20,480)", False


def last_assistant(msgs):
    for m in reversed(msgs):
        if m["role"] == "assistant":
            return m["content"]
    raise ValueError("no assistant message")


def lenstats(vals):
    s = sorted(vals)
    n = len(s)
    return {
        "mean": sum(s) / n,
        "median": statistics.median(s),
        "p10": s[int(0.10 * (n - 1))],
        "p90": s[int(0.90 * (n - 1))],
    }


def pct(k, n):
    return f"{100.0 * k / n:.1f}%" if n else "n/a"


def main() -> None:
    recs, src_desc, is_full = load_pref()
    n = len(recs)
    mixes = sorted({r["dataset_name"] for r in recs})
    mix_counts = {m: 0 for m in mixes}
    for r in recs:
        mix_counts[r["dataset_name"]] += 1

    # ---------- template inventory + value distributions (all rows) ----------
    sys_prompts = {}
    suffix_templates = {}
    conf_values = {v: {} for v in VARIANTS}
    anomalies = 0  # variant assistant text not equal to base + suffix
    for r in recs:
        sp = r["chosen_high"][0]["content"] if r["chosen_high"][0]["role"] == "system" else None
        sys_prompts[sp] = sys_prompts.get(sp, 0) + 1
        for v in VARIANTS:
            base = last_assistant(r[BASE_OF[v]])
            var = last_assistant(r[v])
            if not var.startswith(base):
                anomalies += 1
                continue
            suff = var[len(base):]
            tpl = re.sub(r"\d+(?:\.\d+)?", "{N}", suff)
            suffix_templates[tpl] = suffix_templates.get(tpl, 0) + 1
            m = CONF_SUFFIX.search(var)
            val = m.group(1) if m else "NOMATCH"
            conf_values[v][val] = conf_values[v].get(val, 0) + 1

    # ---------- response length stats ----------
    lens = {}
    for field in ("chosen", "rejected") + VARIANTS:
        chars = [len(last_assistant(r[field])) for r in recs]
        words = [len(last_assistant(r[field]).split()) for r in recs]
        lens[field] = (lenstats(chars), lenstats(words))

    # ---------- R3 contamination scan on BASE responses ----------
    # hits[mix][side][tier] = count of responses with >= 1 match in that tier
    hits = {m: {"chosen": {"strong": 0, "weak": 0}, "rejected": {"strong": 0, "weak": 0}}
            for m in mixes}
    pattern_hits = {name: 0 for name in list(STRONG_PATTERNS) + list(WEAK_PATTERNS)}
    conf_colon_hits = {"chosen": 0, "rejected": 0}
    trailing_hits = {"chosen": 0, "rejected": 0}        # overall
    trailing_by_mix = {m: 0 for m in mixes}             # chosen + rejected pooled
    trailing_example = None
    examples = {"strong": [], "weak": []}
    strong_rows = {"chosen": set(), "rejected": set()}  # row idx, for double-stack
    for i, r in enumerate(recs):
        for side in ("chosen", "rejected"):
            text = last_assistant(r[side])
            strong_names = [nm for nm, p in STRONG_PATTERNS.items() if p.search(text)]
            weak_names = [nm for nm, p in WEAK_PATTERNS.items() if p.search(text)]
            for nm in strong_names + weak_names:
                pattern_hits[nm] += 1
            if strong_names:
                hits[r["dataset_name"]][side]["strong"] += 1
                strong_rows[side].add(i)
            if weak_names:
                hits[r["dataset_name"]][side]["weak"] += 1
            if CONF_COLON.search(text):
                conf_colon_hits[side] += 1
            if CONF_TRAILING.search(text):
                trailing_hits[side] += 1
                trailing_by_mix[r["dataset_name"]] += 1
                if trailing_example is None:
                    trailing_example = (r["dataset_name"], side,
                                        text[-160:].replace("\n", " "))
            for tier, names in (("strong", strong_names), ("weak", weak_names)):
                if names and len(examples[tier]) < 3:
                    m = (STRONG_PATTERNS if tier == "strong" else WEAK_PATTERNS)[names[0]].search(text)
                    start = max(0, m.start() - 60)
                    snip = text[start:start + 200].replace("\n", " ")
                    examples[tier].append(
                        (r["dataset_name"], side, names[0], snip))

    # Double-stacking: every variant is base + "\nConfidence: N."; a variant
    # double-stacks iff its base response already strong-matches.
    n_var = 4 * n
    double_stack = 2 * (len(strong_rows["chosen"]) + len(strong_rows["rejected"]))

    # ---------- prompt-collections check ----------
    precs, psrc_desc, p_is_full = load_prompts()
    pn = len(precs)
    pmix = {}
    p_sys = {}
    p_with_sys = 0
    p_identical = 0
    p_mod_with_sys = 0
    p_mod_total = 0
    for r in precs:
        pmix[r["dataset"]] = pmix.get(r["dataset"], 0) + 1
        sysmsgs = [m["content"] for m in r["confidence_prompt"] if m["role"] == "system"]
        nonsys = [m["content"] for m in r["confidence_prompt"] if m["role"] != "system"]
        basemsgs = [m["content"] for m in r["prompt"]]
        for s in sysmsgs:
            p_sys[s] = p_sys.get(s, 0) + 1
        if sysmsgs:
            p_with_sys += 1
        if nonsys == basemsgs:
            p_identical += 1
        if r["modified"]:
            p_mod_total += 1
            if sysmsgs:
                p_mod_with_sys += 1

    # ---------- example KTO records (shortest simple_math row) ----------
    sm = [(i, len(last_assistant(r["chosen_high"])))
          for i, r in enumerate(recs) if r["dataset_name"] == "simple_math"]
    ex_idx = min(sm, key=lambda t: (t[1], t[0]))[0] if sm else 0
    ex_row = recs[ex_idx]

    def kto_record(variant):
        msgs = [{"role": m["role"], "content": m["content"]} for m in ex_row[variant]]
        return {"conversations": msgs, "label": KTO_LABEL[variant]}

    def render_jsonl(rec, limit=600):
        s = json.dumps(rec, ensure_ascii=False)
        out = []
        for m in rec["conversations"]:
            c = m["content"]
            if len(c) > limit:
                m = dict(m, content=c[:limit] + " ...[truncated for display]")
            out.append(m)
        return json.dumps({"conversations": out, "label": rec["label"]}, ensure_ascii=False)

    ex_true = render_jsonl(kto_record("chosen_high"))
    ex_false = render_jsonl(kto_record("rejected_high"))

    # ================= R1 markdown =================
    full_counts_note = ("Counts below are the full-dataset counts." if is_full else
                        "Counts below are SAMPLE counts (head-200 per mixture); "
                        "full-mixture counts are in datasets/reward-calibration/dataset.md.")
    r1 = [
        "# Reward-Calibration (CRM) to KTO recipe (auto-generated by meta-analysis/analysis/rewardcal_audit.py)",
        "",
        "Source data: HINT-lab/calibration_preference_mixture_final-v0.1 (CRM",
        "training mixture for arXiv 2410.09724, \"Taming Overconfidence in LLMs:",
        "Reward Calibration in RLHF\") and HINT-lab/prompt-collections-final-v0.3.",
        f"Loaded preference mixture from: {src_desc}.",
        f"Loaded prompt collections from: {psrc_desc}.",
        "",
        "Purpose: paper-2 protocol input. KTO needs binary desirable/undesirable",
        "labels, not preference pairs; this documents the exact relabeling of the",
        "CRM confidence-augmented variants into KTO labels, the dataset's actual",
        "construction, and the stats needed to configure training.",
        "",
        "## 1. The CRM construction (verified on the data)",
        "",
        "Every row holds one prompt with a correct-ish (`chosen`) and a wrong-ish",
        "(`rejected`) response, both single-turn [user, assistant]. The four",
        "variant fields are mechanical augmentations of those two conversations:",
        "",
        "1. a confidence-elicitation system prompt is prepended, and",
        "2. a verbalized confidence statement is appended to the assistant turn.",
        "",
        f"- Distinct system prompts across all {n} rows: {len(sys_prompts)}"
        f" (every row uses the identical prompt; full text in section 3).",
        f"- Distinct appended suffix templates across all {n} rows x 4 variants",
        f"  (digits normalized to {{N}}): {len(suffix_templates)}.",
        f"- Rows where a variant is NOT exactly base-response + suffix: {anomalies}.",
        "",
        "| suffix template (repr) | count |",
        "|---|---|",
    ]
    for tpl, c in sorted(suffix_templates.items(), key=lambda kv: -kv[1]):
        r1.append(f"| `{tpl!r}` | {c} |")
    r1 += [
        "",
        "Confidence values are integers, uniform over a high band and a low band:",
        "",
        "| variant | value counts |",
        "|---|---|",
    ]
    for v in VARIANTS:
        dist = ", ".join(f"{k}: {c}" for k, c in
                         sorted(conf_values[v].items(),
                                key=lambda kv: float(kv[0]) if kv[0] != "NOMATCH" else -1))
        r1.append(f"| {v} | {dist} |")
    r1 += [
        "",
        "So the entire confidence signal is one template, `\\nConfidence: {N}.`,",
        "with N drawn uniformly from {7, 8, 9, 10} for *_high and {0, 1, 2, 3}",
        "for *_low. There is no paraphrase diversity in the augmentation; any",
        "style diversity in hedging comes from the base responses themselves",
        "(quantified in meta-analysis/evidence/rewardcal-contamination-audit.md).",
        "",
        "## 2. Row counts per source mixture",
        "",
        full_counts_note,
        "",
        "| dataset_name | rows | KTO records after mapping (x4) |",
        "|---|---|---|",
    ]
    for m in sorted(mix_counts, key=lambda k: -mix_counts[k]):
        r1.append(f"| {m} | {mix_counts[m]} | {4 * mix_counts[m]} |")
    r1 += [
        f"| **total** | **{n}** | **{4 * n}** |",
        "",
        "Prompt collections (PPO rollout prompts, not needed for KTO but part of",
        "the released recipe):",
        "",
        "| dataset | rows |",
        "|---|---|",
    ]
    for m in sorted(pmix, key=lambda k: -pmix[k]):
        r1.append(f"| {m} | {pmix[m]} |")
    r1 += [
        f"| **total** | **{pn}** |",
        "",
        f"Structure check: {p_identical}/{pn} confidence_prompt message lists are",
        "the base prompt with at most a system prompt prepended; the",
        f"confidence-elicitation system prompt appears in {p_with_sys}/{pn} rows,",
        f"exactly the `modified == True` rows ({p_mod_with_sys}/{p_mod_total}),",
        f"using {len(p_sys)} distinct system prompt(s) (same text as section 3).",
        "The remaining rows are unmodified prompts, matching the paper's mixed",
        "PPO rollout design (confidence elicited on a subset of rollouts).",
        "",
        "## 3. The confidence-elicitation system prompt (verbatim)",
        "",
        # 4-backtick fence: the prompt text itself contains ``` sequences.
        "````",
        next(iter(sys_prompts)),
        "````",
        "",
        "## 4. Exact CRM -> KTO mapping",
        "",
        "CRM trains reward(chosen_high) > reward(chosen_low) and",
        "reward(rejected_low) > reward(rejected_high): confidence congruent with",
        "correctness should score higher. The binary relabeling for KTO is:",
        "",
        "| variant | content | confidence | congruent? | KTO label |",
        "|---|---|---|---|---|",
        "| chosen_high | correct response | high (7-10) | yes | **true** (desirable) |",
        "| rejected_low | wrong response | low (0-3) | yes | **true** (desirable) |",
        "| chosen_low | correct response | low (0-3) | no | **false** (undesirable) |",
        "| rejected_high | wrong response | high (7-10) | no | **false** (undesirable) |",
        "",
        f"Balance: {2 * n} desirable / {2 * n} undesirable (exactly 50/50; every",
        "row contributes 2 of each). Per-mixture balance is also exactly 50/50",
        "by construction.",
        "",
        "### Design tensions to resolve in the protocol",
        "",
        "1. **label=true on wrong content (rejected_low).** KTO raises the",
        "   likelihood of the whole completion, not just the confidence token.",
        "   Labeling rejected_low desirable rewards generating the wrong answer",
        "   (with low confidence), not only the calibrated hedge. A",
        "   correctness-safe alternative drops rejected_low from the desirable",
        "   set: {chosen_high} -> true, {chosen_low, rejected_high} -> false,",
        f"   giving {n} true / {2 * n} false (1:2). KTO handles imbalance via",
        "   `desirable_weight` / `undesirable_weight` (set desirable_weight ~ 2x).",
        "   Decision: run the congruence mapping as primary (it is the faithful",
        "   CRM transplant) and the correctness-safe mapping as an ablation arm.",
        "2. **Near-duplicate completions.** For a given row, chosen_high and",
        "   chosen_low differ ONLY in the final confidence integer (likewise",
        "   rejected_high/rejected_low). The desirable/undesirable contrast is",
        "   therefore carried almost entirely by 1-2 tokens. That is precisely",
        "   the calibration signal, but it means each prompt appears 4 times in",
        "   the KTO set with two distinct response bodies. Keep all 4 per row",
        "   (the contrast needs both sides); do not deduplicate by prompt.",
        "3. **System prompt dependence.** All augmented variants carry the same",
        "   confidence-elicitation system prompt. A model trained only on these",
        "   may only verbalize confidence when that exact system prompt is",
        "   present. If generalization without the prompt is wanted, add a",
        "   no-system-prompt variant arm or paraphrase the elicitation prompt.",
        "4. **Single-template confidence.** `Confidence: {N}.` (0-10 integer) is",
        "   the only phrasing. Evaluation should elicit the same format;",
        "   transfer to free-form hedging is an open question the contamination",
        "   audit speaks to.",
        "",
        "## 5. KTO record shape and example records",
        "",
        "Trainer format per .skills/fine-tuning/reference/dataset-formats.md",
        "(conversations + boolean label, one JSON object per line):",
        "",
        "```jsonl",
        '{"conversations":[{"role":"user","content":"..."},{"role":"assistant","content":"good response"}],"label":true}',
        '{"conversations":[{"role":"user","content":"..."},{"role":"assistant","content":"bad response"}],"label":false}',
        "```",
        "",
        f"Example records built from the shortest simple_math row (row index {ex_idx}",
        "in load order; long content truncated for display only, marked inline):",
        "",
        "Desirable (chosen_high -> label true):",
        "",
        "```json",
        ex_true,
        "```",
        "",
        "Undesirable (rejected_high -> label false):",
        "",
        "```json",
        ex_false,
        "```",
        "",
        "## 6. Interleaving requirement",
        "",
        "Per KTO_TRAINING_REFERENCE.md and the existing stager, the KTO JSONL",
        "must alternate true/false examples (the stager interleaves with",
        "zip_longest). With the 50/50 congruence mapping, emit",
        "true,false,true,false,... by pairing each row's (chosen_high,",
        "chosen_low) and (rejected_low, rejected_high) in a fixed order. With",
        "the 1:2 correctness-safe mapping, zip_longest still applies; the tail",
        "will be all-false, so shuffle rows (fixed seed) before interleaving.",
        "",
        "## 7. Response length stats (final assistant message)",
        "",
        "Variants are base + ~16 chars of suffix, so base and variant stats",
        "nearly coincide; both reported for completeness.",
        "",
        "| field | chars mean / median / p10 / p90 | words mean / median / p10 / p90 |",
        "|---|---|---|",
    ]
    for field in ("chosen", "rejected") + VARIANTS:
        c, w = lens[field]
        r1.append(
            f"| {field} | {c['mean']:.0f} / {c['median']:.0f} / {c['p10']:.0f} / {c['p90']:.0f} "
            f"| {w['mean']:.0f} / {w['median']:.0f} / {w['p10']:.0f} / {w['p90']:.0f} |")
    r1 += [
        "",
        "Note for Qwen2.5-3B/7B training configs: p90 chosen length is",
        f"{lens['chosen'][1]['p90']:.0f} words ({lens['chosen'][0]['p90']:.0f} chars); with the system prompt",
        "(~90 words) and user prompt on top, a 2048-token max_seq_length covers",
        "the large majority of records; verify against the tokenizer before",
        "committing (word counts here are whitespace splits, not tokens).",
        "",
        "## Limitations",
        "",
        "- License: the HF datasets carry no license tag (repo is Apache-2.0);",
        "  verify before redistributing any derived KTO file.",
        "- `chosen`/`rejected` quality is inherited from 12 heterogeneous",
        "  preference sources; `chosen` is not verified-correct in general",
        "  (only preferred), so \"correct/wrong\" above is shorthand for",
        "  preferred/dispreferred.",
        "- Word counts are whitespace splits, not tokenizer tokens.",
    ]
    if not is_full:
        r1.append("- Computed on the stratified sample, not the full mixture; "
                  "per-mixture stats are head-of-file rows, not random samples.")
    r1.append("")

    OUT_R1.parent.mkdir(parents=True, exist_ok=True)
    OUT_R1.write_text("\n".join(r1))
    print(f"wrote {OUT_R1.relative_to(EH)}")

    # ================= R3 markdown =================
    tot = {"chosen": {"strong": 0, "weak": 0}, "rejected": {"strong": 0, "weak": 0}}
    for m in mixes:
        for side in ("chosen", "rejected"):
            for tier in ("strong", "weak"):
                tot[side][tier] += hits[m][side][tier]

    r3 = [
        "# Reward-Calibration contamination audit (auto-generated by analysis/rewardcal_audit.py)",
        "",
        "Question: how much verbalized confidence / hedging already sits INSIDE",
        "the base `chosen`/`rejected` responses of",
        "HINT-lab/calibration_preference_mixture_final-v0.1, BEFORE the CRM",
        "confidence augmentation? Pre-existing hedging conflates style with the",
        "calibration signal: a reward model (or KTO policy) trained on the",
        "augmented variants can pick up on incidental hedging phrases rather",
        "than the appended `Confidence: {N}.` statement, and augmented variants",
        "that already hedge carry two confidence signals that may disagree.",
        "",
        f"Data: {src_desc}. Unit of analysis: the final assistant message of the",
        "base `chosen` and `rejected` conversations (all rows are single-turn).",
        "Detection is REGEX-ONLY (no LLM judge): exact patterns below, applied",
        "case-insensitively; a response counts as a hit if any pattern in the",
        "tier matches at least once.",
        "",
        "## Regex inventory",
        "",
        "Strong tier (explicit self-referential confidence or knowledge",
        "disclaimers):",
        "",
        "| name | pattern |",
        "|---|---|",
    ]
    for nm, p in STRONG_PATTERNS.items():
        r3.append(f"| {nm} | `{p.pattern}` |")
    r3 += [
        "",
        "Weak tier (generic hedging words; heavy overcount of",
        "calibration-relevant hedging since these occur in ordinary prose):",
        "",
        "| name | pattern |",
        "|---|---|",
    ]
    for nm, p in WEAK_PATTERNS.items():
        r3.append(f"| {nm} | `{p.pattern}` |")
    r3 += [
        "",
        "## Contamination rates",
        "",
        "Overall (share of responses with at least one match):",
        "",
        "| side | n | strong tier | weak tier |",
        "|---|---|---|---|",
        f"| chosen | {n} | {tot['chosen']['strong']} ({pct(tot['chosen']['strong'], n)}) "
        f"| {tot['chosen']['weak']} ({pct(tot['chosen']['weak'], n)}) |",
        f"| rejected | {n} | {tot['rejected']['strong']} ({pct(tot['rejected']['strong'], n)}) "
        f"| {tot['rejected']['weak']} ({pct(tot['rejected']['weak'], n)}) |",
        "",
        "Per source mixture:",
        "",
        "| dataset_name | n | chosen strong | chosen weak | rejected strong | rejected weak |",
        "|---|---|---|---|---|---|",
    ]
    for m in sorted(mix_counts, key=lambda k: -mix_counts[k]):
        c = mix_counts[m]
        h = hits[m]
        r3.append(
            f"| {m} | {c} | {pct(h['chosen']['strong'], c)} | {pct(h['chosen']['weak'], c)} "
            f"| {pct(h['rejected']['strong'], c)} | {pct(h['rejected']['weak'], c)} |")
    r3 += [
        "",
        "Per-pattern hit counts (responses, chosen + rejected pooled, a response",
        "can hit several patterns):",
        "",
        "| pattern | tier | responses hit |",
        "|---|---|---|",
    ]
    for nm in STRONG_PATTERNS:
        r3.append(f"| {nm} | strong | {pattern_hits[nm]} |")
    for nm in WEAK_PATTERNS:
        r3.append(f"| {nm} | weak | {pattern_hits[nm]} |")
    r3 += [
        "",
        "## Example hits (verbatim, truncated to 200 chars)",
        "",
    ]
    for tier in ("strong", "weak"):
        r3.append(f"### {tier} tier")
        r3.append("")
        for mx, side, nm, snip in examples[tier]:
            r3.append(f"- [{mx} / {side} / {nm}] `{snip}`")
        r3.append("")
    r3 += [
        "## Double-stacking in the augmented variants",
        "",
        "Verified mechanically: every one of the 4 variant responses equals its",
        "base response plus the single suffix template `\\nConfidence: {N}.`",
        f"({anomalies} exceptions out of {4 * n}). Therefore an augmented variant",
        "double-stacks (pre-existing hedging AND appended confidence statement",
        "in the same response) exactly when its base response strong-matches:",
        "",
        f"- Variant records double-stacked (strong tier): {double_stack} of {n_var}"
        f" ({pct(double_stack, n_var)}).",
        f"- Base responses already containing the literal token `confidence:`",
        f"  (direct format collision with the appended statement): chosen",
        f"  {conf_colon_hits['chosen']} ({pct(conf_colon_hits['chosen'], n)}), rejected"
        f" {conf_colon_hits['rejected']} ({pct(conf_colon_hits['rejected'], n)}).",
        "",
        "The sharpest case: base responses that already END with a verbalized",
        "confidence statement (regex `confidence\\s*:\\s*\\d{1,3}\\s*%?\\s*\\.?\\s*$`,",
        "a legacy of UltraFeedback's own generation prompt, typically",
        "`Confidence: 95%`):",
        "",
        f"- chosen: {trailing_hits['chosen']} ({pct(trailing_hits['chosen'], n)});"
        f" rejected: {trailing_hits['rejected']} ({pct(trailing_hits['rejected'], n)}).",
        "- By mixture (chosen + rejected pooled): "
        + ", ".join(f"{m}: {trailing_by_mix[m]}"
                    for m in sorted(trailing_by_mix, key=lambda k: -trailing_by_mix[k])
                    if trailing_by_mix[m]) + ".",
        (f"- Example tail [{trailing_example[0]} / {trailing_example[1]}]: "
         f"`{trailing_example[2]}`" if trailing_example else "- No example found."),
        "",
        "For such a row, the augmented chosen_low variant reads",
        "`... Confidence: 95%\\nConfidence: 2.` Two contradictory confidence",
        "statements in one desirable-or-undesirable completion: the cleanest",
        "demonstration that augmentation was applied without screening the base",
        "responses for pre-existing confidence statements.",
        "",
        "A double-stacked chosen_low or rejected_low can be internally",
        "contradictory (confident prose + appended `Confidence: 1.`), and a",
        "double-stacked record gives the trained model two confidence cues of",
        "which only one is controlled by the label.",
        "",
        "## Caveats",
        "",
        "- Regex-only, no judge. The strong tier UNDERCOUNTS (misses",
        "  paraphrases such as \"my best guess\", \"take this with a grain of",
        "  salt\", hedging without first-person markers) and OVERCOUNTS in",
        "  places (e.g. `confidence score` inside ML/code discussion text, or",
        "  quoted/role-played speech). The weak tier badly OVERCOUNTS:",
        "  probably/likely/maybe are ordinary prose and most weak hits are not",
        "  calibration statements. Treat strong as a floor-ish estimate with",
        "  noise and weak as a loose upper bound on hedging-adjacent style.",
        "- Matches are detected anywhere in the response, not only in",
        "  conclusion position where a calibration statement would sit.",
        "- Single-pattern attribution in the examples lists the first matching",
        "  pattern only.",
    ]
    if not is_full:
        r3.append("- Computed on the stratified sample (head rows per mixture), "
                  "not the full 25,524-row mixture.")
    r3.append("")

    OUT_R3.parent.mkdir(parents=True, exist_ok=True)
    OUT_R3.write_text("\n".join(r3))
    print(f"wrote {OUT_R3.relative_to(EH)}")

    # ================= figure =================
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGDIR.mkdir(parents=True, exist_ok=True)
    order = sorted(mix_counts, key=lambda k: -mix_counts[k])
    xs = range(len(order))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=False)
    for ax, tier in zip(axes, ("strong", "weak")):
        ch = [100.0 * hits[m]["chosen"][tier] / mix_counts[m] for m in order]
        rj = [100.0 * hits[m]["rejected"][tier] / mix_counts[m] for m in order]
        w = 0.38
        ax.bar([x - w / 2 for x in xs], ch, w, color="#2a7", label="chosen")
        ax.bar([x + w / 2 for x in xs], rj, w, color="#c66", label="rejected")
        ax.set_xticks(list(xs))
        ax.set_xticklabels(order, rotation=60, ha="right", fontsize=7)
        ax.set_title(f"{tier} tier")
        ax.set_ylabel("% responses with a hedging/confidence match")
        ax.grid(alpha=0.3, axis="y")
        ax.legend(fontsize=8)
    fig.suptitle(
        "Reward-Calibration base responses: pre-existing verbalized confidence/hedging (regex-only)",
        fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGDIR / "rewardcal_contamination.png", dpi=160)
    plt.close(fig)
    print("wrote figures/rewardcal_contamination.png")


if __name__ == "__main__":
    main()
