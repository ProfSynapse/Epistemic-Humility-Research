---
aliases:
- composite SIC reward
- retrieval-utility reward
- format-validity reward
tags:
- kg/method
- concept
- method
kg:
  id: method:sic-composite-reward
  type: method
  status: canonical
area: methods
related:
- '[[2606.08571--structured-ignorance-certificates]]'
- '[[structured-ignorance-certificates]]'
- '[[group-relative-policy-optimization]]'
- '[[rule-based-reward-model]]'
- '[[ternary-reward-design]]'
- '[[grpo-eliminates-critic-reduces-memory]]'
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
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[rule-based-reward-model]]'
  target_id: method:rule-based-reward-model
  confidence: medium
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: medium
- type: related_to
  target: '[[grpo-eliminates-critic-reduces-memory]]'
  target_id: mechanism:grpo-eliminates-critic-reduces-memory
  confidence: medium
---

A GRPO reward function composed of three components: retrieval utility (whether the proposed query would retrieve useful information), concept specificity (precision of the enumerated missing concepts), and output-format validity (syntactic JSON correctness). Used to train models to produce high-quality Structured Ignorance Certificates.

**Why it matters here:** Decomposes the quality of a structured ignorance declaration into measurable sub-signals, enabling gradient-based learning of epistemic output format rather than relying on binary pass/fail rewards.

**Lineage:** Introduced in Sahoo 2026 (arXiv 2606.08571) as the training signal for SIC fine-tuning.
