---
aliases:
- GPT Discards Input Representation After First Layer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gpt-input-discarded-immediately
  type: mechanism
  status: canonical
cause: Autoregressive next-token prediction objective requiring conversion of input token representations to predicted-output representations
effect: After the very first transformer layer, intermediate activations are already far closer in KL divergence to the final output distribution than to the input token distribution -- input space is discarded discontinuously rather than gradually
polarity: enables
related:
- '[[ll2020--interpreting-gpt-the-logit-lens]]'
- '[[gpt-2]]'
- '[[logit-lens]]'
- '[[input-discarding]]'
- '[[kl-divergence]]'
relationships:
- type: supported_by
  target: '[[ll2020--interpreting-gpt-the-logit-lens]]'
  target_id: paper:ll2020
  confidence: high
- type: related_to
  target: '[[gpt-2]]'
  target_id: model:gpt-2
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[input-discarding]]'
  target_id: term:input-discarding
---

Nostalgebraist (ll2020) applies the logit lens to GPT-2 and finds that after only the first transformer layer the residual stream's implied token distribution has already moved decisively away from the input token and toward the model's final next-token prediction. KL divergence from the input token peaks at layer one and then falls monotonically, while KL divergence from the final output falls throughout. This abrupt, discontinuous discarding of input identity in the earliest layer reveals that GPT immediately reframes its representation in terms of the prediction task.
