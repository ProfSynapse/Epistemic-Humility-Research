---
aliases:
- Abstention Inflation
tags:
- kg/term
- concept
- term
kg:
  id: term:abstention-inflation
  type: term
  status: canonical
area: terms
related:
- '[[2507.16199--llm-abstention-can-be-prompt-artifact-addition]]'
- '[[extra-option-structurally-triggers-abstention]]'
- '[[instruction-tuning-installs-abstention-inflation-bias]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2507.16199--llm-abstention-can-be-prompt-artifact-addition]]'
  target_id: paper:2507.16199
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[extra-option-structurally-triggers-abstention]]'
  target_id: mechanism:extra-option-structurally-triggers-abstention
  confidence: high
- type: related_to
  target: '[[instruction-tuning-installs-abstention-inflation-bias]]'
  target_id: mechanism:instruction-tuning-installs-abstention-inflation-bias
  confidence: high
---

Ling et al. (2025) name "Abstention Inflation" the phenomenon where an LLM abstains not because of genuine uncertainty about the answer but because a prompt contains a structural cue (an extra "Unknown"-like option) that the model has learned to treat as an abstention slot, even on questions it can answer correctly without that option present.

**Why it matters here:** Abstention Inflation is the sharpest evidence that at least some measured "abstention" is a prompt artifact rather than a calibration signal, directly relevant to interpreting any prompted-abstention baseline used alongside SFT/DPO/KTO-trained abstention: a prompted "Unknown" option in an eval harness can inflate apparent abstention independent of whether the underlying uncertainty is genuine, so trained-vs-prompted comparisons need to control for this structural trigger, not just wording.
