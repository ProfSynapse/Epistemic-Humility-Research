---
aliases:
- residual sharpening in final layers grows norm and orients toward the output
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:late-layer-residual-sharpening-grows-norm-toward-unembedding
  type: mechanism
  status: canonical
cause: "final-layer suppression neurons dominating during the residual-sharpening stage."
effect: "MLP-output norm rises and logit entropy falls, producing a large late-layer residual displacement oriented toward the unembedding basis."
polarity: increases
related:
- '[[2406.19384--remarkable-robustness-llms-stages-inference]]'
- '[[stages-of-inference]]'
- '[[residual-stream-refinement]]'
relationships:
- type: supported_by
  target: '[[2406.19384--remarkable-robustness-llms-stages-inference]]'
  target_id: paper:2406.19384
  confidence: high
- type: related_to
  target: '[[stages-of-inference]]'
  target_id: term:stages-of-inference
  confidence: high
- type: related_to
  target: '[[residual-stream-refinement]]'
  target_id: term:residual-stream-refinement
  confidence: medium
---

Lad et al. show that in the final layers rising MLP-output norm and falling
entropy mark a residual-sharpening stage in which suppression neurons finalize
the output distribution, so a large late-layer displacement pointing toward the
unembedding is expected structure rather than an anomaly; middle layers are by
contrast robust and near-interchangeable.
