---
aliases:
- LACIE human transfer
- simulated listener calibration generalizes to humans
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lacie-listener-aware-calibration-transfers-to-humans
  type: mechanism
  status: canonical
cause: "DPO finetuning with a simulated LLM listener scoring speaker answer acceptance (LACIE training)"
effect: "Human annotators accept 47% fewer incorrect answers from the trained model without significantly increasing rejection of correct answers, improving human-judged precision by 15 points"
polarity: enables
related:
- '[[2405.21028--lacie-listener-aware-calibration]]'
- '[[lacie]]'
- '[[direct-preference-optimization]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[verbalized-confidence]]'
relationships:
- type: supported_by
  target: '[[2405.21028--lacie-listener-aware-calibration]]'
  target_id: paper:2405.21028
  confidence: high
- type: related_to
  target: '[[lacie]]'
  target_id: method:lacie
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
---

Training with a Mistral-7B listener model as the acceptance signal produces confidence expression patterns that real human listeners read correctly. In a human study (n=79 base / n=78 LACIE items), Mistral-7B+LACIE produced 17 false accepts versus 32 for the base model (47% reduction, p<0.05 McNemar's test), with false rejections increasing by only 1 (6 to 7, p=1.0 not significant). Human precision rose from 0.49 to 0.64. The transfer holds because LACIE optimizes over both implicit cues (tone, detail level) and explicit epistemic markers, the same cues human listeners use. (Table 2, Section 4.3)
