---
aliases:
- Knowledge circuit isolation preserves substantial model performance
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:knowledge-circuit-isolation-preserves-performance
  type: mechanism
  status: canonical
cause: Using only the sparse knowledge circuit subgraph (less than 10% of full graph) in isolation
effect: Model maintains more than 70% of its original factual-recall performance (Hit@10); some relations improve, e.g. Landmark-country from 0.16 to 0.36
polarity: enables
related:
- '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
- '[[knowledge-circuits]]'
- '[[hit-at-10]]'
- '[[automated-circuit-discovery]]'
relationships:
- type: supported_by
  target: '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
  target_id: paper:2405.17969
  confidence: high
- type: related_to
  target: '[[knowledge-circuits]]'
  target_id: term:knowledge-circuits
- type: related_to
  target: '[[hit-at-10]]'
  target_id: metric:hit-at-10
- type: related_to
  target: '[[automated-circuit-discovery]]'
  target_id: method:automated-circuit-discovery
---

[[knowledge-circuits]] are sparse subgraphs of the full transformer computation graph identified via automated circuit discovery; despite comprising less than 10% of all nodes, running the model with only the circuit subgraph active preserves more than 70% of original factual-recall performance measured by [[hit-at-10]] (arXiv:2405.17969). For some relational categories the isolated circuit actually outperforms the full model (Landmark-country: 0.16 -> 0.36), suggesting that non-circuit components introduce noise or interference for those relations. This supports the claim that factual knowledge is localized to compact, functionally sufficient subnetworks rather than being diffusely distributed.
