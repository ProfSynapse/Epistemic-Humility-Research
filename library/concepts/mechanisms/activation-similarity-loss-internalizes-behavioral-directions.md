---
aliases:
- Cosine activation loss tunes a behavioral vector into model weights
- Residual-stream alignment loss internalizes steering directions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:activation-similarity-loss-internalizes-behavioral-directions
  type: mechanism
  status: canonical
cause: "Fine-tuning penalizes cosine distance between selected residual-stream activations and a contrastively derived behavioral direction, alongside a token loss."
effect: "The trained model expresses the direction's behavior without online activation injection."
polarity: enables
related:
- '[[2409.06927--representation-tuning]]'
- '[[representation-tuning]]'
- '[[cosine-similarity]]'
relationships:
- type: supported_by
  target: '[[2409.06927--representation-tuning]]'
  target_id: paper:2409.06927
  confidence: high
- type: related_to
  target: '[[representation-tuning]]'
  target_id: method:representation-tuning
  confidence: high
- type: related_to
  target: '[[cosine-similarity]]'
  target_id: metric:cosine-similarity
  confidence: high
---

The paper tunes Llama-2-13B-Chat at selected attention modules in layers 11 through 17. The joint cosine and token objective moves activations toward honesty or dishonesty vectors and changes model behavior after the intervention hook is removed.
