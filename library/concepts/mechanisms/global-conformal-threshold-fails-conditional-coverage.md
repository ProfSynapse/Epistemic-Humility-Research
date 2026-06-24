---
aliases:
- marginal-only conformal miscalibrates heterogeneous categories
- global quantile threshold coverage failure
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:global-conformal-threshold-fails-conditional-coverage
  type: mechanism
  status: canonical
cause: "A single globally calibrated conformal threshold applied uniformly across heterogeneous prompt categories"
effect: "Systematic over-coverage in easier categories (more claims filtered than necessary) and under-coverage in harder categories (factually incorrect claims retained)"
polarity: prevents
related:
- '[[2604.13991--adaptive-conformal-factuality]]'
- '[[adaptive-conformal-factuality]]'
- '[[conditional-coverage]]'
- '[[calibration]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2604.13991--adaptive-conformal-factuality]]'
  target_id: paper:2604.13991
  confidence: high
- type: related_to
  target: '[[adaptive-conformal-factuality]]'
  target_id: method:adaptive-conformal-factuality
  confidence: high
- type: related_to
  target: '[[conditional-coverage]]'
  target_id: term:conditional-coverage
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
---

When a conformal threshold is calibrated jointly across categories with substantially different nonconformity score distributions, the single quantile cannot match the conditional quantile for each category separately. Harder categories (e.g., Inventions, Landmarks, Events, Artworks) tend to have higher nonconformity scores; a joint quantile that achieves global target coverage is too permissive for these and too strict for easier categories. The effect is empirically confirmed across three LLM families in this paper: for Mistral 7B the Landmarks category reaches only 73.49% coverage against an 80% target, and for Gemma-3 12B the Artworks and Events categories reach 68.00% and 73.39% respectively. Adaptive score normalization via conditional quantile regression corrects this without sacrificing marginal guarantees.
