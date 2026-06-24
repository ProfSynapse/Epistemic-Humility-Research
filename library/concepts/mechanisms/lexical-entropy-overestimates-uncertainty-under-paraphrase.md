---
aliases:
- paraphrase inflation in entropy
- semantic equivalence entropy bias
- token-entropy paraphrase inflation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lexical-entropy-overestimates-uncertainty-under-paraphrase
  type: mechanism
  status: canonical
cause: "Computing predictive entropy over token sequences when the model generates multiple semantically equivalent paraphrases of a single correct answer"
effect: "Entropy is inflated relative to genuine semantic uncertainty, causing the model to appear more uncertain about questions it effectively knows, and degrading AUROC of uncertainty-based abstention or selective classification"
polarity: increases
related:
- '[[2302.09664--semantic-uncertainty-kuhn]]'
- '[[semantic-entropy]]'
- '[[semantic-equivalence]]'
- '[[bidirectional-entailment-clustering]]'
- '[[dominant-uncertainty-source-shifts-with-model-scale]]'
relationships:
- type: supported_by
  target: '[[2302.09664--semantic-uncertainty-kuhn]]'
  target_id: paper:2302.09664
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: high
- type: related_to
  target: '[[semantic-equivalence]]'
  target_id: term:semantic-equivalence
  confidence: high
- type: related_to
  target: '[[bidirectional-entailment-clustering]]'
  target_id: method:bidirectional-entailment-clustering
  confidence: high
- type: related_to
  target: '[[dominant-uncertainty-source-shifts-with-model-scale]]'
  target_id: mechanism:dominant-uncertainty-source-shifts-with-model-scale
  confidence: high
---

In free-form NLG, many token sequences can express the same meaning. When a model samples M answers to a question it effectively knows, a substantial fraction of those samples will be paraphrases of the same meaning. Standard predictive entropy treats each unique token sequence as a distinct outcome, assigning high entropy to a distribution that is actually concentrated on one meaning. Semantic entropy corrects this by clustering semantically equivalent sequences and summing their likelihoods before computing entropy, recovering a lower and more accurate uncertainty estimate. Empirically, this correction yields AUROC gains of 2-5 points on TriviaQA and CoQA with OPT models, and the gains widen with model size as larger models generate more fluent and diverse paraphrases.
