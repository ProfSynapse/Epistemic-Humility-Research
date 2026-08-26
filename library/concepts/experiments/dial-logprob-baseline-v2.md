---
title: dial-logprob-baseline-v2
aliases:
- Dial token-logprob baseline, clean redo (generation-time token-ID cache)
- v2 dial-vs-sequence-probability baseline redo
tags:
- kg/experiment
- experiment
- correctness-dial
kg:
  id: experiment:dial-logprob-baseline-v2
  type: experiment
  status: canonical
related:
- '[[dial-logprob-baseline]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[sequence-probability]]'
- '[[reproduction-bet-causes-generation-capture-round-trip-failure]]'
relationships:
- type: builds_on
  target: '[[dial-logprob-baseline]]'
  target_id: experiment:dial-logprob-baseline
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v2/AMENDMENT.md (Motivation and
    posture; builds on v1's DATA-STAGE STOP, diagnoses the round-trip
    failure to v1's harness discarding generation-time token IDs, and
    inherits v1's populations, gates, and falsifier verbatim)
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v2/AMENDMENT.md (Design; dial refit
    reproduces the source cell's signed AUROC, S 0.834 at L20, T 0.819 at
    L22, before any comparison is unblinded)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v2/AMENDMENT.md (Design; primary
    logprob variant is length-normalized mean answer-span token logprob,
    inherited verbatim from v1)
- type: supports
  target: '[[reproduction-bet-causes-generation-capture-round-trip-failure]]'
  target_id: mechanism:reproduction-bet-causes-generation-capture-round-trip-failure
  confidence: high
  evidence:
  - "experiments/dial-logprob-baseline-v2/AMENDMENT.md#outcome (LP-G0 data-stage
    stop both arms -- S dial refit 0.8395 vs signed 0.834 outside 0.002
    tolerance, 282/1836 (15.4%) round-trip failures; T dial refit 0.8164 vs
    signed 0.819, 93/1488 (6.3%) round-trip failures)"
---

Clean redo of [[dial-logprob-baseline]] (v1) after v1's DATA-STAGE STOP was
traced to a specific implementation gap: v1's harness computed the exact
generation-time answer-span token IDs in memory during `model.generate()`
but discarded them, persisting only decoded text, forcing a re-tokenization
that is not bit-stable at BPE span boundaries. v2's fix: one
`model.generate(..., output_scores=True, return_dict_in_generate=True)`
call per row so the exact generation-time token IDs and per-step logits are
captured directly, never re-tokenized, with a stricter LP-G0 round-trip
check (content match, not just token count) and a new confirmation
falsifier testing whether the gated redo would land outside v1's own
descriptive band. Populations, dial refit procedure, logprob variants, and
the primary falsifier all carry over verbatim from v1.

Resolved 2026-08-13. **LP-G0 data-stage stop, both arms -- no result, per
the registered pre-outcome rule.** S base arm: dial refit 0.8395 vs signed
0.834 (|diff| 0.0055, outside the 0.002 tolerance); row counts passed
(1836/1836); byte-for-byte answer_text round-trip failed on 282/1836 rows
(15.4%). T deployed arm: dial refit 0.8164 vs signed 0.819 (|diff| 0.0026);
row counts passed (1488/1488); round-trip failed on 93/1488 rows (6.3%).
Per the registered discipline ("any mismatch is a data-stage stop, not a
result"), the downstream dial-vs-logprob margins the harness computed
before halting are explicitly NOT results and are not reportable; both
committed JSONs carry `gate_verdict.stopped_at_lp_g0 = true` as the sole
verdict. The working hypothesis, recorded but not diagnosed behind the
stop: exact greedy-decode reproduction of June-cached generations drifted
under a later torch 2.10.0+cu128 stack and 4-bit quantized kernels. See
[[reproduction-bet-causes-generation-capture-round-trip-failure]] for the
shared root cause with v1.

**Lineage:** builds on [[dial-logprob-baseline]] (v1); its own unresolved
round-trip failure motivated [[dial-logprob-baseline-v3]], which removes
the reproduction bet entirely rather than tightening the round-trip check
further. Source of truth: `experiments/dial-logprob-baseline-v2/AMENDMENT.md`,
Outcome section, resolved 2026-08-13.
