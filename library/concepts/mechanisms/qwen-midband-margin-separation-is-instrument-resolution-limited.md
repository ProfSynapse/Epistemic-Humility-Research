---
title: qwen-midband-margin-separation-is-instrument-resolution-limited
aliases:
- fine-ladder retest halts at RG0 before a separation verdict is possible
- boundary-row tipping is batch-composition dependent, not cleanly quantization-limited
  or cleanly real
- byte-identical reuse guard is the wrong bar under bf16 batched decoding
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-midband-margin-separation-is-instrument-resolution-limited
  type: mechanism
  status: canonical
cause: "M1 (margin-mapping)'s censoring-aware separation criterion failed at coarse ladder resolution (observable bound 2.0 against a 2.5 floor), but the coarse 10-rung ladder quantized achievable bounds to {2.0, 3.0} with nothing between, so the criterion could not have returned any value in the interval containing the floor. M1b (margin-separation-fine-ladder) retested the same criterion at fine resolution inside the critical bracket (0.5x, 0.75x], generating four new rungs (0.55x-0.7x) for only the 53 confab rows whose M1 tipping fell there, with the 0.6x rung constructed so the observable bound reaches exactly 2.5 if the merged confab median falls at or below it. The pre-registered RG0 drift check regenerated M1's own 0.75x-rung rows and compared them byte-for-byte against M1's committed runlog before any fine-rung criterion could be computed."
effect: "The RG0 check found 3 of 8 probe rows diverging in completion text and halted per the signed rule (any mismatch halts, lifts to PI, never a silent retry). Diagnostics on all 53 refined rows regenerated fresh at 0.5x and 0.75x showed detector bits 98.1% identical (52/53) and bracket (tipping) classification preserved on 51/53, but byte match only 74%/87%: the drift is stochastic bf16 batch-composition non-determinism (row 131 flips its tipping bit across batch sizes with no other variable changing), not a deterministic environment shift. The boundary rows have no batch-invariant tipping classification: the per-row bracket noise (~4%) is the same order as M1's own accepted 3.5% non-monotone rate (C1 ceiling 0.05), so the point-estimate criterion at the 0.6x boundary is not well-posed when the median sits within the instrument's own reproducibility noise. M1's Claim 1 falsification stands, but the miss is neither a clean quantization artifact nor a clean real separation; a byte-identical reuse guard is shown to be the wrong bar under bf16 batched greedy decoding, since completion text depends on batch composition even in a stable environment."
polarity: prevents
related:
- '[[margin-separation-fine-ladder]]'
- '[[margin-mapping]]'
- '[[margin-theory-of-epistemic-state]]'
- '[[qwen-midband-commitment-margins-miss-separation-floor]]'
- '[[commitment-margin]]'
relationships:
- type: supported_by
  target: '[[margin-separation-fine-ladder]]'
  target_id: experiment:margin-separation-fine-ladder
  confidence: high
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md#outcome (Outcome;
    RG0 drift check halt, diagnostics, and one-sentence verdict)
- type: related_to
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md (Motivation and
    posture; M1b retests M1's censoring-aware separation criterion at fine
    resolution inside M1's own critical bracket)
- type: related_to
  target: '[[margin-theory-of-epistemic-state]]'
  target_id: term:margin-theory-of-epistemic-state
  confidence: high
  evidence:
  - docs/research/margin-theory-framework.md (section 2, Claim 1)
- type: related_to
  target: '[[qwen-midband-commitment-margins-miss-separation-floor]]'
  target_id: mechanism:qwen-midband-commitment-margins-miss-separation-floor
  confidence: high
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md (Outcome; M1's
    Claim 1 falsification stands, the resolution excuse removed but not
    confirmed as real separation either)
- type: related_to
  target: '[[commitment-margin]]'
  target_id: term:commitment-margin
  confidence: medium
  evidence:
  - experiments/margin-separation-fine-ladder/AMENDMENT.md (Design; tipping
    dose convention carried byte-identical from M1)
---

The margin-separation-fine-ladder experiment (M1b) set out to answer the one
question M1 (margin-mapping) could not: whether the merged confab median,
measured at fine ladder resolution inside the critical bracket, reaches the
registered 2.5 separation floor. It never got to compute that criterion. The
signed rg0_drift_check regenerated M1's own 0.75x-rung rows and found 3 of 8
diverging from the committed runlog, halting the run per the pre-registered
rule.

Diagnostics run on the halt (booleans/lengths/offsets only, no completion
text; gitignored) show the divergence is not an environment shift:
detector-bit stability across fresh 0.5x/0.75x regenerations is 98.1%
(52/53), and bracket classification is preserved on 51/53 rows, but
byte-for-byte match is only 74%/87%. Row 131 flips its tipping bit purely as
a function of batch size (bs1 refused=False, bs4 refused=True matching M1,
bs8 refused=False), which is the fingerprint of stochastic bf16
batched-decoding non-determinism, not a deterministic drift.

**Why it matters here:** the boundary rows M1b needed to classify precisely
have no batch-invariant tipping classification. The ~4% per-row bracket noise
this reveals is the same order as the 3.5% non-monotone rate M1 itself
accepted under its C1 construct-integrity ceiling (0.05), so a point-estimate
criterion pinned to a single rung boundary (median vs the 0.6x rung) is not
well-posed at this resolution: the answer would depend on which batch
composition happened to run. M1's Claim 1 falsification (observable bound 2.0
vs floor 2.5) stands unchanged; M1b establishes that the miss is neither a
clean quantization artifact (which a fine ladder would have resolved) nor a
clean real separation (which a stable boundary classification would have
confirmed), but sits inside the instrument's own reproducibility noise.

**Instrument lesson (durable):** the RG0 reuse guard was drafted as
byte-identity, which is the wrong bar under bf16 batched greedy decoding:
completion text depends on batch composition, so byte-identity is
unreachable across batching regimes even without any environment change. A
design that reuses or merges rows across batching regimes carries a seam of
irreducible per-row noise at exactly this magnitude; the guard should have
checked detector-bit / bracket-preservation, not byte identity. This was a
drafting gap the pre-sign red-team review also missed, and it changes the
reuse-guard convention for future amendments that mix batching regimes.

**Lineage:** direct retest of [[margin-mapping]] (M1)'s Claim 1 separation
criterion within [[margin-theory-of-epistemic-state]], reusing M1's
substrate, direction, dose law, decoding, detector stack, and criterion
byte-identically. Resolves the quantization-vs-real ambiguity left open by
[[qwen-midband-commitment-margins-miss-separation-floor]] as
instrument-resolution-limited rather than confirming either alternative.
Source of truth: `experiments/margin-separation-fine-ladder/AMENDMENT.md`,
Outcome section, resolved 2026-07-17.
