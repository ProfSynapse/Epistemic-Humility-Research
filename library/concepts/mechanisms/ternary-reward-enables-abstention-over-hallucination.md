---
aliases:
- ternary grading separates abstention from hallucination
- three-way reward creates abstention gradient
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ternary-reward-enables-abstention-over-hallucination
  type: mechanism
  status: canonical
cause: "A ternary reward (+1 correct, 0 abstain, -1 hallucinate) inside GRPO's group-relative advantage estimation"
effect: "Abstention receives strictly higher group-relative advantage than hallucination in groups where no correct answer is sampled, producing a policy gradient that preferentially converts hallucinations into abstentions"
polarity: enables
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[binary-grading-reinforces-hallucination]]'
- '[[ternary-reward-design]]'
- '[[truthrl]]'
- '[[group-relative-policy-optimization]]'
- '[[abstention]]'
- '[[hallucination]]'
- '[[over-abstention]]'
relationships:
- type: supported_by
  target: '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
  target_id: paper:2509.25760
  confidence: high
- type: related_to
  target: '[[binary-grading-reinforces-hallucination]]'
  target_id: mechanism:binary-grading-reinforces-hallucination
  confidence: high
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: high
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: high
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: high
---

Under binary reward both abstention and hallucination receive -1; within a GRPO group their advantages are equal and the policy has no signal to prefer abstention. Under ternary reward, abstention receives 0 and hallucination -1; even when no group member answers correctly, abstention has a positive advantage relative to hallucination. Table 3 confirms: ternary TruthRL reaches T=37.2/H=19.4 on CRAG versus binary T=20.8/H=39.5. The effect generalizes across four benchmarks and five model sizes (Tables 1, 7).
