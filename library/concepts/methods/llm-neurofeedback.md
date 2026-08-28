---
aliases:
- LLM neurofeedback
- Activation neurofeedback for language models
- Neurofeedback in-context learning
tags:
- kg/method
- concept
- method
kg:
  id: method:llm-neurofeedback
  type: method
  status: canonical
area: methods
related:
- '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
- '[[in-context-learning]]'
- '[[linear-probe]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
  target_id: paper:2505.13763
  confidence: high
- type: derived_from
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

LLM neurofeedback converts a residual-stream projection into a discrete label
and supplies sentence-label pairs as in-context examples. A reporting task asks
the model to predict a new activation label. Explicit and implicit control tasks
ask it to move later activations toward a target label.

**Why it matters here:** The method directly tests whether prompt-conditioned
model computation can report or influence selected internal activations. It
uses no parameter updates and does not install a permanent readout-to-action
connection in model weights.

**Lineage:** It combines [[in-context-learning]] with labels computed from
principal-component or [[linear-probe]] directions in the [[residual-stream]].
