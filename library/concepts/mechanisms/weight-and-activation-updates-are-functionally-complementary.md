---
aliases:
- Weight and activation updates provide complementary functions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:weight-and-activation-updates-are-functionally-complementary
  type: mechanism
  status: canonical
cause: "Weight updates alter the model's transformation while [[post-block-activation-steering]] adds an input-dependent residual correction."
effect: "Joint adaptation can represent useful changes that either update space alone does not capture."
polarity: enables
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[post-block-activation-steering]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[post-block-activation-steering]]'
  target_id: method:post-block-activation-steering
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

The paper derives first-order conditions that connect weight updates with
activation shifts, but also identifies functions available to only one update
space. The joint experiments support this complementarity by sometimes
exceeding both individual baselines.
