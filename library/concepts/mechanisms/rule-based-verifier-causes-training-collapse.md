---
aliases:
- string-match verifier causes over-abstention
- rule-based reward collapses to abstention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rule-based-verifier-causes-training-collapse
  type: mechanism
  status: canonical
cause: "Using string-match (rule-based) answer verification as the reward signal in GRPO training for open-domain QA"
effect: "Model collapses into near-total abstention (T=-3.6, H=3.6) because paraphrase-correct answers are systematically misclassified as wrong, starving the policy of genuine positive reward and making abstention the only strategy with non-negative expected return"
polarity: enables
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[ternary-reward-enables-abstention-over-hallucination]]'
- '[[truthrl]]'
- '[[over-abstention]]'
- '[[llm-as-judge]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
  target_id: paper:2509.25760
  confidence: high
- type: related_to
  target: '[[ternary-reward-enables-abstention-over-hallucination]]'
  target_id: mechanism:ternary-reward-enables-abstention-over-hallucination
  confidence: high
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
---

String matching misclassifies semantically correct but lexically variant answers as hallucinations. Under ternary reward this means abstentions (0) reliably dominate attempted answers (-1), driving the model toward universal abstention. Table 5: rule-based T=-3.6/H=3.6 vs. LLM-based T=37.2/H=19.4. This is a practical failure mode for any RL-based truthfulness training that uses deterministic string verification rather than semantic matching.
