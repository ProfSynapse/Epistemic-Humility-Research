---
aliases:
- Per-flavor doubt residuals persist beyond the shared trunk
- doubt trunk with flavor branches
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:flavor-specific-doubt-residuals-persist
  type: mechanism
  status: canonical
cause: "Projecting the shared known/unknown trunk direction out of each unanswerability flavor's whitened doubt direction (L20/24/28, raw instruct base)."
effect: "Each flavor retains 20-42 percent of its direction norm, and that residual alone still separates the flavor's unknowns from knowns at 0.69-0.91 AUROC; per-flavor directions align at only ~0.71 mean whitened cosine, with counterfactual the outlier both ways (cosine 0.575, strongest residual 0.91)."
polarity: enables
related:
- '[[internal-flavor-geometry--category-fleet]]'
- '[[unanswerability-detection-shares-one-axis-across-flavors]]'
- '[[refusal-directions-are-geometrically-distinct]]'
- '[[refusal-concept-cone]]'
- '[[known-unknowns-taxonomy]]'
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
  target: '[[refusal-directions-are-geometrically-distinct]]'
  target_id: mechanism:refusal-directions-are-geometrically-distinct
  confidence: medium
- type: related_to
  target: '[[refusal-concept-cone]]'
  target_id: term:refusal-concept-cone
  confidence: medium
- type: related_to
  target: '[[known-unknowns-taxonomy]]'
  target_id: term:known-unknowns-taxonomy
  confidence: high
---

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

Session-0036 category-geometry arm. The complement of the one-axis detection result:
the shared trunk carries the answerable/unanswerable judgment, but each flavor
arrives at it from its own angle and keeps a discriminative fingerprint after the
trunk is removed. This is the compound-caution prediction at the flavor level (a
shared core plus flavor-specific components) and it nominates concrete steering
targets, with the counterfactual residual the most distinct. Caveat from the same
arm: the known/unknown split is also a dataset split, which affects trunk magnitude
but not the between-flavor structure. The item-22a follow-up showed these residuals
are near-collinear re-expressions of one doubt geometry for predicting behavior, so
treat them as accents on the trunk, not independent factors.
