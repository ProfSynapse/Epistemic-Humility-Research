---
aliases:
- attribution/hedging/refusal data mix reduces hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:attribution-hedging-refusal-data-reduces-hallucination
  type: mechanism
  status: canonical
cause: "Post-training data mix includes subsets that specifically encourage better in-context attribution, hedging, and refusals"
effect: "Performance on factuality metrics improves without degrading performance on other metrics"
polarity: decreases
related:
- '[[2607.02770--gemma-4-technical-report]]'
- '[[hallucination]]'
- '[[instruction-tuning]]'
relationships:
- type: supported_by
  target: '[[2607.02770--gemma-4-technical-report]]'
  target_id: paper:2607.02770
  confidence: low
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: medium
---

Gemma 4's post-training data mix deliberately includes subsets designed to
teach better in-context attribution, appropriate hedging, and refusals on
questions the model should not answer. The claim is that this data mix
reduces hallucination on factuality metrics without a corresponding drop in
other capability metrics, but the technical report does not publish the
ablation numbers that would isolate this subset's contribution (Section 3,
Data filtering).

**Why it matters here:** this is a low-confidence, non-quantified claim from a
model-family technical report rather than a controlled ablation study, so it
supports the general direction of attribution/hedging/refusal data as a
hallucination-reduction lever without providing causal effect sizes.

**Lineage:** related to [[hallucination]] as the target failure mode and
[[instruction-tuning]] as the training stage where such data mixes are
typically applied.
