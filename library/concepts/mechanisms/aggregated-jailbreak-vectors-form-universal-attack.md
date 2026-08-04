---
aliases:
- Aggregated Jailbreak Vectors Form Universal Attack
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:aggregated-jailbreak-vectors-form-universal-attack
  type: mechanism
  status: canonical
cause: "Averaging 20 randomly sampled direction vectors that each jailbreak a single fixed prompt via [[universal-steering-attack]], using only black-box steering access and no harmful training data"
effect: "The aggregated vector generalizes to unseen JailbreakBench prompts, boosting harmful compliance roughly 4x over matched random steering (e.g. 50.4% on Llama3.1-70B; 5.7% to 63.4% on Falcon3-7B)"
polarity: enables
related:
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
- '[[universal-steering-attack]]'
- '[[jailbreakbench]]'
relationships:
- type: supported_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
- type: related_to
  target: '[[universal-steering-attack]]'
  target_id: method:universal-steering-attack
  confidence: high
- type: related_to
  target: '[[jailbreakbench]]'
  target_id: dataset:jailbreakbench
  confidence: high
---

Averaging together just 20 randomly sampled steering vectors, each of which was found to jailbreak a single fixed harmful prompt, produces a single aggregated vector that generalizes to unseen prompts: it boosts harmful compliance roughly 4x over matched random steering on JailbreakBench (e.g. 50.4% on Llama3.1-70B, double the random rate; 5.7% to 63.4% on Falcon3-7B, nearly 10x) (arXiv:2509.22067, Fig. 7, Sec 4.4). The attack requires only black-box steering access and knowledge of a single harmful prompt, no gradients, logits, model weights, or harmful training data, though its effectiveness is model-dependent (reduced on Qwen2.5-32B).
