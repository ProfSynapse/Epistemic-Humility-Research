---
aliases:
- factuality tuning style degradation
- DPO factuality tone shift
- factuality alignment tax
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:factuality-style-cost
  type: mechanism
  status: canonical
cause: "DPO fine-tuning on factuality preference pairs (FactTune-FS or FactTune-MC)"
effect: "Generation style shifts toward terse, objective prose and away from conversational or narrative tone, rated as less conversational by GPT-4 in a majority of samples"
polarity: mediates
related:
- '[[2311.08401--finetuning-for-factuality]]'
- '[[alignment-tax]]'
- '[[direct-preference-optimization]]'
- '[[facttune-fs]]'
- '[[facttune-mc]]'
- '[[hallucination]]'
- '[[over-hedging]]'
relationships:
- type: supported_by
  target: '[[2311.08401--finetuning-for-factuality]]'
  target_id: paper:2311.08401
  confidence: high
- type: related_to
  target: '[[alignment-tax]]'
  target_id: term:alignment-tax
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[facttune-fs]]'
  target_id: method:facttune-fs
  confidence: high
- type: related_to
  target: '[[facttune-mc]]'
  target_id: method:facttune-mc
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[over-hedging]]'
  target_id: term:over-hedging
  confidence: high
---

When DPO optimizes for factual accuracy by preferring completions with fewer unverified claims, the model learns to avoid hedged, anecdotal, or conversational elaboration, since such text often contains speculative or stylistically inflated content that scores lower on automated factuality metrics. The result is a qualitative style shift that users perceive as less engaging even when the factual content improves. This is the closest analogue in this paper to the alignment tax: no capability benchmark regresses, but generation style changes in ways that matter for deployment. Tian et al. measure it as GPT-4 preference ratings: 77.5% of Llama-1 samples and 65.6% of Llama-2 samples rated less conversational post-FactTune-FS (Section 4.1).
