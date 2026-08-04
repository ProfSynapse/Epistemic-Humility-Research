---
aliases:
- Random Direction Steering Breaks Alignment Safeguards
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:random-direction-steering-breaks-alignment-safeguards
  type: mechanism
  status: canonical
cause: "Adding a random, semantically empty direction vector to the residual stream via [[activation-steering]], with no targeting of any refusal-related structure"
effect: "Harmful compliance rises from a 0% unsteered baseline to 1-13% across model families on [[jailbreakbench]] (up to 18% for Llama3.1-8B at c=2.0), with vulnerability concentrated in early and middle layers"
polarity: enables
related:
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
- '[[activation-steering]]'
- '[[jailbreakbench]]'
relationships:
- type: supported_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[jailbreakbench]]'
  target_id: dataset:jailbreakbench
  confidence: high
---

Steering a model's residual stream in a randomly sampled direction, with no semantic targeting of refusal or safety structure whatsoever, is sufficient on its own to break alignment safeguards: harmful compliance on JailbreakBench rises from 0% unsteered to 1-13% across Llama3.1, Qwen2.5, Falcon3, and FalconH1 families (up to 18% for Llama3.1-8B at coefficient 2.0), concentrated in early and middle layers (arXiv:2509.22067, Fig. 2, Sec 4.1). This shows alignment is fragile to arbitrary perturbation of the residual stream, not just to adversarially chosen directions.
