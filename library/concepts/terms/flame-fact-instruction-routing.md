---
aliases:
- fact-based instruction classification
- instruction type classification
- factual instruction routing
tags:
- kg/term
- concept
- term
kg:
  id: term:flame-fact-instruction-routing
  type: term
  status: canonical
area: terms
related:
- '[[2405.01525--flame-factuality-aware-alignment]]'
- '[[flame-factuality-aware-alignment]]'
- '[[instruction-tuning]]'
- '[[hallucination]]'
- '[[factscore]]'
relationships:
- type: proposed_by
  target: '[[2405.01525--flame-factuality-aware-alignment]]'
  target_id: paper:2405.01525
  confidence: high
- type: related_to
  target: '[[flame-factuality-aware-alignment]]'
  target_id: method:flame-factuality-aware-alignment
  confidence: medium
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: medium
---

A step in FLAME that prompts an SFT model to classify each instruction as fact-requiring or not, then applies different supervision strategies (self-generated PT responses vs human responses for SFT; factuality preference pairs only for fact-requiring inputs in DPO) based on the label.

**Why it matters here:** Ablation shows this routing is necessary: removing it drops Alpaca Eval win rate by 3.6 points and Bio FActScore by 1.1 points, because naive application of self-generation or factuality preference pairs to all instructions harms non-factual tasks.

**Lineage:** Novel to FLAME; extends the observation from the pilot study that factual alignment strategy should be conditioned on whether the instruction demands factual content.
