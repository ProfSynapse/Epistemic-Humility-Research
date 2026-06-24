---
aliases:
- per-sample cluster-size reward
- fine-grained confidence reward for abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fine-grained-semantic-confidence-reward
  type: mechanism
  status: canonical
cause: "Replacing a coarse global entropy reward with a per-sample cluster-size-based confidence reward within GRPO abstention training (FiSCoRe)"
effect: "OOD reliability (F1_rel) is substantially higher than GRPO with coarse entropy reward and SFT baselines, while in-domain reliability is competitive; reward hacking via universal abstention is prevented by the accuracy auxiliary"
polarity: increases
related:
- '[[2510.24020--fiscore-semantic-confidence-reward]]'
- '[[group-relative-policy-optimization]]'
- '[[bidirectional-entailment-clustering]]'
- '[[semantic-entropy]]'
- '[[sft-abstention-overfits-indomain]]'
- '[[abstention-generalization-failure]]'
- '[[rlhf-generalisation-advantage-scales-with-shift-severity]]'
- '[[fiscore]]'
- '[[f1-rel-reliability-metric]]'
relationships:
- type: supported_by
  target: '[[2510.24020--fiscore-semantic-confidence-reward]]'
  target_id: paper:2510.24020
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[bidirectional-entailment-clustering]]'
  target_id: method:bidirectional-entailment-clustering
  confidence: high
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: high
- type: related_to
  target: '[[sft-abstention-overfits-indomain]]'
  target_id: mechanism:sft-abstention-overfits-indomain
  confidence: high
- type: related_to
  target: '[[abstention-generalization-failure]]'
  target_id: mechanism:abstention-generalization-failure
  confidence: high
- type: related_to
  target: '[[rlhf-generalisation-advantage-scales-with-shift-severity]]'
  target_id: mechanism:rlhf-generalisation-advantage-scales-with-shift-severity
  confidence: high
- type: related_to
  target: '[[fiscore]]'
  target_id: method:fiscore
  confidence: high
- type: related_to
  target: '[[f1-rel-reliability-metric]]'
  target_id: metric:f1-rel-reliability-metric
  confidence: high
---

During GRPO training, FiSCoRe generates G=10 rollouts per question and clusters them by bidirectional NLI entailment into semantic equivalence classes. Each rollout receives a confidence reward of 1 if the model's verbalized 'sure'/'unsure' output matches whether that rollout's cluster exceeds threshold tau=5, and 0 otherwise. This per-sample signal resolves the ambiguity in coarse global entropy (where one borderline entropy score is assigned uniformly to all rollouts), giving the model a clearer, sample-specific training gradient. The GRPO-SE vs FiSCoRe comparison on Qwen2.5-7B-Instruct TriviaQA (F1_rel 72.0 vs 81.1) isolates this reward granularity as the causal variable, since architecture, data, and optimizer are identical.
