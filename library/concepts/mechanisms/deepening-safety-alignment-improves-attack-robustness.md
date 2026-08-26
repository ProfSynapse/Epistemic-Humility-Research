---
aliases:
- Safety-recovery data augmentation improves robustness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:deepening-safety-alignment-improves-attack-robustness
  type: mechanism
  status: canonical
cause: "Augmenting SFT data with safety-recovery examples that continue a harmful-looking prefix with a refusal, extending the depth of the token positions over which the model is trained to be safe, beyond just the first few tokens"
effect: "Attack success rate drops sharply across inference-time exploits (prefilling, GCG adversarial suffixes, decoding-parameter manipulation) and the model shows improved durability against fine-tuning attacks"
polarity: decreases
related:
- '[[2406.05946--safety-alignment-should-be-made-more-than]]'
- '[[shallow-safety-alignment]]'
- '[[safety-alignment-concentrates-on-first-output-tokens]]'
relationships:
- type: supported_by
  target: '[[2406.05946--safety-alignment-should-be-made-more-than]]'
  target_id: paper:2406.05946
  confidence: high
- type: related_to
  target: '[[shallow-safety-alignment]]'
  target_id: term:shallow-safety-alignment
  confidence: high
- type: related_to
  target: '[[safety-alignment-concentrates-on-first-output-tokens]]'
  target_id: mechanism:safety-alignment-concentrates-on-first-output-tokens
  confidence: high
---

Comparing the initial Llama-2-7B-Chat model against a version fine-tuned with safety-recovery data augmentation, attack success rate (ASR) on HEx-PHI prefilling attacks drops from 42.1%/51.5%/56.1%/57.0% (at 5/10/20/40 forced tokens respectively) to 2.8%/2.9%/3.4%/4.5%; GCG adversarial-suffix ASR drops from 36.5% (HEx-PHI) / 65.6% (AdvBench) to 18.4% / 19.0%; and decoding-parameter exploit ASR drops from 54.9% (HEx-PHI) / 84.3% (MaliciousInstruct) to 11.3% / 1.0% (Table 2, Section 3.2). The augmented model also shows better durability against downstream fine-tuning attacks. Qi et al. (2024) present this as a counterfactual demonstrating that shallow safety alignment is a fixable root cause: training safety behavior into more than just the first few tokens meaningfully closes these vulnerabilities.
