---
aliases:
- privileged self-access requirement
- input-unrecoverable internal information condition
- introspection privileged-access test
tags:
- kg/term
- concept
- term
kg:
  id: term:privileged-access-condition
  type: term
  status: canonical
area: verification
related:
- '[[2605.26242--can-llms-introspect-reality-check]]'
- '[[introspective-awareness]]'
- '[[input-only-introspection-control]]'
- '[[second-order-computation-condition]]'
relationships:
- type: proposed_by
  target: '[[2605.26242--can-llms-introspect-reality-check]]'
  target_id: paper:2605.26242
  confidence: high
- type: required_by
  target: '[[introspective-awareness]]'
  target_id: term:introspective-awareness
  confidence: high
- type: measured_by
  target: '[[input-only-introspection-control]]'
  target_id: method:input-only-introspection-control
  confidence: high
- type: related_to
  target: '[[second-order-computation-condition]]'
  target_id: term:second-order-computation-condition
  confidence: high
---

The privileged-access condition requires an introspection task to depend on internal information that cannot be recovered from the input alone. A label may be derived from a hidden state yet fail this condition when semantic or lexical input features predict the same label.

**Why it matters here:** It separates access to a model-specific state from ordinary input-driven self-prediction.

**Lineage:** The [[input-only-introspection-control]] tests this condition. The paper treats it as necessary but insufficient without the [[second-order-computation-condition]].
