---
aliases:
- OT
- Overthinking
tags:
- kg/term
- concept
- term
kg:
  id: term:overthinking
  type: term
  status: canonical
area: verification
introduced-by: "[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]"
related:
- '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2605.05715--decodable-but-not-corrected-fixed-residual-stream]]'
  target_id: paper:2605.05715
  confidence: high
---

Overthinking (OT) is a stable behavioral failure regime (Jaccard >= 0.81, 94% inter-annotator agreement) in which a model answers a question correctly under resampling (e.g., self-consistency, best-of-N) yet fails when it reasons over an extended chain-of-thought on the same instance.

**Why it matters here:** OT is the case study [[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] uses to probe the classification-correction gap: the OT signal is linearly decodable from the residual stream at 71.6% accuracy, yet fixed linear steering families cannot exploit that decodability to correct the failure.

**Lineage:** proposed and operationalized in arXiv:2605.05715 for medical QA (MedQA) and replicated cross-domain on MMLU-STEM.
