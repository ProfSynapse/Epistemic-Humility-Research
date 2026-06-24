---
aliases:
- ThinkPack library
- thinkpack Python package
tags:
- kg/method
- concept
- method
kg:
  id: method:thinkpack
  type: method
  status: canonical
area: methods
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[reasoning-trace-collapse]]'
- '[[valid-reasoning-rate]]'
- '[[loss-masking-preserves-reasoning-traces]]'
- '[[low-rank-adaptation]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2605.21127--silent-reasoning-trace-suppression]]'
  target_id: paper:2605.21127
  confidence: high
- type: related_to
  target: '[[reasoning-trace-collapse]]'
  target_id: term:reasoning-trace-collapse
  confidence: medium
- type: related_to
  target: '[[valid-reasoning-rate]]'
  target_id: metric:valid-reasoning-rate
  confidence: medium
- type: related_to
  target: '[[loss-masking-preserves-reasoning-traces]]'
  target_id: mechanism:loss-masking-preserves-reasoning-traces
  confidence: medium
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
---

A lightweight open-source Python library (PyPI/GitHub) providing model-agnostic utilities for reasoning-aware training and evaluation of HuggingFace transformers models. Exposes four modules: thinkpack.chat (chat template construction), thinkpack.parse (trace parsing into valid/empty/missing/truncated), thinkpack.stats (VR/ER/MR/TR/Rpass@1 computation), and thinkpack.mask (loss masking for masked-think and response-only strategies).

**Why it matters here:** ThinkPack operationalizes the structural evaluation framework for reasoning-trace collapse, enabling reproducible cross-model comparison without model-specific parsing code. Directly applicable to Phase 1 monitoring.

**Lineage:** Released alongside Twist et al. 2026 (arXiv:2605.21127), Section 4 and Appendix A.
