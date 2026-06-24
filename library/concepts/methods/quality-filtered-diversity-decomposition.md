---
aliases:
- D_all vs D_correct decomposition
- quality-control vs genuine-narrowing decomposition
tags:
- kg/method
- concept
- method
kg:
  id: method:quality-filtered-diversity-decomposition
  type: method
  status: canonical
area: methods
related:
- '[[2604.16027--posttraining-diversity-collapse]]'
- '[[output-diversity-collapse]]'
- '[[vendi-score]]'
- '[[self-consistency]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2604.16027--posttraining-diversity-collapse]]'
  target_id: paper:2604.16027
  confidence: high
- type: related_to
  target: '[[output-diversity-collapse]]'
  target_id: term:output-diversity-collapse
  confidence: medium
- type: related_to
  target: '[[vendi-score]]'
  target_id: metric:vendi-score
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
---

A measurement method that separates aggregate diversity reduction (D_all: SBERT on all K outputs) into a quality-control component (removal of incorrect outputs) and a residual genuine-narrowing component (D_correct: SBERT on the K_correct >= 2 correct outputs). The gap D_all - D_correct reflects diversity from error variety; D_correct captures homogenization among correct solutions. Analogous Vendi scores V_all and V_correct are computed over the same splits.

**Why it matters here:** Resolves the ambiguity between 'diversity collapse is harmful' and 'it is just quality control'. On some tasks nearly all narrowing reflects error removal; on others most is genuine homogenization that limits majority-voting gains.

**Lineage:** Introduced by Karouzos et al. (2604.16027) on six verifiable tasks (GSM8K, MATH-Algebra, MATH-Geometry, HumanEval, MBPP, IFEval).
