---
aliases:
- In-context learning adds new demonstration-attending heads to the circuit
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:icl-adds-demonstration-attending-heads
  type: mechanism
  status: canonical
cause: Provision of few-shot demonstrations (in-context learning)
effect: New attention heads emerge in the knowledge circuit that attend to the demonstration context, enabling correction of previously incorrect answers
polarity: enables
related:
- '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
- '[[in-context-learning]]'
- '[[knowledge-circuits]]'
- '[[mover-head]]'
relationships:
- type: supported_by
  target: '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
  target_id: paper:2405.17969
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
- type: related_to
  target: '[[knowledge-circuits]]'
  target_id: term:knowledge-circuits
- type: related_to
  target: '[[mover-head]]'
  target_id: term:mover-head
---

Circuit analysis comparing zero-shot and few-shot prompts reveals that [[in-context-learning]] augments rather than replaces the base knowledge circuit: new attention heads appear that attend specifically to the in-context demonstration examples, enabling the model to correct answers it would otherwise get wrong (arXiv:2405.17969). These demonstration-attending heads integrate with existing [[mover-head]] machinery to route contextually provided information to the prediction position. The additive circuit structure explains why ICL can override parametric knowledge without disrupting the underlying factual-recall mechanism.
