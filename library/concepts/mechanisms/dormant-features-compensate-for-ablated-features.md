---
aliases:
- Dormant Features Compensate When Primary Features Are Ablated
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dormant-features-compensate-for-ablated-features
  type: mechanism
  status: canonical
cause: "Ablation of the primary active causal [[sparse-autoencoder|SAE]] refusal feature set, removing their contribution to the [[refusal-direction]]"
effect: "Previously zero-activation (dormant) SAE features switch on and partially restore refusal, preventing the minimal primary set alone from fully jailbreaking the model (77 dormant compensating features for LLaMA, 1656 for Gemma)"
polarity: prevents
related:
- '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
- '[[sparse-autoencoder]]'
- '[[refusal-hydra-effect]]'
- '[[refusal-direction]]'
relationships:
- type: supported_by
  target: '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
  target_id: paper:2509.09708
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[refusal-hydra-effect]]'
  target_id: term:refusal-hydra-effect
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
---

Refusal is not fully concentrated in a single primary feature set: ablating the primary causal features activates previously dormant SAE features that partially reconstruct the refusal signal, a pattern consistent with the [[refusal-hydra-effect]]. The beyond-sorry paper (arXiv:2509.09708) documents 77 such compensating dormant features for LLaMA and 1656 for Gemma, explaining why minimal primary ablations achieve only partial jailbreaking and why Gemma is more robust than LLaMA. This distributed redundancy implies that robust jailbreaking requires ablating both the primary and the compensating feature sets, substantially increasing the attack complexity.
