---
aliases:
- faithful uncertainty expression
- uncertainty faithful to intrinsic uncertainty
- expressed-intrinsic uncertainty alignment
tags:
- kg/term
- concept
- term
kg:
  id: term:faithful-uncertainty
  type: term
  status: canonical
area: terms
related:
- '[[2605.01428--hallucinations-undermine-trust-metacognition]]'
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[faithful-calibration]]'
- '[[self-knowledge]]'
- '[[hallucination]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2605.01428--hallucinations-undermine-trust-metacognition]]'
  target_id: paper:2605.01428
  confidence: high
- type: studied_by
  target: '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
  target_id: paper:2606.32032
  confidence: high
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
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

Faithful uncertainty is the idea that a model's expressed uncertainty should track its intrinsic uncertainty rather than merely sounding cautious or confident as a stylistic policy. It reframes hallucination as a trust problem: the most damaging failures are often not just wrong answers, but wrong answers delivered with unwarranted certainty.

**Why it matters here:** The concept motivates training and evaluation targets beyond hard abstention. A model can serve users better by distinguishing confident answers, explicit uncertainty, and abstention, especially when search or deferral is available.

**Lineage:** proposed as a position framing in [[2605.01428--hallucinations-undermine-trust-metacognition]] and operationalized through faithful-calibration training in [[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]].
