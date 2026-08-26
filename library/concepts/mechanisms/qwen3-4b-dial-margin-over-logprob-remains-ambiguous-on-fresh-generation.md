---
title: qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation
aliases:
- Dial margin over sequence probability lands in the ambiguous band on fresh
  Qwen3-4B generation
- v3 S-arm result, first gated dial-vs-logprob comparison in the lineage
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen3-4b-dial-margin-over-logprob-remains-ambiguous-on-fresh-generation
  type: mechanism
  status: canonical
cause: "Comparing the correctness dial's out-of-fold AUROC against the Qwen3-4B Instruct base's own length-normalized answer-span log-probability AUROC, on fresh, self-consistently generated rows (S arm, 1820 answered rows) captured with zero round-trip integrity divergence -- the first gated (not merely descriptive) measurement of this comparison in the dial-logprob-baseline lineage."
effect: "The dial-minus-logprob margin is small and statistically uncertain: +0.0118, paired 95% CI [-0.0122, +0.0359] (n_boot 2000, seed 20260813; fresh dial OOF AUROC 0.8301, at or above the 0.75 sanity bound and close to the June-signed 0.834). The margin lands inside the pre-registered ambiguous band (0 < margin < +0.05, or CI straddling 0) rather than clearing the +0.05 LP3-G1 novelty floor, so the gate does not pass; the dial-novelty falsifier (logprob AUROC at or above dial AUROC) does not fire either. The result closely matches v1's earlier non-gated descriptive read on the same population (+0.014, CI [-0.011, +0.040]), now delivered as a clean, gated measurement rather than a caveated descriptive number."
polarity: complicates
related:
- '[[dial-logprob-baseline-v3]]'
- '[[per-answer-correctness-linearly-readable-post-generation]]'
- '[[model-accuracy-strengthens-probability-correctness-signal]]'
- '[[sequence-probability]]'
relationships:
- type: supported_by
  target: '[[dial-logprob-baseline-v3]]'
  target_id: experiment:dial-logprob-baseline-v3
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md#outcome (S arm; "the
    registered ambiguous-band disposition applies verbatim -- reported as a
    small/uncertain margin, gate not passed, gate not retuned")
- type: related_to
  target: '[[per-answer-correctness-linearly-readable-post-generation]]'
  target_id: mechanism:per-answer-correctness-linearly-readable-post-generation
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Design; dial is the
    S-cell's own out-of-fold post-generation correctness probe, layer L20)
- type: related_to
  target: '[[model-accuracy-strengthens-probability-correctness-signal]]'
  target_id: mechanism:model-accuracy-strengthens-probability-correctness-signal
  confidence: medium
  evidence:
  - experiments/dial-logprob-baseline/AMENDMENT.md (Motivation; Zenn and
    Geiping 2026 within-dataset probability-correctness signal, the
    competitor baseline the dial is benchmarked against)
- type: related_to
  target: '[[sequence-probability]]'
  target_id: term:sequence-probability
  confidence: high
  evidence:
  - experiments/dial-logprob-baseline-v3/AMENDMENT.md (Design; primary
    logprob variant is length-normalized mean answer-span token logprob)
---

After two cells (v1, v2) halted before ever computing a gated dial-versus-
logprob comparison, [[dial-logprob-baseline-v3]]'s S arm is the first clean
measurement in the lineage: with capture integrity perfect (zero round-trip
divergences) and the dial reading at 0.8301 OOF AUROC on fresh data (close
to the June-signed 0.834), the dial's margin over the raw model's own
length-normalized answer-span log-probability is +0.0118 with a 95% CI of
[-0.0122, +0.0359]. That is positive but comfortably under the +0.05
novelty floor, and the interval straddles zero, so it lands squarely in the
lineage's own pre-registered ambiguous band rather than either passing the
gate or triggering the dial-novelty falsifier.

**Why it matters here:** this is not a null result in the sense of "nothing
happened" -- the instrument worked (integrity clean, dial reads at a
sensible AUROC) and the measurement is real, it is simply inconclusive at
the registered precision. It also closes an open question the lineage
carried since v1: v1's own descriptive (non-gated) base-arm number was
+0.014 [-0.011, +0.040], and v3's gated number (+0.0118 [-0.0122, +0.0359])
lands almost on top of it, so the exact-precision redo confirms rather than
overturns what the earlier, integrity-caveated read had suggested. On the
base model, sequence probability alone already captures nearly all of the
dial's separation; the dial's independent value over free sequence
probability, if any, remains to be established elsewhere (the T-arm
deployed-checkpoint comparison, which v1's own descriptive numbers
suggested is where the dial's margin is largest, was not measured in v3
for want of answered rows past the pre-registered power floor).

**Lineage:** the S-arm finding of [[dial-logprob-baseline-v3]] (resolved
2026-08-13), the first gated result in the dial-logprob-baseline cascade
that began with [[dial-logprob-baseline]] (v1) and continued through
[[dial-logprob-baseline-v2]] (v2).
