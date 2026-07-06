---
aliases:
- cMFG*
- equal-mass cMFG*
- refined cMFG*
- width-weighted cMFG*
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:cmfg-star-equal-mass
  type: metric
  status: canonical
area: metrics
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[cmfg-star]]'
- '[[faithful-calibration]]'
- '[[brier-score]]'
- '[[consistency-based-confidence]]'
relationships:
- type: proposed_by
  target: '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
  target_id: paper:2606.32032
  confidence: high
- type: related_to
  target: '[[cmfg-star]]'
  target_id: metric:cmfg-star
  confidence: medium
  note: "Same surface name but a distinct equal-mass/bin-width formulation in this paper."
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: high
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: high
---

The equal-mass `cMFG*` metric refines conditional mean faithful generation by sorting examples by intrinsic confidence, partitioning them into equal-mass bins, and weighting each bin by its width on the intrinsic-confidence axis. It is intended to remove empty-bin artifacts and avoid penalizing models whose intrinsic-confidence support occupies only part of the full 0-1 range.

**Why it matters here:** This metric is the paper's main faithful-calibration score and is distinct from ordinary factual calibration metrics such as [[brier-score]].

**Lineage:** A refinement of cMFG for faithful calibration. It shares the `cMFG*` surface name with [[cmfg-star]] in the vault, but this note preserves the paper-specific equal-mass/bin-width formulation to avoid conflating two different metrics.
