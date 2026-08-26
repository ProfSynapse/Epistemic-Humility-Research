---
title: dial-logprob-baseline
aliases:
- Dial token-logprob baseline (LP)
- v1 dial-vs-sequence-probability baseline
tags:
- kg/experiment
- experiment
- correctness-dial
kg:
  id: experiment:dial-logprob-baseline
  type: experiment
  status: canonical
related:
- '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[sequence-probability]]'
- '[[reproduction-bet-causes-generation-capture-round-trip-failure]]'
relationships:
- type: builds_on
  target: '[[2606.27359--when-likely-answers-right-sequence-probability-correctness]]'
  target_id: paper:2606.27359
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md (Motivation and posture;
    cites Zenn and Geiping 2026's within-dataset probability-correctness
    Pearson r 0.66 base / 0.59 post-trained as the reason the dial's margin
    over sequence probability was worth quantifying)
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md (Motivation; reference
    dial numbers AUROC 0.834 Instruct base L20 / 0.819 deployed L22, the
    competitor this cell benchmarks against)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md (Design; primary logprob
    variant is length-normalized mean answer-span token logprob)
- type: supports
  target: '[[reproduction-bet-causes-generation-capture-round-trip-failure]]'
  target_id: mechanism:reproduction-bet-causes-generation-capture-round-trip-failure
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md#outcome (LP-G0 DATA-STAGE
    STOP; exact sequence round-trip FAILED on 14/1836 S + 16/1488 T rows,
    0.9% pooled, off by exactly one BPE token; generation-time token IDs
    were never cached)
---

First cell of the dial-token-logprob-baseline lineage: closes paper 4's
limitation 8 by benchmarking the correctness dial's discriminative power
against the cheapest internal competitor, the model's own answer-span
sequence probability, on the amendment S base population (primary) and the
amendment T deployed population (descriptive). Exploratory Tier-2 lab cell,
never pooled with the locked Phase 1 matrix.

Resolved 2026-07-18 as a **DATA-STAGE STOP**. LP-G0's dial-reproduction and
row-count sub-criteria both passed, but the exact answer-span round-trip
sub-criterion failed on 30/3324 rows (14/1836 S, 16/1488 T; 0.9% pooled),
each off by exactly one BPE token. Root cause: generation-time token IDs
were never cached, so the harness had to invert the decode by re-tokenizing
cached answer text, which is not bit-stable at BPE span boundaries. Per the
gate's own registered wording ("any mismatch is a data-stage stop, not a
result"), the stop fires and no gated comparison is reported; see
[[reproduction-bet-causes-generation-capture-round-trip-failure]].

Descriptive-only numbers, computed for transparency on the round-trip-clean
rows and explicitly NOT gated: S base arm (n=1822, 498c/1324w) dial 0.8338
vs primary logprob 0.8198, margin +0.014, paired 95% CI [-0.011, +0.040].
T deployed arm (n=1472, 979c/493w) dial 0.8183 vs primary logprob 0.6608,
margin +0.158, CI [+0.122, +0.192]. The orchestrator's pre-run blind guess
(logprob AUROC 0.60-0.72) was wrong: sequence probability on the raw base
already captures nearly all of the dial's separation. The directional
picture the caveated numbers suggest is that the dial's clear margin over
sequence probability appears on the deployed, trained checkpoint (where
logprob degrades to 0.661 while the dial holds 0.818), not on the raw base
-- a reading that needed a successor cell to confirm at gated precision.

**Lineage:** motivated by `papers/paper-4-two-signal-readout/manuscript.md`
limitation 8. Superseded by [[dial-logprob-baseline-v2]] (clean redo
attempt, also a data-stage stop) and [[dial-logprob-baseline-v3]] (first
cell in the lineage to reach a gated comparison). Source of truth:
`experiments/dial-logprob-baseline/AMENDMENT.md`, Outcome section, resolved
2026-07-18.
