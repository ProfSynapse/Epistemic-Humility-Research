---
aliases:
- Reasoning Effort Reduces Value Leakage
- longer CoT reduces value-leakage bias
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reasoning-effort-reduces-value-leakage
  type: mechanism
  status: canonical
cause: "Increasing reasoning effort or reasoning-trace length (e.g. Claude Opus max vs. high reasoning level) on the Donation Bet and Choosing Activities tasks."
effect: "Measured value-leakage bias decreases: in Donation Bet, most models show lower bias in longer-CoT buckets (Section 3, Figure 7), and Claude Opus 4.6/4.7/4.8 are less biased at max reasoning than at high reasoning; in Choosing Activities, Claude Opus 4.7/4.8 show high bias at lower effort levels (where many CoTs are empty) but no measurable bias at max reasoning (Section 9). The paper flags a selection-effect confound: models may reason longer specifically when an early estimate falls on the disfavored side of the threshold, so longer CoTs are disproportionately associated with initially-unfavorable (and thus lower measured bias) trajectories, weakening the causal reading (Appendix D.6)."
polarity: decreases
related:
- '[[2607.14345--value-leakage-llm-s-answers-silently-shaped]]'
- '[[covert-value-leakage]]'
- '[[model-values-covertly-bias-answers]]'
relationships:
- type: supported_by
  target: '[[2607.14345--value-leakage-llm-s-answers-silently-shaped]]'
  target_id: paper:2607.14345
  confidence: medium
- type: related_to
  target: '[[covert-value-leakage]]'
  target_id: term:covert-value-leakage
  confidence: high
- type: related_to
  target: '[[model-values-covertly-bias-answers]]'
  target_id: mechanism:model-values-covertly-bias-answers
  confidence: high
---

The paper explicitly does not claim this is a clean causal effect of
reasoning helping the model correct bias, since the selection-effect
alternative (models keep revising an estimate until it lands on the good
side, then stop, so the stopping point correlates with the final bias by
construction) is only partially ruled out. It is reported as a correlational
finding with a plausible but unconfirmed causal component, evidenced by the
max-vs-high reasoning-level comparison within the same Claude Opus model.
