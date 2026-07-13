---
aliases:
- H3 termination-rule instrumentation defect
- eos-at-final-position misgraded as not-terminated
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:batched-termination-rule-misgrades-eos-at-final-position
  type: mechanism
  status: canonical
cause: "A batched sampled-decode grading harness requires terminated_naturally to satisfy eos_pos < n_new_tokens - 1, stricter than the registered metric text (\"terminated naturally, stopped before max_new\"); when 8 identical-prompt copies are batched together and a snap-induced write compresses refusals to near-identical short lengths, the batch member(s) tying for longest-in-batch emit eos at the block's final position."
effect: "764 of 769 refused-but-well-formed fired-confab samples in a text-persisting single-seed diagnostic failed ONLY the termination conjunct (eos at the final position, otherwise complete clean refusal text), collapsing the original K=5 pooled majority-vote conversion to 140/925 = 15.1% against the 63.5% floor and producing a FALSIFIED verdict on an instrumentation artifact rather than a real behavioral null. Persisting per-sample text and eos position (instead of booleans only) was what made the failure diagnosable. Fixing the rule to \"eos anywhere in the block, or block shorter than max_new\" (matching the registered text) restored pooled majority-vote conversion to 643/925 = 69.5%, verified by triple agreement: diagnostic replay, a parity recompute on the diagnostic's persisted inputs, and an independent full K=5 re-run."
polarity: decreases
related:
- '[[snap-seed-sampled-decode-replication]]'
- '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
- '[[sampled-decode-preserves-doubt-gated-caution-headline]]'
relationships:
- type: supported_by
  target: '[[snap-seed-sampled-decode-replication]]'
  target_id: experiment:snap-seed-sampled-decode-replication
  confidence: high
  evidence:
  - experiments/snap-seed-sampled-decode-replication/AMENDMENT.md#outcome (Instrument correction history)
- type: related_to
  target: '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
  target_id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  confidence: medium
- type: related_to
  target: '[[sampled-decode-preserves-doubt-gated-caution-headline]]'
  target_id: mechanism:sampled-decode-preserves-doubt-gated-caution-headline
  confidence: high
---

A durable methods finding from `snap-seed-sampled-decode-replication` (H3):
a batched termination-rule conjunct that is stricter than its own registered
metric text can manufacture a false behavioral null when the intervention
under test compresses generations to near-identical lengths within a batch.
The original K=5 sampled-decode run resolved FALSIFIED on exactly this
defect; only persisting per-sample generation text (rather than booleans
alone) made the failure anatomy recoverable, and the corrected rule
reproduced the true conversion rate, closed by diagnostic-replay, parity-
recompute, and independent-rerun agreement. This is a distinct root cause
from [[qwen35-batch-composition-flips-greedy-decode-outcomes]] (bf16
batch-composition changing matmul reduction order and flipping greedy
tie-breaks on a different model family): both are batched-decode grading
hazards on this program's instruments, but one is a numerics artifact and
this one is a grading-conjunct defect exposed only under sampled decode.
