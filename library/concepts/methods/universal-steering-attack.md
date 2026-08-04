---
aliases:
- universal jailbreak vector
- aggregated random-direction attack
- weaponized random steering
tags:
- kg/method
- concept
- method
kg:
  id: method:universal-steering-attack
  type: method
  status: canonical
area: methods
related:
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
- '[[activation-steering]]'
- '[[steering-vector]]'
relationships:
- type: proposed_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Universal steering attack averages 20 randomly sampled direction vectors that each successfully jailbreak a single fixed prompt into one aggregated vector, which then generalizes to jailbreak unseen prompts. It is fully black-box: it needs only steering access and observed model outputs on one harmful prompt, no gradients, logits, or model weights, and no harmful training data.

**Why it matters here:** demonstrates that random-direction steering vulnerabilities compose into a practical, transferable jailbreak: the aggregated vector roughly quadruples harmful compliance over matched random steering (e.g. 50.4% on Llama3.1-70B; 5.7% to 63.4% on Falcon3-7B) on unseen JailbreakBench prompts, though effectiveness is model-dependent (reduced on Qwen2.5-32B).

**Lineage:** built directly on [[activation-steering]]; aggregates individually weak random [[steering-vector]]s into a single potent attack vector rather than optimizing a targeted direction.
