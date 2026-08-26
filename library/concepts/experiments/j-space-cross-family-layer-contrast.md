---
title: j-space-cross-family-layer-contrast
aliases:
- cross-family J-space mid-band actuation contrast
- does mid-band actuation transfer across model families
tags:
- kg/experiment
- experiment
- j-space
- cross-family
kg:
  id: experiment:j-space-cross-family-layer-contrast
  type: experiment
  status: canonical
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[activation-steering]]'
- '[[known-unknown-direction]]'
- '[[mistral-7b]]'
- '[[gemma-4]]'
relationships:
- type: builds_on
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/j-space-cross-family-layer-contrast/AMENDMENT.md (Consumed
    doubt-snap artifacts; reuses its resolved per-family eval pool, FIT/HELD-OUT
    split, and frozen late-site direction/gate verbatim for llama-3.2-3b,
    mistral-7b-v0.3, and qwen3.5-4b)
- type: related_to
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: high
  evidence:
  - experiments/j-space-cross-family-layer-contrast/AMENDMENT.md (Motivation
    and posture; asks whether that experiment's raw-base Qwen3-4B mid-band
    write-site advantage over the late hs34 site transfers across model
    families, or is a Qwen3-lineage idiosyncrasy)
- type: supports
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/j-space-cross-family-layer-contrast/AMENDMENT.md#outcome
    (per-family primary gates -- llama-3.2-3b PASS both gates at hs17,
    mistral-7b-v03 misses the G1 floor only at hs15, a marginal rather than
    uniform result)
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: medium
  evidence:
  - experiments/j-space-cross-family-layer-contrast/AMENDMENT.md#outcome
    (llama's mid-band held-out clean_tighten 0.7420 and mistral's 0.4893 both
    far exceed doubt-snap's late-site FIT peaks of 0.184 and 0.000
    respectively, consistent with that mechanism's wrong-site-not-absent-
    mechanism reading, though this experiment's own outcome has no
    random-direction control)
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[mistral-7b]]'
  target_id: model:mistral-7b
  confidence: low
- type: related_to
  target: '[[gemma-4]]'
  target_id: model:gemma-4
  confidence: low
---

Cross-family generalization test of J-space mid-band actuation: does the
mid-band write-site advantage found on raw-base Qwen3-4B
(`j-space-calibrated-layer-contrast-qwen3-4b`) transfer to other model
families, or is it a Qwen3-lineage idiosyncrasy? Mirrors the shape of
Amendment Z's cross-family confirmatory of the training-free two-signal
readout and reuses its four checkpoints and run order (llama-3.2-3b,
mistral-7b-v0.3, qwen3.5-4b, gemma-4-E4B). Consumes
`doubt-snap-cross-family-confirmatory`'s resolved per-family eval pools,
FIT/HELD-OUT splits, and frozen late-site direction/gate verbatim for three
of the four families; gemma-4-E4B fresh-mines its own pool because its row
text was absent from the doubt-snap Modal volume. The only new work is
per-family J-lens mid-band localization, mid-band direction fits, and dose
calibration (mid-run revised to a per-family norm-scaled ratio ladder after
llama and mistral's original absolute dose ladder proved
instrument-resolution-limited on their own residual-stream norms).

**VERDICT: INCONCLUSIVE**, signed 2026-07-24, closed out permanently
2026-08-18 without running the remaining families. Only 2 of the 4
registered families ran past the G0 instrument-validity gate. Llama-3.2-3b's
best mid-band site (hs17) passed both primary gates on held-out: confab
`clean_tighten` 647/872 = 0.7420 (Wilson 95% [0.7119, 0.7699]) against the
0.50/0.40 floor, and known-correct cost 4/334 = 0.0120 (PASS, but
non-diagnostic since the KU gate fired on 0 dosed known-correct rows).
Mistral-7b-v0.3's best mid-band site (hs15) missed G1 on the point estimate
only (642/1312 = 0.4893 against the 0.50 floor; Wilson lower 0.4624 still
clears the 0.40 sub-criterion) -- a marginal floor miss, not a collapse.
Qwen3.5-4b and gemma-4-E4B never ran: gemma-4-E4B stopped at G0 because its
activations were corrupted by `use_cache=False` (blocks 24-41 read donor K/V
from blocks 22/23 through the cache object, so disabling the cache starves
them), making its 0/176 late-arm write null uninterpretable rather than
negative; qwen3.5-4b's run was never completed before the close-out decided
the best reachable outcome (running it alone could reach at most "2 of 3 run
families pass," the user's own registered MIXED call) did not justify
further GPU spend once gemma's instrument defect made the 3-of-4 SUCCESS bar
arithmetically unreachable. Per the pre-registered roll-up rule ("fewer than
3 families ran => INCONCLUSIVE, not a pass"), the cross-family question is
not answered in either direction; llama PASS and mistral marginal-FAIL stand
as recorded evidence but are not pooled into a claim.

A descriptive finding outside the gates: gemma-4-E4B's corrected
(`use_cache=True`) activations are readable at every depth (held-out
KU-direction AUROC >= 0.977 from hs5 through hs42, peaking at hs18, relative
depth 0.429, at 0.9999), a saturated read profile that supplies no
site-selection signal for that family and sharpens the read/write
dissociation already visible in llama and mistral: sites chosen by a read
criterion are not thereby good write sites.

Two registered-instrument defects were found at resolve and recorded rather
than worked around: G2 (the known-correct cost cap) is non-diagnostic here
because the KU gate never fires on known-correct rows in these families
(the dosed known-correct denominator is 0 on every measured layer), so its
registered PASS stands per the standing non-diagnostic-gate rule but carries
that caveat and must not be cited as evidence of write selectivity; and the
success/falsifier rule is stated inconsistently between this document and
`experiment.yaml`, resolved in favor of the conservative INCONCLUSIVE
reading. Source of truth:
`experiments/j-space-cross-family-layer-contrast/AMENDMENT.md` (Outcome and
Close-out sections).
