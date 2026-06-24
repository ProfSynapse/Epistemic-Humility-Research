---
aliases:
- Instruction-tuned base doubles TruthfulQA gain
- Base-model amplification of alignment truthfulness
- Instruction tuning primes alignment for truthfulness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuned-base-amplifies-alignment-truthfulness-gain
  type: mechanism
  status: canonical
cause: "Using an instruction-tuned model (rather than a raw pre-trained or SFT-warmed model) as the starting point for RL-free alignment fine-tuning (DPO, KTO, IPO, CPO)"
effect: "TruthfulQA gains from alignment are approximately doubled relative to starting from a pre-trained base: KTO and IPO each add roughly 17.5 percentage points over the SFT baseline (49.46% to 66.97%) vs roughly 9.5 percentage points from the pre-trained base (43.73% to 52.98%)"
polarity: increases
related:
- '[[2404.14723--insights-into-alignment-dpo-variants]]'
- '[[kahneman-tversky-optimization]]'
- '[[identity-preference-optimization]]'
- '[[direct-preference-optimization]]'
- '[[contrastive-preference-optimization]]'
- '[[instruction-tuning]]'
- '[[supervised-finetuning]]'
- '[[truthfulqa]]'
- '[[instruction-tuning-improves-self-knowledge]]'
- '[[truthfulness-helpfulness-tradeoff-under-activation-steering]]'
relationships:
- type: supported_by
  target: '[[2404.14723--insights-into-alignment-dpo-variants]]'
  target_id: paper:2404.14723
  confidence: high
- type: related_to
  target: '[[kahneman-tversky-optimization]]'
  target_id: method:kahneman-tversky-optimization
  confidence: high
- type: related_to
  target: '[[identity-preference-optimization]]'
  target_id: method:identity-preference-optimization
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[contrastive-preference-optimization]]'
  target_id: method:contrastive-preference-optimization
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: high
- type: related_to
  target: '[[instruction-tuning-improves-self-knowledge]]'
  target_id: mechanism:instruction-tuning-improves-self-knowledge
  confidence: high
- type: related_to
  target: '[[truthfulness-helpfulness-tradeoff-under-activation-steering]]'
  target_id: mechanism:truthfulness-helpfulness-tradeoff-under-activation-steering
  confidence: high
---

Saeidi et al. (2024, Tables 3 and 9) show that applying the same alignment methods to Mistral-Instruct-7B-v0.2 instead of Mistral-7B-v0.1 produces roughly 2x larger TruthfulQA improvements. The effect is specific to truthfulness: reasoning (Table 2) and MMLU (Table 3) show similar ordering across scenarios, with no comparable amplification. The instruction-tuned base likely provides a richer internal representation of what constitutes a true vs false claim, giving alignment a better signal to optimize against. This finding extends instruction-tuning-improves-self-knowledge beyond unanswerable-question detection to factual truthfulness under alignment, and contextualizes the known effect from inference-time-intervention, where instruction-tuned models (Alpaca, Vicuna) showed larger ITI gains than base models.
