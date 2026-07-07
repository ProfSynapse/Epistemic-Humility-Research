---
aliases:
- Unverbalized reasoning steps live in the global workspace and causally drive the final answer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:global-workspace-mediates-intermediate-reasoning-steps
  type: mechanism
  status: canonical
cause: "An intermediate, never-verbalized computational step in a multi-hop reasoning chain (e.g. the identity implied by a definitional clue) is represented in the model's J-space"
effect: "swapping that intermediate step's J-lens vector for a different concept's causally changes the model's final answer, succeeding on 54% of trials on Claude Haiku 4.5, 70% on Claude Sonnet 4.5, and 70% on Claude Opus 4.5, and taking effect roughly 17% earlier in the layer stack than swaps of the final-answer token itself"
polarity: mediates
related:
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[global-workspace]]'
- '[[jacobian-lens]]'
- '[[claude-sonnet-4-5]]'
- '[[claude-haiku-4-5]]'
- '[[claude-opus-4-5]]'
relationships:
- type: supported_by
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: high
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[claude-sonnet-4-5]]'
  target_id: model:claude-sonnet-4-5
  confidence: medium
- type: related_to
  target: '[[claude-haiku-4-5]]'
  target_id: model:claude-haiku-4-5
  confidence: medium
- type: related_to
  target: '[[claude-opus-4-5]]'
  target_id: model:claude-opus-4-5
  confidence: medium
---

On two-hop factual-recall prompts (e.g. "The number of legs on the animal that
spins webs is"), an intermediate concept the model never verbalizes (spider)
is nonetheless present in its [[global-workspace]] and causally mediates the
final answer: swapping that intermediate concept's [[jacobian-lens]] vector
for another's (spider -> ant) changes the emitted answer accordingly (8 -> 6,
Figure 13). Lens-coordinate swaps on this construction succeed on 54% of
trials on Claude Haiku 4.5, 70% on Claude Sonnet 4.5, and 70% on Claude Opus
4.5 (Figure 15), and the intermediate-concept swap takes effect roughly 17%
earlier in the layer stack than a swap of the final-answer token, consistent
with the intermediate step being computed and represented before the final
answer is settled (Figure 15). The J-space component of a probe for this
intermediate step flips the final answer on 61% of trials versus 28% for the
probe's non-J-space component (Figure 16).
