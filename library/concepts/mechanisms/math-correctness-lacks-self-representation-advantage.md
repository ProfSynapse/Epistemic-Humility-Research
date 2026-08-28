---
aliases:
- Mathematical correctness has no privileged probe premium
- Peer representations match self probes on math disagreements
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:math-correctness-lacks-self-representation-advantage
  type: mechanism
  status: canonical
cause: "Self and peer probes predict target-model correctness on MATH and GSM1K, including items where their correctness labels disagree."
effect: "The target representation shows no consistent AUC advantage over the tested external representations at any probed depth."
polarity: decouples
related:
- '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
- '[[privileged-correctness-knowledge]]'
- '[[premium-gap]]'
relationships:
- type: supported_by
  target: '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
  target_id: paper:2604.12373
  confidence: high
- type: related_to
  target: '[[privileged-correctness-knowledge]]'
  target_id: term:privileged-correctness-knowledge
  confidence: high
- type: related_to
  target: '[[premium-gap]]'
  target_id: metric:premium-gap
  confidence: high
---

On mathematical disagreement subsets, external probes matched or exceeded self probes under both linear and MLP classifiers. MATH gaps fluctuated near zero, while GSM1K gaps were predominantly negative. This null is scoped to the tested models, tasks, question representations, and probe classes.
