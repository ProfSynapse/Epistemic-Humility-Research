---
aliases:
- Clustering question embeddings yields graded calibration targets
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:clustering-question-embeddings-yields-graded-calibration-targets
  type: mechanism
  status: canonical
cause: "Clustering normalized sentence embeddings of questions with HDBSCAN and assigning each input the target LLM's observed accuracy over its cluster as the calibration target."
effect: "Produces fine-grained, semantically coherent graded targets without LLM internals, and these train better calibrators than simple binary correct/incorrect targets."
polarity: increases
related:
- '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
- '[[clustering-derived-calibration-target]]'
- '[[apricot]]'
- '[[expected-calibration-error]]'
relationships:
- type: supported_by
  target: '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
  target_id: paper:2403.05973
  confidence: high
- type: related_to
  target: '[[clustering-derived-calibration-target]]'
  target_id: method:clustering-derived-calibration-target
  confidence: high
- type: related_to
  target: '[[apricot]]'
  target_id: method:apricot
  confidence: high
---

Ulmer et al. 2024 show clustered questions are far more semantically similar than
random pairs (within-cluster cosine .60/.70 vs ~.00 on TriviaQA/CoQA) and that
cluster-accuracy targets train better calibrators than binary correct/incorrect
targets for both Vicuna and GPT-3.5 on both datasets (Tables 2-3).
