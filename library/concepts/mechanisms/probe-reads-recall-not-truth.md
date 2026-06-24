---
aliases:
- internal states reflect recall not truthfulness
- hidden states capture knowledge utilization not correctness
- recall-truthfulness conflation in probes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:probe-reads-recall-not-truth
  type: mechanism
  status: canonical
cause: "LLMs use the same subject-driven information-flow pathway (early-layer subject-token MLP activations \u2192 mid-layer attention propagation \u2192 late-layer last-token accumulation) for both factually correct outputs and associated hallucinations, because both emerge from parametric associations triggered by the input subject."
effect: "Hidden-state probes and black-box confidence signals effectively detect unassociated hallucinations (AUROC 0.81-0.93) but cannot distinguish associated hallucinations from factual outputs (AUROC 0.46-0.69, with black-box baselines at near-chance), because the two categories are geometrically overlapping in activation space by layer 25."
polarity: prevents
related:
- '[[2510.09033--probes-read-recall-not-truth]]'
- '[[ah-uh-hallucination-taxonomy]]'
- '[[associated-hallucination]]'
- '[[unassociated-hallucination]]'
- '[[linear-probe]]'
- '[[causal-intervention]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
- '[[generation-discrimination-gap]]'
relationships:
- type: supported_by
  target: '[[2510.09033--probes-read-recall-not-truth]]'
  target_id: paper:2510.09033
  confidence: high
- type: related_to
  target: '[[ah-uh-hallucination-taxonomy]]'
  target_id: term:ah-uh-hallucination-taxonomy
  confidence: high
- type: related_to
  target: '[[associated-hallucination]]'
  target_id: term:associated-hallucination
  confidence: high
- type: related_to
  target: '[[unassociated-hallucination]]'
  target_id: term:unassociated-hallucination
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: high
---

Causal mediation analysis on LLaMA-3-8B and Mistral-7B-v0.3 shows that interventions on subject-token MLP representations, attention flow from subject to last token, and last-token hidden states all produce large JS-divergence shifts for both FAs and AHs but small shifts for UHs. As a result, last-token hidden states at layer 25 show cosine similarity dropping to approximately 0.2 for FAs and AHs (reflecting subject-specific dispersion) while UHs remain at approximately 0.5 (reflecting clustered, subject-independent representations). Probes trained on this signal read recall structure, not truth, so they reliably identify UHs (which bypass the recall pathway) but cannot identify AHs (which follow it). This is not a failure of a specific probe design but a structural property of how factual errors arise.
