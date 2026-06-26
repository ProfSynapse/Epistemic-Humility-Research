---
aliases:
- knowledge-awareness direction causally controls refusal vs hallucination
- steering the known/unknown-entity direction flips refusal and hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entity-recognition-direction-gates-refusal-vs-hallucination
  type: mechanism
  status: canonical
cause: "Adding or ablating the sparse-autoencoder entity-recognition (known vs unknown entity) direction in the residual stream during a factual query."
effect: "The model is driven to refuse questions about entities it knows, or to hallucinate attributes of entities it does not know when it would otherwise refuse."
polarity: mediates
related:
- '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
- '[[entity-recognition-direction]]'
- '[[refusal-direction]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
relationships:
- type: supported_by
  target: '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
  target_id: paper:2411.14257
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction]]'
  target_id: term:entity-recognition-direction
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
---

Ferrando et al. show the entity-recognition direction is not merely
correlational: steering with the "unknown entity" direction makes the model
refuse questions about entities it actually knows, and steering with the "known
entity" direction makes it hallucinate plausible attributes for entities it does
not know (Gemma 2 2B/9B). The same knowledge-awareness axis thus gates the
refuse-versus-attempt decision in both directions, behaving as a
knowledge-conditioned abstention control rather than a clean binary gate.
