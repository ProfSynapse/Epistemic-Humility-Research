---
aliases:
- parameter sharing increases input-dependent depth use
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:parameter-sharing-increases-input-dependent-depth-use
  type: mechanism
  status: canonical
cause: "tying parameters across layers (universal-transformer-style weight sharing, as in MoEUT) instead of using a stack of distinct, layer-specific weights."
effect: "the effective computational depth a given input recruits becomes more input-dependent, since the same shared weights can be reapplied a variable number of times rather than depth being fixed by a static count of distinct parameter blocks."
polarity: increases
related:
- '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
- '[[moeut]]'
relationships:
- type: supported_by
  target: '[[2505.13898--do-language-models-use-their-depth-efficiently]]'
  target_id: paper:2505.13898
  confidence: medium
- type: related_to
  target: '[[moeut]]'
  target_id: method:moeut
  confidence: high
---

Csordás et al. include a parameter-shared architecture ([[moeut]]) alongside
standard non-tied models when analyzing depth use. Because a weight-tied model
applies the same block repeatedly rather than a fixed sequence of distinct
layers, the amount of computation an input actually recruits is decoupled from
a static layer count and can vary more with the input itself, in contrast to
the largely input-independent depth budget the paper finds in standard
architectures.

**Lineage:** contrasts with
[[second-half-layers-refine-without-composing]] and
[[depth-scaling-spreads-computation-rather-than-composing-new]], both of which
describe fixed, non-tied stacks; [[moeut]] is the architecture instantiating
the parameter sharing this mechanism describes.
