---
aliases:
- false-option rejection
- false option rejection
- None of the above selection
- NOTA selection
- reject option
tags:
- kg/term
- concept
- term
kg:
  id: term:false-option-rejection
  type: term
  status: canonical
area: terms
related:
- '[[epistemic-humility]]'
- '[[abstention]]'
- '[[hallucination]]'
- '[[humblebench]]'
- '[[humility-score]]'
---

False-option rejection is the ability, in a forced-choice multiple-choice
setting, to reject every offered answer when none is supported by the evidence,
typically by selecting an explicit "None of the above" (NOTA) option. It is the
narrow, directly observable behavioral facet of [[epistemic-humility]] that
HumbleBench isolates, as distinct from calibrated uncertainty, confidence
calibration, or principled refusal in general. In the visual setting it requires a
model to reject plausible but visually unsupported object, attribute, or relation
choices rather than committing to one.

**Why it matters here:** Framing abstention as false-option rejection makes it
objectively measurable without an LLM judge: correctness reduces to whether the
model picked NOTA when it should. HumbleBench
([[2509.09658--humblebench-epistemic-humility-multimodal]]) shows models can score
well on recognition yet fail badly at false-option rejection, which is why it
reports the [[humility-score]] alongside accuracy.

**Lineage:** an operational facet of [[epistemic-humility]]; measured by
[[humility-score]]; the failure to do it is a form of [[hallucination]].
