---
aliases:
- Representation rerouting disrupts harmful generation across attacks
- Circuit breakers generalize across jailbreak attacks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:representation-rerouting-disrupts-harmful-generation-across-attacks
  type: mechanism
  status: canonical
cause: "Low-rank adapters reroute representations produced during harmful response trajectories away from their frozen-model directions."
effect: "Harmful generation and action compliance decrease across unseen text, image, embedding, representation, and function-calling attacks."
polarity: prevents
related:
- '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
- '[[representation-rerouting]]'
- '[[harmbench]]'
relationships:
- type: supported_by
  target: '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
  target_id: paper:2406.04313
  confidence: high
- type: related_to
  target: '[[representation-rerouting]]'
  target_id: method:representation-rerouting
  confidence: high
- type: related_to
  target: '[[harmbench]]'
  target_id: dataset:harmbench
  confidence: high
---

RR lowered average HarmBench compliance from 76.7% to 9.8% for Mistral-7B-Instruct-v2 and from 38.1% to 3.8% for Llama-3-8B-Instruct. The reported scope is harmful-content generation and does not cover arbitrary adversarial misclassification.
