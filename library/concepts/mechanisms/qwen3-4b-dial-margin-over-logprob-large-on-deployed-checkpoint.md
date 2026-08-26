---
title: qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint
aliases:
- Dial margin over sequence probability is large and gated on the deployed
  abstention-trained Qwen3-4B checkpoint
- T-arm gated confirmation, LT-G1 PASS
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen3-4b-dial-margin-over-logprob-large-on-deployed-checkpoint
  type: mechanism
  status: canonical
cause: "Comparing the correctness dial's out-of-fold AUROC against the deployed abstention-trained Qwen3-4B checkpoint's own length-normalized mean answer-span log-probability AUROC, on fresh, self-consistently generated rows at adequate power (T arm, 1,501 answered rows, LT-G0 integrity clean, 0 capture divergences)."
effect: "The dial-minus-logprob margin is large and gated: +0.1393, paired 95% CI [0.1031, 0.1755] (n_boot 2000, seed 20260813; fresh dial OOF AUROC 0.7962 vs primary mean_answer_span logprob AUROC 0.6569). The margin clears the +0.05 LT-G1 novelty floor and the CI excludes zero; the dial-novelty falsifier does not fire. This is the first gated (not merely descriptive) deployed-checkpoint measurement in the dial-logprob-baseline lineage, superseding v1's +0.158 descriptive read (round-trip caveat) and v2's unblinded stopped-cell +0.1747 read."
polarity: increases
related:
- '[[dial-logprob-t-deployed-confirmatory]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[sequence-probability]]'
- '[[dial-margin-over-logprob-is-checkpoint-dependent]]'
relationships:
- type: supported_by
  target: '[[dial-logprob-t-deployed-confirmatory]]'
  target_id: experiment:dial-logprob-t-deployed-confirmatory
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md#outcome
    (LT-G1 PASS, dial AUROC 0.7962 vs primary mean_answer_span logprob
    AUROC 0.6569, margin +0.1393, paired bootstrap 95% CI [0.1031,
    0.1755])
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md (Design;
    dial is an out-of-fold refit at the T-cell's own signed layer, L22)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md (Design;
    primary logprob variant is length-normalized mean answer-span token
    logprob)
- type: related_to
  target: '[[dial-margin-over-logprob-is-checkpoint-dependent]]'
  target_id: mechanism:dial-margin-over-logprob-is-checkpoint-dependent
  confidence: high
  evidence:
  - experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md#outcome
    (this T-arm PASS paired with v3's S-arm ambiguous-band result is the
    evidence for the checkpoint-dependence claim)
---

The fourth cell in the dial-logprob-baseline lineage ([[dial-logprob-t-deployed-confirmatory]])
is the first to gate the deployed-checkpoint (T-arm) comparison at
adequate power. Where v3's S arm (raw base) landed in the ambiguous band
at +0.0118, the T arm on the deployed abstention-trained checkpoint clears
the +0.05 novelty floor by a wide margin: dial AUROC 0.7962 against the
checkpoint's own mean answer-span logprob AUROC 0.6569, a paired margin of
+0.1393 with a 95% CI of [0.1031, 0.1755] that excludes zero.

**Why it matters here:** this closes the T-side question the lineage
carried open since v1 (whose descriptive-only T read, +0.158, came with a
round-trip integrity caveat) and v2 (whose unblinded T number, +0.1747,
came from a data-stage-stopped cell never intended to be citable). Both
earlier reads pointed the same direction as this cell's gated number,
which now supersedes them as the sole citable deployed-checkpoint margin
in the lineage.

**Lineage:** the T-arm finding of [[dial-logprob-t-deployed-confirmatory]]
(resolved 2026-08-13), paired with [[dial-logprob-baseline-v3]]'s S-arm
ambiguous-band result to establish
[[dial-margin-over-logprob-is-checkpoint-dependent]].
