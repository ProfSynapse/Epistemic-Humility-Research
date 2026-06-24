---
aliases:
- calibration plot
- confidence calibration diagram
- reliability plot
tags:
- kg/term
- concept
- term
kg:
  id: term:reliability-diagram
  type: term
  status: canonical
area: terms
related:
- '[[1706.04599--on-calibration-of-modern-neural-networks]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[temperature-scaling]]'
relationships:
- type: proposed_by
  target: '[[1706.04599--on-calibration-of-modern-neural-networks]]'
  target_id: paper:1706.04599
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[temperature-scaling]]'
  target_id: method:temperature-scaling
  confidence: medium
---

A visual calibration diagnostic that plots empirical accuracy as a function of predicted confidence, grouping predictions into equally-spaced or equal-frequency bins. A perfectly calibrated model produces the identity diagonal; bars above the diagonal indicate underconfidence and bars below indicate overconfidence. Gap bars (shaded red) show the per-bin miscalibration magnitude.

**Why it matters here:** Reliability diagrams are the standard visual accompaniment to ECE in calibration papers and a useful diagnostic for checking whether SFT, DPO, or KTO training distorts the confidence-accuracy relationship in a particular regime (e.g., high-confidence predictions).

**Lineage:** Formalized by DeGroot and Fienberg (1983); popularized in neural network calibration by Niculescu-Mizil and Caruana (2005) and Guo et al. (arXiv:1706.04599, Figure 1, Figure 4). Companion to [[expected-calibration-error]] as a scalar summary.
