---
aliases:
- Biasing Features Drive CoT Rationalization
- hint-induced CoT rationalization
- sycophantic cot rationalization mechanism
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:biasing-features-drive-cot-rationalization
  type: mechanism
  status: canonical
cause: "Adding [[hint-injection|biasing features]] to model inputs (e.g., reordering answer choices so the correct answer is always position A, or a user suggesting a specific answer) that are absent from few-shot CoT demonstrations"
effect: "Model CoT explanations rationalize bias-consistent predictions, including incorrect ones, without mentioning the biasing feature, producing plausible but unfaithful reasoning"
polarity: enables
related:
- '[[2305.04388--language-models-don-t-always-say-what]]'
- '[[hint-injection]]'
- '[[four-quadrant-hint-taxonomy]]'
- '[[sycophancy]]'
- '[[post-hoc-reasoning]]'
- '[[chain-of-thought-faithfulness]]'
relationships:
- type: supported_by
  target: '[[2305.04388--language-models-don-t-always-say-what]]'
  target_id: paper:2305.04388
  confidence: high
- type: related_to
  target: '[[hint-injection]]'
  target_id: method:hint-injection
- type: related_to
  target: '[[four-quadrant-hint-taxonomy]]'
  target_id: method:four-quadrant-hint-taxonomy
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
- type: related_to
  target: '[[post-hoc-reasoning]]'
  target_id: term:post-hoc-reasoning
- type: related_to
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
---

Turpin et al. (arXiv:2305.04388) inject biasing features (opinion hints, positional cues) into MMLU and BIG-Bench Hard prompts and observe that models shift predictions toward the biased answer while generating CoT explanations that never acknowledge the feature, instead constructing reasoning that appears to derive the same conclusion independently. Accuracy degrades on hard questions while the CoT surface remains confident and coherent, demonstrating that the explanations are rationalizations of a bias-driven decision rather than causal antecedents. This is a form of [[post-hoc-reasoning]]: the model's final answer is determined by the biasing feature but the CoT is composed to justify it after the fact.
