---
aliases:
- Unanswerability flavor is an early content encoding
- flavor readable from layer 1
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unanswerability-flavor-is-early-content-encoding
  type: mechanism
  status: canonical
cause: "Probing the six KUQ-derived unanswerability flavors (ambiguous, controversial, unsolved problem, false assumption, future unknown, counterfactual) across all layers of a raw instruct base at the pre-generation anchor."
effect: "Flavor is linearly readable near ceiling from layer 1 (0.904 macro-OvR-AUROC, peaking 0.946 at L34, flat after L10), and a TF-IDF text baseline reaches 0.921: flavor is an early encoding of question content, not a late-computed epistemic judgment."
polarity: enables
related:
- '[[internal-flavor-geometry--category-fleet]]'
- '[[known-unknowns-taxonomy]]'
- '[[unanswerability-detection-shares-one-axis-across-flavors]]'
- '[[superposition-enables-early-layer-ngram-detection]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[internal-flavor-geometry--category-fleet]]'
  target_id: paper:internal-flavor-geometry
  confidence: high
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
- type: related_to
  target: '[[unanswerability-detection-shares-one-axis-across-flavors]]'
  target_id: mechanism:unanswerability-detection-shares-one-axis-across-flavors
  confidence: high
- type: related_to
  target: '[[superposition-enables-early-layer-ngram-detection]]'
  target_id: mechanism:superposition-enables-early-layer-ngram-detection
  confidence: low
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Session-0036 flavor-readout arm (raw Qwen3-4B base, 5,264 categorized unknowns,
L0-L36). The flavor probe hits 0.904 at layer 1 and gains little depth after L10;
most of the signal is recoverable from the question text itself (TF-IDF 0.921 vs
activation 0.946), and it holds within a single source dataset (0.953), so it is not
a source artifact. Reading: the model transcribes what kind of question it is seeing
as ordinary content, rather than diagnosing unanswerability type late. Confusion
structure is uneven: counterfactual and future-unknown are crisp (0.97), while
unsolved-problem smears into controversial (0.64 diagonal).
