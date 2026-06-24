---
aliases:
- token-probability truth confound
- length-frequency probability confound
- LLM probability unreliable for veracity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sentence-probability-confounds-truth-detection
  type: mechanism
  status: canonical
cause: "LLM-assigned sentence probability depends on token frequency and sentence length as well as factual correctness"
effect: "Raw sentence probability is unreliable as a truth detector; short or lexically common false sentences can outscore longer true sentences, and normalization helps only partially"
polarity: prevents
related:
- '[[2304.13734--internal-state-knows-lying]]'
- '[[saplma]]'
- '[[hallucination]]'
- '[[verbalized-confidence]]'
- '[[p-ik-ood-generalization-gap]]'
relationships:
- type: supported_by
  target: '[[2304.13734--internal-state-knows-lying]]'
  target_id: paper:2304.13734
  confidence: high
- type: related_to
  target: '[[saplma]]'
  target_id: method:saplma
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
---

Azaria and Mitchell (2304.13734) show that the It-is-true normalization baseline achieves only 55.9% average accuracy on externally generated sentences (Table 1), barely above random, while SAPLMA achieves 71.0%. The paper gives concrete examples in Table 5 and Section 6: 'The Earth is flat like a pancake' receives high probability because the phrase appears in training data, while 'Jennifer Aniston is a female person' (an implicit truth never stated in training) receives low probability despite being correct. This demonstrates that token probability conflates familiarity with correctness in a way that hidden-state probes avoid, and motivates using calibrated internal-state signals rather than output distributions for veracity assessment.
