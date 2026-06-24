---
aliases:
- UH
- unassociated hallucinations
- knowledge-detached hallucination
tags:
- kg/term
- concept
- term
kg:
  id: term:unassociated-hallucination
  type: term
  status: canonical
area: terms
related:
- '[[2510.09033--probes-read-recall-not-truth]]'
- '[[associated-hallucination]]'
- '[[hallucination]]'
- '[[ah-uh-hallucination-taxonomy]]'
- '[[probe-reads-recall-not-truth]]'
- '[[knowledge-boundary]]'
- '[[popqa]]'
relationships:
- type: proposed_by
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: high
- type: related_to
  target: '[[associated-hallucination]]'
  target_id: term:associated-hallucination
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[ah-uh-hallucination-taxonomy]]'
  target_id: term:ah-uh-hallucination-taxonomy
  confidence: medium
- type: related_to
  target: '[[probe-reads-recall-not-truth]]'
  target_id: mechanism:probe-reads-recall-not-truth
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: medium
---

A factual error produced without reliance on parametric associations to the input subject. The model's internal information flow is weak on the standard subject-to-last-token pathway, yielding subject-token norms approximately 4% below FA baseline at layer 1 and diverging further through mid-layers, clustered last-token representations (cosine similarity approximately 0.5 vs approximately 0.2 for FAs by layer 25), and high-entropy output distributions.

**Why it matters here:** UHs are the easy case for hallucination detection: internal probes and black-box methods all reach 0.81-0.93 AUROC because UH last-token states form a compact cluster in representation space. UH samples also support refusal-tuning generalization (82% refusal ratio on held-out UHs). UHs dominate low-popularity subjects, reflecting gaps in parametric knowledge encoding during pretraining.

**Lineage:** Introduced and operationalized in Cheang et al. (2510.09033); the mechanism connecting subject-popularity to UH prevalence connects to PopQA (Mallen et al. 2023) work on when not to trust language models.
