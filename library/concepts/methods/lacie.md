---
aliases:
- Listener-Aware Calibration for Implicit and Explicit confidence
- listener-aware finetuning
- LACIE finetuning
tags:
- kg/method
- concept
- method
kg:
  id: method:lacie
  type: method
  status: canonical
area: methods
related:
- '[[2405.21028--lacie-listener-aware-calibration]]'
- '[[direct-preference-optimization]]'
- '[[low-rank-adaptation]]'
- '[[verbalized-confidence]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[abstention]]'
- '[[triviaqa]]'
- '[[truthfulqa]]'
- '[[dpo-reduces-over-abstention]]'
- '[[ternary-reward-enables-abstention-over-hallucination]]'
relationships:
- type: proposed_by
  target: '[[2405.21028--lacie-listener-aware-calibration]]'
  target_id: paper:2405.21028
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[dpo-reduces-over-abstention]]'
  target_id: mechanism:dpo-reduces-over-abstention
  confidence: medium
- type: related_to
  target: '[[ternary-reward-enables-abstention-over-hallucination]]'
  target_id: mechanism:ternary-reward-enables-abstention-over-hallucination
  confidence: medium
---

A DPO-based finetuning method that calibrates LLM confidence by running a two-agent speaker-listener game: the speaker model generates diverse long-form answers, a simulated listener model scores whether each sounds convincing, and a conservative preference function (rewarding true-accepts and true-rejects equally, penalizing false-accepts more than false-rejects) builds training pairs for DPO. The method targets both implicit confidence cues (tone, detail, backstory) and explicit markers (numeric scores, epistemic hedges). Trained with QLoRA rank-16, at most 250 DPO steps, on 13,785 TriviaQA preference pairs.

**Why it matters here:** Establishes the strongest published DPO calibration baseline for listener-induced AUROC and human false-acceptance rate; shows a conservative preference ordering produces large emergent abstention gains without any abstention training data, providing a direct performance target and ablation structure for the locked training-regimen SFT/DPO/KTO comparison.

**Lineage:** Builds on direct-preference-optimization (Rafailov et al. 2024) and RSA pragmatics modeling (Frank and Goodman 2012); extends truthful-only DPO with a listener-acceptance signal; evaluated against verbalized-confidence and epistemic-marker calibration baselines.
