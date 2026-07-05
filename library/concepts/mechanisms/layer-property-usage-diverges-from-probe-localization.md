---
aliases:
- Layer Property Usage Diverges from Probe Localization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layer-property-usage-diverges-from-probe-localization
  type: mechanism
  status: canonical
cause: "Applying amnesic intervention at intermediate BERT layers versus reading probe accuracy at those layers"
effect: "Different and sometimes opposing layer-importance orderings: POS is most causally impactful at layer 11 under non-masked setting (-41 pts) while probing accuracy is high and flat across all layers (>80%), contradicting standard pipeline localization hypotheses"
polarity: prevents
related:
- '[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]'
- '[[amnesic-probing]]'
- '[[linear-probe]]'
- '[[layer-wise-property-importance]]'
relationships:
- type: supported_by
  target: '[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]'
  target_id: paper:2006.00995
  confidence: high
- type: related_to
  target: '[[amnesic-probing]]'
  target_id: method:amnesic-probing
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[layer-wise-property-importance]]'
  target_id: term:layer-wise-property-importance
contradicted-by: []
---

Standard [[linear-probe]] accuracy is high and roughly flat across BERT layers for POS tags, suggesting the property is uniformly encoded. Yet [[amnesic-probing]] shows causal impact peaks sharply at layer 11 (-41 pts LM accuracy upon erasure in the non-masked setting), with other layers showing little or no effect. This divergence means that where a property is linearly readable and where it is causally used are distinct questions, and pipeline-style localization based on probing accuracy alone yields misleading layer attributions. The finding is documented in arXiv:2006.00995.
