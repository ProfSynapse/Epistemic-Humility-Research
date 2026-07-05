---
aliases:
- probe-behavior gap
- probing limitations
- probing-performance uncorrelated to task importance
- Probing Accuracy / Task Importance Disconnect
tags:
- kg/term
- concept
- term
kg:
  id: term:probing-accuracy-task-importance-disconnect
  type: term
  status: canonical
area: verification
introduced-by: "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
related:
- "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
- "[[linear-probe]]"
- "[[amnesic-probing]]"
relationships:
- type: proposed_by
  target: "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
  target_id: paper:2006.00995
  confidence: high
- type: related_to
  target: "[[linear-probe]]"
  target_id: method:linear-probe
- type: related_to
  target: "[[amnesic-probing]]"
  target_id: method:amnesic-probing
---

The probing-accuracy/task-importance disconnect is the empirically demonstrated
phenomenon that a high linear-probe accuracy for property Z in a neural
representation does not imply that Z is causally used by the model when performing
task T. Standard probing conflates encoding (is Z decodable?) with usage (does the
model consult Z?), so behavioral or causal conclusions drawn from probe accuracy
alone are invalid.

**Why it matters here:** This disconnect is especially consequential for
epistemic-humility research: a model may achieve near-perfect decoding accuracy on
a known-unknown or uncertainty axis while that axis has zero causal influence on
whether the model answers or abstains. Recognizing the gap directs interventions
toward the readout channel (how the signal reaches the output) rather than the
representation itself, and motivates causal tools such as [[amnesic-probing]].

**Lineage:** named and evidenced in the amnesic-probing paper; [[amnesic-probing]]
is the primary method for detecting and quantifying this disconnect.
