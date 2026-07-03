---
aliases:
- Persona vector projection enables pre-generation trait monitoring
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:persona-projection-enables-pre-generation-monitoring
  type: mechanism
  status: canonical
cause: "Projecting the final prompt-token activation onto a [[persona-vectors|persona vector]] before generation begins, using the cosine similarity as a trait propensity score"
effect: "Strong prediction of trait expression in the subsequent response (r=0.75 to 0.83), enabling deployment-time monitoring without waiting for output tokens"
polarity: enables
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
- '[[persona-vectors]]'
- '[[representation-reading]]'
- '[[representation-engineering]]'
relationships:
- type: supported_by
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[representation-reading]]'
  target_id: method:representation-reading
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
---

Before the model generates a single output token, the prompt encoding already carries reliable information about which character traits will be expressed in the response. The cosine projection of the final prompt-token hidden state onto each persona vector predicts trait expression scores with correlations of r=0.75 to 0.83 across held-out prompts (arXiv:2507.21509). This pre-generation readout enables a deployment-time safety monitor that can flag or reject potentially harmful responses before they are produced, removing the latency of waiting for full generation.
