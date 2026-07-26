---
aliases:
- SAE Benign Feature Steering Breaks Alignment Comparable to Random
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-benign-feature-steering-breaks-alignment-comparable-to-random
  type: mechanism
  status: canonical
cause: "Steering along semantically benign [[sparse-autoencoder]] feature directions (e.g. 'modal verbs', 'brand identity'), not directions selected for any harm-related meaning"
effect: "Harmful compliance rises 1-4% higher than matched random-direction steering; 817/1000 tested SAE features jailbreak at least one prompt, with the most potent features generalizing poorly across harm categories"
polarity: enables
related:
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
- '[[sparse-autoencoder]]'
- '[[random-direction-steering-breaks-alignment-safeguards]]'
relationships:
- type: supported_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
  confidence: high
- type: related_to
  target: '[[random-direction-steering-breaks-alignment-safeguards]]'
  target_id: mechanism:random-direction-steering-breaks-alignment-safeguards
  confidence: high
---

Steering along interpretable, semantically benign SAE feature directions (identified via Goodfire's SAE trained on layer 19 of Llama3.1-8B) is comparably dangerous to steering along fully random directions: it yields 1-4% higher harmful compliance than matched random steering, and 817 of 1000 tested SAE features jailbreak at least one harmful prompt (arXiv:2509.22067, Fig. 5, Sec 4.2-4.3). The most potent jailbreaking features (e.g. "modal verbs", "brand identity") are themselves semantically unrelated to harm and generalize poorly across harm categories, undermining the assumption that interpretable, benign-looking steering directions are safe.
