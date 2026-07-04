---
aliases:
- Refusal threshold varies by unanswerability flavor
- same doubt dial, different alarm settings
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refusal-threshold-varies-by-unanswerability-flavor
  type: mechanism
  status: canonical
cause: "Regressing refuse/answer behavior on caution boundary distance jointly with unanswerability flavor (942 eligible generations, instruction-tuned checkpoint on the AH surface)."
effect: "Refusal is one curve in boundary distance (AUROC 0.956) but flavors sit at significantly different trigger thresholds (offset p=0.004, no slope interaction p=0.35): future-unknown questions are refused 93 percent vs ~68 percent for controversial/unsolved, and confabulation concentrates in the lenient flavors (31-33 percent vs 7 percent)."
polarity: mediates
related:
- '[[internal-flavor-geometry--category-fleet]]'
- '[[unanswerability-detection-shares-one-axis-across-flavors]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[penalty-lambda-controls-abstention-threshold]]'
- '[[known-unknowns-taxonomy]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[internal-flavor-geometry--category-fleet]]'
  target_id: paper:internal-flavor-geometry
  confidence: high
- type: related_to
  target: '[[unanswerability-detection-shares-one-axis-across-flavors]]'
  target_id: mechanism:unanswerability-detection-shares-one-axis-across-flavors
  confidence: high
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: medium
- type: related_to
  target: '[[penalty-lambda-controls-abstention-threshold]]'
  target_id: mechanism:penalty-lambda-controls-abstention-threshold
  confidence: medium
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
---

Session-0036 pliability arm. The behavior model is a single internal doubt reading
passed through per-flavor trigger points: no evidence the slope (how behavior tracks
doubt) differs by flavor, strong evidence the intercept does. The practical
consequence is that confabulation risk is flavor-structured even at matched internal
doubt: the flavors the model is most willing to gamble on (controversial, unsolved
problem) are exactly where it fabricates 4x more. For deployment readouts this
argues for per-flavor operating points on one shared gate rather than separate
gates.
