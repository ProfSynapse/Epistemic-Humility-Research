---
aliases:
- Self-Ask Prompting Induces Overconfidence on Unknown Questions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-ask-induces-overconfidence
  type: mechanism
  status: canonical
cause: '[[self-ask-prompting]], which asks the model to answer first before classifying a question as known/unknown'
effect: Reduced classification accuracy on the known-vs-unknown task compared to zero-shot, because models always attempt an answer and become overconfident in the result
polarity: decreases
related:
- '[[2305.13712--kuq-knowledge-of-knowledge]]'
- '[[self-ask-prompting]]'
relationships:
- type: supported_by
  target: '[[2305.13712--kuq-knowledge-of-knowledge]]'
  target_id: paper:2305.13712
  confidence: high
- type: related_to
  target: '[[self-ask-prompting]]'
  target_id: method:self-ask-prompting
---

When a model generates an answer before evaluating whether the question is within its knowledge, the act of generation anchors the model toward treating the produced answer as correct. This self-generated prior inflates confidence and leads the model to classify the question as "known" more frequently than is warranted. The KUQ paper (arXiv:2305.13712) documents this as a systematic failure of self-ask prompting that makes it counterproductive for [[known-unknowns-taxonomy|known-unknown]] discrimination.
