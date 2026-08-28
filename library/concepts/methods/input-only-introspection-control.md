---
aliases:
- layer-0 introspection baseline
- input-only hidden-label baseline
- semantic shortcut control for self-report
tags:
- kg/method
- concept
- method
kg:
  id: method:input-only-introspection-control
  type: method
  status: canonical
area: verification
related:
- '[[2605.26242--can-llms-introspect-reality-check]]'
- '[[privileged-access-condition]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2605.26242--can-llms-introspect-reality-check]]'
  target_id: paper:2605.26242
  confidence: high
- type: related_to
  target: '[[privileged-access-condition]]'
  target_id: term:privileged-access-condition
  confidence: high
- type: variation_of
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

The input-only introspection control predicts hidden-state-derived labels from uncontextualized layer-0 embeddings or removes semantic correlations by randomizing labels before the hidden-state proxy is fit. If these baselines match the model's self-report performance, the task does not require privileged access to the later state that defined the label.

**Why it matters here:** It tests whether apparent self-monitoring is instead ordinary prediction from visible semantic features.

**Lineage:** The method applies [[linear-probe]] and label-randomization controls to the [[privileged-access-condition]] for introspection claims.
