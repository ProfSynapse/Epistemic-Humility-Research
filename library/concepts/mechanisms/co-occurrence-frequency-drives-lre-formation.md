---
aliases:
- Co-occurrence frequency drives LRE formation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:co-occurrence-frequency-drives-lre-formation
  type: mechanism
  status: canonical
cause: "High [[subject-object-co-occurrence-frequency]] between a subject entity and its relational object in pretraining data"
effect: "Formation of high-quality (high causality) [[linear-relation-embedding|linear relational embeddings]] for that factual relation, as measured by LRE causality scores"
polarity: increases
related:
- '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
- '[[linear-relation-embedding]]'
- '[[subject-object-co-occurrence-frequency]]'
- '[[pretraining-co-occurrence-threshold]]'
relationships:
- type: supported_by
  target: '[[2504.12459--linear-representations-pretraining-data-frequency-language-models]]'
  target_id: paper:2504.12459
  confidence: high
- type: related_to
  target: '[[linear-relation-embedding]]'
  target_id: method:linear-relation-embedding
- type: related_to
  target: '[[subject-object-co-occurrence-frequency]]'
  target_id: term:subject-object-co-occurrence-frequency
- type: related_to
  target: '[[pretraining-co-occurrence-threshold]]'
  target_id: term:pretraining-co-occurrence-threshold
---

Linear relational embeddings capture the mapping from a subject representation to an object representation for a factual relation via a single weight matrix. The LRE quality (causality score) is predicted by how often the subject and object co-occur in the pretraining corpus: relations with high co-occurrence yield high-causality LREs while rare co-occurrences yield unreliable or non-causal mappings (arXiv:2504.12459). This finding situates LRE formation as a data-driven process shaped by the statistical structure of the training corpus rather than an architectural property of the transformer.
