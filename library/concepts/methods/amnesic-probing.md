---
aliases:
- Amnesic Counterfactuals
- amnesic intervention
tags:
- kg/method
- concept
- method
kg:
  id: method:amnesic-probing
  type: method
  status: canonical
area: methods
introduced-by: "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
related:
- "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
- "[[linear-probe]]"
- "[[inlp]]"
relationships:
- type: proposed_by
  target: "[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]"
  target_id: paper:2006.00995
  confidence: high
- type: derived_from
  target: "[[linear-probe]]"
  target_id: method:linear-probe
- type: derived_from
  target: "[[inlp]]"
  target_id: method:inlp
---

Amnesic probing is a counterfactual method for measuring the causal utility of an
encoded property Z for a downstream task T. It projects a layer's hidden states
into the nullspace of a linear probe for Z (using INLP) and then runs the model
forward from that edited state, measuring how much task performance drops. Unlike
standard probing, which asks only whether Z is linearly decodable, amnesic probing
asks whether the model actually uses Z when performing T.

**Why it matters here:** The probe-behavior gap is central to epistemic-humility
research: a model may encode its own uncertainty reliably (high probe accuracy on
the known-unknown axis) yet never consult that signal when generating its answer.
Amnesic probing provides the causal instrument needed to distinguish these two
cases, informing whether interventions must target the readout channel rather than
the representation itself.

**Lineage:** derives from [[linear-probe]] and [[inlp]]; the causal framing
motivates [[probing-accuracy-task-importance-disconnect]] as a documented failure
mode of purely correlational probing.
