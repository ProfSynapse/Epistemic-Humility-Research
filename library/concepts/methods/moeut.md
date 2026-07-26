---
aliases:
- MoEUT
- Mixture-of-Experts Universal Transformer
tags:
- kg/method
- concept
- method
kg:
  id: method:moeut
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[causal-intervention]]'
relationships:
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
---

MoEUT (Mixture-of-Experts Universal Transformer) is a transformer variant that
ties parameters across layers in the style of a universal transformer -- the
same shared weights are applied at each computation step -- while using a
mixture-of-experts routing layer to give the shared block enough capacity to
remain competitive with a non-tied stack of distinct layers. Because the same
weights can be invoked a variable number of times per input, effective
computational depth is decoupled from the number of distinct parameter blocks.

**Why it matters here:** a parameter-shared architecture like MoEUT is used as
a contrast case to non-tied architectures when asking whether models use depth
efficiently, since shared weights make input-dependent depth use structurally
possible rather than merely a hypothesis about a fixed stack of layers.
