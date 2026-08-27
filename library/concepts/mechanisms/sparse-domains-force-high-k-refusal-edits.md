---
aliases:
- sparse refusal domains require dense masks
- weak-domain refusal edits damage utility
- high-k refusal masks collapse utility
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sparse-domains-force-high-k-refusal-edits
  type: mechanism
  status: canonical
cause: "A harm domain has a sparse or weak contrastive refusal signal, as in the medical and legal domains in [[cast-refusal-benchmark]]"
effect: "The refusal edit requires a larger row mask, increasing perplexity and reducing downstream utility on MMLU, GSM8K, and IFEval"
polarity: causes
area: safety-evaluation
related:
- '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
- '[[cast-refusal-benchmark]]'
- '[[perplexity]]'
- '[[mmlu]]'
- '[[gsm8k]]'
- '[[ifeval]]'
relationships:
- type: supported_by
  target: '[[2607.05355--faithfulness-refusal-causal-audit-neuron-selectors]]'
  target_id: paper:2607.05355
  confidence: high
  evidence:
  - Section 6.4
  - Table 45
- type: related_to
  target: '[[cast-refusal-benchmark]]'
  target_id: dataset:cast-refusal-benchmark
  confidence: high
- type: related_to
  target: '[[perplexity]]'
  target_id: metric:perplexity
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: high
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: high
- type: related_to
  target: '[[ifeval]]'
  target_id: dataset:ifeval
  confidence: high
---

When a refusal domain has a weak or sparse contrastive signal, a row-mask edit may need a larger selected fraction to affect behavior, and that density can damage general utility. Faithfulness to Refusal shows this for medical and legal domains on LLaMA-3.1-8B, where refusal rates rise only with high-cost masks that increase perplexity and reduce MMLU, GSM8K, and IFEval.

**Implication:** Refusal and abstention edits need domain-specific utility gates. A mask that works for hate or crime cannot be assumed safe for lower-signal domains.
