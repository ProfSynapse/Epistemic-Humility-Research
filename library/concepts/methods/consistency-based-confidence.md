---
aliases:
- self-consistency confidence
- induced consistency
- answer consistency
- Consistency-Based Confidence
tags:
- kg/method
- concept
- method
kg:
  id: method:consistency-based-confidence
  type: method
  status: canonical
area: methods
related:
- '[[verbalized-confidence]]'
- '[[confidence-elicitation]]'
- '[[self-consistency]]'
relationships:
- type: variation_of
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
---

Consistency-based confidence is a family of uncertainty estimation methods that sample multiple responses from an LLM and use the degree of agreement across those responses as a proxy for model confidence, without requiring the model to explicitly state a probability. High agreement across samples implies high confidence; diverging answers signal uncertainty. The approach is black-box, requiring only repeated sampling rather than logit access or internal state inspection.

**Why it matters here:** Because abstention decisions ideally track genuine model uncertainty, consistency-based signals offer a way to detect knowledge gaps without fine-tuning, making them relevant to calibration studies across SFT, DPO, and KTO checkpoints.

**Lineage:** variant of [[verbalized-confidence]]; related to [[self-consistency]] and the broader [[confidence-elicitation]] family.
