#!/usr/bin/env python3
"""Secondary analyses of the FActScore (Min et al., EMNLP 2023) released data.

Input: docs/epistemic-humility/datasets/factscore-data/
  labeled/{InstructGPT,ChatGPT,PerplexityAI}.jsonl
      183 human-annotated bio generations each (549 total). Each record:
      input, output, topic, cat (=[rarity_tier, region]), annotations[]. Each
      annotation has human-atomic-facts[] with label in {S, NS, IR}
      (Supported / Not Supported / Irrelevant). Human labels only; NO automated
      labels are stored here.
  unlabeled/{12 models}.jsonl
      12 LMs x 500 prompts (same 500 entities per model), INCLUDING abstentions.
      Record: input, output, topic, cat.
  unlabeled-predictions/{12 models}.jsonl
      Same 12 LMs, abstentions EXCLUDED (row count 333-500). Record: facts[],
      LLAMA+NP_Labels[] (present on every row), ChatGPT_Labels[] (present on a
      ~20% subset of rows only), prompt. Labels in {S, NS}.

File-name map (unlabeled -> unlabeled-predictions): the prediction files use
lowercased / abbreviated names. "alpaca.jsonl" is Alpaca-65B by elimination
(alpaca-7B.jsonl and alpaca-13B.jsonl cover the other two; all three Alpacas
respond 500/500 per the FActScore paper, consistent with this mapping).

Post-training type (from the meta-analysis brief):
  RLHF      : GPT-4, ChatGPT, InstructGPT
  SFT-only  : Alpaca-7B/13B/65B, Vicuna-7B/13B, MPT-Chat-7B, Dolly-12B
  base/weak : Pythia-12B, Stablelm-alpha-7B

Join key: labeled and unlabeled use DISJOINT entity sets (verified: 0 of 183
labeled topics appear among the 500 unlabeled topics), so the two halves of the
analysis never share a generation. unlabeled-predictions carries no topic/cat
field, only a `prompt` string; it is joined back to unlabeled by a normalized
topic key (strip the "Question: Tell me a bio of " prefix, strip trailing
periods, drop a trailing "(...)" disambiguator, lowercase). With that key every
prediction row maps to exactly one unlabeled row for all 12 models, and the
abstention count derived by the join equals 500 - (prediction rows) exactly
(asserted at runtime); see the SANITY block.

Analyses (claims C1 post-training and calibration, C3 over-refusal operating
points, C4 scale alone):
  F1 Respond-ratio vs factual precision by post-training type. Respond ratio =
     (prediction rows)/500. Precision = fraction of atomic facts labeled S,
     computed separately under LLAMA+NP_Labels (all responding rows) and under
     ChatGPT_Labels (the ~20% subset that carries them). n reported for both.
  F2 Abstention-by-rarity dose-response. Abstention identified by exclusion from
     unlabeled-predictions (the authors' own criterion), cross-checked by a
     documented refusal-text detector. Per (model, rarity tier) abstention rate
     from unlabeled/; per (model, rarity tier) factual error rate (NS share of
     S+NS human-atomic-facts) from labeled/.
  F3 Judge-noise quantification. Per-fact agreement between ChatGPT_Labels and
     LLAMA+NP_Labels on the both-labeled fact subset (overall + per model),
     compared against the prior Cheng-data 43-51% label-noise finding.
     Human-vs-auto agreement is NOT computable here (labeled and prediction
     entity sets are disjoint and labeled carries no auto labels); stated as a
     limitation.

Output (deterministic, recomputable; this script is the provenance):
  meta-analysis/evidence/factscore-reanalysis.md
  meta-analysis/analysis/figures/factscore_respond_precision.png
  meta-analysis/analysis/figures/factscore_rarity.png

Run: python3 factscore_reanalysis.py
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / "datasets" / "factscore-data"
OUT = HERE.parent / "evidence" / "factscore-reanalysis.md"
FIGDIR = HERE / "figures"

# unlabeled file stem -> (prediction file stem, post-training type)
MODELS = [
    ("GPT-4", "gpt4", "RLHF"),
    ("ChatGPT", "ChatGPT", "RLHF"),
    ("InstructGPT", "InstructGPT", "RLHF"),
    ("Alpaca-7B", "alpaca-7B", "SFT-only"),
    ("Alpaca-13B", "alpaca-13B", "SFT-only"),
    ("Alpaca-65B", "alpaca", "SFT-only"),
    ("Vicuna-7B", "vicuna-7b", "SFT-only"),
    ("Vicuna-13B", "vicuna-13b", "SFT-only"),
    ("MPT-Chat-7B", "mpt-7b", "SFT-only"),
    ("Dolly-12B", "dolly-12b", "SFT-only"),
    ("Pythia-12B", "pythia-12b", "base/weak"),
    ("Stablelm-alpha-7B", "stablelm-alpha-7b", "base/weak"),
]
LABELED = ["InstructGPT", "ChatGPT", "PerplexityAI"]
TIERS = ["very rare", "rare", "medium", "freq", "very freq"]
TYPE_STYLE = {  # color, marker for figures
    "RLHF": ("#27b", "o"),
    "SFT-only": ("#d90", "s"),
    "base/weak": ("#888", "^"),
}

# Refusal-text detector (F2 cross-check). Applied to the first 400 chars of the
# generation, case-insensitive. Patterns were tuned against the authors'
# exclusion signal (abstention = excluded from unlabeled-predictions); see the
# F2 section of the report for the measured TP/FN/FP. The exclusion signal, not
# this regex, is the PRIMARY abstention definition.
REFUSAL = re.compile(
    r"(i'?m sorry|i am sorry|i cannot|i can'?t|i could not|i couldn'?t"
    r"|i do not have|i don'?t have|no information"
    r"|not (a )?(widely[- ]known|well[- ]known|notable|prominent)"
    r"|no (prominent|notable|well[- ]known) (figure|person|individual)"
    r"|unable to (find|provide)"
    r"|there (is|isn'?t) (limited|insufficient|no|not much|any|much) .{0,20}information"
    r"|could not find|couldn'?t find|cannot find|as an ai language model"
    r"|i'?m not (familiar|aware)|i am not (familiar|aware)"
    r"|i have no (information|knowledge)|unfortunately,? i"
    r"|difficult to provide|impossible to provide"
    r"|may refer to (different|multiple|several)|relatively unknown|less[- ]known)",
    re.I,
)


def read_jsonl(path):
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def norm_key(text, is_prompt):
    """Normalized topic key used to join predictions back to unlabeled rows."""
    t = text.replace("Question: Tell me a bio of ", "") if is_prompt else text
    t = t.strip().rstrip(".").strip()
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)  # drop trailing "(disambiguator)"
    return t.lower()


def pct(num, den):
    return 100.0 * num / den if den else float("nan")


def p1(x):
    return "n/a" if x != x else f"{x:.1f}"  # x!=x catches NaN


def main():
    # ---------- load prediction files (precision, response ratio, judge labels) ----------
    pred = {}  # unlabeled_name -> dict
    for uname, pname, _ in MODELS:
        rows = list(read_jsonl(DATA / "unlabeled-predictions" / f"{pname}.jsonl"))
        ll_s = ll_n = 0
        cg_s = cg_n = 0
        cg_rows = 0
        agree = both = 0
        for r in rows:
            ll = r.get("LLAMA+NP_Labels") or []
            cg = r.get("ChatGPT_Labels") or []
            for x in ll:
                ll_s += x == "S"
                ll_n += x == "NS"
            if cg:
                cg_rows += 1
                for x in cg:
                    cg_s += x == "S"
                    cg_n += x == "NS"
            if cg and ll and len(cg) == len(ll):
                for a, b in zip(cg, ll):
                    both += 1
                    agree += a == b
        pred[uname] = {
            "rows": len(rows),
            "ll_facts": ll_s + ll_n,
            "ll_prec": pct(ll_s, ll_s + ll_n),
            "cg_rows": cg_rows,
            "cg_facts": cg_s + cg_n,
            "cg_prec": pct(cg_s, cg_s + cg_n),
            "agree": agree,
            "both": both,
            "keys": {norm_key(r["prompt"], True) for r in rows},
        }

    # ---------- load unlabeled (abstention by exclusion + by text, per tier) ----------
    unl = {}  # unlabeled_name -> {"by_tier": {tier: [n, abst_excl, abst_text]}, totals}
    for uname, _, _ in MODELS:
        pkeys = pred[uname]["keys"]
        by_tier = {t: [0, 0, 0] for t in TIERS}  # [n, abst_by_exclusion, abst_by_text]
        n_rows = abst_excl = abst_text = 0
        tp = fn = fp = 0
        unmatched_pred = set(pkeys)
        for r in read_jsonl(DATA / "unlabeled" / f"{uname}.jsonl"):
            n_rows += 1
            tier = (r.get("cat") or ["?"])[0]
            k = norm_key(r["topic"], False)
            unmatched_pred.discard(k)
            excluded = k not in pkeys  # PRIMARY abstention signal
            fired = bool(REFUSAL.search(r["output"][:400]))
            if tier in by_tier:
                by_tier[tier][0] += 1
                by_tier[tier][1] += excluded
                by_tier[tier][2] += fired
            abst_excl += excluded
            abst_text += fired
            tp += excluded and fired
            fn += excluded and not fired
            fp += (not excluded) and fired
        unl[uname] = {
            "n_rows": n_rows,
            "abst_excl": abst_excl,
            "abst_text": abst_text,
            "by_tier": by_tier,
            "tp": tp,
            "fn": fn,
            "fp": fp,
            "unmatched_pred": len(unmatched_pred),
        }

    # ---------- SANITY: abstention by join must equal 500 - prediction rows ----------
    sanity_lines = []
    for uname, _, _ in MODELS:
        by_join = unl[uname]["abst_excl"]
        by_count = unl[uname]["n_rows"] - pred[uname]["rows"]
        ok = by_join == by_count and unl[uname]["unmatched_pred"] == 0
        sanity_lines.append((uname, by_join, by_count, unl[uname]["unmatched_pred"], ok))
        assert ok, (
            f"join sanity failed for {uname}: abst_by_join={by_join}, "
            f"500-pred_rows={by_count}, unmatched_pred_keys={unl[uname]['unmatched_pred']}"
        )

    # ---------- labeled per-tier human factual error rate ----------
    lab = {}  # labeled_name -> {"by_tier": {tier:[S,NS,IR]}, "none_ann": k, "rows": n}
    for m in LABELED:
        by_tier = {t: [0, 0, 0] for t in TIERS}  # [S, NS, IR]
        none_ann = rows = 0
        for r in read_jsonl(DATA / "labeled" / f"{m}.jsonl"):
            rows += 1
            tier = (r.get("cat") or ["?"])[0]
            ann = r.get("annotations")
            if not ann:  # abstention / undecomposable generation: no atomic facts
                none_ann += 1
                continue
            if tier not in by_tier:
                continue
            for a in ann:
                for fct in (a.get("human-atomic-facts") or []):
                    lb = fct.get("label")
                    if lb == "S":
                        by_tier[tier][0] += 1
                    elif lb == "NS":
                        by_tier[tier][1] += 1
                    elif lb == "IR":
                        by_tier[tier][2] += 1
        lab[m] = {"by_tier": by_tier, "none_ann": none_ann, "rows": rows}

    # ===================== write report =====================
    L = []
    L += [
        "# FActScore reanalysis (auto-generated by analysis/factscore_reanalysis.py)",
        "",
        "Source: Min et al. (EMNLP 2023) released data,",
        "datasets/factscore-data/ (labeled/, unlabeled/, unlabeled-predictions/).",
        "labeled/ holds 183 human-annotated bio generations each for InstructGPT,",
        "ChatGPT, PerplexityAI (per-fact human label S/NS/IR). unlabeled/ holds",
        "12 LMs x 500 raw generations including abstentions. unlabeled-predictions/",
        "holds the same 12 LMs with abstentions excluded and per-fact automated",
        "labels: LLAMA+NP_Labels on every row, ChatGPT_Labels on a ~20% subset.",
        "",
        "Post-training type: RLHF (GPT-4, ChatGPT, InstructGPT); SFT-only (Alpaca",
        "7B/13B/65B, Vicuna 7B/13B, MPT-Chat 7B, Dolly 12B); base/weak (Pythia 12B,",
        "Stablelm-alpha 7B). Rates rounded to 1 decimal percent. No pooling across",
        "models except where explicitly labelled an overall total.",
        "",
        "Join: labeled and unlabeled entity sets are disjoint (0 of 183 labeled",
        "topics among the 500 unlabeled topics), so F1/F3 (prediction-based) and the",
        "labeled error-rate half of F2 never share a generation. Predictions are",
        "joined to unlabeled by a normalized topic key (strip prompt prefix and",
        "trailing periods, drop a trailing parenthetical disambiguator, lowercase).",
        "",
        "### Join sanity check (recomputed two ways)",
        "",
        "Abstention count by topic-key join must equal 500 minus the prediction-row",
        "count (predictions exclude abstentions). Asserted at runtime for all 12",
        "models; every prediction key matched exactly one unlabeled row.",
        "",
        "| model | abstain (join) | 500 - pred rows | unmatched pred keys |",
        "|---|---|---|---|",
    ]
    for uname, bj, bc, un, _ in sanity_lines:
        L.append(f"| {uname} | {bj} | {bc} | {un} |")
    L.append("")

    # ---------------- F1 ----------------
    L += [
        "## F1. Respond-ratio vs factual precision, by post-training type (C1/C3/C4)",
        "",
        "Respond ratio = prediction rows / 500. Precision = share of atomic facts",
        "labeled S. LLAMA+NP precision is over every responding row; ChatGPT",
        "precision is over only the ~20% of rows carrying ChatGPT_Labels (n shown).",
        "",
        "| model | type | respond % | LLAMA+NP prec % | LL facts (n) | ChatGPT prec % | CG rows (n) | CG facts (n) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for uname, _, ptype in MODELS:
        d = pred[uname]
        rr = pct(d["rows"], 500)
        L.append(
            f"| {uname} | {ptype} | {p1(rr)} | {p1(d['ll_prec'])} | {d['ll_facts']} "
            f"| {p1(d['cg_prec'])} | {d['cg_rows']} | {d['cg_facts']} |"
        )
    # group means (unweighted across models within type) for orientation only
    def grp(ptype, field, transform=lambda d: d):
        vals = [transform(pred[u])[field] if isinstance(transform(pred[u]), dict) else None
                for u, _, t in MODELS if t == ptype]
        return vals
    L += [
        "",
        "Per-type ranges (min-max across the models in each type; not pooled facts):",
        "",
    ]
    for ptype in ("RLHF", "SFT-only", "base/weak"):
        rrs = [pct(pred[u]["rows"], 500) for u, _, t in MODELS if t == ptype]
        lls = [pred[u]["ll_prec"] for u, _, t in MODELS if t == ptype]
        L.append(
            f"- {ptype}: respond {p1(min(rrs))}-{p1(max(rrs))}%, "
            f"LLAMA+NP precision {p1(min(lls))}-{p1(max(lls))}%"
        )
    L += [
        "",
        "Reading. The two newest RLHF models (GPT-4, ChatGPT) sit at the top-right",
        "operating point: they abstain most among instruction models (respond"
        f" {p1(pct(pred['GPT-4']['rows'],500))}% / {p1(pct(pred['ChatGPT']['rows'],500))}%)"
        " AND carry the highest factual precision",
        f"(LLAMA+NP {p1(pred['GPT-4']['ll_prec'])}% / {p1(pred['ChatGPT']['ll_prec'])}%),"
        " the long-form analog of the abstention",
        "operating point seen in AbstentionBench. InstructGPT is an RLHF outlier:",
        f"it responds {p1(pct(pred['InstructGPT']['rows'],500))}% (essentially never abstains)"
        f" at {p1(pred['InstructGPT']['ll_prec'])}% precision,",
        "so the RLHF label alone does not buy the operating point; the newer RLHF",
        "models do. SFT-only models mostly respond at or near 100% (Alpaca x3,",
        "Dolly all 100.0%) with lower precision, though Vicuna and MPT-Chat abstain",
        "substantially - SFT-only is not a uniform always-answer bloc. The two",
        "base/weak models split the abstention axis from the precision axis:",
        f"Stablelm-alpha abstains the MOST of any model (responds {p1(pct(pred['Stablelm-alpha-7B']['rows'],500))}%)"
        f" yet has the LOWEST",
        f"precision ({p1(pred['Stablelm-alpha-7B']['ll_prec'])}% LLAMA+NP) - abstention volume without"
        " knowledge-aligned selectivity,",
        "whereas Pythia responds 100.0%. So scale/abstention-rate alone does not",
        "produce the humility operating point (C4); the newer RLHF recipe does.",
        "",
        "Note: ChatGPT precision exceeds LLAMA+NP precision for every model (e.g.",
        "ChatGPT-judge gives ChatGPT itself"
        f" {p1(pred['ChatGPT']['cg_prec'])}% vs {p1(pred['ChatGPT']['ll_prec'])}% under LLAMA+NP),"
        " and ChatGPT",
        "judging ChatGPT's own generations is self-judging; see F3 and Limitations.",
        "",
    ]

    # ---------------- F2 ----------------
    L += [
        "## F2. Abstention-by-rarity dose-response (C1/C3/C4)",
        "",
        "Abstention detector (PRIMARY): a generation abstained if its topic key is",
        "absent from that model's unlabeled-predictions file (the authors exclude",
        "abstentions when building predictions). Cross-check (SECONDARY): a",
        "regex refusal-text detector over the first 400 characters of the",
        "generation (pattern in the script header / REFUSAL). Agreement of the text",
        "detector against the exclusion signal, pooled across all 12 models:",
        "",
    ]
    TP = sum(unl[u]["tp"] for u, _, _ in MODELS)
    FN = sum(unl[u]["fn"] for u, _, _ in MODELS)
    FP = sum(unl[u]["fp"] for u, _, _ in MODELS)
    tot_excl = TP + FN
    L += [
        f"- Exclusion-defined abstentions: n = {tot_excl} (of {12*500} generations).",
        f"- Text detector recall vs exclusion: {p1(pct(TP, tot_excl))}% "
        f"(TP {TP}, FN {FN}).",
        f"- Text detector also fired on {FP} responding (non-excluded) generations",
        "  (false positives: bios containing a hedge/apology mid-text). The text",
        "  detector is reported only as a coherence cross-check; the exclusion",
        "  signal is used for all rates below.",
        "",
        "### Abstention rate by rarity tier (from unlabeled/, exclusion signal)",
        "",
        "Each cell: abstention % (abstained / n in tier). n per tier is 100 for",
        "every model (500 entities split 100 per tier).",
        "",
        "| model | type | very rare | rare | medium | freq | very freq |",
        "|---|---|---|---|---|---|---|",
    ]
    for uname, _, ptype in MODELS:
        cells = []
        for t in TIERS:
            n, ae, _ = unl[uname]["by_tier"][t]
            cells.append(p1(pct(ae, n)))
        L.append(f"| {uname} | {ptype} | " + " | ".join(cells) + " |")
    L += [
        "",
        "Reading. The newer RLHF models show a clear rarity dose-response in",
        "abstention: ChatGPT and GPT-4 abstain far more on very-rare entities than",
        "on frequent ones (monotone or near-monotone down the tiers), i.e. they",
        "withhold at the knowledge frontier. Alpaca x3, Dolly, and Pythia abstain",
        "0.0% at every tier (flat, no frontier sensitivity). Vicuna and MPT-Chat",
        "(SFT-only) and Stablelm-alpha (base/weak) DO abstain more on rarer tiers,",
        "so a rarity gradient is not unique to RLHF; what is unique to the newer",
        "RLHF models is pairing that gradient with high precision (F1). Stablelm",
        "abstains heavily across all tiers including frequent ones, consistent with",
        "indiscriminate rather than knowledge-targeted refusal.",
        "",
        "### Factual error rate by rarity tier (from labeled/, human labels)",
        "",
        "Error rate = NS / (S + NS) over human-atomic-facts (IR excluded). Counts",
        "are facts, not generations. Rows with null annotations (abstentions /",
        "undecomposable) contribute no facts and are excluded (count shown).",
        "Entity sets here are DISJOINT from unlabeled/, so these are a parallel",
        "rarity probe, not the same generations as the abstention table above.",
        "",
        "| model | null-ann rows | very rare | rare | medium | freq | very freq |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in LABELED:
        cells = []
        for t in TIERS:
            s, ns, _ = lab[m]["by_tier"][t]
            cells.append(p1(pct(ns, s + ns)))
        L.append(f"| {m} | {lab[m]['none_ann']} (of {lab[m]['rows']}) | " + " | ".join(cells) + " |")
    L += [
        "",
        "Fact counts per tier (S / NS / IR) for transparency:",
        "",
        "| model | tier | S | NS | IR |",
        "|---|---|---|---|---|",
    ]
    for m in LABELED:
        for t in TIERS:
            s, ns, ir = lab[m]["by_tier"][t]
            L.append(f"| {m} | {t} | {s} | {ns} | {ir} |")
    L += [
        "",
        "Reading. Factual error rises monotonically with entity rarity for all",
        "three labeled models. InstructGPT degrades hardest at the frontier",
        f"({p1(pct(lab['InstructGPT']['by_tier']['very rare'][1], sum(lab['InstructGPT']['by_tier']['very rare'][:2])))}% error on very-rare facts vs"
        f" {p1(pct(lab['InstructGPT']['by_tier']['very freq'][1], sum(lab['InstructGPT']['by_tier']['very freq'][:2])))}% on very-frequent);"
        " ChatGPT is",
        f"lower but still steep ({p1(pct(lab['ChatGPT']['by_tier']['very rare'][1], sum(lab['ChatGPT']['by_tier']['very rare'][:2])))}% -> {p1(pct(lab['ChatGPT']['by_tier']['very freq'][1], sum(lab['ChatGPT']['by_tier']['very freq'][:2])))}%);"
        " PerplexityAI (retrieval-",
        f"augmented) is flattest and lowest ({p1(pct(lab['PerplexityAI']['by_tier']['very rare'][1], sum(lab['PerplexityAI']['by_tier']['very rare'][:2])))}% -> {p1(pct(lab['PerplexityAI']['by_tier']['very freq'][1], sum(lab['PerplexityAI']['by_tier']['very freq'][:2])))}%)."
        " Put with the",
        "abstention table: when a model responds anyway on rare entities, the",
        "facts it produces are wrong 50-86% of the time (InstructGPT/ChatGPT),",
        "which is exactly the regime where the newer RLHF models choose to abstain.",
        "",
    ]

    # ---------------- F3 ----------------
    L += [
        "## F3. Judge-noise quantification (metric reliability)",
        "",
        "Per-fact agreement between the two automated judges (ChatGPT_Labels vs",
        "LLAMA+NP_Labels) on the fact subset where BOTH are present and aligned in",
        "length. This is the ~20% of prediction rows carrying ChatGPT_Labels.",
        "",
        "| model | facts compared (n) | agreement % | disagreement % |",
        "|---|---|---|---|",
    ]
    tot_agree = tot_both = 0
    for uname, _, _ in MODELS:
        d = pred[uname]
        tot_agree += d["agree"]
        tot_both += d["both"]
        ag = pct(d["agree"], d["both"])
        L.append(f"| {uname} | {d['both']} | {p1(ag)} | {p1(100 - ag)} |")
    overall = pct(tot_agree, tot_both)
    L += [
        f"| OVERALL (pooled facts) | {tot_both} | {p1(overall)} | {p1(100 - overall)} |",
        "",
        "Reading. The two automated judges disagree on"
        f" {p1(100 - overall)}% of atomic facts overall",
        f"(per-model {p1(min(pct(pred[u]['agree'], pred[u]['both']) for u, _, _ in MODELS))}-"
        f"{p1(max(pct(pred[u]['agree'], pred[u]['both']) for u, _, _ in MODELS))}% agreement)."
        " For comparison, our Cheng-data",
        "reanalysis found 43-51% label noise; FActScore's two judges agree more",
        "than that (disagreement here is roughly half the Cheng figure), but a",
        f"{p1(100 - overall)}% per-fact disagreement is still a material reliability"
        " floor on any",
        "single-judge FActScore number. Disagreement is HIGHER for the higher-",
        "precision models (GPT-4/ChatGPT) and lower for the low-precision ones,",
        "so judge noise is not uniform across the precision range used in F1.",
        "",
        "Human-vs-auto agreement is NOT computable from these files: the labeled/",
        "set carries only human labels (no stored automated labels) and its 183",
        "entities are disjoint from the 500 unlabeled entities that the automated",
        "predictions cover, so there is no generation on which both a human and an",
        "automated label exist. We therefore report only auto-vs-auto agreement and",
        "flag the missing human anchor as a limitation.",
        "",
        "## Limitations",
        "",
        "- Self-judging: ChatGPT_Labels are produced by ChatGPT, and three of the",
        "  judged models are GPT-family (GPT-4, ChatGPT, InstructGPT). ChatGPT",
        "  precision exceeds LLAMA+NP precision for every model (F1), consistent",
        "  with a lenient or self-favoring judge; treat F1 ChatGPT-precision",
        "  columns as an upper bound, not ground truth.",
        "- Label coverage: ChatGPT_Labels exist on only ~20% of responding rows",
        "  (69-100 rows per model), so F1 ChatGPT precision and the entire F3",
        "  agreement analysis rest on that subset; LLAMA+NP precision uses all rows.",
        "- No human anchor on the prediction set (disjoint entity sets), so F3 is",
        "  auto-vs-auto reliability only; absolute judge accuracy is not measured.",
        "- F2's two halves use disjoint entities (abstention from the 500-entity",
        "  unlabeled set; error rate from the 183-entity labeled set), so the",
        "  abstention-vs-error pairing is a population-level juxtaposition, not a",
        "  within-generation trade-off.",
        "- PerplexityAI appears only in labeled/ (no unlabeled / prediction files),",
        "  so it has an error-rate-by-tier row but no respond-ratio or abstention",
        "  row. Alpaca-65B's prediction file is alpaca.jsonl (by elimination).",
        "- Rates are descriptive; no per-question variances or seeds are released,",
        "  and the 100-per-tier entity bins are the authors' fixed split (not",
        "  resampled), so no confidence intervals are computed.",
        "",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L))
    print(f"wrote {OUT.relative_to(HERE.parent.parent)}")

    # ===================== figures =====================
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGDIR.mkdir(parents=True, exist_ok=True)

    # F1: respond ratio vs precision scatter, colored by post-training type
    fig, ax = plt.subplots(figsize=(7.5, 6))
    seen = set()
    for uname, _, ptype in MODELS:
        d = pred[uname]
        color, marker = TYPE_STYLE[ptype]
        rr = pct(d["rows"], 500)
        ax.scatter(rr, d["ll_prec"], c=color, marker=marker, s=70, zorder=3,
                   label=ptype if ptype not in seen else None)
        seen.add(ptype)
        ax.annotate(uname, (rr, d["ll_prec"]), fontsize=6.5,
                    xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("respond ratio % (lower = abstains more)")
    ax.set_ylabel("LLAMA+NP factual precision % (share of atomic facts Supported)")
    ax.set_title("FActScore: respond ratio vs factual precision, by post-training type\n"
                 "(newer RLHF = low respond + high precision, top-left)", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=9, title="post-training type", loc="best")
    fig.tight_layout()
    fig.savefig(FIGDIR / "factscore_respond_precision.png", dpi=160)
    plt.close(fig)

    # F2: abstention-by-rarity (left) + error-by-rarity (right)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    xs = range(len(TIERS))
    for uname, _, ptype in MODELS:
        color, _ = TYPE_STYLE[ptype]
        ys = [pct(unl[uname]["by_tier"][t][1], unl[uname]["by_tier"][t][0]) for t in TIERS]
        axes[0].plot(xs, ys, "o-", color=color, alpha=0.8, linewidth=1.3, markersize=4)
        # label rightmost point
        axes[0].annotate(uname, (xs[-1], ys[-1]), fontsize=5.5,
                         xytext=(3, 0), textcoords="offset points", color=color)
    axes[0].set_xticks(list(xs))
    axes[0].set_xticklabels(TIERS, fontsize=8, rotation=20)
    axes[0].set_ylabel("abstention rate % (n=100 per tier per model)")
    axes[0].set_title("Abstention vs entity rarity (12 models)", fontsize=10)
    axes[0].grid(alpha=0.3)
    lab_colors = {"InstructGPT": "#27b", "ChatGPT": "#d90", "PerplexityAI": "#2a7"}
    for m in LABELED:
        ys = [pct(lab[m]["by_tier"][t][1], sum(lab[m]["by_tier"][t][:2])) for t in TIERS]
        axes[1].plot(xs, ys, "s-", color=lab_colors[m], linewidth=1.6, markersize=5, label=m)
    axes[1].set_xticks(list(xs))
    axes[1].set_xticklabels(TIERS, fontsize=8, rotation=20)
    axes[1].set_ylabel("factual error rate % (NS / (S+NS) human facts)")
    axes[1].set_title("Factual error vs entity rarity (labeled set)", fontsize=10)
    axes[1].grid(alpha=0.3)
    axes[1].legend(fontsize=8)
    # type legend for left panel
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], color=c, marker=m, linestyle="-", label=t)
               for t, (c, m) in TYPE_STYLE.items()]
    axes[0].legend(handles=handles, fontsize=8, title="post-training type", loc="best")
    fig.suptitle("FActScore: rarity dose-response (abstention left, factual error right)", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGDIR / "factscore_rarity.png", dpi=160)
    plt.close(fig)
    print("wrote figures/factscore_respond_precision.png, factscore_rarity.png")


if __name__ == "__main__":
    main()
