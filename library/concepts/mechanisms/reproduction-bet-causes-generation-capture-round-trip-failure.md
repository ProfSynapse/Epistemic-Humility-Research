---
title: reproduction-bet-causes-generation-capture-round-trip-failure
aliases:
- Betting on past-generation reproduction causes token round-trip failure
- Dial-logprob baseline v1/v2 data-stage stops share one root cause
- Re-tokenizing or replaying a cached generation is not bit-stable
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reproduction-bet-causes-generation-capture-round-trip-failure
  type: mechanism
  status: canonical
cause: "Reconstructing a generation's exact answer-span token identities after the fact rather than capturing them at generation time: v1 re-tokenized the decoded answer text in isolation to invert a discard-then-decode pipeline, and v2 attempted to byte-for-byte reproduce months-old cached rows under a newer torch/CUDA/quantization stack via one model.generate(..., output_scores=True) call per row."
effect: "A pre-registered integrity gate (LP-G0's round-trip sub-criterion) fails on a nonzero share of rows: v1, 30/3324 rows (0.9% pooled) off by exactly one BPE token at answer-span boundaries; v2, 282/1836 S-arm (15.4%) and 93/1488 T-arm (6.3%) rows fail byte-for-byte, alongside the dial refit itself missing its 0.002 reproduction tolerance on both arms (0.0055 / 0.0026). Per each cell's own registered discipline ('any mismatch is a data-stage stop, not a result'), both cells halt before any dial-vs-logprob comparison can be gated. The failure point in both cases is the reproduction bet, not the underlying comparison."
polarity: causes
related:
- '[[dial-logprob-baseline]]'
- '[[dial-logprob-baseline-v2]]'
- '[[dial-logprob-baseline-v3]]'
- '[[sequence-probability]]'
relationships:
- type: supported_by
  target: '[[dial-logprob-baseline]]'
  target_id: experiment:dial-logprob-baseline
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md#outcome (LP-G0 DATA-STAGE
    STOP; exact sequence round-trip FAILED 14/1836 S + 16/1488 T rows, 0.9%
    pooled, off by exactly one BPE token)
- type: supported_by
  target: '[[dial-logprob-baseline-v2]]'
  target_id: experiment:dial-logprob-baseline-v2
  confidence: high
  evidence:
  - "experiments/dial-logprob-baseline-v2/AMENDMENT.md#outcome (LP-G0 data-stage
    stop both arms -- dial refit outside 0.002 tolerance, 282/1836 (15.4%) S
    and 93/1488 (6.3%) T byte-for-byte round-trip failures)"
- type: related_to
  target: '[[dial-logprob-baseline-v3]]'
  target_id: experiment:dial-logprob-baseline-v3
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Why a v3, and what it
    changes; v3 removes the reproduction bet entirely rather than tolerating
    it, designing this failure class out)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: medium
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md (Design; the halted
    comparison was against the model's own answer-span sequence probability)
---

Two independent cells in the dial-token-logprob-baseline lineage (v1 and v2)
set out to compare the correctness dial's AUROC against the model's own
answer-span sequence probability, and both halted before computing a
reportable comparison, for the same underlying reason: each bet on exactly
reproducing a past generation event rather than capturing the generation's
own token identities and logprobs at the moment they were produced. v1
discarded the generation-time token IDs and tried to invert the decode by
re-tokenizing the cached answer text, which is not bit-stable at BPE span
boundaries (30/3324 rows off by one token). v2 tried to regenerate the same
months-old cached rows byte-for-byte under a newer torch/CUDA/quantization
stack, which drifted on 282/1836 (S) and 93/1488 (T) rows, with the dial
refit itself also missing its reproduction tolerance on both arms.

**Why it matters here:** neither halt says anything about the dial's actual
margin over sequence probability; the comparison itself was never wrong, and
the populations, gates, and falsifier were unaffected. The recurring failure
identifies the reproduction bet as the fragile step, which is what motivated
[[dial-logprob-baseline-v3]] to remove it entirely (fresh, self-consistent
generation with in-call token/logprob/hidden-state capture) rather than
tolerate it with a wider tolerance band.

**Lineage:** first observed in [[dial-logprob-baseline]] (v1, resolved
2026-07-18), recurred in [[dial-logprob-baseline-v2]] (resolved 2026-08-13)
despite a redesigned capture path aimed at exactly this failure mode, and
eliminated in [[dial-logprob-baseline-v3]] (resolved 2026-08-13) by removing
the bet rather than tightening it.
