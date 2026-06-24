---
aliases:
- paraphrase divergence probe
- UU probability probe
tags:
- kg/method
- concept
- method
kg:
  id: method:paraphrase-divergence-probe
  type: method
  status: canonical
area: methods
related:
- '[[2606.08571--structured-ignorance-certificates]]'
- '[[structured-ignorance-certificates]]'
- '[[semantic-entropy]]'
- '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
- '[[consistency-based-confidence]]'
- '[[self-consistency]]'
relationships:
- type: proposed_by
  target: '[[2606.08571--structured-ignorance-certificates]]'
  target_id: paper:2606.08571
  confidence: high
- type: related_to
  target: '[[structured-ignorance-certificates]]'
  target_id: method:structured-ignorance-certificates
  confidence: medium
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[lexical-entropy-overestimates-uncertainty-under-paraphrase]]'
  target_id: mechanism:lexical-entropy-overestimates-uncertainty-under-paraphrase
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
---

A behavioral probe trained on model responses to paraphrased versions of the same query. High divergence across paraphrases of an unknown-unknown question is taken as evidence that the model's output is not grounded in stable knowledge, yielding an unknown-unknown probability score. Used to verify that SIC-tuned outputs systematically reflect higher epistemic uncertainty.

**Why it matters here:** Provides an output-level signal for unknown-unknown probability without requiring access to model internals, and confirms that learned SIC behavior generalizes across surface rephrasing rather than fitting specific lexical patterns.

**Lineage:** Introduced in Sahoo 2026 (arXiv 2606.08571) as a probe to validate the SIC fine-tuning approach.
