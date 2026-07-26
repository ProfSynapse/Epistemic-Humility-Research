---
aliases:
- Middle Repeat
- middle-layer weight sharing
tags:
- kg/method
- concept
- method
kg:
  id: method:middle-layer-repeat
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[layer-skipping]]'
relationships:
- type: proposed_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: medium
- type: related_to
  target: '[[layer-skipping]]'
  target_id: method:layer-skipping
---

Middle Repeat replaces a contiguous span of a frozen pretrained transformer's
middle layers with N copies of a single layer's weights -- typically the
center layer of the span -- so the same transformation is applied repeatedly
in place of the original distinct layers, holding the total layer count
constant.

**Why it matters here:** Middle Repeat is the sharpest test of whether middle
layers are truly redundant or merely share a compatible representation space:
because it collapses benchmark performance to random-baseline levels far
faster than skipping the same layers, it shows middle layers are not
functionally interchangeable copies of each other despite sharing a common
representation space.

**Lineage:** proposed in arXiv:2407.09298 as a contrast condition against
[[layer-skipping|layer skipping]] on the same layer spans.
