---
aliases:
- Layer-0 features explain hidden-label prediction
- Semantic correlates imitate activation self-report
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:input-semantic-shortcuts-mimic-hidden-state-self-report
  type: mechanism
  status: canonical
cause: "Hidden-state-derived labels remain correlated with semantic, lexical, or entity features present in the model's input embeddings."
effect: "A model or input-only probe predicts those labels without privileged access to the later hidden state used to construct them."
polarity: enables
related:
- '[[2605.26242--can-llms-introspect-reality-check]]'
- '[[input-only-introspection-control]]'
- '[[privileged-access-condition]]'
relationships:
- type: supported_by
  target: '[[2605.26242--can-llms-introspect-reality-check]]'
  target_id: paper:2605.26242
  confidence: high
- type: related_to
  target: '[[input-only-introspection-control]]'
  target_id: method:input-only-introspection-control
  confidence: high
- type: related_to
  target: '[[privileged-access-condition]]'
  target_id: term:privileged-access-condition
  confidence: high
---

Layer-0 probes matched or exceeded in-context prediction for PCA-derived and Belief Dominance labels. Randomly relabeling the supervised proxy removed its semantic alignment and reduced performance near the majority baseline, supporting an input-shortcut explanation for the tested self-report tasks.
