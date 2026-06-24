---
aliases:
- linear direction intervention
- vector arithmetic intervention
- residual stream steering
- Activation Intervention via Vector Arithmetic
tags:
- kg/method
- concept
- method
kg:
  id: method:activation-intervention
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[linear-probe]]'
- '[[residual-stream]]'
- '[[steering-vector]]'
- '[[activation-addition]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: variation_of
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

Activation intervention modifies a model's internal belief state by adding a linear probe direction vector to the [[residual-stream]] at every layer during a forward pass, following the update x' = x + alpha * p, where p is the probe direction for a target concept and alpha is an intervention strength scalar. Unlike gradient-based activation editing or iterative optimization methods, the intervention requires only a single vector addition per layer. It was notably used in OthelloGPT studies to test whether probed board-state directions causally govern the model's move predictions, not merely correlate with them.

**Why it matters here:** Activation intervention is the causal-verification complement to correlational probing for epistemic-humility features: adding or subtracting a [[known-unknown-direction]] or [[truth-direction]] vector tests whether the model's abstention behavior is mechanistically controlled by that direction, not just associated with it.

**Lineage:** a variation of [[linear-probe]] from correlational to causal use; closely related to [[activation-addition]] and [[steering-vector]] (which operate on the same residual-stream additive principle); grounded in the [[linear-representation-hypothesis]].
