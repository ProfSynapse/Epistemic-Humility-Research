---
aliases:
- H3 headline decode-robustness (73.5%/3.1% survives sampling)
- doubt-gated caution snap survives temperature-0.7 sampled decode
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sampled-decode-preserves-doubt-gated-caution-headline
  type: mechanism
  status: canonical
cause: "Re-measuring the resolved doubt-gated caution snap's frozen instrument (same directions, gate threshold, standardization, and held-out split; no refit) under temperature-0.7, top_p-0.9 sampled decoding (N=8 samples per row, K=5 independent seeds, majority-vote >=5/8 aggregation) in place of the original single greedy decode, on the corrected termination-rule instrument."
effect: "Pooled majority-vote confab clean_tighten conversion is 643/925 = 69.5% (Wilson 95% CI [66.5%, 72.4%]), above the pre-registered 63.5% floor in every one of the 5 seeds individually (68.1%-70.8%), only about 4 points below the greedy reproduction of 73.5%. Known-correct false-refusal cost stays low at 60/1290 = 4.65% (Wilson upper bound 5.9%, below the 12% ceiling), and both G3 placebo margins (random-direction near-no-op, permuted-gate materially worse) hold in all 5 seeds. The resolved 73.5%/3.1% greedy headline is decode-robust rather than an artifact of a single deterministic decode, so it no longer needs to be re-scoped to \"one greedy decode.\""
polarity: mediates
related:
- '[[snap-seed-sampled-decode-replication]]'
- '[[doubt-gated-caution-tighten]]'
- '[[batched-termination-rule-misgrades-eos-at-final-position]]'
relationships:
- type: supported_by
  target: '[[snap-seed-sampled-decode-replication]]'
  target_id: experiment:snap-seed-sampled-decode-replication
  confidence: high
  evidence:
  - experiments/snap-seed-sampled-decode-replication/AMENDMENT.md#outcome
- type: related_to
  target: '[[doubt-gated-caution-tighten]]'
  target_id: experiment:doubt-gated-caution-tighten
  confidence: high
- type: related_to
  target: '[[batched-termination-rule-misgrades-eos-at-final-position]]'
  target_id: mechanism:batched-termination-rule-misgrades-eos-at-final-position
  confidence: high
---

*Legacy naming note (2026-08-16): this note's title/slug predates the program's vocabulary rename; see `papers/common/terminology.md` for current running-prose terms (known-unknown direction, KU readout gate, refusal axis, KU-readout coupling, IDK switch). The slug stays verbatim under usage rule 1.*

The resolved Qwen3-4B doubt-gated caution snap's headline
(gated confab clean_tighten 73.5%, known-correct false-refusal 3.1%,
[[doubt-gated-caution-tighten]]) was established under a single greedy
decode only. `snap-seed-sampled-decode-replication` (H3) closes that
credibility gap: on the corrected termination-rule instrument, the same
frozen directions and gate under temperature-0.7 sampled decoding degrade
only mildly (69.5% pooled majority-vote conversion, every seed above the
63.5% floor) rather than collapsing, and cost and placebo specificity both
hold. The headline is therefore decode-robust, not scoped to greedy decode
alone. This result depends on
[[batched-termination-rule-misgrades-eos-at-final-position]] having been
diagnosed and fixed first: on the original (defective) instrument, the same
comparison read as a falsified 15.1% pooled conversion.
